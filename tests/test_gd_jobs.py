"""Testy zleceń: biblioteka, new, draft, freeze, verify_layers, status."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "graphic-designer"
sys.path.insert(0, str(PLUGIN / "scripts"))

import designer  # noqa: E402
from gd import jobs  # noqa: E402
from gd.common import GdError  # noqa: E402

KIWI = REPO / "tests" / "fixture" / "graphic-designer" / "kiwi"


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = designer.main([str(a) for a in args])
    return code, out.getvalue() + err.getvalue()


def job_of(out):
    return Path(out.split("JOB:", 1)[1].strip().splitlines()[0])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Env(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)
        self.old_home = os.environ.get("GD_HOME")
        os.environ["GD_HOME"] = str(self.tmp / "home")
        self.addCleanup(self._restore)
        self.lib = self.tmp / "Grafiki robocze ł"
        self.png = self.tmp / "a.png"
        self.png.write_bytes(b"\x89PNG-fake-1")

    def _restore(self):
        if self.old_home is None:
            os.environ.pop("GD_HOME", None)
        else:
            os.environ["GD_HOME"] = self.old_home

    def chdir(self, path):
        cwd = os.getcwd()
        os.chdir(path)
        self.addCleanup(os.chdir, cwd)

    def set_lib(self):
        self.assertEqual(run("library", "--set", self.lib)[0], 0)

    def new_job(self, title="Plakat ślub 14.03", formats="ig-post"):
        self.set_lib()
        code, out = run("new", "--title", title, "--formats", formats, "--brand", KIWI / "brand")
        self.assertEqual(code, 0, out)
        return job_of(out)


REAL_BRIEF = """# Brief zlecenia

## Cel
Zachęcić do zapisu na warsztaty ceramiki w sobotę wieczorem.

## Odbiorca
Mieszkańcy dzielnicy, Instagram, post 4:5.

