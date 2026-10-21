# MRV2 Draft Sliding Window — P0–P7 Implementation Snapshot

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

## 1. What this feature is

`draft_window_size` gives MRV2 speculative Draft Attention a bounded, recent read
view while retaining full/global Target and write state. It migrates the intended
MRV1 behavior without copying MRV1's repeated-window, multi-group alias, dynamic-K,
or ownership defects.

```text
Draft read:  canonical full state → block-aligned recent view
Target read: full
KV write:    full absolute slot
positions/query layout: absolute and unchanged
```

## 2. Frozen invariants

1. Only Draft read table/length may change.
2. Canonical block tables, KV allocation, positions, query starts and full slot
   mapping remain full/global.
3. Target metadata owner, nested storage and behavior remain unchanged.
4. MTP and DeepSeek-V4 co-trained DSpark are forced OFF before numeric validation.
5. Window materialization always reads canonical FullSource, never a prior Window.
6. `mapping_epoch` is caller-owned and monotonic; pointer/object identity is not
   freshness.
7. Generation, ordered requests, gid, provider, source, phase/step, lane and topology
   must match at consumption.
8. Active backing cannot be overwritten before the reader completes.
9. Production modifies vllm-ascend only; vLLM remains exact baseline.
10. Unsupported Graph/backend/parallel/async/prefix/serving routes fail closed.

## 3. Architecture by phase

```text
P1 policy + integer math + typed plans
  ↓
P2 actual consumer inventory + canonical FullSource + valid counts + provider
  ↓
P3 generation/mapping_epoch + stable workspace + lease + typed inputs + Draft store
  ↓
P4a DFlash / eligible DSpark exact serialized eager consumer
  or
P4b Eagle3 static-K first-pass + per-step eager consumer
  ↓
P7 exact Eager capability/topology Gate
```

P5/P6 built Graph host-static identity/carrier contracts, but P6A found no existing
authorized Ascend-owned startup pre-capture injection seam. The owner froze Graph at
P6/P6A and activated only the Eager Track. P7 then completed an honest matrix:
positive exact routes are `READY_FOR_NPU`; every other route is forced off, owner
blocked, fail closed, or host-static only.

## 4. Configuration-to-operator flow

```text
draft_window_size
→ resolve policy
→ CONFIG_OFF / FORCED_OFF / eligible
→ P7 hardware/backend/method/group/topology/mode capability decision
→ P2 inventory and canonical FullSource
→ P1 scalar plan + P2 descriptor
→ production mapping_epoch + ordered request fingerprint
→ P3 generation + lease + stable workspace
→ immutable DraftMetadataInputs
→ validate_for(expected identity)
→ DraftMetadataStore
→ P4a or P4b Draft-private metadata
→ Ascend metadata builder
→ FIA Draft operator
```

The unmodified world is parallel:

```text
scheduler/KV allocation
→ canonical full table
→ absolute positions/query layout
→ full slot_mapping and physical KV write
→ Target metadata/Attention/logits
```

## 5. Current exact positive candidates

- normalized Eagle3, configured static K;
- normalized DFlash;
- eligible non-V4 co-trained DSpark;
- one executable dense GQA/FIA direct-prefix gid;
- `AttentionBackendFamily.STANDARD`;
- graph NONE / enforce eager;
- async false;
- TP=DP=PP=PCP=DCP=1;
- SP, DSA-CP, FlashComm and prefix cache off;
- pure decode after all-prefill baseline bypass.

These rows are `READY_FOR_NPU`, not `SUPPORTED`.

## 6. Explicit non-support and owner blockers

- Forced OFF: MTP and DeepSeek-V4 co-trained DSpark.
- Owner blocked: plain Eagle, Eagle3 dynamic K, heterogeneous multi-group, mixed/
  general serving.
- Fail closed: DFlash2, DSA/SFA/MLA/native/recycling, homogeneous multi-group,
  parallel dimensions >1, SP/DSA-CP/FlashComm, prefix cache and 310P compatibility.
