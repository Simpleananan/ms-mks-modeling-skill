from pathlib import Path
import hashlib
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackageStructureTests(unittest.TestCase):

    def test_skill_frontmatter_agent_skills_constraints(self):
        text = (ROOT / "SKILL.md").read_text("utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---", 2)[1]
        name = re.search(r"(?m)^name:\s*(.+?)\s*$", frontmatter).group(1)
        description = re.search(r"(?m)^description:\s*(.+?)\s*$", frontmatter).group(1)
        self.assertRegex(name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(name), 64)
        self.assertTrue(description.strip())
        self.assertLessEqual(len(description), 1024)
        self.assertIn("license: LICENSE", frontmatter)
        self.assertIn("compatibility:", frontmatter)
        version = (ROOT / "VERSION").read_text("utf-8").strip()
        self.assertIn(f'version: "{version}"', frontmatter)
        compatibility_match = re.search(r"(?m)^compatibility:\s*(.+?)\s*$", frontmatter)
        if compatibility_match:
            self.assertLessEqual(len(compatibility_match.group(1)), 500)


    def test_version_markers_are_synchronized(self):
        version = (ROOT / "VERSION").read_text("utf-8").strip()
        skill = (ROOT / "SKILL.md").read_text("utf-8")
        readme = (ROOT / "README.md").read_text("utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text("utf-8")
        release = (ROOT / "docs" / "RELEASE_VALIDATION.md").read_text("utf-8")
        self.assertIn(f'version: "{version}"', skill)
        self.assertIn(version, readme)
        self.assertIn(f"## v{version}", changelog)
        self.assertIn(version, release)

    def test_readme_uses_current_codex_local_skill_location(self):
        readme = (ROOT / "README.md").read_text("utf-8")
        self.assertIn(".agents/skills", readme)
        self.assertNotIn("git clone https://github.com/Simpleananan/ms-mks-modeling-skill.git ~/.codex/skills", readme)

    def test_relative_markdown_links_exist(self):
        link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        missing = []
        for path in ROOT.rglob("*.md"):
            text = path.read_text("utf-8")
            for match in link_re.finditer(text):
                target = match.group(1).strip()
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = target.split("#", 1)[0]
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    missing.append((path.relative_to(ROOT).as_posix(), target))
        self.assertEqual(missing, [])

    def test_manifest_matches_packaged_files(self):
        manifest = ROOT / "MANIFEST.sha256"
        self.assertTrue(manifest.is_file())
        listed = {}
        for line in manifest.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            digest, rel = line.split("  ", 1)
            rel = rel.removeprefix("./")
            listed[rel] = digest
        actual = {}
        for path in ROOT.rglob("*"):
            if not path.is_file() or path == manifest:
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            rel = path.relative_to(ROOT).as_posix()
            actual[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(set(listed), set(actual))
        self.assertEqual(listed, actual)


    def test_skill_doctor_accepts_matching_discovery_folder(self):
        with tempfile.TemporaryDirectory() as td:
            skills_root = Path(td)
            install = skills_root / "ms-mks-modeling"
            install.mkdir()
            (install / "SKILL.md").write_text(
                "---\nname: ms-mks-modeling\ndescription: test\n---\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "python",
                    str(ROOT / "scripts" / "skill_doctor.py"),
                    "--skills-root",
                    str(skills_root),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS: exactly one", result.stdout)

    def test_skill_doctor_warns_on_folder_name_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            skills_root = Path(td)
            install = skills_root / "ms-mks-modeling-skill"
            install.mkdir()
            (install / "SKILL.md").write_text(
                "---\nname: ms-mks-modeling\ndescription: test\n---\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "python",
                    str(ROOT / "scripts" / "skill_doctor.py"),
                    "--skills-root",
                    str(skills_root),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("folder name", result.stdout)


    def test_skill_doctor_default_uses_current_user_location(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / "home"
            cwd = Path(td) / "work"
            install = home / ".agents" / "skills" / "ms-mks-modeling"
            install.mkdir(parents=True)
            cwd.mkdir()
            (install / "SKILL.md").write_text(
                "---\nname: ms-mks-modeling\ndescription: test\n---\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)
            result = subprocess.run(
                ["python", str(ROOT / "scripts" / "skill_doctor.py")],
                cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS: exactly one current", result.stdout)

    def test_skill_doctor_flags_legacy_user_location(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / "home"
            cwd = Path(td) / "work"
            install = home / ".codex" / "skills" / "ms-mks-modeling"
            install.mkdir(parents=True)
            cwd.mkdir()
            (install / "SKILL.md").write_text(
                "---\nname: ms-mks-modeling\ndescription: test\n---\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)
            result = subprocess.run(
                ["python", str(ROOT / "scripts" / "skill_doctor.py")],
                cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("legacy", result.stdout.lower())
            self.assertIn(".agents", result.stdout)

    def test_single_runtime_skill(self):
        skills = list(ROOT.rglob("SKILL.md"))
        self.assertEqual(
            [p.relative_to(ROOT).as_posix() for p in skills],
            ["SKILL.md"],
        )

    def test_preserved_full_workflow_sections(self):
        text = (ROOT / "references" / "modeling_and_validation.md").read_text("utf-8")
        for heading in [
            "## Orientation from incomplete prompts",
            "## Target-paper reconstruction",
            "## Literature streams and recomposition",
            "## Candidate generation and evaluation",
            "## Research convergence",
            "## Explain solution logic",
            "## Repair and selective revision",
            "## Shadow draft",
            "## Formal certification architecture: closure before conclusion",
            "## Research-object fit and model architecture",
            "## Breadth-first model census and canonicalization",
            "## Independent solution-space discovery",
            "## Mechanism identification and falsification",
            "## Cross-claim and narrative synthesis",
        ]:
            self.assertIn(heading, text)

    def test_preserved_evidence_sections(self):
        text = (ROOT / "references" / "evidence_policy.md").read_text("utf-8")
        self.assertIn("## Exemplar retrieval and novelty screening", text)
        self.assertIn("## Citation and evidence display", text)
        self.assertIn("PROCESS_EVIDENCE firewall", text)
        self.assertIn("## Evidence roles for model architecture and mechanism", text)

    def test_runtime_answer_and_resume_rules_preserved(self):
        text = (ROOT / "SKILL.md").read_text("utf-8")
        for token in [
            "## Answer projection and display",
            "Math Display Gate",
            "Draft follows model; draft never determines model.",
            "## Resume",
        ]:
            self.assertIn(token, text)

    def test_v05_discovery_and_mechanism_behavioral_cases_present(self):
        text = (ROOT / "tests" / "BEHAVIORAL_ACCEPTANCE.md").read_text("utf-8")
        for heading in [
            "## B22 — Broad audit does not anchor on propositions",
            "## B23 — Cross-material timing drift",
            "## B24 — Claim-independent omitted branch discovery",
            "## B27 — Mechanism misattribution",
            "## B28 — Minimal-model challenge",
            "## B31 — Local task does not trigger whole-paper bureaucracy",
        ]:
            self.assertIn(heading, text)

    def test_v05_current_model_tracks_model_level_state(self):
        text = (ROOT / "templates" / "current_model.md").read_text("utf-8")
        for heading in [
            "## Material map",
            "## Canonical model map",
            "## Independent solution-space / regime map",
            "## Assumption-leverage map",
            "## Mechanism map and falsification status",
            "## Cross-material / implementation / cross-claim consistency",
            "## Institution-to-model mapping",
        ]:
            self.assertIn(heading, text)

    def test_v05_rc2_integrity_extensions_present(self):
        modeling = (ROOT / "references" / "modeling_and_validation.md").read_text("utf-8")
        evidence = (ROOT / "references" / "evidence_policy.md").read_text("utf-8")
        behavior = (ROOT / "tests" / "BEHAVIORAL_ACCEPTANCE.md").read_text("utf-8")
        ab = ROOT / "tests" / "A_B_EVALUATION.md"
        for token in [
            "institution-to-model map",
            "code, algorithms, or numerical routines",
            "Negative-space benchmark check",
            "claim-independent first pass",
        ]:
            self.assertIn(token, modeling)
        self.assertIn("Institution-mapping evidence", evidence)
        self.assertIn("Implementation evidence", evidence)
        for heading in [
            "## B32 — Institution-to-model mapping drift",
            "## B33 — Formal model versus computational implementation",
            "## B34 — Missing mechanism-isolating benchmark",
        ]:
            self.assertIn(heading, behavior)
        self.assertTrue(ab.is_file())
        self.assertIn("Material defect discovery", ab.read_text("utf-8"))

    def test_feedback_decision_algorithm_preserved(self):
        text = (ROOT / "references" / "feedback_and_decisions.md").read_text("utf-8")
        self.assertIn("## Decision-node algorithm", text)
        self.assertIn("Research constraint", text)
        self.assertIn("Modeling proposal", text)


if __name__ == "__main__":
    unittest.main()
