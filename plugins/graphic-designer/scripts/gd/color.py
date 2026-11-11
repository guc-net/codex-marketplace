"""Kolory HEX i kontrast WCAG 2.x."""
from __future__ import annotations

import re

from .common import GdError


def parse_hex(s: str) -> tuple:
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", str(s).strip())
    if not m:
        raise GdError(f"zły kolor „{s}”: oczekiwano #RRGGBB")
    h = m.group(1)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def luminance(rgb) -> float:
    def lin(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    """Stosunek kontrastu WCAG; argumenty: napis #RRGGBB albo krotka RGB."""
    la, lb = (luminance(parse_hex(x) if isinstance(x, str) else x) for x in (a, b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)
