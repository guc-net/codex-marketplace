"""Minimalny zapis PNG bez zależności — do obrazów testowych."""
import struct
import zlib


def png(sciezka, szer, wys, kolor, pasek=(40, 37, 34)):
    wiersze = []
    for y in range(wys):
        k = pasek if y < wys // 12 or y >= wys - wys // 12 else kolor
        wiersze.append(b"\x00" + bytes(k) * szer)

    def blok(typ, dane):
        return struct.pack(">I", len(dane)) + typ + dane + struct.pack(">I", zlib.crc32(typ + dane) & 0xFFFFFFFF)

    with open(sciezka, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(blok(b"IHDR", struct.pack(">IIBBBBB", szer, wys, 8, 2, 0, 0, 0)))
        f.write(blok(b"IDAT", zlib.compress(b"".join(wiersze), 9)))
        f.write(blok(b"IEND", b""))
