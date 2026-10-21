# MRV2 Draft Sliding Window — P7-E Eager Completion Implementation Notes

## Document status

| Item | Value |
|---|---|
| Phase | P7-E independent review adjudicated; static final frozen |
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` (unchanged, clean) |
| vLLM-Ascend parent | `7599497ab2694c4cf343f61f82f449980d8bad93` |
| Parent tree | `b4f7d12bd24b0a7632f9e606b29703a7c96278de` |
| P7-E commit | `7feb6def64d2dd483627dab6ee5cf7b05d7503f0` |
| Review-fix commit | `4753742ab181920292c504a79eedecf9b428ae1b` |
| P7-E final tree | `b7e525c3c9d45617ad1023ad45c6948c466a3631` |
| Branch | `feature/p7-eager-completion` |
| Graph Track | **FROZEN at P6/P6A** |
| NPU status | no new P7 NPU evidence |
| Release | **HOLD** |

This file now includes the independent-review adjudication and static freeze. It
does not claim runtime support for any newly inventoried route.

## 1. What P7-E solves

P1–P4 built and connected the exact eager read plane. P5–P6 added Graph-side
contracts, but P6A found no authorized existing pre-capture injection seam. The
owner then split the work into a frozen Graph Track and an active Eager Track.

P7-E closes the *local classification and ownership foundation* for the Eager
Track:

1. every named method/backend/group/topology/execution mode gets one explicit
   capability status;
2. the decision is made before FullSource/workspace/lease allocation;
3. a typed topology fingerprint follows an admitted P3 generation;
4. DCP interval projection is defined as `local(E)-local(S)` without enabling DCP;
5. a bounded host async state machine demonstrates multi-lane ownership while
   production async remains fail closed;
6. unresolved general serving is recorded as an owner/release blocker.

P7-E does **not** make all routes positive. Completing the matrix means each route
has an auditable outcome, including a reasoned `FAIL_CLOSED` or `OWNER_BLOCKED`.

## 2. Non-goals and hard boundaries

P7-E does not:

- modify vLLM;
- touch Graph capture, P5/P6 provider installation, replay/update carrier, or Graph gates;
- enable `FULL`, `FULL_DECODE_ONLY`, or `PIECEWISE`;
- enable DSA, SFA, MLA, native/recycling, multi-group, parallel, async, prefix, or mixed serving;
- change positions, query layout, slot mapping, Target metadata, or canonical FullSource;
- choose a product policy for general serving versus single-active-request admission;
- claim NPU stream ordering, physical reads, performance, or async safety.

## 3. Source preflight conclusions

The detailed inventory is in `P7_Eager_Source_Inventory.md`. The important source
facts are:

- the only existing positive Window consumer is the P4 single executable
  dense-GQA/FIA direct-prefix route;
- DFlash and eligible DSpark use the P4a one-shot timing; Eagle3 static-K uses
  the P4b proposal/step timing;
- DSA carries SAS/QLI/compressor/SWA-derived state, SFA has main/indexer carriers,
  MLA has distinct exact/upper/padding consumers, and recycling has residency/
  eviction/in-flight state; none has the typed intersection contract required by
  the Frozen Design;
- no `dsa_v41.py` exists in this checkout;
- homogeneous multi-group lacks per-gid projection and live consumers;
- heterogeneous multi-group still requires owner semantics;
- pinned async scheduling can overlap batches, but the P4 owner is serialized and
  no production NPU completion event is bound to the Window lease;
- mixed prefill/decode still raises in the live P4 path and server evidence shows
  that this can abort EngineCore.

## 4. Files changed

| File | Before | After | Why |
|---|---|---|---|
| `worker/v2/spec_decode/draft_window_eager_capability.py` | absent | status enum, topology fingerprint, evaluator, DCP interval projection | one auditable decision before Window allocation |
| `worker/v2/spec_decode/draft_window_async.py` | absent | bounded host async lane/state owner | prove host lifecycle without enabling live async |
| `worker/v2/spec_decode/draft_window.py` | serialized lane and no topology identity | capability preflight, topology propagation, explicit lane, pending-reader polling | bind route identity to the existing P3 owner and support host lifecycle proof |
| `tests/ut/spec_decode/test_draft_window_eager_capability.py` | absent | method/backend/group/topology/parallel/DCP decisions | contract and negative-gate coverage |
| `tests/ut/spec_decode/test_draft_window_async.py` | absent | multi-lane lifecycle, completion, abort, pressure, ABA | state-machine regression coverage |
| `tests/ut/spec_decode/test_draft_window.py` | P1–P3/P4 contracts | production fingerprint and pre-FullSource async rejection tests | prove the evaluator is on the real source path |

No Graph file, eager metadata builder, speculator forward, scheduler, Target code,
or vLLM file changed.

## 5. Capability decision flow

```text
P1 policy
  ├─ CONFIG_OFF ------------------------------> CONFIG_OFF / zero P7 state
  ├─ FORCED_OFF ------------------------------> FORCED_OFF / zero P7 state
  └─ ELIGIBLE_ON
        ↓
