# Co nowego w pluginie „graphic-designer”

Najnowsza wersja na górze. Ten plik czyta plugin, kiedy mówi Ci o aktualizacji —
pisz więc tak, żeby rozumiał to ktoś, kto nie programuje.

## 0.3.0 — 2026-11-12

- Nowa procedura „social-content”: treści na Instagram i inne sieci. Dobiera format do celu (post, karuzela, relacja, okładka rolki), układa hasło otwierające i opis posta, a trzy kierunki do wyboru różnią się **sposobem przyciągnięcia uwagi** (duże hasło, człowiek w akcji, zbliżenie na fakturę, niespodzianka w kadrze, pytanie, liczba, seria), nie samym kolorem. Przed pokazem asystent robi „test przewijania” na pomniejszonym podglądzie.
- Dwa nowe pliki wiedzy: `social.md` (jak zatrzymać przewijanie, wzory haseł, karuzela, relacja, seria) i `copy-pl.md` (polszczyzna w hasłach i opisach, szkielet opisu posta, uczciwość obietnic).
- Karuzela: nowe formaty `ig-carousel-1` … `ig-carousel-10` (każdy slajd to osobna kompozycja 1080×1350 px, ze sprawdzaniem jak przy poście). Brief ma sekcję o mediach (hasło, opis posta, liczba slajdów).
- Naprawa po teście 12.11.2026: wprowadzenie „Jak pracujemy” pokazywało się jako dwa gęste akapity, bo pozycje były sklejone w jednej linii. Teraz to lista numerowana, a procedura wymaga takiego układu w każdej odpowiedzi (listy w osobnych liniach, pusta linia przed i po).
- Odpowiedź z gotową grafiką ma zawsze cztery części: plik, wynik kontroli, samoocena, lista „do sprawdzenia przez człowieka” (wcześniej asystent potrafił podać tylko link do pliku).
- Gdy styl „nie pasuje” osobie, asystent najpierw szuka rozwiązania w obrębie marki, a użycie fontu albo koloru spoza biblii zgłasza wprost i czeka na „tak” (kontrola automatyczna tego nie wyłapuje).

## 0.2.0 — 2026-11-12

