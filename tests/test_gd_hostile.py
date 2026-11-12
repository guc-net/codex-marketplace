"""Wrogie kompozycje: po regule Codexa `render` i `check` działają poza piaskownicą, więc strona
nie może wykonywać skryptów, łączyć się z siecią, ładować ramek ani czytać plików spoza marki."""
from __future__ import annotations

import contextlib
import html.parser
import re
import shutil
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_gd_render import KIWI, PLUGIN, BrowserCase, has_browser, run  # noqa: E402

sys.path.insert(0, str(PLUGIN / "scripts"))

from gd import brand as brandlib  # noqa: E402
from gd import browser, png, render  # noqa: E402
from gd.common import GdError  # noqa: E402

import png as testpng  # noqa: E402  (tests/png.py: zapis obrazów testowych)

FMT = {"id": "ig-post", "width": 1080, "height": 1350}
BLUE = (0, 0, 255)


def pixel(path, x, y):
    return tuple(png.read(path).pixel(x, y)[:3])


class Recorder:
    """Lokalny serwer HTTP, który zapisuje każde żądanie."""

    def __init__(self):
        seen = self.requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                seen.append(self.path)
                self.send_response(200)
                self.send_header("Content-Type", "text/css")
                self.end_headers()
                self.wfile.write(b"body{}")

            do_POST = do_GET  # noqa: N815

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


