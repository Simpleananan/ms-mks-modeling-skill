#!/usr/bin/env python3
"""Build, incrementally update, and query a local MS/MKS evidence index.

The source roots are read-only inputs. The SQLite database is disposable derived
data and must live outside every source root. This script performs lexical recall
and optional local semantic retrieval at paper level, then returns artifact-bound
passages. Codex must do structural comparison and evidence qualification. Ranking
scores are never evidence-strength scores.

Dependencies: Python standard library and an installed ``pdftotext`` executable.
Semantic embedding additionally requires ``sentence-transformers``.
"""

from __future__ import annotations

import argparse
import concurrent.futures
from datetime import datetime, timezone
import difflib
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import struct
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile


SCHEMA_VERSION = 8
SUPPORTED_SUFFIXES = {".pdf", ".docx", ".md", ".zip", ".7z"}
CANONICAL_ROLES = {
    "MAIN_ARTICLE",
    "ONLINE_APPENDIX",
    "COMMENT_CORRECTION",
    "PROCESS_EVIDENCE",
    "OTHER",
}
DEFAULT_RETRIEVAL_ROLES = (
    "MAIN_ARTICLE",
    "ONLINE_APPENDIX",
    "COMMENT_CORRECTION",
)
PROFILE_VERSION = 1
OPAQUE_SUFFIXES = {".zip", ".7z"}
DUPLICATE_IDENTITY_CONFLICT_PREFIX = "identical_content_hash_with_distinct_identity:"

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
APPENDIX_RE = re.compile(
    r"(?i)(?:^|[\s_.\-(\[{])(?:online[\s_.-]*appendix|"
    r"supplement(?:al|ary)?(?:[\s_.-]*material)?|supporting[\s_.-]*information|"
    r"technical[\s_.-]*appendix|appendix|OA|附录)(?=$|[\s_.\-)\]}])"
)
CORRECTION_RE = re.compile(
    r"(?i)(?:^|[\s_.-])(?:erratum|correction|corrigendum|comments?|commentary|rejoinder|勘误|更正|评论与回应)"
    r"(?:[\s_.-]+(?:to|on))?(?:$|[\s_.-])"
)

ROOT_ROLE_PAPER = "PAPER"
ROOT_ROLE_PROCESS = "PROCESS"
ROOT_ROLES = {ROOT_ROLE_PAPER, ROOT_ROLE_PROCESS}

IDENTITY_RANK = {
    "COMPANION_UNBOUND": -1,
    "PROVISIONAL_FILENAME": 0,
    "METADATA_KEY": 1,
    "MANIFEST_ID": 2,
    "DOI": 3,
}
VERSION_RANK = {
    "UNSPECIFIED": 0,
    "PREPRINT": 1,
    "PUBLISHED_APPENDIX": 2,
    "PUBLISHED": 3,
}

PROVENANCE_RANK = {
    "": 0,
    "FILENAME_FALLBACK": 1,
    "LEARNED_FILENAME_PATTERN": 1,
    "DOI_NAMESPACE": 2,
    "MARKDOWN_HEADING": 2,
    "PDF_DOCUMENT_METADATA": 3,
    "MARKDOWN_FRONTMATTER": 4,
    "SOURCE_SECTION": 4,
    "SOURCE_FRONT_MATTER": 5,
    "SOURCE_CITATION_BLOCK": 5,
    "MANIFEST": 6,
}

CANONICAL_FILENAME_RE = re.compile(
    r"(?P<yy>\d{2})_(?P<code>mksc|mnsc)\.(?P<doi_year>\d{4})\."
    r"(?P<suffix>\d+)_(?P<role>[A-Z]{1,3})_(?P<body>.+)",
    re.I,
)


def normalize_doi(value: str) -> str:
    value = normalize_space(value).casefold()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)
    match = DOI_RE.search(value)
    return match.group(0).rstrip(".,;)") if match else ""


def normalize_identity_text(value: str) -> str:
    value = normalize_space(value).casefold()
    return re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).strip()


def metadata_paper_id(title: str, authors: str, year: str) -> str:
    key = "|".join(
        [normalize_identity_text(title), normalize_identity_text(authors), year.strip()]
    )
    return "meta:" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def identity_from_metadata(
    *, doi: str, title: str, authors: str, year: str, explicit_paper_id: str = ""
) -> tuple[str, str]:
    normalized_doi = normalize_doi(doi)
    if normalized_doi:
        return f"doi:{normalized_doi}", "DOI"
    if explicit_paper_id:
        return explicit_paper_id, "MANIFEST_ID"
    if title and authors and re.fullmatch(r"(?:18|19|20)\d{2}", year or ""):
        return metadata_paper_id(title, authors, year), "METADATA_KEY"
    fallback = normalize_identity_text(title) or "unknown"
    digest = hashlib.sha256(fallback.encode("utf-8")).hexdigest()[:24]
    return f"provisional:{digest}", "PROVISIONAL_FILENAME"


