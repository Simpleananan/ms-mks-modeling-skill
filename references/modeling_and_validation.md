# Modeling and validation

Load this reference for substantive construction, diagnosis, repair, or revision. Do not expose it as a checklist dump.

## Quality criterion

The primary criterion is **Structural Traceability**:

`real/theoretical problem -> research object -> primitives/institution -> timing/information/actions -> strategic response or feasible set -> equilibrium/solution space -> mechanism -> prediction/claim/welfare/boundary`.

A model is good when every claim-bearing link can be identified, justified, and stress-tested, and when the model architecture is no larger than needed to carry the research object. A model is poor when the research question is not carried by the institution, information, actions, payoffs, or solution concept; when the result is inserted through an assumption; or when extra structure prevents mechanism identification.

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
- For source-based audits when material: derivation provenance and source dependencies
- For long formal work when material: constraint inventory, regime/boundary map, and scoped solution certificates

For each major assumption, record its **role**, **conclusion load**, and **dependency**. Ask whether it enables tractability, defines the institution, selects an equilibrium, or directly supplies the claimed effect.


## Research-object fit and model architecture

Before treating solution or proposition verification as the center of the task, ask whether the model is the right formal object for the research question.

For a new or revised baseline, identify:

- the **research object**: the strategic/informational/institutional phenomenon the model is meant to explain;
- the **endogenous carrier**: which decisions, beliefs, constraints, or equilibrium feedback make that object consequential;
- the **architecture**: which primitives, timing/information choices, actions, and solution concept are necessary to represent that carrier;
- the **claim object**: whether the intended contribution is primarily a mechanism, institution, formal solution, boundary, prediction, welfare result, or explanation of a phenomenon.
- the **institution-to-model map** when the paper makes institution-specific claims: which real or documented features justify observability, control rights, timing, participation, outside options, constraints, and market structure. Distinguish purposeful abstraction from a mismatch that changes the research object.

Do not treat mathematical validity as sufficient model quality. A model can be internally correct but research-design weak when the claimed construct is only renamed rather than made consequential, the result is mechanically encoded in an assumption, the architecture contains unnecessary structure that hides the mechanism, or the extension changes the research object while being described as mere robustness.

Use three research-design probes when decision-relevant:

1. **Minimal-model challenge:** is there a strictly smaller formalization that preserves the research object, strategic mechanism, and main result? If yes, prefer the smaller baseline unless the extra structure is needed for institutional fidelity or a distinct contribution object.
2. **Assumption-to-result distance:** does a load-bearing result emerge through endogenous strategic responses, or is it almost directly imposed by the sign/ranking assumed in a primitive? A direct effect is not invalid, but do not overstate it as a new strategic mechanism.
3. **Result-desirability firewall:** never choose primitives because they manufacture a preferred reversal, non-monotonicity, welfare conflict, or surprising sign. Model selection should follow institutional fit, endogenous logic, assumption burden, mechanism clarity, contribution object, and tractability.

These are research-design diagnostics, not universal journal rules. Calibrate claims about MS/MKS practice through the evidence protocol rather than treating this Skill's design heuristic as field law.

## Breadth-first model census and canonicalization

For a **MODEL/PAPER-WIDE** audit, do not begin by treating the paper's propositions as the complete search space. First perform a low-cost breadth-first census of model-bearing material. The goal is not to solve every appendix; it is to know what formal objects exist and where they change.

Build a compact **Material Map** covering, when present: baseline model/setup; formal definitions; propositions/lemmas; proof appendices; technical appendices; extensions/robustness; welfare section; numerical/computational section or code; and any model-bearing tables/figures. Then construct one **Canonical Model Map** of the current model objects:

`players -> timing/commitment -> information/beliefs -> actions/domains -> payoffs/constraints -> solution concept -> regime/equilibrium objects -> claims/interpretations`.

Use this map for **cross-material consistency**. When the same canonical object appears in multiple locations, compare it rather than assuming identity. Check especially:

