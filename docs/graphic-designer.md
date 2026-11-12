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

**Konfiguracja (raz, na Macu).** Po instalacji aplikacja może od razu zaproponować konfigurację;
jeśli nie, napisz **„Skonfiguruj graphic-designer”**. Dzięki niej Codex nie pyta o zgodę przy
każdym składaniu grafiki. Co dokładnie zapisuje i jak to cofnąć: sekcja „Co robi konfiguracja
i jak ją cofnąć”.

## Jak zacząć (krok po kroku)

Dla kogoś, kto nie wie nic o pluginach.

1. **Zainstaluj plugin, potem zawsze zacznij NOWĄ rozmowę.** Rozmowa założona przed instalacją
   albo przed aktualizacją nie widzi pluginu ani jego nowej wersji.
2. **Skonfiguruj plugin (raz).** Po instalacji aplikacja może od razu zaproponować konfigurację.
   Jeśli nie, napisz: „Skonfiguruj graphic-designer”. Asystent sprawdzi, co działa, wyjaśni,
   dlaczego na Macu przeglądarka potrzebuje wyjątku od piaskownicy, i da Ci wybór. Niczego nie
   zapisze bez Twojego „tak”. Po zapisaniu reguł zamknij aplikację całkiem i otwórz ją ponownie.
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
   konfiguracji z punktu 2 większość tych okien znika. Szczegóły są niżej, w sekcji „Piaskownica
   Codexa”.

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
awarią.

**Dlaczego tak jest na Macu (sprawdzone 11.11.2026).** Piaskownica Codexa na macOS blokuje
programom dostęp do usług systemu, z których Chrome korzysta zaraz po starcie: do usługi okien,
do uruchamiania programów i do kontroli uprawnień. Dziennik odmów piaskownicy pokazuje te odmowy,
a Chrome kończy się awarią. Żaden przełącznik Chrome (także wyłączenie jego własnej piaskownicy)
tego nie naprawia, bo to system odmawia, a nie Chrome. Poza piaskownicą Chrome działa
normalnie, więc jedyne wyjście to uruchamiać go poza nią: za jednorazową zgodą albo dzięki
konfiguracji opisanej niżej. Wbudowana przeglądarka aplikacji tu nie pomoże: w naszych próbach
z 11.11.2026 blokowała adresy `file://` i zapisywała tylko JPEG (w Twojej wersji aplikacji może to
wyglądać inaczej). Wtedy `env` pokazuje `BROWSER-TEST: FAILED`, a `render` zwraca komunikat
zaczynający się od `SANDBOX?:`.

Na Macu przeglądarka w piaskownicy kończy się awarią, a system pokazuje okienko „Google Chrome
quit unexpectedly”. Plugin wie o tym i w piaskownicy w ogóle jej nie uruchamia: `env` pokazuje
wtedy `BROWSER-TEST: SKIPPED`. Jeśli okienko mimo to się pojawi, kliknij „Ignore”.

To nie jest błąd Twojej marki ani grafiki. Plugin poprosi Cię o **jednorazową zgodę** na
uruchomienie polecenia poza piaskownicą (okno zgody w aplikacji). Możesz też uruchomić
aplikację z szerszymi uprawnieniami. Po zgodzie Chrome działa (sprawdzone 11.11.2026 w aplikacji Codex na Macu): składa poprawny plik
PNG. Komunikaty w wyniku polecenia o `CVDisplayLink` i „Trying to load the allocator multiple
times” to nieszkodliwy szum. Jeśli okno zgody pozwala zapamiętać decyzję dla takich poleceń,
możesz z tego skorzystać. Nie eksportuj grafiki przez wbudowaną przeglądarkę aplikacji: w naszych
próbach blokowała adresy `file://`. Bez zgody plugin nie złoży ani nie sprawdzi grafiki; może
tylko proponować kierunki i szkice. Podobnie pyta o zgodę na dostęp do sieci (sprawdzenie
aktualizacji) i na zapis w Twojej bibliotece grafik.

Gdyby plugin mimo uruchomienia poza piaskownicą nadal pisał `SANDBOX?:` albo `SKIPPED` (błędnie
uznał, że jest w piaskownicy), poproś agenta, żeby powtórzył polecenie z `GD_BROWSER_TRY=1` na
początku. To wymusza próbę uruchomienia przeglądarki.

## Co robi konfiguracja i jak ją cofnąć

Konfiguracja (procedura „setup”; uruchomisz ją słowami „Skonfiguruj graphic-designer”) jest
jednorazowa i dotyczy głównie Maca w aplikacji Codex. Asystent pokazuje wszystko, co ma zapisać,
i pyta o zgodę. Na pytanie „Czy dopisać te reguły?” odpowiadasz Ty.

**Co zapisuje**

- Mały plik startowy `designer.py` w folderze `graphic-designer` wewnątrz folderu Codexa:
  `~/.codex/graphic-designer/designer.py` (przy ustawionej zmiennej `CODEX_HOME` w tym folderze).
  Codex chroni swój folder przed zapisem z piaskownicy, więc agent pracujący w piaskownicy nie
  podmieni pliku, któremu reguły ufają. Ścieżka do pliku nie zawiera numeru wersji, więc nie
  zmienia się przy aktualizacjach pluginu i reguły nie przestają działać. Plik sam znajduje
  najnowszą wersję pluginu, ale tylko w folderze `plugins/cache/guc-net/graphic-designer/` Codexa
  (wersje zapisane jako `X.Y.Z`, z plikiem `plugin.json` o nazwie `graphic-designer`).
  Twoje ustawienia (biblioteka zleceń, sprawdzenie aktualizacji) zostają tam, gdzie były:
  w `~/.graphic-designer` (inny folder wskaże zmienna `GD_HOME`).
