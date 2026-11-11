"""Testy składania: przeglądarka, formaty, HTML, PNG, PDF, env."""
from __future__ import annotations

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
PLUGIN = REPO / "plugins" / "graphic-designer"
sys.path.insert(0, str(PLUGIN / "scripts"))

import designer  # noqa: E402
from gd import brand as brandlib  # noqa: E402
from gd import browser, png, render  # noqa: E402
from gd.common import GdError  # noqa: E402

KIWI = REPO / "tests" / "fixture" / "graphic-designer" / "kiwi"


def has_browser():
    try:
        browser.find()
        return True
    except GdError:
        return False


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = designer.main([str(a) for a in args])
    return code, out.getvalue() + err.getvalue()


class EnvVars(unittest.TestCase):
    def setenv(self, key, value):
        old = os.environ.get(key)
        self.addCleanup(lambda: os.environ.pop(key, None) if old is None else os.environ.update({key: old}))
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


class NoRender(EnvVars):
    def test_find_respects_env(self):
        self.setenv("GD_BROWSER", "/nie/ma/przegladarki")
        with self.assertRaises(GdError) as cm:
            browser.find()
        self.assertTrue(str(cm.exception).startswith("NO BROWSER"))

    def test_missing_browser_message(self):
        self.setenv("GD_BROWSER", "/nie/ma/przegladarki")
        self.setenv("GD_HOME", tempfile.mkdtemp())
        code, out = run("env")
        self.assertEqual(code, 0)
        self.assertIn("NO BROWSER", out)
        self.assertNotIn("Traceback", out)

    def test_render_without_browser_exits_1(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name).resolve()
        self.setenv("GD_HOME", str(root / "home"))
        lib = root / "Grafiki robocze ł"
        self.assertEqual(run("library", "--set", lib)[0], 0)
        code, out = run("new", "--title", "Plakat ślub", "--formats", "ig-post", "--brand", KIWI / "brand")
        self.assertEqual(code, 0, out)
        job = Path(out.split("JOB:", 1)[1].strip().splitlines()[0])
        (job / "composition" / "ig-post.html").write_text(
            "<!doctype html><html><head></head><body>x</body></html>", encoding="utf-8")
        self.setenv("GD_BROWSER", "/nie/ma/przegladarki")
        code, out = run("render", "--job", job)
        self.assertEqual(code, 1)
        self.assertIn("NO BROWSER", out)
        self.assertNotIn("Traceback", out)

    def test_formats_values(self):
        f = render.formats()
        table = {
            "ig-post": (1080, 1350, False, None, (34, 34, 34, 34)),
            "ig-square": (1080, 1080, False, None, (34, 34, 34, 34)),
            "ig-story": (1080, 1920, False, None, (270, 65, 340, 65)),
            "fb-event": (1920, 1005, False, None, (189, 360, 189, 360)),
            "a4-print": (2551, 3579, True, [216, 303], (71, 71, 71, 71)),
            "a3-print": (3579, 5031, True, [303, 426], (71, 71, 71, 71)),
        }
        self.assertEqual(set(f), set(table))
        for k, (w, h, pdf, mm, safe) in table.items():
            s = f[k]["safe"]
            self.assertEqual((f[k]["width"], f[k]["height"], f[k]["pdf"], f[k]["page_mm"],
                              (s["top"], s["right"], s["bottom"], s["left"])), (w, h, pdf, mm, safe), k)

    def test_build_html_injects(self):
        with tempfile.TemporaryDirectory() as d:
            comp = Path(d) / "ig-post.html"
            comp.write_text('<html><head><title>x</title></head><body>'
                            '<img src="brand:logo/full.png"></body></html>', encoding="utf-8")
            b = brandlib.load(KIWI / "brand")
            built = render.build_html(comp, b, render.formats()["ig-post"])
            self.addCleanup(shutil.rmtree, built.parent, True)
            html = built.read_text(encoding="utf-8")
        self.assertIn("@font-face", html)
        self.assertIn("data:font/ttf;base64,", html)
        self.assertIn("--color-primary: #2BB673", html)
        self.assertNotIn("brand:logo/full.png", html)
        self.assertIn((KIWI / "brand" / "logo" / "full.png").resolve().as_uri(), html)
        self.assertLess(html.index("gd-inject"), html.index("</head>"))
        self.assertIn('id="gd-report"', html)

    def test_missing_brand_file_fails_before_browser(self):
        with tempfile.TemporaryDirectory() as d:
            comp = Path(d) / "x.html"
            comp.write_text('<html><head></head><body><img src="brand:logo/nie-ma.png"></body></html>',
                            encoding="utf-8")
            with self.assertRaises(GdError) as cm:
                render.build_html(comp, brandlib.load(KIWI / "brand"), render.formats()["ig-post"])
        self.assertIn("logo/nie-ma.png", str(cm.exception))


