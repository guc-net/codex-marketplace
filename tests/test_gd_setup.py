"""Testy konfiguracji: stały skrypt startowy, reguły Codexa, doctor."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "graphic-designer"
sys.path.insert(0, str(PLUGIN / "scripts"))

import designer  # noqa: E402
from gd import browser, onboard  # noqa: E402
from gd.common import GdError  # noqa: E402

TEMPLATE = PLUGIN / "templates" / "launcher.py"
WINDOWS = os.name == "nt"


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = designer.main([str(a) for a in args])
    return code, out.getvalue() + err.getvalue()


def put(path, text):
    """Zapis bajtów: na Windows `write_text` zamieniłby \n na \r\n i zepsuł porównania."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def esc(path):
    """Ścieżka tak, jak stoi w literale reguły (z ucieczką ukośników, także na Windows)."""
    return onboard.starlark_string(str(path))[1:-1]


class Sandboxed(unittest.TestCase):
    """Fałszywe CODEX_HOME i GD_HOME w katalogu tymczasowym; żadnych dotknięć prawdziwego domu."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.codex_home = self.tmp / "codex"
        self.gd_home = self.tmp / "gdhome"
        patcher = mock.patch.dict(os.environ, {"CODEX_HOME": str(self.codex_home),
                                               "GD_HOME": str(self.gd_home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        for key in ("GD_PLUGIN_ROOT", "CODEX_SANDBOX", "GD_BROWSER_TRY", "OPENAI_API_KEY",
                    "GD_UPDATE_SOURCE"):
            os.environ.pop(key, None)

    @property
    def launcher(self):
        return self.codex_home / "graphic-designer" / "designer.py"

    @property
    def legacy_launcher(self):
        return self.gd_home / "designer.py"

    @property
    def rules_file(self):
        return self.codex_home / "rules" / "default.rules"

    @property
    def backup_file(self):
        return self.codex_home / "rules" / "default.rules.graphic-designer.bak"

    def install_launcher(self):
        code, out = run("setup-launcher")
        self.assertEqual(code, 0, out)

    def fake_plugin(self, version, marketplace="guc-net", with_script=True, name="graphic-designer",
                    manifest=True):
        root = self.codex_home / "plugins" / "cache" / marketplace / "graphic-designer" / version
        (root / "scripts").mkdir(parents=True)
        if with_script:
            (root / "scripts" / "designer.py").write_text(
                "import sys\nprint('FAKE', %r, sys.argv[0], *sys.argv[1:])\n"
                "sys.exit(int(__import__('os').environ.get('FAKE_EXIT', '0')))\n" % version,
                encoding="utf-8")
        if manifest:
            (root / "plugin.json").write_text(json.dumps({"name": name, "version": version}),
                                              encoding="utf-8")
        return root


def load_launcher():
    spec = importlib.util.spec_from_file_location("gd_launcher_under_test", TEMPLATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LauncherFinding(Sandboxed):
    def picked(self):
        return load_launcher().find_designer().parent.parent.name

    def test_template_exists_and_is_stdlib_only(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("from __future__ import annotations", text)
        self.assertIn("runpy", text)
        self.assertIn(onboard.LAUNCHER_MARKER, text)
        imports = set(re.findall(r"^(?:import|from) ([\w.]+)", text, re.M))
        self.assertTrue(imports <= {"__future__", "json", "os", "re", "runpy", "sys", "pathlib"}, imports)

    def test_picks_highest_version_numerically(self):
        for v in ("0.2.0", "0.10.0", "0.9.5"):
            self.fake_plugin(v)
        self.assertEqual(self.picked(), "0.10.0")

    def test_other_marketplaces_are_ignored(self):
        self.fake_plugin("0.2.0", "guc-net")
        self.fake_plugin("9.9.9", "inny-katalog")
        self.assertEqual(self.picked(), "0.2.0")

    def test_only_a_foreign_marketplace_is_not_enough(self):
        self.fake_plugin("1.0.0", "inny-katalog")
        with self.assertRaises(LookupError):
            load_launcher().find_designer()

    def test_only_plain_releases_are_considered(self):
        self.fake_plugin("0.2.0")
        for junk in ("0.3.0-beta.1", "0.3.0.old", "v0.3.0", "backup-2025", "0.3", "1.0.0-rc1", "2025",
                     "0.3.0 "):
            self.fake_plugin(junk)
        self.assertEqual(self.picked(), "0.2.0")

    def test_prerelease_does_not_beat_the_release(self):
        self.fake_plugin("0.2.0")
        self.fake_plugin("0.2.0-beta.1")
        self.assertEqual(self.picked(), "0.2.0")

    def test_junk_alone_is_not_accepted(self):
        for junk in ("0.2.0-beta.1", "0.2.0.old", "backup-2025", "abc"):
            self.fake_plugin(junk)
        with self.assertRaises(LookupError):
            load_launcher().find_designer()

    def test_plugin_json_must_name_graphic_designer(self):
        self.fake_plugin("0.2.0")
        self.fake_plugin("0.3.0", name="inny-plugin")
        self.fake_plugin("0.4.0", manifest=False)
        broken = self.fake_plugin("0.5.0", manifest=False)
        (broken / "plugin.json").write_text("{nie json", encoding="utf-8")
        listed = self.fake_plugin("0.6.0", manifest=False)
        (listed / "plugin.json").write_text("[1, 2]", encoding="utf-8")
        self.assertEqual(self.picked(), "0.2.0")

    def test_ignores_versions_without_script(self):
        self.fake_plugin("0.2.0")
        self.fake_plugin("0.9.0", with_script=False)
        self.assertEqual(self.picked(), "0.2.0")

    def test_plugin_root_variable_no_longer_redirects(self):
        other = self.tmp / "inny-plugin"
        (other / "scripts").mkdir(parents=True)
        (other / "scripts" / "designer.py").write_text("print('x')\n", encoding="utf-8")
        (other / "plugin.json").write_text(json.dumps({"name": "graphic-designer"}), encoding="utf-8")
        os.environ["GD_PLUGIN_ROOT"] = str(other)
        with self.assertRaises(LookupError):
            load_launcher().find_designer()
        self.assertNotIn("GD_PLUGIN_ROOT", TEMPLATE.read_text(encoding="utf-8"))

    def test_nothing_found_explains_how_to_install(self):
        with self.assertRaises(LookupError) as cm:
            load_launcher().find_designer()
        msg = str(cm.exception)
        self.assertIn("nie znalazłem", msg)
        self.assertIn("codex plugin add graphic-designer@guc-net", msg)
        self.assertIn(str(self.codex_home), msg)

    def test_codex_home_defaults_to_dot_codex(self):
        os.environ.pop("CODEX_HOME")
        self.assertEqual(load_launcher().cache_dir(), Path.home() / ".codex" / "plugins" / "cache")


class LauncherProcess(Sandboxed):
    def start(self, *args, **extra):
        self.install_launcher()
        env = dict(os.environ)
        env.update(extra)
        proc = subprocess.run([sys.executable, str(self.launcher)] + list(args), env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def test_runs_the_highest_version_with_arguments_and_argv0(self):
        self.fake_plugin("0.2.0")
        root = self.fake_plugin("0.10.0")
        code, out, _ = self.start("render", "--job", "a")
        self.assertEqual(code, 0)
        self.assertIn("FAKE 0.10.0", out)
        self.assertIn(str(root / "scripts" / "designer.py"), out)
        self.assertTrue(out.strip().endswith("render --job a"), out)

    def test_exit_code_is_passed_through(self):
        self.fake_plugin("0.2.0")
        code, _, _ = self.start("x", FAKE_EXIT="3")
        self.assertEqual(code, 3)

    def test_no_plugin_exits_1_with_polish_message_and_no_traceback(self):
        code, out, err = self.start("version")
        self.assertEqual(code, 1)
        self.assertIn("PROBLEM:", out + err)
        self.assertIn("nie znalazłem", out + err)
        self.assertNotIn("Traceback", out + err)

    def test_runs_the_real_designer_from_a_cache_tree(self):
        root = self.codex_home / "plugins" / "cache" / "guc-net" / "graphic-designer" / "9.9.9"
        shutil.copytree(PLUGIN, root, ignore=shutil.ignore_patterns("__pycache__"))
        code, out, err = self.start("version")
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), manifest["version"])


class SetupLauncher(Sandboxed):
    def test_installs_the_template_in_the_codex_folder_and_prints_the_absolute_path(self):
        code, out = run("setup-launcher")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.launcher.read_bytes(), TEMPLATE.read_bytes())
        self.assertEqual(self.launcher, self.codex_home / "graphic-designer" / "designer.py")
        self.assertIn(str(self.launcher), out)
        self.assertTrue(self.launcher.is_absolute())
        self.assertIn("OK:", out)
        self.assertFalse(self.legacy_launcher.exists())

    def test_is_idempotent(self):
        run("setup-launcher")
        before = self.launcher.stat().st_mtime_ns
        code, out = run("setup-launcher")
        self.assertEqual(code, 0)
        self.assertIn("aktualny", out)
        self.assertIn(str(self.launcher), out)
        self.assertEqual(self.launcher.stat().st_mtime_ns, before)

    def test_updates_a_stale_launcher(self):
        put(self.launcher, "# stary\n")
        code, out = run("setup-launcher")
        self.assertEqual(code, 0)
        self.assertIn("zaktualizowano", out)
        self.assertEqual(self.launcher.read_bytes(), TEMPLATE.read_bytes())

    @unittest.skipIf(WINDOWS, "bit wykonywalny dotyczy systemów uniksowych")
    def test_launcher_is_executable(self):
        run("setup-launcher")
        self.assertTrue(os.access(self.launcher, os.X_OK))

    def test_default_location_without_codex_home(self):
        os.environ.pop("CODEX_HOME")
        self.assertEqual(onboard.launcher_path(), Path.home() / ".codex" / "graphic-designer" / "designer.py")

    def test_settings_stay_in_gd_home(self):
        run("setup-launcher")
        run("library", "--set", self.tmp / "grafiki")
        self.assertTrue((self.gd_home / "settings.json").is_file())
        self.assertFalse((self.codex_home / "settings.json").exists())
        self.assertEqual(sorted(p.name for p in self.codex_home.iterdir()), ["graphic-designer"])

    def test_our_launcher_in_the_old_place_is_removed(self):
        put(self.legacy_launcher, TEMPLATE.read_text(encoding="utf-8"))
        code, out = run("setup-launcher")
        self.assertEqual(code, 0, out)
        self.assertFalse(self.legacy_launcher.exists())
        self.assertIn("usunięto dawny plik", out)
        self.assertTrue(self.launcher.is_file())

    def test_old_launcher_is_removed_even_when_the_new_one_is_current(self):
        run("setup-launcher")
        put(self.legacy_launcher, "#!/usr/bin/env python3\n\"\"\"" + onboard.LAUNCHER_MARKER + ".\"\"\"\n")
        code, out = run("setup-launcher")
        self.assertIn("aktualny", out)
        self.assertIn("usunięto dawny plik", out)
        self.assertFalse(self.legacy_launcher.exists())

    def test_a_foreign_file_in_the_old_place_is_left_alone(self):
        put(self.legacy_launcher, "# to jest mój własny skrypt\n")
        code, out = run("setup-launcher")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.legacy_launcher.read_bytes(), "# to jest mój własny skrypt\n".encode("utf-8"))
        self.assertIn("UWAGA", out)
        self.assertIn("nie ruszam", out)

    def test_warns_when_the_rules_still_trust_the_old_file(self):
        put(self.legacy_launcher, TEMPLATE.read_text(encoding="utf-8"))
        put(self.rules_file, onboard.rules_block(self.legacy_launcher))
        code, out = run("setup-launcher")
        self.assertEqual(code, 0, out)
        self.assertIn("reguły Codexa nadal ufają", out)
        self.assertIn("setup-rules --apply", out)

    def test_no_rules_warning_when_nothing_trusts_the_old_file(self):
        put(self.legacy_launcher, TEMPLATE.read_text(encoding="utf-8"))
        code, out = run("setup-launcher")
        self.assertNotIn("reguły Codexa nadal ufają", out)


class RulesBlock(Sandboxed):
    RULE = re.compile(r'^prefix_rule\(pattern=\["python3", ".*", "([a-z-]+)"\], decision="allow"\)$')
    WINDOWS_PATH = r"C:\Users\Ala Kowalska\.codex\graphic-designer\designer.py"

    def test_block_shape(self):
        block = onboard.rules_block(self.launcher)
        lines = block.splitlines()
        self.assertEqual(lines[0], "# >>> graphic-designer (zarządzane przez plugin) >>>")
        self.assertEqual(lines[-1], "# <<< graphic-designer <<<")
        self.assertTrue(block.endswith("\n"))
        rules = [self.RULE.match(l) for l in lines if l.startswith("prefix_rule(")]
        self.assertTrue(all(rules))
        self.assertEqual([m.group(1) for m in rules], ["env", "render", "check", "update-check", "doctor"])
        for l in lines[1:-1]:
            self.assertTrue(l.startswith("#") or l.startswith("prefix_rule("), l)
        comment = " ".join(l for l in lines if l.startswith("#"))
        for phrase in ("poza piaskownicą", "bez pytania", "tylko początek polecenia",
                       "ręczne zmiany w środku bloku znikną"):
            self.assertIn(phrase, comment)

    def test_allowed_subcommands_exist_in_the_script(self):
        script = (PLUGIN / "scripts" / "designer.py").read_text(encoding="utf-8")
        commands = set(re.findall(r'add_parser\(\s*"([\w-]+)"', script))
        for sub in onboard.ALLOWED_SUBCOMMANDS:
            self.assertIn(sub, commands)
        self.assertEqual(onboard.ALLOWED_SUBCOMMANDS, ("env", "render", "check", "update-check", "doctor"))

    def test_string_literals_are_escaped(self):
        s = onboard.starlark_string
        self.assertEqual(s("/tmp/a b/x.py"), '"/tmp/a b/x.py"')
        self.assertEqual(s(self.WINDOWS_PATH),
                         '"C:\\\\Users\\\\Ala Kowalska\\\\.codex\\\\graphic-designer\\\\designer.py"')
        self.assertEqual(s('a"b'), '"a\\"b"')
        self.assertEqual(s("a\\b"), '"a\\\\b"')
        self.assertEqual(s("\x00x\n"), '"\\u0000x\\n"')
        self.assertEqual(s("zażółć"), '"zażółć"')

    def test_block_uses_the_escaping_helper_for_any_path(self):
        for text in ("/tmp/a b/designer.py", self.WINDOWS_PATH, '/tmp/a"b/designer.py', "/tmp/a\\b/x.py"):
            with self.subTest(text):
                block = onboard.rules_block(Path(text))
                self.assertIn(onboard.starlark_string(str(Path(text))), block)
                self.assertEqual(len([l for l in block.splitlines() if l.startswith("prefix_rule(")]), 5)

    def test_windows_path_gets_doubled_backslashes_in_the_rule(self):
        block = onboard.rules_block(Path(self.WINDOWS_PATH))
        self.assertIn('"C:\\\\Users\\\\Ala Kowalska\\\\.codex\\\\graphic-designer\\\\designer.py"', block)
        self.assertNotIn("C:\\Users\\Ala", block.replace("\\\\", "/"))

    def test_text_search_understands_what_the_block_writes(self):
        for text in ("/tmp/a b/designer.py", self.WINDOWS_PATH):
            with self.subTest(text):
                p = Path(text)
                allowed = onboard.rules_allowing(onboard.rules_block(p), p)
                self.assertEqual(allowed, set(onboard.ALLOWED_SUBCOMMANDS))

    def test_unicode_line_separators_in_a_path_do_not_split_the_block(self):
        block = onboard.rules_block(Path("/tmp/a\u2028b/designer.py"))
        lines = onboard._split_lines(block)
        self.assertEqual(len(lines), len(block.split("\n")) - 1)
        self.assertEqual(onboard._find_block(lines, Path("x")), (0, len(lines) - 1))
        self.assertEqual(onboard._split_lines("a\u2028b\r\nc\rd"), ["a\u2028b\r\n", "c\r", "d"])

    @unittest.skipUnless(shutil.which("codex"), "brak polecenia codex")
    def test_real_codex_accepts_the_block(self):
        put(self.rules_file, onboard.rules_block(self.launcher))
        for sub in onboard.ALLOWED_SUBCOMMANDS:
            proc = subprocess.run(["codex", "execpolicy", "check", "--rules", str(self.rules_file), "--",
                                   "python3", str(self.launcher), sub, "--x"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(json.loads(proc.stdout)["decision"], "allow", sub)


class SetupRules(Sandboxed):
    ORIGINAL = ('# moje reguły\nprefix_rule(pattern=["git", "status"], decision="allow")\n\n'
                'prefix_rule(pattern=["rm", "-rf"], decision="forbidden")\n')

    def setUp(self):
        super().setUp()
        self.install_launcher()

    def read(self):
        return self.rules_file.read_bytes().decode("utf-8")

    def rules_dir_listing(self):
        return sorted(p.name for p in self.rules_file.parent.iterdir())

    def test_default_prints_the_proposal_and_writes_nothing(self):
        code, out = run("setup-rules")
        self.assertEqual(code, 0, out)
        self.assertFalse(self.rules_file.exists())
        self.assertFalse(self.rules_file.parent.exists())
        self.assertIn(onboard.rules_block(self.launcher), out)
        self.assertIn(str(self.rules_file), out)
        self.assertIn("nic nie zapisuję", out)
        for text in ("poza piaskownicą", "bez pytania", "env, render, check, update-check, doctor",
                     "ponownie", "setup-rules --apply", "setup-rules --remove",
                     "argumenty (np. --job <folder>) nie są ograniczone", "zasadą CSP",
                     "dowolny plik graficzny z dysku", "Otwieraj tylko zlecenia, którym ufasz",
                     "jednorazowa kopia default.rules.graphic-designer.bak"):
            self.assertIn(text, out)

    def test_apply_creates_dir_and_file(self):
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(), onboard.rules_block(self.launcher))
        self.assertIn("poza piaskownicą", out)
        self.assertIn("Uruchom Codex ponownie", out)
        self.assertIn("dowolny plik graficzny z dysku", out)
        self.assertEqual(self.rules_dir_listing(), ["default.rules"])

    @unittest.skipIf(WINDOWS, "uprawnienia plików są uniksowe")
    def test_new_file_is_readable_by_codex(self):
        run("setup-rules", "--apply")
        self.assertEqual(self.rules_file.stat().st_mode & 0o777, 0o644)

    def test_apply_appends_after_existing_content_and_keeps_it_byte_for_byte(self):
        original = self.ORIGINAL + "# znak \u2028 w komentarzu\n"
        put(self.rules_file, original)
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.rules_file.read_bytes(),
                         (original + "\n" + onboard.rules_block(self.launcher)).encode("utf-8"))

    def test_apply_adds_missing_final_newline_without_changing_the_rest(self):
        put(self.rules_file, 'prefix_rule(pattern=["ls"], decision="allow")')
        run("setup-rules", "--apply")
        self.assertTrue(self.read().startswith('prefix_rule(pattern=["ls"], decision="allow")\n\n# >>>'))

    def test_apply_keeps_windows_line_endings(self):
        original = b'# a\r\nprefix_rule(pattern=["ls"], decision="allow")\r\n'
        self.rules_file.parent.mkdir(parents=True)
        self.rules_file.write_bytes(original)
        run("setup-rules", "--apply")
        data = self.rules_file.read_bytes()
        self.assertTrue(data.startswith(original + b"\r\n# >>>"))
        self.assertNotIn(b"\r\r", data)
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))
        run("setup-rules", "--remove")
        self.assertEqual(self.rules_file.read_bytes(), original)

    def test_new_file_on_any_system_has_unix_line_endings(self):
        run("setup-rules", "--apply")
        self.assertNotIn(b"\r", self.rules_file.read_bytes())

    def test_apply_twice_is_idempotent(self):
        run("setup-rules", "--apply")
        first = self.rules_file.read_bytes()
        mtime = self.rules_file.stat().st_mtime_ns
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0)
        self.assertIn("już", out)
        self.assertEqual(self.rules_file.read_bytes(), first)
        self.assertEqual(self.rules_file.stat().st_mtime_ns, mtime)
        self.assertEqual(self.read().count("# >>> graphic-designer"), 1)

    def test_apply_rewrites_a_block_that_trusts_the_old_launcher_path(self):
        before = '# przed\nprefix_rule(pattern=["a"], decision="allow")\n'
        after = 'prefix_rule(pattern=["po"], decision="allow")\n'
        put(self.rules_file, before + "\n" + onboard.rules_block(self.legacy_launcher) + "\n" + after)
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0, out)
        self.assertIn("zaktualizowano", out)
        self.assertIn("ręczne zmiany w środku bloku znikają", out)
        final = self.read()
        self.assertNotIn(esc(self.legacy_launcher), final)
        self.assertIn(esc(self.launcher), final)
        self.assertEqual(final.count("# >>> graphic-designer"), 1)
        self.assertEqual(final, before + "\n" + onboard.rules_block(self.launcher) + "\n" + after)

    def test_apply_overwrites_everything_between_the_markers(self):
        block = onboard.rules_block(self.launcher)
        edited = block.replace("# <<< graphic-designer <<<",
                               'prefix_rule(pattern=["rm"], decision="allow")\n# <<< graphic-designer <<<')
        put(self.rules_file, edited)
        code, out = run("setup-rules", "--apply")
        self.assertIn("zaktualizowano", out)
        self.assertEqual(self.read(), block)

    def test_remove_restores_the_original_exactly(self):
        put(self.rules_file, self.ORIGINAL)
        run("setup-rules", "--apply")
        code, out = run("setup-rules", "--remove")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(), self.ORIGINAL)
        self.assertIn("usunięto", out)
        self.assertIn("ponownie", out)

    def test_remove_deletes_only_the_marked_block_in_the_middle_of_a_file(self):
        block = onboard.rules_block(self.launcher)
        put(self.rules_file, "# góra\n\n" + block + '\n# dół\nprefix_rule(pattern=["x"], decision="allow")\n')
        run("setup-rules", "--remove")
        self.assertEqual(self.read(), '# góra\n\n# dół\nprefix_rule(pattern=["x"], decision="allow")\n')

    def test_remove_when_there_is_no_block(self):
        put(self.rules_file, "# nic\n")
        code, out = run("setup-rules", "--remove")
        self.assertEqual(code, 0, out)
        self.assertIn("nie ma bloku", out)
        self.assertEqual(self.read(), "# nic\n")

    def test_remove_without_a_rules_file(self):
        code, out = run("setup-rules", "--remove")
        self.assertEqual(code, 0, out)
        self.assertIn("nie ma bloku", out)
        self.assertFalse(self.rules_file.exists())

    def test_damaged_block_is_not_touched(self):
        damaged = "# >>> graphic-designer (zarządzane przez plugin) >>>\nprefix_rule(x)\n"
        put(self.rules_file, damaged)
        for flag in ("--apply", "--remove"):
            code, out = run("setup-rules", flag)
            self.assertEqual(code, 1, out)
            self.assertIn("PROBLEM:", out)
            self.assertEqual(self.read(), damaged)

    def test_apply_without_the_launcher_points_to_setup_launcher(self):
        self.launcher.unlink()
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 1)
        self.assertIn("setup-launcher", out)
        self.assertFalse(self.rules_file.exists())

    def test_print_without_the_launcher_warns(self):
        self.launcher.unlink()
        code, out = run("setup-rules")
        self.assertEqual(code, 0)
        self.assertIn("setup-launcher", out)

    def test_write_failure_gives_the_terminal_command(self):
        with mock.patch.object(onboard, "_write", side_effect=PermissionError(13, "Permission denied")):
            code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 1)
        self.assertIn("PROBLEM:", out)
        self.assertIn("Terminalu", out)
        self.assertIn(f"python3 {self.launcher} setup-rules --apply", out)

    def test_apply_and_remove_exclude_each_other(self):
        with self.assertRaises(SystemExit) as cm:
            run("setup-rules", "--apply", "--remove")
        self.assertEqual(cm.exception.code, 2)

    def test_never_writes_outside_the_rules_file(self):
        before = set(self.codex_home.rglob("*"))
        run("setup-rules", "--apply")
        after = set(self.codex_home.rglob("*"))
        self.assertEqual(after - before, {self.codex_home / "rules", self.rules_file})

    # --- kopia zapasowa -------------------------------------------------------------------

    def test_first_apply_to_an_existing_file_makes_a_one_time_backup(self):
        put(self.rules_file, self.ORIGINAL)
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.backup_file.read_bytes(), self.ORIGINAL.encode("utf-8"))
        self.assertIn(str(self.backup_file), out)
        self.assertEqual(self.rules_dir_listing(), ["default.rules", "default.rules.graphic-designer.bak"])

    def test_backup_is_never_overwritten(self):
        put(self.rules_file, self.ORIGINAL)
        run("setup-rules", "--apply")
        self.backup_file.write_bytes(b"STARA KOPIA")
        run("setup-rules", "--remove")
        put(self.rules_file, self.ORIGINAL + "# nowa linia\n")
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.backup_file.read_bytes(), b"STARA KOPIA")

    def test_a_brand_new_file_needs_no_backup(self):
        run("setup-rules", "--apply")
        self.assertFalse(self.backup_file.exists())

    def test_backup_does_not_look_like_a_rules_file(self):
        put(self.rules_file, self.ORIGINAL)
        run("setup-rules", "--apply")
        self.assertEqual([p.name for p in self.rules_file.parent.glob("*.rules")], ["default.rules"])

    def test_no_backup_when_nothing_changes(self):
        run("setup-rules", "--apply")
        run("setup-rules", "--apply")
        self.assertFalse(self.backup_file.exists())

    # --- zapis atomowy --------------------------------------------------------------------

    def test_a_failed_replace_leaves_the_original_untouched(self):
        put(self.rules_file, self.ORIGINAL)
        with mock.patch("gd.onboard.os.replace", side_effect=OSError("dysk pełny")):
            code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 1, out)
        self.assertIn("PROBLEM:", out)
        self.assertIn("Plik zostaje bez zmian", out)
        self.assertEqual(self.read(), self.ORIGINAL)
        self.assertEqual([n for n in self.rules_dir_listing() if n.endswith(".tmp")], [])

    def test_a_failure_while_writing_leaves_no_temporary_file(self):
        put(self.rules_file, self.ORIGINAL)
        with mock.patch("gd.onboard.os.fsync", side_effect=OSError("błąd zapisu")):
            code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 1, out)
        self.assertEqual(self.read(), self.ORIGINAL)
        self.assertEqual([n for n in self.rules_dir_listing() if n.endswith(".tmp")], [])

    def test_a_failed_remove_leaves_the_file_as_it_was(self):
        put(self.rules_file, self.ORIGINAL)
        run("setup-rules", "--apply")
        with_block = self.rules_file.read_bytes()
        with mock.patch("gd.onboard.os.replace", side_effect=OSError("dysk pełny")):
            code, out = run("setup-rules", "--remove")
        self.assertEqual(code, 1, out)
        self.assertEqual(self.rules_file.read_bytes(), with_block)

    def test_write_goes_through_a_temporary_file_in_the_same_directory(self):
        put(self.rules_file, self.ORIGINAL)
        real = os.replace
        calls = []

        def spy(src, dst):
            calls.append((Path(src), Path(dst)))
            return real(src, dst)

        with mock.patch("gd.onboard.os.replace", side_effect=spy):
            run("setup-rules", "--apply")
        self.assertEqual(len(calls), 1)
        src, dst = calls[0]
        self.assertEqual(src.parent, dst.parent)
        self.assertNotEqual(src, dst)
        self.assertFalse(src.exists())

    @unittest.skipIf(WINDOWS, "uprawnienia plików są uniksowe")
    def test_permissions_of_an_existing_file_are_preserved(self):
        put(self.rules_file, self.ORIGINAL)
        os.chmod(self.rules_file, 0o640)
        run("setup-rules", "--apply")
        self.assertEqual(self.rules_file.stat().st_mode & 0o777, 0o640)
        run("setup-rules", "--remove")
        self.assertEqual(self.rules_file.stat().st_mode & 0o777, 0o640)

    @unittest.skipIf(WINDOWS, "dowiązania symboliczne wymagają uprawnień na Windows")
    def test_a_symlinked_rules_file_stays_a_symlink(self):
        real = self.tmp / "dotfiles" / "reguly"
        put(real, self.ORIGINAL)
        self.rules_file.parent.mkdir(parents=True)
        self.rules_file.symlink_to(real)
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0, out)
        self.assertTrue(self.rules_file.is_symlink())
        self.assertIn("# >>> graphic-designer", real.read_text(encoding="utf-8"))
        self.assertTrue((self.tmp / "dotfiles" / "reguly.graphic-designer.bak").is_file())
        run("setup-rules", "--remove")
        self.assertTrue(self.rules_file.is_symlink())
        self.assertEqual(real.read_bytes(), self.ORIGINAL.encode("utf-8"))


def fake_codex(directory, stdout, code=0, record=None):
    directory.mkdir(parents=True, exist_ok=True)
    script = directory / "codex"
    body = "#!/bin/sh\n"
    if record:
        body += 'printf \'%s\\n\' "$@" > ' + f"'{record}'\n"
    body += f"echo '{stdout}'\nexit {code}\n"
    script.write_bytes(body.encode("utf-8"))
    script.chmod(0o755)
    return script


FAKE_CHROME = Path("/fake/Chrome")
ALLOW_JSON = '{"matchedRules":[{"prefixRuleMatch":{"decision":"allow"}}],"decision":"allow"}'
NO_MATCH_JSON = '{"matchedRules":[]}'


class DoctorCase(Sandboxed):
    def setUp(self):
        super().setUp()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        os.environ["PATH"] = str(self.bin)  # bez prawdziwego codex
        patches = [mock.patch.object(onboard, "is_mac", return_value=True),
                   mock.patch.object(browser, "find", return_value=FAKE_CHROME),
                   mock.patch.object(browser, "smoke_test", return_value="BROWSER-TEST: OK")]
        self.mocks = [p.start() for p in patches]
        for p in patches:
            self.addCleanup(p.stop)
        self.smoke = self.mocks[2]

    def doctor(self):
        code, out = run("doctor")
        self.assertEqual(code, 0, out)
        return out.splitlines()

    def prepare_all(self):
        self.install_launcher()
        run("setup-rules", "--apply")
        run("library", "--set", self.tmp / "grafiki")

    def starts(self, lines, prefix):
        return [l for l in lines if l.startswith(prefix)]

    def find(self, lines, text):
        found = [l for l in lines if text in l]
        self.assertTrue(found, f"brak '{text}' w:\n" + "\n".join(lines))
        return found[0]

    def test_everything_set_up_has_no_todo(self):
        self.prepare_all()
        lines = self.doctor()
        self.assertEqual(self.starts(lines, "TODO:"), [], "\n".join(lines))
        self.assertIn("OK:", self.find(lines, "stały skrypt")[:3])
        self.assertTrue(self.find(lines, "reguły").startswith("OK:"))

    def test_every_line_has_a_known_prefix(self):
        lines = self.doctor()
        self.assertTrue(lines)
        for l in lines:
            self.assertTrue(l.startswith(("OK:", "TODO:", "INFO:")), l)

    def test_fresh_machine_lists_todos_each_with_one_next_step(self):
        lines = self.doctor()
        todos = self.starts(lines, "TODO:")
        self.assertGreaterEqual(len(todos), 3, "\n".join(lines))
        for l in todos:
            self.assertEqual(l.count("Następny krok:"), 1, l)
        self.assertIn("setup-launcher", self.find(lines, "stały skrypt"))
        self.assertIn("setup-rules", self.find(lines, "reguł"))
        self.assertIn("library --set", self.find(lines, "biblioteka"))

    def test_next_step_for_launcher_uses_the_plugin_script_path(self):
        line = self.find(self.doctor(), "stały skrypt")
        self.assertIn(str(PLUGIN / "scripts" / "designer.py"), line)

    def test_stale_launcher_is_a_todo(self):
        self.prepare_all()
        put(self.launcher, "# stary\n")
        line = self.find(self.doctor(), "stały skrypt")
        self.assertTrue(line.startswith("TODO:"), line)
        self.assertIn("nieaktualny", line)

    def test_rules_missing_for_some_subcommands(self):
        self.install_launcher()
        self.rules_file.parent.mkdir(parents=True)
        q = onboard.starlark_string(str(self.launcher))
        put(self.rules_file,
            f'prefix_rule(pattern=["python3", {q}, "render"], decision="allow")\n'
            f'# prefix_rule(pattern=["python3", {q}, "check"], decision="allow")\n'
            f'prefix_rule(pattern=["python3", {q}, "env"], decision="prompt")\n')
        line = self.find(self.doctor(), "reguł")
        self.assertTrue(line.startswith("TODO:"), line)
        for sub in ("env", "check", "update-check", "doctor"):
            self.assertIn(sub, line.split("Następny krok:")[0])
        self.assertNotIn("render", line.split("Następny krok:")[0])

    def test_multiline_rule_is_found(self):
        self.install_launcher()
        q = onboard.starlark_string(str(self.launcher))
        text = "".join(f'prefix_rule(\n  pattern=["python3", {q}, "{s}"],\n  decision="allow",\n)\n'
                       for s in onboard.ALLOWED_SUBCOMMANDS)
        put(self.rules_file, text)
        self.assertTrue(self.find(self.doctor(), "reguły").startswith("OK:"))

    def test_rules_with_a_different_launcher_path_ask_to_update(self):
        self.prepare_all()
        text = self.rules_file.read_bytes().decode("utf-8").replace(
            esc(self.launcher), esc(self.tmp / "dawna" / "sciezka" / "designer.py"))
        put(self.rules_file, text)
        line = self.find(self.doctor(), "reguł")
        self.assertTrue(line.startswith("TODO:"), line)
        self.assertIn("setup-rules --apply", line)
        self.assertIn("inną ścieżkę", line)

    def test_checks_all_rules_files_in_the_directory(self):
        self.install_launcher()
        run("setup-rules", "--apply")
        os.replace(self.rules_file, self.rules_file.parent / "inne.rules")
        self.assertTrue(self.find(self.doctor(), "reguły").startswith("OK:"))

    def test_sandbox_skips_the_browser_test_like_env(self):
        os.environ["CODEX_SANDBOX"] = "seatbelt"
        with mock.patch.object(browser, "in_codex_sandbox", return_value=True):
            lines = self.doctor()
        self.smoke.assert_not_called()
        line = self.find(lines, "próbny start")
        self.assertTrue(line.startswith("INFO:"), line)
        self.assertIn("pominięty", line)
        self.assertIn("seatbelt", self.find(lines, "CODEX_SANDBOX"))

    def test_browser_test_ok(self):
        line = self.find(self.doctor(), "próbny start")
        self.assertTrue(line.startswith("OK:"), line)

    def test_browser_test_failed_is_a_todo(self):
        self.smoke.return_value = "BROWSER-TEST: FAILED (kod 134) — SANDBOX?: coś"
        line = self.find(self.doctor(), "próbny start")
        self.assertTrue(line.startswith("TODO:"), line)
        self.assertEqual(line.count("Następny krok:"), 1)

    def test_no_browser_is_a_todo_and_skips_the_browser_test(self):
        self.mocks[1].side_effect = GdError("NO BROWSER: nie znalazłem przeglądarki. zainstaluj Chrome")
        lines = self.doctor()
        self.assertTrue(self.find(lines, "przeglądarki").startswith("TODO:"))
        self.smoke.assert_not_called()

    def test_browser_found_is_ok_with_path(self):
        line = self.find(self.doctor(), str(FAKE_CHROME))
        self.assertTrue(line.startswith("OK:"), line)

    def test_python_version_lines(self):
        self.assertTrue(onboard.python_line((3, 13, 1)).startswith("OK:"))
        low = onboard.python_line((3, 8, 10))
        self.assertTrue(low.startswith("TODO:"))
        self.assertIn("Następny krok:", low)

    def test_api_key_warning_only_when_set(self):
        self.assertEqual([l for l in self.doctor() if "OPENAI_API_KEY" in l], [])
        os.environ["OPENAI_API_KEY"] = "sk-test"
        line = self.find(self.doctor(), "OPENAI_API_KEY")
        self.assertTrue(line.startswith("INFO:"), line)
        self.assertNotIn("sk-test", line)

    def test_codex_sandbox_not_set(self):
        line = self.find(self.doctor(), "CODEX_SANDBOX")
        self.assertTrue(line.startswith("INFO:"), line)

    def test_library_ok_when_set(self):
        run("library", "--set", self.tmp / "grafiki")
        line = self.find(self.doctor(), "biblioteka")
        self.assertTrue(line.startswith("OK:"), line)
        self.assertIn(str(self.tmp / "grafiki"), line)

    def test_command_form_uses_the_absolute_launcher_path(self):
        self.install_launcher()
        line = self.find(self.doctor(), "Polecenie do uruchamiania")
        self.assertTrue(line.startswith("INFO:"))
        self.assertIn(f"python3 {self.launcher} <polecenie>", line)
        # pełna ścieżka, bez skrótu i bez zmiennej (krótkie nazwy Windows mogą zawierać ~ w środku)
        self.assertNotIn("python3 ~", line)
        self.assertNotIn("$HOME", line)
        self.assertTrue(Path(line.split("python3 ", 1)[1].split(" <polecenie>")[0].strip('"')).is_absolute())

    def test_command_form_without_launcher_uses_the_plugin_script(self):
        line = self.find(self.doctor(), "Polecenie do uruchamiania")
        self.assertIn(str(PLUGIN / "scripts" / "designer.py"), line)

    def test_browser_failure_hint_depends_on_the_sandbox(self):
        self.smoke.return_value = "BROWSER-TEST: FAILED (kod 134) — coś"
        plain = self.find(self.doctor(), "próbny start")
        self.assertIn("sprawdź, czy przeglądarka uruchamia się ręcznie", plain)
        self.assertNotIn("poza piaskownicą", plain)
        os.environ["CODEX_SANDBOX"] = "seatbelt"
        os.environ["GD_BROWSER_TRY"] = "1"  # wymuszona próba także w piaskownicy
        sandboxed = self.find(self.doctor(), "próbny start")
        self.assertIn("poza piaskownicą", sandboxed)
        self.assertEqual(sandboxed.count("Następny krok:"), 1)

    # --- przeniesienie stałego skryptu (przegląd 0.2.0, I1) -------------------------------

    def legacy_ours(self):
        put(self.legacy_launcher, "\"\"\"" + onboard.LAUNCHER_MARKER + ".\"\"\"\n")

    def test_missing_launcher_with_an_old_copy_mentions_it(self):
        self.legacy_ours()
        line = self.find(self.doctor(), "stały skrypt")
        self.assertTrue(line.startswith("TODO:"), line)
        self.assertIn("dawna kopia", line)
        self.assertIn(str(self.legacy_launcher), line)
        self.assertEqual(line.count("Następny krok:"), 1)

    def test_current_launcher_with_an_old_copy_asks_to_remove_it(self):
        self.prepare_all()
        self.legacy_ours()
        lines = self.doctor()
        ok = self.find(lines, "jest zainstalowany i aktualny")
        self.assertTrue(ok.startswith("OK:"), ok)
        old = self.find(lines, "dawny stały skrypt startowy nadal leży")
        self.assertTrue(old.startswith("TODO:"), old)
        self.assertIn("setup-launcher", old)

    def test_a_foreign_file_in_the_old_place_is_not_mentioned(self):
        self.prepare_all()
        put(self.legacy_launcher, "# cudzy plik\n")
        lines = self.doctor()
        self.assertEqual([l for l in lines if "dawn" in l], [], "\n".join(lines))
        self.assertEqual(self.starts(lines, "TODO:"), [])

    def test_rules_that_still_trust_the_old_file_are_called_out(self):
        self.prepare_all()
        text = self.rules_file.read_bytes().decode("utf-8").replace(
            esc(self.launcher), esc(self.legacy_launcher))
        put(self.rules_file, text)
        line = self.find(self.doctor(), "reguł")
        self.assertTrue(line.startswith("TODO:"), line)
        self.assertIn("ufają jeszcze dawnemu plikowi", line)
        self.assertIn(str(self.legacy_launcher), line)
        self.assertIn("setup-rules --apply", line)

    def test_not_mac_makes_launcher_and_rules_informational(self):
        self.mocks[0].return_value = False
        run("library", "--set", self.tmp / "grafiki")
        lines = self.doctor()
        self.assertEqual(self.starts(lines, "TODO:"), [], "\n".join(lines))
        self.assertTrue(self.find(lines, "stały skrypt").startswith("INFO:"))
        self.assertTrue(self.find(lines, "reguł").startswith("INFO:"))

    def test_doctor_writes_nothing(self):
        self.prepare_all()
        before = sorted(str(p) for p in self.tmp.rglob("*"))
        self.doctor()
        self.assertEqual(sorted(str(p) for p in self.tmp.rglob("*")), before)

    def test_a_failing_check_does_not_break_doctor(self):
        with mock.patch.object(onboard, "library_line", side_effect=RuntimeError("zepsute")):
            lines = self.doctor()
        line = self.find(lines, "zepsute")
        self.assertTrue(line.startswith("INFO:"), line)

    @unittest.skipIf(WINDOWS, "atrapa codex to skrypt sh")
    def test_codex_execpolicy_allow_is_ok(self):
        self.prepare_all()
        record = self.tmp / "args.txt"
        fake_codex(self.bin, ALLOW_JSON, record=record)
        lines = self.doctor()
        line = self.find(lines, "execpolicy")
        self.assertTrue(line.startswith("OK:"), line)
        args = record.read_text(encoding="utf-8").split("\n")
        self.assertEqual(args[:2], ["execpolicy", "check"])
        self.assertIn(str(self.rules_file), args)
        self.assertEqual(args[args.index("--") + 1:args.index("--") + 4], ["python3", str(self.launcher), "render"])

    @unittest.skipIf(WINDOWS, "atrapa codex to skrypt sh")
    def test_codex_execpolicy_without_match_is_a_todo(self):
        self.prepare_all()
        fake_codex(self.bin, NO_MATCH_JSON)
        line = self.find(self.doctor(), "execpolicy")
        self.assertTrue(line.startswith("TODO:"), line)

    @unittest.skipIf(WINDOWS, "atrapa codex to skrypt sh")
    def test_codex_failure_is_informational(self):
        self.prepare_all()
        fake_codex(self.bin, "boom", code=1)
        line = self.find(self.doctor(), "execpolicy")
        self.assertTrue(line.startswith("INFO:"), line)

    def test_no_codex_on_path_is_informational(self):
        self.prepare_all()
        line = self.find(self.doctor(), "execpolicy")
        self.assertTrue(line.startswith("INFO:"), line)

    @unittest.skipIf(WINDOWS, "atrapa codex to skrypt sh")
    def test_execpolicy_is_skipped_when_no_rules_exist(self):
        self.install_launcher()
        record = self.tmp / "args.txt"
        fake_codex(self.bin, ALLOW_JSON, record=record)
        lines = self.doctor()
        self.assertFalse(record.exists())
        self.assertTrue(self.find(lines, "execpolicy").startswith("INFO:"))


if __name__ == "__main__":
    unittest.main()
