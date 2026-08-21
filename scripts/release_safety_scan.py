#!/usr/bin/env python3
"""Conservative pre-release scan for secrets; optional stricter personal-data scan."""
from __future__ import annotations

import argparse
from pathlib import Path
import re

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
TEXT_SUFFIXES = {
    ".md", ".py", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".csv", ".tsv", ".ps1", ".sh",
}

SECRET_PATTERNS = {
    "OpenAI-style API key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "Anthropic-style API key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,255}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "private-key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "JWT-like token": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
}

PERSONAL_PATTERNS = {
    "email address": re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    "Windows user-home path": re.compile(r"(?i)\b[A-Z]:\\Users\\(?!<|USER|USERNAME)[^\\\n\r`\"]+"),
    "Unix user-home path": re.compile(r"/(?:Users|home)/(?!<|user/)[^/\s]+(?:/[^\s`\"']*)?"),
    "PRC mobile number": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "PRC resident ID-like number": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "submission/manuscript ID-like value": re.compile(r"\b(?:MS|MKSC|MKS|JMR)[-_A-Z]*-?\d{2,}(?:-\d+)*\b", re.I),
}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--strict-personal",
        action="store_true",
        help="also flag emails, user-home paths, phone/ID-like values, and manuscript IDs",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    patterns = dict(SECRET_PATTERNS)
    if args.strict_personal:
        patterns.update(PERSONAL_PATTERNS)

    findings = []
    for path in iter_files(root):
        rel = path.relative_to(root)
        try:
            text = path.read_text("utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in patterns.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                sample = match.group(0)
                if len(sample) > 100:
                    sample = sample[:97] + "..."
                findings.append((str(rel), line, label, sample))

    if findings:
        print("Potential release-safety findings:")
        for rel, line, label, sample in findings:
            print(f"- {rel}:{line}: {label}: {sample}")
        return 1

    mode = "secrets + personal-data patterns" if args.strict_personal else "secret patterns"
    print(f"PASS: no configured {mode} detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
