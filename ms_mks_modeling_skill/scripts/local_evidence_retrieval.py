#!/usr/bin/env python3
"""Build, incrementally update, and query an optional local MS/MKS evidence index.

Local sources are user-authorized read-only inputs and are explicitly classified
as published-paper roots or review/response process roots. The SQLite database is
disposable derived data and must live outside every source root. This script never
performs web retrieval and never uploads local content. It performs lexical recall
and work-level grouping; the calling model must do structural semantic reranking
and evidence qualification. A BM25 score is never an evidence-strength score.

Dependencies: Python standard library and an installed ``pdftotext`` executable.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import uuid
import zipfile


SCHEMA_VERSION = 2
SUPPORTED_SUFFIXES = {".pdf", ".docx"}
CANONICAL_ROLES = {
    "MAIN_ARTICLE",
    "ONLINE_APPENDIX",
    "COMMENT_CORRECTION",
    "PROCESS_EVIDENCE",
    "OTHER",
}
FILENAME_ROLE = {"A": "MAIN_ARTICLE", "F": "ONLINE_APPENDIX"}


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def normalize_space(text: str) -> str:
    text = text.replace("\u00ad", "").replace("\x00", " ")
    return re.sub(r"[ \t\r]+", " ", text).strip()


def canonical_path(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def path_is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def validate_locations(
    db_path: Path, source_roots: list[tuple[Path, str]]
) -> list[tuple[Path, str]]:
    if not source_roots:
        raise ValueError("At least one --paper-root or --process-root is required")
    resolved: list[tuple[Path, str]] = []
    seen: set[tuple[str, str]] = set()
    db_real = db_path.resolve()
    for root, source_kind in source_roots:
        real = root.resolve()
        if not real.is_dir():
            raise ValueError(f"Source root is not a directory: {real}")
        if path_is_within(db_real, real):
            raise ValueError(
                f"Derived index must be outside source root: db={db_real} root={real}"
            )
        key = (canonical_path(real), source_kind)
        if key not in seen:
            seen.add(key)
            resolved.append((real, source_kind))
    return resolved


def iter_source_files(root: Path):
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        dirnames[:] = [
            name for name in dirnames if not (directory_path / name).is_symlink()
        ]
        for name in filenames:
            path = directory_path / name
            if path.suffix.lower() in SUPPORTED_SUFFIXES and not path.is_symlink():
                yield path


def scan_sources(source_roots: list[tuple[Path, str]]) -> list[tuple[str, str, str]]:
    found: dict[str, tuple[str, str, str]] = {}
    for root, source_kind in source_roots:
        for path in iter_source_files(root):
            key = canonical_path(path)
            current = found.get(key)
            if current is not None and current[2] != source_kind:
                raise ValueError(
                    f"The same file is reachable from paper and process roots: {path}"
                )
            found[key] = (str(path.resolve()), str(root.resolve()), source_kind)
    return [found[key] for key in sorted(found)]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_id_for(path: Path) -> str:
    return hashlib.sha1(canonical_path(path).encode("utf-8")).hexdigest()


def classify_role(stem: str, source_kind: str, filename_role: str | None) -> str:
    if source_kind == "process":
        return "PROCESS_EVIDENCE"
    lowered = stem.lower()
    corrective_terms = (
        "erratum",
        "correction",
        "corrigendum",
        "comment on",
        "commentary on",
        "rejoinder",
        "勘误",
        "更正",
        "评论与回应",
    )
    if any(term in lowered for term in corrective_terms):
        return "COMMENT_CORRECTION"
    return filename_role or "OTHER"


def parse_source(path: Path, source_root: Path, source_kind: str) -> dict:
    stat = path.stat()
    rel = path.relative_to(source_root).as_posix()
    stem = path.stem
    journal = ""
    year = ""
    doi = ""
    work_id = stem
    title = stem
    authors = ""
    filename_role: str | None = None

    canonical = re.match(
        r"(?P<yy>\d{2})_(?P<code>mksc|mnsc)\.(?P<doi_year>\d{4})\."
        r"(?P<suffix>\d+)_(?P<role>[AFYZ])_(?P<body>.+)",
        stem,
        re.I,
    )
    if canonical:
        code = canonical.group("code").lower()
        journal = "Marketing Science" if code == "mksc" else "Management Science"
        doi = f"10.1287/{code}.{canonical.group('doi_year')}.{canonical.group('suffix')}"
        work_id = doi.lower()
        filename_role = FILENAME_ROLE.get(canonical.group("role").upper(), "OTHER")
        year = "20" + canonical.group("yy")
        body = canonical.group("body").split("__", 1)[0]
        title = body.rsplit("_", 1)[-1].replace("- ", ": ").strip()
    elif source_kind == "process":
        if rel.startswith("ManagementScience/"):
            journal = "Management Science submission process"
        elif rel.startswith("MarketingScience/") or stem.startswith("MKSC-"):
            journal = "Marketing Science submission process"
        else:
            journal = rel.split("/", 1)[0] if "/" in rel else "Submission process"
        manuscript = re.match(r"((?:MS|MKSC|JMR)[-_A-Z]*-?\d+(?:-\d+)?)", stem, re.I)
        if manuscript:
            work_id = manuscript.group(1).upper()
        date_match = re.search(r"_(20\d{6})_", stem)
        if date_match:
            year = date_match.group(1)[:4]
        title = stem.split("__", 1)[0]
    else:
        journal = "Management Science / Marketing Science local corpus"
        title = stem.split("__", 1)[0]

    role = classify_role(stem, source_kind, filename_role)
    return {
        "artifact_id": artifact_id_for(path),
        "source_path": str(path.resolve()),
        "source_root": str(source_root.resolve()),
        "source_kind": source_kind,
        "source_rel": f"{source_kind}/{rel}",
        "work_id": work_id,
        "role": role,
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "doi": doi,
        "extension": path.suffix.lower(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "content_hash": "",
    }


def pdf_pages(path: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", "--", str(path), "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=180,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("pdftotext executable was not found") from exc
    if proc.returncode != 0:
        message = proc.stderr.decode("utf-8", errors="replace")[-1000:]
        raise RuntimeError(f"pdftotext failed: {message}")
    return proc.stdout.decode("utf-8", errors="replace").split("\f")


def docx_blocks(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"</w:(?:p|tr)>", "\n\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    return [html.unescape(re.sub(r"<[^>]+>", "", xml))]


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


def extract_one(args: tuple[str, str, str]) -> dict:
    path_s, root_s, source_kind = args
    path, root = Path(path_s), Path(root_s)
    meta = parse_source(path, root, source_kind)
    try:
        meta["content_hash"] = file_sha256(path)
        units = pdf_pages(path) if path.suffix.lower() == ".pdf" else docx_blocks(path)
        chunks = []
        if units:
            front = normalize_space(units[0])
            cite = re.search(
                r"To cite this article:\s*(.+?)\s*\((20\d{2})\)", front, re.I
            )
            if cite:
                meta["authors"] = normalize_space(cite.group(1))
        for unit_index, unit in enumerate(units, start=1):
            for chunk_index, (start, end, text) in enumerate(make_chunks(unit), start=1):
                if len(text) < 60:
                    continue
                page = unit_index if path.suffix.lower() == ".pdf" else None
                default_section = f"page {page}" if page is not None else "document body"
                chunks.append(
                    {
                        "page": page,
                        "section": guess_section(text, default_section),
                        "chunk_index": chunk_index,
                        "char_start": start,
                        "char_end": end,
                        "text": text,
                    }
                )
        meta["chunks"] = chunks
        meta["error"] = ""
    except Exception as exc:  # Preserve extraction failures for auditability.
        meta["chunks"] = []
        meta["error"] = f"{type(exc).__name__}: {exc}"
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
  source_kind TEXT NOT NULL,
  source_rel TEXT NOT NULL,
  work_id TEXT NOT NULL,
  role TEXT NOT NULL,
  title TEXT NOT NULL,
  authors TEXT NOT NULL,
  year TEXT NOT NULL,
  journal TEXT NOT NULL,
  doi TEXT NOT NULL,
  extension TEXT NOT NULL,
  size INTEGER NOT NULL,
  mtime_ns INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  error TEXT NOT NULL
);
CREATE INDEX documents_work_idx ON documents(work_id);
CREATE INDEX documents_root_idx ON documents(source_root);
CREATE TABLE chunks (
  chunk_id INTEGER PRIMARY KEY,
  doc_id INTEGER NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
  page INTEGER,
  section TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  char_start INTEGER NOT NULL,
  char_end INTEGER NOT NULL,
  text TEXT NOT NULL
);
CREATE INDEX chunks_doc_idx ON chunks(doc_id);
CREATE VIRTUAL TABLE chunks_fts USING fts5(
  text,
  title,
  work_id,
  role,
  journal,
  tokenize='unicode61 remove_diacritics 2'
);
"""


