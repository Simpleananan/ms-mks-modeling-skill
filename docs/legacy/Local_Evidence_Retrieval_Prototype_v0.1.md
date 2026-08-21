# Local Evidence Retrieval Prototype v0.1

> Status: benchmark complete; this is a prototype decision, not a final `SKILL.md`.  
> Date: 2026-08-13  
> Read-only sources used during the private benchmark: an authorized paper corpus and an authorized review/response corpus. Public release uses configurable `<PAPER_LIBRARY_ROOT>` and `<PROCESS_LIBRARY_ROOT>` paths.  
> Retained artifact: `local_evidence_retrieval.py`; the 321.5 MB benchmark index is disposable derived data and is not retained.

## 1. Executive decision

**Decision: select C, implemented as a hybrid: filename/metadata `rg` for identity lookup + persistent lightweight SQLite FTS5 candidate retrieval + Codex structural reranking and evidence qualification.** A pure filename/ripgrep path is too brittle for assumptions and process evidence. Bare FTS5 is materially better at passage discovery but does not know whether a passage matches the game's structure or whether it can bear the proposed claim. Codex reranking is therefore not an optional polishing step: it is the layer that turns lexical candidates into modeling evidence.

SQLite is warranted here, but only as a rebuildable local index, not a service or research workbench. The corpus benchmark indexed 2,171 readable PDF/DOCX artifacts into 158,014 page-located chunks; 3 empty PDFs failed visibly. The prototype index occupied 337,088,512 bytes (321.5 MB). Warm lexical queries normally returned in roughly 0.2–0.7 seconds; the broad PROCESS_EVIDENCE query took about 2.1 seconds. The expensive operation was first-pass PDF parsing, not SQLite querying. Consequently, rebuilding the entire index per task is rejected; an actual technical design needs incremental freshness checks based on path, size and modification time.

The benchmark verdict is **GO WITH PATCHES for Skill Technical Design v0.1**. The retrieval route is viable and improves judgment, but the retained script remains a minimal reference prototype, not deployment-ready code: author/section extraction, work deduplication, incremental update and rank diversification require prototype hardening.

## 2. Benchmark design

### 2.1 Methods actually compared

| Method | Actual implementation | What it was allowed to do |
|---|---|---|
| A. lexical/ripgrep baseline | `rg --files` against titles/paths; on-demand `pdftotext` + lexical grep after a work was discovered | No prebuilt full-text corpus; represents the cheapest local-first route |
| B. SQLite FTS5/BM25 | PDF page and DOCX-body extraction; overlapping chunks; FTS5 `bm25()` across chunk text plus weighted title/work/role/journal fields | Retrieve and locate candidate passages; no semantic interpretation |
| C. lexical + Codex reranking | B's bounded candidate pool, plus known-identity hits from A; Codex compares structural features and evidence role/depth, groups main/OA by work, and excludes merely topical hits | May rerank/exclude, but may not invent missing text or upgrade evidence depth |

This is not a winner-by-total-score test. Each question records discovery, passage quality, evidence qualification and decision impact separately. Query wording was allowed to change when the first lexical form exposed a vocabulary mismatch; that behavior is part of C, not hidden tuning to a known answer.

### 2.2 Retrieval and evidence units

The useful hierarchy is:

`work -> artifact/version role -> page/section -> chunk -> qualified use`

A chunk alone is not a citation, and a PDF alone is not evidence. The prototype retained the following fields: `work_id`, `role`, `title`, `authors`, `year`, `journal`, `doi`, `source_path/source_rel`, `page`, `section`, `chunk_index`, character offsets and `chunk_text`. Roles tested were `MAIN_ARTICLE`, `ONLINE_APPENDIX`, `PREPRINT`, `PUBLISHED_CORRECTIVE_EVIDENCE`, `PROCESS_EVIDENCE`, `DATA_OR_CODE`, and `OTHER`.

Two metadata lessons matter. First, filename year may be an ingestion/publication code rather than the printed publication year; qualified citations must prefer the article's citation block. Second, authors cannot safely be inferred from filenames. The prototype attempts conservative front-page citation-block extraction, but the mini-test on the 2025 Articles-in-Advance layout correctly left the field empty rather than guessing. Any parse failure must therefore become explicit `UNKNOWN` until Codex confirms the first page or official metadata; empty strings must never be rendered as complete citations.

