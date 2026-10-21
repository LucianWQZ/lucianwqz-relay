# P4 GitHub Clean-room Deployment Audit

> Audit date: 2026-10-12 (Asia/Shanghai)  
> Scope: GitHub-only source recovery, exact-tree comparison, local import/static/CPU validation readiness  
> Production changes made by this audit: none  
> Final verdict: **DEPLOYMENT READINESS: BLOCKED**

## 1. Executive conclusion

The local P0→P4b implementation is fully committed and its current worktree is clean, but the final vLLM-Ascend branch has **not been published to the configured GitHub `origin`**.

The target remote currently advertises only:

```text
841dc6ccdb134eab7ad09008859834d0572ee83f  refs/heads/lucian-dev
```

It does not advertise `refs/heads/feature/p4b-eagle3-static-k`, and a fetch-by-SHA from a fresh GitHub clone fails with:

```text
fatal: remote error: upload-pack: not our ref 1011e2c2fa99729a46efde5b5bbaf6daed975a2c
```

All ten delivery commits are absent from the fresh clone object database. Therefore a machine with GitHub as its only source cannot check out the Final tree, import the new modules, compile that Final source, or run the requested Final regression suites. Freeze artifacts remain valid and independently recoverable, but using them would violate this audit's GitHub-only premise.

## 2. Frozen identities

| Repository | Required commit | Required tree |
|---|---|---|
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |
| vLLM-Ascend Final | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` | `7d165d585755766e7493e02f0281598e4aca3602` |
| vLLM-Ascend feature baseline | `841dc6ccdb134eab7ad09008859834d0572ee83f` | `19693c4a2d634ad190c0703f77364e9bf2481a47` |

## 3. Current source audit

### 3.1 Current vLLM-Ascend

```text
repository: /Users/wenqingzhang/Desktop/vllm/vllm-ascend
origin:     https://github.com/LucianWQZ/vllm-ascend.git
upstream:   https://github.com/vllm-project/vllm-ascend.git
branch:     feature/p4b-eagle3-static-k
upstream tracking branch: none
HEAD:       1011e2c2fa99729a46efde5b5bbaf6daed975a2c
tree:       7d165d585755766e7493e02f0281598e4aca3602
status:     clean
stash list: empty
attached worktrees: only the current production worktree
```

Current graph:

```text
* 1011e2c fix(spec-decode): address P4b Eagle3 window review findings
* d0c8883 feat(spec-decode): integrate MRV2 draft windows for Eagle3 eager
* 4c1f691 fix(spec-decode): address P4a Ascend-only review findings
* 0dd83e9 feat(spec-decode): integrate MRV2 draft windows in Ascend eager path
* 1672788 fix(spec-decode): address P3 draft-window review findings
* feab28f feat(spec-decode): add MRV2 draft-window runtime ownership
* fac8412 fix(spec-decode): address P2 draft-window review findings
* 8357967 feat(spec-decode): add MRV2 draft-window source inventory
* c58daea fix(spec-decode): address P1 draft-window review findings
* b12399a feat(spec-decode): add MRV2 draft-window policy and math
* 841dc6c feature baseline
```

This proves the local implementation is committed rather than stored only in the worktree, stash, or untracked files. It does not prove publication to GitHub.

### 3.2 Current vLLM

```text
repository: /Users/wenqingzhang/Desktop/vllm/vllm
origin:     https://github.com/LucianWQZ/vllm.git
upstream:   https://github.com/vllm-project/vllm.git
branch:     lucian-dev
HEAD:       84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree:       f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
status:     clean
prototype symbol DraftAttentionReadInputs: absent
```

## 4. GitHub remote audit

### 4.1 vLLM-Ascend target remote

Command:

```bash
git ls-remote --heads origin \
  refs/heads/feature/p4b-eagle3-static-k \
  refs/heads/feature/p4a-ascend-only \
  refs/heads/lucian-dev
