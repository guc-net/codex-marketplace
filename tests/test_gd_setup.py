"""Testy konfiguracji: stały skrypt startowy, reguły Codexa, doctor, manifest."""
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
        for key in ("GD_PLUGIN_ROOT", "CODEX_SANDBOX", "GD_BROWSER_TRY", "OPENAI_API_KEY"):
            os.environ.pop(key, None)

    @property
    def launcher(self):
        return self.gd_home / "designer.py"

    @property
    def rules_file(self):
        return self.codex_home / "rules" / "default.rules"

    def install_launcher(self):
        code, out = run("setup-launcher")
        self.assertEqual(code, 0, out)

    def fake_plugin(self, version, marketplace="guc-net", with_script=True):
        root = self.codex_home / "plugins" / "cache" / marketplace / "graphic-designer" / version
        (root / "scripts").mkdir(parents=True)
        if with_script:
            (root / "scripts" / "designer.py").write_text(
                "import sys\nprint('FAKE', %r, sys.argv[0], *sys.argv[1:])\n"
                "sys.exit(int(__import__('os').environ.get('FAKE_EXIT', '0')))\n" % version,
                encoding="utf-8")
        return root


def load_launcher():
    spec = importlib.util.spec_from_file_location("gd_launcher_under_test", TEMPLATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LauncherFinding(Sandboxed):
    def test_template_exists_and_is_stdlib_only(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("from __future__ import annotations", text)
        self.assertIn("runpy", text)
        imports = set(re.findall(r"^(?:import|from) ([\w.]+)", text, re.M))
        self.assertTrue(imports <= {"__future__", "os", "re", "runpy", "sys", "pathlib"}, imports)

    def test_picks_highest_version_numerically(self):
        for v in ("0.2.0", "0.10.0", "0.9.5"):
            self.fake_plugin(v)
        found = load_launcher().find_designer()
        self.assertEqual(found.parent.parent.name, "0.10.0")

    def test_picks_highest_across_marketplaces(self):
        self.fake_plugin("0.2.0", "guc-net")
        self.fake_plugin("0.3.1", "inny-katalog")
        self.assertEqual(load_launcher().find_designer().parent.parent.name, "0.3.1")

    def test_ignores_versions_without_script(self):
        self.fake_plugin("0.2.0")
        self.fake_plugin("0.9.0", with_script=False)
        self.assertEqual(load_launcher().find_designer().parent.parent.name, "0.2.0")

    def test_override_with_plugin_root(self):
        self.fake_plugin("0.9.0")
        other = self.tmp / "inny-plugin"
        (other / "scripts").mkdir(parents=True)
        (other / "scripts" / "designer.py").write_text("print('x')\n", encoding="utf-8")
        os.environ["GD_PLUGIN_ROOT"] = str(other)
        self.assertEqual(load_launcher().find_designer(), other / "scripts" / "designer.py")

    def test_override_pointing_nowhere_is_an_error_not_a_fallback(self):
        self.fake_plugin("0.9.0")
        os.environ["GD_PLUGIN_ROOT"] = str(self.tmp / "nie-ma")
        with self.assertRaises(LookupError) as cm:
            load_launcher().find_designer()
        self.assertIn("GD_PLUGIN_ROOT", str(cm.exception))

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

    def test_runs_the_real_designer_through_plugin_root_override(self):
        code, out, err = self.start("version", GD_PLUGIN_ROOT=str(PLUGIN))
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), manifest["version"])


