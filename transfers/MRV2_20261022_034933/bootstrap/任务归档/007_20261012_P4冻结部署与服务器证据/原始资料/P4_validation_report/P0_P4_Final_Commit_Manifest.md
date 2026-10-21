# MRV2 Draft Sliding Window P0–P4 Final Commit Manifest

> Generated from the real local Git history on 2026-10-13.  
> Delivery repository: `vllm-ascend` only.  
> Production source was not modified while producing this manifest.

## 1. Baselines

| Repository | Role | SHA | Tree / status |
|---|---|---|---|
| vLLM | immutable dependency | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`; clean |
| vLLM-Ascend | feature base | `841dc6ccdb134eab7ad09008859834d0572ee83f` | delivery series base |
| vLLM-Ascend | Final | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` | tree `7d165d585755766e7493e02f0281598e4aca3602`; clean |

Local branch: `feature/p4b-eagle3-static-k`.

## 2. Exact graph

```text
1011e2c2 (HEAD -> feature/p4b-eagle3-static-k, origin/feature/p4b-eagle3-static-k)
* fix(spec-decode): address P4b Eagle3 window review findings
* d0c88838 feat(spec-decode): integrate MRV2 draft windows for Eagle3 eager
* 4c1f6914 fix(spec-decode): address P4a Ascend-only review findings
* 0dd83e9f feat(spec-decode): integrate MRV2 draft windows in Ascend eager path
* 16727882 fix(spec-decode): address P3 draft-window review findings
* feab28f5 feat(spec-decode): add MRV2 draft-window runtime ownership
* fac84121 fix(spec-decode): address P2 draft-window review findings
* 83579675 feat(spec-decode): add MRV2 draft-window source inventory
* c58daea0 fix(spec-decode): address P1 draft-window review findings
* b12399ad feat(spec-decode): add MRV2 draft-window policy and math
* 841dc6cc feature base
```

## 3. Per-commit manifest

### 3.1 P1 implementation

| Field | Value |
|---|---|
| SHA | `b12399ad915415ce45105df5b0601848e7b70f6f` |
| Parent | `841dc6ccdb134eab7ad09008859834d0572ee83f` |
| Subject | `feat(spec-decode): add MRV2 draft-window policy and math` |
| Author/date | Lucian `<2207456347@qq.com>` / 2026-10-10 03:48:35 +08:00 |
| Stat | 8 files, `+1107/-1` |
| Phase/reason | P1 policy、pure math、types、baseline factory receiver |
| Tests | policy/math/factory/DFlash2/hidden-state regression |
| Later review | normalization、warning scope、factory parity、geometry和test oracle需修 |
| Cherry-pick | 只能作为10-commit series第1个；单独提交不是可发布Feature |

Files:

- `tests/ut/spec_decode/test_dflash2_v2.py`
- `tests/ut/spec_decode/test_draft_window.py` (new)
- `tests/ut/worker/test_extract_hidden_states_speculator_v2.py`
- `vllm_ascend/worker/v2/spec_decode/__init__.py`
- `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py`
- `vllm_ascend/worker/v2/spec_decode/dflash/speculator.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window.py` (new)
- `vllm_ascend/worker/v2/spec_decode/dspark/speculator.py`

### 3.2 P1 review-fix

| Field | Value |
|---|---|
| SHA | `c58daea0df34d1a6253dc34221d2a084b13affd5` |
| Parent | `b12399ad915415ce45105df5b0601848e7b70f6f` |
| Subject | `fix(spec-decode): address P1 draft-window review findings` |
| Stat | 4 files, `+213/-16` |
| Reason | DeepSeek adjudication fixes and stronger regressions |
| Files | `test_dflash2_v2.py`, `test_draft_window.py`, `spec_decode/__init__.py`, `draft_window.py` |
| Cherry-pick | Requires P1 implementation; mandatory for all later commits |

### 3.3 P2 implementation

| Field | Value |
|---|---|
| SHA | `83579675a997a44b293ff0ee1cb088a2eef0ed13` |
| Parent | `c58daea0df34d1a6253dc34221d2a084b13affd5` |
| Subject | `feat(spec-decode): add MRV2 draft-window source inventory` |
| Stat | 6 files, `+1880/-8` |
| Reason | inventory、canonical FullSource、valid counts、single-group direct-prefix provider |
| Files | `test_dflash2_v2.py`, `test_draft_window.py`, AR/DFlash/DSpark speculators, `draft_window.py` |
| Later review | FlashComm env、pointer freshness、configured K、real BlockTables和int64 coverage |
| Cherry-pick | Requires both P1 commits; not independently releaseable |

