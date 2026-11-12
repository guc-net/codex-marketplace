---
name: design-job
description: Zaprojektuj plakat, post, relację, okładkę wydarzenia, logo na zdjęciu, napis, grafikę na Instagram albo do druku (A4, A3). Używaj przy każdej prośbie o zrobienie lub poprawienie grafiki — prowadzi od zlecenia przez kierunki i etapy do sprawdzonych plików ostatecznych.
---

# Zlecenie graficzne — od pomysłu do gotowych plików

Mów po polsku, krótko, bez żargonu. Polecenia uruchamiasz sam, DESIGNER to ścieżka skryptu
(jak w procedurze `graphic-designer`: `python3 DESIGNER …`, Windows `py -3 DESIGNER …`).
Przykłady poniżej używają zmyślonej marki „Kiwi Studio”.

Człowiek ocenia i akceptuje; ty proponujesz. Niczego nie publikujesz w mediach
społecznościowych — plugin tego nie robi. Do repozytorium trafiają tylko grafiki ostateczne.

## Obowiązkowa kolejność

Zanim zaczniesz, przejdź tę listę po kolei. Nic nie pomijasz po cichu.

1. **Brief** — pytania i `brief.md` (krok 1).
2. **Kierunki + STOP** — trzy różne kierunki zapisane przez `draft --direction` i czekanie
   na wybór (krok 2).
3. **`choose`** — zaraz po wyborze osoby: `DESIGNER choose --job <slug> --direction <litera>`;
   dla zlecenia bez rundy kierunków `DESIGNER choose --job <slug> --direct`. Bez tego `check`
   nie przejdzie.
4. **Etapy z `draft` i `freeze`** — każdy obraz z generatora przechodzi przez `draft`,
   a po akceptacji jest zamrożony przez `freeze` (krok 3).
5. **`render`** — składanie plików (krok 5).
6. **`check`** — musi dać `OK` (krok 5).
7. **Samoocena** według rubryki z `../graphic-designer/references/critique.md`.
8. **Lista do sprawdzenia przez człowieka** — po pokazie złożonej grafiki (krok 6, punkt 4).
9. **Dopiero potem pokaz** osobie jako gotowa praca.

Skrypt pilnuje tej kolejności: `status` pokazuje etap i następny krok, a `check` zgłasza
błąd `process`, gdy brief jest pusty albo nie zapisano wyboru kierunku (a `finalize` bez
czystego `check` nie zamknie pakietu).

Gdy grafika ma trafić na Instagram, Facebooka albo inną sieć (post, karuzela, relacja, okładka
rolki), przeczytaj najpierw procedurę **social-content**: dobiera format do celu, hasło otwierające
(hak) i opis posta, a kierunki różnią się **sposobem przyciągnięcia uwagi**, nie tylko wyglądem.

Kierunki pomijasz tylko w dwóch przypadkach: osoba opisała dokładnie gotowy wygląd, albo
to zwykłe nałożenie (logo na zdjęcie). Wtedy od razu `choose --direct`. Prośba, która podaje tylko temat, format i datę
(np. „post na warsztaty ceramiki w sobotę”), **nie** jest takim opisem: najpierw zadaj 2–4
pytań do briefu (cel i odbiorca, nastrój, elementy obowiązkowe, teksty dosłownie), potem
zaproponuj trzy kierunki i zatrzymaj się.

Każdy obraz z generatora użyty w kompozycji ma przejść przez `draft` i po akceptacji zostać
zamrożony przez `freeze`; nie kopiuj go do `layers/` ręcznie (wtedy `check` zgłosi, że
warstwa użyta w kompozycji nie jest zamrożona). Osoba nie zobaczy „finału” bez `check` z wynikiem `OK`. Jeśli `render` albo
`check` nie działa (np. przeglądarka nie startuje w piaskownicy: wynik z `SANDBOX?:`),
poproś o jednorazową zgodę na uruchomienie poza piaskownicą; nie składaj grafiki innym
narzędziem. Przy odmowie zgody nie ma pliku ostatecznego: pokazujesz tylko kierunki i szkice
i mówisz wprost, że bez zgody nie złożysz ani nie sprawdzisz grafiki. Po pokazie złożonej
grafiki wypisz listę „do sprawdzenia przez człowieka”.

