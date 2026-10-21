# MRV2 Draft Sliding Window — P7-E Eager Source Inventory

## Document status

| Item | Value |
|---|---|
| Date | 2026-10-14 (Asia/Shanghai) |
| Stage | P7-E independent review adjudicated; static final frozen |
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c`, clean, unmodified |
| vLLM-Ascend parent | `7599497ab2694c4cf343f61f82f449980d8bad93` |
| P7-E commit | `7feb6def64d2dd483627dab6ee5cf7b05d7503f0` |
| Review-fix commit | `4753742ab181920292c504a79eedecf9b428ae1b` |
| Final tree | `b7e525c3c9d45617ad1023ad45c6948c466a3631` |
| Repository rule | `R-REPO-01`: production modifies `vllm-ascend` only |
| Graph Track | Frozen at P6/P6A; B/C not authorized |
| NPU status | No P7-E NPU run; existing P4 evidence is scoped separately |

This inventory answers what the exact checkout can express safely. A route marked
`FAIL_CLOSED` is an intentional production result, not an unfinished positive
implementation. No local result in this document is named `SUPPORTED`.

## 1. Inherited P1–P6 data flow

```text
P1 policy and integer Window plan
  -> P2 actual consumer inventory and canonical FullSource
  -> P3 generation / mapping_epoch / workspace / lease / typed inputs / Draft store
  -> P4a DFlash or eligible DSpark serialized eager consumer
  -> P4b Eagle3 static-K serialized eager per-step consumer
```

P7-E does not redesign that read plane. It adds:

```text
exact inventory + runtime context
  -> P7EagerCapabilityDecision
  -> P7EagerTopologyFingerprint
  -> READY_FOR_NPU only
  -> existing P2/P3/P4 eager path
