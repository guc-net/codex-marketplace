---
name: komiks-odcinek
description: Faza odcinków komiksu w produkcji — scenariusz z dialogami, generowanie plansz z obrazami referencyjnymi z biblii, kolejne wersje (v1, v2…), wybór finału i odświeżenie strony HTML. Używaj, gdy ktoś chce nowy odcinek albo poprawić plansze odcinka.
---

# Faza odcinków

Skrypt KOMIKS i zasady rozmowy — jak w skillu `komiks`. Biblii tu **nie zmieniasz**.

## Przebieg

1. **Pomysł** — użytkownik opisuje temat. `KOMIKS odcinek-nowy --komiks <folder>
   --tytul "Tytuł" --opis "pomysł jednym zdaniem"`.
2. **Scenariusz** — przeczytaj `biblia/` (ton, kadry, dymki, postaci, miejsca) i napisz
   scenariusz do `odcinki/NNN-…/scenariusz.md`: plansze → kadry → miejsce, kto co robi,
   **dialog dosłownie**. Pokaż go w czacie jako tekst i zapytaj, co zmienić w słowach.
   Krótkie kwestie (zasady z `dymki.md`). Poprawki tekstu nanosisz w scenariuszu.
3. **Generowanie** — dla każdej planszy jeden obraz w proporcjach `format`, na wejściu:
   wzór stylu (`biblia/styl/`), arkusze występujących postaci, potrzebne pozy, obraz
   miejsca. W prompcie: który obraz jest czym, opis kadrów, dialog do dymków
   **dosłownie, z polskimi znakami**. Zapis:
   `KOMIKS odcinek-wersja <nr> --komiks <folder> --najnowsze <liczba plansz>
   --prompt-plik <plik z promptem> --referencja <ścieżka> --referencja <ścieżka>`
   (albo `--plik` dla każdej planszy po kolei). Prompt zapisz wcześniej do pliku
   tymczasowego w odcinku i podaj przez `--prompt-plik`.
4. **Ocena** — pokaż wynik. Poprawka („w kadrze 3 ma się uśmiechać”, „literówka
   w dymku”) = nowa generacja (edycja z poprzednią wersją na wejściu) → nowa wersja
   `v2`, `v3`… Poprzednich nie kasujesz.
   - Jeśli poprawka dotyczy **stałego wyglądu lub zasad** („niech zawsze nosi
     okulary”), zapytaj: „Tylko w tym kadrze czy na stałe?”. Domyślnie tylko kadr.
     „Na stałe” → skill `komiks-zmiana`.
   - Jeśli literówki w dymkach powtarzają się, powiedz, że zapiszemy to jako pytanie
     o tryb dymków nakładanych (na razie nieobsługiwany).
5. **Final** — „ta jest dobra” → `KOMIKS odcinek-final <nr> v<N> --komiks <folder>`,
   potem `KOMIKS strona --komiks <folder>` i `KOMIKS sprawdz --komiks <folder>`.
   Podaj ścieżki do gotowych plików w `final/` (do wrzucenia na Instagram) i do
   `strona/index.html`.

## Pilnuj

- Odcinek zapisuje, w której wersji biblii powstał — nie zmieniaj tego ręcznie.
- Jeśli `sprawdz` zgłasza zmianę biblii bez zatwierdzenia — zatrzymaj się i powiedz.
- Przed serią generacji powiedz, ile obrazów zrobisz (limit planu).
