# Pytania przy zakładaniu komiksu

Zadawaj po **jednym pytaniu naraz**, krótko, z gotową odpowiedzią domyślną
w nawiasie — użytkownik może napisać „tak” albo „dalej” i idziesz z domyślną.
Pytania „na start” zadajesz od razu. Pytania „później” — dopiero w kroku, który
ich potrzebuje; nie zasypuj nimi na początku.

## Na start (przed pierwszym obrazem)

| # | Pytanie | Domyślnie | Gdzie zapisujesz |
|---|---|---|---|
| 1 | Jak ma się nazywać komiks? | — (trzeba podać) | `nowy --tytul` |
| 2 | O czym jest i po co: czego ma nauczyć albo co sprzedać? | — | `biblia/ton.md` |
| 3 | Dla kogo? (wiek, kim są odbiorcy) | dorośli obserwujący profil | `biblia/ton.md` |
| 4 | Gdzie publikujesz? | Instagram | `--kanal` |
| 5 | Jeden obraz w poście czy karuzela kilku plansz? | jeden obraz | `--plansze-na-post` |
| 6 | Pion 4:5 czy kwadrat 1:1? | pion 4:5 (`1080x1350`) | `--format` |
| 7 | Jaki ton: zabawny, ciepły, ironiczny, poważny? | ciepły z humorem | `biblia/ton.md` |
| 8 | W jakim języku dialogi? | polski | `--jezyk` |
| 9 | Ile stałych postaci i kto to? (imię, rola, 1 zdanie) | 1–2 postaci | `postac` + `postac.md` |
| 10 | Czy Ty sam/sama masz być postacią? Jeśli tak — 1–2 zdjęcia (twarz z przodu i z boku). | nie | `postaci/<imię>/zdjecia/` |
| 11 | Masz przykłady stylu, które Ci się podobają? Wklej 3–5 obrazów albo nazwij profil. | nie — pokażę próbki | `projekt/inspiracje/` |

## Później, gdy będzie potrzeba

| Kiedy | Pytanie | Domyślnie |
|---|---|---|
| przy arkuszach postaci | Czy postaci mają mieć też widoki z góry i z dołu? (przydają się, jeśli będą sceny z lotu ptaka albo „z żabiej perspektywy”) | nie (`--widoki-dodatkowe gora,dol` gdy tak) |
| przy arkuszach postaci | Jakie miny będą najczęstsze? | radość, zdziwienie, złość, smutek, zamyślenie, śmiech |
| przy miejscach | Gdzie dzieje się akcja? (2–3 stałe miejsca) | jedno miejsce |
| przy kadrach | Ile kadrów na planszy? | 4 (2×2) |
| przy dymkach | Jak długie kwestie? | najwyżej 12 słów w dymku |
| przy dymkach | Czy będziesz poprawiać tekst sam w Canvie? | nie — tekst w obrazie |
| przed odcinkami | Jak często odcinek? | 1 w tygodniu (`--rytm`) |
| przed odcinkami | Czy każdy odcinek kończy się stałym elementem (puenta, rada, logo)? | puenta w ostatnim kadrze |

Po pytaniach na start powiedz jednym zdaniem, co zapisałeś, i przejdź do propozycji stylów.
Odpowiedzi można zmienić później: format, karuzela, kanał i rytm siedzą w `komiks.yaml`.