### 2.3 Chunk policy tested

- PDF: preserve physical PDF page and never cross a page boundary; target about 1,400 characters with about 220-character overlap.
- DOCX process material: body chunks with `page = null`; retain source artifact identity and paragraph/body locator.
- Retrieval returns the stored chunk, not a context-free FTS snippet.
- At qualification time, expand one neighboring chunk or reopen the page when a sentence lacks assumptions, subject, comparison baseline or result scope.
- Main article and OA share `work_id`, but remain separate artifacts. Multiple copies with the same work identity must be collapsed before reranking.

The 1,400/220 setting was adequate for most prose mechanisms and process criticisms. It is not adequate for proofs spanning several pages; D3 qualification must retrieve the proposition, assumptions and relevant proof chain, not merely a high-scoring proof fragment.

### 2.4 Evidence depth and usefulness gate

The v0.2 policy survived the test:

- **D0** metadata/discovery: existence, title, authors, outlet, DOI, version only.
- **D1** official abstract: stated problem, coarse primitives and stated headline result only.
- **D2** relevant full-text model/results sections: timing, information, action, payoff role and scoped mechanism.
- **D3** full model plus relevant proposition/proof: exact result and equilibrium/proof scrutiny.
- **D4** main + OA/code/version chain: robustness, deviations, selection, alternative timing and version-sensitive claims.

An item is **MATERIAL** only if it changes or narrows at least one of: formalization, activated check, claim boundary, modeling verdict, uncertainty/confidence, or comparison between alternatives. Otherwise it is **DECORATIVE/NONMATERIAL**, even when the paper is prestigious and topically close. No benchmark used D0/D1 to infer an exact assumption, proof or equilibrium completeness.

## 3. Benchmark results by question

### Q1 — Timing/institution

**Question.** Find MS/MKS platform/information models with different commitment or timing structures.

**A behavior.** A strict filename pattern combining platform, information and timing/commitment returned no hit. A broader title search found information-sharing papers but could not reveal their stage order. This is a discovery false negative, not proof that the corpus lacks evidence.

**B behavior.** A broad FTS query returned 12 passages, including false positives such as *Strategic Timing and Dynamic Pricing for Online Resource Allocation*. It also retrieved the useful main/OA pair for Zha et al. and the relevant platform-information papers. BM25 ranked vocabulary overlap, not institutional equivalence.

**C qualification.** The strongest pair was:

1. Yong Zha, Quan Li, Tingliang Huang, and Yugang Yu (2023), “Strategic Information Sharing of Online Platforms as Resellers or Marketplaces,” *Marketing Science* 42(4):659–678, DOI `10.1287/mksc.2022.1397`. Main article, PDF pp. 7–9 (D2) states the sequence: platform commission and sharing contracts precede demand-signal realization; later wholesale and retail decisions follow, with retail prices set simultaneously. OA Appendix G, PDF pp. 9–10 (D4), reverses the order of commission and information-sharing contracting and reports Proposition G1: this alternative order does not change the platform's optimal decisions in the studied channel structures.
2. Qiaochu Wang, Yan Huang, Stefanus Jasin, and Param Vir Singh (2023), “Algorithmic Transparency with Strategic Users,” *Management Science* 69(4):2297–2317, DOI `10.1287/mnsc.2022.4475`. Main text, PDF pp. 4 and 17–19 (D2/D3) separates a baseline without firm commitment power from a Stackelberg/full-transparency case with commitment.

**Modeling judgment changed.** Timing robustness is not a generic property of “platform information models.” Zha et al. makes one local ordering swap without changing its policy result; Wang et al. treats commitment power as an economically meaningful regime and reports strengthened results. Therefore a proposed model must declare what is committed, observed and when; an OA robustness check in one institution cannot justify ignoring timing in another.

**Evaluation.** Discovery: A poor, B good with noise, C good. Passage depth: main + OA, D4 for the local timing swap. Qualification: MATERIAL (activated commitment/observability/timing checks and narrowed transferability). False positives: generic dynamic-pricing papers and preprints sharing “timing.” Missing evidence: no universal comparative theorem. Web fallback: no. Stop: further hits would add examples but would not change the viable distinction between locally innocuous order swaps and commitment-regime changes.

### Q2 — Assumption: common signal/shared posterior

