# Local MS/MKS Knowledge-Base Verification

Use this after installing the release candidate. The purpose is to test whether the protocol is supported by a broader local MS/MKS corpus and to find where it is overgeneralized.

## A. Verify the public calibration anchors

Retrieve the local main article + relevant online appendix for each DOI in `references/ms_mks_calibration.md`. Confirm or reject the specific listed calibration point rather than merely confirming the paper exists.

Priority checks:

1. `10.1287/mksc.2024.0960`
   - seller adoption/deviation conditions;
   - independent-signal robustness;
   - observability extension;
   - whether a stated inequality-defined regime is explicitly shown empty.
2. `10.1287/mksc.2022.1397`
   - threshold definitions;
   - case-by-case backward induction;
   - nonnegative-quantity/feasibility conditions.
3. `10.1287/mnsc.2022.4475`
   - strategic-user response and scope conditions.
4. `10.1287/mksc.2022.1392`
   - strategic investment/disclosure/consumer-belief interaction.
5. `10.1287/mnsc.2023.4770`
   - direct vs information/participation mechanisms and extensions.
6. `10.1287/mnsc.2021.03426`
   - distinction between rational-equilibrium predictions and behavioral evidence/modeling.

Record any mismatch and modify the calibration file rather than forcing the local paper to fit the protocol.

## B. Test whether the closure checks generalize

Sample at least 10 structurally nearby analytical papers across MS and MKS. For each paper, code whether its formal analysis activates:

- continuous constrained choice;
- piecewise demand/best response;
- participation/IR/IC;
- threshold-defined parameter regions;
- multiple equilibrium/mechanism cases;
- information/observability changes;
- appendix-only boundary qualifications;
- numerical or computational verification.

Then ask whether the Skill's corresponding check would have been useful, irrelevant, or misleading.

The target is not 100% activation. The target is correct **conditional activation**.

## C. Falsify the Skill itself

Search the local corpus for counterexamples to these design assumptions:

- cases where exhaustive boundary analysis is unnecessary because a theorem establishes interiority globally;
- models where the author's alternative solution route is intentionally equivalent and dual-track reconstruction would add no value;
- computational models where analytical regime decomposition is infeasible and numerical global methods are the primary proof device;
- papers where process materials contain corrections not yet incorporated in the published artifact.

If found, refine activation rules rather than weakening validation globally.

## D. Acceptance criterion

Promote the release candidate only if:

- no calibration statement materially misrepresents its source;
- conditional checks do not systematically over-trigger on unrelated model classes;
- empty-set, boundary, constraint-completeness, and source-acknowledgment cases produce the intended behavior;
- retrieval keeps paper/process evidence separated in the actual local folder structure;
- duplicate Skill discovery has been removed from the test environment.

## E. Test the v0.5 discovery and mechanism layer

The v0.5 diagnostics must be falsified against the local MS/MKS corpus rather than assumed to be journal norms.

Sample structurally close analytical papers and inspect main text plus relevant supplements. For each paper, record whether the authors perform the **underlying research function**, regardless of label or exposition style:

- **model census / consistency function:** do formal objects remain consistent across model setup, proofs, extensions, numerical sections, and welfare claims? If definitions change, are the changes explicit and treated as a new regime/model?
- **solution-space discovery function:** does the analysis characterize all materially relevant branches or establish conditions that rule them out without enumeration?
- **mechanism-isolation function:** are benchmarks, decompositions, comparative statics, extensions, or other devices used to identify which strategic force produces the result?
- **assumption-leverage function:** can one tell which assumptions are load-bearing versus mainly tractability/institutional assumptions?
- **minimal-baseline function:** is the baseline smaller than later extensions in a way that isolates the central force, or do strong papers sometimes require rich baselines for institutional fidelity?
- **narrative-scope function:** do abstract/discussion/managerial claims stay within the formal domain, and how are broader implications qualified?

Do not code only whether a paper literally contains a “mechanism shutdown” or “minimal model” section. The Skill should learn the function, not force one presentation format.

### Counterexample searches

Actively look for papers where:

- a proposition-first proof structure is sufficient because a preceding theorem already gives global model closure;
- a rich baseline is essential and a minimal-model challenge would misleadingly prefer a stripped model;
- a direct effect is the intended contribution and mechanism-falsification language would overstate the need for strategic feedback;
- numerical/computational global solution is the natural solution-space discovery device;
- extensions legitimately change the research object and are explicitly framed as such rather than robustness;
- narrative claims are broader than proposition statements but are still justified by separate analysis outside the proposition.

Use these counterexamples to refine activation conditions rather than weakening the whole architecture.

## F. A/B behavioral gain test

Do not evaluate the Skill only on cases where the prompt already names the defect. Compare Skill versus no-Skill on **hidden-defect** cases such as:

1. main-text/appendix timing drift not mentioned in the prompt;
2. an omitted equilibrium/participation branch not named by the author;
3. two individually correct propositions with an uncovered parameter interval;
4. a correct formal proposition but an overgeneralized discussion claim;
5. a claimed mechanism that disappears under a coherent shutdown/freeze test;
6. a baseline with non-load-bearing complexity that a smaller nested model removes.

Measure at least:

- new consequential issues discovered;
- false positives / manufactured objections;
- source-attribution accuracy;
- formal correctness and scope calibration;
- mechanism-attribution accuracy;
- unnecessary token/compute overhead on LOCAL tasks.

The goal is not “Skill finds more problems at any cost.” The goal is **higher decision value per audit**: more material discoveries, fewer unsupported objections, and no major loss of efficiency on narrow tasks.
