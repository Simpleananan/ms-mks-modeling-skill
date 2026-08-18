# Modeling and validation

Load this reference for substantive construction, diagnosis, repair, or revision. Do not expose it as a checklist dump.

## Quality criterion

The primary criterion is **Structural Traceability**:

`real/theoretical problem -> primitives/institution -> strategic response or feasible set -> equilibrium -> prediction/claim/welfare/boundary`.

A model is good when every claim-bearing link can be identified, justified, and stress-tested. A model is poor when the research question is not carried by the institution, information, actions, payoffs, or solution concept; when the result is inserted through an assumption; or when extra structure prevents mechanism identification.

Do not reward a result merely for being counterintuitive. Substantive results can arise from opposing mechanisms, trade-offs, feedback loops, regime changes, or equilibrium selection. Use no more complexity than the research question requires, but retain structure needed to represent the institution, strategic interaction, equilibrium, or solution method. Simplicity is not evidence of quality.

Allocate scrutiny by **conclusion load**. Lead with a concern only when resolving it could materially change the research object, institutional interpretation, model identity, strategic response, equilibrium, main proposition, contribution, or welfare implication. A normalization, reduced form, functional form, or auxiliary assumption is not an objection merely because reality admits more detail. If its relaxation leaves the claimed strategic link intact, state the boundary when useful and move on. When a direct derivation or source inspection can settle the concern, verify it before assigning severity.

Evaluate model quality relative to the paper's claim:

- **Research and construct fit:** a construct-specific claim needs formal structure that makes the construct consequential through information, technology, feasible actions, control rights, dynamics, payoffs, or strategic feedback. Renaming a generic parameter is a diagnostic warning, not a veto. A reduced form is appropriate when the claim is deliberately general and the mapping to the application is credible.
- **Mechanism and informativeness:** identify the endogenous dependency that produces the result. It need not contain opposing effects or a surprising sign. A mechanically direct effect can still be useful when the contribution lies in a new institution, equilibrium object, formal solution, boundary, or welfare implication; otherwise, do not overstate it as a new strategic mechanism.
- **Solution quality:** do not require closed form. Analytical characterizations, implicit solutions, thresholds, fixed points, numerical equilibria, and computational results are acceptable when their domain, existence or convergence, stability, economic interpretation, and claim scope are adequately established. A few favorable parameter examples cannot support a broad proposition without sensitivity analysis or a more general explanation.

Do not combine these dimensions into a fixed score. Their importance follows the research question and intended contribution.

## Working model representation

Use readable Markdown, not a model database. Track only fields needed by the task:

- Research problem and claim domain
- Institution and exogenous primitives
- Players
- Timing and commitment points
- Information, beliefs, and observability/verifiability
- Feasible actions and strategies
- Payoffs, constraints, and accounting identities
- Solution/equilibrium concept and selection rule
- Claims and welfare objects
- Mechanism chain
- Open issues and unresolved formal debt
- Material alternative branches

For each major assumption, record its **role**, **conclusion load**, and **dependency**. Ask whether it enables tractability, defines the institution, selects an equilibrium, or directly supplies the claimed effect.

## Orientation from incomplete prompts

Do not make the user formalize a model before helping. When the input is a question, phenomenon, institution, case, broad topic, target paper, or a statement of uncertainty:

1. Recover facts already present in the prompt and supplied sources; do not ask for them again.
2. Identify the institutional feature, strategic actors, strategic tension, and the allocation of information, commitment, and control rights.
3. State a provisional research object and the endogenous decisions that could carry it.
4. Form a small set of non-equivalent research questions and minimum formalizations. Keep them provisional.
5. Retrieve structurally close work when evidence could eliminate, sharpen, or rank a branch.
6. Compare the branches before asking the user. Ask one batched question only if the surviving alternatives change the research object or formal game and evidence cannot select one.

When the user is unsure what to study, report what the setting could support, why the viable questions differ, which direction currently has the strongest case, and the largest unresolved uncertainty. Preserve two branches when a reliable ranking is unavailable. Sparse-idea generation remains experimental.

## Target-paper reconstruction

Before extending a target paper, reconstruct its research question, institution, players, timing, information, actions, payoffs, solution concept, main mechanism, load-bearing assumptions, and claim boundary. Record the function of a formal benchmark when one exists; otherwise identify the comparison, decomposition, or proof dependency that isolates the result. Inspect the main text and relevant appendix. The abstract cannot support formal details.

Evaluate a proposed change through its causal path: primitive change; strategic-response change; equilibrium consequence; prediction, welfare, or boundary consequence; new endogenous feedback. Adding a variable, actor, heterogeneity, a continuous version of a binary choice, a new industry label, or extra realism does not establish a contribution without that path.