- Jeśli wcześniejsza wersja zapisała plik startowy w `~/.graphic-designer/designer.py`, `setup-launcher`
  usuwa go (tylko gdy to nasz plik; cudzego nie rusza) i ostrzega, gdy reguły nadal mu ufają.
  Wtedy `setup-rules --apply` przepisze reguły na nową ścieżkę.
- Jeden blok reguł Codexa, dopisany na końcu pliku `~/.codex/rules/default.rules` (albo w folderze
  wskazanym zmienną `CODEX_HOME`), między liniami `# >>> graphic-designer (zarządzane przez plugin) >>>`
  i `# <<< graphic-designer <<<`. Reszty pliku nie rusza i nie przepisuje; jeśli pliku nie ma,
  powstaje nowy. Plik jest zapisywany atomowo (najpierw plik tymczasowy, potem podmiana), więc
  przy błędzie zostaje taki, jaki był. Przed pierwszą zmianą istniejącego pliku powstaje
  jednorazowa kopia `default.rules.graphic-designer.bak` w tym samym folderze; kolejnych zmian
  nie kopiuje i istniejącej kopii nie nadpisuje. Przy aktualizacji bloku plugin zastępuje całą
  treść między znacznikami, więc ręczne zmiany w środku bloku znikają.

**Co te reguły pozwalają, uczciwie.** Pięć poleceń pluginu: `env`, `render`, `check`,
`update-check` i `doctor`, uruchamianych dokładnie przez ten plik startowy. Uruchamiają się
**poza piaskownicą i bez pytania o zgodę**. Trzeba to rozumieć tak:

- Reguła dopasowuje tylko początek polecenia (`python3 <plik> render`). Argumenty po nim, np.
  `--job <folder>`, nie są ograniczone. Nie jest to więc „zgoda na jedno konkretne zlecenie”.
- `render` i `check` otwierają stronę ze zlecenia w Chrome **bez piaskownicy**. Plugin zamyka
  tę stronę zasadą bezpieczeństwa przeglądarki (CSP): bez skryptów, bez połączeń z siecią, bez
  ramek i wtyczek, bez przekierowań; Chrome dostaje też flagi wyłączające rozszerzenia i
  synchronizację. Sprawdzamy to testami z prawdziwą przeglądarką.
- Zostaje jedno znane ograniczenie: strona ze zlecenia może pokazać na składanym obrazie **dowolny
  plik graficzny z dysku** (obrazy z adresów `file:` są dozwolone, bo zlecenia korzystają z
  logo i zdjęć w swoich folderach). Skrypty i sieć są zablokowane, więc taki plik nie wyjdzie
  przez sieć, ale może trafić do gotowego PNG. Dlatego otwieraj tylko zlecenia, którym ufasz (własne albo od zaufanej osoby).
- Plugin sprawdza też, że fonty i logo z biblii marki leżą w folderze marki, a foldery `final/`
  i `drafts/` zlecenia nie wskazują poza zlecenie.
- `update-check` nie przyjmuje już adresu ani pliku w argumentach: sprawdza tylko oficjalny adres
  pluginu i zapisuje wynik w pliku `update.json` w folderze ustawień (zmienna `GD_UPDATE_SOURCE`
  jest tylko do testów).

Każde inne polecenie dalej działa według zwykłych zasad i pyta o zgodę. Reguły muszą się zgadzać
co do litery, dlatego asystent używa pełnej ścieżki pliku startowego.

**Dwie inne możliwości.** Pod polem wiadomości w aplikacji jest wybór trybu uprawnień (m.in.
„Approve for me” i „Full access”; nazwy mogą się różnić w Twojej wersji aplikacji). To działa od
ręki, ale uprawnienia są wtedy szersze w całej rozmowie, nie tylko dla pluginu. Albo nic nie
konfiguruj i zgadzaj się jednorazowo za każdym razem. Plugin nie może zmienić tych ustawień
aplikacji za Ciebie.

**Po zapisaniu reguł** zamknij aplikację całkiem, otwórz ją ponownie i zacznij nową rozmowę. Codex
czyta reguły tylko przy starcie. Poproś „Sprawdź konfigurację graphic-designer” (to polecenie
`doctor`), żeby zobaczyć, co działa i co zostało do zrobienia.

**Jak cofnąć**

1. Poproś asystenta: „Usuń reguły graphic-designer”. Uruchomi `setup-rules --remove`, które usuwa
   tylko oznaczony blok. Albo wykonaj to samo w Terminalu:
   `python3 ~/.codex/graphic-designer/designer.py setup-rules --remove`.
2. Możesz też otworzyć `~/.codex/rules/default.rules` i skasować linie od `# >>> graphic-designer`
   do `# <<< graphic-designer <<<` (włącznie), nic poza nimi. Kopię
   `default.rules.graphic-designer.bak` możesz zostawić albo skasować.
3. Zamknij aplikację i otwórz ją ponownie. Plik startowy możesz zostawić (nic nie robi sam z siebie)
   albo usunąć: to tylko `~/.codex/graphic-designer/designer.py`. Folder `~/.graphic-designer`
   zawiera Twoje ustawienia, więc go nie kasuj.

## Telefon

Nie wiadomo jeszcze, czy plugin działa w aplikacji ChatGPT na telefonie. Nie sprawdzaliśmy tego,
więc na razie nie obiecujemy. Gdy to zbadamy, zapiszemy wynik tutaj.

## Aktualizacje

Plugin raz dziennie sprawdza (`update-check`), czy jest nowsza wersja, i mówi, co się zmieniło.
Ręcznie: `codex plugin marketplace upgrade guc-net`, potem nowa rozmowa. Historię zmian
czytasz w `plugins/graphic-designer/CHANGELOG.md`.
