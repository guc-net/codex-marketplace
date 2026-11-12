"""Pakiety grafik w repozytorium: udostępnienie, zamknięcie, przejęcie. Skrypt nie woła gita."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import List, Optional

from . import brand as brandlib
from . import checks, jobs, render
from .common import GdError, now_iso


def target(repo: Path, job: dict) -> Path:
    month = str(job.get("created", ""))[:7]
    if len(month) != 7:
        month = now_iso()[:7]
    return Path(repo) / "graphics" / f"{month}-{job['slug']}"


def _copy_dir(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)


def _copy_inputs(job: Path, pkg: Path) -> None:
    pkg.mkdir(parents=True, exist_ok=True)
    if (job / "brief.md").is_file():
        shutil.copyfile(job / "brief.md", pkg / "brief.md")
    _copy_dir(job / "layers", pkg / "layers")
    _copy_dir(job / "composition", pkg / "composition")


def _layer_lines(job: Path) -> List[str]:
    lines = []
    for m in jobs.layer_metas(job):
        note = f": {m['note']}" if m.get("note") else ""
        lines.append(f"- {m.get('file') or m.get('name')} (źródło: {m.get('source', '?')}){note}")
    return lines or ["- brak warstw"]


def _format_lines(data: dict) -> List[str]:
    known = render.formats()
    return [f"- {i}: {known[i]['width']}×{known[i]['height']} px" if i in known else f"- {i}"
            for i in data.get("formats", [])]


def _refuse_finalized(pkg: Path, replace: bool) -> None:
    if (pkg / "final").exists() and not replace:
        raise GdError(f"pakiet {pkg} jest już zamknięty (ma final/) i nic nie nadpisuję. "
                      "Zastąp go za zgodą: --replace.")


def share(job_dir: Path, repo: Path, replace: bool = False) -> Path:
    job = Path(job_dir)
    data = jobs.load(job)
    pkg = target(repo, data)
    _refuse_finalized(pkg, replace)
    if replace and (pkg / "final").exists():
        shutil.rmtree(pkg / "final")
    _copy_inputs(job, pkg)
    text = "\n".join([
        f"# {data.get('title', job.name)}", "",
        "Stan: w toku (grafika nie jest jeszcze zaakceptowana).", "",
        "## Formaty", *_format_lines(data), "",
        "## Warstwy", *_layer_lines(job), "",
        f"Data: {now_iso()[:10]}", ""])
    (pkg / "README.md").write_text(text, encoding="utf-8")
    return pkg


def finalize(job_dir: Path, repo: Path, approved_by: str, replace: bool = False,
             accept_problems: bool = False) -> Path:
    job = Path(job_dir)
    data = jobs.load(job)
    known = render.formats()
    missing = []
    for i in data.get("formats", []):
        missing.append(f"final/{i}.png") if not (job / "final" / f"{i}.png").is_file() else None
        if known.get(i, {}).get("pdf") and not (job / "final" / f"{i}.pdf").is_file():
            missing.append(f"final/{i}.pdf")
    if missing:
        raise GdError("brak gotowych plików: " + ", ".join(missing)
                      + ". Złóż grafikę poleceniem render.")
    pkg = target(repo, data)
    _refuse_finalized(pkg, replace)
    bad = [f for f in checks.run(job) if not f.ok]
    if bad and not accept_problems:
        raise GdError(f"sprawdzenie znalazło {len(bad)} problemów, więc nie zamykam pakietu:\n"
                      + "\n".join(f"- [{f.format}] {f.code}: {f.message}" for f in bad)
                      + "\nPopraw grafikę albo zaakceptuj problemy świadomie: --accept-problems.")
    for d in ("final", "layers", "composition"):
        if (pkg / d).exists():
            shutil.rmtree(pkg / d)
    _copy_inputs(job, pkg)
    (pkg / "final").mkdir(parents=True, exist_ok=True)
    for f in sorted((job / "final").glob("*")):
        if f.is_file() and f.stem in data.get("formats", []):  # tylko formaty zlecenia
            shutil.copyfile(f, pkg / "final" / f.name)
    b = render._brand_of(job)
    lines = [f"# {data.get('title', job.name)}", "",
             "Stan: zamknięty (zaakceptowany).", "",
             f"Zaakceptował/a: {approved_by}, {now_iso()}", ""]
    if b is not None:
        lines += [f"Marka: {b.name} (wersja {b.version})", ""]
    lines += ["## Formaty", *_format_lines(data), "", "## Warstwy", *_layer_lines(job), ""]
    if bad:
        lines += ["## Zaakceptowane problemy",
                  *[f"- [{f.format}] {f.code}: {f.message}" for f in bad], ""]
    (pkg / "README.md").write_text("\n".join(lines), encoding="utf-8")
    data["stage"] = "final"
    jobs.save(job, data)
    return pkg


def adopt(package_dir: Path, title: Optional[str] = None) -> Path:
    pkg = Path(package_dir).expanduser().resolve()
    comp = pkg / "composition"
    if not comp.is_dir() or not list(comp.glob("*.html")):
        raise GdError(f"w pakiecie {pkg} nie ma composition/*.html")
    layers = pkg / "layers"
    bad = []
    for meta_path in sorted(layers.glob("*.json")) if layers.is_dir() else []:
        try:
            m = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            bad.append(meta_path.stem)
            continue
        f = layers / (m.get("file") or "")
        if not m.get("file") or not f.is_file() or jobs.sha256_of(f) != m.get("sha256"):
            bad.append(m.get("name", meta_path.stem))
    if bad:
        raise GdError("warstwy w pakiecie zmieniły się albo zniknęły (nie zgadza się SHA-256): "
                      + ", ".join(bad))
    if not title:
        title = pkg.name
        readme = pkg / "README.md"
        if readme.is_file():
            first = readme.read_text(encoding="utf-8").splitlines()[:1]
            if first and first[0].startswith("# "):
                title = first[0][2:].strip()
    formats = [p.stem for p in sorted(comp.glob("*.html"))]
    brand_dir = brandlib.find_brand(pkg)
    job = jobs.create(title, formats, None, brand_dir)
    for d in ("layers", "composition"):
        _copy_dir(pkg / d, job / d)
    if (pkg / "brief.md").is_file():
        shutil.copyfile(pkg / "brief.md", job / "brief.md")
    data = jobs.load(job)
    data["stage"] = "stages"
    data["chosen"] = "direct"  # przejęty pakiet nie ma rundy kierunków
    jobs.save(job, data)
    return job