- Konfiguracja na początek: nowa procedura „setup” prowadzi krok po kroku (aplikacja Codex może ją zaproponować tuż po instalacji; inaczej napisz „Skonfiguruj graphic-designer”). Sprawdza, co działa, i mówi, co jest do zrobienia.
- Na Macu Chrome nie startuje w piaskownicy Codexa: system macOS nie pozwala mu tam połączyć się z usługami okien i uruchamiania programów (sprawdzone 11.11.2026; żaden przełącznik Chrome tego nie naprawia). Konfiguracja proponuje reguły Codexa, które pozwalają uruchamiać poza piaskownicą, bez pytania, pięć poleceń pluginu (`env`, `render`, `check`, `update-check`, `doctor`). Uczciwie: reguła sprawdza tylko początek polecenia, więc nie ogranicza argumentów, a Chrome składa wtedy stronę ze zlecenia bez piaskownicy. Zamyka ją zasada bezpieczeństwa przeglądarki (bez skryptów, sieci i ramek), ale strona nadal może pokazać na obrazie dowolny plik graficzny z dysku, więc otwieraj tylko zlecenia, którym ufasz. Reguły dopisują się tylko za Twoją zgodą, na końcu pliku reguł; przed pierwszą zmianą powstaje jednorazowa kopia `default.rules.graphic-designer.bak`, a cofniesz je jednym poleceniem.
- Nowe polecenia: stały skrypt startowy w folderze Codexa (`~/.codex/graphic-designer/designer.py`, chronionym przed zapisem z piaskownicy; jego ścieżka nie zmienia się przy aktualizacjach pluginu, więc reguły nie przestają działać), dopisywanie i usuwanie reguł oraz sprawdzenie konfiguracji z podpowiedzią następnego kroku. Stały skrypt wybiera tylko wersje z folderu Codexa dla pluginu `graphic-designer` z katalogu `guc-net`, o numerze `X.Y.Z`, z własnym `plugin.json`; wersje próbne i cudze foldery pomija. Ustawienia zostają w `~/.graphic-designer`. Jeśli wcześniejsza wersja zapisała plik startowy tam, `setup-launcher` usuwa go (tylko nasz) i ostrzega, gdy reguły nadal mu ufają.
- Na początku rozmowy na Macu asystent raz proponuje konfigurację, a gdy odmówisz, pracuje dalej i prosi o zgodę przy poleceniach, które jej wymagają.
- Naprawa po pierwszym teście w aplikacji Codex na Macu: przeglądarka, którą plugin składa grafiki, wywracała się w piaskownicy Codexa, a asystent po cichu przechodził na inne narzędzie i pomijał sprawdzanie.
- Gdy przeglądarka się wywróci, plugin mówi wprost, że to zapewne piaskownica, i że trzeba poprosić Cię o jednorazową zgodę na uruchomienie poza nią.
- Polecenie sprawdzające środowisko robi teraz próbny start przeglądarki i pokazuje, czy się udał. Przeglądarka zabita z zewnątrz (np. brak pamięci) nie jest już brana za problem piaskownicy.
- Asystent nie zmienia po cichu biblioteki zleceń i nie zakłada drugiej; o zapis w Twojej bibliotece prosi o zgodę.
- Brak sieci przy sprawdzaniu aktualizacji: asystent pyta raz o zgodę zamiast pomijać.
- Procedura zlecenia ma obowiązkową kolejność: brief, kierunki do wyboru, etapy z zamrożeniem obrazów, składanie, sprawdzenie, samoocena, lista do sprawdzenia przez człowieka. Prośba z samym tematem, formatem i datą nie pomija pytań ani kierunków.
- Nowe polecenie `choose`: zapisuje, który kierunek wybrała osoba (albo że zlecenie nie ma rundy kierunków).
- Skrypt pilnuje procesu: pokazuje etap zlecenia i następny krok, a sprawdzenie zgłasza błąd, gdy brief jest pusty albo nie wybrano kierunku; bez czystego sprawdzenia nie da się zamknąć pakietu. Komunikat o niezamrożonej warstwie mówi teraz, co zrobić.
- Na początku rozmowy o grafice asystent krótko mówi, jak pracujemy (pytania, kierunki, etapy, kontrola, akceptacja).
- Dokumentacja: „Jak zacząć (krok po kroku)” w opisie pluginu i w dokumentacji, z podpowiedzią, jak włączyć plugin przez `@`, jaki model wybrać i co zrobić, gdy asystent pomija kroki.
- Na Macu w piaskownicy Codexa plugin nie uruchamia przeglądarki, bo system pokazywał wtedy okno „Google Chrome quit unexpectedly”; od razu mówi, że trzeba zgody na uruchomienie poza piaskownicą. Po tej zgodzie Chrome działa poprawnie (sprawdzone 11.11.2026).
- Wyjaśnione, co jest nieszkodliwe (komunikaty o `CVDisplayLink` i „allocator”, okno „quit unexpectedly”) i że wbudowana przeglądarka aplikacji nie nadaje się do eksportu: w naszych próbach z 11.11.2026 blokowała adresy `file://` (w Twojej wersji aplikacji może to wyglądać inaczej).
- Bezpieczeństwo składania: strona ze zlecenia dostaje zasadę bezpieczeństwa przeglądarki (bez skryptów, połączeń z siecią, ramek i przekierowań), a Chrome flagi wyłączające rozszerzenia i synchronizację; sprawdzamy to testami z prawdziwą przeglądarką, także z atakami, które bez tej zasady się udają. Fonty i logo z biblii marki muszą leżeć w jej folderze (`.ttf`, `.otf`, `.woff`, `.woff2`); ścieżki bezwzględne, `..` i dowiązania na zewnątrz kończą się błędem. Foldery `final/` i `drafts/` zlecenia nie mogą wskazywać poza zlecenie.
- `update-check` nie przyjmuje już adresu ani pliku w argumentach (`--source`, `--cache`): sprawdza tylko oficjalny adres pluginu, a wynik zapisuje w `update.json` w folderze ustawień. Zmienna `GD_UPDATE_SOURCE` służy tylko testom.
- Zapis reguł jest atomowy (plik tymczasowy, potem podmiana): przy błędzie oryginał zostaje nietknięty. Zachowuje uprawnienia pliku i dowiązania symboliczne oraz końce linii Windows. Stały skrypt nie przyjmuje już zmiennej wskazującej inny folder pluginu.
- Windows: reguły zapisują ścieżki z poprawnym znakiem ucieczki (`\\`), a pliki reguł czytamy i zapisujemy jako bajty, więc system nie zmienia końców linii.

## 0.1.0 — 2026-11-11

- Pierwsza wersja pluginu: projektant grafik zgodnych z marką.
- Biblia marki (kolory, fonty, logo) w osobnym folderze; plugin pilnuje, żeby grafika z niej korzystała.
- Zlecenia z kierunkami, wersjami roboczymi i zamrożonymi warstwami; każda wersja zostaje zapisana.
- Składanie grafik w HTML do PNG (a dla druku do PDF ze spadem): Instagram, relacje, okładka wydarzenia, A4 i A3.
- Sprawdzanie przed pokazaniem: rozmiar, fonty, polskie znaki, kontrast, strefy bezpieczne, proporcje i rozmiar logo.
- Pakiety grafik zapisywane w repozytorium projektu.
- Wiedza projektanta po polsku (logo, typografia, kolor, kompozycja, plakat, druk, polecenia do generatora obrazów).
- Raz dziennie plugin sprawdza, czy jest nowa wersja, i mówi, co się zmieniło.