### 3.4 P2 review-fix

| Field | Value |
|---|---|
| SHA | `fac84121ddf84fe5a76cd739432cea3b61365a9b` |
| Parent | `83579675a997a44b293ff0ee1cb088a2eef0ed13` |
| Subject | `fix(spec-decode): address P2 draft-window review findings` |
| Stat | 2 files, `+223/-39` |
| Files | `tests/ut/spec_decode/test_draft_window.py`, `vllm_ascend/worker/v2/spec_decode/draft_window.py` |
| Cherry-pick | Requires P2 implementation; mandatory for P3+ |

### 3.5 P3 implementation

| Field | Value |
|---|---|
| SHA | `feab28f573b973a6b970cef56d1baa35191ab319` |
| Parent | `fac84121ddf84fe5a76cd739432cea3b61365a9b` |
| Subject | `feat(spec-decode): add MRV2 draft-window runtime ownership` |
| Stat | 6 files, `+1501/-18` |
| Reason | generation/mapping_epoch、workspace、lease、typed inputs、DraftMetadataStore |
| Files | `test_draft_window.py`, `test_draft_window_runtime.py` (new), AR/DFlash/DSpark speculators, `draft_window.py` |
| Later review | Target optionality、slotted alias；P4 provenance/validation/D2H prerequisites |
| Cherry-pick | Requires P1+P2 complete chain; not user-visible without P4 |

### 3.6 P3 review-fix

| Field | Value |
|---|---|
| SHA | `16727882744c935d9e899f7775353b57738852bc` |
| Parent | `feab28f573b973a6b970cef56d1baa35191ab319` |
| Subject | `fix(spec-decode): address P3 draft-window review findings` |
| Stat | 2 files, `+138/-14` |
| Files | `tests/ut/spec_decode/test_draft_window_runtime.py`, `vllm_ascend/worker/v2/spec_decode/draft_window.py` |
| Cherry-pick | Requires P3 implementation; this is P4a parent |

### 3.7 P4a Ascend-only implementation

| Field | Value |
|---|---|
| SHA | `0dd83e9f75d4b2d766126af3a7f92352e342f756` |
| Parent | `16727882744c935d9e899f7775353b57738852bc` |
| Subject | `feat(spec-decode): integrate MRV2 draft windows in Ascend eager path` |
| Stat | 12 files, `+2160/-50` |
| Reason | Ascend-only DFlash/DSpark eager live consumer、exact CPU seam、backend carrier |
| Production files | `attention_v1.py`, `attention/utils.py`, `worker/v2/attn_utils.py`, DFlash/DSpark speculators, `draft_window.py`, `draft_window_eager.py` (new) |
| Test files | `test_attention_v1.py`, `test_draft_window.py`, `test_draft_window_eager.py` (new), `test_draft_window_runtime.py`, `test_attn_utils_v2.py` |
| Later review | profile/prefill startup、NumPy alias、vendor-local differential/drift、rotating GPU view naming |
| Cherry-pick | Requires full P1–P3 chain; static only until exact NPU gate closes |

### 3.8 P4a review-fix

| Field | Value |
|---|---|
| SHA | `4c1f69146915f4f0ae5a6a61371ebfe181237d8f` |
| Parent | `0dd83e9f75d4b2d766126af3a7f92352e342f756` |
| Subject | `fix(spec-decode): address P4a Ascend-only review findings` |
| Stat | 5 files, `+323/-23` |
| Files | `test_draft_window.py`, `test_draft_window_eager.py`, `test_draft_window_runtime.py`, `draft_window.py`, `draft_window_eager.py` |
| Cherry-pick | Requires P4a implementation; this is P4b parent |

### 3.9 P4b Eagle3 implementation

| Field | Value |
|---|---|
| SHA | `d0c8883816f0e1fe333dc9f3197d3c4e47c475a5` |
| Parent | `4c1f69146915f4f0ae5a6a61371ebfe181237d8f` |
| Subject | `feat(spec-decode): integrate MRV2 draft windows for Eagle3 eager` |
| Stat | 5 files, `+2250/-5` |
| Reason | Eagle3 static-K first-pass、proposal-frozen anchor、per-step FullSource refresh/lifecycle |
| Production files | AR speculator, `draft_window.py`, `draft_window_eagle3.py` (new) |
| Test files | `test_draft_window.py`, `test_draft_window_eagle3.py` (new) |
| Later review | continuing prefill abort、FIA exact evidence、semantic-kernel drift guard、rejection documentation |
| Cherry-pick | Requires P4a Final and full P1–P3 chain |

