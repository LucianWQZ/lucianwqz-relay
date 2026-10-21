# P5 Ascend-only Draft Window Graph Binding Foundation — Implementation Notes

## Document status

| Item | Final fact |
|---|---|
| Frozen design | `MRV2_Speculative_Draft_Sliding_Window_Final_Design.md` |
| Implementation plan | `MRV2_Draft_Window_Implementation_Plan.md` |
| vLLM baseline | `84030bbe3d74d99bad477a3d2e37a973ccd8865c`，clean，未修改 |
| vLLM-Ascend parent | P4 Final `1011e2c2fa99729a46efde5b5bbaf6daed975a2c` |
| P5 branch | `feature/p5-ascend-graph-binding-foundation` |
| P5 commit | `266eec5d6a7bd391d6287937ebc03b2289b5618f` |
| P5 tree | `dd8bee7c63b250639345bea4aa5560ef176bda2c` |
| Repository rule | `R-REPO-01`：production 只修改 `vllm-ascend` |
| Local result | P5 foundation / source spy static contract implemented |
| User-visible Graph Window | **仍 fail closed** |
| NPU evidence | 未运行；P5 不声称 Graph correctness 或 support |

P5 是 production foundation，不是 Graph enablement。它把 P3 的稳定 workspace、完整
generation identity 和 P4 的唯一 live validation boundary，显式接到 Ascend 自有的 graph
manager 观测面；它没有移除任何 `FULL`、`FULL_DECODE_ONLY`、`PIECEWISE` Gate。

## 1. P5 Source Preflight

### 1.1 Exact checkouts

Preflight 开始时及提交后均确认：

```text
vLLM HEAD        = 84030bbe3d74d99bad477a3d2e37a973ccd8865c
vLLM status      = clean
vLLM-Ascend base = 1011e2c2fa99729a46efde5b5bbaf6daed975a2c
P5 HEAD          = 266eec5d6a7bd391d6287937ebc03b2289b5618f
```

未引入 upstream prototype API，未修改 pinned vLLM，未修改 site-packages。

### 1.2 Eagle3 live call chain

```text
AscendAutoRegressiveSpeculator.propose()
  -> cache current InputBatch
  -> Eagle3 proposal scope / P4 mapping_epoch
  -> upstream AutoRegressiveSpeculator.propose()
     -> prepare full positions/query/slot mappings
     -> first pass:
        eager -> Ascend _prefill()
        FULL  -> prefill_cudagraph_manager.run_fullgraph()
     -> later AR steps:
        eager -> Ascend/upstream _multi_step_decode() -> per-step _generate_draft()
        FULL  -> decode_cudagraph_manager.run_fullgraph()
```

当前 Window ON graph route 在 P2 runtime capability gate 被拒绝，因此 production 不会创建
P3/P5 state。P4b eager 的 `_validated_eagle3_read_inputs()` 是唯一 live read-input boundary；
P5 在该 boundary 完成 P3 validation 后增加 `LIVE` 观测，provider 不存在时严格 no-op。

### 1.3 Eagle3 capture call chain

```text
AscendAutoRegressiveSpeculator.capture()
  -> prefill_cudagraph_manager.capture(_prefill, ...)
     -> AutoRegressiveAclGraphManager.capture()
        -> CAPTURE observation (only if an instance provider exists)
        -> communicator/model capture scopes
        -> upstream SpeculatorCudaGraphManager.capture()
        -> captured first-pass graph consumer
        -> CONSUMER observation
  -> decode_cudagraph_manager.capture(_multi_step_decode, ...)
     -> AutoRegressiveAclGraphManager.capture()
        -> CAPTURE observation
        -> Ascend create_forward_fn + generic CudaGraphManager.capture()
        -> captured merged AR graph consumer
        -> CONSUMER observation
```

First-pass 与 AR-step 不是一个模糊 `graph_supported=True` 路由；它们分别使用
`EAGLE3_FIRST_PASS` / `EAGLE3_AR_STEP`，并强制 `PROPOSAL/step=0` 与
`STEP/step>0` identity。

### 1.4 Eagle3 replay call chain

