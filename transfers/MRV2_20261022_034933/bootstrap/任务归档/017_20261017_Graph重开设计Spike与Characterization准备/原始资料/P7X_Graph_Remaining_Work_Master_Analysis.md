# P7-X MRV2 Draft Sliding Window — Graph Remaining Work Master Analysis

## Executive Summary

本轮不是重新设计 Sliding Window，而是完成两件彼此严格分离的工作：

1. 把 `c43989aabd9b40a561987d39f4ba4516934f2f5b` 的 Ascend-owned capture seam POC 接成一个**默认关闭、仅供 NPU 表征的 base candidate**；
2. 对 Graph × TP/Async/Prefix/Chunked/Mixed/Multi-request/DSA/DSA-CP/SFA/MLA/multi-group/Eagle3/DFlash2 一次性完成源码闭环和实现蓝图。

当前 Graph Track 的事实状态不是“这些 feature 都没有基础”。P1–P7-X 已经为 non-Graph/eager 路径建立 policy、FullSource、Window math、workspace/lease、generation identity、typed transport、method consumer、parallel fingerprint、async ownership、prefix/phase plan。剩余工作是把这些已有契约与 Graph 的 capture address、persistent carrier、backend-derived state、replay/update timeline 和 NPU completion 组合起来。

公共 helper patch 已基本定型：

```text
P3/P7-X generation
    → persistent DraftWindowGraphBindingProvider backing
    → Draft-private InputBuffers capture context
    → patched Ascend capture helper
    → Ascend build_attn_metadata
    → full slot/query/write carriers preserved
```

本轮新增 commit：

```text
8cb4bed670f395c257c1233db944395159916009
spike(spec-decode): prepare graph window characterization
```

它只支持 base characterization route：DFlash 或 eligible DSpark、single dense GQA/FIA group、STANDARD hardware family、TP/DP/PP/PCP/DCP=1、sync、prefix off、FULL/FULL_DECODE_ONLY。它不删除任何公开 Graph fail-closed Gate，也不是产品开关。

还缺的主要不是 host 结构，而是设备证据：真实 ACL Graph capture operand 地址、replay 时 operator physical read-set、UPDATE 对 replay N 还是 N+1 生效、stream completion 与 backing 覆盖安全、Target/write oracle、性能同步成本。TP16、Async、Prefix 等还各有明确代码增量，但不再需要重新做 source spike。

## 1. Exact Baseline

| Repository | Branch | SHA | Tree | Status |
|---|---|---|---|---|
| vLLM | `lucian-dev` | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` | clean, unchanged |
| vLLM-Ascend P7-X perf base | `perf/p7x-draft-window-hotpath` | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` | — | ancestor |
| capture seam POC | `spike/p7x-draft-window-graph-patch` | `c43989aabd9b40a561987d39f4ba4516934f2f5b` | `5caecd1613206904a59960c23f22883115a9fd96` | ancestor |
| base characterization | same branch | `8cb4bed670f395c257c1233db944395159916009` | `899899c23fdc87acaed49c889eecd1f7889ad9c4` | clean |

Commit graph：

```text
1b7215c37  perf(spec-decode): reduce MRV2 draft window hot-path overhead
    ↓
c43989aab  spike(spec-decode): prototype draft window graph capture patch
    ↓
8cb4bed67  spike(spec-decode): prepare graph window characterization
```

R-REPO-01 保持：production/source spike 仅修改 vllm-ascend；pinned vLLM 无 diff。

## 2. Frozen Semantics

Window Graph 只允许改变：

- Draft read block table；
- Draft exact/upper read length；
- 由上述 read state 派生、且属于 Draft 的 backend metadata。

必须保持：

- canonical Full block table；
- absolute positions；
- query layout；
- full slot mapping；
- physical KV write allocation/address；
- Target metadata/cache；
- replay protocol `metadata rebuild → REPLAY → CONSUMER → UPDATE`。

禁止 module global、ContextVar、Target owner swap、temporary full-table swap、修改 vLLM、把 UPDATE 前移到 REPLAY 前。

## 3. Base Candidate Data Flow

```text
policy ELIGIBLE_ON
    ↓
strict internal env flag = 1
    ↓
validate actual Graph context before P2 allocation
    ↓
reuse P2/P7-X inventory with only graph dimension masked internally
    ↓
P3 runtime/workspace + P6 provider
    ↓
register identities from query_cudagraph_manager._capture_descs
    ↓ startup
Draft-private InputBuffers capture scope
    ↓
Ascend capture helper seeds persistent Window backing
    ↓ runtime proposal
existing P4 materialization (same generation / same mapping_epoch)
    ↓
copy into persistent graph carrier; build Draft-private metadata
    ↓
DFlashAclGraphManager.run_fullgraph
    ↓
consume explicit carrier metadata
    ↓
REPLAY → CONSUMER → UPDATE
```

