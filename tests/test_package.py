from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_frontmatter_is_valid_and_minimal(self):
        text = (ROOT / "SKILL.md").read_text("utf-8")
        front = text.split("---", 2)[1]
        top_level = set(re.findall(r"(?m)^([a-z][a-z0-9_-]*):", front))
        self.assertEqual(top_level, {"name", "description", "license", "metadata"})
        self.assertRegex(front, r"(?m)^name:\s+ms-mks-modeling\s*$")
        version = (ROOT / "VERSION").read_text("utf-8").strip()
        self.assertRegex(front, rf'(?m)^\s+version:\s+"{re.escape(version)}"\s*$')
        description_lines = []
        capture = False
        for line in front.splitlines():
            if line.startswith("description:"):
                capture = True
                continue
            if capture and re.match(r"^[a-z][a-z0-9_-]*:", line):
                break
            if capture:
                description_lines.append(line.strip())
        self.assertLessEqual(len(" ".join(description_lines)), 1024)

    def test_runtime_references_are_linked_and_exist(self):
        text = (ROOT / "SKILL.md").read_text("utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        expected = {
            "references/research_design.md",
            "references/formal_validation.md",
            "references/evidence_policy.md",
            "references/feedback_and_decisions.md",
            "references/retrieval_contract.md",
            "templates/current_model.md",
        }
        self.assertTrue(expected.issubset(set(links)))
        self.assertTrue(all((ROOT / link).is_file() for link in links))

    def test_package_contains_only_intended_long_term_files(self):
        files = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file()
            and not {"__pycache__", ".pytest_cache"}.intersection(path.parts)
            and path.suffix != ".pyc"
            and path.name != ".coverage"
            and not path.name.startswith("coverage.")
        }
        expected = {
            ".gitignore",
            "LICENSE",
            "README.md",
            "SKILL.md",
            "VERSION",
            "references/evidence_policy.md",
            "references/feedback_and_decisions.md",
            "references/formal_validation.md",
            "references/research_design.md",
            "references/retrieval_contract.md",
            "scripts/local_evidence_retrieval.py",
            "templates/current_model.md",
            "tests/test_local_evidence_retrieval.py",
            "tests/test_package.py",
        }
        self.assertEqual(files, expected)

    def test_no_legacy_or_development_language_in_runtime(self):
        runtime = "\n".join(
            (ROOT / rel).read_text("utf-8")
            for rel in [
                "SKILL.md",
                "references/research_design.md",
                "references/formal_validation.md",
                "references/evidence_policy.md",
                "references/feedback_and_decisions.md",
                "references/retrieval_contract.md",
            ]
        )
        for token in ["v0.1", "v0.2", "rc7", "PRODUCT SPEC", "MKS_PROCESS_ROOT_NAMES"]:
            self.assertNotIn(token, runtime)


if __name__ == "__main__":
    unittest.main()
