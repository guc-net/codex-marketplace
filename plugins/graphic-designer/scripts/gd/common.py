"""Wspólne drobiazgi: błąd użytkownika, komunikaty, ustawienia, nazwy."""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent


class GdError(Exception):
    """Błąd użytkownika — drukujemy komunikat bez śladu stosu."""


def info(text: str = "") -> None:
    """Wypisz na stdout; UTF-8 także na Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass
    print(text)


def gd_home() -> Path:
    """Folder ustawień pluginu: GD_HOME albo ~/.graphic-designer."""
    home = os.environ.get("GD_HOME")
    return Path(home).expanduser() if home else Path.home() / ".graphic-designer"


def settings_path() -> Path:
    return gd_home() / "settings.json"


def read_settings() -> dict:
    path = settings_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise GdError(f"nie mogę odczytać ustawień {path}: {e}")
    return data if isinstance(data, dict) else {}


def write_settings(d: dict) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()


_EXTRA = {"ł": "l", "Ł": "l", "ø": "o", "đ": "d", "ß": "ss"}


def slug(text: str) -> str:
    """ASCII kebab-case; polskie litery transliterowane."""
    text = "".join(_EXTRA.get(c, c) for c in text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
