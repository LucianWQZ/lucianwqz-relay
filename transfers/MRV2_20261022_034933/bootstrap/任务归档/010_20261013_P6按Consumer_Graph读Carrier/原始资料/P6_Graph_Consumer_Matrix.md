# MRV2 Draft Sliding Window — P6 Graph Consumer Matrix

## Status and scope

- vLLM: `84030bbe3d74d99bad477a3d2e37a973ccd8865c`（unchanged）
- vLLM-Ascend parent: `0702c89d2aa41d47ae2379fc6de883140277fbef`
- P6: `20673a1ced10160d8f8d1aaa79230e6ce0409d3c`
- P6 review-fix: `7599497ab2694c4cf343f61f82f449980d8bad93`
- Final tree: `b4f7d12bd24b0a7632f9e606b29703a7c96278de`
- Evidence level: host/static source and state-machine contract only
- User-visible Graph Window: **STILL FAIL-CLOSED**
- NPU capture/replay/update/operator behavior: **NOT VERIFIED**

`Consumer` below is classified only where the current source reaches the real
`update_full_graph_params -> impl_cls.update_graph_params` entrance. It does not claim that the
already-submitted replay consumed the new value.

## Per-consumer inventory

| Method | Route | Mode | Capture | Replay source | UPDATE path | Consumer | Static status | Runtime status |
|---|---|---|---|---|---|---|---|---|
| Eagle3 | first pass | FULL | Ascend observes manager entry, but upstream creates dummy metadata internally; P6 carrier cannot be injected safely | explicit Draft-private carrier is required; Target-derived metadata is rejected | AR manager → `update_full_graph_params` → exact FIA impl | `TASK_REBOUND` only at actual UPDATE entrance | **PARTIAL**: carrier/update contract proven; capture blocked | NPU OPEN; user Gate closed |
| Eagle3 | AR step | FULL | same startup-capture limitation | one explicit carrier per AR consumer; K=3 host test keeps step source/length distinct | AR manager → real FIA update | `TASK_REBOUND` at UPDATE entrance | **PARTIAL** | NPU OPEN; user Gate closed |
| DFlash | query graph | FULL | same startup-capture limitation | one explicit DFlash carrier; baseline/Target carrier cannot win; full write/query reference is revalidated | DFlash manager resolves route from P2 inventory → real FIA update | `TASK_REBOUND` at UPDATE entrance | **PARTIAL** | NPU OPEN; user Gate closed |
| DSpark | inherited query graph | FULL | inherits DFlash capture path and limitation | explicit DSpark route/carrier; DFlash route mismatch fails; no class-name heuristic | shared DFlash manager resolves `dspark` from P2 inventory → real FIA update | `TASK_REBOUND` at UPDATE entrance | **PARTIAL** | NPU OPEN; user Gate closed |
| Eagle3 | first pass | FULL_DECODE_ONLY | no safe capture carrier; phase semantics not inventoried for Window | not enabled | unresolved | `UNRESOLVED` | **BLOCKED** | fail closed |
| Eagle3 | AR step | FULL_DECODE_ONLY | no safe capture carrier | not enabled | unresolved | `UNRESOLVED` | **BLOCKED** | fail closed |
| DFlash | query graph | FULL_DECODE_ONLY | route not source-verified | not enabled | unresolved | `UNRESOLVED` | **BLOCKED** | fail closed |
| DSpark | inherited query graph | FULL_DECODE_ONLY | route not source-verified | not enabled | unresolved | `UNRESOLVED` | **BLOCKED** | fail closed |
| Eagle3 | first pass | PIECEWISE | piecewise capture/task ownership not inventoried | not enabled | unresolved | `UNRESOLVED` | **BLOCKED** | fail closed |
| Eagle3 | AR step | PIECEWISE | piecewise capture/task ownership not inventoried | not enabled | unresolved | `UNRESOLVED` | **BLOCKED** | fail closed |
| DFlash | query graph | PIECEWISE | piecewise carrier path not source-verified | not enabled | unresolved | `UNRESOLVED` | **BLOCKED** | fail closed |
| DSpark | inherited query graph | PIECEWISE | piecewise carrier path not source-verified | not enabled | unresolved | `UNRESOLVED` | **BLOCKED** | fail closed |

## Consumer-kind decision

| Kind | P6 decision | Evidence |
|---|---|---|
| `DIRECT_CAPTURED` | No route classified | The captured dummy metadata is internal to pinned vLLM and does not expose an Ascend-owned operand injection seam. |
| `TASK_REBOUND` | Source-derived only for the exact standard FIA implementation at UPDATE | `AscendAttentionBackendImpl.update_graph_params` rebinds task metadata table/read lengths inside the graph task update boundary. |
| `BACKEND_DERIVED` | No route classified | No separate verified backend-derived read carrier exists in the eligible P6 inventory. |
| `UNRESOLVED` | Default before actual backend attribution, and permanent for uninventoried routes | Caller declarations are not accepted as backend evidence. |

## Exact source order

```text
Draft-private metadata build / carrier submit
    -> pre-replay identity and object check
    -> REPLAY
    -> Python CONSUMER observation
    -> UPDATE binding validation
    -> backend update entry
```

Because UPDATE is after replay, P6 deliberately records
`update_effective_generation_ids=None` and `NEEDS_NPU_TIMELINE`. Static source cannot decide
whether task rebinding affects replay N, replay N+1, or another launch boundary.

For every FULL row above, “explicit carrier” now means both halves are bound:

- Window read table/device exact/CPU exact/upper come from provider-owned carrier backing;
- full slot mapping/query layout/positions owner/attention state/token count/causal contract come
  from `DraftWindowGraphWriteSideReference` and are checked again at the actual UPDATE entrance.

This closes the review's static write-side parity gap, but it does not change any row's
capture/runtime status.

## Gate conclusion

```text
P6 STATIC PER-CONSUMER CONTRACT: PARTIAL
P6 CAPTURE PATH: BLOCKED UNDER R-REPO-01
P6 NPU GRAPH: NOT VERIFIED
GRAPH WINDOW USER GATE: STILL FAIL-CLOSED
```
