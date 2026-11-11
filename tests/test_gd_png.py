"""Testy odczytu PNG bez zależności."""
from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "plugins" / "graphic-designer" / "scripts"))
sys.path.insert(0, str(REPO / "tests"))

from gd import png  # noqa: E402
from gd.common import GdError  # noqa: E402
import png as testpng  # noqa: E402


def _chunk(typ, data):
    return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def write_raw(path, w, h, depth, ctype, rows, interlace=0):
    raw = b"".join(b"\x00" + r for r in rows)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, depth, ctype, 0, 0, interlace)))
        f.write(_chunk(b"IDAT", zlib.compress(raw)))
        f.write(_chunk(b"IEND", b""))


class PngTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_rgb_fixture(self):
        p = self.dir / "a.png"
        testpng.png(p, 20, 24, (10, 200, 30))
        img = png.read(p)
        self.assertEqual((img.width, img.height), (20, 24))
        self.assertEqual(img.pixel(10, 12), (10, 200, 30, 255))
        self.assertEqual(png.size(p), (20, 24))

    def test_reads_rgba_alpha(self):
        p = self.dir / "b.png"
        rows = [bytes([1, 2, 3, 0, 9, 8, 7, 255]), bytes([4, 5, 6, 128, 0, 0, 0, 255])]
        write_raw(p, 2, 2, 8, 6, rows)
        img = png.read(p)
        self.assertEqual(img.pixel(0, 0)[3], 0)
        self.assertEqual(img.pixel(1, 0), (9, 8, 7, 255))
        self.assertEqual(img.pixel(0, 1), (4, 5, 6, 128))

    def test_gray_and_gray_alpha(self):
        p = self.dir / "g.png"
        write_raw(p, 2, 1, 8, 0, [bytes([10, 20])])
        self.assertEqual(png.read(p).pixel(1, 0), (20, 20, 20, 255))
        p2 = self.dir / "ga.png"
        write_raw(p2, 2, 1, 8, 4, [bytes([10, 0, 20, 255])])
        self.assertEqual(png.read(p2).pixel(0, 0), (10, 10, 10, 0))

    def test_filters(self):
        # filtr 1 (Sub) i 2 (Up) na RGB 2x2
        p = self.dir / "f.png"
        raw = b"\x01" + bytes([5, 5, 5, 1, 1, 1]) + b"\x02" + bytes([1, 1, 1, 1, 1, 1])
        with open(p, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            f.write(_chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)))
            f.write(_chunk(b"IDAT", zlib.compress(raw)))
            f.write(_chunk(b"IEND", b""))
        img = png.read(p)
        self.assertEqual(img.pixel(1, 0)[:3], (6, 6, 6))
        self.assertEqual(img.pixel(0, 1)[:3], (6, 6, 6))
        self.assertEqual(img.pixel(1, 1)[:3], (7, 7, 7))

    def _write_filtered(self, path, w, h, rows):
        """rows: lista (filtr, bajty) dla obrazu RGB 8-bit."""
        raw = b"".join(bytes([f]) + r for f, r in rows)
        with open(path, "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\n")
            fh.write(_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)))
            fh.write(_chunk(b"IDAT", zlib.compress(raw)))
            fh.write(_chunk(b"IEND", b""))

    def test_filter_none_and_average(self):
        # wiersz 0: filtr 0; wiersz 1: filtr 3 (średnia z lewego i górnego, w dół)
        # piksel 0: lewy=0, górny=(10,20,30) -> pred (5,10,15); surowe (1,2,3) -> (6,12,18)
        # piksel 1: lewy=(6,12,18), górny=(40,50,60) -> pred (23,31,39); surowe (4,5,6) -> (27,36,45)
        p = self.dir / "avg.png"
        self._write_filtered(p, 2, 2, [
            (0, bytes([10, 20, 30, 40, 50, 60])),
            (3, bytes([1, 2, 3, 4, 5, 6])),
        ])
        img = png.read(p)
        self.assertEqual(img.pixel(0, 0), (10, 20, 30, 255))
        self.assertEqual(img.pixel(1, 0), (40, 50, 60, 255))
        self.assertEqual(img.pixel(0, 1), (6, 12, 18, 255))
        self.assertEqual(img.pixel(1, 1), (27, 36, 45, 255))

    def test_filter_paeth_picks_a_b_and_c(self):
        # wiersz 0 (filtr 0): piksel 0 = c = (95,95,50), piksel 1 = b = (100,10,100)
        # wiersz 1 (filtr 4), piksel 0: a=c=0, wybór b=(95,95,50);
        #   surowe (171,5,216) -> (10,100,10) (=: a dla piksela 1)
        # piksel 1, a=(10,100,10) b=(100,10,100) c=(95,95,50), kanał po kanale:
        #   R: a=10,b=100,c=95 -> p=15, odległości 5/85/80 -> wybiera a=10
        #   G: a=100,b=10,c=95 -> p=15, odległości 85/5/80 -> wybiera b=10
        #   B: a=10,b=100,c=50 -> p=60, odległości 50/40/10 -> wybiera c=50
        #   surowe (190,50,205) -> (200,60,255)
        p = self.dir / "paeth.png"
        self._write_filtered(p, 2, 2, [
            (0, bytes([95, 95, 50, 100, 10, 100])),
            (4, bytes([171, 5, 216, 190, 50, 205])),
        ])
        img = png.read(p)
        self.assertEqual(img.pixel(0, 1), (10, 100, 10, 255))
        self.assertEqual(img.pixel(1, 1), (200, 60, 255, 255))

    def test_region_mean(self):
        p = self.dir / "m.png"
        row = bytes([255, 255, 255, 255]) * 5 + bytes([0, 0, 0, 255]) * 5
        write_raw(p, 10, 2, 8, 6, [row, row])
        img = png.read(p)
        self.assertTrue(all(abs(c - 127.5) <= 1 for c in png.region_mean(img, (0, 0, 10, 2))))
        self.assertEqual(png.region_mean(img, (0, 0, 5, 2)), (255, 255, 255))
        self.assertEqual(png.region_mean(img, (5, 0, 500, 500)), (0, 0, 0))  # przycięte

    def test_region_mean_ignores_transparent(self):
        p = self.dir / "t.png"
        write_raw(p, 2, 1, 8, 6, [bytes([200, 0, 0, 255, 0, 255, 0, 0])])
        img = png.read(p)
        self.assertEqual(png.region_mean(img, (0, 0, 2, 1)), (200, 0, 0))
        self.assertEqual(png.region_mean(img, (0, 0, 2, 1), ignore_transparent=False), (100, 128, 0))
        with self.assertRaises(GdError):
            png.region_mean(img, (1, 0, 1, 1))
        with self.assertRaises(GdError):
            png.region_mean(img, (50, 50, 5, 5))

    def test_not_png_raises(self):
        p = self.dir / "x.png"
        p.write_bytes(b"to nie jest obraz")
        with self.assertRaises(GdError):
            png.read(p)
        with self.assertRaises(GdError):
            png.size(p)
        with self.assertRaises(GdError):
            png.read(self.dir / "brak.png")

    def test_unsupported_raise(self):
        p = self.dir / "u.png"
        write_raw(p, 1, 1, 16, 2, [bytes(6)])
        with self.assertRaises(GdError):
            png.read(p)
        write_raw(p, 1, 1, 8, 3, [bytes(1)])
        with self.assertRaises(GdError):
            png.read(p)
        write_raw(p, 1, 1, 8, 2, [bytes(3)], interlace=1)
        with self.assertRaises(GdError):
            png.read(p)


if __name__ == "__main__":
    unittest.main()