DOCUMENT_COLUMNS = (
    "artifact_id",
    "source_path",
    "source_root",
    "source_kind",
    "source_rel",
    "work_id",
    "role",
    "title",
    "authors",
    "year",
    "journal",
    "doi",
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


def initialize_index(con: sqlite3.Connection, source_roots: list[tuple[Path, str]]) -> None:
    con.executescript(SCHEMA)
    con.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    con.executemany(
        "INSERT INTO meta(key,value) VALUES (?,?)",
        [
            ("schema_version", str(SCHEMA_VERSION)),
            ("source_roots", json.dumps([{"path": str(root), "kind": kind} for root, kind in source_roots], ensure_ascii=False)),
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
    if item["content_hash"]:
        duplicate = con.execute(
            "SELECT work_id FROM documents WHERE content_hash=? LIMIT 1",
            (item["content_hash"],),
        ).fetchone()
        if duplicate:
            item["work_id"] = duplicate[0]
    values = [item[column] for column in DOCUMENT_COLUMNS]
    placeholders = ",".join("?" for _ in DOCUMENT_COLUMNS)
    cursor = con.execute(
        f"INSERT INTO documents ({','.join(DOCUMENT_COLUMNS)}) VALUES ({placeholders})",
        values,
    )
    doc_id = cursor.lastrowid
    for chunk in item["chunks"]:
        chunk_cursor = con.execute(
            """INSERT INTO chunks
            (doc_id,page,section,chunk_index,char_start,char_end,text)
            VALUES (?,?,?,?,?,?,?)""",
            (
                doc_id,
                chunk["page"],
                chunk["section"],
                chunk["chunk_index"],
                chunk["char_start"],
                chunk["char_end"],
                chunk["text"],
            ),
        )
        con.execute(
            """INSERT INTO chunks_fts(rowid,text,title,work_id,role,journal)
            VALUES (?,?,?,?,?,?)""",
            (
                chunk_cursor.lastrowid,
                chunk["text"],
                item["title"],
                item["work_id"],
                item["role"],
                item["journal"],
            ),
        )


def extract_many(paths: list[tuple[str, str, str]], workers: int):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(extract_one, paths)


def index_summary(con: sqlite3.Connection, db_path: Path) -> dict:
    return {
        "documents": con.execute("SELECT count(*) FROM documents").fetchone()[0],
        "works": con.execute("SELECT count(DISTINCT work_id) FROM documents").fetchone()[0],
        "chunks": con.execute("SELECT count(*) FROM chunks").fetchone()[0],
        "errors": con.execute("SELECT count(*) FROM documents WHERE error <> ''").fetchone()[0],
        "roles": dict(con.execute("SELECT role,count(*) FROM documents GROUP BY role")),
        "db_bytes": db_path.stat().st_size if db_path.exists() else 0,
    }


def build_index(db_path: Path, source_roots: list[tuple[Path, str]], workers: int) -> None:
    source_roots = validate_locations(db_path, source_roots)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = db_path.with_name(f".{db_path.name}.building-{uuid.uuid4().hex}")
    paths = scan_sources(source_roots)
    started = time.perf_counter()
    con: sqlite3.Connection | None = None
    try:
        con = sqlite3.connect(temporary)
        initialize_index(con, source_roots)
        with con:
            for item in extract_many(paths, workers):
                insert_document(con, item)
        con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('optimize')")
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


def update_index(db_path: Path, source_roots: list[tuple[Path, str]], workers: int) -> None:
    source_roots = validate_locations(db_path, source_roots)
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    started = time.perf_counter()
    paths = scan_sources(source_roots)
    scanned = {canonical_path(Path(path)): (path, root, kind) for path, root, kind in paths}
    root_kinds = {canonical_path(root): kind for root, kind in source_roots}
    all_existing = list(
        con.execute(
            "SELECT doc_id,source_path,source_root,source_kind,size,mtime_ns FROM documents"
        )
    )
    existing = {
        canonical_path(Path(row["source_path"])): row
        for row in all_existing
        if root_kinds.get(canonical_path(Path(row["source_root"]))) == row["source_kind"]
    }
    removed = [
        row
        for row in all_existing
        if root_kinds.get(canonical_path(Path(row["source_root"]))) != row["source_kind"]
        or canonical_path(Path(row["source_path"])) not in scanned
    ]
    changed: list[tuple[str, str, str]] = []
    added = 0
    replaced = 0
    for key, pair in scanned.items():
        path = Path(pair[0])
        stat = path.stat()
        row = existing.get(key)
        if row is None:
            changed.append(pair)
            added += 1
        elif row["size"] != stat.st_size or row["mtime_ns"] != stat.st_mtime_ns:
            changed.append(pair)
            replaced += 1

    extracted = list(extract_many(changed, workers))
    try:
        with con:
            for row in removed:
                delete_document(con, row["doc_id"])
            for item in extracted:
                old = con.execute(
                    "SELECT doc_id FROM documents WHERE source_path=?",
                    (item["source_path"],),
                ).fetchone()
                if old:
                    delete_document(con, old["doc_id"])
                insert_document(con, item)
            con.execute(
                "INSERT INTO meta(key,value) VALUES ('source_roots',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (json.dumps([{"path": str(root), "kind": kind} for root, kind in source_roots], ensure_ascii=False),),
            )
            con.execute(
                "INSERT INTO meta(key,value) VALUES ('last_update_utc',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(int(time.time())),),
            )
        if removed or extracted:
            con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('optimize')")
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
    if journal:
        clauses.append("d.journal LIKE ?")
        parameters.append(f"%{journal}%")
    return " AND ".join(clauses), parameters


def search_index(
    db_path: Path,
    query: str,
    limit: int,
    passages_per_work: int,
    roles: list[str],
    journal: str | None,
    output_format: str,
) -> None:
    con = open_index(db_path)
    con.row_factory = sqlite3.Row
    where, filters = build_search_sql(roles, journal)
    candidate_limit = max(200, limit * passages_per_work * 20)
    params: list[object] = [query, *filters, candidate_limit]
    sql = f"""
      SELECT c.chunk_id,
             bm25(chunks_fts, 1.0, 2.0, 1.2, 0.3, 0.3) AS lexical_score,
             d.artifact_id, d.content_hash, d.work_id, d.role, d.title,
             d.authors, d.year, d.journal, d.doi, d.source_path, d.source_rel,
             c.page, c.section, c.chunk_index, c.char_start, c.char_end, c.text
      FROM chunks_fts
      JOIN chunks c ON c.chunk_id = chunks_fts.rowid
      JOIN documents d ON d.doc_id = c.doc_id
      WHERE {where}
      ORDER BY lexical_score ASC
      LIMIT ?
    """
    try:
        rows = list(con.execute(sql, params))
    except sqlite3.OperationalError as exc:
        con.close()
        raise ValueError(f"Invalid FTS5 query {query!r}: {exc}") from exc
    con.close()

    groups: dict[str, dict] = {}
    order: list[str] = []
    for row in rows:
        work_id = row["work_id"]
        if work_id not in groups:
            if len(order) >= limit:
                continue
            order.append(work_id)
            groups[work_id] = {
                "work_id": work_id,
                "title": row["title"],
                "authors": row["authors"],
                "year": row["year"],
                "journal": row["journal"],
                "doi": row["doi"],
                "best_lexical_score": row["lexical_score"],
                "artifacts": [],
                "passages": [],
                "reranking_status": "PENDING_CODEX_STRUCTURAL_RERANK",
                "evidence_strength": "UNQUALIFIED",
            }
        group = groups.get(work_id)
        if group is None:
            continue
        artifact = {
            "artifact_id": row["artifact_id"],
            "role": row["role"],
            "source_path": row["source_path"],
            "source_rel": row["source_rel"],
            "content_hash": row["content_hash"],
        }
        if not any(a["artifact_id"] == artifact["artifact_id"] for a in group["artifacts"]):
            # Exact duplicate bytes remain auditable but do not add another artifact slot.
            if not any(
                artifact["content_hash"] and a["content_hash"] == artifact["content_hash"]
                for a in group["artifacts"]
            ):
                group["artifacts"].append(artifact)
        if len(group["passages"]) < passages_per_work:
            group["passages"].append(
                {
                    "chunk_id": row["chunk_id"],
                    "artifact_id": row["artifact_id"],
                    "role": row["role"],
                    "page": row["page"],
                    "section": row["section"],
                    "chunk_index": row["chunk_index"],
                    "char_start": row["char_start"],
                    "char_end": row["char_end"],
                    "lexical_score": row["lexical_score"],
                    "chunk_text": row["text"],
                }
            )

    for work_id in order:
        group = groups[work_id]
        if output_format == "jsonl":
            print(json.dumps(group, ensure_ascii=False))
            continue
        print(f"work_id: {group['work_id']}")
        for key in ("title", "authors", "year", "journal", "doi"):
            print(f"{key}: {group[key]}")
        print(f"best_lexical_score: {group['best_lexical_score']}")
        print("reranking_status: PENDING_CODEX_STRUCTURAL_RERANK")
        print("evidence_strength: UNQUALIFIED")
        for passage in group["passages"]:
            location = f"page={passage['page']} section={passage['section']}"
            print(
                f"  passage chunk_id={passage['chunk_id']} role={passage['role']} {location}"
            )
            print(f"  {passage['chunk_text']}")
        print()


def inspect_index(
    db_path: Path, chunk_id: int | None, work_id: str | None, context: int
) -> None:
    if chunk_id is None and not work_id:
        raise ValueError("inspect requires --chunk-id or --work-id")
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
            """SELECT c.chunk_id,d.work_id,d.artifact_id,d.role,d.title,d.authors,
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
            """SELECT c.chunk_id,d.work_id,d.artifact_id,d.role,d.title,d.authors,
                      d.year,d.journal,d.doi,d.source_path,d.source_rel,c.page,
                      c.section,c.chunk_index,c.char_start,c.char_end,c.text
               FROM chunks c JOIN documents d ON d.doc_id=c.doc_id
               WHERE d.work_id=? ORDER BY d.role,c.page,c.chunk_index""",
            (work_id,),
        )
    found = False
    for row in rows:
        found = True
        print(json.dumps(dict(row), ensure_ascii=False))
    con.close()
    if not found:
        raise ValueError(f"No passages found for work_id: {work_id}")


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
            "--paper-root", action="append", default=[], type=Path,
            help="Authorized read-only root containing published papers/appendices",
        )
        subparser.add_argument(
            "--process-root", action="append", default=[], type=Path,
            help="Authorized read-only root containing reviewer/editor/response materials",
        )
        subparser.add_argument(
            "--workers",
            type=positive_int,
            default=max(2, min(8, os.cpu_count() or 2)),
        )

    search = sub.add_parser("search")
    search.add_argument("--db", required=True, type=Path)
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=positive_int, default=10, help="work groups")
    search.add_argument("--passages-per-work", type=positive_int, default=2)
    search.add_argument("--role", action="append", default=[])
    search.add_argument("--journal")
    search.add_argument("--format", choices=("human", "jsonl"), default="human")

    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("--db", required=True, type=Path)
    selector = inspect_parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--chunk-id", type=int)
    selector.add_argument("--work-id")
    inspect_parser.add_argument("--context", type=int, default=1)

    stats_parser = sub.add_parser("stats")
    stats_parser.add_argument("--db", required=True, type=Path)
    stats_parser.add_argument("--format", choices=("human", "json"), default="human")

    args = parser.parse_args()
    try:
        if args.cmd in {"build", "update"}:
            source_roots = [
                *((path, "paper") for path in args.paper_root),
                *((path, "process") for path in args.process_root),
            ]
            if args.cmd == "build":
                build_index(args.db, source_roots, args.workers)
            else:
                update_index(args.db, source_roots, args.workers)
        elif args.cmd == "search":
            search_index(
                args.db,
                args.query,
                args.limit,
                args.passages_per_work,
                args.role,
                args.journal,
                args.format,
            )
        elif args.cmd == "inspect":
            if args.context < 0:
                raise ValueError("--context cannot be negative")
            inspect_index(args.db, args.chunk_id, args.work_id, args.context)
        else:
            stats(args.db, args.format)
    except (ValueError, RuntimeError, sqlite3.Error, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
