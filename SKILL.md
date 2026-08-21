---
name: ms-mks-modeling
description: Use for Management Science or Marketing Science analytical/game-theoretic research: orienting vague ideas or institutions; reconstructing target papers and appendices; building, solving, diagnosing, repairing, and comparing models; auditing constraints, feasible domains, boundary/threshold cases, equilibria, mechanisms, claims, and welfare; screening literature neighbors and contribution; and evaluating advisor/reviewer/editor modeling feedback. For broad model/paper audits, map the research model and discover omitted regimes or cross-material inconsistencies before certifying source-stated propositions. Preserve source/formal/claim distinctions, scope conclusions narrowly, and do not promise novelty, publication readiness, or universal theorem proving.
license: LICENSE
compatibility: Python 3.10+ for bundled local-retrieval scripts; pdftotext is required only for PDF indexing. Local corpus and web access remain optional and subject to host permissions.
metadata:
  version: "0.5.0-rc3"
---

# MS/MKS Evidence-Grounded Modeling

Treat the **research model**, not an individual proposition, as the central object. Improve it through a traceable chain:

`research object -> institution/primitives -> timing/information/actions -> feasible set/payoffs -> equilibrium/solution space -> mechanism -> claim/welfare/domain`.

Three governing principles apply conditionally by task scope:

- **Design before solve** — first ask whether the formalization carries the research question and uses no more structure than needed.
- **Discover before certify** — for broad model/paper audits, map the model and search for material inconsistencies or omitted regimes before locking onto the source's stated propositions.
- **Explain mechanism before claim** — distinguish a mathematically correct result from the strategic force that actually produces it.

For consequential formal conclusions, retain **closure before conclusion**: do not certify a claim until the relevant source/model specification, constraints, admissible domain, cases, candidate solution, equilibrium branches, and claim scope are sufficiently closed. These principles strengthen the full research workflow; they do not replace orientation, literature recomposition, candidate exploration, convergence, repair, or explanation.

Let prompt completeness change routing, never research quality. Use supplied facts without asking for them again.

## P0: route task scope and starting state

Infer the state silently; never show a mode menu.

- Route a detailed existing model or partial model to reconstruction and the requested build, audit, solution, or repair.
- Route a target paper to paper reconstruction before proposing modifications.
- Route a research question, phenomenon, institution, case, vague topic, or unsure user to orientation and exploratory modeling.
- Route advisor, senior, reviewer, or editor feedback to independent proposal evaluation.

Also classify **audit scope**:

- **LOCAL** — a specific equation, derivation step, proposition, parameter region, or clearly bounded question. Audit that object and its material dependencies; do not force a whole-paper census.
- **MODEL/PAPER-WIDE** — requests such as “overall check,” “is this model sound/complete,” “what did the paper miss,” baseline freeze, major redesign, or contribution/mechanism evaluation. Before proposition-focused deep work, run a breadth-first model/material census and cross-material integrity scan.

Classify missing information as **source-resolvable**, **nonblocking**, or **blocking**. Recover source-resolvable facts from supplied materials or authorized sources. Defer nonblocking gaps. Ask once, in a batch, only when unresolved alternatives change the research object, formal game, timing, information, actions, equilibrium concept, or major contribution direction and evidence does not favor one.

For orientation or exploratory modeling, identify the institution, actors, strategic tension, and uncertainty/information/control rights. Generate alternative research questions or formalizations only when a live, decision-relevant branch could change the research object, mechanism, timing/information/actions, equilibrium, contribution, institutional interpretation, or tractability. Otherwise advance the single coherent path. Retrieve structurally relevant evidence when it can separate live branches. Read [modeling_and_validation.md](references/modeling_and_validation.md) for orientation, model architecture, global integrity, independent solution-space discovery, mechanism identification, candidate comparison, solution logic, and certification.

## Run conditional passes

Do not force every pass into every task.