class Tags(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def tags_of(text):
    p = Tags()
    p.feed(text)
    return p.tags


class BuildCase(BrowserCase):
    """Budowanie strony bez przeglądarki."""

    def build(self, text, brand=None, fmt=FMT):
        comp = self.tmp / "kompozycja.html"
        comp.write_text(text, encoding="utf-8")
        built = render.build_html(comp, brand, fmt)
        self.addCleanup(shutil.rmtree, built.parent, ignore_errors=True)
        return built.read_text(encoding="utf-8")


class TestBuiltPage(BuildCase):
    DOC = '<!doctype html><html><head><meta charset="utf-8"><title>x</title></head><body>Cześć</body></html>'

    def policy(self, built):
        content = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">', built).group(1)
        return {d.split(" ", 1)[0]: d.split(" ", 1)[1] for d in content.split("; ")}

    def test_csp_meta_is_the_first_thing_after_the_doctype(self):
        built = self.build(self.DOC)
        self.assertRegex(built, r'^<!doctype html><meta http-equiv="Content-Security-Policy"')
        first = tags_of(built)[0]
        self.assertEqual(first[0], "meta")
        self.assertEqual(first[1]["http-equiv"], "Content-Security-Policy")

    def test_policy_directives(self):
        pol = self.policy(self.build(self.DOC))
        self.assertEqual(pol["default-src"], "'none'")
        self.assertRegex(pol["script-src"], r"^'nonce-[A-Za-z0-9_-]{16,}'$")
        for directive in ("connect-src", "frame-src", "object-src", "form-action"):
            self.assertEqual(pol[directive], "'none'", directive)
        self.assertEqual(pol["style-src"], "'unsafe-inline'")
        self.assertEqual(pol["img-src"], "file: data:")
        self.assertEqual(pol["font-src"], "data:")
        self.assertEqual(pol["base-uri"], "file:")
        self.assertNotIn("unsafe-eval", " ".join(pol.values()))
        self.assertNotIn("http", " ".join(pol.values()))

    def test_nonce_is_fresh_and_only_our_script_has_it(self):
        a = self.build(self.DOC.replace("</body>", "<script>x()</script></body>"))
        b = self.build(self.DOC)
        nonce_a = re.search(r"'nonce-([^']+)'", a).group(1)
        nonce_b = re.search(r"'nonce-([^']+)'", b).group(1)
        self.assertNotEqual(nonce_a, nonce_b)
        scripts = [attrs for tag, attrs in tags_of(a) if tag == "script"]
        self.assertEqual([s.get("nonce") for s in scripts], [None, nonce_a])
        self.assertIn(f'<script nonce="{nonce_a}">', a)

    def test_charset_and_base_follow_and_stay_in_the_first_kilobyte(self):
        built = self.build(self.DOC)
        self.assertLess(built.index('<meta charset="utf-8">'), 1024)
        self.assertLess(built.index("<base href="), built.index("<title>"))
        self.assertLess(built.index("Content-Security-Policy"), built.index('<meta charset="utf-8">'))

    def test_csp_goes_before_everything_in_odd_documents(self):
        evil = "<script>pwned()</script>"
        cases = {
            "bez doctype": evil + "<p>x</p>",
            "skrypt przed doctype": evil + "<!doctype html><html><head></head><body></body></html>",
            "skrypt przed <head>": "<!doctype html><html>" + evil + "<head></head><body></body></html>",
            "BOM": "﻿" + evil + "<html><body></body></html>",
            "komentarz z --!>": "<!-- --!>" + evil + " --><!doctype html><html><body></body></html>",
            "komentarz <!-->": "<!-->" + evil + "<!doctype html><html><body></body></html>",
            "wielkie litery": "<!DOCTYPE HTML><HTML><HEAD>" + evil + "</HEAD><BODY></BODY></HTML>",
        }
        for name, text in cases.items():
            with self.subTest(name):
                built = self.build(text)
                self.assertLess(built.index("Content-Security-Policy"), built.index("pwned()"))

    def test_plain_comment_before_doctype_keeps_standards_mode(self):
        built = self.build("<!-- licencja -->\n" + self.DOC)
        self.assertLess(built.index("<!doctype html>"), built.index("Content-Security-Policy"))
        self.assertLess(built.index("licencja"), built.index("<!doctype html>"))

    def test_refresh_meta_is_rejected_in_any_spelling(self):
        for meta in ('<meta http-equiv="refresh" content="0;url=file:///etc/hosts">',
                     "<META HTTP-EQUIV=Refresh CONTENT='0;url=file:///etc/hosts'>",
                     '<meta http-equiv="re&#102;resh" content="0;url=file:///etc/hosts">',
                     '<meta http-equiv="&#x72;efresh" content="0">'):
            with self.subTest(meta):
                with self.assertRaises(GdError) as cm:
                    self.build(self.DOC.replace("<title>", meta + "<title>"))
                self.assertIn("refresh", str(cm.exception))

    def test_brand_references_outside_the_brand_folder_are_rejected(self):
        secret = self.tmp / "sekret.txt"
        secret.write_text("TAJNE", encoding="utf-8")
        brand = brandlib.load(self.brand_dir)
        for ref in ("brand:../../sekret.txt", f"brand:{secret}", "brand:logo/../../../sekret.txt"):
            with self.subTest(ref):
                with self.assertRaises(GdError) as cm:
                    self.build(f'<img src="{ref}">', brand)
                self.assertIn("poza folder marki", str(cm.exception))

    def write_brand(self, **fonts):
        """Biblia marki z podmienionym `font.heading.file` (reszta jak Kiwi)."""
        text = (self.brand_dir / "brand.md").read_text(encoding="utf-8")
        text = re.sub(r'font\.heading\.file: "[^"]*"', 'font.heading.file: "%s"' % fonts["file"], text)
        (self.brand_dir / "brand.md").write_text(text, encoding="utf-8")
        return brandlib.load(self.brand_dir)

    def test_font_outside_the_brand_folder_is_rejected(self):
        secret = self.tmp / "sekret.ttf"
        secret.write_bytes(b"SEKRETNA-TRESC")
        for file in (str(secret).replace("\\", "/"), "../../sekret.ttf"):
            with self.subTest(file):
                b = self.write_brand(file=file)
                self.assertTrue(brandlib.path_problems(b))
                errors, _ = brandlib.validate(b)
                self.assertTrue(any("poza folderem marki" in e for e in errors), errors)
                with self.assertRaises(GdError) as cm:
                    self.build(self.DOC, b)
                self.assertIn("poza swojego folderu", str(cm.exception))

    @unittest.skipIf(sys.platform == "win32", "dowiązania symboliczne wymagają uprawnień na Windows")
    def test_symlink_pointing_outside_is_rejected(self):
        secret = self.tmp / "sekret.ttf"
        secret.write_bytes(b"SEKRETNA-TRESC")
        link = self.brand_dir / "fonts" / "link.ttf"
        link.symlink_to(secret)
        b = self.write_brand(file="fonts/link.ttf")
        self.assertTrue(brandlib.path_problems(b))
        with self.assertRaises(GdError):
            self.build(self.DOC, b)

    def test_font_extension_must_be_a_font(self):
        (self.brand_dir / "fonts" / "notatki.txt").write_text("nie font", encoding="utf-8")
        b = self.write_brand(file="fonts/notatki.txt")
        errors, _ = brandlib.validate(b)
        self.assertTrue(any(".ttf, .otf, .woff albo .woff2" in e for e in errors), errors)
        with self.assertRaises(GdError):
            self.build(self.DOC, b)

    def test_all_four_font_extensions_are_accepted_and_embedded_with_their_type(self):
        self.assertEqual(brandlib.FONT_EXTENSIONS, (".ttf", ".otf", ".woff", ".woff2"))
        src = self.brand_dir / "fonts" / "Anton-Regular.ttf"
        for ext, mime in ((".otf", "font/otf"), (".woff", "font/woff"), (".woff2", "font/woff2")):
            with self.subTest(ext):
                shutil.copyfile(src, self.brand_dir / "fonts" / f"Anton{ext}")
                b = self.write_brand(file=f"fonts/Anton{ext}")
                self.assertEqual(brandlib.path_problems(b), [])
                self.assertIn(f"data:{mime};base64,", self.build(self.DOC, b))

    def test_normal_brand_has_no_path_problems(self):
        b = brandlib.load(self.brand_dir)
        self.assertEqual(brandlib.path_problems(b), [])
        self.assertEqual(brandlib.validate(b)[0], [])


@unittest.skipUnless(has_browser(), "brak przeglądarki")
class TestHostileCompositions(BrowserCase):
    """Prawdziwa przeglądarka i wrogie kompozycje. Każdy atak sprawdzamy też na „kontroli”
    (bez zasady CSP i bez flag), żeby test dowodził, że atak bez obrony działa."""

    BG = "<style>html,body{background:#0000ff}</style>"

    @contextlib.contextmanager
    def no_defenses(self):
        with mock.patch.object(render, "csp_policy", return_value=""), \
                mock.patch.object(browser, "HARDEN_FLAGS", []):
            yield

    def go(self, body, head="", fmt="ig-post"):
        job = self.new_job(fmt)
        self.write(job, fmt, body, self.BG + head)
        return job

    def rendered(self, job, fmt="ig-post"):
        code, out = run("render", "--job", job)
        return code, out, job / "final" / f"{fmt}.png"

    def dom(self, job, fmt="ig-post"):
        brand = brandlib.load(self.brand_dir)
        built = render.build_html(job / "composition" / f"{fmt}.html", brand, FMT)
        try:
            return browser.dump_dom(built, FMT["width"], FMT["height"])
        finally:
            shutil.rmtree(built.parent, ignore_errors=True)

    def shot(self, job, fmt="ig-post"):
        """Zrzut strony bez raportu (raport odrzuciłby zepsuty obraz z wrogiej kompozycji)."""
        built = render.build_html(job / "composition" / f"{fmt}.html", brandlib.load(self.brand_dir), FMT)
        try:
            out = self.tmp / "zrzut.png"
            browser.screenshot(built, out, FMT["width"], FMT["height"])
            return out
        finally:
            shutil.rmtree(built.parent, ignore_errors=True)

    @staticmethod
    def hijacked(dom):
        """Czy skrypt strony zmienił <html>/<body> (nie liczy się sam tekst skryptu w DOM)."""
        tags = re.findall(r"<(?:html|body)\b[^>]*>", dom)
        return any("data-pwned" in t for t in tags) or "<title>PWNED</title>" in dom

    SCRIPTS = ('<script>document.body.style.background="red";document.body.setAttribute("data-pwned","1");'
               'document.title="PWNED"</script>'
               '<img src="x" onerror="document.body.setAttribute(\'data-pwned2\',\'1\')">'
               '<svg onload="document.body.setAttribute(\'data-pwned3\',\'1\')"><script>'
               'document.body.setAttribute("data-pwned4","1")</script></svg>')

    def test_page_scripts_do_not_run(self):
        job = self.go(self.SCRIPTS)
        self.assertFalse(self.hijacked(self.dom(job)))
        self.assertEqual(pixel(self.shot(job), 5, 5), BLUE)
        # kontrola: bez obrony skrypt zmienia stronę
        with self.no_defenses():
            dom = self.dom(job)
        self.assertTrue(self.hijacked(dom), "kontrola: bez obrony skrypt działa")
        for n in ("data-pwned2", "data-pwned3", "data-pwned4"):
            self.assertIn(n + '="1"', dom)

    def test_scripts_hidden_before_the_head_or_in_tricky_comments_do_not_run(self):
        job = self.new_job()
        evil = '<script>document.documentElement.setAttribute("data-pwned","1")</script>'
        for text in (evil + "<!doctype html><html><head></head><body></body></html>",
                     "<!doctype html><html>" + evil + "<head></head><body></body></html>",
                     "<!-- --!>" + evil + " --><!doctype html><html><head></head><body></body></html>"):
            (job / "composition" / "ig-post.html").write_text(text, encoding="utf-8")
            self.assertFalse(self.hijacked(self.dom(job)), text[:40])
            with self.no_defenses():
                self.assertTrue(self.hijacked(self.dom(job)), "kontrola: " + text[:40])

    def test_iframe_with_a_local_file_is_blocked(self):
        secret = self.tmp / "sekret.html"
        secret.write_text('<body style="background:#ff0000">TAJNE</body>', encoding="utf-8")
        job = self.go(f'<iframe src="{secret.as_uri()}" style="position:absolute;left:0;top:0;'
                      'width:1080px;height:1350px;border:0"></iframe>')
        code, out, final = self.rendered(job)
        self.assertEqual(code, 0, out)
        self.assertNotEqual(pixel(final, 500, 500), (255, 0, 0))
        shutil.rmtree(job / "final")
        with self.no_defenses():
            code, out, final = self.rendered(job)
            self.assertEqual(pixel(final, 500, 500), (255, 0, 0), "kontrola: bez obrony ramka działa")

    def hostile_network_page(self, base):
        head = (f'<link rel="stylesheet" href="{base}/link.css">'
                f'<style>@import url({base}/import.css);'
                f'@font-face{{font-family:Evil;src:url({base}/font.woff2)}}'
                f'.x{{font-family:Evil;background:url({base}/bg.png)}}</style>'
                f'<link rel="preconnect" href="{base}"><link rel="prefetch" href="{base}/prefetch">'
                f'<link rel="dns-prefetch" href="{base}"><link rel="icon" href="{base}/icon.png">')
        body = (f'<div class="x">x</div><img src="{base}/img.png">'
                f'<script>fetch("{base}/fetch");var r=new XMLHttpRequest();r.open("GET","{base}/xhr");'
                f'r.send();new Image().src="{base}/beacon";navigator.sendBeacon("{base}/sendbeacon")</script>'
                f'<iframe src="{base}/frame"></iframe><object data="{base}/object"></object>'
                f'<video poster="{base}/poster"></video><audio src="{base}/audio"></audio>'
                f'<form action="{base}/form"><input type="image" src="{base}/inputimg"></form>')
        return body, head

    def run_network_attack(self, rec):
        body, head = self.hostile_network_page(rec.url)
        job = self.go(body, head)
        # względny adres obok wrogiego <base>: musi iść do naszego <base>, nie do serwera
        text = (job / "composition" / "ig-post.html").read_text(encoding="utf-8")
        text = text.replace("<head>", f'<head><base href="{rec.url}/">', 1).replace(
            "</body>", '<img src="wzgledny.png"></body>')
        (job / "composition" / "ig-post.html").write_text(text, encoding="utf-8")
        run("render", "--job", job)
        run("check", "--job", job)
        self.dom(job)

    def test_network_is_blocked_by_csp_alone_and_with_flags(self):
        for flags in ([], list(browser.HARDEN_FLAGS)):
            with self.subTest(flags=bool(flags)), Recorder() as rec:
                with mock.patch.object(browser, "HARDEN_FLAGS", flags):
                    self.run_network_attack(rec)
                self.assertEqual(rec.requests, [])

    def test_control_without_defenses_does_reach_the_server(self):
        with Recorder() as rec, self.no_defenses():
            self.run_network_attack(rec)
        self.assertTrue(rec.requests, "kontrola: bez obrony strona łączy się z serwerem")

    def test_network_is_blocked_in_pdf_too(self):
        with Recorder() as rec:
            body, head = self.hostile_network_page(rec.url)
            job = self.new_job("a4-print")
            self.write(job, "a4-print", body, self.BG + head)
            run("render", "--job", job)
            self.assertEqual(rec.requests, [])

    def test_meta_refresh_is_refused_and_leaves_no_picture(self):
        secret = self.tmp / "sekret.html"
        secret.write_text('<body style="background:#ff0000">TAJNE</body>', encoding="utf-8")
        for meta in (f'<meta http-equiv="refresh" content="0;url={secret.as_uri()}">',
                     f'<meta http-equiv="re&#102;resh" content="0;url={secret.as_uri()}">'):
            job = self.go("", meta)
            code, out, final = self.rendered(job)
            self.assertEqual(code, 1, out)
            self.assertIn("refresh", out)
            self.assertFalse(final.exists())

    def test_absolute_font_path_is_refused(self):
        secret = self.tmp / "sekret.ttf"
        secret.write_bytes(b"SEKRETNA-TRESC")
        path = str(secret).replace("\\", "/")
        text = (self.brand_dir / "brand.md").read_text(encoding="utf-8")
        text = re.sub(r'font\.heading\.file: "[^"]*"', f'font.heading.file: "{path}"', text)
        (self.brand_dir / "brand.md").write_text(text, encoding="utf-8")
        job = self.go('<div data-gd="text" style="font-family:Anton">x</div>')
        code, out, final = self.rendered(job)
        self.assertEqual(code, 1, out)
        self.assertIn("poza swojego folderu", out)
        self.assertFalse(final.exists())
        code, out = run("check", "--job", job)
        self.assertEqual(code, 1, out)
        code, out = run("brand", "--path", self.brand_dir)
        self.assertEqual(code, 1, out)
        self.assertIn("poza folderem marki", out)

    def test_our_own_report_still_works_under_the_policy(self):
        job = self.go('<div data-gd="text" id="t" style="font-family:Anton;color:#fff">Cześć</div>')
        rep = render.report(job / "composition" / "ig-post.html", brandlib.load(self.brand_dir), FMT)
        self.assertTrue(rep["fonts"]["Anton"])
        self.assertEqual([e["id"] for e in rep["elements"]], ["t"])

    def test_normal_composition_renders_and_passes_check(self):
        body = ('<div data-gd="text" style="position:absolute;left:100px;top:100px;font-family:Anton;'
                'font-size:80px;color:#F5F5F5">Ślub w sobotę</div>'
                '<img data-gd="logo" src="brand:logo/full.png" width="300" '
                'style="position:absolute;left:100px;top:600px">')
        job = self.new_job()
        self.write(job, "ig-post", body, "<style>html,body{background:#101010}</style>")
        code, out, final = self.rendered(job)
        self.assertEqual(code, 0, out)
        self.assertEqual(pixel(final, 5, 5), (0x10, 0x10, 0x10))
        code, out = run("check", "--job", job)
        self.assertEqual((code, out.strip().splitlines()[0]), (0, "OK: 12/12"), out)

    def test_starter_template_renders_and_layer_images_load(self):
        job = self.new_job()
        shutil.copyfile(PLUGIN / "templates" / "composition-starter.html",
                        job / "composition" / "ig-post.html")
        code, out, final = self.rendered(job)
        self.assertEqual(code, 0, out)
        # zamrożona warstwa obok kompozycji (adres względny przez <base>) też się wczytuje
        testpng.png(job / "layers" / "tlo.png", 200, 200, (255, 0, 0), pasek=(255, 0, 0))
        self.write(job, "ig-post", '<img data-gd="layer" src="../layers/tlo.png" '
                   'style="position:absolute;left:0;top:0">')
        code, out, final = self.rendered(job)
        self.assertEqual(code, 0, out)
        self.assertEqual(pixel(final, 50, 50), (255, 0, 0))

    def test_local_image_files_still_show_up_documented_residual_risk(self):
        """CSP pozwala na obrazy z plików (`img-src file:`): kompozycja może pokazać dowolny plik
        graficzny z dysku w wyniku. Opisane w dokumentacji; to test, że zachowanie jest świadome."""
        photo = self.tmp / "zdjecie.png"
        testpng.png(photo, 200, 200, (255, 0, 0), pasek=(255, 0, 0))
        job = self.go(f'<img src="{photo.as_uri()}" style="position:absolute;left:0;top:0">')
        code, out, final = self.rendered(job)
        self.assertEqual(code, 0, out)
        self.assertEqual(pixel(final, 50, 50), (255, 0, 0))

    @unittest.skipIf(sys.platform == "win32", "dowiązania symboliczne wymagają uprawnień na Windows")
    def test_render_refuses_to_write_through_a_symlinked_output_folder(self):
        elsewhere = self.tmp / "gdzie-indziej"
        elsewhere.mkdir()
        job = self.go('<div data-gd="text">x</div>')
        shutil.rmtree(job / "final", ignore_errors=True)
        (job / "final").symlink_to(elsewhere, target_is_directory=True)
        code, out = run("render", "--job", job)
        self.assertEqual(code, 1, out)
        self.assertIn("poza folderem zlecenia", out)
        self.assertEqual(list(elsewhere.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
