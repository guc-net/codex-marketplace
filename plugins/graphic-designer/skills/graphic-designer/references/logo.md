# Logo

Logo to gotowy plik, nie rysunek do powtórzenia. Nie przerysowujesz go, nie odtwarzasz
generatorem obrazów i nie poprawiasz jego liter. Wstawiasz plik z biblii marki.

## Czego szukamy w dobrym logo

- **Stosowne:** pasuje do charakteru marki (studio jogi i sklep z rowerami mają różne logo).
- **Wyróżniające i zapamiętywalne:** da się je narysować z pamięci, na przykład na serwetce.
- **Proste:** działa i duże, i malutkie. Im prostsze, tym mniej wyjątkowe, więc pytanie brzmi:
  jak zapamiętywalne może być, zostając prostym?

Nowe logo zaczynaj od czerni i bieli. Kolor dodajesz na końcu.

## Komplet wariantów

Biblia marki powinna mieć: wersję pełną (znak z napisem), sam znak, wersję jednokolorową
na jasne tło i jednokolorową na ciemne. Format główny to SVG. Brakuje wariantu? Powiedz o tym,
nie zgaduj i nie odbijaj kolorów samodzielnie.

## Zasady użycia

- **Pole ochronne:** wokół logo zostaje pusty margines (zwykle wysokość jednej litery znaku).
  Nic na to pole nie wchodzi: tekst, krawędź, ozdoba.
- **Rozmiar minimalny:** poniżej niego logo przestaje być czytelne. Wartość jest w bibliotece
  marki (`min_width_px`); `check` pilnuje jej w pikselach.
- **Bez zniekształceń:** nie rozciągasz, nie ściskasz, nie pochylasz. Skalujesz tylko
  proporcjonalnie. `check` porównuje proporcje logo na grafice z oryginałem.
- **Bez efektów na samym logo:** cień, poświata i gradient na logo to osobna decyzja marki.
  Poświata może być częścią tła, nie wariantem znaku, chyba że biblia mówi inaczej.
- **Kontrast:** reguły dostępności zwalniają logotypy z wymogu kontrastu, ale to wyjątek prawny,
  nie projektowy. Logo, którego nie widać, nie działa. Wybierz wariant pasujący do tła.

## Przykład (Kiwi Studio)

Plakat z ciemnym tłem dostaje wariant jednokolorowy „na ciemne”, w prawym dolnym rogu, z polem
ochronnym równym wysokości litery „K”. Nie wstawiasz tam wariantu z kolorowym znakiem, jeśli
zlewa się z tłem.

## Co `check` liczy za Ciebie

`logo-source` (logo pochodzi z pliku marki), `logo-distortion` (proporcje), `logo-min-width`
(rozmiar minimalny).
