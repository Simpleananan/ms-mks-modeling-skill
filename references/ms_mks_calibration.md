# MS/MKS calibration anchors

Public-source verification date: **2026-08-21**.

This file calibrates the Skill against public examples from **Management Science** and **Marketing Science**. These are **exemplars, not universal journal rules**. Public abstract/article-page evidence supports only the structural observations stated below. Exact threshold algebra, proof completeness, boundary coverage, or appendix-specific claims require D3/D4 inspection of the full article and relevant supplemental material—preferably through the user's authorized local knowledge base.

## Publicly verified calibration anchors

### Liu & Long — *Data and Algorithms: Strategic Disclosure of Competitiveness on Platforms Through Marketplace Analytics*

Marketing Science 45(3):653–674; published online 2025; DOI `10.1287/mksc.2024.0960`.

The official article page states that the platform jointly chooses a data-access policy and algorithm design in a marketplace-analytics setting, that sellers respond to the platform's analytics/adoption environment, and that the results vary with competition conditions. The page also links online appendices. This supports treating data access, information design, seller response, and competition regime as jointly strategic rather than evaluating one object mechanically in isolation.

**Local-KB D3/D4 targets:** inspect the exact equilibrium construction, seller adoption/deviation conditions, all parameter-region inequalities, boundary/equality cases, and observability/signal robustness extensions. In particular, test whether any conjunction of reported regime conditions is empty rather than assuming nonemptiness.

### Zha, Li, Huang & Yu — *Strategic Information Sharing of Online Platforms as Resellers or Marketplaces*

Marketing Science 42(4):659–678; DOI `10.1287/mksc.2022.1397`.

The official abstract distinguishes reseller and marketplace selling structures and reports that optimal information sharing depends on the selling format, competition, and—under the marketplace format—forecasting accuracy. This supports institution-specific case analysis and parameter/regime scoping rather than transferring one equilibrium characterization across formally different channel structures.

**Local-KB D3/D4 targets:** inspect the online appendix for threshold definitions, backward-induction case splits, feasibility conditions (including quantity/demand restrictions), threshold equality treatment, and coverage of all claimed regions.

### Shi, Srinivasan & Zhang — *Design of Platform Reputation Systems: Optimal Information Disclosure*

Marketing Science 42(3):500–520; DOI `10.1287/mksc.2022.1392`.

The official abstract describes a three-player game in which sellers choose quality investment, the platform chooses how much rating information to disclose, and Bayesian consumers make purchase decisions. It identifies both a seller-investment effect and a sales effect. This supports tracing a disclosure claim through endogenous responses of multiple strategic actors rather than treating disclosure as a one-player comparative static.

### Wang, Huang, Jasin & Singh — *Algorithmic Transparency with Strategic Users*

Management Science 69(4):2297–2317; DOI `10.1287/mnsc.2022.4475`.

The official abstract explicitly models strategic users under algorithmic transparency and states results under identified conditions, including cases where transparency can benefit the firm and cases where users are not necessarily better off. This supports making strategic response and claim conditions explicit instead of assuming monotone effects of more transparency.

### Liu, Lou, Zhao & Li — *Unintended Consequences of Advances in Matching Technologies: Information Revelation and Strategic Participation on Gig-Economy Platforms*

Management Science 70(3):1729–1754; DOI `10.1287/mnsc.2023.4770`.

The official abstract separates a direct matching-enhancement effect from an indirect information-revelation/worker-participation effect and studies several extensions. This supports mechanism decomposition and tracing a technological change through endogenous participation rather than extrapolating from the direct effect alone.

### Kulkarni & Kalkanci — *Spatial Information Sharing on On-Demand Service Platforms*

Management Science, published online 2026; DOI `10.1287/mnsc.2021.03426`.

The official abstract reports both game-theoretic predictions and laboratory evidence, and states that a behavioral equilibrium describes experimental behavior better than the rational equilibrium. This supports tying a conclusion to the actual solution/behavioral concept used and avoiding silent transfer between equilibrium concepts.


## v0.5 research-design calibration

The public anchors above support a cautious shift from proposition-only checking toward model- and mechanism-level analysis, but only at the level actually visible in official article/abstract pages:

- Liu & Long explicitly frame data-access policy and algorithm design as **intertwined decisions**, supporting analysis of endogenous interaction among model objects rather than evaluating one policy variable in isolation.
- Zha et al. explicitly compare different selling structures and report different information-sharing implications across those structures, supporting institution/regime-specific modeling rather than silent transfer of one solution across different games.
- Shi et al. explicitly model seller investment, platform disclosure, and Bayesian consumer response, supporting multi-actor strategic-response tracing.
- Liu et al. explicitly separate a direct matching-enhancement effect from an information-revelation/participation effect, supporting mechanism decomposition rather than attributing the net result to the direct technological effect alone.
- Kulkarni & Kalkanci explicitly distinguish rational-equilibrium predictions from a behavioral-equilibrium account of observed behavior, supporting solution-concept-specific claim scope.

These examples do **not** establish that MS/MKS universally requires a minimal-model challenge, mechanism-shutdown test, breadth-first paper census, or any fixed audit order. In v0.5 those are research-assistant diagnostics designed to improve model discovery and attribution. Treat them as hypotheses about good analytical-modeling practice until the user's local corpus shows recurring use or close analogues.

### Local-KB tests added for v0.5

Use D3/D4 inspection of multiple structurally close MS/MKS papers to test whether and how strong papers actually:

1. isolate a claimed mechanism with benchmarks, decompositions, comparative statics, or extensions that shut down a strategic force;
2. distinguish load-bearing assumptions from tractability assumptions;
3. use smaller benchmark models before adding institutional richness;
4. maintain timing, information, domains, and equilibrium concepts consistently between main text and appendices;
5. keep narrative/managerial claims within the formal proposition domain;
6. separate robustness that pressure-tests a mechanism from extensions that create a new research object.

Record counterexamples. If strong papers routinely support a practice by a different device than the Skill expects, generalize the Skill to the underlying research function rather than enforcing one proof/exposition format.

## What these anchors do not establish

They do not prove that every MS/MKS paper must follow one proof order, use one equilibrium concept, or run every closure check. The activation rule is structural: use a check when the current model and claim contain the corresponding object.

They also do not establish a universal 'MS/MKS norm' from one exemplar. Strong norm claims require multiple recent, structurally relevant papers plus any necessary classic theory. Record contrary exemplars rather than forcing consensus.

## Local knowledge-base verification protocol

Use the user's local corpus to test the Skill itself, not merely to find supportive examples. For each proposed norm or gate:

1. retrieve several structurally close MS/MKS papers;
2. inspect main text plus relevant appendix/proof at D3/D4 depth;
3. record positive, contrastive, and counterexamples;
4. distinguish a recurring practice from a mathematically necessary condition;
5. revise the Skill if a rule is overgeneralized, under-specified, or journal-inappropriate.
