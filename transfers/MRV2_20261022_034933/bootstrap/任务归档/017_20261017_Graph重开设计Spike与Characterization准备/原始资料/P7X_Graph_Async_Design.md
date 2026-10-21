# P7-X Graph Async Design

## Decision

```text
GRAPH_ASYNC_DESIGN: IMPLEMENTATION-READY
GRAPH_ASYNC_CODE: NOT IMPLEMENTED
GRAPH_ASYNC_NPU: NOT VERIFIED
```

## 1. Existing Eager State Machine

`worker/v2/spec_decode/draft_window_async.py`已经实现host/static：

```text
FREE
→ ACQUIRED
→ MATERIALIZED
→ BOUND
→ SUBMITTED
→ CONSUMER_COMPLETE
→ RETIRED
→ FREE
```

每lane拥有独立P3 runtime/workspace，使用真实`torch.npu.Event` completion abstraction，支持bounded pressure、reverse completion、abort和stale handle拒绝。

## 2. Why Eager Async Is Insufficient for Graph

Eager completion event通常记录在Draft forward提交后。Graph路径还包括captured task replay、backend update和潜在异步task执行。以下均不能自动等价于consumer complete：

- Python `run_fullgraph`返回；
- `observe(CONSUMER)`被调用；
- `update_full_graph_params`返回；
- UPDATE event存在但未证明覆盖当前replay。

所以Graph必须从实际ACL Graph replay/task owner取得device completion token。

## 3. Carrier Bank

最安全结构：

```text
(capture descriptor, execution lane, consumer ordinal)
    → one stable persistent carrier backing
```

理由：同一个captured address不能在两个inflight generation间共享可变content。若backend未来证明task参数可安全选择不同address，可优化，但不能先假设。

## 4. Required State

- Graph operation/submission id；
- capture descriptor；
- execution lane；
- runtime generation/mapping/request fingerprint；
- backend/consumer identity；
- table/length content version；
- device replay completion event；
- update source/effective generation；
- abort owner和retirement owner；
- backend-derived buffer set。

## 5. Exact Implementation Seams

| File | Function/Class | Work |
|---|---|---|
| `draft_window_async.py` | pool/handle state | generic Graph completion token或并列Graph pool |
| `draft_window_graph.py` | provider carrier registry | descriptor×lane×consumer bank |
| `draft_window_graph_characterization.py` | installer | lane registration，仍default-off |
| `dflash/aclgraph.py::run_fullgraph` | submit boundary | 绑定submission和真实event |
| `compilation/acl_graph.py` / graph runner | task completion source | source审计后提供typed event，不能global lookup |
| backend adapters | derived buffers | 与lane同生命周期 |

## 6. Safe Overwrite Rule

Persistent carrier只有在以下条件同时满足后可重写：

```text
submitted replay has a device completion token
AND token reports complete
AND backend-derived readers are complete
AND previous runtime identity is retired
```

UPDATE(N)调用完成不够。若静态无法确定event覆盖哪个generation，保持`NEEDS_NPU_TIMELINE`和Graph Gate关闭。

## 7. Abort Semantics

- abort-before-submit：清理carrier binding、P3 store、lane，立即可复用；
- abort-after-submit：不能立即复用；转pending，等待真实device completion；
- builder/update异常：若未submit则同步清理；若已submit则保留completion owner；
- process-level reset：逐lane等待/释放，不blind zero状态。

## 8. Red Test List

1. two inflight generations使用不同backing address；
2. delayed A、early B、reverse completion；
3. A pending时同lane overwrite失败；
4. bounded pool pressure只等待/拒绝，不覆盖；
5. stale handle/ABA/generation mismatch；
6. wrong descriptor/lane/consumer；
7. abort before/after submit；
8. event属于另一generation时拒绝；
9. backend-derived buffer alias workspace/FullSource时拒绝；
10. OFF/forced-OFF零pool/provider。

禁止用`sleep`证明race。

## 9. NPU Campaign

至少2–4 lanes，构造A/B/C并让完成顺序与提交顺序不同。抓取task/event timestamps、carrier content version、physical read-set和retire时刻。PASS要求event前无overwrite、reverse completion不污染、pressure deterministic、Target/write不变。

## 10. Dependency

Async依赖目标backend同步Graph carrier先通过G1–G5。FIA、DSA、SFA、Eagle3各自需要验证completion覆盖其全部consumer，不能只做一套Async结论后横向继承。
