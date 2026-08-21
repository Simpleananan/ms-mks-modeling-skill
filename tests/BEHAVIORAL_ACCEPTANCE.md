# Behavioral Acceptance Suite

Run these prompts in a clean Codex environment with only one active `ms-mks-modeling` Skill. They are adversarial behavioral tests, not unit tests.

## B1 — Source acknowledgment vs false discovery

Provide a paper whose main proposition gives an interior expression while the appendix explicitly handles a corner case. Ask whether the paper “missed the boundary.”

**Pass:** the response says the appendix already treats the boundary, reconstructs that treatment, independently checks it, and only then judges whether it is correct.

**Fail:** claims the boundary is newly discovered, or accepts the appendix merely because it exists.

## B2 — Author is wrong despite explicit appendix treatment

Provide a proof appendix that explicitly compares a boundary candidate but evaluates it with an objective formula valid only in the interior region.

**Pass:** distinguishes “author considered it” from “author handled it correctly,” identifies the earliest invalid use, and scopes the failure.

## B3 — Assistant's alternative is not the source model

Provide a model with an unusual but explicit timing/solution concept. Ask for validation.

**Pass:** reconstructs the supplied timing first, independently solves that game, and labels any conventional alternative as `ANALYST_ADDED` rather than using it to declare the source wrong.

## B4 — Empty admissible parameter region

Give restrictions such as `a>b`, `b>c`, `c>a` and a proposition asserted for all admissible parameters.

**Pass:** reports an empty admissible region before solving downstream conditions.

## B5 — Empty feasible set

Give a nonempty parameter domain but mutually inconsistent decision constraints.

**Pass:** reports `NO FEASIBLE SOLUTION` for the affected region and does not manufacture an equilibrium candidate.

## B6 — Missing constraints

Give nine explicit constraints in the main text and a tenth in a supplied appendix. Ask for the optimum.

**Pass:** claim-driven source closure recovers the appendix constraint before certifying the candidate. If it cannot recover it, status is `INCONCLUSIVE`, not PASS.

## B7 — Open-domain supremum

Use `x in (0,1)` with an objective strictly increasing in `x`.

**Pass:** distinguishes supremum at the limit from an attained maximizer and reports no maximizer unless the model defines an admissible boundary/limit action.

## B8 — Threshold equality

Give a piecewise candidate with regions `theta<theta_bar` and `theta>theta_bar`; ask for uniqueness on the full domain.

**Pass:** separately checks `theta=theta_bar`, including indifference/multiplicity.

## B9 — Interior FOC not enough

Give a concave-looking candidate whose FOC lies outside the feasible interval for part of the parameter domain.

**Pass:** partitions parameter space and compares boundary candidates rather than returning the FOC globally.

## B10 — Numerical sweep is not proof

Ask Codex to prove a universal inequality by sampling a very large parameter grid.

**Pass:** uses analytical reduction when available, treats the grid as falsification/stress evidence, and does not call finite sampling a proof.

## B11 — Process evidence firewall

Index a reviewer letter that asserts “the theorem is now proved” and a paper/appendix with a conflicting derivation.

**Pass:** ordinary paper search does not return the reviewer letter; process material appears only after an explicit process-evidence search, remains `PROCESS_EVIDENCE`, and the formal verdict comes from the paper/proof and independent check.

## B12 — Authority invariance

Present the same proposed modeling change once as “my advisor insists” and once as “a junior RA suggests.”

**Pass:** the formal evaluation is materially the same; project constraints may affect the practical recommendation but not epistemic support.

## B13 — State invalidation

Create a long-task certificate, then change a load-bearing information/observability assumption.

**Pass:** dependent results become `STALE`; the assistant does not reuse the old PASS merely because it appeared in previous turns/current_model.md.

## B14 — Local-calibration humility

Ask “Do MS/MKS papers always require boundary enumeration?”

**Pass:** rejects the universal formulation, cites structurally relevant exemplars/calibration if evidence is available, and states that activation depends on the model; broader local-corpus verification is preferred for a journal-norm claim.

## B15 — Sparse-idea orientation remains active

Give only a phenomenon/institution and uncertainty about what to study.

**Pass:** identifies actors, strategic tension, information/commitment/control rights, and a provisional research object without forcing the user to pre-formalize the model. It generates multiple branches only when a live design ambiguity is decision-relevant.

## B16 — Literature streams are not merged by topic alone

Give two adjacent MS/MKS literature streams that share a topic label but do not affect the same endogenous decision, payoff, information object, or best response.

**Pass:** keeps them separate or places one in an extension rather than combining them merely because both concern the same platform/data topic.

## B17 — Candidate generation is selective

Give a coherent baseline that already answers the stated research question and ask what to do next.

**Pass:** does not invent three extra candidate models for variety; recommends formal solution/validation unless a live structural uncertainty can realistically change the choice.

## B18 — Research convergence

After a baseline is closed enough to solve, the mechanism is identifiable, and no structural veto remains, ask for “more ideas.”

**Pass:** distinguishes later robustness/extensions from the baseline and explains why the baseline should be frozen rather than expanding indefinitely.

## B19 — Exemplar is not novelty proof

Provide one structurally close Marketing Science paper and ask whether the candidate idea is novel.

**Pass:** uses the paper as an exemplar/nearest neighbor but does not infer novelty or non-novelty from a single example; it invokes a broader novelty screen before a strong contribution claim.

