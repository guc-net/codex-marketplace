---
name: komiks-zmiana
description: Zmiana biblii komiksu w produkcji (wygląd postaci, styl, kolory, stałe miejsca, zasady kadrów i dymków) — wniosek z różnicami i wpływem, obowiązkowe wyraźne TAK, zatwierdzenie albo odrzucenie z wpisem w dzienniku. Używaj zawsze, gdy prośba zmienia coś na stałe, a nie tylko w jednym kadrze.
---

# Zmiana biblii — tylko za wyraźną zgodą

Biblia wpływa na wszystkie kolejne odcinki. **Żadna zmiana nie wchodzi bez wyraźnego
„TAK” użytkownika.** Brak odpowiedzi, „może”, „chyba”, „zobaczymy”, zmiana tematu =
**nie zatwierdzono**. Skrypt KOMIKS (jak w skillu `komiks`) wymusza tę regułę:
`biblia/` zmienia tylko polecenie `zmiana-zatwierdz`, a `sprawdz` wykrywa każdą inną zmianę.

## Przebieg

1. **Upewnij się**, że to zmiana stała, a nie poprawka jednego kadru
   („Tylko w tym odcinku czy od teraz zawsze?”). Sprawdź w `zmiany/`, czy podobny
   wniosek nie był już odrzucony — jeśli był, powiedz o tym.
2. **Wniosek** — `KOMIKS zmiana-nowa --komiks <folder> --nazwa okulary-ady
   --tytul "Ada nosi okulary" --opis "co się zmienia i dlaczego, słowami"`.
   Skrypt tworzy kopię roboczą biblii w `zmiany/NNNN-…/biblia/`.
3. **Zmiany wprowadzaj tylko w kopii roboczej** (`zmiany/NNNN-…/biblia/…`), nigdy
   w `biblia/`. Nowe obrazy (np. arkusz z okularami) generuj ze starym arkuszem na
   wejściu i zapisuj do kopii: `KOMIKS obraz --do <kopia>/postaci/ada/arkusz.png --nadpisz`.
4. **Pokaż** — `KOMIKS zmiana-pokaz <nr> --komiks <folder>` daje listę plików, różnice
   tekstu i wpływ. Przedstaw to po ludzku:
   - co się zmienia (słowami);
   - które pliki (dla obrazów pokaż stary i nowy obok siebie);
   - **wpływ**: „gotowe odcinki zostają w biblii vN; od następnego obowiązuje vN+1;
     trzeba wygenerować X obrazów”.
   Zakończ dokładnie pytaniem: **„Zatwierdzasz zmianę biblii na wersję N+1? Napisz TAK.”**
5. **Odpowiedź**
   - Zaczyna się od „TAK” → `KOMIKS zmiana-zatwierdz <nr> --komiks <folder>
     --zgoda "<dokładne słowa użytkownika>"`. Powiedz: „Biblia vN+1 zatwierdzona”.
   - Wyraźne „nie” → `KOMIKS zmiana-odrzuc <nr> --komiks <folder> --powod "<słowa>"`.
     Wpis zostaje w dzienniku, żeby nie proponować tego w kółko.
   - Cokolwiek innego → wniosek zostaje otwarty; przypomnij o nim przy następnej
     okazji. Nie zatwierdzaj „domyślnie”.
6. Po zatwierdzeniu uruchom `KOMIKS sprawdz` i `KOMIKS strona` (dziennik zmian na
   stronie się odświeży).
