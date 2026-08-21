# Design v0.5 — research-model-centered discovery, mechanism, and certification

## Why v0.5 exists

v0.4 solved an important class of failures: premature formal closure around constraints, parameter regions, boundaries, candidate validity, equilibrium branches, and claim scope. Behavioral testing then revealed a deeper limitation: a system can validate an **author-named proposition** rigorously while still failing to discover model-level problems that the author did not nominate for inspection.

v0.5 therefore changes the center of gravity from **proposition-centered validation** to **research-model-centered reasoning** without removing the v0.4 certification layer or the original end-to-end research workflow.

## Three governing principles

1. **Design before solve** — determine whether the formal architecture actually carries the research object and whether a smaller model would do the same job.
2. **Discover before certify** — in broad audits, map the model and independently discover materially distinct solution regimes before using the source's propositions as the search space.
3. **Explain mechanism before claim** — distinguish a mathematically correct result from the strategic or direct force that actually creates it.

`Closure before conclusion` remains the certification rule inside this larger architecture.

## Task-scope routing

v0.5 explicitly distinguishes:

- **LOCAL** tasks: one equation, derivation, proposition, parameter region, or bounded formal question. Run only the integrity/discovery/certification checks capable of changing that local answer.
- **MODEL/PAPER-WIDE** tasks: whole-model soundness, overall paper audit, completeness, baseline freeze, major redesign, mechanism/contribution assessment, or “what did the paper miss?” Run the breadth-first census and cross-material integrity pass before deep proposition audit.

This prevents the new global layer from turning every local calculation into whole-paper bureaucracy.

## Model-level pipeline

For broad analytical-model work the conceptual pipeline is:

`research object -> model architecture -> material/model census -> cross-material integrity -> independent solution-space discovery -> mechanism identification/falsification -> claim certification -> cross-claim/research judgment`.

### 1. Research object and architecture

Identify the strategic/institutional phenomenon, the endogenous carrier, the necessary primitives, and the intended contribution object. Use a minimal-model challenge, assumption-to-result distance, and a result-desirability firewall when they can change model selection.

### 2. Breadth-first census and canonical model map

Map model-bearing materials first, then canonicalize repeated formal objects such as timing, information, domains, constraints, equilibrium concepts, benchmarks, and welfare definitions. When application claims or computational results are load-bearing, also compare institution-to-model mappings and supplied implementation/code against the same canonical model. The purpose is anti-anchoring and cross-material consistency—not exhaustive reading.

### 3. Independent solution-space discovery

The independent path must not merely re-derive the author's displayed formula. The first pass is **claim-independent**, not literally blind: already-seen source results are not treated as the derivation target. It first identifies natural regime-generating objects (active constraints, participation switches, indifference conditions, boundaries, piecewise changes, equilibrium-selection points) and characterizes materially distinct feasible/equilibrium branches. Only afterward are these compared with the source's named propositions.

### 4. Mechanism identification and falsification

When a mechanism claim is load-bearing, trace `assumption/primitive -> strategic response -> equilibrium object -> result`. Use only decision-relevant interventions: assumption leverage, mechanism shutdown/freeze, benchmark isolation, negative-space benchmark reasoning, minimal-model comparison, or alternative-mechanism checks. A direct effect is allowed; the requirement is accurate attribution.

### 5. Claim certification

Retain v0.4 source/formal/claim truth, source acknowledgment, dual-track divergence diagnosis, C0-C8 closure, boundary/threshold analysis, substitution-back, equilibrium closure, claim scoping, and targeted falsification.

### 6. Cross-claim and narrative synthesis

A set of locally correct propositions can still leave parameter gaps, inconsistent assumptions, incompatible equilibrium selections, or narrative overreach. Broad audits therefore reconcile claims and compare formal scope with abstract/discussion/managerial claims.

## Failure taxonomy

v0.5 distinguishes four failure classes:

1. **Formal failure** — the mathematics/equilibrium condition is wrong.
2. **Completeness failure** — the local calculation is correct but constraints, branches, boundaries, or parameter regions are omitted.
3. **Mechanism failure** — the result is correct but the claimed causal/strategic mechanism is not the actual carrier.
4. **Research-design failure** — the model may be formally correct but is unnecessarily complex, weakly mapped to the institution, result-engineered, contribution-colliding, or built around a research object different from the one claimed.

Severity follows downstream research consequence, not category labels.

## MS/MKS calibration boundary

The public calibration file verifies only structural observations directly supported by official INFORMS article/abstract pages. v0.5's minimal-model challenge, breadth-first census, mechanism-shutdown test, and fixed audit order are **not presented as universal MS/MKS norms**. They are research-assistant diagnostics whose usefulness and journal fit should be stress-tested against the user's local MS/MKS corpus at D3/D4 depth.

The Skill should generalize to the **function** strong papers perform (mechanism isolation, scope discipline, institutional coherence), not enforce one exposition or proof style.

## Preservation invariant

v0.5 is additive. It retains:

- orientation from incomplete prompts;
- target-paper reconstruction;
- literature-stream recomposition;
- candidate generation and evaluation;
- research convergence;
- solution explanation;
- repair and selective revision;
- shadow drafting;
- exemplar retrieval versus novelty screening;
- process-evidence firewall;
- stakeholder decision routing;
- v0.4 formal certification and retrieval engineering.

Package tests assert these sections remain present so later revisions do not silently turn the Skill into a narrow theorem checker.