关键点：candidate 不重新 materialize、不推进第二个 epoch；它复用 upstream Graph 调用前已经由 P4 产生的真实 P3 generation，替换该 generation 中不再使用的 eager metadata entry。任何 stale mapping epoch、descriptor、bucket、gid、route、backend/builder identity 都 hard fail。

## 4. G1–G5 Observability

| Gate | Candidate field/evidence | 本地能证明 | 仍需 NPU |
|---|---|---|---|
| G1 capture address | `backing_table_address` + capture descriptor | capture helper收到persistent backing | operator实际capture同一地址 |
| G2 content refresh | stage sequence + table/exact/upper snapshots | A/B/A'同址内容更新、generation不同 | replay间device可见性与无早覆盖 |
| G3 physical-read oracle | CPU table/length snapshot | 期望可见块/长度 | kernel/operator真实read-set |
| G4 full write oracle | slot/position/query address和values | candidate不提供Window slot override | NPU写地址/Target logits不变 |
| G5 timeline | `CAPTURE/MATERIALIZED/BOUND/LIVE/REPLAY/CONSUMER/UPDATE` | Python调用顺序 | UPDATE effective generation、stream完成 |

Recorder 是 instance-owned、bounded、默认静默。它会做显式 D2H snapshot，因此仅用于 characterization，不能用于性能结论。

## 5. Changed Source Map

| File | Function/Class | Change | Baseline effect |
|---|---|---|---|
| `vllm_ascend/envs.py` | env registry | strict default-off internal flag | unset/0 无状态 |
| `worker/v2/spec_decode/draft_window.py` | `_build_draft_window_source_capability_for_context` | 复用冻结 inventory；仅 candidate 可传已验证 context | public entry exact unchanged |
| `worker/v2/spec_decode/draft_window_graph_characterization.py` | candidate/session/recorder | provider install、capture identity、runtime bind、G1–G5 | 无 flag 不构造 |
| `worker/v2/spec_decode/draft_window_eager.py` | `_validated_draft_attention_read_inputs` | candidate 存在时记录 real materialization | 其他路径仍走 P6 observer |
| `worker/v2/spec_decode/dflash/speculator.py` | source init / graph manager init | DFlash candidate bootstrap | CONFIG/FORCED/OFF/eager不安装 |
| `worker/v2/spec_decode/dspark/speculator.py` | same | eligible DSpark candidate bootstrap | V4 co-trained forced-OFF不进入 |
| `worker/v2/spec_decode/dflash/aclgraph.py` | `run_fullgraph` | builder前唯一 prepare/bind 点 | provider absent 为 no-op |
| `worker/v2/spec_decode/dflash/capture.py` | capture helper | G1/G3/G4 bounded snapshots | non-characterization observer no-op |
| `tests/ut/spec_decode/test_draft_window_graph_characterization.py` | 16 contracts | OFF/identity/lifecycle/A-B-A/cleanup/order | CPU/static only |

## 6. Feature Closure Summary

| Feature | Existing eager owner | Graph-specific delta | Shared provider reuse | New adapter/state | Current status |
|---|---|---|---|---|---|
| DFlash base | P4/P7-X parallel path | capture + persistent FIA carrier | yes | current candidate | NPU characterization ready |
| eligible DSpark | same + K/K+1 query width | route/fingerprint exact width | yes | current candidate | NPU characterization ready |
| TP16 | per-rank P7 topology/FullSource | rank in capture identity; per-rank address/read oracle | yes, one provider/rank | rank-aware identity and campaign | design ready |
| Async | P7 async lane pool | carrier bank by descriptor×lane×consumer; graph completion event | provider core yes | Graph lane adapter/event | design ready |
| Prefix | resident snapshot + row phase plan | resident epoch and eviction hold through completion | provider core yes | resident-aware refresh/identity | design ready |
| Chunked/Mixed/Multi | row-wise phase plan + request fingerprint | bucket/phase participation and safe fallback | provider core yes | phase/bucket adapter | design ready; product policy required for mixed |
| DSA | `AscendDSAMetadataBuilder` | stable SAS/SWA/slot-derived capture buffers; update is no-op | identity core only | DSA derived-carrier adapter | design ready |
| DSA-CP | `AscendDSACPMetadataBuilder` | global→rank-local projection + per-step derived bank | identity core only | DSA-CP adapter | design ready |
| SFA/indexer | `AscendSFAMetadataBuilder` | stable main/indexer/top-k/QLI state; update is no-op | identity core only | separate SFA/indexer adapter | design ready, high risk |
| MLA | `AscendMLAMetadataBuilder/Impl` | MLA schema-specific decode carrier/rebind | identity core partly | MLA adapter | design ready |
| multi-group | P2 inventory/P7 source | one generation + N gid carriers | provider must generalize | per-gid bank/consumer ordinal | design ready |
| Eagle3 | P4b AR path | distinct capture manager; first pass + K per-step carriers | provider core yes | Eagle3 capture adapter | design ready |
| DFlash2 | method-specific selector | base Graph support itself absent | no | upstream method prerequisite | blocked before Window |

