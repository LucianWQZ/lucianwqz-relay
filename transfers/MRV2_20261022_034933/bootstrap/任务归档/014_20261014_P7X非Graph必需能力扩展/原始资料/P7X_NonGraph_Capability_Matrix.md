# P7-X Non-Graph Capability Matrix

Only the following states are used: `CONFIG_OFF`, `FORCED_OFF`,
`LOCAL_STATIC_READY`, `REPORT1_RUNTIME_DEPENDENT`, `SOURCE_BLOCKED`, and
`GRAPH_FROZEN`.

## Method and policy

| Route | Status | Reason |
|---|---|---|
| no `draft_window_size` | `CONFIG_OFF` | no P2/P3/P7-X Window state |
| MTP + configured Window | `FORCED_OFF` | warning once; policy returns before numeric/inventory |
| DeepSeek-V4 co-trained DSpark + configured Window | `FORCED_OFF` | warning once; zero downstream Window state |
| Eagle3 static-K eager | `LOCAL_STATIC_READY` | P4b frozen anchor plus P7-X phase/prefix/TP contracts |
| DFlash eager | `LOCAL_STATIC_READY` | P4a consumer plus P7-X phase/TP/prefix/async contracts |
| eligible DSpark eager | `LOCAL_STATIC_READY` | actual K/K+1 query width retained |
| plain Eagle | `SOURCE_BLOCKED` | no product/read-consumer contract; ON cannot silently fall back |
| Eagle3 dynamic-K | `SOURCE_BLOCKED` | proposal horizon contract is static-K only |
| DFlash2 | `SOURCE_BLOCKED` | no verified explicit read consumer |

## Backend/provider

| Backend/layout | Status | Provider/limitation |
|---|---|---|
| dense GQA/FIA direct prefix | `LOCAL_STATIC_READY` | canonical kernel-block table and exact/upper carrier |
| uncompressed DSA/SWA, ratio 0 or 1 | `LOCAL_STATIC_READY` | canonical source plus native SWA intersection in real builder/operator |
| uncompressed DSA-CP | `LOCAL_STATIC_READY` | actual `AscendDSACPMetadataBuilder`; local derived metadata remains NPU evidence |
| compressed DSA / compressor / QLI | `SOURCE_BLOCKED` | direct-prefix source cannot represent compressed/indexed visibility safely |
| SFA main/indexer | `REPORT1_RUNTIME_DEPENDENT` | per-token index translation and persistent derived owner unresolved |
| MLA | `REPORT1_RUNTIME_DEPENDENT` | actual exact/upper operand and derived state unresolved |
| native SWA/recycling/offload | `REPORT1_RUNTIME_DEPENDENT` | physical resident-set/eviction provider not established for the required route |
| unknown builder/layout | `REPORT1_RUNTIME_DEPENDENT` | no model-name inference or dense fallback |

## Topology and execution

| Combination | Status | Contract |
|---|---|---|
| TP1 | `LOCAL_STATIC_READY` | existing path |
| ordinary TP2/TP4/TP16 | `LOCAL_STATIC_READY` | replicated logical read view, rank included in immutable topology identity |
| DSA-CP | `LOCAL_STATIC_READY` | DSA-CP builder-derived local state from common Window metadata |
| DP>1, PP>1, PCP>1, DCP>1, SP | `REPORT1_RUNTIME_DEPENDENT` | actual runtime carrier/projection authority unresolved |
| FlashComm outside DSA-CP | `REPORT1_RUNTIME_DEPENDENT` | comm owner/stream/carrier unresolved |
| homogeneous multi-group | `REPORT1_RUNTIME_DEPENDENT` | one canonical S is proven; live grouped P3/P4 carrier absent |
| heterogeneous multi-group | `REPORT1_RUNTIME_DEPENDENT` | per-layout provider and required-route identity unresolved |
| async DFlash/eligible DSpark dense | `LOCAL_STATIC_READY` | bounded pool defaults/minimums to host overlap; normal poll is nonblocking; exhaustion waits oldest real event without overwrite; NPU ordering/performance open |
| async Eagle3 or async DSA | `REPORT1_RUNTIME_DEPENDENT` | proposal-step binding or lane-owned backend-derived buffers unresolved |
| any Graph mode | `GRAPH_FROZEN` | unchanged fail-closed user Gate |
| COMPATIBILITY/310P family | `SOURCE_BLOCKED` | rejected before FullSource; MTP still forced OFF by policy |

## Request/serving features

| Feature | Status | Static contract |
|---|---|---|
| prefix miss/hit/shared prefix | `LOCAL_STATIC_READY` | current canonical owner + persistent valid block counts |
| prefix eviction/reuse | `LOCAL_STATIC_READY` | source/mapping/request generation mismatch rejects stale state |
| pure continuing scheduler prefill | `LOCAL_STATIC_READY` | baseline full-read bypass; no fake Window generation |
| terminal prefill to decode | `LOCAL_STATIC_READY` | Window generation and row-phase identity |
| mixed continuing/terminal/decode batch | `LOCAL_STATIC_READY` | continuing rows use current canonical full extent, other rows are Windowed |
| batch>1/reorder/finish-add/row reuse | `LOCAL_STATIC_READY` | ordered request + mapping epoch + phase fingerprints |
| preemption/resume | `LOCAL_STATIC_READY` host contract | resumed proposal receives a new generation/epoch; NPU campaign pending |

`LOCAL_STATIC_READY` never means `SUPPORTED`. Every positive route still needs
the exact Node101 NPU campaign and independent review.

Report1 observed P8 rather than P7-X: A3 is STANDARD-family; Qwen DFlash TP1
and Eagle3 TP1 are usable fixtures; DFlash/DSpark resolve async true by default;
GLM target/draft assets are known, but the MRV2 Draft backend/builder/gids/block
geometry were not observed. Therefore no status above is promoted to NPU PASS.
