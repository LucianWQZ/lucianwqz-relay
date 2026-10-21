# P7-X Graph TP / TP16 Design

## Decision

```text
GRAPH_TP_DESIGN: IMPLEMENTATION-READY
GRAPH_TP_CODE: NOT IMPLEMENTED
GRAPH_TP_NPU: NOT VERIFIED
```

## 1. Current Ownership

每个TP rank是独立worker/process，拥有自己的：

- `AscendDFlashSpeculator`或`AscendDSparkSpeculator`；
- local `BlockTables`和canonical FullSource；
- P3 workspace/lease；
- ACL Graph manager和capture descriptors；
- P6 provider/carrier bank。

因此provider天然instance-scoped、per-rank，不需要跨rank共享Python对象或device address。

## 2. Mathematical Contract

Window scalar plan在所有rank使用相同absolute logical区间：

```text
S = align_down(max(H-W, 0), B)
V = E-S
```

普通TP不切分sequence，所以每rank保持同一个logical `V`；禁止：

```text
V_local = V / TP
```

每rank从自己的canonical full table取得对应物理block IDs。逻辑可见集相同，物理表内容可因rank-local KV ownership而不同。

## 3. Required Typed Delta

`DraftWindowGraphRouteFingerprint`或等价capture fingerprint增加并强校验：

- `tensor_parallel_rank`；
- `parallel_read_semantics`，base为`replicated`；
- TP world size（已有）；
- backend/builder per-rank identity；
- FlashComm/sequence-parallel mode（已有布尔但必须参与compatibility）；
- provider schema version bump。

CaptureIdentity仍不含request generation。RuntimeBindingIdentity继续含generation/mapping/request/lane，并必须与rank fingerprint兼容。

## 4. Exact Implementation Files

| File | Function | Delta |
|---|---|---|
| `worker/v2/spec_decode/draft_window_graph.py` | `DraftWindowGraphRouteFingerprint` | rank/read-semantics字段与diagnostic |
| same | `register_capture_identity` / compatibility validator | rank/world/semantics hard check |
| `draft_window_graph_characterization.py` | install/source validation |允许TP>1 only after rank fields; per-rank recorder |
| `dflash/aclgraph.py` | `capture/run_fullgraph` |无全局集合；每rank本地bind/update |
| `draft_window_eager_capability.py` | existing topology builder |复用`tensor_parallel_rank`与`parallel_read_semantics` |

不应修改pinned vLLM。

## 5. Capture and Runtime

```text
rank r FullSource
→ rank r P3 table
→ rank r provider carrier
→ rank r capture identity
→ rank r Ascend metadata
→ rank r FIA operator
```

Cross-rank coordination只用于验证同proposal/generation语义，不用于传table。capture descriptor必须在每rank解析为唯一carrier。

## 6. Failure Rules

以下在P2/workspace前或bind前hard fail：

- rank不在`[0,tp_size)`；
- runtime tp_size/rank与capture fingerprint不同；
-某rank无registered descriptor；
- backend/builder/layout跨rank意外不同；
- `parallel_read_semantics`不是已验证值；
- SP/DSA-CP/FlashComm被当作普通TP；
- partial rank submission或generation skew。

## 7. Red Test List

1. TP2/TP4/TP16 fake workers各有不同provider/backing address；
2. 所有rank scalar S/E/V相同；
3. rank-local tables允许内容不同但都来自本rankFullSource；
4. 错误`V/TP` oracle必须失败；
5. rank0 identity不能bind rank1 generation；
6. runtime world size drift失败；
7. one-rank stale epoch导致整个case失败；
8. full slot/positions/query保持本rankcanonical owner；
9. CONFIG_OFF/FORCED_OFF每rank零Graph state；
10. public Graph Gate仍关闭。

## 8. TP16 NPU Oracle

每rank记录：

- global proposal id/generation/mapping_epoch；
- rank/world；
- capture descriptor和backing address；
- local canonical full table；
- materialized Window table和exact/upper；
- actual operator block table/length pointer；
- physical read-set；
- full slot/write pointer和值；
- replay/update/completion event。

PASS要求：所有ranklogical S/E/V一致；operator读取各自expected local blocks；无rank读到另一rank/stale generation；Target/logits与scope内oracle一致。

## 9. Dependencies and Iterations

TP16只依赖base G1–G5，不依赖Prefix或Async。建议一轮local rank-aware implementation + 一轮TP16 NPU；若FlashComm也mandatory，应作为独立后续组合，而不是混入基础TP。