When asked why or how the authors designed the model, distinguish two objects:

- **Reconstructed design logic**: infer the function of primitives, timing, assumptions, benchmarks, and their structure-to-result links from the final paper.
- **Historical development process**: describe chronology only when working-paper versions, reviewer/editor materials, response letters, revision records, or explicit author statements support it.

If chronology evidence is absent, state once that the explanation reconstructs design logic from the final paper and does not claim the authors' actual sequence of thought.

## Build or complete

1. State a provisional research problem and claim domain.
2. Reconstruct the institution before choosing convenient equations.
3. Specify timing, information, and actions together; verify every strategy is feasible at its information set.
4. Define payoffs and constraints, including outside options and accounting closure.
5. Select the weakest solution concept sufficient for the research question.
6. Derive the mechanism chain and distinguish necessary structure from convenience.
7. Preserve non-equivalent formalizations when they imply different timing, information, feasible deviations, or equilibria.
8. Mark sparse-idea constructions as candidates, not validated models.

## Literature streams and recomposition

Split retrieval into mechanism streams when a question draws on distinct formal traditions, such as search, information design, and price competition. Use each stream to recover canonical primitives, timing, information, actions, and strategic responses. Recompose only after checking the model-level connection.

Allow two streams into the same baseline only when at least one of these links is material:

- they affect the same endogenous decision;
- an action from one changes payoffs in the other;
- they share a state, signal, information constraint, or control variable;
- one changes the other's best response;
- they create an equilibrium feedback absent from either stream alone;
- removing one changes the research question.

Topical overlap alone does not justify combination. Put a weakly connected stream in an extension, a separate branch, or drop it. Prefer the baseline that identifies one mechanism cleanly.

## Candidate generation and evaluation

Generate several non-equivalent candidates before recommending one. Do not recommend the first plausible idea. Compare only dimensions that can affect the research decision:

- research-question, primitive, mechanism, and strategic-response deltas;
- fit with the institution;
- nearest-neighbor collision and the evidence available to assess it;
- assumption load and risk that assumptions encode the result;
- mechanism identifiability and tractability;
- whether the research object changes;
- whether a smaller model answers the same question.

Also identify the intended contribution object. A defensible delta may lie in a mechanism, institution, formal solution or method, explanation of a phenomenon, prediction, welfare result, or boundary. Do not require mechanism novelty when another contribution object is the stated research objective.

Generate candidates around a discriminating question, such as whether two information channels are substitutes or complements. Do not select assumptions to manufacture a reversal, non-monotonicity, welfare conflict, or surprising sign. Mark a candidate **high risk** when its value depends on obtaining a preferred sign.

When candidates are responses to a failed result or model obstacle, generate them from the causal diagnosis rather than from adjacent topics. Decompose the result into the strategic forces that determine it; identify which force is missing, misrepresented, or genuinely contrary to the original intuition; and vary only structures capable of changing that force. Include the possibility that the model is informative and the original intuition should be revised.

Seek an early decisive test when one exists: a structural veto, limiting case, deviation, sign decomposition, feasibility condition, or nearest-neighbor collision that can eliminate a branch before full solution. State what outcome would reverse the current recommendation. Do not force a binary test when several independent uncertainties remain.

When asked for one direction, complete the comparison internally and choose among three calibrated outputs:

- **Select** when one candidate has a concrete structural advantage under the stated research objective and no unresolved evidence gap could plausibly reverse it.
- **Conditional select** when the ranking changes with the research objective, institutional fidelity, contribution object, or tractability constraint. State the condition that would reverse the recommendation.
- **INCONCLUSIVE** when missing nearest-neighbor evidence, unresolved formal feasibility, or an unspecified objective could plausibly change the winner.

For a selection, return one recommendation with its minimum viable model and largest risk. Include one runner-up only when it exposes a consequential trade-off. Do not convert a narrative preference or a paper's precedent into dominance.

## Activate checks from structure

Run only checks triggered by the actual model and claim.

