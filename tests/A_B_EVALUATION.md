# A/B evaluation protocol — Skill versus no-Skill

Use this protocol to test whether the Skill adds research value rather than merely producing longer answers. Run the same hidden-defect task in fresh, independent conversations with and without the Skill. Do not reveal the planted defect in the prompt.

## Primary metrics

Score each item 0–2 unless otherwise noted.

1. **Material defect discovery**
   - 0: misses the consequential issue;
   - 1: notices a symptom but not the underlying structural defect;
   - 2: identifies the defect and its downstream consequence.

2. **Independent discovery gain**
   - 0: only checks author-named propositions/paths;
   - 1: performs some independent checks but stays mostly source-conditioned;
   - 2: discovers a material issue/regime/benchmark not nominated by the source or prompt.

3. **False-positive control**
   - 0: elevates nonissues/stylizations into model failures;
   - 1: raises weak concerns with limited calibration;
   - 2: ranks concerns by consequence and dismisses immaterial differences.

4. **Source attribution accuracy**
   - 0: misstates what the author/source did or presents an author-treated issue as new;
   - 1: partially distinguishes source treatment from independent judgment;
   - 2: clearly separates source treatment, independent analysis, and remaining disagreement.

5. **Scope calibration**
   - 0: gives unconditional PASS/FAIL beyond the verified domain;
   - 1: gives partial qualifications;
   - 2: scopes existence/uniqueness/global/narrative claims to the verified region and branch.

6. **Mechanism diagnosis**
   - 0: accepts or rejects the mechanism by narrative intuition;
   - 1: traces the mechanism but does not isolate it;
   - 2: distinguishes necessity, contribution, and scope using a coherent benchmark/intervention when decision-relevant.

7. **Research-design value**
   - 0: only checks algebra;
   - 1: comments on assumptions/complexity generically;
   - 2: identifies a concrete architecture, minimal-model, institution-mapping, robustness, or contribution implication that can improve the research design.

8. **Local-task overhead**
   - 0: turns a bounded task into unnecessary whole-paper bureaucracy;
   - 1: some avoidable overhead;
   - 2: stays local unless a material dependency requires expansion.

## Hard-error flags

Record separately; one hard error can outweigh a higher verbosity/coverage score:

- fabricated source content or citation;
- omitted explicit constraint that invalidates the result;
- declares existence on an empty admissible/feasible set;
- treats finite numerical sampling as proof of a universal claim;
- silently changes timing/information/equilibrium concept;
- treats process evidence as formal proof;
- claims a diagnostic freeze is a valid equilibrium counterfactual when it is not;
- claims novelty from one exemplar.

## Comparison rule

Do not judge Skill value by whether both versions mention the same headline issue. Compare:

- **material recall**: how many consequential hidden defects are found;
- **precision**: how many raised concerns are actually material;
- **causal depth**: whether the response identifies the earliest broken link/mechanism carrier;
- **scope discipline**: whether verdicts match the verified domain;
- **research actionability**: whether the proposed repair/test changes the research decision;
- **overhead**: whether local tasks remain proportionate.

A meaningful Skill gain should improve at least one of material recall, precision, causal depth, or scope discipline **without materially degrading the others or local-task overhead**.

## Suggested experiment design

- Use at least 8–12 hidden-defect cases spanning formal, completeness, mechanism, research-design, cross-material, and local-task cases.
- Randomize whether the planted defect appears in main text, appendix, numerical material, or institutional description.
- Keep prompts identical across conditions.
- Start fresh conversations to avoid memory/context contamination.
- Blind the scorer to condition when feasible.
- Record both the first answer and the answer after one neutral follow-up such as “再自检一下有没有遗漏”。
- Report per-case scores and failure types, not only an average score.

The behavioral cases in `BEHAVIORAL_ACCEPTANCE.md` can seed the test set, but use paraphrased or novel variants so the evaluation measures generalization rather than prompt matching.
