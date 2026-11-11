"""Przeglądarka bez okna: wyszukiwanie, zrzut ekranu, DOM po skryptach, PDF."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from . import png
from .common import GdError

TIMEOUT = 120
VIRTUAL_TIME_MS = 5000

_MAC = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"]
_LINUX = ["google-chrome", "chromium", "chromium-browser", "microsoft-edge"]
_WIN = [("Google", "Chrome", "Application", "chrome.exe"),
        ("Microsoft", "Edge", "Application", "msedge.exe")]

_HINT = ("zainstaluj Google Chrome (albo Chromium, Microsoft Edge) albo wskaż przeglądarkę zmienną "
         "środowiskową GD_BROWSER=<ścieżka do pliku programu>")


def _candidates() -> List[Path]:
    out: List[Path] = [Path(p) for p in _MAC]
    for name in _LINUX:
        found = shutil.which(name)
        if found:
            out.append(Path(found))
    for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            out.extend(Path(base).joinpath(*parts) for parts in _WIN)
    return out


def find() -> Path:
    env = os.environ.get("GD_BROWSER")
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return p
        raise GdError(f"NO BROWSER: GD_BROWSER wskazuje {env}, a tam nie ma pliku. "
                      f"Popraw ścieżkę albo usuń zmienną. Inaczej: {_HINT}")
    for p in _candidates():
        if p.is_file():
            return p
    raise GdError(f"NO BROWSER: nie znalazłem przeglądarki. {_HINT}")


# Wywrotka przeglądarki: sygnały ILL (4), TRAP (5), ABRT (6), BUS (10), SEGV (11). Python widzi je
# jako kody ujemne, powłoka jako 128 + numer sygnału. KILL (-9, np. brak pamięci) i TERM (-15)
# oraz zwykłe kody błędu (1, 2) to nie ślad piaskownicy.
_CRASH_CODES = (-4, -5, -6, -10, -11, 132, 133, 134, 138, 139)

SANDBOX_HINT = ("SANDBOX?: przeglądarka wywróciła się zaraz po starcie. Najpewniej piaskownica "
                "Codexa nie pozwala jej uruchomić. Poproś osobę o jednorazową zgodę i uruchom to "
                "samo polecenie jeszcze raz poza piaskownicą. Nie zastępuj składania innym "
                "narzędziem.")


BLOCKED_HINT = ("SANDBOX?: wykryłem piaskownicę Codexa na macOS (CODEX_SANDBOX=seatbelt), w której "
                "Chrome się wywraca, więc go tu nie uruchamiam. Poproś osobę o jednorazową zgodę i "
                "uruchom to samo polecenie jeszcze raz poza piaskownicą. Próbę w piaskownicy wymusisz "
                "zmienną GD_BROWSER_TRY=1. Nie zastępuj składania innym narzędziem.")

SKIPPED_LINE = ("BROWSER-TEST: SKIPPED (piaskownica Codexa na macOS: Chrome się tu wywraca, a system "
                "pokazuje okno „Google Chrome quit unexpectedly”). Uruchom `env` poza piaskownicą.")


def in_codex_sandbox() -> bool:
    """Piaskownica Codexa na macOS (Seatbelt), chyba że wymuszono próbę zmienną GD_BROWSER_TRY."""
    return os.environ.get("CODEX_SANDBOX") == "seatbelt" and not os.environ.get("GD_BROWSER_TRY")


class BrowserExit(GdError):
    """Przeglądarka zakończyła się błędem; `code` to jej kod wyjścia."""

    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


def is_crash(code: int) -> bool:
    return code in _CRASH_CODES


def _is_root() -> bool:
    return hasattr(os, "geteuid") and os.geteuid() == 0


def _exec(target: str, extra: List[str], w: int, h: int, capture_stdout: bool = False,
          timeout: int = TIMEOUT) -> str:
    exe = find()
    if in_codex_sandbox():
        raise GdError(BLOCKED_HINT)
    profile = tempfile.mkdtemp(prefix="gd-profile-")
    try:
        cmd = [str(exe), "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               "--no-default-browser-check", f"--user-data-dir={profile}",
               f"--window-size={w},{h}", f"--virtual-time-budget={VIRTUAL_TIME_MS}",
               "--default-background-color=00000000"]
        if _is_root():
            cmd.append("--no-sandbox")
        if os.name == "posix":
            cmd.append("--disable-dev-shm-usage")
        cmd += extra + [target]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise GdError(f"przeglądarka nie skończyła w {timeout} s i została przerwana")
        except OSError as e:
            raise GdError(f"nie mogę uruchomić przeglądarki {exe}: {e}")
        stderr = proc.stderr.decode("utf-8", "replace")
        stderr = "\n".join(l for l in stderr.splitlines()
                           if "Trying to load the allocator" not in l)
        _run.last_stderr = stderr  # type: ignore[attr-defined]
        if proc.returncode != 0:
            msg = f"przeglądarka zakończyła się kodem {proc.returncode}: {stderr[-600:]}"
            if is_crash(proc.returncode):
                msg = f"{SANDBOX_HINT} {msg}"
            raise BrowserExit(msg, proc.returncode)
        return proc.stdout.decode("utf-8", "replace") if capture_stdout else ""
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def _run(html: Path, extra: List[str], w: int, h: int, capture_stdout: bool = False) -> str:
    return _exec(Path(html).resolve().as_uri(), extra, w, h, capture_stdout)


def smoke_test(timeout: int = 30) -> str:
    """Raz uruchamia znalezioną przeglądarkę na pustej stronie. Zwraca linię `BROWSER-TEST: …`."""
    if in_codex_sandbox():
        return SKIPPED_LINE + "\n" + BLOCKED_HINT
    try:
        _exec("about:blank", ["--dump-dom"], 400, 300, capture_stdout=True, timeout=timeout)
    except BrowserExit as e:
        return f"BROWSER-TEST: FAILED (kod {e.code}) — {e}"
    except (GdError, OSError) as e:
        return f"BROWSER-TEST: FAILED — {e}"
    return "BROWSER-TEST: OK"


def _tail() -> str:
    return getattr(_run, "last_stderr", "")[-600:]


def screenshot(html: Path, out: Path, w: int, h: int) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="gd-shot-"))
    try:
        shot = tmp / "shot.png"
        _run(html, [f"--screenshot={shot}"], w, h)
        if not shot.is_file():
            raise GdError(f"przeglądarka nie zapisała zrzutu. {_tail()}")
        got = png.size(shot)
        if tuple(got) != (w, h):
            raise GdError(f"zrzut ma rozmiar {got[0]}×{got[1]} zamiast {w}×{h}. {_tail()}")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(shot, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def dump_dom(html: Path, w: int, h: int) -> str:
    return _run(html, ["--dump-dom"], w, h, capture_stdout=True)


def pdf(html: Path, out: Path, w: int, h: int) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="gd-pdf-"))
    try:
        dest = tmp / "out.pdf"
        _run(html, [f"--print-to-pdf={dest}", "--no-pdf-header-footer"], w, h)
        if not dest.is_file():
            raise GdError(f"przeglądarka nie zapisała PDF. {_tail()}")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(dest, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
