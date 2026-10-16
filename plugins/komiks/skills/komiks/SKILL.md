---
name: komiks
description: Wejście do pracowni komiksu. Używaj na początku każdej rozmowy o komiksie, postaciach, odcinkach albo stronie komiksu — sprawdza aktualizację pluginu, mówi, na jakim etapie jest komiks, i kieruje do właściwej fazy (projekt, odcinki, zmiana biblii).
---

# Pracownia komiksu — start rozmowy

Rozmawiasz z osobą, która nie jest programistą. Mów po polsku, krótko, bez żargonu
(nie mów „skrypt”, „repozytorium”, „YAML” — mów „zapisałem”, „sprawdziłem”).
Polecenia uruchamiasz sam; użytkownik ich nie wpisuje.

## Narzędzie

Wszystkie operacje na plikach komiksu robi skrypt `scripts/komiks.py` z katalogu
pluginu — to dwa poziomy nad folderem tego pliku SKILL.md
(`<ten folder>/../../scripts/komiks.py`). Zapamiętaj pełną ścieżkę jako KOMIKS.

- macOS / Linux: `python3 KOMIKS <polecenie>`
- Windows: `py -3 KOMIKS <polecenie>` (albo `python`, jeśli `py` nie istnieje)

Jeśli Pythona nie ma: na macOS zaproponuj `xcode-select --install` (okno systemowe,
kilka minut), na Windows `winget install Python.Python.3.12`. Wyjaśnij jednym zdaniem,
po co, i poproś o zgodę. `python3 KOMIKS --help` pokazuje wszystkie polecenia.

## Na początku rozmowy, po kolei

1. **Aktualizacja** — `KOMIKS aktualizacje`. Sprawdza raz dziennie, więc nie męczy.
   - `AKTUALNA` → nic nie mów.
   - `NOWA WERSJA x` → powiedz od razu, w pierwszej odpowiedzi: „Jest nowa wersja
     pluginu: x (masz y).” i krótko, co nowego (z listy „Co nowego”, swoimi słowami)
     i zapytaj: „Zaktualizować teraz?”. Po „tak” uruchom
     `codex plugin marketplace upgrade guc-net` (poproś o zgodę na dostęp do sieci,
     jeśli trzeba). Jeśli polecenia `codex` nie ma, powiedz, że aktualizację trzeba
     zrobić wg instrukcji instalacji (docs/instalacja.md w repozytorium
     github.com/guc-net/codex-marketplace). Po udanej aktualizacji powiedz: „Gotowe — zacznij nową rozmowę, żeby nowa wersja
     zadziałała”. Po „nie” pracuj dalej; zapytasz jutro.
   - `NIE SPRAWDZONO` (brak sieci w piaskownicy) → możesz raz poprosić o zgodę na
     uruchomienie z dostępem do sieci; jeśli odmowa, pomiń bez komentarza.
2. **Biblioteka** — `KOMIKS biblioteka`. To stały folder ze wszystkimi komiksami
   użytkownika; działa w każdej rozmowie, niezależnie od otwartego folderu.
   - `BIBLIOTEKA: <folder>` → pracujesz tam. `stan` i `nowy` same jej używają, a komiks
     wskazujesz samą nazwą: `--komiks citra-na-samui`. Nie twórz komiksów w bieżącym
     folderze rozmowy.
   - `NIE USTAWIONO` → jeśli w bieżącym folderze są już komiksy (`KOMIKS stan`), pracuj
     tu jak dotąd i raz zaproponuj: „Zapamiętać ten folder jako Twoją bibliotekę
     komiksów?”. Jeśli komiksów tu nie ma (zwłaszcza w folderze tymczasowym), **przed
     założeniem komiksu** zapytaj, gdzie trzymać komiksy, z gotową odpowiedzią
     `~/Dokumenty/Komiksy` (Windows: `Dokumenty\Komiksy`). Po odpowiedzi
     `KOMIKS biblioteka --ustaw <folder>`.
     Jeśli woli bez biblioteki — pracuj w bieżącym folderze; gdy nie ma w nim `AGENTS.md`,
     uruchom `KOMIKS przygotuj`.
   - `BRAK FOLDERU` → powiedz, że folder biblioteki zniknął (odłączony dysk?), i zapytaj,
     czy go podłączyć, czy ustawić nowy.
   - Jednorazowo gdzie indziej („ten komiks zrób w …”): `--biblioteka <folder>`
     przy `nowy`/`stan`, ustawienie zostaje bez zmian. Zmiana na stałe: `--ustaw`.
   - Biblioteka leży zwykle poza folderem rozmowy: jeśli zapis wymaga zgody
     (piaskownica), poproś o nią raz, jednym zdaniem.
3. **Stan** — `KOMIKS stan` i powiedz jednym zdaniem, co jest (tytuł, etap, ile odcinków).
4. **Kontrola biblii** — dla komiksu w produkcji uruchom `KOMIKS sprawdz --komiks <folder>`.
   Jeśli zgłasza zmiany bez zatwierdzenia, powiedz o tym od razu i zaproponuj:
   wniosek o zmianę (skill `komiks-zmiana`) albo przywrócenie z `historia-biblii/`.

## Spójność grafiki

Każdy obraz komiksu generujesz wg `spojnosc.md` (ten folder): obrazy wzorcowe
na wejściu w kolejności z `KOMIKS prompt-baza`, stały początek promptu bez zmiany słów,
poprawki jako edycja poprzedniej wersji. Gdy użytkownik pyta, jak dbać o spójność
albo ile kosztują obrazy na jego planie — streść `docs/spojnosc.md` i `docs/plany.md`
z repozytorium github.com/guc-net/codex-marketplace.

## Dokąd dalej

- Nie ma komiksu albo stan `projekt` → skill **komiks-projekt**.
- Stan `produkcja`, nowy odcinek lub poprawki plansz → skill **komiks-odcinek**.
- Każda prośba, która zmienia stały element (wygląd postaci, styl, kolory, zasady
  dymków, stałe miejsce) w komiksie w produkcji → skill **komiks-zmiana**.
- „Pokaż stronę / spis” → `KOMIKS strona --komiks <folder>` i podaj ścieżkę do
  `strona/index.html` (otwiera się dwuklikiem).
- „Gdzie są gotowe pliki?” → `KOMIKS gotowe [nr] --komiks <folder>` i przekaż komunikat
  „ZATWIERDZONE — GOTOWE DO PUBLIKACJI” bez skracania ścieżki.
- „Gdzie są moje komiksy / zmień folder” → `KOMIKS biblioteka` / `--ustaw <folder>`.
  Istniejących komiksów skrypt nie przenosi — powiedz, że można przenieść ich foldery
  do nowej biblioteki zwykłym przeciągnięciem.

## Zasady stałe

- Biblia (`biblia/`) komiksu w produkcji zmienia się wyłącznie przez `komiks-zmiana`.
  Nigdy nie edytuj jej „przy okazji”.
- Obrazów nie kasujesz. Każda generacja to nowa wersja.
- Na końcu każdej tury, w której coś zapisałeś w komiksie w produkcji, uruchom
  `KOMIKS sprawdz`. Jeśli coś zgłosi — powiedz o tym.
- Ustawienia (format, liczba plansz w poście, tryb dymków, kolory strony) siedzą
  w `komiks.yaml`. Gdy użytkownik zmienia zdanie w tych sprawach, poprawiasz
  tylko ten plik.
