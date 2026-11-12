"""Testy procedur (skills) pluginu graphic-designer."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "graphic-designer"
SKILLS = PLUGIN / "skills"
NAMES = ("graphic-designer", "design-job", "brand-kit", "design-review", "setup")
REQUEST_WORDS = ("Zaprojektuj", "Plakat", "Grafika", "Ocena", "Biblia", "Start", "Skonfiguruj")


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, path
    return dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)


class SkillsCase(unittest.TestCase):
    def test_all_skills_exist(self):
        for name in NAMES:
            path = SKILLS / name / "SKILL.md"
            self.assertTrue(path.is_file(), name)
            self.assertEqual(frontmatter(path)["name"], name)

    def test_descriptions_start_with_request_words(self):
        for name in NAMES:
            desc = frontmatter(SKILLS / name / "SKILL.md")["description"]
            self.assertTrue(desc.startswith(REQUEST_WORDS), f"{name}: {desc[:40]}")
            self.assertGreater(len(desc), 40)

    def test_referenced_files_exist(self):
        pattern = r"`((?:\.\./[\w-]+/)?references/[\w-]+\.md)`"
        total = 0
        for name in NAMES:
            skill = SKILLS / name / "SKILL.md"
            for ref in re.findall(pattern, skill.read_text(encoding="utf-8")):
                total += 1
                self.assertTrue((skill.parent / ref).is_file(), f"{name}: brak {ref}")
        self.assertGreater(total, 5)

    def test_no_bare_reference_names(self):
        """Wiedza tylko jako references/<x>.md (ruling R2), nigdy goły plik w backtickach."""
        bare = ("critique", "typography", "color", "composition", "poster", "formats", "print",
                "logo", "image-prompting", "generic-ai-tells")
        for name in NAMES:
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            for b in bare:
                self.assertNotRegex(text, rf"`{b}\.md`", f"{name}: goły {b}.md")

    def test_skill_size(self):
        for name in NAMES:
            lines = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8").count("\n")
            self.assertLess(lines, 500, name)

    def test_commands_and_flags_exist_in_script(self):
        """Każde polecenie i flaga w blokach `DESIGNER ...` istnieje w skrypcie."""
        script = (PLUGIN / "scripts" / "designer.py").read_text(encoding="utf-8")
        commands = set(re.findall(r'add_parser\(\s*"([\w-]+)"', script))
        flags = set(re.findall(r'add_argument\(\s*"(--[\w-]+)"', script))
        self.assertIn("render", commands)
        for name in NAMES:
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            for cmd in re.findall(r"`DESIGNER ([a-z][\w-]*)", text):
                self.assertIn(cmd, commands, f"{name}: {cmd}")
            for line in re.findall(r"`DESIGNER [^`]*", text):
                for flag in re.findall(r"(?<![\w-])(--[a-z][\w-]*)", line):
                    self.assertIn(flag, flags | {"--help"}, f"{name}: {flag}")

    def test_key_rules_encoded(self):
        job = (SKILLS / "design-job" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("Nie zmieniam:", "Zmieniam tylko:", "freeze", "check", "finalize", "Kiwi Studio"):
            self.assertIn(phrase, job)
        entry = (SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("update-check", "env", "Graphics-work", "OPENAI_API_KEY"):
            self.assertIn(phrase, entry)

    def test_sandbox_handling_in_entry_skill(self):
        entry = (SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("BROWSER-TEST: FAILED", "SANDBOX?:", "poza piaskownicą", "jednorazową zgodę",
                       "ImageMagick", "Zakaz", "nie przechodź po cichu",
                       "nie dostarczaj", "kierunki i szkice"):
            self.assertIn(phrase, entry)
        for cmd in ("`render`", "`check`", "`env`", "`update-check`"):
            self.assertIn(cmd, entry)

    def test_network_permission_is_explicit_step(self):
        entry = (SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8")
        block = entry[entry.index("`NIE SPRAWDZONO`"):entry.index("**Środowisko**")]
        self.assertIn("nie pomijaj tego po cichu", block)
        for n in ("1.", "2.", "3."):
            self.assertIn(n, block)
        self.assertIn("zgodę", block)

    def test_library_not_changed_without_asking(self):
        entry = (SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Biblioteki nie zmieniasz sam", entry)
        self.assertIn("GD_HOME", entry)
        self.assertIn("nie zakładaj drugiej", entry)
        self.assertIn("zgodę na zapis", entry)

    def test_mandatory_order_in_design_job(self):
        job = (SKILLS / "design-job" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Obowiązkowa kolejność", job)
        head = job[job.index("## Obowiązkowa kolejność"):job.index("## Kto co robi")]
        positions = [head.index(w) for w in ("**Brief**", "**Kierunki", "**`choose`**", "Etapy z `draft`",
                                             "**`render`**", "**`check`**", "**Samoocena**",
                                             "**Lista do sprawdzenia", "**Dopiero potem pokaz**")]
        self.assertEqual(positions, sorted(positions))
        # „Obowiązkowa kolejność” jest przed resztą procedury
        self.assertLess(job.index("## Obowiązkowa kolejność"), job.index("## 1. Zlecenie"))

    def test_topic_format_date_request_is_not_finished_look(self):
        job = (SKILLS / "design-job" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("tylko temat, format i datę", job)
        self.assertIn("**nie** jest takim opisem", job)
        self.assertIn("2–4", job)
        self.assertIn("zaproponuj trzy kierunki i zatrzymaj się", job)

    def test_generated_images_go_through_draft_and_freeze(self):
        job = (SKILLS / "design-job" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("przejść przez `draft`", job)
        self.assertIn("zamrożony przez `freeze`", job)
        self.assertIn("nie kopiuj go do `layers/` ręcznie", job)
        self.assertIn("bez `check` z wynikiem `OK`", job)
        self.assertIn("nie składaj grafiki innym", job)
        self.assertIn("do sprawdzenia przez człowieka", job)

    def test_layperson_trigger_words_open_the_two_main_descriptions(self):
        for name in ("graphic-designer", "design-job"):
            desc = frontmatter(SKILLS / name / "SKILL.md")["description"]
            self.assertTrue(desc.startswith("Zaprojektuj plakat, post, relację"), f"{name}: {desc[:50]}")

    def test_intro_block_in_entry_skill(self):
        raw = (SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8")
        entry = " ".join(raw.split())
        self.assertIn("Pierwsza odpowiedź w rozmowie o grafice", entry)
        for part in ("Jak pracujemy:", "kilka pytań o zlecenie,",
                     "trzy kierunki do wyboru (zatrzymam się i poczekam na Twoją decyzję),",
                     "dopracowanie wybranego etapami,", "złożenie i automatyczna kontrola,",
                     "gotowe pliki do Twojej akceptacji — niczego nie publikuję."):
            self.assertIn(part, entry)
        self.assertIn("raz na rozmowę", entry)

    def test_intro_block_is_a_real_markdown_list(self):
        """Każda pozycja wprowadzenia w osobnej linii (błąd z testu 12.11.2026: pozycje się sklejały)."""
        raw = (SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8")
        start = raw.index("**Jak pracujemy:**")
        block = raw[start:raw.index("```", start)].strip().splitlines()
        self.assertEqual(block[0], "**Jak pracujemy:**")
        self.assertEqual(block[1], "")
        items = block[2:]
        self.assertEqual(len(items), 5)
        for n, line in enumerate(items, 1):
            self.assertTrue(line.startswith(f"{n}. "), line)
            self.assertEqual(len(re.findall(r"\d\)", line)), 0, line)

    def test_formatting_rules_in_entry_skill(self):
        entry = " ".join((SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("## Jak formatujesz odpowiedzi", entry)
        self.assertIn("w osobnej linii", entry)
        self.assertIn("pustą linię", entry)

    def test_final_answer_has_four_parts_and_off_brand_needs_consent(self):
        job = " ".join((SKILLS / "design-job" / "SKILL.md").read_text(encoding="utf-8").split())
        for part in ("**Plik:**", "**Kontrola automatyczna:**", "**Samoocena:**",
                     "**Do sprawdzenia przez człowieka:**", "tylko link do pliku nie spełnia"):
            self.assertIn(part, job)
        self.assertIn("najpierw szukaj rozwiązania **w obrębie marki**", job)
        self.assertIn("czekaj na „tak”", job)

    def test_failed_browser_test_without_sandbox_marker_is_neutral(self):
        entry = " ".join((SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("nie twierdź, że to piaskownica", entry)
        self.assertIn("nieznanej przyczyny", entry)

    def test_choose_in_design_job_order(self):
        job = (SKILLS / "design-job" / "SKILL.md").read_text(encoding="utf-8")
        head = job[job.index("## Obowiązkowa kolejność"):job.index("## Kto co robi")]
        self.assertLess(head.index("Kierunki + STOP"), head.index("`choose`"))
        self.assertLess(head.index("`choose`"), head.index("Etapy z `draft` i `freeze`"))
        self.assertIn("DESIGNER choose --job <slug> --direct", job)
        self.assertIn("DESIGNER choose --job <slug> --direction", job)
        self.assertIn("process", head)

    def test_no_claim_that_stage_stays_brief(self):
        job = (SKILLS / "design-job" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("zostaje wtedy", job)
        self.assertIn("nie jest zamrożona", job)

    def test_refusal_means_no_final_file_in_design_job(self):
        job = (SKILLS / "design-job" / "SKILL.md").read_text(encoding="utf-8")
        job = " ".join(job.split())
        self.assertIn("Przy odmowie zgody nie ma pliku ostatecznego", job)
        self.assertIn("Po pokazie złożonej grafiki wypisz listę", job)

    def test_seatbelt_skip_handling_in_entry_skill(self):
        entry = " ".join((SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8").split())
        for phrase in ("BROWSER-TEST: SKIPPED", "zapamiętać tę decyzję", "CVDisplayLink", "allocator",
                       "quit unexpectedly", "Ignore", "wbudowanej przeglądarki aplikacji", "file://"):
            self.assertIn(phrase, entry)

    def test_skill_explains_forcing_the_browser(self):
        entry = " ".join((PLUGIN / "skills" / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("GD_BROWSER_TRY=1 python3", entry)

    def test_seatbelt_docs_and_changelog(self):
        docs = " ".join((PLUGIN.parent.parent / "docs" / "graphic-designer.md").read_text(encoding="utf-8").split())
        for phrase in ("quit unexpectedly", "Ignore", "Po zgodzie Chrome działa", "11.11.2026", "file://"):
            self.assertIn(phrase, docs)
        log = (PLUGIN / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("plugin nie uruchamia przeglądarki", log)

    def test_setup_description_has_trigger_words(self):
        desc = frontmatter(SKILLS / "setup" / "SKILL.md")["description"]
        self.assertTrue(desc.startswith("Skonfiguruj graphic-designer"), desc[:40])
        for word in ("pierwsze uruchomienie", "konfiguracja", "ustaw", "reguły", "uprawnienia", "doctor",
                     "zgodę przy każdym składaniu grafiki", "piaskownicy", "macOS"):
            self.assertIn(word, desc)

    def test_setup_flow_and_consent(self):
        text = " ".join((SKILLS / "setup" / "SKILL.md").read_text(encoding="utf-8").split())
        for phrase in ("`DESIGNER doctor`", "`DESIGNER setup-launcher`", "`DESIGNER setup-rules`",
                       "`DESIGNER setup-rules --apply`", "`DESIGNER setup-rules --remove`",
                       "`DESIGNER library --set <folder>`",
                       # zgoda przed zapisem
                       "Nigdy nie zapisujesz reguł bez wyraźnej zgody", "Czy dopisać te reguły?",
                       "Dopiero po wyraźnym „tak”", "dokładny tekst bloku",
                       # tylko dopisywanie
                       "dopisuje na końcu pliku reguł", "ręczne zmiany w środku bloku znikają", "Nie zmieniasz niczego innego",
                       "reszty pliku nie ruszasz",
                       # restart i cofnięcie
                       "Codex czyta reguły tylko przy starcie", "Zamknij aplikację całkiem",
                       "nową rozmowę", "Cofnięcie", "# >>> graphic-designer",
                       # Terminal, gdy zapis się nie uda
                       "dokładne polecenie do Terminala",
                       # zgoda także na plik startowy, kopia zapasowa
                       "To samo dotyczy pliku startowego", "Czy mogę?", "default.rules.graphic-designer.bak",
                       # model i biblioteka
                       "gpt-6.1-sol", "Medium", "/model", "Graphics-work"):
            self.assertIn(phrase, text)
        self.assertLess(text.index("Czy dopisać te reguły?"), text.index("`DESIGNER setup-rules --apply`"))

    def test_setup_explains_the_three_options_and_the_tradeoff(self):
        text = " ".join((SKILLS / "setup" / "SKILL.md").read_text(encoding="utf-8").split())
        block = text[text.index("trzy możliwości"):text.index("Krok 3a")]
        for phrase in ("Reguły tylko dla pięciu poleceń pluginu — zalecane, ale z zastrzeżeniami",
                       "Szerszy tryb w aplikacji", "Approve for me",
                       "Full access", "w całej rozmowie, nie tylko dla pluginu", "kompromis",
                       "Zgoda za każdym razem", "Nic się nie zapisuje",
                       # uczciwie o tym, co reguła pozwala (przegląd 0.2.0, C1)
                       "reguła sprawdza tylko początek polecenia", "nie jest ograniczone",
                       "bez skryptów, bez sieci, bez ramek",
                       "dowolny plik graficzny z dysku", "otwieraj tylko zlecenia, którym ufasz"):
            self.assertIn(phrase, block)
        self.assertLess(block.index("Reguły tylko dla pięciu poleceń"), block.index("Szerszy tryb"))
        self.assertLess(block.index("Szerszy tryb"), block.index("Zgoda za każdym razem"))

    def test_setup_says_what_it_cannot_do(self):
        text = " ".join((SKILLS / "setup" / "SKILL.md").read_text(encoding="utf-8").split())
        for phrase in ("Nie umiem zmienić ustawień aplikacji", "Ustawienia → Browser", "file://",
                       "11.11.2026", "mogą się różnić"):
            self.assertIn(phrase, text)

    def test_setup_is_plain_language(self):
        text = (SKILLS / "setup" / "SKILL.md").read_text(encoding="utf-8")
        for jargon in ("deploy", "commit", "repozytorium"):
            self.assertNotIn(jargon, text.lower())

    def test_entry_skill_uses_the_launcher_with_the_absolute_path(self):
        entry = " ".join((SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8").split())
        for phrase in ("Stały skrypt startowy", "Polecenie do uruchamiania", "pełnej postaci",
                       "<CODEX_HOME albo ~/.codex>/graphic-designer/designer.py",
                       "przed `python3` nie wolno nic dopisywać", "`~` ani `$HOME`",
                       "ścieżki z folderu pluginu", "GD_BROWSER_TRY=1 python3"):
            self.assertIn(phrase, entry)

    def test_entry_skill_offers_setup_once_before_work(self):
        entry = " ".join((SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8").split())
        phrase = "Skonfigurować to raz, żeby Codex nie pytał o zgodę przy każdym składaniu grafiki?"
        self.assertIn(phrase, entry)
        self.assertIn("raz, przed rozpoczęciem pracy", entry)
        self.assertIn("nie pytaj drugi raz w tej rozmowie", entry)
        self.assertIn("Skonfiguruj graphic-designer", entry)
        self.assertIn("procedura **setup**", entry)
        # konfiguracja jest przed krokami startowymi, a odmowa nie blokuje pracy
        self.assertLess(entry.index(phrase), entry.index("1. **Aktualizacja**"))
        self.assertIn("pracuj dalej", entry[entry.index(phrase):entry.index("1. **Aktualizacja**")])

    def test_reference_path_rule_still_holds(self):
        entry = (SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`references/brief.md`", entry)
        self.assertIn("Wiedza projektanta leży w `references/`", entry)

    def test_manifest_runs_the_setup_skill_after_install(self):
        import json
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        path = manifest["extensions"]["com.openai"]["onboardingSkill"]
        self.assertEqual(path, "./skills/setup/SKILL.md")
        self.assertTrue((PLUGIN / path).is_file())

    def test_setup_docs_explain_what_it_does_and_how_to_undo(self):
        docs = " ".join((PLUGIN.parent.parent / "docs" / "graphic-designer.md").read_text(encoding="utf-8").split())
        readme = " ".join((PLUGIN / "README.md").read_text(encoding="utf-8").split())
        for phrase in ("Co robi konfiguracja i jak ją cofnąć", "Skonfiguruj graphic-designer",
                       "Czy dopisać te reguły?", "# >>> graphic-designer (zarządzane przez plugin) >>>",
                       "# <<< graphic-designer <<<", "poza piaskownicą i bez pytania o zgodę",
                       "setup-rules --remove", "default.rules", "CODEX_HOME", "GD_HOME",
                       "Codex czyta reguły tylko przy starcie", "Approve for me", "Full access",
                       "usługi okien", "11.11.2026", "nie zawiera numeru wersji",
                       # nowe miejsce pliku, kopia zapasowa, uczciwie o regule (przegląd 0.2.0)
                       "~/.codex/graphic-designer/designer.py", "default.rules.graphic-designer.bak",
                       "Reguła dopasowuje tylko początek polecenia", "dowolny plik graficzny z dysku",
                       "otwieraj tylko zlecenia, którym ufasz", "GD_UPDATE_SOURCE",
                       "ręczne zmiany w środku bloku znikają"):
            self.assertIn(phrase, docs)
        for phrase in ("Skonfiguruj graphic-designer", "Co robi konfiguracja i jak ją cofnąć",
                       "`doctor`", "`setup-launcher`", "`setup-rules`"):
            self.assertIn(phrase, readme)

    def test_nothing_is_called_narrow_without_qualification(self):
        """Reguła pozwala uruchamiać poza piaskownicą z dowolnymi argumentami: żadnego „wąskie”."""
        files = [PLUGIN / "README.md", PLUGIN / "CHANGELOG.md", PLUGIN.parent.parent / "docs" / "graphic-designer.md"]
        files += sorted(SKILLS.glob("*/SKILL.md"))
        for f in files:
            text = f.read_text(encoding="utf-8").lower()
            self.assertNotIn("wąsk", text, f)
            self.assertNotIn("narrow", text, f)

    def test_skills_say_procedure_not_skill(self):
        for f in sorted(SKILLS.glob("*/SKILL.md")):
            text = f.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"\bskill(u|a|e|i|ach)?\b", f)

    def test_launcher_location_is_the_codex_folder_everywhere(self):
        """Stary adres pliku startowego może wystąpić tylko jako opis migracji."""
        docs = (PLUGIN.parent.parent / "docs" / "graphic-designer.md").read_text(encoding="utf-8")
        readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
        entry = (SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8")
        for name, text in (("docs", docs), ("README", readme), ("entry", entry)):
            self.assertNotIn("GD_HOME albo ~/.graphic-designer>/designer.py", text, name)
            self.assertNotIn("python3 ~/.graphic-designer/designer.py", text, name)
        self.assertIn("python3 ~/.codex/graphic-designer/designer.py setup-rules --remove", docs)

    def test_setup_asks_before_installing_the_launcher(self):
        text = " ".join((SKILLS / "setup" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertLess(text.index("Czy mogę?"), text.index("uruchom `DESIGNER setup-launcher`"))

    def test_version_is_consistent_and_changelog_is_folded(self):
        import json
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        version = tuple(int(n) for n in manifest["version"].split("."))
        self.assertGreaterEqual(version, (0, 2, 0))
        table = (PLUGIN.parent.parent / "README.md").read_text(encoding="utf-8")
        row = [l for l in table.splitlines() if l.startswith("| [graphic-designer]")][0]
        self.assertTrue(row.rstrip().endswith(f"| {manifest['version']} |"), row)
        log = (PLUGIN / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^## 0\.2\.0 ", log, re.M)), 1)
        self.assertNotRegex(log, r"(?m)^## 0\.1\.1")
        self.assertIn("plugin nie uruchamia przeglądarki", log)


if __name__ == "__main__":
    unittest.main()
