# MRV2 Draft Sliding Window — P8-E Owner Mandatory Matrix

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

`Mandatory?` remains `OWNER_DECISION_REQUIRED` wherever no signed owner scope
exists. This document does not infer product scope from code reachability.

| ID | Model | Draft model | Method | Backend | Groups | W | K/query width | Hardware family | Topology | Async | Serving scope | Mandatory? | Static | NPU | Performance | Owner decision |
|---|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|---|---|
| OM-01 | owner-approved dense target | Eagle3 checkpoint | Eagle3 static K | dense GQA/FIA | 1 | positive, `W>=K` and validated | configured static K; campaign K=3 | STANDARD, each device separate | TP=DP=PP=PCP=DCP=1; SP/DSA-CP/FlashComm off; eager | false | single request then controlled multi-request | `OWNER_DECISION_REQUIRED` | `READY_FOR_NPU` | old P4 Node133/A2 single-request only; rerun at P7 SHA | OPEN | Decide exact devices, models, K/W and whether single-request evidence is mandatory or only diagnostic |
| OM-02 | owner-approved dense target | owner-signed DFlash checkpoint (absolute realpath + revision/hash required) | DFlash | dense GQA/FIA | 1 | valid | K+1 | STANDARD | exact serialized topology | false | pure decode | `OWNER_DECISION_REQUIRED` | `READY_FOR_NPU` | none at P7 final | OPEN | Supply and approve the exact target/draft pair, device campaign and acceptance thresholds before execution |
| OM-03 | non-V4 co-trained eligible target | owner-signed DSpark checkpoint (absolute realpath + revision/hash required) | eligible DSpark | dense GQA/FIA | 1 | valid | default K and explicit K+1 | STANDARD | exact serialized topology | false | pure decode | `OWNER_DECISION_REQUIRED` | `READY_FOR_NPU` | none at P7 final | OPEN | Supply the exact model pair and decide whether both anchor modes are mandatory; K+1 requires a draft checkpoint whose resolved HF config sets `sample_from_anchor=false` |
| OM-04 | any | MTP | MTP | any | any | any configured value | n/a | any | any | any | baseline | mandatory negative | `FORCED_OFF` | negative Gate only | n/a | Preserve warning-once and zero Window state |
| OM-05 | DeepSeek-V4 family | co-trained DSpark | DSpark | any | any | any configured value | n/a | any | any | any | baseline | mandatory negative | `FORCED_OFF` | negative Gate only | n/a | Preserve forced-OFF product policy |
| OM-06 | any | plain Eagle | Eagle | any | any | any | undefined | any | any | any | any | `OWNER_DECISION_REQUIRED` | `OWNER_BLOCKED` / operational fail closed | none | n/a | Define semantics or keep unsupported; current code rejects |
| OM-07 | any | Eagle3 | dynamic K | any | any | any | scheduled/dynamic | any | eager | false | decode | `OWNER_DECISION_REQUIRED` | `OWNER_BLOCKED` | none | n/a | Define horizon/anchor semantics before implementation |
| OM-08 | any | any | any | heterogeneous multi-group | >1 | any | any | any | eager | false | any | `OWNER_DECISION_REQUIRED` | `OWNER_BLOCKED` | none | n/a | Decide product semantics and legacy-defect treatment |
| OM-09 | any | any | DFlash2 | inherited DFlash classes | any | any | any | STANDARD | eager | false | any | `OWNER_DECISION_REQUIRED` | `FAIL_CLOSED` | none | n/a | Do not infer support from inheritance |
| OM-10 | V4/V4.1 or sparse target | any | any | DSA / compressor / QLI | any | any | per-token | any | eager | false | any | `OWNER_DECISION_REQUIRED` | `FAIL_CLOSED` | none | n/a | Typed visibility/residency intersection required |
| OM-11 | any | any | any | SFA main/indexer | any | any | per-token | any | eager | false | any | `OWNER_DECISION_REQUIRED` | `FAIL_CLOSED` | none | n/a | Main/indexer same-generation carrier required |
| OM-12 | any | any | any | MLA | any | any | backend-specific | any | eager | false | any | `OWNER_DECISION_REQUIRED` | `FAIL_CLOSED` | none | n/a | Distinct exact/upper/padding contract required |
| OM-13 | any | any | any | native/recycling/offload | any | any | resident-set | any | eager | false | any | `OWNER_DECISION_REQUIRED` | `FAIL_CLOSED` | none | n/a | Resident-set, eviction and in-flight reuse contract required |
| OM-14 | any | any | any | homogeneous multi-group | >1 | any | any | STANDARD | eager | false | any | `OWNER_DECISION_REQUIRED` | `FAIL_CLOSED` | none | n/a | Per-gid provider and same-generation binding required |
| OM-15 | any | any | any | dense FIA | 1 | valid | method-specific | STANDARD | any of TP/DP/PP/PCP/DCP >1 | false | any | `OWNER_DECISION_REQUIRED` | `FAIL_CLOSED` | none | n/a | Rank-local table/consumer/lifetime not implemented |
| OM-16 | any | any | any | any | any | valid | any | STANDARD | SP, DSA-CP, or FlashComm on | false | any | `OWNER_DECISION_REQUIRED` | `FAIL_CLOSED` | none | n/a | No Window generation carrier for these modes |
| OM-17 | any | any | positive method | dense FIA | 1 | valid | method-specific | STANDARD | exact eager | true | any | `OWNER_DECISION_REQUIRED` | `STATIC_READY` | not ready | n/a | Live binding and NPU completion event must be designed before campaign |
| OM-18 | any | any | positive method | dense FIA | 1 | valid | method-specific | STANDARD | eager | false | prefix cache on | `OWNER_DECISION_REQUIRED` | `FAIL_CLOSED` | none | n/a | Explicit prefix-cache isolation contract required |
| OM-19 | any | any | positive method | dense FIA | 1 | valid | method-specific | STANDARD | FULL/FULL_DECODE_ONLY/PIECEWISE | any | any | owner requires eventually, but Graph Track currently frozen | `GRAPH_FROZEN` | not verified | n/a | Reopen Graph only on an authorized capture seam |
| OM-20 | any | any | positive method | dense FIA | 1 | valid | method-specific | STANDARD | exact eager | false | mixed/general serving | `OWNER_DECISION_REQUIRED` | `OWNER_BLOCKED` | server observed abort at old P4 SHA | n/a | Choose general support or safe early single-active admission; release cannot proceed meanwhile |
| OM-21 | any | any | positive non-MTP method | compatibility backend | 1 | valid | any | COMPATIBILITY / 310P | eager | false | any | mandatory negative | `FAIL_CLOSED` before FullSource | negative Gate only | n/a | Preserve the Window hardware-family gate. The 310P patch delegates non-MTP startup to the baseline factory; this Feature does not claim a general MTP-only startup rule. |

## Owner actions required before release

1. Select mandatory positive methods, model pairs, devices and W/K values.
2. Decide general-serving support versus a safe, early single-active-request product scope.
3. Decide whether A3/A5 are mandatory in addition to A2; evidence never transfers by family label.
4. Decide whether Level-5 read-set and device happens-before are mandatory release evidence.
5. Reopen Graph Track only through one of the documented resume triggers; P8 does not choose B/C.

```text
OWNER MANDATORY MATRIX: PARTIAL
Reason: engineering states are complete, but product Mandatory/Optional choices and G-MIXED scope are unresolved.
```
