"""Repozytorium jest publiczne: w plikach pluginu graphic-designer nie ma zakazanych słów."""
from __future__ import annotations

import hashlib
import re
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

FORBIDDEN_SHA256 = {
    "2410bb3e2b179dd2c5f3d6b5b311f6caf60fd250af0bda80dac9c7ee052e5170",
    "a266cbe3a16b755e38e83488e0c0f5f4a379f07a2fbc52536d543f44bcc5a34e",
    "ea5c5136eef136aa9dc493319db6a1a9f73352da080d5cc752e586590d691441",
    "41a990c1d80e5f31053c88f36f339de603ea6007c03bcbc6f3c2fdffbe4dd6be",
    # sześć kolorów HEX (małe litery, bez #); wartości zapisane tylko jako skróty
    "a61b1949b612e7c9955584f2f3aa75746705675bc2931dbf8733bb3508ff447e",
    "486aa2763ceb00a6ec148416739d85de102ad276477390d20f6088db69cde0c8",
    "942129b8535f5857595f2c122c377a88e436b46df4210abeedd82c4331598d1a",
    "e6f442eb9c04f9ec333d8bd0cc7831af9dd69356bc16a11e92d425ccfed4d4d3",
    "7ebdd1f78536a9cafe76b72a962f75f2a38795de75fb6c4227b166407f2ef070",
    "8529607e9c544b9c2ed52695cb83775471f980280a1460496f0e81d17ac2b88b",
}


FONT_SUFFIXES = {".ttf", ".otf", ".woff", ".woff2"}


def files_to_check():
    paths = [p for p in (REPO / "plugins" / "graphic-designer").rglob("*") if p.is_file()]
    paths += sorted((REPO / "docs").glob("graphic-designer*.md"))
    paths += [p for p in (REPO / "tests").rglob("*") if p.is_file()]
    return [p for p in paths if "__pycache__" not in p.parts and p.suffix not in FONT_SUFFIXES]


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None  # plik binarny


def violations(paths, forbidden):
    found = []
    for path in paths:
        text = read_text(path)
        if text is None:
            continue
        for word in set(re.findall(r"\w+", text.lower())):
            if hashlib.sha256(word.encode("utf-8")).hexdigest() in forbidden:
                found.append(str(path))
                break
    return found


class TestPublicContent(unittest.TestCase):
    def test_no_forbidden_words(self):
        self.assertEqual(violations(files_to_check(), FORBIDDEN_SHA256), [])

    def test_forbidden_detector_works(self):
        word = "kiwiforbidden"
        extended = set(FORBIDDEN_SHA256) | {hashlib.sha256(word.encode("utf-8")).hexdigest()}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plik.txt"
            path.write_text(f"Ala ma {word.upper()}, a kot nie.", encoding="utf-8")
            self.assertEqual(violations([path], extended), [str(path)])
            self.assertEqual(violations([path], FORBIDDEN_SHA256), [])


if __name__ == "__main__":
    unittest.main()
