# Local literature retrieval and citation contract

Load this reference before searching an authorized local corpus, changing its index, screening contribution collision, or preparing a claim-bearing citation.

## Non-negotiable invariants

1. **Identity is explicit.** Every candidate and evidence passage must resolve to one `paper_id`, one artifact, and one content hash. DOI identity is preferred. Complete manifest metadata (`title + authors + year`) is the next-best deterministic identity; filename-derived identities remain `PROVISIONAL_FILENAME` and cannot pass a formal citation check.
2. **Evidence does not drift.** Retrieval summaries, tags, embeddings, and Codex-generated mechanism descriptions are navigation aids, never source evidence. A claim-bearing judgment must return to an inspected source location.
3. **Novelty is not a single Top-K result.** An absence/collision judgment must use an intentionally broad, multi-query search and record the corpus fingerprint and coverage boundary. Failure to retrieve is not evidence of nonexistence.
4. **Citations separate truth from display.** Verify bibliographic identity and claim support at an inspected location. Check target-journal formatting only when producing a manuscript or bibliography that requires it; conversational display may remain deliberately compact. Passing one check does not imply the others.

These invariants constrain evidence quality, not the research path. Codex chooses query families, retrieval arms, candidate counts, sections, comparison dimensions, and reading depth according to the live modeling decision.

## Division of responsibility

- The library-maintenance module recognizes, indexes, and links PDFs, Markdown, appendices, and other artifacts that the user has already placed in the authorized corpus. MinerU conversion is performed by the user outside this Skill; neither this Skill nor the retrieval script converts documents.
- `local_evidence_retrieval.py` owns deterministic profile/manifest ingestion, hashing, incremental synchronization, separated paper/passage retrieval, bounded full-text rescue, exact lookup, artifact-linked passages, and benchmark measurement.
- Codex owns task-specific query design, structural comparison, evidence-depth qualification, source inspection, model reconstruction, claim-support judgment, and stopping.

Do not let this Skill rename, convert, download, or rewrite corpus files. Source roots are read-only. Store the SQLite index, manifest, embeddings, benchmark, and research state outside every source root.

## Paper identity, artifacts, and versions

`paper_id` identifies a scholarly work; a path identifies only an artifact location.

- Preferred identity: `doi:<normalized-doi>`.
- Without a DOI: a manifest-provided stable ID, then a deterministic key from normalized title, authors, and year.
- Filename-only grouping is provisional. It is useful for recall but must be repaired before formal citation or confident deduplication.
- Main PDF, online appendix, correction, source DOCX, and MinerU/other Markdown are separate artifacts. They share a `paper_id` only after deterministic metadata or user-confirmed manifest binding establishes that relationship.
- Code, data, replication archives, and other miscellaneous attachments are linked artifacts, not alternative article versions. They may support reproduction or reveal implemented assumptions, but do not inherit the evidentiary role of the published article.
- A Markdown file is `STRUCTURED_COMPANION`. It can improve navigation and retrieval, but it does not silently replace the published PDF. For a load-bearing claim, check the PDF or establish and retain the companion-to-PDF location mapping.
- An unmanifested Markdown file remains `COMPANION_UNBOUND`, is excluded from paper candidates, and may appear in `companion-suggestions`. Same directory plus high stem/title agreement creates a review suggestion only; it never auto-merges identity. Confirm the link by adding `paper_id`/DOI in the manifest.
- `content_hash` identifies artifact bytes. The paper `content_fingerprint` changes when canonical metadata or any linked artifact changes. A separate `retrieval_fingerprint` uses only ordinary searchable article/correction artifacts and searchable metadata: changing an opaque Z package changes source inventory but does not invalidate paper retrieval or embeddings, while changing searchable body text does.
- Identical bytes assigned to distinct paper identities are a blocking conflict, not a deduplication shortcut. Recompute that conflict from the current corpus after every synchronization so deleting or correcting the duplicate also clears the obsolete alarm; never retain a generated historical conflict as if it described current evidence.
- A working paper and published article are not automatically the same evidentiary version merely because their titles resemble each other. Link them only with verified metadata and retain the version used for each claim.

