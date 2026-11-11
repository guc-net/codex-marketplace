# Przygotowanie do druku

Wymagania różnią się między drukarniami. **Czytaj specyfikację wybranej drukarni** i jej wartości
stawiaj ponad tym plikiem.

## Typowe wymagania

- **Spad 3 mm z każdej strony.** Tło i obrazy wychodzą poza format cięcia, żeby po przycięciu nie
  została biała krawędź. Spad to tło wysunięte poza format, nie rozciągnięty projekt.
- **Marginesy wewnętrzne** co najmniej 3 mm od linii cięcia dla tekstu i logo (w formatach
  `a4-print` i `a3-print` strefa bezpieczna wynosi 71 px, czyli ok. 6 mm przy 300 dpi).
- **Rozdzielczość** 300 dpi w skali 1:1 dla zdjęć (część drukarni przyjmuje 250–350).
- **Kolor:** drukarnie pracują w CMYK. Ekranowe RGB przy konwersji traci nasycenie.
- **Fonty** zamienione na krzywe albo osadzone w PDF.
- **PDF** bez hasła, w wersji podanej przez drukarnię. Znaczniki cięcia poza spadem, jeśli drukarnia
  o nie prosi.

## Co robi plugin, a czego nie

`render` buduje PNG i PDF o wymiarach ze spadem (strona 216×303 mm dla A4). To plik z ekranowym RGB.
**Nie konwertuje na CMYK** i nie dodaje znaczników cięcia. Przed wysłaniem do drukarni człowiek
sprawdza plik, a konwersję robi drukarnia albo program graficzny.

## Neony i kolory poza zakresem CMYK

Jaskrawe zielenie, róże i pomarańcze z ekranu często nie istnieją w CMYK. Wtedy:
- pokaż klientowi, jak zmieni się wygląd (zwykle wyblaknie),
- zapytaj drukarnię o farbę dodatkową (fluorescencyjną, kolor z wzornika), droższą, bo to osobna forma,
- numer wzornika uzgadnia drukarnia, bo wzornik nigdy nie jest identyczny z kolorem ekranu.

## Lista do sprawdzenia przez człowieka

Teksty i data, adres i kod QR (czy prowadzi, gdzie trzeba), prawa do zdjęć i zgoda osób na
zdjęciu, specyfikacja drukarni, korekta na papierze, jeśli nakład jest duży.