```

Observed output:

```text
841dc6ccdb134eab7ad09008859834d0572ee83f  refs/heads/lucian-dev
```

Findings:

- `feature/p4b-eagle3-static-k`: absent.
- `feature/p4a-ascend-only`: absent.
- `lucian-dev`: still at feature baseline `841dc6cc…`.
- Full advertised heads/tags contain no Final SHA.
- Explicit `refs/pull/*/{head,merge}` search contains none of the ten delivery SHAs.
- Fetching Final SHA directly returns `upload-pack: not our ref`.

The local Final branch has no configured upstream tracking ref, which is consistent with it never having been published.

### 4.2 Delivery-object availability in a fresh clone

Each delivery SHA was queried with `git cat-file --batch-check` in the new GitHub clone:

```text
b12399ad915415ce45105df5b0601848e7b70f6f missing
c58daea0df34d1a6253dc34221d2a084b13affd5 missing
83579675a997a44b293ff0ee1cb088a2eef0ed13 missing
fac84121ddf84fe5a76cd739432cea3b61365a9b missing
feab28f573b973a6b970cef56d1baa35191ab319 missing
16727882744c935d9e899f7775353b57738852bc missing
0dd83e9f75d4b2d766126af3a7f92352e342f756 missing
4c1f69146915f4f0ae5a6a61371ebfe181237d8f missing
d0c8883816f0e1fe333dc9f3197d3c4e47c475a5 missing
1011e2c2fa99729a46efde5b5bbaf6daed975a2c missing
```

This is the exact deployment blocker.

### 4.3 vLLM target remote

Command:

```bash
git ls-remote --heads origin refs/heads/lucian-dev
```

Observed output:

```text
84030bbe3d74d99bad477a3d2e37a973ccd8865c  refs/heads/lucian-dev
```

The exact required vLLM baseline is available from GitHub.

## 5. Clean-room clone

The audit created a new root using `mktemp`; it did not reuse either current `.git`, current source tree, worktree, build cache, bundle, or patch:

```text
/private/tmp/mrv2-github-cleanroom.g80G5o/
```

Commands:

```bash
git clone --branch lucian-dev --single-branch --no-tags \
  https://github.com/LucianWQZ/vllm-ascend.git \
  /private/tmp/mrv2-github-cleanroom.g80G5o/vllm-ascend

git clone --branch lucian-dev --single-branch --no-tags \
  https://github.com/LucianWQZ/vllm.git \
  /private/tmp/mrv2-github-cleanroom.g80G5o/vllm
```

Both clones completed successfully over GitHub.

### 5.1 Clean vLLM-Ascend clone result

```text
branch: lucian-dev
HEAD:   841dc6ccdb134eab7ad09008859834d0572ee83f
tree:   19693c4a2d634ad190c0703f77364e9bf2481a47
status: clean
```

Attempted Final checkout prerequisite:

```bash
git fetch origin 1011e2c2fa99729a46efde5b5bbaf6daed975a2c
```

Result: exit 128, `upload-pack: not our ref`. No Final checkout was possible.

The clean clone contains none of the new `draft_window*.py` modules or their tests because it is exactly the pre-feature baseline.

### 5.2 Clean vLLM clone result

```text
branch: lucian-dev
HEAD:   84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree:   f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
status: clean
DraftAttentionReadInputs search: no matches
```

The required unmodified vLLM source is reproducibly available from GitHub.

## 6. Tree identity

| Side | Commit | Tree | Result |
|---|---|---|---|
| Current local Final | `1011e2c…` | `7d165d585755766e7493e02f0281598e4aca3602` | expected Final |
| GitHub clean clone advertised branch | `841dc6c…` | `19693c4a2d634ad190c0703f77364e9bf2481a47` | feature baseline only |
| GitHub clean clone Final | unavailable | unavailable | **BLOCKED: commit not on remote** |

Tree identity cannot pass because GitHub cannot supply the Final commit. This is not caused by an untracked file or a tree mismatch inside the Final commit: the entire ten-commit lineage is unpublished.

## 7. Import, compile, and static checks

Required Final modules:

- `draft_window`
- `draft_window_eager`
- `draft_window_eagle3`
- DFlash speculator
- DSpark speculator
- AR/Eagle3 speculator
- `attn_utils`
- `attention_v1`

Status: **NOT RUN — BLOCKED BEFORE CHECKOUT**.

Running these checks against the GitHub baseline would test the wrong source and could create a false PASS. The three new Draft Window modules are absent from that baseline. The vLLM prototype-symbol guard was run and passed, but it cannot substitute for Final vLLM-Ascend import/compile evidence.

Commands to run after the Final branch is published and freshly cloned:

```bash
python -m compileall -q \
  vllm_ascend/worker/v2/spec_decode \
  vllm_ascend/worker/v2/attn_utils.py \
  vllm_ascend/attention/attention_v1.py

ruff check <P0-P4b changed Python files>
ruff format --check <P0-P4b changed Python files>
```

The import command must import every module listed above from the clean clone with the independently cloned vLLM baseline on its Python path.

## 8. Targeted regression status

| Requested scope | Clean-room result | Reason |
|---|---|---|
| P1 policy/math/types | NOT RUN | Final source/tests unavailable from GitHub |
| P2 inventory/FullSource/provider | NOT RUN | same blocker |
| P3 runtime/lifetime/store | NOT RUN | same blocker |
| P4a eager | NOT RUN | same blocker |
| P4b Eagle3 | NOT RUN | same blocker |
| DFlash/DSpark/DFlash2 | NOT RUN | same blocker |
| `attn_utils` | NOT RUN | same blocker |
| `attention_v1` | NOT RUN | same blocker |
| Full locally runnable `spec_decode` | NOT RUN | same blocker |

No VWN or other host-environment failure was classified as PASS. No regression result from the current worktree or prior Freeze notes was reused as clean-room evidence.

After publication, the minimum rerun set is:

```bash
pytest -q tests/ut/spec_decode/test_draft_window.py
pytest -q tests/ut/spec_decode/test_draft_window_runtime.py
pytest -q tests/ut/spec_decode/test_draft_window_eager.py
pytest -q tests/ut/spec_decode/test_draft_window_eagle3.py
pytest -q tests/ut/spec_decode/test_dflash2_v2.py
pytest -q tests/ut/worker/test_attn_utils_v2.py
pytest -q tests/ut/attention/test_attention_v1.py
pytest -q tests/ut/spec_decode
```

Any known VWN host failure must again be reported as an environment failure, not a PASS.

## 9. Freeze artifact cross-check

The existing Freeze package was inspected separately from the GitHub-only recovery decision.

### 9.1 Integrity

`shasum -a 256 -c SHA256SUMS` passed for every file listed in the original Freeze manifest. The later audit report itself is a post-Freeze record and is intentionally not part of the original checksum set.

### 9.2 Full Diff

- Manifested base: `841dc6ccdb134eab7ad09008859834d0572ee83f`.
- Manifested head: `1011e2c2fa99729a46efde5b5bbaf6daed975a2c`.
- `git apply --check` passed against the fresh GitHub baseline clone.
- Patch covers the expected 18 files.

### 9.3 Commit Manifest and format-patches

- Commit Manifest records the exact baseline, Final SHA, and Final tree.
- Ten binary format patches are present.
- Their `From` headers match the exact ten delivery SHAs in lineage order.

### 9.4 Git Bundle

The bundle verifies successfully and contains:

```text
1011e2c2fa99729a46efde5b5bbaf6daed975a2c refs/heads/feature/p4b-eagle3-static-k
```

It explicitly requires baseline `841dc6cc…`, as documented for the shallow source repository.

These results prove that the Freeze package can recover the Final implementation. They do **not** prove GitHub-only deployment because the task explicitly forbids relying on external patches or bundles for that verdict.

## 10. Exact blocker and required corrective action

### Blocker owner

Repository owner / developer with push authority to:

```text
https://github.com/LucianWQZ/vllm-ascend.git
```

### Required state change

Publish the exact local branch tip, preserving its ten-commit ancestry, for example:

```bash
git -C /Users/wenqingzhang/Desktop/vllm/vllm-ascend \
  push --set-upstream origin \
  feature/p4b-eagle3-static-k:feature/p4b-eagle3-static-k
```

This audit did **not** run that command because the request authorized verification, not publication.

After pushing, repeat:

1. `git ls-remote` and confirm the branch ref equals `1011e2c…`.
2. Delete/create a new clean-room directory.
3. Clone the feature branch solely from GitHub.
4. Confirm Final HEAD/tree and clean status.
5. Clone/check out exact vLLM baseline.
6. Run imports, compileall, static checks, and the requested regression suites.
7. Record real failures without converting environment failures into PASS.

## 11. Limitations of a future PASS

Even after the branch is published and all clean-room CPU/static checks pass, that would prove only:

- GitHub source transport;
- exact commit/tree restoration;
- module import and compilation;
- local static and CPU contracts.

It would still not prove:

- NPU runtime correctness;
- actual Draft Attention physical read-set;
- stream/event lifetime behavior;
- Draft/Target logits equivalence;
- D2H or end-to-end performance.

`G-GQA-EAGER`, `G-AR-STEP`, and Feature release therefore remain unchanged.

## 12. Final verdict

### `DEPLOYMENT READINESS: BLOCKED`

Exact blocker: GitHub `origin` does not contain or advertise `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` or any of the ten delivery commits. A new GitHub-only environment can recover only baseline `841dc6cc…`, so Final tree identity, imports, compilation, static checks, and CPU regressions cannot be executed under the required premise.

# Post-Publish Revalidation

> Revalidation date: 2026-10-12 15:10 CST (Asia/Shanghai)  
> Scope: publish the frozen branch without rewriting history, then repeat GitHub-only clean-source recovery and locally executable validation  
> Production/test source changes made by this revalidation: none  
> This section supersedes only the deployment verdict above. The original BLOCKED result is intentionally retained as the pre-publication historical record.

## 1. Pre-push identity and lineage gate

The delivery worktree was audited before the push:

```text
repository: /Users/wenqingzhang/Desktop/vllm/vllm-ascend
branch:     feature/p4b-eagle3-static-k
HEAD:       1011e2c2fa99729a46efde5b5bbaf6daed975a2c
tree:       7d165d585755766e7493e02f0281598e4aca3602
status:     clean
origin:     https://github.com/LucianWQZ/vllm-ascend.git
```

`git merge-base --is-ancestor <commit> 1011e2c2...` succeeded for all ten frozen delivery commits, in order:

```text
b12399ad915415ce45105df5b0601848e7b70f6f
c58daea0df34d1a6253dc34221d2a084b13affd5
83579675a997a44b293ff0ee1cb088a2eef0ed13
fac84121ddf84fe5a76cd739432cea3b61365a9b
feab28f573b973a6b970cef56d1baa35191ab319
16727882744c935d9e899f7775353b57738852bc
0dd83e9f75d4b2d766126af3a7f92352e342f756
4c1f69146915f4f0ae5a6a61371ebfe181237d8f
d0c8883816f0e1fe333dc9f3197d3c4e47c475a5
1011e2c2fa99729a46efde5b5bbaf6daed975a2c
```

No squash, rebase, amend, cherry-pick to `lucian-dev`, or force option was used.

## 2. Publication result

Executed exactly:

```bash
git push --set-upstream origin \
  feature/p4b-eagle3-static-k:feature/p4b-eagle3-static-k
```

The push created only the new feature branch. Immediate and final remote verification returned:

```text
1011e2c2fa99729a46efde5b5bbaf6daed975a2c  refs/heads/feature/p4b-eagle3-static-k
```

`git branch -vv` now records:

```text
feature/p4b-eagle3-static-k  1011e2c [origin/feature/p4b-eagle3-static-k]
```

The existing remote `lucian-dev` branch was not updated.

## 3. New GitHub clean-room recovery

An entirely new source root was created with `mktemp -d`:

```text
/private/tmp/mrv2-postpublish-cleanroom.MEebDh
```

The source checkouts did not reuse the current repository's `.git`, source tree, worktree, or build cache.

### 3.1 vLLM-Ascend clone

```bash
git clone \
  --branch feature/p4b-eagle3-static-k \
  --single-branch \
  https://github.com/LucianWQZ/vllm-ascend.git \
  /private/tmp/mrv2-postpublish-cleanroom.MEebDh/vllm-ascend
```

Observed identity:

```text
HEAD:   1011e2c2fa99729a46efde5b5bbaf6daed975a2c
tree:   7d165d585755766e7493e02f0281598e4aca3602
status: clean
```

The fresh clone's `git log -10 --oneline` contains the same ten delivery commits, with `1011e2c2...` at the tip and `b12399ad...` as the first feature commit.

### 3.2 Exact vLLM baseline

The independent vLLM clone was recovered from:

```text
https://github.com/LucianWQZ/vllm.git
```

It was explicitly checked out at the required commit:

```text
HEAD:   84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree:   f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
status: clean
```

`rg DraftAttentionReadInputs` returned no matches (exit 1 due to an empty result), proving that the historical upstream prototype API is absent.

### 3.3 Tree identity

```text
current Final tree:      7d165d585755766e7493e02f0281598e4aca3602
GitHub clone Final tree: 7d165d585755766e7493e02f0281598e4aca3602
```

Result: exact tree identity passed.

## 4. Compile, import, and static checks

The clean source paths were forced explicitly:

```bash
export PYTHONPATH=/private/tmp/mrv2-postpublish-cleanroom.MEebDh/vllm-ascend:/private/tmp/mrv2-postpublish-cleanroom.MEebDh/vllm
export VLLM_VERSION=0.29.0
```

The existing Python virtual environment was used only as the host dependency interpreter; none of the requested vLLM/vLLM-Ascend modules was imported from the current production worktree or an installed package. The repository's own `tests/ut/conftest.py` CPU/build-info shims were used because this host has no built vLLM/Ascend extension. Every relevant module's `__file__` was asserted to be under the new clean-room paths.

### 4.1 Compile

```bash
python -m compileall -q \
  vllm_ascend/worker/v2/spec_decode \
  vllm_ascend/worker/v2/attn_utils.py \
  vllm_ascend/attention/attention_v1.py
```

Result: exit 0.

### 4.2 Imports and provenance

All requested imports completed successfully under the CPU test harness:

| Module | Resolved source |
|---|---|
| `vllm` | clean-room vLLM clone |
| `draft_window` | clean-room vLLM-Ascend clone |
| `draft_window_eager` | clean-room vLLM-Ascend clone |
| `draft_window_eagle3` | clean-room vLLM-Ascend clone |
| DFlash speculator | clean-room vLLM-Ascend clone |
| DSpark speculator | clean-room vLLM-Ascend clone |
| AR/Eagle3 speculator | clean-room vLLM-Ascend clone |
| `attn_utils` | clean-room vLLM-Ascend clone |
| `attention_v1` | clean-room vLLM-Ascend clone |

The import emitted expected CPU-host warnings for missing generated `_version`, `vllm._C`, Triton, and Ascend custom-op libraries. No requested import resolved to the original Mac source tree or an installed vLLM/vLLM-Ascend package.

### 4.3 Static formatting checks

The 18 changed Python files from the exact baseline-to-Final range were checked:

```text
ruff check:          All checks passed!
ruff format --check: 18 files already formatted
```

## 5. Clean-room regression results

All commands below ran from the GitHub clean clone with the exact clean-room vLLM source on `PYTHONPATH`.

| Command | Result | Classification |
|---|---:|---|
| `pytest -q tests/ut/spec_decode/test_draft_window.py` | `135 passed, 1 warning` | PASS |
| `pytest -q tests/ut/spec_decode/test_draft_window_runtime.py` | `32 passed, 1 warning` | PASS |
| `pytest -q tests/ut/spec_decode/test_draft_window_eager.py` | `40 passed, 1 warning` | PASS |
| `pytest -q tests/ut/spec_decode/test_draft_window_eagle3.py` | `31 passed, 1 warning` | PASS |
| `pytest -q tests/ut/spec_decode/test_dflash2_v2.py` | `6 passed, 1 warning` | PASS |
| `pytest -q tests/ut/worker/test_attn_utils_v2.py` | `45 passed, 1 warning` | PASS |
| `pytest -q tests/ut/attention/test_attention_v1.py` | `41 passed, 1 warning, 2 subtests passed` | PASS |
| `pytest -q tests/ut/spec_decode` | `472 passed, 13 skipped, 7 failed, 1 warning, 2 subtests passed` | **NOT PASS — host limitation** |
| `pytest -q tests/ut/spec_decode --ignore=tests/ut/spec_decode/test_speculators_vwn_eagle3.py` | `470 passed, 13 skipped, 1 warning, 2 subtests passed` | PASS for locally runnable suite |

The seven full-suite failures are all in `tests/ut/spec_decode/test_speculators_vwn_eagle3.py`:

```text
TestVwnLlamaDecoderLayer::test_forward_layer0[4-1.5]
TestVwnLlamaDecoderLayer::test_forward_layer0[4-1.0]
TestVwnLlamaDecoderLayer::test_qkv_proj_input_size_layer0
TestVwnLlamaModel::test_forward[1-False]
TestVwnLlamaModel::test_forward[1-True]
TestEagle3VwnLlamaForCausalLM::test_init_and_forward
TestEagle3VwnLlamaForCausalLM::test_embed_input_ids
```

Each fails at the existing host-only backend selection boundary with:

```text
ValueError: Invalid attention backend for None
```

These failures are intentionally not reported as PASS. They are the same known VWN host backend limitation recorded before publication; no new Draft Window test failed. The separately executed locally runnable suite excludes only that file and passes.

## 6. Freeze artifact cross-check after publication

The package at `/Users/wenqingzhang/Desktop/Note/MRV2/P4_freeze` was revalidated against the published clean clone:

- `shasum -a 256 -c SHA256SUMS`: every listed artifact is `OK`.
- Commit Manifest and Implementation Snapshot record baseline `841dc6cc...`, Final `1011e2c2...`, and tree `7d165d58...` exactly.
- All ten files listed by `format-patches/SERIES` are present; their `From` headers are the exact delivery SHA sequence.
- `git bundle verify MRV2_P0_P4b.bundle`: success.
- Bundle head: `1011e2c2... refs/heads/feature/p4b-eagle3-static-k`.
- Bundle prerequisite: `841dc6cc...`, as documented for the incremental shallow-history bundle.
- `git apply --check MRV2_P0_P4b_Full_Diff.patch` passed in a separate checkout at exact baseline `841dc6cc...`.
- Applying that Full Diff to the index and running `git write-tree` produced `7d165d585755766e7493e02f0281598e4aca3602`, exactly equal to the GitHub Final tree.

The audit report is a post-Freeze record and remains intentionally outside the original immutable `SHA256SUMS` set.

## 7. Final repository audit

After push, cloning, compilation, tests, and artifact verification:

| Repository | HEAD | Status | Additional evidence |
|---|---|---|---|
| Current vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | clean | no prototype API |
| Current vLLM-Ascend | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` | clean | tracks `origin/feature/p4b-eagle3-static-k`; tree `7d165d58...` |
| Clean-room vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | clean | detached exact baseline |
| Clean-room vLLM-Ascend | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` | clean | recovered solely from GitHub |

No production commit or source/test modification was created by this publication audit.

## 8. Post-publish final verdict

### `DEPLOYMENT READINESS: PASS`

GitHub now transports the complete ten-commit lineage. A new clone recovers the exact Final commit and tree, imports and compiles the required source, and passes every requested targeted test plus the locally runnable `spec_decode` suite.

This PASS proves only:

- GitHub source transport;
- exact commit/tree recovery;
- clean-source imports and compilation;
- local static and CPU contracts.

It does **not** prove:

- NPU runtime correctness;
- actual Draft Attention physical read-set;
- real device stream/event lifecycle;
- Draft/Target runtime logits equivalence;
- D2H or end-to-end performance.

`G-GQA-EAGER`, `G-AR-STEP`, and Feature release therefore remain open/HOLD exactly as before. No P5 work was started.
