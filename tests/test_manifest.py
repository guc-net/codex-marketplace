"""Walidacja marketplace i manifestów pluginów wg dokumentacji Codexa (październik 2026)."""
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def wczytaj(sciezka):
    return json.loads(sciezka.read_text(encoding="utf-8"))


def frontmatter(sciezka):
    m = re.match(r"---\n(.*?)\n---\n", sciezka.read_text(encoding="utf-8"), re.S)
    assert m, f"{sciezka}: brak front mattera"
    pary = (linia.split(":", 1) for linia in m.group(1).splitlines() if ":" in linia)
    return {k.strip(): v.strip() for k, v in pary}


class TestMarketplace(unittest.TestCase):
    def setUp(self):
        self.mp = wczytaj(REPO / ".agents" / "plugins" / "marketplace.json")

    def test_marketplace(self):
        self.assertTrue(KEBAB.match(self.mp["name"]))
        self.assertTrue(self.mp["interface"]["displayName"])
        self.assertTrue(self.mp["plugins"])
        nazwy = [p["name"] for p in self.mp["plugins"]]
        self.assertEqual(len(nazwy), len(set(nazwy)))

    def test_wpisy_i_pluginy(self):
        for wpis in self.mp["plugins"]:
            with self.subTest(plugin=wpis["name"]):
                for pole in ("policy", "category"):
                    self.assertIn(pole, wpis)
                self.assertIn(wpis["policy"]["installation"], ("AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"))
                self.assertIn("authentication", wpis["policy"])
                zrodlo = wpis["source"]
                self.assertEqual(zrodlo["source"], "local")
                self.assertTrue(zrodlo["path"].startswith("./"))
                katalog = (REPO / zrodlo["path"]).resolve()
                self.assertTrue(str(katalog).startswith(str(REPO)), "ścieżka poza repo")
                self.sprawdz_plugin(katalog, wpis["name"])

    def sprawdz_plugin(self, katalog, nazwa):
        m = wczytaj(katalog / "plugin.json")
        self.assertEqual(m["name"], nazwa)
        self.assertTrue(KEBAB.match(m["name"]))
        self.assertTrue(SEMVER.match(m["version"]), m["version"])
        self.assertTrue(m["description"])
        self.assertIn("agent-plugins.org", m["$schema"])
        openai = m["extensions"]["com.openai"]
        for pole in ("displayName", "shortDescription", "developerName", "category"):
            self.assertTrue(openai["interface"][pole], pole)
        sciezki = [openai.get("onboardingSkill"), openai["interface"].get("composerIcon"),
                   openai["interface"].get("logo")]
        for s in filter(None, sciezki):
            self.assertTrue(s.startswith("./"), s)
            self.assertTrue((katalog / s).is_file(), s)

        skille = sorted((katalog / "skills").glob("*/SKILL.md"))
        self.assertTrue(skille)
        for skill in skille:
            fm = frontmatter(skill)
            self.assertEqual(fm.get("name"), skill.parent.name, skill)
            self.assertGreater(len(fm.get("description", "")), 40, skill)
            # pliki pomocnicze, do których skill odsyła („pytania.md”, „../komiks/spojnosc.md”)
            for ref in re.findall(r"`((?:\.\./[\w-]+/)?[\w-]+\.md)`", skill.read_text(encoding="utf-8")):
                if ref not in ("SKILL.md", "AGENTS.md", "postac.md", "styl.md", "ton.md", "kadry.md",
                               "dymki.md", "scenariusz.md"):
                    self.assertTrue((skill.parent / ref).is_file(), f"{skill}: brak {ref}")

        # wersja w manifeście = najnowszy wpis w CHANGELOG pluginu
        changelog = (katalog / "CHANGELOG.md").read_text(encoding="utf-8")
        wpisy = re.findall(r"^##\s+\[?v?(\d+\.\d+\.\d+)", changelog, re.M)
        self.assertTrue(wpisy, "CHANGELOG bez wpisów")
        self.assertEqual(wpisy[0], m["version"], "plugin.json i CHANGELOG mają różne wersje")
        self.assertFalse((katalog / ".codex-plugin").exists(),
                         "manifest jest w plugin.json; .codex-plugin by go zastąpił")


if __name__ == "__main__":
    unittest.main()
