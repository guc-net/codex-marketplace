"""Testy sprawdzania aktualizacji i zgodności formats.md z formats.json."""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
        # GD_HOME i GD_UPDATE_SOURCE to jedyne przełączniki; drugi jest tylko do testów
        patcher = mock.patch.dict(os.environ, {"GD_HOME": str(self.tmp / "home")})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("GD_UPDATE_SOURCE", None)

    @property
    def cache(self):
        return self.tmp / "home" / "update.json"

    def source(self, version):
        src = self.tmp / "source"
        src.mkdir(exist_ok=True)
        (src / "plugin.json").write_text(json.dumps({"version": version}), encoding="utf-8")
        (src / "CHANGELOG.md").write_text(
            "# Zmiany\n\n## 9.1.0 — 2030-01-02\n\n- Nowe układy.\n\n## 9.0.0 — 2030-01-01\n\n- Duże zmiany.\n\n"
            f"## {update.installed_version()} — 2026-11-11\n\n- Pierwsza wersja.\n", encoding="utf-8")
        return src.as_uri() + "/"

    def point_at(self, source):
        os.environ["GD_UPDATE_SOURCE"] = source

    def test_update_newer(self):
        self.point_at(self.source("9.1.0"))
        code, out = run("update-check")
        self.assertEqual(code, 0)
        self.assertIn("NOWA WERSJA 9.1.0", out)
        self.assertIn("Nowe układy.", out)
        self.assertIn("Duże zmiany.", out)
        self.assertNotIn("Pierwsza wersja.", out)
        self.assertIn("codex plugin marketplace upgrade guc-net", out)

    def test_update_current(self):
        self.point_at(self.source(update.installed_version()))
        code, out = run("update-check")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("AKTUALNA"), out)

    def test_update_cached_today(self):
        self.point_at(self.source("9.1.0"))
        run("update-check")
        self.point_at("file:///nie/ma/")
        code, out = run("update-check")
        self.assertEqual(code, 0)
        self.assertIn("NOWA WERSJA 9.1.0", out)
        self.assertIn("Sprawdzono już dziś", out)
        code, out = run("update-check", "--force")
        self.assertEqual(code, 2)

    def test_update_offline(self):
        self.point_at("file:///nie/ma/")
        code, out = run("update-check")
        self.assertEqual(code, 2)
        self.assertTrue(out.startswith("NIE SPRAWDZONO"), out)
        self.assertFalse(self.cache.exists())

    def test_default_cache_respects_gd_home(self):
        self.assertEqual(update.default_cache(), self.tmp / "home" / "update.json")

    # Reguła Codexa dopasowuje tylko początek polecenia, więc polecenie nie może przyjmować
    # argumentów, którymi przekieruje się adres albo plik (przegląd 0.2.0, C2).
    def test_command_takes_no_source_or_cache_arguments(self):
        for flag in ("--source", "--cache"):
            with self.assertRaises(SystemExit) as cm:
                run("update-check", flag, "cokolwiek")
            self.assertEqual(cm.exception.code, 2, flag)
        ns = designer.parser().parse_args(["update-check", "--force"])
        self.assertEqual(set(vars(ns)) - {"command", "func"}, {"force"})

    def test_cannot_overwrite_an_arbitrary_file(self):
        precious = self.tmp / "cenny.txt"
        precious.write_text("nie ruszać", encoding="utf-8")
        with self.assertRaises(SystemExit):
            run("update-check", "--source", self.source("9.1.0"), "--cache", precious)
        self.assertEqual(precious.read_text(encoding="utf-8"), "nie ruszać")

    def test_cache_is_always_in_gd_home(self):
        self.point_at(self.source("9.1.0"))
        run("update-check")
        self.assertTrue(self.cache.is_file())
        self.assertEqual([p.name for p in (self.tmp / "home").iterdir()], ["update.json"])

    def test_official_address_is_hardcoded(self):
        self.assertEqual(update.source_url(), update.SOURCE_URL)
        self.assertTrue(update.SOURCE_URL.startswith(
            "https://raw.githubusercontent.com/guc-net/codex-marketplace/"))

    def test_source_variable_is_only_for_tests_and_documented_as_such(self):
        self.point_at("file:///tests-only/")
        self.assertEqual(update.source_url(), "file:///tests-only/")
        text = (PLUGIN / "scripts" / "gd" / "update.py").read_text(encoding="utf-8")
        self.assertIn("tylko do testów", text)


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
