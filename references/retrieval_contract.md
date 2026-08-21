# Local Evidence Retrieval Contract

The local retrieval layer is optional. It performs lexical recall and work-level grouping; the modeling agent remains responsible for structural reranking, evidence-depth qualification, and formal reasoning.

## 1. Authorization and local-data boundary

- Read local corpus roots only when the user has supplied/authorized them for the task.
- Treat source roots as read-only inputs.
- Store the derived SQLite index outside every source root.
- Never modify, rename, move, or delete source papers or process materials.
- Do not send private local text, unpublished manuscript identifiers, private filenames, or machine-local paths to public web search.
- For web fallback, use public metadata (e.g. DOI/title already public) or a de-identified structural query.
- Do not commit derived databases, private corpora, local state, credentials, or logs to the public repository.

These are runtime data-boundary rules, not a claim that this repository operates a hosted service or collects user data.

## 2. Evidence roles are explicit

Roots are classified by the command line, not by hidden folder-name conventions or environment variables.

- `--paper-root PATH` -> published/formal local corpus. Repeat as needed.
- `--process-root PATH` -> reviewer/editor/author-response or other process evidence. Repeat as needed.
- legacy `--root PATH` -> deprecated alias for `--paper-root`; use only for migration.

A root may not be supplied simultaneously as both paper and process evidence, and declared source roots must not overlap or nest inside one another.

Example:

```bash
python scripts/local_evidence_retrieval.py build \
  --db /path/outside/corpus/ms_mks.sqlite \
  --paper-root /path/to/papers \
  --process-root /path/to/process-materials
```

Windows PowerShell:

```powershell
python scripts/local_evidence_retrieval.py build `
  --db D:\indexes\ms_mks.sqlite `
  --paper-root D:\research\papers `
  --process-root D:\research\process_materials
```

No `MKS_PROCESS_ROOT_NAMES` environment variable is used.

## 3. Commands

### Build

```bash
python scripts/local_evidence_retrieval.py build \
  --db /outside/root/ms_mks.sqlite \
  --paper-root /corpus/papers \
  --process-root /corpus/process
```

### Incremental update

Fast default update uses path + size + modification time and, when no roots are supplied, reuses the root configuration stored by the previous build/update:

```bash
python scripts/local_evidence_retrieval.py update \
  --db /outside/root/ms_mks.sqlite
```

If any `--paper-root` or `--process-root` arguments are supplied on update, they are the **complete authoritative root set** for the derived index. Use this deliberately when adding/removing roots; documents from omitted roots are pruned. Source roots must be disjoint rather than nested, so each indexed file has unambiguous provenance and evidence role.

If files may have been restored/synchronized while preserving size and timestamps, enable content verification:

```bash
python scripts/local_evidence_retrieval.py update \
  --db /outside/root/ms_mks.sqlite \
  --verify-hash
```

`--verify-hash` intentionally hashes otherwise unchanged files; use it as a periodic integrity check rather than mandatory cost on every edit.

### Search

```bash
python scripts/local_evidence_retrieval.py search \
  --db /outside/root/ms_mks.sqlite \
  --query 'information disclosure equilibrium' \
  --limit 10
```

Ordinary search excludes `PROCESS_EVIDENCE` by default. Retrieve process evidence explicitly only when it is the live evidence need:

```bash
python scripts/local_evidence_retrieval.py search \
  --db /outside/root/ms_mks.sqlite \
  --query 'reviewer boundary condition' \
  --role PROCESS_EVIDENCE
```

### Inspect and stats

```bash
python scripts/local_evidence_retrieval.py inspect --db /outside/root/ms_mks.sqlite --chunk-id 123 --context 2
python scripts/local_evidence_retrieval.py stats --db /outside/root/ms_mks.sqlite
```

## 4. Retrieval pipeline

Use:

`FTS5 lexical recall -> work-level grouping -> structural reranking -> evidence-depth qualification -> modeling/validation`.

Do not treat BM25/FTS score as evidence quality.

For a formal target-paper claim, retrieval is not finished until the relevant main-text statement and proof/appendix dependencies are inspected. Search broader literature only if the modeling decision requires comparison or precedent.

## 5. Process-evidence firewall

`PROCESS_EVIDENCE` may generate questions such as:

- Which assumption did a reviewer contest?
- Which boundary or deviation was added during revision?
- Which institutional interpretation was disputed?

It must not be silently promoted into published/formal evidence. A response letter saying “we proved X” does not prove X; inspect the corresponding model/proof.

## 6. Filesystem safety

The scanner must not descend through symlinks or Windows reparse-point/junction children. It also verifies that a candidate file resolves inside its declared source root before indexing it. A junction inside a corpus should be skipped, not crash the build and not pull an external tree into the index.

The database location is rejected if it lies inside any source root.

## 7. Freshness semantics

Default incremental detection is optimized for normal editing. It can miss an adversarial or synchronization scenario in which both file size and timestamp are preserved. `--verify-hash` closes that boundary by comparing current SHA-256 with the stored content hash.

A schema-version mismatch requires rebuilding the derived index. The source corpus is unaffected.

## 8. Public-web fallback

Local-first does not mean local-only. Use web fallback when public verification, publication status, corrections, or missing literature can materially change the answer. Keep web queries abstracted away from nonpublic content unless the user has made that content public and explicitly wants it searched.
