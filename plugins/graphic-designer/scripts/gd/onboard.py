"""Konfiguracja pierwszego uruchomienia: stały skrypt startowy, reguły Codexa, doctor."""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, List, Optional, Set, Tuple

from . import browser, jobs
from .common import PLUGIN_ROOT, GdError, gd_home

# Polecenia, które reguły pozwalają uruchamiać poza piaskownicą, bez pytania o zgodę.
ALLOWED_SUBCOMMANDS = ("env", "render", "check", "update-check", "doctor")
BEGIN = "# >>> graphic-designer (zarządzane przez plugin) >>>"
END = "# <<< graphic-designer <<<"
TEMPLATE = PLUGIN_ROOT / "templates" / "launcher.py"
# To zdanie jest w każdej wersji szablonu: po nim poznajemy, że plik jest nasz (przed usunięciem).
LAUNCHER_MARKER = "Stały skrypt startowy pluginu graphic-designer"
BACKUP_SUFFIX = ".graphic-designer.bak"
NEXT = "Następny krok:"


def codex_home() -> Path:
    home = os.environ.get("CODEX_HOME")
    return Path(home).expanduser() if home else Path.home() / ".codex"


def rules_dir() -> Path:
    return codex_home() / "rules"


def rules_file() -> Path:
    return rules_dir() / "default.rules"


def launcher_path() -> Path:
    """Stały skrypt leży w folderze Codexa, który Codex chroni przed zapisem z piaskownicy także
    wtedy, gdy osoba otworzy swój katalog domowy jako projekt (przegląd 0.2.0, I1)."""
    return codex_home() / "graphic-designer" / "designer.py"


def legacy_launcher_path() -> Path:
    """Dawne miejsce (0.2.0 przed poprawką): folder ustawień pluginu, niechroniony przez Codex."""
    return gd_home() / "designer.py"


def plugin_script() -> Path:
    return PLUGIN_ROOT / "scripts" / "designer.py"


def is_mac() -> bool:
    return sys.platform == "darwin"


def _q(path: Path) -> str:
    """Ścieżka w poleceniu: jeden argument, z cudzysłowem tylko gdy trzeba."""
    text = str(path)
    if os.name == "posix":
        return shlex.quote(text)
    return f'"{text}"' if " " in text else text


def current_command() -> str:
    """`python3 <stały skrypt>` gdy jest zainstalowany, inaczej `python3 <skrypt z pluginu>`."""
    return f"python3 {_q(launcher_path() if launcher_path().is_file() else plugin_script())}"


# ---------------------------------------------------------------- stały skrypt startowy

def is_our_launcher(path: Path) -> bool:
    try:
        return path.is_file() and LAUNCHER_MARKER in path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False


def legacy_state() -> str:
    """absent, ours (nasz plik w dawnym miejscu) albo foreign (cudzy plik pod tą nazwą)."""
    old = legacy_launcher_path()
    if old == launcher_path() or not old.is_file():
        return "absent"
    return "ours" if is_our_launcher(old) else "foreign"


def setup_launcher() -> Tuple[str, str]:
    """Instaluje albo aktualizuje stały skrypt i sprząta dawne miejsce.

    Zwraca (status, dawny): status to installed, updated albo current; dawny to absent, removed
    (nasz plik usunięty) albo foreign (cudzego pliku nie ruszamy)."""
    wanted = TEMPLATE.read_bytes()
    dest = launcher_path()
    try:
        current = dest.read_bytes() if dest.is_file() else None
        status = "current"
        if current != wanted:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(wanted)
            if os.name == "posix":
                dest.chmod(0o755)
            status = "installed" if current is None else "updated"
    except OSError as e:
        raise GdError(f"nie mogę zapisać {dest}: {e}")
    legacy = legacy_state()
    if legacy == "ours":
        try:
            legacy_launcher_path().unlink()
        except OSError as e:
            raise GdError(f"zainstalowałem {dest}, ale nie mogę usunąć dawnego pliku "
                          f"{legacy_launcher_path()}: {e}")
        legacy = "removed"
    return status, legacy


def launcher_state() -> str:
    """missing, stale albo ok."""
    dest = launcher_path()
    if not dest.is_file():
        return "missing"
    try:
        return "ok" if dest.read_bytes() == TEMPLATE.read_bytes() else "stale"
    except OSError:
        return "stale"