def manifest_record_hash(record: dict | None) -> str:
    if not record:
        return ""
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def profile_rule_hash(path: Path, corpus_profile: dict | None) -> str:
    """Hash only the confirmed filename rule capable of changing this artifact."""
    match = CANONICAL_FILENAME_RE.match(path.stem)
    if not match:
        return ""
    rule = (corpus_profile or {}).get("artifact_codes", {}).get(
        match.group("role").upper()
    )
    if not rule:
        return ""
    payload = json.dumps(rule, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_corpus_profile(
    profile_path: Path | None, root_specs: list[tuple[Path, str]]
) -> dict[str, dict]:
    """Load user-confirmed, root-scoped conventions; never infer identity from it alone."""
    if profile_path is None:
        return {}
    profile_path = profile_path.resolve()
    if not profile_path.is_file():
        raise ValueError(f"Corpus profile does not exist: {profile_path}")
    for root, _ in root_specs:
        if path_is_within(profile_path, root):
            raise ValueError("Corpus profile must live outside every evidence root")
    try:
        payload = json.loads(profile_path.read_text("utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid corpus profile JSON: {exc}") from exc
    if payload.get("profile_version") != PROFILE_VERSION:
        raise ValueError(
            f"Unsupported corpus profile version: {payload.get('profile_version')!r}"
        )
    configured = {canonical_path(root): (root, role) for root, role in root_specs}
    records: dict[str, dict] = {}
    for index, record in enumerate(payload.get("corpora", []), start=1):
        try:
            root = Path(record["root"]).resolve()
        except (KeyError, TypeError) as exc:
            raise ValueError(f"Corpus profile record {index} has no valid root") from exc
        key = canonical_path(root)
        if key not in configured:
            continue
        codes = record.get("artifact_codes", {})
        if not isinstance(codes, dict):
            raise ValueError(f"Corpus profile artifact_codes must be an object: {root}")
        for code, rule in codes.items():
            if not isinstance(rule, dict) or rule.get("role") not in CANONICAL_ROLES:
                raise ValueError(f"Invalid artifact-code rule {code!r} for {root}")
            if rule.get("basis") != "USER_CONFIRMED":
                raise ValueError(
                    f"Artifact-code rule {code!r} is not USER_CONFIRMED; "
                    "automatic suggestions cannot become identity rules"
                )
        records[key] = record
    return records


def discover_corpus_profile(root_specs: list[tuple[Path, str]]) -> Path | None:
    """Find a conventional profile beside one root or at several roots' common parent."""
    if not root_specs:
        return None
    try:
        common = Path(os.path.commonpath([str(root.resolve()) for root, _ in root_specs]))
    except ValueError:
        return None
    # With one root, ``commonpath`` is the evidence root itself, where derived
    # state is forbidden.  Its parent is therefore the conventional profile
    # location.  With sibling roots, ``common`` is already their shared parent.
    locations = [common, common.parent]
    for location in locations:
        candidate = location / ".msmks" / "corpus_profile.json"
        if not candidate.is_file():
            continue
        if any(path_is_within(candidate, root) for root, _ in root_specs):
            continue
        return candidate.resolve()
    return None


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def normalize_space(text: str) -> str:
    text = text.replace("\u00ad", "").replace("\x00", " ")
    return re.sub(r"[ \t\r]+", " ", text).strip()


def _filesystem_path(path: Path) -> str:
    """Return a Windows extended-length path for Python file operations."""
    raw = str(path.resolve())
    if os.name != "nt" or raw.startswith("\\\\?\\"):
        return raw
    if raw.startswith("\\\\"):
        return "\\\\?\\UNC\\" + raw.lstrip("\\")
    return "\\\\?\\" + raw


def _display_path(path: Path) -> str:
    """Return an absolute human-facing path without the Windows long-path prefix."""
    return os.path.abspath(str(path))


def canonical_path(path: Path) -> str:
    return os.path.normcase(_filesystem_path(path))


def path_is_within(path: Path, directory: Path) -> bool:
    try:
        path_key = canonical_path(path)
        directory_key = canonical_path(directory)
        return os.path.commonpath([path_key, directory_key]) == directory_key
    except (OSError, ValueError):
        return False


def validate_locations(
    db_path: Path, root_specs: list[tuple[Path, str]]
) -> list[tuple[Path, str]]:
    if not root_specs:
        raise ValueError("At least one --paper-root or --process-root is required")
    resolved: list[tuple[Path, str]] = []
    seen: dict[str, str] = {}
    for root, root_role in root_specs:
        if root_role not in ROOT_ROLES:
            raise ValueError(f"Unknown root role: {root_role}")
        real = root.resolve()
        if not real.is_dir():
            raise ValueError(f"Source root is not a directory: {real}")
        key = canonical_path(real)
        prior = seen.get(key)
        if prior is not None and prior != root_role:
            raise ValueError(
                f"Source root cannot be both PAPER and PROCESS evidence: {real}"
            )
        if prior is None:
            seen[key] = root_role
            resolved.append((real, root_role))
    for i, (root_a, role_a) in enumerate(resolved):
        for root_b, role_b in resolved[i + 1 :]:
            if path_is_within(root_a, root_b) or path_is_within(root_b, root_a):
                raise ValueError(
                    "Source roots must be disjoint to preserve unambiguous provenance: "
                    f"{root_a} ({role_a}) overlaps {root_b} ({role_b})"
                )

    db_real = db_path.resolve()
    for root, _ in resolved:
        if path_is_within(db_real, root):
            raise ValueError(
                f"Derived index must be outside source root: db={db_real} root={root}"
            )
    return resolved


def is_link_or_reparse(path: Path) -> bool:
    """Return True for symlinks and Windows reparse-point/junction entries."""
    try:
        if path.is_symlink():
            return True
        info = os.lstat(_filesystem_path(path))
    except OSError:
        return False
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attrs = getattr(info, "st_file_attributes", 0)
    return bool(flag and attrs & flag)


def iter_source_files(root: Path):
    root_real = root.resolve()
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        if not path_is_within(directory_path, root_real):
            dirnames[:] = []
            continue
        kept_dirs = []
        for name in dirnames:
            child = directory_path / name
            if is_link_or_reparse(child):
                continue
            if not path_is_within(child, root_real):
                continue
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in filenames:
            path = directory_path / name
            if path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            if is_link_or_reparse(path):
                continue
            if not path_is_within(path, root_real):
                continue
            yield path


def scan_sources(
    root_specs: list[tuple[Path, str]]
) -> list[tuple[str, str, str]]:
    found: dict[str, tuple[str, str, str]] = {}
    for root, root_role in root_specs:
        for path in iter_source_files(root):
            key = canonical_path(path)
            prior = found.get(key)
            if prior and prior[2] != root_role:
                raise ValueError(
                    f"File discovered under conflicting evidence roles: {path}"
                )
            found[key] = (_display_path(path), _display_path(root), root_role)
    return [found[key] for key in sorted(found)]


def corpus_structure(root: Path) -> dict:
    """Profile naming/layout metadata without extracting document bodies."""
    extensions: dict[str, int] = {}
    artifact_codes: dict[str, int] = {}
    unmatched_prefixes: dict[str, int] = {}
    count = 0
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        dirnames[:] = [
            name
            for name in dirnames
            if not is_link_or_reparse(directory_path / name)
        ]
        for name in filenames:
            path = directory_path / name
            if is_link_or_reparse(path):
                continue
            count += 1
            extension = path.suffix.casefold()
            extensions[extension] = extensions.get(extension, 0) + 1
            canonical = re.match(
                r"^\d+_(?:mnsc|mksc)\.\d{4}\.\d+_([A-Z]{1,3})_", path.stem, re.I
            )
            if canonical:
                code = canonical.group(1).upper()
                artifact_codes[code] = artifact_codes.get(code, 0) + 1
            else:
                manuscript = re.match(
                    r"^(?:MS|MKSC|JMR)[-_A-Z]*-?\d+(?:-\d+)?_", path.stem, re.I
                )
                prefix = "MANUSCRIPT_ID" if manuscript else path.stem.split("_", 1)[0][:80]
                unmatched_prefixes[prefix] = unmatched_prefixes.get(prefix, 0) + 1
    return {
        "files": count,
        "extensions": dict(sorted(extensions.items())),
        "artifact_codes": dict(sorted(artifact_codes.items())),
        "unmatched_prefixes": dict(sorted(unmatched_prefixes.items())),
        "top_directories": sorted(
            child.name for child in root.iterdir() if child.is_dir() and not is_link_or_reparse(child)
        ),
    }


def audit_corpus_profile(
    profile_path: Path, root_specs: list[tuple[Path, str]]
) -> None:
    profiles = load_corpus_profile(profile_path, root_specs)
    results = []
    for root, root_role in root_specs:
        record = profiles.get(canonical_path(root), {})
        observed = corpus_structure(root)
        baseline = record.get("observed_structure", {})
        known_codes = set(record.get("artifact_codes", {})) | set(
            record.get("known_unmapped_codes", [])
        )
        unknown_codes = sorted(set(observed["artifact_codes"]) - known_codes)
        new_extensions = sorted(
            set(observed["extensions"]) - set(baseline.get("extensions", {}))
        )
        new_directories = sorted(
            set(observed["top_directories"]) - set(baseline.get("top_directories", []))
        )
        new_unmatched = sorted(
            set(observed["unmatched_prefixes"])
            - set(baseline.get("unmatched_prefixes", {}))
        )
        reasons = []
        if unknown_codes:
            reasons.append(f"unknown artifact codes: {unknown_codes}")
        if new_extensions:
            reasons.append(f"new extensions: {new_extensions}")
        if new_directories:
            reasons.append(f"new top directories: {new_directories}")
        if new_unmatched:
            reasons.append(f"new unmatched filename prefixes: {new_unmatched[:10]}")
        results.append(
            {
                "root": str(root),
                "root_role": root_role,
                "status": "PROFILE_REVIEW" if reasons else "CURRENT",
                "reasons": reasons,
                "observed": observed,
            }
        )
    print(
        json.dumps(
            {
                "profile": str(profile_path.resolve()),
                "profile_hash": file_sha256(profile_path),
                "corpora": results,
            },
            ensure_ascii=False,
        )
    )


def load_manifest(
    manifest_path: Path | None, root_specs: list[tuple[Path, str]]
) -> dict[str, dict]:
    """Load JSON/JSONL metadata keyed by absolute path or root-relative path.

    The manifest is authoritative for bibliographic metadata but never for file
    contents. Unknown fields are retained for forward compatibility; identity
    fields are validated when attached to a discovered artifact.
    """
    if manifest_path is None:
        return {}
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        raise ValueError(f"Manifest does not exist: {manifest_path}")
    for root, _ in root_specs:
        if path_is_within(manifest_path, root):
            raise ValueError(
                f"Manifest must live outside read-only source roots: {manifest_path}"
            )
    raw = manifest_path.read_text("utf-8-sig")
    try:
        if manifest_path.suffix.casefold() == ".jsonl":
            records = [json.loads(line) for line in raw.splitlines() if line.strip()]
        else:
            parsed = json.loads(raw)
            records = parsed.get("papers", parsed) if isinstance(parsed, dict) else parsed
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid manifest JSON: {manifest_path}: {exc}") from exc
    if not isinstance(records, list):
        raise ValueError("Manifest must be a JSON array, {'papers': [...]}, or JSONL")

    roots_by_name = {root.name: root for root, _ in root_specs}
    result: dict[str, dict] = {}
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"Manifest record {index} is not an object")
        raw_path = str(record.get("path") or record.get("source_path") or "").strip()
        if not raw_path:
            raise ValueError(f"Manifest record {index} has no path")
        candidate = Path(raw_path)
        candidates: list[Path] = []
        if candidate.is_absolute():
            candidates.append(candidate)
        else:
            parts = candidate.as_posix().split("/", 1)
            if len(parts) == 2 and parts[0] in roots_by_name:
                candidates.append(roots_by_name[parts[0]] / parts[1])
            candidates.extend(root / candidate for root, _ in root_specs)
        existing = [path for path in candidates if path.is_file()]
        if len(existing) != 1:
            raise ValueError(
                f"Manifest path must resolve to exactly one source artifact: {raw_path}"
            )
        key = canonical_path(existing[0])
        if key in result:
            raise ValueError(f"Duplicate manifest path: {raw_path}")
        result[key] = record
    return result


def manifest_path_from_meta(db_path: Path) -> Path | None:
    con = open_index(db_path)
    row = con.execute("SELECT value FROM meta WHERE key='manifest_path'").fetchone()
    con.close()
    return Path(row[0]) if row and row[0] else None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_filesystem_path(path), "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_id_for(path: Path) -> str:
    return hashlib.sha1(canonical_path(path).encode("utf-8")).hexdigest()


def classify_role(stem: str, root_role: str, filename_role: str | None) -> str:
    if root_role == ROOT_ROLE_PROCESS:
        return "PROCESS_EVIDENCE"
    # A user-confirmed, root-scoped mapping outranks generic filename markers.
    if filename_role:
        return filename_role
    lowered = stem.lower()
    if any(marker in lowered for marker in ("在线附录", "__附录", "online appendix")):
        return "ONLINE_APPENDIX"
    if CORRECTION_RE.search(lowered):
        return "COMMENT_CORRECTION"
    if APPENDIX_RE.search(stem):
        return "ONLINE_APPENDIX"
    return "MAIN_ARTICLE"


def normalized_work_title(stem: str) -> str:
    """Normalize common main/OA/correction filename variants to one work key."""
    cleaned = stem
    for pattern in (APPENDIX_RE, CORRECTION_RE):
        cleaned = pattern.sub(" ", cleaned)
    cleaned = re.sub(
        r"(?i)\b(?:online|supplemental|supplementary|supporting|information|material)\b",
        " ",
        cleaned,
    )
    cleaned = re.sub(r"(?i)^\s*(?:to|for|of|on)\b", " ", cleaned)
    cleaned = re.sub(r"[^\w]+", " ", cleaned, flags=re.UNICODE)
    return normalize_space(cleaned).casefold() or stem.casefold()


def parse_source(
    path: Path,
    source_root: Path,
    root_role: str,
    manifest: dict | None = None,
    corpus_profile: dict | None = None,
) -> dict:
    file_stat = os.stat(_filesystem_path(path))
    rel = path.relative_to(source_root).as_posix()
    stem = path.stem
    journal = ""
    year = ""
    doi = ""
    title = stem
    authors = ""
    abstract = ""
    keywords = ""
    filename_role: str | None = None
    artifact_version = "UNSPECIFIED"
    access_status = "UNSPECIFIED"
    role_confidence = "LOW"
    role_basis = "DEFAULT"
    profile_artifact_kind = ""
    provenance: dict[str, str] = {}

    canonical = CANONICAL_FILENAME_RE.match(stem)
    if canonical:
        code = canonical.group("code").lower()
        journal = "Marketing Science" if code == "mksc" else "Management Science"
        doi = f"10.1287/{code}.{canonical.group('doi_year')}.{canonical.group('suffix')}"
        artifact_code = canonical.group("role").upper()
        rule = (corpus_profile or {}).get("artifact_codes", {}).get(artifact_code)
        if rule:
            filename_role = rule["role"]
            artifact_version = str(rule.get("version") or "UNSPECIFIED").upper()
            access_status = str(rule.get("access") or "UNSPECIFIED").upper()
            profile_artifact_kind = str(rule.get("artifact_kind") or "").upper()
            role_confidence = "HIGH"
            role_basis = "CORPUS_PROFILE_USER_CONFIRMED"
        year = "20" + canonical.group("yy")
        body = canonical.group("body").split("__", 1)[0]
        title = body.rsplit("_", 1)[-1].replace("- ", ": ").strip()
        provenance.update(
            {
                "title": "LEARNED_FILENAME_PATTERN",
                "year": "LEARNED_FILENAME_PATTERN",
                "journal": "DOI_NAMESPACE",
                "doi": "LEARNED_FILENAME_PATTERN",
            }
        )
    elif root_role == ROOT_ROLE_PROCESS:
        if rel.startswith("ManagementScience/"):
            journal = "Management Science submission process"
        elif rel.startswith("MarketingScience/") or stem.startswith("MKSC-"):
            journal = "Marketing Science submission process"
        else:
            journal = rel.split("/", 1)[0] if "/" in rel else "Submission process"
        manuscript = re.match(r"((?:MS|MKSC|JMR)[-_A-Z]*-?\d+(?:-\d+)?)", stem, re.I)
        if manuscript:
            explicit_paper_id = manuscript.group(1).upper()
        else:
            explicit_paper_id = ""
        date_match = re.search(r"_(20\d{6})_", stem)
        if date_match:
            year = date_match.group(1)[:4]
        title = stem.split("__", 1)[0]
    else:
        journal = "Management Science / Marketing Science local corpus"
        title = stem.split("__", 1)[0]

    if path.suffix.casefold() == ".md" and not manifest:
        try:
            preview = path.read_text("utf-8-sig", errors="replace")[:20000]
            frontmatter = markdown_frontmatter(preview)
            for field in ("title", "authors", "year", "journal", "doi", "abstract", "keywords"):
                if frontmatter.get(field):
                    value = frontmatter[field]
                    if isinstance(value, list):
                        value = "; ".join(str(item) for item in value)
                    if field == "doi":
                        value = normalize_doi(str(value))
                    locals_value = normalize_space(str(value))
                    if field == "title":
                        title = locals_value
                    elif field == "authors":
                        authors = locals_value
                    elif field == "year":
                        year = locals_value
                    elif field == "journal":
                        journal = locals_value
                    elif field == "doi":
                        doi = locals_value
                    elif field == "abstract":
                        abstract = locals_value
                    elif field == "keywords":
                        keywords = locals_value
                    provenance[field] = "MARKDOWN_FRONTMATTER"
            heading = re.search(r"(?m)^#\s+(.+?)\s*$", preview)
            if heading and not frontmatter.get("title"):
                title = normalize_space(re.sub(r"[*_`]", "", heading.group(1)))
                provenance["title"] = "MARKDOWN_HEADING"
        except OSError:
            pass

    role = classify_role(stem, root_role, filename_role)
    if filename_role:
        role_basis = role_basis or "CORPUS_PROFILE_USER_CONFIRMED"
    elif role == "ONLINE_APPENDIX":
        role_confidence, role_basis = "MEDIUM", "SEMANTIC_FILENAME_MARKER"
    elif root_role == ROOT_ROLE_PROCESS:
        role_confidence, role_basis = "HIGH", "AUTHORIZED_PROCESS_ROOT"
    explicit_paper_id = locals().get("explicit_paper_id", "")
    metadata_source = "FILENAME_FALLBACK"
    if manifest:
        metadata_source = "MANIFEST"
        title = normalize_space(str(manifest.get("title") or title))
        raw_authors = manifest.get("authors") or authors
        authors = (
            "; ".join(normalize_space(str(value)) for value in raw_authors)
            if isinstance(raw_authors, list)
            else normalize_space(str(raw_authors))
        )
        year = str(manifest.get("year") or year).strip()
        journal = normalize_space(str(manifest.get("journal") or journal))
        doi = normalize_doi(str(manifest.get("doi") or doi))
        abstract = normalize_space(str(manifest.get("abstract") or ""))
        raw_keywords = manifest.get("keywords") or ""
        keywords = (
            "; ".join(normalize_space(str(value)) for value in raw_keywords)
            if isinstance(raw_keywords, list)
            else normalize_space(str(raw_keywords))
        )
        role = str(manifest.get("role") or role).upper()
        if role not in CANONICAL_ROLES:
            raise ValueError(f"Unknown manifest evidence role {role!r} for {path}")
        explicit_paper_id = str(manifest.get("paper_id") or "").strip()
        provenance.update(
            {
                field: "MANIFEST"
                for field in ("title", "authors", "year", "journal", "doi", "abstract", "keywords")
                if manifest.get(field)
            }
        )
        if str(manifest.get("identity_status") or "").upper() == "PROVISIONAL_FILENAME":
            explicit_paper_id = ""

    identity_title = title
    if metadata_source == "FILENAME_FALLBACK" and not doi and not authors:
        identity_title = normalized_work_title(stem)
    paper_id, identity_status = identity_from_metadata(
        doi=doi,
        title=identity_title,
        authors=authors,
        year=year,
        explicit_paper_id=explicit_paper_id,
    )
    # An unmanifested Markdown file is only a possible companion.  Sharing a
    # stem with a PDF is not sufficient authority to merge scholarly identity.
    if (
        path.suffix.casefold() == ".md"
        and not manifest
        and identity_status == "PROVISIONAL_FILENAME"
    ):
        digest = hashlib.sha256(canonical_path(path).encode("utf-8")).hexdigest()[:24]
        paper_id, identity_status = f"companion:{digest}", "COMPANION_UNBOUND"
    if profile_artifact_kind:
        artifact_kind = profile_artifact_kind
    elif path.suffix.casefold() == ".md":
        artifact_kind = "STRUCTURED_COMPANION"
    elif root_role == ROOT_ROLE_PROCESS:
        artifact_kind = "PROCESS_FILE"
    elif role == "ONLINE_APPENDIX":
        artifact_kind = "APPENDIX_PDF" if path.suffix.casefold() == ".pdf" else "APPENDIX_FILE"
    elif path.suffix.casefold() == ".pdf":
        artifact_kind = "PRIMARY_PDF"
    elif path.suffix.casefold() in {".zip", ".7z"}:
        artifact_kind = "ARCHIVE_ATTACHMENT"
    else:
        artifact_kind = "SOURCE_DOCUMENT"
    if manifest and manifest.get("artifact_kind"):
        artifact_kind = str(manifest["artifact_kind"]).upper()
    return {
        "artifact_id": artifact_id_for(path),
        "source_path": _display_path(path),
        "source_root": _display_path(source_root),
        "root_role": root_role,
        "source_rel": f"{source_root.name}/{rel}",
        "paper_id": paper_id,
        "identity_status": identity_status,
        "role": role,
        "artifact_kind": artifact_kind,
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "doi": normalize_doi(doi),
        "abstract": abstract,
        "keywords": keywords,
        "artifact_version": artifact_version,
        "access_status": access_status,
        "role_confidence": role_confidence,
        "role_basis": role_basis,
        "metadata_provenance": json.dumps(provenance, ensure_ascii=False, sort_keys=True),
        "metadata_source": metadata_source,
        "manifest_hash": manifest_record_hash(manifest),
        "profile_rule_hash": profile_rule_hash(path, corpus_profile),
        "extension": path.suffix.lower(),
        "size": file_stat.st_size,
        "mtime_ns": file_stat.st_mtime_ns,
        "content_hash": "",
    }


def _run_pdftotext(path: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["pdftotext", "-layout", "--", str(path), "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=180,
    )


def _pdftotext_error(proc: subprocess.CompletedProcess[bytes]) -> str:
    return proc.stderr.decode("utf-8", errors="replace")[-1000:]


def pdf_pages(path: Path) -> list[str]:
    try:
        proc = _run_pdftotext(path)
    except FileNotFoundError as exc:
        raise RuntimeError("pdftotext executable was not found") from exc
    if proc.returncode != 0:
        direct_error = _pdftotext_error(proc)
        # Some Windows Poppler builds cannot open long or non-ASCII paths even
        # though Python can. Retry through an ASCII temporary alias. Prefer a
        # hard link to avoid copying large PDFs; fall back to a temporary copy
        # when links are unavailable or cross-volume.
        try:
            with tempfile.TemporaryDirectory(prefix="msmks-pdf-") as td:
                alias = Path(td) / "source.pdf"
                source_for_fs = _filesystem_path(path)
                try:
                    os.link(source_for_fs, alias)
                except OSError:
                    shutil.copyfile(source_for_fs, alias)
                try:
                    proc = _run_pdftotext(alias)
                except FileNotFoundError as exc:
                    raise RuntimeError("pdftotext executable was not found") from exc
        except OSError as exc:
            raise RuntimeError(
                f"pdftotext failed on the source path and temporary alias creation failed: {exc}; "
                f"direct error: {direct_error}"
            ) from exc
        if proc.returncode != 0:
            fallback_error = _pdftotext_error(proc)
            raise RuntimeError(
                "pdftotext failed on both the source path and a temporary ASCII alias; "
                f"direct error: {direct_error}; alias error: {fallback_error}"
            )
    return proc.stdout.decode("utf-8", errors="replace").split("\f")


def docx_blocks(path: Path) -> list[str]:
    with zipfile.ZipFile(_filesystem_path(path)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"</w:(?:p|tr)>", "\n\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    return [html.unescape(re.sub(r"<[^>]+>", "", xml))]


def markdown_blocks(path: Path) -> list[str]:
    return [path.read_text("utf-8-sig", errors="replace")]


def markdown_frontmatter(text: str) -> dict:
    """Parse a conservative scalar/list subset of YAML front matter."""
    match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, re.S)
    if not match:
        return {}
    output: dict[str, object] = {}
    allowed = {"title", "authors", "year", "journal", "doi", "abstract", "keywords"}
    for line in match.group(1).splitlines():
        item = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*?)\s*$", line)
        if not item or item.group(1).casefold() not in allowed:
            continue
        key, raw = item.group(1).casefold(), item.group(2).strip()
        if raw.startswith("[") and raw.endswith("]"):
            output[key] = [
                value.strip().strip("\"'") for value in raw[1:-1].split(",") if value.strip()
            ]
        else:
            output[key] = raw.strip("\"'")
    return output


def markdown_sections(path: Path) -> tuple[dict, list[tuple[str, str]]]:
    """Return front matter plus deterministic ATX-heading hierarchy sections."""
    text = path.read_text("utf-8-sig", errors="replace").replace("\r", "")
    metadata = markdown_frontmatter(text)
    text = re.sub(r"\A---\s*\n.*?\n---\s*(?:\n|\Z)", "", text, count=1, flags=re.S)
    stack: list[str] = []
    current = "document body"
    buffer: list[str] = []
    sections: list[tuple[str, str]] = []

    def flush() -> None:
        content = "\n".join(buffer).strip()
        if content:
            sections.append((current, content))

    for line in text.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if not heading:
            buffer.append(line)
            continue
        flush()
        buffer = []
        level = len(heading.group(1))
        title = normalize_space(re.sub(r"[*_`]", "", heading.group(2)))
        stack[level - 1 :] = [title]
        current = " > ".join(stack)
    flush()
    return metadata, sections or [("document body", text)]


def pdf_embedded_metadata(path: Path) -> dict[str, str]:
    """Read lightweight PDF document metadata through Poppler when available."""
    try:
        proc = subprocess.run(
            ["pdfinfo", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}
    if proc.returncode != 0:
        return {}
    output: dict[str, str] = {}
    key_map = {"title": "title", "author": "authors", "keywords": "keywords", "subject": "subject"}
    for line in proc.stdout.decode("utf-8", errors="replace").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        mapped = key_map.get(key.strip().casefold())
        if mapped and normalize_space(value):
            output[mapped] = normalize_space(value)
    subject = output.get("subject", "")
    year_match = re.search(r"\b((?:19|20)\d{2})\b", subject)
    if year_match:
        output["year"] = year_match.group(1)
    if re.search(r"\bMarketing Science\b", subject, re.I):
        output["journal"] = "Marketing Science"
    elif re.search(r"\bManagement Science\b", subject, re.I):
        output["journal"] = "Management Science"
    return output


def extract_abstract(front_text: str) -> str:
    match = re.search(
        r"(?is)\babstract\b\s*[:.\-]?\s*(.{80,5000}?)(?=\n\s*(?:keywords?|1\.?\s+introduction|introduction)\b)",
        front_text,
    )
    return normalize_space(match.group(1))[:5000] if match else ""


def make_chunks(
    text: str, target: int = 1400, overlap: int = 220
) -> list[tuple[int, int, str]]:
    text = text.replace("\r", "")
    paragraphs = [
        normalize_space(part)
        for part in re.split(r"\n{2,}|(?<=\.)\s*\n", text)
        if normalize_space(part)
    ]
    if not paragraphs:
        clean = normalize_space(text)
        return [(0, len(clean), clean)] if clean else []
    chunks: list[tuple[int, int, str]] = []
    buffer = ""
    start = 0
    cursor = 0
    for paragraph in paragraphs:
        if len(paragraph) > target:
            if buffer:
                chunks.append((start, start + len(buffer), buffer))
                buffer = ""
            step = max(1, target - overlap)
            for offset in range(0, len(paragraph), step):
                piece = paragraph[offset : offset + target]
                if piece:
                    chunks.append((cursor + offset, cursor + offset + len(piece), piece))
                if offset + target >= len(paragraph):
                    break
            cursor += len(paragraph) + 1
            continue
        if buffer and len(buffer) + len(paragraph) + 1 > target:
            chunks.append((start, start + len(buffer), buffer))
            tail = buffer[-overlap:] if overlap else ""
            start = max(0, cursor - len(tail))
            buffer = (tail + " " + paragraph).strip()
        else:
            if not buffer:
                start = cursor
            buffer = (buffer + " " + paragraph).strip()
        cursor += len(paragraph) + 1
    if buffer:
        chunks.append((start, start + len(buffer), buffer))
    return chunks


def guess_section(text: str, default: str) -> str:
    candidate = normalize_space(text)[:180]
    match = re.match(
        r"(?i)(abstract|introduction|model|setting|analysis|equilibrium|results?|"
        r"welfare|discussion|conclusion|proof|appendix|online appendix|[1-9]\.?\s+[A-Z][^.]{2,80})",
        candidate,
    )
    return normalize_space(match.group(0))[:120] if match else default


def extract_one(args: tuple) -> dict:
    path_s, root_s, root_role, *rest = args
    manifest = rest[0] if rest else None
    corpus_profile = rest[1] if len(rest) > 1 else None
    path, root = Path(path_s), Path(root_s)
    meta = parse_source(path, root, root_role, manifest, corpus_profile)
    try:
        meta["content_hash"] = file_sha256(path)
        provenance = json.loads(meta.get("metadata_provenance") or "{}")
        if path.suffix.lower() == ".pdf":
            embedded = pdf_embedded_metadata(path)
            for field in ("title", "authors", "year", "journal", "keywords"):
                if embedded.get(field) and provenance.get(field) != "MANIFEST":
                    meta[field] = embedded[field]
                    provenance[field] = "PDF_DOCUMENT_METADATA"
            units = pdf_pages(path)
        elif path.suffix.lower() == ".docx":
            units = docx_blocks(path)
        elif path.suffix.lower() == ".md":
            md_metadata, md_sections = markdown_sections(path)
            for field in ("title", "authors", "year", "journal", "doi", "abstract", "keywords"):
                if md_metadata.get(field) and provenance.get(field) != "MANIFEST":
                    value = md_metadata[field]
                    if isinstance(value, list):
                        value = "; ".join(str(item) for item in value)
                    meta[field] = normalize_doi(str(value)) if field == "doi" else normalize_space(str(value))
                    provenance[field] = "MARKDOWN_FRONTMATTER"
            units = [text for _, text in md_sections]
        else:
            # Archives are linked and hashed, but their contents are intentionally
            # opaque during ordinary indexing.  Inspect only for a task that needs
            # replication code/data or implemented-model evidence.
            units = []
        chunks = []
        if units:
            front = normalize_space(" ".join(units[:2]))
            doi_match = DOI_RE.search(front)
            if doi_match:
                doi = normalize_doi(doi_match.group(0))
                if meta["doi"] and meta["doi"] != doi and provenance.get("doi") == "MANIFEST":
                    meta["identity_conflict"] = f"manifest_or_filename_doi={meta['doi']} content_doi={doi}"
                else:
                    meta["doi"] = doi
                    provenance["doi"] = "SOURCE_FRONT_MATTER"
                    meta["paper_id"], meta["identity_status"] = identity_from_metadata(
                        doi=doi,
                        title=meta["title"],
                        authors=meta["authors"],
                        year=meta["year"],
                    )
                doi_lower = doi.casefold()
                if "/mksc." in doi_lower:
                    meta["journal"] = "Marketing Science"
                elif "/mnsc." in doi_lower:
                    meta["journal"] = "Management Science"
            cite = re.search(
                r"To cite this article:\s*(.+?)\s*\((20\d{2})\)", front, re.I
            )
            if cite:
                if provenance.get("authors") != "MANIFEST":
                    meta["authors"] = normalize_space(cite.group(1))
                    provenance["authors"] = "SOURCE_CITATION_BLOCK"
                if provenance.get("year") != "MANIFEST":
                    meta["year"] = cite.group(2)
                    provenance["year"] = "SOURCE_CITATION_BLOCK"
            if not meta["abstract"]:
                meta["abstract"] = extract_abstract("\n".join(units[:2]))
                if meta["abstract"]:
                    provenance["abstract"] = "SOURCE_SECTION"
        # Identity is decided only after the full metadata cascade.  Embedded
        # metadata or source front matter can turn an unrenamed file into a
        # deterministic title+authors+year identity even when no DOI exists.
        complete_metadata_identity = (
            bool(meta["title"] and meta["authors"])
            and bool(re.fullmatch(r"(?:18|19|20)\d{2}", meta["year"] or ""))
        )
        if meta["identity_status"] in {"PROVISIONAL_FILENAME", "METADATA_KEY"} and (
            meta["doi"] or complete_metadata_identity
        ):
            meta["paper_id"], meta["identity_status"] = identity_from_metadata(
                doi=meta["doi"],
                title=meta["title"],
                authors=meta["authors"],
                year=meta["year"],
            )
        for unit_index, unit in enumerate(units, start=1):
            for chunk_index, (start, end, text) in enumerate(make_chunks(unit), start=1):
                if len(text) < 60:
                    continue
                page = unit_index if path.suffix.lower() == ".pdf" else None
                if path.suffix.lower() == ".md":
                    default_section = md_sections[unit_index - 1][0]
                else:
                    default_section = f"page {page}" if page is not None else "document body"
                chunks.append(
                    {
                        "page": page,
                        "section": default_section
                        if path.suffix.lower() == ".md"
                        else guess_section(text, default_section),
                        "chunk_index": chunk_index,
                        "char_start": start,
                        "char_end": end,
                        "text": text,
                    }
                )
        meta["chunks"] = chunks
        meta["metadata_provenance"] = json.dumps(
            provenance, ensure_ascii=False, sort_keys=True
        )
        meta["error"] = ""
        meta.setdefault("identity_conflict", "")
    except Exception as exc:  # Preserve extraction failures for auditability.
        meta["chunks"] = []
        meta["error"] = f"{type(exc).__name__}: {exc}"
        meta.setdefault("identity_conflict", "")
    return meta


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE documents (
  doc_id INTEGER PRIMARY KEY,
  artifact_id TEXT UNIQUE NOT NULL,
  source_path TEXT UNIQUE NOT NULL,
  source_root TEXT NOT NULL,
  root_role TEXT NOT NULL,
  source_rel TEXT NOT NULL,
  paper_id TEXT NOT NULL,
  identity_status TEXT NOT NULL,
  role TEXT NOT NULL,
  artifact_kind TEXT NOT NULL,
  artifact_version TEXT NOT NULL,
  access_status TEXT NOT NULL,
  role_confidence TEXT NOT NULL,
  role_basis TEXT NOT NULL,
  title TEXT NOT NULL,
  authors TEXT NOT NULL,
  year TEXT NOT NULL,
  journal TEXT NOT NULL,
  doi TEXT NOT NULL,
  abstract TEXT NOT NULL,
  keywords TEXT NOT NULL,
  metadata_source TEXT NOT NULL,
  metadata_provenance TEXT NOT NULL,
  manifest_hash TEXT NOT NULL,
  profile_rule_hash TEXT NOT NULL,
  identity_conflict TEXT NOT NULL,
  extension TEXT NOT NULL,
  size INTEGER NOT NULL,
  mtime_ns INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  error TEXT NOT NULL
);
CREATE INDEX documents_paper_idx ON documents(paper_id);
CREATE INDEX documents_root_idx ON documents(source_root);
CREATE TABLE papers (
  paper_pk INTEGER PRIMARY KEY,
  paper_id TEXT UNIQUE NOT NULL,
  identity_status TEXT NOT NULL,
  title TEXT NOT NULL,
  normalized_title TEXT NOT NULL,
  authors TEXT NOT NULL,
  year TEXT NOT NULL,
  journal TEXT NOT NULL,
  doi TEXT NOT NULL,
  abstract TEXT NOT NULL,
  keywords TEXT NOT NULL,
  headings TEXT NOT NULL,
  metadata_source TEXT NOT NULL,
  metadata_provenance TEXT NOT NULL,
  metadata_conflict TEXT NOT NULL,
  bibliography_fingerprint TEXT NOT NULL,
  retrieval_fingerprint TEXT NOT NULL,
  content_fingerprint TEXT NOT NULL
);
CREATE UNIQUE INDEX papers_doi_idx ON papers(doi) WHERE doi <> '';
CREATE TABLE chunks (
  chunk_id INTEGER PRIMARY KEY,
  doc_id INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  page INTEGER,
  section TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  char_start INTEGER NOT NULL,
  char_end INTEGER NOT NULL,
  text TEXT NOT NULL
  ,locator_id TEXT UNIQUE NOT NULL
);
CREATE INDEX chunks_doc_idx ON chunks(doc_id);
CREATE VIRTUAL TABLE chunks_fts USING fts5(
  text,
  title,
  paper_id,
  role,
  journal,
  tokenize='unicode61 remove_diacritics 2'
);
CREATE VIRTUAL TABLE papers_fts USING fts5(
  title,
  authors,
  abstract,
  keywords,
  headings,
  journal,
  tokenize='unicode61 remove_diacritics 2'
);
CREATE TABLE embeddings (
  paper_id TEXT NOT NULL,
  model TEXT NOT NULL,
  model_revision TEXT NOT NULL,
  document_prefix TEXT NOT NULL,
  query_prefix TEXT NOT NULL,
  content_fingerprint TEXT NOT NULL,
  dimensions INTEGER NOT NULL,
  vector BLOB NOT NULL,
  PRIMARY KEY (paper_id, model, model_revision)
);
CREATE TABLE companion_candidates (
  companion_artifact_id TEXT NOT NULL,
  candidate_paper_id TEXT NOT NULL,
  score REAL NOT NULL,
  basis TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  PRIMARY KEY (companion_artifact_id, candidate_paper_id)
);
"""


DOCUMENT_COLUMNS = (
    "artifact_id",
    "source_path",
    "source_root",
    "root_role",
    "source_rel",
    "paper_id",
    "identity_status",
    "role",
    "artifact_kind",
    "artifact_version",
    "access_status",
    "role_confidence",
    "role_basis",
    "title",
    "authors",
    "year",
    "journal",
    "doi",
    "abstract",
    "keywords",
    "metadata_source",
    "metadata_provenance",
    "manifest_hash",
    "profile_rule_hash",
    "identity_conflict",
    "extension",
    "size",
    "mtime_ns",
    "content_hash",
    "error",
)


def open_index(db_path: Path) -> sqlite3.Connection:
    if not db_path.is_file():
        raise ValueError(f"Index does not exist: {db_path}")
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON")
    version = con.execute("PRAGMA user_version").fetchone()[0]
    if version != SCHEMA_VERSION:
        con.close()
        raise ValueError(
            f"Index schema {version} is incompatible with {SCHEMA_VERSION}; run build"
        )
    return con


def serialize_root_specs(root_specs: list[tuple[Path, str]]) -> str:
    return json.dumps(
        [{"path": str(root), "role": role} for root, role in root_specs],
        ensure_ascii=False,
    )


def stored_root_specs(db_path: Path) -> list[tuple[Path, str]]:
    con = open_index(db_path)
    row = con.execute("SELECT value FROM meta WHERE key='source_roots'").fetchone()
    con.close()
    if not row:
        raise ValueError("Index has no stored source-root configuration; run build")
    try:
        raw = json.loads(row[0])
        specs = [(Path(item["path"]), item["role"]) for item in raw]
    except (TypeError, KeyError, json.JSONDecodeError) as exc:
        raise ValueError("Index source-root configuration is invalid; rebuild the index") from exc
    if not specs:
        raise ValueError("Index has an empty source-root configuration; rebuild the index")
    return specs


def initialize_index(
    con: sqlite3.Connection,
    root_specs: list[tuple[Path, str]],
    manifest_path: Path | None = None,
    profile_path: Path | None = None,
) -> None:
    con.executescript(SCHEMA)
    con.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    con.executemany(
        "INSERT INTO meta(key,value) VALUES (?,?)",
        [
            ("schema_version", str(SCHEMA_VERSION)),
            ("source_roots", serialize_root_specs(root_specs)),
            ("manifest_path", str(manifest_path.resolve()) if manifest_path else ""),
            ("profile_path", str(profile_path.resolve()) if profile_path else ""),
            ("profile_hash", file_sha256(profile_path) if profile_path else ""),
            ("created_utc", str(int(time.time()))),
            ("last_update_utc", str(int(time.time()))),
        ],
    )


def delete_document(con: sqlite3.Connection, doc_id: int) -> None:
    con.execute(
        "DELETE FROM chunks_fts WHERE rowid IN (SELECT chunk_id FROM chunks WHERE doc_id=?)",
        (doc_id,),
    )
    con.execute("DELETE FROM documents WHERE doc_id=?", (doc_id,))


def insert_document(con: sqlite3.Connection, item: dict) -> None:
    values = [item[column] for column in DOCUMENT_COLUMNS]
    placeholders = ",".join("?" for _ in DOCUMENT_COLUMNS)
    cursor = con.execute(
        f"INSERT INTO documents ({','.join(DOCUMENT_COLUMNS)}) VALUES ({placeholders})",
        values,
    )
    doc_id = cursor.lastrowid
    for chunk in item["chunks"]:
        locator_payload = "|".join(
            [
                item["artifact_id"],
                item["content_hash"],
                str(chunk["page"] or ""),
                chunk["section"],
                str(chunk["char_start"]),
                str(chunk["char_end"]),
                hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest(),
            ]
        )
        locator_id = "loc:" + hashlib.sha256(locator_payload.encode("utf-8")).hexdigest()[:32]
        chunk_cursor = con.execute(
            """INSERT INTO chunks
            (doc_id,page,section,chunk_index,char_start,char_end,text,locator_id)
            VALUES (?,?,?,?,?,?,?,?)""",
            (
                doc_id,
                chunk["page"],
                chunk["section"],
                chunk["chunk_index"],
                chunk["char_start"],
                chunk["char_end"],
                chunk["text"],
                locator_id,
            ),
        )
        con.execute(
            """INSERT INTO chunks_fts(rowid,text,title,paper_id,role,journal)
            VALUES (?,?,?,?,?,?)""",
            (
                chunk_cursor.lastrowid,
                chunk["text"],
                item["title"],
                item["paper_id"],
                item["role"],
                item["journal"],
            ),
        )


def extraction_inputs(
    paths: list[tuple[str, str, str]],
    manifest: dict[str, dict],
    profiles: dict[str, dict] | None = None,
) -> list[tuple[str, str, str, dict | None, dict | None]]:
    return [
        (
            path,
            root,
            role,
            manifest.get(canonical_path(Path(path))),
            (profiles or {}).get(canonical_path(Path(root))),
        )
        for path, root, role in paths
    ]


def extract_many(paths: list[tuple], workers: int):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(extract_one, paths)


def without_generated_duplicate_conflict(value: str) -> str:
    """Remove only conflicts derived from the current duplicate-byte grouping."""
    return "; ".join(
        part
        for part in (piece.strip() for piece in (value or "").split("; "))
        if part and not part.startswith(DUPLICATE_IDENTITY_CONFLICT_PREFIX)
    )


def reconcile_duplicate_identity_conflicts(con: sqlite3.Connection) -> None:
    """Recompute duplicate-byte conflicts so corpus deletions can clear stale alarms."""
    rows = list(
        con.execute(
            "SELECT doc_id,content_hash,paper_id,identity_conflict FROM documents"
        )
    )
    groups: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        if row["content_hash"]:
            groups.setdefault(row["content_hash"], []).append(row)
    for artifacts in groups.values():
        paper_ids = sorted({row["paper_id"] for row in artifacts})
        generated = (
            f"{DUPLICATE_IDENTITY_CONFLICT_PREFIX} {' vs '.join(paper_ids)}"
            if len(paper_ids) > 1
            else ""
        )
        for row in artifacts:
            retained = without_generated_duplicate_conflict(row["identity_conflict"])
            updated = "; ".join(value for value in (retained, generated) if value)
            if updated != row["identity_conflict"]:
                con.execute(
                    "UPDATE documents SET identity_conflict=? WHERE doc_id=?",
                    (updated, row["doc_id"]),
                )


def refresh_papers(con: sqlite3.Connection) -> str:
    """Rebuild paper-level identity and FTS views from artifact records."""
    con.row_factory = sqlite3.Row
    reconcile_duplicate_identity_conflicts(con)
    old_fingerprints = dict(
        con.execute("SELECT paper_id,retrieval_fingerprint FROM papers")
    )
    con.execute("DELETE FROM papers_fts")
    con.execute("DELETE FROM papers")
    rows = list(
        con.execute(
            "SELECT * FROM documents ORDER BY paper_id, "
            "CASE metadata_source WHEN 'MANIFEST' THEN 0 ELSE 1 END, "
            "CASE artifact_kind WHEN 'PRIMARY_PDF' THEN 0 WHEN 'APPENDIX_PDF' THEN 1 "
            "WHEN 'SOURCE_DOCUMENT' THEN 2 WHEN 'STRUCTURED_COMPANION' THEN 3 ELSE 4 END"
        )
    )
    grouped: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        grouped.setdefault(row["paper_id"], []).append(row)

    source_parts: list[str] = []
    coverage_parts: list[str] = []
    ranking_parts: list[str] = []
    for paper_id, artifacts in grouped.items():
        canonical = max(
            artifacts,
            key=lambda row: (
                IDENTITY_RANK.get(row["identity_status"], -1),
                row["metadata_source"] == "MANIFEST",
                VERSION_RANK.get(row["artifact_version"], 0),
                row["artifact_kind"] == "PRIMARY_PDF",
            ),
        )
        fields = {}
        paper_provenance: dict[str, str] = {}
        conflicts = []
        for field in ("title", "authors", "year", "journal", "doi", "keywords"):
            candidates = []
            for row in artifacts:
                if not row[field]:
                    continue
                provenance = json.loads(row["metadata_provenance"] or "{}")
                field_source = provenance.get(field, "")
                candidates.append(
                    (
                        PROVENANCE_RANK.get(field_source, 0),
                        row["metadata_source"] == "MANIFEST",
                        row["artifact_kind"] == "PRIMARY_PDF",
                        VERSION_RANK.get(row["artifact_version"], 0),
                        str(row[field]),
                        field_source,
                    )
                )
            if candidates:
                selected = max(candidates, key=lambda item: item[:4])
                fields[field] = selected[4]
                paper_provenance[field] = selected[5]
                best_rank = selected[0]
                best_values = {
                    normalize_space(item[4])
                    for item in candidates
                    if item[:4] == selected[:4] and normalize_space(item[4])
                }
                if len(best_values) > 1 and best_rank >= PROVENANCE_RANK["PDF_DOCUMENT_METADATA"]:
                    conflicts.append(f"{field}={sorted(best_values)!r}")
            else:
                fields[field] = ""
        conflicts.extend(row["identity_conflict"] for row in artifacts if row["identity_conflict"])
        abstract_candidates = []
        for row in artifacts:
            if not row["abstract"]:
                continue
            provenance = json.loads(row["metadata_provenance"] or "{}")
            source = provenance.get("abstract", "")
            abstract_candidates.append(
                (
                    PROVENANCE_RANK.get(source, 0),
                    row["metadata_source"] == "MANIFEST",
                    VERSION_RANK.get(row["artifact_version"], 0),
                    str(row["abstract"]),
                    source,
                )
            )
        if abstract_candidates:
            selected_abstract = max(abstract_candidates, key=lambda item: item[:3])
            abstract = selected_abstract[3]
            paper_provenance["abstract"] = selected_abstract[4]
        else:
            abstract = ""
        headings = "; ".join(
            dict.fromkeys(
                normalize_space(row[0])
                for artifact in artifacts
                if artifact["root_role"] != ROOT_ROLE_PROCESS
                for row in con.execute(
                    "SELECT section FROM chunks WHERE doc_id=? ORDER BY page,chunk_index",
                    (artifact["doc_id"],),
                )
                if row[0]
                and normalize_space(row[0]).casefold() != "document body"
                and not re.fullmatch(r"page\s+\d+", normalize_space(row[0]), re.I)
            )
        )
        hashes = sorted({row["content_hash"] for row in artifacts if row["content_hash"]})
        retrieval_artifacts = [
            row
            for row in artifacts
            if row["root_role"] != ROOT_ROLE_PROCESS
            and row["role"] in DEFAULT_RETRIEVAL_ROLES
            and row["artifact_kind"] != "STRUCTURED_COMPANION"
        ]
        retrieval_hashes = sorted(
            {row["content_hash"] for row in retrieval_artifacts if row["content_hash"]}
        )
        fingerprint_source = json.dumps(
            [paper_id, fields, abstract, headings, hashes], ensure_ascii=False, sort_keys=True
        )
        fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()
        bibliography_payload = json.dumps(
            [
                paper_id,
                canonical["identity_status"],
                {key: fields[key] for key in ("title", "authors", "year", "journal", "doi")},
                paper_provenance,
                sorted(conflicts),
            ],
            ensure_ascii=False,
            sort_keys=True,
        )
        bibliography_fingerprint = hashlib.sha256(
            bibliography_payload.encode("utf-8")
        ).hexdigest()
        retrieval_payload = json.dumps(
            [
                paper_id,
                fields["title"],
                fields["authors"],
                abstract,
                fields["keywords"],
                headings,
                fields["journal"],
                retrieval_hashes,
                SCHEMA_VERSION,
            ],
            ensure_ascii=False,
            sort_keys=True,
        )
        retrieval_fingerprint = hashlib.sha256(
            retrieval_payload.encode("utf-8")
        ).hexdigest()
        cursor = con.execute(
            """INSERT INTO papers
            (paper_id,identity_status,title,normalized_title,authors,year,journal,doi,
             abstract,keywords,headings,metadata_source,metadata_provenance,
             metadata_conflict,bibliography_fingerprint,retrieval_fingerprint,
             content_fingerprint)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                paper_id,
                canonical["identity_status"],
                fields["title"],
                normalize_identity_text(fields["title"]),
                fields["authors"],
                fields["year"],
                fields["journal"],
                normalize_doi(fields["doi"]),
                abstract,
                fields["keywords"],
                headings,
                "FIELD_LEVEL_CASCADE",
                json.dumps(paper_provenance, ensure_ascii=False, sort_keys=True),
                "; ".join(conflicts),
                bibliography_fingerprint,
                retrieval_fingerprint,
                fingerprint,
            ),
        )
        con.execute(
            """INSERT INTO papers_fts
            (rowid,title,authors,abstract,keywords,headings,journal)
            VALUES (?,?,?,?,?,?,?)""",
            (
                cursor.lastrowid,
                fields["title"],
                fields["authors"],
                abstract,
                fields["keywords"],
                headings,
                fields["journal"],
            ),
        )
        source_parts.append(f"{paper_id}:{fingerprint}")
        if retrieval_artifacts:
            coverage_parts.append(paper_id)
            ranking_parts.append(retrieval_fingerprint)
        if old_fingerprints.get(paper_id) not in (None, retrieval_fingerprint):
            con.execute("DELETE FROM embeddings WHERE paper_id=?", (paper_id,))
    current_ids = set(grouped)
    for old_id in set(old_fingerprints) - current_ids:
        con.execute("DELETE FROM embeddings WHERE paper_id=?", (old_id,))
    con.execute("DELETE FROM companion_candidates")
    companions = list(
        con.execute(
            "SELECT artifact_id,source_rel,title FROM documents "
            "WHERE artifact_kind='STRUCTURED_COMPANION' AND identity_status='COMPANION_UNBOUND'"
        )
    )
    targets = list(
        con.execute(
            "SELECT artifact_id,paper_id,source_rel,title FROM documents "
            "WHERE root_role<>? AND artifact_kind<>'STRUCTURED_COMPANION'",
            (ROOT_ROLE_PROCESS,),
        )
    )
    for companion in companions:
        companion_dir = str(Path(companion["source_rel"]).parent).casefold()
        companion_stem = normalized_work_title(Path(companion["source_rel"]).stem)
        companion_title = normalize_identity_text(companion["title"])
        for target in targets:
            if str(Path(target["source_rel"]).parent).casefold() != companion_dir:
                continue
            stem_score = difflib.SequenceMatcher(
                None, companion_stem, normalized_work_title(Path(target["source_rel"]).stem)
            ).ratio()
            title_score = difflib.SequenceMatcher(
                None, companion_title, normalize_identity_text(target["title"])
            ).ratio()
            if stem_score >= 0.9 and title_score >= 0.9:
                con.execute(
                    """INSERT INTO companion_candidates
                    (companion_artifact_id,candidate_paper_id,score,basis)
                    VALUES (?,?,?,?)""",
                    (
                        companion["artifact_id"],
                        target["paper_id"],
                        min(stem_score, title_score),
                        "same-directory + stem/title similarity; confirmation required",
                    ),
                )

    source_fingerprint = hashlib.sha256(
        "\n".join(sorted(source_parts)).encode("utf-8")
    ).hexdigest()
    root_row = con.execute("SELECT value FROM meta WHERE key='source_roots'").fetchone()
    coverage_fingerprint = hashlib.sha256(
        ((root_row[0] if root_row else "") + "\n" + "\n".join(sorted(coverage_parts))).encode("utf-8")
    ).hexdigest()
    ranking_fingerprint = hashlib.sha256(
        "\n".join(sorted(ranking_parts)).encode("utf-8")
    ).hexdigest()
    for key, value in (
        ("corpus_fingerprint", source_fingerprint),
        ("source_fingerprint", source_fingerprint),
        ("coverage_fingerprint", coverage_fingerprint),
        ("ranking_fingerprint", ranking_fingerprint),
    ):
        con.execute(
            "INSERT INTO meta(key,value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
    return source_fingerprint


def index_summary(con: sqlite3.Connection, db_path: Path) -> dict:
    fingerprint = con.execute(
        "SELECT value FROM meta WHERE key='corpus_fingerprint'"
    ).fetchone()
    profile_path = con.execute(
        "SELECT value FROM meta WHERE key='profile_path'"
    ).fetchone()
    profile_hash = con.execute(
        "SELECT value FROM meta WHERE key='profile_hash'"
    ).fetchone()
    return {
        "documents": con.execute("SELECT count(*) FROM documents").fetchone()[0],
        "papers": con.execute("SELECT count(*) FROM papers").fetchone()[0],
        "chunks": con.execute("SELECT count(*) FROM chunks").fetchone()[0],
        "errors": con.execute("SELECT count(*) FROM documents WHERE error <> ''").fetchone()[0],
        "provisional_identities": con.execute(
            "SELECT count(*) FROM papers WHERE identity_status IN "
            "('PROVISIONAL_FILENAME','COMPANION_UNBOUND')"
        ).fetchone()[0],
        "unbound_companions": con.execute(
            "SELECT count(*) FROM documents WHERE identity_status='COMPANION_UNBOUND'"
        ).fetchone()[0],
        "companion_suggestions": con.execute(
            "SELECT count(*) FROM companion_candidates WHERE status='PENDING'"
        ).fetchone()[0],
        "metadata_conflicts": con.execute(
            "SELECT count(*) FROM papers WHERE metadata_conflict <> ''"
        ).fetchone()[0],
        "bibliographic_gaps": con.execute(
            "SELECT count(*) FROM papers WHERE title='' OR authors='' OR year='' OR journal=''"
        ).fetchone()[0],
        "roles": dict(con.execute("SELECT role,count(*) FROM documents GROUP BY role")),
        "corpus_fingerprint": fingerprint[0] if fingerprint else "",
        "profile_path": profile_path[0] if profile_path else "",
        "profile_hash": profile_hash[0] if profile_hash else "",
        **retrieval_fingerprints(con),
        "db_bytes": db_path.stat().st_size if db_path.exists() else 0,
    }


def build_index(
    db_path: Path,
    root_specs: list[tuple[Path, str]],
    workers: int,
    manifest_path: Path | None = None,
    profile_path: Path | None = None,
) -> None:
    root_specs = validate_locations(db_path, root_specs)
    if profile_path is None:
        profile_path = discover_corpus_profile(root_specs)
    manifest = load_manifest(manifest_path, root_specs)
    profiles = load_corpus_profile(profile_path, root_specs)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = db_path.with_name(f".{db_path.name}.building-{uuid.uuid4().hex}")
    paths = scan_sources(root_specs)
    started = time.perf_counter()
    con: sqlite3.Connection | None = None
    try:
        con = sqlite3.connect(temporary)
        initialize_index(con, root_specs, manifest_path, profile_path)
        with con:
            for item in extract_many(extraction_inputs(paths, manifest, profiles), workers):
                insert_document(con, item)
            if paths and con.execute("SELECT count(*) FROM chunks").fetchone()[0] == 0:
                errors = con.execute(
                    "SELECT count(*) FROM documents WHERE error <> ''"
                ).fetchone()[0]
                raise RuntimeError(
                    "No searchable passages were extracted; "
                    f"documents={len(paths)} extraction_errors={errors}. "
                    "Check pdftotext, file integrity, and source formats."
                )
            refresh_papers(con)
        con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('optimize')")
        con.execute("INSERT INTO papers_fts(papers_fts) VALUES('optimize')")
        con.commit()
        con.close()
        con = None
        os.replace(temporary, db_path)
        final = open_index(db_path)
        summary = index_summary(final, db_path)
        final.close()
        summary.update(
            {
                "command": "build",
                "scanned": len(paths),
                "elapsed_s": round(time.perf_counter() - started, 2),
            }
        )
        print(json.dumps(summary, ensure_ascii=False))
    finally:
        if con is not None:
            con.close()
        if temporary.exists():
            temporary.unlink()


def update_index(
    db_path: Path,
    root_specs: list[tuple[Path, str]],
    workers: int,
    verify_hash: bool = False,
    manifest_path: Path | None = None,
    profile_path: Path | None = None,
) -> None:
    root_specs = validate_locations(db_path, root_specs)
    if manifest_path is None:
        manifest_path = manifest_path_from_meta(db_path)
    if profile_path is None:
        profile_con = open_index(db_path)
        profile_row = profile_con.execute(
            "SELECT value FROM meta WHERE key='profile_path'"
        ).fetchone()
        profile_con.close()
        profile_path = Path(profile_row[0]) if profile_row and profile_row[0] else None
    if profile_path is None:
        profile_path = discover_corpus_profile(root_specs)
    manifest = load_manifest(manifest_path, root_specs)
    profiles = load_corpus_profile(profile_path, root_specs)
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    old_profile_row = con.execute(
        "SELECT value FROM meta WHERE key='profile_hash'"
    ).fetchone()
    current_profile_hash = file_sha256(profile_path) if profile_path else ""
    profile_changed = (old_profile_row[0] if old_profile_row else "") != current_profile_hash
    started = time.perf_counter()
    paths = scan_sources(root_specs)
    scanned = {
        canonical_path(Path(path)): (path, root, root_role)
        for path, root, root_role in paths
    }
    existing = {
        canonical_path(Path(row["source_path"])): row
        for row in con.execute(
            "SELECT doc_id,source_path,source_root,root_role,size,mtime_ns,content_hash,"
            "manifest_hash,profile_rule_hash "
            "FROM documents"
        )
    }
    removed = [row for key, row in existing.items() if key not in scanned]
    changed: list[tuple[str, str, str]] = []
    added = 0
    replaced = 0
    verified_hashes = 0
    hash_mismatches = 0
    for key, triple in scanned.items():
        path = Path(triple[0])
        root_role = triple[2]
        root_profile = profiles.get(canonical_path(Path(triple[1])))
        info = os.stat(_filesystem_path(path))
        row = existing.get(key)
        if row is None:
            changed.append(triple)
            added += 1
            continue
        metadata_changed = (
            row["size"] != info.st_size
            or row["mtime_ns"] != info.st_mtime_ns
            or row["root_role"] != root_role
            or row["manifest_hash"]
            != manifest_record_hash(manifest.get(canonical_path(path)))
            or row["profile_rule_hash"] != profile_rule_hash(path, root_profile)
        )
        if metadata_changed:
            changed.append(triple)
            replaced += 1
            continue
        if verify_hash:
            verified_hashes += 1
            current_hash = file_sha256(path)
            if current_hash != row["content_hash"]:
                hash_mismatches += 1
                changed.append(triple)
                replaced += 1

    extracted = list(extract_many(extraction_inputs(changed, manifest, profiles), workers))
    extraction_failures_preserved = 0
    try:
        with con:
            for row in removed:
                delete_document(con, row["doc_id"])
            for item in extracted:
                old = con.execute(
                    "SELECT doc_id FROM documents WHERE source_path=?",
                    (item["source_path"],),
                ).fetchone()
                extraction_failed = item["error"] or (
                    not item["chunks"] and item["extension"] not in OPAQUE_SUFFIXES
                )
                if old and extraction_failed:
                    extraction_failures_preserved += 1
                    continue
                if old:
                    delete_document(con, old["doc_id"])
                insert_document(con, item)
            if paths and con.execute("SELECT count(*) FROM chunks").fetchone()[0] == 0:
                raise RuntimeError(
                    "Update would leave the index with no searchable passages; "
                    "existing searchable records were preserved where possible."
                )
            con.execute(
                "INSERT INTO meta(key,value) VALUES ('source_roots',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (serialize_root_specs(root_specs),),
            )
            con.execute(
                "INSERT INTO meta(key,value) VALUES ('last_update_utc',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(int(time.time())),),
            )
            con.execute(
                "INSERT INTO meta(key,value) VALUES ('manifest_path',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(manifest_path.resolve()) if manifest_path else "",),
            )
            con.execute(
                "INSERT INTO meta(key,value) VALUES ('profile_path',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(profile_path.resolve()) if profile_path else "",),
            )
            con.execute(
                "INSERT INTO meta(key,value) VALUES ('profile_hash',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (file_sha256(profile_path) if profile_path else "",),
            )
            refresh_papers(con)
        if removed or extracted:
            con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('optimize')")
            con.execute("INSERT INTO papers_fts(papers_fts) VALUES('optimize')")
            con.commit()
        summary = index_summary(con, db_path)
        summary.update(
            {
                "command": "update",
                "scanned": len(paths),
                "added": added,
                "replaced": replaced,
                "removed": len(removed),
                "unchanged": len(paths) - added - replaced,
                "verify_hash": verify_hash,
                "verified_hashes": verified_hashes,
                "hash_mismatches": hash_mismatches,
                "extraction_failures_preserved": extraction_failures_preserved,
                "profile_changed": profile_changed,
                "elapsed_s": round(time.perf_counter() - started, 2),
            }
        )
        print(json.dumps(summary, ensure_ascii=False))
    finally:
        con.close()


def build_search_sql(roles: list[str], journal: str | None) -> tuple[str, list[object]]:
    clauses = ["chunks_fts MATCH ?"]
    parameters: list[object] = []
    if roles:
        invalid = sorted(set(roles) - CANONICAL_ROLES)
        if invalid:
            raise ValueError(f"Unknown evidence role(s): {', '.join(invalid)}")
        clauses.append("d.role IN (" + ",".join("?" for _ in roles) + ")")
        parameters.extend(roles)
    else:
        # Ordinary research retrieval excludes both process records and optional
        # miscellaneous/replication attachments.  Request those roles explicitly.
        clauses.append(
            "d.role IN (" + ",".join("?" for _ in DEFAULT_RETRIEVAL_ROLES) + ")"
        )
        parameters.extend(DEFAULT_RETRIEVAL_ROLES)
    if journal:
        clauses.append("d.journal LIKE ?")
        parameters.append(f"%{journal}%")
    return " AND ".join(clauses), parameters


def safe_fts_query(query: str, match: str = "all") -> str:
    """Convert ordinary text into a safely quoted FTS5 query."""
    tokens = re.findall(r"\w+", query, flags=re.UNICODE)
    if not tokens:
        raise ValueError("Search query contains no searchable text")
    quoted = [f'"{token}"' for token in tokens]
    if match == "phrase":
        return '"' + " ".join(tokens) + '"'
    if match == "all":
        return " ".join(quoted)
    if match == "any":
        return " OR ".join(quoted)
    raise ValueError(f"Unknown lexical match policy: {match}")


def corpus_fingerprint(con: sqlite3.Connection) -> str:
    row = con.execute("SELECT value FROM meta WHERE key='corpus_fingerprint'").fetchone()
    return row[0] if row else ""


def retrieval_fingerprints(con: sqlite3.Connection) -> dict[str, str]:
    rows = dict(
        con.execute(
            "SELECT key,value FROM meta WHERE key IN "
            "('source_fingerprint','coverage_fingerprint','ranking_fingerprint')"
        )
    )
    return {
        "source_fingerprint": rows.get("source_fingerprint", corpus_fingerprint(con)),
        "coverage_fingerprint": rows.get("coverage_fingerprint", ""),
        "ranking_fingerprint": rows.get("ranking_fingerprint", ""),
    }


def paper_filters(roles: list[str], journal: str | None) -> tuple[str, list[object]]:
    clauses = []
    params: list[object] = []
    if roles:
        invalid = sorted(set(roles) - CANONICAL_ROLES)
        if invalid:
            raise ValueError(f"Unknown evidence role(s): {', '.join(invalid)}")
        clauses.append(
            "EXISTS (SELECT 1 FROM documents d WHERE d.paper_id=p.paper_id "
            "AND d.role IN (" + ",".join("?" for _ in roles) + ") "
            "AND d.artifact_kind <> 'STRUCTURED_COMPANION')"
        )
        params.extend(roles)
    else:
        clauses.append(
            "EXISTS (SELECT 1 FROM documents d WHERE d.paper_id=p.paper_id "
            "AND d.role IN ("
            + ",".join("?" for _ in DEFAULT_RETRIEVAL_ROLES)
            + ") AND d.artifact_kind <> 'STRUCTURED_COMPANION')"
        )
        params.extend(DEFAULT_RETRIEVAL_ROLES)
    if journal:
        clauses.append("p.journal LIKE ?")
        params.append(f"%{journal}%")
    return " AND ".join(clauses), params


def lexical_candidates(
    con: sqlite3.Connection,
    query: str,
    limit: int,
    roles: list[str],
    journal: str | None,
    raw_fts: bool,
    match: str,
) -> list[dict]:
    where, filters = paper_filters(roles, journal)
    fts_query = query if raw_fts else safe_fts_query(query, match)
    sql = f"""
      SELECT p.*,
             bm25(papers_fts, 5.0, 1.5, 3.0, 2.0, 1.5, 0.5) AS lexical_score
      FROM papers_fts
      JOIN papers p ON p.paper_pk = papers_fts.rowid
      WHERE papers_fts MATCH ? AND {where}
      ORDER BY lexical_score ASC
      LIMIT ?
    """
    try:
        return [dict(row) for row in con.execute(sql, [fts_query, *filters, limit])]
    except sqlite3.OperationalError as exc:
        raise ValueError(f"Invalid FTS5 query {query!r}: {exc}") from exc


def unpack_vector(blob: bytes, dimensions: int) -> tuple[float, ...]:
    return struct.unpack(f"<{dimensions}f", blob)


def semantic_candidates(
    con: sqlite3.Connection,
    query_vector: list[float],
    model: str,
    model_revision: str,
    document_prefix: str,
    query_prefix: str,
    limit: int,
    roles: list[str],
    journal: str | None,
) -> list[dict]:
    where, filters = paper_filters(roles, journal)
    sql = f"""
        SELECT p.*,e.dimensions,e.vector
      FROM papers p JOIN embeddings e ON e.paper_id=p.paper_id
      WHERE e.model=? AND e.model_revision=? AND e.document_prefix=? AND e.query_prefix=?
        AND e.content_fingerprint=p.retrieval_fingerprint
        AND {where}
    """
    qnorm = math.sqrt(sum(value * value for value in query_vector)) or 1.0
    scored = []
    for row in con.execute(
        sql, [model, model_revision, document_prefix, query_prefix, *filters]
    ):
        vector = unpack_vector(row["vector"], row["dimensions"])
        if len(vector) != len(query_vector):
            continue
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        score = sum(a * b for a, b in zip(query_vector, vector)) / (qnorm * norm)
        item = {key: row[key] for key in row.keys() if key not in {"vector", "dimensions"}}
        item["semantic_score"] = score
        scored.append(item)
    scored.sort(key=lambda item: item["semantic_score"], reverse=True)
    return scored[:limit]


def reciprocal_rank_fusion(
    ranked_lists: list[list[dict]], limit: int, k: int = 60
) -> list[dict]:
    fused: dict[str, dict] = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            paper_id = item["paper_id"]
            target = fused.setdefault(paper_id, dict(item, fusion_score=0.0))
            target.update({key: value for key, value in item.items() if key.endswith("_score")})
            target["fusion_score"] += 1.0 / (k + rank)
    return sorted(fused.values(), key=lambda item: item["fusion_score"], reverse=True)[:limit]


def fulltext_rescue_candidates(
    con: sqlite3.Connection,
    query: str,
    limit: int,
    chunk_pool: int,
    roles: list[str],
    journal: str | None,
    match: str,
) -> list[dict]:
    """Search passages globally with a pre-pool per-paper cap, then aggregate."""
    paper_where, paper_params = paper_filters(roles, journal)
    active_roles = roles or list(DEFAULT_RETRIEVAL_ROLES)
    chunk_role_sql = "d.role IN (" + ",".join("?" for _ in active_roles) + ")"
    fts_query = safe_fts_query(query, match)
    rows = list(
        con.execute(
            f"""WITH matched AS (
                   SELECT rowid,
                          bm25(chunks_fts,1.0,1.5,1.0,0.2,0.2) AS passage_score
                   FROM chunks_fts
                   WHERE chunks_fts MATCH ?
                 ), ranked AS (
                   SELECT p.*,c.chunk_id,c.locator_id,d.artifact_id,d.artifact_kind,
                          d.role,d.source_path,d.source_rel,d.content_hash,c.page,c.section,
                          c.char_start,c.char_end,c.text,matched.passage_score,
                          row_number() OVER (
                            PARTITION BY p.paper_id
                            ORDER BY matched.passage_score ASC,c.chunk_id ASC
                          ) AS paper_hit_rank
                   FROM matched
                   JOIN chunks c ON c.chunk_id=matched.rowid
                   JOIN documents d ON d.doc_id=c.doc_id
                   JOIN papers p ON p.paper_id=d.paper_id
                   WHERE {chunk_role_sql}
                     AND EXISTS (
                       SELECT 1 FROM documents eligible
                       WHERE eligible.paper_id=p.paper_id
                         AND eligible.role IN ('MAIN_ARTICLE','ONLINE_APPENDIX','COMMENT_CORRECTION')
                         AND eligible.artifact_kind<>'STRUCTURED_COMPANION'
                     )
                     AND {paper_where}
                 )
                 SELECT * FROM ranked
                 WHERE paper_hit_rank=1
                 ORDER BY passage_score ASC
                 LIMIT ?""",
            [fts_query, *active_roles, *paper_params, chunk_pool],
        )
    )
    grouped: dict[str, dict] = {}
    contribution_counts: dict[str, int] = {}
    for rank, row in enumerate(rows, start=1):
        paper_id = row["paper_id"]
        item = grouped.setdefault(
            paper_id,
            {
                key: row[key]
                for key in row.keys()
                if key
                not in {
                    "chunk_id", "locator_id", "artifact_id", "artifact_kind", "role",
                    "source_path", "source_rel", "content_hash", "page", "section",
                    "char_start", "char_end", "text", "passage_score",
                }
            },
        )
        count = contribution_counts.get(paper_id, 0)
        item["fulltext_score"] = item.get("fulltext_score", 0.0) + 1.0 / (60 + rank)
        contribution_counts[paper_id] = count + 1
        item.setdefault("rescue_passages", []).append(
            {
                    "chunk_id": row["chunk_id"],
                    "locator_id": row["locator_id"],
                    "artifact_id": row["artifact_id"],
                    "artifact_kind": row["artifact_kind"],
                    "role": row["role"],
                    "source_path": row["source_path"],
                    "source_rel": row["source_rel"],
                    "content_hash": row["content_hash"],
                    "page": row["page"],
                    "section": row["section"],
                    "char_start": row["char_start"],
                    "char_end": row["char_end"],
                    "chunk_text": row["text"],
                    "passage_score": row["passage_score"],
            }
        )
    return sorted(
        grouped.values(), key=lambda item: item.get("fulltext_score", 0.0), reverse=True
    )[:limit]


def load_embedding_model(
    model: str,
    model_revision: str,
    allow_model_download: bool = False,
):
    if not model_revision and not Path(model).expanduser().exists():
        raise ValueError(
            "A pinned --model-revision is required for a named semantic model; "
            "a local model directory may be used without one"
        )
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Semantic retrieval requires the optional sentence-transformers package"
        ) from exc
    kwargs = {"local_files_only": not allow_model_download}
    if model_revision:
        kwargs["revision"] = model_revision
    return SentenceTransformer(model, **kwargs)