class SetupLauncher(Sandboxed):
    def test_installs_the_template_and_prints_the_absolute_path(self):
        code, out = run("setup-launcher")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.launcher.read_bytes(), TEMPLATE.read_bytes())
        self.assertIn(str(self.launcher), out)
        self.assertTrue(Path(str(self.launcher)).is_absolute())
        self.assertIn("OK:", out)

    def test_is_idempotent(self):
        run("setup-launcher")
        before = self.launcher.stat().st_mtime_ns
        code, out = run("setup-launcher")
        self.assertEqual(code, 0)
        self.assertIn("aktualny", out)
        self.assertIn(str(self.launcher), out)
        self.assertEqual(self.launcher.stat().st_mtime_ns, before)

    def test_updates_a_stale_launcher(self):
        self.gd_home.mkdir()
        self.launcher.write_text("# stary\n", encoding="utf-8")
        code, out = run("setup-launcher")
        self.assertEqual(code, 0)
        self.assertIn("zaktualizowano", out)
        self.assertEqual(self.launcher.read_bytes(), TEMPLATE.read_bytes())

    @unittest.skipIf(WINDOWS, "bit wykonywalny dotyczy systemów uniksowych")
    def test_launcher_is_executable(self):
        run("setup-launcher")
        self.assertTrue(os.access(self.launcher, os.X_OK))

    def test_default_home_without_gd_home(self):
        os.environ.pop("GD_HOME")
        self.assertEqual(onboard.launcher_path(), Path.home() / ".graphic-designer" / "designer.py")


