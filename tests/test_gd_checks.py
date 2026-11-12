"""Testy sprawdzania grafik: kontrast, znaki, strefy, logo, warstwy."""
from __future__ import annotations

import os
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_gd_render import KIWI, PLUGIN, BrowserCase, has_browser, run  # noqa: E402

PLUGIN_STARTER = PLUGIN / "templates" / "composition-starter.html"
TEXT_OK = ('<div data-gd="text" style="position:absolute;left:100px;top:100px;'
           'font-family:Anton;font-size:80px;color:%s">%s</div>')
LOGO_OK = ('<img data-gd="logo" src="brand:logo/full.png" width="300" '
           'style="position:absolute;left:100px;top:600px">')
BG = "<style>html,body{background:%s}</style>"


@unittest.skipUnless(has_browser(), "brak przeglądarki")
class Checks(BrowserCase):
    def go(self, body, bg="#101010", fmt="ig-post", render=True):
        job = self.new_job(fmt)
        self.write(job, fmt, body, BG % bg)
        if render:
            code, out = run("render", "--job", job)
            self.assertEqual(code, 0, out)
        return job

    def problems(self, job):
        code, out = run("check", "--job", job)
        return code, out

    def test_clean_composition_passes(self):
        job = self.go(TEXT_OK % ("#F5F5F5", "Ślub w sobotę") + LOGO_OK)
        code, out = self.problems(job)
        self.assertEqual((code, out.strip().splitlines()[0]), (0, "OK: 12/12"), out)

    def test_low_contrast_flagged(self):
        job = self.go(TEXT_OK % ("#2A6F97", "14.03"), bg="#14213D")
        code, out = self.problems(job)
        self.assertEqual(code, 3, out)
        self.assertIn("[ig-post] contrast:", out)
        self.assertIn("«14.03»", out)
        self.assertIn("2,9:1", out)
        self.assertIn("3:1", out)

    def test_forbidden_pair_flagged(self):
        job = self.go(TEXT_OK % ("#FF8A00", "Hej"), bg="#2BB673")
        code, out = self.problems(job)
        self.assertEqual(code, 3, out)
        self.assertIn("forbidden:", out)
        self.assertIn("accent-orange", out)

    def test_text_outside_safe_zone_story(self):
        job = self.go(TEXT_OK.replace("top:100px", "top:100px") % ("#F5F5F5", "Za wysoko"),
                      fmt="ig-story")
        code, out = self.problems(job)
        self.assertEqual(code, 3, out)
        self.assertIn("[ig-story] safe-zone:", out)

    def test_missing_glyph_flagged(self):
        job = self.go(TEXT_OK % ("#F5F5F5", "Hej ★"))
        code, out = self.problems(job)
        self.assertEqual(code, 3, out)
        self.assertIn("glyphs:", out)
        self.assertIn("★", out)
        self.assertIn("Anton", out)

    def test_logo_distorted_flagged(self):
        job = self.go('<img data-gd="logo" src="brand:logo/full.png" width="400" height="100" '
                      'style="position:absolute;left:100px;top:600px">')
        code, out = self.problems(job)
        self.assertEqual(code, 3, out)
        self.assertIn("logo-distortion:", out)

    def test_logo_not_from_brand_flagged(self):
        job = self.new_job()
        shutil.copyfile(KIWI / "brand" / "logo" / "full.png", job / "layers" / "x.png")
        self.write(job, "ig-post", '<img data-gd="logo" src="../layers/x.png" width="300" '
                   'style="position:absolute;left:100px;top:600px">', BG % "#101010")
        run("render", "--job", job)
        code, out = self.problems(job)
        self.assertEqual(code, 3, out)
        self.assertIn("logo-source:", out)

    def test_logo_too_small_flagged(self):
        job = self.go(LOGO_OK.replace('width="300"', 'width="120"'))
        code, out = self.problems(job)
        self.assertEqual(code, 3, out)
        self.assertIn("logo-min-width:", out)
        self.assertIn("240", out)

    def test_missing_final_is_finding_not_exception(self):
        job = self.go(TEXT_OK % ("#F5F5F5", "Hej"), render=False)
        code, out = self.problems(job)
        self.assertEqual(code, 3, out)
        self.assertIn("size:", out)
        self.assertIn("uruchom render", out)
        self.assertNotIn("Traceback", out)

    def test_changed_layer_flagged(self):
        job = self.new_job()
        src = self.tmp / "tlo.png"
        shutil.copyfile(KIWI / "brand" / "logo" / "mark.png", src)
        code, out = run("freeze", "--job", job, "--name", "tlo", "--file", src, "--source", "photo",
                        "--approved-by", "Ala")
        self.assertEqual(code, 0, out)
        self.write(job, "ig-post", '<img src="../layers/tlo.png" style="width:100px">', BG % "#101010")
        run("render", "--job", job)
        self.assertEqual(self.problems(job)[0], 0)
        (job / "layers" / "tlo.png").write_bytes(b"zmienione")
        code, out = self.problems(job)
        self.assertEqual(code, 3, out)
        self.assertIn("layers:", out)
        self.assertIn("tlo", out)

    def test_exit_code_3_on_problems(self):
        job = self.go(TEXT_OK % ("#F5F5F5", "Hej ★"))
        code, out = self.problems(job)
        self.assertEqual(code, 3)
        self.assertTrue(out.startswith("PROBLEMS: "), out)
        self.assertRegex(out, r"- \[ig-post\] \S+: ")