**Question.** Find common-signal/shared-posterior information structures and identify the assumption's formal role.

**A behavior.** Title/path retrieval returned no hit; the assumption is in model text/OA, not the title.

**B behavior.** A first exact-phrase query produced no hit because line breaks and phrasing differed. Query expansion to `(common AND signal) OR (independent AND signals) OR (share AND posterior)` retrieved many semantically wrong uses of “common”; the relevant OA appeared around rank 13. This is a clear BM25 limitation.

**C qualification.** Yi Liu and Fei Long (2025), “Data and Algorithms: Strategic Disclosure of Competitiveness on Platforms Through Marketplace Analytics,” *Marketing Science*, Articles in Advance, DOI `10.1287/mksc.2024.0960`. Main article PDF p. 11 (D2) says a representative third-party provider makes both sellers observe the same signal. OA A.3.1, PDF pp. 17–20 (D4), replaces that with different independent providers/signals, resolves equilibrium again, and reports robustness of the key argument.

**Formal role.** The common signal gives symmetric information and a shared posterior in the relevant adoption profile, reducing the pricing game to a common-belief/symmetric representation. With independent signals, each seller's price must condition on its own posterior and the expected rival price; the feasible strategy and integration burden change. It is therefore a tractability and equilibrium-correlation assumption, not merely exposition. The OA shows robustness of a key argument in this model; it does not prove all claims or all parameter boundaries are invariant.

**Evaluation.** Discovery: A failed; B high recall/poor rank; C recovered the structural match. Passage depth: D4 main/OA. Qualification: MATERIAL (changed formalization and confidence, narrowed “innocuous”). False positives: experiments with common signals, common retailers, common platforms, and unrelated personalized-product models. Missing evidence: the benchmark did not audit every OA derivation. Web fallback: no. Stop: exact baseline plus relaxation and a solved consequence chain were available; additional papers were unlikely to change this assumption-role judgment.

### Q3 — Transparency -> strategic response -> outcome

**Question.** Find evidence that information transparency changes competition through strategic response.

**A behavior.** The exact title *Algorithmic Transparency with Strategic Users* was easily discovered. A therefore works when the user's vocabulary is already the paper's title vocabulary.

**B behavior.** Expanded FTS returned the paper's main text and OA heavily; repeated passages from one work dominated the top ranks. Work-level collapse was necessary.

**C qualification.** Wang et al. (2023), DOI `10.1287/mnsc.2022.4475`, main article PDF pp. 2–4 and 17–19 (D2/D3). Transparency lets agents game correlational features; anticipating this, high types invest more in causal features, and under stated cost/productivity conditions the firm can benefit. Commitment changes the game form, so the baseline and Stackelberg extension must not be blended.

**Modeling judgment changed.** “Transparency increases/decreases competition” is too coarse. A traceable claim must name (i) what becomes observable, (ii) whose feasible action or cost changes, (iii) how equilibrium response changes, and (iv) which payoff/outcome is evaluated. The paper supports transparency -> manipulation/investment response -> classification/productivity consequences, not a universal price-competition effect.

**Evaluation.** Discovery: A/B both strong; C essential for scope. Passage depth: D2/D3; OA available. Qualification: MATERIAL (narrowed the mechanism and activated response/commitment checks). False positives: repeated chunks from the same work and generic transparency mentions. Missing evidence: direct Bertrand competition is not this paper's outcome. Web fallback: no. Stop: main model and commitment extension resolved the mechanism and boundary; more citations would be decorative for this claim.

### Q4 — Contrastive mechanisms

**Question.** Find two related papers with different mechanisms/conclusions and trace the difference to primitives.

**A behavior.** Broad title search found several platform disclosure papers, including a good candidate, but could not choose a contrast based on title alone.

**B behavior.** `platform AND information AND disclosure AND competition` returned 12 passages dominated by *Design of Platform Reputation Systems*. It also retrieved Zha et al. BM25 did not enforce candidate diversity.

**C qualification and contrast.** Compare:

- Zijun (June) Shi, Kannan Srinivasan, and Kaifu Zhang (2023), “Design of Platform Reputation Systems: Optimal Information Disclosure,” *Marketing Science* 42(3):500–520, DOI `10.1287/mksc.2022.1392`; main PDF pp. 2–3, 9–14 and 16–18 (D2/D3). Ratings inform consumers; sellers can invest in quality. Partial disclosure can raise platform profit through sales-increasing, quality-improving and, in the competitive-supply extension, competition-softening effects.
- Zha et al. (2023), DOI `10.1287/mksc.2022.1397`; main PDF pp. 7–9 and 13–14 (D2/D3). A platform privately observes demand and chooses whom to inform under reseller/marketplace channel structures. Informed manufacturers/retailers adjust wholesale/retail decisions; information and competition effects differ by channel role and demand variability.

The contrast is not “one paper favors disclosure and one opposes it.” The first makes consumer learning and endogenous seller quality investment central; the second makes platform channel role, demand signal allocation and price/quantity responses central. Different recipients, endogenous actions, contracts and platform revenue sources produce different mechanisms and boundaries.

**Evaluation.** Discovery: A moderate; B high passage recall but low diversity; C strong. Passage depth: D2/D3 with OA available. Qualification: MATERIAL (changed the comparison from headline direction to primitive/mechanism differences). False positives: unrelated platform-power and generic disclosure works; many within-work duplicates. Missing evidence: no claim that these are the only admissible formalizations. Web fallback: no. Stop: two structurally close but non-equivalent exemplars made the primitive-to-mechanism contrast identifiable; a third did not promise a decision delta.

### Q5 — Failure/process evidence

**Question.** Find real criticisms/revision evidence about timing, observability or assumption-driven results.

**A behavior.** Filename keyword search returned no relevant hit because filenames identify manuscripts and document roles, not critique content. The existing process index can aid topic discovery but is not page-level full-text evidence.

**B behavior.** Role-filtered FTS retrieved actual reports. A broad OR query took about 2.1 seconds and surfaced useful and noisy results. Targeted follow-ups recovered:

- **Synthetic process case A — incentive timing.** A reviewer notes that the assumed sequence makes an incentive effectively chosen after a downstream price, activating a timing/commitment check.
- **Synthetic process case B — observability and differentiation.** A reviewer notes that inventory observability and absent downstream differentiation carry much of the result, activating an assumption-load check.
- **Synthetic process case C — stage-definition consistency.** A reviewer identifies an inconsistency between “entry” and “entry jointly with control structure” as the first-stage action.
- **Synthetic process case D — persuasion commitment/verifiability.** A reviewer asks how an information designer commits to a signal structure and how another party verifies it when contracts normally condition on observable/verifiable outcomes.

**C qualification.** All four are **PROCESS_EVIDENCE**. In the public package they are structure-preserving synthetic versions of private benchmark criticisms that activate timing, observability, commitment/verifiability and assumption-load checks. They are not published formal truth and cannot establish that a proposition is mathematically false. Where the corpus only contains reports/decision letters rather than an author response or later model, the revision consequence is evidence of demanded repair or rejection, not evidence that a repair succeeded.

**Evaluation.** Discovery: A failed; B strong; C's role firewall decisive. Passage depth: full process text, but outside the D0–D4 published-evidence ladder; label PROCESS_EVIDENCE. Qualification: MATERIAL as a check generator, NONAUTHORITATIVE for formal verdicts. False positives: process hits using “sequence” generically. Missing evidence: several cases lack a linked author response/revised manuscript, so “revision succeeded” is INCONCLUSIVE. Web fallback: no; web cannot replace private/local process files. Stop: multiple independent critiques covered the activated checks; further reports would not change the protocol judgment.

### Q6 — Nearest-neighbor trap

**Question.** Retrieve from the structural description: “two competing sellers receive information about a state and then set prices simultaneously; the platform controls information precision/disclosure.”

**A behavior.** A title/path expression returned only the reputation-system pair and missed the exact nearest neighbor. Broadening to “pricing” generated many topical false positives. This is the benchmark's clearest failure of filename retrieval.

**B behavior.** `sellers AND signal AND pricing AND platform` returned 12 passages. The exact work, Liu and Long (2025), appeared immediately, but an unclassified duplicate (`EBSCO-FullText...`) ranked alongside it, and weaker neighbors about price signals also appeared.

**C structural rerank.** Liu and Long (2025), DOI `10.1287/mksc.2024.0960`, main PDF pp. 6–8 (D2/D3) is the exact nearest neighbor: two sellers simultaneously choose adoption, the platform designs TPR/TNR, the state realizes, sellers observe analytics signals/update beliefs, and then set prices simultaneously without observing each other's price or adoption. Main p. 7 states that pre-adoption unobservability/commitment carries the open-access result; OA A.3.1, pp. 17–20, tests independent rather than common third-party signals.

