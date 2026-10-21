# MRV2 Draft Sliding Window — P8-E Runtime Evidence Ledger

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

Evidence is scoped by commit, machine, device, route and level. A narrower row
never upgrades a broader claim.

| Evidence | Machine | Device family | Commit | Method / route | Evidence level | Valid scope | Cannot prove |
|---|---|---|---|---|---|---|---|
| P4 restore and binary binding | node133 | ascend-910b2 / A2 | Ascend `1011e2c2...`, vLLM `84030bbe...` | repository/runtime binding | source/restore | Exact P4 tree restored and runtime imported that tree | P7 tree, model correctness, physical reads |
| P4a implementation notes | local Mac | host CPU | `4c1f691...` / shared fix in `1011e2c2...` | DFlash / eligible DSpark | static/CPU | Policy, metadata seam, OFF parity, fail-closed | Any NPU Window-ON behavior, performance |
| P4b R3 single-request campaign | node133 | ascend-910b2 / A2 | production `1011e2c2...`; server-only debug `2a485613...` isolated | Eagle3, K=3, W=64, TP1 eager, one request | NPU L3 + operator-argument L4 | 284/284 proposals, 852/852 active rows, 33/33 Draft FIA exact lengths; write/Target checks for observed route | P7 SHA, A3/A5, multi-request, kernel L5 reads, device lifetime, performance; the debug commit/diff is unavailable in the local repo and freeze bundle, so its instrumentation cannot be code-audited here |
| Boundary/non-boundary traces | node133 | A2 | `1011e2c2...` | Eagle3 exact route | NPU L3/L4 | Short/long and observed aligned/nonaligned anchors in recorded fixtures | Isolated every future-column transition or deterministic cross-boundary rejection |
| Sequential A→C→A | node133 | A2 | `1011e2c2...` | Eagle3 exact route | NPU live | Same-engine sequential isolation, disjoint epoch ranges, repeated A output equality | Concurrent A/B/A, persistent row reuse, strict reorder |
| Controlled multi-request attempts | node133 | A2 | `1011e2c2...` | Eagle3 | negative runtime evidence | Four available constructions failed to form batch>1 pure decode | Impossibility of pure-decode batch generally; request-isolation correctness |
| Mixed arrival evidence | node133 | A2 | `1011e2c2...` | Eagle3 | NPU failure evidence | Mixed prefill/decode raises and can terminate EngineCore | A safe admission policy or general-serving support |
| Slot oracle | node133 | A2 | `1011e2c2...` | Eagle3 | incomplete | Static full-slot contract plus before/after trace values | Independent complete physical slot recomputation; traces were truncated |
| Device lifetime / NO_SYNC | node133 | A2 | `1011e2c2...` | Eagle3 | insufficient | Output did not depend on debug synchronization in observed run | Stream happens-before, no early workspace overwrite |
| P4 negative Gates | node133 | A2 | `1011e2c2...` | graph/async/prefix/TP/mixed | partial NPU negative | Five of six selected negative configurations rejected as expected | Dynamic-K CLI route; P7 hardware-family Gate |
| Node101 restore/binding | Node101 | A3 | no artifact | none | missing | Nothing | Any A3 statement; status is UNKNOWN |
| R4 performance | none | none | none | none | not run | Nothing | Latency, throughput, memory, synchronization, D2H/H2D |
| P5/P6 Graph host contracts | local Mac | host CPU | `7599497...` | replay/update carrier | static only | Typed capture/runtime identities, provider and replay/update fail-closed contracts | Startup capture binding, graph address, effective update generation, NPU read-set |
| P6A seam search | local Mac | host/source | no production commit after `7599497...` | Graph capture | source investigation | No existing authorized Ascend-owned pre-capture injection seam found | Impossibility under a future new seam or owner-authorized B/C |
| P7/P8-final local acceptance | local Mac | host CPU | `4753742...` | all eager capability rows | static/CPU | 360 targeted passes from the exact nine-file command recorded in `P8_Local_Test_Results.md`; capability/Gate/topology/async-host contracts; full 310P negative regression | Any P7 NPU route, live async, physical reads, performance |

## Evidence rules

- P4b evidence does not prove P4a DFlash or DSpark.
- Node133 A2 does not prove Node101 A3 or A5.
- Single request does not prove batch>1, reorder, row reuse, or general serving.
- L4 operator arguments do not prove L5 kernel physical reads.
- Host fake completion does not prove NPU completion or stream ordering.
- P4 evidence does not transfer to P7 final SHA without rerun.
- Debug commits are observation tools only and are not production ancestors.
- Debug SHA `2a485613...` exists only in the archived server-report provenance available
  to this delivery. It is absent from the local Git object database and bundle;
  therefore this package cannot independently inspect its instrumentation diff.

```text
P7-FINAL EAGER NPU VERIFIED: NO
P7-FINAL PERFORMANCE VERIFIED: NO
```