class BrowserCase(EnvVars):
    """Wspólne przygotowanie zleceń z przeglądarką (bez własnych testów)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.setenv("GD_HOME", str(self.tmp / "home"))
        self.lib = self.tmp / "Grafiki robocze ł"
        code, _ = run("library", "--set", self.lib)
        self.assertEqual(code, 0)
        self.brand_dir = self.tmp / "marka" / "brand"
        shutil.copytree(KIWI / "brand", self.brand_dir)

    def new_job(self, formats="ig-post", title="Plakat ślub", ready=True):
        """Zlecenie; `ready` = prawdziwy brief i `choose --direct`, żeby `check` nie wołał o proces."""
        code, out = run("new", "--title", title, "--formats", formats, "--project", "Plakat ślub",
                        "--brand", self.brand_dir)
        self.assertEqual(code, 0, out)
        job = Path(out.split("JOB:", 1)[1].strip().splitlines()[0])
        if ready:
            self.make_ready(job)
        return job

    def make_ready(self, job):
        (job / "brief.md").write_text(REAL_BRIEF, encoding="utf-8")
        code, out = run("choose", "--job", job, "--direct")
        self.assertEqual(code, 0, out)

    def write(self, job, fmt, body, head=""):
        (job / "composition" / f"{fmt}.html").write_text(
            f'<!doctype html><html><head><meta charset="utf-8">{head}</head><body>{body}</body></html>',
            encoding="utf-8")


@unittest.skipUnless(has_browser(), "brak przeglądarki")
class WithBrowser(BrowserCase):
    def test_render_png_exact_size(self):
        job = self.new_job("ig-post,ig-story")
        body = ('<div data-gd="text" style="font-family:Anton;font-size:90px;color:var(--color-primary)">'
                'Ślub w sobotę, żółć</div><img data-gd="logo" src="brand:logo/full.png" width="300">')
        for f in ("ig-post", "ig-story"):
            self.write(job, f, body, "<style>body{background:var(--color-background)}</style>")
        code, out = run("render", "--job", job)
        self.assertEqual(code, 0, out)
        self.assertIn("RENDERED:", out)
        self.assertEqual(png.size(job / "final" / "ig-post.png"), (1080, 1350))
        self.assertEqual(png.size(job / "final" / "ig-story.png"), (1080, 1920))
        self.assertEqual(png.read(job / "final" / "ig-post.png").pixel(5, 5)[:3], (0x10, 0x10, 0x10))

    def test_render_moves_stage_to_composition_but_preview_does_not(self):
        job = self.new_job()
        stage = lambda: json.loads((job / "job.json").read_text(encoding="utf-8"))["stage"]  # noqa: E731
        self.assertEqual(stage(), "stages")
        shutil.copyfile(PLUGIN / "templates" / "composition-starter.html",
                        job / "composition" / "ig-post.html")
        self.assertEqual(run("render", "--job", job, "--preview")[0], 0)
        self.assertEqual(stage(), "stages")
        self.assertEqual(run("render", "--job", job)[0], 0)
        self.assertEqual(stage(), "composition")

    def test_starter_renders(self):
        job = self.new_job()
        shutil.copyfile(PLUGIN / "templates" / "composition-starter.html",
                        job / "composition" / "ig-post.html")
        code, out = run("render", "--job", job)
        self.assertEqual(code, 0, out)

    def test_render_transparent_background(self):
        job = self.new_job()
        self.write(job, "ig-post", '<div data-gd="text" style="position:absolute;left:400px;top:400px">x</div>')
        code, out = run("render", "--job", job)
        self.assertEqual(code, 0, out)
        self.assertEqual(png.read(job / "final" / "ig-post.png").pixel(0, 0)[3], 0)

    def test_render_pdf_page_size(self):
        job = self.new_job("a4-print")
        self.write(job, "a4-print", '<div style="width:100%;height:100%;background:#2BB673"></div>')
        code, out = run("render", "--job", job)
        self.assertEqual(code, 0, out)
        self.assertEqual(png.size(job / "final" / "a4-print.png"), (2551, 3579))
        pdf = (job / "final" / "a4-print.pdf").read_bytes()
        box = re.search(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]", pdf)
        self.assertIsNotNone(box)
        nums = [float(x) for x in box.groups()]
        for got, want in zip(nums, [0, 0, 612, 859]):
            self.assertAlmostEqual(got, want, delta=1)
        self.assertEqual(len(re.findall(rb"/Type\s*/Page\b", pdf)), 1)

    def test_render_fails_on_missing_font(self):
        (self.brand_dir / "fonts" / "Anton-Regular.ttf").unlink()
        job = self.new_job()
        self.write(job, "ig-post", '<div data-gd="text" style="font-family:\'Anton\'">x</div>')
        code, out = run("render", "--job", job)
        self.assertEqual(code, 1)
        self.assertIn("Anton", out)
        self.assertNotIn("Traceback", out)
        self.assertEqual(list((job / "final").iterdir()), [])

    def test_unused_missing_font_is_fine(self):
        (self.brand_dir / "fonts" / "Anton-Regular.ttf").unlink()
        job = self.new_job()
        self.write(job, "ig-post", '<div data-gd="text" style="font-family:sans-serif">x</div>')
        code, out = run("render", "--job", job)
        self.assertEqual(code, 0, out)

    def test_broken_image_fails(self):
        job = self.new_job()
        self.write(job, "ig-post", '<img src="../layers/nie-ma.png">')
        code, out = run("render", "--job", job)
        self.assertEqual(code, 1)
        self.assertIn("nie-ma.png", out)
        self.assertEqual(list((job / "final").iterdir()), [])

    def test_listed_format_without_composition(self):
        job = self.new_job("ig-post,ig-story")
        self.write(job, "ig-post", "<p>x</p>")
        code, out = run("render", "--job", job)
        self.assertEqual(code, 1)
        self.assertIn("composition/ig-story.html", out)
        code, out = run("render", "--job", job, "--format", "ig-post")
        self.assertEqual(code, 0, out)
        self.assertTrue((job / "final" / "ig-post.png").is_file())

    def test_preview_goes_to_drafts(self):
        job = self.new_job("ig-story")
        self.write(job, "ig-story", '<div style="width:100%;height:100%;background:#fff"></div>')
        code, out = run("render", "--job", job, "--preview")
        self.assertEqual(code, 0, out)
        prev = job / "drafts" / "preview-ig-story.png"
        self.assertEqual(png.size(prev), (1080, 1920))
        self.assertEqual(list((job / "final").iterdir()), [])
        img = png.read(prev)
        r, g, b, _ = img.pixel(500, 10)       # górna strefa: czerwony odcień
        self.assertGreater(r, g + 40)
        self.assertEqual(img.pixel(500, 900)[:3], (255, 255, 255))  # środek bez nakładki

    def test_inherited_body_font_not_loaded_is_fine(self):
        job = self.new_job()
        self.write(job, "ig-post", '<div data-gd="text" style="font-family:sans-serif">x</div>',
                   "<style>body{font-family:Anton}</style>")
        code, out = run("render", "--job", job)
        self.assertEqual(code, 0, out)

    def test_hidden_element_with_brand_font_is_fine(self):
        job = self.new_job()
        self.write(job, "ig-post", '<div style="display:none;font-family:Anton">x</div>'
                   '<div data-gd="text" style="font-family:sans-serif">y</div>')
        code, out = run("render", "--job", job)
        self.assertEqual(code, 0, out)

    def test_broken_font_file_still_fails(self):
        job = self.new_job()
        font = self.brand_dir / "fonts" / "Anton-Regular.ttf"
        font.write_bytes(font.read_bytes()[:200])
        self.write(job, "ig-post", '<div data-gd="text" style="font-family:Anton">x</div>')
        code, out = run("render", "--job", job)
        self.assertEqual(code, 1, out)
        self.assertIn("Anton", out)
        self.assertNotIn("Traceback", out)

    def test_render_format_must_belong_to_job(self):
        job = self.new_job("ig-post")
        self.write(job, "ig-post", "<p>x</p>")
        self.write(job, "ig-story", "<p>x</p>")
        code, out = run("render", "--job", job, "--format", "ig-story")
        self.assertEqual(code, 1, out)
        self.assertIn("ig-story", out)
        self.assertEqual(list((job / "final").iterdir()), [])

    def test_report_contains_elements(self):
        job = self.new_job()
        self.write(job, "ig-post", '<div id="t" data-gd="text" style="font-family:Anton;color:#ff0000">Cześć</div>')
        b = brandlib.load(self.brand_dir)
        rep = render.report(job / "composition" / "ig-post.html", b, render.formats()["ig-post"])
        el = rep["elements"][0]
        self.assertEqual((el["gd"], el["id"], el["text"], el["font"], el["color"]),
                         ("text", "t", "Cześć", "Anton", "#ff0000"))
        self.assertTrue(rep["fonts"]["Anton"])
        self.assertEqual(rep["images_broken"], [])


class EnvCommand(EnvVars):
    def test_env_warns_api_key(self):
        self.setenv("OPENAI_API_KEY", "x")
        code, out = run("env")
        self.assertEqual(code, 0)
        self.assertIn("WARNING: OPENAI_API_KEY", out)
        self.assertRegex(out, r"PYTHON: \d+\.\d+\.\d+")

    def test_env_no_warning_without_key(self):
        self.setenv("OPENAI_API_KEY", "")
        code, out = run("env")
        self.assertNotIn("WARNING", out)


REAL_BRIEF = """# Brief zlecenia

