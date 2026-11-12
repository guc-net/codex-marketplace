# Formaty i wymiary

Źródłem prawdy jest `templates/formats.json`. Poniższa tabela to jego czytelna kopia
(pilnuje tego test). Strefa bezpieczna: ile pikseli od krawędzi zostawić na ważne treści
(góra / prawo / dół / lewo).

| id | Nazwa | Wymiar (px) | PDF | Strona (mm) | Strefa bezpieczna (px) |
|---|---|---|---|---|---|
| `ig-post` | Post na Instagram (4:5) | 1080×1350 | nie | — | 34 / 34 / 34 / 34 |
| `ig-square` | Post kwadratowy na Instagram | 1080×1080 | nie | — | 34 / 34 / 34 / 34 |
| `ig-carousel-1` … `ig-carousel-10` | Karuzela na Instagram, jeden slajd (4:5) | 1080×1350 | nie | — | 34 / 34 / 34 / 34 |
| `ig-story` | Relacja na Instagram (9:16) | 1080×1920 | nie | — | 270 / 65 / 340 / 65 |
| `fb-event` | Okładka wydarzenia na Facebooku | 1920×1005 | nie | — | 189 / 360 / 189 / 360 |
| `a4-print` | Plakat A4 do druku | 2551×3579 | tak | 216×303 | 71 / 71 / 71 / 71 |
| `a3-print` | Plakat A3 do druku | 3579×5031 | tak | 303×426 | 71 / 71 / 71 / 71 |

## Uwagi

- **Karuzela:** każdy slajd to osobny format (`ig-carousel-1`, `ig-carousel-2`, `ig-carousel-3`, `ig-carousel-4`, `ig-carousel-5`, `ig-carousel-6`, `ig-carousel-7`, `ig-carousel-8`, `ig-carousel-9`, `ig-carousel-10`), z własną
  kompozycją `composition/ig-carousel-N.html`. Rozmiar jak `ig-post`. Zlecenie zakładasz z tyloma slajdami, ile
  ma karuzela, np. `--formats ig-carousel-1,ig-carousel-2,ig-carousel-3`. Dla dłuższej serii dodaj formaty do
  `templates/formats.json`.

- **Instagram, siatka profilu:** pokazuje kadr 3:4 ze środka posta pionowego (ok. 1012×1350), więc
  najważniejsze treści trzymaj blisko środka.
- **Relacja (story):** u góry i na dole zasłaniają ją elementy aplikacji (nazwa, pole odpowiedzi),
  stąd duże strefy. Źródła podają różne wartości, dlatego sprawdź podgląd w samej aplikacji.
- **Okładka wydarzenia:** telefon tnie ją mocniej niż komputer. Tekst trzymaj w środku.
- **Druk A4 i A3:** wymiary zawierają spad 3 mm z każdej strony (A4 216×303 mm, A3 303×426 mm
  przy 300 dpi). Zob. `print.md`.
- Wymiary serwisów społecznościowych bywają zmieniane. Rozbieżność z aktualną specyfikacją
  zgłoś, zamiast po cichu jej ufać.

## Format spoza listy

Nowy format dodaje się do `templates/formats.json` (id, wymiar, strefa bezpieczna), nie w locie
w kompozycji. Wtedy `render` i `check` znają jego wymiary.
