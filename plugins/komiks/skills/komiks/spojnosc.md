# Reguły spójności grafiki (dla Ciebie, modelu)

Komiks jest spójny, kiedy każdy obraz powstaje z **tych samych obrazów wzorcowych
i tych samych słów**. Opis bez obrazów daje za każdym razem inną postać.

## Zawsze przed generacją

1. Uruchom `KOMIKS prompt-baza --komiks <folder> --postac <imię> [--postac …]
   [--miejsce <miejsce>] [--widok tyl]`. Dostajesz listę obrazów na wejściu w ustalonej
   kolejności i początek promptu.
2. Podaj na wejściu **dokładnie te obrazy, w tej kolejności**, i w prompcie nazwij
   każdy: „Obraz 1 to wzór stylu, obraz 2 to arkusz postaci Oli, obraz 3 to tło kuchni”.
3. Prompt zaczynaj od wydruku `prompt-baza` **bez zmiany słów** (Blok stylu, bloki
   postaci, format, Nie rób). Dopiero potem: co dzieje się w kadrach i dialog.
4. Dobierz widok z arkusza obrotu do kadru: postać odwrócona plecami → `--widok tyl`,
   z boku → `profil-lewy`/`profil-prawy`, z lotu ptaka → `gora` (jeśli jest).
5. Dialog do dymków dosłownie w cudzysłowie, z polskimi znakami; napisz, że poza
   dymkami nie ma żadnego innego tekstu.

## Nie rób

- Nie opisuj postaci w locie innymi słowami („ruda dziewczynka”, gdy w biblii jest
  „Ola, 8 lat, rude warkocze”) — zmienia się wtedy wygląd. Używaj bloku postaci.
- Nie dokładaj stylów („w stylu Pixara”, „bardziej filmowo”), których nie ma w `styl.md`.
- Nie pisz długich promptów: Blok stylu + bloki postaci + 1–3 zdania na kadr + dialog.
  Każdy dodatkowy przymiotnik to okazja do odjazdu.
- Nie generuj od zera, kiedy poprawiasz. Poprawka = **edycja** poprzedniej wersji
  (obraz na wejściu) z opisem: „zmień tylko X, wszystko inne zostaw dokładnie tak samo”.
  Jeśli się da, zaznacz obszar kadru i opisz zmianę tylko tam.
- Nie zmieniaj kilku rzeczy naraz — jedna poprawka, jedna nowa wersja.
- Nie zmieniaj biblii przy okazji. Stała zmiana wyglądu = skill `komiks-zmiana`.

## Gdy postać „odjeżdża”

1. Porównaj wynik z arkuszem i widokami (proporcje, kolory z kodami, znaki szczególne).
2. Edytuj kadr z arkuszem na wejściu: „popraw postać, żeby wyglądała jak na obrazie 2:
   …”. Zwykle wystarcza jedna edycja.
3. Jeśli odjeżdża stale w jednym ujęciu (np. z tyłu) — brakuje widoku. W projekcie
   dorób go; w produkcji zaproponuj wniosek o zmianę biblii z nowym widokiem.

## Arkusz obrotu postaci

Każda postać ma w `biblia/postaci/<imię>/`:

- `arkusz.png` — wszystkie widoki obok siebie na jednym obrazie, pełna sylwetka,
  ta sama skala, neutralne jasne tło, bez cienia rzucanego;
- `widoki/przod.png`, `tyl.png`, `profil-lewy.png`, `profil-prawy.png`,
  `trzy-czwarte.png` — obowiązkowo; `gora.png`, `dol.png` — gdy `widoki_dodatkowe`
  w `komiks.yaml` ich wymaga (skrypt nie zamrozi biblii bez kompletu);
- `mimika.png` — 6 min na jednym obrazie; `pozy/` — 3–6 typowych póz z opisem `.md`;
- `postac.md` — proporcje (np. „4 głowy wzrostu”), **paleta z kodami kolorów**,
  znaki szczególne, ubiór, charakter, Blok postaci.

Kolejność: najpierw `arkusz.png` (z wzorem stylu na wejściu; dla postaci-autora także
ze zdjęciami), potem każdy widok osobno z arkuszem i wzorem stylu na wejściu: „Pokaż
tę samą postać z obrazu 2, widok z tyłu, pełna sylwetka, ta sama skala i kolory”.
Lewy i prawy profil generuj osobno — lustrzane odbicie zamienia stronę przedziałka,
torby czy znaku szczególnego.