## Cel
Zachęcić do zapisu na warsztaty ceramiki w sobotę wieczorem.

## Odbiorca
Mieszkańcy dzielnicy, Instagram, post 4:5.

## Teksty dosłowne
- Nagłówek: Wieczór z gliną
- Data i godzina: sobota, 18.00
"""


def fake_browser(tmp, body):
    """Mały skrypt udający przeglądarkę (tylko systemy z powłoką sh)."""
    path = Path(tmp) / "fake-browser.sh"
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


@unittest.skipIf(os.name == "nt", "atrapa przeglądarki to skrypt sh")
class SandboxCrash(EnvVars):
    """Awaria przeglądarki w piaskownicy Codexa ma dać jasny trop SANDBOX?."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.html = self.tmp / "x.html"
        self.html.write_text("<html><body>x</body></html>", encoding="utf-8")

    def crash(self, body):
        self.setenv("GD_BROWSER", str(fake_browser(self.tmp, body)))
        with self.assertRaises(GdError) as cm:
            browser.dump_dom(self.html, 100, 100)
        return str(cm.exception)

    def test_exit_134_is_sandbox_hint(self):
        msg = self.crash("exit 134")
        self.assertTrue(msg.startswith("SANDBOX?:"), msg)
        self.assertIn("piaskownic", msg)
        self.assertIn("poza piaskownicą", msg)
        self.assertIn("przeglądarka zakończyła się kodem 134", msg)

    def test_signal_abort_is_sandbox_hint(self):
        msg = self.crash("kill -ABRT $$")
        self.assertTrue(msg.startswith("SANDBOX?:"), msg)
        self.assertIn("kodem -6", msg)

    def test_exit_139_and_133_are_sandbox_hint(self):
        for code in (133, 139):
            self.assertTrue(self.crash(f"exit {code}").startswith("SANDBOX?:"), code)

    def test_other_crash_signals_are_sandbox_hint(self):
        for sig in ("ILL", "TRAP", "SEGV"):
            self.assertTrue(self.crash(f"kill -{sig} $$").startswith("SANDBOX?:"), sig)
        for code in (132, 138):
            self.assertTrue(self.crash(f"exit {code}").startswith("SANDBOX?:"), code)

    def test_kill_and_term_are_not_sandbox_hint(self):
        for sig in ("KILL", "TERM"):
            msg = self.crash(f"kill -{sig} $$")
            self.assertFalse(msg.startswith("SANDBOX?:"), (sig, msg))
            self.assertIn("kodem -", msg)

    def test_is_crash_list(self):
        for code in (-4, -5, -6, -10, -11, 132, 133, 134, 138, 139):
            self.assertTrue(browser.is_crash(code), code)
        for code in (0, 1, 2, -2, -9, -15, 137, 143, 255):
            self.assertFalse(browser.is_crash(code), code)

    def test_ordinary_failure_has_no_sandbox_hint(self):
        msg = self.crash("echo zly argument >&2; exit 1")
        self.assertFalse(msg.startswith("SANDBOX?:"), msg)
        self.assertIn("kodem 1", msg)
        self.assertIn("zly argument", msg)


