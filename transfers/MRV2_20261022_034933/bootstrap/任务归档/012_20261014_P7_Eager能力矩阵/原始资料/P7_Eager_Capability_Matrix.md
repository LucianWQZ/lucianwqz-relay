# MRV2 Draft Sliding Window — P7-E Capability Matrix

## Status vocabulary

These are the only P7-E matrix values:

| State | Meaning |
|---|---|
| `CONFIG_OFF` | `draft_window_size` is absent; exact baseline, zero Window state |
| `FORCED_OFF` | product policy disables Window before numeric/inventory/state work |
| `OWNER_BLOCKED` | a product/semantic decision is missing; Codex cannot choose it |
| `FAIL_CLOSED` | source proves the route lacks a required typed contract; runtime must reject |
| `STATIC_READY` | host-only contract exists; no live/NPU enablement is allowed |
| `READY_FOR_NPU` | local source/static contract is closed for an exact route; not `SUPPORTED` |

No row in this document uses `SUPPORTED`.

## 1. Method matrix

| Method | Backend/layout | Graph | Async | Topology | Serving phase | State | Evidence / next step |
|---|---|---|---|---|---|---|---|
| Eagle3 static K | single dense GQA/FIA | NONE | false | TP/DP/PP/PCP/DCP=1; SP/DSA-CP/FlashComm off | pure decode after prefill bypass | `READY_FOR_NPU` | P4b static; scoped Node133 A2 single-request L3/L4 exists; multi-request/lifetime/L5 remain open |
| DFlash | single dense GQA/FIA | NONE | false | all world sizes 1; flags off | pure decode | `READY_FOR_NPU` | P4a static only; run full NPU physical-read/profiler matrix |
| eligible DSpark | single dense GQA/FIA | NONE | false | all world sizes 1; flags off | pure decode | `READY_FOR_NPU` | P4a static only; test K and K+1 query-width cases on NPU |
| MTP | any | any | any | any | any | `FORCED_OFF` | retain warning/policy and zero state |
| DeepSeek-V4 co-trained DSpark | DSpark/complex target | any | any | any | any | `FORCED_OFF` | retain policy order and zero state |
| plain Eagle | any | any | any | any | any | `OWNER_BLOCKED / FAIL_CLOSED` | owner must define semantics; current P1 policy rejects at configuration time |
| Eagle3 dynamic K | dense GQA or other | NONE | false | TP1 reference | decode | `OWNER_BLOCKED` | owner contract needed for horizon/anchor under scheduled K |
| DFlash2 | inherited DFlash classes | NONE | false | TP1 reference | decode | `FAIL_CLOSED` | establish actual consumer/timing before enabling |

## 2. Backend matrix

| Backend/layout | Table/visibility reality | Typed generation provider | State | Required next step |
|---|---|---|---|---|
| dense GQA / FIA direct prefix | one block table + exact/upper; P4 Draft-private metadata | yes for single gid serialized eager | `READY_FOR_NPU` | route-specific NPU oracle |
| DSA-v1 SWA | per-token SWA indices + SAS + full write slots | no | `FAIL_CLOSED` | provider for `V_draft ∩ V_native ∩ V_resident`, indices, buffers, lease |
| DSA-v1 compressor/QLI | logical table plus compressor/QLI physical/residual metadata | no | `FAIL_CLOSED` | typed compressor/QLI generation contract |
| SFA main | MLA-like table/length plus top-k sparse state | no | `FAIL_CLOSED` | per-token visibility and operator carrier |
| SFA indexer | independent indexer cache/table/slot/length | no | `FAIL_CLOSED` | main/indexer same-generation contract |
| MLA | distinct decode/prefill metadata, CPU/device length, padding | no | `FAIL_CLOSED` | exact/upper/derived-buffer producer and live consumer proof |
| native SWA/circular/chunked | non-prefix native visibility | no | `FAIL_CLOSED` | typed native visibility provider |
| sparse KV offload/recycling | resident LRU, membership, selection and in-flight reuse | no | `FAIL_CLOSED` | resident-set provider and eviction/lifetime proof |
| V4/V4.1 complex Draft compositions | actual dsa_v1/sfa_v1/indexer/deepseek_v4 consumer | no | `FAIL_CLOSED` | backend-specific contracts; target model identity alone is not a Draft-backend Gate; do not invent `dsa_v41.py` |

## 2.1 Hardware-family matrix

| Attention backend family | Representative profile | State | Evidence / next step |
|---|---|---|---|
| `STANDARD` | A2/A3/A5 | route-dependent; exact dense candidate may be `READY_FOR_NPU` | still requires device/method-specific NPU evidence; one device's evidence does not generalize |
| `COMPATIBILITY` | 310P | `FAIL_CLOSED` | the Window family Gate rejects before FullSource; non-MTP startup delegates to the baseline factory and is outside this Feature's contract |

## 3. Group matrix

| Group shape | State | Invariant |
|---|---|---|
| one dense direct-prefix gid | `READY_FOR_NPU` for exact serialized eager topology | one canonical absolute S, one generation |
| homogeneous multi-group | `FAIL_CLOSED` | no per-gid projection/valid-count/consumer binding yet |
| heterogeneous multi-group | `OWNER_BLOCKED` | legacy defect/product semantics unresolved |
| multiple consumers sharing a gid | `FAIL_CLOSED` | no unambiguous owner/consumer carrier |

