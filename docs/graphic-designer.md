# Plugin „graphic-designer”: projektant grafik

Plugin do Codexa, który robi grafiki zgodne z Twoją marką: plakaty, posty, relacje, okładki
wydarzeń, wydruki A4 i A3. Czyta bibliotekę marki (kolory, fonty, logo), składa grafikę z warstw,
sprawdza błędy i zapisuje każdą wersję. Rozmawiasz po polsku, jak z projektantem.

## Instalacja

Dwa polecenia (w terminalu albo poproś o to Codexa):

```
codex plugin marketplace add guc-net/codex-marketplace
codex plugin add graphic-designer@guc-net
```

Potem **uruchom ponownie aplikację ChatGPT** i zacznij **nową rozmowę** w Codexie.
Szczegóły i zrzuty ekranu: [instalacja.md](instalacja.md). Do składania grafik potrzebna jest
przeglądarka Chrome, Edge albo Chromium (plugin ją znajdzie; sprawdzi to polecenie `env`).

## Jak zacząć

Napisz na przykład:

- „Zaprojektujmy plakat na wieczór z ceramiką w sobotę o 18.00”
- „Nałóż nasze logo na to zdjęcie”
- „Wymyślmy napis do posta”

Plugin zapyta, gdzie trzymać zlecenia (biblioteka), zbierze krótki brief (cel, odbiorca, teksty
dosłownie, formaty), pokaże kilka kierunków do wyboru, a potem dopracuje wybrany. Nic nie
publikuje i niczego nie wysyła do drukarni: na końcu dostajesz pliki i listę rzeczy do
sprawdzenia przez człowieka.

Biblia marki to folder `brand/` z plikiem `brand.md`, logo i fontami. Jeśli jej nie masz,
plugin założy szkielet i poprowadzi Cię przez uzupełnienie.

## Jak zacząć (krok po kroku)

Dla kogoś, kto nie wie nic o pluginach.

1. **Zainstaluj plugin, potem zawsze zacznij NOWĄ rozmowę.** Rozmowa założona przed instalacją
   albo przed aktualizacją nie widzi pluginu ani jego nowej wersji.
2. **Otwórz folder, w którym leży `brand/`** (biblia marki: kolory, fonty, logo). Jeśli takiego
   folderu nie masz, otwórz dowolny: plugin zapyta wtedy o logo, kolory i fonty.
3. **Napisz, co chcesz zrobić.** Plugin zwykle włącza się sam, gdy prosisz o grafikę. Żeby mieć
   pewność, wpisz `@` i wybierz `graphic-designer` przed swoją prośbą (w aplikacji Codex
   podpowiedź brzmi „Type @ to invoke the plugin or one of its bundled skills explicitly”).
   W wierszu poleceń `/plugins` pokazuje zainstalowane pluginy.
4. **Wybierz model:** zalecany jest `gpt-6.1-sol` na poziomie Medium. W wierszu poleceń
   zmienisz go przez `/model`, w aplikacji przez wybór modelu pod polem wiadomości.
5. **Czego oczekiwać.** Agent powinien: zadać kilka pytań o zlecenie, pokazać trzy kierunki
   i **poczekać na Twój wybór**, dopracować wybrany etapami, złożyć grafikę, sprawdzić ją
   automatycznie i dać listę rzeczy do sprawdzenia przez Ciebie. Jeśli pominie krok (np. od razu
   pokaże „gotową” grafikę), napisz: **„Wróć do procedury pluginu graphic-designer: najpierw
   brief i kierunki.”**
6. **Okno z prośbą o zgodę** (piaskownica Codexa, sieć, zapis w Twoim folderze) znaczy: zezwól
   jednorazowo. Plugin prosi tylko wtedy, gdy bez tego nie złoży albo nie sprawdzi grafiki.
   Szczegóły są niżej, w sekcji „Piaskownica Codexa”.

## Jak działa spójność

Model nie pamięta Twojej marki między rozmowami, więc spójność bierze się z kilku rzeczy:

- **Biblia marki** jest jedna i zapisana w plikach, nie w pamięci modelu. Kolory, fonty i logo
  zawsze pochodzą z niej.
- **Napisy i logo składa HTML**, nie generator obrazów. Generator robi tylko tła i zdjęcia.
- **Zatwierdzone warstwy są zamrożone** (kopia z sumą kontrolną). Plugin wykrywa, gdy się zmienią.
- **Sprawdzanie przed pokazaniem:** rozmiar, fonty, polskie znaki, kontrast, strefy bezpieczne,
  proporcje i rozmiar logo.
- **Zasady dla poleceń do generatora** (stały blok stylu, jedna zmiana na turę) są w
  `plugins/graphic-designer/skills/graphic-designer/references/image-prompting.md`.

Ogólny opis spójności grafik: [spojnosc.md](spojnosc.md).

## Koszty

Obrazy z generatora liczą się do limitu Codexa i zużywają go kilka razy szybciej niż zwykła rozmowa.
Które plany mają obrazy i co zrobić po wyczerpaniu limitu: [plany.md](plany.md).

Uwaga: jeśli w środowisku ustawiony jest klucz `OPENAI_API_KEY`, Codex może liczyć obrazy według
cennika API (za każdy obraz), a nie z abonamentu. Polecenie `env` ostrzega o tym. Nie ustawiaj
klucza, jeśli chcesz zostać przy abonamencie.

## Piaskownica Codexa

Codex uruchamia polecenia w piaskownicy, która ogranicza dostęp do sieci, do plików i do
niektórych programów. Przeglądarka Chrome w piaskownicy czasem nie startuje i kończy się
awarią. Wtedy `env` pokazuje `BROWSER-TEST: FAILED`, a `render` zwraca komunikat zaczynający
się od `SANDBOX?:`.

To nie jest błąd Twojej marki ani grafiki. Plugin poprosi Cię o **jednorazową zgodę** na
uruchomienie polecenia poza piaskownicą (okno zgody w aplikacji). Możesz też uruchomić
aplikację z szerszymi uprawnieniami. Bez zgody plugin nie złoży ani nie sprawdzi grafiki; może
tylko proponować kierunki i szkice. Podobnie pyta o zgodę na dostęp do sieci (sprawdzenie
aktualizacji) i na zapis w Twojej bibliotece grafik.

## Telefon

Nie wiadomo jeszcze, czy plugin działa w aplikacji ChatGPT na telefonie. Nie sprawdzaliśmy tego,
więc na razie nie obiecujemy. Gdy to zbadamy, zapiszemy wynik tutaj.

## Aktualizacje

Plugin raz dziennie sprawdza (`update-check`), czy jest nowsza wersja, i mówi, co się zmieniło.
Ręcznie: `codex plugin marketplace upgrade guc-net`, potem nowa rozmowa. Historię zmian
czytasz w `plugins/graphic-designer/CHANGELOG.md`.