- timing and observability across model setup and proofs;
- information sets and what strategies are allowed to condition on;
- action/parameter domains and boundary conventions;
- constraint sets, outside options, accounting identities, and participation conditions;
- solution/equilibrium concept and selection/refinement;
- benchmark definitions and welfare/accounting baselines;
- notation that is reused with changed meaning;
- proposition scope versus abstract, introduction, discussion, managerial implications, figures, or numerical experiments;
- when code, algorithms, or numerical routines are supplied or load-bearing, objective functions, constraints, parameter domains, initialization/selection rules, and reported outputs versus the canonical model. Treat implementation drift as consequential only when it can change the computed object or claim.

A cross-material inconsistency is consequential only if it can change feasibility, the solution/equilibrium set, the mechanism, or the claim. An **explicitly declared** extension/robustness variant may intentionally change timing, information, domains, or the solution concept; record it as a separate model branch rather than an inconsistency. The concern is a silent change, an unacknowledged transfer of a result across non-equivalent branches, or a narrative that treats the variants as the same game. Do not inflate editorial or notation differences into model failures.

For a **LOCAL** task, skip the global census unless a material dependency points outside the scoped object. This breadth-first step is an anti-anchoring device, not a requirement to read an entire paper for a one-line derivative.

## Orientation from incomplete prompts

Do not make the user formalize a model before helping. When the input is a question, phenomenon, institution, case, broad topic, target paper, or a statement of uncertainty:

1. Recover facts already present in the prompt and supplied sources; do not ask for them again.
2. Identify the institutional feature, strategic actors, strategic tension, and the allocation of information, commitment, and control rights.
3. State a provisional research object and the endogenous decisions that could carry it.
4. Test whether the provisional path is already coherent. Form multiple non-equivalent research questions or minimum formalizations only when a live ambiguity or obstacle creates a decision-relevant branch. Keep any branch provisional.
5. Retrieve structurally close work when evidence could eliminate, sharpen, or rank a live branch.
6. Compare branches before asking the user when branches exist. Ask one batched question only if the surviving alternatives change the research object or formal game and evidence cannot select one.

When the user is unsure what to study, report what the setting could support, why the viable questions differ, which direction currently has the strongest case, and the largest unresolved uncertainty. Preserve two branches when a reliable ranking is unavailable. Sparse-idea generation remains experimental.

## Target-paper reconstruction

Before extending a target paper, reconstruct its research question, institution, players, timing, information, actions, payoffs, solution concept, main mechanism, load-bearing assumptions, and claim boundary. Record the function of a formal benchmark when one exists; otherwise identify the comparison, decomposition, or proof dependency that isolates the result. Inspect the main text and relevant appendix. The abstract cannot support formal details.

Match the reconstruction to the user's objective. For paper understanding, recover and explain the paper's own structure and load-bearing dependency without adding an unsolicited model audit or broader literature search. Activate critique, nearest-neighbor comparison, or redesign only when the user asks for evaluation or extension, or when an unresolved inconsistency prevents faithful reconstruction.

Evaluate a proposed change through its causal path: primitive change; strategic-response change; equilibrium consequence; prediction, welfare, or boundary consequence; new endogenous feedback. Adding a variable, actor, heterogeneity, a continuous version of a binary choice, a new industry label, or extra realism does not establish a contribution without that path.

When asked why or how the authors designed the model, distinguish two objects:

- **Reconstructed design logic**: infer the function of primitives, timing, assumptions, benchmarks, and their structure-to-result links from the final paper.
- **Historical development process**: describe chronology only when working-paper versions, reviewer/editor materials, response letters, revision records, or explicit author statements support it.

If chronology evidence is absent, state once that the explanation reconstructs design logic from the final paper and does not claim the authors' actual sequence of thought.

### Source truth, formal truth, and claim truth

For validation of an existing paper/model, separate three questions:

1. **Source truth:** what the source actually states, assumes, derives, and qualifies.
2. **Formal truth:** what follows mathematically from the reconstructed primitives, domains, timing, information, payoffs, and constraints.
3. **Claim truth:** the exact parameter/equilibrium/domain scope on which the proposition or interpretation is supported.

Source authority establishes what was claimed or attempted; it does not establish formal validity. Conversely, an assistant's alternative derivation does not establish that the source is wrong until non-equivalent assumptions, domains, conventions, or solution concepts have been ruled out.

