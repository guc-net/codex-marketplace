---
name: social-content
description: Zaprojektuj post na Instagram, karuzelę, relację, okładkę rolki albo serię treści; hasło otwierające, opis posta i pomysł, który zatrzymuje przewijającą osobę. Używaj, gdy grafika ma trafić do mediów społecznościowych — dobiera format do celu, układa hasło, opis i kolejność slajdów, a składanie grafiki oddaje procedurze design-job.
---

# Treści na media społecznościowe

Mów po polsku, krótko, bez żargonu (nie „hook”, „CTA”, „reach” — mów „hasło otwierające”,
„wezwanie do działania”, „zasięg”). Odpowiedzi układaj według zasad z procedury `graphic-designer`
(listy w osobnych liniach). Plugin niczego nie publikuje: osoba wrzuca gotowe pliki sama.

Post w mediach ma jedną robotę: **zatrzymać kciuk w ułamku sekundy** i po chwili skłonić do jednej
rzeczy (zapisu, zapisania posta, przesłania dalej, wejścia na profil). Ładna grafika, która nie
zatrzymuje, przegrywa z brzydką, która zatrzymuje. DESIGNER to ścieżka skryptu (jak w procedurze
`graphic-designer`).

## Kolejność

1. **Cel w jednym zdaniu.** Z briefu albo dopytaj: „Co ma zrobić osoba po zobaczeniu tego posta?”
   Jeden post, jeden cel, jedno wezwanie do działania. Odbiorca: kto przewija i w jakim nastroju.
2. **Format do celu** (tabela niżej). Zaproponuj jedną odpowiedź, nie menu.
3. **Hasło otwierające.** Pomysły na hasło piszesz z `../graphic-designer/references/social.md`
   (wzory haseł) i `../graphic-designer/references/copy-pl.md` (polszczyzna, ton). Daj **trzy
   różne hasła** do wyboru, każde w osobnej linii; teksty dosłowne zatwierdza osoba.
4. **Trzy kierunki = trzy sposoby przyciągnięcia uwagi**, nie trzy kolory. Wybierz trzy różne z listy
   w `../graphic-designer/references/social.md` (np. duże hasło, człowiek w akcji, zbliżenie na
   fakturę). Każdy kierunek: nazwa, jedno zdanie idei, jak przyciąga wzrok, jak wygląda w
   małym podglądzie. **Zatrzymaj się i czekaj na wybór** (zapis: `design-job`, krok 2).
5. **Dopracowanie i składanie** idzie przez procedurę **design-job** (etapy, `freeze`, `render`,
   `check`). Zlecenie zakładasz z formatami z tabeli, np. `DESIGNER new --title "Warsztaty
   ceramiki" --formats ig-post,ig-story`.
6. **Opis posta** piszesz po wyborze kierunku i pokazujesz razem z grafiką (wzór w
   `../graphic-designer/references/copy-pl.md`). Zapisz go w `brief.md`, w sekcji o mediach.
7. **Test przewijania** (rozdział „Przed pokazem”) — zawsze przed pokazem grafiki.

## Format do celu

| Cel | Format | Id w pluginie |
|---|---|---|
| Zapisy na wydarzenie, warsztat, zajęcia | post 4:5 z datą na pierwszym planie, do tego relacja z przypomnieniem | `ig-post`, `ig-story` |
| Wyjaśnić, nauczyć, pokazać proces, rozwiać wątpliwości | karuzela (5–8 slajdów) | `ig-carousel-1` … `ig-carousel-10` |
| Dotrzeć do nowych osób | okładka rolki i post z mocnym hasłem | `ig-story`, `ig-post` |
| Przypomnienie w ostatniej chwili („zostało 3 miejsca”) | relacja | `ig-story` |
| Okładka wydarzenia na Facebooku | okładka | `fb-event` |
| Plakat na ścianę | A4 albo A3 | `a4-print`, `a3-print` |

Rozmiary i strefy bezpieczne: `../graphic-designer/references/formats.md`. Na profilu Instagram
pokazuje środek obrazu w kadrze 3:4, więc to, co ważne, trzymaj blisko środka.

## Karuzela — jak ją układać

- Slajd 1 działa **sam**: to hasło i obietnica. Jeśli ktoś zobaczy tylko ten slajd, ma już
  powód, żeby przesunąć. Małą wskazówkę („przesuń”) dodaj tylko, gdy układ jej nie sugeruje.
- Slajdy 2 do przedostatniego: **jedna myśl na slajd**, krótko, ta sama siatka, ten sam rytm.
- Ostatni slajd: jedno wezwanie do działania i dane praktyczne (data, miejsce, jak się zapisać).
- Połącz slajdy jednym elementem wizualnym (kolor tła na przemian, obiekt przechodzący przez
  krawędź, numeracja), żeby czuć serię.
- Każdy slajd to osobna kompozycja `composition/ig-carousel-N.html`. Przed `check` upewnij się, że
  masz kompozycję dla każdego numeru z zlecenia.

## Relacja i okładka rolki

Pionowo 9:16 (`ig-story`). U góry i na dole zasłaniają ją elementy aplikacji (strefy w `../graphic-designer/references/formats.md`).
Jedna wiadomość do przeczytania w 2–3 sekundy. Ankiety, pytania i naklejki z odliczaniem dodaje
człowiek w aplikacji; zostaw na nie puste miejsce i powiedz, gdzie. Okładka rolki: krótki tytuł
w środku, bo siatka profilu przycina boki.

## Przed pokazem: test przewijania

Zrób podgląd poleceniem `DESIGNER render --job <slug> --preview` i oceń go tak, jakby był
pomniejszony do szerokości telefonu (ok. 420 px). Odpowiedz na każdy punkt jednym zdaniem:

1. **Zatrzymuje:** po pół sekundy wiadomo, o czym to jest i co jest „inne”?
2. **Hasło:** jedno, do siedmiu słów, konkretne?
3. **Mały podgląd:** hasło i data czytelne bez powiększania?
4. **Jeden cel:** jedna wiadomość, jedno wezwanie do działania?
5. **Prawda:** obietnica z hasła jest prawdziwa (bez wabika, bez zmyślonych liczb i opinii)?
6. **Środek kadru:** najważniejsze mieści się w kadrze 3:4 profilu?
7. **Mało tekstu:** na grafice tylko to, co zatrzymuje i informuje; reszta w opisie posta?
8. **Dostępność:** kontrast sprawdzi `check`; dopisz propozycję tekstu alternatywnego do posta.
9. **Nie jak wszyscy:** nic z `../graphic-designer/references/generic-ai-tells.md` i coś, co jest
   tylko tej marki?

Niezaliczone popraw przed pokazem albo powiedz wprost, czego nie da się naprawić.

## Czego nie robisz

- Nie obiecujesz zasięgu ani wyników. Publikacja, godzina i płatna promocja to decyzja człowieka.
- Nie wymyślasz opinii, liczb uczestników, nagród ani „ostatnich miejsc”, jeśli osoba tego nie podała.
- Nie kopiujesz cudzych postów ani znaków innych marek; inspiracja tak, kopia nie.
- Nie przekraczasz biblii marki (kolory, fonty, logo) bez zgody; zasady w procedurze **design-job**.
