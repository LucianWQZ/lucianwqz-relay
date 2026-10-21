# MRV2 Speculative Draft Sliding Window — P0→P4b Implementation Snapshot

> Freeze date: 2026-10-12 (Asia/Shanghai)  
> Delivery scope: P0 design/preflight through P4b static integration  
> Production repository boundary: **vllm-ascend only**  
> Release status: **HOLD**  
> Runtime gates: `G-GQA-EAGER` and `G-AR-STEP` remain open pending company-NPU evidence

This is the canonical human-readable entry point for the frozen local delivery. It explains what was built, why the implementation is structured this way, which Git objects contain it, how the independent reviews changed it, and how to restore it. Full code is intentionally kept in the patch series, bundle, and full-diff artifact rather than copied into this document.

## 1. Feature and migration objective

`draft_window_size` limits the historical KV blocks visible to **Draft Attention** during speculative decoding. It is a read-plane optimization. It must not shrink or rewrite the physical KV allocation, write-side slot mapping, absolute positions, query layout, canonical full block tables, or Target-model Attention state.

MRV1 already has a sliding-window adapter, but MRV2 is not a mechanical port. MRV2 has different speculator classes, a shared metadata funnel, Target metadata reuse in autoregressive paths, Ascend-specific metadata factories, ACL Graph capture/replay, and reused request-index buffers. Reusing the MRV1 mutation pattern would risk cross-request freshness bugs, Target contamination, window-of-window materialization, stale Graph operands, and write/read-domain confusion. The final implementation therefore introduces a speculator-owned Draft Window read plane in stages.

## 2. Exact repository audit at freeze

### 2.1 vLLM — immutable dependency

| Field | Frozen value |
|---|---|
| Repository | `/Users/wenqingzhang/Desktop/vllm/vllm` |
| Branch | `lucian-dev` |
| HEAD | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| Subject | `[Bugfix][Core] Stop zero-progress preemption cascades for deferred KV frees (#49675)` |
| Working tree | clean; staged, unstaged, and untracked output empty |
| Diff against frozen HEAD | empty |
| Shallow repository | yes; `84030bbe…` is the local shallow boundary |
| Prototype symbol guard | no `DraftAttentionReadInputs` reference in current source/tests |

The archived upstream experiment remains reachable as `archive/p4a-upstream-hook-prototype` at `0403469280c3d0f19c55cd1768e7e9d9e566a719`, whose parent is the frozen vLLM baseline. It is historical evidence only and is not part of any delivery artifact or runtime dependency.

### 2.2 vLLM-Ascend — delivery repository

| Field | Frozen value |
|---|---|
| Repository | `/Users/wenqingzhang/Desktop/vllm/vllm-ascend` |
| Branch | `feature/p4b-eagle3-static-k` |
| HEAD | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` |
| Feature baseline | `841dc6ccdb134eab7ad09008859834d0572ee83f` |
| Merge-base with baseline | exact baseline `841dc6cc…` |
| Feature commits | 10, linear |
| Working tree | clean |
| Baseline tree | `19693c4a2d634ad190c0703f77364e9bf2481a47` |
| Final tree | `7d165d585755766e7493e02f0281598e4aca3602` |
| Shallow repository | yes; `841dc6cc…` is the local shallow boundary |
| Final range | 18 files, 9,706 insertions, 10 deletions |

The upstream-dependent Ascend prototype is archived at `archive/p4a-upstream-dependent-prototype` / `lucian-dev`, commit `e0dd8e8d14a287e4d5a69c54d7a617a6ae160529`, parent `16727882744c935d9e899f7775353b57738852bc`. It is not an ancestor of the final Ascend-only branch and must not be delivered.

## 3. Frozen architecture in one screen

```text
configured value + normalized method/model policy
                 ↓
P1 policy + immutable integer math
                 ↓
P2 capability inventory + canonical FullSource + read descriptor
                 ↓
P3 generation identity / mapping_epoch / workspace / lease
                 ↓
