# Typografia

## Zasady podstawowe

- **Najwyżej dwie rodziny krojów, na plakacie trzy role:** nagłówek, tekst, drobny druk.
  Dwa kroje mają się wyraźnie różnić, inaczej wyglądają na pomyłkę.
- **Pogrubienie i kursywa rzadko, nigdy razem.** Wyróżniasz jednym sposobem naraz.
- **Kerning włączony** (przeglądarka robi to domyślnie; nie wyłączaj w CSS).
- **Wersaliki i kapitaliki** w małych stopniach potrzebują dodatkowego światła między literami,
  rzędu 5–12%. Wielkie nagłówki plakatowe składa się ciaśniej, decyzja wzrokowa.
- **Interlinia** 120–145% stopnia pisma. Dla jednowierszowego nagłówka można mniej.
- **Długość wiersza** 45–90 znaków. Na plakacie zwykle krócej.

## Hierarchia wielkości

Najwyżej trzy wielkości i najwyżej dwa duże elementy. Najważniejszy element jest 2–3 razy większy
od reszty. Jeśli dwa napisy mają podobną wielkość, wybierz, który ma wygrać.

## Fonty w tym pluginie

Tekst składa się w HTML z fontów z biblii marki, osadzonych w pliku (render nie sięga do sieci).
Generator obrazów nie zna Twoich fontów i nie gwarantuje polskich znaków, więc **tekstu nie
zamawiasz u generatora**. `check` sprawdza, czy fonty z biblii marki się wczytały (`fonts`) i czy każdy font
ma wszystkie użyte znaki (`glyphs`): ą ć ę ł ń ó ś ź ż.

## Polskie pułapki

- Spójniki jednoliterowe („i”, „w”, „z”, „a”, „o”, „u”) nie zostają na końcu wiersza. Wstaw
  twardą spację po spójniku (`&nbsp;`).
- Cudzysłów polski „tak”, nie "tak". Półpauza w przedziałach: 10–12, z kropką w godzinie 18.30 albo
  dwukropkiem, zależnie od marki, ale jednolicie.
- Data i dzień tygodnia mają się zgadzać (sprawdź w kalendarzu, nie z głowy).

## Przykład (Kiwi Studio)

Nagłówek „Wieczór z ceramiką” w kroju bezszeryfowym, wersaliki, 3 razy większy od opisu. Opis w
drugim, neutralnym kroju. Data w nagłówkowym kroju, ale o jeden stopień mniejsza. Razem trzy
wielkości i dwa duże elementy (nagłówek i data).