@unittest.skipUnless(has_browser(), "brak przeglądarki")
class ChecksFixes(BrowserCase):
    def test_starter_comment_is_not_a_layer(self):
        job = self.new_job()
        shutil.copyfile(PLUGIN_STARTER, job / "composition" / "ig-post.html")
        self.assertEqual(run("render", "--job", job)[0], 0)
        code, out = run("check", "--job", job)
        self.assertNotIn("layers:", out)
        self.assertNotIn("nie jest zamrożona", out)

    def test_stale_final_flagged(self):
        job = self.new_job()
        self.write(job, "ig-post", TEXT_OK % ("#F5F5F5", "Ślub") + LOGO_OK, BG % "#101010")
        self.assertEqual(run("render", "--job", job)[0], 0)
        self.assertEqual(run("check", "--job", job)[0], 0)
        comp = job / "composition" / "ig-post.html"
        later = (job / "final" / "ig-post.png").stat().st_mtime + 30
        os.utime(comp, (later, later))
        code, out = run("check", "--job", job)
        self.assertEqual(code, 3, out)
        self.assertIn("[ig-post] fresh:", out)
        self.assertIn("composition/ig-post.html", out)
        self.assertEqual(run("render", "--job", job)[0], 0)
        os.utime(comp, (later, later))
        os.utime(job / "final" / "ig-post.png", (later + 5, later + 5))
        self.assertEqual(run("check", "--job", job)[0], 0)

    def test_unfrozen_layer_message_tells_to_freeze(self):
        job = self.new_job()
        (job / "layers" / "tlo.png").write_bytes((KIWI / "brand" / "logo" / "mark.png").read_bytes())
        self.write(job, "ig-post", TEXT_OK % ("#F5F5F5", "Ślub") + LOGO_OK
                   + '<img src="../layers/tlo.png" style="position:absolute;left:500px;top:700px;width:100px">',
                   BG % "#101010")
        self.assertEqual(run("render", "--job", job)[0], 0)
        code, out = run("check", "--job", job)
        self.assertEqual(code, 3, out)
        self.assertIn("nie jest zamrożona", out)
        self.assertIn("freeze", out)

    def test_font_family_case_insensitive(self):
        job = self.new_job()
        self.write(job, "ig-post", TEXT_OK.replace("font-family:Anton", "font-family:anton")
                   % ("#F5F5F5", "Hej ★"), BG % "#101010")
        self.assertEqual(run("render", "--job", job)[0], 0)
        code, out = run("check", "--job", job)
        self.assertEqual(code, 3, out)
        self.assertIn("glyphs:", out)
        self.assertIn("★", out)

if __name__ == "__main__":
    unittest.main()