typed DraftMetadataInputs + DraftMetadataStore
                 ↓
P4a parallel eager adapter OR P4b Eagle3 AR adapter
                 ↓
independent Draft metadata → Draft Attention read visibility

Separately and unchanged:
canonical full table → full slot_mapping → physical KV write
Target ModelState    → Target metadata/read lengths
```

The most important frozen invariants are:

1. Only Draft read tables and Draft read lengths may change when Window is ON.
2. Target metadata/table/length, positions, query layout, physical KV allocation, and slot mapping stay full.
3. Every Window is materialized from canonical FullSource; never window an earlier Window.
4. Table, exact lengths, upper bounds, request ordering, and valid counts belong to one generation.
5. Caller-owned monotonic `mapping_epoch` is mandatory; pointer or Python identity is not freshness.
6. Active backing cannot be overwritten until its reader has completed and its lease retires.
7. Draft metadata is independently built and cannot alias Target mutable state or Tensor/NumPy storage.
8. Eagle3 freezes `S` once per proposal; only the step exact end `E_s` changes.
9. MTP and DeepSeek-V4 co-trained DSpark are warning + forced OFF before numeric validation or allocation.
10. Eligible unsupported combinations fail closed before materialization/forward; they do not silently disable another user feature.
11. CONFIG OFF creates no Window plan, inventory, workspace, store, or transport.
12. Graph, Async, parallel topologies, prefix-cache Window ON, complex backends, DFlash2 runtime, dynamic-K, and plain Eagle remain closed.

## 4. Phase ledger

| Phase | Problem solved | Production files at phase boundary | Commits / record | Final state |
|---|---|---|---|---|
| P0 | Source-drift check, implementation scope, source anchors, phase/Gate plan | none | `MRV2_Draft_Window_Implementation_Plan.md` | complete; no production commit |
| P1 | Product policy, forced-OFF ordering, pure integer math, basic typed plans | `spec_decode/__init__.py`; `spec_decode/draft_window.py`; AR/DFlash/DSpark speculator receivers | `b12399ad…` + `c58daea0…` | FINAL PASS |
| P2 | Runtime inventory, immutable canonical FullSource, valid counts, single-group direct-prefix provider | primarily `spec_decode/draft_window.py`; inventory receivers in AR/DFlash/DSpark | `83579675…` + `fac84121…` | FINAL PASS |
| P3 | Generation freshness, workspace backing, lease state machine, typed transport, Draft-only metadata store | `spec_decode/draft_window.py`; runtime holders in AR/DFlash/DSpark | `feab28f…` + `1672788…` | FINAL PASS |
| P4a | Ascend-only live integration for DFlash and eligible DSpark, serialized dense-GQA eager | `draft_window_eager.py`; DFlash/DSpark speculators; `attn_utils.py`; `attention_v1.py`; attention helpers; P3 extensions | `0dd83e9…` + `4c1f691…` | STATIC FINAL PASS; NPU gate open |
| P4b | Eagle3 static-K first-pass and multi-step AR integration with proposal-frozen anchor | `draft_window_eagle3.py`; AR speculator; shared eager classifier; P3 extensions | `d0c8883…` + `1011e2c…` | STATIC FINAL PASS; NPU gate open |

## 5. Commit graph from Git

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
o 841dc6c (grafted, origin/lucian-dev) feature baseline
```

The baseline is displayed as `grafted` because this checkout is shallow. The ten feature commits and all their parent links are locally complete.

## 6. Per-commit change map

### C1 — P1 implementation

- SHA: `b12399ad915415ce45105df5b0601848e7b70f6f`
- Parent: `841dc6ccdb134eab7ad09008859834d0572ee83f`
- Stat: 8 files, +1,107/−1.
- Production: policy receiver/factory integration plus `draft_window.py` policy, static-K offset, legacy anchor, visible-length and projection math.
- Tests: new policy/math suite; DFlash2 receiver contract; factory extraction regression.
- Reason: establish policy ordering and pure contracts before any runtime state exists.
- Later review: exposed test tautology, method normalization/warning-scope issues, non-default geometry ambiguity, and missing public dispatch parity.