```

`CONFIG_OFF`, `FORCED_OFF`, `OWNER_BLOCKED`, `FAIL_CLOSED`, and `STATIC_READY`
all stop before live FullSource/workspace allocation. `STATIC_READY` is used only
for the bounded host async lifecycle; it is not an enablement state.

## 2. Method inventory

| Method/route | Exact source fact | Read width/anchor fact | P7-E state | Reason |
|---|---|---|---|---|
| Eagle3 static K | `autoregressive/speculator.py` + `draft_window_eagle3.py` | configured K; proposal-frozen `S`; per-step exact `E_s`; canonical FullSource refresh | `READY_FOR_NPU` for exact single-group serialized route | P4b carrier exists; single-request NPU L3/L4 evidence is scoped to P4 Final SHA |
| DFlash | `dflash/speculator.py` + `draft_window_eager.py` | fixed DFlash query width `K+1`; `future_offset=0` | `READY_FOR_NPU` for exact single-group serialized route | P4a static carrier exists; no Window-ON NPU evidence on the evidence machine |
| eligible DSpark | `dspark/speculator.py` + `draft_window_eager.py` | actual query width: default anchor sampling uses K, explicit false uses K+1 | `READY_FOR_NPU` for exact single-group serialized route | only non-DeepSeek-V4 co-trained DSpark passes policy |
| MTP | `resolve_draft_window_policy()` | n/a | `FORCED_OFF` | forced off before numeric validation and P2/P3/P7 state |
| DeepSeek-V4 co-trained DSpark | `resolve_draft_window_policy()` | n/a | `FORCED_OFF` | model/method product rule; zero Window infrastructure |
| plain Eagle | P1 policy rejects | no owner-approved Window semantics | `OWNER_BLOCKED` and runtime fail closed | shared AR mechanics do not authorize the method |
| Eagle3 dynamic K | P1 future-offset validation and P7 decision | no stable proposal horizon contract | `OWNER_BLOCKED` and runtime fail closed | configured/scheduled K must not be guessed |
| DFlash2 | `dflash2/speculator.py` inherits implementation classes, but P2 records route `dflash2` explicitly | DFlash inheritance is not consumer evidence | `FAIL_CLOSED` | no P7-E Window metadata-consumer contract |

Plain Eagle's product semantics remain `OWNER_BLOCKED`, while the actual current
production outcome is configuration-time `FAIL_CLOSED` in P1. These are different
facts: missing owner semantics do not make the route executable.

## 3. Reference backend: dense GQA / FIA

The only positive local candidate remains:

- one executable global gid;
- exact `FullAttentionSpec`;
- `AscendAttentionBackend` and `AscendAttentionMetadataBuilder`;
- direct-prefix block-table carrier;
- Graph mode `NONE` (or `enforce_eager` producing effective `NONE`);
- async false;
- TP/DP/PP/PCP/DCP all 1;
- SP, DSA-CP, FlashComm, and prefix cache false;
- serialized lane 0.

P4 changes only Draft read table/length. Slot mapping, absolute positions,
query layout, Target metadata, canonical FullSource, KV allocation, and KV writes
remain full-context state.

Existing runtime evidence must remain scoped:

- P4a DFlash/DSpark Window ON: static verified, NPU OPEN.
- P4b Eagle3 static K=3, W=64, Qwen3-4B + Eagle3, Node133 A2,
  TP1 serialized eager: single-request L3/L4 evidence exists.
- P4b `G-AR-STEP`: still OPEN because controlled multi-request, independent
  slot oracle, device lifetime, and L5 kernel read evidence remain incomplete.

### 3.1 Hardware-family inventory

The final P7 runtime context records the semantic
`AttentionBackendFamily`, not a model-name string or direct `is_310p` branch.

| Family | Current devices/profile | P7-E result | Independent source fact |
|---|---|---|---|
| `STANDARD` | A2/A3/A5 profiles | may continue to the remaining route gates | `READY_FOR_NPU` still requires exact method/backend/topology checks and device-specific NPU evidence |
| `COMPATIBILITY` | 310P profile | `FAIL_CLOSED` before FullSource | The P7 hardware-family Gate rejects Window; the 310P patch delegates non-MTP methods to the baseline speculator factory. |

P8 delivery review corrected the earlier P7 adjudication: non-MTP 310P startup is
delegated to the baseline factory and is not generally MTP-only. The explicit family
Gate is therefore the relevant protection preventing subclass/profile drift from
turning Draft Window positive before FullSource.

## 4. DSA-v1 inventory

Relevant code is in `vllm_ascend/attention/dsa_v1.py`; there is no
`dsa_v41.py` in this checkout.

`AscendDSAReqMetadata` carries more than a prefix table and one length:

- logical/raw `block_table`, `seq_lens`, `query_start_loc`, and full write
  `slot_mapping`;
- storage block size and physical/compressed layout state;
- SAS metadata;
- QLI metadata, QLI cumulative query/key lengths, and compressor residuals;
- compressor output and cache-group identity;
- DSpark per-token SWA indices and vision SWA indices.

For DSpark sparse SWA, `build_dspark_swa_indices()` constructs a per-token slot
set. It derives a start position from native SWA, a visible length, and physical
slots. The builder owns a persistent `dspark_swa_indices_buffer` because the
operator can capture that address. This is not equivalent to a direct-prefix
Window block table.

For DeepSeek-V4 DSA, compressor/QLI state changes the logical-to-physical
visibility and residual lengths. P7 found no generation-scoped provider that
computes and owns:

```text
V_final = V_draft intersection V_native intersection V_resident
```

for table, SAS/QLI/compressor outputs, exact/upper lengths, and all derived
buffers as one lease. DSA therefore remains `FAIL_CLOSED`; it is not approximated
with `min(W, retention)`.

## 5. SFA and indexer inventory

Relevant code:

- `vllm_ascend/attention/sfa_v1.py`
- `vllm_ascend/attention/indexer.py`
- `vllm_ascend/attention/context_parallel/sfa_cp.py`

The SFA main attention and SFA indexer are separate consumers. The indexer has
its own block table, slot mapping, sequence lengths, query cumulative lengths,
RoPE state, and rank-local key/query lengths. SFA top-k visibility is per-token,
not a single request-level prefix length.

No P7 typed provider binds, under one generation and lease:

- the Draft absolute interval;
- per-token index filtering/translation;
- main/indexer cache-group relation;
- backend-owned table/length and top-k buffers;
- DCP/DSA-CP variants.

SFA and the indexer remain `FAIL_CLOSED`. Absolute positions and full write slots
must not be changed to simulate support.

## 6. MLA inventory

`vllm_ascend/attention/mla_v1.py` defines a distinct metadata model with:

- top-level block tables, exact sequence lengths, CPU lengths, query starts,
  and slot mappings;
- decode/prefill submetadata;
- graph padding and attention masks;
- PCP/DCP-specific builders and operator inputs.

MLA cannot inherit the GQA direct-prefix contract. P7 found no typed producer for
Window exact/upper, padding, derived decode metadata, and actual operator operand
under one generation lease. MLA remains `FAIL_CLOSED`.

## 7. DeepSeek-V4 / V4.1 source reality

The checkout composes V4/V4.1 behavior through the actual `dsa_v1.py`,
`sfa_v1.py`, `indexer.py`, context-parallel modules, and `deepseek_v4/*` model
code. An absent `dsa_v41.py` must not appear in an implementation plan.

DeepSeek-V4 co-trained DSpark is forced off before any inventory. Actual V4/V4.1
Draft consumers classified as DSA/SFA/MLA inherit those complex contracts and
remain `FAIL_CLOSED` until a real typed provider exists. Target model identity by
itself is not evidence of the Draft backend; P7 therefore does not invent a
model-name-wide V4 Gate.

## 8. Recycling / native SWA / sparse KV offload

Native sliding/circular/chunked specs are classified
`NATIVE_OR_RECYCLING`. `sfa_kv_offload.py` additionally owns request identity,
selection tables/status, membership maps, top-k resident capacity, CPU/device
movement, and in-flight buffers.

No source contract presently proves gap, prefix+tail, overhang, recycled block,
stale resident, eviction, and in-flight reuse for a Draft generation. These
routes remain `FAIL_CLOSED`; no resident set is inferred from a scalar capacity.

## 9. Multi-group inventory

P2 enumerates every actual consumer and preserves each global gid. P7 assigns:

| Shape | State | Missing contract |
|---|---|---|
| single group | eligible only for dense direct-prefix reference route | none beyond current P4/NPU gates |
| homogeneous multi-group | `FAIL_CLOSED` | shared absolute S plus independent per-gid projection, valid count, backend carrier, and same-generation binding |
| heterogeneous multi-group | `OWNER_BLOCKED` | product semantics and legacy heterogeneous defect decision |

P7 never re-aligns S per gid, never uses an LCM anchor, never windows a previous
Window, and never shallow-clones mutable metadata across groups.

## 10. Parallel eager inventory

`P7EagerTopologyFingerprint` records every topology input even when rejected.

| Topology | Current source fact | P7-E state |
|---|---|---|
| TP > 1 | draft/target sharding exists, but no rank-local Window read carrier or cross-rank lifetime proof | `FAIL_CLOSED` |
| DP > 1 | runners exist independently; no Window generation/isolation evidence across serving batches | `FAIL_CLOSED` |
| PP > 1 | pipeline draft mechanics exist; no stage-owned Window projection/lifetime contract | `FAIL_CLOSED` |
| PCP > 1 | replicated draft helpers exist; no Window read carrier parity at the real consumer | `FAIL_CLOSED` |
| DCP > 1 | interleaved prefix projection exists; table/operator binding is not implemented | `FAIL_CLOSED` |
| SP | runtime flag is inventoried | `FAIL_CLOSED` |
| DSA-CP | selects different DSA/SFA builders and metadata | `FAIL_CLOSED` |
| FlashComm | additional config or environment chooses the mode; it cannot transport generation state | `FAIL_CLOSED` |

For future DCP work, P7 implements and tests only the correct mathematical seam:

```text
local_visible(rank) = local_prefix(E, rank) - local_prefix(S, rank)
```

It explicitly does not use `V / dcp_world_size`. This helper does not enable DCP.

## 11. Async eager inventory

Pinned vLLM may use more than one concurrent batch under async scheduling, and
the upstream workspace-lane helper does not carry Draft Window generation state.
The P3 production owner was one serialized lane.

P7 adds a bounded host lifecycle foundation with independent P3 runtime/workspace
owners per lane:

```text
FREE -> ACQUIRED -> MATERIALIZED -> BOUND -> SUBMITTED
     -> CONSUMER_COMPLETE -> RETIRED -> FREE
```

It proves host ownership, pressure, delayed/reverse completion, abort, exception,
request replacement, and ABA behavior using explicit completion tokens. It is
not installed in DFlash, DSpark, or Eagle3 production flow. No real NPU event,
stream happens-before, or multi-step async consumer is bound. Therefore async is
`STATIC_READY`, and `require_live_materialization()` rejects it before FullSource.

Review-final binding additionally rejects any backend-derived tensor that aliases
the Window workspace, canonical FullSource table/count storage, or nested Target
state. A rejection aborts the generation and retires the host handle.

## 12. Request lifecycle and serving

`_requires_prefill_baseline_bypass()` has the current exact behavior:

- no prefill: continue the eligible eager Window route;
- all active rows prefilling: baseline full-context bypass; no generation;
- mixed prefill/decode: runtime `NotImplementedError`.

Server evidence shows the mixed exception can terminate EngineCore and fail all
concurrent requests. No owner choice exists between general-serving support and
a single-active-request product. P7 therefore records:

```text
G-MIXED = OWNER_BLOCKED
FEATURE RELEASE = HOLD
```

P7 does not redesign scheduler/admission and does not pretend the runtime abort
is an acceptable early admission policy.

## 13. Prefix and prefill

| Route | State |
|---|---|
| pure scheduler prefill | baseline bypass |
| mixed prefill/decode | `OWNER_BLOCKED`, current runtime fail closed, release blocker |
| Windowed/chunked prefill | `FAIL_CLOSED` |
| prefix cache + Window | `FAIL_CLOSED` before source/workspace |

## 14. Graph boundary

P7 changes no Graph manager, capture path, replay/update carrier, provider
installation, or Graph gate. Effective graph modes `FULL`,
`FULL_DECODE_ONLY`, and `PIECEWISE` classify `FAIL_CLOSED` before FullSource.

```text
GRAPH TRACK: FROZEN
GRAPH WINDOW USER GATE: STILL FAIL-CLOSED
B/C: NOT AUTHORIZED
```

## 15. Final inventory conclusion

- Method inventory: complete; every named route has one state.
- Backend inventory: complete; only dense FIA direct-prefix is a positive local
  candidate, all complex backends have an explicit missing contract.
- Parallel inventory: complete; fingerprint and DCP formula exist, all live
  parallel routes remain fail closed.
- Async host ownership: implemented and static-tested; live binding absent.
- Serving/mixed: owner blocked and release blocking.
- NPU: no new P7 evidence.

## 16. Independent Review Resolution

The review produced one Major, two Minor, and three questions. Final adjudication:

| ID | Resolution | Inventory consequence |
|---|---|---|
| F-01 | `PARTIALLY_ACCEPTED` | Add semantic hardware-family inventory/Gate; reject the claim that non-MTP 310P was currently production-reachable. |
| F-02 | `PARTIALLY_ACCEPTED` | Add host derived-buffer isolation; no live async consumer was shown. |
| F-03 | `ACCEPTED` | Enforce topology identity in the serialized runtime. |
| Q-01 | `OWNER_BLOCKED` | Plain Eagle is owner-blocked semantically and configuration-time fail closed operationally. |
| Q-02 | `OWNER_BLOCKED` | Mixed serving remains a release blocker. |
| Q-03 | `INSUFFICIENT_EVIDENCE` | Do not add a target-model-name Gate; continue classifying the actual Draft consumer. |

```text
METHOD / BACKEND / PARALLEL INVENTORY: COMPLETE
ASYNC HOST CONTRACT: PASS
P7-E STATIC FINAL: PASS
P7-E NPU: NOT VERIFIED
GRAPH TRACK: FROZEN
FEATURE RELEASE: HOLD
```