class RulesBlock(Sandboxed):
    RULE = re.compile(r'^prefix_rule\(pattern=\["python3", ".*", "([a-z-]+)"\], decision="allow"\)$')

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
        self.assertIn("poza piaskownicą", comment)
        self.assertIn("bez pytania", comment)

    def test_allowed_subcommands_exist_in_the_script(self):
        script = (PLUGIN / "scripts" / "designer.py").read_text(encoding="utf-8")
        commands = set(re.findall(r'add_parser\(\s*"([\w-]+)"', script))
        for sub in onboard.ALLOWED_SUBCOMMANDS:
            self.assertIn(sub, commands)
        self.assertEqual(onboard.ALLOWED_SUBCOMMANDS, ("env", "render", "check", "update-check", "doctor"))

    def test_path_is_quoted_and_escaped(self):
        block = onboard.rules_block(Path('/tmp/a b/"x"/designer.py'))
        self.assertIn('"/tmp/a b/\\"x\\"/designer.py"', block)

    @unittest.skipIf(WINDOWS, "ścieżka z odwrotnym ukośnikiem w nazwie to przypadek uniksowy")
    def test_backslash_is_escaped(self):
        block = onboard.rules_block(Path("/tmp/a\\b/designer.py"))
        self.assertIn('"/tmp/a\\\\b/designer.py"', block)

    @unittest.skipUnless(shutil.which("codex"), "brak polecenia codex")
    def test_real_codex_accepts_the_block(self):
        self.rules_file.parent.mkdir(parents=True)
        self.rules_file.write_text(onboard.rules_block(self.launcher), encoding="utf-8")
        for sub in onboard.ALLOWED_SUBCOMMANDS:
            proc = subprocess.run(["codex", "execpolicy", "check", "--rules", str(self.rules_file), "--",
                                   "python3", str(self.launcher), sub, "--x"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(json.loads(proc.stdout)["decision"], "allow", sub)


class SetupRules(Sandboxed):
    def setUp(self):
        super().setUp()
        self.install_launcher()

    def read(self):
        return self.rules_file.read_bytes().decode("utf-8")

    def test_default_prints_the_proposal_and_writes_nothing(self):
        code, out = run("setup-rules")
        self.assertEqual(code, 0, out)
        self.assertFalse(self.rules_file.exists())
        self.assertFalse(self.rules_file.parent.exists())
        self.assertIn(onboard.rules_block(self.launcher), out)
        self.assertIn(str(self.rules_file), out)
        self.assertIn("nic nie zapisuję", out)
        for text in ("poza piaskownicą", "bez pytania", "env, render, check, update-check, doctor",
                     "ponownie", "setup-rules --apply", "setup-rules --remove"):
            self.assertIn(text, out)

    def test_apply_creates_dir_and_file(self):
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(), onboard.rules_block(self.launcher))
        self.assertIn("poza piaskownicą", out)
        self.assertIn("Uruchom Codex ponownie", out)

    def test_apply_appends_after_existing_content_and_keeps_it_byte_for_byte(self):
        self.rules_file.parent.mkdir(parents=True)
        original = ('# moje reguły\nprefix_rule(pattern=["git", "status"], decision="allow")\n\n'
                    'prefix_rule(pattern=["rm", "-rf"], decision="forbidden")\n')
        self.rules_file.write_bytes(original.encode("utf-8"))
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0, out)
        text = self.read()
        self.assertTrue(text.startswith(original + "\n# >>> graphic-designer"), text)
        self.assertEqual(text, original + "\n" + onboard.rules_block(self.launcher))

    def test_apply_adds_missing_final_newline_without_changing_the_rest(self):
        self.rules_file.parent.mkdir(parents=True)
        self.rules_file.write_bytes(b'prefix_rule(pattern=["ls"], decision="allow")')
        run("setup-rules", "--apply")
        self.assertTrue(self.read().startswith('prefix_rule(pattern=["ls"], decision="allow")\n\n# >>>'))

    def test_apply_keeps_windows_line_endings(self):
        self.rules_file.parent.mkdir(parents=True)
        original = b'# a\r\nprefix_rule(pattern=["ls"], decision="allow")\r\n'
        self.rules_file.write_bytes(original)
        run("setup-rules", "--apply")
        data = self.rules_file.read_bytes()
        self.assertTrue(data.startswith(original + b"\r\n# >>>"))
        self.assertNotIn(b"\r\r", data)
        self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))

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

    def test_apply_updates_the_block_when_the_launcher_path_changes(self):
        self.rules_file.parent.mkdir(parents=True)
        self.rules_file.write_text('# przed\nprefix_rule(pattern=["a"], decision="allow")\n',
                                   encoding="utf-8")
        run("setup-rules", "--apply")
        old = str(self.launcher)
        text = self.read()
        self.rules_file.write_text(text + '\nprefix_rule(pattern=["po"], decision="allow")\n',
                                   encoding="utf-8")
        new_home = self.tmp / "inny dom"
        os.environ["GD_HOME"] = str(new_home)
        self.install_launcher()
        code, out = run("setup-rules", "--apply")
        self.assertEqual(code, 0, out)
        self.assertIn("zaktualizowano", out)
        final = self.read()
        self.assertNotIn(old, final)
        self.assertIn(str(new_home / "designer.py"), final)
        self.assertEqual(final.count("# >>> graphic-designer"), 1)
        self.assertTrue(final.startswith('# przed\nprefix_rule(pattern=["a"], decision="allow")\n\n# >>>'))
        self.assertTrue(final.endswith('# <<< graphic-designer <<<\n\nprefix_rule(pattern=["po"], '
                                       'decision="allow")\n'))

    def test_remove_restores_the_original_exactly(self):
        self.rules_file.parent.mkdir(parents=True)
        original = '# moje\nprefix_rule(pattern=["git"], decision="allow")\n'
        self.rules_file.write_text(original, encoding="utf-8")
        run("setup-rules", "--apply")
        code, out = run("setup-rules", "--remove")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read(), original)
        self.assertIn("usunięto", out)
        self.assertIn("ponownie", out)

    def test_remove_deletes_only_the_marked_block_in_the_middle_of_a_file(self):
        self.rules_file.parent.mkdir(parents=True)
        run("setup-rules", "--apply")
        block = onboard.rules_block(self.launcher)
        self.rules_file.write_text("# góra\n\n" + block + "\n# dół\nprefix_rule(pattern=[\"x\"], "
                                   "decision=\"allow\")\n", encoding="utf-8")
        run("setup-rules", "--remove")
        self.assertEqual(self.read(), '# góra\n\n# dół\nprefix_rule(pattern=["x"], decision="allow")\n')

    def test_remove_when_there_is_no_block(self):
        self.rules_file.parent.mkdir(parents=True)
        self.rules_file.write_text("# nic\n", encoding="utf-8")
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
        self.rules_file.parent.mkdir(parents=True)
        damaged = "# >>> graphic-designer (zarządzane przez plugin) >>>\nprefix_rule(x)\n"
        self.rules_file.write_text(damaged, encoding="utf-8")
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
        before = {p for p in self.codex_home.rglob("*")} if self.codex_home.exists() else set()
        run("setup-rules", "--apply")
        after = {p for p in self.codex_home.rglob("*")}
        self.assertEqual(after - before, {self.codex_home / "rules", self.rules_file})


