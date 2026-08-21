# MS/MKS Modeling Skill

**A critical modeling copilot for analytical and game-theoretic research.**

`ms-mks-modeling` is an evidence-grounded Agent Skill for researchers working on **Management Science / Marketing Science–style analytical models**. It helps move from a vague research idea to a tractable model, reconstruct target papers and appendices, compare candidate formalizations, solve and diagnose equilibria, pressure-test mechanisms, audit boundaries and feasibility, and keep final claims inside what the model actually supports.

The goal is not to make the model agree with the user, the paper, or the AI's first derivation. The goal is to make the **research model more defensible, interpretable, and auditable**.

> **Model-first, not proposition-first.** For broad audits, the Skill maps the research object and model architecture before locking onto author-stated propositions; for a local equation or derivation question, it stays local and avoids whole-paper bureaucracy.

## Why this Skill exists

Large language models are often good at algebra once the right equations are on the page, but analytical research can fail earlier than the algebra. Common failure modes include:

- silently solving a slightly different model from the one the paper actually specifies;
- reading the main proposition while missing a constraint, qualification, or changed assumption elsewhere;
- treating an interior first-order condition as a globally valid equilibrium;
- overlooking an empty parameter region, infeasible candidate, corner, threshold-equality case, or competing equilibrium branch;
- reproducing the author's proof path without independently asking what the model itself allows;
- attributing a result to a mechanism that is not actually carrying it;
- adding realism or extensions that make the model larger without making the research question better;
- overstating contribution or managerial implications beyond the formal domain.

This Skill is designed around those failures.

## What makes it different

### 1. End-to-end research modeling, not just equation checking

It supports the full workflow:

- **Idea orientation** — turn a phenomenon, institution, case, or vague topic into a sharper research object and minimum formalization.
- **Target-paper reconstruction** — recover the main model, timing, information, constraints, proof logic, and relevant appendix material before modifying it.
- **Model construction** — connect literature streams only when they create a real endogenous interaction rather than a topical mash-up.
- **Candidate comparison** — compare alternative games by research-object fit, assumptions, mechanism, tractability, collision risk, and decisive tests.
- **Formal solution and diagnosis** — solve, explain, repair, and validate the model without treating a candidate solution as automatically meaningful.
- **Mechanism analysis** — distinguish "the math works" from "this is why the result happens."
- **Contribution screening** — separate exemplar retrieval from broader nearest-neighbor novelty screening.
- **Feedback evaluation** — evaluate advisor, reviewer, editor, or senior-researcher proposals independently rather than accepting them by authority.

### 2. Research-model-centered auditing

For whole-model or whole-paper audits, the Skill follows a broader sequence before narrow proposition certification:

`research object -> model architecture -> material/model census -> cross-material integrity -> independent solution-space discovery -> mechanism identification -> claim certification -> research judgment`

For an existing paper or model it distinguishes:

- **source truth** — what the paper or user actually states;
- **formal truth** — what follows from the reconstructed formal system;
- **claim truth** — where the stated proposition is actually valid.

The source path is reconstructed faithfully, but the independent pass does not use the source's final formula, threshold, or qualitative sign as its target. It first asks what materially distinct solution regimes the canonical model itself permits.

### 3. Closure before strong conclusions

Before an applicable `PASS`, `UNIQUE`, `GLOBAL`, or existence conclusion, the Skill checks the relevant combination of:

- source/model specification closure;
- constraint completeness;
- parameter-domain consistency;
- feasible-set nonemptiness;
- boundary, corner, and threshold cases;
- substitution-back into defining conditions;
- omitted deviations and equilibrium branches;
- claim-domain scope;
- one targeted falsification attempt against a load-bearing node.

A correct derivative is not automatically a valid equilibrium. A valid candidate is not automatically a global claim.

### 4. Mechanism diagnosis, not just result reproduction

When mechanism interpretation is decision-relevant, the Skill can use:

- assumption-leverage mapping;
- mechanism-isolating benchmarks;
- coherent shutdown/neutralization tests;
- clearly labeled diagnostic freezes;
- minimal-model challenges;
- cross-claim and narrative-scope checks.

These are diagnostics, not journal dogma. A mechanism-freeze that changes the game is not treated as a legitimate equilibrium benchmark, and a result that survives a shutdown does not imply the mechanism has zero effect on magnitude, thresholds, welfare, or scope.