**Modeling judgment changed.** The exact neighbor makes four checks mandatory for a similar model: pre-adoption observability and commitment, common versus private posteriors, simultaneous adoption/equilibrium selection, and simultaneous price deviations. A reputation-system paper is topically close but structurally different because the information recipient and endogenous seller action are consumer learning and quality investment.

**Evaluation.** Discovery: A poor, B excellent recall, C exact and explainable. Passage depth: D4 main/OA. Qualification: MATERIAL (changed nearest-neighbor set, activated checks, and narrowed the claim boundary). False positives: an unclassified duplicate of the exact PDF, price-as-quality-signal papers, and generic transparency works. Missing evidence: none for identifying the local nearest neighbor; full proof audit remains outside retrieval. Web fallback: no. Stop: exact D4 local match found; further search was unlikely to change the viable formalization or nearest-neighbor identity.

## 4. No-retrieval control

**Control.** Given `pi(p) = (p-c)(a-bp)`, with `b>0`, assess local concavity and the interior maximizer.

The router correctly skipped local and web retrieval and computed directly (verified with SymPy):

`pi'(p)=a+bc-2bp`, `pi''(p)=-2b<0`, and `p*=(a+bc)/(2b)`. Demand at that point is `(a-bc)/2`; hence a positive-demand interior solution additionally requires `a>bc` (with any other domain constraints checked separately).

Literature would be NONMATERIAL here: it would not change the algebra, domain condition or confidence. This control falsifies any policy that equates “evidence-first” with “always search.”

## 5. Cross-method findings

| Dimension | A: title/path rg | B: FTS5/BM25 | C: bounded rerank + qualification |
|---|---|---|---|
| Known paper identity | Excellent and cheap | Good | Good |
| Hidden assumption/process critique | Poor | Good recall | Good, if candidate recalled |
| Structural description | Poor | Moderate-to-good recall | Best observed precision |
| Passage/page locator | Requires on-demand extraction | Built in | Preserved and expanded when necessary |
| Main/OA/process distinction | Filename heuristics only | Explicit role field | Enforced in judgment |
| Duplicate/work collapse | Weak | Weak in raw ranking | Required |
| Claim qualification | None | None | Required |
| Failure mode | False negatives | lexical false positives/repetition | model misreading or overconfident rerank |

The test does not establish a universal recall percentage: six questions are diagnostic, not a statistically representative gold set. It does establish that A fails on precisely the evidence types the proposed Skill needs, and that B without C produces citation candidates rather than evidence-grounded judgments.

## 6. Selected retrieval design

### 6.1 Runtime flow

1. **Route.** If the task is fully specified local algebra/computation, calculate first and do not retrieve. Retrieve when literature can change formalization, an activated check, nearest neighbors, a claim boundary or uncertainty.
2. **Identity pass.** Use `rg --files`/metadata for DOI, exact title, manuscript ID and known filenames. This is retained as a fast path, not the main discovery engine.
3. **Candidate pass.** Query a persistent local FTS5 index with 2–4 structural facets, using several small query rewrites when terminology differs. Do not require every prose facet in one AND query.
4. **Work collapse.** Merge duplicate copies and group main/OA/preprint/process artifacts under `work_id`. Diversify candidates across works before returning multiple chunks from one work.
5. **Codex structural rerank.** Compare candidates on institution/players, timing, information and observability, actions, payoff/contract, equilibrium, mechanism, requested role, evidence depth and outlet/recency. Reranking is a reasoned feature comparison, not an opaque relevance score.
6. **Qualification.** Open the page/neighboring chunks. Assign role and D0–D4. Record exactly what the passage supports and what it does not. PROCESS_EVIDENCE may activate a check but cannot decide formal truth.
7. **Usefulness gate.** Cite in the modeling judgment only if the evidence changes/narrows a listed decision variable; otherwise label context/decorative or omit it.
8. **Stop or fallback.** Stop when new candidates are duplicate/weaker and cannot change formalization, conflict, assumption justification or boundary. Trigger web only for a missing current/nearest-neighbor work, official metadata/version status, or insufficient local D2–D4 coverage. A D1 web abstract never fills a D3 gap.

