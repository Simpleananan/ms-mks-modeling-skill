# Formal validation and diagnosis

Load this reference when the task asks whether a model, equilibrium, proposition, mechanism, welfare statement, or computational result is correct or complete. Apply checks from the model structure and claim; do not run a universal checklist.

## Separate the objects being validated

For source-based work distinguish:

- **Source truth:** what the source states, assumes, derives, and qualifies.
- **Formal truth:** what follows from the reconstructed primitives, domains, timing, information, actions, payoffs, constraints, and solution concept.
- **Claim truth:** the exact parameter, equilibrium, and domain scope supported by the analysis.

Source authority establishes what was claimed, not mathematical validity. An alternative derivation does not establish source error until differences in assumptions, domains, conventions, and solution concepts are ruled out.

When the source already treats a material boundary, exception, deviation, regime, or robustness case, acknowledge that treatment before giving an independent judgment. Do not present a source-handled issue as a new discovery.

When provenance matters, mark a load-bearing object as source-explicit, derived, necessary but unstated, conventional, analyst-added, or unknown. Do not silently convert an analyst-added condition into an author or user assumption.

## Scope the audit

For a local equation, derivation, proposition, or region, inspect that object and any dependency capable of overturning it.

For a broad model or paper audit, first build a compact material map and one canonical model map:

`players -> timing/commitment -> information/beliefs -> actions/domains -> payoffs/constraints -> solution concept -> regimes/equilibria -> claims`.

Compare repeated definitions across model text, proofs, appendices, extensions, welfare sections, and supplied code or numerical routines when material. Treat an explicitly declared extension as a separate branch, not an inconsistency. Report silent changes only when they alter feasibility, equilibrium, mechanism, or claim scope.

### Material coverage before an absence-based diagnosis

Before declaring a primitive, assumption, constraint, definition, equilibrium condition, selection rule, or boundary case formally missing, identify the supplied model-bearing locations where it could reasonably appear. Search relevant main-text sections, appendices, proofs, supplements, cross-references, and linked model/code files, then inspect the locations capable of resolving the issue. A material map is claim-relative: it does not require reading every supplied file for a local calculation.

Use separate conclusions:

- **FORMALLY MISSING:** the relevant supplied materials have been covered sufficiently and the object is absent or cannot be reconstructed. Use `FAIL` only if that absence violates an activated formal obligation or invalidates the scoped claim.
- **FORMALLY PRESENT / ADEQUATELY LOCATED:** the object or proof is in a linked appendix, supplement, or proof and the main text states the applicable scope or gives an adequate cross-reference. Do not manufacture an exposition defect merely because details are outside the main text.
- **FORMALLY PRESENT / EXPOSITION GAP:** the object exists elsewhere and repairs formal closure, but the claim-bearing presentation is materially overbroad, untimely, or incorrectly cross-referenced. Diagnose the exposition or claim-scope problem without calling the scoped model formally incomplete.
- **UNRESOLVED / SOURCE-RESOLVABLE:** plausible model-bearing locations remain unchecked or unavailable. Record a candidate gap and continue retrieval; do not upgrade absence to `FAIL`.

This gate applies to conclusions whose evidence is nonappearance. It does not suppress a concrete contradiction, infeasible candidate, omitted profitable deviation, or counterexample already established within the relevant scope. If the user explicitly asks whether a standalone excerpt is self-contained, evaluate that exposition scope directly while withholding any claim that the complete model lacks the object.

## Evidence-based criticism of published work

Published status raises the prior that the paper survived review; it does not certify every equation, proof, interpretation, or sentence. Critique in this order:

1. Recover the exact claim, baseline assumptions, parameter domain, version, and linked proof/appendix treatment.
2. Rule out extraction/OCR corruption, notation conventions, an explicitly separate extension, and a silently changed comparison benchmark.
3. Produce the cheapest decisive basis: an internal source conflict, violated condition, infeasible candidate, algebraic divergence, admissible counterexample, omitted profitable deviation, or numerical reproduction with verified implementation.
4. Classify narrowly:
   - **CONFIRMED FORMAL ERROR** only when the scoped claim fails on a verified admissible case or derivation;
   - **CLAIM-SCOPE / EXPOSITION PROBLEM** when the formal result survives in its baseline domain but prose, abstract, or managerial interpretation exceeds that domain;
   - **LIKELY TYPO** only when local inconsistency and surrounding derivation identify the intended correction;
   - **UNRESOLVED** when another version, appendix passage, extraction check, or derivation can still decide the issue.

Do not call an assumption wrong merely because it is restrictive, or a result wrong because it is counterintuitive. Conversely, do not suppress a supported problem because the paper is published. State the earliest failing link, affected scope, and whether the main theorem, extension, interpretation, or only notation is implicated.

Across claims, inspect material parameter gaps or overlaps, changes in assumptions or equilibrium selection, and whether discussion, welfare, policy, or managerial conclusions exceed the formally certified scope.

Use two paths for consequential source validation:

1. Reconstruct the source's derivation and equilibrium logic faithfully.
2. Independently characterize the material feasible/equilibrium branches from the canonical model rather than treating the source's final formula as a premise.

