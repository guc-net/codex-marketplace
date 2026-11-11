# Samoocena przed pokazaniem: 14 punktów

Przejdź listę przed każdym pokazaniem pracy. Przy każdym punkcie napisz: spełnia / nie spełnia
i jedno zdanie dowodu. Niezaliczone popraw przed pokazaniem; jeśli się nie da, powiedz to wprost.
Punkty oznaczone **[check]** liczy skrypt (`designer.py check`), resztę oceniasz sam, patrząc na
podgląd.

| # | Punkt | Pytanie | Kto |
|---|---|---|---|
| 1 | Zlecenie | Czy praca realizuje „jedną wiadomość” i cel z briefu? | Ty |
| 2 | Hierarchia | Po zmrużeniu oczu widać CO, potem KIEDY? Najwyżej 3 wielkości i 2 duże elementy? | Ty |
| 3 | Jeden mocny element | Jest jeden punkt skupienia? Przechodzi test „usuń jeden dodatek”? | Ty |
| 4 | Kontrast | Tekst ≥ 4,5:1, duży ≥ 3:1 | **[check]** `contrast` |
| 5 | Wibracja i zakazy | Brak zakazanych zestawień kolorów z biblii; brak drobnego tekstu na styku jaskrawych barw | **[check]** `forbidden`, resztę Ty |
| 6 | Paleta | Tylko kolory marki, mniej więcej 60-30-10, jeden akcent | Ty |
| 7 | Typografia | Role krojów zgodne z biblią; fonty wczytane, polskie znaki są w fontach; brak pogrubienia z kursywą | **[check]** `fonts`, `glyphs`; reszta Ty |
| 8 | Tekst dosłowny | Każde słowo zgodne z briefem, polskie znaki poprawne, data i dzień tygodnia się zgadzają | Ty |
| 9 | Logo | Plik z biblii, właściwy wariant, pole ochronne, nie za małe, bez zniekształceń | **[check]** `logo-source`, `logo-distortion`, `logo-min-width`; pole ochronne Ty |
| 10 | Strefy bezpieczne | Nic ważnego w strefach interfejsu i przycięcia | **[check]** `safe-zone` |
| 11 | Marginesy | Nic nie wypada poza format, nic nie nachodzi przypadkiem | Ty (część w `safe-zone`) |
| 12 | Zamrożone warstwy | Zatwierdzone elementy bez zmian względem poprzedniej wersji | **[check]** `layers` |
| 13 | Generyczność | Żaden znak z `generic-ai-tells.md`; co jest tylko tej marki? | Ty |
| 14 | Technika | Wymiary w pikselach zgodne z formatem; dla druku: spad, uwaga o CMYK i kolorach poza zakresem | **[check]** `size`; reszta Ty |

## Jak to zapisać

Krótko, na liście. Przykład:

```
4. Kontrast: spełnia. contrast 12/12 par.
8. Tekst dosłowny: nie spełnia. W briefie „Wieczór z ceramiką”, na grafice „Wieczór z ceramika”. Poprawiam.
```

Nie pokazuj pracy z otwartym punktem 4, 8, 9 ani 10. To są błędy, nie kwestie gustu.

## Czego ta lista nie zastępuje

Zatwierdza człowiek. Lista nie sprawdza prawdziwości dat, adresów ani praw do zdjęć. Te rzeczy
trafiają do listy „do sprawdzenia przez człowieka” na końcu zlecenia.
