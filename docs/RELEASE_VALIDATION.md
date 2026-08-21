# Release validation — v0.5.0-rc3

Validation date: **2026-08-21**.

## Scope

This audit rechecked the full v0.5 package rather than only the modeling prompt. It covered runtime instructions, Agent Skills metadata, current Codex discovery guidance, retrieval scripts, package tests, cross-file versioning, Markdown links, release manifest, README positioning, and the preservation of the research-model-centered workflow introduced in v0.5.

The research logic itself was not expanded merely to improve the README. rc3 is primarily a **distribution, discoverability, presentation, and release-integrity** tightening on top of rc2.

## Issues found in rc2

### 1. User-level Codex install path in README was stale

rc2 still instructed users to clone into `~/.codex/skills`. Current OpenAI Codex documentation lists `$HOME/.agents/skills` as the user-level local Skill location and scans repository `.agents/skills` directories from CWD up to the repository root.

**rc3 fix:** README and migration guidance now use `.agents/skills`; `.codex/skills` appears only as a legacy migration location.

### 2. `skill_doctor.py` mirrored an older discovery model

The rc2 doctor defaulted to `$HOME/.codex/skills` plus only `$CWD/.agents/skills`. That could both privilege the old user path and miss repository-scoped Skill roots located above a nested CWD.

**rc3 fix:** the doctor now checks:

- current user root: `$HOME/.agents/skills`;
- repository `.agents/skills` roots from CWD upward to the Git root;
- legacy `$HOME/.codex/skills` only as a migration warning.

It remains read-only and never deletes or retargets files.

### 3. Trigger metadata was valid but unnecessarily long

rc2's `description` satisfied the 1024-character Agent Skills limit but used **957 characters** and front-loaded a long capability list before the clearest "Use for..." trigger. Current Codex guidance notes that Skill descriptions may be shortened when many Skills are installed and recommends front-loading the key use case and trigger words.

**rc3 fix:** the description is shortened to **763 characters** and begins with the MS/MKS analytical/game-theoretic use case while preserving broad trigger coverage.

### 4. README was technically complete but weak as a public project page

The rc2 README opened with version history and installation details before clearly communicating the research problem, differentiators, and typical uses. It read more like internal release documentation than a GitHub landing page.

**rc3 fix:** README is reorganized around:

`research problem -> differentiators -> typical prompts -> model-centered workflow -> installation -> optional local corpus -> data boundary -> limitations -> validation -> repository map`.

The public language is intentionally descriptive rather than normative; no promotional wording is promoted into runtime requirements.

### 5. Release checks did not automatically guard several presentation/distribution drifts

The package had manual link checks and hard-coded version assertions, but no generic cross-file version synchronization check and no automated local Markdown-link integrity test.

**rc3 fix:** added generic version synchronization, relative Markdown-link validation, README current-path regression checks, and current/legacy `skill_doctor` behavior tests.

## Current Agent Skills / Codex compatibility check

Checked against:

- OpenAI, **Build skills**: <https://learn.chatgpt.com/docs/build-skills>
- Agent Skills specification: <https://agentskills.io/specification>

Confirmed for this package:

- one root `SKILL.md` in the installable Skill directory;
- `name: ms-mks-modeling` conforms to naming constraints;
- installable ZIP root is `ms-mks-modeling/`, matching the frontmatter name;
- description is non-empty and below 1024 characters;
- compatibility field is below 500 characters;
- license points to the bundled `LICENSE` file;
- detailed material remains progressively disclosed through `references/` rather than expanding `SKILL.md` into a monolithic reference;
- current user/repository local discovery guidance uses `.agents/skills`;
- README notes that direct Skill folders are appropriate for local/repository use while current OpenAI guidance prefers Plugins for broader installable distribution.

## Automated package checks

After final edits and manifest regeneration, the source-tree suite ran **27 tests: 26 PASS; 1 SKIP**. The only skip in the Linux build environment is the Windows-only junction creation test.

Checks include:

- Python/unit-test suite;
- Agent Skills frontmatter constraints;
- version synchronization across `VERSION`, `SKILL.md`, README, changelog, and this release-validation file;
- single runtime `SKILL.md`;
- original full-workflow preservation;
- v0.5 research-object/model-census/solution-discovery/mechanism/cross-claim preservation;
- answer-projection, Math Display Gate, draft discipline, and Resume preservation;
- current-model state-map preservation;
- default `PROCESS_EVIDENCE` exclusion and explicit process search;
- stored-root reuse and explicit-root pruning;
- conflicting/overlapping evidence-root rejection;
- source-root write containment and symlink traversal containment;
- same-size/same-mtime replacement detection under `--verify-hash`;
- current user Skill-location doctor behavior;
- legacy `.codex/skills` warning behavior;
- discovery-folder/name diagnostics;
- relative Markdown-link integrity;
- README current install-path regression;
- release secret scan;
- strict personal-data pattern scan;
- deterministic manifest/tree equivalence;
- rc2 institution-mapping / implementation-consistency / negative-space benchmark tests;
- A/B evaluation protocol presence/content.

## Behavioral acceptance suite

`tests/BEHAVIORAL_ACCEPTANCE.md` contains **34 adversarial cases**.

B1–B21 preserve the v0.4 tests for source acknowledgment, author error, alternate formulation, empty domains/feasible sets, constraints, boundaries, threshold equality, numerical-proof limits, process evidence, authority invariance, state invalidation, sparse orientation, literature recomposition, convergence, novelty screening, solution explanation, and stakeholder classification.

B22–B34 add hidden-defect tests for proposition anchoring, cross-material timing drift, author-unnamed equilibrium branches, narrative scope overreach, cross-claim gaps, mechanism misattribution, unnecessary model complexity, result engineering, robustness targeting, LOCAL-task over-triggering, institution-to-model drift, formal-model/code drift, and missing mechanism-isolating benchmarks.

These behavioral cases are specifications, not automated LLM judgments. They still need clean Skill-versus-no-Skill execution using `tests/A_B_EVALUATION.md`.

## Research-model architecture status

The v0.5 architecture remains unchanged in substance from rc2:

- `LOCAL` versus `MODEL/PAPER-WIDE` audit scope;
- research-object/model-architecture quality before formal certification;
- breadth-first Material/Canonical Model census for broad audits;
- claim-independent solution-space discovery;
- mechanism identification/falsification with safeguards;
- cross-claim/narrative synthesis;
- v0.4 C0–C8 source/constraint/domain/feasibility/boundary/candidate/equilibrium/claim closure and targeted falsification.

rc3 does **not** add new modeling gates merely for release polish.

## MS/MKS calibration status

The public calibration layer remains deliberately narrow. Official INFORMS article/abstract pages are used only for structural examples; they are not treated as proof of universal MS/MKS norms.

Stronger questions—proof completeness, boundary coverage, empty regimes, mechanism-isolation practices, baseline minimality, cross-material consistency, and narrative-scope discipline—remain D3/D4 local-corpus verification tasks under `docs/LOCAL_KB_VERIFICATION.md`.

## Remaining release gates before stable v0.5.0

1. Run the full unit suite on the target Windows machine so the junction/reparse-point creation test executes rather than skips.
2. Run B1–B34 in a clean Skill-versus-no-Skill A/B setup with special attention to material discovery gain and false-positive rate.
3. Run the local MS/MKS D3/D4 verification protocol, including counterexamples to the Skill's own mechanism/minimality diagnostics.
4. Confirm that broad audits improve material issue discovery without materially degrading LOCAL-task efficiency.
5. Confirm the final installation/update flow on the actual Codex client used by the target researchers.
