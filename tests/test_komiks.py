"""Testy skryptu komiks.py: strona HTML na przykładowym komiksie, biblia, odcinki, aktualizacje."""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "plugins" / "komiks" / "scripts"))
sys.path.insert(0, str(REPO / "tests"))

import komiks  # noqa: E402
from png import png, rozmiar_png  # noqa: E402

FIXTURE = REPO / "tests" / "fixture" / "przyklad"


def uruchom(*argumenty):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        kod = komiks.main([str(a) for a in argumenty])
    return kod, out.getvalue() + err.getvalue()


class ZFolderem(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        # ustawienia biblioteki tylko w folderze testu, nigdy w katalogu domowym
        self._ustawienia = os.environ.get("KOMIKS_USTAWIENIA")
        os.environ["KOMIKS_USTAWIENIA"] = str(self.tmp / "ustawienia" / "ustawienia.json")

    def tearDown(self):
        if self._ustawienia is None:
            os.environ.pop("KOMIKS_USTAWIENIA", None)
        else:
            os.environ["KOMIKS_USTAWIENIA"] = self._ustawienia
        self._tmp.cleanup()

    def kopia_fixture(self):
        cel = self.tmp / "przyklad"
        shutil.copytree(FIXTURE, cel)
        return cel


class TestStrona(ZFolderem):
    def test_strona_na_fixture(self):
        kat = self.kopia_fixture()
        kod, wyjscie = uruchom("strona", "--komiks", kat)
        self.assertEqual(kod, 0, wyjscie)
        strona = kat / "strona"
        index = (strona / "index.html").read_text(encoding="utf-8")
        self.assertIn("Przygody Marchewki", index)
        self.assertIn('href="odcinki/001.html"', index)
        self.assertIn('href="odcinki/002.html"', index)
        self.assertIn("Śniadanie bez cukru", index)

        o1 = (strona / "odcinki" / "001.html").read_text(encoding="utf-8")
        o2 = (strona / "odcinki" / "002.html").read_text(encoding="utf-8")
        self.assertIn('rel="next" href="002.html"', o1)
        self.assertNotIn('rel="prev"', o1)
        self.assertIn('rel="prev" href="001.html"', o2)
        self.assertNotIn('rel="next"', o2)
        self.assertIn('rel="index" href="../index.html"', o2)
        self.assertIn("biblia v1", o1)

        # Wszystkie lokalne odnośniki i obrazy prowadzą do istniejących plików (działa z dysku).
        for plik in strona.rglob("*.html"):
            tresc = plik.read_text(encoding="utf-8")
            for cel in re.findall(r'(?:href|src)="([^"#]+)"', tresc):
                self.assertTrue((plik.parent / cel).resolve().is_file(), f"{plik.name} -> {cel}")
            self.assertIn('<meta charset="utf-8">', tresc)
            self.assertNotIn("{{", tresc)
        self.assertEqual(len(list((strona / "obrazy").iterdir())), 4)

        zmiany = (strona / "zmiany.html").read_text(encoding="utf-8")
        self.assertIn("Marchewka nosi okulary", zmiany)
        self.assertIn("biblia v2", zmiany)

    def test_strona_buduje_od_zera(self):
        kat = self.kopia_fixture()
        uruchom("strona", "--komiks", kat)
        (kat / "strona" / "smiec.html").write_text("x", encoding="utf-8")
        uruchom("strona", "--komiks", kat)
        self.assertFalse((kat / "strona" / "smiec.html").exists())

    def test_tytul_jest_escapowany(self):
        kat = self.kopia_fixture()
        dane = komiks.czytaj_yaml(kat / "komiks.yaml")
        dane["tytul"] = "<b>Zły & dobry</b>"
        komiks.zapisz_yaml(kat / "komiks.yaml", dane)
        uruchom("strona", "--komiks", kat)
        index = (kat / "strona" / "index.html").read_text(encoding="utf-8")
        self.assertIn("&lt;b&gt;Zły &amp; dobry&lt;/b&gt;", index)


class TestBiblia(ZFolderem):
    def test_fixture_jest_czysta(self):
        kod, wyjscie = uruchom("sprawdz", "--komiks", self.kopia_fixture())
        self.assertEqual(kod, 0, wyjscie)

    def test_sprawdz_wykrywa_zmiane_bez_zgody(self):
        kat = self.kopia_fixture()
        with open(kat / "biblia" / "styl.md", "a", encoding="utf-8") as f:
            f.write("\nPrzy okazji: neonowe kolory.\n")
        (kat / "biblia" / "postaci" / "marchewka" / "arkusz.png").unlink()
        kod, wyjscie = uruchom("sprawdz", "--komiks", kat)
        self.assertEqual(kod, 1)
        self.assertIn("zmieniony bez zatwierdzenia: biblia/styl.md", wyjscie)
        self.assertIn("usunięty bez zatwierdzenia: biblia/postaci/marchewka/arkusz.png", wyjscie)

    def test_zmiana_wymaga_tak(self):
        kat = self.kopia_fixture()
        kod, _ = uruchom("zmiana-nowa", "--komiks", kat, "--nazwa", "kolory",
                         "--tytul", "Jaśniejsze kolory", "--opis", "Paleta pastelowa.")
        self.assertEqual(kod, 0)
        robocza = kat / "zmiany" / "0003-kolory" / "biblia"
        (robocza / "styl.md").write_text("# Styl\n\nPastele.\n", encoding="utf-8")

        kod, wyjscie = uruchom("zmiana-pokaz", "3", "--komiks", kat)
        self.assertIn("zmieniony: styl.md", wyjscie)
        self.assertIn("+Pastele.", wyjscie)
        self.assertIn("biblia v2 → v3", wyjscie)

        for zla in ("może", "ok", "zobaczymy", "nie tak"):
            kod, wyjscie = uruchom("zmiana-zatwierdz", "3", "--komiks", kat, "--zgoda", zla)
            self.assertEqual(kod, 1, zla)
        self.assertEqual(komiks.wersja_biblii(kat), 2)

        kod, wyjscie = uruchom("zmiana-zatwierdz", "3", "--komiks", kat, "--zgoda", "TAK, zatwierdzam")
        self.assertEqual(kod, 0, wyjscie)
        self.assertEqual(komiks.wersja_biblii(kat), 3)
        self.assertIn("Pastele.", (kat / "biblia" / "styl.md").read_text(encoding="utf-8"))
        self.assertIn("Pastele.", (kat / "historia-biblii" / "v3" / "styl.md").read_text(encoding="utf-8"))
        self.assertNotIn("Pastele.", (kat / "historia-biblii" / "v2" / "styl.md").read_text(encoding="utf-8"))
        meta, _ = komiks._naglowek_wniosku(kat / "zmiany" / "0003-kolory.md")
        self.assertEqual(meta["status"], "zatwierdzona")
        self.assertEqual(meta["zgoda"], "TAK, zatwierdzam")
        self.assertFalse(robocza.exists())
        self.assertEqual(uruchom("sprawdz", "--komiks", kat)[0], 0)

    def test_odrzucenie_zostaje_w_dzienniku(self):
        kat = self.kopia_fixture()
        uruchom("zmiana-nowa", "--komiks", kat, "--nazwa", "kapelusz", "--tytul", "Kapelusz", "--opis", "x")
        kod, _ = uruchom("zmiana-odrzuc", "3", "--komiks", kat, "--powod", "nie, bez kapelusza")
        self.assertEqual(kod, 0)
        meta, _ = komiks._naglowek_wniosku(kat / "zmiany" / "0003-kapelusz.md")
        self.assertEqual(meta["status"], "odrzucona")
        self.assertEqual(komiks.wersja_biblii(kat), 2)

    def test_jeden_otwarty_wniosek_naraz(self):
        kat = self.kopia_fixture()
        uruchom("zmiana-nowa", "--komiks", kat, "--nazwa", "a", "--tytul", "A", "--opis", "a")
        kod, wyjscie = uruchom("zmiana-nowa", "--komiks", kat, "--nazwa", "b", "--tytul", "B", "--opis", "b")
        self.assertEqual(kod, 1)
        self.assertIn("otwarty wniosek", wyjscie)


class TestCalyPrzebieg(ZFolderem):
    def test_od_projektu_do_strony(self):
        kod, _ = uruchom("przygotuj", "--folder", self.tmp)
        self.assertTrue((self.tmp / "AGENTS.md").is_file())
        kod, wyjscie = uruchom("nowy", "--tytul", "Żółta łódź", "--folder", self.tmp)
        self.assertEqual(kod, 0, wyjscie)
        kat = self.tmp / "zolta-lodz"
        self.assertEqual(komiks.wczytaj_komiks(kat)["tytul"], "Żółta łódź")
        self.assertEqual(uruchom("postac", "--komiks", kat, "--imie", "Ola")[0], 0)

        # bez pełnego arkusza obrotu postaci nie ma produkcji
        kod, wyjscie = uruchom("start-produkcji", "--komiks", kat, "--zgoda", "TAK")
        self.assertEqual(kod, 1)
        self.assertIn("lewy profil", wyjscie)
        for w in komiks.WIDOKI:
            png(kat / "biblia" / "postaci" / "ola" / "widoki" / f"{w}.png", 4, 4, (9, 9, 9))

        # bez zgody nie ma produkcji, a odcinka nie da się założyć w projekcie
        self.assertEqual(uruchom("start-produkcji", "--komiks", kat, "--zgoda", "chyba")[0], 1)
        self.assertEqual(uruchom("odcinek-nowy", "--komiks", kat, "--tytul", "X")[0], 1)
        self.assertEqual(uruchom("start-produkcji", "--komiks", kat, "--zgoda", "Tak")[0], 0)
        self.assertEqual(komiks.wersja_biblii(kat), 1)
        # w produkcji postaci nie dodaje się wprost
        self.assertEqual(uruchom("postac", "--komiks", kat, "--imie", "Ala")[0], 1)

        self.assertEqual(uruchom("odcinek-nowy", "--komiks", kat, "--tytul", "Pierwszy rejs")[0], 0)
        gen = self.tmp / "generacje" / "sesja"
        gen.mkdir(parents=True)
        png(gen / "a.png", 20, 25, (200, 100, 50))
        kod, wyjscie = uruchom("odcinek-wersja", "1", "--komiks", kat, "--najnowsze", "1",
                               "--z-katalogu", self.tmp / "generacje", "--prompt", "kadr")
        self.assertEqual(kod, 0, wyjscie)
        png(gen / "b.png", 20, 25, (50, 100, 200))
        uruchom("odcinek-wersja", "1", "--komiks", kat, "--plik", gen / "b.png")
        odc = kat / "odcinki" / "001-pierwszy-rejs"
        self.assertTrue((odc / "wersje" / "v1" / "plansza-1.png").is_file())
        self.assertTrue((odc / "wersje" / "v2" / "plansza-1.png").is_file())
        self.assertEqual(uruchom("odcinek-final", "1", "v2", "--komiks", kat)[0], 0)
        self.assertEqual((odc / "final" / "plansza-1.png").read_bytes(), (gen / "b.png").read_bytes())
        # plik na Instagram ma dokładnie format z komiks.yaml
        self.assertEqual(rozmiar_png(kat / "gotowe" / odc.name / "plansza-1.png"), (1080, 1350))
        self.assertEqual(komiks.czytaj_yaml(odc / "odcinek.yaml")["final"], "wersje/v2")

        self.assertEqual(uruchom("obraz", "--do", kat / "projekt" / "probna", "--z-katalogu",
                                 self.tmp / "generacje")[0], 0)
        self.assertTrue((kat / "projekt" / "probna.png").is_file())

        self.assertEqual(uruchom("strona", "--komiks", kat)[0], 0)
        self.assertIn("Pierwszy rejs", (kat / "strona" / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(uruchom("sprawdz", "--komiks", kat)[0], 0)
        kod, wyjscie = uruchom("stan", "--folder", self.tmp)
        self.assertIn("Żółta łódź", wyjscie)
        self.assertIn("gotowe 1", wyjscie)


class TestFormatPosta(ZFolderem):
    def test_pion_2_3_dociety_do_4_5(self):
        # generator daje 2:3 z ciemnym paskiem u góry i dołu; po docięciu do 4:5 pasków brak
        png(self.tmp / "a.png", 64, 96, (200, 100, 50))
        r = komiks.do_formatu(self.tmp / "a.png", self.tmp / "b.png", 40, 50)
        self.assertEqual(r["uciete"], (0, 16))
        w, h, wiersze = komiks._czytaj_png(self.tmp / "b.png")
        self.assertEqual((w, h), (40, 50))
        self.assertEqual(tuple(wiersze[0][:3]), (200, 100, 50))
        self.assertEqual(tuple(wiersze[-1][-3:]), (200, 100, 50))

    def test_poziom_dociety_do_kwadratu(self):
        png(self.tmp / "a.png", 96, 64, (10, 20, 30))
        r = komiks.do_formatu(self.tmp / "a.png", self.tmp / "b.png", 32, 32)
        self.assertEqual((r["uciete"], komiks._czytaj_png(self.tmp / "b.png")[:2]), ((32, 0), (32, 32)))

    def test_filtry_png_i_alfa(self):
        # PNG z filtrami Sub/Up/Avg/Paeth i kanałem alfa — jak z generatora
        w, h = 7, 5
        piks = [[(x * 30 % 256, y * 50 % 256, (x * y * 17) % 256, 255 if x else 0) for x in range(w)]
                for y in range(h)]
        surowe, poprz = b"", [0] * (w * 4)
        for y, rzad in enumerate(piks):
            linia = [v for p in rzad for v in p]
            f = y % 5
            out = []
            for i, v in enumerate(linia):
                a = linia[i - 4] if i >= 4 else 0
                b, c = poprz[i], (poprz[i - 4] if i >= 4 else 0)
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = [0, a, b, (a + b) // 2, a if pa <= pb and pa <= pc else b if pb <= pc else c][f]
                out.append((v - pr) & 255)
            surowe += bytes([f] + out)
            poprz = linia
        import struct, zlib
        def blok(typ, dane):
            return struct.pack(">I", len(dane)) + typ + dane + struct.pack(">I", zlib.crc32(typ + dane))
        (self.tmp / "f.png").write_bytes(b"\x89PNG\r\n\x1a\n" + blok(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                                         + blok(b"IDAT", zlib.compress(surowe)) + blok(b"IEND", b""))
        _, _, wiersze = komiks._czytaj_png(self.tmp / "f.png")
        for y in range(h):
            self.assertEqual(tuple(wiersze[y][3:6]), piks[y][1][:3])
            self.assertEqual(tuple(wiersze[y][:3]), (255, 255, 255))  # przezroczysty → białe tło

    def test_polecenie_instagram_i_format_1_1(self):
        kat = Path(shutil.copytree(FIXTURE, self.tmp / "k"))
        dane = komiks.czytaj_yaml(kat / "komiks.yaml")
        dane["format"] = "1080x1080"
        komiks.zapisz_yaml(kat / "komiks.yaml", dane)
        odc = next(p for p in komiks.odcinki(kat) if (p / "final").is_dir())
        kod, wyjscie = uruchom("instagram", odc.name, "--komiks", kat)
        self.assertEqual(kod, 0, wyjscie)
        for p in komiks.obrazy_w(kat / "gotowe" / odc.name):
            self.assertEqual(rozmiar_png(p), (1080, 1080))
        kod, wyjscie = uruchom("prompt-baza", "--komiks", kat)
        self.assertIn("kwadratowy, proporcje 1:1", wyjscie)


class TestBiblioteka(ZFolderem):
    def test_bez_biblioteki_jak_dawniej(self):
        kod, wyjscie = uruchom("biblioteka")
        self.assertEqual(kod, 0)
        self.assertIn("NIE USTAWIONO", wyjscie)
        stary = os.getcwd()
        os.chdir(self.tmp)
        try:
            self.assertEqual(uruchom("nowy", "--tytul", "Tu")[0], 0)
        finally:
            os.chdir(stary)
        self.assertTrue((self.tmp / "tu" / "komiks.yaml").is_file())

    def test_biblioteka_niezalezna_od_biezacego_folderu(self):
        bib = self.tmp / "Komiksy"
        kod, wyjscie = uruchom("biblioteka", "--ustaw", bib)
        self.assertEqual(kod, 0, wyjscie)
        self.assertTrue((bib / "AGENTS.md").is_file())
        roboczy = self.tmp / "codex-tmp-rozmowa"
        roboczy.mkdir()
        stary = os.getcwd()
        os.chdir(roboczy)  # „nowa rozmowa” w przypadkowym folderze
        try:
            self.assertEqual(uruchom("nowy", "--tytul", "Moja seria")[0], 0)
            self.assertEqual(uruchom("nowy", "--tytul", "Druga seria")[0], 0)
            kod, wyjscie = uruchom("stan")
            self.assertIn(f"Biblioteka komiksów: {bib.resolve()}", wyjscie)
            self.assertIn("Moja seria", wyjscie)
            self.assertIn("Druga seria", wyjscie)
            # komiks po samej nazwie, bez pełnej ścieżki
            self.assertEqual(uruchom("postac", "--komiks", "moja-seria", "--imie", "Ola")[0], 0)
            # bez --komiks przy kilku komiksach: prośba o nazwę
            kod, wyjscie = uruchom("sprawdz")
            self.assertEqual(kod, 1)
            self.assertIn("druga-seria, moja-seria", wyjscie)
            # jednorazowe nadpisanie lokalizacji
            inny = self.tmp / "inny"
            self.assertEqual(uruchom("nowy", "--tytul", "Gdzie indziej", "--biblioteka", inny)[0], 0)
        finally:
            os.chdir(stary)
        self.assertEqual(list(roboczy.iterdir()), [])
        self.assertTrue((bib / "moja-seria" / "biblia" / "postaci" / "ola" / "postac.md").is_file())
        self.assertTrue((self.tmp / "inny" / "gdzie-indziej" / "komiks.yaml").is_file())
        self.assertFalse((bib / "gdzie-indziej").exists())
        kod, wyjscie = uruchom("biblioteka")
        self.assertIn(f"BIBLIOTEKA: {bib.resolve()}", wyjscie)
        self.assertIn("Komiksów w bibliotece: 2", wyjscie)
        kod, wyjscie = uruchom("biblioteka", "--wylacz")
        self.assertIn("NIE USTAWIONO", uruchom("biblioteka")[1])
        self.assertTrue((bib / "moja-seria" / "komiks.yaml").is_file())

    def test_brak_folderu_biblioteki(self):
        bib = self.tmp / "dysk"
        uruchom("biblioteka", "--ustaw", bib)
        shutil.rmtree(bib)
        kod, wyjscie = uruchom("stan")
        self.assertEqual(kod, 1)
        self.assertIn("Nie ma folderu biblioteki", wyjscie)

    def test_ostrzega_przed_folderem_tymczasowym(self):
        kod, wyjscie = uruchom("biblioteka", "--ustaw", Path(tempfile.gettempdir()) / "komiksy-x")
        self.assertIn("folder tymczasowy", wyjscie)
        shutil.rmtree(Path(tempfile.gettempdir()) / "komiksy-x")


class TestGotowe(ZFolderem):
    def komiks_z_odcinkiem(self, plansze):
        kat = self.kopia_fixture()
        dane = komiks.czytaj_yaml(kat / "komiks.yaml")
        dane["tytul"] = "Moja seria"
        komiks.zapisz_yaml(kat / "komiks.yaml", dane)
        uruchom("odcinek-nowy", "--komiks", kat, "--tytul", "Plaża")
        odc = kat / "odcinki" / "003-plaza"
        pliki = []
        for i in range(plansze):
            pliki += ["--plik", self.tmp / f"p{i}.png"]
            png(self.tmp / f"p{i}.png", 40, 60, (10 * i, 100, 50))
        uruchom("odcinek-wersja", "3", "--komiks", kat, *pliki)
        return kat, odc, pliki

    def test_karuzela_komunikat_i_folder(self):
        kat, odc, _ = self.komiks_z_odcinkiem(3)
        kod, wyjscie = uruchom("odcinek-final", "3", "v1", "--komiks", kat)
        self.assertEqual(kod, 0, wyjscie)
        gotowe = kat / "gotowe" / "003-plaza"
        self.assertIn("ZATWIERDZONE — GOTOWE DO PUBLIKACJI", wyjscie)
        self.assertIn("Gotowe materiały do publikacji dla „Moja seria”, odcinek 003 („Plaża”):", wyjscie)
        self.assertIn(f"\n{gotowe.resolve()}\n", wyjscie)
        self.assertIn("3 slajdy • PNG 1080 × 1350 px • kolejność publikacji: 1 → 3", wyjscie)
        self.assertIn("  3. plansza-3.png", wyjscie)
        self.assertEqual(sorted(p.name for p in komiks.obrazy_w(gotowe)),
                         ["plansza-1.png", "plansza-2.png", "plansza-3.png"])
        self.assertIn("ZATWIERDZONE", (gotowe / "zatwierdzone.txt").read_text(encoding="utf-8"))
        self.assertFalse((odc / "instagram").exists())
        # to samo później, bez ponownego liczenia
        kod, wyjscie2 = uruchom("gotowe", "3", "--komiks", kat)
        self.assertIn("3 slajdy • PNG 1080 × 1350 px", wyjscie2)

    def test_pojedyncza_plansza(self):
        kat, odc, _ = self.komiks_z_odcinkiem(1)
        kod, wyjscie = uruchom("odcinek-final", "3", "v1", "--komiks", kat)
        self.assertIn("1 slajd • PNG 1080 × 1350 px • pojedynczy post", wyjscie)

    def test_zmiana_finalu_podmienia_gotowe_i_zachowuje_historie(self):
        kat, odc, _ = self.komiks_z_odcinkiem(3)
        uruchom("odcinek-final", "3", "v1", "--komiks", kat)
        png(self.tmp / "nowa.png", 40, 50, (1, 2, 3))
        uruchom("odcinek-wersja", "3", "--komiks", kat, "--plik", self.tmp / "nowa.png")
        kod, wyjscie = uruchom("odcinek-final", "3", "v2", "--komiks", kat)
        self.assertIn("1 slajd", wyjscie)
        gotowe = kat / "gotowe" / "003-plaza"
        self.assertEqual([p.name for p in komiks.obrazy_w(gotowe)], ["plansza-1.png"])
        self.assertEqual(len(komiks.obrazy_w(odc / "wersje" / "v1")), 3)
        historia = (odc / "historia-finalu.md").read_text(encoding="utf-8")
        self.assertIn("final = wersje/v1", historia)
        self.assertIn("final = wersje/v2 (wcześniej wersje/v1)", historia)
        self.assertEqual(uruchom("sprawdz", "--komiks", kat)[0], 0)

    def test_stary_odcinek_bez_gotowe(self):
        kat = self.kopia_fixture()
        kod, wyjscie = uruchom("gotowe", "--komiks", kat)
        self.assertEqual(kod, 0, wyjscie)
        self.assertIn("odcinek 001", wyjscie)
        self.assertIn("odcinek 002", wyjscie)
        self.assertTrue((kat / "gotowe" / "001-sok-to-nie-owoc" / "plansza-1.png").is_file())
        self.assertIn("gotowe do publikacji:", uruchom("stan", "--folder", kat)[1])


class TestProjektV02(ZFolderem):
    def nowy(self, *opcje):
        kod, wyjscie = uruchom("nowy", "--tytul", "Talerz", "--folder", self.tmp, *opcje)
        self.assertEqual(kod, 0, wyjscie)
        return self.tmp / "talerz"

    def test_odpowiedzi_na_pytania_startowe(self):
        kat = self.nowy("--format", "1080x1080", "--plansze-na-post", "3", "--kanal", "instagram",
                        "--rytm", "1 w tygodniu", "--widoki-dodatkowe", "gora,dol")
        dane = komiks.wczytaj_komiks(kat)
        self.assertEqual((dane["format"], dane["plansze_na_post"], dane["rytm"]),
                         ("1080x1080", 3, "1 w tygodniu"))
        uruchom("postac", "--komiks", kat, "--imie", "Adam")
        postac = (kat / "biblia" / "postaci" / "adam" / "postac.md").read_text(encoding="utf-8")
        for widok in ("widoki/przod.png", "widoki/tyl.png", "widoki/profil-lewy.png",
                      "widoki/profil-prawy.png", "widoki/trzy-czwarte.png", "widoki/gora.png", "widoki/dol.png"):
            self.assertIn(widok, postac)
        self.assertEqual(komiks.braki_widokow(kat)["adam"],
                         ["przod", "tyl", "profil-lewy", "profil-prawy", "trzy-czwarte", "gora", "dol"])
        kod, wyjscie = uruchom("stan", "--folder", self.tmp)
        self.assertIn("z dołu", wyjscie)

    def test_gora_dol_tylko_na_zyczenie(self):
        kat = self.nowy()
        uruchom("postac", "--komiks", kat, "--imie", "Ola")
        self.assertNotIn("gora", komiks.braki_widokow(kat)["ola"])
        self.assertNotIn("gora.png", (kat / "biblia" / "postaci" / "ola" / "postac.md").read_text(encoding="utf-8"))

    def test_prompt_baza(self):
        kat = self.nowy()
        uruchom("postac", "--komiks", kat, "--imie", "Ola")
        uruchom("miejsce", "--komiks", kat, "--nazwa-miejsca", "Kuchnia")
        b = kat / "biblia"
        styl = (b / "styl.md").read_text(encoding="utf-8")
        styl = styl.replace("(2–4 zdania, które idą DOSŁOWNIE na początek każdego promptu; nie zmieniaj ich słów)",
                            "Ligne claire, równa czarna kontur 2 px, płaskie kolory.")
        styl = styl.replace("(lista negatywów, np. fotorealizm; plastikowy połysk; gradienty jak z AI; inne style)",
                            "- fotorealizm\n- plastikowy połysk")
        (b / "styl.md").write_text(styl, encoding="utf-8")
        postac = b / "postaci" / "ola" / "postac.md"
        postac.write_text(postac.read_text(encoding="utf-8").replace(
            "(1–3 zdania do każdego promptu, zawsze tymi samymi słowami)", "Ola, 8 lat, rude warkocze."),
            encoding="utf-8")
        png(b / "styl" / "wzor-01.png", 4, 4, (1, 2, 3))
        png(b / "postaci" / "ola" / "arkusz.png", 4, 4, (1, 2, 3))
        png(b / "postaci" / "ola" / "widoki" / "tyl.png", 4, 4, (1, 2, 3))
        png(b / "miejsca" / "kuchnia.png", 4, 4, (1, 2, 3))
        kod, wyjscie = uruchom("prompt-baza", "--komiks", kat, "--postac", "Ola", "--widok", "tyl",
                               "--miejsce", "Kuchnia")
        self.assertEqual(kod, 0, wyjscie)
        kolejnosc = [wyjscie.index(x) for x in ("1. biblia/styl/wzor-01.png", "2. biblia/postaci/ola/arkusz.png",
                                                "3. biblia/postaci/ola/widoki/tyl.png", "4. biblia/miejsca/kuchnia.png")]
        self.assertEqual(kolejnosc, sorted(kolejnosc))
        self.assertIn("Ligne claire, równa czarna kontur 2 px", wyjscie)
        self.assertIn("ola: Ola, 8 lat, rude warkocze.", wyjscie)
        self.assertIn("Nie rób: fotorealizm; plastikowy połysk", wyjscie)
        self.assertIn("pionowy, proporcje 4:5", wyjscie)
        self.assertNotIn("UWAGA", wyjscie)
        self.assertEqual(uruchom("prompt-baza", "--komiks", kat, "--postac", "Ola", "--widok", "bok")[0], 1)

    def test_komiks_z_wersji_010_dziala(self):
        # Fixture to komiks założony w 0.1.0 (stary styl.md i postac.md, bez widoki/).
        kat = self.kopia_fixture()
        self.assertEqual(uruchom("sprawdz", "--komiks", kat)[0], 0)
        kod, wyjscie = uruchom("prompt-baza", "--komiks", kat, "--postac", "marchewka")
        self.assertEqual(kod, 0, wyjscie)
        self.assertIn("biblia/postaci/marchewka/arkusz.png", wyjscie)
        self.assertIn("Blok stylu", wyjscie)  # uwaga o brakującej sekcji, bez błędu
        self.assertEqual(uruchom("stan", "--folder", kat)[0], 0)


class TestAktualizacje(ZFolderem):
    def zrodlo(self, wersja):
        zr = self.tmp / "zrodlo"
        zr.mkdir(exist_ok=True)
        (zr / "plugin.json").write_text(json.dumps({"version": wersja}), encoding="utf-8")
        (zr / "CHANGELOG.md").write_text(
            "# Zmiany\n\n## 9.1.0 — 2030-01-02\n\n- Nowe dymki.\n\n## 9.0.0 — 2030-01-01\n\n- Duże zmiany.\n\n"
            f"## {komiks.wersja_zainstalowana()} — 2026-10-15\n\n- Pierwsza wersja.\n", encoding="utf-8")
        return zr.as_uri() + "/"

    def test_nowa_wersja(self):
        kod, wyjscie = uruchom("aktualizacje", "--zrodlo", self.zrodlo("9.1.0"), "--pamiec", self.tmp / "p.json")
        self.assertEqual(kod, 0)
        self.assertIn("NOWA WERSJA 9.1.0", wyjscie)
        self.assertIn("Nowe dymki.", wyjscie)
        self.assertIn("Duże zmiany.", wyjscie)
        self.assertNotIn("Pierwsza wersja.", wyjscie)
        self.assertIn("codex plugin marketplace upgrade guc-net", wyjscie)
        # drugi raz tego samego dnia — z pamięci, bez sieci
        kod, wyjscie = uruchom("aktualizacje", "--zrodlo", "file:///nie/ma", "--pamiec", self.tmp / "p.json")
        self.assertIn("Sprawdzono już dziś", wyjscie)

    def test_aktualna(self):
        kod, wyjscie = uruchom("aktualizacje", "--zrodlo", self.zrodlo(komiks.wersja_zainstalowana()),
                               "--pamiec", self.tmp / "p.json")
        self.assertIn("AKTUALNA", wyjscie)

    def test_brak_sieci(self):
        kod, wyjscie = uruchom("aktualizacje", "--zrodlo", "file:///nie/ma/", "--pamiec", self.tmp / "p.json", "--wymus")
        self.assertEqual(kod, 2)
        self.assertIn("NIE SPRAWDZONO", wyjscie)


class TestYaml(ZFolderem):
    def test_polskie_znaki_i_cudzyslowy(self):
        dane = {"tytul": 'Ala: "kot" # nie komentarz', "numer": 7, "final": None}
        komiks.zapisz_yaml(self.tmp / "a.yaml", dane)
        self.assertEqual(komiks.czytaj_yaml(self.tmp / "a.yaml"), dane)

    def test_reczna_edycja(self):
        (self.tmp / "b.yaml").write_text("# komentarz\ntytul: Gołe słowa  # uwaga\nformat: '1080x1080'\n",
                                         encoding="utf-8")
        self.assertEqual(komiks.czytaj_yaml(self.tmp / "b.yaml"), {"tytul": "Gołe słowa", "format": "1080x1080"})

    def test_odmiana(self):
        self.assertEqual([komiks.liczba(n, "plansza", "plansze", "plansz") for n in (1, 2, 5, 12, 22)],
                         ["1 plansza", "2 plansze", "5 plansz", "12 plansz", "22 plansze"])

    def test_slug(self):
        self.assertEqual(komiks.slug("Żółta łódź — część 2!"), "zolta-lodz-czesc-2")


if __name__ == "__main__":
    unittest.main()