Track load-bearing source/model objects with one provenance label when the distinction matters: `EXPLICIT_SOURCE`, `DERIVED`, `IMPLICIT_NECESSARY`, `CONVENTIONAL`, `ANALYST_ADDED`, or `UNKNOWN`. Never silently convert a conventional or analyst-added condition into an author/user assumption.

For consequential validation, use a **dual-track audit**:

- **Track A — source path:** reconstruct how the author/user moves from primitives and assumptions to the stated result without silently replacing the derivation or equilibrium concept.
- **Track B — independent path:** derive or characterize the materially relevant solution set/regime structure from the reconstructed primitives, timing, information, strategy domains, payoffs, and constraints; the source's final formula, threshold, qualitative sign, or proposition partition is not a premise.

If the tracks disagree, locate the **earliest material divergence** before assigning fault. A mismatch can arise from source error, reconstruction error, a hidden assumption, a domain convention, a different equilibrium/solution concept, or genuinely non-equivalent formulations.

After the breadth-first census when the task is MODEL/PAPER-WIDE, use **claim-driven source closure** for deep verification rather than a generic instruction to read everything: follow a proposition through the proof, cited lemma/definition, threshold construction, and relevant appendix branch until the dependencies needed for the current judgment are resolved or explicitly marked unresolved. For LOCAL tasks, claim-driven closure may be the first deep-reading step.

Apply a **Material Source Acknowledgment Rule** in user-facing answers: when the main text or appendix already treats a material boundary, threshold, exception, deviation, robustness case, or equilibrium branch, state that the source treats it, summarize the treatment at the depth needed for the judgment, then state whether the independent audit accepts it and why. Do not turn an author-addressed issue into a supposed new discovery.

## Build or complete

1. State a provisional research problem and claim domain.
2. Reconstruct the institution before choosing convenient equations.
3. Specify timing, information, and actions together; verify every strategy is feasible at its information set.
4. Define payoffs and constraints, including outside options and accounting closure.
5. Select the weakest solution concept sufficient for the research question.
6. Derive the mechanism chain and distinguish necessary structure from convenience.
7. Preserve non-equivalent formalizations when they imply different timing, information, feasible deviations, or equilibria.
8. Mark sparse-idea constructions as candidates, not validated models.

Before judging contribution or projecting a compressed answer, verify that the model contains every object needed to define feasible strategies and the stated solution or equilibrium concept. A user-facing overview may omit already verified details; the internal construction and validation may not.

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

Generate multiple non-equivalent candidates only when the current path fails or a live design choice could change the research object, strategic mechanism, timing/information/actions, equilibrium, contribution, institutional interpretation, or tractability. If one coherent path already answers the research question and no unresolved condition could plausibly reverse that assessment, proceed with it instead of inventing alternatives. When candidates are live, do not recommend the first plausible idea; compare only dimensions that can affect the research decision:

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

## Research convergence

Recommend freezing the baseline and moving to formal solution or validation when it carries the research question, its formal game is sufficiently closed, its claim-bearing mechanism is identifiable, no unresolved structural veto could plausibly overturn it, and the available nearest-neighbor evidence is adequate for the current decision. Continue exploration only when a live uncertainty has realistic decision value. Do not delay the baseline for optional realism, another extension, or a merely imaginable candidate; record these as later tests when material.


## Independent solution-space discovery

For broad validation, do not make the author's proposition formula the target of the first independent derivation. Starting from the canonical model, ask what materially distinct feasible and equilibrium regimes the model itself permits.

Use a **claim-independent first pass** when feasible. This is a procedural anti-anchoring device, not a claim that the model has forgotten source propositions already read:

1. identify natural regime-generating objects: active constraints, participation switches, indifference conditions, strategy-domain boundaries, sign changes, piecewise objectives/best responses, state/support boundaries, and equilibrium-selection points;
2. derive or characterize the resulting candidate branches/solution correspondence;
3. establish which branches are feasible or nonempty and which are dominated, impossible, or redundant;
4. only then compare that independently generated solution-space map with the source's named propositions, thresholds, or qualitative claims.