def fake_codex(directory, stdout, code=0, record=None):
    directory.mkdir(parents=True, exist_ok=True)
    script = directory / "codex"
    body = "#!/bin/sh\n"
    if record:
        body += 'printf \'%s\\n\' "$@" > ' + f"'{record}'\n"
    body += f"echo '{stdout}'\nexit {code}\n"
    script.write_text(body, encoding="utf-8")
    script.chmod(0o755)
    return script


ALLOW_JSON = '{"matchedRules":[{"prefixRuleMatch":{"decision":"allow"}}],"decision":"allow"}'
NO_MATCH_JSON = '{"matchedRules":[]}'


class DoctorCase(Sandboxed):
    def setUp(self):
        super().setUp()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        os.environ["PATH"] = str(self.bin)  # bez prawdziwego codex
        patches = [mock.patch.object(onboard, "is_mac", return_value=True),
                   mock.patch.object(browser, "find", return_value=Path("/fake/Chrome")),
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
        self.launcher.write_text("# stary\n", encoding="utf-8")
        line = self.find(self.doctor(), "stały skrypt")
        self.assertTrue(line.startswith("TODO:"), line)
        self.assertIn("nieaktualny", line)

    def test_rules_missing_for_some_subcommands(self):
        self.install_launcher()
        self.rules_file.parent.mkdir(parents=True)
        q = json.dumps(str(self.launcher))
        self.rules_file.write_text(
            f'prefix_rule(pattern=["python3", {q}, "render"], decision="allow")\n'
            f'# prefix_rule(pattern=["python3", {q}, "check"], decision="allow")\n'
            f'prefix_rule(pattern=["python3", {q}, "env"], decision="prompt")\n', encoding="utf-8")
        line = self.find(self.doctor(), "reguł")
        self.assertTrue(line.startswith("TODO:"), line)
        for sub in ("env", "check", "update-check", "doctor"):
            self.assertIn(sub, line.split("Następny krok:")[0])
        self.assertNotIn("render", line.split("Następny krok:")[0])

    def test_multiline_rule_is_found(self):
        self.install_launcher()
        self.rules_file.parent.mkdir(parents=True)
        q = json.dumps(str(self.launcher))
        text = "".join(f'prefix_rule(\n  pattern=["python3", {q}, "{s}"],\n  decision="allow",\n)\n'
                       for s in onboard.ALLOWED_SUBCOMMANDS)
        self.rules_file.write_text(text, encoding="utf-8")
        self.assertTrue(self.find(self.doctor(), "reguły").startswith("OK:"))

    def test_rules_with_a_different_launcher_path_ask_to_update(self):
        self.prepare_all()
        text = self.rules_file.read_text(encoding="utf-8").replace(str(self.launcher), "/dawna/sciezka/designer.py")
        self.rules_file.write_text(text, encoding="utf-8")
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
        line = self.find(self.doctor(), "/fake/Chrome")
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
        self.assertNotIn("~", line)
        self.assertNotIn("$HOME", line)

    def test_command_form_without_launcher_uses_the_plugin_script(self):
        line = self.find(self.doctor(), "Polecenie do uruchamiania")
        self.assertIn(str(PLUGIN / "scripts" / "designer.py"), line)

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