## Kto co robi: generator a składanie

Generator obrazów przy każdej edycji renderuje cały obraz od nowa, nie przyjmuje własnych
fontów, a w Codexie nie ma maski ani wyboru rozmiaru w pikselach. Dlatego:

| Element | Kto robi |
|---|---|
| pomysły, szkice kierunków, nastrój | generator |
| tła, ilustracje, tekstury, elementy dekoracyjne | generator, potem warstwa zamrożona |
| liternictwo odręczne albo ozdobne (np. nowy napis eventu) | generator z przezroczystym tłem, potem warstwa zamrożona |
| logo marki, gotowe znaki | **plik z biblii marki**, nigdy generator |
| zdjęcia osób | **oryginalny plik**, nigdy generator |
| teksty informacyjne (data, miejsce, cena, wezwanie do działania) | **skład w fontach marki**, nigdy generator |
| złożenie całości, formaty, eksport | skrypt składający (`render`) |

Logo i dokładny tekst składasz z plików poleceniem `render`; generatorowi ich nie zlecasz.
Tekst w generatorze tylko wtedy, gdy liternictwo jest elementem graficznym, a nie informacją;
wtedy sprawdzasz każdą literę i polskie znaki. Jak pisać polecenia dla generatora:
`../graphic-designer/references/image-prompting.md`.

## 1. Zlecenie

1. Jeśli zlecenia jeszcze nie ma: `DESIGNER new --title "Plakat otwarcia" --formats ig-post,ig-story`
   (opcjonalnie `--project <nazwa>` i `--brand <folder brand/>`). Dostępne formaty:
   `ig-post`, `ig-square`, `ig-story`, `fb-event`, `a4-print`, `a3-print`
   (rozmiary i strefy: `../graphic-designer/references/formats.md`, wydruk: `../graphic-designer/references/print.md`).
   Gdy nie ma biblii marki, zlecenie powstaje bez niej; po jej założeniu
   `DESIGNER set-brand --job <slug> --brand <folder>`.
2. Wypełnij `brief.md` w folderze zlecenia według `../graphic-designer/references/brief.md`: cel, odbiorca, jedna
   wiadomość, teksty dosłowne (z polskimi znakami), formaty, elementy obowiązkowe, materiały
   wejściowe i ich rola, nastrój, czego nie chcemy. **Brakujących tekstów i formatów nie
   zgaduj — dopytaj.** Krótkie zlecenie („logo na moje zdjęcie, post 4:5”) nie wymaga długiego
   wywiadu: dopytaj tylko o to, czego brakuje.
3. Daty i dni tygodnia z briefu sprawdź (czy 14.03 to naprawdę sobota); rozbieżność zgłoś.

## 2. Kierunki — STOP na wybór

Przy zleceniu z otwartą formą zaproponuj **kilka kierunków naraz, domyślnie trzy**, wyraźnie
różnych na jednej nazwanej osi: koncepcja, układ, typografia albo akcent kolorystyczny.
Kierunek różniący się od innych tylko kolorem odpada. Każdy ma:

- nazwę w 1–3 słowach (np. „Wiosenna gęstwina”),
- jedno zdanie idei,
- proporcje palety (np. 60% tło, 30% zieleń, 10% pomarańcz — role z biblii marki),
- rolę krojów (co nagłówkiem, co tekstem),
- podgląd (szkic z generatora albo makieta).

Każdy podgląd zapisz: `DESIGNER draft --job <slug> --file <plik> --direction A --note "Wiosenna
gęstwina: ciemne tło, zielony napis"` (polecenie generatora dodaj w `--prompt`).