The target is not exhaustive enumeration of every mathematical object. Focus on materially distinct regimes capable of changing the research question, mechanism, equilibrium, welfare, or claim scope. Prefer structural decomposition to brute-force parameter grids.

For a narrow LOCAL task, independent discovery can be limited to the branches and constraints capable of overturning that local conclusion.

## Mechanism identification and falsification

A correct equilibrium characterization does not by itself validate the paper's explanation of **why** the result occurs. When mechanism claims are load-bearing, map the causal dependency:

`primitive/assumption -> belief or strategic response -> best response/participation/information feedback -> equilibrium object -> result`.

Then test whether the named mechanism actually carries the result. Multiple mechanisms may coexist, so distinguish **necessity**, **marginal contribution**, and **scope effects** rather than forcing a single cause. Use only the cheapest discriminating interventions needed:

- **Assumption-leverage map:** identify which assumptions each main result depends on and how changing/removing them changes the result.
- **Mechanism shutdown/freeze:** when a coherent nested benchmark exists, remove or endogenously neutralize the proposed intermediate strategic response and re-solve. A purely exogenous freeze can be used as a diagnostic sensitivity check, but do not treat it as an equilibrium counterfactual when it violates the game's information, incentives, or feasibility. If the result persists, the named mechanism is not necessary for the result's existence; it may still affect magnitude, scope, welfare, or thresholds.
- **Benchmark isolation:** turn off the proposed force (e.g., full information, no competition, fixed participation, exogenous decision) when that benchmark is conceptually coherent; compare what disappears.
- **Negative-space benchmark check:** when a paper attributes a result to a named mechanism, ask what coherent benchmark would remove or neutralize that force and whether the paper/model contains an equivalent comparison. Missing that benchmark does not by itself invalidate the model, but it can leave the mechanism insufficiently isolated.
- **Minimal-model challenge:** remove non-load-bearing structure and test whether the result and mechanism survive.
- **Alternative-mechanism check:** ask whether another primitive or constraint directly generates the observed sign/threshold, especially when the named mechanism is only narrative.

Do not require every useful result to contain a multi-step feedback loop. A paper may contribute a new institution, formal solution, boundary, direct effect, or welfare implication. The requirement is accurate attribution: label a direct or assumption-driven effect honestly rather than inflating it into a strategic mechanism.

Treat robustness as a **mechanism pressure test**, not a list of decorative extensions. Prioritize relaxations of assumptions with high conclusion load or weak institutional support. A robustness exercise should state which load-bearing assumption it challenges and what result/mechanism would be threatened if the extension reverses it.

## Cross-claim and narrative synthesis

After local proposition checks, ask whether the collection of claims is jointly coherent when the task is broad. Check for parameter-region gaps/overlaps, incompatible assumptions across propositions, benchmark changes, different equilibrium selections, and welfare definitions that prevent claims from being combined.

Also compare formal scope with narrative scope. An abstract, introduction, discussion, managerial implication, figure caption, or numerical summary must not silently upgrade a conditional or branch-specific result into a universal statement. A formally correct proposition can coexist with an overstated narrative; report these separately.

## Formal certification architecture: closure before conclusion

The general failure mode to prevent is **premature closure**: deriving a coherent candidate before the source specification, feasible set, cases, or claim domain are actually closed. Boundary mistakes, omitted constraints, empty parameter regions, hidden assumptions, and missed equilibrium branches are different manifestations of this same problem.

Before a consequential `PASS`, `UNIQUE`, `GLOBAL`, or equilibrium-existence conclusion, activate the following certification obligations when structurally relevant. A non-activated item is `NOT APPLICABLE`; do not perform bureaucracy for its own sake.

### C0 — Source closure

Identify the decisive source/model dependencies. Recover source-resolvable conditions from supplied/authorized material; do not silently fill unresolved formal gaps with a conventional assumption. If an unresolved source ambiguity can change feasibility, the equilibrium set, or the main claim, the verdict is scoped or `INCONCLUSIVE`.

### C1 — Constraint closure

Inventory every condition needed to define admissibility or equilibrium, including as applicable: action/strategy domains, accounting identities, probability bounds, market coverage and nonnegative demand/quantity, participation/IR, IC, capacity, budget balance, market clearing, Bayesian plausibility, outside options, state-transition consistency, and equilibrium-specific inequalities.

