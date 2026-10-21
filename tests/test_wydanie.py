"""Skrypt wydania: notatki z CHANGELOG i tagi `<plugin>-v<wersja>`."""
import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("wydanie", REPO / ".github" / "scripts" / "wydanie.py")
wydanie = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wydanie)

CHANGELOG = """# Co nowego

Wstęp.

## 1.1.0 — 2026-10-21

- Nowość.
  Ciąg dalszy.

## 1.0.0 — 2026-10-01

- Pierwsza wersja.
"""


class TestWydanie(unittest.TestCase):
    def test_notatki_tylko_z_sekcji_wersji(self):
        self.assertEqual(wydanie.notatki(CHANGELOG, "1.1.0"), "- Nowość.\n  Ciąg dalszy.\n")
        self.assertEqual(wydanie.notatki(CHANGELOG, "1.0.0"), "- Pierwsza wersja.\n")

    def test_brak_sekcji_to_blad(self):
        with self.assertRaises(ValueError):
            wydanie.notatki(CHANGELOG, "2.0.0")

    def test_plan_dla_pluginow_z_marketplace(self):
        tagi = {tag: tytul for tag, tytul, _ in wydanie.plan()}
        self.assertIn("komiks", {t.rsplit("-v", 1)[0] for t in tagi})
        for tag, tytul in tagi.items():
            nazwa, wersja = tag.rsplit("-v", 1)
            self.assertEqual(tytul, f"{nazwa} {wersja}")


if __name__ == "__main__":
    unittest.main()
