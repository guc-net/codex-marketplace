# Kolor

## Kontrast tekstu do tła

Liczymy go wzorem WCAG (skrypt `check`, punkt `contrast`). Progi, bez zaokrąglania w górę:

| Tekst | Minimum |
|---|---|
| zwykły | 4,5:1 |
| duży (od ok. 24 px albo od ok. 18,7 px pogrubiony) | 3:1 |
| bardzo wysoki standard (AAA) | 7:1 |

4,499:1 nie przechodzi. Logotypy i tekst czysto dekoracyjny są zwolnione.

Przykłady na ogólnych parach: nasycony fiolet na prawie czarnym tle ma około 2,9:1, więc
nie nadaje się na tekst (nawet duży). Ten sam fiolet jako duża płaszczyzna z białym tekstem
daje około 7:1 i jest bezpieczny. Jasna zieleń na czarnym ma około 15:1, a na białym zaledwie 1,3:1.

## Harmonie

- **Analogiczne:** barwy sąsiednie na kole (30–60°). Spokojne, spójne.
- **Dopełniające:** przeciwległe (180°). Mocne, energiczne.
- **Dopełniające rozszczepione:** barwa i dwie sąsiadki jej dopełnienia. Mocne, ale bezpieczniejsze.
- **Triada:** co 120°. Żywe, trudne do utrzymania.

## Wibracja

Dwie nasycone barwy o podobnej jasności (np. czerwień z nasyconym niebieskim) „drgają” na styku.
Drobny tekst na takim styku męczy oczy. Leczenie: różnica jasności, neutralny pas między nimi
albo takie pary wyłącznie na dużych, dekoracyjnych płaszczyznach.

## Proporcje 60-30-10

Wytyczna, nie prawo: około 60% kolor dominujący (zwykle tło), 30% drugi, 10% jeden akcent
(wezwanie do działania, wyróżnienie). Jeden akcent na pracę.

## Ciemne tło

Nasycone kolory na bardzo ciemnym tle bywają męczące. Jeśli marka je lubi, stosuj je
na duże litery i płaszczyzny, a drobny tekst ciągły składaj bielą albo złamaną bielą.

## Jaśniejsze i ciemniejsze odcienie

Odcienie koloru marki licz w przestrzeni percepcyjnej (OKLCH), nie dodawaniem bieli w RGB.
Ale paleta marki jest zamknięta: nowych kolorów nie dodajesz, tylko pytasz.

## Ekran a druk

Ekran to RGB, druk to CMYK. Neonowe i bardzo nasycone kolory często leżą poza zakresem CMYK.
Drukarnia może zaproponować farbę dodatkową (np. fluorescencyjną), droższą. Zgłoś to przy
każdym projekcie do druku. Zob. `print.md`.

## Co `check` liczy za Ciebie

`contrast` (pary tekst/tło) i `forbidden` (zestawienia kolorów, które biblia marki zakazuje, np. „żółty tekst na białym tle”).