P2 inventory + runtime context
        ↓
evaluate_draft_window_eager_capability()
  ├─ owner-contract gap ----------------------> OWNER_BLOCKED
  ├─ unsupported/unsafe source or topology ---> FAIL_CLOSED
  ├─ host-only lifecycle ---------------------> STATIC_READY
  └─ exact single dense serialized eager -----> READY_FOR_NPU
        ↓ only READY_FOR_NPU
FullSource → provider → P3 runtime/workspace/lease → P4 eager consumer
```

`require_live_materialization()` is the enforcement point. It accepts only
`READY_FOR_NPU`; `STATIC_READY` is intentionally not enough.

## 6. Status definitions

| Status | Meaning | Can allocate P2/P3 live state? |
|---|---|---|
| `CONFIG_OFF` | no user Window request | no |
| `FORCED_OFF` | policy requires baseline behavior | no |
| `OWNER_BLOCKED` | product/semantic decision is absent | no |
| `FAIL_CLOSED` | current source lacks a safe verified contract | no |
| `STATIC_READY` | host/type/state contract exists, device/live binding does not | no |
| `READY_FOR_NPU` | exact local route can enter existing P4 live path and needs/retains NPU gate | yes |

No P7 status is named `SUPPORTED`.

## 7. Topology fingerprint

`P7EagerTopologyFingerprint` is immutable and records method, runtime route,
semantic attention-backend hardware family, backend/builder identities, global
gids, layouts, block geometry, all requested parallel dimensions, graph mode,
async, prefix cache, provider schema, and lane.

It is attached to `DraftWindowGenerationIdentity`; async handles and each lane's
P3 runtime must carry the exact same value. The final runtime validates it before
materialization/refresh and before active inputs are consumed, so a mismatched
lane/topology cannot write backing, bind, or continue a generation.

See `P7_Eager_Topology_Fingerprint_Spec.md` for the field contract.

## 8. Method decisions

| Method | Decision |
|---|---|
| Eagle3 static K | exact P4b dense serialized eager route is `READY_FOR_NPU`; scoped P4b single-request NPU evidence remains separate |
| DFlash | exact P4a dense serialized eager route is `READY_FOR_NPU`; `G-GQA-EAGER` remains NPU-open |
| eligible DSpark | same as DFlash, with actual P4a query-width contract |
| MTP | `FORCED_OFF` before downstream Window state |
| DeepSeek-V4 co-trained DSpark | `FORCED_OFF` before downstream Window state |
| plain Eagle | owner semantics are absent (`OWNER_BLOCKED`); current P1 production behavior is configuration-time `FAIL_CLOSED`, never silent inheritance from Eagle3 |
| Eagle3 dynamic-K | `OWNER_BLOCKED`; proposal horizon has no frozen contract |
| DFlash2 | `FAIL_CLOSED`; inheritance does not establish a consumer contract |

## 9. Backend and multi-group decisions

Only `DENSE_GQA_DIRECT_PREFIX` can reach the existing live P4 consumer.

Complex layouts fail before FullSource because P7 cannot reduce their semantics to
`min(W, retention)`. Their required formula remains:

```text
V_final = V_draft ∩ V_native ∩ V_resident
```

The missing typed carrier/provider for that intersection is named in each decision.
Homogeneous multi-group is `FAIL_CLOSED`; heterogeneous multi-group is
`OWNER_BLOCKED`. P7 does not change the canonical absolute anchor and never applies
a Window to a prior Window.

The hardware-family decision is equally explicit. Only
`AttentionBackendFamily.STANDARD` can reach a positive P7-E candidate.
`COMPATIBILITY` (the 310P family) fails before FullSource. Independently, the
current 310P model runner/model state already reject every speculative method
except MTP, and MTP is P1 `FORCED_OFF`; the new family gate makes the capability
contract auditable and future-drift resistant rather than fixing a currently
reachable Window route.

## 10. Parallel eager contract

All live parallel dimensions remain `FAIL_CLOSED`. The fingerprint nevertheless
captures them so a future caller cannot masquerade as TP1/DP1.

The only new mathematical seam is DCP projection:

```text
local_visible(rank) = local_prefix(E, rank) - local_prefix(S, rank)
```

Tests cover non-divisible and interleaved intervals and demonstrate why
`V / dcp_world_size` is wrong. This helper does not build a rank-local table or
bind an operator, so DCP is not enabled.

FlashComm configuration/environment only determines a mode bit in the fingerprint;
it never transports generation or Window state.

## 11. Async host foundation

`DraftWindowEagerAsyncPool` owns a fixed tuple of independent P3 runtime/workspace
instances. Each lane has a stable backing and at most one active handle. The state
machine is:

```text
FREE → ACQUIRED → MATERIALIZED → BOUND → SUBMITTED
     → CONSUMER_COMPLETE → RETIRED → FREE
