"""Składanie kompozycji HTML do PNG i PDF przez przeglądarkę bez okna."""
from __future__ import annotations

import base64
import html as htmllib
import json
import re
import secrets
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from . import browser, jobs
from . import brand as brandlib
from .brand import Brand
from .common import PLUGIN_ROOT, GdError

MM_PER_INCH = 25.4


def formats() -> Dict[str, dict]:
    return {f["id"]: f for f in jobs.known_formats()}


# --- brand: i fonty -----------------------------------------------------------

_BRAND_REF = re.compile(r"""(?<=["'(])brand:([^"')]+)""")


def _brand_uris(text: str, brand: Optional[Brand]) -> str:
    missing: List[str] = []

    def repl(m):
        rel = m.group(1).strip()
        if brand is None:
            missing.append(f"brand:{rel} (zlecenie nie ma biblii marki)")
            return m.group(0)
        path = (brand.dir / rel)
        if not brandlib.inside(brand.dir, path):
            missing.append(f"brand:{rel} (ścieżka wychodzi poza folder marki {brand.dir})")
            return m.group(0)
        if not path.is_file():
            missing.append(f"brand:{rel} (nie ma pliku {path})")
            return m.group(0)
        return path.resolve().as_uri()

    out = _BRAND_REF.sub(repl, text)
    if missing:
        raise GdError("kompozycja odwołuje się do plików, których nie ma w bibliotece marki: "
                      + "; ".join(missing))
    return out


def _font_faces(brand: Optional[Brand]) -> str:
    if brand is None:
        return ""
    css = []
    for f in brand.fonts.values():
        if not f.family or f.file is None or not f.file.is_file():
            continue
        if not brandlib.inside(brand.dir, f.file) or f.file.suffix.lower() not in brandlib.FONT_EXTENSIONS:
            continue  # build_html odrzuca to wcześniej; tu tylko druga linia obrony
        mime = FONT_MIME[f.file.suffix.lower()]
        data = base64.b64encode(f.file.read_bytes()).decode("ascii")
        family = f.family.replace("\\", "\\\\").replace('"', '\\"')
        css.append(f'@font-face{{font-family:"{family}";src:url("data:{mime};base64,{data}");}}')
    return "\n".join(css)


FONT_MIME = {".ttf": "font/ttf", ".otf": "font/otf", ".woff": "font/woff", ".woff2": "font/woff2"}

# Zasada bezpieczeństwa strony (CSP), wstrzykiwana jako PIERWSZY element: kompozycja bywa pisana
# przez agenta, a po regule Codexa Chrome działa poza piaskownicą. Bez skryptów strony (tylko nasz
# raport, z jednorazowym nonce), bez sieci, ramek, obiektów, @import i zewnętrznych fontów.
# Obrazy tylko z plików i data:, fonty tylko z data: (fonty marki wstawiamy sami jako data:).
# `base-uri file:` zamiast 'none', bo sami wstawiamy <base> (jako pierwszy, więc inny <base>
# kompozycji i tak jest pomijany).
CSP_DIRECTIVES = ("default-src 'none'", "script-src 'nonce-{nonce}'", "style-src 'unsafe-inline'",
                  "img-src file: data:", "font-src data:", "connect-src 'none'", "frame-src 'none'",
                  "object-src 'none'", "base-uri file:", "form-action 'none'")


def csp_policy(nonce: str) -> str:
    return "; ".join(d.format(nonce=nonce) for d in CSP_DIRECTIVES)


# <meta http-equiv="refresh"> to jedyne przekierowanie bez skryptu, a CSP go nie blokuje.
_REFRESH = re.compile(r"http-equiv\s*=\s*[\"']?\s*refresh", re.I)


def _reject_redirects(text: str, composition: Path) -> None:
    if _REFRESH.search(htmllib.unescape(text)):
        raise GdError(f"kompozycja {composition.name} zawiera <meta http-equiv=\"refresh\">, który "
                      "przekierowuje stronę. Usuń go: kompozycja ma być jedną nieruchomą stroną.")