# ---------------------------------------------------------------- reguły Codexa

def starlark_string(text: str) -> str:
    """Literał tekstowy do reguł Codexa (Starlark): cudzysłowy, odwrotne ukośniki (ścieżki z Windows)
    i znaki sterujące zapisane przez ucieczkę, więc ścieżka nie wychodzi poza literał."""
    return json.dumps(text, ensure_ascii=False)


def rules_block(launcher: Path, eol: str = "\n") -> str:
    """Blok reguł między znacznikami; kończy się znakiem nowej linii."""
    path = starlark_string(str(launcher))
    lines = [
        BEGIN,
        "# Reguły Codexa dla pluginu graphic-designer. Pozwalają uruchamiać poza piaskownicą,",
        "# bez pytania o zgodę, tylko te polecenia pluginu: " + ", ".join(ALLOWED_SUBCOMMANDS) + ".",
        "# Powód: Chrome, którym plugin składa grafiki, nie startuje w piaskownicy Codexa na macOS.",
        "# Reguła dopasowuje tylko początek polecenia: argumenty po nim nie są ograniczone.",
        "# Blok dopisuje i aktualizuje plugin (designer.py setup-rules --apply); przy aktualizacji",
        "# nadpisuje całą treść między znacznikami, więc ręczne zmiany w środku bloku znikną.",
        "# Usuniesz go poleceniem setup-rules --remove albo ręcznie, razem z liniami początku i",
        "# końca. Po każdej zmianie uruchom Codex ponownie, bo czyta reguły przy starcie.",
    ]
    lines += [f'prefix_rule(pattern=["python3", {path}, "{sub}"], decision="allow")'
              for sub in ALLOWED_SUBCOMMANDS]
    lines.append(END)
    return eol.join(lines) + eol


_LINE = re.compile(r"[^\r\n]*(?:\r\n|\n|\r)|[^\r\n]+")


def _split_lines(text: str) -> List[str]:
    """Linie z końcami (tylko \\n, \\r\\n i \\r; `str.splitlines` dzieli też na U+2028 i innych)."""
    return _LINE.findall(text)


def _read(path: Path) -> str:
    """Treść jako tekst UTF-8, bez żadnej zamiany końców linii (czytamy bajty)."""
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise GdError(f"nie mogę odczytać {path}: {e}")