```

It covers two or more in-flight generations, delayed and reverse completion,
bounded pressure, abort-before-submit, abort-after-submit, completion-query
exceptions, stale handles, request replacement/reorder, and backend-derived buffer
lifetime. It uses explicit fake completion tokens rather than sleeps.

At `BOUND`, every backend-derived tensor is rejected if its storage aliases the
Window workspace, canonical FullSource (table or valid-count owners), or any nested
Target tensor/NumPy/mutable storage. Validation failure aborts the active P3
generation and retires the handle. This is a host ownership contract; there is
still no live backend-derived-buffer consumer or NPU completion event.

There is intentionally no speculator installation point. The live capability
evaluator returns `STATIC_READY` for async and rejects it before FullSource. See
`P7_Eager_Async_State_Machine.md`.

## 12. Request lifecycle and mixed serving

Current P4 behavior remains:

- pure scheduler prefill: baseline full-context bypass, zero Window generation;
- pure decode exact route: existing P4 Window path;
- mixed prefill/decode: `NotImplementedError`.

Server evidence demonstrates a service-wide EngineCore abort for mixed arrival.
No owner decision exists to implement general serving or to productize an early
single-active-request admission restriction. P7 therefore records:

```text
G-MIXED: OWNER_BLOCKED
FEATURE RELEASE: HOLD
```

This is not deferred as an acceptable runtime failure; it is a release blocker.

## 13. Read/write invariant audit

| State | P7 effect |
|---|---|
| Draft read table/length | unchanged for the existing P4 live route; newly fingerprinted |
| canonical FullSource | borrowed read-only; no alias from async workspace |
| physical KV allocation | unchanged |
| slot mapping | unchanged and still full/absolute |
| positions/query layout | unchanged |
| Target metadata/store | unchanged |
| Graph provider/capture/replay | unchanged; frozen |

## 14. Tests

Exact post-commit local results:

| Command / scope | Result | Limitation |
|---|---|---|
| P1–P7 targeted, including P5/P6 graph-host regressions and DFlash2 | `360 passed` | host/static only |
| full `tests/ut/spec_decode` | `588 passed, 13 skipped, 7 failed, 2 subtests passed` | seven failures are retained failures, not PASS; all stop in upstream `selector.py:208` with `Invalid attention backend for None` while constructing VWN and do not traverse P7 |
| full `tests/ut/attention` | `472 passed, 3 skipped, 24 subtests passed` | host/static; includes complex backend regressions |
| full `tests/ut/distributed` | `572 passed, 284 subtests passed` | required unsandboxed localhost-port bind; host/static |
| `tests/ut/worker/v2` | `31 passed, 18 subtests passed` | host/static |
| BlockTables | `14 passed, 21 subtests passed` | current real test paths |
| attn_utils + attention_v1 targeted | `86 passed, 2 subtests passed` | overlaps the full attention suite |
| 310P v2 model-runner regression | `41 passed` | confirms non-MTP speculative methods are rejected before Window infrastructure |
| Ruff check | PASS | six changed files |
| Ruff format check | PASS | six changed files |
| targeted Mypy `--follow-imports=skip` | PASS | three production modules |
| compileall | PASS | spec_decode and changed tests |
| `git diff --check 7599497..HEAD` | PASS | P7 commit range |
| locally executable hooks | PASS | ruff, format, codespell, typos, filenames, package-init, logger, forbidden imports, boolean-context-manager, long-functions |
| aggregate pre-commit | environment-blocked | actionlint Go dependencies timed out at `proxy.golang.org`; gitleaks is unavailable and its fallback needs missing `wget`; neither is reported PASS |

The first worker command attempted during validation named two nonexistent test
paths (`test_dcp.py` / `test_pcp.py`) and exited before collection. It was corrected
to the real `test_dcp_manager.py`, `test_pcp_manager_v2.py`, and
`test_mtp_pcp_speculator_v2.py` paths, which are included in the `158 passed` row.

Principal P7 tests prove:

| Test family | What it proves | What it does not prove |
|---|---|---|
| capability decisions | every inventoried route has one state; rejection precedes live allocation | backend/NPU correctness |
| topology identity | immutable route/lane identity follows a generation | distributed rank correctness |
| DCP arithmetic | correct integer projection formula | rank-local table/consumer binding |
| async pool | host ownership, pressure, completion, abort, ABA | NPU event or stream ordering |
| production integration | exact route carries fingerprint; async stops before FullSource | async live forward |
| P1–P6 regressions | prior contracts remain intact | device behavior |

Known full-suite host failures in VWN backend construction must remain recorded as
environment failures, not PASS.

## 15. Runtime and evidence status

- P4b retains its already audited *scoped* Node133/A2 single-request NPU evidence.
- P4a DFlash/DSpark remain NPU-open.
- P7 added no device evidence for complex backend, parallel, async, or mixed serving.
- Node133/A2 evidence must not be generalized to Node101/A3.
- `READY_FOR_NPU` means a candidate for an exact campaign, not supported/released.

The campaign matrix is `P7_Eager_NPU_Test_Matrix.md`.

## 16. Developer reading order

1. `draft_window_eager_capability.py`: states, fingerprint, evaluator, DCP seam.
2. `draft_window.py::build_draft_window_source_capability`: real pre-allocation enforcement.
3. `draft_window.py::DraftWindowGenerationIdentity`: topology binding.
4. `draft_window.py::DraftWindowRuntimeState`: lane and pending-reader ownership.
5. `draft_window_async.py`: host-only multi-lane lifecycle.
6. `test_draft_window_eager_capability.py`: route matrix and arithmetic oracle.
7. `test_draft_window_async.py`: state transitions and failure cleanup.
8. `P7_Eager_Capability_Matrix.md`: product-facing final local matrix.

## 17. Independent Review Resolution

### 17.1 Review metadata

| Item | Value |
|---|---|
| Review | `P7_Eager_DeepSeek_Independent_Review.md` |
| Original commit | `7feb6def64d2dd483627dab6ee5cf7b05d7503f0` |
| Review-fix commit | `4753742ab181920292c504a79eedecf9b428ae1b` |
| Final tree | `b7e525c3c9d45617ad1023ad45c6948c466a3631` |
| Adjudication date | 2026-10-14 (Asia/Shanghai) |

### 17.2 Resolution table

| ID | Severity | Reviewer finding | Resolution | Evidence | Code / document action |
|---|---|---|---|---|---|
| F-01 | Major | Capability lacked a platform dimension, so 310P would be classified `READY_FOR_NPU`. | `ACCEPTED` after P8 factual correction | Missing family identity and live reachability risk were real. P8 source recheck showed `_init_speculator_310p` delegates non-MTP methods to the baseline factory; the original P7 “MTP-only startup” rationale was false. | Added typed `AttentionBackendFamily`; only `STANDARD` is eligible and `COMPATIBILITY` fails before FullSource. Unit/production-order regressions are the actual defense. |
| F-02 | Minor | Async `backend_derived_buffers` had no alias/owner validation. | `PARTIALLY_ACCEPTED` | The host contract gap was real; there is no production installation/consumer, so no current live Target/write corruption path was demonstrated. | Reject storage alias with Window backing, canonical FullSource, or nested Target state; validation failure aborts/retire state. Added three red-to-green alias tests. |
| F-03 | Minor | Topology fingerprint was recorded but not enforced in the standard serialized runtime. | `ACCEPTED` | A runtime's fingerprint could be changed after generation creation; source identity could otherwise mask the missing invariant. | Validate topology before materialize/refresh and before active-input use. Added a same-source pre-write drift regression. |
| Q-01 | Question | Plain Eagle wording should distinguish owner policy from actual runtime rejection. | `OWNER_BLOCKED` | Owner semantics remain undefined; current `resolve_draft_window_policy()` rejects plain Eagle at configuration time. | Matrix now says `OWNER_BLOCKED / configuration-time FAIL_CLOSED`; no production expansion. |
| Q-02 | Question | Mixed serving remains a service-wide abort risk. | `OWNER_BLOCKED` | Runtime still raises before epoch creation; no admission/general-serving owner choice exists. | Retain `G-MIXED: OWNER_BLOCKED / RELEASE_BLOCKER`; no scheduler scope expansion. |
| Q-03 | Question | Consider a model-wide DeepSeek-V4 Gate. | `INSUFFICIENT_EVIDENCE` | Current architecture inventories the actual Draft consumer; target model identity alone does not prove DSA/SFA/MLA. Actual complex compositions already fail closed and V4 co-trained DSpark is forced off. | Narrowed documentation; no unsupported model-name Gate added. |

### 17.3 Red-to-green evidence

Before the production fix, the five new regressions failed exactly at the missing
contracts: one `COMPATIBILITY` route returned `READY_FOR_NPU`, three derived-buffer
aliases were accepted, and one topology drift wrote/continued instead of failing.
After the fix, those regressions and the existing 310P early-gate check pass. The
full targeted P1–P7 set is `360 passed`.

### 17.4 Final invariant audit

- vLLM remains exact and unmodified at `84030bbe...`.
- No Graph/capture/provider source was changed; all Graph modes remain fail closed.
- `CONFIG_OFF`/`FORCED_OFF` still create zero P7 state.
- Only `STANDARD` hardware-family candidates can reach FullSource; 310P
  `COMPATIBILITY` fails earlier.
- topology mismatch fails before workspace write and again before active consume.
- async derived buffers cannot alias Window, canonical FullSource, or Target state.
- slot mapping, positions, query layout, canonical FullSource, Target metadata, and
  KV write behavior remain unchanged.
- Complex backends, parallel, live async, prefix, and mixed serving are not enabled.

### 17.5 Final freeze

```text
P7-E METHOD MATRIX: COMPLETE
P7-E BACKEND MATRIX: COMPLETE
P7-E PARALLEL MATRIX: COMPLETE
P7-E ASYNC STATIC: PASS
G-MIXED: OWNER_BLOCKED / RELEASE_BLOCKER
P7-E CAPABILITY MATRIX: COMPLETE
P7-E NPU: NOT VERIFIED
GRAPH TRACK: FROZEN
P7-E STATIC FINAL: PASS
P8-E ENTRY: READY
FEATURE RELEASE: HOLD
```

`PASS` means the matrix is complete, positive host contracts are static-correct,
and every other route rejects honestly. It is not a support or release claim.

