"""Znaki w fontach: które znaki tekstu font ma, a których mu brakuje (tabela cmap)."""
from __future__ import annotations

import struct
from pathlib import Path

from .common import GdError

_SFNT = (b"\x00\x01\x00\x00", b"OTTO", b"true")
_MAX_CP = 0x10FFFF


def _u16(d: bytes, o: int) -> int:
    return struct.unpack_from(">H", d, o)[0]


def _u32(d: bytes, o: int) -> int:
    return struct.unpack_from(">I", d, o)[0]


def _find_cmap(d: bytes, name: str) -> int:
    magic = d[:4]
    base = 0
    if magic == b"ttcf":  # kolekcja: bierzemy pierwszy font
        base = _u32(d, 12)
        magic = d[base:base + 4]
    if magic not in _SFNT:
        raise GdError(f"{name} nie jest fontem TTF ani OTF.")
    for i in range(_u16(d, base + 4)):
        o = base + 12 + 16 * i
        if d[o:o + 4] == b"cmap":
            return _u32(d, o + 8)
    raise GdError(f"{name}: font nie ma tabeli znaków (cmap).")


def _format4(d: bytes, o: int) -> set:
    seg = _u16(d, o + 6) // 2
    end, start = o + 14, o + 16 + 2 * seg
    delta, rng = start + 2 * seg, start + 4 * seg
    out = set()
    for i in range(seg):
        e, s = _u16(d, end + 2 * i), _u16(d, start + 2 * i)
        dl, ro = _u16(d, delta + 2 * i), _u16(d, rng + 2 * i)
        for c in range(s, min(e, 0xFFFE) + 1):
            if ro == 0:
                gid = (c + dl) & 0xFFFF
            else:
                p = rng + 2 * i + ro + 2 * (c - s)
                if p + 2 > len(d):
                    continue
                gid = _u16(d, p)
                if gid:
                    gid = (gid + dl) & 0xFFFF
            if gid:
                out.add(c)
    return out


def _format12(d: bytes, o: int) -> set:
    out = set()
    for i in range(_u32(d, o + 12)):
        s, e, g = struct.unpack_from(">III", d, o + 16 + 12 * i)
        for c in range(s, min(e, _MAX_CP) + 1):
            if g + (c - s):
                out.add(c)
    return out


def _rank(platform: int, encoding: int):
    if platform == 3 and encoding == 10:
        return 0
    if platform == 3 and encoding == 1:
        return 1
    if platform == 0:
        return 2
    return None


def codepoints(path: Path) -> set:
    """Zbiór kodów znaków (Unicode), które font ma. Tylko TTF i OTF."""
    path = Path(path)
    try:
        d = path.read_bytes()
    except OSError as e:
        raise GdError(f"nie mogę odczytać fontu {path}: {e}")
    if d[:4] in (b"wOFF", b"wOF2"):
        raise GdError(f"{path.name}: font w formacie WOFF nie jest obsługiwany, podaj TTF albo OTF.")
    try:
        cmap = _find_cmap(d, path.name)
        candidates = []
        for i in range(_u16(d, cmap + 2)):
            platform, encoding, off = struct.unpack_from(">HHI", d, cmap + 4 + 8 * i)
            rank = _rank(platform, encoding)
            fmt = _u16(d, cmap + off)
            if rank is not None and fmt in (4, 12):
                candidates.append((rank, cmap + off, fmt))
        if not candidates:
            raise GdError(f"{path.name}: font nie ma obsługiwanej tabeli znaków Unicode.")
        _, o, fmt = min(candidates)
        return _format4(d, o) if fmt == 4 else _format12(d, o)
    except struct.error:
        raise GdError(f"{path.name}: uszkodzony plik fontu.")


def missing_chars(path: Path, text: str) -> list:
    """Znaki z tekstu, których font nie ma: bez białych znaków, bez powtórzeń, po kolei."""
    have = codepoints(path)
    out = []
    for ch in text:
        if ch.isspace() or ch in out:
            continue
        if ord(ch) not in have:
            out.append(ch)
    return out
