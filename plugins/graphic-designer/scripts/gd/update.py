"""Sprawdzanie, czy jest nowsza wersja pluginu (raz dziennie, bez błędu przy braku sieci)."""
from __future__ import annotations

import datetime
import json
import os
import re
import urllib.request
from pathlib import Path

from gd.common import PLUGIN_ROOT

SOURCE_URL = "https://raw.githubusercontent.com/guc-net/codex-marketplace/main/plugins/graphic-designer/"
MARKETPLACE = "guc-net"


def default_cache() -> Path:
    home = os.environ.get("GD_HOME")
    base = Path(home).expanduser() if home else Path.home() / ".graphic-designer"
    return base / "update.json"


def installed_version() -> str:
    return json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]


def _tuple(version: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", version)[:3])


def newer_entries(changelog: str, since: str) -> str:
    """Sekcje CHANGELOG („## x.y.z …”) nowsze niż zainstalowana wersja."""
    out, current = [], False
    for line in changelog.splitlines():
        m = re.match(r"^##\s+\[?v?(\d+\.\d+\.\d+)", line)
        if m:
            current = _tuple(m.group(1)) > _tuple(since)
        if current:
            out.append(line)
    return "\n".join(out).strip()


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "graphic-designer-plugin"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode("utf-8")


def check(cache: Path, source: str, force: bool = False) -> str:
    """Zwróć tekst wyniku: zaczyna się od AKTUALNA, NOWA WERSJA albo NIE SPRAWDZONO."""
    installed = installed_version()
    today = datetime.date.today().isoformat()
    if not force and cache.is_file():
        try:
            state = json.loads(cache.read_text(encoding="utf-8"))
            if state.get("date") == today and state.get("installed") == installed and state.get("result"):
                return state["result"] + "\n(Sprawdzono już dziś.)"
        except (ValueError, OSError):
            pass
    try:
        latest = json.loads(_fetch(source + "plugin.json"))["version"]
        changelog = _fetch(source + "CHANGELOG.md")
    except Exception as e:  # sieć bywa zablokowana przez sandbox, to nie jest błąd użytkownika
        return f"NIE SPRAWDZONO: brak połączenia ({type(e).__name__}). Zainstalowana wersja: {installed}."
    if _tuple(latest) > _tuple(installed):
        result = (f"NOWA WERSJA {latest} (zainstalowana {installed}).\n"
                  "Co nowego:\n" + (newer_entries(changelog, installed) or "(brak opisu)") + "\n"
                  f"Aktualizacja: codex plugin marketplace upgrade {MARKETPLACE}, potem nowa rozmowa.")
    else:
        result = f"AKTUALNA: {installed}."
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"date": today, "installed": installed, "result": result},
                                    ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return result
