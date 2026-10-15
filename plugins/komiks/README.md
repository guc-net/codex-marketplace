# Plugin „komiks”

Pracownia komiksu w Codexie. Komiks to folder na Twoim dysku:

```
Komiksy/                     ← ten folder otwierasz w Codexie
  AGENTS.md
  moj-komiks/
    komiks.yaml              ← tytuł, format posta, kolory strony
    biblia/                  ← styl, postaci, miejsca, kadry, dymki (wersja w WERSJA)
    zmiany/                  ← dziennik zmian biblii (propozycja / zatwierdzona / odrzucona)
    historia-biblii/v1, v2…  ← zamrożone wersje biblii
    odcinki/001-…/           ← scenariusz, wersje/v1, v2… z promptami, final/
    strona/index.html        ← strona komiksu (budowana od zera, nie edytuj ręcznie)
```

Skille: `komiks` (start rozmowy, aktualizacje), `komiks-projekt` (biblia krok po kroku),
`komiks-odcinek` (scenariusz → plansze → final → strona), `komiks-zmiana` (zmiana biblii
tylko po „TAK”).

Narzędzie: `scripts/komiks.py` — czysty Python 3.9+, bez doinstalowywania bibliotek.
`python3 scripts/komiks.py --help` pokazuje polecenia.

Ustawienia, które zależą od Twoich decyzji (format 4:5 czy 1:1, karuzela, tryb dymków,
kolory strony), siedzą w `komiks.yaml` — zmiana decyzji = zmiana jednego pliku.

Jak zacząć: [../../docs/jak-zaczac.md](../../docs/jak-zaczac.md).
