# guc-net — pluginy do Codexa

Marketplace pluginów do **Codexa** (w aplikacji desktopowej ChatGPT i w Codex CLI).
Jedno repozytorium, wiele pluginów: dodajesz je raz, a kolejne pluginy i ich nowe
wersje przychodzą z tego samego miejsca.

| Plugin | Co robi | Wersja |
|---|---|---|
| [komiks](plugins/komiks/) | Pracownia komiksu ze stałymi postaciami: biblia stylu i postaci z zatwierdzanymi zmianami, odcinki z wersjami plansz, strona HTML | 0.1.0 |

## Instalacja

Krok po kroku, ze zrzutami: [docs/instalacja.md](docs/instalacja.md).
W skrócie (terminal albo poproś o to Codexa):

```
codex plugin marketplace add guc-net/codex-marketplace
codex plugin add komiks@guc-net
```

Potem uruchom ponownie aplikację ChatGPT i zacznij nową rozmowę w Codexie.

## Aktualizacja

Plugin sam mówi na początku rozmowy, że jest nowa wersja, i pyta, czy zaktualizować.
Ręcznie:

```
codex plugin marketplace upgrade guc-net
```

## Dla twórców

```
.agents/plugins/marketplace.json   # katalog pluginów (nazwa marketplace: guc-net)
plugins/<plugin>/plugin.json       # manifest (format Agent Plugins + extensions.com.openai)
plugins/<plugin>/skills/*/SKILL.md # skille
plugins/<plugin>/CHANGELOG.md      # „co nowego” — czyta go plugin przy aktualizacji
tests/                             # python -m unittest discover -s tests
```

Wydanie: podbij `version` w `plugin.json`, dopisz sekcję na górze `CHANGELOG.md`
(pierwsza sekcja musi mieć tę samą wersję — pilnuje tego test), scal do `main`,
otaguj `<plugin>-v<wersja>` i utwórz wydanie na GitHubie. Użytkownicy dostają wersję
z `main` (tak działa `marketplace upgrade`), więc **`main` = wydana wersja**.

Licencja: MIT.