Potem **zatrzymaj się i czekaj na wybór**. Gdy osoba wybierze, zapisz to od razu:
`DESIGNER choose --job <slug> --direction A`. Liczbę kierunków osoba może zmienić; przy więcej niż
trzech powiedz, że każdy obraz zużywa limit. Zlecenie z jasno opisanym efektem („nałóż logo na
zdjęcie”) pomija ten krok: zapisz `DESIGNER choose --job <slug> --direct` i przejdź od razu do jednego
etapu, czyli złożenia.

## 3. Etapy

Po wyborze kierunku dopracowujesz go etapami. Typowa kolejność: **liternictwo albo logo →
tło → pozostałe elementy → złożenie**. Etapy nie są sztywne. Po każdym etapie pokaż wynik
i czekaj na „akceptuję” albo poprawkę.

- Każdą propozycję i każdą wersję zapisuj w `drafts/` poleceniem `draft` (jak wyżej). Przy
  poprawkach `--direction` to litera wybranego kierunku (np. `A`), a `--note` mówi, co się zmieniło
  w tej wersji.
  Wersje to `v1`, `v2`, … — nigdy nie nadpisujesz poprzedniej, a każda ma jedno zdanie,
  co się zmieniło.
- **Zamrożenie po akceptacji etapu:** `DESIGNER freeze --job <slug> --name tlo --file
  drafts/<plik> --source generated --approved-by "<imię osoby>" --prompt "<dosłowne polecenie>"
  --inputs <pliki wejściowe po przecinku> --note "<jedno zdanie>"`. Źródło (`--source`):
  `generated`, `photo`, `brand` albo `composed`. Zamrożona warstwa jest nietykalna: nie generujesz
  jej ponownie. Gdy prośba narusza zamrożony element, nazwij to wprost („to tło jest zamrożone
  — odmrozić?”). Po „tak” użyj `freeze` z `--replace`, nie wcześniej.
- Po zamrożeniu **zapytaj, czy udostępnić pracę w toku zespołowi** (`share`): „Zapisać to, co
  mamy, jako pakiet w repozytorium, żeby inni mogli zobaczyć?” Bez „tak” nie rób tego.
  `DESIGNER share --job <slug> --repo <korzeń repozytorium>` (`--replace`, gdy pakiet już
  ma `final/`); potem zapisz pakiet w repozytorium według `AGENTS.md` tego repozytorium.

## 4. Poprawki: jedna zmiana na turę

Osoba prosi o zmiany — zrób **jedną zmianę na wersję**; resztę zapisz i zrób w kolejnych turach.
Każde polecenie dla generatora zawiera blok:

```
Nie zmieniam: kompozycja, paleta, napis, światło, tło za postacią.
Zmieniam tylko: kolor listków z jasnej na ciemną zieleń.
```

Wynik poprzedniej wersji idzie do generatora jako obraz wejściowy (edycja, nie nowe losowanie).
Zapisz wersję przez `draft` z krótkim opisem. Stały blok stylu wklejaj dosłownie
(`../graphic-designer/references/image-prompting.md`).

## 5. Złożenie, sprawdzenie, pokaz

1. Kompozycję piszesz jako `composition/<format-id>.html` (punkt wyjścia: szablon
   `templates/composition-starter.html` z pluginu). Logo: `src="brand:logo/full.png"` z atrybutem
   `data-gd="logo"`; warstwy: `src="../layers/<plik>"`; teksty: `data-gd="text"`; kolory przez
   `var(--color-<rola>)`, fonty tylko z biblii. Zasady: `../graphic-designer/references/composition.md`,
   `../graphic-designer/references/typography.md`, `../graphic-designer/references/color.md`, `../graphic-designer/references/logo.md`,
   `../graphic-designer/references/poster.md`.
2. Podgląd ze strefami bezpiecznymi: `DESIGNER render --job <slug> --preview` (zapisuje
   w `drafts/`). Obejrzyj go sam przed pokazem.