## 4. Parallel matrix

| Dimension | Value | State | Source fact / missing proof |
|---|---:|---|---|
| TP | 1 | part of exact candidate | reference route only |
| TP | >1 | `FAIL_CLOSED` | no rank-local Window table/consumer proof |
| DP | 1 | part of exact candidate | reference route only |
| DP | >1 | `FAIL_CLOSED` | no generation isolation across concurrent runners |
| PP | 1 | part of exact candidate | reference route only |
| PP | >1 | `FAIL_CLOSED` | no stage-owned projection/lifetime contract |
| PCP | 1 | part of exact candidate | reference route only |
| PCP | >1 | `FAIL_CLOSED` | replicated draft path lacks Window carrier parity |
| DCP | 1 | part of exact candidate | reference route only |
| DCP | >1 | `FAIL_CLOSED` | only `local(E)-local(S)` helper is proven; live table/operator is not |
| SP | false | part of exact candidate | reference route only |
| SP | true | `FAIL_CLOSED` | no rank-local Window contract |
| DSA-CP | false | part of exact candidate | reference route only |
| DSA-CP | true | `FAIL_CLOSED` | different metadata/consumer family |
| FlashComm | false | part of exact candidate | reference route only |
| FlashComm | true | `FAIL_CLOSED` | env/config selects mode only; no generation transport |

## 5. Execution-mode matrix

| Mode | State | Allocation / behavior |
|---|---|---|
| graph NONE, async false | `READY_FOR_NPU` only for exact single dense route | existing P2/P3/P4 allocation and consumer |
| graph NONE, async true | `STATIC_READY` | bounded host pool exists; live source capability rejects before FullSource |
| FULL | `FAIL_CLOSED` | Graph Track frozen |
| FULL_DECODE_ONLY | `FAIL_CLOSED` | Graph Track frozen |
| PIECEWISE | `FAIL_CLOSED` | Graph Track frozen |
| prefix cache ON | `FAIL_CLOSED` | rejects before source/workspace |

## 6. Request lifecycle matrix

| Situation | State | Current behavior | Product consequence |
|---|---|---|---|
| pure scheduler prefill | `STATIC_READY` baseline behavior | full-context bypass, zero generation | safe baseline; not Window ON |
| single active decode request | `READY_FOR_NPU` exact route | P4 consumer path | P4b scoped evidence only; P4a still NPU open |
| sequential same-engine requests | `READY_FOR_NPU` exact route | source evidence and P4b scoped NPU isolation | persistent row reuse not observed on NPU |
| batch >1 pure decode | `READY_FOR_NPU` only as local contract | static P3 supports rows; runtime route was not constructed in server campaign | needs controlled NPU construction |
| mixed prefill/decode | `OWNER_BLOCKED` | runtime `NotImplementedError`; server observed EngineCore abort | release blocker |
| general serving | `OWNER_BLOCKED` | no safe admission policy | owner must choose general support or early single-active restriction |
| finish/add/reorder/row replacement | `STATIC_READY` host contract | mapping_epoch + request fingerprint tests pass | requires route-specific NPU serving evidence |

## 7. OFF matrix

| Policy | State | P7/P3/P5 allocation |
|---|---|---|
| no `draft_window_size` | `CONFIG_OFF` | zero |
| MTP with configured value | `FORCED_OFF` | zero |
| DeepSeek-V4 co-trained DSpark with configured value | `FORCED_OFF` | zero |

## 7.1 Independent Review Resolution

| Finding | Resolution | Matrix change |
|---|---|---|
| F-01 platform dimension | `ACCEPTED` after P8 factual correction | Added hardware-family axis and pre-FullSource `COMPATIBILITY` rejection. P8 source recheck disproved the earlier MTP-only startup rationale: `_init_speculator_310p` delegates every non-MTP route to the baseline factory. |
| F-02 derived-buffer alias | `PARTIALLY_ACCEPTED` | Async host contract now rejects Window/FullSource/Target aliases; no live async route is enabled. |
| F-03 topology enforcement | `ACCEPTED` | Runtime validates exact fingerprint before write/refresh/consume. |
| Q-01 plain Eagle | `OWNER_BLOCKED` | Matrix now distinguishes absent owner semantics from current configuration-time rejection. |
| Q-02 mixed serving | `OWNER_BLOCKED` | Remains `RELEASE_BLOCKER`. |
| Q-03 V4 model-wide Gate | `INSUFFICIENT_EVIDENCE` | Matrix stays based on actual Draft consumer/backend composition. |

## 8. Release view

```text
P7-E MATRIX INVENTORY: COMPLETE
P7-E POSITIVE LOCAL ROUTES: exact single-group dense-GQA serialized eager only
P7-E ASYNC STATIC CONTRACT: PASS; capability remains STATIC_READY / live fail closed
G-MIXED: OWNER_BLOCKED / RELEASE_BLOCKER
P7-E NPU: NOT VERIFIED by P7
GRAPH TRACK: FROZEN
P7-E STATIC FINAL: PASS
P8-E ENTRY: READY
FEATURE RELEASE: HOLD
```