| Trigger | Checks to activate |
|---|---|
| Any substantive claim | Claim-domain alignment; primitive-to-claim trace; equilibrium and boundary completeness |
| Private information or inference | Information sets; strategy feasibility; posterior/Bayes consistency; off-path beliefs when relevant |
| Signaling, disclosure, communication | Sender/receiver incentives; credibility; observability; verifiability; commitment; pooling/separation and deviations |
| Multiple equilibria or refinement | Existence; selection/refinement; whether the claim depends on selection |
| Participation, contracting, mechanism design | Participation/IR; IC and deviations; implementability; transfers; budget or feasibility constraints |
| Demand, price, quantity, competition | Demand partition; market coverage; boundary consumers; price/quantity deviations; existence and uniqueness |
| Dynamic game | Continuation values; history dependence; sequential rationality; terminal and transversality conditions |
| Search or stopping | Stopping rule; option value; beliefs over search histories; boundary behavior |
| Matching, capacity, congestion | Feasible matching; rationing; capacity and congestion consistency |
| Fixed-point, continuum, or functional-strategy equilibrium | Strategy-space/domain definition; measurability; compactness/continuity or the stated substitute; correspondence properties; fixed-point existence; uniqueness only when claimed |
| Computation or approximation | Domain; numerical stability; global versus local optimum; reproducibility; symbolic/numeric cross-check |
| Welfare or platform accounting | Consumer/producer/platform components; transfers versus real surplus; omitted externalities; baseline comparability |

Use these statuses:

- **PASS (scope)**: the named property holds on a stated parameter/domain/equilibrium scope.
- **FAIL**: a concrete counterexample, violated condition, infeasible action, missing equilibrium case, or accounting inconsistency is shown.
- **WARNING**: a material dependency or boundary risk remains, but the available check does not yet invalidate the scoped claim.
- **INCONCLUSIVE**: required primitives, dependencies, formal derivation, or evidence are unavailable or conflicting.
- **NOT APPLICABLE**: the model structure does not activate the check.

Never infer global validity from a local derivative, one numerical case, or one equilibrium branch.

## Evidence Critic pass

After a candidate construction or diagnosis exists, evaluate it independently and in order of downstream consequence:

1. What is the strongest structural failure that could overturn the claim?
2. Which assumption carries the most conclusion load, and does it encode the result?
3. Which feasible alternative, deviation, continuation, or equilibrium branch was omitted?
4. What counterexample or contrastive evidence could materially challenge generalization? Skip this search when the claim is already scoped and the contrast cannot change the decision.
5. Which missing evidence or calculation would change the recommendation?

Do not restate the candidate in skeptical language. Produce an actual test or competing branch when one is decision-relevant; otherwise state “no material challenge found within scope.” Keep minor exposition or realism caveats subordinate to a claim-bearing structural issue.

## Explain solution logic

For “how is this model solved?” explain both order and dependency. Name the object produced at a later stage—such as a continuation value, posterior, best response, feasible correspondence, or algorithmic estimate—and show how it enters an earlier objective, constraint, belief, or equilibrium condition. Identify the step on which the main result depends. Mention thresholds or regions only when they perform this role. Keep full first- and second-order conditions, posterior expansions, integrations, derivative chains, and threshold algebra hidden unless the user requests a proof, is learning the derivation, or cannot audit the conclusion without them. Perform every activated formal check even when its algebra is not displayed.

## Repair and selective revision

After diagnosing a consequential obstacle, continue the research loop:

1. Trace the failed result to the primitive, strategic response, feasibility condition, or equilibrium dependency that produces it and identify the affected claim.
2. Separate a false or incomplete research intuition from a model that omits or misrepresents the intended institutional force.
3. Construct a small set of causally distinct responses: repair the current link, redesign the relevant game element, narrow the claim, or accept the result and revise the theory. Prefer the smallest repair only when it preserves the research object and intended mechanism; redesign when the current primitives, timing, information, actions, or equilibrium concept define the wrong game.
4. Retrieve only when a formal precedent, alternative primitive, institutional fact, or nearest neighbor could change the available responses.
5. Test the cheapest decisive implication of each viable response before undertaking a full solution.
6. Compare what each response solves, its new assumption debt, whether the research object changes, and which downstream derivations must be redone.
7. Implement the selected response and re-solve or re-check every affected dependency; do not patch prose alone.

Use an extension only to test mechanism necessity, a boundary, endogenization, an alternative explanation, or robustness. Do not add realism indiscriminately, preserve a preferred sign by assumption, or keep repairing a formalization after its research object has drifted. If no credible response survives, report that result as research information rather than manufacturing another candidate.

## Shadow draft

Create or update a Working Model Draft when a multi-part model needs a stable shared representation. Update it after changes to primitives, timing, information, actions, payoffs, equilibrium, mechanism, or claim boundary. Do not generate it for a one-line algebra check or when the user supplied a complete, internally consistent representation and no revision is needed.

**Draft follows model; draft never determines model.** If a formal result changes, revise the draft and narrative. Never alter the model to preserve an attractive story.

For cross-session work, keep the Working Model Draft synchronized with the active research object and distinguish proved, numerically observed, conjectured, and literature-supported statements. Retain a rejected branch only as a one-line guard against repetition, together with a condition that would justify reopening it.
