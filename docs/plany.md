# Plany ChatGPT a obrazy w Codexie

Stan na **16.10.2026**, wyłącznie z oficjalnych stron OpenAI (linki na dole).
OpenAI zmienia limity często — aktualne liczby zawsze pokazuje Twój panel użycia
(w Codexie CLI polecenie `/status`).

## W skrócie

- **Obrazy w Codexie są na planach Plus, Pro, Business i Enterprise/Edu. Na Free
  ich nie ma.** Dla planu Go strona OpenAI tego nie mówi — niepotwierdzone.
- Codex rysuje modelem **`gpt-image-2`**. Przyjmuje obrazy referencyjne (dlatego
  plugin podaje arkusze postaci na wejściu) i umie **edytować** istniejący obraz,
  także tylko zaznaczony fragment.
- **Obraz nie ma osobnego limitu.** Liczy się do wspólnego limitu Codexa (ten sam co
  wiadomości), ale zużywa go **średnio 3–5 razy szybciej** niż zwykła tura —
  im większy i lepszej jakości obraz, tym więcej.
- **OpenAI nie publikuje, ile obrazów daje który plan.** Ile Ci zostało, widać tylko
  w panelu użycia.
- Po wyczerpaniu limitu: na Plus i Pro można **dokupić kredyty** bez zmiany planu
  (ceny kredytów zależą od planu, OpenAI nie podaje ich na tej stronie), albo poczekać
  na odnowienie. Turę, która już trwa, Codex dokończy.

## Plany

| Plan | Cena | Obrazy w Codexie | Uwagi |
|---|---|---|---|
| Free | 0 $ | **nie** | tylko lekki model w aplikacji desktop |
| Go | 8 $ / mies. | niepotwierdzone | strona opisuje Go jako „lekkie zadania”; plan nie występuje w tabeli funkcji |
| Plus | 20 $ / mies. | tak | „kilka sesji tygodniowo”; okna limitu 5-godzinne i tygodniowe; dokupowanie kredytów |
| Pro | od 100 $ / mies. (100, 200, 500 $) | tak | brak limitu 5-godzinnego, limit tygodniowy może obowiązywać; dokupowanie kredytów |
| Business | 20 $ / os. / mies. rocznie, 25 $ miesięcznie (od 2 osób) | tak | kredyty firmowe |
| Enterprise / Edu | wycena indywidualna | tak | przy rozliczaniu kredytami brak stałych limitów |

## Rozmiary i jakość

W Codexie piszesz po prostu, jaki obraz chcesz (format bierze plugin z `komiks.yaml`).
Strona Codexa nie wymienia ustawień rozmiaru ani jakości. Dla tego samego modelu
w API OpenAI podaje: zalecane rozmiary **1024×1024**, **1024×1536** (pion),
**1536×1024** (poziom), jakość **low / medium / high**, maks. 3840 px na dłuższym boku,
proporcje najwyżej 3:1.

## Ile to kosztuje, gdy płacisz za sztukę

Przy dużych seriach OpenAI radzi podłączyć w Codexie własny klucz API — wtedy obrazy
nie zjadają limitu planu, tylko kosztują wg cennika API. Ceny jednego obrazu
`gpt-image-2` (sam wynik, bez obrazów na wejściu):

| Jakość | 1024×1024 | 1024×1536 (pion) |
|---|---|---|
| low (szkic) | 0,006 $ | 0,005 $ |
| medium | 0,053 $ | 0,041 $ |
| high | 0,211 $ | 0,165 $ |

Obrazy referencyjne na wejściu też są liczone (jako tokeny wejścia), więc realna
plansza z 3–4 referencjami kosztuje trochę więcej niż w tabeli.

## Ile obrazów zużywa komiks (szacunek pluginu)

| Etap | Obrazów |
|---|---|
| propozycje stylów | 5–8 |
| jedna postać z arkuszem obrotu, mimiką i pozami | 12–20 |
| miejsce | 1–2 |
| plansza próbna | 1–3 |
| **cały projekt (2 postaci, 2 miejsca)** | **35–55** |
| odcinek: 1 plansza | 2–4 |
| odcinek: karuzela 3 plansz | 6–12 |

Jak oszczędzać: słowa poprawiaj w scenariuszu, nie na obrazach; poprawiaj kadr edycją,
nie od zera; projekt rozłóż na kilka dni; scenariusze rób na zapas, gdy limit się kończy.

## Czego nie udało się potwierdzić

- Czy plan **Go** generuje obrazy w Codexie.
- Liczby obrazów na plan i okno czasowe (OpenAI ich nie publikuje).
- Ceny kredytów dla Plus i Pro w dolarach.
- Limity obrazów w zwykłym czacie ChatGPT („zależą od planu i ustawień workspace”).
- Strony help.openai.com i chatgpt.com/pricing nie dały się odczytać automatycznie,
  więc nie były porównane.

## Źródła (sprawdzone 16.10.2026)

- Plany i limity Codexa, kredyty, tabela funkcji: https://learn.chatgpt.com/docs/pricing
- Obrazy w Codexie (model, referencje, edycja, klucz API): https://learn.chatgpt.com/docs/image-generation
- Rozmiary, jakość i ceny obrazów w API: https://developers.openai.com/api/docs/guides/image-generation
- Model `gpt-image-2`: https://developers.openai.com/api/docs/models/gpt-image-2