def encode_query(model_object, query: str) -> list[float]:
    vector = model_object.encode([query], normalize_embeddings=True)[0]
    return [float(value) for value in vector]


def best_passages(
    con: sqlite3.Connection,
    paper_id: str,
    query: str,
    limit: int,
    roles: list[str],
    raw_fts: bool,
    match: str,
) -> list[dict]:
    where, filters = build_search_sql(roles, None)
    fts_query = query if raw_fts else safe_fts_query(query, match)
    sql = f"""
      SELECT c.chunk_id,bm25(chunks_fts,1.0,2.0,1.2,0.3,0.3) lexical_score,
             d.artifact_id,d.artifact_kind,d.role,d.source_path,d.source_rel,d.content_hash,
             c.page,c.section,c.chunk_index,c.char_start,c.char_end,c.locator_id,c.text
      FROM chunks_fts
      JOIN chunks c ON c.chunk_id=chunks_fts.rowid
      JOIN documents d ON d.doc_id=c.doc_id
      WHERE {where} AND d.paper_id=?
       ORDER BY lexical_score ASC,
                CASE d.artifact_kind WHEN 'PRIMARY_PDF' THEN 0 WHEN 'APPENDIX_PDF' THEN 1
                WHEN 'SOURCE_DOCUMENT' THEN 2 WHEN 'STRUCTURED_COMPANION' THEN 3 ELSE 4 END,
               c.chunk_id ASC
      LIMIT ?
    """
    try:
        rows = con.execute(sql, [fts_query, *filters, paper_id, limit])
        output = []
        for row in rows:
            item = dict(row)
            item["chunk_text"] = item.pop("text")
            output.append(item)
        return output
    except sqlite3.OperationalError as exc:
        raise ValueError(
            f"Passage retrieval failed for query {query!r}; this is not evidence absence"
        ) from exc