def _doctype_end(text: str) -> Optional[int]:
    """Pozycja tuż za doctype, jeśli przed nim są tylko BOM, białe znaki i zwykłe komentarze.

    Komentarz bierzemy tylko wtedy, gdy przeglądarka na pewno zakończy go w tym samym miejscu
    co my (pierwsze `-->`): bez `--!>` w środku i bez zapisu `<!-->` albo `<!--->`. Inaczej
    skrypt ukryty „w komentarzu” mógłby wykonać się przed naszą zasadą bezpieczeństwa."""
    i, n = (1 if text.startswith("\ufeff") else 0), len(text)
    while True:
        while i < n and text[i] in "\t\n\f\r ":
            i += 1
        if not text.startswith("<!--", i):
            break
        j = text.find("-->", i + 4)
        body = text[i + 4:j] if j >= 0 else ""
        if j < 0 or body.startswith((">", "->")) or "--!>" in body:
            return None
        i = j + 3
    if text[i:i + 9].lower() != "<!doctype":
        return None
    j = text.find(">", i)
    return j + 1 if j >= 0 else None


def _insert_prelude(text: str, prelude: str) -> str:
    """Wstawia `prelude` po doctype (żeby nie zmieniać trybu strony) albo na samym początku,
    przed jakąkolwiek treścią kompozycji."""
    pos = _doctype_end(text)
    if pos is None:
        pos = 1 if text.startswith("\ufeff") else 0
    return text[:pos] + prelude + text[pos:]


_REPORT_JS = r"""
(function () {
  var BRAND = %BRAND%;
  var DECLARED = %DECLARED%;
  function hex(c) {
    var m = c.match(/[\d.]+/g) || [0, 0, 0];
    return "#" + [0, 1, 2].map(function (i) {
      return ("0" + Math.round(Number(m[i])).toString(16)).slice(-2);
    }).join("");
  }
  function families(cs) {
    return cs.fontFamily.split(",").map(function (s) { return s.trim().replace(/^["']|["']$/g, ""); });
  }
  function run() {
    var report = {fonts: {}, fonts_used: [], elements: [], images_broken: []};
    var used = {};
    Array.prototype.forEach.call(document.querySelectorAll("body, body *"), function (el) {
      families(getComputedStyle(el)).forEach(function (f) { used[f.toLowerCase()] = true; });
    });
    BRAND.forEach(function (fam) {
      report.fonts[fam] = DECLARED.indexOf(fam) >= 0 && document.fonts.check("16px " + JSON.stringify(fam));
      if (used[fam.toLowerCase()]) report.fonts_used.push(fam);
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-gd]"), function (el) {
      var cs = getComputedStyle(el), r = el.getBoundingClientRect();
      var item = {gd: el.getAttribute("data-gd"), id: el.id || "",
                  text: (el.textContent || "").trim(), font: families(cs)[0],
                  color: hex(cs.color),
                  box: [r.x, r.y, r.width, r.height].map(function (n) { return Math.round(n * 10) / 10; })};
      if (el.tagName === "IMG") item.natural = [el.naturalWidth, el.naturalHeight];
      report.elements.push(item);
    });
    Array.prototype.forEach.call(document.images, function (img) {
      if (img.complete && img.naturalWidth === 0) report.images_broken.push(img.getAttribute("src") || "");
    });
    document.getElementById("gd-report").textContent = JSON.stringify(report);
  }
  function go() {
    // fonty z @font-face ładują się leniwie: wczytaj każdy zadeklarowany, zanim zmierzysz
    var loads = DECLARED.map(function (f) {
      return document.fonts.load("16px " + JSON.stringify(f)).catch(function () {});
    });
    Promise.all(loads).then(function () { return document.fonts.ready; }).then(run, run);
  }
  if (document.readyState === "complete") go(); else window.addEventListener("load", go);
})();
"""


