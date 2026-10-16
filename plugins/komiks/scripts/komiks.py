#!/usr/bin/env python3
"""Narzędzie pluginu „komiks”: katalog komiksu, biblia, odcinki, strona HTML.

Działa na czystym Pythonie 3.9+ (bez doinstalowywania czegokolwiek).
Wszystkie komunikaty są po polsku, bo czyta je Codex i powtarza użytkownikowi.

Uruchamianie:  python3 komiks.py <polecenie> [opcje]      (Windows: py -3 komiks.py ...)
Pomoc:         python3 komiks.py --help
"""

import argparse
import datetime as dt
import difflib
import filecmp
import html
import json
import math
import os
import re
import shutil
import struct
import sys
import tempfile
import unicodedata
import urllib.request
import zlib
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SZABLON_STRONY = PLUGIN_ROOT / "szablony" / "strona"
REPO = "guc-net/codex-marketplace"
MARKETPLACE = "guc-net"
SUROWY_URL = "https://raw.githubusercontent.com/" + REPO + "/main/plugins/komiks/"
OBRAZY = {".png", ".jpg", ".jpeg", ".webp"}
TEKSTOWE = {".md", ".txt", ".yaml", ".yml", ""}

# Arkusz obrotu postaci: każdy widok to osobny obraz w biblia/postaci/<postać>/widoki/.
WIDOKI = {
    "przod": "przód",
    "tyl": "tył",
    "profil-lewy": "lewy profil",
    "profil-prawy": "prawy profil",
    "trzy-czwarte": "3/4",
}
WIDOKI_DODATKOWE = {"gora": "z góry", "dol": "z dołu"}  # tylko na życzenie (komiks.yaml)

DOMYSLNY_KOMIKS = {
    "tytul": "",
    "jezyk": "pl",
    "stan": "projekt",
    "kanal": "instagram",
    "rytm": "",                     # np. "1 odcinek w tygodniu"
    "widoki_dodatkowe": "",         # "gora,dol" = postaci także z góry i z dołu
    # Odpowiedzi na otwarte pytania zmieniają tylko te pola:
    "format": "1080x1350",          # Instagram 4:5; 1080x1080 dla 1:1
    "plansze_na_post": 1,           # >1 = karuzela
    "dymki": "w-obrazie",           # w-obrazie | nakladane (na przyszłość)
    "autor": "",
    "kolor_tla": "#fbf7f0",
    "kolor_tekstu": "#2b2522",
    "kolor_akcentu": "#d9480f",
    "font": "Georgia, 'Times New Roman', serif",
}


class Blad(Exception):
    """Błąd użytkownika — drukujemy komunikat bez śladu stosu."""


# --- mały YAML: tylko płaskie „klucz: wartość” ------------------------------
# Pliki muszą być czytelne dla człowieka i bez zależności, więc obsługujemy
# podzbiór YAML: jedna para na linię, napisy w cudzysłowie JSON albo gołe,
# liczby całkowite, komentarze „#”.

def czytaj_yaml(sciezka):
    dane = {}
    for nr, linia in enumerate(Path(sciezka).read_text(encoding="utf-8").splitlines(), 1):
        if not linia.strip() or linia.lstrip().startswith("#"):
            continue
        if ":" not in linia:
            raise Blad(f"{sciezka}:{nr}: oczekiwano „klucz: wartość”, jest: {linia!r}")
        klucz, wartosc = linia.split(":", 1)
        dane[klucz.strip()] = _wartosc_yaml(wartosc.strip(), sciezka, nr)
    return dane


def _wartosc_yaml(w, sciezka, nr):
    if w.startswith('"'):
        try:
            return json.loads(w)
        except ValueError:
            raise Blad(f"{sciezka}:{nr}: zły napis w cudzysłowie: {w}")
    if w.startswith("'") and w.endswith("'") and len(w) >= 2:
        return w[1:-1].replace("''", "'")
    w = re.sub(r"\s+#.*$", "", w)
    if re.fullmatch(r"-?\d+", w):
        return int(w)
    if w in ("", "~", "null"):
        return None
    return w


def zapisz_yaml(sciezka, dane, naglowek=None):
    linie = [f"# {naglowek}"] if naglowek else []
    for k, v in dane.items():
        if v is None:
            linie.append(f"{k}:")
        elif isinstance(v, int) and not isinstance(v, bool):
            linie.append(f"{k}: {v}")
        else:
            linie.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
    Path(sciezka).write_text("\n".join(linie) + "\n", encoding="utf-8")


# --- pomocnicze ----------------------------------------------------------------

def slug(tekst):
    t = unicodedata.normalize("NFKD", tekst.replace("ł", "l").replace("Ł", "L"))
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:50].strip("-") or "bez-nazwy"


def teraz():
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def dzis():
    return dt.date.today().isoformat()


def liczba(n, jeden, kilka, wiele):
    """Polska odmiana: 1 plansza, 2 plansze, 5 plansz."""
    if n == 1:
        return f"{n} {jeden}"
    return f"{n} {kilka if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else wiele}"


def info(tekst=""):
    print(tekst)


# --- biblioteka: jeden stały folder ze wszystkimi komiksami -------------------
# Ustawienie leży w katalogu domowym, a nie w komiksie, żeby działało w każdej
# nowej rozmowie — niezależnie od folderu, który Codex akurat otworzył.
# Bez ustawienia wszystko działa jak w 0.2: komiksy w bieżącym folderze.

def plik_ustawien():
    return Path(os.environ.get("KOMIKS_USTAWIENIA")
                or Path.home() / ".komiks-plugin" / "ustawienia.json").expanduser()


def czytaj_ustawienia():
    plik = plik_ustawien()
    if not plik.is_file():
        return {}
    try:
        dane = json.loads(plik.read_text(encoding="utf-8"))
    except ValueError:
        raise Blad(f"{plik}: uszkodzony plik ustawień. Ustaw bibliotekę od nowa: "
                   "komiks.py biblioteka --ustaw <folder>")
    return dane if isinstance(dane, dict) else {}


def zapisz_ustawienia(dane):
    plik = plik_ustawien()
    plik.parent.mkdir(parents=True, exist_ok=True)
    plik.write_text(json.dumps(dane, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def biblioteka():
    """Folder biblioteki z ustawień albo None."""
    sciezka = czytaj_ustawienia().get("biblioteka")
    return Path(sciezka).expanduser() if sciezka else None


def folder_komiksow(folder=None):
    """Gdzie są komiksy: --folder (jednorazowo) > biblioteka z ustawień > bieżący folder."""
    if folder:
        return Path(folder).expanduser().resolve()
    bib = biblioteka()
    if bib is None:
        return Path(".").resolve()
    if not bib.is_dir():
        raise Blad(f"Nie ma folderu biblioteki komiksów: {bib} (odłączony dysk albo przeniesiony "
                   "folder?). Podłącz go albo ustaw nowy: komiks.py biblioteka --ustaw <folder>")
    return bib


def komiksy_w(korzen):
    if (korzen / "komiks.yaml").is_file():
        return [korzen]
    if not korzen.is_dir():
        return []
    return sorted(p for p in korzen.iterdir() if (p / "komiks.yaml").is_file())


def znajdz_komiks(sciezka):
    """Katalog komiksu: podany wprost, sama nazwa komiksu z biblioteki albo najbliższy
    rodzic z komiks.yaml; poza komiksem — jedyny komiks w bibliotece."""
    bib = biblioteka()
    p = Path(sciezka or ".").expanduser()
    if sciezka and not p.is_absolute() and not p.exists() and bib and (bib / p).is_dir():
        p = bib / p
    p = p.resolve()
    for kandydat in [p, *p.parents]:
        if (kandydat / "komiks.yaml").is_file():
            return kandydat
    if not sciezka and bib and bib.is_dir():
        komiksy = komiksy_w(bib)
        if len(komiksy) == 1:
            return komiksy[0]
        if komiksy:
            raise Blad(f"W bibliotece {bib} jest kilka komiksów: "
                       f"{', '.join(k.name for k in komiksy)}. Podaj --komiks <nazwa>.")
    raise Blad(f"Nie znaleziono komiks.yaml w {p} ani wyżej. Podaj --komiks <folder komiksu>.")


def wczytaj_komiks(kat):
    dane = dict(DOMYSLNY_KOMIKS)
    dane.update(czytaj_yaml(kat / "komiks.yaml"))
    return dane


def wersja_biblii(kat):
    plik = kat / "biblia" / "WERSJA"
    try:
        return int(plik.read_text(encoding="utf-8").strip() or 0)
    except FileNotFoundError:
        return 0
    except ValueError:
        raise Blad(f"{plik}: oczekiwano jednej liczby.")


def pliki_drzewa(kat):
    if not kat.is_dir():
        return []
    return sorted(p.relative_to(kat).as_posix() for p in kat.rglob("*")
                  if p.is_file() and p.name != ".DS_Store")


def roznice(stary, nowy, pomin=("WERSJA",)):
    """Zwraca (dodane, usuniete, zmienione) między dwoma drzewami katalogów."""
    a = set(pliki_drzewa(stary)) - set(pomin)
    b = set(pliki_drzewa(nowy)) - set(pomin)
    zmienione = sorted(f for f in a & b
                       if not filecmp.cmp(stary / f, nowy / f, shallow=False))
    return sorted(b - a), sorted(a - b), zmienione


def kopiuj_drzewo(zrodlo, cel):
    if cel.exists():
        shutil.rmtree(cel)
    shutil.copytree(zrodlo, cel)


def odcinki(kat):
    folder = kat / "odcinki"
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir()
                  if p.is_dir() and (p / "odcinek.yaml").is_file())


def znajdz_odcinek(kat, nazwa):
    for p in odcinki(kat):
        if p.name == nazwa or p.name.split("-", 1)[0] == nazwa.zfill(3):
            return p
    raise Blad(f"Nie ma odcinka „{nazwa}”. Istniejące: " +
               (", ".join(p.name for p in odcinki(kat)) or "brak"))


def wersje_odcinka(odc):
    folder = odc / "wersje"
    if not folder.is_dir():
        return []
    return sorted((p for p in folder.iterdir() if p.is_dir() and re.fullmatch(r"v\d+", p.name)),
                  key=lambda p: int(p.name[1:]))


def obrazy_w(folder):
    return sorted((p for p in folder.iterdir() if p.suffix.lower() in OBRAZY),
                  key=lambda p: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p.name)])


