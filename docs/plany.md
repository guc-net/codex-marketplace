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

## Rozmiar, rozdzielczość i jakość

**W Codexie nie wymusisz rozmiaru w pikselach ani jakości.**
Wbudowane narzędzie do obrazów nie ma takich ustawień — OpenAI w instrukcji dla
Codexa pisze wprost, że jakość i rozmiar to opcje tylko trybu przez API
(z własnym kluczem). Możesz poprosić o **proporcje** („pionowo 4:5”, „kwadrat”),
a generator sam dobiera piksele: na prośbę o 4:5 dał nam 1122×1402, na inne
prośby 1024×1536 czy 1536×1024.

Dlatego plugin robi tak:

1. Prosi generator o proporcje posta z `komiks.yaml` (4:5 albo 1:1) i o margines
   przy krawędziach (twarze i dymki nie przy samym brzegu).
2. Po wybraniu finału sam robi folder **`gotowe/`**: plansze docięte od środka
   do dokładnych proporcji i przeskalowane do **1080×1350** (albo 1080×1080).
   Oryginały w pełnej jakości zostają w `final/`.
3. Jeśli coś trzeba było uciąć albo mocno powiększyć, mówi o tym — wtedy obejrzyj
   dymki na brzegach.

Przez API (własny klucz, płatne za sztukę) da się ustawić więcej: rozmiar dowolny
w granicach (boki podzielne przez 16, do 3840 px, proporcje do 3:1 — np. 1088×1360
to dokładne 4:5), jakość **low / medium / high** (nowsze modele `gpt-image-2.5`
także xhigh i max). Codex w aplikacji rysuje `gpt-image-2`.

### Czy jakość wpływa na czas generowania?

Według OpenAI — **tak, ale tylko tam, gdzie jakość da się wybrać (API)**:

- „Use quality low for quick drafts. For final assets, compare higher quality
  settings to find the right balance of detail, latency, and cost” — niższa
  jakość = szybciej i taniej, wyższa = więcej szczegółów, dłużej.
- Dla starszych modeli OpenAI pisze, że czas i koszt rosną z liczbą „tokenów
  obrazu”: 1024×1536 to 408 (low) / 1584 (medium) / 6240 (high).
- Kwadrat generuje się zwykle najszybciej; skomplikowany prompt może trwać do 2 minut.
- W Codexie obraz zużywa limit 3–5× szybciej niż zwykła tura, „zależnie od jakości
  i rozmiaru”.

Własnego pomiaru low vs high nie zrobiliśmy: w aplikacji nie ma przełącznika
jakości, a do API potrzebny jest płatny klucz, którego tu nie używamy.

**Decyzja w pluginie:** jakości nie obniżamy. Arkusze postaci, widoki, wzory stylu,
próbki stylów i finały — zawsze pełna jakość. Szybki szkic (ołówek, sam układ
planszy) jest tylko opcją: plugin robi go wyłącznie wtedy, gdy o to poprosisz.

## Ile to kosztuje, gdy płacisz za sztukę

Przy dużych seriach OpenAI radzi podłączyć w Codexie własny klucz API — wtedy obrazy
nie zjadają limitu planu, tylko kosztują wg cennika API. Ceny jednego obrazu
`gpt-image-2` (sam wynik, bez obrazów na wejściu):

| Jakość | 1024×1024 | 1024×1536 (pion) |
|---|---|---|
| low | 0,006 $ | 0,005 $ |
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
- Czy zwykły czat ChatGPT (poza Codexem) ma przełącznik rozmiaru albo jakości obrazu.
- Strony help.openai.com i chatgpt.com/pricing nie dały się odczytać automatycznie,
  więc nie były porównane.

## Źródła (sprawdzone 16.10.2026)

- Plany i limity Codexa, kredyty, tabela funkcji: https://learn.chatgpt.com/docs/pricing
- Obrazy w Codexie (model, referencje, edycja, klucz API): https://learn.chatgpt.com/docs/image-generation
- Rozmiary, jakość, czas i ceny obrazów w API: https://developers.openai.com/api/docs/guides/image-generation
- Brak ustawień rozmiaru i jakości we wbudowanym narzędziu: instrukcja OpenAI dla
  Codexa „imagegen” dołączona do Codexa CLI 0.162.1 (`~/.codex/skills/.system/imagegen/SKILL.md`)
- Model `gpt-image-2`: https://developers.openai.com/api/docs/models/gpt-image-2