### 5. MS/MKS evidence calibration without outsourcing the mathematics

The Skill can work **without** a local knowledge base. When literature evidence matters, it distinguishes institutional precedent, primitive precedent, mechanism precedent, solution/equilibrium convention, and novelty collision.

Public MS/MKS examples in [`references/ms_mks_calibration.md`](references/ms_mks_calibration.md) are used as calibration anchors—not as universal journal rules. Stronger proof-, appendix-, or norm-level judgments should be checked against multiple structurally relevant papers, ideally through an authorized local corpus at D3/D4 depth.

## Typical ways to use it

You can give it a one-line idea:

> "Platforms are starting to disclose seller analytics to merchants. Is there a good strategic modeling question here?"

A target paper:

> "Reconstruct this paper's baseline model and appendix first. Then tell me where an extension on asymmetric analytics would actually change the strategic object."

A model draft:

> "Audit this model as a whole. Do not only check my propositions—look for missing regimes, inconsistent assumptions, or places where the mechanism is being written into the assumptions."

A specific derivation:

> "Check Proposition 2 and the threshold at which the interior solution hits the boundary. Stay local unless another part of the model is materially required."

A contribution question:

> "Compare this mechanism with the nearest MS/MKS neighbors. Separate structural precedent from actual novelty collision."

A reviewer/advisor suggestion:

> "My advisor wants endogenous participation added. Decide whether that actually fixes a structural weakness or just makes the model larger."

## How the Skill reasons

The core trace is:

`problem -> institution/primitives -> timing/information -> strategies/feasible set -> payoffs/constraints -> solution space -> mechanism -> claim/welfare/domain`

Two scope modes keep the workflow proportional to the task:

- **LOCAL** — a bounded equation, derivation, proposition, parameter region, or formal question. Only necessary dependencies are audited.
- **MODEL/PAPER-WIDE** — an overall model check, baseline redesign, "what did the paper miss?", mechanism evaluation, contribution assessment, or completeness audit. The Skill first builds a breadth-first material/model map and cross-material consistency view.

Detailed runtime logic lives in [`SKILL.md`](SKILL.md) and [`references/modeling_and_validation.md`](references/modeling_and_validation.md).

## Install for local Codex use

