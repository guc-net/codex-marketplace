# Projektant grafik

Plugin do Codexa: grafiki zgodne z marką (plakaty, posty, relacje, okładki wydarzeń, wydruki A4 i A3).
Czyta bibliotekę marki (kolory, fonty, logo), składa grafikę warstwami w HTML, sprawdza ją skryptem
i zapisuje każdą wersję.

Dokumentacja dla użytkownika: [docs/graphic-designer.md](../../docs/graphic-designer.md)
(instalacja, jak zacząć, spójność, koszty).

## Jak zacząć (krok po kroku)

Dla kogoś, kto nie wie nic o pluginach.

1. **Zainstaluj plugin, potem zawsze zacznij NOWĄ rozmowę.** Rozmowa założona przed instalacją
   albo przed aktualizacją nie widzi pluginu ani jego nowej wersji.
2. **Skonfiguruj plugin (raz).** Po instalacji aplikacja może od razu zaproponować konfigurację.
   Jeśli nie, napisz: „Skonfiguruj graphic-designer”. Asystent sprawdzi, co działa, wyjaśni,
   dlaczego na Macu przeglądarka potrzebuje wyjątku od piaskownicy, i niczego nie zapisze bez
   Twojego „tak”. Po zapisaniu reguł zamknij aplikację całkiem i otwórz ją ponownie. Co zapisuje
   i jak to cofnąć: sekcja „Co robi konfiguracja i jak ją cofnąć” w
   [docs/graphic-designer.md](../../docs/graphic-designer.md).
3. **Otwórz folder, w którym leży `brand/`** (biblia marki: kolory, fonty, logo). Jeśli takiego
   folderu nie masz, otwórz dowolny: plugin zapyta wtedy o logo, kolory i fonty.
4. **Napisz, co chcesz zrobić.** Plugin zwykle włącza się sam, gdy prosisz o grafikę. Żeby mieć
   pewność, wpisz `@` i wybierz `graphic-designer` przed swoją prośbą (w aplikacji Codex
   podpowiedź brzmi „Type @ to invoke the plugin or one of its bundled skills explicitly”).
   W wierszu poleceń `/plugins` pokazuje zainstalowane pluginy.
5. **Wybierz model:** zalecany jest `gpt-6.1-sol` na poziomie Medium. W wierszu poleceń
   zmienisz go przez `/model`, w aplikacji przez wybór modelu pod polem wiadomości.
6. **Czego oczekiwać.** Agent powinien: zadać kilka pytań o zlecenie, pokazać trzy kierunki
   i **poczekać na Twój wybór**, dopracować wybrany etapami, złożyć grafikę, sprawdzić ją
   automatycznie i dać listę rzeczy do sprawdzenia przez Ciebie. Jeśli pominie krok (np. od razu
   pokaże „gotową” grafikę), napisz: **„Wróć do procedury pluginu graphic-designer: najpierw
   brief i kierunki.”**
7. **Okno z prośbą o zgodę** (piaskownica Codexa, sieć, zapis w Twoim folderze) znaczy: zezwól
   jednorazowo. Plugin prosi tylko wtedy, gdy bez tego nie złoży albo nie sprawdzi grafiki. Po
   konfiguracji z punktu 2 większość tych okien znika.
   Szczegóły: sekcja „Piaskownica Codexa” w [docs/graphic-designer.md](../../docs/graphic-designer.md).

## Wiedza projektanta

Krótkie pliki w `skills/graphic-designer/references/`: `brief.md`, `logo.md`, `typography.md`,
`color.md`, `composition.md`, `poster.md`, `formats.md`, `print.md`, `image-prompting.md`,
`generic-ai-tells.md`, `critique.md` (14 punktów samooceny, z oznaczeniem, które liczy skrypt).

## Skrypt

`python3 plugins/graphic-designer/scripts/designer.py <polecenie>` (Windows: `py -3`).
Polecenia: `version`, `library`, `new`, `set-brand`, `status`, `draft`, `choose`, `freeze`, `brand`,
`brand-init`, `brand-log`, `render`, `check`, `share`, `finalize`, `adopt`, `env`, `update-check`,
`doctor`, `setup-launcher`, `setup-rules`. Pomoc: `designer.py <polecenie> --help`.

Konfiguracja: `doctor` pokazuje, co działa i jaki jest następny krok (nic nie zmienia);
`setup-launcher` instaluje stały skrypt startowy w `~/.codex/graphic-designer/designer.py`
(`CODEX_HOME`; folder chroniony przez Codex, ustawienia zostają w `~/.graphic-designer`,
`GD_HOME`), który znajduje najnowszą wersję pluginu, i usuwa nasz dawny plik z `~/.graphic-designer`;
`setup-rules` pokazuje, a z `--apply` dopisuje albo z `--remove` usuwa oznaczony blok reguł Codexa
(`~/.codex/rules/default.rules`; przed pierwszą zmianą powstaje kopia
`default.rules.graphic-designer.bak`). Reguły pozwalają uruchamiać poza piaskownicą, bez pytania,
tylko `env`, `render`, `check`, `update-check` i `doctor` przez stały skrypt. Reguła dopasowuje
tylko początek polecenia, więc argumenty nie są ograniczone; stronę ze zlecenia zamyka zasada
bezpieczeństwa przeglądarki (bez skryptów, sieci i ramek), ale może ona pokazać na obrazie dowolny
plik graficzny z dysku, więc otwieraj tylko zlecenia, którym ufasz. `update-check` nie przyjmuje
adresu ani pliku w argumentach.

Skrypt pilnuje procesu: `choose` zapisuje wybrany kierunek (`--direct` dla zlecenia bez rundy
kierunków), `status` pokazuje etap i następny krok, a `check` zgłasza błąd `process`, gdy brief
jest pusty albo nie zapisano wyboru. `finalize` nie zamknie pakietu bez czystego `check`.