def _write(path: Path, text: str) -> None:
    """Zapis atomowy: plik tymczasowy w tym samym katalogu, potem os.replace. Zachowuje uprawnienia
    istniejącego pliku i dowiązanie symboliczne (zapis idzie do celu). Przy błędzie oryginał zostaje
    nietknięty, a plik tymczasowy znika. Zapisuje bajty, więc system nie zmieni końców linii."""
    target = Path(os.path.realpath(str(path)))
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(text.encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        if target.exists():
            shutil.copymode(str(target), tmp)
        else:
            os.chmod(tmp, 0o644)
        os.replace(tmp, str(target))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def backup_path() -> Path:
    target = Path(os.path.realpath(str(rules_file())))
    return target.with_name(target.name + BACKUP_SUFFIX)


def _backup_once(path: Path) -> None:
    """Jednorazowa kopia pliku reguł sprzed pierwszego zapisu; istniejącej kopii nie nadpisuje."""
    backup = backup_path()
    if not backup.exists():
        shutil.copyfile(os.path.realpath(str(path)), str(backup))


def _find_block(lines: List[str], path: Path) -> Optional[Tuple[int, int]]:
    """Indeksy pierwszej i ostatniej linii bloku albo None; uszkodzony blok to błąd."""
    starts = [i for i, l in enumerate(lines) if l.strip() == BEGIN]
    ends = [i for i, l in enumerate(lines) if l.strip() == END]
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise GdError(f"blok graphic-designer w {path} jest uszkodzony (brakuje linii początku albo "
                      "końca, albo jest ich więcej niż po jednej). Niczego nie zmieniam; popraw plik "
                      "ręcznie albo usuń znaczniki.")
    return starts[0], ends[0]


def apply_rules() -> str:
    """Dopisuje albo aktualizuje blok. Zwraca: created, added, updated albo current."""
    launcher = launcher_path()
    if not launcher.is_file():
        raise GdError(f"nie ma stałego skryptu startowego {launcher}. Najpierw zainstaluj go: "
                      f"python3 {_q(plugin_script())} setup-launcher")
    path = rules_file()
    existed = path.is_file()
    text = _read(path) if existed else ""
    eol = "\r\n" if "\r\n" in text else "\n"
    block = rules_block(launcher, eol)
    lines = _split_lines(text)
    span = _find_block(lines, path)
    try:
        if span is not None:
            start, end = span
            tail = lines[end][len(lines[end].rstrip("\r\n")):]
            if "".join(lines[start:end + 1]).rstrip("\r\n") == block.rstrip("\r\n"):
                return "current"
            lines[start:end + 1] = [block.rstrip("\r\n") + tail]
            _backup_once(path)
            _write(path, "".join(lines))
            return "updated"
        new_text = text
        if text:
            if not text.endswith(("\n", "\r")):
                new_text += eol
            new_text += eol
        if existed:
            _backup_once(path)
        _write(path, new_text + block)
    except OSError as e:
        raise GdError(_write_failure(path, e))
    return "added" if existed else "created"


def _write_failure(path: Path, error: Exception) -> str:
    return (f"nie mogę zapisać {path}: {error}. Plik zostaje bez zmian. Uruchom to samo w Terminalu "
            f"(poza Codexem): python3 {_q(launcher_path())} setup-rules --apply")


def remove_rules() -> str:
    """Usuwa tylko blok (i jedną pustą linię przed nim). Zwraca: removed albo absent."""
    path = rules_file()
    if not path.is_file():
        return "absent"
    lines = _split_lines(_read(path))
    span = _find_block(lines, path)
    if span is None:
        return "absent"
    start, end = span
    if start > 0 and lines[start - 1].strip() == "":
        start -= 1
    del lines[start:end + 1]
    try:
        _write(path, "".join(lines))
    except OSError as e:
        raise GdError(_write_failure(path, e).replace("--apply", "--remove"))
    return "removed"


def rules_reference(path: Path) -> bool:
    """Czy któryś plik reguł zawiera ścieżkę `path` (jako literał reguły)."""
    needle = starlark_string(str(path))
    try:
        return any(needle in _read(p) for p in rule_files())
    except GdError:
        return False


def rules_allowing(text: str, launcher: Path) -> Set[str]:
    """Podpolecenia, na które reguły z `text` pozwalają dla danego skryptu (przeszukiwanie tekstu)."""
    body = "".join(l for l in _split_lines(text) if not l.lstrip().startswith("#"))
    quoted = re.escape(starlark_string(str(launcher)))
    pattern = re.compile(r'pattern\s*=\s*\[\s*"python3"\s*,\s*' + quoted + r'\s*(?:,\s*"([\w-]+)"\s*)?[,\]]')
    allowed: Set[str] = set()
    for stmt in re.split(r"(?=prefix_rule\s*\()", body):
        if not stmt.lstrip().startswith("prefix_rule"):
            continue
        if not re.search(r'decision\s*=\s*["\']allow["\']', stmt):
            continue
        m = pattern.search(stmt)
        if m:
            allowed.update([m.group(1)] if m.group(1) else ALLOWED_SUBCOMMANDS)
    return allowed


# ---------------------------------------------------------------- doctor

def _todo(what: str, step: str) -> str:
    return f"TODO: {what}. {NEXT} {step}."


def python_line(version: Tuple[int, ...]) -> str:
    text = ".".join(str(n) for n in version[:3])
    if tuple(version[:2]) >= (3, 9):
        return f"OK: Python {text}."
    return _todo(f"Python {text} jest za stary (potrzebny 3.9 albo nowszy)",
                 "zainstaluj nowszego (macOS: xcode-select --install, Windows: winget install "
                 "Python.Python.3.12)")


def browser_lines() -> List[str]:
    try:
        exe = browser.find()
    except GdError as e:
        detail = str(e).replace("NO BROWSER: ", "", 1).split(". ")[0]
        return [_todo(f"przeglądarka nie jest dostępna ({detail})",
                      "zainstaluj Google Chrome (albo Chromium, Microsoft Edge) albo wskaż przeglądarkę "
                      "zmienną GD_BROWSER=<ścieżka do pliku programu>")]
    lines = [f"OK: przeglądarka: {exe}."]
    if browser.in_codex_sandbox():
        lines.append("INFO: próbny start przeglądarki pominięty: w piaskownicy Codexa na macOS Chrome "
                     "się wywraca. Po konfiguracji Codex uruchamia doctor poza piaskownicą i wtedy "
                     "próba się odbywa.")
        return lines
    result = browser.smoke_test().splitlines()[0]
    if result.startswith("BROWSER-TEST: OK"):
        lines.append("OK: próbny start przeglądarki udał się.")
    else:
        if os.environ.get("CODEX_SANDBOX"):
            step = ("uruchom to polecenie poza piaskownicą (konfiguracja reguł robi to bez pytania "
                    "i jest opisana w procedurze setup)")
        else:
            step = ("sprawdź, czy przeglądarka uruchamia się ręcznie, albo wskaż inną zmienną "
                    "GD_BROWSER=<ścieżka do pliku programu>")
        lines.append(_todo(f"próbny start przeglądarki nie udał się ({result[:300]})", step))
    return lines


def library_line() -> str:
    lib = jobs.library()
    if lib is None:
        return _todo("biblioteka zleceń nie jest ustawiona",
                     f"zapytaj, gdzie trzymać grafiki (np. ~/Documents/Graphics-work), potem "
                     f"{current_command()} library --set <folder>")
    if not lib.is_dir():
        return _todo(f"biblioteka zleceń {lib} nie istnieje (odłączony dysk?)",
                     f"podłącz dysk albo ustaw nowy folder: {current_command()} library --set <folder>")
    return f"OK: biblioteka zleceń: {lib}."


def api_key_lines() -> List[str]:
    if os.environ.get("OPENAI_API_KEY"):
        return ["INFO: Uwaga: OPENAI_API_KEY jest ustawiony, więc obrazy będą liczone według cennika API, "
                "a nie z abonamentu."]
    return []


def sandbox_line() -> str:
    value = os.environ.get("CODEX_SANDBOX")
    if value == "seatbelt":
        return ("INFO: CODEX_SANDBOX=seatbelt: to piaskownica Codexa na macOS; przeglądarka musi "
                "działać poza nią (reguły albo zgoda na uruchomienie poza piaskownicą).")
    if value:
        return f"INFO: CODEX_SANDBOX={value}."
    return "INFO: CODEX_SANDBOX nie jest ustawione: polecenie działa poza piaskownicą Codexa albo poza Codexem."


def _need(what: str, step: str) -> str:
    """TODO na macOS, a poza nim tylko INFO (reguły są potrzebne tylko tam)."""
    if is_mac():
        return _todo(what, step)
    return f"INFO: {what}; na tym systemie jest potrzebne tylko do reguł Codexa na macOS ({step})."


def launcher_lines() -> List[str]:
    path, state, legacy = launcher_path(), launcher_state(), legacy_state()
    old = legacy_launcher_path()
    step = f"python3 {_q(plugin_script())} setup-launcher"
    if state == "ok":
        lines = [f"OK: stały skrypt startowy jest zainstalowany i aktualny: {path}."]
    else:
        what = ("stały skrypt startowy nie jest zainstalowany" if state == "missing"
                else "stały skrypt startowy jest nieaktualny") + f" ({path})"
        if legacy == "ours":
            what += (f"; jego dawna kopia leży jeszcze w {old}, w miejscu, które agent z piaskownicy "
                     "mógłby zmienić")
        lines = [_need(what, step + " (zainstaluje w chronionym miejscu i usunie dawny plik)")]
    if state == "ok" and legacy == "ours":
        lines.append(_need(f"dawny stały skrypt startowy nadal leży w {old} (miejsce niechronione)",
                           step + " (usunie go)"))
    return lines


def rule_files() -> List[Path]:
    return sorted(p for p in rules_dir().glob("*.rules") if p.is_file())


def rules_lines() -> List[str]:
    launcher = launcher_path()
    files = rule_files()
    texts = [_read(p) for p in files]
    allowed: Set[str] = set()
    for text in texts:
        allowed |= rules_allowing(text, launcher)
    missing = [s for s in ALLOWED_SUBCOMMANDS if s not in allowed]
    has_block = any(BEGIN in text for text in texts)
    step = f"python3 {_q(plugin_script())} setup-rules"
    if not missing:
        lines = ["OK: reguły Codexa pozwalają na: " + ", ".join(ALLOWED_SUBCOMMANDS)
                 + " (poza piaskownicą, bez pytania)."]
    elif has_block:
        what = (f"blok reguł graphic-designer jest nieaktualny: brakuje reguł dla {', '.join(missing)} "
                f"albo wskazuje inną ścieżkę niż {launcher}")
        old = legacy_launcher_path()
        if any(starlark_string(str(old)) in t for t in texts):
            what += f" (reguły ufają jeszcze dawnemu plikowi {old}, który agent z piaskownicy mógłby zmienić)"
        lines = [_todo(what, f"{step} --apply (zaktualizuje blok po Twojej zgodzie), potem uruchom Codex "
                             "ponownie")]
    else:
        what = "brak reguł Codexa dla: " + ", ".join(missing)
        after = "" if launcher_state() == "ok" else " po zainstalowaniu stałego skryptu"
        todo = _todo(what, f"{step} (pokaże propozycję; zapis dopiero po Twojej zgodzie){after}")
        lines = [todo if is_mac() else
                 f"INFO: {what}; na tym systemie są potrzebne tylko na macOS."]
    lines.append(execpolicy_line(launcher, files, "render" in missing))
    return lines


def execpolicy_line(launcher: Path, files: List[Path], render_missing: bool) -> str:
    codex = shutil.which("codex")
    if not codex:
        return ("INFO: nie ma polecenia codex w PATH, więc nie sprawdzam reguł przez execpolicy "
                "(to sprawdzenie jest dokładne, ale opcjonalne).")
    if not files:
        return f"INFO: pomijam sprawdzenie execpolicy: w {rules_dir()} nie ma plików z regułami."
    cmd = [codex, "execpolicy", "check"]
    for f in files:
        cmd += ["--rules", str(f)]
    cmd += ["--", "python3", str(launcher), "render"]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        if proc.returncode != 0:
            raise ValueError(f"kod wyjścia {proc.returncode}")
        decision = json.loads(proc.stdout.decode("utf-8", "replace")).get("decision")
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        return f"INFO: nie udało się uruchomić codex execpolicy check ({e}); nic złego, to sprawdzenie opcjonalne."
    if decision == "allow":
        return "OK: codex execpolicy potwierdza: render ze stałego skryptu wolno uruchomić poza piaskownicą bez pytania."
    shown = decision or "brak pasującej reguły"
    if render_missing:
        return f"INFO: codex execpolicy: dla render {shown}, zgodnie z wynikiem wyżej."
    return _todo(f"codex execpolicy nie pozwala na render ze stałego skryptu (decyzja: {shown})",
                 f"python3 {_q(plugin_script())} setup-rules --apply, potem uruchom Codex ponownie")


def command_line() -> str:
    if launcher_path().is_file():
        return (f"INFO: Polecenie do uruchamiania: python3 {_q(launcher_path())} <polecenie>. Używaj "
                "dokładnie tej pełnej ścieżki, bez skrótów i bez zmiennych przed python3, bo reguły "
                "Codexa dopasowują początek polecenia.")
    return (f"INFO: Polecenie do uruchamiania (stałego skryptu jeszcze nie ma): "
            f"python3 {_q(plugin_script())} <polecenie>.")


def doctor_lines() -> List[str]:
    steps: List[Tuple[str, Callable[[], List[str]]]] = [
        ("Python", lambda: [python_line(tuple(sys.version_info[:3]))]),
        ("przeglądarka", lambda: browser_lines()),
        ("biblioteka", lambda: [library_line()]),
        ("klucz API", lambda: api_key_lines()),
        ("piaskownica", lambda: [sandbox_line()]),
        ("stały skrypt", lambda: launcher_lines()),
        ("reguły", lambda: rules_lines()),
        ("polecenie", lambda: [command_line()]),
    ]
    out: List[str] = []
    for name, step in steps:
        try:
            out.extend(step())
        except Exception as e:  # doctor niczego nie psuje i zawsze kończy się kodem 0
            out.append(f"INFO: nie udało się sprawdzić ({name}): {e}")
    return out
