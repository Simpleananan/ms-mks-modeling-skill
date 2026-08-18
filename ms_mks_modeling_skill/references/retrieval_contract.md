# Evidence retrieval contract

Load this reference before running `scripts/local_evidence_retrieval.py`, choosing local/web source mode, or deciding local-to-web fallback. Also load `evidence_policy.md` to qualify retrieved passages.

## Source-mode gate

Local evidence is optional, not a prerequisite. Resolve one mode before literature retrieval:

- **HYBRID** — authorized local paper and/or review-response materials are available. Search them first and use web retrieval for live evidence gaps.
- **WEB_ONLY** — no authorized local source is available, or the user declines local scanning. Retrieve from the web and continue the same modeling/validation workflow.
- **LOCAL_ONLY** — only when the user explicitly disallows web retrieval; report corpus-coverage limitations.

If uploaded papers or review/response materials are already present, treat them as authorized local evidence for the current task and do not ask again. If retrieval is needed and no local source is known, ask once whether the user wants local paper/review-response sources combined with web search. Never send private full text, reviewer text, response text, local paths, or manuscript identifiers to a web search service; use public DOI/title metadata or a de-identified structural query.

## Architecture and write boundary

Use this pipeline:

`rg identity/file discovery -> persistent incremental SQLite FTS5 recall -> work-level grouping -> Codex structural semantic reranking -> evidence qualification -> modeling reasoning`.

The index is disposable derived data. Keep it outside every source root. The script reads PDF/DOCX sources and never writes to them. Do not put caches, extracted text, sidecars, or metadata files in a knowledge base. Rebuild the index if its schema is incompatible.

## Commands

```powershell
python scripts/local_evidence_retrieval.py build --db <derived-index.sqlite> --paper-root <paper-root> --process-root <review-response-root>
python scripts/local_evidence_retrieval.py update --db <derived-index.sqlite> --paper-root <paper-root> --process-root <review-response-root>
python scripts/local_evidence_retrieval.py search --db <derived-index.sqlite> --query 'platform AND disclosure' --limit 8 --passages-per-work 2 --format jsonl
python scripts/local_evidence_retrieval.py inspect --db <derived-index.sqlite> --chunk-id <id> --context 1
python scripts/local_evidence_retrieval.py stats --db <derived-index.sqlite> --format json
```

Use `rg --files` first for likely filenames, DOI fragments, manuscript IDs, and exact known terms. Use FTS5 for passage recall and structural query variants. `build` creates a new persistent index; `update` adds, replaces, and removes only changed artifacts in one SQLite transaction.

## Retrieval units and roles

Keep both work identity and artifact identity. Group duplicate files, main articles, and appendices at the work level so one paper cannot occupy the candidate set through many chunks.

Minimum metadata: `work_id`, `artifact_id`, role, title, authors, year, journal, DOI when available, page/section, source path, relative source, chunk index/text, file size/mtime/content hash, extraction error, and lexical score. Empty metadata stays unknown; do not infer it from a search snippet.

Roles are `MAIN_ARTICLE`, `ONLINE_APPENDIX`, `COMMENT_CORRECTION`, and `PROCESS_EVIDENCE`, with `OTHER` for unclassified artifacts. Role is not evidence strength.

## Query, grouping, and reranking

1. Express the evidence need as a structural question, not only topic keywords.
2. Generate a small set of lexical variants for institution, actors, timing/information, actions, and mechanism.
3. Recall more candidates than will be cited.
4. Group by `work_id`; inspect at most a few top passages per work before expanding.
5. Have Codex rerank work groups using structural fit: institution, timing/commitment, information, feasible actions, payoff mechanism, claim, and evidence depth.
6. Inspect the full chunk and nearby chunks/pages before relying on it.
7. Apply D0-D4 and the evidence-usefulness gate. `bm25`/`lexical_score` never means evidence strength.

The script deliberately does not decide semantic relevance, modeling quality, evidence depth, or whether a citation supports a claim.

## Hybrid/local-to-web fallback

In **HYBRID** mode, start with authorized local sources and trigger official web retrieval when a live evidence need remains and one of these holds:

- no structurally close local work was found after reasonable query reformulation;
- local evidence stops at D0/D1 for a D2/D3 judgment;
- recent MS/MKS norms or publications may change the nearest-neighbor or contribution comparison;
- local evidence conflicts and an official article, appendix, correction, or version is needed;
- a decisive DOI, appendix, or passage is missing locally.

In **WEB_ONLY** mode, begin with authoritative web retrieval immediately and apply the same D0-D4 qualification, usefulness gate, version checks, and decision-delta stopping rule. Absence of a local corpus must not lower the formal modeling/validation standard.

Prioritize official Management Science/Marketing Science sources, then other relevant UTD journals. Record why fallback was triggered. Do not use web search to compensate for an unformulated evidence need.

## Stopping rule

Continue only if another retrieval step has a realistic chance of changing a viable formalization, nearest-neighbor set, evidence conflict, assumption justification, claim boundary, verdict, or confidence. Stop when the decision is stable across the strongest retrieved evidence and one material contrast, or when further access cannot raise the needed evidence depth. State coverage limitations honestly.

For pure algebra, supplied first-order conditions, deterministic computation, or an internal contradiction fully decidable from the model, skip retrieval and calculate directly.