## Teksty dosłowne
- Nagłówek: Wieczór z gliną
- Data i godzina: sobota, 18.00
"""


class TestProcess(Env):
    """Bramki procesu: kierunki, `choose`, etapy, status, `check`."""

    def data(self, job):
        return json.loads((job / "job.json").read_text(encoding="utf-8"))

    def draft(self, job, direction="A"):
        code, out = run("draft", "--job", job, "--file", self.png, "--direction", direction,
                        "--note", "szkic")
        self.assertEqual(code, 0, out)

    def test_draft_records_direction_and_moves_stage(self):
        job = self.new_job()
        self.assertEqual(self.data(job)["stage"], "brief")
        self.draft(job, "A")
        d = self.data(job)
        self.assertEqual(d["stage"], "directions")
        self.assertIn("A", d["directions"])
        self.draft(job, "B")
        self.draft(job, "A")
        d = self.data(job)
        self.assertEqual(sorted(d["directions"]), ["A", "B"])
        self.assertEqual(d["stage"], "directions")
        self.assertIsNone(d["chosen"])

    def test_choose_direction_ok(self):
        job = self.new_job()
        self.draft(job, "A")
        self.draft(job, "B")
        code, out = run("choose", "--job", job.name, "--direction", "B")
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("OK:"), out)
        d = self.data(job)
        self.assertEqual((d["chosen"], d["stage"]), ("B", "stages"))

    def test_choose_direction_is_case_insensitive(self):
        job = self.new_job()
        self.draft(job, "A")
        self.assertEqual(run("choose", "--job", job, "--direction", "a")[0], 0)
        self.assertEqual(self.data(job)["chosen"], "A")

    def test_choose_unknown_direction(self):
        job = self.new_job()
        self.draft(job, "A")
        code, out = run("choose", "--job", job, "--direction", "C")
        self.assertEqual(code, 1, out)
        self.assertIn("PROBLEM", out)
        self.assertIn("C", out)
        self.assertIn("draft --direction", out)
        self.assertNotIn("Traceback", out)
        d = self.data(job)
        self.assertEqual((d["chosen"], d["stage"]), (None, "directions"))

    def test_choose_direction_without_any_draft(self):
        job = self.new_job()
        code, out = run("choose", "--job", job, "--direction", "A")
        self.assertEqual(code, 1, out)
        self.assertIn("draft --direction", out)
        self.assertIn("--direct", out)

    def test_choose_direct(self):
        job = self.new_job()
        code, out = run("choose", "--job", job, "--direct")
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("OK:"), out)
        d = self.data(job)
        self.assertEqual((d["chosen"], d["stage"]), ("direct", "stages"))

    def test_choose_needs_exactly_one_option(self):
        job = self.new_job()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                run("choose", "--job", job)
            with self.assertRaises(SystemExit):
                run("choose", "--job", job, "--direct", "--direction", "A")

    def test_stage_never_goes_back(self):
        job = self.new_job()
        self.assertEqual(run("choose", "--job", job, "--direct")[0], 0)
        self.draft(job, "A")
        self.assertEqual(self.data(job)["stage"], "stages")
        jobs.advance(job, "composition")
        jobs.advance(job, "stages")
        self.assertEqual(self.data(job)["stage"], "composition")

    def test_status_shows_stage_and_next_step(self):
        job = self.new_job()
        code, out = run("status", "--job", job.name)
        self.assertIn("etap: brief → dopytaj o brief", out)
        self.draft(job, "A")
        self.assertIn("etap: directions → pokaż kierunki i poczekaj na wybór", run("status")[1])
        run("choose", "--job", job, "--direct")
        self.assertIn("etap: stages → dopracuj etapami", run("status", "--job", job.name)[1])

    def check_out(self, job):
        code, out = run("check", "--job", job)
        return code, [l for l in out.splitlines() if "] process:" in l]

    def test_check_fails_without_brief(self):
        job = self.new_job()
        run("choose", "--job", job, "--direct")
        code, lines = self.check_out(job)
        self.assertEqual(code, 3)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("brief.md", lines[0])
        self.assertIn("[-] process:", lines[0])

    def test_check_fails_when_brief_is_only_a_few_words(self):
        job = self.new_job()
        run("choose", "--job", job, "--direct")
        (job / "brief.md").write_text("# Brief\n\n## Cel\nPost\n- Nagłówek: Hej\n", encoding="utf-8")
        self.assertEqual(len(self.check_out(job)[1]), 1)

    def test_check_fails_without_choose(self):
        job = self.new_job()
        (job / "brief.md").write_text(REAL_BRIEF, encoding="utf-8")
        code, lines = self.check_out(job)
        self.assertEqual(code, 3)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("choose", lines[0])
        self.assertIn("choose --direct", lines[0])

    def test_check_process_passes_after_brief_and_choose(self):
        job = self.new_job()
        self.draft(job, "A")
        (job / "brief.md").write_text(REAL_BRIEF, encoding="utf-8")
        self.assertEqual(run("choose", "--job", job, "--direction", "A")[0], 0)
        code, lines = self.check_out(job)
        self.assertEqual(lines, [])

    def test_unfilled_template_brief_fails(self):
        job = self.new_job()
        self.assertFalse(jobs.brief_filled(job))
        (job / "brief.md").write_text(REAL_BRIEF, encoding="utf-8")
        self.assertTrue(jobs.brief_filled(job))
        (job / "brief.md").unlink()
        self.assertFalse(jobs.brief_filled(job))


class TestLibrary(Env):
    def test_library_set_and_get(self):
        code, out = run("library", "--set", self.lib)
        self.assertEqual(code, 0)
        self.assertIn("LIBRARY:", out)
        self.assertTrue(self.lib.is_dir())
        code, out = run("library")
        self.assertTrue(out.startswith("LIBRARY:"), out)
        self.assertIn("Grafiki robocze ł", out)
        self.assertEqual(jobs.library(), self.lib)

    def test_library_not_set(self):
        code, out = run("library")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("NOT SET"), out)

    def test_library_missing(self):
        self.set_lib()
        self.lib.rmdir()
        code, out = run("library")
        self.assertTrue(out.startswith("MISSING"), out)


class TestNew(Env):
    def test_new_job_layout(self):
        job = self.new_job()
        self.assertEqual(job, self.lib / "kiwi-studio" / "plakat-slub-14-03")
        data = json.loads((job / "job.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["title"], "Plakat ślub 14.03")
        self.assertEqual(data["project"], "kiwi-studio")
        self.assertEqual(data["formats"], ["ig-post"])
        self.assertEqual(data["stage"], "brief")
        self.assertEqual(data["brand"], str((KIWI / "brand").resolve()))
        template = PLUGIN / "skills" / "graphic-designer" / "references" / "brief.md"
        self.assertEqual((job / "brief.md").read_text(encoding="utf-8"),
                         template.read_text(encoding="utf-8"))
        for d in ("drafts", "layers", "composition", "final"):
            self.assertTrue((job / d).is_dir(), d)

    def test_collision_gets_suffix(self):
        first = self.new_job()
        code, out = run("new", "--title", "Plakat ślub 14.03", "--formats", "ig-post", "--brand", KIWI / "brand")
        self.assertEqual(code, 0)
        self.assertTrue(job_of(out).name == first.name + "-2")

    def test_no_brand_project(self):
        self.set_lib()
        self.chdir(self.tmp)
        code, out = run("new", "--title", "Test", "--formats", "ig-post")
        self.assertEqual(code, 0, out)
        self.assertEqual(job_of(out).parent.name, "bez-marki")
        code, out = run("new", "--title", "Inny", "--formats", "ig-post",
                        "--project", "Wesele Ani")
        self.assertEqual(job_of(out).parent.name, "wesele-ani")

    def test_explicit_brand_not_found(self):
        self.set_lib()
        code, out = run("new", "--title", "X", "--formats", "ig-post", "--brand", self.tmp)
        self.assertEqual(code, 1)
        self.assertIn("PROBLEM:", out)

    def test_unknown_format_lists_known(self):
        self.set_lib()
        code, out = run("new", "--title", "X", "--formats", "ig-post,nie-ma")
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("PROBLEM:"), out)
        self.assertIn("nie-ma", out)
        for fid in ("ig-post", "ig-square", "ig-story", "fb-event", "a4-print", "a3-print"):
            self.assertIn(fid, out)

    def test_new_without_library(self):
        code, out = run("new", "--title", "X", "--formats", "ig-post")
        self.assertEqual(code, 1)
        self.assertIn("library", out)

    def test_set_brand_updates_job(self):
        self.set_lib()
        self.chdir(self.tmp)
        code, out = run("new", "--title", "Bez marki", "--formats", "ig-post")
        job = job_of(out)
        self.assertIsNone(jobs.load(job)["brand"])
        code, out = run("set-brand", "--job", job, "--brand", KIWI)
        self.assertEqual(code, 0, out)
        self.assertEqual(jobs.load(job)["brand"], str((KIWI / "brand").resolve()))
        # po slugu
        code, out = run("set-brand", "--job", job.name, "--brand", self.tmp)
        self.assertEqual(code, 1)
        self.assertIn("PROBLEM:", out)


class TestJobLookup(Env):
    def test_job_by_slug_and_ambiguity(self):
        job = self.new_job()
        self.assertEqual(jobs.job_dir(job.name), job)
        other = self.lib / "inny" / job.name
        other.mkdir(parents=True)
        (other / "job.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(GdError) as cm:
            jobs.job_dir(job.name)
        self.assertIn("inny", str(cm.exception))
        self.assertIn("kiwi-studio", str(cm.exception))
        self.assertEqual(jobs.job_dir(str(job)), job)

    def test_missing_job(self):
        self.set_lib()
        with self.assertRaises(GdError):
            jobs.job_dir("nie-ma")


class TestDraft(Env):
    def test_draft_versions(self):
        job = self.new_job()
        for _ in range(2):
            code, out = run("draft", "--job", job.name, "--file", self.png, "--direction", "A", "--note", "pierwszy")
            self.assertEqual(code, 0, out)
        self.assertTrue((job / "drafts" / "A-v1.png").is_file())
        self.assertTrue((job / "drafts" / "A-v2.png").is_file())
        meta = json.loads((job / "drafts" / "A-v2.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["direction"], "A")
        self.assertEqual(meta["version"], 2)
        self.assertEqual(meta["note"], "pierwszy")
        self.assertTrue(self.png.is_file())

    def test_draft_missing_file(self):
        job = self.new_job()
        code, out = run("draft", "--job", job.name, "--file", self.tmp / "nie.png", "--direction", "A", "--note", "x")
        self.assertEqual(code, 1)


class TestFreeze(Env):
    def freeze(self, job, name="background", extra=()):
        return run("freeze", "--job", job.name, "--name", name, "--file", self.png,
                   "--source", "generated", "--approved-by", "Ola", *extra)

    def test_freeze_copies_with_sha(self):
        job = self.new_job()
        code, out = self.freeze(job, extra=("--prompt", "las", "--inputs", "a,b", "--note", "ok"))
        self.assertEqual(code, 0, out)
        layer = job / "layers" / "background.png"
        self.assertEqual(layer.read_bytes(), self.png.read_bytes())
        self.assertTrue(self.png.is_file())
        meta = json.loads((job / "layers" / "background.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["sha256"], sha(layer))
        self.assertEqual(meta["file"], "background.png")
        self.assertTrue(meta["frozen"])
        self.assertEqual(meta["inputs"], ["a", "b"])
        self.assertEqual(meta["approved_by"], "Ola")

    def test_freeze_refuses_overwrite(self):
        job = self.new_job()
        self.freeze(job)
        before = sha(job / "layers" / "background.png")
        self.png.write_bytes(b"\x89PNG-fake-2")
        code, out = self.freeze(job)
        self.assertEqual(code, 1)
        self.assertIn("background-v2", out)
        self.assertEqual(sha(job / "layers" / "background.png"), before)
        code, out = self.freeze(job, extra=("--replace",))
        self.assertEqual(code, 0, out)
        self.assertNotEqual(sha(job / "layers" / "background.png"), before)

    def test_freeze_case_variant_refused(self):
        job = self.new_job()
        self.freeze(job)
        before = sha(job / "layers" / "background.png")
        self.png.write_bytes(b"\x89PNG-other")
        code, out = self.freeze(job, name="Background")
        self.assertEqual(code, 1)
        self.assertEqual(sha(job / "layers" / "background.png"), before)

    def test_draft_case_variant_does_not_overwrite(self):
        job = self.new_job()
        run("draft", "--job", job.name, "--file", self.png, "--direction", "A", "--note", "x")
        before = sha(job / "drafts" / "A-v1.png")
        self.png.write_bytes(b"\x89PNG-other")
        run("draft", "--job", job.name, "--file", self.png, "--direction", "a", "--note", "x")
        self.assertEqual(sha(job / "drafts" / "A-v1.png"), before)
        self.assertEqual(len(list((job / "drafts").glob("*.png"))), 2)

    def test_replace_from_the_layer_itself_keeps_it(self):
        job = self.new_job()
        self.freeze(job)
        layer = job / "layers" / "background.png"
        before = sha(layer)
        code, out = run("freeze", "--job", job.name, "--name", "background", "--file", layer,
                        "--source", "generated", "--approved-by", "Ola", "--replace")
        self.assertEqual(code, 0, out)
        self.assertEqual(sha(layer), before)
        meta = json.loads((job / "layers" / "background.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["sha256"], before)
        self.assertEqual([p.name for p in (job / "layers").iterdir() if p.name.startswith(".")], [])

    def test_extensionless_and_json_sources_refused(self):
        job = self.new_job()
        for name in ("plik", "plik.json"):
            f = self.tmp / name
            f.write_bytes(b"x")
            code, out = self.freeze_file(job, f)
            self.assertEqual(code, 1, out)
            code, out = run("draft", "--job", job.name, "--file", f, "--direction", "A", "--note", "x")
            self.assertEqual(code, 1, out)

    def freeze_file(self, job, f):
        return run("freeze", "--job", job.name, "--name", "x", "--file", f,
                   "--source", "generated", "--approved-by", "Ola")

    def test_freeze_bad_source(self):
        job = self.new_job()
        code, out = run("freeze", "--job", job.name, "--name", "x", "--file", self.png,
                        "--source", "magia", "--approved-by", "Ola")
        self.assertEqual(code, 1)
        self.assertIn("generated", out)

    def test_verify_layers_detects_change(self):
        job = self.new_job()
        self.freeze(job)
        self.freeze(job, name="foto")
        self.assertEqual(jobs.verify_layers(job), [])
        p = job / "layers" / "background.png"
        p.write_bytes(p.read_bytes() + b"x")
        (job / "layers" / "foto.png").unlink()
        self.assertEqual(jobs.verify_layers(job), ["background", "foto"])

class TestRelativeFile(Env):
    def test_freeze_accepts_path_relative_to_job(self):
        job = self.new_job()
        self.assertEqual(run("draft", "--job", job.name, "--file", self.png,
                             "--direction", "A", "--note", "x")[0], 0)
        elsewhere = self.tmp / "gdzie-indziej"
        elsewhere.mkdir()
        cwd = os.getcwd()
        os.chdir(elsewhere)
        self.addCleanup(os.chdir, cwd)
        code, out = run("freeze", "--job", job.name, "--name", "tlo", "--file", "drafts/A-v1.png",
                        "--source", "generated", "--approved-by", "Ola")
        self.assertEqual(code, 0, out)
        self.assertTrue((job / "layers" / "tlo.png").is_file())
        code, out = run("freeze", "--job", job.name, "--name", "inna", "--file", "drafts/nie-ma.png",
                        "--source", "generated", "--approved-by", "Ola")
        self.assertEqual(code, 1)


class TestStatus(Env):
    def test_status_lists_jobs_and_repo_packages(self):
        job = self.new_job(formats="ig-post,ig-story")
        run("freeze", "--job", job.name, "--name", "bg", "--file", self.png,
            "--source", "photo", "--approved-by", "Ola")
        repo = self.tmp / "repo"
        (repo / "graphics" / "2026-11-w-toku").mkdir(parents=True)
        (repo / "graphics" / "2026-10-gotowe" / "final").mkdir(parents=True)
        (repo / "src").mkdir()
        cwd = os.getcwd()
        os.chdir(repo / "src")
        self.addCleanup(os.chdir, cwd)
        code, out = run("status")
        self.assertEqual(code, 0, out)
        self.assertIn("Plakat ślub 14.03", out)
        self.assertIn("brief", out)
        self.assertIn("ig-post", out)
        self.assertIn("ig-story", out)
        self.assertIn("2026-11-w-toku", out)
        self.assertNotIn("2026-10-gotowe", out)
        code, out = run("status", "--job", job.name)
        self.assertEqual(code, 0, out)
        self.assertIn("Plakat ślub 14.03", out)

    def test_status_nothing(self):
        code, out = run("status")
        self.assertEqual(code, 0, out)
        self.assertIn("NOT SET", out)


class TestStatusCorrupt(Env):
    def test_corrupt_job_json_does_not_break_status(self):
        good = self.new_job("Dobre zlecenie")
        bad = self.new_job("Zepsute zlecenie")
        (bad / "job.json").write_text("{nie json", encoding="utf-8")
        code, out = run("status")
        self.assertEqual(code, 0, out)
        self.assertIn("Dobre zlecenie", out)
        self.assertIn(f"{bad.parent.name}/{bad.name}: PROBLEM: nie mogę odczytać job.json", out)
        self.assertNotIn("Traceback", out)
        self.assertTrue(good.is_dir())

if __name__ == "__main__":
    unittest.main()
