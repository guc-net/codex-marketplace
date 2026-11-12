---
name: setup
description: Skonfiguruj graphic-designer — pierwsze uruchomienie po instalacji, konfiguracja i ustawienia pluginu. Używaj, gdy osoba mówi „skonfiguruj”, „ustaw”, „pierwsze uruchomienie”, „reguły”, „uprawnienia”, „doctor”, gdy Codex pyta o zgodę przy każdym składaniu grafiki albo gdy przeglądarka Chrome wywraca się w piaskownicy na macOS. Prowadzi krok po kroku, pyta o zgodę przed każdym zapisem i niczego nie zmienia po cichu.
---

# Konfiguracja pluginu — jednorazowo, krok po kroku

Rozmawiasz z osobą, która nie jest programistką. Mów po polsku, krótko, bez żargonu (nie mów
„skrypt”, „reguła prefiksowa”, „piaskownica” bez wyjaśnienia). Polecenia uruchamiasz sam;
osoba ich nie wpisuje. Cel: żeby Codex nie pytał o zgodę przy każdym składaniu grafiki, a przy
tym nie dostał więcej uprawnień, niż trzeba.

DESIGNER to pełna ścieżka skryptu `designer.py` (jak w procedurze `graphic-designer`):
`<ten folder>/../../scripts/designer.py`, z `python3` na macOS i Linuksie albo `py -3` na Windows.
Gdy stały skrypt startowy już jest, używaj jego ścieżki dokładnie w takiej formie, jaką wypisuje
`doctor` w linii „Polecenie do uruchamiania”.

## Zasady, które obowiązują w całej procedurze

- **Nigdy nie zapisujesz reguł bez wyraźnej zgody.** Zgoda to jasne „tak” na pytanie
  „Czy dopisać te reguły?”. „Może”, „chyba” albo brak odpowiedzi to „nie”. To samo dotyczy pliku
  startowego: najpierw pytasz, potem zapisujesz.
- **Nie zmieniasz niczego innego w ustawieniach Codexa.** Nie edytujesz `config.toml` ani
  cudzych plików z regułami. Reguły pluginu to jeden oznaczony blok, który skrypt dopisuje
  na końcu pliku reguł (przy aktualizacji zastępuje go w całości, więc ręczne zmiany w środku bloku
  znikają); reszty pliku nie ruszasz i nie przepisujesz.
- **Nie umiem zmienić ustawień aplikacji** (tryb uprawnień, ustawienia przeglądarki). Mówisz
  osobie, gdzie kliknąć, i czekasz, aż to zrobi.
- Nie przechodzisz po cichu na inne narzędzie do składania grafiki, gdy coś nie działa.

## Krok 1. Sprawdź, co już działa

Uruchom `DESIGNER doctor`. Niczego nie zmienia i zawsze kończy się bez błędu. Każda linia zaczyna się
od `OK:` (jest dobrze), `TODO:` (do zrobienia; po „Następny krok:” stoi, co zrobić) albo
`INFO:` (do wiadomości). Opowiedz wynik krótko, po jednym zdaniu na rzecz: Python, przeglądarka,
biblioteka zleceń, stały skrypt startowy, reguły. Pomiń szczegóły techniczne (np. wynik
`execpolicy`). Gdy nie ma żadnego `TODO:`, powiedz „Wszystko skonfigurowane” i zakończ.

## Krok 2. Dlaczego przeglądarka potrzebuje wyjątku (macOS w Codexie)

Ten krok tylko wtedy, gdy `doctor` pokazuje `TODO:` przy stałym skrypcie albo regułach, albo
`CODEX_SANDBOX=seatbelt`. Wyjaśnij własnymi słowami, w trzech zdaniach:

- Plugin składa grafikę w przeglądarce Chrome.
- Codex uruchamia polecenia w zamkniętej piaskownicy, a w niej macOS nie pozwala Chrome połączyć
  się z usługami systemu (okna, uruchamianie programów), więc Chrome się wywraca — sprawdziliśmy to
  11.11.2026 i żadne ustawienie przeglądarki tego nie naprawia.
- Dlatego Chrome musi działać poza piaskownicą; pytanie tylko, jak to zezwolić.

Przedstaw **trzy możliwości** i zarekomenduj pierwszą:

