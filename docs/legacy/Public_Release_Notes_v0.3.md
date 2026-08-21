# Public Release Notes v0.3

This release keeps the original modeling and evidence-qualification logic while changing the distribution boundary.

## Functional change

Retrieval now has an explicit evidence-source gate:

1. reuse papers/review-response materials already supplied in the task;
2. otherwise, when retrieval is needed, ask once whether the user wants to combine authorized local knowledge bases with web search;
3. run HYBRID when local sources are authorized;
4. run WEB_ONLY when local sources are unavailable/declined;
5. run LOCAL_ONLY only when web use is explicitly prohibited.

The absence of a local corpus no longer blocks literature-backed modeling. The presence of a local corpus strengthens retrieval but does not change evidence qualification: reviewer/editor/response materials remain process evidence and must be independently checked.

## Privacy change

The public package removes direct local paths and private submission identifiers. Private review-process benchmark examples are replaced by synthetic, structure-preserving cases that activate the same timing, observability, stage-consistency, and commitment/verifiability checks.

The local retrieval script now classifies source roots explicitly with `--paper-root` and `--process-root`; it no longer depends on a private folder name to infer evidence role.
