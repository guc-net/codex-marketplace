# Propozycje stylów na start

Na początku pokaż **4–6 zupełnie różnych stylów**, a nie warianty jednego. Wszystkie
próbki to **ta sama scena** z tymi samymi postaciami i tym samym kadrem — wtedy
widać różnicę stylu, a nie treści.

## Scena-próbka

Jedna plansza, jeden kadr, format z `komiks.yaml`: główna postać komiksu w jego
typowym miejscu, w środku krótkiej rozmowy, z jednym dymkiem (3–5 słów po polsku).
Jeśli postaci jeszcze nie ma — użyj opisu z odpowiedzi na pytanie 9.

## Katalog (wybierz 4–6, zawsze z różnych grup)

| Nazwa | Grupa | Jednym zdaniem dla użytkownika | Do promptu |
|---|---|---|---|
| ligne claire | czysta linia | jak „Tintin”: równy czarny kontur, płaskie kolory, jasno i czytelnie | clean uniform black outlines, flat colors, no hatching, even lighting |
| manga | czysta linia | czarno-biała albo z jednym kolorem, wyraziste miny, linie ruchu | manga style, screentone shading, expressive eyes, speed lines |
| flat vector | grafika | jak ilustracje z aplikacji: proste kształty, bez konturu, pastelowe plamy | flat vector graphic, only solid flat color shapes, no outlines, no texture, no shading, 5-color palette; not a painted illustration |
| akwarela | malarska | miękkie plamy koloru, papier widać spod farby, ciepło i bajkowo | watercolor illustration, soft washes, visible paper texture, loose pencil lines |
| gwasz / książka dla dzieci | malarska | kryjąca farba, zaokrąglone postaci, mocne kolory | gouache picture-book illustration, opaque paint, rounded shapes |
| noir / tusz | kontrast | czarny tusz, mocne cienie, mało koloru, poważniej | high-contrast black ink, heavy shadows, spot color only |
| retro komiks lat 50 | druk | kropki rastra, żółtawy papier, kolory jak z gazety | 1950s comic print, halftone dots, off-register colors, aged paper |
| linoryt | druk | grube cięte linie, 2–3 kolory, jak odbitka | linocut print, bold carved lines, 2–3 ink colors, paper grain |
| kredka / szkicownik | ręczna | jak z notesu, kreska ołówka i kredki, bardzo „nie-AI” | colored pencil sketchbook, visible strokes, imperfect lines, cream paper |
| 3D plastelina | przestrzenna | figurki jak z plasteliny, ciepłe światło | claymation look, plasticine figures, soft studio light |

Domyślny zestaw, gdy użytkownik nie ma preferencji: **ligne claire, akwarela,
flat vector, retro komiks lat 50, linoryt** (5 próbek). Gdy zależy mu, żeby było
„mniej AI-owe”, dołóż kredkę / szkicownik zamiast flat vector.

**Uwaga:** model ciąga wszystkie próbki do jednego, „bajkowego” wyglądu — akwarela,
kredka i flat vector potrafią wyjść prawie tak samo. W opisie stylu bądź skrajny
(„tylko płaskie plamy, bez konturu, bez faktury, bez cieniowania, 5 kolorów”) i dopisz,
czym próbka **nie** ma być („nie jak malowana ilustracja książkowa”). Jeśli dwie
próbki wyglądają podobnie, zamień jedną na styl z innej grupy, zanim pokażesz.

## Jak to przeprowadzić

1. Powiedz, ile próbek zrobisz (każda zużywa limit planu) — domyślnie 5.
2. Generuj każdą osobno, tym samym opisem sceny, zmieniając tylko opis stylu. Zapisuj:
   `KOMIKS obraz --do <komiks>/projekt/style/01-ligne-claire.png`, `02-akwarela.png`…
3. Pokaż wszystkie naraz z nazwą i jednym zdaniem. Zapytaj: „Który najbardziej? Możesz
   też połączyć dwa, np. kreskę z pierwszego i kolory z trzeciego”.
4. Mieszanka albo korekta = jedna–dwie nowe próbki z wybranymi próbkami na wejściu.
5. Zwycięzca → `KOMIKS obraz --do <komiks>/biblia/styl/wzor-01.png --plik <próbka>`.
   Najlepiej 2–3 wzory (różne kadry w tym samym stylu): `wzor-02.png`, `wzor-03.png`.
6. Wypełnij `biblia/styl.md`: nazwa i pochodzenie, kreska, **paleta z kodami kolorów**,
   światło, faktura, kadrowanie, liternictwo, **Blok stylu** (2–4 stałe zdania po
   angielsku albo polsku — od teraz idą dosłownie na początek każdego promptu)
   i **Nie rób** (negatywy: odrzucone style, „nie fotorealizm”, „nie plastikowy połysk”,
   „bez gradientów jak z AI”, „bez dodatkowego tekstu poza dymkami”).
7. Odrzucone próbki zostają w `projekt/style/` — przydają się jako „tak nie”.
