"""Testy skryptu komiks.py: strona HTML na przykładowym komiksie, biblia, odcinki, aktualizacje."""
import contextlib
import io
import json
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
from png import png  # noqa: E402

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

    def tearDown(self):
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