def artifacts_for_paper(con: sqlite3.Connection, paper_id: str) -> list[dict]:
    return [
        dict(row)
        for row in con.execute(
            """SELECT artifact_id,artifact_kind,role,root_role,source_path,source_rel,
                      artifact_version,access_status,role_confidence,role_basis,
                      metadata_provenance,content_hash,error
               FROM documents WHERE paper_id=? ORDER BY
               CASE artifact_kind WHEN 'PRIMARY_PDF' THEN 0 WHEN 'APPENDIX_PDF' THEN 1
               WHEN 'SOURCE_DOCUMENT' THEN 2 WHEN 'STRUCTURED_COMPANION' THEN 3 ELSE 4 END""",
            (paper_id,),
        )
    ]


def companion_suggestions(db_path: Path, output_format: str) -> None:
    """Emit conservative binding candidates; never mutate paper identity."""
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    rows = list(
        con.execute(
            """SELECT cc.*,d.source_path,d.source_rel,d.title AS companion_title,
                      p.title AS candidate_title,p.doi,p.identity_status
               FROM companion_candidates cc
               JOIN documents d ON d.artifact_id=cc.companion_artifact_id
               JOIN papers p ON p.paper_id=cc.candidate_paper_id
               ORDER BY cc.score DESC,d.source_rel"""
        )
    )
    con.close()
    payload = [dict(row) for row in rows]
    if output_format == "json":
        print(json.dumps({"suggestions": payload, "count": len(payload)}, ensure_ascii=False))
    else:
        for row in payload:
            print(json.dumps(row, ensure_ascii=False))


