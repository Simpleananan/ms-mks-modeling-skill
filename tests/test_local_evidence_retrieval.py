from __future__ import annotations

import importlib.util
import argparse
import os
from pathlib import Path
import sqlite3
import subprocess
import io
from contextlib import redirect_stdout
import tempfile
import unittest
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
        '<w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p></w:body></w:document>'
    )
    info = zipfile.ZipInfo("word/document.xml")
    info.date_time = (2026, 1, 1, 0, 0, 0)
    info.compress_type = zipfile.ZIP_STORED
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(info, xml.encode("utf-8"))


class RetrievalTests(unittest.TestCase):
    def test_process_root_is_explicitly_classified(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"
            process = base / "process"
            papers.mkdir(); process.mkdir()
            write_docx(papers / "paper.docx", "formal article text " * 8)
            write_docx(process / "response.docx", "review response text " * 8)
            db = base / "index.sqlite"
            mod.build_index(
                db,
                [(papers, mod.ROOT_ROLE_PAPER), (process, mod.ROOT_ROLE_PROCESS)],
                workers=1,
            )
            con = sqlite3.connect(db)
            rows = dict(con.execute("SELECT source_rel, role FROM documents"))
            con.close()
            self.assertEqual(rows["process/response.docx"], "PROCESS_EVIDENCE")
            self.assertNotEqual(rows["papers/paper.docx"], "PROCESS_EVIDENCE")


    def test_overlapping_roots_are_rejected(self):
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

    def test_update_explicit_roots_prunes_omitted_root(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"; papers.mkdir()
            process = base / "process"; process.mkdir()
            write_docx(papers / "paper.docx", "shared keyword formal paper " * 8)
            write_docx(process / "response.docx", "shared keyword reviewer response " * 8)
            db = base / "index.sqlite"
            mod.build_index(
                db,
                [(papers, mod.ROOT_ROLE_PAPER), (process, mod.ROOT_ROLE_PROCESS)],
                workers=1,
            )
            mod.update_index(db, [(papers, mod.ROOT_ROLE_PAPER)], workers=1)
            con = sqlite3.connect(db)
            rows = list(con.execute("SELECT role FROM documents ORDER BY role"))
            roots = con.execute("SELECT value FROM meta WHERE key='source_roots'").fetchone()[0]
            con.close()
            self.assertEqual(rows, [("OTHER",)])
            self.assertNotIn(str(process.resolve()), roots)

    def test_stored_roots_can_be_reused_for_update(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"; papers.mkdir()
            process = base / "process"; process.mkdir()
            write_docx(papers / "paper.docx", "formal article text " * 8)
            write_docx(process / "response.docx", "review response text " * 8)
            db = base / "index.sqlite"
            expected = [(papers.resolve(), mod.ROOT_ROLE_PAPER), (process.resolve(), mod.ROOT_ROLE_PROCESS)]
            mod.build_index(db, expected, workers=1)
            args = argparse.Namespace(
                paper_root=[], root=[], process_root=[], db=db
            )
            stored = mod.root_specs_from_args(args, reuse_stored_for_update=True)
            self.assertEqual(stored, expected)
            mod.update_index(db, stored, workers=1)
            con = sqlite3.connect(db)
            count = con.execute("SELECT count(*) FROM documents").fetchone()[0]
            con.close()
            self.assertEqual(count, 2)

    def test_default_search_excludes_process_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            papers = base / "papers"; papers.mkdir()
            process = base / "process"; process.mkdir()
            write_docx(papers / "paper.docx", "sharedkeyword formal article evidence " * 8)
            write_docx(process / "response.docx", "sharedkeyword reviewer process evidence " * 8)
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
                    db, "sharedkeyword", 10, 2, ["PROCESS_EVIDENCE"], None, "jsonl"
                )
            self.assertIn("PROCESS_EVIDENCE", out.getvalue())

    def test_same_root_cannot_have_conflicting_roles(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"
            root.mkdir()
            with self.assertRaises(ValueError):
                mod.validate_locations(
                    Path(td) / "index.sqlite",
                    [(root, mod.ROOT_ROLE_PAPER), (root, mod.ROOT_ROLE_PROCESS)],
                )

    def test_db_inside_source_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"
            root.mkdir()
            with self.assertRaises(ValueError):
                mod.validate_locations(
                    root / "index.sqlite",
                    [(root, mod.ROOT_ROLE_PAPER)],
                )

    def test_verify_hash_catches_same_size_same_mtime_replacement(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "papers"
            root.mkdir()
            path = root / "paper.docx"
            write_docx(path, "A" * 120)
            db = base / "index.sqlite"
            mod.build_index(db, [(root, mod.ROOT_ROLE_PAPER)], workers=1)
            original_stat = path.stat()
            con = sqlite3.connect(db)
            old_hash = con.execute("SELECT content_hash FROM documents").fetchone()[0]
            con.close()

            write_docx(path, "B" * 120)
            self.assertEqual(path.stat().st_size, original_stat.st_size)
            os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

            mod.update_index(db, [(root, mod.ROOT_ROLE_PAPER)], workers=1, verify_hash=False)
            con = sqlite3.connect(db)
            unchanged_hash = con.execute("SELECT content_hash FROM documents").fetchone()[0]
            con.close()
            self.assertEqual(unchanged_hash, old_hash)

            mod.update_index(db, [(root, mod.ROOT_ROLE_PAPER)], workers=1, verify_hash=True)
            con = sqlite3.connect(db)
            new_hash = con.execute("SELECT content_hash FROM documents").fetchone()[0]
            con.close()
            self.assertNotEqual(new_hash, old_hash)
            self.assertEqual(new_hash, mod.file_sha256(path))

    def test_symlink_child_is_not_scanned(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "root"; root.mkdir()
            outside = base / "outside"; outside.mkdir()
            write_docx(outside / "outside.docx", "outside text " * 8)
            link = root / "linked"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlink unavailable")
            found = mod.scan_sources([(root, mod.ROOT_ROLE_PAPER)])
            self.assertEqual(found, [])

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction_child_is_not_scanned(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "root"; root.mkdir()
            outside = base / "outside"; outside.mkdir()
            write_docx(outside / "outside.docx", "outside text " * 8)
            junction = root / "junction"
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )
            if result.returncode != 0:
                self.skipTest("junction creation unavailable")
            found = mod.scan_sources([(root, mod.ROOT_ROLE_PAPER)])
            self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
