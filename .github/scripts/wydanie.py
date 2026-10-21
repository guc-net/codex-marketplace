"""Wydanie po scaleniu: każdy plugin, którego wersja z plugin.json nie ma jeszcze tagu
`<plugin>-v<wersja>`, dostaje tag na bieżącym commicie i wydanie na GitHubie z notatkami
z sekcji tej wersji w CHANGELOG.md. Scalone do `main` = na marketplace.

  python .github/scripts/wydanie.py            # wydaj brakujące (wymaga gh i GH_TOKEN)
  python .github/scripts/wydanie.py --sprawdz  # tylko pokaż, co by poszło
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent


def notatki(changelog, wersja):
    """Treść sekcji `## <wersja> …` z CHANGELOG, bez nagłówka."""
    linie, w_sekcji = [], False
    for linia in changelog.splitlines():
        if linia.startswith("## "):
            if w_sekcji:
                break
            m = re.match(r"^##\s+\[?v?(\d+\.\d+\.\d+)", linia)
            w_sekcji = bool(m) and m.group(1) == wersja
            continue
        if w_sekcji:
            linie.append(linia)
    tekst = "\n".join(linie).strip()
    if not tekst:
        raise ValueError(f"CHANGELOG nie ma sekcji {wersja}")
    return tekst + "\n"


def plan(repo=REPO):
    """[(tag, tytuł, notatki)] dla każdego pluginu z marketplace."""
    mp = json.loads((repo / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
    wynik = []
    for wpis in mp["plugins"]:
        katalog = repo / wpis["source"]["path"]
        wersja = json.loads((katalog / "plugin.json").read_text(encoding="utf-8"))["version"]
        tekst = notatki((katalog / "CHANGELOG.md").read_text(encoding="utf-8"), wersja)
        wynik.append((f"{wpis['name']}-v{wersja}", f"{wpis['name']} {wersja}", tekst))
    return wynik


def tag_istnieje(tag):
    out = subprocess.run(["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
                         cwd=REPO, check=True, capture_output=True, text=True).stdout
    return bool(out.strip())


def main(argv):
    sprawdz = "--sprawdz" in argv
    commit = os.environ.get("GITHUB_SHA") or subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    for tag, tytul, tekst in plan():
        if tag_istnieje(tag):
            print(f"{tag}: już wydane")
            continue
        print(f"{tag}: {'do wydania' if sprawdz else 'wydaję'} na {commit[:7]}")
        if sprawdz:
            print(tekst)
            continue
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as f:
            f.write(tekst)
        subprocess.run(["gh", "release", "create", tag, "--target", commit, "--title", tytul,
                        "--notes-file", f.name], cwd=REPO, check=True)


if __name__ == "__main__":
    main(sys.argv[1:])
