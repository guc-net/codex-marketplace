"""Testy procedur (skills) pluginu graphic-designer."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent / "plugins" / "graphic-designer"
SKILLS = PLUGIN / "skills"
NAMES = ("graphic-designer", "design-job", "brand-kit", "design-review")
REQUEST_WORDS = ("Plakat", "Grafika", "Ocena", "Biblia", "Start")


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


if __name__ == "__main__":
    unittest.main()