3. Pliki właściwe: `DESIGNER render --job <slug>` (`--format <id>` tylko dla jednego formatu).
4. **`DESIGNER check --job <slug>`** — liczy kontrast, wymiary, fonty, brakujące znaki i strefy
   bezpieczne. `OK` (kod 0) → dalej. `PROBLEMS: n` (kod 3) → popraw albo powiedz wprost, czego nie
   da się naprawić. Brakujący znak w foncie (np. „ą”) to błąd do naprawienia, nie do pominięcia.
5. Samoocena według rubryki w `../graphic-designer/references/critique.md` (14 punktów, przy każdym: spełnia /
   nie spełnia i jedno zdanie dowodu). Nie pomijaj jej. Sprawdź też `../graphic-designer/references/generic-ai-tells.md`. Bez biblii
   marki pomiń punkty marki i powiedz o tym.
6. Dopiero wtedy pokaż złożoną grafikę osobie. **Odpowiedź z gotową grafiką ma zawsze cztery
   części, każdą jako osobną krótką listę:**

   - **Plik:** pełna ścieżka i wymiary.
   - **Kontrola automatyczna:** wynik `check` (np. „OK: 12/12”) i, co ważne, co pominięto.
   - **Samoocena:** punkty rubryki w skrócie; niezaliczone wymień wprost.
   - **Do sprawdzenia przez człowieka:** lista z rozdziału 6, punkt 4 (teksty słowo po słowie,
     data i dzień tygodnia, godzina i miejsce, adres, do którego prowadzi kod QR, zgody osób
     na zdjęciach, logo partnerów) oraz każdy wyjątek od biblii marki.

   Odpowiedź zawierająca tylko link do pliku nie spełnia tej procedury.

## 6. Akceptacja i pakiet

Gdy osoba mówi, że grafika jest gotowa:

1. Uruchom `check` jeszcze raz — **`check` musi przejść przed `finalize`.**
2. `DESIGNER finalize --job <slug> --repo <korzeń repozytorium> --approved-by "<imię osoby>"`.
   Zamyka zlecenie jako pakiet `graphics/<RRRR-MM>-<zlecenie>/` (gotowe pliki we wszystkich
   formatach, warstwy, kompozycje, `README.md`). `--accept-problems` tylko po wyraźnej decyzji
   osoby, która zna listę problemów; `--replace`, gdy pakiet już istnieje i ma być zastąpiony.
3. Skrypt nie używa gita. Pakiet zapisz w repozytorium według `AGENTS.md` tego repozytorium,
   na osobnym branchu, i **zaproponuj PR** — nie merguj sam.
4. Pokaż **listę do sprawdzenia przez człowieka**: teksty słowo po słowie, data i dzień
   tygodnia, godzina i miejsce, link albo kod, zgoda osób widocznych na zdjęciach, nazwy
   i logo partnerów.
5. Powiedz jasno: grafikę akceptuje człowiek, a publikacji w mediach społecznościowych plugin
   nie robi — osoba wrzuca ją sama.

## Granice

- **Wycięcie postaci ze zdjęcia** — „jeszcze tego nie umiem”. Zaproponuj zdjęcie wycięte
  wcześniej (np. aplikacją Zdjęcia na Macu albo iPhonie) jako plik z przezroczystym tłem;
  wejdzie jako warstwa.
- Logo i zdjęcia osób nigdy z generatora. Tylko oryginalny plik.
- Kolory i fonty spoza biblii marki — tylko za zgodą osoby; zmiana biblii to procedura **brand-kit**.
  Gdy osoba mówi, że styl jest „za ciężki” albo „nie ten”, najpierw szukaj rozwiązania **w obrębie
  marki** (inne proporcje, więcej światła, mniejszy nagłówek, inna waga, inny kadr). Jeśli to nie
  wystarcza i chcesz użyć innego kroju albo koloru, powiedz to wprost („Biblia ma tylko Anton; proponuję
  dla tego posta krój z szeryfami — zgoda?”) i czekaj na „tak”. Zapisz wyjątek w `brief.md`.
  `check` tego nie wyłapie: fonty spoza biblii pomija i tylko o tym wspomina.
- Wydruk (A4, A3): spad i PDF — `../graphic-designer/references/print.md`.