1. **Reguły tylko dla pięciu poleceń pluginu — zalecane, ale z zastrzeżeniami.** Do pliku reguł
   Codexa trafia krótki blok, który pozwala uruchamiać poza piaskownicą bez pytania pięć poleceń
   tego pluginu (`env`, `render`, `check`, `update-check`, `doctor`), tylko przez jeden plik
   startowy. Powiedz wprost, na czym polegają zastrzeżenia: reguła sprawdza tylko początek
   polecenia, więc to, co jest po nim (np. które zlecenie złożyć), nie jest ograniczone. Chrome
   składa wtedy stronę ze zlecenia bez piaskownicy. Plugin zamyka tę stronę zasadą
   bezpieczeństwa przeglądarki (bez skryptów, bez sieci, bez ramek), ale strona nadal może
   pokazać na składanym obrazie dowolny plik graficzny z dysku. Dlatego otwieraj tylko zlecenia,
   którym ufasz. Cała reszta zostaje jak była. Cofnięcie jest proste.
2. **Szerszy tryb w aplikacji.** Pod polem wiadomości jest wybór trybu uprawnień (m.in. „Approve
   for me” i „Full access” według stanu z 11.11.2026; nazwy mogą się różnić w Twojej wersji
   aplikacji). To działa od ręki,
   ale uprawnienia są szersze **w całej rozmowie, nie tylko dla pluginu**: więcej poleceń, także
   niezwiązanych z grafiką, wykona się bez Twojej zgody albo bez ograniczeń piaskownicy. Powiedz to
   wprost, jako kompromis: wygoda kosztem kontroli. Tego ustawienia zmienić za osobę nie mogę.
3. **Zgoda za każdym razem.** Nic się nie zapisuje. Przy każdym składaniu i sprawdzaniu pojawi się
   okno zgody. Dobre, gdy grafiki robi się rzadko.

Zapytaj, którą wybiera. Bez odpowiedzi nie zakładaj, że wybrała pierwszą.

## Krok 3a. Wybór 1: reguły tylko dla pięciu poleceń

1. **Stały skrypt startowy.** Najpierw zapytaj: „Zapiszę mały plik startowy w folderze Codexa
   (`~/.codex/graphic-designer/`), żeby jego ścieżka nie zmieniała się przy aktualizacjach
   pluginu. Czy mogę?” Dopiero po „tak” uruchom `DESIGNER setup-launcher`. Może być potrzebna
   jeszcze zgoda w oknie aplikacji, bo to folder poza projektem. Z wyniku zapamiętaj pełną
   ścieżkę (`LAUNCHER:`); od teraz to jest DESIGNER. Jeśli wynik mówi, że usunął dawny plik z
   `~/.graphic-designer/designer.py` albo że reguły nadal ufają dawnemu plikowi, wykonaj też
   kroki 2–5: reguły trzeba przepisać na nową ścieżkę.
2. **Pokaż, co zostanie zapisane.** Uruchom `DESIGNER setup-rules` (bez dodatkowych opcji; niczego
   nie zapisuje) i pokaż osobie **dokładny tekst bloku** z wyniku, w bloku kodu, razem ze ścieżką
   pliku. Wyjaśnij zwykłymi słowami: pięć poleceń tego pluginu, z tego jednego pliku, będzie się
   uruchamiać poza piaskownicą bez pytania; Chrome dostaje wtedy stronę z jej zlecenia i nie ma
   ograniczeń piaskownicy, a strona ze zlecenia nie może uruchamiać skryptów ani łączyć się z siecią.
   Blok dopisuje się na końcu, reszta pliku zostaje bez zmian, a przed pierwszą zmianą istniejącego
   pliku powstaje jednorazowa kopia `default.rules.graphic-designer.bak`. Powiedz też, że to
   nie jest ograniczenie dostępu do plików: strona ze zlecenia może pokazać na obrazie dowolny
   plik graficzny z dysku, więc otwierać trzeba tylko zlecenia, którym ufasz.
3. **Zapytaj o zgodę, dokładnie tak:** „Czy dopisać te reguły?” i poczekaj na odpowiedź.
4. **Dopiero po wyraźnym „tak”** uruchom `DESIGNER setup-rules --apply`. Folder Codexa leży poza
   projektem, więc potrzebna będzie jedna zgoda w oknie aplikacji. Jeśli skrypt nie może zapisać
   pliku, nie kombinuj: podaj osobie **dokładne polecenie do Terminala** z komunikatu błędu
   (zaczyna się od `python3`), powiedz, że Terminal otworzy wpisując jego nazwę w Spotlight, i że
   wystarczy je wkleić i nacisnąć Enter.
