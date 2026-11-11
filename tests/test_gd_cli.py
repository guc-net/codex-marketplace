"""Testy wejścia skryptu designer.py."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "graphic-designer"
sys.path.insert(0, str(PLUGIN / "scripts"))

import designer  # noqa: E402
from gd.common import slug  # noqa: E402


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = designer.main([str(a) for a in args])
    return code, out.getvalue() + err.getvalue()


class TestCli(unittest.TestCase):
    def test_version_matches_manifest(self):
        code, out = run("version")
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), manifest["version"])

    def test_slug_transliterates(self):
        self.assertEqual(slug("Plakat ślub Łódź 14.03"), "plakat-slub-lodz-14-03")

    def test_error_has_no_traceback(self):
        code, out = run("status", "--job", "nie-ma")
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("PROBLEM:"), out)
        self.assertNotIn("Traceback", out)


if __name__ == "__main__":
    unittest.main()
