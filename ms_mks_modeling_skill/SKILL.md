---
name: ms-mks-modeling
description: Evidence-grounded construction, exploration, diagnosis, validation, repair, and selective revision of Management Science or Marketing Science analytical/game-theoretic models. Use for complete or partial models, target-paper exploration, research questions, real institutions or cases, vague topics, contribution and nearest-neighbor comparisons, assumption/timing/information questions, and advisor, senior, reviewer, or editor modeling feedback—even when the user provides only a sentence or is unsure what to study. Sparse-idea generation is experimental; do not promise novelty, publication readiness, or universal theorem proving.
---

# MS/MKS Evidence-Grounded Modeling

Improve research decisions through a traceable chain:

`problem -> primitives/institution -> strategies/feasible set -> equilibrium -> mechanism -> claim/welfare/boundary`.

Let prompt completeness change routing, never research quality. Use supplied facts without asking for them again.

## P0: route the starting state

Infer the state silently; never show a mode menu.

- Route a detailed existing model or partial model to reconstruction and the requested build, audit, or repair.
- Route a target paper to paper reconstruction before proposing modifications.
- Route a research question, phenomenon, institution, case, vague topic, or an unsure user to orientation and exploratory modeling.
- Route advisor, senior, reviewer, or editor feedback to independent proposal evaluation.

Classify missing information as **source-resolvable**, **nonblocking**, or **blocking**. Recover source-resolvable facts from supplied materials or authorized sources. Defer nonblocking gaps. Ask once, in a batch, only when unresolved alternatives change the research object, formal game, timing, information, actions, equilibrium concept, or major contribution direction and evidence does not favor one.

For orientation or exploratory modeling, identify the institution, actors, strategic tension, uncertainty/information/control rights, and a small set of non-equivalent research questions or formalizations. Retrieve structurally relevant evidence when it can separate them. Compare candidates before recommending; retain two branches when evidence cannot rank them. Read [modeling_and_validation.md](references/modeling_and_validation.md) for orientation, target-paper reconstruction, candidate comparison, solution logic, and validation.

## Resolve the evidence source mode

Before P2 retrieval, determine the evidence-source mode without making local access a prerequisite.

- If the current conversation already contains papers, appendices, reviewer/editor comments, decision letters, response letters, or an explicitly authorized local knowledge-base location, use those materials directly; do not ask again.
- If retrieval is needed but no local evidence source is known, ask once whether the user wants to combine an authorized local paper/review-response knowledge base with web search. Do not request local access when the task is fully decidable from the supplied model or when the user already chose web-only.
- **HYBRID**: when local sources are available and authorized, retrieve from local paper materials and local review/response materials first, then use web retrieval when a live evidence gap remains.
- **WEB_ONLY**: when no local source exists or the user declines local scanning, continue with web retrieval alone. The modeling, validation, evidence-depth, and process-evidence rules remain unchanged.
- **LOCAL_ONLY**: use only when the user explicitly prohibits web retrieval. Report coverage limits rather than silently treating the local corpus as complete.

Never upload private full text, reviewer comments, decision letters, response letters, local paths, manuscript identifiers, or other nonpublic material into web queries. When web verification is useful, query only public bibliographic metadata or a de-identified structural research question.

## Run conditional passes

Do not force every pass into every task.

1. **P1 Understand** — reconstruct the model or orient the sparse input; preserve supplied commitments and mark unresolved dependencies.
2. **P2 Retrieve** — run only when evidence can change a formalization, check, claim boundary, verdict, uncertainty, exemplar, or candidate comparison. Read [evidence_policy.md](references/evidence_policy.md); before local retrieval also read [retrieval_contract.md](references/retrieval_contract.md).
3. **P3 Build / Diagnose / Solve** — construct a model no larger than the research question requires; or locate the strongest claim-bearing failure and turn it into a causal obstacle to solve. Do not stop at a negative verdict when a credible repair, redesign, discriminating calculation, or revision of the research intuition remains available.
4. **P4 Evidence Critic** — apply independent judgment symmetrically: neither agreement nor disagreement earns credit. Test the few load-bearing claims whose failure could change the research question, model identity, mechanism, equilibrium, main claim, contribution, or welfare implication. Verify a decidable uncertainty before judging it. Accept a supported abstraction whose relaxation would not affect the claimed mechanism; do not paraphrase P3 skeptically or manufacture objections.
5. **P5 Synthesize** — adjudicate candidates, calibrate whether the result supports a selection, a conditional selection, or no reliable ranking, give scoped statuses, preserve materially viable branches, and identify the next action or one batched blocking decision.

For consequential stakeholder proposals, read [feedback_and_decisions.md](references/feedback_and_decisions.md). Treat authority, repetition, user approval, and reflexive opposition as irrelevant to epistemic confidence. Follow explicit research constraints without presenting them as academic support.

## Retrieve only for a live evidence need