- Host static only: async bounded ownership model; no live binding/event.
- Graph frozen: FULL, FULL_DECODE_ONLY and PIECEWISE.

## 7. Runtime evidence boundary

Old Node133/A2 evidence at P4 final `1011e2c2...` proves a scoped Eagle3 K=3,
W=64, TP1 eager, single-request L3/L4 path and observed write/Target isolation. It
does not prove P7 final, DFlash, DSpark, A3/A5, batch>1, persistent row reuse, L5
kernel reads, device lifetime, performance, or release readiness. Mixed serving was
observed to abort EngineCore and remains a release blocker.

## 8. Local P8 acceptance result

At P7 final:

- two repository SHAs/trees and clean states match;
- the exact nine-file P1–P7 targeted suite recorded in `P8_Local_Test_Results.md`
  passes 360 tests;
- Attention, distributed, worker, BlockTables, attn_utils and 310P regressions pass;
- full spec_decode has 588 passes and seven retained VWN host-environment failures;
- Ruff, format, targeted Mypy, compileall, diff-check and local hooks pass;
- no new production fix or commit was needed.

The complete command/result ledger is in `P8_Eager_Delivery_Acceptance_Report.md`.

## 9. Delivery and recovery

This package provides:

- binary-safe base-to-final full diff;
- 16 ordered `git format-patch --binary` files;
- an incremental Git bundle carrying the final branch above the exact base;
- commit manifest and snapshot;
- canonical notes/evidence copies;
- SHA256SUMS.

Preferred offline recovery from an existing clean base repository:

```bash
git checkout 841dc6ccdb134eab7ad09008859834d0572ee83f
git fetch /path/to/P8_eager_freeze/MRV2_P0_P7.bundle \
  refs/heads/feature/p7-eager-completion:refs/heads/restored-p7
git checkout restored-p7
git rev-parse HEAD HEAD^{tree}
```

The source checkout is shallow. Network access was unavailable when attempting to
unshallow it, so the bundle deliberately declares `841dc6cc...` as a prerequisite.
`git bundle verify` and an actual fetch/checkout from a clean base clone both
reconstructed the exact final commit and tree. It is not a standalone-clone bundle.

Review-preserving recovery:

```bash
git checkout 841dc6ccdb134eab7ad09008859834d0572ee83f
git am /path/to/P8_eager_freeze/format-patches/*.patch
git rev-parse HEAD HEAD^{tree}
```

Emergency tree-only recovery:

```bash
git checkout 841dc6ccdb134eab7ad09008859834d0572ee83f
git apply --check /path/to/P8_eager_freeze/MRV2_P0_P7_Full_Diff.patch
git apply /path/to/P8_eager_freeze/MRV2_P0_P7_Full_Diff.patch
```

Expected final tree is `b7e525c3c9d45617ad1023ad45c6948c466a3631`.

## 10. Independent-review finalization

Independent delivery review completed with no production correctness/Gate finding.
Six documentation/evidence issues were accepted, one server-only debug SHA remains
insufficient for local source inspection, and two inputs remain owner-blocked. The
package now records the exact 360-test command, correct 310P baseline-factory fact,
correct 51/71 config result, DSpark HF-config mechanism, negative launch flags, a
dedicated write-side slot diagnostic, and explicit model-identity prerequisites.
Final production SHA/tree and all Frozen invariants are unchanged.

## 11. Next authorized action

Independent delivery review and Codex adjudication are complete. The next authorized
action is the company-server comprehensive Eager NPU campaign after owner-supplied
mandatory model/device/W/K inputs. It does not authorize Graph, mixed-serving,
parallel, complex-backend or live-async implementation.

```text
READY FOR COMPREHENSIVE EAGER NPU: YES
G-MIXED: OWNER_BLOCKED / RELEASE_BLOCKER
EAGER RELEASE: HOLD
FULL FEATURE RELEASE: HOLD
```
