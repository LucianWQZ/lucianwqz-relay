# P7-X Graph Prefix Cache Design

## Decision

```text
GRAPH_PREFIX_DESIGN: IMPLEMENTATION-READY
GRAPH_PREFIX_CODE: NOT IMPLEMENTED
GRAPH_PREFIX_NPU: NOT VERIFIED
```

## 1. Existing Eager Foundation

`worker/v2/spec_decode/draft_window_nongraph.py`已提供：

- `build_prefix_resident_snapshot`：由canonical FullSource、idx mapping、ordered request IDs生成per-row valid block count；
- `build_phase_aware_materialization_plan`：continuing prefill读full resident prefix，terminal/decode按Window plan；
- row phase fingerprint与source shortage检查。

最终可见集不是简单`min(W, retention)`，而是：

```text
V_final = V_draft ∩ V_native ∩ V_resident
```

## 2. Graph-specific Delta

Capture只固定capacity/address，不能冻结某次dummy residency。Runtime每proposal必须刷新：

- resident valid block counts；
- table内容；
- exact/upper lengths；
- active/tail rows；
- backend derived state（若DSA/SFA/indexer）；
- resident epoch/source version。

Prefix eviction与physical block reuse可能发生在Graph consumer仍inflight时，因此需要resident hold/lifetime token，而不仅是mapping_epoch。

## 3. Identity Extension

建议加入typed runtime字段：

- prefix cache enabled/mode；
- resident snapshot version/epoch；
- per-gid resident owner/version；
- eviction hold id；
- row phase fingerprint；
- request fingerprint + mapping_epoch（已有）。

CaptureIdentity只记录prefix-capable layout/schema，不包含runtime resident epoch。

## 4. Exact Source Seams

| File | Function | Role |
|---|---|---|
| `draft_window_nongraph.py` | `build_prefix_resident_snapshot` | runtime resident oracle |
| same | `build_phase_aware_materialization_plan` | Window/native/resident intersection |
| `draft_window_eager.py` | `_materialize_draft_window_read_inputs` | current producer |
| `draft_window_graph.py` | bind compatibility | add resident identity/lifetime validation |
| `draft_window_graph_characterization.py` | installer/prepare | prefix-capable candidate after base evidence |
| backend adapters | metadata refresh | FIA rebind或derived buffer refresh |

## 5. Runtime Flow

```text
request IDs + idx_mapping + mapping_epoch
→ prefix cache resident snapshot
→ row phase plan
→ canonical FullSource descriptor
→ P3 workspace
→ Graph persistent carrier refresh
→ backend derived refresh
→ replay
→ device completion
→ release eviction hold
```

## 6. Eviction and Reuse Rules

- active Graph reader引用的physical block不得被回收后以新语义复用；
- eviction在bind前发生：新snapshot反映它；
- eviction在submit后发生：必须由hold token阻止或使request不被调度；
- same physical block id ABA不能仅靠table值检测，需cache version/lifetime；
- request row reuse必须由request fingerprint + epoch检测。

## 7. Backend Interaction

- FIA：table/length可通过已有task update重绑；
- DSA：SAS/SWA indices由resident-filtered table/length派生，必须原地刷新persistent derived buffers；
- SFA/indexer：main和indexer resident set都必须同generation；
- MLA：MLA decode metadata需使用resident-filteredtable/length；
- recycling/native SWA：其resident provider必须与prefix provider做真正集合交集。

## 8. Fail-closed Rules

以下任一发生即在replay前拒绝：

- resident snapshot缺少active row；
- block count超过canonical valid source；
- resident owner/version变化；
- active reader无eviction hold；
- backend derived state仍属于旧resident epoch；
- prefix flag与capture fingerprint不同；
- prefix+mixed phase无明确schema。

## 9. Red Test List

1. full hit、partial hit、miss；
2. prefix+tail/gap/overhang；
3. eviction before bind；
4. eviction after submit被hold阻止；
5. physical block ABA/recycled id；
6. reorder/finish/add/row replacement；
7. per-gid resident count；
8. backend derived state stale；
9. A/B/A' stable address/newresident epoch；
10. OFF/forced-OFF零prefixGraph state。

## 10. NPU Oracle

记录cache hit/miss/evict事件、resident version、full table、Window table、operator read-set、slot/write和completion。至少执行：hit→decode、partial hit→tail、evict→reuse、A/B/A'、batch reorder。

## 11. Risk

Prefix Graph风险主要是lifetime而非Window math。没有设备completion与cache eviction owner对接时，不能开放，即使table内容在CPU oracle上正确。