### Root-scoped corpus profile

On first contact with a recurring library, inspect the file inventory and only a bounded, purposive content sample. Store language, directory organization, available artifact types, reliable metadata sources, observed filename patterns, and unresolved patterns in a profile outside every evidence root. Reuse it across conversations. Counts and directory inventories are dated observations, not an allowlist or frozen corpus definition. Ordinary additions, deletions, modifications, and renames are handled by index synchronization; run `profile-audit` when new naming, extension, or directory patterns may change interpretation, and refresh only artifacts whose applicable confirmed rule changed. Descriptive profile edits must not trigger full-corpus extraction.

An observed filename pattern is not an identity rule. The script applies `artifact_codes` only when each mapping has `basis: USER_CONFIRMED`. Keep role, scholarly version, and access status separate: an open-access suffix describes access, not whether a file is a main article or appendix. Unknown codes stay unknown until confirmed. DOI/content metadata and the manifest outrank the profile for paper identity and bibliography.

Confirmed filename codes are corpus-specific. Record each confirmed meaning in the profile for the corpus where it was confirmed, keep access status separate from scholarly role, and never carry one corpus's code meanings into a different corpus without separate confirmation. A code that has not been confirmed stays unknown.

Filename normalization is optional. Files that do not match a learned pattern remain indexable. Resolve them through manifest, DOI/front matter, embedded metadata, then title/authors/year; if these are insufficient, keep a provisional identity and surface it for later repair. Lack of a renamed filename may reduce identity confidence or pairing quality, but must not make a readable paper unusable.

### Manifest

Use JSONL, a JSON array, or `{"papers": [...]}`. Each record must contain `path`; provide as many of `paper_id`, `doi`, `title`, `authors`, `year`, `journal`, `abstract`, `keywords`, `role`, and `artifact_kind` as are known. `authors` and `keywords` may be strings or lists. The manifest is authoritative for metadata, not file contents.

```json
{"path":"papers/paper.pdf","doi":"10.1287/mnsc.2025.1234","title":"...","authors":["A. Author","B. Author"],"year":2025,"journal":"Management Science"}
{"path":"papers/paper.md","paper_id":"doi:10.1287/mnsc.2025.1234","artifact_kind":"STRUCTURED_COMPANION"}
```

Audit `stats` after build/update. Resolve provisional identities and metadata conflicts before citing affected papers. Bibliographic metadata follows a field-level cascade: manifest, source DOI/citation block or front matter, embedded document metadata, then filename/DOI-namespace fallbacks. Cache each field's provenance. A complete-looking citation assembled only from fallback fields does not pass bibliographic truth. Public Crossref/OpenAlex or publisher metadata may verify identity, but do not send private titles, manuscript identifiers, filenames, or paths to public services.

Run `companion-suggestions --db ...` after adding MinerU Markdown. Review the candidate and then bind it in the manifest; the command deliberately has no “accept automatically” mode.

For Markdown with ATX headings, parse front matter and preserve the full section hierarchy (`Model > Timing`, `Appendix > Proof`, and so on) deterministically. Use this structure for navigation and passage location. When Markdown is absent, PDF extraction remains the normal path. Structured Markdown improves location efficiency; it does not gain evidentiary authority over the published PDF.

`manifest-export --db ... --out ...` creates an atomic JSONL bootstrap outside the corpus. Treat it as a review queue: enrich missing authors/year/journal/DOI through the library-maintenance workflow, then pass the corrected file back through `--manifest`. Do not assume exported filename fallbacks are already verified metadata.

### External bibliographic catalog versus local artifact manifest

A Web of Science, Crossref, OpenAlex, or reference-manager export can broaden discovery and improve metadata, but it is not the local artifact manifest. Keep catalog records without local files and artifact-bound manifest records in separate layers. Match catalog records to local papers by DOI first; use normalized title plus authors/year only as a confidence-scored candidate match, never an automatic weak merge.

