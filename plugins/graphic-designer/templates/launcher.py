#!/usr/bin/env python3
"""Stały skrypt startowy pluginu graphic-designer.

Instaluje go polecenie `designer.py setup-launcher` do `<CODEX_HOME albo ~/.codex>/graphic-designer/`.
Ścieżka pluginu w Codexie zawiera numer wersji i zmienia się przy każdej aktualizacji, a reguły
Codexa dopasowują dokładną ścieżkę. Dlatego reguły wskazują ten plik, a on sam znajduje najnowszą
wersję pluginu i uruchamia jej `scripts/designer.py` z tymi samymi argumentami.

Uruchamia tylko pluginy z `<CODEX_HOME>/plugins/cache/guc-net/graphic-designer/<X.Y.Z>/`, w których
jest `scripts/designer.py` i `plugin.json` z nazwą „graphic-designer”. Zmienna CODEX_HOME (domyślnie
~/.codex) to jedyny przełącznik. Plik jest nadpisywany przez `setup-launcher`; nie edytuj go ręcznie.
"""
from __future__ import annotations

import json
import os
import re
import runpy
import sys
from pathlib import Path

MARKETPLACE = "guc-net"
PLUGIN = "graphic-designer"
INSTALL_HINT = "codex plugin add graphic-designer@guc-net"
_RELEASE = re.compile(r"^\d+\.\d+\.\d+$")


def cache_dir() -> Path:
    home = os.environ.get("CODEX_HOME")
    base = Path(home).expanduser() if home else Path.home() / ".codex"
    return base / "plugins" / "cache"


def _is_our_plugin(manifest: Path) -> bool:
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("name") == PLUGIN
    except (OSError, ValueError, AttributeError):
        return False


def find_designer() -> Path:
    """Najnowszy `scripts/designer.py`; LookupError z opisem po polsku, gdy go nie ma.

    Bierzemy tylko katalogi z samą wersją X.Y.Z (bez przedwersji, kopii i śmieci) z marketplace
    guc-net, z prawdziwym plugin.json. Wersje porównujemy liczbowo (0.10.0 > 0.9.5)."""
    base = cache_dir() / MARKETPLACE / PLUGIN
    found = []
    if base.is_dir():
        for folder in base.iterdir():
            script = folder / "scripts" / "designer.py"
            if (_RELEASE.fullmatch(folder.name) and folder.is_dir() and script.is_file()
                    and _is_our_plugin(folder / "plugin.json")):
                found.append((tuple(int(n) for n in folder.name.split(".")), script))
    if not found:
        raise LookupError(f"nie znalazłem pluginu graphic-designer w {base}. Zainstaluj go albo "
                          f"zaktualizuj ({INSTALL_HINT}).")
    return max(found)[1]


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
