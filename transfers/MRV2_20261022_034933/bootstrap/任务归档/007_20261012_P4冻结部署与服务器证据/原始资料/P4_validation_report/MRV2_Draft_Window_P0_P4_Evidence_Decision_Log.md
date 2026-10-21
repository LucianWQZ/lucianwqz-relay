# MRV2 Draft Sliding Window P0–P4 Evidence Decision Log

> 目的：记录本地源码、Freeze包与服务器证据发生表面冲突时的最终事实裁决。  
> Production：vLLM `84030bbe...`；vLLM-Ascend `1011e2c2...`。  
> 服务器证据机：Node133 / `ascend-910b2`（A2）。Node101/A3：**UNKNOWN**。

## 1. Evidence priority

1. 本地真实production源码与Git历史；
2. 服务器原始trace/log索引；
3. 服务器中文终局报告；
4. Implementation Notes；
5. Frozen Design；
6. 推断。

服务器debug SHA `2a485613...`只用于observability。六个debug commits均非Final ancestor，
不能写入production lineage或作为部署依赖。

## 2. 证据等级解释

| Level | 本项目含义 | 能证明 | 不能证明 |
|---|---|---|---|
| Static/CPU | types/math/state machine/source/differential tests | host contract与代码控制流 | NPU kernel、stream时序、性能 |
| L3 | production runtime state/descriptor/materialized tables trace | 输入状态与canonical投影一致 | operator或kernel一定消费 |
| L4 | FIA operator调用参数 | backend/operator入口收到目标table/length | device kernel实际读了哪些KV |
| L5 | kernel/profiler physical read trace | physical read-set与时序 | 未执行时不能由L4推断 |

因此服务器P4b结论是L3+L4，不得写成Level 5。

## 3. Runtime Evidence Decision Table

| Claim | Server verdict | Local source compatibility | Final decision | Remaining evidence |
|---|---|---|---|---|
| Production SHA/tree | CONFIRMED | 两repo本地exact且clean；Final tree `7d165d58...` | PASS | 无 |
| Debug lineage隔离 | CONFIRMED | debug commits非Final ancestors | PASS；debug不得交付 | 持续审计 |
| P1 policy/math | static PASS | source/tests一致 | PASS static | 无独立NPU gate |
| P2 source/provider | static PASS | source/tests一致 | PASS static | runtime由具体P4 route证明 |
| P3 ownership/lifetime | static PASS | source/state-machine一致 | PASS static / NPU lifetime OPEN | device happens-before |
| P4a static | STATIC_VERIFIED | DFlash/DSpark integration存在且CPU green | PASS static | 无 |
| P4a Window ON NPU | NOT_EVIDENCED | 源码不能代替NPU | **OPEN** | physical read、Target/write、lifecycle、profiler |
| GLM DSpark TP8 OFF smoke可代替P4a | 不可 | OFF且TP8不是eligible exact route | REJECTED | 必须Window ON exact route |
| P4b single-request semantic | PASS L3+L4 | frozen S、per-step E/V、source/materialize和exact carrier一致 | **PASS scoped** | L5/lifetime/performance仍缺 |
| P4b FullSource projection | 852/852 equality | 每step从canonical source materialize | PASS scoped | 多请求与isolated future-column event |
| P4b proposal steps | 284/284 exp==obs==3 | static K=3 contract一致 | PASS scoped | 其它K与dynamic-K不外推 |
| P4b exact boundary | E04 L0=189,H=192,start=128 | integer math一致 | PASS observed fixture | 更多W/B组合仍属static覆盖 |
| write/Target isolation | 84/84 before==after | full slot/positions/query/Target invariant一致 | PASS observed route | 多请求/parallel仍未证 |
| controlled multi-request pure decode | INCOMPLETE；四种构造未形成batch>1 | source支持fingerprint，但runtime未触达 | **OPEN**；不能称PASS或普遍不可能 | 可控scheduler/admission harness |
| sequential same-engine isolation | PASS A→C→A | epochs/fingerprints/retirement一致 | PASS as sequential evidence | 不是simultaneous batch证明 |
| persistent row reuse | NOT_OBSERVED | static contract存在 | OPEN | instrument idx_mapping并构造same-row replacement |
| strict reorder `[A,B]→[B,A]` | NOT_OBSERVED | static contract存在 | OPEN | batch>1 trace |
| independent slot oracle | REFUTED_AS_ACHIEVED / INCOMPLETE | static保持full slot，但trace截断 | OPEN | 完整FullSource/slot值 + 独立recompute |
| FIA operator inputs | L4 PASS；Draft 33/33 kv==visible exact | explicit exact carrier一致 | PASS at L4 | P4a与L5 |
| kernel physical read-set | NOT_OBSERVED | 无源码反证 | **OPEN** | profiler/kernel trace |
| future-column real inter-step demand | PARTIAL | CPU future-column oracle存在 | PARTIAL runtime | 隔离出step间新增column需求事件 |
| rejection cross-boundary | INSUFFICIENT_EVIDENCE | CPU rejection tests存在 | OPEN runtime | deterministic rejection fixture |
| NO_SYNC result | scope-limited equality | 不等于completion ownership | 只证明结果非观测插桩依赖 | device happens-before evidence |
| device lifetime | OPEN | CPU lease不能替代stream event | **OPEN** | event/timeline/profiler |
| general online mixed arrivals | UNSUPPORTED_WITH_ENGINE_ABORT | source在mixed proposal hard reject | **BLOCKED** | 支持mixed或admission前安全拒绝 |
| negative Gates | 5/6 confirmed | source中均有fail-closed | PARTIAL runtime PASS | dynamic-K negative未跑 |
| R4 performance | NOT_RUN | static无性能结论 | **OPEN** | profiler、latency、throughput、D2H/H2D |
| P5 readiness | design preflight READY；Graph ON BLOCKED | graph Gate仍闭合 | P5 DESIGN READY / ENABLE BLOCKED | P5 source/design proof后再审 |
| Feature release | HOLD | 所有open项与product scope未闭合 | **HOLD** | owner mandatory matrix |

