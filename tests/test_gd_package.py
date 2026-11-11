"""Testy pakietów: share, finalize, adopt."""
from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_gd_render import KIWI, BrowserCase, has_browser, run  # noqa: E402

from gd import png  # noqa: E402

GOOD = ('<div data-gd="text" style="position:absolute;left:100px;top:100px;font-family:Anton;'
        'font-size:80px;color:#F5F5F5">Ślub w sobotę</div>'
        '<img data-gd="logo" src="brand:logo/full.png" width="300" '
        'style="position:absolute;left:100px;top:600px">'
        '<img src="../layers/tlo.png" style="position:absolute;left:500px;top:700px;width:100px">')
BAD = ('<div data-gd="text" style="position:absolute;left:100px;top:100px;font-family:Anton;'
       'font-size:80px;color:#2F4F6F">14.03</div>')
BG = "<style>html,body{background:#101010}</style>"


class PackageCase(BrowserCase):
    def setUp(self):
        super().setUp()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        shutil.copytree(KIWI / "brand", self.repo / "brand")

    def job_with_layer(self, formats="ig-post", body=GOOD, ready=True):
        job = self.new_job(formats, ready=ready)
        src = self.tmp / "tlo.png"
        shutil.copyfile(KIWI / "brand" / "logo" / "mark.png", src)
        code, out = run("freeze", "--job", job, "--name", "tlo", "--file", src, "--source", "photo",
                        "--approved-by", "Ala", "--note", "tło ze zdjęcia")
        self.assertEqual(code, 0, out)
        for f in formats.split(","):
            self.write(job, f, body, BG)
        (job / "drafts" / "A-v1.png").write_bytes(b"szkic")
        return job

    def pkg(self, job):
        month = json.loads((job / "job.json").read_text(encoding="utf-8"))["created"][:7]
        return self.repo / "graphics" / f"{month}-{job.name}"

    def finalized(self, **kw):
        job = self.job_with_layer(**kw)
        self.assertEqual(run("render", "--job", job)[0], 0)
        code, out = run("finalize", "--job", job, "--repo", self.repo, "--approved-by", "Ala")
        self.assertEqual(code, 0, out)
        return job


class NoBrowser(PackageCase):
    def test_share_excludes_drafts(self):
        job = self.job_with_layer()
        (job / "final" / "ig-post.png").write_bytes(b"x")
        code, out = run("share", "--job", job, "--repo", self.repo)
        self.assertEqual(code, 0, out)
        pkg = self.pkg(job)
        self.assertIn(f"PACKAGE: {pkg}", out)
        self.assertTrue((pkg / "layers" / "tlo.png").is_file())
        self.assertTrue((pkg / "layers" / "tlo.json").is_file())
        self.assertTrue((pkg / "composition" / "ig-post.html").is_file())
        self.assertTrue((pkg / "brief.md").is_file())
        self.assertFalse((pkg / "drafts").exists())
        self.assertFalse((pkg / "final").exists())
        readme = (pkg / "README.md").read_text(encoding="utf-8")
        self.assertIn("w toku", readme)
        self.assertIn("tło ze zdjęcia", readme)
        # ponowne udostępnienie aktualizuje pakiet
        (job / "brief.md").write_text("nowy brief", encoding="utf-8")
        self.assertEqual(run("share", "--job", job, "--repo", self.repo)[0], 0)
        self.assertEqual((pkg / "brief.md").read_text(encoding="utf-8"), "nowy brief")

    def test_share_refuses_finalized(self):
        job = self.job_with_layer()
        pkg = self.pkg(job)
        (pkg / "final").mkdir(parents=True)
        code, out = run("share", "--job", job, "--repo", self.repo)
        self.assertEqual(code, 1, out)
        self.assertIn("--replace", out)
        self.assertEqual(run("share", "--job", job, "--repo", self.repo, "--replace")[0], 0)

    def test_finalize_requires_final_files(self):
        job = self.job_with_layer("ig-post,a4-print")
        (job / "final" / "ig-post.png").write_bytes(b"x")
        code, out = run("finalize", "--job", job, "--repo", self.repo, "--approved-by", "Ala")
        self.assertEqual(code, 1, out)
        self.assertIn("a4-print.png", out)
        self.assertIn("a4-print.pdf", out)
        self.assertNotIn("Traceback", out)
        self.assertFalse(self.pkg(job).exists())

    def test_adopt_keeps_layers_frozen(self):
        job = self.job_with_layer()
        self.assertEqual(run("share", "--job", job, "--repo", self.repo)[0], 0)
        pkg = self.pkg(job)
        code, out = run("adopt", "--package", pkg)
        self.assertEqual(code, 0, out)
        new = Path(out.split("JOB:", 1)[1].strip().splitlines()[0])
        self.assertNotEqual(new, job)
        self.assertEqual(new.parent.name, "kiwi-studio")
        meta = json.loads((new / "layers" / "tlo.json").read_text(encoding="utf-8"))
        self.assertTrue(meta["frozen"])
        data = json.loads((new / "job.json").read_text(encoding="utf-8"))
        self.assertEqual(data["formats"], ["ig-post"])
        self.assertEqual(data["brand"], str((self.repo / "brand").resolve()))
        self.assertTrue((new / "composition" / "ig-post.html").is_file())
        self.assertEqual(run("status", "--job", new)[0], 0)
        self.assertNotIn("PROBLEM", run("status", "--job", new)[1])

    def test_adopt_is_chosen_direct_at_stages(self):
        job = self.job_with_layer()
        self.assertEqual(run("share", "--job", job, "--repo", self.repo)[0], 0)
        code, out = run("adopt", "--package", self.pkg(job))
        self.assertEqual(code, 0, out)
        new = Path(out.split("JOB:", 1)[1].strip().splitlines()[0])
        data = json.loads((new / "job.json").read_text(encoding="utf-8"))
        self.assertEqual((data["stage"], data["chosen"]), ("stages", "direct"))

    def test_adopt_detects_changed_layer(self):
        job = self.job_with_layer()
        self.assertEqual(run("share", "--job", job, "--repo", self.repo)[0], 0)
        pkg = self.pkg(job)
        (pkg / "layers" / "tlo.png").write_bytes(b"zmienione")
        code, out = run("adopt", "--package", pkg)
        self.assertEqual(code, 1, out)
        self.assertIn("tlo", out)
        self.assertNotIn("Traceback", out)