# --- polecenia: start ----------------------------------------------------------

AGENTS_MD = """# Komiksy

Ten folder to pracownia komiksów. Pracuj w nim pluginem **komiks**:
na początku każdej rozmowy użyj skilla `komiks` (sprawdza aktualizacje
i mówi, na jakim etapie jest każdy komiks).

- Każdy podfolder z plikiem `komiks.yaml` to osobny komiks.
- Biblii komiksu (`biblia/`) w fazie produkcji nie zmieniaj bez zatwierdzenia
  przez użytkownika — tylko procedurą skilla `komiks-zmiana`.
- Rozmawiaj po polsku, prostym językiem, bez żargonu technicznego.
"""

SZKIELET_STYLU = """# Styl

(nazwa stylu i skąd: wybrana próbka, ewentualnie mieszanka dwóch)

## Kreska

## Paleta

(5–8 kolorów z kodami, np. #F4A259 marchewkowy; kolor tła)

## Światło i cień

## Faktura i wykończenie

## Kadrowanie

(typowa odległość kamery, wysokość horyzontu)

## Liternictwo dymków

## Blok stylu

(2–4 zdania, które idą DOSŁOWNIE na początek każdego promptu; nie zmieniaj ich słów)

## Nie rób

(lista negatywów, np. fotorealizm; plastikowy połysk; gradienty jak z AI; inne style)
"""

SZKIELET_BIBLII = {
    "styl.md": SZKIELET_STYLU,
    "kadry.md": "# Kadry\n\n(typowe układy plansz, format, kadr otwierający i zamykający)\n",
    "dymki.md": "# Dymki\n\nTryb: tekst w obrazie.\n\n(długość kwestii, kto mówi pierwszy, styl liter)\n",
    "ton.md": "# O czym jest ten komiks\n\n(temat, odbiorca, morał, czego nie mówimy)\n",
}


def _wyglada_na_tymczasowy(folder):
    tekst = folder.as_posix().lower()
    tmp = Path(tempfile.gettempdir()).resolve().as_posix().lower()
    return (tekst.startswith(tmp + "/") or tekst == tmp or "/var/folders/" in tekst
            or "/.codex/" in tekst or "/tmp/" in tekst + "/")


def cmd_biblioteka(a):
    dane = czytaj_ustawienia()
    if a.ustaw:
        folder = Path(a.ustaw).expanduser().resolve()
        if folder.exists() and not folder.is_dir():
            raise Blad(f"{folder} to plik, nie folder.")
        folder.mkdir(parents=True, exist_ok=True)
        if not (folder / "AGENTS.md").exists():
            (folder / "AGENTS.md").write_text(AGENTS_MD, encoding="utf-8")
        dane["biblioteka"] = str(folder)
        zapisz_ustawienia(dane)
        info(f"BIBLIOTEKA: {folder}")
        info("Od teraz nowe komiksy powstają tutaj, a stan pokazuje wszystkie komiksy z tego "
             "folderu — także w nowej rozmowie, niezależnie od otwartego folderu.")
        info(f"Komiksów w bibliotece: {len(komiksy_w(folder))}.")
        if _wyglada_na_tymczasowy(folder):
            info("UWAGA: to wygląda na folder tymczasowy — może zniknąć. Lepiej wybrać folder "
                 "w dokumentach albo projektach.")
        return 0
    if a.wylacz:
        dane.pop("biblioteka", None)
        zapisz_ustawienia(dane)
        info("NIE USTAWIONO: biblioteka wyłączona, komiksy znów w bieżącym folderze. "
             "Pliki komiksów zostały na miejscu.")
        return 0
    bib = biblioteka()
    if bib is None:
        info("NIE USTAWIONO: komiksy powstają w bieżącym folderze. "
             "Ustaw: komiks.py biblioteka --ustaw <folder>")
        return 0
    if not bib.is_dir():
        info(f"BRAK FOLDERU: biblioteka {bib} nie istnieje (odłączony dysk?).")
        return 1
    info(f"BIBLIOTEKA: {bib}")
    info(f"Komiksów w bibliotece: {len(komiksy_w(bib))}.")
    return 0


def cmd_przygotuj(a):
    folder = folder_komiksow(a.folder)
    folder.mkdir(parents=True, exist_ok=True)
    plik = folder / "AGENTS.md"
    if plik.exists() and not a.nadpisz:
        info(f"AGENTS.md już jest w {folder} — zostawiam bez zmian.")
    else:
        plik.write_text(AGENTS_MD, encoding="utf-8")
        info(f"Zapisano {plik}.")


def cmd_nowy(a):
    tytul = a.tytul.strip()
    if not tytul:
        raise Blad("Podaj tytuł komiksu.")
    folder = folder_komiksow(a.folder) / (a.nazwa or slug(tytul))
    if (folder / "komiks.yaml").exists():
        raise Blad(f"Komiks już istnieje: {folder}")
    for pod in ["biblia/styl", "biblia/postaci", "biblia/miejsca", "zmiany",
                "historia-biblii", "odcinki", "projekt"]:
        (folder / pod).mkdir(parents=True, exist_ok=True)
    dane = dict(DOMYSLNY_KOMIKS, tytul=tytul, utworzono=dzis())
    for k in ("format", "autor", "jezyk", "kanal", "rytm", "plansze_na_post", "widoki_dodatkowe"):
        if getattr(a, k):
            dane[k] = getattr(a, k)
    zapisz_yaml(folder / "komiks.yaml", dane, "Ustawienia komiksu. Stan zmienia skrypt, resztę możesz poprawić.")
    (folder / "biblia" / "WERSJA").write_text("0\n", encoding="utf-8")
    for nazwa, tresc in SZKIELET_BIBLII.items():
        (folder / "biblia" / nazwa).write_text(tresc, encoding="utf-8")
    info(f"Założono komiks „{tytul}” w {folder}")
    info("Stan: projekt. Następny krok: ton.md (o czym i dla kogo).")


def cmd_postac(a):
    kat = znajdz_komiks(a.komiks)
    _wymagaj_projektu(kat, "dodawać postaci wprost do biblii")
    folder = kat / "biblia" / "postaci" / (a.nazwa or slug(a.imie))
    if folder.exists():
        raise Blad(f"Postać już istnieje: {folder}")
    (folder / "pozy").mkdir(parents=True)
    (folder / "widoki").mkdir()
    widoki = {**WIDOKI, **{k: v for k, v in WIDOKI_DODATKOWE.items() if k in _dodatkowe(kat)}}
    (folder / "postac.md").write_text(
        f"# {a.imie}\n\n## Wygląd\n\n(wzrost względem innych postaci, proporcje w głowach, "
        "kształt twarzy, włosy)\n\n## Paleta\n\n(kody kolorów: skóra, włosy, oczy, ubranie)\n\n"
        "## Znaki szczególne\n\n(to, co ma być widać ZAWSZE, np. pieprzyk nad lewą brwią)\n\n"
        "## Ubiór\n\n## Charakter i sposób mówienia\n\n## Czego nie robi\n\n"
        "## Blok postaci\n\n(1–3 zdania do każdego promptu, zawsze tymi samymi słowami)\n\n"
        "## Pliki\n\n- arkusz.png — wszystkie widoki obok siebie na jednym obrazie\n" +
        "".join(f"- widoki/{k}.png — {v}\n" for k, v in widoki.items()) +
        "- mimika.png — zestaw min\n- pozy/ — typowe pozy, każda z opisem .md\n",
        encoding="utf-8")
    info(f"Dodano postać {a.imie}: {folder.relative_to(kat)}")
    info("Widoki do wygenerowania: " + ", ".join(f"widoki/{k}.png" for k in widoki))


