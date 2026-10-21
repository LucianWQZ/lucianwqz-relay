# P8-E Freeze Reproducibility Report

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

## 1. Range and expected identity

```text
base SHA   841dc6ccdb134eab7ad09008859834d0572ee83f
final SHA  4753742ab181920292c504a79eedecf9b428ae1b
final tree b7e525c3c9d45617ad1023ad45c6948c466a3631
commits    16, linear
```

The source vLLM-Ascend checkout is shallow. An attempt to fetch the omitted history
from GitHub could not connect to port 443 in this execution environment. Therefore
the bundle is intentionally incremental and declares the exact base as a
prerequisite; this limitation is part of the artifact contract.

## 2. Binary-safe full diff

Artifact: `MRV2_P0_P7_Full_Diff.patch`.

Verification performed on a fresh clean checkout at the exact base:

1. `git apply --check` passed.
2. The patch was applied to a second clean baseline checkout.
3. Files were staged and `git write-tree` returned
   `b7e525c3c9d45617ad1023ad45c6948c466a3631`.

This is an emergency tree recovery path. It does not retain commit metadata.

## 3. Format-patch series

Artifact directory: `format-patches/`, containing 16 ordered binary-safe patches.

Verification performed:

1. clean checkout at `841dc6cc...`;
2. `git am` of the complete series in lexical order;
3. clean resulting working tree;
4. resulting tree exactly
   `b7e525c3c9d45617ad1023ad45c6948c466a3631`.

The recreated commit IDs may differ when committer metadata differs. Tree identity,
patch order, authorship and commit messages are retained.

## 4. Incremental Git bundle

Artifact: `MRV2_P0_P7.bundle`.

The bundle was created for `feature/p7-eager-completion` while excluding exact base
`841dc6cc...`; the base is therefore an explicit prerequisite.

Verification performed:

1. `git bundle verify MRV2_P0_P7.bundle` passed and reported the prerequisite.
2. A clean baseline repository fetched the branch from the bundle.
3. The fetched branch resolved to exact final SHA `4753742...`.
4. Its tree resolved to exact final tree `b7e525c...`.
5. The restored working tree was clean.

Recovery command:

```bash
git checkout 841dc6ccdb134eab7ad09008859834d0572ee83f
git fetch /path/to/MRV2_P0_P7.bundle \
  refs/heads/feature/p7-eager-completion:refs/heads/restored-p7
git checkout restored-p7
test "$(git rev-parse HEAD)" = \
  4753742ab181920292c504a79eedecf9b428ae1b
test "$(git rev-parse HEAD^{tree})" = \
  b7e525c3c9d45617ad1023ad45c6948c466a3631
```

Direct `git clone MRV2_P0_P7.bundle` is not a supported recovery path for this
incremental artifact.

## 5. Integrity

`SHA256SUMS` covers every packaged regular file except itself and is verified after
the package is finalized. Any subsequent edit requires regeneration and
re-verification.

## 6. Post-independent-review regeneration

After review adjudication, the binary-safe full diff, all 16 format patches and the
incremental bundle were regenerated from the unchanged final production source.
Fresh temporary repositories repeated full-diff `git apply --check`/`write-tree`,
complete `git am`, and prerequisite-aware bundle fetch. Every route recovered tree
`b7e525c3c9d45617ad1023ad45c6948c466a3631`; format-patch and bundle restored
working trees were clean. The command-level record is
`P8_Eager_Cleanroom_Restore_Report.md`.

The independent review, adjudication corrections and clean-room report are included
in the final package and covered by the regenerated checksum index. Production
HEAD/tree and the 16-commit lineage did not change.

```text
FULL DIFF RESTORE: PASS
FORMAT-PATCH RESTORE: PASS
INCREMENTAL BUNDLE RESTORE: PASS WITH EXACT-BASE PREREQUISITE
FINAL TREE EQUALITY: PASS
POST-REVIEW ARTIFACT REGENERATION: PASS
```
