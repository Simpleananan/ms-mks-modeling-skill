# Evidence policy

Load this reference when literature, institutional facts, modeling norms, examples, contribution, or external process materials can affect the answer.

## Evidence is for decisions

An item is **MATERIAL** only if it changes or narrows at least one of:

- formalization;
- activated validation check;
- claim boundary;
- modeling verdict or repair;
- uncertainty/confidence;
- comparison between alternatives.

If it only adds a citation to an unchanged statement, label it **DECORATIVE / NONMATERIAL** internally and omit it. Retrieval count, journal status, and lexical score do not substitute for support.

For each important judgment, aim to establish:

`Judgment -> Why -> Paper example -> Exact support -> Boundary/counterexample`.

Do not force both sides when the issue is settled or the contrast is irrelevant, but seek supporting plus boundary/contrastive evidence when it could change the recommendation.

## Evidence depth D0-D4

- **D0 — identity only**: title/metadata/search result. Supports discovery only.
- **D1 — abstract/summary**: supports broad topic, question, setting, or headline result; not exact assumptions, timing, proof, or equilibrium completeness.
- **D2 — main-text passage**: supports the inspected definition, assumption, timing, mechanism statement, proposition, or discussion within its local scope.
- **D3 — formal main text plus relevant appendix/proof**: can support exact formal dependencies, proof conditions, equilibrium construction, robustness, or omitted cases that were actually inspected.
- **D4 — triangulated evidence**: D2/D3 evidence is checked against linked appendix, correction/comment/rejoinder, revision history, data/code, or a contrastive formal paper. D4 increases auditability, not automatic truth.

Never reconstruct D2/D3 details from D0/D1. If full text is unavailable, downgrade the claim and confidence.

## Source priority and scope

1. Search the authorized local paper knowledge base first.
2. For current MS/MKS modeling norms, nearest neighbors, and contemporary exemplars, prioritize Management Science and Marketing Science from roughly the last 3–5 years.
3. Use other UTD journals when the research domain or formal neighbor requires them.
4. Classic theory, mathematical methods, correction/comment/rejoinder, and AI-method evidence are not restricted to UTD journals.
5. Use official journal or publisher pages for web fallback when possible; inspect full text or official OA. Search snippets support discovery only.

This is a priority rule, not an exclusion rule. “No counterexample found” never means no counterexample exists.

Use a single paper as a precedent only for the inspected structural move and its scope. Describe a practice as a field norm only after repeated, structurally relevant evidence; otherwise attribute it to the paper. Absence of a direct precedent is not a veto on a model. A new linkage can be a valid candidate when its component primitives have defensible institutional or theoretical foundations and the resulting strategies, equilibrium, and claims are established by the new analysis. In that case, literature supports the components and boundaries—not the untested linkage itself.

Do not let retrieval define the candidate space before the research problem is understood. For a phenomenon-led task, first form provisional structural hypotheses, then use literature to challenge, refine, or screen them. Retrieve earlier when the task is paper-led, when a modeling convention is needed to make the game coherent, or when collision risk is already decision-relevant.

## Exemplar retrieval and novelty screening

Keep these evidence tasks separate.

- **EXEMPLAR_RETRIEVAL**: find a few structurally close papers that show how an institution, assumption, timing choice, or mechanism is modeled. Use them as supporting or contrastive examples; do not infer novelty from this sample.
- **NOVELTY_SCREEN**: compare a candidate against a broader nearest-neighbor set, emphasizing recent Management Science and Marketing Science work and expanding to other UTD journals when needed. Check the research question, primitives, timing/information, strategic response, mechanism, and claims—not title keywords alone.

Working papers can warn of collision but do not establish the published-literature boundary. Non-UTD work can reveal a mechanism or neighbor. Process materials do not prove novelty in the published literature.

Without sufficient nearest-neighbor comparison, limit the conclusion to “collision risk,” “potential mechanism delta,” or “novelty not established.” Do not claim that an idea is independent, already non-novel, highly publishable, or has little contribution space.