## 7. DFlash vs DSpark

DFlash 的 query width 固定为 `K+1`。DSpark 的 width 由 checkpoint/config 的 `sample_from_anchor` 决定，可为 `K` 或 `K+1`。已有 fingerprint 同时含：

- normalized method/route；
- `static_k`；
- `query_width`；
- capture descriptor/bucket；
- padded request/token geometry。

因此 base identity 足以区分两者；NPU campaign 仍必须分别覆盖 DSpark K 与 K+1。

## 8. TP16 Conclusion

每个 TP worker/process 拥有自己的 speculator、local `BlockTables`、graph manager、P3 workspace 与 provider。逻辑 Window `[S,E)` 在所有 rank 一致，物理 block table 由各 rank 的 canonical FullSource 投影；绝不能做 `V/TP`。

必须新增/冻结的 capture identity 字段：`tensor_parallel_rank`、`parallel_read_semantics`、通信/FlashComm mode（若启用）。TP16 需要每 rank table/exact/operator read-set 与 full slot/write oracle。它不依赖 Async 或 Prefix，可在 base G1–G5 通过后独立开发与验证。

## 9. Async Conclusion

已有 eager async pool 不能直接证明 Graph 安全。Graph 需要：

```text
descriptor × lane × consumer → persistent carrier bank
```

覆盖 carrier 的最早合法时点是对应 replay 的真实 NPU completion event 已完成之后，不是 Python `run_fullgraph` 返回、不是 UPDATE 调用结束、也不是 eager forward event。需要扩展 lane ownership、Graph submission token 和 reverse-completion tests；base provider/state schema可复用。

## 10. Prefix / Chunked / Mixed / Multi-request Conclusion

Prefix 的最终可见集仍是：

```text
V_final = V_draft ∩ V_native ∩ V_resident
```

Graph persistent carrier不仅要刷新Window table/length，还必须在 DSA/SFA 等 backend 刷新 derived metadata。resident epoch、eviction hold 和 block reuse 必须进入runtime identity/lifetime。

FULL_DECODE_ONLY 的 Draft query graph只应消费 decode proposal。Chunked prefill会改变 FullSource、resident count、seq lengths 和 mapping epoch，即使该 chunk 自身不进入 Draft Graph。Mixed batch不能假设为 uniform decode bucket；要么有明确 mixed capture schema，要么在 replay前安全走 eager/拒绝，不能 silent reuse decode carrier。

Graph carrier固定的是 storage，不是 request row。reorder/finish/add/row reuse 由 ordered request fingerprint + mapping_epoch + generation 检测。

## 11. DSA / DSA-CP / Complex Backend Conclusion

FIA 的 `AscendAttentionBackendImpl.update_graph_params` 能 task-rebind table/length；DSA 和 SFA 的 `update_graph_params` 是 no-op，所以其 SAS/SWA/indexer 等 operand 是 DIRECT_CAPTURED/BACKEND_DERIVED，必须有稳定地址并在 replay 前原地刷新。

DSA-CP 的 Window 计划仍是 global logical `[S,E)`；`AscendDSACPMetadataBuilder` 再投影 local query/seq/index state。不能在 P1/P2 先除 CP world size，也不能改变 full slot/write。

MLA 有真实 task update，但 schema 与 FIA 不同，需要 MLA-specific carrier adapter。SFA main + indexer/QLI 需要单独 adapter；不能把 FIA provider直接标成支持。

## 12. Eagle3 Conclusion

Eagle3 使用 `AutoRegressiveAclGraphManager`，不经过 DFlash capture helper。可复用 provider/identity/backing/observer core，但必须新增 Eagle3 capture adapter：

- first-pass 一组 persistent carrier；
- proposal-frozen `S`；
- static K 的每个 AR step 独立 carrier/consumer ordinal；
- 每 step 从 canonical FullSource 刷新，exact `E_s` 变化；
- step table/length必须同代，禁止lag一step。