def cmd_miejsce(a):
    kat = znajdz_komiks(a.komiks)
    _wymagaj_projektu(kat, "dodawać miejsca wprost do biblii")
    plik = kat / "biblia" / "miejsca" / f"{a.nazwa or slug(a.nazwa_miejsca)}.md"
    if plik.exists():
        raise Blad(f"Miejsce już istnieje: {plik}")
    plik.write_text(f"# {a.nazwa_miejsca}\n\n(opis tła; obraz obok pod tą samą nazwą .png)\n",
                    encoding="utf-8")
    info(f"Dodano miejsce: {plik.relative_to(kat)}")


def _dodatkowe(kat):
    return [w.strip() for w in str(wczytaj_komiks(kat).get("widoki_dodatkowe") or "").split(",")
            if w.strip() in WIDOKI_DODATKOWE]


def braki_widokow(kat):
    """{postać: [brakujące widoki]} dla postaci w biblii; pusty słownik = komplet."""
    wymagane = list(WIDOKI) + _dodatkowe(kat)
    braki = {}
    for postac in sorted((kat / "biblia" / "postaci").glob("*/postac.md")):
        folder = postac.parent / "widoki"
        jest = {p.stem for p in obrazy_w(folder)} if folder.is_dir() else set()
        brak = [w for w in wymagane if w not in jest]
        if brak:
            braki[postac.parent.name] = brak
    return braki


def _opis_brakow(braki):
    nazwy = {**WIDOKI, **WIDOKI_DODATKOWE}
    return "; ".join(f"{p}: " + ", ".join(nazwy[w] for w in b) for p, b in braki.items())


def _wymagaj_projektu(kat, czynnosc):
    if wczytaj_komiks(kat)["stan"] != "projekt":
        raise Blad(f"Komiks jest w produkcji — nie można {czynnosc}. "
                   "Użyj wniosku o zmianę: komiks.py zmiana-nowa ...")


def cmd_start_produkcji(a):
    kat = znajdz_komiks(a.komiks)
    dane = wczytaj_komiks(kat)
    if dane["stan"] != "projekt":
        raise Blad("Ten komiks jest już w produkcji.")
    _wymagaj_zgody(a.zgoda)
    braki = [n for n in ("styl.md", "ton.md", "kadry.md", "dymki.md")
             if not (kat / "biblia" / n).is_file()]
    if braki:
        raise Blad("Brakuje plików biblii: " + ", ".join(braki))
    widoki = braki_widokow(kat)
    if widoki:
        raise Blad("Arkusze postaci są niepełne (brakuje widoków w widoki/): " + _opis_brakow(widoki) +
                   ". Wygeneruj je z arkuszem i wzorem stylu na wejściu.")
    (kat / "biblia" / "WERSJA").write_text("1\n", encoding="utf-8")
    kopiuj_drzewo(kat / "biblia", kat / "historia-biblii" / "v1")
    dane["stan"] = "produkcja"
    zapisz_yaml(kat / "komiks.yaml", dane, "Ustawienia komiksu. Stan zmienia skrypt, resztę możesz poprawić.")
    _wpis_zmiany(kat, "poczatek", "Początek: biblia v1", "zatwierdzona",
                 "Koniec fazy projektu. Biblia zamrożona jako wersja 1.",
                 zgoda=a.zgoda, wersja=1)
    info("Biblia v1 zatwierdzona. Komiks w produkcji — można robić odcinki.")


def _wymagaj_zgody(zgoda):
    if not zgoda or not re.match(r"^\s*tak\b", zgoda, re.I):
        raise Blad("Brak wyraźnej zgody. Podaj --zgoda z dokładnymi słowami użytkownika "
                   "(muszą zaczynać się od „TAK”).")


# --- polecenia: zmiany biblii -------------------------------------------------

def _wnioski(kat):
    folder = kat / "zmiany"
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.glob("[0-9][0-9][0-9][0-9]-*.md"))


def _naglowek_wniosku(plik):
    tekst = plik.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", tekst, re.S)
    if not m:
        return {}, tekst
    dane = {}
    for linia in m.group(1).splitlines():
        if ":" in linia:
            k, v = linia.split(":", 1)
            dane[k.strip()] = _wartosc_yaml(v.strip(), plik, 0)
    return dane, tekst[m.end():]