def build_html(composition: Path, brand: Optional[Brand], fmt: dict, hide_text: bool = False,
               pdf: bool = False, overlay: bool = False) -> Path:
    """Zapisuje kompozycję z wstrzykniętymi fontami, zmiennymi i raportem; zwraca ścieżkę pliku."""
    composition = Path(composition)
    try:
        text = composition.read_text(encoding="utf-8")
    except OSError as e:
        raise GdError(f"nie mogę odczytać {composition}: {e}")
    _reject_redirects(text, composition)
    problems = brandlib.path_problems(brand) if brand is not None else []
    if problems:
        raise GdError("biblia marki wskazuje pliki spoza swojego folderu albo pliki złego typu: "
                      + "; ".join(problems))
    text = _brand_uris(text, brand)
    w, h = fmt["width"], fmt["height"]
    base = composition.resolve().parent.as_uri().rstrip("/") + "/"
    css = []
    if brand is not None:
        css.append(_font_faces(brand))
        css.append(":root{" + brandlib.css_vars(brand).replace("\n", " ") + "}")
    css.append(f"html,body{{width:{w}px;height:{h}px;margin:0;overflow:hidden}}")
    css.append("*{-webkit-print-color-adjust:exact;print-color-adjust:exact}")
    if pdf and fmt.get("page_mm"):
        pw, ph = fmt["page_mm"]
        css.append(f"@page{{size:{pw}mm {ph}mm;margin:0}}")
        # strona ma wymiar w mm, a kompozycja w px: skalujemy ją na całą stronę
        css.append(f"html{{zoom:{pw / MM_PER_INCH * 96 / w:.8f}}}")
    if hide_text:
        css.append('[data-gd="text"]{visibility:hidden}')
    head = '<style id="gd-inject">\n' + "\n".join(c for c in css if c) + "\n</style>\n"
    nonce = secrets.token_urlsafe(18)  # nowy przy każdym budowaniu; strona go nie zna
    # Pierwsze w <head>: zasada bezpieczeństwa, potem kodowanie (musi być w pierwszym 1 KB) i <base>.
    prelude = (f'<meta http-equiv="Content-Security-Policy" content="{csp_policy(nonce)}">\n'
               '<meta charset="utf-8">\n'
               f'<base href="{htmllib.escape(base)}">\n')
    s = fmt.get("safe") or {}
    tail = ""
    if overlay:
        shade = "position:absolute;background:rgba(255,0,0,.35)"
        top, right, bottom, left = (s.get(k, 0) for k in ("top", "right", "bottom", "left"))
        tail += (f'<div id="gd-safe-overlay" style="position:absolute;left:0;top:0;width:{w}px;'
                 f'height:{h}px;pointer-events:none;z-index:2147483647">'
                 f'<div style="{shade};left:0;top:0;width:{w}px;height:{top}px"></div>'
                 f'<div style="{shade};left:0;bottom:0;width:{w}px;height:{bottom}px"></div>'
                 f'<div style="{shade};left:0;top:{top}px;width:{left}px;height:{h - top - bottom}px"></div>'
                 f'<div style="{shade};right:0;top:{top}px;width:{right}px;height:{h - top - bottom}px"></div>'
                 "</div>\n")
    families = [f.family for f in brand.fonts.values() if f.family] if brand else []
    declared = [f.family for f in brand.fonts.values()
                if f.family and f.file is not None and f.file.is_file()] if brand else []
    js = _REPORT_JS.replace("%BRAND%", json.dumps(families)).replace("%DECLARED%", json.dumps(declared))
    js = js.replace("</", "<\\/")
    tail += f'<pre id="gd-report" hidden></pre>\n<script nonce="{nonce}">{js}</script>\n'

    if re.search(r"</head\s*>", text, re.I):
        text = re.sub(r"</head\s*>", lambda m: head + m.group(0), text, count=1, flags=re.I)
    elif re.search(r"<body[^>]*>", text, re.I):
        text = re.sub(r"<body[^>]*>", lambda m: head + m.group(0), text, count=1, flags=re.I)
    else:
        prelude += head
    text = _insert_prelude(text, prelude)
    if re.search(r"</body\s*>", text, re.I):
        idx = [m.start() for m in re.finditer(r"</body\s*>", text, re.I)][-1]
        text = text[:idx] + tail + text[idx:]
    else:
        text += tail
    tmp = Path(tempfile.mkdtemp(prefix="gd-build-"))
    out = tmp / "composition.html"
    out.write_text(text, encoding="utf-8")
    return out


