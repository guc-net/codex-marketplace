"""Automatyczne sprawdzanie wyrenderowanej grafiki przed pokazem."""
from __future__ import annotations

import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Optional

from . import browser, color, fonts, jobs, png, render
from .brand import Brand
from .common import GdError

TOLERANCE = 24          # ΔRGB na kanał przy porównaniu z kolorem z biblii
SAFE_EPS = 0.5          # px luzu na zaokrąglenia pomiaru
LARGE_TEXT_SHARE = 0.04
DISTORTION_MAX = 0.01


@dataclass
class Finding:
    format: str
    code: str
    ok: bool
    message: str


def _pl(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


class _Logos(HTMLParser):
    """Zbiera atrybut src elementów data-gd="logo" w kolejności dokumentu."""

    def __init__(self):
        super().__init__()
        self.srcs: List[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("data-gd") == "logo":
            self.srcs.append((a.get("src") or "").strip())

    handle_startendtag = handle_starttag


def _close(a, b) -> bool:
    return all(abs(x - y) <= TOLERANCE for x, y in zip(a, b))


def _role_color(brand: Brand, role: str):
    return color.parse_hex(brand.colors[role]) if role in brand.colors else None


def _group(fmt: str, code: str, problems: List[str], ok_msg: str) -> List[Finding]:
    if problems:
        return [Finding(fmt, code, False, p) for p in problems]
    return [Finding(fmt, code, True, ok_msg)]


def _backgrounds(comp: Path, brand: Optional[Brand], fmt: dict, elements: list):
    """Średnie tło pod każdym tekstem: (rgb albo None, notatka)."""
    built = render.build_html(comp, brand, fmt, hide_text=True)
    tmp = Path(tempfile.mkdtemp(prefix="gd-check-"))
    try:
        shot = tmp / "bg.png"
        browser.screenshot(built, shot, fmt["width"], fmt["height"])
        img = png.read(shot)
    finally:
        shutil.rmtree(built.parent, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)
    out = []
    for el in elements:
        try:
            out.append(png.region_mean(img, tuple(round(v) for v in el["box"])))
        except GdError:
            fallback = color.parse_hex(brand.colors["background"]) \
                if brand and "background" in brand.colors else None
            out.append(fallback)
    return out


def _check_format(job: Path, fid: str, fmt: dict, brand: Optional[Brand]) -> List[Finding]:
    comp = job / "composition" / f"{fid}.html"
    if not comp.is_file():
        return [Finding(fid, "composition", False, f"brak pliku composition/{fid}.html")]
    w, h = fmt["width"], fmt["height"]
    res: List[Finding] = []

    final = job / "final" / f"{fid}.png"
    if not final.is_file():
        res.append(Finding(fid, "size", False, f"brak pliku final/{fid}.png, uruchom render"))
    else:
        got = png.size(final)
        res.append(Finding(fid, "size", got == (w, h),
                           f"Plik final/{fid}.png ma {got[0]}×{got[1]} px, potrzeba {w}×{h} px"
                           if got != (w, h) else f"Plik ma {w}×{h} px"))

    if final.is_file():
        newest = max([comp] + [p for p in (job / "layers").glob("*") if p.is_file() and p.suffix != ".json"],
                     key=lambda p: p.stat().st_mtime)
        if newest.stat().st_mtime > final.stat().st_mtime:
            res.append(Finding(fid, "fresh", False,
                               f"Plik final/{fid}.png jest starszy niż {newest.relative_to(job).as_posix()}; "
                               "uruchom render jeszcze raz"))

    rep = render.report(comp, brand, fmt)
    els = rep.get("elements", [])
    texts = [e for e in els if e["gd"] == "text"]
    logos = [e for e in els if e["gd"] == "logo"]

    problems = [f"Font „{fam}” z biblii marki nie wczytał się, a kompozycja go używa"
                for fam in rep.get("fonts_used", []) if not rep.get("fonts", {}).get(fam)]
    res += _group(fid, "fonts", problems, "Fonty z biblii marki wczytane")

    problems, notes = [], []
    by_family = {f.family.casefold(): f for f in brand.fonts.values() if f.family} if brand else {}
    for e in texts:
        f = by_family.get(e["font"].casefold())
        if f is None or f.file is None or not f.file.is_file():
            notes.append(e["font"])
            continue
        miss = fonts.missing_chars(f.file, e["text"])
        if miss:
            problems.append(f"Tekst «{e['text']}» zawiera znaki, których font {e['font']} nie ma: "
                            + " ".join(miss))
    ok_msg = "Wszystkie znaki są w fontach"
    if notes:
        ok_msg += " (pominięto fonty spoza biblii: " + ", ".join(sorted(set(notes))) + ")"
    res += _group(fid, "glyphs", problems, ok_msg)

    c_problems, f_problems, notes = [], [], []
    if texts:
        bgs = _backgrounds(comp, brand, fmt, texts)
        for e, bg in zip(texts, bgs):
            fg = color.parse_hex(e["color"])
            if bg is None:
                notes.append(e["text"])
                continue
            need = 3.0 if e["box"][3] >= LARGE_TEXT_SHARE * h else 4.5
            ratio = color.contrast(fg, bg)
            if ratio < need:
                c_problems.append(f"Tekst «{e['text']}» ma kontrast {_pl(ratio)}:1 z tłem, "
                                  f"potrzeba co najmniej {_pl(need).replace(',0', '')}:1")
            if brand:
                for fr, br, why in brand.forbidden:
                    a, b = _role_color(brand, fr), _role_color(brand, br)
                    if a and b and _close(fg, a) and _close(bg, b):
                        f_problems.append(f"Tekst «{e['text']}» w kolorze {fr} na tle {br} jest "
                                          f"zakazany w bibliotece marki ({why})")
    ok_c = "Kontrast tekstu wystarcza"
    if notes:
        ok_c = ("Pominięto kontrast dla tekstów bez tła i bez koloru tła w bibliotece marki: "
                + ", ".join("«%s»" % n for n in notes))
    res += _group(fid, "contrast", c_problems, ok_c)
    res += _group(fid, "forbidden", f_problems, "Brak zakazanych zestawień kolorów")

    s = fmt["safe"]
    zone = (s["left"], s["top"], w - s["right"], h - s["bottom"])
    problems = []
    for e in texts + logos:
        x, y, bw, bh = e["box"]
        if (x < zone[0] - SAFE_EPS or y < zone[1] - SAFE_EPS
                or x + bw > zone[2] + SAFE_EPS or y + bh > zone[3] + SAFE_EPS):
            name = f"Tekst «{e['text']}»" if e["gd"] == "text" else "Logo"
            problems.append(f"{name} wychodzi poza strefę bezpieczną (x {zone[0]}–{zone[2]}, "
                            f"y {zone[1]}–{zone[3]} px); jego pudełko: x {round(x)}–{round(x + bw)}, "
                            f"y {round(y)}–{round(y + bh)} px")
    res += _group(fid, "safe-zone", problems, "Tekst i logo są w strefie bezpiecznej")

    parser = _Logos()
    parser.feed(comp.read_text(encoding="utf-8"))
    problems = []
    for i, src in enumerate(parser.srcs, 1):
        if not src.startswith("brand:"):
            problems.append(f"Logo nr {i} ma src „{src}”, a powinno pochodzić z biblii marki (brand:logo/…)")
        elif brand is None or not (brand.dir / src[len("brand:"):]).is_file():
            problems.append(f"Logo „{src}” nie ma pliku w bibliotece marki")
    res += _group(fid, "logo-source", problems, "Logo pochodzi z biblii marki")

    problems = []
    for e in logos:
        nw, nh = e.get("natural") or (0, 0)
        bw, bh = e["box"][2], e["box"][3]
        if nw and nh and bh and abs((bw / bh) / (nw / nh) - 1) > DISTORTION_MAX:
            problems.append(f"Logo ma proporcje pudełka {_pl(bw / bh)} zamiast {_pl(nw / nh)} "
                            "(rozciągnięte albo ściśnięte)")
    res += _group(fid, "logo-distortion", problems, "Logo ma właściwe proporcje")

    problems = []
    for src, e in zip(parser.srcs, logos):
        if not (brand and src.startswith("brand:")):
            continue
        target = (brand.dir / src[len("brand:"):]).resolve()
        for name, lg in brand.logos.items():
            if lg.file is not None and lg.file.resolve() == target and lg.min_width_px \
                    and e["box"][2] < lg.min_width_px:
                problems.append(f"Logo „{name}” ma {round(e['box'][2])} px szerokości, "
                                f"potrzeba co najmniej {lg.min_width_px} px")
    res += _group(fid, "logo-min-width", problems, "Logo nie jest za małe")

    problems = []
    changed = jobs.verify_layers(job)
    if changed:
        problems.append("Zamrożone warstwy zmieniły się albo zniknęły: " + ", ".join(changed))
    frozen = {m.get("file"): m.get("frozen") is True for m in jobs.layer_metas(job)}
    text = re.sub(r"<!--.*?-->", "", comp.read_text(encoding="utf-8"), flags=re.S)
    for name in sorted(set(re.findall(r"\.\./layers/([^\"')\s?#]+)", text))):
        if not frozen.get(name):
            problems.append(f"Warstwa „{name}” użyta w kompozycji nie jest zamrożona")
    res += _group(fid, "layers", problems, "Warstwy zamrożone i niezmienione")
    return res


def run(job_dir: Path) -> List[Finding]:
    job = Path(job_dir)
    data = jobs.load(job)
    known = render.formats()
    ids = list(data.get("formats", []))
    for i in ids:
        if i not in known:
            raise GdError(f"nieznany format {i}. Znane formaty: {', '.join(known)}")
    brand = render._brand_of(job)
    out: List[Finding] = []
    for i in ids:
        out += _check_format(job, i, known[i], brand)
    return out
