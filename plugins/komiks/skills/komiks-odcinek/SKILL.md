---
name: komiks-odcinek
description: Faza odcinków komiksu w produkcji — pomysł, scenariusz z dialogami i storyboard tekstowy, szybki szkic, plansze generowane z obrazami referencyjnymi z biblii, kolejne wersje (v1, v2…), wybór finału, strona HTML i pliki na Instagram. Używaj, gdy ktoś chce nowy odcinek albo poprawić plansze odcinka.
---

# Faza odcinków

Skrypt KOMIKS i zasady rozmowy — jak w skillu `komiks`; reguły generowania —
`../komiks/spojnosc.md`. Biblii tu **nie zmieniasz**.

Zasada oszczędzania: **słowa poprawiamy w tekście, nie na obrazach**. Obraz
generujesz dopiero, gdy użytkownik zatwierdził scenariusz i storyboard.

## Przebieg (gdzie zatwierdza użytkownik — ✔)

1. **Pomysł** — użytkownik opisuje temat. `KOMIKS odcinek-nowy --komiks <folder>
   --tytul "Tytuł" --opis "pomysł jednym zdaniem"`. (0 obrazów)
2. **Scenariusz** ✔ — przeczytaj `biblia/` (ton, kadry, dymki, postaci, miejsca) i napisz
   `odcinki/NNN-…/scenariusz.md`: plansze → kadry → miejsce, kto co robi, **dialog
   dosłownie**. Pokaż w czacie jako tekst i zapytaj, co zmienić w słowach. Krótkie kwestie
   (zasady z `dymki.md`). Poprawki nanosisz w scenariuszu. (0 obrazów)
3. **Storyboard tekstowy** ✔ — do każdego kadru dopisz w scenariuszu jedną linię
   ujęcia: plan (pełna postać / półzbliżenie / zbliżenie), skąd patrzy kamera, który
   widok postaci z arkusza (przód, tył, profil…), gdzie dymek. Zapytaj, czy tak.
   (0 obrazów)
4. **Szybki szkic** (opcjonalnie, gdy plansza ma 4+ kadry albo trudny układ) — jedna
   generacja całej planszy z dopiskiem „rough sketch, simple pencil lines, low detail,
   no color” i bez dymków; tylko do sprawdzenia układu. Szkic zapisz jako wersję
   (`odcinek-wersja`) — nic nie ginie. (1 obraz na planszę)
5. **Plansza** ✔ — dla każdej planszy jeden obraz w proporcjach `format`. Najpierw
   `KOMIKS prompt-baza --komiks <folder> --postac … --miejsce … [--widok …]`; obrazy
   z jej listy na wejściu w tej kolejności (przy szkicu — dodaj go na końcu jako „układ
   kadrów”), prompt zaczynasz od jej wydruku bez zmian, dalej kadry i dialog **dosłownie,
   z polskimi znakami**. Prompt zapisz do pliku w odcinku i zapisz wynik:
   `KOMIKS odcinek-wersja <nr> --komiks <folder> --najnowsze <liczba plansz>
   --prompt-plik <plik> --referencja <ścieżka> --referencja <ścieżka>`
   (albo `--plik` dla każdej planszy po kolei). (1 obraz na planszę)
6. **Poprawki** ✔ — pokaż wynik. Poprawka („w kadrze 3 ma się uśmiechać”, „literówka
   w dymku”) = **edycja** poprzedniej wersji z nią na wejściu, jedna rzecz naraz →
   nowa wersja `v2`, `v3`… Poprzednich nie kasujesz. (zwykle 1–3 obrazy na planszę)
   - Jeśli poprawka dotyczy **stałego wyglądu lub zasad** („niech zawsze nosi
     okulary”), zapytaj: „Tylko w tym kadrze czy na stałe?”. Domyślnie tylko kadr.
     „Na stałe” → skill `komiks-zmiana`.
   - Jeśli literówki w dymkach powtarzają się, powiedz, że zapiszemy to jako pytanie
     o tryb dymków nakładanych (na razie nieobsługiwany).
7. **Final** ✔ — „ta jest dobra” → `KOMIKS odcinek-final <nr> v<N> --komiks <folder>`,
   potem `KOMIKS strona --komiks <folder>` i `KOMIKS sprawdz --komiks <folder>`.
8. **Na Instagram** — podaj ścieżki plików w `final/` w kolejności karuzeli
   (`plansza-1`, `plansza-2`…) i przypomnij: format `komiks.yaml` to już proporcje
   posta, więc wrzuca bez przycinania. Zaproponuj podpis posta (2–3 zdania + 3–5
   hasztagów) w czacie. Strona: `strona/index.html`.

## Ile to kosztuje

Przed generowaniem powiedz liczbę: odcinek z jedną planszą to zwykle **2–4 obrazy**
(szkic + plansza + 1–2 poprawki), karuzela z 3 planszami — **6–12**. Gdy limit się
kończy: dokończ scenariusze i storyboardy na zapas (tekst nie zużywa limitu obrazów),
generuj po odnowieniu.

## Pilnuj

- Odcinek zapisuje, w której wersji biblii powstał — nie zmieniaj tego ręcznie.
- Jeśli `sprawdz` zgłasza zmianę biblii bez zatwierdzenia — zatrzymaj się i powiedz.
- Jeśli `prompt-baza` zgłasza UWAGA (np. brak Bloku stylu w komiksie z wersji 0.1),
  powiedz o tym raz i zaproponuj uzupełnienie wnioskiem o zmianę biblii.