### 6.2 Minimum metadata

Required document/work fields: `work_id`, `artifact_id`, `role`, `title`, `authors`, printed/publication year, `journal`, `doi`, `version/status`, `source_path`, file size, modification time, parse status/error, parent/main-work link. Required chunk fields: `chunk_id`, `artifact_id`, physical PDF page (nullable for DOCX), printed page when reliably parsed (optional), section heading/path, chunk ordinal, character offsets and text.

Unknown values are explicit, not guessed. `role` and parse error are veto fields: an unlabeled duplicate or failed extraction cannot silently become qualified evidence.

### 6.3 Do we need SQLite and an independent index?

**Yes, given this corpus and task profile.** A transient index is too expensive, and direct `rg` cannot search PDFs. A rebuildable independent SQLite file is the smallest practical way to obtain repeatable full-text ranking, page locators, role filters and work joins without paid APIs. “Independent” means outside the read-only source folders and safe to delete/rebuild; it does not mean a daemon, MCP service, vector DB or permissions subsystem.

Required patch before deployment: incremental add/update/delete by file fingerprint, atomic rebuild/swap, configuration of the two allowed roots, deduplication by DOI/work+content hash, and a compact parse-error report. The index itself is cache/derived state and should not be shipped as a formal research output.

### 6.4 Codex reranking contract

Codex receives a bounded, diversified candidate set (normally 10–30 work-level candidates, not a fixed paper quota) and returns for each retained work: structural match, mismatch, role/depth, supporting passage locator, supported judgment, boundary, and exclusion reason for deceptively close candidates. It must never raise evidence depth, silently fill missing metadata, or treat BM25 order as epistemic strength.

## 7. Rejected alternatives and why

- **A alone — rejected as the default.** It is retained only for identity lookup. It failed Q1/Q2/Q5/Q6 discovery because the decisive structure lives inside model/OA/process text.
- **B alone — rejected as answer-producing retrieval.** It recalled useful passages but ranked high-frequency lexical matches, duplicates and repeated chunks from one work. It cannot distinguish process criticism from formal truth or topical similarity from institutional equivalence.
- **C over A-only candidates — rejected.** Semantic reranking cannot recover a paper that filename retrieval never recalled.
- **Paid embeddings/vector DB — deferred, not justified.** The hybrid recovered all benchmark targets without an external API. The remaining errors are mainly parsing, metadata, deduplication and model qualification; embeddings do not automatically solve them.
- **Rebuild-on-every-query — rejected.** First-pass parsing of roughly 2,000 PDFs dominated runtime and produced a 321.5 MB index. Warm retrieval is cheap; index reuse/incremental freshness is necessary.
- **One fixed natural-language query — rejected.** Q2 showed phrase/line-break/vocabulary mismatch. Query decomposition and bounded rewrites are necessary, with decision-delta stopping rather than a fixed number of searches.
- **One global relevance score — rejected.** It would conceal role/depth vetoes and the difference between passage recall and evidence usefulness.

## 8. Retrieval failure modes

1. Filename-only false negatives for assumptions, timing and reviewer criticism.
2. Exact-phrase failure from PDF line breaks, ligatures and alternate terminology.
3. High-frequency-term false positives (“common,” “timing,” “platform,” “information”).
4. Within-work repetition crowding out candidate diversity.
5. Duplicate PDFs with weak filenames outranking the canonical work.
6. Work identity leakage: main, OA and preprint treated as independent papers.
7. Physical PDF page versus printed article page mismatch.
8. Two-column extraction interleaving sentences; the prototype's `pdftotext -layout` was adequate for tested passages but not guaranteed.
9. DOCX has no stable page locator; paragraph/section locator is needed.
10. Three empty/deleted-backup PDFs produced visible parse errors; invisible skipping would create false coverage confidence.
11. FTS query syntax and Windows console encoding caused real prototype failures; UTF-8 output and stored-chunk return were added.
12. Structural reranking can still be wrong: the hardest residual risk is Codex mistaking a topical passage for a formal analogue.

## 9. Evidence qualification failures observed

