#!/usr/bin/env python3
"""Stały skrypt startowy pluginu graphic-designer.

Ten plik instaluje polecenie `designer.py setup-launcher` do folderu ustawień
(GD_HOME albo ~/.graphic-designer). Ścieżka pluginu w Codexie zawiera numer wersji
i zmienia się przy każdej aktualizacji, a reguły Codexa dopasowują dokładną ścieżkę.
Dlatego reguły wskazują ten plik, a on sam znajduje najnowszą wersję pluginu
i uruchamia jej `scripts/designer.py` z tymi samymi argumentami.

Zmienne: CODEX_HOME (domyślnie ~/.codex), GD_PLUGIN_ROOT (folder pluginu zamiast szukania).
Plik jest nadpisywany przez `setup-launcher`; nie edytuj go ręcznie.
"""
from __future__ import annotations

import os
import re
import runpy
import sys
from pathlib import Path

INSTALL_HINT = "codex plugin add graphic-designer@guc-net"


def cache_dir() -> Path:
    home = os.environ.get("CODEX_HOME")
    base = Path(home).expanduser() if home else Path.home() / ".codex"
    return base / "plugins" / "cache"


def _version_key(version: str) -> tuple:
    return tuple(int(n) for n in re.findall(r"\d+", version))


def find_designer() -> Path:
    """Najnowszy scripts/designer.py pluginu; LookupError z opisem po polsku, gdy go nie ma."""
    override = os.environ.get("GD_PLUGIN_ROOT")
    if override:
        script = Path(override).expanduser() / "scripts" / "designer.py"
        if script.is_file():
            return script
        raise LookupError(f"GD_PLUGIN_ROOT wskazuje {override}, a tam nie ma scripts/designer.py. "
                          "Popraw ścieżkę albo usuń zmienną.")
    cache = cache_dir()
    found = []
    for script in cache.glob("*/graphic-designer/*/scripts/designer.py"):
        if script.is_file():
            found.append((_version_key(script.parent.parent.name), script.parent.parent.name, script))
    if not found:
        raise LookupError(f"nie znalazłem pluginu graphic-designer w {cache}. Zainstaluj go "
                          f"({INSTALL_HINT}) albo wskaż jego folder zmienną GD_PLUGIN_ROOT.")
    return max(found)[2]


def main() -> int:
    try:
        script = find_designer()
    except LookupError as e:
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except (ValueError, OSError):
                    pass
        print(f"PROBLEM: {e}", file=sys.stderr)
        return 1
    sys.argv[0] = str(script)
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
