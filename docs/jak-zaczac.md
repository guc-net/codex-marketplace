# Ściąga: jak zrobić komiks z pluginem „komiks”

Rozmawiasz z Codexem normalnie, po polsku. Pliki porządkuje plugin — nie musisz
ich otwierać, ale możesz (to zwykłe teksty i obrazy).

Dwie inne ściągi: [jak dbać o spójność grafiki](spojnosc.md) i
[co daje który plan ChatGPT](plany.md).

## Biblioteka komiksów (raz na zawsze)

Plugin trzyma wszystkie Twoje komiksy w jednym folderze — **bibliotece**. Za pierwszym
razem zapyta, gdzie ma być (np. `Dokumenty/Komiksy`). Potem pamięta to w każdej nowej
rozmowie, nawet jeśli Codex otworzy inny folder: tam zakłada nowe komiksy i stamtąd
pokazuje stan wszystkich serii.

| Chcesz | Napisz |
|---|---|
| ustawić albo zmienić bibliotekę | „Trzymaj moje komiksy w `/Users/ja/Projects/komiksy`” |
| sprawdzić, gdzie jest | „Gdzie są moje komiksy?” |
| jeden komiks gdzie indziej (bez zmiany ustawienia) | „Ten komiks zrób w `Pulpit/próba`” |

Gotowe pliki każdego odcinka leżą w komiksie, w folderze `gotowe/` — jeden podfolder
na odcinek, zawsze z aktualnym finałem. Jeśli wybierzesz inny final, plugin podmieni
pliki w tym folderze; wcześniejsze wersje nie giną.

## Etap 1: projekt (raz na komiks)

Napisz **„Zacznijmy nowy komiks”**. Codex przeprowadzi Cię po kolei:

1. **Pytania na start** — po jednym, każde z gotową odpowiedzią (napisz „dalej”,
   jeśli pasuje): tytuł, o czym i po co, dla kogo, gdzie publikujesz, jeden obraz
   czy karuzela, pion 4:5 czy kwadrat, ton, język dialogów, postaci, czy Ty jesteś
   postacią (wtedy 1–2 zdjęcia), przykłady stylu, które Ci się podobają.
   Resztę pytań (miny, miejsca, kadry, rytm odcinków) Codex zada później, gdy będą
   potrzebne.
2. **Style** — Codex pokaże **4–6 zupełnie różnych stylów** (np. czysta kreska jak
   w „Tintinie”, akwarela, grafika wektorowa, retro komiks z lat 50., linoryt) — to samo
   ujęcie w każdym, żeby łatwo porównać. Wybierasz jeden albo łączysz dwa
   („kreska z pierwszego, kolory z trzeciego”). Odrzucone zostają jako „tak nie”.
3. **Postaci z każdej strony** — dla każdej postaci arkusz: **przód, tył, lewy profil,
   prawy profil i 3/4**, a jeśli chcesz — także **z góry i z dołu**. Do tego miny
   i typowe pozy, stałe kolory, proporcje i znaki szczególne.
4. **Miejsca** — stałe tła (gabinet, kuchnia…).
5. **Kadry i dymki** — ile kadrów na planszy, jak długie kwestie.
6. **Plansza próbna** — jeśli jest dobra, Codex zapyta, czy **zamrozić biblię**.
   Odpowiedz **TAK**.

## Etap 2: odcinki (ile chcesz)

| Krok | Co robisz | Obrazów |
|---|---|---|
| 1. Pomysł | **„Zróbmy odcinek o tym, że sok to nie owoc”** | 0 |
| 2. Scenariusz | czytasz dialogi i poprawiasz słowa: **„W kadrze 4 niech powie: zjedz, nie pij”** ✔ | 0 |
| 3. Storyboard | Codex opisuje każdy kadr jednym zdaniem (plan, skąd kamera) ✔ | 0 |
| 4. Szkic | tylko jeśli poprosisz: **„najpierw szybki szkic”** — ołówek, sam układ | 1 |
| 5. Plansza | Codex rysuje z obrazami postaci i stylu na wejściu → **wersja 1** ✔ | 1 na planszę |
| 6. Poprawki | **„W kadrze 3 ma się uśmiechać”** → wersja 2, 3… (stare nie giną) ✔ | 1–3 |
| 7. Final | **„Ta jest dobra”** → final, strona komiksu się odświeża ✔ | 0 |
| 8. Gotowe | Codex poda **pełną ścieżkę** folderu z gotowymi plikami (dokładnie 1080×1350), liczbę slajdów, kolejność publikacji i podpis posta | 0 |

✔ = tu decydujesz Ty. **Słowa poprawiaj w kroku 2 i 3** — tekst nic nie kosztuje,
każdy obraz zużywa limit planu.

## Zmiana na stałe (biblia)

**„Niech Pani Miska od teraz nosi okulary”** — Codex zapyta, czy to tylko ten kadr,
czy na stałe. Jeśli na stałe: pokaże, co się zmieni i na które odcinki wpłynie,
i poprosi o **TAK**. Bez „TAK” nic się nie zmienia. Stare odcinki zostają w swojej
wersji biblii; na stronie widać dziennik zmian.

## Przydatne zdania

| Chcesz | Napisz |
|---|---|
| zobaczyć, gdzie jesteś | „Na jakim etapie jest mój komiks?” |
| zobaczyć stronę | „Pokaż stronę komiksu” |
| znaleźć pliki do publikacji | „Gdzie są gotowe pliki odcinka 3?” |
| wrócić do starszej wersji planszy | „Weź wersję 2 jako final” |
| zmienić format posta | „Od teraz kwadrat 1:1” |
| oszczędzić limit | „Najpierw tylko scenariusze na trzy odcinki, bez obrazów” |

**Dobre rady:** zanim poprosisz o serię obrazów, zapytaj, ile ich będzie. Cały projekt
(2 postaci, 2 miejsca) to zwykle 35–55 obrazów — rozłóż go na kilka dni. Krótkie
kwestie w dymkach wychodzą czyściej niż długie zdania.