```text
AutoRegressiveAclGraphManager.run_fullgraph(desc)
  -> speculator.build_draft_attn_metadatas(...)
  -> update_stream waits for current stream
  -> REPLAY observation
  -> upstream SpeculatorCudaGraphManager.run_fullgraph(desc)
     -> generic graph runner dispatches ACL graph replay
     -> captured attention consumer executes here
  -> CONSUMER observation
  -> establish draft forward context
  -> UPDATE observation
  -> update_full_graph_params(..., draft_attn_metadatas=...)
     -> backend update_graph_params()
  -> return replay output
```

这里的顺序非常重要：`REPLAY -> CONSUMER -> UPDATE` 是当前 exact checkout 的 Python
控制流，不是设计图推断。

### 1.5 DFlash live/capture/replay call chain

Live：

```text
AscendDFlashSpeculator.propose()
  -> cache InputBatch
  -> P4 proposal scope / mapping_epoch
  -> upstream DFlash propose()
     -> prepare_dflash_inputs (full positions/query/physical slot state)
     -> build Draft metadata
        -> P4 single validation boundary
        -> P5 LIVE observation when provider exists
     -> eager _generate_draft() or query_cudagraph_manager.run_fullgraph()
```

Capture：

```text
upstream DFlashSpeculator.capture()
  -> DFlashAclGraphManager.capture()
     -> CAPTURE
     -> existing communicator/model capture scopes
     -> upstream DFlashCudaGraphManager.capture()
     -> captured attention consumer
     -> CONSUMER
```

Replay：

```text
DFlashAclGraphManager.run_fullgraph(desc)
  -> build_draft_attn_metadatas()
  -> stream wait
  -> REPLAY
  -> upstream DFlashCudaGraphManager.run_fullgraph(desc)
     -> actual captured consumer
  -> CONSUMER
  -> forward context
  -> UPDATE
  -> update_full_graph_params(...)
```

### 1.6 DSpark relationship

`AscendDSparkSpeculator` 复用 DFlash query graph manager 与 P4a eager integration seam；区别
在 method identity、query width 与自己的 metadata update。P5 因而使用独立 `DSPARK`
route，但 capture/replay source points 位于同一个 `DFlashAclGraphManager`。测试以真实
`method=dspark` P3 runtime 验证 `DSPARK` route，不能拿 DFlash identity 冒充。

### 1.7 Backend update path

`vllm_ascend.compilation.acl_graph.update_full_graph_params()` 解析 backend impl 后调用
`impl_cls.update_graph_params(...)`。标准 FIA 的 `AscendAttentionImpl.update_graph_params()`
会从 `draft_attn_metadatas` 取 read length/block-table carrier，并通过 NPU graph-task update
重绑任务参数；这种 consumer 分类为 `TASK_REBOUND`。其他 backend 将来必须逐项标明：

- `DIRECT_CAPTURED`：capture 时直接固定地址；
- `TASK_REBOUND`：通过 graph-task update 重绑；
- `BACKEND_DERIVED`：backend 从其它 carrier 派生真实 operand。

P5 只建立三类 typed vocabulary 和 source trace；不据此自动批准任何 backend。

## 2. Source drift

### SD-P5-01 — replay/update timing

旧设计中对 `enable_enpu` 的一条假设认为 MRV2 可以在 replay 前更新 graph parameters。
当前 exact source 不是该时序：AR 与 DFlash/DSpark manager 都先调用
`super().run_fullgraph()`，随后才调用 `update_full_graph_params()`。

最终裁决：

```text
Historical assumption: update -> replay -> consumer
Current source:        replay -> consumer -> update
Status:                CHANGED / old enable_enpu timing invalidated
P5 consequence:        source spy must expose this order; Graph ON remains blocked
```

P5 没有试图“修”这个时序。P6 必须在真实 NPU 上证明 task update 对当前/下一次 replay
的生效关系，再决定安全 binding 点。

### SD-P5-02 — Ascend-owned instance seam exists

历史 Plan 倾向 upstream `DraftCaptureBindingProvider` / optional hook。R-REPO-01 后重新检查
发现 Ascend manager 已由现有项目 patch architecture 安装，且 speculator 初始化后把
`self` 明确写入 manager 的 `speculator` 字段。因此可在不新增 monkeypatch、不修改 vLLM、
不使用 global/ContextVar 的前提下，通过现有 instance reference 建立 source observation。

