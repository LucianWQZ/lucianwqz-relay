# MRV2 P0→P4b Commit Manifest

> Generated from the actual local Git object graph on 2026-10-12.  
> This manifest describes the only deliverable production lineage.  
> Repository rule: vLLM remains immutable; production changes exist only in vLLM-Ascend.

## 1. Identity

| Item | Value |
|---|---|
| vLLM required HEAD | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| vLLM-Ascend repository | `/Users/wenqingzhang/Desktop/vllm/vllm-ascend` |
| vLLM-Ascend baseline | `841dc6ccdb134eab7ad09008859834d0572ee83f` |
| vLLM-Ascend final branch | `feature/p4b-eagle3-static-k` |
| vLLM-Ascend final HEAD | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` |
| Baseline tree | `19693c4a2d634ad190c0703f77364e9bf2481a47` |
| Final tree | `7d165d585755766e7493e02f0281598e4aca3602` |
| Merge-base | exact baseline `841dc6cc…` |
| Delivery commit count | 10 |
| Repository shape | shallow; baseline is a grafted/shallow root |

## 2. Exact Git graph

```text
* 1011e2c (HEAD -> feature/p4b-eagle3-static-k) fix(spec-decode): address P4b Eagle3 window review findings
* d0c8883 feat(spec-decode): integrate MRV2 draft windows for Eagle3 eager
* 4c1f691 (feature/p4a-ascend-only) fix(spec-decode): address P4a Ascend-only review findings
* 0dd83e9 feat(spec-decode): integrate MRV2 draft windows in Ascend eager path
* 1672788 fix(spec-decode): address P3 draft-window review findings
* feab28f feat(spec-decode): add MRV2 draft-window runtime ownership
* fac8412 fix(spec-decode): address P2 draft-window review findings
* 8357967 feat(spec-decode): add MRV2 draft-window source inventory
* c58daea fix(spec-decode): address P1 draft-window review findings
* b12399a feat(spec-decode): add MRV2 draft-window policy and math
o 841dc6c (grafted, origin/lucian-dev) [Performance][Attention] Use native scatter for GLM-5.3-Flash NoPE KV cache writes (#16756)
```

The linear dependency is:

```text
841dc6c baseline
  → b12399a P1
  → c58daea P1 review-fix
  → 8357967 P2
  → fac8412 P2 review-fix
  → feab28f P3
  → 1672788 P3 review-fix
  → 0dd83e9 P4a Ascend-only
  → 4c1f691 P4a review-fix
  → d0c8883 P4b Eagle3
  → 1011e2c P4b review-fix
```

## 3. Commit inventory and dependency policy

All commits were authored by `Lucian <2207456347@qq.com>`. The safe migration unit is the complete ordered series. “Independently applicable” below means applicability to the exact stated parent, not semantic independence from earlier phases.

### 3.1 `b12399ad915415ce45105df5b0601848e7b70f6f`

- Subject: `feat(spec-decode): add MRV2 draft-window policy and math`
- Parent: `841dc6ccdb134eab7ad09008859834d0572ee83f`
- Author date: `2026-10-10T03:48:35+08:00`
- Phase: P1 implementation.
- Stat: 8 files, 1,107 insertions, 1 deletion.
- Independently applicable: **yes, only onto exact feature baseline**. It is not a complete/releasable Feature by itself.
- Production files:
  - `vllm_ascend/worker/v2/spec_decode/__init__.py`
  - `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py`
  - `vllm_ascend/worker/v2/spec_decode/dflash/speculator.py`
  - `vllm_ascend/worker/v2/spec_decode/draft_window.py`
  - `vllm_ascend/worker/v2/spec_decode/dspark/speculator.py`
- Test files:
  - `tests/ut/spec_decode/test_dflash2_v2.py`
  - `tests/ut/spec_decode/test_draft_window.py`
  - `tests/ut/worker/test_extract_hidden_states_speculator_v2.py`
- Purpose: centralized product policy, forced-OFF ordering, legacy anchor and pure Window math, typed policy/plan receivers.
- Later review findings: test tautology, separator normalization, warning scope, unknown reason fall-through, geometry precondition and public factory parity.
- Patch file: `format-patches/0001-feat-spec-decode-add-MRV2-draft-window-policy-and-ma.patch`.

### 3.2 `c58daea0df34d1a6253dc34221d2a084b13affd5`

- Subject: `fix(spec-decode): address P1 draft-window review findings`
- Parent: `b12399ad915415ce45105df5b0601848e7b70f6f`
- Author date: `2026-10-10T04:37:01+08:00`
- Phase: P1 review-fix.
- Stat: 4 files, 213 insertions, 16 deletions.
- Independently applicable: **no**; requires C1.
- Production files: `spec_decode/__init__.py`, `spec_decode/draft_window.py`.
- Tests: `test_dflash2_v2.py`, `test_draft_window.py`.
- Purpose: close P1 review with real dispatch parity, exact policy identity/warning behavior, exhaustive diagnostics, and geometry fail-closed tests.
- Later status: P1 FINAL PASS; no unresolved P1 blocker.
- Patch file: `format-patches/0002-fix-spec-decode-address-P1-draft-window-review-findi.patch`.

### 3.3 `83579675a997a44b293ff0ee1cb088a2eef0ed13`

- Subject: `feat(spec-decode): add MRV2 draft-window source inventory`
- Parent: `c58daea0df34d1a6253dc34221d2a084b13affd5`
- Author date: `2026-10-10T05:33:36+08:00`
- Phase: P2 implementation.
- Stat: 6 files, 1,880 insertions, 8 deletions.
- Independently applicable: **no**; requires P1 Final.
- Production files: AR/DFlash/DSpark speculators and `spec_decode/draft_window.py`.
- Tests: `test_draft_window.py`, `test_dflash2_v2.py`.
- Purpose: capability inventory, canonical FullSource, valid-count gather, source identity, single-group direct-prefix provider and read descriptor.
- Later review findings: env FlashComm bypass, pointer freshness blind spot, self-proving Eagle3 offset check, real BlockTables/int64 gaps, exception semantics and release Gate.
- Patch file: `format-patches/0003-feat-spec-decode-add-MRV2-draft-window-source-invent.patch`.

### 3.4 `fac84121ddf84fe5a76cd739432cea3b61365a9b`

- Subject: `fix(spec-decode): address P2 draft-window review findings`
- Parent: `83579675a997a44b293ff0ee1cb088a2eef0ed13`
- Author date: `2026-10-10T10:21:16+08:00`
- Phase: P2 review-fix.
- Stat: 2 files, 223 insertions, 39 deletions.
- Independently applicable: **no**; requires C2 and P1 Final.
- Production file: `vllm_ascend/worker/v2/spec_decode/draft_window.py`.
- Test file: `tests/ut/spec_decode/test_draft_window.py`.
- Purpose: authoritative runtime capability parsing, independent offset provenance, real-source and dtype coverage, stable error contracts.
- Later status: P2 FINAL PASS; P3 must use caller-owned monotonic `mapping_epoch` because pointer identity remains intentionally one-batch-only.
- Patch file: `format-patches/0004-fix-spec-decode-address-P2-draft-window-review-findi.patch`.

### 3.5 `feab28f573b973a6b970cef56d1baa35191ab319`

- Subject: `feat(spec-decode): add MRV2 draft-window runtime ownership`
- Parent: `fac84121ddf84fe5a76cd739432cea3b61365a9b`
- Author date: `2026-10-10T11:19:13+08:00`
- Phase: P3 implementation.
- Stat: 6 files, 1,501 insertions, 18 deletions.
- Independently applicable: **no**; requires P2 Final.
- Production files: `spec_decode/draft_window.py` and AR/DFlash/DSpark runtime holders.
- Tests: `test_draft_window.py`, new `test_draft_window_runtime.py`.
- Purpose: immutable generation/request identity, mapping epoch, stable workspace, lease pool/state transitions, typed transport, Draft-only metadata store.
- Later review findings: Target guard could be omitted, slots alias traversal gap, plus P4 obligations for production epoch provenance, one validation boundary and hot-D2H policy.
- Patch file: `format-patches/0005-feat-spec-decode-add-MRV2-draft-window-runtime-owner.patch`.

### 3.6 `16727882744c935d9e899f7775353b57738852bc`

- Subject: `fix(spec-decode): address P3 draft-window review findings`
- Parent: `feab28f573b973a6b970cef56d1baa35191ab319`
- Author date: `2026-10-10T12:13:20+08:00`
- Phase: P3 review-fix.
- Stat: 2 files, 138 insertions, 14 deletions.
- Independently applicable: **no**; requires C3.
- Production file: `vllm_ascend/worker/v2/spec_decode/draft_window.py`.
- Test file: `tests/ut/spec_decode/test_draft_window_runtime.py`.
- Purpose: mandatory real Target metadata, MRO slots alias detection, empty/exception lifecycle regressions, explicit caller-owned epoch contract.
- Later status: P3 FINAL PASS; no live Attention binding at this commit.
- Patch file: `format-patches/0006-fix-spec-decode-address-P3-draft-window-review-findi.patch`.

### 3.7 `0dd83e9f75d4b2d766126af3a7f92352e342f756`

- Subject: `feat(spec-decode): integrate MRV2 draft windows in Ascend eager path`
- Parent: `16727882744c935d9e899f7775353b57738852bc`
- Author date: `2026-10-10T15:42:37+08:00`
- Phase: P4a Ascend-only implementation.
- Stat: 12 files, 2,160 insertions, 50 deletions.
- Independently applicable: **no**; requires P1–P3 Final and exact unmodified vLLM baseline.
- Production files:
  - `vllm_ascend/attention/attention_v1.py`
  - `vllm_ascend/attention/utils.py`
  - `vllm_ascend/worker/v2/attn_utils.py`
  - `vllm_ascend/worker/v2/spec_decode/dflash/speculator.py`
  - `vllm_ascend/worker/v2/spec_decode/dspark/speculator.py`
  - `vllm_ascend/worker/v2/spec_decode/draft_window.py`
  - new `vllm_ascend/worker/v2/spec_decode/draft_window_eager.py`
- Test files: attention-v1, attn-utils-v2, draft-window policy/runtime, and new eager integration suite.
- Purpose: explicit instance-scoped Ascend-only live read path, production epoch source, single validate boundary, DFlash/eligible DSpark serialized eager integration.
- Later review findings: profile/prefill reachability, vendor-local assembly equivalence, NumPy aliases, valid-count owner naming, static no-global guard, NPU D2H performance.
- Patch file: `format-patches/0007-feat-spec-decode-integrate-MRV2-draft-windows-in-Asc.patch`.

### 3.8 `4c1f69146915f4f0ae5a6a61371ebfe181237d8f`

- Subject: `fix(spec-decode): address P4a Ascend-only review findings`
- Parent: `0dd83e9f75d4b2d766126af3a7f92352e342f756`
- Author date: `2026-10-10T16:34:00+08:00`
- Phase: P4a review-fix.
- Stat: 5 files, 323 insertions, 23 deletions.
- Independently applicable: **no**; requires Ascend-only C4.
- Production files: `spec_decode/draft_window.py`, `spec_decode/draft_window_eager.py`.
- Tests: policy/runtime/eager integration files.
- Purpose: terminal pure-prefill baseline bypass, explicit nonuniform rejection, Tensor/NumPy isolation, stable valid-count ownership, positive assembly differential and transport guard.
- Later finding: P4b review CB-01 showed continuing pure chunked prefill still aborted; final shared correction is in `1011e2c…`.
- Patch file: `format-patches/0008-fix-spec-decode-address-P4a-Ascend-only-review-findi.patch`.

### 3.9 `d0c8883816f0e1fe333dc9f3197d3c4e47c475a5`

- Subject: `feat(spec-decode): integrate MRV2 draft windows for Eagle3 eager`
- Parent: `4c1f69146915f4f0ae5a6a61371ebfe181237d8f`
- Author date: `2026-10-10T17:48:00+08:00`
- Phase: P4b Eagle3 static-K implementation.
- Stat: 5 files, 2,250 insertions, 5 deletions.
- Independently applicable: **no**; requires P4a Final and all lower phases.
- Production files: AR speculator, `draft_window.py`, new `draft_window_eagle3.py`.
- Tests: policy extension and new `test_draft_window_eagle3.py`.
- Purpose: proposal-entry L0/static K, frozen H/S, first-pass private Draft metadata, per-step E/V, FullSource refresh, future block and rejection/lifecycle contracts.
- Later review findings: continuing pure prefill abort, FIA exact carrier evidence, missing semantic-kernel drift hashes, rejection/prefill documentation.
- Patch file: `format-patches/0009-feat-spec-decode-integrate-MRV2-draft-windows-for-Ea.patch`.

### 3.10 `1011e2c2fa99729a46efde5b5bbaf6daed975a2c`

- Subject: `fix(spec-decode): address P4b Eagle3 window review findings`
- Parent: `d0c8883816f0e1fe333dc9f3197d3c4e47c475a5`
- Author date: `2026-10-11T14:05:36+08:00`
- Phase: P4b review-fix / current Final.
- Stat: 5 files, 119 insertions, 44 deletions.
- Independently applicable: **no**; requires C5 and full preceding chain.
- Production files: `spec_decode/draft_window_eager.py`, `spec_decode/draft_window_eagle3.py`.
- Tests: `test_attention_v1.py`, eager integration, Eagle3 integration.
- Purpose: all pure scheduler-prefill chunks baseline-bypass without Window state; exact FIA carrier differential; semantic-kernel drift guard; retain mixed-prefill rejection.
- Final status: P4b STATIC FINAL PASS; NPU runtime Gate remains open.
- Patch file: `format-patches/0010-fix-spec-decode-address-P4b-Eagle3-window-review-fin.patch`.

## 4. Final baseline→HEAD changed-file list

Range summary: 18 files changed, 9,706 insertions, 10 deletions.

```text
M tests/ut/attention/test_attention_v1.py
M tests/ut/spec_decode/test_dflash2_v2.py
A tests/ut/spec_decode/test_draft_window.py
A tests/ut/spec_decode/test_draft_window_eager.py
A tests/ut/spec_decode/test_draft_window_eagle3.py
A tests/ut/spec_decode/test_draft_window_runtime.py
M tests/ut/worker/test_attn_utils_v2.py
M tests/ut/worker/test_extract_hidden_states_speculator_v2.py
M vllm_ascend/attention/attention_v1.py
M vllm_ascend/attention/utils.py
M vllm_ascend/worker/v2/attn_utils.py
M vllm_ascend/worker/v2/spec_decode/__init__.py
M vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py
M vllm_ascend/worker/v2/spec_decode/dflash/speculator.py
A vllm_ascend/worker/v2/spec_decode/draft_window.py
A vllm_ascend/worker/v2/spec_decode/draft_window_eager.py
A vllm_ascend/worker/v2/spec_decode/draft_window_eagle3.py
M vllm_ascend/worker/v2/spec_decode/dspark/speculator.py
```

## 5. Superseded prototype objects — excluded from delivery

### vLLM upstream prototype

| Field | Value |
|---|---|
| Commit | `0403469280c3d0f19c55cd1768e7e9d9e566a719` |
| Parent | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| Subject | `feat(spec-decode): allow explicit draft attention read inputs` |
| Ref | `archive/p4a-upstream-hook-prototype` |
| Stat | 3 files, 258 insertions, 22 deletions |
| Verdict | technically proven, **not deliverable** under `R-REPO-01` |

It is absent from the format-patch series, full diff, and incremental bundle.

### vLLM-Ascend upstream-dependent prototype

| Field | Value |
|---|---|
| Commit | `e0dd8e8d14a287e4d5a69c54d7a617a6ae160529` |
| Parent | `16727882744c935d9e899f7775353b57738852bc` |
| Subject | `feat(spec-decode): enable gated MRV2 draft windows for dense eager` |
| Refs | `archive/p4a-upstream-dependent-prototype`, `lucian-dev` |
| Stat | 12 files, 1,748 insertions, 50 deletions |
| Verdict | depends on prohibited upstream API; **do not cherry-pick** |

It is on a sibling lineage from P3 Final and is not an ancestor of final HEAD.

## 6. Recovery artifact semantics

| Artifact | Preserves commits | Preserves author/message | Requires exact baseline | Tested result |
|---|---:|---:|---:|---|
| `format-patches/*.patch` | recreates 10 commits; committer metadata may change hash | yes | yes | `git am` clean; final tree exact |
| `MRV2_P0_P4b.bundle` | yes, exact commit hashes | yes | yes, because source is shallow | verify PASS; offline fetch recovered exact HEAD/tree |
| `MRV2_P0_P4b_Full_Diff.patch` | no | no | yes | `git apply --check` PASS |

### Shallow bundle constraint

The final bundle was deliberately created as `841dc6cc… .. feature/p4b-eagle3-static-k`. `git bundle verify` reports:

```text
contains: 1011e2c2fa99729a46efde5b5bbaf6daed975a2c refs/heads/feature/p4b-eagle3-static-k
requires: 841dc6ccdb134eab7ad09008859834d0572ee83f
```

A standalone clone without the prerequisite fails by design. Fetching into a repository that has the exact baseline works fully offline. This is more honest than emitting a shallow bundle that claims complete history but cannot traverse the baseline parent.

## 7. Cherry-pick guidance

- Preferred: apply all ten patches in lexical order with one `git am format-patches/*.patch` invocation.
- Do not omit review-fix commits; each records correctness findings, not cosmetic cleanup.
- Do not start at P4a/P4b without P1–P3; their types, source contract, and lifetime protocol are required.
- Do not mix the final Ascend-only chain with either superseded prototype.
- Do not apply any vLLM patch. The required vLLM source is exactly `84030bbe…`.
- P1–P3 alone must not be presented as an enabled Feature; the live read consumer begins only in P4a/P4b.

## 8. Audit checks used to generate this manifest

```text
git merge-base 841dc6cc… 1011e2c… = 841dc6cc…
git rev-list --count 841dc6cc…..1011e2c… = 10
git diff --stat 841dc6cc…..1011e2c… = 18 files, +9706/-10
git apply --check MRV2_P0_P4b_Full_Diff.patch = exit 0
git am format-patches/*.patch = 10/10 applied
restored format-patch tree = final tree = 7d165d585755766e7493e02f0281598e4aca3602
git bundle verify MRV2_P0_P4b.bundle = PASS, prerequisite 841dc6cc…
offline baseline-seeded bundle fetch = exact HEAD 1011e2c… and exact final tree
```

All file-level hashes are recorded in the package-root `SHA256SUMS`.