def passage_search(
    db_path: Path,
    paper_id: str,
    query: str,
    limit: int,
    strategy: str,
    model: str,
    model_revision: str,
    document_prefix: str,
    query_prefix: str,
    allow_model_download: bool = False,
) -> None:
    """Retrieve evidence only inside one already-selected paper."""
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    rows = list(
        con.execute(
            """SELECT c.chunk_id,c.locator_id,c.page,c.section,c.char_start,c.char_end,c.text,
                      d.artifact_id,d.artifact_kind,d.role,d.source_path,d.content_hash
               FROM chunks c JOIN documents d ON d.doc_id=c.doc_id
               WHERE d.paper_id=?
                 AND d.role IN ('MAIN_ARTICLE','ONLINE_APPENDIX','COMMENT_CORRECTION')
               ORDER BY CASE d.artifact_kind WHEN 'PRIMARY_PDF' THEN 0
                        WHEN 'APPENDIX_PDF' THEN 1 WHEN 'SOURCE_DOCUMENT' THEN 2
                        WHEN 'STRUCTURED_COMPANION' THEN 3 ELSE 4 END,
                        c.page,c.chunk_index""",
            (paper_id,),
        )
    )
    if not rows:
        con.close()
        raise ValueError(f"No passages found for paper_id: {paper_id}")
    if strategy == "lexical":
        results = best_passages(con, paper_id, query, limit, [], False, "all")
    elif strategy == "semantic":
        if not model:
            con.close()
            raise ValueError("--model is required for semantic passage retrieval")
        model_object = load_embedding_model(
            model, model_revision, allow_model_download
        )
        qvector = encode_query(model_object, query_prefix + query)
        vectors = model_object.encode(
            [document_prefix + row["text"] for row in rows],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        scored = []
        for row, vector in zip(rows, vectors):
            item = dict(row)
            item["semantic_score"] = sum(
                a * float(b) for a, b in zip(qvector, vector)
            )
            item["chunk_text"] = item.pop("text")
            scored.append(item)
        results = sorted(scored, key=lambda item: item["semantic_score"], reverse=True)[:limit]
    else:
        con.close()
        raise ValueError("Passage retrieval strategy must be lexical or semantic")
    con.close()
    for item in results:
        print(json.dumps(dict(item, layer="passage", strategy=strategy), ensure_ascii=False))


def search_index(
    db_path: Path,
    query: str | list[str],
    limit: int,
    passages_per_work: int,
    roles: list[str],
    journal: str | None,
    output_format: str,
    raw_fts: bool = False,
    match: str = "all",
    strategy: str = "lexical",
    model: str = "",
    model_revision: str = "",
    document_prefix: str = "",
    query_prefix: str = "",
    full_text_rescue: bool = False,
    rescue_chunk_pool: int = 1000,
    allow_model_download: bool = False,
) -> None:
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    queries = [query] if isinstance(query, str) else list(dict.fromkeys(query))
    if not queries:
        con.close()
        raise ValueError("At least one query branch is required")
    if raw_fts and len(queries) > 1:
        con.close()
        raise ValueError("--raw-fts accepts one query branch only")
    if not raw_fts and any(re.search(r"[\u3400-\u9fff]{2,}", branch) for branch in queries):
        print(
            "warning: unicode61 treats contiguous Chinese letters as one token; "
            "for a mainly English corpus, formulate English scholarly query branches "
            "or use a benchmarked multilingual semantic arm",
            file=sys.stderr,
        )
    candidate_pool = max(limit * 4, 50)
    lexical_arms = [
        lexical_candidates(con, branch, candidate_pool, roles, journal, raw_fts, match)
        for branch in queries
    ]
    rescue_arms = (
        [
            fulltext_rescue_candidates(
                con, branch, candidate_pool, rescue_chunk_pool, roles, journal, match
            )
            for branch in queries
        ]
        if full_text_rescue
        else []
    )
    if strategy in {"semantic", "hybrid"}:
        if not model:
            con.close()
            raise ValueError("--model is required for semantic or hybrid retrieval")
        model_object = load_embedding_model(
            model, model_revision, allow_model_download
        )
        semantic_arms = [
            semantic_candidates(
                con,
                encode_query(model_object, query_prefix + branch),
                model,
                model_revision,
                document_prefix,
                query_prefix,
                candidate_pool,
                roles,
                journal,
            )
            for branch in queries
        ]
        if not any(semantic_arms):
            con.close()
            raise ValueError("No compatible paper embeddings found; run embed first")
    else:
        semantic_arms = []
    if strategy == "lexical":
        combined_arms = [*lexical_arms, *rescue_arms]
        candidates = (
            combined_arms[0][:limit]
            if len(combined_arms) == 1
            else reciprocal_rank_fusion(combined_arms, limit)
        )
    elif strategy == "semantic":
        combined_arms = [*semantic_arms, *rescue_arms]
        candidates = (
            combined_arms[0][:limit]
            if len(combined_arms) == 1
            else reciprocal_rank_fusion(combined_arms, limit)
        )
    elif strategy == "hybrid":
        candidates = reciprocal_rank_fusion(
            [*lexical_arms, *semantic_arms, *rescue_arms], limit
        )
    else:
        con.close()
        raise ValueError(f"Unknown retrieval strategy: {strategy}")

    fingerprints = retrieval_fingerprints(con)
    run_payload = json.dumps(
        {
            "ranking_fingerprint": fingerprints["ranking_fingerprint"],
            "queries": queries,
            "match": "raw" if raw_fts else match,
            "strategy": strategy,
            "model": model,
            "model_revision": model_revision,
            "document_prefix": document_prefix,
            "query_prefix": query_prefix,
            "roles": sorted(roles),
            "journal": journal or "",
            "limit": limit,
            "full_text_rescue": full_text_rescue,
            "rescue_chunk_pool": rescue_chunk_pool if full_text_rescue else 0,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    run_fingerprint = hashlib.sha256(run_payload.encode("utf-8")).hexdigest()
    groups = []
    for rank, item in enumerate(candidates, start=1):
        group = {key: value for key, value in item.items() if key != "paper_pk"}
        group.update(
            {
                "rank": rank,
                "strategy": strategy,
                "query_match": "raw" if raw_fts else match,
                "query_branches": queries,
                "full_text_rescue": full_text_rescue,
                "corpus_fingerprint": fingerprints["source_fingerprint"],
                **fingerprints,
                "retrieval_run_fingerprint": run_fingerprint,
                "artifacts": artifacts_for_paper(con, item["paper_id"]),
                "passages": [],
                "reranking_status": "PENDING_CODEX_STRUCTURAL_COMPARISON",
                "evidence_strength": "UNQUALIFIED",
            }
        )
        seen_locators = set()
        passage_arms = [
            best_passages(
                con, item["paper_id"], branch, passages_per_work, roles, raw_fts, match
            )
            for branch in queries
        ]
        # Round-robin allocation prevents the first query formulation from
        # consuming the full evidence budget before other retrieval branches
        # can contribute their distinct supporting location.
        max_arm = max((len(arm) for arm in passage_arms), default=0)
        for offset in range(max_arm):
            for arm in passage_arms:
                if offset >= len(arm):
                    continue
                passage = arm[offset]
                if passage["locator_id"] not in seen_locators:
                    group["passages"].append(passage)
                    seen_locators.add(passage["locator_id"])
                if len(group["passages"]) >= passages_per_work:
                    break
            if len(group["passages"]) >= passages_per_work:
                break
        groups.append(group)
    con.close()

    for group in groups:
        if output_format == "jsonl":
            print(json.dumps(group, ensure_ascii=False))
            continue
        print(f"paper_id: {group['paper_id']}")
        for key in ("title", "authors", "year", "journal", "doi"):
            print(f"{key}: {group[key]}")
        for key in ("lexical_score", "semantic_score", "fusion_score"):
            if key in group:
                print(f"{key}: {group[key]}")
        print("reranking_status: PENDING_CODEX_STRUCTURAL_COMPARISON")
        print("evidence_strength: UNQUALIFIED")
        for passage in group["passages"]:
            location = f"page={passage['page']} section={passage['section']}"
            print(
                f"  passage chunk_id={passage['chunk_id']} role={passage['role']} {location}"
            )
            print(f"  {passage['chunk_text']}")
        print()


def inspect_index(
    db_path: Path, chunk_id: int | None, paper_id: str | None, context: int
) -> None:
    if chunk_id is None and not paper_id:
        raise ValueError("inspect requires --chunk-id or --paper-id")
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    if chunk_id is not None:
        anchor = con.execute(
            "SELECT doc_id FROM chunks WHERE chunk_id=?", (chunk_id,)
        ).fetchone()
        if not anchor:
            con.close()
            raise ValueError(f"Unknown chunk_id: {chunk_id}")
        rows = con.execute(
            """SELECT c.chunk_id,c.locator_id,d.paper_id,d.artifact_id,d.artifact_kind,d.role,d.root_role,d.title,d.authors,
                      d.year,d.journal,d.doi,d.source_path,d.source_rel,c.page,
                      c.section,c.chunk_index,c.char_start,c.char_end,c.text
               FROM chunks c JOIN documents d ON d.doc_id=c.doc_id
               WHERE c.doc_id=? AND c.chunk_id BETWEEN ? AND ?
               ORDER BY c.chunk_id""",
            (
                anchor["doc_id"],
                chunk_id - context,
                chunk_id + context,
            ),
        )
    else:
        rows = con.execute(
            """SELECT c.chunk_id,c.locator_id,d.paper_id,d.artifact_id,d.artifact_kind,d.role,d.root_role,d.title,d.authors,
                      d.year,d.journal,d.doi,d.source_path,d.source_rel,c.page,
                      c.section,c.chunk_index,c.char_start,c.char_end,c.text
               FROM chunks c JOIN documents d ON d.doc_id=c.doc_id
               WHERE d.paper_id=? ORDER BY d.role,c.page,c.chunk_index""",
            (paper_id,),
        )
    found = False
    for row in rows:
        found = True
        print(json.dumps(dict(row), ensure_ascii=False))
    con.close()
    if not found:
        raise ValueError(f"No passages found for paper_id: {paper_id}")


def lookup_index(
    db_path: Path, doi: str | None, title: str | None, output_format: str
) -> None:
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    if doi:
        normalized = normalize_doi(doi)
        if not normalized:
            con.close()
            raise ValueError(f"Invalid DOI: {doi}")
        rows = list(con.execute("SELECT * FROM papers WHERE doi=?", (normalized,)))
        lookup = {"kind": "doi", "value": normalized}
    elif title:
        normalized = normalize_identity_text(title)
        rows = list(
            con.execute("SELECT * FROM papers WHERE normalized_title=?", (normalized,))
        )
        lookup = {"kind": "title", "value": normalized}
    else:
        con.close()
        raise ValueError("lookup requires --doi or --title")
    fingerprint = corpus_fingerprint(con)
    output = [
        dict(
            dict(row),
            lookup=lookup,
            corpus_fingerprint=fingerprint,
            artifacts=artifacts_for_paper(con, row["paper_id"]),
        )
        for row in rows
    ]
    con.close()
    if output_format == "json":
        print(json.dumps({"matches": output, "count": len(output)}, ensure_ascii=False))
    else:
        for item in output:
            print(json.dumps(item, ensure_ascii=False))


def export_manifest(db_path: Path, output_path: Path) -> None:
    root_specs = stored_root_specs(db_path)
    output_path = output_path.resolve()
    for root, _ in root_specs:
        if path_is_within(output_path, root):
            raise ValueError(f"Manifest output must be outside source roots: {output_path}")
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """SELECT d.source_rel,d.paper_id,d.role,d.artifact_kind,d.artifact_version,
                  d.access_status,d.role_confidence,d.role_basis,d.content_hash,
                  p.identity_status,p.title,p.authors,p.year,p.journal,p.doi,p.abstract,
                  p.keywords,p.metadata_provenance
           FROM documents d JOIN papers p ON p.paper_id=d.paper_id
           ORDER BY d.source_rel"""
    )
    records = []
    for row in rows:
        record = {
            "path": row["source_rel"],
            "paper_id": row["paper_id"],
            "doi": row["doi"],
            "title": row["title"],
            "authors": row["authors"],
            "year": row["year"],
            "journal": row["journal"],
            "abstract": row["abstract"],
            "keywords": row["keywords"],
            "role": row["role"],
            "artifact_kind": row["artifact_kind"],
            "artifact_version": row["artifact_version"],
            "access_status": row["access_status"],
            "role_confidence": row["role_confidence"],
            "role_basis": row["role_basis"],
            "metadata_provenance": json.loads(row["metadata_provenance"] or "{}"),
            "identity_status": row["identity_status"],
            "content_hash": row["content_hash"],
        }
        records.append(record)
    con.close()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.writing-{uuid.uuid4().hex}")
    try:
        temporary.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
            "utf-8",
        )
        os.replace(temporary, output_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(
        json.dumps(
            {"command": "manifest-export", "records": len(records), "output": str(output_path)},
            ensure_ascii=False,
        )
    )


def embed_index(
    db_path: Path,
    model: str,
    model_revision: str,
    document_prefix: str,
    query_prefix: str,
    batch_size: int,
    allow_model_download: bool = False,
) -> None:
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    rows = list(
        con.execute(
            """SELECT p.paper_id,p.retrieval_fingerprint,p.title,p.abstract,p.keywords,p.headings
               FROM papers p JOIN papers_fts pf ON pf.rowid=p.paper_pk
               WHERE EXISTS (SELECT 1 FROM documents d WHERE d.paper_id=p.paper_id
                             AND d.role IN ('MAIN_ARTICLE','ONLINE_APPENDIX','COMMENT_CORRECTION')
                             AND d.artifact_kind<>'STRUCTURED_COMPANION')
               ORDER BY p.paper_id"""
        )
    )
    if not rows:
        con.close()
        raise ValueError("Index contains no papers to embed")
    model_object = load_embedding_model(model, model_revision, allow_model_download)
    texts = [
        document_prefix
        + row["title"]
        + "\n"
        + row["abstract"]
        + "\n"
        + row["keywords"]
        + "\n"
        + row["headings"]
        for row in rows
    ]
    vectors = model_object.encode(
        texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=True
    )
    with con:
        con.execute(
            "DELETE FROM embeddings WHERE model=? AND model_revision=?",
            (model, model_revision),
        )
        for row, vector in zip(rows, vectors):
            values = [float(value) for value in vector]
            con.execute(
                """INSERT INTO embeddings
                (paper_id,model,model_revision,document_prefix,query_prefix,
                 content_fingerprint,dimensions,vector)
                VALUES (?,?,?,?,?,?,?,?)""",
                (
                    row["paper_id"],
                    model,
                    model_revision,
                    document_prefix,
                    query_prefix,
                    row["retrieval_fingerprint"],
                    len(values),
                    struct.pack(f"<{len(values)}f", *values),
                ),
            )
    print(
        json.dumps(
            {
                "command": "embed",
                "papers": len(rows),
                "model": model,
                "model_revision": model_revision,
                "document_prefix": document_prefix,
                "query_prefix": query_prefix,
                "corpus_fingerprint": corpus_fingerprint(con),
            },
            ensure_ascii=False,
        )
    )
    con.close()


def _open_citation_ledger(path: Path) -> sqlite3.Connection:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    columns = [
        row[1] for row in con.execute("PRAGMA table_info(citation_evidence)")
    ]
    legacy_rows: list[dict] = []
    if columns and "evidence_id" not in columns:
        legacy_rows = [
            dict(zip(columns, row))
            for row in con.execute("SELECT * FROM citation_evidence")
        ]
        legacy_name = f"citation_evidence_legacy_{int(time.time())}"
        con.execute(f"ALTER TABLE citation_evidence RENAME TO {legacy_name}")
    con.execute(
        """CREATE TABLE IF NOT EXISTS citation_evidence (
          evidence_id TEXT PRIMARY KEY,
          claim_id TEXT NOT NULL,
          claim_text TEXT NOT NULL,
          verdict TEXT NOT NULL,
          rationale TEXT NOT NULL,
          paper_id TEXT NOT NULL,
          artifact_id TEXT NOT NULL,
          chunk_id INTEGER NOT NULL,
          locator_id TEXT NOT NULL,
          page INTEGER,
          section TEXT NOT NULL,
          source_hash TEXT NOT NULL,
          supporting_passage TEXT NOT NULL,
          bibliography_fingerprint TEXT NOT NULL,
          verified_at TEXT NOT NULL
        )"""
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS citation_evidence_claim_idx "
        "ON citation_evidence(claim_id)"
    )
    for record in legacy_rows:
        evidence_id = "ev:" + hashlib.sha256(
            "|".join(
                [
                    str(record.get("claim_id", "")),
                    str(record.get("paper_id", "")),
                    str(record.get("locator_id", "")),
                ]
            ).encode("utf-8")
        ).hexdigest()[:32]
        con.execute(
            """INSERT OR IGNORE INTO citation_evidence
            (evidence_id,claim_id,claim_text,verdict,rationale,paper_id,artifact_id,
             chunk_id,locator_id,page,section,source_hash,supporting_passage,
             bibliography_fingerprint,verified_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                evidence_id,
                record.get("claim_id", ""),
                record.get("claim_text", ""),
                record.get("verdict", "UNCERTAIN"),
                record.get("rationale", ""),
                record.get("paper_id", ""),
                record.get("artifact_id", ""),
                record.get("chunk_id", 0),
                record.get("locator_id", ""),
                record.get("page"),
                record.get("section", ""),
                record.get("source_hash", ""),
                record.get("supporting_passage", ""),
                "",
                record.get("verified_at", ""),
            ),
        )
    con.commit()
    return con


def citation_record(
    db_path: Path,
    paper_id: str,
    chunk_id: int | None,
    ledger_path: Path | None = None,
    claim_id: str = "",
    claim_text: str = "",
    verdict: str = "",
    rationale: str = "",
) -> None:
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    paper = con.execute("SELECT * FROM papers WHERE paper_id=?", (paper_id,)).fetchone()
    if not paper:
        con.close()
        raise ValueError(f"Unknown paper_id: {paper_id}")
    identity_ok = (
        paper["identity_status"] in {"DOI", "MANIFEST_ID", "METADATA_KEY"}
        and not paper["metadata_conflict"]
    )
    missing_bibliography = [
        key for key in ("title", "authors", "year", "journal") if not paper[key]
    ]
    bibliography_provenance = json.loads(paper["metadata_provenance"] or "{}")
    low_truth_fields = [
        key
        for key in ("title", "authors", "year", "journal")
        if bibliography_provenance.get(key, "")
        in {
            "",
            "LEARNED_FILENAME_PATTERN",
            "FILENAME_FALLBACK",
            "MARKDOWN_HEADING",
            "PDF_DOCUMENT_METADATA",
            "MARKDOWN_FRONTMATTER",
        }
    ]
    binding = {"status": "NOT_RUN", "reason": "No claim location supplied"}
    if chunk_id is not None:
        row = con.execute(
            """SELECT c.chunk_id,c.locator_id,c.page,c.section,c.text,d.paper_id,
                      d.artifact_id,d.artifact_kind,d.role,d.source_path,d.content_hash
               FROM chunks c JOIN documents d ON d.doc_id=c.doc_id
               WHERE c.chunk_id=?""",
            (chunk_id,),
        ).fetchone()
        if not row or row["paper_id"] != paper_id:
            binding = {"status": "FAIL", "reason": "Chunk is absent or belongs to another paper"}
        elif row["role"] == "PROCESS_EVIDENCE":
            binding = {"status": "FAIL", "reason": "Process evidence cannot support a paper claim"}
        elif row["artifact_kind"] == "STRUCTURED_COMPANION":
            binding = {
                "status": "WARNING",
                "reason": "Companion text is navigational until checked against the primary PDF",
                "location": dict(row),
            }
        else:
            binding = {"status": "BOUND", "location": dict(row)}
    saved = None
    if ledger_path is not None:
        for root, _ in stored_root_specs(db_path):
            if path_is_within(ledger_path.resolve(), root):
                con.close()
                raise ValueError("Citation ledger must live outside every evidence root")
        if chunk_id is None or binding.get("status") != "BOUND":
            con.close()
            raise ValueError(
                "Saving claim evidence requires a valid primary/source --chunk-id; "
                "an unverified Markdown companion is navigation only"
            )
        if not claim_id or not claim_text or verdict not in {
            "SUPPORTED", "PARTIAL", "UNSUPPORTED", "UNCERTAIN"
        }:
            con.close()
            raise ValueError(
                "Ledger save requires --claim-id, --claim-text, and a valid --verdict"
            )
        location = binding["location"]
        verified_at = datetime.now(timezone.utc).isoformat()
        evidence_id = "ev:" + hashlib.sha256(
            "|".join([claim_id, paper_id, location["locator_id"]]).encode("utf-8")
        ).hexdigest()[:32]
        ledger = _open_citation_ledger(ledger_path)
        with ledger:
            ledger.execute(
                """INSERT INTO citation_evidence
                (evidence_id,claim_id,claim_text,verdict,rationale,paper_id,artifact_id,
                 chunk_id,locator_id,page,section,source_hash,supporting_passage,
                 bibliography_fingerprint,verified_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(evidence_id) DO UPDATE SET
                  claim_text=excluded.claim_text,verdict=excluded.verdict,
                  rationale=excluded.rationale,paper_id=excluded.paper_id,
                  artifact_id=excluded.artifact_id,chunk_id=excluded.chunk_id,
                  locator_id=excluded.locator_id,page=excluded.page,section=excluded.section,
                  source_hash=excluded.source_hash,
                  supporting_passage=excluded.supporting_passage,
                  bibliography_fingerprint=excluded.bibliography_fingerprint,
                  verified_at=excluded.verified_at""",
                (
                    evidence_id,
                    claim_id,
                    claim_text,
                    verdict,
                    rationale,
                    paper_id,
                    location["artifact_id"],
                    location["chunk_id"],
                    location["locator_id"],
                    location["page"],
                    location["section"],
                    location["content_hash"],
                    location["text"],
                    paper["bibliography_fingerprint"],
                    verified_at,
                ),
            )
        ledger.close()
        saved = {
            "ledger": str(ledger_path.resolve()),
            "claim_id": claim_id,
            "evidence_id": evidence_id,
            "verified_at": verified_at,
        }
    output = {
        "paper_id": paper_id,
        "identity_check": {
            "status": "PASS" if identity_ok else "FAIL",
            "identity_status": paper["identity_status"],
            "metadata_conflict": paper["metadata_conflict"],
        },
        "claim_binding": binding,
        "claim_support_check": "REQUIRES_CODEX_SOURCE_READING",
        "bibliographic_completeness": {
            "status": "PASS" if not missing_bibliography else "FAIL",
            "missing": missing_bibliography,
        },
        "bibliographic_truth": {
            "status": "PASS"
            if not missing_bibliography and not low_truth_fields
            else "FAIL",
            "low_confidence_fields": low_truth_fields,
            "provenance": bibliography_provenance,
        },
        "reference_format_check": "REQUIRES_COMPLETE_METADATA_TARGET_TEXT_AND_CURRENT_JOURNAL_STYLE",
        "metadata": {
            key: paper[key] for key in ("title", "authors", "year", "journal", "doi")
        },
        "corpus_fingerprint": corpus_fingerprint(con),
        "saved_evidence": saved,
    }
    con.close()
    print(json.dumps(output, ensure_ascii=False))


def citation_audit(db_path: Path, ledger_path: Path) -> None:
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    ledger = _open_citation_ledger(ledger_path)
    ledger.row_factory = sqlite3.Row
    results = []
    for record in ledger.execute(
        "SELECT * FROM citation_evidence ORDER BY claim_id,evidence_id"
    ):
        current = con.execute(
            """SELECT c.locator_id,d.content_hash,d.paper_id,d.artifact_id
               FROM chunks c JOIN documents d ON d.doc_id=c.doc_id
               WHERE c.locator_id=?""",
            (record["locator_id"],),
        ).fetchone()
        if not current:
            status = "SOURCE_STALE"
            reason = "supporting locator is absent from the current source version"
        elif (
            current["content_hash"] != record["source_hash"]
            or current["paper_id"] != record["paper_id"]
            or current["artifact_id"] != record["artifact_id"]
        ):
            status = "SOURCE_STALE"
            reason = "source hash or identity binding changed"
        else:
            current_paper = con.execute(
                "SELECT bibliography_fingerprint FROM papers WHERE paper_id=?",
                (record["paper_id"],),
            ).fetchone()
            if (
                not current_paper
                or not record["bibliography_fingerprint"]
                or current_paper["bibliography_fingerprint"]
                != record["bibliography_fingerprint"]
            ):
                status = "BIBLIOGRAPHY_STALE"
                reason = "bibliographic identity fields or their provenance changed"
            else:
                status = "CURRENT"
                reason = "identity, bibliography, locator, and source hash still match"
        results.append(
            {
                "evidence_id": record["evidence_id"],
                "claim_id": record["claim_id"],
                "paper_id": record["paper_id"],
                "status": status,
                "reason": reason,
                "verified_at": record["verified_at"],
            }
        )
    ledger.close()
    con.close()
    print(json.dumps({"citation_audit": results, "count": len(results)}, ensure_ascii=False))


def load_benchmark(path: Path) -> list[dict]:
    raw = path.read_text("utf-8-sig")
    try:
        if path.suffix.casefold() == ".jsonl":
            rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
        else:
            parsed = json.loads(raw)
            rows = parsed.get("queries", parsed) if isinstance(parsed, dict) else parsed
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid benchmark JSON: {exc}") from exc
    if not isinstance(rows, list) or not rows:
        raise ValueError("Benchmark must contain at least one query")
    for row in rows:
        queries = row.get("queries") or ([row["query"]] if row.get("query") else [])
        if (
            not row.get("query_id")
            or not queries
            or not row.get("relevant_paper_ids")
        ):
            raise ValueError(
                "Each benchmark row needs query_id, query or queries, and relevant_paper_ids"
            )
        row["queries"] = queries
    return rows


def benchmark_index(
    db_path: Path,
    benchmark_path: Path,
    ks: list[int],
    strategy: str,
    model: str,
    model_revision: str,
    document_prefix: str,
    query_prefix: str,
    full_text_rescue: bool = False,
    rescue_chunk_pool: int = 1000,
    allow_model_download: bool = False,
) -> None:
    rows = load_benchmark(benchmark_path)
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    max_k = max(ks)
    model_object = None
    model_load_s = 0.0
    if strategy in {"semantic", "hybrid"}:
        if not model:
            con.close()
            raise ValueError("--model is required for semantic or hybrid benchmark")
        model_started = time.perf_counter()
        model_object = load_embedding_model(
            model, model_revision, allow_model_download
        )
        model_load_s = time.perf_counter() - model_started
    per_query = []
    totals = {k: 0.0 for k in ks}
    hard_negative_totals = {k: 0 for k in ks}
    hard_negative_denominators = {k: 0 for k in ks}
    query_times = []
    for row in rows:
        query_started = time.perf_counter()
        match = row.get("match", "all")
        lexical_arms = [
            lexical_candidates(con, query, max_k * 4, [], None, False, match)
            for query in row["queries"]
        ]
        rescue_arms = (
            [
                fulltext_rescue_candidates(
                    con, query, max_k * 4, rescue_chunk_pool, [], None, match
                )
                for query in row["queries"]
            ]
            if full_text_rescue
            else []
        )
        semantic_arms = (
            [
                semantic_candidates(
                    con,
                    encode_query(model_object, query_prefix + query),
                    model,
                    model_revision,
                    document_prefix,
                    query_prefix,
                    max_k * 4,
                    [],
                    None,
                )
                for query in row["queries"]
            ]
            if model_object is not None
            else []
        )
        if strategy == "lexical":
            arms = [*lexical_arms, *rescue_arms]
        elif strategy == "semantic":
            arms = [*semantic_arms, *rescue_arms]
        elif strategy == "hybrid":
            arms = [*lexical_arms, *semantic_arms, *rescue_arms]
        else:
            con.close()
            raise ValueError(f"Unknown benchmark strategy: {strategy}")
        candidates = arms[0] if len(arms) == 1 else reciprocal_rank_fusion(arms, max_k)
        formulation_arms = []
        for index in range(len(row["queries"])):
            if strategy == "lexical":
                query_arms = [lexical_arms[index]]
            elif strategy == "semantic":
                query_arms = [semantic_arms[index]]
            else:
                query_arms = [lexical_arms[index], semantic_arms[index]]
            if rescue_arms:
                query_arms.append(rescue_arms[index])
            formulation_arms.append(
                query_arms[0]
                if len(query_arms) == 1
                else reciprocal_rank_fusion(query_arms, max_k)
            )
        ranked = [item["paper_id"] for item in candidates]
        relevant = set(row["relevant_paper_ids"])
        recalls = {}
        for k in ks:
            value = len(relevant.intersection(ranked[:k])) / len(relevant)
            totals[k] += value
            recalls[f"Recall@{k}"] = value
            known_hard_negatives = set(row.get("hard_negative_paper_ids", []))
            hard_negative_totals[k] += len(known_hard_negatives.intersection(ranked[:k]))
            hard_negative_denominators[k] += len(known_hard_negatives)
        query_elapsed = time.perf_counter() - query_started
        query_times.append(query_elapsed)
        per_query.append(
            {
                "query_id": row["query_id"],
                "case_type": row.get("case_type", "unspecified"),
                **recalls,
                "missed_at_max_k": sorted(relevant - set(ranked[:max_k])),
                "hard_negative_hits_at_max_k": sorted(
                    set(row.get("hard_negative_paper_ids", [])).intersection(ranked[:max_k])
                ),
                "formulation_recall_at_max_k": [
                    len(relevant.intersection({item["paper_id"] for item in arm[:max_k]}))
                    / len(relevant)
                    for arm in formulation_arms
                ],
                "retrieval_s": round(query_elapsed, 6),
            }
        )
    sorted_times = sorted(query_times)
    p95_index = max(0, math.ceil(0.95 * len(sorted_times)) - 1)
    output = {
        "strategy": strategy,
        "layer": "paper",
        "full_text_rescue": full_text_rescue,
        "rescue_chunk_pool": rescue_chunk_pool if full_text_rescue else 0,
        "queries": len(rows),
        "metrics": {f"Recall@{k}": totals[k] / len(rows) for k in ks},
        "hard_negative_hit_rate": {
            f"HardNegativeHitRate@{k}": (
                hard_negative_totals[k] / hard_negative_denominators[k]
                if hard_negative_denominators[k]
                else None
            )
            for k in ks
        },
        "cost": {
            "model_load_s": round(model_load_s, 6),
            "retrieval_total_s": round(sum(query_times), 6),
            "retrieval_mean_s": round(sum(query_times) / len(query_times), 6),
            "retrieval_p95_s": round(sorted_times[p95_index], 6),
        },
        "per_query": per_query,
        "corpus_fingerprint": corpus_fingerprint(con),
        **retrieval_fingerprints(con),
        "benchmark_hash": file_sha256(benchmark_path),
    }
    con.close()
    print(json.dumps(output, ensure_ascii=False))


def stats(db_path: Path, output_format: str) -> None:
    con = open_index(db_path)
    output = index_summary(con, db_path)
    output["schema_version"] = SCHEMA_VERSION
    output["source_roots"] = json.loads(
        con.execute("SELECT value FROM meta WHERE key='source_roots'").fetchone()[0]
    )
    con.close()
    if output_format == "json":
        print(json.dumps(output, ensure_ascii=False))
    else:
        for key, value in output.items():
            print(f"{key}: {value}")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def root_specs_from_args(
    args: argparse.Namespace, *, reuse_stored_for_update: bool = False
) -> list[tuple[Path, str]]:
    paper_roots = [*args.paper_root, *args.root]
    if args.root:
        print(
            "warning: --root is deprecated; use --paper-root",
            file=sys.stderr,
        )
    explicit = [
        *((path, ROOT_ROLE_PAPER) for path in paper_roots),
        *((path, ROOT_ROLE_PROCESS) for path in args.process_root),
    ]
    if explicit:
        return explicit
    if reuse_stored_for_update:
        return stored_root_specs(args.db)
    return []


def main() -> None:
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="Read-only local evidence recall with persistent incremental FTS5"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    for command in ("build", "update"):
        subparser = sub.add_parser(command)
        subparser.add_argument("--db", required=True, type=Path)
        subparser.add_argument(
            "--manifest",
            type=Path,
            help="optional JSON/JSONL bibliographic manifest outside source roots",
        )
        subparser.add_argument(
            "--profile",
            type=Path,
            help="optional root-scoped corpus profile outside evidence roots",
        )
        subparser.add_argument(
            "--paper-root", action="append", default=[], type=Path,
            help="published/formal evidence root; repeat as needed; on update, any supplied roots replace the stored root configuration",
        )
        subparser.add_argument(
            "--process-root", action="append", default=[], type=Path,
            help="review/editor/author-response process-evidence root; repeat as needed; on update, any supplied roots replace the stored root configuration",
        )
        subparser.add_argument(
            "--root", action="append", default=[], type=Path,
            help="deprecated alias for --paper-root",
        )
        subparser.add_argument(
            "--workers",
            type=positive_int,
            default=max(2, min(8, os.cpu_count() or 2)),
        )
        if command == "update":
            subparser.add_argument(
                "--verify-hash", action="store_true",
                help="hash otherwise unchanged files to detect timestamp-preserving replacements",
            )

    search = sub.add_parser("search")
    search.add_argument("--db", required=True, type=Path)
    search.add_argument(
        "--query", required=True, action="append",
        help="one coherent query branch; repeat only for genuinely distinct terminology/mechanisms",
    )
    search.add_argument(
        "--raw-fts",
        action="store_true",
        help="interpret --query as raw FTS5 syntax instead of natural-language text",
    )
    search.add_argument("--match", choices=("any", "all", "phrase"), default="all")
    search.add_argument(
        "--strategy", choices=("lexical", "semantic", "hybrid"), default="lexical"
    )
    search.add_argument("--model", default="")
    search.add_argument("--model-revision", default="")
    search.add_argument(
        "--allow-model-download",
        action="store_true",
        help="allow sentence-transformers to fetch a pinned model revision; local-only by default",
    )
    search.add_argument("--document-prefix", default="")
    search.add_argument("--query-prefix", default="")
    search.add_argument("--limit", type=positive_int, default=10, help="paper candidates")
    search.add_argument(
        "--passages-per-paper",
        "--passages-per-work",
        dest="passages_per_paper",
        type=positive_int,
        default=2,
    )
    search.add_argument("--role", action="append", default=[])
    search.add_argument("--journal")
    search.add_argument(
        "--full-text-rescue",
        action="store_true",
        help="on-demand global passage retrieval aggregated back to paper_id",
    )
    search.add_argument(
        "--rescue-chunk-pool",
        type=positive_int,
        default=1000,
        help="maximum globally ranked chunks inspected by each rescue query branch",
    )
    search.add_argument("--format", choices=("human", "jsonl"), default="human")

    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--db", required=True, type=Path)
    selector = inspect_parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--chunk-id", type=int)
    selector.add_argument("--paper-id")
    inspect_parser.add_argument("--context", type=int, default=1)

    stats_parser = sub.add_parser("stats")
    stats_parser.add_argument("--db", required=True, type=Path)
    stats_parser.add_argument("--format", choices=("human", "json"), default="human")

    lookup_parser = sub.add_parser("lookup")
    lookup_parser.add_argument("--db", required=True, type=Path)
    lookup_selector = lookup_parser.add_mutually_exclusive_group(required=True)
    lookup_selector.add_argument("--doi")
    lookup_selector.add_argument("--title")
    lookup_parser.add_argument("--format", choices=("jsonl", "json"), default="jsonl")

    manifest_export_parser = sub.add_parser("manifest-export")
    manifest_export_parser.add_argument("--db", required=True, type=Path)
    manifest_export_parser.add_argument("--out", required=True, type=Path)

    embed_parser = sub.add_parser("embed")
    embed_parser.add_argument("--db", required=True, type=Path)
    embed_parser.add_argument("--model", required=True)
    embed_parser.add_argument("--model-revision", default="")
    embed_parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="allow sentence-transformers to fetch a pinned model revision; local-only by default",
    )
    embed_parser.add_argument("--document-prefix", default="")
    embed_parser.add_argument("--query-prefix", default="")
    embed_parser.add_argument("--batch-size", type=positive_int, default=16)

    companion_parser = sub.add_parser("companion-suggestions")
    companion_parser.add_argument("--db", required=True, type=Path)
    companion_parser.add_argument("--format", choices=("jsonl", "json"), default="jsonl")

    passage_parser = sub.add_parser("passage-search")
    passage_parser.add_argument("--db", required=True, type=Path)
    passage_parser.add_argument("--paper-id", required=True)
    passage_parser.add_argument("--query", required=True)
    passage_parser.add_argument("--limit", type=positive_int, default=10)
    passage_parser.add_argument("--strategy", choices=("lexical", "semantic"), default="lexical")
    passage_parser.add_argument("--model", default="")
    passage_parser.add_argument("--model-revision", default="")
    passage_parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="allow sentence-transformers to fetch a pinned model revision; local-only by default",
    )
    passage_parser.add_argument("--document-prefix", default="")
    passage_parser.add_argument("--query-prefix", default="")

    citation_parser = sub.add_parser("citation-record")
    citation_parser.add_argument("--db", required=True, type=Path)
    citation_parser.add_argument("--paper-id", required=True)
    citation_parser.add_argument("--chunk-id", type=int)
    citation_parser.add_argument("--ledger", type=Path)
    citation_parser.add_argument("--claim-id", default="")
    citation_parser.add_argument("--claim-text", default="")
    citation_parser.add_argument(
        "--verdict", choices=("SUPPORTED", "PARTIAL", "UNSUPPORTED", "UNCERTAIN"), default=""
    )
    citation_parser.add_argument("--rationale", default="")

    citation_audit_parser = sub.add_parser("citation-audit")
    citation_audit_parser.add_argument("--db", required=True, type=Path)
    citation_audit_parser.add_argument("--ledger", required=True, type=Path)

    benchmark_parser = sub.add_parser("benchmark")
    benchmark_parser.add_argument("--db", required=True, type=Path)
    benchmark_parser.add_argument("--benchmark", required=True, type=Path)
    benchmark_parser.add_argument("--k", action="append", type=positive_int, default=[])
    benchmark_parser.add_argument(
        "--strategy", choices=("lexical", "semantic", "hybrid"), default="lexical"
    )
    benchmark_parser.add_argument("--model", default="")
    benchmark_parser.add_argument("--model-revision", default="")
    benchmark_parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="allow sentence-transformers to fetch a pinned model revision; local-only by default",
    )
    benchmark_parser.add_argument("--document-prefix", default="")
    benchmark_parser.add_argument("--query-prefix", default="")
    benchmark_parser.add_argument("--full-text-rescue", action="store_true")
    benchmark_parser.add_argument("--rescue-chunk-pool", type=positive_int, default=1000)

    profile_audit_parser = sub.add_parser("profile-audit")
    profile_audit_parser.add_argument("--profile", required=True, type=Path)
    profile_audit_parser.add_argument("--paper-root", action="append", default=[], type=Path)
    profile_audit_parser.add_argument("--process-root", action="append", default=[], type=Path)
    profile_audit_parser.add_argument("--root", action="append", default=[], type=Path)

    args = parser.parse_args()
    try:
        if args.cmd == "build":
            build_index(
                args.db, root_specs_from_args(args), args.workers, args.manifest, args.profile
            )
        elif args.cmd == "update":
            update_index(
                args.db,
                root_specs_from_args(args, reuse_stored_for_update=True),
                args.workers,
                verify_hash=args.verify_hash,
                manifest_path=args.manifest,
                profile_path=args.profile,
            )
        elif args.cmd == "search":
            search_index(
                args.db,
                args.query,
                args.limit,
                args.passages_per_paper,
                args.role,
                args.journal,
                args.format,
                args.raw_fts,
                args.match,
                args.strategy,
                args.model,
                args.model_revision,
                args.document_prefix,
                args.query_prefix,
                args.full_text_rescue,
                args.rescue_chunk_pool,
                args.allow_model_download,
            )
        elif args.cmd == "inspect":
            if args.context < 0:
                raise ValueError("--context cannot be negative")
            inspect_index(args.db, args.chunk_id, args.paper_id, args.context)
        elif args.cmd == "lookup":
            lookup_index(args.db, args.doi, args.title, args.format)
        elif args.cmd == "manifest-export":
            export_manifest(args.db, args.out)
        elif args.cmd == "embed":
            embed_index(
                args.db,
                args.model,
                args.model_revision,
                args.document_prefix,
                args.query_prefix,
                args.batch_size,
                args.allow_model_download,
            )
        elif args.cmd == "companion-suggestions":
            companion_suggestions(args.db, args.format)
        elif args.cmd == "passage-search":
            passage_search(
                args.db, args.paper_id, args.query, args.limit, args.strategy,
                args.model, args.model_revision, args.document_prefix, args.query_prefix,
                args.allow_model_download,
            )
        elif args.cmd == "citation-record":
            citation_record(
                args.db, args.paper_id, args.chunk_id, args.ledger, args.claim_id,
                args.claim_text, args.verdict, args.rationale,
            )
        elif args.cmd == "citation-audit":
            citation_audit(args.db, args.ledger)
        elif args.cmd == "benchmark":
            benchmark_index(
                args.db,
                args.benchmark,
                args.k or [20, 50],
                args.strategy,
                args.model,
                args.model_revision,
                args.document_prefix,
                args.query_prefix,
                args.full_text_rescue,
                args.rescue_chunk_pool,
                args.allow_model_download,
            )
        elif args.cmd == "profile-audit":
            audit_corpus_profile(args.profile, root_specs_from_args(args))
        else:
            stats(args.db, args.format)
    except (ValueError, RuntimeError, sqlite3.Error, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