因此 Eagle3是“公共provider + 新capture adapter”，不是强行走DFlash helper。

## 13. Dependency Graph and Parallel Work

Base G1–G5 是所有正向路径的共同设备门。通过后可并行推进：

- TP16 rank-aware carrier；
- sync Prefix resident-aware carrier；
- Eagle3 capture adapter；
- DSA derived carrier；
- MLA adapter。

Async依赖所选backend/adapter先有正确的同步Graph carrier；DSA-CP依赖DSA + CP projection；Mixed依赖phase/bucket policy；multi-group依赖各gid backend adapter。

详见 `P7X_Graph_Feature_Dependency_Graph.md`。

## 14. Maturity

| Area | Maturity | Explanation |
|---|---|---|
| Architecture | GREEN | read/write boundary、owner、typed identity已冻结 |
| Capture seam | GREEN (source/static) | POC + instance-owned patched helper；NPU地址仍待证 |
| Runtime carrier | GREEN (host/static) | same-generation bind、A/B/A、stale/cleanup已测 |
| G1–G5 instrumentation | GREEN (ready) | default-off、bounded、字段完整；尚未跑NPU |
| NPU correctness | RED | physical read/timeline/stream未验证 |
| TP/TP16 | YELLOW | eager owner与Graph delta明确，未编码/未NPU |
| Async | YELLOW | state machine明确，缺Graph completion绑定 |
| Prefix | YELLOW | resident算法已存在，缺Graph residency lifetime |
| Chunked/Mixed/Multi | YELLOW | phase/identity已有，缺Graph bucket与owner policy |
| DSA | YELLOW | builder/derived buffers已定位，缺adapter |
| DSA-CP | YELLOW | local projection已定位，依赖DSA Graph adapter |
| SFA/MLA/indexer | YELLOW/RED | seams明确；SFA/indexer新增面较大 |
| Multi-group | YELLOW |逻辑契约明确，provider仍single-group |
| Eagle3 | YELLOW |独立call chain已闭环，capture adapter未编码 |
| Product readiness | RED | public Gate冻结；无NPU Graph证据 |

## 15. Tests and Static Checks

| Command class | Result | Limitation |
|---|---|---|
| Candidate + P6 carrier | 65 passed | CPU/static |
| P1–P7X/P5/P6/graph targeted | 444 passed | CPU/static |
| attn_utils/attention_v1/BlockTables | 101 passed + 23 subtests | host |
| full `tests/ut/spec_decode` | 654 passed, 13 skipped, 7 failed | 7 failures all stop at host `Invalid attention backend for None`; not PASS |
| Ruff check / format check | PASS | changed files |
| targeted Mypy | PASS | `--follow-imports=skip`, pinned vLLM on PYTHONPATH |
| compileall / diff-check | PASS | changed paths |
| repository pre-commit | ENVIRONMENT BLOCKED | actionlint Go dependencies timed out at `proxy.golang.org` |

异常清理新增了真实 RED→GREEN：recorder在metadata bind之后失败时，旧实现留下 `BOUND` carrier；修复后 provider释放bound state，proposal scope继续作为P3唯一retirement owner，下一generation可安全绑定。

## 16. Required Remaining Iterations

对 base DFlash/DSpark single-card route，实际最少还需要：

```text
1 NPU iteration (G1–G5)
→ 1 local adjudication/cleanup iteration
→ 1 NPU confirmation/performance iteration
```

若 G1–G5 首轮暴露真正carrier/timeline代码问题，则多一轮 local fix + NPU rerun。

对全 feature Graph completion，建议按依赖而非按feature逐个source-spike：

```text
Iteration A: base G1–G5 NPU
Iteration B: 并行实现 TP16 + Prefix + Eagle3 adapter + DSA/MLA adapter
Iteration C: 一次批量 G6 NPU campaign
Iteration D: Async + DSA-CP + multi-group/mixed integration
Iteration E: final NPU/performance/release adjudication
```

也就是在 base evidence顺利的情况下，大约 **2 local implementation iterations + 2 NPU campaigns + 1 final cleanup/freeze**。SFA/indexer或mixed产品范围若被列为首版mandatory，可能再增加1–2轮。

## 17. Final Status

```text
COMMON GRAPH SEAM: GREEN (source/static)
BASE RUNTIME CARRIER: GREEN (host/static)
G1-G5: READY FOR NPU CHARACTERIZATION
PUBLIC GRAPH SUPPORT: STILL FROZEN
GRAPH NPU CORRECTNESS: NOT VERIFIED
DO NOT PUSH
```

本轮不声称 Graph Window supported，不继承 eager NPU evidence，不把CPU snapshot当physical read proof。