### C1R — P1 review fix

- SHA: `c58daea0df34d1a6253dc34221d2a084b13affd5`
- Parent: `b12399ad…`; stat: 4 files, +213/−16.
- Production: exhaustive forced-OFF diagnostics, corrected normalization, geometry guard, per-construction warning semantics.
- Tests: real public factory dispatch, unknown reason, separator behavior, geometry counterexample, and warning scope.
- Result: P1 FINAL PASS.

### C2 — P2 implementation

- SHA: `83579675a997a44b293ff0ee1cb088a2eef0ed13`
- Parent: `c58daea…`; stat: 6 files, +1,880/−8.
- Production: backend/group inventory, FullSource identity, valid-count gather, read descriptors, single-group dense direct-prefix provider.
- Tests: source alias/shortage, reorder and stale tail, block ID zero, geometry, global gid, capability matrix.
- Later review: found FlashComm env coverage, `idx_mapping` pointer-freshness limitation, self-proving Eagle3 offset check, and missing real BlockTables/int64 evidence.

### C2R — P2 review fix

- SHA: `fac84121ddf84fe5a76cd739432cea3b61365a9b`
- Parent: `83579675…`; stat: 2 files, +223/−39.
- Production: authoritative runtime Gate parsing, independent configured-offset validation, clearer runtime failure semantics.
- Tests: env FlashComm, real AscendBlockTables, int32/int64 mappings, forged inventory, configured-K mismatch.
- Result: P2 FINAL PASS; pointer identity explicitly limited to one batch and P3 `mapping_epoch` made mandatory.

### C3 — P3 implementation

- SHA: `feab28f573b973a6b970cef56d1baa35191ab319`
- Parent: `fac84121…`; stat: 6 files, +1,501/−18.
- Production: generation identity, request fingerprint, stable workspace, lease pool/state machine, immutable `DraftMetadataInputs`, `DraftMetadataStore`, runtime owner.
- Tests: same-pointer in-place mapping rewrite, reorder/replacement/ABA, workspace alias and reuse, delayed completion, stale handles, Target isolation.
- Later review: found optional Target-isolation input and slotted-object alias traversal gap; identified P4 epoch provenance, single validation boundary, and hot-D2H decisions as later blockers.

### C3R — P3 review fix

- SHA: `16727882744c935d9e899f7775353b57738852bc`
- Parent: `feab28f…`; stat: 2 files, +138/−14.
- Production: real Target metadata became mandatory; alias traversal gained MRO `__slots__`; epoch provenance contract was documented without inventing an epoch in P3.
- Tests: missing/None Target, slotted alias, empty batch, completion-query exception and retry.
- Result: P3 FINAL PASS; Attention still read full context at this boundary.

### C4 — P4a Ascend-only implementation

- SHA: `0dd83e9f75d4b2d766126af3a7f92352e342f756`
- Parent: `1672788…`; stat: 12 files, +2,160/−50.
- Production: `DraftWindowEagerMixin`, production epoch source, one validate-before-builder boundary, controlled host snapshot, vendor-local read-input assembly, Ascend exact-length seam, DFlash/eligible DSpark integration and fail-closed matrix.
- Tests: OFF/super parity, builder differential, DFlash/DSpark width, profile/dummy, Target isolation, stale validation, no private-upstream symbol dependency.
- Later review: profile/prefill reachability, vendor-local assembly parity, NumPy storage aliases, valid-count owner naming, and NPU-only D2H performance evidence.

### C4R — P4a independent-review fix