The question is not only whether the constraints already noticed are satisfied, but what justifies believing the relevant inventory is complete for the claim under review.

### C2 — Parameter-domain consistency

Treat the admissible parameter region itself as an object. Check whether the conjunction of stated parameter restrictions is nonempty. If the claimed regime is empty, report that directly; do not continue as if it described an attainable case.

### C3 — Feasible-set existence

For the claimed parameter region, establish that the feasible set is nonempty before treating first-order conditions or a candidate formula as a solution. If no feasible strategy/profile exists, report `NO FEASIBLE SOLUTION` or the equivalent scoped failure.

### C4 — Boundary and Threshold Gate

Trigger this gate when the model contains any of the following: continuous price/quantity/effort/quality/disclosure precision; open or semi-open strategy domains; piecewise objectives or best responses; participation/IC/probability constraints; mechanism-switch thresholds; parameter-region propositions; corner/constrained optima; comparison across mechanisms/institutions/outside options; equality boundaries; or multiplicity.

When triggered, exhaust the material cases: interior candidates, all active boundaries, threshold equalities, piecewise-switch points, open-domain limits, ties/indifference/multiplicity, and global cross-region comparisons. Check that the claimed regions cover the relevant admissible domain without unjustified gaps or overlaps.

For open or semi-open domains, distinguish an attained maximum/minimum from a supremum/infimum. A boundary value outside the feasible set is not a solution.

### C5 — Candidate verification / substitution-back

Every retained candidate must be checked against its action domain and every defining feasibility condition, then against the relevant optimality/equilibrium conditions. Do not treat a solved FOC, symbolic expression, or solver output as self-certifying. Check any algebraic transformations that can lose or introduce roots, including division by an expression that can equal zero, squaring, logs/roots, and branch simplifications.

### C6 — Equilibrium closure

Check the feasible deviations, participation choices, continuation branches, equilibrium candidates, and selection/refinement conditions capable of overturning the claim. An interior best response is not a global equilibrium merely because its local derivative is correct.

### C7 — Claim closure

The statement certified must match the domain actually checked. Distinguish local, branch-specific, parameter-region, and global validity. If the source's proposition is broader than the verified result, correct the proposition scope rather than upgrading the calculation.

### C8 — Targeted falsification

After constructing the strongest case for the claim, make one explicit attempt to break the load-bearing node. Target threshold neighborhoods, active-constraint intersections, equality cases, extreme admissible parameters, denominators/singularities, competing equilibrium branches, and profitable deviations. Numerical sampling is useful for finding counterexamples and stress-testing; failure to find a counterexample on a grid is not proof of a universal claim.

Prefer `analytical/symbolic reduction -> regime partition -> targeted computation -> counterexample search` over brute-force high-dimensional sweeps.

### Solution certificates and stale dependencies

For cross-session work, a strong result should be stored as a scoped certificate, not merely as a narrative conclusion. Record the claim, verified domain, decisive assumptions/constraints, source anchors if relevant, activated boundary/equilibrium checks, unresolved exclusions, and conditions that would invalidate the certificate. If a depended-on primitive, timing/information condition, action domain, payoff/constraint, or solution concept changes, mark the certificate `STALE` and rerun the affected checks rather than relying on conversation memory.

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

1. For a broad audit, what model-level inconsistency or omitted regime could matter even if no author-named proposition points to it?
2. What is the strongest structural failure that could overturn the claim?
3. Which assumption carries the most conclusion load, and does it encode the result?
4. If a mechanism is claimed, does the result survive a mechanism shutdown/freeze or smaller benchmark, and would that change the interpretation?
5. Which feasible alternative, deviation, continuation, or equilibrium branch was omitted?
6. What counterexample or contrastive evidence could materially challenge generalization? Skip this search when the claim is already scoped and the contrast cannot change the decision.
7. Which missing evidence or calculation would change the recommendation?
8. If the claim is about existence, uniqueness, a threshold, or a global region, what is the cheapest targeted falsification attempt that could overturn it?

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
