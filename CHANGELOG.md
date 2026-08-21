# Changelog

## v0.5.0-rc3 — 2026-08-21

### Distribution and Codex discovery

- Updated user-level installation guidance from the legacy `~/.codex/skills` location to the current Codex `$HOME/.agents/skills` location, while retaining `.codex/skills` only as a migration diagnostic.
- Reworked `skill_doctor.py` to inspect the current user Skill root plus repository `.agents/skills` roots from CWD up to the Git root, mirroring current Codex discovery more closely.
- Added explicit warnings when only a legacy user-level copy exists or when a current install coexists with a legacy copy.
- Shortened and front-loaded `SKILL.md` trigger metadata so the main MS/MKS modeling use cases remain visible if Codex truncates Skill descriptions in large Skill sets.

### GitHub presentation

- Rebuilt `README.md` as a public-facing project page: research pain points and differentiators first, then typical prompts, model-centered workflow, current installation steps, optional local evidence retrieval, boundaries, validation, and repository map.
- Kept README positioning descriptive rather than normative: it does not turn marketing language into runtime requirements or claim universal MS/MKS practices.
- Clarified that the repository is a standalone GitHub Skill for local Codex use, while current OpenAI guidance recommends Plugins for broader installable distribution.

### Release validation

- Added generic version-synchronization tests across `VERSION`, `SKILL.md`, README, changelog, and release-validation documentation.
- Added local Markdown-link validation and a regression check that README no longer teaches the legacy `~/.codex/skills` clone path.
- Added default-location and legacy-location tests for `skill_doctor.py`.
- Preserved the v0.5 research-model-centered workflow, v0.4 C0-C8 certification layer, retrieval behavior, local-data firewall, and behavioral A/B protocols unchanged in substance.

## v0.5.0-rc2 — 2026-08-21

### Research-model-centered architecture

- Added explicit `LOCAL` versus `MODEL/PAPER-WIDE` task scope so broad audits gain global discovery without burdening local algebra/proposition questions.
- Added research-object/model-architecture analysis before solution, including a minimal-model challenge, assumption-to-result distance, and a result-desirability firewall.
- Added breadth-first Material Map and Canonical Model Map for whole-paper/model audits so proposition lists no longer define the entire validation search space.
- Added cross-material consistency checks for timing, information, action/parameter domains, constraints, solution concept, benchmarks, welfare definitions, notation, and narrative scope.
- Strengthened the independent path from re-deriving an author-named candidate to claim-independent characterization of materially relevant solution/regime structure before comparison with source propositions.
- Added mechanism identification/falsification using assumption-leverage mapping, mechanism shutdown/freeze, benchmark isolation, minimal-model comparison, and alternative-mechanism checks when decision-relevant.
- Added cross-claim synthesis for parameter gaps/overlaps, incompatible assumptions or equilibrium selections, and proposition-to-discussion scope overreach.
- Preserved v0.4 C0-C8 formal certification, boundary/threshold analysis, source acknowledgment, scoped certificates, retrieval firewall, and all original end-to-end research modules.

### Evidence and MS/MKS calibration

- Added explicit evidence roles for institutional precedent, primitive precedent, mechanism precedent, solution/equilibrium convention, and novelty collision.
- Added mechanism-driven retrieval guidance derived from the canonical model graph rather than topic labels alone.
- Added v0.5 local-corpus falsification targets for mechanism isolation, assumption leverage, minimal baselines, cross-material consistency, and narrative-scope discipline.
- Explicitly states that breadth-first census, mechanism-shutdown, and minimal-model diagnostics are Skill heuristics to test against MS/MKS papers, not universal journal rules.

### Behavioral regression

- Added hidden-defect acceptance cases for proposition anchoring, cross-material timing drift, omitted branches, narrative overreach, cross-claim gaps, mechanism misattribution, unnecessary model complexity, result engineering, robustness targeting, and local-task over-triggering.
- Expanded persistent state with Material Map, Canonical Model Map, independent solution-space map, Assumption-Leverage Map, mechanism-falsification state, and cross-material/cross-claim consistency notes.