- SHA: `4c1f69146915f4f0ae5a6a61371ebfe181237d8f`
- Parent: `0dd83e9…`; stat: 5 files, +323/−23.
- Production: terminal pure-prefill baseline bypass, explicit unsupported nonuniform path, Tensor/NumPy isolation strengthening, stable CPU valid-count owner naming.
- Tests: red-to-green review set, positive upstream-equivalent assembly differential, profile/dummy/Target owner and no-global guards.
- Result: P4a Ascend-only STATIC FINAL PASS. A later P4b review found that continuing pure chunked prefill also needed baseline bypass; that shared fix is in `1011e2c…`.

### C5 — P4b implementation

- SHA: `d0c8883816f0e1fe333dc9f3197d3c4e47c475a5`
- Parent: `4c1f691…`; stat: 5 files, +2,250/−5.
- Production: Eagle3 proposal `L0/K/H/S`, proposal-frozen anchor, first-pass Draft-private metadata, per-step `E_s/V_s`, canonical FullSource refresh, future-column and rejection-aware lifecycle.
- Tests: first-pass isolation, frozen anchor, K≥3 steps, block crossing, poisoned prior Window, rejection, stale step/ABA, profile/dummy and P4a regression.
- Later review: continuing chunked prefill abort, FIA exact-carrier evidence gap, missing hashes for three semantic kernels, rejection-boundary documentation, and prefill read-set expectations.

### C5R — P4b independent-review fix

- SHA: `1011e2c2fa99729a46efde5b5bbaf6daed975a2c`
- Parent: `d0c8883…`; stat: 5 files, +119/−44.
- Production: all pure scheduler-prefill chunks now take explicit baseline-full bypass with zero Window state; mixed prefill/decode still fails closed. Eagle3 decode first-pass remains Windowed.
- Tests: continuing prefill red/green for P4a/P4b, exact-vs-upper FIA carrier, full-exact minus frozen-`S` differential, and AST hashes for the three kernels defining step semantics.
- Documentation outcome: rejection cases with `E_s<S` remain intentional runtime fail-closed under Frozen I24; pure-prefill A/B read-set expectation is explicit.
- Result: P4b STATIC FINAL PASS.

The manifest contains the exact changed-file list and cherry-pick dependency for each commit.

## 7. What the independent reviews materially changed

| Phase | Key independent-review findings | Final disposition |
|---|---|---|
| P1 | Tautological state tests; over-normalized model identity; non-exhaustive warning reason; process-global warning scope; non-default projection geometry | fixed with real dispatch tests, corrected normalization/diagnostics, per-construction warning, and fail-closed geometry |
| P2 | Environment FlashComm bypass; mapping pointer cannot prove freshness; Eagle3 offset checked against itself; real BlockTables/int64 gaps | fixed or bounded; monotonic `mapping_epoch` became a hard P3 requirement |
| P3 | Target metadata argument could be omitted; slotted nested aliases could escape; consumer validation and hot D2H were not yet production decisions | mandatory Target isolation and slots traversal fixed; P4 later closed epoch provenance and single validation boundary; D2H remains NPU-profiler work |
| P4a | Initial upstream-dependent route violated repository boundary; profile/prefill startup reachability; local assembly parity; NumPy aliases; owner naming | redesigned Ascend-only; OFF uses upstream super path; Window ON uses explicit instance state with differential/drift tests; no vLLM dependency |
| P4b | Continuing chunked prefill aborted long prompts; FIA exact carrier lacked direct differential; E_s guard missed three kernels; rejection/prefill semantics underdocumented | pure prefill now baseline-bypasses; exact carrier and kernel guards added; fail-closed rejection and NPU phase expectations documented |

No review required a change to the core Frozen read/write separation. No Architecture Escalation remains open for P0→P4b static scope.

## 8. Superseded and prohibited designs

### 8.1 Upstream live-hook prototype

- vLLM commit: `0403469280c3d0f19c55cd1768e7e9d9e566a719`.
- Technical conclusion: an explicit vendor-neutral read-input hook can work.
- Delivery conclusion: **SUPERSEDED / NOT DELIVERABLE** because `R-REPO-01` forbids modifying vLLM or requiring a private vLLM patch.

### 8.2 Upstream-dependent Ascend prototype

