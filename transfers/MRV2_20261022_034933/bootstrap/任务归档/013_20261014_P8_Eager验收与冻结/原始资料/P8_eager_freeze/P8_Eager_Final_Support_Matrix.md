# MRV2 Draft Sliding Window — P8-E Final Eager Support Matrix

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

## Status vocabulary

The Eager matrix uses only `CONFIG_OFF`, `FORCED_OFF`, `OWNER_BLOCKED`,
`FAIL_CLOSED`, `STATIC_READY`, `READY_FOR_NPU`, `NPU_VERIFIED`, and
`SUPPORTED`. Graph is tracked separately as `GRAPH_FROZEN`.

- `READY_FOR_NPU` means the P7 local source/static contract is complete for one
  exact route. It is not runtime support.
- `NPU_VERIFIED` is valid only for the exact commit, machine, device, method,
  topology, and request scope named by the evidence.
- No P7-final route is `SUPPORTED`; no NPU campaign ran at P7 final SHA.

## Final matrix at P7 final production

| Dimension | Exact route / condition | Final state | Allocation and behavior | Evidence boundary / next step |
|---|---|---|---|---|
| Feature OFF | `draft_window_size=None`, any method | `CONFIG_OFF` | Exact baseline; zero Window plan, inventory, FullSource, workspace, P7 async state, or Graph provider | Factory and OFF-parity tests; preserve in every NPU A/B campaign |
| MTP | Any configured numeric Window | `FORCED_OFF` | Warning-once policy returns before numeric validation and all Window state | Static policy/order tests; verify baseline run and zero trace on NPU |
| DeepSeek-V4 co-trained DSpark | `method=dspark`, target model type starts with `deepseek_v4` | `FORCED_OFF` | Same early baseline return as MTP | Static policy/order tests; verify warning and zero state on NPU |
| Eagle3 static K | Dense FIA/GQA, one gid, `STANDARD`, graph NONE, async false, all world sizes 1, flags/prefix off, pure decode | `READY_FOR_NPU` | P4b first-pass Draft-private metadata; proposal-frozen S; each step refreshes from canonical FullSource | Old P4 SHA has scoped Node133/A2 single-request L3/L4 evidence; rerun full campaign at `4753742...` before any `NPU_VERIFIED` claim |
| DFlash | Same exact dense serialized topology | `READY_FOR_NPU` | P4a query width K+1, Draft-only read table/length | Static only; run physical-read, slot/Target, lifetime and profiler campaign |
| Eligible DSpark | Non-V4 co-trained; same exact dense serialized topology | `READY_FOR_NPU` | Actual query width: anchor default K, explicit false K+1 | Static only; run both widths on NPU |
| Plain Eagle | Window configured | `OWNER_BLOCKED` | Current implementation rejects at configuration time before Window state | Owner must define semantics; do not reinterpret shared AR mechanics |
| Eagle3 dynamic K | Dynamic speculative decoding true | `OWNER_BLOCKED` | Rejects before proposal Window state | Owner contract needed for proposal horizon/anchor |
| DFlash2 | Any Window ON route | `FAIL_CLOSED` | P2 inventory identity is not runtime enablement | Establish actual consumer/timing before reconsideration |
| Dense FIA/GQA backend | Exact single-gid direct-prefix route above | `READY_FOR_NPU` | Existing P2/P3/P4 carrier only | Device-specific campaign; `STANDARD` family is not cross-device proof |
| DSA-v1 / SAS / QLI / compressor | Any | `FAIL_CLOSED` | Reject before live FullSource/workspace | Needs typed `V_draft ∩ V_native ∩ V_resident` and derived-buffer lease |
| SFA main / indexer | Any | `FAIL_CLOSED` | Reject before live FullSource/workspace | Needs per-token visibility and same-generation main/indexer carrier |
| MLA | Any | `FAIL_CLOSED` | Reject before live FullSource/workspace | Needs exact/upper/padding and actual operand contract |
| Native SWA / circular / chunked | Any | `FAIL_CLOSED` | Reject before live FullSource/workspace | Needs resident/visibility provider, not a scalar `min` approximation |
| Recycling / sparse KV offload | Any | `FAIL_CLOSED` | Reject before live FullSource/workspace | Needs eviction, stale resident and in-flight ownership proof |
| V4/V4.1 complex composition | Actual Draft consumer resolves to DSA/SFA/MLA/native | `FAIL_CLOSED` | Classified from consumer, not target model name | Backend-specific contract required |
| Homogeneous multi-group | More than one executable gid | `FAIL_CLOSED` | No per-gid materialization occurs | Needs one absolute S plus per-gid projection/count/carrier under one generation |
| Heterogeneous multi-group | Different backend/layout/geometry groups | `OWNER_BLOCKED` | No materialization | Owner must resolve semantics and legacy defect policy |
| TP/DP/PP/PCP/DCP > 1 | Any positive method | `FAIL_CLOSED` | P7 fingerprint rejects before live source; DCP helper is math only | `MATH_READY ≠ LIVE_SUPPORT`; needs rank-local data plane and NPU proof |
| SP / DSA-CP / FlashComm | Enabled | `FAIL_CLOSED` | Reject before live source | Environment may select a mode but never transports generation state |
| Prefix cache | Enabled | `FAIL_CLOSED` | Reject before live source/workspace | Needs explicit cache/read/write isolation contract |
| Async eager | Async true, graph NONE | `STATIC_READY` | Bounded host pool/state machine only; live materialization rejects | Production binding and real NPU completion event are absent |
| Pure scheduler prefill | All active rows prefilling | `STATIC_READY` | Baseline full-context bypass; zero Window generation | Safe baseline behavior, not Window ON support |
| Mixed prefill/decode | Any positive method | `OWNER_BLOCKED` | Current runtime throws before epoch creation; server observed EngineCore abort | Release blocker; owner must choose general support or safe early single-active admission |
| General serving / uncontrolled arrival | Any | `OWNER_BLOCKED` | No safe admission restriction | Release blocker |
| 310P compatibility family | `AttentionBackendFamily.COMPATIBILITY` | `FAIL_CLOSED` | P7 family gate rejects Window before FullSource. The 310P patch delegates non-MTP methods to the baseline speculator factory; non-MTP baseline startup is outside this Feature's contract. | Hardware-family regression must remain green; do not describe the general 310P factory as MTP-only |
| A2 / A3 / A5 standard profiles | `AttentionBackendFamily.STANDARD` | Route-dependent `READY_FOR_NPU` only | Family classification allows evaluation; it does not establish device support | Run each device independently; Node133 A2 evidence does not cover A3/A5 |
| FULL / FULL_DECODE_ONLY / PIECEWISE | Any Window configuration | `GRAPH_FROZEN` | Graph capability and method gates reject; P6 provider has no production installation point | Resume only after owner reopens Graph Track and a legal capture seam exists |

## Frozen read/write boundary

Window ON may change only the Draft read table and Draft read lengths. Canonical
FullSource, positions, query layout, full slot mapping, physical KV writes, Target
metadata, Target reads, and Target owner/content remain full-context state.

## Final local conclusion

```text
EAGER CAPABILITY MATRIX: COMPLETE
POSITIVE LOCAL ROUTES: Eagle3 static-K, DFlash, eligible DSpark — exact dense serialized eager only
ASYNC: STATIC_READY / LIVE FAIL-CLOSED
G-MIXED: OWNER_BLOCKED / RELEASE_BLOCKER
P7-FINAL NPU EVIDENCE: NONE
SUPPORTED ROWS: NONE
GRAPH: GRAPH_FROZEN
```
