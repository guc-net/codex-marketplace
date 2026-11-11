# Projektant grafik

Plugin do Codexa: grafiki zgodne z marką (plakaty, posty, relacje, okładki wydarzeń, wydruki A4 i A3).
Czyta bibliotekę marki (kolory, fonty, logo), składa grafikę warstwami w HTML, sprawdza ją skryptem
i zapisuje każdą wersję.

Dokumentacja dla użytkownika: [docs/graphic-designer.md](../../docs/graphic-designer.md)
(instalacja, jak zacząć, spójność, koszty).

## Wiedza projektanta

Krótkie pliki w `skills/graphic-designer/references/`: `brief.md`, `logo.md`, `typography.md`,
`color.md`, `composition.md`, `poster.md`, `formats.md`, `print.md`, `image-prompting.md`,
`generic-ai-tells.md`, `critique.md` (14 punktów samooceny, z oznaczeniem, które liczy skrypt).

## Skrypt

`python3 plugins/graphic-designer/scripts/designer.py <polecenie>` (Windows: `py -3`).
Polecenia: `version`, `library`, `new`, `set-brand`, `status`, `draft`, `freeze`, `brand`,
`brand-init`, `brand-log`, `render`, `check`, `share`, `finalize`, `adopt`, `env`, `update-check`.
Pomoc: `designer.py <polecenie> --help`.