@unittest.skipIf(os.name == "nt", "atrapa przeglądarki to skrypt sh")
class EnvSmokeTest(EnvVars):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_env_browser_test_ok(self):
        self.setenv("GD_BROWSER", str(fake_browser(self.tmp, "echo '<html></html>'")))
        code, out = run("env")
        self.assertEqual(code, 0)
        self.assertIn("BROWSER: ", out)
        self.assertIn("BROWSER-TEST: OK", out)

    def test_env_browser_test_crash(self):
        self.setenv("GD_BROWSER", str(fake_browser(self.tmp, "exit 134")))
        code, out = run("env")
        self.assertEqual(code, 0)
        self.assertIn("BROWSER: ", out)
        self.assertRegex(out, r"BROWSER-TEST: FAILED \(kod 134\) — SANDBOX\?:")

    def test_env_browser_test_ordinary_failure(self):
        self.setenv("GD_BROWSER", str(fake_browser(self.tmp, "exit 2")))
        code, out = run("env")
        self.assertEqual(code, 0)
        self.assertRegex(out, r"BROWSER-TEST: FAILED \(kod 2\)")
        self.assertNotIn("SANDBOX?", out)

    def test_env_smoke_test_survives_oserror(self):
        from unittest import mock
        self.setenv("GD_BROWSER", str(fake_browser(self.tmp, "echo '<html></html>'")))
        with mock.patch.object(browser.tempfile, "mkdtemp", side_effect=OSError("brak TMPDIR")):
            code, out = run("env")
        self.assertEqual(code, 0)
        self.assertIn("BROWSER-TEST: FAILED", out)
        self.assertIn("brak TMPDIR", out)
        self.assertRegex(out, r"PYTHON: \d+")

    def test_env_no_browser_no_smoke_test(self):
        self.setenv("GD_BROWSER", "/nie/ma/przegladarki")
        code, out = run("env")
        self.assertEqual(code, 0)
        self.assertIn("NO BROWSER", out)
        self.assertNotIn("BROWSER-TEST", out)


if __name__ == "__main__":
    unittest.main()
