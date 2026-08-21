#!/usr/bin/env python3
"""Read-only diagnostic for ms-mks-modeling discovery/install conflicts.

Current Codex local discovery follows Agent Skills locations such as
$HOME/.agents/skills and repository .agents/skills directories. The old
$HOME/.codex/skills location is inspected only as a legacy migration check.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re

NAME_RE = re.compile(r"(?m)^name:\s*([^\n#]+?)\s*$")
TARGET_NAME = "ms-mks-modeling"


@dataclass(frozen=True)
class RootSpec:
    path: Path
    label: str
    legacy: bool = False


def read_skill_name(path: Path) -> str | None:
    try:
        text = path.read_text("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = NAME_RE.search(text[:8000])
    return match.group(1).strip().strip('"\'') if match else None


def find_skills(root: Path):
    if not root.is_dir():
        return
    # Skill roots are normally immediate child directories. Also accept a root
    # that is itself a Skill so explicit diagnostics can target one checkout.
    candidates = [root]
    try:
        candidates.extend(path for path in root.iterdir() if path.is_dir())
    except OSError:
        return
    seen = set()
    for candidate in candidates:
        skill_file = candidate / "SKILL.md"
        if not skill_file.is_file():
            continue
        key = str(skill_file.resolve())
        if key in seen:
            continue
        seen.add(key)
        name = read_skill_name(skill_file)
        if name:
            yield name, candidate, candidate.resolve()


def repo_skill_roots(cwd: Path) -> list[RootSpec]:
    """Mirror Codex's repo discovery from CWD upward to the repo root."""
    cwd = cwd.resolve()
    chain = [cwd, *cwd.parents]
    repo_root = next((path for path in chain if (path / ".git").exists()), None)
    if repo_root is None:
        return [RootSpec(cwd / ".agents" / "skills", "repo:CWD")]

    roots: list[RootSpec] = []
    for path in chain:
        roots.append(RootSpec(path / ".agents" / "skills", f"repo:{path}"))
        if path == repo_root:
            break
    return roots


def default_root_specs() -> list[RootSpec]:
    specs = [RootSpec(Path.home() / ".agents" / "skills", "user")]
    specs.extend(repo_skill_roots(Path.cwd()))
    # Historical compatibility check only. Current Codex docs use
    # $HOME/.agents/skills for user-level local Skills.
    specs.append(RootSpec(Path.home() / ".codex" / "skills", "legacy-user", legacy=True))

    deduped: list[RootSpec] = []
    seen: set[str] = set()
    for spec in specs:
        key = str(spec.path.resolve()) if spec.path.exists() else str(spec.path.absolute())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(spec)
    return deduped


def inspect_specs(specs: list[RootSpec]):
    found: list[tuple[RootSpec, Path, Path]] = []
    for spec in specs:
        for name, display, resolved in find_skills(spec.path) or []:
            if name == TARGET_NAME:
                found.append((spec, display, resolved))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report ms-mks-modeling discovery conflicts; never modifies installations. "
            "Defaults to current Codex user/repository Skill locations plus a legacy-path check."
        )
    )
    parser.add_argument(
        "--skills-root",
        action="append",
        type=Path,
        default=[],
        help="Explicit Skill root to inspect. When supplied, default/legacy locations are not added.",
    )
    args = parser.parse_args()

    explicit = bool(args.skills_root)
    specs = (
        [RootSpec(path, f"explicit:{path}") for path in args.skills_root]
        if explicit
        else default_root_specs()
    )
    found = inspect_specs(specs)

    current = [item for item in found if not item[0].legacy]
    legacy = [item for item in found if item[0].legacy]

    if not found:
        print("No ms-mks-modeling Skill found in the inspected locations.")
        if not explicit:
            print(f"Expected user location: {Path.home() / '.agents' / 'skills' / TARGET_NAME}")
        return 0

    if current:
        print("Current discovery locations:")
        for spec, display, resolved in current:
            print(f"- [{spec.label}] discovered: {display}")
            print(f"  resolves_to: {resolved}")
            if display.name != TARGET_NAME:
                print(
                    "  WARNING: discovery folder name should match frontmatter name "
                    f"'{TARGET_NAME}'."
                )

    if legacy:
        print("Legacy locations detected:")
        for spec, display, resolved in legacy:
            print(f"- [{spec.label}] discovered: {display}")
            print(f"  resolves_to: {resolved}")
            print(
                "  WARNING: current Codex documentation uses $HOME/.agents/skills "
                "for user-level local Skills; review this legacy copy during migration."
            )

    folder_mismatch = any(display.name != TARGET_NAME for _, display, _ in current)

    if explicit:
        if len(current) > 1:
            distinct_targets = {str(resolved) for _, _, resolved in current}
            print("WARNING: multiple inspected discovery locations use the same frontmatter name.")
            if len(distinct_targets) > 1:
                print("FAIL: duplicate locations resolve to different Skill copies.")
                return 2
            print("WARNING: aliases resolve to one target, but duplicate discovery may still be ambiguous.")
            return 1
        if folder_mismatch:
            print("WARNING: the discovery folder name does not match the Skill name.")
            return 1
        print("PASS: exactly one matching ms-mks-modeling discovery location was found.")
        return 0

    if not current and legacy:
        print(
            "WARNING: only a legacy user-level install was found. Migrate or link it to "
            f"{Path.home() / '.agents' / 'skills' / TARGET_NAME}."
        )
        return 1

    if len(current) > 1:
        distinct_targets = {str(resolved) for _, _, resolved in current}
        print(
            "WARNING: multiple current discovery locations use the same frontmatter name. "
            "Codex does not merge same-name Skills."
        )
        if len(distinct_targets) > 1:
            print("FAIL: current duplicate locations resolve to different Skill copies.")
            return 2
        print("WARNING: aliases resolve to one target, but duplicate discovery may still be ambiguous.")
        return 1

    if folder_mismatch:
        print("WARNING: one current Skill was found, but its discovery folder name does not match the Skill name.")
        return 1

    if legacy:
        print(
            "WARNING: the current install is valid, but a legacy ~/.codex/skills copy also exists. "
            "Remove or archive the legacy copy once you confirm it is no longer needed."
        )
        return 1

    print("PASS: exactly one current ms-mks-modeling discovery location was found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
