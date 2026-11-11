# Generator obrazów: jak pisać polecenia

Generator (wbudowany w Codexa) służy do **tła, tekstury, ilustracji, zdjęcia i szkiców kierunków**.
Napisy, logo i układ składasz osobno, w HTML. Generator ma ograniczoną precyzję tekstu, położenia
i powtarzalności elementów marki.

## Stały blok stylu

Zapisz raz kilka zdań opisujących styl marki (materiał, światło, paleta, nastrój, czego nie robić)
i **wklejaj go dosłownie do każdego polecenia**, bez zmian. Zmiana słów to zmiana stylu.

Przykład (Kiwi Studio): „Ciepłe światło dzienne, miękkie cienie, surowa glina i drewno, paleta
zieleni i kremu, bez ludzi w kadrze, bez napisów, bez logo.”

## Obrazy wzorcowe i ich role

Dołączasz do 5 obrazów. Każdemu przypisz rolę numerem: „Obraz 1 to szkic układu, obraz 2 to
zdjęcie wnętrza jako wzór światła. Nie kopiuj układu z obrazu 2.” Bez ról model sam zgaduje,
co z czym zrobić.

## Jedna zmiana na turę

Przy poprawkach zmieniaj jedną rzecz, inaczej reszta się rozjeżdża. Zawsze dwie listy:

```
Nie zmieniam: kadr, światło, kolory, układ, zawartość na stole.
Zmieniam tylko: filiżankę po lewej na kubek z uchem.
```

Powtarzaj listę „Nie zmieniam” w każdej turze. „Jak wcześniej” nie działa, model nie pamięta
dokładnie.

## Poprzednia wersja jako wejście

Do poprawki dołączasz **zatwierdzoną wersję**, nie pierwszy szkic. Zatwierdzoną wersję zapisz
w zleceniu (`draft`, potem `freeze`). Jeśli jakaś część ma zostać identyczna co do piksela,
złóż zatwierdzony fragment z oryginałem poza generatorem, nie proś go o to.

## Tekst na obrazie

Zwykle wcale: napisy daje HTML. Wyjątek: napis jest elementem rysunku (szyld w zdjęciu). Wtedy
podaj go **w cudzysłowie**, ile razy ma się pojawić, „bez żadnego innego tekstu”, a nietypowe słowa
przeliterowane. Sprawdź każdą literę i polskie znaki.

## Przezroczyste tło

Poproś o przezroczyste tło wprost („na przezroczystym tle, sam obiekt”). **Szachownica narysowana
na obrazie nie jest przezroczystością.** Sprawdź w pliku kanał alfa (czy narożniki mają alfa 0).
Jeśli nie ma, poproś o jednolite tło w kolorze, którego nie ma w obiekcie, i wytnij je lokalnie.

## Proporcje słowami

Codex nie ma pola na rozmiar w pikselach. Mów słowami: „pionowo, proporcje jak w plakacie 4:5”,
„szeroko, jak okładka, 1,9:1”, „kwadrat”. Docelowe wymiary ustalasz potem przy składaniu w HTML,
więc zostaw zapas na kadrowanie (ważne rzeczy w środku).

## O co NIE prosić generatora

- **Logo i znaków marki.** Narysuje je po swojemu. Wstawiasz plik z biblii marki.
- **Prawdziwych twarzy konkretnych osób.** Nie odtworzy ich wiernie, a to kwestia zgody i praw.
  Używasz zdjęć dostarczonych przez zlecającego.
- **Tekstów informacyjnych:** daty, adresu, ceny, kodu QR. Błędy są cicho i trudno je zauważyć.
- **Dokładnego układu** („tytuł 120 px od lewej”). Układ robisz w HTML.

## Sprawdzenie po każdej turze

Czy zmieniło się tylko to, o co prosiłeś? Czy napisy (jeśli są) są poprawne? Czy kształty
zatwierdzonych elementów są nienaruszone? Czy plik ma prawdziwą przezroczystość, jeśli jej chciałeś?
Zapisz polecenie dosłownie razem z wersją (`draft --prompt`).
