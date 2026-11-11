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

## Telefon

Nie wiadomo jeszcze, czy plugin działa w aplikacji ChatGPT na telefonie. Nie sprawdzaliśmy tego,
więc na razie nie obiecujemy. Gdy to zbadamy, zapiszemy wynik tutaj.

## Aktualizacje

Plugin raz dziennie sprawdza (`update-check`), czy jest nowsza wersja, i mówi, co się zmieniło.
Ręcznie: `codex plugin marketplace upgrade guc-net`, potem nowa rozmowa. Historię zmian
czytasz w `plugins/graphic-designer/CHANGELOG.md`.
