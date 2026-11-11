"""Testy sprawdzania znaków w fontach."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "plugins" / "graphic-designer" / "scripts"))

from gd import fonts  # noqa: E402
from gd.common import GdError  # noqa: E402

ANTON = REPO / "tests" / "fixture" / "graphic-designer" / "kiwi" / "brand" / "fonts" / "Anton-Regular.ttf"


class FontsTest(unittest.TestCase):
    def test_anton_has_polish(self):
        self.assertEqual(fonts.missing_chars(ANTON, "Zażółć gęślą jaźń"), [])

    def test_codepoints(self):
        cps = fonts.codepoints(ANTON)
        self.assertIn(ord("A"), cps)
        self.assertIn(ord("ł"), cps)
        self.assertNotIn(ord("★"), cps)

    def test_reports_missing(self):
        self.assertEqual(fonts.missing_chars(ANTON, "a★b"), ["★"])

    def test_missing_order_unique_no_whitespace(self):
        self.assertEqual(fonts.missing_chars(ANTON, "日 a ★ 日 \n ★ 日"), ["日", "★"])

    def test_woff_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for magic in (b"wOFF", b"wOF2"):
                p = Path(d) / "f.woff"
                p.write_bytes(magic + bytes(40))
                with self.assertRaises(GdError) as cm:
                    fonts.codepoints(p)
                self.assertIn("podaj TTF albo OTF", str(cm.exception))

    def test_not_a_font_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.ttf"
            p.write_bytes(b"nie font")
            with self.assertRaises(GdError):
                fonts.codepoints(p)
            with self.assertRaises(GdError):
                fonts.codepoints(Path(d) / "brak.ttf")


if __name__ == "__main__":
    unittest.main()
