---
name: brand-kit
description: Biblia marki — kolory, paleta, fonty, logo, przykłady „tak” i „nie”. Używaj, gdy osoba chce zapisać markę, dodać logo albo font, zmienić kolor, wyjaśnić, czego marka nie robi, albo gdy zlecenie graficzne trzeba zrobić bez gotowej biblii.
---

# Biblia marki — zakładanie i zmiany

Mów po polsku, krótko, bez żargonu. DESIGNER to ścieżka skryptu (jak w procedurze `graphic-designer`).
Przykłady używają zmyślonej marki „Kiwi Studio”.

Biblia marki to folder `brand/`: `brand.md` (kolory, fonty, logo, zakazy, opis marki), `logo/`,
`fonts/`, `examples/approved/`, `examples/rejected/`, `CHANGES.md`. Wszystkie grafiki
w zleceniach biorą z niej kolory, fonty i logo.

## Sprawdzenie, co jest

`DESIGNER brand` (albo `--path <folder>`). `BRAND: …` — jest; `NO BRAND` — nie ma.
Skrypt zbiera wszystkie problemy naraz (zły kolor, brak pliku logo, brak wymaganej roli):
przekaż je osobie jako krótką listę i zaproponuj poprawki. Fonty oznaczone jako jeszcze
niedostarczone to ostrzeżenie, nie błąd.

## Zakładanie nowej biblii (z załączników i rozmowy)

1. Poproś o to, co osoba ma: logo (najlepiej PNG z przezroczystym tłem albo SVG), kolory,
   fonty (pliki `.ttf` albo `.otf`), kilka grafik „tak, takie chcemy” i „nie, takich nie”,
   zdjęcia. Czego nie ma — dopytaj krótko, po jednym pytaniu naraz:
   „Jaki jest główny kolor marki? Ciemne czy jasne tło? Jakie fonty?”
2. `DESIGNER brand-init --name "Kiwi Studio" --dir <folder>` zakłada szkielet `brand/`.
3. Uzupełnij `brand.md` na podstawie załączników: wymagane role kolorów (główny, tło, tekst),
   dodatkowe role, fonty z rolami (nagłówki, tekst, ozdobny), warianty logo z informacją, na
   jakim tle działają, i minimalną szerokością, zakazane pary kolorów z jednozdaniowym powodem.
   Zasady doboru: `../graphic-designer/references/color.md`,
   `../graphic-designer/references/typography.md`, `../graphic-designer/references/logo.md`.
   Skopiuj pliki logo i fontów do `logo/` i `fonts/`.
4. Przykłady do `examples/approved/` i `examples/rejected/`, każdy z **jednym zdaniem**, dlaczego
   dobry albo zły (np. „zbyt dużo tekstu na zdjęciu”). Plik z opisem obok obrazu.
5. `DESIGNER brand` — popraw, aż zgłosi `BRAND`. Pokaż osobie krótkie podsumowanie: kolory,
   fonty, logo, zakazy, i zapytaj, czy się zgadza.

## Zmiana istniejącej biblii — tylko za wyraźnym „tak”

Biblia wpływa na wszystkie przyszłe grafiki, więc **żadna zmiana nie wchodzi bez wyraźnego „tak”**.
Brak odpowiedzi, „może”, „chyba”, „zobaczymy”, zmiana tematu = nie zatwierdzono.

1. Upewnij się, że to zmiana stała, a nie wyjątek w jednym zleceniu („Tylko do tego plakatu
   czy od teraz zawsze?”). Wyjątek robisz w zleceniu, biblii nie ruszasz.
2. Powiedz, co dokładnie się zmieni (stara i nowa wartość) i na co wpłynie, i zapytaj wprost:
   „Zapisać tę zmianę w biblii marki?”
3. Po wyraźnym „tak”: edytuj `brand.md` (i pliki w `logo/`, `fonts/`), potem
   `DESIGNER brand-log --change "Kolor akcentu z #FF8A00 na #F5A300" --approved-by "<imię osoby>"`.
   To podbija wersję i dopisuje wpis do `CHANGES.md`. Na końcu `DESIGNER brand`.
4. Po „nie”: nic nie zmieniaj; zlecenie rób dalej według obecnej biblii.

## Praca bez biblii marki

- Powiedz, że nie znasz marki, i poproś o to, co osoba ma: logo, kolory, fonty, przykłady,
  zdjęcia. Na telefonie lub bez plików osoba dołącza je jako załączniki, a o kolory i fonty
  pytasz krótko (kolor główny, tło, czy są własne fonty).
- Na laptopie załóż biblię w folderze zlecenia: `DESIGNER brand-init --name "<nazwa>" --dir <folder
  zlecenia>`, uzupełnij `brand.md` z załączników (tylko to, co osoba dała), a potem
  `DESIGNER set-brand --job <zlecenie> --brand <folder zlecenia>/brand`. Dzięki temu `brand:` w
  kompozycji, logo i `check` działają tak samo jak z gotową marką.
- Tymczasowa karta marki w `brief.md` (kilka zdań o kolorach, fontach i logo) jest tylko na
  telefon, gdzie nie uruchamiasz skryptu.
- Po zleceniu zapytaj: „Przenieść ten folder `brand/` do repozytorium marki?” Po „tak” — procedura
  zakładania wyżej.
- Bez biblii samoocena pomija punkty marki i mówisz to wprost.

## Zasady

- Nie wymyślaj kolorów, fontów ani logo, których osoba nie dostarczyła. Logo to zawsze plik.
- Nie kasuj poprzednich wersji logo ani fontów — dodaj nowy plik i zmień wskazanie w `brand.md`.
- Biblia leży w repozytorium marki; zapisanie jej tam robisz według `AGENTS.md`, na osobnym
  branchu, z propozycją PR.