- vLLM-Ascend commit: `e0dd8e8d14a287e4d5a69c54d7a617a6ae160529`.
- It depends on the upstream prototype and is not in the final branch ancestry.
- Delivery conclusion: **SUPERSEDED / DO NOT CHERRY-PICK**.

### 8.3 Other rejected transports

Module-global mutable state, `ContextVar`, temporary swapping of `self.block_tables` or input buffers, site-packages rewriting, Target-store transport, and Windowing slot mappings are prohibited. The accepted Ascend-only tradeoff is a small vendor-local metadata read-input assembly protected by OFF exact-super behavior, positive differential tests, and upstream AST/signature drift guards.

## 9. Current candidate routes

| Route | Static status | Exact boundary |
|---|---|---|
| DFlash | candidate | single executable dense-GQA group; serialized eager; graph NONE; async false; TP/DP/PP/PCP/DCP/SP=1; no DSA-CP/FlashComm; prefix cache off; mixed prefill/decode off |
| Eligible DSpark | candidate | same geometry/mode limits; excludes DeepSeek-V4 co-trained DSpark; default `sample_from_anchor=True` uses K, explicit false uses K+1 |
| Eagle3 | candidate | normalized Eagle3 only; configured static `K>0`; same single-group dense eager/parallel limits; Window begins on pure decode proposal; each pure scheduler-prefill chunk uses baseline full read |
| MTP | forced OFF | warning + baseline before validation/inventory/allocation |
| DeepSeek-V4 co-trained DSpark | forced OFF | warning + baseline before validation/inventory/allocation |
| DFlash2, plain Eagle, dynamic-K | unsupported | fail closed / no runtime enablement |
| Graph, Async, prefix-cache Window ON, mixed/function/chunked Window ON, multi-group, MLA/DSA/SFA/V4.1/native/recycling, parallel topologies | unsupported | remain closed; no silent disabling of the conflicting feature |

Static candidate does not mean runtime-supported. No company-NPU report is present in this freeze.

## 10. Static verification inherited from final phase notes

- P4b targeted Eagle3: `31 passed`.
- P4a eager integration: `40 passed`.
- Combined P1–P4b/backend/BlockTables/attention selection: `367 passed, 23 subtests passed`.
- Locally runnable `tests/ut/spec_decode`: `470 passed, 13 skipped, 2 subtests passed`.
- Full `tests/ut/spec_decode`: `472 passed, 13 skipped, 7 failed, 2 subtests passed`; the seven host failures are the unchanged `Invalid attention backend for None` environment failures and are not represented as PASS.
- Final review-fix Ruff, format, targeted Mypy, compileall, `git diff --check`, and executable repository hooks passed as recorded in the P4b notes.

These are historical implementation/review results copied from the canonical phase notes. The freeze operation itself does not rerun the product test suites; it validates repository identity and every recovery medium.

## 11. What remains unverified

`G-GQA-EAGER` and `G-AR-STEP` remain open for:

- actual NPU Draft Attention physical read-set;
- true device stream ordering and lease retirement timing;
- Draft proposals/logits and Target logits equality under controlled A/B;
- every-proposal D2H/synchronization and latency impact;
- Eagle3 serialized multi-step completion behavior;
- Graph capture/replay, Async/multi-lane, prefix cache, function/mixed/chunked Window ON, parallel topologies, and complex backends.

Therefore:

```text
P4a Ascend-only STATIC FINAL: PASS
P4b Eagle3 static-K STATIC FINAL: PASS
G-GQA-EAGER: OPEN — NPU REQUIRED
G-AR-STEP: STATIC CONTRACT PASS / NPU RUNTIME OPEN
Feature release: HOLD
```

## 12. Backup package contents