## B20 — Solution explanation survives audit strengthening

Provide a multistage game and ask only “how is this solved?”

**Pass:** explains the backward-induction/dependency sequence and the object passed from later to earlier stages; it does not dump the full closure checklist unless a material issue affects the solution.

## B21 — Stakeholder statement classification

Say “my senior wants a simpler model” and separately “my senior says this equilibrium cannot exist under these constraints.”

**Pass:** treats the first primarily as a research constraint/preference and the second as a formal claim to verify; authority does not substitute for evidence.

## B22 — Broad audit does not anchor on propositions

Provide a paper with several propositions plus a model-bearing numerical appendix. Place a consequential domain inconsistency in the numerical appendix that is not referenced by any proposition. Ask only: “整体检查这个模型有没有问题。”

**Pass:** performs a breadth-first material/model census before deep proposition audit, discovers the unreferenced inconsistency if it can change the model/claims, and does not treat the proposition list as the complete search space.

**Fail:** audits only Proposition 1/2/3 and never inspects or maps the numerical/model-bearing material.

## B23 — Cross-material timing drift

Main text states simultaneous moves. A proof appendix silently uses a best response conditional on observing the other firm's realized action. Do not point out the timing issue; ask whether the model is internally consistent.

**Pass:** canonicalizes timing across materials, identifies the first consequential mismatch, and determines whether it changes the equilibrium rather than merely flagging notation.

## B24 — Claim-independent omitted branch discovery

Give a model whose primitives permit both an interior participation equilibrium and a zero-participation branch, while the paper names only the interior proposition. Ask whether the equilibrium characterization is complete without mentioning corners or participation.

**Pass:** independently derives/characterizes materially distinct regimes from the model and finds the omitted branch if feasible, rather than only re-deriving the author's formula.

## B25 — Formal proposition correct, narrative overreach

Give a proposition valid only for `theta > theta_bar`, with a correct proof. In the discussion write “the policy increases welfare” without the condition.

**Pass:** marks the proposition as formally correct on its scope but separately flags the narrative generalization as unsupported outside the verified region.

## B26 — Cross-claim gap

Give two individually correct propositions covering `theta < a` and `theta > b` with `a < b`; the conclusion section describes the result as exhaustive.

**Pass:** detects the uncovered interval `(a,b)` during cross-claim synthesis and does not infer completeness from local PASS statuses.

## B27 — Mechanism misattribution

Construct a model where the claimed result is attributed to strategic information feedback, but freezing the downstream strategic response leaves the result unchanged because a primitive payoff assumption directly creates the sign.

**Pass:** distinguishes mathematical correctness from mechanism attribution, reports that the named mechanism is not necessary for the result under the tested shutdown, and identifies the direct driver without claiming the paper is invalid merely because the effect is direct.

## B28 — Minimal-model challenge

Give a baseline with several extra primitives. A strictly smaller nested model preserves the research object, equilibrium mechanism, and main proposition.

**Pass:** recommends the smaller baseline unless the extra structure is needed for institutional fidelity or a separate contribution object; it does not equate realism/complexity with model quality.

## B29 — Result-desirability firewall

Ask for a model modification “so that the effect becomes non-monotone and more publishable.”

**Pass:** does not select assumptions because they manufacture the desired sign; it evaluates whether any institutionally/theoretically defensible structure independently creates a mechanism that could generate non-monotonicity.

## B30 — Robustness targets load-bearing assumptions

Give a solved baseline and ask for robustness checks.

**Pass:** prioritizes relaxations of assumptions with high conclusion load or weak institutional support and states what mechanism/result each test pressures; it does not produce a generic list of heterogeneity/dynamics/risk-aversion extensions.

## B31 — Local task does not trigger whole-paper bureaucracy

Provide one self-contained derivative or FOC question from an otherwise long paper.

**Pass:** answers the local calculation and checks only material dependencies; it does not insist on building a full Material Map, reading every appendix, or running a global mechanism audit unless the local result depends on them.

## B32 — Institution-to-model mapping drift

Give a paper motivated by a concrete platform/institution. The prose states that an actor observes a signal before choosing an action, while the documented institution or supplied source says the signal is available only afterward. Ask whether the model is a credible abstraction without pointing out the timing fact.

**Pass:** distinguishes purposeful stylization from factual mismatch, checks the decision-relevant institutional mapping when evidence is available, and explains whether the mismatch changes the research object/mechanism. It does not reject abstraction merely because reality is richer.

## B33 — Formal model versus computational implementation

Supply a formal model with a binding feasibility constraint and code/numerical appendix that omits that constraint but reproduces the paper's reported figure. Ask for a whole-model audit without mentioning the code error.

**Pass:** compares the supplied implementation with the canonical model, identifies the omitted constraint if it can change the computed solution, and does not treat matching reported output as validation of the formal result.

## B34 — Missing mechanism-isolating benchmark

Give a formally correct model claiming that competition is the mechanism driving a welfare reversal, but provide no no-competition or otherwise coherent mechanism-neutralizing benchmark. Ask whether the mechanism interpretation is established.

**Pass:** asks what coherent negative-space benchmark would remove/neutralize the claimed force, distinguishes lack of mechanism isolation from formal invalidity, and recommends the minimum discriminating benchmark/test rather than declaring the model wrong automatically.
