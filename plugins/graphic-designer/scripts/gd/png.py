"""Odczyt PNG bez zależności: wymiary, piksele (z alfą), średni kolor obszaru."""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

from .common import GdError

_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


class Image:
    """Obraz 8-bit; wiersze trzymane jako bytes (kanały po kolei)."""

    def __init__(self, width: int, height: int, channels: int, rows: list):
        self.width = width
        self.height = height
        self.channels = channels
        self.rows = rows

    def pixel(self, x: int, y: int) -> tuple:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise GdError(f"piksel ({x}, {y}) leży poza obrazem {self.width}×{self.height}.")
        c = self.channels
        row = self.rows[y]
        i = x * c
        if c == 1:
            v = row[i]
            return (v, v, v, 255)
        if c == 2:
            v = row[i]
            return (v, v, v, row[i + 1])
        if c == 3:
            return (row[i], row[i + 1], row[i + 2], 255)
        return (row[i], row[i + 1], row[i + 2], row[i + 3])


def _header_and_chunks(path: Path):
    try:
        data = Path(path).read_bytes()
    except OSError as e:
        raise GdError(f"nie mogę odczytać pliku {path}: {e}")
    if data[:8] != _SIGNATURE:
        raise GdError(f"{Path(path).name} nie jest plikiem PNG.")
    return data


def size(path: Path) -> tuple:
    """(szerokość, wysokość) z nagłówka IHDR, bez dekodowania obrazu."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
    except OSError as e:
        raise GdError(f"nie mogę odczytać pliku {path}: {e}")
    if len(head) < 24 or head[:8] != _SIGNATURE or head[12:16] != b"IHDR":
        raise GdError(f"{Path(path).name} nie jest plikiem PNG.")
    return struct.unpack(">II", head[16:24])


def _unfilter(raw: bytes, w: int, h: int, bpp: int) -> list:
    stride = w * bpp
    if len(raw) < h * (stride + 1):
        raise GdError("plik PNG jest uszkodzony (za mało danych obrazu).")
    prev = bytearray(stride)
    rows = []
    for y in range(h):
        p = y * (stride + 1)
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        if f == 0:
            pass
        elif f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif f == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        else:
            raise GdError(f"plik PNG jest uszkodzony (nieznany filtr {f}).")
        rows.append(bytes(line))
        prev = line
    return rows


def read(path: Path) -> Image:
    name = Path(path).name
    data = _header_and_chunks(path)
    i, idat, header = 8, [], None
    while i + 8 <= len(data):
        n, typ = struct.unpack(">I4s", data[i:i + 8])
        chunk = data[i + 8:i + 8 + n]
        i += 12 + n
        if typ == b"IHDR":
            if len(chunk) != 13:
                raise GdError(f"{name}: uszkodzony nagłówek PNG.")
            header = struct.unpack(">IIBBBBB", chunk)
        elif typ == b"IDAT":
            idat.append(chunk)
        elif typ == b"IEND":
            break
    if header is None or not idat:
        raise GdError(f"{name}: uszkodzony plik PNG (brak nagłówka albo danych).")
    w, h, depth, ctype, _, _, interlace = header
    if ctype == 3:
        raise GdError(f"{name}: PNG z paletą nie jest obsługiwany. Zapisz obraz jako RGB albo RGBA.")
    if depth == 16:
        raise GdError(f"{name}: PNG 16-bitowy nie jest obsługiwany. Zapisz obraz jako 8-bitowy.")
    if interlace:
        raise GdError(f"{name}: PNG z przeplotem nie jest obsługiwany. Zapisz obraz bez przeplotu.")
    channels = _CHANNELS.get(ctype)
    if channels is None or depth != 8:
        raise GdError(f"{name}: nieobsługiwany rodzaj PNG (głębia {depth}, typ {ctype}).")
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as e:
        raise GdError(f"{name}: uszkodzone dane obrazu PNG ({e}).")
    return Image(w, h, channels, _unfilter(raw, w, h, channels))


def region_mean(img: Image, box: tuple, ignore_transparent: bool = True) -> tuple:
    """Średni kolor (r, g, b) w obszarze (x, y, szer, wys), przyciętym do obrazu."""
    x, y, bw, bh = box
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(img.width, int(x + bw)), min(img.height, int(y + bh))
    if x1 <= x0 or y1 <= y0:
        raise GdError(f"obszar {tuple(box)} leży poza obrazem {img.width}×{img.height}.")
    c = img.channels
    sr = sg = sb = n = 0
    for yy in range(y0, y1):
        row = img.rows[yy]
        for xx in range(x0, x1):
            i = xx * c
            if c == 1:
                r = g = b = row[i]
                a = 255
            elif c == 2:
                r = g = b = row[i]
                a = row[i + 1]
            elif c == 3:
                r, g, b, a = row[i], row[i + 1], row[i + 2], 255
            else:
                r, g, b, a = row[i], row[i + 1], row[i + 2], row[i + 3]
            if ignore_transparent and a == 0:
                continue
            sr += r
            sg += g
            sb += b
            n += 1
    if n == 0:
        raise GdError("w obszarze nie ma widocznych pikseli (wszystkie są przezroczyste).")
    return (round(sr / n), round(sg / n), round(sb / n))
