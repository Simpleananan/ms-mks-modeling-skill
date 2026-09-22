from __future__ import annotations

import importlib.util
import io
from contextlib import redirect_stdout
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
import zipfile


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "local_evidence_retrieval.py"
spec = importlib.util.spec_from_file_location("local_evidence_retrieval", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def write_docx(path: Path, text: str) -> None:
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", xml.encode("utf-8"))


def write_profile(path: Path, root: Path, *, note: str = "") -> None:
    path.write_text(
        json.dumps(
            {
                "profile_version": 1,
                "note": note,
                "corpora": [
                    {
                        "root": str(root),
                        "artifact_codes": {
                            "A": {
                                "role": "MAIN_ARTICLE",
                                "version": "PUBLISHED",
                                "access": "UNSPECIFIED",
                                "basis": "USER_CONFIRMED",
                            },
                            "F": {
                                "role": "ONLINE_APPENDIX",
                                "version": "PUBLISHED_APPENDIX",
                                "access": "UNSPECIFIED",
                                "basis": "USER_CONFIRMED",
                            },
                            "Z": {
                                "role": "OTHER",
                                "version": "UNSPECIFIED",
                                "access": "UNSPECIFIED",
                                "artifact_kind": "REPLICATION_PACKAGE",
                                "basis": "USER_CONFIRMED",
                            },
                        },
                    }
                ],
            }
        ),
        "utf-8",
    )


class RetrievalTests(unittest.TestCase):
    def test_pdf_extraction_retries_through_ascii_alias(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / ("很长的中文路径" * 20 + ".pdf")
            source.write_bytes(b"placeholder")
            calls = []

            def fake_run(path):
                calls.append(Path(path))
                if len(calls) == 1:
                    return subprocess.CompletedProcess([], 1, b"", b"cannot open path")
                self.assertEqual(Path(path).name, "source.pdf")
                self.assertTrue(Path(path).is_file())
                return subprocess.CompletedProcess([], 0, b"page one\fpage two", b"")

            with mock.patch.object(mod, "_run_pdftotext", side_effect=fake_run):
                pages = mod.pdf_pages(source)

            self.assertEqual(pages[:2], ["page one", "page two"])
            self.assertEqual(calls[0], source)
            self.assertNotEqual(calls[1], source)
            self.assertFalse(calls[1].exists())

    def test_generic_main_appendix_and_correction_roles_and_grouping(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            names = [
                "A Study.docx",
                "A Study Online Appendix.docx",
                "A Study Correction.docx",
                "Comment on A Study.docx",
            ]
            for name in names:
                (root / name).touch()
            parsed = [mod.parse_source(root / name, root, mod.ROOT_ROLE_PAPER) for name in names]
            self.assertEqual(
                [item["role"] for item in parsed],
                [
                    "MAIN_ARTICLE",
                    "ONLINE_APPENDIX",
                    "COMMENT_CORRECTION",
                    "COMMENT_CORRECTION",
                ],
            )
            self.assertEqual(len({item["paper_id"] for item in parsed}), 1)

    def test_common_appendix_filename_variants(self):
        variants = [
            "A Study (Online Appendix)",
            "A Study [Online Appendix]",
            "Online Appendix to A Study",
            "Appendix to A Study",
            "A Study Supplementary Material",
            "A Study Supporting Information",
        ]
        for stem in variants:
            with self.subTest(stem=stem):
                self.assertEqual(
                    mod.classify_role(stem, mod.ROOT_ROLE_PAPER, None),
                    "ONLINE_APPENDIX",
                )
                self.assertEqual(mod.normalized_work_title(stem), "a study")

    def test_doi_in_content_overrides_filename_work_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "supplement.docx"
            write_docx(path, "doi: 10.1287/mksc.2024.0001 formal appendix text " * 5)
            item = mod.extract_one((str(path), str(root), mod.ROOT_ROLE_PAPER))
            self.assertEqual(item["doi"], "10.1287/mksc.2024.0001")
            self.assertEqual(item["paper_id"], "doi:10.1287/mksc.2024.0001")
            self.assertEqual(item["identity_status"], "DOI")
            self.assertEqual(item["journal"], "Marketing Science")

    def test_generic_main_and_appendix_group_in_built_index(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "Platform Analytics.docx", "main model pricing evidence " * 8)
            write_docx(
                papers / "Platform Analytics Online Appendix.docx",
                "appendix proof equilibrium evidence " * 8,
            )
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            works = con.execute("SELECT count(*) FROM papers").fetchone()[0]
            roles = {row[0] for row in con.execute("SELECT role FROM documents")}
            con.close()
            self.assertEqual(works, 1)
            self.assertEqual(roles, {"MAIN_ARTICLE", "ONLINE_APPENDIX"})

    def test_long_unbroken_text_is_bounded(self):
        chunks = mod.make_chunks("x" * 5000, target=1000, overlap=100)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(text) <= 1000 for _, _, text in chunks))

    def test_build_rejects_silently_empty_index(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "empty.docx", "too short")
            db = base / "index.sqlite"
            with self.assertRaises(RuntimeError):
                mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            self.assertFalse(db.exists())

    def test_build_keeps_partial_index_when_one_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "good.docx", "searchable model evidence " * 10)
            (papers / "bad.pdf").write_bytes(b"not a pdf")
            db = base / "index.sqlite"
            with mock.patch.object(
                mod, "pdf_pages", side_effect=RuntimeError("simulated PDF failure")
            ):
                mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            documents, chunks, errors = con.execute(
                "SELECT count(*), (SELECT count(*) FROM chunks), "
                "sum(CASE WHEN error <> '' THEN 1 ELSE 0 END) FROM documents"
            ).fetchone()
            con.close()
            self.assertEqual((documents, errors), (2, 1))
            self.assertGreater(chunks, 0)

    def test_update_reuses_roots_stored_by_build(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "first.docx", "first searchable evidence " * 10)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            write_docx(papers / "second.docx", "second searchable evidence " * 10)
            stored = mod.stored_root_specs(db)
            self.assertEqual(stored, [(papers.resolve(), mod.ROOT_ROLE_PAPER)])
            mod.update_index(db, stored, workers=1)
            con = sqlite3.connect(db)
            documents = con.execute("SELECT count(*) FROM documents").fetchone()[0]
            con.close()
            self.assertEqual(documents, 2)

    def test_failed_update_preserves_existing_searchable_record(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            path = papers / "paper.docx"
            write_docx(path, "searchable formal article evidence " * 8)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            before = con.execute("SELECT content_hash FROM documents").fetchone()[0]
            before_chunks = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
            con.close()

            path.write_bytes(b"not a valid docx")
            out = io.StringIO()
            with redirect_stdout(out):
                mod.update_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            summary = json.loads(out.getvalue())
            self.assertEqual(summary["extraction_failures_preserved"], 1)

            con = sqlite3.connect(db)
            after = con.execute("SELECT content_hash FROM documents").fetchone()[0]
            after_chunks = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
            con.close()
            self.assertEqual(after, before)
            self.assertEqual(after_chunks, before_chunks)

    def test_process_evidence_is_explicit_and_excluded_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            process = base / "process"
            papers.mkdir()
            process.mkdir()
            write_docx(papers / "paper.docx", "sharedkeyword formal article evidence " * 8)
            write_docx(process / "response.docx", "sharedkeyword reviewer response evidence " * 8)
            db = base / "index.sqlite"
            mod.build_index(
                db,
                [(papers, mod.ROOT_ROLE_PAPER), (process, mod.ROOT_ROLE_PROCESS)],
                workers=1,
            )
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(db, "sharedkeyword", 10, 2, [], None, "jsonl")
            self.assertNotIn("PROCESS_EVIDENCE", out.getvalue())

            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(
                    db, "response", 10, 2, ["PROCESS_EVIDENCE"], None, "jsonl"
                )
            self.assertIn("PROCESS_EVIDENCE", out.getvalue())

    def test_natural_language_queries_are_fts_safe(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(
                papers / "paper.docx",
                "platform algorithm equilibrium price competition evidence " * 8,
            )
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            for query in [
                "price-competition",
                "platform/algorithm",
                "equilibrium (platform)",
                "price competition?",
            ]:
                with self.subTest(query=query), redirect_stdout(io.StringIO()):
                    mod.search_index(db, query, 10, 2, [], None, "jsonl")

    def test_safe_query_and_raw_fts_are_distinct(self):
        self.assertEqual(
            mod.safe_fts_query("price OR competition"),
            '"price" "OR" "competition"',
        )
        self.assertEqual(
            mod.safe_fts_query("price OR competition", "all"),
            '"price" "OR" "competition"',
        )
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "price competition paper.docx", "price competition evidence " * 12)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(
                    db,
                    "price OR competition",
                    10,
                    2,
                    [],
                    None,
                    "jsonl",
                    raw_fts=True,
                )
            self.assertIn("MAIN_ARTICLE", out.getvalue())

    def test_overlapping_roots_and_database_inside_root_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            parent = base / "corpus"
            child = parent / "process"
            child.mkdir(parents=True)
            with self.assertRaises(ValueError):
                mod.validate_locations(
                    base / "index.sqlite",
                    [(parent, mod.ROOT_ROLE_PAPER), (child, mod.ROOT_ROLE_PROCESS)],
                )
            with self.assertRaises(ValueError):
                mod.validate_locations(
                    parent / "index.sqlite", [(parent, mod.ROOT_ROLE_PAPER)]
                )

    def test_verify_hash_detects_preserved_size_and_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            path = papers / "paper.docx"
            write_docx(path, "A" * 160)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            original = path.stat()
            con = sqlite3.connect(db)
            old_hash = con.execute("SELECT content_hash FROM documents").fetchone()[0]
            con.close()

            write_docx(path, "B" * 160)
            self.assertEqual(path.stat().st_size, original.st_size)
            os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
            mod.update_index(
                db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1, verify_hash=True
            )
            con = sqlite3.connect(db)
            new_hash = con.execute("SELECT content_hash FROM documents").fetchone()[0]
            con.close()
            self.assertNotEqual(new_hash, old_hash)

    def test_manifest_controls_identity_and_links_markdown_companion(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            pdf = papers / "opaque.pdf"
            md = papers / "opaque.md"
            pdf.write_bytes(b"placeholder")
            md.write_text("platform disclosure equilibrium evidence " * 10, "utf-8")
            manifest = base / "manifest.jsonl"
            records = [
                {
                    "path": "papers/opaque.pdf",
                    "doi": "10.1287/mnsc.2025.1234",
                    "title": "Strategic Platform Disclosure",
                    "authors": ["A. Author", "B. Author"],
                    "year": 2025,
                    "journal": "Management Science",
                },
                {
                    "path": "papers/opaque.md",
                    "paper_id": "doi:10.1287/mnsc.2025.1234",
                    "doi": "10.1287/mnsc.2025.1234",
                    "title": "Strategic Platform Disclosure",
                    "authors": ["A. Author", "B. Author"],
                    "year": 2025,
                    "journal": "Management Science",
                },
            ]
            manifest.write_text(
                "\n".join(json.dumps(row) for row in records), "utf-8"
            )
            db = base / "index.sqlite"
            with mock.patch.object(
                mod, "pdf_pages", return_value=["formal primary evidence " * 10]
            ):
                mod.build_index(
                    db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1, manifest_path=manifest
                )
            con = sqlite3.connect(db)
            self.assertEqual(con.execute("SELECT count(*) FROM papers").fetchone()[0], 1)
            kinds = {row[0] for row in con.execute("SELECT artifact_kind FROM documents")}
            status = con.execute("SELECT identity_status FROM papers").fetchone()[0]
            con.close()
            self.assertEqual(kinds, {"PRIMARY_PDF", "STRUCTURED_COMPANION"})
            self.assertEqual(status, "DOI")

    def test_exact_lookup_is_not_fuzzy(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(
                papers / "24_mnsc.2024.1234_A_Zh_Strategic Disclosure.docx",
                "strategic disclosure model evidence " * 10,
            )
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.lookup_index(db, "10.1287/mnsc.2024.1234", None, "json")
            self.assertEqual(json.loads(out.getvalue())["count"], 1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.lookup_index(db, None, "unrelated title", "json")
            self.assertEqual(json.loads(out.getvalue())["count"], 0)

    def test_paper_level_search_returns_one_candidate_for_repeated_chunks(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "shared concept paper.docx", "shared concept " * 1000)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(db, "shared concept", 20, 2, [], None, "jsonl")
            rows = [json.loads(line) for line in out.getvalue().splitlines() if line]
            self.assertEqual(len(rows), 1)
            self.assertIn("paper_id", rows[0])
            self.assertIn("corpus_fingerprint", rows[0])

    def test_benchmark_reports_recall_and_misses(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "platform pricing.docx", "platform price competition " * 10)
            write_docx(papers / "privacy.docx", "consumer privacy regulation " * 10)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            relevant = con.execute(
                "SELECT paper_id FROM papers WHERE normalized_title='platform pricing'"
            ).fetchone()[0]
            con.close()
            benchmark = base / "benchmark.jsonl"
            benchmark.write_text(
                json.dumps(
                    {
                        "query_id": "q1",
                        "query": "platform pricing",
                        "relevant_paper_ids": [relevant],
                    }
                ),
                "utf-8",
            )
            out = io.StringIO()
            with redirect_stdout(out):
                mod.benchmark_index(db, benchmark, [1, 20], "lexical", "", "", "", "")
            result = json.loads(out.getvalue())
            self.assertEqual(result["metrics"]["Recall@1"], 1.0)
            self.assertEqual(result["per_query"][0]["missed_at_max_k"], [])
            self.assertIn("retrieval_mean_s", result["cost"])
            self.assertIn("HardNegativeHitRate@1", result["hard_negative_hit_rate"])

    def test_rrf_fuses_paper_rankings_without_score_comparability(self):
        first = [{"paper_id": "a"}, {"paper_id": "b"}]
        second = [{"paper_id": "b"}, {"paper_id": "c"}]
        fused = mod.reciprocal_rank_fusion([first, second], 3)
        self.assertEqual(fused[0]["paper_id"], "b")

    def test_optional_semantic_index_uses_recorded_model_configuration(self):
        class FakeModel:
            def encode(self, texts, **kwargs):
                return [
                    [1.0, 0.0] if "privacy" in text.casefold() else [0.0, 1.0]
                    for text in texts
                ]

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "privacy.docx", "consumer privacy regulation " * 10)
            write_docx(papers / "pricing.docx", "platform price competition " * 10)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            with mock.patch.object(mod, "load_embedding_model", return_value=FakeModel()):
                with redirect_stdout(io.StringIO()):
                    mod.embed_index(db, "fake", "r1", "doc: ", "query: ", 8)
                out = io.StringIO()
                with redirect_stdout(out):
                    mod.search_index(
                        db,
                        "privacy-like-concept",
                        1,
                        1,
                        [],
                        None,
                        "jsonl",
                        strategy="semantic",
                        model="fake",
                        model_revision="r1",
                        document_prefix="doc: ",
                        query_prefix="query: ",
                    )
            result = json.loads(out.getvalue())
            self.assertEqual(result["title"], "privacy")
            self.assertEqual(result["strategy"], "semantic")

    def test_embedding_model_is_local_only_and_revision_pinned_by_default(self):
        constructor = mock.Mock(return_value=object())
        fake_module = types.SimpleNamespace(SentenceTransformer=constructor)
        with mock.patch.dict(sys.modules, {"sentence_transformers": fake_module}):
            loaded = mod.load_embedding_model("BAAI/bge-m3", "commit-123")
        self.assertIsNotNone(loaded)
        constructor.assert_called_once_with(
            "BAAI/bge-m3", revision="commit-123", local_files_only=True
        )
        with self.assertRaisesRegex(ValueError, "revision"):
            mod.load_embedding_model("BAAI/bge-m3", "")

    def test_manifest_metadata_changes_are_incremental_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            path = papers / "paper.docx"
            write_docx(path, "formal searchable evidence " * 10)
            manifest = base / "manifest.jsonl"

            def write_manifest(title):
                manifest.write_text(
                    json.dumps(
                        {
                            "path": "papers/paper.docx",
                            "paper_id": "paper:stable",
                            "title": title,
                            "authors": ["A. Author"],
                            "year": 2025,
                            "journal": "Management Science",
                        }
                    ),
                    "utf-8",
                )

            write_manifest("Old Title")
            db = base / "index.sqlite"
            mod.build_index(
                db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1, manifest_path=manifest
            )
            write_manifest("New Title")
            with redirect_stdout(io.StringIO()):
                mod.update_index(
                    db,
                    [(papers, mod.ROOT_ROLE_PAPER)],
                    workers=1,
                    manifest_path=manifest,
                )
            con = sqlite3.connect(db)
            title = con.execute("SELECT title FROM papers").fetchone()[0]
            con.close()
            self.assertEqual(title, "New Title")

    def test_citation_preflight_separates_identity_from_metadata_completeness(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(
                papers / "24_mnsc.2024.1234_A_Zh_Strategic Disclosure.docx",
                "strategic disclosure evidence " * 10,
            )
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.citation_record(db, "doi:10.1287/mnsc.2024.1234", None)
            result = json.loads(out.getvalue())
            self.assertEqual(result["identity_check"]["status"], "PASS")
            self.assertEqual(result["bibliographic_completeness"]["status"], "FAIL")
            self.assertIn("authors", result["bibliographic_completeness"]["missing"])

    def test_manifest_export_is_outside_corpus_and_roundtrippable(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "paper.docx", "searchable evidence " * 10)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            with self.assertRaises(ValueError):
                mod.export_manifest(db, papers / "manifest.jsonl")
            output = base / "manifest.jsonl"
            with redirect_stdout(io.StringIO()):
                mod.export_manifest(db, output)
            records = mod.load_manifest(output, [(papers.resolve(), mod.ROOT_ROLE_PAPER)])
            self.assertEqual(len(records), 1)

    def test_paper_fts_does_not_concatenate_full_text(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "neutral title.docx", "uniquebodymechanism evidence " * 10)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            columns = [row[1] for row in con.execute("PRAGMA table_info(papers_fts)")]
            con.close()
            self.assertNotIn("body", columns)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(db, "uniquebodymechanism", 10, 2, [], None, "jsonl")
            self.assertEqual(out.getvalue(), "")

    def test_unmanifested_markdown_is_suggested_but_not_auto_bound(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            pdf = papers / "opaque.pdf"
            md = papers / "opaque.md"
            pdf.write_bytes(b"placeholder")
            md.write_text("# Strategic Platform Disclosure\n\nmodel evidence " * 10, "utf-8")
            manifest = base / "manifest.jsonl"
            manifest.write_text(
                json.dumps(
                    {
                        "path": "papers/opaque.pdf",
                        "doi": "10.1287/mnsc.2025.1234",
                        "title": "Strategic Platform Disclosure",
                        "authors": ["A. Author"],
                        "year": 2025,
                        "journal": "Management Science",
                    }
                ),
                "utf-8",
            )
            db = base / "index.sqlite"
            with mock.patch.object(mod, "pdf_pages", return_value=["primary evidence " * 10]):
                mod.build_index(
                    db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1, manifest_path=manifest
                )
            con = sqlite3.connect(db)
            identities = dict(con.execute("SELECT paper_id,identity_status FROM documents"))
            suggestions = con.execute("SELECT count(*) FROM companion_candidates").fetchone()[0]
            con.close()
            self.assertEqual(len(identities), 2)
            self.assertIn("COMPANION_UNBOUND", identities.values())
            self.assertEqual(suggestions, 1)

    def test_multiple_query_branches_fuse_at_paper_level(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "algorithm transparency.docx", "algorithm evidence " * 20)
            write_docx(papers / "strategic disclosure.docx", "disclosure evidence " * 20)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(
                    db,
                    ["algorithm transparency", "strategic disclosure"],
                    10,
                    1,
                    [],
                    None,
                    "jsonl",
                )
            rows = [json.loads(line) for line in out.getvalue().splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(len(row["query_branches"]) == 2 for row in rows))

    def test_saved_citation_evidence_detects_source_staleness(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            path = papers / "24_mnsc.2024.1234_A_Zh_Strategic Disclosure.docx"
            write_docx(path, "supporting strategic disclosure claim " * 10)
            db = base / "index.sqlite"
            ledger = base / "citation-ledger.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            chunk_id = con.execute("SELECT chunk_id FROM chunks LIMIT 1").fetchone()[0]
            con.close()
            with redirect_stdout(io.StringIO()):
                mod.citation_record(
                    db,
                    "doi:10.1287/mnsc.2024.1234",
                    chunk_id,
                    ledger,
                    "claim-1",
                    "Disclosure changes competition.",
                    "SUPPORTED",
                    "Direct model statement.",
                )
            out = io.StringIO()
            with redirect_stdout(out):
                mod.citation_audit(db, ledger)
            self.assertEqual(json.loads(out.getvalue())["citation_audit"][0]["status"], "CURRENT")
            write_docx(path, "changed source evidence " * 20)
            with redirect_stdout(io.StringIO()):
                mod.update_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.citation_audit(db, ledger)
            self.assertEqual(
                json.loads(out.getvalue())["citation_audit"][0]["status"], "SOURCE_STALE"
            )

    def test_user_confirmed_profile_separates_role_version_and_access(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(
                papers / "24_mnsc.2024.1234_AO_Zh_Open Article.docx",
                "formal evidence " * 20,
            )
            profile_dir = base / ".msmks"
            profile_dir.mkdir()
            profile = profile_dir / "corpus_profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "profile_version": 1,
                        "corpora": [
                            {
                                "root": str(papers),
                                "artifact_codes": {
                                    "AO": {
                                        "role": "MAIN_ARTICLE",
                                        "version": "PUBLISHED",
                                        "access": "OPEN_ACCESS",
                                        "basis": "USER_CONFIRMED",
                                    }
                                },
                                "observed_structure": {},
                            }
                        ],
                    }
                ),
                "utf-8",
            )
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            role, version, access, basis = con.execute(
                "SELECT role,artifact_version,access_status,role_basis FROM documents"
            ).fetchone()
            con.close()
            self.assertEqual((role, version, access), ("MAIN_ARTICLE", "PUBLISHED", "OPEN_ACCESS"))
            self.assertEqual(basis, "CORPUS_PROFILE_USER_CONFIRMED")

    def test_source_citation_year_overrides_filename_prefix(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            path = base / "22_mksc.2022.1397_A_Zh_Strategic Information Sharing.pdf"
            path.write_bytes(b"placeholder")
            front = (
                "To cite this article: Yong Zha, Quan Li (2023) Strategic Information Sharing. "
                "https://doi.org/10.1287/mksc.2022.1397 " + "source evidence " * 20
            )
            with mock.patch.object(mod, "pdf_pages", return_value=[front]), mock.patch.object(
                mod,
                "pdf_embedded_metadata",
                return_value={"title": "Strategic Information Sharing", "journal": "Marketing Science"},
            ):
                item = mod.extract_one((str(path), str(base), mod.ROOT_ROLE_PAPER, None, None))
            self.assertEqual(item["year"], "2023")
            provenance = json.loads(item["metadata_provenance"])
            self.assertEqual(provenance["year"], "SOURCE_CITATION_BLOCK")

    def test_markdown_frontmatter_and_heading_hierarchy_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            path = base / "paper.md"
            path.write_text(
                """---
title: Structured Paper
authors: [A. Author, B. Author]
year: 2025
journal: Management Science
doi: 10.1287/mnsc.2025.9999
keywords: [platform, disclosure]
---
# Structured Paper
## Model
The platform and two sellers choose disclosure policies before price competition. """
                + "model evidence " * 20
                + """
### Timing
The platform moves first and sellers price second. """
                + "timing evidence " * 20
                + """
## Appendix
### Proof of Proposition 1
The proof establishes the equilibrium threshold. """
                + "proof evidence " * 20,
                "utf-8",
            )
            item = mod.extract_one((str(path), str(base), mod.ROOT_ROLE_PAPER, None, None))
            self.assertEqual(item["paper_id"], "doi:10.1287/mnsc.2025.9999")
            sections = {chunk["section"] for chunk in item["chunks"]}
            self.assertIn("Structured Paper > Model", sections)
            self.assertIn("Structured Paper > Model > Timing", sections)
            self.assertIn("Structured Paper > Appendix > Proof of Proposition 1", sections)

    def test_fulltext_rescue_recovers_body_only_mechanism_by_paper(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(
                papers / "neutral article.docx",
                "equilibrium leakage threshold under reseller governance " * 200,
            )
            write_docx(papers / "unrelated article.docx", "consumer search evidence " * 20)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(
                    db, "leakage threshold reseller", 5, 2, [], None, "jsonl"
                )
            self.assertEqual(out.getvalue(), "")
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(
                    db,
                    "leakage threshold reseller",
                    5,
                    2,
                    [],
                    None,
                    "jsonl",
                    full_text_rescue=True,
                    rescue_chunk_pool=100,
                )
            result = json.loads(out.getvalue())
            self.assertEqual(result["title"], "neutral article")
            self.assertTrue(result["full_text_rescue"])
            self.assertLessEqual(len(result["rescue_passages"]), 3)

    def test_user_confirmed_z_archive_is_linked_as_replication_package(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(
                papers / "24_mnsc.2024.1234_A_Zh_Dynamic Paper.docx",
                "formal model evidence " * 20,
            )
            archive_path = papers / "24_mnsc.2024.1234_Z_Zh_Dynamic Paper.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("code/solve_model.py", "print('not executed')")
                archive.writestr("data/results.csv", "x,y\n1,2\n")
            profile_dir = base / ".msmks"
            profile_dir.mkdir()
            (profile_dir / "corpus_profile.json").write_text(
                json.dumps(
                    {
                        "profile_version": 1,
                        "corpora": [
                            {
                                "root": str(papers),
                                "artifact_codes": {
                                    "A": {
                                        "role": "MAIN_ARTICLE",
                                        "version": "PUBLISHED",
                                        "access": "UNSPECIFIED",
                                        "basis": "USER_CONFIRMED",
                                    },
                                    "Z": {
                                        "role": "OTHER",
                                        "version": "UNSPECIFIED",
                                        "access": "UNSPECIFIED",
                                        "artifact_kind": "REPLICATION_PACKAGE",
                                        "basis": "USER_CONFIRMED",
                                    },
                                },
                            }
                        ],
                    }
                ),
                "utf-8",
            )
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            con.row_factory = sqlite3.Row
            rows = list(
                con.execute(
                    "SELECT role,artifact_kind FROM documents ORDER BY artifact_kind"
                )
            )
            paper_count = con.execute("SELECT count(*) FROM papers").fetchone()[0]
            archive_chunks = con.execute(
                "SELECT count(*) FROM chunks c JOIN documents d ON d.doc_id=c.doc_id "
                "WHERE d.artifact_kind='REPLICATION_PACKAGE'"
            ).fetchone()[0]
            con.close()
            self.assertEqual(paper_count, 1)
            self.assertIn(
                ("OTHER", "REPLICATION_PACKAGE"),
                [(row["role"], row["artifact_kind"]) for row in rows],
            )
            self.assertEqual(archive_chunks, 0)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(
                    db,
                    "solve_model",
                    5,
                    2,
                    [],
                    None,
                    "jsonl",
                    full_text_rescue=True,
                )
            self.assertEqual(out.getvalue(), "")

    def test_z_only_attachment_requires_explicit_other_role(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            archive_path = papers / "24_mnsc.2024.9999_Z_Zh_Archive Only.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("code/model.py", "print('not executed')")
            profile_dir = base / ".msmks"
            profile_dir.mkdir()
            (profile_dir / "corpus_profile.json").write_text(
                json.dumps(
                    {
                        "profile_version": 1,
                        "corpora": [
                            {
                                "root": str(papers),
                                "artifact_codes": {
                                    "Z": {
                                        "role": "OTHER",
                                        "version": "UNSPECIFIED",
                                        "access": "UNSPECIFIED",
                                        "artifact_kind": "REPLICATION_PACKAGE",
                                        "basis": "USER_CONFIRMED",
                                    }
                                },
                            }
                        ],
                    }
                ),
                "utf-8",
            )
            # A searchable document keeps the mixed index valid while the Z-only
            # paper remains outside ordinary paper retrieval.
            write_docx(papers / "ordinary article.docx", "ordinary evidence " * 20)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(db, "archive only", 5, 2, [], None, "jsonl")
            self.assertEqual(out.getvalue(), "")
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(db, "archive only", 5, 2, ["OTHER"], None, "jsonl")
            result = json.loads(out.getvalue())
            self.assertEqual(result["paper_id"], "doi:10.1287/mnsc.2024.9999")
            self.assertEqual(result["passages"], [])

    def test_incremental_update_handles_add_modify_rename_and_delete(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            first = papers / "first download.docx"
            second = papers / "second download.docx"
            write_docx(first, "first model evidence " * 20)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)

            write_docx(second, "second model evidence " * 20)
            with redirect_stdout(io.StringIO()):
                mod.update_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            write_docx(first, "modified first model evidence " * 30)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.update_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            self.assertEqual(json.loads(out.getvalue())["replaced"], 1)

            renamed = papers / "unrenamed publisher title.docx"
            second.rename(renamed)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.update_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            rename_summary = json.loads(out.getvalue())
            self.assertEqual((rename_summary["added"], rename_summary["removed"]), (1, 1))

            first.unlink()
            with redirect_stdout(io.StringIO()):
                mod.update_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            paths = [row[0] for row in con.execute("SELECT source_path FROM documents")]
            con.close()
            self.assertEqual(paths, [str(renamed.resolve())])

    def test_embedded_metadata_recomputes_unrenamed_pdf_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "downloaded-paper.pdf"
            path.write_bytes(b"placeholder")
            embedded = {
                "title": "Verified Source Title",
                "authors": "A. Author; B. Author",
                "year": "2024",
                "journal": "Management Science",
            }
            with mock.patch.object(mod, "pdf_embedded_metadata", return_value=embedded), mock.patch.object(
                mod,
                "pdf_pages",
                return_value=["Model evidence without a DOI " * 10],
            ):
                item = mod.extract_one(
                    (str(path), str(root), mod.ROOT_ROLE_PAPER, None, None)
                )
            self.assertEqual(item["identity_status"], "METADATA_KEY")
            self.assertTrue(item["paper_id"].startswith("meta:"))

    def test_identical_bytes_with_distinct_dois_surface_identity_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            profile = base / "profile.json"
            write_profile(profile, papers)
            first = papers / "24_mnsc.2024.5001_A_First.pdf"
            second = papers / "24_mnsc.2024.5002_A_Second.pdf"
            first.write_bytes(b"identical")
            second.write_bytes(b"identical")
            db = base / "index.sqlite"
            with mock.patch.object(
                mod, "pdf_pages", return_value=["Model searchable evidence " * 10]
            ), mock.patch.object(mod, "pdf_embedded_metadata", return_value={}):
                mod.build_index(
                    db,
                    [(papers, mod.ROOT_ROLE_PAPER)],
                    workers=1,
                    profile_path=profile,
                )
            con = sqlite3.connect(db)
            paper_ids = {row[0] for row in con.execute("SELECT paper_id FROM papers")}
            conflicts = [
                row[0]
                for row in con.execute(
                    "SELECT identity_conflict FROM documents ORDER BY source_rel"
                )
            ]
            con.close()
            self.assertEqual(len(paper_ids), 2)
            self.assertTrue(all("distinct_identity" in value for value in conflicts))

    def test_removed_duplicate_clears_generated_identity_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            profile = base / "profile.json"
            write_profile(profile, papers)
            first = papers / "24_mnsc.2024.5001_A_First.pdf"
            second = papers / "24_mnsc.2024.5002_A_Second.pdf"
            first.write_bytes(b"identical")
            second.write_bytes(b"identical")
            db = base / "index.sqlite"
            with mock.patch.object(
                mod, "pdf_pages", return_value=["Model searchable evidence " * 10]
            ), mock.patch.object(mod, "pdf_embedded_metadata", return_value={}):
                mod.build_index(
                    db,
                    [(papers, mod.ROOT_ROLE_PAPER)],
                    workers=1,
                    profile_path=profile,
                )
                second.unlink()
                with redirect_stdout(io.StringIO()):
                    mod.update_index(
                        db,
                        [(papers, mod.ROOT_ROLE_PAPER)],
                        workers=1,
                        profile_path=profile,
                    )
            con = sqlite3.connect(db)
            try:
                conflicts = [
                    row[0] for row in con.execute("SELECT identity_conflict FROM documents")
                ]
                paper_conflicts = [
                    row[0] for row in con.execute("SELECT metadata_conflict FROM papers")
                ]
            finally:
                con.close()
            self.assertEqual(conflicts, [""])
            self.assertEqual(paper_conflicts, [""])

    def test_modified_z_archive_updates_hash_without_creating_chunks(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            profile = base / "profile.json"
            write_profile(profile, papers)
            write_docx(
                papers / "24_mnsc.2024.5100_A_Main.docx",
                "formal searchable model evidence " * 10,
            )
            archive = papers / "24_mnsc.2024.5100_Z_Data.zip"
            archive.write_bytes(b"archive-v1")
            db = base / "index.sqlite"
            mod.build_index(
                db,
                [(papers, mod.ROOT_ROLE_PAPER)],
                workers=1,
                profile_path=profile,
            )
            con = sqlite3.connect(db)
            before = con.execute(
                "SELECT content_hash,size FROM documents WHERE role='OTHER'"
            ).fetchone()
            con.close()
            archive.write_bytes(b"archive-v2-with-new-bytes")
            with redirect_stdout(io.StringIO()):
                mod.update_index(
                    db,
                    [(papers, mod.ROOT_ROLE_PAPER)],
                    workers=1,
                    profile_path=profile,
                )
            con = sqlite3.connect(db)
            after = con.execute(
                "SELECT content_hash,size FROM documents WHERE role='OTHER'"
            ).fetchone()
            archive_chunks = con.execute(
                "SELECT count(*) FROM chunks c JOIN documents d ON d.doc_id=c.doc_id "
                "WHERE d.role='OTHER'"
            ).fetchone()[0]
            con.close()
            self.assertNotEqual(before, after)
            self.assertEqual(archive_chunks, 0)

    def test_appendix_passage_can_outrank_weaker_main_text_hit(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(
                papers / "Evidence Paper.docx",
                "rare mechanism appears once " + "background filler " * 100,
            )
            write_docx(
                papers / "Evidence Paper Online Appendix.docx",
                "rare mechanism " * 20 + "decisive proof boundary condition " * 20,
            )
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            con.row_factory = sqlite3.Row
            paper_id = con.execute("SELECT paper_id FROM papers LIMIT 1").fetchone()[0]
            hit = mod.best_passages(
                con, paper_id, "rare mechanism", 1, [], False, "all"
            )[0]
            con.close()
            self.assertEqual(hit["role"], "ONLINE_APPENDIX")

    def test_passage_query_error_is_not_reported_as_no_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(papers / "Evidence Paper.docx", "searchable mechanism " * 20)
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            con.row_factory = sqlite3.Row
            try:
                paper_id = con.execute("SELECT paper_id FROM papers LIMIT 1").fetchone()[0]
                with self.assertRaisesRegex(ValueError, "Passage retrieval failed"):
                    mod.best_passages(con, paper_id, '"', 1, [], True, "all")
            finally:
                con.close()

    def test_fulltext_rescue_diversifies_before_global_pool_cutoff(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(
                papers / "First Paper.docx",
                ("collision mechanism " * 80 + "\n\n") * 8,
            )
            write_docx(
                papers / "Second Paper.docx",
                "collision mechanism identifies a distinct relevant paper " * 10,
            )
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            con.row_factory = sqlite3.Row
            candidates = mod.fulltext_rescue_candidates(
                con, "collision mechanism", 10, 3, [], None, "all"
            )
            con.close()
            self.assertEqual(len({item["paper_id"] for item in candidates}), 2)

    def test_body_change_invalidates_ranking_but_z_change_does_not(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            profile = base / "profile.json"
            write_profile(profile, papers)
            article = papers / "24_mnsc.2024.5200_A_Main.docx"
            archive = papers / "24_mnsc.2024.5200_Z_Data.zip"
            write_docx(article, "Model old body evidence " * 20)
            archive.write_bytes(b"z-v1")
            db = base / "index.sqlite"
            mod.build_index(
                db,
                [(papers, mod.ROOT_ROLE_PAPER)],
                workers=1,
                profile_path=profile,
            )

            def fingerprints():
                con = sqlite3.connect(db)
                values = dict(
                    con.execute(
                        "SELECT key,value FROM meta WHERE key IN "
                        "('source_fingerprint','ranking_fingerprint')"
                    )
                )
                con.close()
                return values

            initial = fingerprints()
            archive.write_bytes(b"z-v2-different")
            with redirect_stdout(io.StringIO()):
                mod.update_index(db, [(papers, mod.ROOT_ROLE_PAPER)], 1, profile_path=profile)
            after_z = fingerprints()
            self.assertNotEqual(initial["source_fingerprint"], after_z["source_fingerprint"])
            self.assertEqual(initial["ranking_fingerprint"], after_z["ranking_fingerprint"])
            write_docx(article, "Model revised body evidence changes retrieval " * 20)
            with redirect_stdout(io.StringIO()):
                mod.update_index(db, [(papers, mod.ROOT_ROLE_PAPER)], 1, profile_path=profile)
            after_body = fingerprints()
            self.assertNotEqual(after_z["ranking_fingerprint"], after_body["ranking_fingerprint"])

    def test_profile_note_change_does_not_reextract_documents(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            profile = base / "profile.json"
            write_profile(profile, papers, note="first")
            for suffix in ("5300", "5301"):
                write_docx(
                    papers / f"24_mnsc.2024.{suffix}_A_Main.docx",
                    "formal searchable evidence " * 10,
                )
            db = base / "index.sqlite"
            mod.build_index(
                db,
                [(papers, mod.ROOT_ROLE_PAPER)],
                workers=1,
                profile_path=profile,
            )
            write_profile(profile, papers, note="documentation-only change")
            out = io.StringIO()
            with redirect_stdout(out):
                mod.update_index(
                    db,
                    [(papers, mod.ROOT_ROLE_PAPER)],
                    workers=1,
                    profile_path=profile,
                )
            result = json.loads(out.getvalue())
            self.assertTrue(result["profile_changed"])
            self.assertEqual(result["replaced"], 0)

    def test_citation_ledger_keeps_multiple_evidence_and_flags_bibliography_stale(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            path = papers / "claim-paper.docx"
            write_docx(path, "supporting claim passage " * 150)
            manifest = base / "manifest.jsonl"

            def write_manifest(title):
                manifest.write_text(
                    json.dumps(
                        {
                            "path": "papers/claim-paper.docx",
                            "doi": "10.1287/mnsc.2024.5400",
                            "title": title,
                            "authors": ["A. Author"],
                            "year": 2024,
                            "journal": "Management Science",
                        }
                    ),
                    "utf-8",
                )

            write_manifest("Original Verified Title")
            db = base / "index.sqlite"
            ledger = base / "citation.sqlite"
            mod.build_index(
                db,
                [(papers, mod.ROOT_ROLE_PAPER)],
                workers=1,
                manifest_path=manifest,
            )
            con = sqlite3.connect(db)
            chunk_ids = [row[0] for row in con.execute("SELECT chunk_id FROM chunks LIMIT 2")]
            con.close()
            self.assertEqual(len(chunk_ids), 2)
            for chunk_id in chunk_ids:
                with redirect_stdout(io.StringIO()):
                    mod.citation_record(
                        db,
                        "doi:10.1287/mnsc.2024.5400",
                        chunk_id,
                        ledger,
                        "claim-shared",
                        "The paper supports a compound claim.",
                        "SUPPORTED",
                        "Joint evidence.",
                    )
            ledger_con = sqlite3.connect(ledger)
            saved = ledger_con.execute(
                "SELECT count(*) FROM citation_evidence WHERE claim_id='claim-shared'"
            ).fetchone()[0]
            ledger_con.close()
            self.assertEqual(saved, 2)
            write_manifest("Corrected Verified Title")
            with redirect_stdout(io.StringIO()):
                mod.update_index(
                    db,
                    [(papers, mod.ROOT_ROLE_PAPER)],
                    workers=1,
                    manifest_path=manifest,
                )
            out = io.StringIO()
            with redirect_stdout(out):
                mod.citation_audit(db, ledger)
            statuses = {
                row["status"] for row in json.loads(out.getvalue())["citation_audit"]
            }
            self.assertEqual(statuses, {"BIBLIOGRAPHY_STALE"})

    def test_multi_query_passages_are_allocated_round_robin(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            write_docx(
                papers / "alpha mechanism beta boundary.docx",
                "alpha mechanism evidence " * 80 + " beta boundary evidence " * 80,
            )
            db = base / "index.sqlite"
            mod.build_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            out = io.StringIO()
            with redirect_stdout(out):
                mod.search_index(
                    db,
                    ["alpha mechanism", "beta boundary"],
                    5,
                    2,
                    [],
                    None,
                    "jsonl",
                )
            result = json.loads(out.getvalue())
            passages = " ".join(item["chunk_text"] for item in result["passages"])
            self.assertIn("alpha mechanism", passages)
            self.assertIn("beta boundary", passages)

    def test_paper_metadata_uses_field_level_provenance_cascade(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            papers.mkdir()
            main = papers / "24_mnsc.2024.5500_A_Main.pdf"
            appendix = papers / "opaque-supplement.pdf"
            main.write_bytes(b"main")
            appendix.write_bytes(b"appendix")
            manifest = base / "manifest.jsonl"
            manifest.write_text(
                json.dumps(
                    {
                        "path": "papers/opaque-supplement.pdf",
                        "paper_id": "doi:10.1287/mnsc.2024.5500",
                        "title": "Manifest Verified Title",
                        "authors": ["Verified Author"],
                        "year": 2025,
                        "journal": "Management Science",
                        "role": "ONLINE_APPENDIX",
                    }
                ),
                "utf-8",
            )

            def embedded(path):
                if path == main:
                    return {
                        "title": "Unreliable Embedded Title",
                        "authors": "Wrong Author",
                        "year": "2024",
                        "journal": "Management Science",
                    }
                return {}

            db = base / "index.sqlite"
            with mock.patch.object(
                mod, "pdf_pages", return_value=["formal searchable evidence " * 10]
            ), mock.patch.object(mod, "pdf_embedded_metadata", side_effect=embedded):
                mod.build_index(
                    db,
                    [(papers, mod.ROOT_ROLE_PAPER)],
                    workers=1,
                    manifest_path=manifest,
                )
            con = sqlite3.connect(db)
            paper = con.execute(
                "SELECT title,authors,year,metadata_source,metadata_provenance "
                "FROM papers WHERE paper_id='doi:10.1287/mnsc.2024.5500'"
            ).fetchone()
            con.close()
            self.assertEqual(paper[:3], ("Manifest Verified Title", "Verified Author", "2025"))
            self.assertEqual(paper[3], "FIELD_LEVEL_CASCADE")
            self.assertEqual(json.loads(paper[4])["title"], "MANIFEST")


if __name__ == "__main__":
    unittest.main()