这改变的是 implementation seam，不改变 Frozen read/write semantics。

## 3. Ascend-only seam selection

| Candidate | Correctness | Instance ownership | Shared mutation | Drift surface | Verdict |
|---|---|---:|---:|---:|---|
| 修改 vLLM generic provider/hook | 可以表达 | 可 | 无 | upstream API | **拒绝：违反 R-REPO-01** |
| 新增 import-time monkeypatch | 难证明 | 弱 | 可能 | 大 | **拒绝** |
| module global / ContextVar transport | 并发不安全 | 否 | 是 | 隐式 | **拒绝** |
| 临时替换 full table/input buffer/Target state | 污染 write/Target | 否 | 是 | 高 | **拒绝** |
| 复制整段 upstream graph builder | 可漂移 | 可 | 无 | 极大 | **拒绝** |
| 现有 Ascend manager + speculator-owned provider | 显式 fail closed | **是** | **无** | 小 | **选择** |

最终 seam：

```text
Speculator instance
  owns P3 DraftWindowRuntimeState
  optionally owns P5 DraftWindowGraphBindingProvider
                  |
                  +-> P4 eager validation boundary: LIVE
                  +-> Ascend graph manager: CAPTURE / REPLAY / UPDATE / CONSUMER
```

Provider 必须显式安装；P5 没有 production 自动安装 caller。这样 CONFIG_OFF、FORCED_OFF
与当前 Graph fail-closed route 都不会创建 P5 provider/descriptor/backing。

## 4. Identity schema

`DraftWindowGraphBindingIdentity` 是 immutable value，携带：

| Field | Source | Purpose |
|---|---|---|
| `method` | P3 normalized method | 区分 Eagle3/DFlash/DSpark |
| `route` | P5 explicit route | 区分 Eagle3 first-pass/AR-step 及 parallel draft |
| `global_group_id` | P3 generation | 锁定真实 consumer gid |
| `proposal_id` | caller/P6 proposal identity | 区分 proposal；不是地址 token |
| `generation_id` | P3 runtime | 防 ABA/stale generation |
| `mapping_epoch` | P4 caller-owned epoch | 防同 pointer 原地改写 |
| ordered request fingerprint | P3 generation | 检测 reorder/finish-add/row replacement |
| actual/padded counts | P3 generation | 锁定active与capture geometry |
| provider id/version | P3 capability/runtime | 防错误 provider/version |
| source owner id | canonical FullSource identity | 检测错误 source owner |
| `phase` / `step` | P3 generation | first-pass 与 AR step 强类型区分 |
| execution lane | P3 generation | 防跨 lane 误绑；当前仅 lane 0 |

任何 generation、mapping_epoch、request fingerprint、gid、route、phase、step、lane、consumer
kind、metadata owner 或 backing identity 不一致都 hard fail。没有自动刷新、静默重绑或旧
generation 复用。

## 5. Stable backing contract

P5 descriptor 引用完整 P3 workspace owner，而不是 per-call slice/clone：

| Backing | Owner | Address | Contents | Freshness |
|---|---|---|---|---|
| Window block table | `DraftWindowWorkspace` | fixed for workspace lifetime | generation mutable | generation + epoch |
| valid block counts | same | fixed | generation mutable | same |
| device exact | same | fixed | generation mutable | same |
| CPU exact | same | fixed | generation mutable | same |
| CPU upper | same | fixed | generation mutable | same |

绑定时及每次 observation 均重新验证：

1. P3 lease仍active；
2. workspace bound identity与inputs一致；
3. backing owner/address/shape/stride/dtype/device未变化；
4. backing不与canonical FullSource table或valid-count storage alias；
5. active binding不能被另一个generation覆盖；
6. retirement后旧descriptor不能observe；
7. 新generation可以在相同地址写入新内容，但旧expectation被拒绝。

P5 descriptor 不包含 positions、slot mapping、Target metadata、canonical FullSource owner，
因此不能成为 write-side override。

## 6. Source-spy schema