- **D0/D1 inflation:** title/abstract language invited stronger claims about exact timing or assumptions than it could support. The benchmark refused that upgrade.
- **OA neglect:** Q1 and Q2 would have produced materially weaker judgments without alternative-timeline and independent-signal appendices.
- **Process/formal conflation:** Q5 reports are valuable check generators but not proofs. A decision letter repeating a reviewer concern does not transform it into a theorem.
- **Revision overclaim:** where no author response/revised model was present, the benchmark could not claim the criticism was repaired.
- **Metadata incompleteness:** the first index build left author fields empty; qualified use required front-page citation blocks. The retained script now attempts this extraction, but failures remain `UNKNOWN`.
- **Year ambiguity:** DOI year/filename prefix and printed publication year can differ. Citation output must use the printed/official year.
- **Decorative proximity:** Q3's paper supports strategic user response, but not a generic Bertrand-competition statement; using it for the latter would be decoration or mis-citation.
- **Robustness inflation:** an OA extension that preserves a “key argument” does not automatically establish unchanged thresholds, welfare claims or equilibrium completeness.

## 10. Web fallback behavior

In the private benchmark, no web fallback was necessary for Q1–Q6: each decision-relevant claim had local D2–D4 main/OA evidence, and Q5 required authorized local process evidence. This is a successful local-first result, not evidence that web is generally unnecessary. Continuing to web would have added citations without a plausible decision delta.

The trigger for web is therefore substantive, not “local search returned fewer than N papers”:

- a current MS/MKS nearest neighbor or version is absent locally;
- official title/authors/year/DOI/status require verification;
- local evidence stops at D0/D1 and the requested judgment requires D2–D4;
- local candidates conflict and a recent UTD paper may change the viable formalization or boundary.

Search official Management Science/Marketing Science sources first, then other UTD outlets when institutionally relevant. If only an official abstract is accessible, label D1 and narrow/withhold the formal judgment. More abstracts do not sum to a proof. Classic theory, mathematical methods, corrections/rejoinders and AI-method evidence remain outside the UTD-only restriction when appropriate; process evidence remains separately labeled.

## 11. Remaining unknowns

- Recall and ranking stability on a larger blind gold set, including paraphrases not sharing obvious structural words.
- Incremental update time and correctness after additions, replacements and deletions.
- Reliable author/section/printed-page extraction across older scans, non-INFORMS layouts and malformed PDFs.
- Whether `pdftotext -layout` is sufficient for formula-heavy two-column proofs, tables and scanned pages; OCR was not needed in the six tests.
- Whether a content hash plus DOI is enough to collapse duplicates without merging corrigenda or materially different versions.
- The smallest candidate budget that preserves recall under Codex context limits; no fixed N is specified by this test.
- Identity-blind evaluation of Codex structural reranking versus BM25, to detect journal/title prestige anchoring.
- D3 proof-chain retrieval across pages and references; current chunks are designed mainly for D2 mechanism retrieval.
- Robust multilingual query expansion between Chinese research descriptions and English paper text.
- Whether local embeddings add value after the above nonsemantic failures are fixed; current evidence does not justify them.

## 12. What is retrieval technology vs model judgment

Retrieval technology should own file discovery, parsing, identity/role/version linkage, candidate generation, page/chunk location, deduplication, freshness and parse-error visibility. It cannot decide whether an assumption writes the result into the model, whether two institutions are genuinely comparable, whether an equilibrium is complete, whether a proof is valid, or whether a process criticism is correct. Those remain model-judgment tasks and require explicit structural reasoning or calculation.

The benchmark's strongest result is therefore not “BM25 wins.” It is: **BM25 makes hidden local evidence reachable; Codex must then prove the evidence-to-judgment link, and the usefulness/depth gates must be allowed to reject citations.**

## 13. Readiness judgment for Skill Technical Design v0.1

**GO WITH PATCHES.** Proceed to a minimal technical design around the selected hybrid, with these gates before freezing it:

1. incremental, atomic independent index outside both source knowledge bases;
2. canonical work/OA/version/process linkage and duplicate collapse;
3. reliable citation metadata with explicit unknowns;
4. role/depth-aware candidate diversification;
5. structured Codex reranking/exclusion reasons;
6. usefulness gate and decision-delta stopping;
7. no-retrieval router for self-contained math;
8. blind benchmark expansion before considering embeddings.

Do not add MCP, a daemon, a vector database, paid APIs, a GUI or a “research workbench.” The current evidence supports one small retrieval script plus a rebuildable SQLite index and Codex-native reasoning—nothing larger yet.