## v0.4.0-rc3 — 2026-08-21

### Release-integrity and Agent Skills compatibility

- Added bundled-license reference, `compatibility`, and version metadata to `SKILL.md` while keeping the trigger description below the Agent Skills 1024-character limit.
- Clarified that the discovery/install folder should be named `ms-mks-modeling` even when the GitHub repository is named `ms-mks-modeling-skill`.
- Fixed `skill_doctor.py` so running it from the source checkout no longer treats the checkout itself as an active discovery root by default; it now also warns on discovery-folder/name mismatch.
- Regenerated the release manifest from the final clean package and added tests that reject stale manifest entries, `__pycache__`, and `.pyc` artifacts.

### Retrieval correctness and process-evidence firewall

- Ordinary search now excludes `PROCESS_EVIDENCE` by default; process materials require explicit `--role PROCESS_EVIDENCE`.
- `update --db ...` now reuses the index's stored root configuration when no roots are supplied.
- Supplying roots on `update` now means the complete authoritative root configuration, and documents from omitted roots are pruned instead of remaining as hidden stale evidence.
- Reject overlapping/nested declared source roots to keep provenance and paper/process roles unambiguous.
- Added regression tests for default process isolation, stored-root reuse, omitted-root pruning, and overlapping-root rejection.

### Formal-protocol clarification

- Clarified that skipping a separate adversarial critic pass for a decidable calculation never skips certification checks activated by the requested conclusion.
- Renamed the C0-C8 precondition language from “proof obligations” to “certification obligations” so the protocol also fits implicit, computational, and numerical solution methods.
- Added a public-source verification date to the MS/MKS calibration file.

## v0.4.0-rc2 — 2026-08-21

### Full-workflow preservation

- Rebuilt v0.4 from the original package rather than from the narrower rc1 rewrite.
- Preserved orientation from incomplete prompts, target-paper reconstruction, literature-stream recomposition, candidate generation/evaluation, research convergence, solution explanation, repair/selective revision, shadow drafting, exemplar-vs-novelty screening, citation rendering, and stakeholder decision routing.
- Preserved original v0.1-v0.3 design/product/retrieval documents under `docs/legacy/` with a historical-status notice.

### Formal modeling and validation

- Added source/formal/claim truth separation and provenance labels.
- Added dual-track source reconstruction and independent derivation with earliest material divergence.
- Added claim-driven source closure and material source acknowledgment for main-text/appendix treatments.
- Added source/constraint/domain/feasible-set/case/candidate/equilibrium/claim closure.
- Added Boundary and Threshold Gate, including threshold equalities and attained optimum versus supremum/infimum.
- Added substitution-back, targeted falsification, scoped solution certificates, and `STALE` dependency handling.
- Added analytical regime decomposition before brute-force parameter sweeps.

### Evidence

- Preserved D0-D4, source-priority, exemplar-vs-novelty, process-evidence firewall, and citation/provenance rules.
- Added conservative MS/MKS public calibration anchors; stronger formal/norm claims are explicitly deferred to D3/D4 local-corpus verification.

### Retrieval and distribution

- Repository root is now the single installable Skill.
- Replaced hidden process-root classification with explicit `--paper-root` / `--process-root`.
- Added Windows symlink/reparse-point/junction containment.
- Added optional `update --verify-hash`.
- Added duplicate-install doctor, deterministic retrieval tests, structural preservation tests, behavioral acceptance cases, and a release scanner.
- Moved runtime data-boundary rules into the retrieval contract; kept the prior privacy document only as historical documentation.
- Replaced the previous license that conflicted with clone/download/agent use with a GitHub-installable research-use license.

## v0.4.0-rc1

Superseded internal release candidate. It introduced the main certification ideas but over-compressed several original full-workflow modules. rc2 restores them.