For search, label catalog results internally as `LOCAL_FULL_TEXT`, `LOCAL_METADATA_ONLY`, or `EXTERNAL_ONLY`. An external abstract can nominate a paper but cannot support a full-text model claim. Do not emit a routine acquisition list. Only when an `EXTERNAL_ONLY` paper's full text is genuinely needed to resolve the current decision, give `English title — authors — why needed`; omit year, journal, DOI, links, and download instructions unless requested. Do not report that Codex read the paper.

Do not import an uninspected all-record export directly as authoritative local metadata: it can contain papers absent from the corpus, duplicates, early-access/final-year discrepancies, and incomplete identifiers. Normalize the actual export format first and retain its source and export date. A parser should be implemented and tested against a user-supplied sample rather than guessing the chosen Web of Science field set.

## Persistent index lifecycle

Use one stable database per authorized root set. `build` is for a missing, incompatible, corrupt, or deliberately rebuilt database. Ordinary corpus changes use `update`; `--verify-hash` catches replacements that preserve size and timestamp. An update without roots reuses the stored root configuration. Supplying roots defines the complete authoritative set.

The paths below are portable examples. Substitute your own; the index, manifest, profile, and research state must stay outside every source root.

```powershell
python scripts/local_evidence_retrieval.py build --db "$HOME\msmks\index\msmks.sqlite" `
  --paper-root "$HOME\corpus\papers" --process-root "$HOME\corpus\process" `
  --manifest "$HOME\msmks\index\paper_manifest.jsonl"

python scripts/local_evidence_retrieval.py update --db "$HOME\msmks\index\msmks.sqlite" --verify-hash
python scripts/local_evidence_retrieval.py stats --db "$HOME\msmks\index\msmks.sqlite" --format json
python scripts/local_evidence_retrieval.py profile-audit --profile "$HOME\msmks\index\corpus_profile.json" `
  --paper-root "$HOME\corpus\papers" --process-root "$HOME\corpus\process"
```

Build is atomic. Extraction failures are reported. A failed update preserves an existing searchable record when possible. Process evidence is excluded from ordinary paper search unless explicitly requested.

`update` rescans the current roots: new files are added, deleted paths are removed, changed size/mtime records are re-extracted, and renames become a remove-plus-add while DOI or verified metadata preserves paper identity. Use `--verify-hash` periodically or before high-stakes work to detect the rare replacement that preserves both size and timestamp. The corpus profile does not need manual rewriting after every ordinary change.

ZIP/7z replication packages are hashed and attached to their paper, but ordinary indexing creates no content passages from them. They remain outside default lexical, semantic, passage, and full-text-rescue retrieval. Inspect archive members or contents only when a task specifically needs code, data, numerical implementation, or an encoded model assumption; never automatically execute them.

## Two retrieval layers and adaptive routing

The candidate object is always a paper. `papers_fts` indexes weighted title, abstract, keywords, headings, authors, and journal metadata; it never concatenates full text into a paper BM25 document. `chunks_fts` indexes full passages. It normally locates evidence inside selected papers, but can also supply a bounded rescue arm whose passage hits are immediately aggregated to `paper_id`. A passage score cannot turn an anonymous chunk into a paper-level nearest neighbor or verified evidence.

- **Exact identity need:** use `lookup --doi` or normalized `lookup --title`. Do not substitute fuzzy search.
- **Clear English concept:** start with one coherent paper-level BM25 branch. Tokens within a branch default to conjunction (`--match all`); use `--match any` only for a deliberately curated synonym set, never for every word in a long question.
- **Chinese question, mainly English corpus:** first formulate English branches for the research object, institution, mechanism, formal objects, and field terminology. SQLite `unicode61` does not supply dependable academic Chinese segmentation. A benchmarked multilingual semantic arm may supplement—not replace—English lexical branches.
- **Vocabulary or conceptual mismatch:** add a benchmarked paper-level semantic arm when title/abstract terminology may differ.
- **Body/appendix-only mechanism or an unexplained miss:** enable bounded full-text rescue. Admit each paper's best passage into the global candidate pool before applying its cutoff, aggregate to paper candidates, and retrieve further passages only after selection. This prevents one verbose paper from crowding every other paper out. Do not run rescue by default merely because it exists.
- **High-stakes broad screening:** generate only causally or terminologically distinct query branches. The number is evidence-driven, not fixed. Repeat `--query` to fuse branches at paper level; inspect misses/near neighbors and expand to public web evidence when the local boundary is inadequate.
- **Deep evidence:** after the candidate set stabilizes, inspect the main article and only the sections/appendices capable of changing the current model or claim.

This is an adaptive escalation policy, not a fixed sequence. A known-paper verification may stop after exact lookup and source inspection. A novelty screen normally cannot.

`--limit` is a per-run candidate budget, not a scientific claim that only that many papers matter. Do not use one universal count and do not run an unbounded search. Start with the cheapest depth capable of changing the decision, then widen when distinct query branches disagree, known relevant papers are missed, the cutoff contains unresolved near-neighbors, or the claim is an absence/collision claim. Stop when additional depth is unlikely to change the candidate set or modeling judgment; if compute or evidence ends first, return `INCONCLUSIVE` with the coverage boundary instead of converting the cutoff into “no literature.”

```powershell
python scripts/local_evidence_retrieval.py lookup --db "$HOME\msmks\index\msmks.sqlite" --doi 10.1287/mnsc.2025.1234
python scripts/local_evidence_retrieval.py search --db "$HOME\msmks\index\msmks.sqlite" `
  --query "platform disclosure competition" `
  --query "information release downstream price competition" `
  --limit 50 --format jsonl
python scripts/local_evidence_retrieval.py search --db "$HOME\msmks\index\msmks.sqlite" `
  --query "leaking equilibrium reseller" --full-text-rescue `
  --rescue-chunk-pool 1000 --limit 50 --format jsonl
python scripts/local_evidence_retrieval.py inspect --db "$HOME\msmks\index\msmks.sqlite" `
  --paper-id doi:10.1287/mnsc.2025.1234
