---
name: komiks-projekt
description: Faza projektu komiksu — prowadzi krok po kroku przez nazwę, temat, styl, postaci (arkusze, mimika, pozy), miejsca, kadry i dymki aż do planszy próbnej i zamrożenia biblii v1. Używaj, gdy ktoś zaczyna nowy komiks albo komiks ma stan „projekt”.
---

# Faza projektu: budujemy biblię

Skrypt KOMIKS i zasady rozmowy — jak w skillu `komiks`. Idziesz po kolei, jeden krok
naraz. Każdy krok kończy się **zapisem do biblii** i jednym zdaniem: „Zapisałem: …”.
W tej fazie biblię zmieniasz wprost (nic jeszcze od niej nie zależy), ale zawsze mówisz,
co zapisałeś.

Zanim zaczniesz, przeczytaj `komiks.yaml` i istniejące pliki `biblia/`, żeby wiedzieć,
na którym kroku jesteście — nie zaczynaj od nowa tego, co już jest.

## Kroki

1. **Nazwa** — zapytaj o tytuł. `KOMIKS nowy --tytul "Tytuł"` (w folderze z komiksami).
   Zapytaj też o format posta (Instagram 4:5 = `1080x1350`, kwadrat = `1080x1080`)
   i czy post to jedna plansza czy karuzela; zapisz w `komiks.yaml`
   (`format`, `plansze_na_post`). Jeśli nie wie — zostaw domyślne i powiedz, że można zmienić.
2. **O czym i dla kogo** → `biblia/ton.md`: temat, odbiorca, morał, ton, czego nie mówimy.
3. **Styl** — zapytaj o przykłady, które mu się podobają (może wkleić obrazy).
   Wygeneruj **3–4 próbki tej samej prostej sceny** w różnych stylach (opisz różnice
   jednym zdaniem każda). Przy wyborze dopytaj o korekty. Zwycięzcę zapisz:
   `KOMIKS obraz --do <komiks>/biblia/styl/wzor-01.png` (bierze ostatnio wygenerowany
   obraz; `--plik` wskazuje konkretny), a opis stylu w `biblia/styl.md`
   (kreska, paleta, światło, faktura, **czego unikać** — np. „nie fotorealizm,
   nie plastikowy połysk, nie typowy wygląd AI”).
4. **Postaci** — dla każdej: `KOMIKS postac --imie "Imię" --komiks <folder>`, potem
   opis w `postac.md`; potem **arkusz referencyjny** (przód / bok / tył, pełna sylwetka,
   neutralne tło) generowany **z wzorem stylu na wejściu** → `arkusz.png`; potem
   `mimika.png` (6 min na jednym obrazie) i 3–6 typowych póz w `pozy/` (obraz + krótki
   `.md`). Każdy następny obraz postaci generuj z jej arkuszem na wejściu.
   Jeśli użytkownik sam ma być postacią, poproś o 1–2 zdjęcia jako referencję.
5. **Miejsca** — `KOMIKS miejsce --nazwa-miejsca "Kuchnia" --komiks <folder>`, opis
   i obraz tła (z wzorem stylu na wejściu) obok, pod tą samą nazwą `.png`.
6. **Kadry i dymki** → `biblia/kadry.md` (typowe układy, np. 1 plansza = 4 kadry 2×2)
   i `biblia/dymki.md` (długość kwestii, kto mówi pierwszy, styl liter). Tryb na start:
   **tekst w obrazie** — powiedz uczciwie, że poprawka tekstu oznacza nową wersję obrazu.
7. **Plansza próbna** — jedna plansza ze wszystkim razem (wzór stylu, arkusze postaci,
   tło na wejściu). Jeśli zaakceptowana, zapytaj wprost:
   „Zamrażam biblię jako wersję 1? Od tej chwili każda zmiana stylu czy postaci będzie
   wymagała Twojego TAK. Napisz TAK.” Po odpowiedzi zaczynającej się od TAK:
   `KOMIKS start-produkcji --komiks <folder> --zgoda "<dokładne słowa>"`.
   Plansza próbna może zostać jako `projekt/plansza-probna.png`.

## Generowanie obrazów

- Zawsze podawaj obrazy referencyjne na wejściu i mów w prompcie, który jest czym
  („obraz 1 to wzór stylu, obraz 2 to arkusz postaci Oli”). Opis bez referencji
  daje inną postać za każdym razem.
- Proporcje obrazu zgodne z `format` z `komiks.yaml`.
- Generacja zużywa limit planu kilka razy szybciej niż zwykła wiadomość — nie generuj
  seriami bez potrzeby; przed większą serią powiedz, ile obrazów zrobisz.
- Wygenerowany obraz zapisujesz poleceniem `KOMIKS obraz --do <ścieżka>`. Jeśli skrypt
  nie znajdzie obrazu (inna lokalizacja), zapytaj, gdzie jest, albo zapisz go sam
  i podaj `--plik`.
