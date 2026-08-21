# Migration to v0.5.0-rc3

## 1. Repository root is the Skill

Older releases placed runtime files under `ms_mks_modeling_skill/`. The current repository root is the single installable Skill.

For current Codex local discovery, place/copy/link the Skill under an active `.agents/skills` directory with the discovery folder named exactly:

```text
ms-mks-modeling
```

For a user-level install, current Codex documentation uses:

```text
$HOME/.agents/skills/ms-mks-modeling
```

Repository-scoped installs can live under the appropriate `.agents/skills` directory from the working directory up to the repository root. Codex may expose multiple same-name Skills rather than merge them, so do not leave different workspace/user copies active unintentionally.

The GitHub repository itself may keep the repository name `ms-mks-modeling-skill`; clone it to a discovery destination named `ms-mks-modeling`, or use a symlink/junction with that name.

Run:

```bash
python scripts/skill_doctor.py
```

The doctor is read-only. It checks current user/repository discovery locations and also reports an old `$HOME/.codex/skills` copy as a **legacy migration warning**; it never deletes or retargets files automatically.

## 2. Rebuild local evidence indexes when coming from pre-v0.4 releases

The retrieval schema changed because indexed documents store explicit root roles (`PAPER` or `PROCESS`). Existing indexes are disposable derived data; rebuild them when migrating from a pre-v0.4 index.

No index-schema rebuild is required solely when moving from v0.5.0-rc1/rc2 to rc3.

## 3. Process evidence is explicit

The old hidden `MKS_PROCESS_ROOT_NAMES` environment-variable behavior is removed. Use `--paper-root` and `--process-root`. Legacy `--root` remains temporarily as a deprecated alias for `--paper-root`.

Ordinary searches exclude `PROCESS_EVIDENCE` unless `--role PROCESS_EVIDENCE` is explicitly requested.

## 4. Root configuration on incremental update

`update --db ...` reuses the root configuration stored in the index when no roots are supplied. If any `--paper-root`/`--process-root` options are supplied on update, that supplied set is treated as the complete desired root configuration; omitted roots are pruned from the derived index.

## 5. Optional hash verification

Normal `update` remains fast using path + size + modification time. Use `update --verify-hash` periodically when sync/backup/restore tools can preserve timestamps and file sizes.

## 6. PRIVACY.md is no longer a runtime file

The active local-data/web-query boundary lives in `references/retrieval_contract.md`, which the Skill loads when local/web retrieval is relevant. The old privacy document is preserved under `docs/legacy/` for design history only.

## 7. Full-workflow preservation

The v0.4/v0.5 line adds formal certification, model-level discovery, and mechanism diagnostics without deleting the original exploratory workflow. See `docs/CONTENT_PRESERVATION.md` for preserved modules.

## 8. v0.5 behavioral change: broad audits start model-first

MODEL/PAPER-WIDE audits perform a breadth-first material/model census and claim-independent solution-space discovery before proposition-focused certification. LOCAL equation/proposition tasks remain scoped and should not trigger a whole-paper census.

If you maintain `.modeling/current_model.md`, migrate only active cross-session projects by adding the Material Map, Canonical Model Map, Assumption-Leverage Map, and cross-material/cross-claim consistency sections when useful. Do not mechanically backfill retired projects.

## 9. rc2 research-integrity tightening retained

The runtime treats application-specific institution mapping and supplied code/numerical implementation as auditable layers when load-bearing. Mechanism audits may ask for a coherent negative-space benchmark, but absence of such a benchmark is a mechanism-identification limitation rather than automatic formal failure.

For A/B testing, prefer `tests/A_B_EVALUATION.md` over informal comparison of answer length or headline issues.

## 10. rc3 distribution/diagnostic update

rc3 updates GitHub-facing installation guidance to the current Codex `.agents/skills` discovery locations, makes `skill_doctor.py` mirror current user/repository discovery more closely while still flagging the old `.codex/skills` location, shortens/front-loads trigger metadata for better implicit Skill matching, and adds release tests for version synchronization and Markdown-link integrity.