```

BM25, cosine similarity, and fusion scores are ranking signals, not evidence strength or structural similarity. Codex compares only task-relevant model structure. Use game objects when a game is activated; use primitives/states/controls/objective/constraints/transition/solution for other analytical forms when applicable. Do not require a universal Model Card.

## Optional semantic and hybrid retrieval

Semantic retrieval is optional and benchmark-gated. The script uses a `sentence-transformers` model, stores paper-level embeddings in SQLite, and performs brute-force cosine search suitable for a personal corpus. Model loading is local-only by default. A named model identifier must include a pinned revision; use a local model directory when no revision is needed. `--allow-model-download` is an explicit network/dependency action and is used only after the user authorizes downloading that pinned revision. It does not require a hosted API or vector database.

```powershell
python scripts/local_evidence_retrieval.py embed --db "$HOME\msmks\index\msmks.sqlite" `
  --model BAAI/bge-m3 --model-revision REVISION --allow-model-download
python scripts/local_evidence_retrieval.py search --db "$HOME\msmks\index\msmks.sqlite" `
  --query "双寡头市场中质量信号如何影响定价" --strategy hybrid `
  --model BAAI/bge-m3 --model-revision REVISION --limit 50
```

Choose a model because it improves held-out retrieval at the layer where it will be used, not because it is fashionable. Paper encoders and passage encoders solve different tasks. For example, SPECTER2 is designed around scientific-paper title/abstract representations and task-specific query/retrieval adapters, whereas BGE-M3 exposes multilingual, long-context dense/sparse/multi-vector capabilities useful to test for cross-lingual and passage retrieval. These are candidate roles, not hard-coded winners. The bundled semantic backend accepts a `sentence-transformers`-compatible dense encoder only: it does not wire SPECTER2's adapter workflow, and using BGE-M3 through this path does not activate its sparse or multi-vector modes. Add a dedicated backend only after a layer-specific benchmark justifies it. A paper benchmark cannot authorize a passage model, or vice versa. Record model revision and query/document prefixes. Hybrid results use reciprocal-rank fusion so incomparable lexical and cosine scales are not directly added. Use `passage-search --paper-id ...` only after paper selection; it does not re-rank the corpus.

