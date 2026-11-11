#!/usr/bin/env python3
"""Projektant grafik: wejście skryptu pluginu graphic-designer."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gd import brand as brandlib  # noqa: E402
from gd import jobs  # noqa: E402
from gd.common import PLUGIN_ROOT, GdError, info, now_iso  # noqa: E402


def cmd_version(args) -> int:
    manifest = json.loads((PLUGIN_ROOT / "plugin.json").read_text(encoding="utf-8"))
    info(manifest["version"])
    return 0


def _job_line(job: Path) -> str:
    try:
        d = jobs.load(job)
    except GdError:
        return f"- {job.parent.name}/{job.name}: PROBLEM: nie mogę odczytać job.json"
    stage = d.get("stage", "?")
    step = jobs.NEXT_STEP.get(stage)
    return (f"- {job.parent.name}/{job.name}: {d.get('title', '?')} | etap: {stage}"
            + (f" → {step}" if step else "")
            + f" | warstwy: {len(jobs.layer_metas(job))} | formaty: {', '.join(d.get('formats', []))}")


def cmd_library(args) -> int:
    from gd.common import read_settings, write_settings
    if args.set:
        folder = Path(args.set).expanduser().resolve()
        if folder.exists() and not folder.is_dir():
            raise GdError(f"{folder} to plik, nie folder")
        folder.mkdir(parents=True, exist_ok=True)
        data = read_settings()
        data["library"] = str(folder)
        write_settings(data)
        info(f"LIBRARY: {folder}")
        info("Nowe zlecenia powstają tutaj, w podfolderach projektów.")
        return 0
    lib = jobs.library()
    if lib is None:
        info("NOT SET: biblioteka zleceń nie jest ustawiona. Ustaw: designer.py library --set <folder>")
    elif not lib.is_dir():
        info(f"MISSING: biblioteka {lib} nie istnieje (odłączony dysk?).")
    else:
        info(f"LIBRARY: {lib}")
        info(f"zleceń: {len(jobs.all_jobs(lib))}")
    return 0


def cmd_new(args) -> int:
    formats = [f.strip() for f in args.formats.split(",") if f.strip()]
    if args.brand:
        brand_dir = brandlib.resolve(Path(args.brand))
        if brand_dir is None:
            raise GdError(f"nie znalazłem biblii marki (brand/brand.md) w {args.brand} ani wyżej")
    else:
        brand_dir = brandlib.find_brand(Path.cwd())
    job = jobs.create(args.title, formats, args.project, brand_dir)
    info(f"JOB: {job}")
    if brand_dir is None:
        info("NO BRAND: zlecenie bez biblii marki. Załóż ją (brand-init --dir <zlecenie>) i zapisz "
             "poleceniem set-brand.")
    else:
        info(f"marka: {brand_dir}")
    return 0


def cmd_set_brand(args) -> int:
    job = jobs.job_dir(args.job)
    brand_dir = brandlib.resolve(Path(args.brand))
    if brand_dir is None:
        raise GdError(f"nie znalazłem biblii marki (brand/brand.md) w {args.brand} ani wyżej")
    saved = jobs.set_brand(job, brand_dir)
    info(f"OK: zlecenie {job.name} używa marki z {saved}")
    return 0


def cmd_status(args) -> int:
    if args.job:
        job = jobs.job_dir(args.job)
        info(f"JOB: {job}")
        info(_job_line(job))
        changed = jobs.verify_layers(job)
        if changed:
            info("PROBLEM: zamrożone warstwy zmieniły się albo zniknęły: " + ", ".join(changed))
        return 0
    lib = jobs.library()
    if lib is None:
        info("NOT SET: biblioteka zleceń nie jest ustawiona. Ustaw: designer.py library --set <folder>")
    elif not lib.is_dir():
        info(f"MISSING: biblioteka {lib} nie istnieje (odłączony dysk?).")
    else:
        found = jobs.all_jobs(lib)
        if found:
            info(f"JOBS: {len(found)} w {lib}")
            for j in found:
                info(_job_line(j))
        else:
            info(f"NO JOBS: w {lib} nie ma jeszcze zleceń.")
    pkgs = jobs.repo_packages(Path.cwd())
    if pkgs:
        info(f"PACKAGES: {len(pkgs)} w toku w repozytorium (graphics/ bez final/)")
        for p in pkgs:
            info(f"- {p.name}")
    else:
        info("NO PACKAGES: w bieżącym repozytorium nie ma pakietów w toku.")
    return 0


def cmd_draft(args) -> int:
    job = jobs.job_dir(args.job)
    dest = jobs.add_draft(job, Path(args.file), args.direction, args.note, args.prompt or "")
    info(f"OK: wersja robocza {dest}")
    return 0


def cmd_choose(args) -> int:
    job = jobs.job_dir(args.job)
    value = jobs.choose(job, args.direction, args.direct)
    if value == "direct":
        info(f"OK: zlecenie {job.name} bez rundy kierunków (direct); etap: stages")
    else:
        info(f"OK: wybrany kierunek {value} w zleceniu {job.name}; etap: stages")
    return 0


def cmd_freeze(args) -> int:
    job = jobs.job_dir(args.job)
    inputs = [i.strip() for i in (args.inputs or "").split(",") if i.strip()]
    dest = jobs.freeze(job, args.name, Path(args.file), args.source, args.prompt or "", inputs,
                       args.approved_by, args.note or "", replace=args.replace)
    info(f"OK: warstwa zamrożona {dest}")
    return 0


def cmd_brand(args) -> int:
    start = Path(args.path).expanduser() if args.path else Path.cwd()
    brand_dir = brandlib.resolve(start)
    if brand_dir is None:
        info("NO BRAND")
        info("Nie znalazłem biblii marki (brand/brand.md). Załóż ją poleceniem brand-init.")
        return 0
    b = brandlib.load(brand_dir)
    errors, warnings = brandlib.validate(b)
    if errors:
        info(f"PROBLEM: biblia marki {brand_dir} ma {len(errors)} błędów:")
        for e in errors:
            info(f"- {e}")
        for w in warnings:
            info(f"UWAGA: {w}")
        return 1
    info(f"BRAND: {brand_dir} ({b.name}, wersja {b.version})")
    info(f"kolory: {len(b.colors)}, fonty: {len(b.fonts)}, logo: {len(b.logos)}")
    for w in warnings:
        info(f"UWAGA: {w}")
    return 0


def cmd_brand_init(args) -> int:
    target = (Path(args.dir).expanduser() if args.dir else Path.cwd()) / "brand"
    if target.exists():
        raise GdError(f"{target} już istnieje; nic nie nadpisuję")
    shutil.copytree(PLUGIN_ROOT / "templates" / "brand-skeleton", target)
    path = target / "brand.md"
    text = path.read_text(encoding="utf-8").replace("{{name}}", json.dumps(args.name, ensure_ascii=False)[1:-1])
    path.write_text(text, encoding="utf-8")
    info(f"OK: założono {target}")
    info("Uzupełnij kolory, fonty i logo, potem uruchom brand.")
    return 0


def cmd_brand_log(args) -> int:
    start = Path(args.path).expanduser() if args.path else Path.cwd()
    brand_dir = brandlib.resolve(start)
    if brand_dir is None:
        raise GdError("nie znalazłem biblii marki (brand/brand.md)")
    version = brandlib.bump_version(brand_dir)
    log = brand_dir / "CHANGES.md"
    old = log.read_text(encoding="utf-8") if log.is_file() else "# Zmiany w bibliotece marki\n"
    if not old.endswith("\n"):
        old += "\n"
    entry = f"- {now_iso()[:10]}: {args.change} (wersja {version}, zatwierdził/a: {args.approved_by})\n"
    log.write_text(old + entry, encoding="utf-8")
    info(f"OK: wersja {version}, wpis dopisany do {log}")
    return 0


def cmd_render(args) -> int:
    from gd import render
    job = jobs.job_dir(args.job)
    files = render.render_job(job, args.format, args.preview)
    if not args.preview:
        jobs.advance(job, "composition")
    info("RENDERED: " + ", ".join(str(f) for f in files))
    return 0


def cmd_check(args) -> int:
    from gd import checks
    job = jobs.job_dir(args.job)
    findings = checks.run(job)
    bad = [f for f in findings if not f.ok]
    if not bad:
        info(f"OK: {len(findings)}/{len(findings)}")
        return 0
    info(f"PROBLEMS: {len(bad)}")
    for f in bad:
        info(f"- [{f.format}] {f.code}: {f.message}")
    return 3


def cmd_share(args) -> int:
    from gd import package
    pkg = package.share(jobs.job_dir(args.job), Path(args.repo).expanduser(), args.replace)
    info(f"PACKAGE: {pkg}")
    info("Pakiet w toku. Zapisz go w repozytorium według AGENTS.md (skrypt nie używa gita).")
    return 0


def cmd_finalize(args) -> int:
    from gd import package
    pkg = package.finalize(jobs.job_dir(args.job), Path(args.repo).expanduser(), args.approved_by,
                           args.replace, args.accept_problems)
    info(f"PACKAGE: {pkg}")
    info("Pakiet zamknięty. Zapisz go w repozytorium według AGENTS.md (skrypt nie używa gita).")
    return 0


def cmd_adopt(args) -> int:
    from gd import package
    job = package.adopt(Path(args.package), args.title)
    info(f"JOB: {job}")
    info("Warstwy zostały zamrożone jak w pakiecie.")
    return 0


def cmd_env(args) -> int:
    import os
    from gd import browser
    try:
        info(f"BROWSER: {browser.find()}")
        info(browser.smoke_test())
    except GdError as e:
        info("NO BROWSER")
        info(str(e).replace("NO BROWSER: ", "", 1))
    info("PYTHON: " + ".".join(str(n) for n in sys.version_info[:3]))
    if os.environ.get("OPENAI_API_KEY"):
        info("WARNING: OPENAI_API_KEY jest ustawiony, więc obrazy będą liczone według cennika API, "
             "a nie z abonamentu.")
    return 0


def cmd_update_check(args) -> int:
    from gd import update
    cache = Path(args.cache).expanduser() if args.cache else update.default_cache()
    text = update.check(cache, args.source or update.SOURCE_URL, args.force)
    info(text)
    return 2 if text.startswith("NIE SPRAWDZONO") else 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="designer.py", description="Projektant grafik.")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("version", help="pokaż wersję pluginu")
    s.set_defaults(func=cmd_version)
    s = sub.add_parser("library", help="pokaż albo ustaw folder biblioteki zleceń")
    s.add_argument("--set", help="folder biblioteki (zostanie utworzony)")
    s.set_defaults(func=cmd_library)
    s = sub.add_parser("new", help="załóż zlecenie")
    s.add_argument("--title", required=True)
    s.add_argument("--formats", required=True, help="identyfikatory po przecinku, np. ig-post,ig-story")
    s.add_argument("--project", help="projekt (domyślnie nazwa marki)")
    s.add_argument("--brand", help="katalog brand/ albo miejsce, od którego szukać")
    s.set_defaults(func=cmd_new)
    s = sub.add_parser("set-brand", help="zapisz bibliotekę marki w zleceniu")
    s.add_argument("--job", required=True)
    s.add_argument("--brand", required=True, help="katalog brand/ albo miejsce, od którego szukać")
    s.set_defaults(func=cmd_set_brand)
    s = sub.add_parser("status", help="pokaż zlecenia i pakiety w toku")
    s.add_argument("--job", help="slug zlecenia albo ścieżka jego folderu")
    s.set_defaults(func=cmd_status)
    s = sub.add_parser("draft", help="zapisz wersję roboczą")
    s.add_argument("--job", required=True)
    s.add_argument("--file", required=True)
    s.add_argument("--direction", required=True)
    s.add_argument("--note", required=True)
    s.add_argument("--prompt")
    s.set_defaults(func=cmd_draft)
    s = sub.add_parser("choose", help="zapisz wybrany kierunek (albo zlecenie bez rundy kierunków)")
    s.add_argument("--job", required=True)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--direction", help="litera kierunku zapisanego wcześniej przez draft --direction")
    g.add_argument("--direct", action="store_true",
                   help="zlecenie bez rundy kierunków (samo nałożenie albo dokładnie opisany wygląd)")
    s.set_defaults(func=cmd_choose)
    s = sub.add_parser("freeze", help="zamroź zatwierdzoną warstwę (kopia, z SHA-256)")
    s.add_argument("--job", required=True)
    s.add_argument("--name", required=True)
    s.add_argument("--file", required=True)
    s.add_argument("--source", required=True, help="generated, photo, brand albo composed")
    s.add_argument("--approved-by", required=True)
    s.add_argument("--prompt")
    s.add_argument("--inputs", help="pliki wejściowe po przecinku")
    s.add_argument("--note")
    s.add_argument("--replace", action="store_true", help="odmroź i zastąp istniejącą warstwę")
    s.set_defaults(func=cmd_freeze)
    s = sub.add_parser("brand", help="sprawdź bibliotekę marki")
    s.add_argument("--path", help="katalog brand/ albo miejsce, od którego szukać")
    s.set_defaults(func=cmd_brand)
    s = sub.add_parser("brand-init", help="załóż szkielet biblii marki")
    s.add_argument("--name", required=True, help="nazwa marki")
    s.add_argument("--dir", help="katalog, w którym powstanie brand/")
    s.set_defaults(func=cmd_brand_init)
    s = sub.add_parser("brand-log", help="dopisz zmianę biblii i podbij wersję")
    s.add_argument("--change", required=True, help="co się zmieniło")
    s.add_argument("--approved-by", required=True, help="kto zatwierdził")
    s.add_argument("--path", help="katalog brand/ albo miejsce, od którego szukać")
    s.set_defaults(func=cmd_brand_log)
    s = sub.add_parser("render", help="złóż kompozycje do PNG (i PDF dla druku)")
    s.add_argument("--job", required=True)
    s.add_argument("--format", help="tylko ten format")
    s.add_argument("--preview", action="store_true", help="podgląd ze strefami bezpiecznymi w drafts/")
    s.set_defaults(func=cmd_render)
    s = sub.add_parser("check", help="sprawdź wyrenderowane grafiki zlecenia")
    s.add_argument("--job", required=True)
    s.set_defaults(func=cmd_check)
    s = sub.add_parser("share", help="udostępnij zlecenie w toku jako pakiet w repozytorium")
    s.add_argument("--job", required=True)
    s.add_argument("--repo", required=True, help="korzeń repozytorium")
    s.add_argument("--replace", action="store_true", help="zastąp pakiet, który ma już final/")
    s.set_defaults(func=cmd_share)
    s = sub.add_parser("finalize", help="zamknij zlecenie jako pakiet w repozytorium")
    s.add_argument("--job", required=True)
    s.add_argument("--repo", required=True, help="korzeń repozytorium")
    s.add_argument("--approved-by", required=True)
    s.add_argument("--accept-problems", action="store_true", help="zamknij mimo problemów ze sprawdzenia")
    s.add_argument("--replace", action="store_true", help="zastąp istniejący pakiet z final/")
    s.set_defaults(func=cmd_finalize)
    s = sub.add_parser("adopt", help="przejmij pakiet z repozytorium jako nowe zlecenie")
    s.add_argument("--package", required=True)
    s.add_argument("--title")
    s.set_defaults(func=cmd_adopt)
    s = sub.add_parser("env", help="sprawdź przeglądarkę, Pythona i zmienne środowiska")
    s.set_defaults(func=cmd_env)
    s = sub.add_parser("update-check", help="sprawdź, czy jest nowsza wersja pluginu (raz dziennie)")
    s.add_argument("--force", action="store_true", help="pomiń wynik z dzisiejszego sprawdzenia")
    s.add_argument("--source", help="adres z plugin.json i CHANGELOG.md (domyślnie GitHub)")
    s.add_argument("--cache", help="plik z wynikiem (domyślnie ~/.graphic-designer/update.json)")
    s.set_defaults(func=cmd_update_check)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.func(args) or 0
    except GdError as e:
        info(f"PROBLEM: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