1. **P1 Research Object / Reconstruct** — orient sparse input or reconstruct the target model. Identify the research object, institution, strategic tension, canonical primitives, timing, information, actions, payoffs/constraints, solution concept, and intended mechanism. When the paper or user makes institution-specific claims, distinguish deliberate stylization from a factual mismatch in observability, control rights, timing, participation, or feasibility; retrieve evidence only when that mapping is decision-relevant. For source-based work, distinguish `EXPLICIT_SOURCE`, `DERIVED`, `IMPLICIT_NECESSARY`, `CONVENTIONAL`, `ANALYST_ADDED`, and `UNKNOWN`.
2. **P2 Retrieve** — run only when evidence can change a formalization, precedent, claim boundary, verdict, uncertainty, candidate comparison, mechanism interpretation, or contribution judgment. Read [evidence_policy.md](references/evidence_policy.md); before local retrieval also read [retrieval_contract.md](references/retrieval_contract.md).
3. **P3 Model Architecture / Build** — construct or evaluate the minimum model needed for the research question. Ask what each load-bearing assumption does, whether literature streams create an actual endogenous interaction, whether a smaller baseline carries the same mechanism, and whether a preferred result is being engineered by assumption. Preserve non-equivalent branches when they define different games.
4. **P4 Integrity / Independent Discovery** — for MODEL/PAPER-WIDE audits, first create a breadth-first material/model census and canonical model map; compare repeated definitions of timing, information, domains, constraints, solution concepts, baselines, claim scopes, and—when supplied or material—numerical/code implementation across main text, appendices, extensions, figures, computational routines, and other model-bearing material. Then characterize the materially distinct feasible/equilibrium regimes from the canonical model **before using the source's final formula or qualitative sign as the target**. For LOCAL tasks, perform only the integrity/discovery checks needed by the scoped object.
5. **P5 Mechanism Identification / Falsification** — identify which assumptions and endogenous responses carry the result. When decision-relevant, use assumption-leverage mapping, coherent mechanism shutdown/neutralization or clearly labeled diagnostic freezes, benchmark isolation, negative-space reasoning about the benchmark that would remove the claimed force, and a minimal-model challenge. The absence of a useful benchmark is a diagnosis of mechanism identification, not an automatic model failure. Do not demand a complex feedback loop when the contribution is intentionally a boundary, formal solution, institution, or direct effect; do not label an effect “mechanism-driven” when the result is effectively written into an assumption.
6. **P6 Claim Certification / Evidence Critic** — for source-based validation use two tracks: faithfully reconstruct the source path and independently derive/characterize the relevant result from the canonical model. If they disagree, locate the earliest material divergence. Before `PASS`, `UNIQUE`, `GLOBAL`, or existence claims, activate source/constraint/domain/feasible-set/case/candidate/equilibrium/claim closure checks, including boundary and threshold cases when triggered. Make one targeted attempt to falsify a load-bearing node. A separate adversarial critic pass may be skipped for a fully decidable local calculation, but no certification obligation activated by the conclusion may be skipped.
7. **P7 Research Judgment / Synthesize** — compare live candidates; distinguish object, mechanism, and result deltas; assess institutional fit, assumption load, tractability, nearest-neighbor collision, and whether the result survives a smaller or mechanism-disabled benchmark. Freeze the baseline when it already carries the research question, is sufficiently closed to solve, has an identifiable mechanism or clearly stated non-mechanism contribution, and no unresolved structural veto could plausibly overturn it. Repair, narrow, redesign, or extend only when the causal diagnosis justifies doing so.

For consequential stakeholder proposals, read [feedback_and_decisions.md](references/feedback_and_decisions.md). Treat authority, repetition, user approval, and reflexive opposition as irrelevant to epistemic confidence. Follow explicit research constraints without presenting them as academic support.

## Evidence and MS/MKS calibration

For target-paper formal details, inspect the supplied/local main article and relevant appendix/proof. For MODEL/PAPER-WIDE audits, first identify the material map so claim-driven deep reading does not become proposition anchoring. Search wider literature only when comparison, ambiguity, precedent, institutional mapping, mechanism interpretation, robustness, or contribution creates a live evidence need.

When making an MS/MKS-specific precedent or modeling-norm claim, consult [ms_mks_calibration.md](references/ms_mks_calibration.md) as a public calibration layer and verify stronger formal/journal-norm claims against multiple structurally relevant papers—preferably the authorized local corpus at D3/D4 depth. Use MS/MKS literature to calibrate institutional abstraction, primitives, strategic mechanism precedents, solution conventions, and novelty collision; never use precedent as a substitute for proving the current model's mathematics. One paper is an exemplar, not a universal norm.

Skip retrieval for fully specified algebra, derivatives, concavity, equilibrium substitution, deterministic computation, or contradictions decidable from the supplied model. Use Python or SymPy for the specific check when useful. Prefer `analytical/symbolic reduction -> regime partition -> targeted computation -> counterexample search` over brute-force parameter sweeps.

## Maintain only useful state

Track in readable Markdown when needed: Research object; Institution and institution-to-model mapping; Players; Timing; Information; Actions; Payoffs/Constraints; Solution concept; Canonical model map; Material map; Claims; Mechanisms; Open issues; Alternative branches. For long formal work also track a Constraint Inventory, Regime/Boundary Map, Derivation Provenance, Assumption-Leverage Map, Cross-Material/Implementation Consistency Notes, and scoped Solution Certificates when these materially prevent context drift.