`DraftWindowGraphSourceEvent` 只在调用方提供 observer 时交付，provider 默认不存事件、不打
日志、不写global。每个事件包含：

- monotonic per-provider sequence；
- `LIVE/CAPTURE/REPLAY/UPDATE/CONSUMER` stage；
- 完整 binding identity；
- consumer kind / metadata owner；
- backing identity；
- table address/geometry fingerprint；
- device exact、CPU exact、CPU upper address/geometry fingerprint。

Fingerprint 刻意不执行 `.cpu()`、`item()`、tensor reduction 或内容拷贝，因此 P5 不给 hot
path 新增 D2H。内容正确性仍由 P3 generation contract、P6/NPU oracle验证。

默认 observer 为 `None`。这不是全局 Debug trace framework，也不是 runtime logging feature。

## 7. Files changed

| File | Change | Why |
|---|---|---|
| `vllm_ascend/worker/v2/spec_decode/draft_window_graph.py` | 新增typed route/stage/consumer/identity/backing/descriptor/provider/observer contract | P5核心；instance-owned，复用P3 backing |
| `.../draft_window_eager.py` | P4a single validation boundary后可选 `LIVE` observation | 对照live source，不改变read inputs |
| `.../draft_window_eagle3.py` | P4b single validation boundary后可选 `LIVE` observation | first-pass/AR step共享typed source spy |
| `.../autoregressive/aclgraph.py` | capture/replay/consumer/update source points | Eagle3 first-pass与AR graph时序 |
| `.../dflash/aclgraph.py` | capture/replay/consumer/update source points | DFlash与DSpark共享graph时序 |
| `tests/ut/spec_decode/test_draft_window_graph_binding.py` | 35项P5 contract/integration tests | identity/backing/spy/method/timing regression |
| `tests/ut/spec_decode/test_draft_window.py` | CONFIG_OFF/FORCED_OFF zero-P5-state断言 | baseline allocation invariant |

没有修改 vLLM；没有修改 scheduler、BlockTables、Target metadata、slot mappings、positions、
attention operator或Graph user Gate。

## 8. Test-first evidence

最初红测在正确 P1–P4 Python 环境中为：

```text
ModuleNotFoundError:
vllm_ascend.worker.v2.spec_decode.draft_window_graph
```

核心实现后 P5 targeted 为 `28 passed`；加入 Eagle3 manager与live boundary覆盖后为
`35 passed`。时序自审又先把expected order改为真实 `REPLAY -> CONSUMER -> UPDATE`，旧
实现得到3个红测，再移动source point后恢复 `35 passed`。

| Command/scope | Result | Limitation |
|---|---|---|
| P5 targeted | `35 passed` | CPU/static spy；非NPU Graph运行 |
| P1–P5 + graph contracts + DFlash2 + attn utils + attention_v1 | `383 passed, 2 subtests passed` | host-only |
| full `tests/ut/spec_decode` | `507 passed, 13 skipped, 7 failed, 2 subtests passed` | 7项既有VWN host backend failure；不是PASS |
| Ruff check / format | PASS | all 7 changed files |
| targeted Mypy | PASS | 5 production source files |
| compileall | PASS | spec_decode + P5 test |
| `git diff --check` | PASS | no whitespace errors |
| executable pre-commit hooks | PASS | Ruff/codespell/typos/filename/init/logger/import/boolean/long-function/symbolic-meta |
| actionlint aggregate setup | environment blocked | Go dependency download timeout |
| gitleaks hook | environment blocked | local `gitleaks` absent and `wget` unavailable；不是PASS |

7个full-suite失败均位于 `test_speculators_vwn_eagle3.py`，错误为
`Invalid attention backend for None`，堆栈不经过P5文件；与P4冻结报告中的同一组host
failure一致。

## 9. Invariant audit

