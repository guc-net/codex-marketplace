# Plugin „komiks”

Pracownia komiksu w Codexie. Komiks to folder na Twoim dysku, w Twojej bibliotece:

```
Komiksy/                     ← biblioteka: wszystkie komiksy (patrz niżej)
  AGENTS.md
  moj-komiks/
    komiks.yaml              ← tytuł, format posta, kolory strony
    biblia/                  ← styl, postaci (z widoki/: przód, tył, profile, 3/4), miejsca, kadry, dymki
    projekt/style/           ← próbki stylów z początku projektu
    zmiany/                  ← dziennik zmian biblii (propozycja / zatwierdzona / odrzucona)
    historia-biblii/v1, v2…  ← zamrożone wersje biblii
    odcinki/001-…/           ← scenariusz, wersje/v1, v2… z promptami, final/, historia-finalu.md
    gotowe/001-…/            ← ZATWIERDZONE, gotowe do publikacji: plansza-1.png… w formacie posta
    strona/index.html        ← strona komiksu (budowana od zera, nie edytuj ręcznie)
```

## Biblioteka komiksów

Biblioteka to jeden stały folder ze wszystkimi komiksami. Ustawienie leży w
`~/.komiks-plugin/ustawienia.json`, więc działa w każdej nowej rozmowie — niezależnie
od folderu, który Codex otworzył. W rozmowie wystarczy napisać „Trzymaj moje komiksy
w …”; plugin sam pyta o bibliotekę, zanim założy pierwszy komiks w pustym folderze.

```
python3 scripts/komiks.py biblioteka                          # pokaż (NIE USTAWIONO / BIBLIOTEKA: …)
python3 scripts/komiks.py biblioteka --ustaw ~/Projects/guc-net/komiksy-codex
python3 scripts/komiks.py biblioteka --wylacz                 # wróć do bieżącego folderu
python3 scripts/komiks.py nowy --tytul "…" --biblioteka ~/Pulpit/proba   # jednorazowo gdzie indziej
python3 scripts/komiks.py stan                                # wszystkie serie z biblioteki
python3 scripts/komiks.py gotowe --komiks citra-na-samui      # komiks samą nazwą z biblioteki
```

Bez ustawionej biblioteki wszystko działa jak w 0.2: komiksy w bieżącym folderze
(`--folder`/`--biblioteka` dalej działa). Istniejących komiksów plugin nie przenosi.

## Gotowe materiały

Po wybraniu finału (`odcinek-final`) plugin buduje od nowa `gotowe/<odcinek>/` —
tylko aktualny final, docięty i przeskalowany do `format` — i drukuje:

```
ZATWIERDZONE — GOTOWE DO PUBLIKACJI
Gotowe materiały do publikacji dla „Citra na Samui”, odcinek 001 („Pierwszy dzień na wyspie”):
/Users/ja/Projects/guc-net/komiksy-codex/citra-na-samui/gotowe/001-pierwszy-dzien-na-wyspie
3 slajdy • PNG 1080 × 1350 px • kolejność publikacji: 1 → 3
  1. plansza-1.png
  2. plansza-2.png
  3. plansza-3.png
```

Ten sam tekst leży w folderze jako `zatwierdzone.txt`, a `gotowe [nr]` pokazuje go
ponownie. Zmiana finału podmienia folder w całości; wersje robocze zostają w
`odcinki/…/wersje/`, każdy wybór finału zapisuje `odcinki/…/historia-finalu.md`.
Odcinki zatwierdzone w 0.2 dostają `gotowe/` przy pierwszym `gotowe`; ich stare foldery
`instagram/` zostają nietknięte.

Skille: `komiks` (start rozmowy, aktualizacje, reguły spójności w `spojnosc.md`),
`komiks-projekt` (pytania startowe, 4–6 stylów, arkusze obrotu postaci, biblia krok po kroku),
`komiks-odcinek` (scenariusz → plansze → final → strona), `komiks-zmiana` (zmiana biblii
tylko po „TAK”).

Narzędzie: `scripts/komiks.py` — czysty Python 3.9+, bez doinstalowywania bibliotek.
`python3 scripts/komiks.py --help` pokazuje polecenia.

Ustawienia, które zależą od Twoich decyzji (format 4:5 czy 1:1, karuzela, tryb dymków,
kolory strony), siedzą w `komiks.yaml` — zmiana decyzji = zmiana jednego pliku.

Jak zacząć: [../../docs/jak-zaczac.md](../../docs/jak-zaczac.md). Spójność grafiki:
[../../docs/spojnosc.md](../../docs/spojnosc.md). Plany i limity obrazów: [../../docs/plany.md](../../docs/plany.md).