## 4. 服务器 conflict-resolution 全量归档

| ID | 原claim | 服务器裁决 | 最终采用 |
|---|---|---|---|
| C01 | Final production SHA/tree identical | CONFIRMED | 接受 |
| C02 | Debug lineage isolated | CONFIRMED | 接受；debug不进production |
| C03 | P4a CPU/static | CONFIRMED | PASS static |
| C04 | P4a NPU Window ON | NOT_EVIDENCED | OPEN |
| C05 | P4b single-request semantics | CONFIRMED | scoped PASS |
| C06 | P4b FullSource projection | CONFIRMED | scoped PASS |
| C07 | write-side/Target isolation | CONFIRMED | scoped PASS |
| C08 | independent slot oracle done | REFUTED | OPEN |
| C09 | Eagle3 K=3 multi-step | CONFIRMED | scoped PASS |
| C10 | future-column real demand | PARTIAL | PARTIAL |
| C11 | cross-boundary rejection | INSUFFICIENT_EVIDENCE | OPEN |
| C12 | controlled multi-request achieved | REFUTED_AS_ACHIEVED | OPEN；不推断永远不可达 |
| C13 | sequential same-engine isolation | CONFIRMED | PASS，限定sequential |
| C14 | persistent row reuse | NOT_OBSERVED | OPEN |
| C15 | strict reorder | NOT_OBSERVED | OPEN |
| C16 | Level-4 FIA operator input | CONFIRMED | L4 PASS |
| C17 | Level-5 kernel read | NOT_OBSERVED | OPEN |
| C18 | device happens-before | INSUFFICIENT_EVIDENCE | OPEN |
| C19 | NO_SYNC evidence scope | CONFIRMED_AS_SCOPE_LIMITED | 仅保留有限结论 |
| C20 | mixed arrival blast radius | CONFIRMED | BLOCKED/general serving风险 |
| C21 | E12 negative gates | CONFIRMED_5_OF_6 | PARTIAL；dynamic-K未跑 |
| C22 | dynamic-K negative | NOT_RUN | OPEN runtime evidence |
| C23 | R4 performance | NOT_RUN | OPEN |
| C24 | P5 readiness | PARTIAL | design ready / graph enable blocked |
| C25 | release status | HOLD | HOLD |

## 5. Final source corrections to older Notes

以下不是篡改历史Notes，而是按Final source确定当前事实：

1. P4a review时曾记录“continuing chunked prefill fail closed”；Final commit `1011e2c2` 已把
   continuing和terminal pure scheduler-prefill统一改为baseline bypass。mixed仍拒绝。
2. P4b Notes review前写“无公司NPU report”；其后服务器终局报告增加了Node133/A2单请求L3+L4证据。
   所以P4b single-request NPU从OPEN更新为scoped PASS，但general `G-AR-STEP`仍OPEN。
3. Frozen/Notes中的静态future-column与rejection oracle不能替代服务器runtime缺口。
4. 服务器Node101/A3报告不存在，不能从A2推断A3。

## 6. 不得越界的表述

禁止在后续报告或PR中写：

- “P4已NPU全量通过”；
- “Eagle3 multi-request已支持”；
- “FIA参数证明kernel physical read-set”；
- “NO_SYNC equality证明workspace overwrite安全”；
- “P4b single-request证明P4a DFlash/DSpark”；
- “Node133 A2证明Node101 A3”；
- “Graph/Async/prefix/parallel/complex backend已支持”；
- “Feature ready/release ready”。

允许的准确表述是：

> P1–P4b production和static contract完成；P4b在Node133/A2的K3/W64/TP1/serialized eager
> 单请求路由有L3+L4证据；P4a NPU、P4b multi-request、L5、device lifetime、performance、Graph及
> release gates仍未关闭。

## 7. Final decisions

```text
P0–P3 PRODUCTION: PARTIAL
P4a STATIC: PASS
P4a NPU: OPEN
P4b STATIC: PASS
P4b SINGLE-REQUEST NPU: PASS
P4b MULTI-REQUEST NPU: OPEN
P0–P4 REQUIRED DELIVERY: PARTIAL
P5 DESIGN ENTRY: READY
P5 PRODUCTION GRAPH ENABLE: BLOCKED
FEATURE RELEASE: HOLD
```