@unittest.skipUnless(has_browser(), "brak przeglądarki")
class Finalize(PackageCase):
    def test_finalize_layout_and_readme(self):
        job = self.finalized()
        pkg = self.pkg(job)
        for p in ("final/ig-post.png", "layers/tlo.png", "layers/tlo.json",
                  "composition/ig-post.html", "brief.md", "README.md"):
            self.assertTrue((pkg / p).is_file(), p)
        self.assertFalse((pkg / "drafts").exists())
        readme = (pkg / "README.md").read_text(encoding="utf-8")
        self.assertIn("Ala", readme)
        self.assertIn("1080×1350", readme)
        self.assertIn("Kiwi Studio", readme)
        self.assertIn("wersja 3", readme)
        self.assertIn("tło ze zdjęcia", readme)
        self.assertNotIn("w toku", readme)
        self.assertEqual(json.loads((job / "job.json").read_text(encoding="utf-8"))["stage"], "final")

    def test_finalize_copies_only_job_formats(self):
        job = self.job_with_layer()
        self.assertEqual(run("render", "--job", job)[0], 0)
        (job / "final" / "ig-story.png").write_bytes(b"obcy")
        code, out = run("finalize", "--job", job, "--repo", self.repo, "--approved-by", "Ala")
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(p.name for p in (self.pkg(job) / "final").iterdir()), ["ig-post.png"])

    def test_finalize_refuses_existing(self):
        job = self.finalized()
        pkg = self.pkg(job)
        before = (pkg / "README.md").read_bytes()
        code, out = run("finalize", "--job", job, "--repo", self.repo, "--approved-by", "Basia")
        self.assertEqual(code, 1, out)
        self.assertIn("--replace", out)
        self.assertEqual((pkg / "README.md").read_bytes(), before)
        code, out = run("finalize", "--job", job, "--repo", self.repo, "--approved-by", "Basia",
                        "--replace")
        self.assertEqual(code, 0, out)
        self.assertIn("Basia", (pkg / "README.md").read_text(encoding="utf-8"))

    def test_finalize_blocked_without_process_then_allowed(self):
        job = self.job_with_layer(ready=False)
        self.assertEqual(run("render", "--job", job)[0], 0)
        args = ("finalize", "--job", job, "--repo", self.repo, "--approved-by", "Ala")
        code, out = run(*args)
        self.assertEqual(code, 1, out)
        self.assertIn("process", out)
        self.assertIn("choose", out)
        self.assertIn("brief.md", out)
        self.assertFalse(self.pkg(job).exists())
        self.make_ready(job)
        code, out = run(*args)
        self.assertEqual(code, 0, out)

    def test_finalize_accept_problems_covers_process(self):
        job = self.job_with_layer(ready=False)
        self.assertEqual(run("render", "--job", job)[0], 0)
        code, out = run("finalize", "--job", job, "--repo", self.repo, "--approved-by", "Ala",
                        "--accept-problems")
        self.assertEqual(code, 0, out)
        self.assertIn("process", (self.pkg(job) / "README.md").read_text(encoding="utf-8"))

    def test_finalize_requires_clean_check(self):
        job = self.job_with_layer(body=BAD)
        self.assertEqual(run("render", "--job", job)[0], 0)
        code, out = run("finalize", "--job", job, "--repo", self.repo, "--approved-by", "Ala")
        self.assertEqual(code, 1, out)
        self.assertIn("contrast", out)
        self.assertFalse(self.pkg(job).exists())
        code, out = run("finalize", "--job", job, "--repo", self.repo, "--approved-by", "Ala",
                        "--accept-problems")
        self.assertEqual(code, 0, out)
        readme = (self.pkg(job) / "README.md").read_text(encoding="utf-8")
        self.assertIn("Zaakceptowane problemy", readme)
        self.assertIn("contrast", readme)

    def test_rerender_from_package_is_identical(self):
        job = self.finalized()
        pkg = self.pkg(job)
        code, out = run("adopt", "--package", pkg)
        self.assertEqual(code, 0, out)
        new = Path(out.split("JOB:", 1)[1].strip().splitlines()[0])
        self.assertEqual(run("render", "--job", new)[0], 0)
        a = png.read(pkg / "final" / "ig-post.png")
        b = png.read(new / "final" / "ig-post.png")
        self.assertEqual((a.width, a.height, a.channels), (b.width, b.height, b.channels))
        total = a.width * a.height * a.channels
        same = 0
        c = a.channels
        for ra, rb in zip(a.rows, b.rows):
            if ra == rb:
                same += len(ra) // c
                continue
            for i in range(0, len(ra), c):
                if max(abs(ra[i + k] - rb[i + k]) for k in range(c)) <= 2:
                    same += 1
        self.assertGreaterEqual(same / (total // c), 0.995)


if __name__ == "__main__":
    unittest.main()
