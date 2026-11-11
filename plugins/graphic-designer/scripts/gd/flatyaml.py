"""Płaski YAML: jedna para `klucz: wartość` na linię (napis, liczba, true/false)."""
from __future__ import annotations

import json
import re

from .common import GdError


def _only_comment(rest: str) -> bool:
    rest = rest.strip()
    return not rest or rest.startswith("#")


def _value(w: str, source: str, nr: int):
    if w.startswith('"'):
        try:
            val, end = json.JSONDecoder().raw_decode(w)
        except ValueError:
            raise GdError(f"{source}:{nr}: zły napis w cudzysłowie: {w}")
        if not isinstance(val, str) or not _only_comment(w[end:]):
            raise GdError(f"{source}:{nr}: zły napis w cudzysłowie: {w}")
        return val
    if w.startswith("'"):
        i = 1
        while i < len(w):
            if w[i] == "'":
                if w[i + 1:i + 2] == "'":
                    i += 2
                    continue
                break
            i += 1
        else:
            raise GdError(f"{source}:{nr}: niezamknięty napis w apostrofach: {w}")
        if not _only_comment(w[i + 1:]):
            raise GdError(f"{source}:{nr}: zły napis w apostrofach: {w}")
        return w[1:i].replace("''", "'")
    w = re.sub(r"\s+#.*$", "", w)
    if re.fullmatch(r"-?\d+", w):
        return int(w)
    if w == "true":
        return True
    if w == "false":
        return False
    if w in ("", "~", "null"):
        return None
    return w


def parse(text: str, source: str) -> dict:
    data: dict = {}
    for nr, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise GdError(f"{source}:{nr}: oczekiwano „klucz: wartość”, jest: {line!r}")
        key, value = line.split(":", 1)
        data[key.strip()] = _value(value.strip(), source, nr)
    return data


def dump(d: dict) -> str:
    lines = []
    for k, v in d.items():
        if v is None:
            lines.append(f"{k}:")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, int):
            lines.append(f"{k}: {v}")
        else:
            lines.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
    return "\n".join(lines) + ("\n" if lines else "")