A retrieval exception is an unresolved tooling state, never an empty evidence set. Surface it and repair or change the query; do not translate a parser, FTS, model, or database failure into “no relevant paper” or “no supporting passage.”

## Retrieval benchmark and missed-retrieval audit

Use a small, real, versioned benchmark in JSONL or JSON. Each paper-retrieval row contains `query_id`, one `query` or multiple equivalent `queries`, and `relevant_paper_ids`; optional `match`, `case_type`, and `hard_negative_paper_ids` expose policy and diagnostic cases. Include:

- exact DOI/title lookup tests, kept separate from fuzzy retrieval metrics;
- Chinese questions against English papers;
- mechanism-equivalent formulations with disjoint surface vocabulary;
- topic-similar but mechanism-different hard negatives;
- long, authentic Chinese and English research questions;
- novelty screens with multiple relevant papers;
- one core paper expressed through multiple query formulations, all of which should retrieve it.

```json
{"query_id":"platform-disclosure-01","queries":["platform disclosure downstream competition","information release price competition"],"relevant_paper_ids":["doi:10...."],"case_type":"query_invariance","match":"all"}
```

Run `benchmark --k 20 --k 50` for each candidate retrieval strategy. Treat Recall@20/50 as the primary safety metric for screening; also inspect per-query misses, known hard-negative hits, and recorded model-load/query time. A set of “papers I remember” is incomplete relevance judgment, so reported recall is benchmark recall, not true corpus recall. Keep a held-out slice or add new queries after failures to reduce overfitting. Promote semantic/hybrid retrieval only when it improves the decision-relevant benchmark without unacceptable cost.

## Dependency-specific staleness, novelty snapshots, and citation evidence

Before writing “not found,” “unexplored,” or a similar contribution claim, retain internally:

- corpus fingerprint and update time;
- local roots and important coverage gaps;
- query families and retrieval arms;
- candidate depth and unresolved near neighbors;
- public-web expansion boundary;
- benchmark version or known recall limitation.

Do not use a single changed fingerprint to invalidate everything:

- `SOURCE_STALE`: the artifact hash or supporting locator for a positive claim changed or disappeared. Recheck only claims depending on that source.
- `BIBLIOGRAPHY_STALE`: verified title, authors, year, journal, DOI, identity status, metadata conflict, or their provenance changed while the supporting source passage remained stable. Recheck identity display separately from claim support.
- `COVERAGE_STALE`: authorized roots or the eligible paper set changed. Re-run absence, novelty, and collision conclusions that depended on coverage.
- `RANKING_STALE`: the saved `retrieval_run_fingerprint` changes because searchable metadata, schema, retrieval configuration, model, query family, or cutoff changed. Re-run saved candidate rankings before relying on their ordering or cutoff.

A new paper can stale “no one studies X” without staling “Paper A proves X.” Save the relevant fingerprint(s) with the claim rather than copying one global status into every result.

Use `citation-record --paper-id ... --chunk-id ...` as a deterministic preflight. It must report both identity completeness and bibliographic-truth provenance. After Codex reads the source and judges support, save each material supporting location with the claim, verdict, rationale, stable locator, page/section, source hash, bibliography fingerprint, supporting passage, and verification time to an external research-workspace ledger with `--ledger`, `--claim-id`, `--claim-text`, and `--verdict`. One claim may retain multiple paper/main-text/appendix evidence rows; adding one must not overwrite another. Run `citation-audit --ledger ...` after source or metadata updates; it detects `SOURCE_STALE` and `BIBLIOGRAPHY_STALE`. The ledger is not generated metadata in the disposable retrieval index. A saved passage still does not replace reading the relevant proof/appendix.

Bibliographic verification runs internally when a citation becomes claim-bearing; it does not require a full formatted citation in the conversational answer. When papers materially informed the answer, list only `Authors — Verified English Title（忠实中文译名）` at the end. Derive the English title from the paper or reliable bibliographic metadata, not the local filename. A Web of Science export can supply candidate metadata, but identity and claim support remain separate checks. Use full target-journal formatting only inside a manuscript/bibliography deliverable that actually requires it.
