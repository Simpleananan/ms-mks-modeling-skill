#!/usr/bin/env python3
"""Regenerate MANIFEST.sha256 from release-relevant repository files."""
from __future__ import annotations

import hashlib
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv"}
SKIP_NAMES = {"MANIFEST.sha256"}


def included_files(root: Path):
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name in SKIP_NAMES or path.suffix == ".pyc":
            continue
        yield path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rebuild(root: Path) -> Path:
    root = root.resolve()
    manifest = root / "MANIFEST.sha256"
    lines = [
        f"{sha256(path)}  ./{path.relative_to(root).as_posix()}"
        for path in included_files(root)
    ]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    output = rebuild(repo_root)
    print(output)