| Invariant | Result |
|---|---|
| vLLM exact baseline / no private patch | PASS |
| only vllm-ascend modified | PASS |
| CONFIG_OFF zero P5 provider/descriptor/backing | PASS |
| FORCED_OFF zero P5 provider/descriptor/backing | PASS |
| Graph baseline path no provider = no-op | PASS |
| generation / mapping_epoch / request/gid/route/phase/step/lane mismatch | hard fail |
| stable address / mutable generation contents | PASS |
| no canonical FullSource alias | PASS |
| no Target/write-side fields | PASS |
| no temporary/per-call clone backing | PASS |
| no stale generation reuse | PASS |
| no module global or ContextVar transport | PASS |
| no shared owner swap | PASS |
| P4a/P4b live read carrier unchanged | PASS |
| `FULL/FULL_DECODE_ONLY/PIECEWISE` Window ON | **STILL FAIL CLOSED** |
| Graph support claim | **NONE** |

## 10. Unsupported routes and NPU gaps

P5 不支持或不启用：

- Eagle3/DFlash/DSpark Graph Window ON；
- FULL、FULL_DECODE_ONLY、PIECEWISE；
- Async；
- multi-group；
- MLA/DSA/SFA/V4.1/native/recycling；
- TP/DP/PP/PCP/DCP/SP/DSA-CP/FlashComm；
- prefix cache或Window化mixed/chunked prefill；
- DFlash2、plain Eagle、MTP、dynamic-K；
- scheduler/admission改动。

仍缺少的真实NPU证据：

1. capture 时 operator 最终绑定的地址；
2. replay 使用的是 capture address、task-rebound address还是backend-derived address；
3. replay后 update 对当前或下一次 replay 的生效语义；
4. actual physical read-set（L5）；
5. generation间 device happens-before / event retirement；
6. graph recapture、shape bucket与lane pressure；
7. latency、D2H/H2D、workspace性能。

## 11. P6 seam

P6 可以复用：

- `DraftWindowGraphRoute`；
- `DraftWindowGraphBindingIdentity` / `Expectation`；
- P3 workspace backing identity；
- explicit install/bind/observe API；
- existing Ascend manager source points；
- P4 live source oracle；
- `DIRECT_CAPTURED/TASK_REBOUND/BACKEND_DERIVED` classification。

但 P6 开始前必须先回答：

1. startup capture generation如何建立，是否需要专门capture identity；
2. capture backing与live P3 workspace是否同一owner/address；
3. 当前 `replay -> consumer -> update` 下，哪个 update影响哪个replay；
4. Eagle3 first-pass与AR-step是否需要独立lane/backing；
5. DFlash/DSpark query width与capture buckets如何绑定；
6. 真实NPU completion token怎样控制workspace重写；
7. 哪个精确method/backend/mode/topology route可单独关闭Graph Gate。

在上述问题和对应NPU证据关闭前：

```text
P5 LOCAL IMPLEMENTATION: PASS
P5 SOURCE SPY: PASS (CPU/static expected-binding observation only)
GRAPH WINDOW ON: STILL FAIL-CLOSED
P6 PRODUCTION ENABLEMENT: BLOCKED
```

## 12. Developer reading order

1. `draft_window.py`：P2/P3 FullSource、generation、workspace、lease。
2. `draft_window_graph.py`：P5 identity/backing/provider/source event。
3. `draft_window_eager.py::_validated_draft_attention_read_inputs()`：P4a/P5 live boundary。
4. `draft_window_eagle3.py::_validated_eagle3_read_inputs()`：P4b/P5 live boundary。
5. `autoregressive/aclgraph.py::capture/run_fullgraph()`：Eagle3 graph source timeline。
6. `dflash/aclgraph.py::capture/run_fullgraph()`：DFlash/DSpark timeline。
7. `attention_v1.py::update_graph_params/full_graph_fia()`：backend task binding/consumer。
8. `test_draft_window_graph_binding.py`：executable contract and current source order。

## 13. Mental model

1. P5不改变Window数学或source。
2. P3 workspace仍是唯一backing owner。
3. 地址稳定不等于generation新鲜；epoch和identity仍必需。
4. Provider属于一个speculator实例，不是global registry。
5. Descriptor只有Draft read state，没有write/Target state。
6. Observer缺省为空，不记录日志。
7. Eagle3 first-pass和AR-step是不同route。
8. DFlash与DSpark共享manager但不共享method identity。
9. 当前真实graph顺序是replay/consumer后update。
10. P5提供证据工具，不提供Graph Window support。

# Independent Review Resolution

## Review metadata