5. **Sprawdź:** uruchom `DESIGNER doctor`. Linia o regułach ma być `OK:`. Jeśli jest `TODO:`,
   przeczytaj mu następny krok i popraw.
6. **Restart.** Powiedz: „Codex czyta reguły tylko przy starcie. Zamknij aplikację całkiem,
   otwórz ją ponownie i zacznij nową rozmowę — wtedy składanie grafik przestanie pytać o zgodę.”
   (W wierszu poleceń: wyjdź i uruchom Codex jeszcze raz.)
7. **Cofnięcie.** Powiedz, że w każdej chwili można to odwrócić: poproś „Usuń reguły
   graphic-designer” — uruchomisz `DESIGNER setup-rules --remove`, który usuwa tylko ten oznaczony
   blok (kopia `default.rules.graphic-designer.bak` zostaje, możesz ją skasować) — albo skasować blok ręcznie (od linii `# >>> graphic-designer` do `# <<< graphic-designer <<<`);
   po zmianie znów trzeba uruchomić Codex ponownie.

## Krok 3b. Wybór 2 albo 3

- **Wybór 2:** powiedz, gdzie kliknąć (selektor trybu pod polem wiadomości), i że po zmianie
  warto zacząć nową rozmowę. Sprawdź `DESIGNER doctor`: przy działającym trybie próbny start
  przeglądarki ma być `OK:`. Niczego nie zapisujesz.
- **Wybór 3:** niczego nie zapisuj. Powiedz, że okno zgody będzie się pojawiać przy `render`,
  `check` i `env`, i że w każdej chwili można napisać „Skonfiguruj graphic-designer”, żeby to zmienić.

## Krok 4. Pozostałe ustawienia (w tej samej rozmowie)

- **Folder na zlecenia.** Gdy `doctor` pokazuje `TODO:` przy bibliotece zleceń, zapytaj, gdzie
  trzymać grafiki, z gotową odpowiedzią `~/Documents/Graphics-work` (Windows:
  `Documents\Graphics-work`). Po odpowiedzi uruchom `DESIGNER library --set <folder>`.
- **Model.** Zalecany jest `gpt-6.1-sol` na poziomie Medium. W aplikacji wybierasz go pod polem
  wiadomości, w wierszu poleceń poleceniem `/model`. To osoba ustawia sama.
- **Sprawdzanie aktualizacji (opcjonalnie).** `DESIGNER update-check` potrzebuje sieci. Po
  konfiguracji z regułami z kroku 3a działa poza piaskownicą, więc sieć ma. Bez reguł plugin raz
  poprosi o zgodę na sieć. Osoba może to też pominąć.
- Jeśli `doctor` zgłosił `OPENAI_API_KEY`, powiedz jednym zdaniem, że obrazy będą wtedy liczone
  według cennika API, a nie z abonamentu.

## Czego ta procedura nie robi

- Nie zmienia ustawień aplikacji Codex: trybu uprawnień (selektor pod polem wiadomości) ani
  ustawień przeglądarki. Według naszych prób z 11.11.2026 Ustawienia → Browser dotyczą tylko
  podglądu stron w aplikacji, jeśli osoba go chce (nazwy i działanie mogą się różnić w jej wersji).
  Do eksportu grafiki wbudowana przeglądarka nie służy: w naszych próbach blokowała adresy
  `file://` i zapisywała tylko JPEG.
- Nie dotyka niczego w konfiguracji Codexa poza oznaczonym blokiem reguł i plikiem startowym w
  `~/.codex/graphic-designer/`, i to tylko za zgodą.
- Na Windows i Linuksie zwykle nic z tego nie jest potrzebne; `doctor` pokaże, jeśli jest inaczej.

## Na koniec

Podsumuj w trzech zdaniach: co zostało ustawione, co osoba musi jeszcze zrobić sama (restart
aplikacji, nowa rozmowa, ewentualnie wybór trybu albo modelu) i jak to cofnąć. Potem zapytaj, jaką
grafikę chce zrobić — dalej prowadzi procedura **graphic-designer**.
