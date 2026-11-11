"""Testy biblii marki: odczyt, walidacja, kolory, założenie, dziennik zmian."""
from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "graphic-designer"
sys.path.insert(0, str(PLUGIN / "scripts"))

import designer  # noqa: E402
from gd import brand, color, flatyaml  # noqa: E402
from gd.common import GdError  # noqa: E402

KIWI = REPO / "tests" / "fixture" / "graphic-designer" / "kiwi"


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = designer.main([str(a) for a in args])
    return code, out.getvalue() + err.getvalue()


class Tmp(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.tmp = Path(self._t.name)

    def copy_kiwi(self) -> Path:
        dst = self.tmp / "kiwi"
        shutil.copytree(KIWI, dst)
        return dst / "brand"


class TestColor(unittest.TestCase):
    def test_contrast_known_values(self):
        self.assertAlmostEqual(color.contrast("#2A6F97", "#14213D"), 2.9, delta=0.01)
        self.assertAlmostEqual(color.contrast("#777777", "#7A7A7A"), 1.04, delta=0.01)
        self.assertEqual(color.contrast("#FFFFFF", "#000000"), 21)

    def test_parse_hex(self):
        self.assertEqual(color.parse_hex("#2bb673"), (43, 182, 115))
        with self.assertRaises(GdError):
            color.parse_hex("#12345")


class TestFlatYaml(unittest.TestCase):
    def test_parse_types_and_roundtrip(self):
        d = flatyaml.parse('a: "x y"\nb: 3\nc: true\nd: false\ne: goły # k\n# nic\n', "t")
        self.assertEqual(d, {"a": "x y", "b": 3, "c": True, "d": False, "e": "goły"})
        self.assertEqual(flatyaml.parse(flatyaml.dump(d), "t"), d)

    def test_quoted_values_with_trailing_comment(self):
        d = flatyaml.parse(
            'a: "#2BB673"   # wymagane\nb: \'x y\'  # k\nc: "z # w"\nd: \'it\'\'s\'\n', "t")
        self.assertEqual(d, {"a": "#2BB673", "b": "x y", "c": "z # w", "d": "it's"})
        with self.assertRaises(GdError):
            flatyaml.parse('a: "x" junk\n', "t")

    def test_error_has_line_number(self):
        with self.assertRaises(GdError) as cm:
            flatyaml.parse("a: 1\nbez dwukropka\n", "brand.md")
        self.assertIn("brand.md:2", str(cm.exception))


class TestBrand(Tmp):
    def test_load_fixture(self):
        b = brand.load(KIWI / "brand")
        self.assertEqual(b.name, "Kiwi Studio")
        self.assertEqual(b.version, 3)
        for role in ("primary", "background", "text"):
            self.assertIn(role, b.colors)
        self.assertTrue(b.fonts["heading"].file.is_file())
        self.assertEqual(b.logos["full"].on, "dark")
        self.assertEqual(b.forbidden[0][:2], ("accent-orange", "primary"))
        self.assertEqual(brand.validate(b), ([], []))
        self.assertIn("--color-primary: #2BB673;", brand.css_vars(b))

    def test_find_brand_walks_up(self):
        deep = self.tmp / "kiwi"
        shutil.copytree(KIWI, deep)
        work = deep / "graphics" / "2026-12-x"
        work.mkdir(parents=True)
        self.assertEqual(brand.find_brand(work), (deep / "brand").resolve())
        self.assertIsNone(brand.find_brand(self.tmp / "nic"))

    def test_validate_reports_all_problems(self):
        d = self.copy_kiwi()
        text = (d / "brand.md").read_text(encoding="utf-8")
        text = text.replace('color.text: "#F5F5F5"', 'color.text: "#12345"')
        text = text.replace('color.background: "#101010"\n', "")
        (d / "brand.md").write_text(text, encoding="utf-8")
        (d / "logo" / "full.png").unlink()
        b = brand.load(d)
        errors, _ = brand.validate(b)
        self.assertEqual(len(errors), 3, errors)
        code, out = run("brand", "--path", d)
        self.assertEqual(code, 1)
        self.assertIn("PROBLEM:", out)
        self.assertNotIn("Traceback", out)

    def test_pending_font_is_warning(self):
        d = self.copy_kiwi()
        with open(d / "brand.md", encoding="utf-8") as f:
            text = f.read()
        text = text.replace("---\nKiwi", 'font.display.family: "Ozdobny"\nfont.display.pending: true\n---\nKiwi')
        (d / "brand.md").write_text(text, encoding="utf-8")
        errors, warnings = brand.validate(brand.load(d))
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1, warnings)

    def test_forbidden_pair_unknown_role(self):
        d = self.copy_kiwi()
        text = (d / "brand.md").read_text(encoding="utf-8")
        text = text.replace("---\nKiwi", 'forbidden.2: "pink on primary"\n---\nKiwi')
        (d / "brand.md").write_text(text, encoding="utf-8")
        errors, _ = brand.validate(brand.load(d))
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("pink", errors[0])

    def test_brand_command(self):
        code, out = run("brand", "--path", KIWI / "brand")
        self.assertEqual(code, 0)
        self.assertIn("BRAND:", out)
        self.assertIn("Kiwi Studio, wersja 3", out)
        code, out = run("brand", "--path", self.tmp)
        self.assertEqual(code, 0)
        self.assertIn("NO BRAND", out)

    def test_brand_init_does_not_overwrite(self):
        code, out = run("brand-init", "--name", "Kiwi Studio", "--dir", self.tmp)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.tmp / "brand" / "brand.md").is_file())
        self.assertTrue((self.tmp / "brand" / "examples" / "approved").is_dir())
        self.assertIn("Kiwi Studio", (self.tmp / "brand" / "brand.md").read_text(encoding="utf-8"))
        code, out = run("brand-init", "--name", "Inna", "--dir", self.tmp)
        self.assertEqual(code, 1)
        self.assertIn("PROBLEM:", out)
        self.assertIn("Kiwi Studio", (self.tmp / "brand" / "brand.md").read_text(encoding="utf-8"))

    def test_brand_log_bumps_version(self):
        d = self.copy_kiwi()
        code, out = run("brand-log", "--path", d, "--change", "nowy zielony", "--approved-by", "Kiwi Owner")
        self.assertEqual(code, 0, out)
        self.assertEqual(brand.load(d).version, 4)
        log = (d / "CHANGES.md").read_text(encoding="utf-8")
        self.assertIn("nowy zielony", log)
        self.assertIn("Kiwi Owner", log)
        self.assertRegex(log, r"\d{4}-\d{2}-\d{2}")
        self.assertIn("Kiwi Studio to zmyślona", (d / "brand.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