### 3.10 P4b review-fix / Final

| Field | Value |
|---|---|
| SHA | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` |
| Parent | `d0c8883816f0e1fe333dc9f3197d3c4e47c475a5` |
| Subject | `fix(spec-decode): address P4b Eagle3 window review findings` |
| Stat | 5 files, `+119/-44` |
| Production files | `draft_window_eager.py`, `draft_window_eagle3.py` |
| Test files | `test_attention_v1.py`, `test_draft_window_eager.py`, `test_draft_window_eagle3.py` |
| Reason | all-pure-prefill baseline bypass、FIA exact-vs-upper contract、semantic kernel drift guard |
| Cherry-pick | Final series tip; do not omit |

## 4. Full range summary

Range:

```text
841dc6ccdb134eab7ad09008859834d0572ee83f
..
1011e2c2fa99729a46efde5b5bbaf6daed975a2c
```

`git diff --stat`：18 files，9706 insertions，10 deletions。

Production files:

- `vllm_ascend/attention/attention_v1.py`
- `vllm_ascend/attention/utils.py`
- `vllm_ascend/worker/v2/attn_utils.py`
- `vllm_ascend/worker/v2/spec_decode/__init__.py`
- `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py`
- `vllm_ascend/worker/v2/spec_decode/dflash/speculator.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eager.py`
- `vllm_ascend/worker/v2/spec_decode/draft_window_eagle3.py`
- `vllm_ascend/worker/v2/spec_decode/dspark/speculator.py`

Test files:

- `tests/ut/attention/test_attention_v1.py`
- `tests/ut/spec_decode/test_dflash2_v2.py`
- `tests/ut/spec_decode/test_draft_window.py`
- `tests/ut/spec_decode/test_draft_window_eager.py`
- `tests/ut/spec_decode/test_draft_window_eagle3.py`
- `tests/ut/spec_decode/test_draft_window_runtime.py`
- `tests/ut/worker/test_attn_utils_v2.py`
- `tests/ut/worker/test_extract_hidden_states_speculator_v2.py`

## 5. Dependency and recovery rules

- The ten commits are one ordered delivery series. Later commits are not independently cherry-pickable onto baseline.
- Review-fix commits are mandatory; do not cherry-pick only C1/C2/C3/C4/C5 feature commits.
- Preferred recovery: Freeze bundle or the verified `format-patches` series from
  `/Users/wenqingzhang/Desktop/Note/MRV2/P4_freeze`.
- Emergency full diff:
  `/Users/wenqingzhang/Desktop/Note/MRV2/P4_freeze/MRV2_P0_P4b_Full_Diff.patch`.
- Exact GitHub branch: `origin/feature/p4b-eagle3-static-k` at `1011e2c2...`.

## 6. Explicitly excluded history

| Commit/history | Status | Reason |
|---|---|---|
| vLLM prototype `0403469280c3d0f19c55cd1768e7e9d9e566a719` | **SUPERSEDED / NOT DELIVERABLE** | modifies upstream vLLM; violates R-REPO-01 |
| Ascend prototype `e0dd8e8d14a287e4d5a69c54d7a617a6ae160529` | **SUPERSEDED / NOT DELIVERABLE** | depends on private upstream prototype API; not Final ancestor |
| server debug tip `2a4856134648c068cab044ddfb11eb0e0d907453` and its debug lineage | **OBSERVATION ONLY** | instrumentation commits; all checked as non-ancestors of Final |

Do not squash/rebase/rewrite these Final SHAs when using the evidence package: trace and review records refer to
the exact ten-commit lineage.

## 7. Gate association

| Commit pair | Final phase status |
|---|---|
| P1 pair | FINAL PASS |
| P2 pair | FINAL PASS |
| P3 pair | FINAL PASS (CPU/static ownership; NPU lifetime remains open) |
| P4a pair | ASCEND-ONLY STATIC FINAL PASS; G-GQA-EAGER OPEN |
| P4b pair | STATIC FINAL PASS; single-request NPU scoped PASS; general G-AR-STEP OPEN |
| Overall | P0–P4 REQUIRED DELIVERY PARTIAL; release HOLD |