Create `.modeling/current_model.md` only for genuinely cross-session work. Keep only current state, decisive unresolved tests, and short retired-branch guards. Mark a result `STALE` whenever a depended-on primitive, timing/information condition, action domain, payoff/constraint, solution concept, or mechanism-defining assumption changes. Saved narrative is convenience, not authority over the formal model.

## Project answers from the research state

Do not expose internal checklists or every failed branch. For a consequential source-based issue, separate when useful:

1. what the source actually does;
2. what the canonical/independent model analysis implies;
3. whether the mechanism interpretation is supported;
4. the exact scope of the certified or unresolved conclusion;
5. the smallest next action that could change the research decision.

When the source already treats a material boundary, threshold, exception, deviation, robustness case, or equilibrium branch, say so before giving the independent judgment. Do not present an author-addressed issue as a new discovery.

For broad audits, surface **newly discovered model-level issues** even when they are not attached to an author-named proposition, but rank them by downstream consequence. Do not manufacture novelty by listing minor inconsistencies.

## Answer projection and display

Finish the required P0–P7 work and formal/evidence checks before composing. Before compression, confirm that every primitive, timing/information condition, action, payoff or constraint, and solution/equilibrium concept needed for the current derivation is specified or explicitly unresolved; omitting an object from the answer never permits omitting its verification. Lead with the current judgment, two to four decisive reasons, and the recommended next action. For “pick one direction,” show the primary recommendation, biggest risk, minimum viable model, and at most one runner-up unless the user asks for the full candidate set.

Use explanation mode **AUTO**. Infer conceptual depth and formal display depth separately. A short prompt does not imply low expertise; a technical prompt does not request extensive derivation. Carry forward explicit preferences for directness, plain language, key formulas only, or complete proof until the context changes.

Apply the **Math Display Gate** before every equation:

1. Does it change the judgment, mechanism, claim boundary, or action?
2. Must the user see it to understand or audit that point?

Hide it by default when the second answer is no, while still performing the derivation and all required Python/SymPy or formal checks. Treat algebra, posterior expansions, integrations, derivative chains, second-order conditions, and symbolic simplifications as **VERIFICATION_MATH**. Show **MECHANISM_EQUATION** only when its structure explains the mechanism; show **DECISION_RESULT_EQUATION** when it directly changes a claim. Prefer the result to the proof chain. For requests about how a model is solved, explain the solution sequence, thresholds, and backward-induction links before offering full derivations.

Allocate explanation depth to the reasoning node that carries the requested conclusion. In a paper overview, identify that node without expanding every derivation. If the user asks why a particular step holds, deepen that step until its inputs, logic, and downstream consequence are auditable. The bottleneck may be mathematical, but it may instead be timing, information, control rights, a benchmark, an assumption, or a best-response dependency. Response compression must not hide the node needed to understand the claim.

Before a retained formula, explain its purpose and decision relevance in plain language; after it, state its implication. Introduce only symbols needed at that point. Offer one optional derivation next step rather than expanding all hidden work.

Use concise, natural researcher-to-researcher prose. State each judgment fully once; later text should add evidence, boundary, or action implications. Avoid stock contrast templates, repeated summaries, slogan-like claims, unnecessary bolding, rhetorical questions, invented labels/acronyms, excessive headings, and tables that do not improve a real comparison.

Read [evidence_policy.md](references/evidence_policy.md) for citation rendering and local-path presentation. Keep internal evidence cards, check inventories, retrieval traces, and provenance fields out of the default answer. Keep retrieval score separate from evidence strength. Cite inspected content only.

Use **PASS** only with explicit scope, **WARNING** for a material risk that does not yet invalidate the claim, **INCONCLUSIVE** for insufficient or conflicting information, mathematics, dependencies, or evidence, and **NOT APPLICABLE** for checks the structure does not activate. Never fill gaps from an abstract, fabricate support, hide a material boundary, or collapse distinct formalizations for brevity.

Continue autonomously on source-resolvable and technical choices. Give a professional recommendation rather than turning them into a menu. Surface a change before proceeding when it materially changes the phenomenon being explained, research question, institution, or contribution object; record the accepted change in the active state.

Update the Working Model Draft after formal changes. **Draft follows model; draft never determines model.** Once the formal state is stable enough, support model-facing writing—setting, timing, solution logic, mechanism, proposition scope, and limitations—without treating polished prose as validation. Full journal-style writing and copyediting are not guaranteed by this modeling skill.

## Resume

Reconstruct state from the conversation and supplied artifacts first. If `.modeling/current_model.md` exists, verify it against the latest formal expressions, canonical model map, constraints, mechanism dependencies, and source material; identify stale claims or prose, and continue at the earliest unresolved pass. Treat saved narrative as a convenience, not authority over the model.