If the paths differ, locate the earliest material divergence before assigning fault.

## Closure before certification

Before a consequential `PASS`, existence, uniqueness, globality, equilibrium, or welfare conclusion, close the obligations activated by the claim:

- **Specification:** all decisive primitives, timing/information rules, action domains, payoffs, constraints, and solution concepts are known or explicitly unresolved.
- **Constraint inventory:** include applicable probability, demand/coverage, participation/IR, IC, capacity, budget, market-clearing, outside-option, transition, and accounting conditions.
- **Parameter domain:** the conjunction of stated restrictions is nonempty.
- **Feasible set:** at least one admissible strategy/profile exists in the claimed region.
- **Candidate verification:** retained candidates satisfy their domains, constraints, defining optimality/equilibrium conditions, and any transformations used to derive them.
- **Boundary and regime coverage:** inspect material corners, threshold equalities, piecewise switches, open-domain limits, participation regimes, ties, multiplicity, and cross-region comparisons.
- **Equilibrium closure:** consider deviations, participation choices, continuation branches, selection or refinement, and alternative candidates capable of overturning the claim.
- **Claim scope:** distinguish local, branch-specific, parameter-region, and global validity.

For open domains, distinguish an attained optimum from a supremum or infimum. A solved FOC, symbolic expression, numerical solver output, or one equilibrium branch is not self-certifying.

After establishing the strongest case, make one targeted attempt to break the load-bearing node. Target an active-constraint intersection, equality case, extreme admissible parameter, singularity, competing branch, or profitable deviation. Numerical counterexample search can falsify a universal claim; failure to find one on a grid is not proof.

Prefer analytical or symbolic reduction, then regime partition, targeted computation, and counterexample search. Use brute-force sweeps only when the solution method genuinely requires them.

## Activate checks from structure

| Model feature | Material checks |
|---|---|
| Private information or inference | Information sets, feasible conditioning, posterior/Bayes consistency, off-path beliefs when relevant |
| Signaling, disclosure, persuasion, communication | Incentives, credibility, observability, verifiability, commitment, pooling/separation, deviations |
| Multiple equilibria or refinement | Existence, selection/refinement, claim dependence on selection |
| Participation, contracts, mechanism design | IR, IC, deviations, implementability, transfers, budget and feasibility |
| Price, quantity, demand, competition | Demand partition, market coverage, boundary consumers, global price/quantity deviations, existence/uniqueness when claimed |
| Dynamic game | Continuation values, history dependence, sequential rationality, terminal/transversality conditions |
| Search, learning, stopping | Belief evolution, stopping rule, option value, history dependence, boundary behavior |
| Matching, capacity, congestion | Feasible matching, rationing, capacity, congestion consistency |
| Fixed point, continuum, functional strategy | Strategy space, measurability, continuity/compactness or substitute conditions, correspondence properties, existence |
| Numerical/computational solution | Implemented objective and constraints, domain, convergence/stability, global versus local solution, reproducibility, sensitivity |
| Welfare/accounting | Stakeholder components, transfers versus real surplus, externalities, baseline comparability |

Checks not activated by the structure are `NOT APPLICABLE`.

## Mechanism validation

A correct equilibrium does not by itself establish why the result occurs. For a load-bearing mechanism claim, map:

`primitive/assumption -> belief or strategic response -> best response/participation/feedback -> equilibrium object -> result`.

Use the cheapest coherent test that distinguishes the explanation:

- relax or remove a high-leverage assumption;
- shut down or endogenously neutralize the proposed intermediate response in a valid nested benchmark;
- compare a benchmark that removes the named force;
- strip non-load-bearing structure;
- test whether another primitive or constraint directly generates the result.

An exogenous freeze that violates incentives or information can diagnose sensitivity but is not an equilibrium counterfactual. If a result survives a mechanism shutdown, the mechanism may still affect magnitude, welfare, or boundaries, but it is not necessary for existence. Missing a convenient benchmark limits mechanism identification; it does not automatically invalidate the model.

Do not require every result to contain opposing effects or a multi-step feedback loop. Attribute a direct or assumption-driven result accurately.

## Independent critic

After construction or diagnosis, ask in order of downstream consequence:

1. What omitted regime, constraint, deviation, or cross-material mismatch could overturn the claim?
2. Which assumption carries the greatest conclusion load, and does it effectively encode the result?
3. Does the claimed mechanism survive a coherent shutdown, smaller model, or alternative explanation?
4. Which evidence or calculation could reverse the recommendation?
5. What is the cheapest falsification attempt for a global, unique, threshold, or existence claim?

Produce an actual test or competing branch when decision-relevant. Otherwise report that no material challenge was found within the stated scope. Do not rephrase the same analysis in a more skeptical tone.

## Status and stale results

Keep validation status separate from assertion type. A source statement, conjecture, numerical pattern, formal derivation, verified claim, literature precedent, and isolated mechanism have different support.

For cross-session work, record important results with their verified domain, decisive dependencies, unresolved exclusions, and invalidation conditions. Mark them stale and rerun affected checks after any depended-on model object changes.