The package follows the [Agent Skills specification](https://agentskills.io/specification). Current Codex documentation loads user-level local skills from `$HOME/.agents/skills` and repository-scoped skills from `.agents/skills` directories. The discovery folder must match the frontmatter name: **`ms-mks-modeling`**.

### macOS / Linux

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/Simpleananan/ms-mks-modeling-skill.git ~/.agents/skills/ms-mks-modeling
```

### Windows PowerShell

```powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
git clone https://github.com/Simpleananan/ms-mks-modeling-skill.git "$HOME\.agents\skills\ms-mks-modeling"
```

If you keep the GitHub checkout somewhere else, point a symlink/junction named `ms-mks-modeling` from an active `.agents/skills` directory to the repository root. Codex supports symlinked Skill directories.

You can also ask Codex's built-in `$skill-installer` to install a Skill from a GitHub repository. If an update does not appear immediately, restart Codex.

After installation, invoke it explicitly with `$ms-mks-modeling` (or choose it from `/skills`), or let Codex invoke it implicitly when the task matches the Skill description.

If you upgraded from an older release or previously had both workspace and user-level copies, run:

```bash
python scripts/skill_doctor.py
```

The doctor is read-only: it reports current and legacy discovery locations and duplicate `ms-mks-modeling` installs; it never deletes or retargets files. See [`MIGRATION.md`](MIGRATION.md).

> Current OpenAI guidance treats direct Skill folders as appropriate for local/repository use and recommends Plugins for broader installable distribution. This repository remains a standalone GitHub Skill for local Codex research workflows.

## Optional local MS/MKS evidence retrieval

A local corpus is **not required**. If you have an authorized paper library, the bundled script can build a disposable SQLite FTS5 index while keeping source files read-only.

```bash
python scripts/local_evidence_retrieval.py build \
  --db /path/outside/the/corpus/evidence.sqlite \
  --paper-root /path/to/papers \
  --process-root /path/to/review-response-materials
```

Later updates can reuse the stored root configuration:

```bash
python scripts/local_evidence_retrieval.py update \
  --db /path/outside/the/corpus/evidence.sqlite
```

If sync/backup software may preserve both modification time and file size, periodically add `--verify-hash`.

Published/formal evidence and reviewer/editor/author-response materials are separated. Ordinary search excludes `PROCESS_EVIDENCE` by default; process materials are searched only when explicitly requested. `pdftotext` is needed for PDF extraction; DOCX extraction uses the Python standard library.

The full retrieval/data-flow contract is in [`references/retrieval_contract.md`](references/retrieval_contract.md).

## Local-data boundary

The Skill does not require uploading a private corpus to a hosted service. Runtime retrieval rules require that:

- local sources are supplied or authorized by the user;
- source roots remain read-only and derived indexes stay outside them;
- process evidence stays separate from published/formal evidence;
- private local text, nonpublic manuscript IDs, private filenames, and local paths are not copied into public web-search queries;
- public fallback uses public bibliographic metadata or de-identified structural queries.

The old standalone privacy document is kept only as historical design material under `docs/legacy/`; the active rules live in the runtime retrieval contract.

## What it does **not** promise

This is a research-assistance workflow, not a correctness oracle. It does **not** promise:

- automatic theorem proving;
- complete enumeration of every equilibrium in arbitrarily complex games;
- novelty or publication readiness from a few retrieved papers;
- correctness merely because an author, reviewer, or published paper states something;
- that a numerical grid proves a global theorem;
- that every diagnostic device in the Skill is a universal MS/MKS journal norm.

The intended gain is better research discipline: broader defect discovery when the task is broad, tighter scope when the task is local, clearer mechanism attribution, and fewer unsupported global conclusions.

## Validation and research-use tests

Automated package checks:

```bash
python -m unittest discover -s tests -v
python scripts/release_safety_scan.py .
python scripts/release_safety_scan.py . --strict-personal
```

Behavioral cases are in [`tests/BEHAVIORAL_ACCEPTANCE.md`](tests/BEHAVIORAL_ACCEPTANCE.md). The paired Skill-vs-no-Skill protocol in [`tests/A_B_EVALUATION.md`](tests/A_B_EVALUATION.md) scores material defect discovery, independent discovery gain, false positives, source attribution, scope calibration, mechanism diagnosis, research-design value, and local-task overhead separately.

Before packaging a release:

```bash
python scripts/rebuild_manifest.py
sha256sum -c MANIFEST.sha256
```

Windows junction/reparse-point protection is implemented and platform-conditionally tested; the RC label should remain until it has also been smoke-tested on the actual Windows setup and the behavioral/A-B suite has been exercised on real modeling cases.

## Repository map

```text
SKILL.md                         # runtime entry point
references/
  modeling_and_validation.md    # research-model workflow + formal certification
  evidence_policy.md            # evidence depth, literature roles, novelty screening
  retrieval_contract.md         # local retrieval and data-flow boundaries
  feedback_and_decisions.md     # advisor/reviewer/stakeholder proposal handling
  ms_mks_calibration.md         # public MS/MKS calibration anchors
scripts/
  local_evidence_retrieval.py   # optional local PDF/DOCX index
  skill_doctor.py               # duplicate/install-location diagnostics
  release_safety_scan.py        # release secret/personal-data scan
  rebuild_manifest.py           # deterministic package manifest
  privacy_scan.py               # deprecated compatibility wrapper
templates/
  current_model.md              # optional cross-session research state
tests/
  test_local_evidence_retrieval.py
  test_package_structure.py
  BEHAVIORAL_ACCEPTANCE.md
  A_B_EVALUATION.md
docs/
  DESIGN_v0.5.md
  LOCAL_KB_VERIFICATION.md
  CONTENT_PRESERVATION.md
  legacy/                       # preserved historical design assets
```

## Release status

Current package: **`v0.5.0-rc3`**.

This release candidate keeps the v0.5 research-model-centered architecture while tightening current Codex installation guidance, Skill discovery diagnostics, trigger metadata, package validation, and the public README. See [`CHANGELOG.md`](CHANGELOG.md) for the full change history and [`docs/RELEASE_VALIDATION.md`](docs/RELEASE_VALIDATION.md) for the release audit.

## License

See [`LICENSE`](LICENSE). The bundled research-use license permits GitHub download/clone, installation, execution by AI research/coding agents, and local modification for personal, academic, educational, and internal research use. It is **source-available**, not an OSI open-source license.