| Item | Value |
|---|---|
| Independent review | P5_DeepSeek_Independent_Review.md |
| Adjudication date | 2026-10-13（Asia/Shanghai） |
| Original P5 commit | 266eec5d6a7bd391d6287937ebc03b2289b5618f |
| Review-fix commit | 0702c89d2aa41d47ae2379fc6de883140277fbef |
| Review-final tree | 2b8fecda15ca57c0062bbfe5eec62ecd0a4c99ac |
| Repository boundary | vLLM-Ascend only；vLLM保持84030bbe3d74d99bad477a3d2e37a973ccd8865c且clean |

裁决共5项：ACCEPTED=2、PARTIALLY_ACCEPTED=3、REJECTED=0、
INSUFFICIENT_EVIDENCE=0。没有Architecture Escalation。

## Resolution table

| ID | Severity | Reviewer finding | Resolution | Evidence | Code action |
|---|---|---|---|---|---|
| M-01 | Major | replay侧build_draft_attn_metadatas()到update_full_graph_params()仍消费baseline/Target-derived metadata；P5 event未证明Window carrier进入Graph consumer | **PARTIALLY_ACCEPTED** | 当前AR manager在autoregressive/aclgraph.py::run_fullgraph()先调用build_draft_attn_metadatas()；AR实现从model_state.attn_metadata过滤，DFlash/DSpark也无Window graph分支。全仓只有测试安装P5 provider，Graph Window user Gate仍在draft_window.py拒绝，所以“尚未接线/尚未观测真实carrier”属实；但在P5接线会越过“不开放Graph/不进入P6”的phase boundary | 不接Graph carrier。收紧draft_window_graph.py模块/event/枚举docstring，明确event只是expected-binding observation，不是metadata/operator consumption证明；将显式carrier injection、Target isolation与无carrier时hard fail写成P6第一交付 |
| m-01 | Minor | bind后canonical FullSource tensor被同owner换绑，observe()未检测 | **ACCEPTED** | 新回归在review前代码得到“Failed: DID NOT RAISE RuntimeError”；FullDraftKVSource.validate_owner_bindings()已有正确owner-object检查，但P5未调用 | 在bind()和每次observe()调用validate_owner_bindings()；新增bind/observe两条换绑回归 |
| m-02 | Minor | consumer_kind/metadata_owner由caller声明，未绑定真实backend identity | **PARTIALLY_ACCEPTED** | 字段确为声明式typed vocabulary；_validate_expectation()只能证明前后声明一致，不能证明真实backend行为。Notes原本已明确“不据此批准backend”，且P5没有production installer/caller，当前也没有可诚实绑定的Window Graph backend consumer | 不在P5增加另一个caller可伪造的backend字段。docstring明确“expected future classification”；P6必须在真实UPDATE点从当前backend/builder派生并校验backend identity |
| Q-01 | Question | generation-scoped binding不能表达startup capture identity | **PARTIALLY_ACCEPTED** | 实际startup capture发生在request/generation之前；当前bind/observe要求active P3 generation，所以事实限制成立。Graph Gate关闭且provider没有production caller，因此该限制不会被误用；单独的capture-scope dataclass仍可增量加入，现有类型没有锁死架构 | P5不发明未经runtime证据批准的capture identity。P6 design入口必须先由owner决定独立CaptureIdentity及其与per-generation content update/lease的关系 |
| Q-02 | Question | P5 SOURCE SPY: PASS只能表示CPU/static Python observation，不表示真实NPU operand/address | **ACCEPTED** | manager测试monkeypatch upstream capture/replay；未执行NPU capture、operator address或physical read-set oracle | 无行为修改；代码docstring与本节固定证据边界，最终状态明确保留NPU/Graph Gate |

Review中的mixed prefill/decode补充不是P5 finding。它仍由既有G-MIXED跟踪，
P5没有修改scheduler/admission或该fail-closed行为。

## Red-to-green evidence

1. 先加入test_observe_rejects_canonical_full_source_table_rebinding。
2. review前实现可复现失败：“Failed: DID NOT RAISE RuntimeError”。
3. 再在DraftWindowGraphBindingProvider.bind/observe加入canonical owner-binding复查。
4. 补充bind前换绑回归，最终两项均通过：2 passed。
5. P5 targeted最终为37 passed。