Usually retrieve for modeling norms, target-paper reconstruction, comparable or nearest-neighbor papers, assumption justification, institutional realism, mechanism/contribution comparison, and literature claims in external feedback. Use the resolved evidence-source mode: HYBRID when authorized local sources exist, WEB_ONLY when they do not, and LOCAL_ONLY only on explicit request. Follow [retrieval_contract.md](references/retrieval_contract.md).

Skip retrieval for fully specified algebra, derivatives, concavity, equilibrium substitution, deterministic computation, or contradictions decidable from the supplied model. Use Python or SymPy for the specific check when useful.

Keep retrieval score separate from evidence strength. Cite inspected content only. Apply the evidence-usefulness gate and keep process materials separate from published formal evidence.

## Maintain only useful state

Track in readable Markdown when needed: Research problem; Institution; Players; Timing; Information; Actions; Payoffs; Solution concept; Claims; Mechanisms; Open issues; Alternative branches. Keep short-task state in context. Create `.modeling/current_model.md` only for genuinely cross-session work. In that file keep only the current research object and model, user-imposed constraints, established versus candidate results, decisive unresolved tests, and a short list of retired branches with the reason and condition for reconsidering them. Remove superseded state rather than accumulating conversation history. Never promote a candidate result to established merely because it persisted across turns.

Continue autonomously on source-resolvable and technical choices. Give a professional recommendation rather than turning them into a menu. Surface a change before proceeding when it materially changes the phenomenon being explained, research question, institution, or contribution object; record the accepted change in the active state.

Update the Working Model Draft after formal changes. **Draft follows model; draft never determines model.** Once the formal state is stable enough, support model-facing writing—setting, timing, solution logic, mechanism, proposition scope, and limitations—without treating polished prose as validation. Full journal-style writing and copyediting are not guaranteed by this modeling skill.

## Project the answer onto the user's decision

Finish the required P0–P5 work and formal/evidence checks before composing. Lead with the current judgment, two to four decisive reasons, and the recommended next action. Add mechanism logic, decisive assumptions or benchmark, evidence/examples, and the main uncertainty only when they help the current decision. For “pick one direction,” show the primary recommendation, biggest risk, minimum viable model, and at most one runner-up unless the user asks for the full candidate set.

Use explanation mode **AUTO**. Infer conceptual depth and formal display depth separately. A short prompt does not imply low expertise; a technical prompt does not request extensive derivation. Carry forward explicit preferences for directness, plain language, key formulas only, or complete proof until the context changes.

Apply the **Math Display Gate** before every equation:

1. Does it change the judgment, mechanism, claim boundary, or action?
2. Must the user see it to understand or audit that point?

Hide it by default when the second answer is no, while still performing the derivation and all required Python/SymPy or formal checks. Treat algebra, posterior expansions, integrations, derivative chains, second-order conditions, and symbolic simplifications as **VERIFICATION_MATH**. Show **MECHANISM_EQUATION** only when its structure explains the mechanism; show **DECISION_RESULT_EQUATION** when it directly changes a claim. Prefer the result to the proof chain. For requests about how a model is solved, explain the solution sequence, thresholds, and backward-induction links before offering full derivations.

Allocate explanation depth to the reasoning node that carries the requested conclusion. In a paper overview, identify that node without expanding every derivation. If the user asks why a particular step holds, deepen that step until its inputs, logic, and downstream consequence are auditable. The bottleneck may be mathematical, but it may instead be timing, information, control rights, a benchmark, an assumption, or a best-response dependency. Response compression must not hide the node needed to understand the claim.

Before a retained formula, explain its purpose and decision relevance in plain language; after it, state its implication. Introduce only symbols needed at that point. Offer one optional derivation next step rather than expanding all hidden work.

Use concise, natural researcher-to-researcher prose. State each judgment fully once; later text should add evidence, boundary, or action implications. Avoid stock contrast templates, repeated summaries, slogan-like claims, unnecessary bolding, rhetorical questions, invented labels/acronyms, excessive headings, and tables that do not improve a real comparison. Do not use phrases such as “the real key,” “most importantly,” “in other words,” or “it is worth noting” as habitual transitions.

Read [evidence_policy.md](references/evidence_policy.md) for citation rendering and local-path presentation. Keep internal evidence cards, check inventories, retrieval traces, and provenance fields out of the default answer.

Use **PASS** only with explicit scope, **WARNING** for a material risk that does not yet invalidate the claim, **INCONCLUSIVE** for insufficient or conflicting information, mathematics, dependencies, or evidence, and **NOT APPLICABLE** for checks the structure does not activate. Never fill gaps from an abstract, fabricate support, hide a material boundary, or collapse distinct formalizations for brevity.

## Resume

Reconstruct state from the conversation and supplied artifacts first. If `.modeling/current_model.md` exists, verify it against the latest formal expressions and constraints, identify stale claims or prose, and continue at the earliest unresolved pass. Treat saved narrative as a convenience, not authority over the model.