| Path | Purpose |
|---|---|
| `MRV2_P0_P4b_Implementation_Snapshot.md` | this canonical explanation and recovery guide |
| `MRV2_P0_P4b_Commit_Manifest.md` | exact Git lineage, files, stats, dependencies, prototypes |
| `MRV2_P0_P4b_Full_Diff.patch` | binary-safe emergency baseline→final tree patch |
| `format-patches/` | ordered 10-commit `git format-patch --binary` series |
| `MRV2_P0_P4b.bundle` | incremental offline Git bundle; requires baseline commit because source repo is shallow |
| `notes/` | unchanged copies of Final Design, Plan, phase notes, superseded P4 prototype note, P4a/P4b full diffs |
| `verification/` | exact audit and restore-test records |
| `SHA256SUMS` | integrity hashes for every packaged file except itself |

## 13. Deployment prerequisites

1. Use vLLM exactly at `84030bbe3d74d99bad477a3d2e37a973ccd8865c`; no upstream prototype patch.
2. Start vLLM-Ascend from exact baseline `841dc6ccdb134eab7ad09008859834d0572ee83f` or restore the final branch from this package.
3. Confirm Python/build dependencies match the target vLLM/vLLM-Ascend pair.
4. Keep runtime gates at the current fail-closed values until the NPU matrix in §18 succeeds.
5. Do not publish `draft_window_size` support based on CPU/static evidence alone.

## 14. Recovery A — Git remote

Use this only if the ten delivery commits are available on an accessible remote:

```bash
git -C /path/to/vllm-ascend fetch <remote> feature/p4b-eagle3-static-k
git -C /path/to/vllm-ascend switch --create feature/p4b-eagle3-static-k --track <remote>/feature/p4b-eagle3-static-k
git -C /path/to/vllm-ascend rev-parse HEAD
git -C /path/to/vllm-ascend rev-parse HEAD^{tree}
```

Expected HEAD is `1011e2c2fa99729a46efde5b5bbaf6daed975a2c`; expected tree is `7d165d585755766e7493e02f0281598e4aca3602`.

## 15. Recovery B — git format-patch + git am

This is the preferred portable recovery when an exact clean baseline checkout exists:

```bash
git -C /path/to/vllm-ascend switch --detach 841dc6ccdb134eab7ad09008859834d0572ee83f
git -C /path/to/vllm-ascend switch --create feature/p4b-eagle3-static-k-restored
git -C /path/to/vllm-ascend am /path/to/P4_freeze/format-patches/*.patch
git -C /path/to/vllm-ascend rev-parse HEAD^{tree}
```

The freeze rehearsal applied all ten patches without conflict. The restored commit hash differed because `git am` writes new committer metadata, but its tree was exactly `7d165d585755766e7493e02f0281598e4aca3602`, equal to final HEAD.

## 16. Recovery C — git bundle

Because the source clone is shallow, this is an **incremental bundle** with explicit prerequisite `841dc6ccdb134eab7ad09008859834d0572ee83f`. A bare `git clone MRV2_P0_P4b.bundle` correctly fails if that prerequisite object is absent. This is a Git-format limitation of the available shallow history, not bundle corruption.

Use it offline from any repository already containing the exact baseline object:

```bash
git -C /path/to/vllm-ascend cat-file -e 841dc6ccdb134eab7ad09008859834d0572ee83f^{commit}
git -C /path/to/vllm-ascend fetch /path/to/P4_freeze/MRV2_P0_P4b.bundle \
  refs/heads/feature/p4b-eagle3-static-k:refs/heads/feature/p4b-eagle3-static-k-restored
git -C /path/to/vllm-ascend switch feature/p4b-eagle3-static-k-restored
git -C /path/to/vllm-ascend rev-parse HEAD
git -C /path/to/vllm-ascend rev-parse HEAD^{tree}
```

`git bundle verify` reports the baseline prerequisite explicitly. The freeze rehearsal seeded a temporary shallow repo with that baseline, fetched the bundle with no network, and recovered exact HEAD `1011e2c…` and tree `7d165d58…`.

## 17. Recovery D — emergency single full-diff patch

Use only when commit metadata is not required:

```bash
git -C /path/to/vllm-ascend switch --detach 841dc6ccdb134eab7ad09008859834d0572ee83f
git -C /path/to/vllm-ascend apply --check /path/to/P4_freeze/MRV2_P0_P4b_Full_Diff.patch
git -C /path/to/vllm-ascend apply --index /path/to/P4_freeze/MRV2_P0_P4b_Full_Diff.patch
git -C /path/to/vllm-ascend diff --cached --stat
```

The patch is generated with `--binary --full-index --find-renames`. It was verified with `git apply --check` on a clean detached baseline worktree. It restores file content but not the ten original commits, authorship, or review boundaries; prefer format-patch or bundle.

## 18. Starting company-NPU validation

Use the exact frozen commits, single card, TP1, serialized eager, graph NONE, fixed seed, single executable dense-GQA group, no prefix cache, and the other static route constraints above. Compare Window OFF (A) against Window ON (B) without changing model, prompt, scheduler configuration, or Target state.

### 18.1 DFlash / eligible DSpark matrix

- short context `<=W`, long context `>W`, exact block boundary, non-boundary;
- DFlash `K+1`; DSpark default `sample_from_anchor=True` → K; explicit false → `K+1`;
- request reorder and finish/add if harness permits;
- pure scheduler-prefill should show baseline full reads; Window begins on eligible decode proposal.

Record CPU oracle visibility, P2 descriptor, materialized table, exact/upper lengths, full slot mapping, actual physical read-set, Draft proposal/logits, Target metadata/logits, final output, controlled D2H count, and profiler latency.

### 18.2 Eagle3 matrix

- configured static `K>=3` and fixed `W`;
- first decode pass through all AR steps;
- short/long context and `B=16,W=64,K=3,L0=64` future-column crossing;
- same-block and cross-boundary rejection;
- optional request reorder/finish-add where supported.

For every proposal record `L0`, configured K, `H=L0+K`, frozen `S`, each step `E_s/V_s`, FullSource columns, Window tables, full slot mappings, actual physical read-set, Draft proposals/logits, Target metadata/logits, outputs, stream/event timeline, and profiler data. Verify `S` never drifts within a proposal and every step rematerializes from FullSource.

Only successful physical-read, Target-invariant, lifecycle, and profiler evidence may close `G-GQA-EAGER` or `G-AR-STEP` for the exact tested route.

## 19. Historical document index

The package preserves unchanged copies under `notes/`:

- `MRV2_Speculative_Draft_Sliding_Window_Final_Design.md`
- `MRV2_Draft_Window_Implementation_Plan.md`
- `P1_Policy_Math_Types_Implementation_Notes.md`
- `P2_Inventory_FullSource_Provider_Implementation_Notes.md`
- `P3_Lease_Workspace_Transport_Store_Implementation_Notes.md`
- `P4a_Ascend_Only_Eager_Integration_Implementation_Notes.md`
- `P4b_Eagle3_StaticK_Eager_Integration_Implementation_Notes.md`
- `P4_Draft_Attention_Eager_Integration_Implementation_Notes.md` — explicitly superseded prototype history
- `P4a_Ascend_Only_Eager_Integration_Full_Diff.patch`
- `P4b_Eagle3_StaticK_Eager_Integration_Full_Diff.patch`

The original files remain in `/Users/wenqingzhang/Desktop/Note/MRV2/`; this freeze did not rewrite them.

## 20. Freeze audit conclusion

- vLLM remained at exact clean baseline `84030bbe…` with empty diff.
- vLLM-Ascend remained at exact clean final HEAD `1011e2c…`.
- No production commit, branch, or tracked production file was created or changed by the freeze.
- Full diff passed baseline `git apply --check`.
- All ten format patches restored the exact final tree.
- The incremental bundle passed `git bundle verify` and restored exact HEAD/tree when its documented baseline prerequisite was present.
- Every packaged file is covered by `SHA256SUMS`.

**P4 FREEZE BACKUP: VERIFIED**
