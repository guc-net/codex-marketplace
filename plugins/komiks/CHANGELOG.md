# Co nowego w pluginie „komiks”

Najnowsza wersja na górze. Ten plik czyta plugin, kiedy mówi Ci o aktualizacji —
pisz więc tak, żeby rozumiał to ktoś, kto nie programuje.

## 0.3.0 — 2026-10-16

- Biblioteka komiksów: jeden stały folder na wszystkie komiksy (np. `Dokumenty/Komiksy`).
  Plugin pyta o niego raz i pamięta go w każdej nowej rozmowie — nowe komiksy powstają
  tam, a „na jakim etapie są moje komiksy” pokazuje wszystkie serie. Koniec komiksów
  zgubionych w przypadkowych folderach. Jeden komiks można zrobić gdzie indziej,
  bez zmiany ustawienia.
- Gotowe materiały w jednym miejscu: po wybraniu finału plugin mówi wprost, gdzie są
  pliki do publikacji — pełna ścieżka, seria i numer odcinka, liczba slajdów, rozmiar
  i kolejność, z napisem „zatwierdzone, gotowe do publikacji”. Pliki leżą w komiksie,
  w folderze `gotowe/`. Inny final podmienia je tam, a wcześniejsze wersje nie giną.
- Twoje komiksy z wersji 0.2 działają dalej; bez ustawionej biblioteki plugin pracuje
  w bieżącym folderze jak dotąd.

## 0.2.1 — 2026-10-16

- Pliki na Instagram w dokładnym rozmiarze: po wybraniu finału plugin sam robi folder
  `instagram/` z planszami 1080×1350 (albo 1080×1080) — docina od środka i skaluje.
  Powie, jeśli coś trzeba było uciąć, żebyś sprawdził dymki przy brzegach.
- Jakość zawsze pełna: postaci, style i finały nigdy w obniżonej jakości. Szybki szkic
  ołówkiem robi się tylko wtedy, gdy o niego poprosisz.
- Ściąga o planach odpowiada, czy da się wybrać rozmiar i jakość obrazu (w Codexie nie)
  i czy jakość zmienia czas generowania.

## 0.2.0 — 2026-10-16

- Nowy komiks zaczyna się od krótkiej listy pytań — po jednym, każde z gotową
  odpowiedzią. Mniej ważne pytania przychodzą później, kiedy są potrzebne.
- Na start 4–6 zupełnie różnych stylów: to samo ujęcie w każdym, żeby łatwo porównać.
  Można wybrać jeden albo połączyć dwa.
- Postaci z każdej strony: przód, tył, lewy i prawy profil, 3/4, a na życzenie także
  z góry i z dołu. Biblia nie zamknie się bez kompletu.
- Spójność grafiki: stały opis stylu, stałe kolory z kodami i lista „czego nie robić”
  idą do każdego obrazu, razem z obrazami postaci we właściwej kolejności.
- Odcinek krok po kroku: scenariusz, opis kadrów, szybki szkic, plansza, poprawki
  jako edycja, final i pliki na Instagram. Przed rysowaniem plugin mówi, ile obrazów
  to zajmie.
- Nowe ściągi: jak dbać o spójność i co daje który plan ChatGPT.
- Twoje komiksy z wersji 0.1 działają dalej bez zmian.

## 0.1.0 — 2026-10-15

Pierwsza wersja.

- Projekt komiksu krok po kroku: temat, styl (próbki do wyboru), postaci z arkuszami,
  mimiką i pozami, stałe miejsca, kadry i dymki, plansza próbna.
- Biblia komiksu z wersjami: po starcie odcinków każda zmiana stylu czy postaci wymaga
  Twojego „TAK”, a dziennik zmian pamięta, kiedy i co zatwierdziłeś albo odrzuciłeś.
- Odcinki: scenariusz z dialogami, plansze generowane z obrazami postaci i stylu
  na wejściu, każda poprawka jako nowa wersja (nic nie ginie), wybór finału.
- Strona komiksu w HTML: spis odcinków, strony z przyciskami i strzałkami, dziennik
  zmian. Otwiera się dwuklikiem, bez internetu.
- Na początku rozmowy plugin sprawdza (raz dziennie), czy jest nowsza wersja, i pyta,
  czy zaktualizować.