原测试只验证“P3 workspace不alias canonical storage”和workspace地址稳定，没有在bind后
替换canonical owner tensor，因此漏掉了“owner对象不变、成员tensor换绑”这一状态转换。

## Final diff

| File | Review-fix |
|---|---|
| vllm_ascend/worker/v2/spec_decode/draft_window_graph.py | bind/observe复查canonical owner bindings；收紧observation/consumer证据语义 |
| tests/ut/spec_decode/test_draft_window_graph_binding.py | 新增bind前与bind后canonical table换绑回归 |

没有修改vLLM，没有新增Graph carrier injection，没有改变Graph mode Gate。

## Final tests

| Command/scope | Result | Limitation |
|---|---|---|
| P5 targeted | 37 passed | CPU/static；非真实ACL Graph/NPU |
| P5 + DSpark/Eagle graph host tests | 55 passed | Python source points；upstream capture/replay被host stub |
| P1–P5 + graph contracts + DFlash2 + DSpark + attn utils + attention_v1 | 403 passed, 2 subtests passed | host-only |
| BlockTables regressions | 14 passed, 21 subtests passed | host-only |
| full tests/ut/spec_decode | 509 passed, 13 skipped, 7 failed, 2 subtests passed | 7项仍是既有VWN host backend “Invalid attention backend for None”；不是PASS |
| Ruff check | PASS | review-fix两文件 |
| Ruff format check | PASS | review-fix两文件 |
| targeted Mypy（repository flags） | PASS | 5个P5 production files |
| compileall | PASS | spec_decode + P5 test |
| git diff --check | PASS | commit前无whitespace error |
| 可执行pre-commit hooks | PASS | Ruff/codespell/typos/filename/init/logger/import/boolean/long-function/symbolic-meta |
| actionlint | ENVIRONMENT BLOCKED | Go dependencies从proxy.golang.org下载超时；不是PASS |
| gitleaks | ENVIRONMENT BLOCKED | 本机无gitleaks且hook所需wget不存在；不是PASS |

## Final invariant audit

| Invariant | Final |
|---|---|
| Ascend-only / vLLM exact baseline | PASS |
| CONFIG_OFF/FORCED_OFF zero P5 state | PASS |
| OFF graph dispatch exact no-op | PASS |
| instance-owned provider / no global / no ContextVar | PASS |
| stable P3 backing / no temporary clone | PASS |
| canonical FullSource no alias | PASS |
| canonical owner replacement detected at bind and observe | PASS |
| generation/mapping/request/gid/route/phase/step/lane mismatch | hard fail |
| Target/write/slot/positions untouched | PASS |
| source event proves actual metadata/operator consumption | **NO — explicitly outside P5 evidence** |
| backend classification proves backend implementation | **NO — typed expectation only** |
| startup capture identity implemented | **NO — P6 design prerequisite** |
| Graph Window ON | **STILL FAIL-CLOSED** |

## Exact P6 entry seam

P6可以进入design/source-spike，但production Graph enablement仍BLOCKED。第一批交付必须按顺序：

1. 定义独立capture-scope identity，不能拿request generation_id/mapping_epoch冒充startup capture；
2. 在Ascend-owned AR/DFlash/DSpark replay metadata路径建立显式Window read-carrier injection；
3. provider存在而carrier仍为baseline/Target-derived时必须hard fail，禁止静默继续；
4. Window Graph metadata必须Draft-private，并重新证明Target/write/slot/positions isolation；
5. 在真实update_full_graph_params入口从当前backend/builder派生backend identity，不采信caller枚举作为证明；
6. 说明upstream capture dummy metadata在R-REPO-01下不可由Ascend直接观测，设计可验证替代source point；
7. 用NPU address、update生效边界、physical read-set、stream/lifetime oracle关闭精确route Gate。

最终冻结状态：

    P5 STATIC FINAL: PASS
    P5 NPU GRAPH: NOT VERIFIED
    GRAPH WINDOW ON: STILL FAIL-CLOSED
    P6 DESIGN ENTRY: READY
    P6 PRODUCTION GRAPH ENABLEMENT: BLOCKED
