---
name: komiks-projekt
description: Faza projektu komiksu — pytania startowe, 4–6 zupełnie różnych stylów do wyboru, postaci z arkuszami obrotu (przód, tył, oba profile, 3/4, opcjonalnie góra i dół), miejsca, kadry i dymki aż do planszy próbnej i zamrożenia biblii v1. Używaj, gdy ktoś zaczyna nowy komiks albo komiks ma stan „projekt”.
---

# Faza projektu: budujemy biblię

Skrypt KOMIKS i zasady rozmowy — jak w skillu `komiks`. Reguły generowania obrazów
są w `../komiks/spojnosc.md` — przeczytaj je przed pierwszym obrazem. Idziesz po kolei,
jeden krok naraz. Każdy krok kończy się **zapisem do biblii** i jednym zdaniem:
„Zapisałem: …”. W tej fazie biblię zmieniasz wprost (nic jeszcze od niej nie zależy),
ale zawsze mówisz, co zapisałeś.

Zanim zaczniesz, przeczytaj `komiks.yaml` i istniejące pliki `biblia/` oraz wynik
`KOMIKS stan`, żeby wiedzieć, na którym kroku jesteście — nie zaczynaj od nowa tego,
co już jest.

## Kroki

1. **Pytania na start** — z pliku `pytania.md` (ten folder), po jednym, z domyślną
   odpowiedzią. Potem `KOMIKS nowy --tytul "Tytuł" --format 1080x1350
   --plansze-na-post 1 --kanal instagram --jezyk pl` (komiks trafi do biblioteki —
   skill `komiks`, krok 2; bez biblioteki do bieżącego folderu)
   i zapis celu, odbiorcy i tonu w `biblia/ton.md` (temat, odbiorca, morał, ton,
   czego nie mówimy). Zdjęcia autora-postaci odłóż do `projekt/zdjecia/`, inspiracje
   do `projekt/inspiracje/`.
2. **Style** — wg `style.md` (ten folder): 4–6 zupełnie różnych stylów, ta sama
   scena-próbka, zapis w `projekt/style/`. Wybór (albo mieszanka) → `biblia/styl/wzor-01.png`
   (najlepiej 2–3 wzory) i pełny `biblia/styl.md` z kodami kolorów, Blokiem stylu
   i listą Nie rób.
3. **Postaci** — dla każdej: `KOMIKS postac --imie "Imię" --komiks <folder>`. Zapytaj,
   czy chce też widoków z góry i z dołu; jeśli tak — dopisz w `komiks.yaml`
   `widoki_dodatkowe: "gora,dol"` **przed** dodaniem postaci. Potem `postac.md`
   (proporcje, paleta z kodami, znaki szczególne, ubiór, charakter, Blok postaci),
   a obrazy wg „Arkusz obrotu postaci” w `../komiks/spojnosc.md`:
   `arkusz.png` → `widoki/przod.png`, `tyl.png`, `profil-lewy.png`, `profil-prawy.png`,
   `trzy-czwarte.png` (+ `gora.png`, `dol.png`) → `mimika.png` → 3–6 póz w `pozy/`.
   Zapis: `KOMIKS obraz --do <komiks>/biblia/postaci/<imię>/widoki/tyl.png`.
   Pokaż widoki razem i zapytaj, czy to ta sama osoba ze wszystkich stron. Poprawiaj
   pojedynczy widok edycją, nie cały arkusz od nowa.
4. **Miejsca** — `KOMIKS miejsce --nazwa-miejsca "Kuchnia" --komiks <folder>`, opis
   i obraz tła (z wzorem stylu na wejściu) obok, pod tą samą nazwą `.png`.
5. **Kadry i dymki** → `biblia/kadry.md` (typowe układy, np. 1 plansza = 4 kadry 2×2,
   odległość kamery, wysokość horyzontu) i `biblia/dymki.md` (długość kwestii, kto mówi
   pierwszy, kształt dymków, krój liter). Tryb na start: **tekst w obrazie** — powiedz
   uczciwie, że poprawka tekstu oznacza nową wersję obrazu.
6. **Plansza próbna** — jedna plansza ze wszystkim razem, prompt z `KOMIKS prompt-baza`.
   Jeśli zaakceptowana, zapytaj wprost:
   „Zamrażam biblię jako wersję 1? Od tej chwili każda zmiana stylu czy postaci będzie
   wymagała Twojego TAK. Napisz TAK.” Po odpowiedzi zaczynającej się od TAK:
   `KOMIKS start-produkcji --komiks <folder> --zgoda "<dokładne słowa>"`.
   Skrypt odmówi, jeśli któraś postać nie ma kompletu widoków — wtedy dorób brakujące.
   Plansza próbna może zostać jako `projekt/plansza-probna.png`.

## Ile obrazów to kosztuje

Powiedz to przed krokiem 2 i przed krokiem 3 (każdy obraz zużywa limit planu kilka
razy szybciej niż zwykła wiadomość):

- style: 4–6 próbek + 1–2 mieszanki;
- każda postać: arkusz 1 + widoki 5 (z górą i dołem 7) + mimika 1 + pozy 3–6,
  plus zwykle 2–4 poprawki — razem ok. 12–20;
- miejsce: 1–2; plansza próbna: 1–3.

Komiks z dwiema postaciami i dwoma miejscami to zwykle **35–55 obrazów** na cały
projekt — rozłóż to na kilka dni, jeśli plan ma mały limit.

## Generowanie obrazów

- Zawsze wg `../komiks/spojnosc.md`: obrazy wzorcowe na wejściu, nazwane w prompcie,
  stałe słowa z `prompt-baza`.
- Proporcje obrazu zgodne z `format` z `komiks.yaml`; arkusze i widoki postaci mogą być
  w innych proporcjach (pełna sylwetka, pion).
- Wygenerowany obraz zapisujesz poleceniem `KOMIKS obraz --do <ścieżka>`. Jeśli skrypt
  nie znajdzie obrazu (inna lokalizacja), zapytaj, gdzie jest, albo zapisz go sam
  i podaj `--plik`.
