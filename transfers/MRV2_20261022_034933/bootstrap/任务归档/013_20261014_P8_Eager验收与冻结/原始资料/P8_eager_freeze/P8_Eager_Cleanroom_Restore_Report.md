# P8-E Clean-room Restore Report

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

## 1. Purpose and identity

This report records the post-independent-review regeneration and clean-room
verification of the P8-E local delivery package. It is source-transport evidence,
not NPU/runtime/performance evidence.

```text
base SHA     841dc6ccdb134eab7ad09008859834d0572ee83f
final SHA    4753742ab181920292c504a79eedecf9b428ae1b
final tree   b7e525c3c9d45617ad1023ad45c6948c466a3631
commit count 16
```

The verification root was a newly created temporary directory:
`/private/tmp/mrv2_p8_cleanroom.YolOUu`. None of its repositories reused the
production working tree or index. The source checkout is shallow, so the Git bundle
is intentionally incremental and requires exact base `841dc6cc...`.

## 2. Production source audit

| Repository | HEAD | Tree | Status |
|---|---|---|---|
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` | clean, zero diff |
| vLLM-Ascend | `4753742ab181920292c504a79eedecf9b428ae1b` | `b7e525c3c9d45617ad1023ad45c6948c466a3631` | clean, zero diff |

`git write-tree` in each source repository returned the tree shown above. No P8
production commit or working-tree edit was made.

## 3. Binary-safe full-diff restoration

Procedure:

1. create a new non-hardlinked local clone;
2. detach at exact base `841dc6cc...`;
3. run `git apply --check MRV2_P0_P7_Full_Diff.patch`;
4. apply the patch, stage every path, and run `git write-tree`;
5. run `git diff --cached --check`.

Result:

```text
git apply --check  PASS
diff-check         PASS
restored tree      b7e525c3c9d45617ad1023ad45c6948c466a3631
tree equality      PASS
```

This is an emergency tree-only recovery path and does not preserve commit history.

## 4. Format-patch restoration

Procedure:

1. create a second new non-hardlinked clone and branch from exact base;
2. apply all 16 regenerated binary-safe patches in lexical order with `git am`;
3. verify commit count, clean status and final tree;
4. compare the restored working tree with production final.

Result:

```text
patches applied    16/16
working tree       clean
restored tree      b7e525c3c9d45617ad1023ad45c6948c466a3631
tree equality      PASS
content diff       empty
```

Authorship, subjects and order are preserved. Recreated commit IDs may differ when
committer metadata differs; exact final tree is the recovery invariant.

## 5. Incremental-bundle restoration

Procedure:

1. initialize a third empty repository;
2. fetch only exact base with `--depth=1` into `refs/heads/base`;
3. verify the regenerated bundle;
4. fetch its `feature/p7-eager-completion` ref as `restored-p7`;
5. checkout, verify SHA/tree/status and count commits above base.

Result:

```text
bundle verify      PASS
declared base      841dc6ccdb134eab7ad09008859834d0572ee83f
restored HEAD      4753742ab181920292c504a79eedecf9b428ae1b
restored tree      b7e525c3c9d45617ad1023ad45c6948c466a3631
commits above base 16
working tree       clean
content diff       empty
```

Direct standalone clone from this incremental bundle is not supported. A repository
containing the exact prerequisite base is mandatory.

## 6. Final package integrity

After all document and artifact regeneration, `SHA256SUMS` is generated over every
regular packaged file except `SHA256SUMS` itself. The final verification command is:

```bash
cd /Users/wenqingzhang/Desktop/Note/MRV2/P8_eager_freeze
shasum -a 256 -c SHA256SUMS
```

The final copy is accepted only if every entry reports `OK` and both production
repositories remain at the exact clean identities in §2.

## 7. Evidence boundary

This report proves:

- exact source-tree reconstruction;
- ordered patch and incremental-bundle recovery;
- package integrity and source-boundary preservation.

It does not prove:

- NPU physical read sets;
- Target logits equality on device;
- stream/event lifetime;
- multi-request or mixed-serving safety;
- performance;
- Graph capture or replay correctness.

```text
FULL DIFF RESTORE: PASS
FORMAT-PATCH RESTORE: PASS
INCREMENTAL BUNDLE RESTORE: PASS WITH EXACT-BASE PREREQUISITE
FINAL TREE EQUALITY: PASS
P8 PRODUCTION SHA/TREE: UNCHANGED
```
