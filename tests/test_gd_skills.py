"""Testy procedur (skills) pluginu graphic-designer."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "graphic-designer"
SKILLS = PLUGIN / "skills"
NAMES = ("graphic-designer", "design-job", "brand-kit", "design-review")
REQUEST_WORDS = ("Zaprojektuj", "Plakat", "Grafika", "Ocena", "Biblia", "Start")


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, path
    return dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)


class SkillsCase(unittest.TestCase):
    def test_four_skills_exist(self):
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
        entry = " ".join((SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("Pierwsza odpowiedź w rozmowie o grafice", entry)
        for part in ("Jak pracujemy:", "1) kilka pytań o zlecenie,",
                     "2) trzy kierunki do wyboru (zatrzymam się i poczekam na Twoją decyzję),",
                     "3) dopracowanie wybranego etapami,", "4) złożenie i automatyczna kontrola,",
                     "5) gotowe pliki do Twojej akceptacji — niczego nie publikuję."):
            self.assertIn(part, entry)
        self.assertIn("raz na rozmowę", entry)
        block = (SKILLS / "graphic-designer" / "SKILL.md").read_text(encoding="utf-8")
        block = block[block.index("Jak pracujemy:"):]
        self.assertLessEqual(len(block[:block.index("```")].strip().splitlines()), 4)

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


if __name__ == "__main__":
    unittest.main()
