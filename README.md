# MS/MKS Modeling

Turn a research intuition, target paper, or unfinished game into a model decision you can defend.

**MS/MKS Modeling** is a local Codex Skill for analytical and game-theoretic research in Management Science, Marketing Science, and neighboring UTD fields. It helps researchers move from vague phenomena to formal research questions, reconstruct published models, diagnose failed mechanisms, compare competing formalizations, repair or redesign a game, and qualify claims with paper- and appendix-level evidence.

It is designed for the point where generic brainstorming stops being useful: when timing, information, actions, incentives, equilibrium, and contribution must line up.

## What it helps you do

- **Start before the model exists.** Orient a phenomenon or institutional observation, identify the strategic tension, and form a small set of genuinely different research directions.
- **Learn a target paper structurally.** Recover the game, the load-bearing assumptions, the solution dependency, the mechanism, and the actual claim boundary.
- **Build and solve.** Translate a research question into primitives, feasible strategies, payoffs, constraints, and an appropriate solution concept.
- **Find the real failure.** Separate notation or exposition issues from structural defects that change the research object, equilibrium, mechanism, or welfare claim.
- **Repair without result engineering.** Trace a broken result to its causal source, test credible repairs, and accept a negative theoretical conclusion when no defensible mechanism survives.
- **Choose among models.** Select, conditionally select, or remain inconclusive based on research fit, strategic consequences, tractability, and nearest-neighbor evidence.
- **Use literature as evidence.** Search local papers and appendices first, distinguish published results from review-process materials, and use web fallback when it can change the decision.

## Why it is different

The Skill follows a complete but model-adaptive research chain:

```text
research object
-> institution
-> applicable formal objects
-> endogenous response
-> equilibrium or solution
-> mechanism or contribution object
-> claim, welfare, and boundary
```

Its output is decision-focused, while formal verification remains complete internally. It does not reward complexity, counterintuitive signs, thresholds, or citations for their own sake. It asks whether the model actually carries the research question and what should happen next.

## Evidence-grounded, local-first

The package includes an SQLite retrieval helper for local PDF, DOCX, and user-supplied structured Markdown collections. It uses stable paper identities and artifact hashes, accepts an external bibliographic manifest, keeps paper-metadata and full-passage indexes separate, retrieves paper candidates before evidence passages, and can invoke bounded full-text rescue when a mechanism appears only in the body or appendix. It conservatively suggests unbound companions and supports exact DOI/title lookup. It does not perform MinerU conversion.

Recurring libraries can keep a root-scoped corpus profile outside the source folders, so Codex reuses confirmed naming conventions and structural observations instead of relearning the corpus every conversation. The profile is not a frozen file list: incremental synchronization handles additions, deletions, edits, and renames. Automatically observed patterns remain review signals; only user-confirmed mappings can classify filename codes. Unrenamed papers remain usable through source metadata or provisional identity. Replication ZIP/7z attachments are linked and hashed but remain opaque and excluded from ordinary retrieval until a task genuinely needs them. Bibliographic fields retain source-level provenance, and Markdown headings are parsed into section hierarchies when Markdown is present.

Lexical retrieval works with the Python standard library and SQLite FTS5. Coherent query branches default to conjunctive matching and can be repeated for paper-level fusion. Optional full-text rescue and local semantic retrieval are benchmark-gated by the decision and retrieval layer. The benchmark reports Recall@K, formulation consistency, hard-negative hits, and misses; exact lookup remains a separate test.

Retrieval supplies candidates and passages. Codex remains responsible for source inspection, evidence qualification, formal reasoning, and research judgment.

## Typical prompts

```text
I have a partial platform-information model. Reconstruct the game, identify the
main structural risk, and help me repair it without changing the research question.
```

```text
Start from this Marketing Science paper and its Online Appendix. Explain the
load-bearing solution step, then compare two possible extensions.
```

```text
My advisor suggests adding endogenous information acquisition. Evaluate whether
that change solves a real problem, what it does to equilibrium, and whether a
smaller alternative exists.
```

## What it does not promise

The Skill does not establish global novelty, guarantee publication, replace institutional knowledge, certify every theorem automatically, or turn review-process opinions into formal truth. Sparse-idea generation and contribution screening remain evidence-bounded research judgments.

## Install

Install this repository with Codex's Skill installer, or place the inner `ms-mks-modeling` directory at:

```text
$HOME/.agents/skills/ms-mks-modeling
```

Codex also supports repository-scoped installation under `.agents/skills`. Keep only one discoverable copy with the name `ms-mks-modeling`. See the [official Codex Skills documentation](https://developers.openai.com/codex/skills) for current discovery locations.

## Project status

Version `0.9.4-rc1` is a release candidate for controlled real-research validation. Automated tests cover package integrity, dynamic corpus synchronization, recomputation and clearing of duplicate-identity conflicts, rule-scoped profile updates, separated retrieval layers, paper-diverse bounded full-text rescue, relevance-first main/appendix passage location, explicit retrieval-error handling, structured Markdown parsing, default isolation and correct versioning of replication packages, field-level metadata provenance, conservative companion binding, balanced multi-query evidence allocation, dependency-specific retrieval staleness, multi-location citation records, bibliographic staleness, and local-only revision-pinned semantic model loading. Real main-article/appendix tests also cover claim-scope qualification; a larger corpus-specific held-out benchmark is still required before claiming retrieval improvement or promoting semantic/hybrid retrieval for high-stakes novelty screening.
