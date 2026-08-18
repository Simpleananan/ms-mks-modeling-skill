# MS/MKS Evidence-Grounded Modeling Skill

A research-modeling skill for constructing, diagnosing, validating, repairing, and comparing analytical/game-theoretic models for **Management Science** and **Marketing Science** contexts. The runtime skill lives in `ms_mks_modeling_skill/`.

## Evidence-source modes

The skill does **not** require a local knowledge base. When literature evidence is needed it resolves one of three modes:

- **HYBRID** — combine authorized local paper/review-response materials with web retrieval. Local evidence is searched first; web is used for remaining live evidence gaps.
- **WEB_ONLY** — if the user has no local corpus or declines local scanning, use web retrieval alone. Modeling and validation quality gates remain the same.
- **LOCAL_ONLY** — only when the user explicitly disables web retrieval; the answer must state corpus-coverage limitations.

If papers, appendices, reviewer/editor comments, decision letters, or response letters are already supplied in the current task, the skill treats them as authorized evidence and does not ask for them again. If retrieval is needed and no local source is known, the skill asks once whether the user wants local sources combined with web search.

Private local material is never sent to web search. Web queries should contain only public bibliographic metadata (for example a published DOI/title) or a de-identified structural question.

## Local retrieval (optional)

The included script builds a disposable read-only-derived SQLite FTS5 index. It supports separate root classes so review-process materials are never mistaken for published evidence.

```bash
python ms_mks_modeling_skill/scripts/local_evidence_retrieval.py build \
  --db /path/outside/the/corpus/evidence.sqlite \
  --paper-root /path/to/papers \
  --process-root /path/to/review-response-materials
```

Use either root type alone if that is all you have. `pdftotext` must be installed for PDF extraction; the Python script otherwise uses the standard library. The index is cache/derived state and should not be committed.

## Repository layout

- `ms_mks_modeling_skill/SKILL.md` — runtime behavior.
- `ms_mks_modeling_skill/references/` — evidence, retrieval, modeling/validation, and feedback rules.
- `ms_mks_modeling_skill/scripts/local_evidence_retrieval.py` — optional local retrieval prototype.
- `docs/` — design and benchmark documentation, with private benchmark identifiers and local paths removed.
- `scripts/privacy_scan.py` — lightweight pre-commit privacy/secret scan.
- `PRIVACY.md` — local-data and public-release boundary.

## Before publishing

Run:

```bash
python scripts/privacy_scan.py .
```

The scanner is intentionally conservative and does not replace GitHub secret scanning or a dedicated tool such as gitleaks/trufflehog. Do not commit local databases, source corpora, review/response materials, `.env` files, or research checkpoints.

## License

No license is bundled in this package. Choose and add a license before public release if you want others to have explicit reuse rights.
