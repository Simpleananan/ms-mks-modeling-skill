# Design v0.4 — full workflow plus formal certification

## Design objective

The Skill remains an end-to-end MS/MKS analytical-modeling research assistant. v0.4 does **not** replace exploratory modeling with model auditing. It adds a formal-certification layer to the existing workflow.

Core research workflow:

`orient/reconstruct -> retrieve when useful -> build/solve/diagnose -> compare/criticize -> converge/repair -> communicate`

Formal certification sits inside the solve/critic stages:

`source reconstruction -> independent derivation -> closure checks -> targeted falsification -> reconcile -> scoped certificate`.

## Why closure is the unifying failure model

The observed failures—misreading an appendix, dropping some constraints, reporting a solution in an empty region, stopping at an interior candidate, missing a threshold equality, or projecting one branch globally—are all forms of premature closure. The Skill therefore asks not only “what did I check?” but “what justifies believing the relevant source/constraint/case/equilibrium/domain set is complete enough for this claim?”

## Dual-track audit

For an existing model, Track A reconstructs the author/user path; Track B derives independently. Agreement increases confidence but does not remove boundary/domain checks. Disagreement triggers earliest-divergence diagnosis instead of immediate deference or contradiction.

## Preservation rule

The v0.4 upgrade follows **preserve unless superseded**. Orientation, literature-stream recomposition, candidate generation, convergence, solution explanation, selective repair, shadow drafting, exemplar-vs-novelty retrieval, citation rendering, and stakeholder decision routing remain first-class capabilities.

## Runtime versus design history

Current runtime authority: `SKILL.md` and `references/`. Historical design assets are under `docs/legacy/` and are never loaded as current runtime rules merely because they remain in the repository.

## Retrieval firewall as an engineering invariant

Process evidence is not merely a label for later reasoning. Ordinary retrieval excludes `PROCESS_EVIDENCE` by default, so reviewer/editor/response material enters a task only through an explicit process-evidence search. Update root configuration is also explicit: no-root update reuses the stored set; supplying roots replaces the complete set and prunes omitted roots. Declared roots must be disjoint so role provenance is not ambiguous.

## Agent Skills packaging invariant

The main `SKILL.md` stays below the Agent Skills recommended size and keeps only always-needed routing, pass activation, evidence/state discipline, answer projection, and resume rules. Detailed modeling, evidence, retrieval, and feedback logic remains one reference hop away. The discovery folder should match the frontmatter name `ms-mks-modeling`; the GitHub repository name need not.