When a question spans distinct mechanism streams, formulate and retrieve each stream separately before comparing work groups. Use stream separation to improve recall and recover canonical primitives; apply the recomposition gate in `modeling_and_validation.md` before combining structures.

## Evidence roles

- `MAIN_ARTICLE`: published article evidence.
- `ONLINE_APPENDIX`: linked formal derivations, proofs, robustness, or extensions.
- `COMMENT_CORRECTION`: published correction, erratum, comment, or rejoinder; inspect its relationship to the target article.
- `PROCESS_EVIDENCE`: reviewer, editor, decision, response, or revision materials.

Maintain the **PROCESS_EVIDENCE firewall**. Process materials can show that a concern arose, what a reviewer or editor requested, what an author claimed to have changed, or—when pre/post materials are actually inspected—what changed between versions. A requested revision does not establish implementation; an author response does not establish formal validity; acceptance does not establish that a particular change caused acceptance. Process materials are not automatically correct and cannot establish a theorem or modeling norm without independent formal or published support. Distinguish reviewer/editor claims, author claims, observed version changes, and the final article.

## Examples

- **Positive exemplar**: show the precise structural move that works and the scope in which it works.
- **Failure evidence**: prefer a documented criticism, correction, response, or version change; state whether the failure was accepted, repaired, disputed, or unresolved.
- **Contrastive example**: compare papers that may both be strong but use different primitives or institutions, producing different mechanisms or boundaries.

Avoid cherry-picking by stating the retrieval scope, choosing examples for structural proximity, looking for a materially different result, and reporting unresolved coverage limits.

## Minimum citation record

Retain internally when available: title, authors, year, journal, DOI, evidence role, source file or official URL, page/section, inspected passage location, evidence depth, exact support, what the passage does not support, applicability to the current model, supporting/contrastive role, unresolved conflict, and evidence usefulness. Hiding provenance never permits skipping these checks.

## Citation and evidence display

Default to numeric citations such as `[1]`, `[2]`, and collect references at the end. If the user explicitly establishes Author-Year style in the first substantive research interaction, or the supplied research text consistently uses `(Author, Year)`, inherit that style. A casual natural-language mention such as “Liu and Long (2025)” does not establish a style. Do not make the user adapt to the Skill's default.

Use paper examples in the body to explain the modeling judgment and state their exact support or boundary. By default, keep DOI, hash, local path, retrieval score, D0-D4 label, evidence-card fields, OA filename, and provenance-audit fields out of the user-facing answer. End references need only authors, title, journal, and year. Expand DOI, page/section, main-article/OA role, and source locator when the user requests detailed provenance or when the disputed claim cannot otherwise be audited.

When both published research and reviewer/editor/response materials appear, separate the external reference list lightly as “Papers” and “Review-process materials,” or the equivalent headings in the response language. Do not expose the internal `PROCESS_EVIDENCE` label; keep its evidentiary limits unchanged.

Show a local source or Skill path only when it helps the user navigate. Put long paths on their own line after a short label such as `Local file:` or `Local location:`; do not embed them inside analytical prose. A path is navigation information and never substitutes for a verified citation.

Before sending, apply the citation-rendering gate:

- every numeric marker has a corresponding reference;
- no dangling “see” or unresolved citation marker remains;
- no retrieval score, evidence-depth tag, evidence-card field, hash, or development syntax leaks into the response;
- the reference list contains only sources used in the answer;
- any local path is separated from the academic claim it helps locate.

Citation-light presentation does not lower verification depth, source qualification, the evidence-usefulness gate, counter/contrastive search, conflict reporting, or confidence calibration. Never omit a material boundary or downgrade **INCONCLUSIVE** merely to keep the answer short.

If sources conflict, describe what differs—primitives, institution, proof scope, versions, or claims—then mark the affected judgment **INCONCLUSIVE** or branch-specific until adjudicated.
