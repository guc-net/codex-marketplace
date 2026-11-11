"""Zlecenia: biblioteka, folder roboczy, wersje robocze, zamrożone warstwy."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import List, Optional

from . import brand as brandlib
from .common import PLUGIN_ROOT, GdError, now_iso, read_settings, slug

SOURCES = ("generated", "photo", "brand", "composed")
SUBDIRS = ("drafts", "layers", "composition", "final")
NO_BRAND_PROJECT = "bez-marki"
STAGES = ("brief", "directions", "stages", "composition", "final")
BRIEF_MIN_CHARS = 80
NEXT_STEP = {
    "brief": "dopytaj o brief i zapisz kierunki (draft --direction)",
    "directions": "pokaż kierunki i poczekaj na wybór, potem choose",
    "stages": "dopracuj etapami (draft, freeze), potem render",
    "composition": "check, samoocena, pokaz z listą do sprawdzenia przez człowieka",
    "final": "zamknięte; nic do zrobienia",
}


# --- biblioteka ---------------------------------------------------------------

def library() -> Optional[Path]:
    """Folder biblioteki z ustawień albo None."""
    value = read_settings().get("library")
    return Path(value).expanduser() if value else None


def require_library() -> Path:
    lib = library()
    if lib is None:
        raise GdError("nie ustawiono biblioteki zleceń. Ustaw ją: designer.py library --set <folder>")
    if not lib.is_dir():
        raise GdError(f"nie ma folderu biblioteki {lib} (odłączony dysk?). Podłącz go albo ustaw nowy: "
                      "designer.py library --set <folder>")
    return lib


# --- formaty ------------------------------------------------------------------

def known_formats() -> list:
    path = PLUGIN_ROOT / "templates" / "formats.json"
    return json.loads(path.read_text(encoding="utf-8"))


def check_formats(ids: List[str]) -> List[str]:
    known = [f["id"] for f in known_formats()]
    if not ids:
        raise GdError(f"podaj co najmniej jeden format. Znane formaty: {', '.join(known)}")
    bad = [i for i in ids if i not in known]
    if bad:
        raise GdError(f"nieznany format: {', '.join(bad)}. Znane formaty: {', '.join(known)}")
    out: List[str] = []
    for i in ids:
        if i not in out:
            out.append(i)
    return out


# --- zlecenia -----------------------------------------------------------------

def all_jobs(lib: Path) -> List[Path]:
    found = []
    for project in sorted(p for p in lib.iterdir() if p.is_dir()):
        for job in sorted(p for p in project.iterdir() if (p / "job.json").is_file()):
            found.append(job)
    return found


def job_dir(job: str) -> Path:
    """Folder zlecenia: ścieżka wprost albo slug zlecenia z biblioteki (dowolny projekt)."""
    p = Path(job).expanduser()
    if (p / "job.json").is_file():
        return p.resolve()
    lib = library()
    if lib is not None and lib.is_dir():
        matches = [j for j in all_jobs(lib) if j.name == job]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise GdError(f"zlecenie „{job}” jest w kilku projektach: "
                          + ", ".join(f"{m.parent.name}/{m.name}" for m in matches)
                          + ". Podaj pełną ścieżkę folderu zlecenia.")
    raise GdError(f"nie ma zlecenia „{job}”. Lista zleceń: designer.py status")


def load(job: Path) -> dict:
    try:
        return json.loads((Path(job) / "job.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise GdError(f"nie mogę odczytać {Path(job) / 'job.json'}: {e}")


def save(job: Path, data: dict) -> None:
    (Path(job) / "job.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                        encoding="utf-8")


def create(title: str, formats: List[str], project: Optional[str], brand_dir: Optional[Path]) -> Path:
    if not title.strip():
        raise GdError("podaj tytuł zlecenia (--title)")
    formats = check_formats(formats)
    lib = require_library()
    brand_name = None
    if brand_dir is not None:
        brand_name = brandlib.load(brand_dir).name
    project_slug = slug(project) if project else (slug(brand_name or "") or NO_BRAND_PROJECT)
    project_slug = project_slug or NO_BRAND_PROJECT
    base = slug(title) or "zlecenie"
    parent = lib / project_slug
    parent.mkdir(parents=True, exist_ok=True)
    name, n = base, 1
    while (parent / name).exists():
        n += 1
        name = f"{base}-{n}"
    job = parent / name
    job.mkdir()
    for d in SUBDIRS:
        (job / d).mkdir()
    shutil.copyfile(PLUGIN_ROOT / "skills" / "graphic-designer" / "references" / "brief.md", job / "brief.md")
    save(job, {
        "schema": 1, "slug": name, "title": title.strip(), "project": project_slug,
        "brand": str(Path(brand_dir).resolve()) if brand_dir is not None else None,
        "formats": formats, "created": now_iso(), "stage": "brief",
        "directions": {}, "chosen": None,
    })
    return job


def advance(job: Path, stage: str) -> None:
    """Przesuwa etap zlecenia do przodu; nigdy nie cofa."""
    data = load(job)
    cur = data.get("stage")
    if cur in STAGES and STAGES.index(cur) >= STAGES.index(stage):
        return
    data["stage"] = stage
    save(job, data)


def brief_filled(job: Path) -> bool:
    """Czy brief.md ma realną treść: poza nagłówkami i tekstem szablonu jest >= 80 znaków."""
    path = Path(job) / "brief.md"
    if not path.is_file():
        return False
    template = PLUGIN_ROOT / "skills" / "graphic-designer" / "references" / "brief.md"
    boiler = {l.strip() for l in template.read_text(encoding="utf-8").splitlines()}
    labels = sorted((l for l in boiler if l.startswith("- ") and l.endswith(":")), key=len, reverse=True)
    kept = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line in boiler:
            continue
        for label in labels:
            if line.startswith(label):
                line = line[len(label):]
                break
        kept.append(line)
    return len("".join("".join(kept).split())) >= BRIEF_MIN_CHARS


def choose(job: Path, direction: Optional[str], direct: bool) -> str:
    """Zapisuje wybór kierunku (albo `direct`: zlecenie bez rundy kierunków). Zwraca zapisaną wartość."""
    if bool(direction) == bool(direct):
        raise GdError("podaj dokładnie jedno: --direction <litera> albo --direct")
    data = load(job)
    if direct:
        value = "direct"
    else:
        known = data.get("directions") or {}
        match = [k for k in known if k.lower() == direction.strip().lower()]
        if not match:
            have = ", ".join(sorted(known)) or "żadnego"
            raise GdError(f"kierunek „{direction}” nie istnieje w zleceniu (zapisane kierunki: {have}). "
                          "Najpierw zapisz go: draft --direction <litera>. "
                          "Zlecenie bez rundy kierunków: choose --direct.")
        value = match[0]
    data["chosen"] = value
    save(job, data)
    advance(job, "stages")
    return value


def set_brand(job: Path, brand_dir: Path) -> Path:
    brandlib.load(brand_dir)  # zły katalog albo biblia -> GdError
    data = load(job)
    data["brand"] = str(Path(brand_dir).resolve())
    save(job, data)
    return Path(brand_dir).resolve()


# --- wersje robocze -----------------------------------------------------------

def _clean(text: str, what: str) -> str:
    out = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-")
    if not out:
        raise GdError(f"{what} „{text}” nie nadaje się na nazwę pliku (użyj liter, cyfr, „-”)")
    return out


def _need_file(src: Path, job: Optional[Path] = None) -> Path:
    src = Path(src).expanduser()
    if not src.is_file() and job is not None and not src.is_absolute() and (Path(job) / src).is_file():
        src = Path(job) / src  # ścieżka względem folderu zlecenia, np. drafts/A-v1.png
    if not src.is_file():
        raise GdError(f"nie ma pliku {src}")
    if not src.suffix or src.suffix.lower() == ".json":
        raise GdError(f"plik {src.name} musi mieć rozszerzenie obrazu (np. .png), nie .json ani bez rozszerzenia")
    return src


def _same_stem(folder: Path, stem: str) -> List[Path]:
    """Pliki o tej samej nazwie bez względu na wielkość liter (macOS i Windows ich nie rozróżniają)."""
    return [p for p in folder.iterdir() if p.stem.lower() == stem.lower()]


def add_draft(job: Path, src: Path, direction: str, note: str, prompt: str) -> Path:
    src = _need_file(src, job)
    direction = _clean(direction, "kierunek")
    drafts = Path(job) / "drafts"
    drafts.mkdir(exist_ok=True)
    n = 1
    while True:
        stem = f"{direction}-v{n}"
        if not _same_stem(drafts, stem):
            break
        n += 1
    dest = drafts / (stem + src.suffix.lower())
    shutil.copyfile(src, dest)
    meta = {"direction": direction, "version": n, "file": dest.name, "note": note,
            "prompt": prompt, "created": now_iso()}
    (drafts / (stem + ".json")).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    data = load(job)
    directions = data.setdefault("directions", {})
    directions[direction] = {"versions": n, "note": note}
    save(job, data)
    advance(job, "directions")
    return dest


# --- warstwy ------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def freeze(job: Path, name: str, src: Path, source: str, prompt: str, inputs: List[str],
           approved_by: str, note: str, replace: bool = False) -> Path:
    if source not in SOURCES:
        raise GdError(f"nieznane źródło „{source}”. Dozwolone: {', '.join(SOURCES)}")
    src = _need_file(src, job)
    name = _clean(name, "nazwa warstwy")
    layers = Path(job) / "layers"
    layers.mkdir(exist_ok=True)
    existing = _same_stem(layers, name)
    if existing and not replace:
        raise GdError(f"warstwa „{name}” jest już zamrożona i nic nie nadpisuję. Nadaj nową nazwę, "
                      f"np. {name}-v2, albo odmroź za zgodą (--replace).")
    dest = layers / (name + src.suffix.lower())
    # najpierw kopia do pliku tymczasowego: źródłem może być sama zastępowana warstwa
    tmp = layers / (".gd-tmp-" + name + src.suffix.lower())
    shutil.copyfile(src, tmp)
    for old in existing:
        old.unlink()
    tmp.replace(dest)
    meta = {"name": name, "file": dest.name, "sha256": sha256_of(dest), "frozen": True,
            "source": source, "prompt": prompt, "inputs": inputs, "created": now_iso(),
            "approved_by": approved_by, "note": note}
    (layers / (name + ".json")).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    return dest


def layer_metas(job: Path) -> List[dict]:
    metas = []
    for p in sorted((Path(job) / "layers").glob("*.json")):
        try:
            metas.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            metas.append({"name": p.stem, "file": None, "sha256": None})
    return metas


def verify_layers(job: Path) -> List[str]:
    """Nazwy warstw, których plik zmienił się względem SHA-256 albo zniknął."""
    bad = []
    for m in layer_metas(job):
        f = Path(job) / "layers" / (m.get("file") or "")
        if not m.get("file") or not f.is_file() or sha256_of(f) != m.get("sha256"):
            bad.append(m.get("name", "?"))
    return bad


# --- pakiety w repozytorium ---------------------------------------------------

def repo_packages(start: Path) -> List[Path]:
    """Pakiety `graphics/*/` bez `final/`, szukane od `start` w górę."""
    cur = Path(start).resolve()
    for d in [cur, *cur.parents]:
        g = d / "graphics"
        if g.is_dir():
            return sorted(p for p in g.iterdir() if p.is_dir() and not (p / "final").exists())
    return []
