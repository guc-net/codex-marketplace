"""Biblia marki: brand/brand.md, walidacja, zmienne CSS."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import color, flatyaml
from .common import GdError

FORMAT = "graphic-designer-brand/1"
REQUIRED_COLORS = ("primary", "background", "text")
LOGO_ON = ("dark", "light", "any")


@dataclass
class Font:
    family: str = ""
    file: Optional[Path] = None
    use: str = ""
    pending: bool = False
    file_raw: str = ""


@dataclass
class Logo:
    file: Optional[Path] = None
    on: str = "any"
    min_width_px: Optional[int] = None
    file_raw: str = ""


@dataclass
class Brand:
    dir: Path
    name: str = ""
    version: int = 0
    colors: Dict[str, str] = field(default_factory=dict)
    fonts: Dict[str, Font] = field(default_factory=dict)
    logos: Dict[str, Logo] = field(default_factory=dict)
    forbidden: List[Tuple[str, str, str]] = field(default_factory=list)
    body: str = ""
    format: str = ""
    raw: dict = field(default_factory=dict)


def find_brand(start: Path) -> Optional[Path]:
    """Szuka `brand/brand.md` od `start` w górę; stop na katalogu domowym i korzeniu."""
    home = Path.home().resolve()
    cur = Path(start).resolve()
    while True:
        if (cur / "brand" / "brand.md").is_file():
            return cur / "brand"
        if cur == home or cur.parent == cur:
            return None
        cur = cur.parent


def resolve(start: Path) -> Optional[Path]:
    """`start` to sam katalog biblii (z `brand.md`) albo miejsce, od którego szukamy w górę."""
    start = Path(start).expanduser()
    if (start / "brand.md").is_file():
        return start
    return find_brand(start)


def split_header(text: str, source: str) -> Tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise GdError(f"{source}: brak nagłówka między liniami „---” na początku pliku")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:]).lstrip("\n")
    raise GdError(f"{source}: nagłówek nie jest zamknięty linią „---”")


def load(brand_dir: Path) -> Brand:
    brand_dir = Path(brand_dir)
    path = brand_dir / "brand.md"
    if not path.is_file():
        raise GdError(f"nie ma pliku {path}")
    header, body = split_header(path.read_text(encoding="utf-8"), str(path))
    raw = flatyaml.parse(header, str(path))
    b = Brand(dir=brand_dir, body=body, raw=raw)
    b.format = str(raw.get("format") or "")
    b.name = str(raw.get("name") or "")
    v = raw.get("version")
    b.version = v if isinstance(v, int) and not isinstance(v, bool) else 0
    for key, val in raw.items():
        parts = key.split(".")
        if parts[0] == "color" and len(parts) == 2:
            b.colors[parts[1]] = str(val)
        elif parts[0] == "font" and len(parts) >= 3:
            f = b.fonts.setdefault(".".join(parts[1:-1]), Font())
            attr = parts[-1]
            if attr == "family":
                f.family = str(val)
            elif attr == "file" and val:
                f.file_raw = str(val)
                f.file = brand_dir / str(val)
            elif attr == "use":
                f.use = str(val or "")
            elif attr == "pending":
                f.pending = val is True
        elif parts[0] == "logo" and len(parts) >= 3:
            lg = b.logos.setdefault(".".join(parts[1:-1]), Logo())
            attr = parts[-1]
            if attr == "file" and val:
                lg.file_raw = str(val)
                lg.file = brand_dir / str(val)
            elif attr == "on":
                lg.on = str(val)
            elif attr == "min-width-px" and isinstance(val, int):
                lg.min_width_px = val
    for key, val in raw.items():
        m = re.fullmatch(r"forbidden\.(\w+)", key)
        if not m:
            continue
        why = str(raw.get(f"{key}.why") or "")
        pair = re.fullmatch(r"\s*(\S+)\s+on\s+(\S+)\s*", str(val))
        if pair:
            b.forbidden.append((pair.group(1), pair.group(2), why))
        else:
            b.forbidden.append((str(val), "", why))
    return b


def validate(b: Brand) -> Tuple[List[str], List[str]]:
    """Zwraca (błędy, ostrzeżenia) — wszystkie naraz."""
    errors: List[str] = []
    warnings: List[str] = []
    if b.format != FORMAT:
        errors.append(f"format: oczekiwano „{FORMAT}”, jest „{b.format}”")
    if not b.name:
        errors.append("brak nazwy marki (klucz name)")
    if b.version < 1:
        errors.append("brak numeru wersji (klucz version, liczba całkowita od 1)")
    for role in REQUIRED_COLORS:
        if role not in b.colors:
            errors.append(f"brak wymaganego koloru color.{role}")
    for role, value in b.colors.items():
        try:
            color.parse_hex(value)
        except GdError:
            errors.append(f"color.{role}: zły kolor „{value}” (oczekiwano #RRGGBB)")
    for name, f in b.fonts.items():
        if not f.family:
            errors.append(f"font.{name}.family: brak nazwy rodziny")
        if f.file is None:
            if f.pending:
                warnings.append(f"font {name}: plik jeszcze nie dostarczony (pending)")
            else:
                errors.append(f"font.{name}.file: brak pliku (a font nie jest oznaczony jako pending)")
            continue
        if f.file.suffix.lower() not in (".ttf", ".otf"):
            errors.append(f"font.{name}.file: oczekiwano .ttf albo .otf, jest „{f.file_raw}”")
        elif not f.file.is_file():
            errors.append(f"font.{name}.file: nie ma pliku {f.file_raw}")
    if not b.logos:
        errors.append("brak logo: potrzebny co najmniej jeden wariant (logo.<nazwa>.file)")
    for name, lg in b.logos.items():
        if lg.file is None:
            errors.append(f"logo.{name}.file: brak ścieżki do pliku")
        elif not lg.file.is_file():
            errors.append(f"logo.{name}.file: nie ma pliku {lg.file_raw}")
        if lg.on not in LOGO_ON:
            errors.append(f"logo.{name}.on: oczekiwano dark, light albo any, jest „{lg.on}”")
    for i, (fg, bg, _why) in enumerate(b.forbidden, 1):
        if not bg:
            errors.append(f"forbidden.{i}: oczekiwano „rola on rola”, jest „{fg}”")
            continue
        for role in (fg, bg):
            if role not in b.colors:
                errors.append(f"forbidden.{i}: nie ma koloru o roli „{role}”")
    return errors, warnings


def css_vars(b: Brand) -> str:
    return "\n".join(f"--color-{role}: {value.upper()};" for role, value in b.colors.items())


def bump_version(brand_dir: Path) -> int:
    """Podbija `version` w nagłówku, zachowując resztę pliku bez zmian."""
    path = Path(brand_dir) / "brand.md"
    text = path.read_text(encoding="utf-8")
    new = [0]

    def repl(m):
        new[0] = int(m.group(2)) + 1
        return f"{m.group(1)}{new[0]}"

    out, n = re.subn(r"(?m)^(version:\s*)(\d+)", repl, text, count=1)
    if not n:
        raise GdError(f"{path}: brak liczbowego klucza version w nagłówku")
    path.write_text(out, encoding="utf-8")
    return new[0]
