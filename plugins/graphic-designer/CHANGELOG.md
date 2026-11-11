# Co nowego w pluginie „graphic-designer”

Najnowsza wersja na górze. Ten plik czyta plugin, kiedy mówi Ci o aktualizacji —
pisz więc tak, żeby rozumiał to ktoś, kto nie programuje.

## 0.1.1 — 2026-11-11

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
- Wyjaśnione, co jest nieszkodliwe (komunikaty o `CVDisplayLink` i „allocator”, okno „quit unexpectedly”) i że wbudowana przeglądarka aplikacji nie nadaje się do eksportu, bo blokuje adresy `file://`.

## 0.1.0 — 2026-11-11

- Pierwsza wersja pluginu: projektant grafik zgodnych z marką.
- Biblia marki (kolory, fonty, logo) w osobnym folderze; plugin pilnuje, żeby grafika z niej korzystała.
- Zlecenia z kierunkami, wersjami roboczymi i zamrożonymi warstwami; każda wersja zostaje zapisana.
- Składanie grafik w HTML do PNG (a dla druku do PDF ze spadem): Instagram, relacje, okładka wydarzenia, A4 i A3.
- Sprawdzanie przed pokazaniem: rozmiar, fonty, polskie znaki, kontrast, strefy bezpieczne, proporcje i rozmiar logo.
- Pakiety grafik zapisywane w repozytorium projektu.
- Wiedza projektanta po polsku (logo, typografia, kolor, kompozycja, plakat, druk, polecenia do generatora obrazów).
- Raz dziennie plugin sprawdza, czy jest nowa wersja, i mówi, co się zmieniło.