def _read_report(dom: str) -> dict:
    m = re.search(r'<pre id="gd-report"[^>]*>(.*?)</pre>', dom, re.S)
    if not m or not m.group(1).strip():
        raise GdError("przeglądarka nie zwróciła raportu z kompozycji (błąd skryptu na stronie?)")
    try:
        return json.loads(htmllib.unescape(m.group(1)))
    except ValueError as e:
        raise GdError(f"raport z kompozycji jest nieczytelny: {e}")


def report(composition: Path, brand: Optional[Brand], fmt: dict) -> dict:
    """Raport pomiarów kompozycji (fonty, elementy, uszkodzone obrazy); używa go też check."""
    built = build_html(composition, brand, fmt)
    try:
        return _read_report(browser.dump_dom(built, fmt["width"], fmt["height"]))
    finally:
        shutil.rmtree(built.parent, ignore_errors=True)


def _verify(rep: dict, fmt_id: str, composition: Path) -> None:
    problems = []
    for fam in rep.get("fonts_used", []):
        if not rep.get("fonts", {}).get(fam):
            problems.append(f"font „{fam}” z biblii marki nie wczytał się (sprawdź plik fontu w brand/fonts/)")
    for src in rep.get("images_broken", []):
        problems.append(f"nie wczytał się obraz „{src}”")
    if problems:
        raise GdError(f"kompozycja {composition.name} (format {fmt_id}): " + "; ".join(problems))


def _brand_of(job: Path) -> Optional[Brand]:
    value = jobs.load(job).get("brand")
    if not value:
        return None
    return brandlib.load(Path(value))


def render_job(job_dir: Path, only: Optional[str] = None, preview: bool = False) -> List[Path]:
    job = Path(job_dir)
    data = jobs.load(job)
    for name in ("final", "drafts"):
        if (job / name).exists() and not brandlib.inside(job, job / name):
            raise GdError(f"folder {name}/ zlecenia wskazuje poza folderem zlecenia "
                          f"({(job / name).resolve()}); nie zapisuję tam. Usuń to dowiązanie.")
    known = formats()
    ids = [only] if only else list(data.get("formats", []))
    if only and only not in data.get("formats", []):
        raise GdError(f"zlecenie nie ma formatu {only}. Formaty zlecenia: "
                      + ", ".join(data.get("formats", [])))
    for i in ids:
        if i not in known:
            raise GdError(f"nieznany format {i}. Znane formaty: {', '.join(known)}")
    missing = [f"composition/{i}.html" for i in ids if not (job / "composition" / f"{i}.html").is_file()]
    if missing:
        raise GdError("brak pliku kompozycji: " + ", ".join(missing)
                      + ". Napisz kompozycję (wzór: templates/composition-starter.html).")
    brand = _brand_of(job)
    # najpierw pomiary wszystkich formatów, żeby błąd nie zostawił połowy wyników
    for i in ids:
        _verify(report(job / "composition" / f"{i}.html", brand, known[i]), i,
                job / "composition" / f"{i}.html")
    produced: List[Path] = []
    for i in ids:
        fmt, comp = known[i], job / "composition" / f"{i}.html"
        w, h = fmt["width"], fmt["height"]
        if preview:
            built = build_html(comp, brand, fmt, overlay=True)
            try:
                out = job / "drafts" / f"preview-{i}.png"
                browser.screenshot(built, out, w, h)
                produced.append(out)
            finally:
                shutil.rmtree(built.parent, ignore_errors=True)
            continue
        built = build_html(comp, brand, fmt)
        try:
            out = job / "final" / f"{i}.png"
            browser.screenshot(built, out, w, h)
            produced.append(out)
        finally:
            shutil.rmtree(built.parent, ignore_errors=True)
        if fmt.get("pdf"):
            built = build_html(comp, brand, fmt, pdf=True)
            try:
                out = job / "final" / f"{i}.pdf"
                browser.pdf(built, out, w, h)
                produced.append(out)
            finally:
                shutil.rmtree(built.parent, ignore_errors=True)
    return produced