def _zapisz_wniosek(plik, dane, cialo):
    linie = ["---"]
    for k, v in dane.items():
        linie.append(f"{k}: {v}" if isinstance(v, int) else f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
    linie.append("---")
    plik.write_text("\n".join(linie) + "\n" + cialo, encoding="utf-8")


def _wpis_zmiany(kat, nazwa, tytul, status, opis, zgoda=None, wersja=None):
    nr = len(_wnioski(kat)) + 1
    plik = kat / "zmiany" / f"{nr:04d}-{slug(nazwa)}.md"
    dane = {"numer": nr, "tytul": tytul, "status": status, "utworzono": teraz()}
    if wersja:
        dane["wersja_biblii"] = wersja
    if zgoda:
        dane["zatwierdzono"] = teraz()
        dane["zgoda"] = zgoda
    _zapisz_wniosek(plik, dane, f"\n# {tytul}\n\n{opis.strip()}\n")
    return plik


def _znajdz_wniosek(kat, nr):
    for p in _wnioski(kat):
        if p.name.startswith(f"{int(nr):04d}-"):
            return p
    raise Blad(f"Nie ma wniosku nr {nr}.")


def cmd_zmiana_nowa(a):
    kat = znajdz_komiks(a.komiks)
    if wczytaj_komiks(kat)["stan"] != "produkcja":
        raise Blad("W fazie projektu biblię zmienia się wprost — wniosek nie jest potrzebny.")
    otwarte = [p.name for p in _wnioski(kat) if _naglowek_wniosku(p)[0].get("status") == "propozycja"]
    if otwarte:
        raise Blad("Jest już otwarty wniosek: " + ", ".join(otwarte) +
                   ". Najpierw go zatwierdź albo odrzuć.")
    plik = _wpis_zmiany(kat, a.nazwa, a.tytul, "propozycja", a.opis)
    robocza = plik.with_suffix("") / "biblia"
    kopiuj_drzewo(kat / "biblia", robocza)
    info(f"Wniosek: {plik.relative_to(kat)}")
    info(f"Wprowadź zmiany w KOPII: {robocza.relative_to(kat)} (nie w biblia/).")
    info("Potem: komiks.py zmiana-pokaz " + str(int(plik.name[:4])))


def cmd_zmiana_pokaz(a):
    kat = znajdz_komiks(a.komiks)
    plik = _znajdz_wniosek(kat, a.numer)
    dane, cialo = _naglowek_wniosku(plik)
    robocza = plik.with_suffix("") / "biblia"
    info(f"Wniosek {plik.name}: {dane.get('tytul')} — status: {dane.get('status')}")
    info(cialo.strip())
    if not robocza.is_dir():
        return
    dodane, usuniete, zmienione = roznice(kat / "biblia", robocza)
    if not (dodane or usuniete or zmienione):
        info("\nKopia robocza nie różni się jeszcze od biblii.")
        return
    info("\nZmiany w plikach biblii:")
    for f in dodane:
        info(f"  + nowy: {f}")
    for f in usuniete:
        info(f"  - usunięty: {f}")
    for f in zmienione:
        info(f"  ~ zmieniony: {f}")
        if Path(f).suffix.lower() in TEKSTOWE:
            stare = (kat / "biblia" / f).read_text(encoding="utf-8").splitlines()
            nowe = (robocza / f).read_text(encoding="utf-8").splitlines()
            for linia in difflib.unified_diff(stare, nowe, "było", "będzie", lineterm="", n=1):
                info("      " + linia)
        else:
            info(f"      obraz: było biblia/{f}, będzie {robocza.relative_to(kat)}/{f}")
    v = wersja_biblii(kat)
    gotowe = [p.name for p in odcinki(kat) if czytaj_yaml(p / "odcinek.yaml").get("final")]
    info(f"\nWpływ: biblia v{v} → v{v + 1}. Odcinki z finałem ({len(gotowe)}) zostają w swoich wersjach biblii; "
         f"nowe odcinki powstaną w v{v + 1}.")


def cmd_zmiana_zatwierdz(a):
    kat = znajdz_komiks(a.komiks)
    plik = _znajdz_wniosek(kat, a.numer)
    dane, cialo = _naglowek_wniosku(plik)
    if dane.get("status") != "propozycja":
        raise Blad(f"Wniosek ma status „{dane.get('status')}”, nie da się go zatwierdzić.")
    _wymagaj_zgody(a.zgoda)
    problemy = _niezatwierdzone(kat)
    if problemy:
        raise Blad("Biblia ma zmiany spoza procedury — najpierw je wyjaśnij (komiks.py sprawdz).")
    robocza_kat = plik.with_suffix("")
    robocza = robocza_kat / "biblia"
    if not any(roznice(kat / "biblia", robocza)):
        raise Blad("Kopia robocza niczego nie zmienia — nie ma czego zatwierdzać.")
    nowa = wersja_biblii(kat) + 1
    kopiuj_drzewo(robocza, kat / "biblia")
    (kat / "biblia" / "WERSJA").write_text(f"{nowa}\n", encoding="utf-8")
    kopiuj_drzewo(kat / "biblia", kat / "historia-biblii" / f"v{nowa}")
    shutil.rmtree(robocza_kat)
    dane.update(status="zatwierdzona", wersja_biblii=nowa, zatwierdzono=teraz(), zgoda=a.zgoda)
    _zapisz_wniosek(plik, dane, cialo)
    info(f"Zmiana zatwierdzona. Biblia ma teraz wersję {nowa}.")


def cmd_zmiana_odrzuc(a):
    kat = znajdz_komiks(a.komiks)
    plik = _znajdz_wniosek(kat, a.numer)
    dane, cialo = _naglowek_wniosku(plik)
    if dane.get("status") != "propozycja":
        raise Blad(f"Wniosek ma status „{dane.get('status')}”.")
    robocza_kat = plik.with_suffix("")
    if robocza_kat.is_dir():
        shutil.rmtree(robocza_kat)
    dane.update(status="odrzucona", odrzucono=teraz())
    if a.powod:
        dane["powod"] = a.powod
    _zapisz_wniosek(plik, dane, cialo)
    info("Wniosek odrzucony i zapisany w dzienniku (nie będzie proponowany ponownie).")


# --- polecenia: odcinki --------------------------------------------------------

SCENARIUSZ = """# {tytul}

Biblia: v{wersja}. Pomysł: {pomysl}

## Plansza 1

### Kadr 1
- Miejsce:
- Kto i co robi:
- Dialog:

### Kadr 2
- Miejsce:
- Kto i co robi:
- Dialog:
"""


def cmd_odcinek_nowy(a):
    kat = znajdz_komiks(a.komiks)
    if wczytaj_komiks(kat)["stan"] != "produkcja":
        raise Blad("Najpierw dokończ projekt komiksu (start-produkcji).")
    nr = max([int(p.name[:3]) for p in odcinki(kat) if p.name[:3].isdigit()] or [0]) + 1
    folder = kat / "odcinki" / f"{nr:03d}-{slug(a.tytul)}"
    (folder / "wersje").mkdir(parents=True)
    v = wersja_biblii(kat)
    zapisz_yaml(folder / "odcinek.yaml", {
        "numer": nr, "tytul": a.tytul, "opis": a.opis or "", "utworzono": dzis(),
        "wersja_biblii": v, "status": "scenariusz", "final": None, "data_publikacji": None,
    })
    (folder / "scenariusz.md").write_text(
        SCENARIUSZ.format(tytul=a.tytul, wersja=v, pomysl=a.opis or ""), encoding="utf-8")
    info(f"Odcinek {nr:03d}: {folder.relative_to(kat)} (biblia v{v})")


def _najnowsze_obrazy(ile, katalog):
    katalog = Path(katalog).expanduser()
    if not katalog.is_dir():
        raise Blad(f"Nie ma katalogu z wygenerowanymi obrazami: {katalog}. Podaj pliki przez --plik.")
    pliki = [p for p in katalog.rglob("*") if p.is_file() and p.suffix.lower() in OBRAZY]
    pliki.sort(key=lambda p: p.stat().st_mtime)
    if len(pliki) < ile:
        raise Blad(f"W {katalog} jest tylko {len(pliki)} obrazów.")
    return pliki[-ile:]


def cmd_obraz(a):
    """Kopiuje ostatnio wygenerowany obraz pod wskazaną ścieżkę (np. arkusz postaci)."""
    zrodlo = Path(a.plik).expanduser() if a.plik else _najnowsze_obrazy(1, a.z_katalogu)[0]
    cel = Path(a.do).expanduser()
    if cel.suffix.lower() not in OBRAZY:
        cel = cel.with_suffix(zrodlo.suffix.lower())
    if cel.exists() and not a.nadpisz:
        raise Blad(f"{cel} już istnieje. Wybierz inną nazwę albo dodaj --nadpisz.")
    cel.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(zrodlo, cel)
    info(f"Zapisano {cel} (z {zrodlo.name}).")


def cmd_odcinek_wersja(a):
    kat = znajdz_komiks(a.komiks)
    odc = znajdz_odcinek(kat, a.odcinek)
    if a.najnowsze:
        zrodla = _najnowsze_obrazy(a.najnowsze, a.z_katalogu)
    else:
        zrodla = [Path(p).expanduser() for p in (a.plik or [])]
    if not zrodla:
        raise Blad("Podaj obrazy: --plik ŚCIEŻKA (kolejno plansze) albo --najnowsze N.")
    for z in zrodla:
        if not z.is_file() or z.suffix.lower() not in OBRAZY:
            raise Blad(f"To nie jest plik obrazu: {z}")
    numer = (int(wersje_odcinka(odc)[-1].name[1:]) if wersje_odcinka(odc) else 0) + 1
    cel = odc / "wersje" / f"v{numer}"
    cel.mkdir(parents=True)
    for i, z in enumerate(zrodla, 1):
        shutil.copy2(z, cel / f"plansza-{i}{z.suffix.lower()}")
    v = wersja_biblii(kat)
    prompt = Path(a.prompt_plik).read_text(encoding="utf-8") if a.prompt_plik else (a.prompt or "")
    (cel / "prompt.md").write_text(
        f"# Wersja v{numer}\n\nUtworzono: {teraz()}\nBiblia: v{v}\n\n"
        f"## Referencje\n\n" + "".join(f"- {r}\n" for r in (a.referencja or [])) +
        f"\n## Prompt\n\n{prompt.strip()}\n", encoding="utf-8")
    dane = czytaj_yaml(odc / "odcinek.yaml")
    dane.update(status="wersje", wersja_biblii=v)
    zapisz_yaml(odc / "odcinek.yaml", dane)
    info(f"Zapisano wersję v{numer} ({liczba(len(zrodla), 'plansza', 'plansze', 'plansz')}): "
         f"{cel.relative_to(kat)}")


def cmd_odcinek_final(a):
    kat = znajdz_komiks(a.komiks)
    odc = znajdz_odcinek(kat, a.odcinek)
    nazwa = a.wersja if a.wersja.startswith("v") else f"v{a.wersja}"
    zrodlo = odc / "wersje" / nazwa
    if not zrodlo.is_dir() or not obrazy_w(zrodlo):
        raise Blad(f"Nie ma wersji {nazwa} z obrazami w {odc.relative_to(kat)}.")
    final = odc / "final"
    if final.exists():
        shutil.rmtree(final)
    final.mkdir()
    for p in obrazy_w(zrodlo):
        shutil.copy2(p, final / p.name)
    m = re.search(r"^Biblia: v(\d+)", (zrodlo / "prompt.md").read_text(encoding="utf-8"), re.M) \
        if (zrodlo / "prompt.md").is_file() else None
    dane = czytaj_yaml(odc / "odcinek.yaml")
    poprzedni = dane.get("final")
    with open(odc / "historia-finalu.md", "a", encoding="utf-8") as f:
        if f.tell() == 0:
            f.write("# Historia wyboru finału\n\nWszystkie wersje zostają w wersje/.\n\n")
        f.write(f"- {teraz()}: final = wersje/{nazwa}"
                + (f" (wcześniej {poprzedni})" if poprzedni else "") + "\n")
    dane.update(status="gotowy", final=f"wersje/{nazwa}")
    if m:
        dane["wersja_biblii"] = int(m.group(1))
    dane["data_publikacji"] = dane.get("data_publikacji") or dzis()
    zapisz_yaml(odc / "odcinek.yaml", dane)
    info(f"Final odcinka {odc.name}: {nazwa} (oryginały w pełnej jakości do strony HTML: "
         f"{final}).")
    info()
    gotowe_materialy(kat, odc)


# --- pliki na Instagram: docięcie i skala PNG (czysty Python) -----------------
# Generator obrazów w Codexie nie daje dokładnych 1080×1350: rozmiar wybiera sam
# (np. 1122×1402 albo 1024×1536). Final docinamy więc do proporcji posta (środek)
# i skalujemy do formatu z komiks.yaml.

def wymiary(format_):
    m = re.fullmatch(r"\s*(\d+)\s*[x×]\s*(\d+)\s*", str(format_ or ""))
    return (int(m.group(1)), int(m.group(2))) if m else None


def _czytaj_png(sciezka):
    """Zwraca (szer, wys, wiersze RGB). PNG 8/16 bit, bez przeplotu; alfa na białym tle."""
    d = Path(sciezka).read_bytes()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise Blad(f"{Path(sciezka).name} nie jest plikiem PNG.")
    i, idat, paleta, naglowek = 8, [], b"", None
    while i + 8 <= len(d):
        n, typ = struct.unpack(">I4s", d[i:i + 8])
        dane = d[i + 8:i + 8 + n]
        i += 12 + n
        if typ == b"IHDR":
            naglowek = struct.unpack(">IIBBBBB", dane)
        elif typ == b"PLTE":
            paleta = dane
        elif typ == b"IDAT":
            idat.append(dane)
        elif typ == b"IEND":
            break
    w, h, glebia, typ_k, _, _, przeplot = naglowek
    kanaly = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(typ_k)
    if przeplot or kanaly is None or glebia not in (8, 16) or (typ_k == 3 and glebia != 8):
        raise Blad(f"{Path(sciezka).name}: nieobsługiwany rodzaj PNG.")
    bpp = kanaly * glebia // 8
    stride = w * bpp
    surowe = zlib.decompress(b"".join(idat))
    poprz, wiersze = bytearray(stride), []
    for y in range(h):
        p = y * (stride + 1)
        f, linia = surowe[p], bytearray(surowe[p + 1:p + 1 + stride])
        if f == 1:
            for x in range(bpp, stride):
                linia[x] = (linia[x] + linia[x - bpp]) & 255
        elif f == 2:
            linia = bytearray((a + b) & 255 for a, b in zip(linia, poprz))
        elif f == 3:
            for x in range(stride):
                linia[x] = (linia[x] + (((linia[x - bpp] if x >= bpp else 0) + poprz[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = linia[x - bpp] if x >= bpp else 0
                b = poprz[x]
                c = poprz[x - bpp] if x >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                linia[x] = (linia[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        wiersze.append(linia)
        poprz = linia
    wynik = []
    for linia in wiersze:
        if glebia == 16:
            linia = linia[0::2]
        if typ_k == 3:
            linia = bytearray(b"".join(paleta[3 * k:3 * k + 3] for k in linia))
        elif typ_k in (4, 6):
            n = kanaly - 1
            alfa = linia[n::kanaly]
            kolor = bytearray(len(linia) // kanaly * n)
            for c in range(n):
                kolor[c::n] = linia[c::kanaly]
            if alfa.count(255) != len(alfa):
                kolor = bytearray((v * a + 255 * (255 - a)) // 255
                                  for v, a in zip(kolor, (a for a in alfa for _ in range(n))))
            linia = kolor
        if typ_k in (0, 4):
            linia = bytearray(v for v in linia for _ in range(3))
        wynik.append(linia)
    return w, h, wynik


def _zapisz_png(sciezka, w, h, wiersze):
    def blok(typ, dane):
        return struct.pack(">I", len(dane)) + typ + dane + struct.pack(">I", zlib.crc32(typ + dane) & 0xFFFFFFFF)
    Path(sciezka).write_bytes(
        b"\x89PNG\r\n\x1a\n" + blok(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
        blok(b"IDAT", zlib.compress(b"".join(b"\x00" + bytes(r) for r in wiersze), 6)) + blok(b"IEND", b""))


def _wagi(poczatek, dlugosc, cel):
    """Filtr trójkątny (jak w programach graficznych): przy zmniejszaniu uśrednia."""
    skala = dlugosc / cel
    zasieg = max(1.0, skala)
    wynik = []
    for j in range(cel):
        srodek = poczatek + (j + 0.5) * skala
        lo = max(poczatek, int(srodek - zasieg))
        hi = min(poczatek + dlugosc, int(srodek + zasieg) + 1)
        ws = [max(0.0, 1 - abs((k + 0.5 - srodek) / zasieg)) for k in range(lo, hi)]
        s = sum(ws) or 1.0
        wynik.append((lo, [x / s for x in ws]))
    return wynik


def do_formatu(zrodlo, cel, szer, wys):
    """Docina PNG do proporcji szer:wys (środek) i skaluje do szer×wys. Zwraca opis zmian."""
    w, h, wiersze = _czytaj_png(zrodlo)
    if w * wys > h * szer:
        cw, ch = round(h * szer / wys), h
    else:
        cw, ch = w, round(w * wys / szer)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    kolumny = _wagi(x0, cw, szer)
    poziomo = {}
    for y in {k for lo, ws in _wagi(y0, ch, wys) for k in range(lo, lo + len(ws))}:
        kanaly = [list(wiersze[y][c::3]) for c in range(3)]
        out = [0.0] * (szer * 3)
        for c in range(3):
            kan = kanaly[c]
            out[c::3] = [sum(v * q for v, q in zip(kan[lo:lo + len(ws)], ws)) for lo, ws in kolumny]
        poziomo[y] = out
    gotowe = []
    for lo, ws in _wagi(y0, ch, wys):
        acc = [v * ws[0] for v in poziomo[lo]]
        for k, q in enumerate(ws[1:], 1):
            acc = [a + v * q for a, v in zip(acc, poziomo[lo + k])]
        gotowe.append(bytearray(min(255, max(0, int(a + 0.5))) for a in acc))
    Path(cel).parent.mkdir(parents=True, exist_ok=True)
    _zapisz_png(cel, szer, wys, gotowe)
    return {"z": (w, h), "uciete": (w - cw, h - ch), "powiekszenie": szer / cw}


# --- gotowe/: jedno miejsce z zatwierdzonymi plikami do publikacji -------------
# <komiks>/gotowe/<odcinek>/ zawiera wyłącznie aktualny final w formacie posta.
# Zmiana finału podmienia ten folder w całości; wersje robocze zostają w wersje/,
# a historia-finalu.md w odcinku pamięta każdy wybór.

INFO_GOTOWE = "zatwierdzone.txt"


def folder_gotowe(kat, odc):
    return kat / "gotowe" / odc.name


def _rozmiar_obrazu(sciezka):
    try:
        with open(sciezka, "rb") as f:
            naglowek = f.read(24)
        if naglowek[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", naglowek[16:24])
    except OSError:
        pass
    return None


def komunikat_gotowe(kat, odc, cel, pliki):
    """pliki: lista (nazwa, (szer, wys) albo None, [uwagi])."""
    tytul = wczytaj_komiks(kat)["tytul"] or kat.name
    od = czytaj_yaml(odc / "odcinek.yaml")
    nr = odc.name.split("-", 1)[0]
    n = len(pliki)
    rozmiary = {r for _, r, _ in pliki}
    rozszerzenia = {Path(nazwa).suffix.lstrip(".").upper() for nazwa, _, _ in pliki}
    if len(rozmiary) == 1 and None not in rozmiary:
        (szer, wys), = rozmiary
        rozmiar = f"{'/'.join(sorted(rozszerzenia))} {szer} × {wys} px"
    else:
        rozmiar = f"{'/'.join(sorted(rozszerzenia))}, różne rozmiary (patrz uwagi)"
    kolejnosc = "pojedynczy post" if n == 1 else f"kolejność publikacji: 1 → {n}"
    linie = [
        "ZATWIERDZONE — GOTOWE DO PUBLIKACJI",
        f"Gotowe materiały do publikacji dla „{tytul}”, odcinek {nr}"
        + (f" („{od['tytul']}”)" if od.get("tytul") else "") + ":",
        str(cel),
        f"{liczba(n, 'slajd', 'slajdy', 'slajdów')} • {rozmiar} • {kolejnosc}",
    ]
    linie += [f"  {i}. {nazwa}" for i, (nazwa, _, _) in enumerate(pliki, 1)]
    uwagi = [f"UWAGA {nazwa}: {u}" for nazwa, _, us in pliki for u in us]
    linie += uwagi
    linie.append(f"Final: {od.get('final') or '?'} (wersje robocze zostają w {odc.relative_to(kat).as_posix()}/wersje/).")
    return "\n".join(linie)


def gotowe_materialy(kat, odc):
    """Buduje od nowa <komiks>/gotowe/<odcinek>/ z finału i drukuje komunikat."""
    final = odc / "final"
    if not final.is_dir() or not obrazy_w(final):
        raise Blad(f"{odc.name}: nie ma jeszcze finału — najpierw odcinek-final.")
    fmt = wczytaj_komiks(kat)["format"]
    wym = wymiary(fmt)
    cel = folder_gotowe(kat, odc)
    if cel.exists():
        shutil.rmtree(cel)
    cel.mkdir(parents=True)
    pliki = []
    for p in obrazy_w(final):
        uwagi = []
        if wym and p.suffix.lower() == ".png":
            szer, wys = wym
            nazwa = p.stem + ".png"
            r = do_formatu(p, cel / nazwa, szer, wys)
            if r["uciete"][1]:
                uwagi.append(f"ucięto {r['uciete'][1]} px z góry i dołu razem — sprawdź, czy dymki są całe")
            if r["uciete"][0]:
                uwagi.append(f"ucięto {r['uciete'][0]} px z boków razem — sprawdź brzegi kadrów")
            if r["powiekszenie"] > 1.15:
                uwagi.append(f"obraz był mały ({r['z'][0]}×{r['z'][1]}), powiększony — może być miękki")
        else:
            nazwa = p.name
            shutil.copy2(p, cel / nazwa)
            uwagi.append(f"format „{fmt}” w komiks.yaml nie wygląda jak 1080x1350 — skopiowany bez docięcia"
                         if not wym else "to nie PNG — skopiowany bez docięcia")
        pliki.append((nazwa, _rozmiar_obrazu(cel / nazwa), uwagi))
    tekst = komunikat_gotowe(kat, odc, cel, pliki)
    (cel / INFO_GOTOWE).write_text(f"{tekst}\nZatwierdzono: {teraz()}\n", encoding="utf-8")
    info(tekst)
    return cel


def cmd_instagram(a):
    kat = znajdz_komiks(a.komiks)
    gotowe_materialy(kat, znajdz_odcinek(kat, a.odcinek))


def cmd_gotowe(a):
    kat = znajdz_komiks(a.komiks)
    if a.odcinek:
        lista = [znajdz_odcinek(kat, a.odcinek)]
    else:
        lista = [p for p in odcinki(kat) if czytaj_yaml(p / "odcinek.yaml").get("final")]
        if not lista:
            info(f"„{wczytaj_komiks(kat)['tytul']}”: nie ma jeszcze zatwierdzonych odcinków.")
            return 0
    for i, odc in enumerate(lista):
        if i:
            info()
        opis = folder_gotowe(kat, odc) / INFO_GOTOWE
        if opis.is_file():
            info(opis.read_text(encoding="utf-8").rstrip())
        else:  # odcinek zatwierdzony przed wersją 0.3 — robimy gotowe/ teraz
            gotowe_materialy(kat, odc)
    return 0


# --- sprawdzanie ---------------------------------------------------------------

def _niezatwierdzone(kat):
    v = wersja_biblii(kat)
    wzor = kat / "historia-biblii" / f"v{v}"
    if not wzor.is_dir():
        return [f"brak zamrożonej kopii historia-biblii/v{v}"]
    dodane, usuniete, zmienione = roznice(wzor, kat / "biblia")
    return ([f"nowy plik bez zatwierdzenia: biblia/{f}" for f in dodane] +
            [f"usunięty bez zatwierdzenia: biblia/{f}" for f in usuniete] +
            [f"zmieniony bez zatwierdzenia: biblia/{f}" for f in zmienione])


def sprawdz_komiks(kat):
    problemy = []
    try:
        dane = wczytaj_komiks(kat)
    except Blad as e:
        return [str(e)]
    if dane["stan"] not in ("projekt", "produkcja"):
        problemy.append(f"komiks.yaml: nieznany stan „{dane['stan']}”")
    try:
        wersja_biblii(kat)
    except Blad as e:
        problemy.append(str(e))
    if dane["stan"] == "produkcja":
        problemy += _niezatwierdzone(kat)
    for odc in odcinki(kat):
        try:
            od = czytaj_yaml(odc / "odcinek.yaml")
        except Blad as e:
            problemy.append(str(e))
            continue
        if od.get("final"):
            if not (odc / od["final"]).is_dir():
                problemy.append(f"{odc.name}: final wskazuje na brakującą {od['final']}")
            if not (odc / "final").is_dir() or not obrazy_w(odc / "final"):
                problemy.append(f"{odc.name}: brak obrazów w final/")
    return problemy


def cmd_sprawdz(a):
    kat = znajdz_komiks(a.komiks)
    problemy = sprawdz_komiks(kat)
    if problemy:
        info("UWAGA — problemy w komiksie:")
        for p in problemy:
            info(f"  - {p}")
        info("Zmian biblii nie wolno wprowadzać bez zgody. Pokaż to użytkownikowi i zaproponuj "
             "wniosek o zmianę albo przywrócenie pliku z historia-biblii/.")
        return 1
    info("OK — biblia zgodna z zatwierdzoną wersją, odcinki kompletne.")
    return 0


def cmd_stan(a):
    korzen = folder_komiksow(a.folder)
    komiksy = komiksy_w(korzen)
    if not a.folder and biblioteka():
        info(f"Biblioteka komiksów: {korzen}")
    if not komiksy:
        info(f"W {korzen} nie ma jeszcze żadnego komiksu.")
        if not (korzen / "AGENTS.md").exists():
            info("Brak AGENTS.md — uruchom: komiks.py przygotuj")
        return
    for kat in komiksy:
        dane = wczytaj_komiks(kat)
        lista = odcinki(kat)
        gotowe = sum(1 for p in lista if czytaj_yaml(p / "odcinek.yaml").get("final"))
        info(f"- {dane['tytul']} ({kat.name}): stan {dane['stan']}, biblia v{wersja_biblii(kat)}, "
             f"odcinki {len(lista)} (gotowe {gotowe}), format {dane['format']}")
        if (kat / "gotowe").is_dir():
            info(f"  gotowe do publikacji: {kat / 'gotowe'}")
        otwarte = [p.name for p in _wnioski(kat) if _naglowek_wniosku(p)[0].get("status") == "propozycja"]
        if otwarte:
            info(f"  otwarty wniosek o zmianę: {', '.join(otwarte)}")
        if dane["stan"] == "projekt":
            probki = kat / "projekt" / "style"
            info(f"  postaci: {len(list((kat / 'biblia' / 'postaci').glob('*/postac.md')))}, "
                 f"wzory stylu: {len(obrazy_w(kat / 'biblia' / 'styl')) if (kat / 'biblia' / 'styl').is_dir() else 0}, "
                 f"próbki stylów: {len(obrazy_w(probki)) if probki.is_dir() else 0}")
            braki = braki_widokow(kat)
            if braki:
                info(f"  brakujące widoki postaci: {_opis_brakow(braki)}")


# --- prompt: stały blok stylu, postaci i referencje --------------------------

def sekcja(plik, tytul):
    """Treść sekcji „## tytul” z pliku Markdown (bez nawiasowych podpowiedzi szkieletu)."""
    if not plik.is_file():
        return ""
    m = re.search(rf"^##\s+{re.escape(tytul)}\s*$(.*?)(?=^##\s|\Z)",
                  plik.read_text(encoding="utf-8"), re.M | re.S)
    if not m:
        return ""
    return re.sub(r"^\(.*\)$", "", m.group(1).strip(), flags=re.M).strip()


def cmd_prompt_baza(a):
    kat = znajdz_komiks(a.komiks)
    biblia = kat / "biblia"
    dane = wczytaj_komiks(kat)
    referencje, uwagi, linie = [], [], []

    def ref(sciezka, opis):
        if sciezka.is_file():
            referencje.append((sciezka, opis))

    for p in obrazy_w(biblia / "styl") if (biblia / "styl").is_dir() else []:
        ref(p, "wzór stylu — tak ma wyglądać kreska, kolor i światło")
    blok = sekcja(biblia / "styl.md", "Blok stylu")
    if not blok:
        uwagi.append("styl.md nie ma sekcji „Blok stylu” — dopisz 2–4 stałe zdania o stylu.")
    zle = [w for w in a.widok or [] if w not in WIDOKI and w not in WIDOKI_DODATKOWE]
    if zle:
        raise Blad("Nieznany widok: " + ", ".join(zle) + ". Są: " + ", ".join([*WIDOKI, *WIDOKI_DODATKOWE]))
    for nazwa in a.postac or []:
        folder = biblia / "postaci" / slug(nazwa)
        if not (folder / "postac.md").is_file():
            raise Blad(f"Nie ma postaci „{nazwa}” w biblii. Są: " + (", ".join(
                p.parent.name for p in sorted((biblia / "postaci").glob("*/postac.md"))) or "brak"))
        imie = folder.name
        ref(folder / "arkusz.png", f"arkusz postaci {imie} — wygląd, proporcje, kolory")
        for w, opis in {**WIDOKI, **WIDOKI_DODATKOWE}.items():
            if w in (a.widok or []):
                ref(folder / "widoki" / f"{w}.png", f"{imie} — widok {opis}")
        opis = sekcja(folder / "postac.md", "Blok postaci") or sekcja(folder / "postac.md", "Wygląd")
        if opis:
            linie.append(f"{imie}: {opis}")
        else:
            uwagi.append(f"{imie}: postac.md nie ma „Blok postaci” — opis postaci weź z arkusza.")
    for nazwa in a.miejsce or []:
        obraz = next((p for p in obrazy_w(biblia / "miejsca") if p.stem == slug(nazwa)), None) \
            if (biblia / "miejsca").is_dir() else None
        if obraz:
            ref(obraz, f"miejsce {obraz.stem} — tło")
        else:
            uwagi.append(f"miejsce {slug(nazwa)}: brak obrazu tła w biblia/miejsca/.")
    nie_rob = sekcja(biblia / "styl.md", "Nie rób")

    info("OBRAZY NA WEJŚCIU (w tej kolejności):")
    for i, (p, opis) in enumerate(referencje, 1):
        info(f"  {i}. {p.relative_to(kat).as_posix()} — {opis}")
    if not referencje:
        info("  (brak — bez obrazów wzorcowych postaci i styl będą się zmieniać)")
    info("")
    info("POCZĄTEK PROMPTU (dosłownie, bez zmian):")
    if blok:
        info(blok)
    info("Postaci wyglądają DOKŁADNIE jak na arkuszach referencyjnych: te same proporcje, kolory, "
         "ubranie i znaki szczególne. Nie zmieniaj stylu względem wzoru stylu.")
    for linia in linie:
        info(linia)
    wym = wymiary(dane["format"])
    if wym:
        w, h = wym
        nwd = math.gcd(w, h)
        uklad = "pionowy" if h > w else "poziomy" if w > h else "kwadratowy"
        info(f"Format obrazu: {uklad}, proporcje {w // nwd}:{h // nwd}. Twarze, dymki i napisy z dala "
             "od samych krawędzi (margines ok. 5%).")
    else:
        info(f"Format obrazu: {dane['format']}.")
    if nie_rob:
        info("Nie rób: " + "; ".join(l.lstrip("-* ").strip() for l in nie_rob.splitlines() if l.strip()))
    info("")
    info("DALEJ: opis kadrów i dialog do dymków dosłownie.")
    for u in uwagi:
        info(f"UWAGA: {u}")


# --- strona HTML ---------------------------------------------------------------

def _esc(t):
    return html.escape(str(t or ""))


def _szablon(nazwa, **pola):
    tekst = (SZABLON_STRONY / nazwa).read_text(encoding="utf-8")
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(pola.get(m.group(1), "")), tekst)


def zbuduj_strone(kat):
    dane = wczytaj_komiks(kat)
    cel = kat / "strona"
    if cel.exists():
        shutil.rmtree(cel)
    (cel / "odcinki").mkdir(parents=True)
    (cel / "obrazy").mkdir()
    css = _szablon("styl.css", tlo=dane["kolor_tla"], tekst=dane["kolor_tekstu"],
                   akcent=dane["kolor_akcentu"], font=dane["font"])
    (cel / "styl.css").write_text(css, encoding="utf-8")
    shutil.copy2(SZABLON_STRONY / "nawigacja.js", cel / "nawigacja.js")

    gotowe = []
    for odc in odcinki(kat):
        od = czytaj_yaml(odc / "odcinek.yaml")
        if od.get("final") and (odc / "final").is_dir() and obrazy_w(odc / "final"):
            gotowe.append((odc, od))
    tytul = _esc(dane["tytul"])
    stopka = f'Wygenerowano {_esc(dzis())} · <a href="{{root}}zmiany.html">dziennik zmian biblii</a>'

    karty = []
    for i, (odc, od) in enumerate(gotowe):
        nr = f"{int(od.get('numer') or i + 1):03d}"
        plansze = []
        for j, obraz in enumerate(obrazy_w(odc / "final"), 1):
            nazwa = f"{nr}-{j}{obraz.suffix.lower()}"
            shutil.copy2(obraz, cel / "obrazy" / nazwa)
            plansze.append(f'<img src="../obrazy/{nazwa}" alt="{_esc(od.get("tytul"))}, plansza {j}" '
                           f'loading="{"eager" if j == 1 else "lazy"}">')
        poprz = f"{int(gotowe[i - 1][1].get('numer') or i):03d}.html" if i > 0 else None
        nast = f"{int(gotowe[i + 1][1].get('numer') or i + 2):03d}.html" if i + 1 < len(gotowe) else None
        nawigacja = "".join([
            f'<a rel="prev" href="{poprz}">← poprzedni</a>' if poprz else '<span class="pusto">← poprzedni</span>',
            '<a rel="index" href="../index.html">spis</a>',
            f'<a rel="next" href="{nast}">następny →</a>' if nast else '<span class="pusto">następny →</span>',
        ])
        (cel / "odcinki" / f"{nr}.html").write_text(_szablon(
            "odcinek.html", tytul_komiksu=tytul, tytul=_esc(od.get("tytul")), numer=nr,
            opis=_esc(od.get("opis")), data=_esc(od.get("data_publikacji")),
            biblia=_esc(od.get("wersja_biblii")), plansze="\n".join(plansze), nawigacja=nawigacja,
            stopka=stopka.replace("{root}", "../")), encoding="utf-8")
        miniatura = f"obrazy/{nr}-1{obrazy_w(odc / 'final')[0].suffix.lower()}"
        karty.append(
            f'<li><a href="odcinki/{nr}.html"><img src="{miniatura}" alt="" loading="lazy">'
            f'<span class="nr">#{nr}</span><span class="tyt">{_esc(od.get("tytul"))}</span>'
            f'<span class="data">{_esc(od.get("data_publikacji"))}</span></a></li>')

    spis = "\n".join(karty) if karty else '<li class="brak">Nie ma jeszcze gotowych odcinków.</li>'
    (cel / "index.html").write_text(_szablon(
        "index.html", tytul_komiksu=tytul, autor=_esc(dane.get("autor")), spis=spis,
        liczba=len(gotowe), stopka=stopka.replace("{root}", "")), encoding="utf-8")

    wpisy = []
    for p in reversed(_wnioski(kat)):
        meta, cialo = _naglowek_wniosku(p)
        opis = "".join(f"<p>{_esc(ak)}</p>" for ak in re.split(r"\n\s*\n", re.sub(r"^#.*$", "", cialo, flags=re.M).strip()) if ak.strip())
        data = str(meta.get("zatwierdzono") or meta.get("odrzucono") or meta.get("utworzono") or "")[:10]
        wersja = f' · biblia v{_esc(meta["wersja_biblii"])}' if meta.get("wersja_biblii") else ""
        wpisy.append(f'<li class="{_esc(meta.get("status"))}"><h2>{_esc(meta.get("tytul"))}</h2>'
                     f'<p class="meta">{_esc(meta.get("status"))} · {_esc(data)}{wersja}</p>{opis}</li>')
    (cel / "zmiany.html").write_text(_szablon(
        "zmiany.html", tytul_komiksu=tytul,
        wpisy="\n".join(wpisy) or '<li class="brak">Brak wpisów.</li>',
        stopka=stopka.replace("{root}", "")), encoding="utf-8")
    return cel, len(gotowe)


def cmd_strona(a):
    kat = znajdz_komiks(a.komiks)
    cel, ile = zbuduj_strone(kat)
    info(f"Strona zbudowana od zera ({liczba(ile, 'odcinek', 'odcinki', 'odcinków')}): {cel / 'index.html'}")
    info("Otwiera się dwuklikiem, bez internetu i serwera.")


# --- aktualizacje --------------------------------------------------------------

def wersja_zainstalowana():
    return json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]


def _krotka(w):
    return tuple(int(x) for x in re.findall(r"\d+", w)[:3])


def nowsze_wpisy(changelog, od_wersji):
    """Sekcje CHANGELOG („## x.y.z …”) nowsze niż zainstalowana wersja."""
    wynik, biezaca = [], None
    for linia in changelog.splitlines():
        m = re.match(r"^##\s+\[?v?(\d+\.\d+\.\d+)", linia)
        if m:
            biezaca = m.group(1) if _krotka(m.group(1)) > _krotka(od_wersji) else None
        if biezaca:
            wynik.append(linia)
    return "\n".join(wynik).strip()


def _pobierz(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "komiks-plugin"}),
                                timeout=10) as r:
        return r.read().decode("utf-8")


def cmd_aktualizacje(a):
    zainstalowana = wersja_zainstalowana()
    pamiec = Path(a.pamiec).expanduser() if a.pamiec else Path.home() / ".komiks-plugin" / "aktualizacje.json"
    if not a.wymus and pamiec.is_file():
        try:
            stan = json.loads(pamiec.read_text(encoding="utf-8"))
            if stan.get("data") == dzis() and stan.get("zainstalowana") == zainstalowana:
                info(f"Sprawdzono już dziś (wersja {zainstalowana}). {stan.get('wynik', '')}")
                return 0
        except ValueError:
            pass
    zrodlo = a.zrodlo or SUROWY_URL
    try:
        najnowsza = json.loads(_pobierz(zrodlo + "plugin.json"))["version"]
        changelog = _pobierz(zrodlo + "CHANGELOG.md")
    except Exception as e:  # sieć bywa zablokowana przez sandbox — to nie jest błąd użytkownika
        info(f"NIE SPRAWDZONO: brak połączenia ({type(e).__name__}). Zainstalowana wersja: {zainstalowana}.")
        return 2
    if _krotka(najnowsza) > _krotka(zainstalowana):
        wynik = f"NOWA WERSJA {najnowsza} (zainstalowana {zainstalowana})."
        info(wynik)
        info("Co nowego:\n" + (nowsze_wpisy(changelog, zainstalowana) or "(brak opisu)"))
        info(f"Aktualizacja: codex plugin marketplace upgrade {MARKETPLACE}, potem nowa rozmowa.")
    else:
        wynik = f"AKTUALNA: {zainstalowana}."
        info(wynik)
    pamiec.parent.mkdir(parents=True, exist_ok=True)
    pamiec.write_text(json.dumps({"data": dzis(), "zainstalowana": zainstalowana, "wynik": wynik},
                                 ensure_ascii=False), encoding="utf-8")
    return 0


def cmd_wersja(a):
    info(wersja_zainstalowana())


# --- wejście -------------------------------------------------------------------

def parser():
    p = argparse.ArgumentParser(prog="komiks.py", description="Pracownia komiksu: biblia, odcinki, strona.")
    sub = p.add_subparsers(dest="polecenie", required=True)

    def dodaj(nazwa, funkcja, pomoc, komiks=True):
        s = sub.add_parser(nazwa, help=pomoc, description=pomoc)
        s.set_defaults(funkcja=funkcja)
        if komiks:
            s.add_argument("--komiks", help="folder komiksu albo jego nazwa w bibliotece "
                                            "(domyślnie bieżący, nadrzędny lub jedyny w bibliotece)")
        return s

    s = dodaj("biblioteka", cmd_biblioteka,
              "pokaż albo ustaw stały folder ze wszystkimi komiksami (bibliotekę)", komiks=False)
    s.add_argument("--ustaw", metavar="FOLDER", help="od teraz komiksy w tym folderze")
    s.add_argument("--wylacz", action="store_true", help="wróć do pracy w bieżącym folderze")

    nadpisz = "jednorazowo ten folder zamiast biblioteki (domyślnie biblioteka albo bieżący)"
    s = dodaj("przygotuj", cmd_przygotuj, "zapisz AGENTS.md w folderze z komiksami", komiks=False)
    s.add_argument("--folder", "--biblioteka", dest="folder", help=nadpisz)
    s.add_argument("--nadpisz", action="store_true")

    s = dodaj("stan", cmd_stan, "pokaż komiksy w bibliotece i ich etap", komiks=False)
    s.add_argument("--folder", "--biblioteka", dest="folder", help=nadpisz)

    s = dodaj("nowy", cmd_nowy, "załóż nowy komiks (faza projektu)", komiks=False)
    s.add_argument("--tytul", required=True)
    s.add_argument("--nazwa", help="nazwa folderu (domyślnie z tytułu)")
    s.add_argument("--folder", "--biblioteka", dest="folder", help=nadpisz)
    s.add_argument("--format")
    s.add_argument("--autor")
    s.add_argument("--jezyk", help="język dialogów, np. pl")
    s.add_argument("--kanal", help="gdzie publikujesz, np. instagram")
    s.add_argument("--rytm", help="jak często odcinek, np. „1 w tygodniu”")
    s.add_argument("--plansze-na-post", type=int, help=">1 = karuzela")
    s.add_argument("--widoki-dodatkowe", help="„gora,dol” = postaci także z góry i z dołu")

    s = dodaj("postac", cmd_postac, "dodaj postać do biblii (faza projektu)")
    s.add_argument("--imie", required=True)
    s.add_argument("--nazwa")

    s = dodaj("miejsce", cmd_miejsce, "dodaj stałe miejsce do biblii (faza projektu)")
    s.add_argument("--nazwa-miejsca", required=True)
    s.add_argument("--nazwa")

    s = dodaj("start-produkcji", cmd_start_produkcji, "zamroź biblię jako v1 i zacznij odcinki")
    s.add_argument("--zgoda", required=True, help="dokładne słowa zgody użytkownika (TAK…)")

    s = dodaj("zmiana-nowa", cmd_zmiana_nowa, "otwórz wniosek o zmianę biblii")
    s.add_argument("--nazwa", required=True, help="krótka nazwa, np. okulary-adama")
    s.add_argument("--tytul", required=True)
    s.add_argument("--opis", required=True, help="co się zmienia i dlaczego")

    s = dodaj("zmiana-pokaz", cmd_zmiana_pokaz, "pokaż wniosek z różnicami i wpływem")
    s.add_argument("numer", type=int)

    s = dodaj("zmiana-zatwierdz", cmd_zmiana_zatwierdz, "zatwierdź wniosek po wyraźnym TAK")
    s.add_argument("numer", type=int)
    s.add_argument("--zgoda", required=True, help="dokładne słowa zgody użytkownika (TAK…)")

    s = dodaj("zmiana-odrzuc", cmd_zmiana_odrzuc, "odrzuć wniosek (zostaje w dzienniku)")
    s.add_argument("numer", type=int)
    s.add_argument("--powod")

    s = dodaj("odcinek-nowy", cmd_odcinek_nowy, "załóż odcinek ze szkicem scenariusza")
    s.add_argument("--tytul", required=True)
    s.add_argument("--opis")

    s = dodaj("odcinek-wersja", cmd_odcinek_wersja, "zapisz nową wersję plansz odcinka (v1, v2…)")
    s.add_argument("odcinek", help="numer (np. 3) albo nazwa folderu")
    s.add_argument("--plik", action="append", help="obraz planszy; powtórz dla kolejnych plansz")
    s.add_argument("--najnowsze", type=int, help="weź N najnowszych obrazów z katalogu generacji")
    s.add_argument("--z-katalogu", default="~/.codex/generated_images")
    s.add_argument("--prompt", help="prompt użyty do generacji")
    s.add_argument("--prompt-plik")
    s.add_argument("--referencja", action="append", help="obraz referencyjny podany na wejściu")

    s = dodaj("odcinek-final", cmd_odcinek_final, "wybierz wersję jako final")
    s.add_argument("odcinek")
    s.add_argument("wersja", help="np. v2")

    s = dodaj("gotowe", cmd_gotowe, "pokaż, gdzie są zatwierdzone pliki do publikacji")
    s.add_argument("odcinek", nargs="?", help="numer odcinka (domyślnie wszystkie zatwierdzone)")

    s = dodaj("instagram", cmd_instagram,
              "zrób od nowa gotowe/ z finału w dokładnym formacie posta (docięcie + skala)")
    s.add_argument("odcinek")

    s = dodaj("obraz", cmd_obraz, "skopiuj ostatnio wygenerowany obraz pod wskazaną ścieżkę", komiks=False)
    s.add_argument("--do", required=True, help="ścieżka docelowa, np. biblia/postaci/ola/arkusz.png")
    s.add_argument("--plik", help="konkretny plik zamiast najnowszego")
    s.add_argument("--z-katalogu", default="~/.codex/generated_images")
    s.add_argument("--nadpisz", action="store_true")

    s = dodaj("prompt-baza", cmd_prompt_baza,
              "stały początek promptu i lista obrazów na wejściu (styl, postaci, miejsce)")
    s.add_argument("--postac", action="append", help="postać w kadrze; powtórz dla kolejnych")
    s.add_argument("--widok", action="append", help="dołóż widok z arkusza obrotu, np. tyl")
    s.add_argument("--miejsce", action="append", help="miejsce z biblii, np. kuchnia")

    dodaj("sprawdz", cmd_sprawdz, "sprawdź, czy biblia nie zmieniła się bez zgody")
    dodaj("strona", cmd_strona, "zbuduj od zera stronę HTML komiksu")

    s = dodaj("aktualizacje", cmd_aktualizacje, "sprawdź, czy jest nowsza wersja pluginu", komiks=False)
    s.add_argument("--wymus", action="store_true", help="sprawdź mimo sprawdzenia dziś")
    s.add_argument("--zrodlo", help=argparse.SUPPRESS)
    s.add_argument("--pamiec", help=argparse.SUPPRESS)

    dodaj("wersja", cmd_wersja, "pokaż zainstalowaną wersję pluginu", komiks=False)
    return p


def main(argv=None):
    for strumien in (sys.stdout, sys.stderr):
        if hasattr(strumien, "reconfigure"):
            strumien.reconfigure(encoding="utf-8")
    a = parser().parse_args(argv)
    try:
        return a.funkcja(a) or 0
    except Blad as e:
        print(f"BŁĄD: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
