"""Testy sprawdzania aktualizacji i zgodności formats.md z formats.json."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "graphic-designer"
sys.path.insert(0, str(PLUGIN / "scripts"))

import designer  # noqa: E402
from gd import update  # noqa: E402


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = designer.main([str(a) for a in args])
    return code, out.getvalue()


class TestUpdate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def source(self, version):
        src = self.tmp / "source"
        src.mkdir(exist_ok=True)
        (src / "plugin.json").write_text(json.dumps({"version": version}), encoding="utf-8")
        (src / "CHANGELOG.md").write_text(
            "# Zmiany\n\n## 9.1.0 — 2030-01-02\n\n- Nowe układy.\n\n## 9.0.0 — 2030-01-01\n\n- Duże zmiany.\n\n"
            f"## {update.installed_version()} — 2026-11-11\n\n- Pierwsza wersja.\n", encoding="utf-8")
        return src.as_uri() + "/"

    def test_update_newer(self):
        code, out = run("update-check", "--source", self.source("9.1.0"), "--cache", self.tmp / "c.json")
        self.assertEqual(code, 0)
        self.assertIn("NOWA WERSJA 9.1.0", out)
        self.assertIn("Nowe układy.", out)
        self.assertIn("Duże zmiany.", out)
        self.assertNotIn("Pierwsza wersja.", out)
        self.assertIn("codex plugin marketplace upgrade guc-net", out)

    def test_update_current(self):
        code, out = run("update-check", "--source", self.source(update.installed_version()),
                        "--cache", self.tmp / "c.json")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("AKTUALNA"), out)

    def test_update_cached_today(self):
        cache = self.tmp / "c.json"
        run("update-check", "--source", self.source("9.1.0"), "--cache", cache)
        code, out = run("update-check", "--source", "file:///nie/ma/", "--cache", cache)
        self.assertEqual(code, 0)
        self.assertIn("NOWA WERSJA 9.1.0", out)
        self.assertIn("Sprawdzono już dziś", out)
        code, out = run("update-check", "--source", "file:///nie/ma/", "--cache", cache, "--force")
        self.assertEqual(code, 2)

    def test_update_offline(self):
        code, out = run("update-check", "--source", "file:///nie/ma/", "--cache", self.tmp / "c.json")
        self.assertEqual(code, 2)
        self.assertTrue(out.startswith("NIE SPRAWDZONO"), out)
        self.assertFalse((self.tmp / "c.json").exists())

    def test_default_cache_respects_gd_home(self):
        import os
        old = os.environ.get("GD_HOME")
        os.environ["GD_HOME"] = str(self.tmp / "home")
        try:
            self.assertEqual(update.default_cache(), self.tmp / "home" / "update.json")
        finally:
            if old is None:
                os.environ.pop("GD_HOME")
            else:
                os.environ["GD_HOME"] = old


class TestFormatsDoc(unittest.TestCase):
    def test_formats_doc_matches_json(self):
        doc = (PLUGIN / "skills" / "graphic-designer" / "references" / "formats.md").read_text(encoding="utf-8")
        formats = json.loads((PLUGIN / "templates" / "formats.json").read_text(encoding="utf-8"))
        self.assertTrue(formats)
        for f in formats:
            self.assertIn(f["id"], doc)
            self.assertIn(f"{f['width']}×{f['height']}", doc, f["id"])


if __name__ == "__main__":
    unittest.main()
