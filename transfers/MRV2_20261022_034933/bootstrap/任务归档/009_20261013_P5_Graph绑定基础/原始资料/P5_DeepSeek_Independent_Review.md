# MRV2 Draft Window P5 — DeepSeek Independent Review

> Reviewer: independent (non-implementer). 仅基于真实 source / commit / 测试执行得出结论。
> 不修改任何 production 代码。
> 日期：2026-10-13。时区：Asia/Shanghai。

## 0. Review object 与可复现事实

| 项 | 独立核实结果 |
|---|---|
| vLLM 仓库 | `/Users/wenqingzhang/Desktop/vllm/vllm` |
| vLLM HEAD | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` ✔ 与要求一致 |
| vLLM `git status --porcelain` | 空（clean） ✔ |
| vLLM-Ascend parent（P4 Final） | `1011e2c2fa99729a46efde5b5bbaf6daed975a2c`，tree `7d165d585755766e7493e02f0281598e4aca3602` |
| P5 commit | `266eec5d6a7bd391d6287937ebc03b2289b5618f`，tree `dd8bee7c63b250639345bea4aa5560ef176bda2c` ✔ 与 Notes/Plan 一致 |
| P5 branch | `feature/p5-ascend-graph-binding-foundation` |
| P5 diff | `git diff 1011e2c 266eec5 --stat` = **7 files, +1333 / −0** |
| vLLM-Ascend `git status --porcelain` | 空（clean） ✔ |

`git diff --name-only 1011e2c 266eec5`（全部在 vllm-ascend，**无任何 vLLM 路径**）：

```text
vllm_ascend/worker/v2/spec_decode/draft_window_graph.py          (new, 473 行)
vllm_ascend/worker/v2/spec_decode/draft_window_eager.py          (+5)
vllm_ascend/worker/v2/spec_decode/draft_window_eagle3.py         (+5)
vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py     (+28)
vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py             (+24)
tests/ut/spec_decode/test_draft_window_graph_binding.py          (new, 795 行)
tests/ut/spec_decode/test_draft_window.py                        (+3)
```

## 1. Repository

| 问题 | 独立结论 | 证据 |
|---|---|---|
| 有没有 vLLM 修改？ | **没有** | 上方 name-only 列表无 vLLM 路径；vLLM HEAD 与要求一致且 clean |
| 有没有 private API 依赖？ | **没有** | `draft_window_graph.py` 只 import P3 本体（`draft_window.py`）与 `torch`；未见 prototype 符号（`DraftAttentionReadInputs`、`_call_draft_attn_metadata_builder`、`read_inputs=`） |
| 有没有 site-packages hack？ | **没有** | `grep -rn "site-packages\|sys.path\|importlib.reload" draft_window_graph.py` → none |
| 有没有 module global / ContextVar？ | **没有** | 模块内无 module-level mutable state；唯一 `global` 命中是诊断字符串 `"global gid"`（`:412`）。provider 是 **instance attribute** `_draft_window_graph_binding_provider`（`:448,458,467`） |
| 有没有 shared Target owner mutation？ | **没有** | `bind`/`observe` 只读（`_tensor_identity` 读 data_ptr/shape/stride/dtype/device；无写、无 copy、无 `.cpu()`、无 reduction）；descriptor 不含 slot/positions/Target 字段（`:123-137`） |

附加：`observe_draft_window_graph_source()` 在 provider 不存在时是**严格 no-op**（`:462-473`，`getattr(...) is None → return None`），且 **install 无 production caller**（全仓检索仅测试文件调用），因此 5 个观测点在生产环境等价于零行为变化。

## 2. Source correctness（live / capture / replay 是否真是当前 checkout）

我逐点对照了真实 source（不只读 Notes）：

| 声明 | 独立核实 | 证据 |
|---|---|---|
| AR replay 顺序 = `REPLAY → CONSUMER → UPDATE` | **成立** | `autoregressive/aclgraph.py:159`（REPLAY 在 `super().run_fullgraph(desc)` 前）、`:161`（CONSUMER 在后）、`:197`（UPDATE 在 `update_full_graph_params(...)` 前）。测试 `test_eagle3_manager_replay_update_consumer_order` 断言该 stage 序列（`test_draft_window_graph_binding.py:768-772`） |
| DFlash/DSpark replay 顺序同上 | **成立** | `dflash/aclgraph.py:102/105/128`；测试 `:693-697` |
| AR capture 两个分支（first-pass / AR merge）都发 `CAPTURE→CONSUMER` | **成立** | `autoregressive/aclgraph.py:89`(CAPTURE)、`:104`(first-pass CONSUMER)、`:138`(generic CONSUMER)；测试参数化覆盖 `is_draft_model_prefill` True/False（`:570-625`） |
| 未沿用旧 `enable_enpu` 时序假设 | **成立** | Notes SD-P5-01；(P3/P4 阶段已独立确认 `enable_enpu` 只影响 replay 前同步、不改变 update/replay 次序) |
| 是否遗漏实际 `update_full_graph_params` 入口 | **没有遗漏** | UPDATE 观测点就插在 `update_full_graph_params(...)` 调用前（两个 manager 各一处） |
| LIVE 观测是否覆盖真实消费边界 | **成立** | 插在 P4a/P4b 唯一 validation boundary 内（`draft_window_eager.py:369`、`draft_window_eagle3.py:383`，均在 `inputs.validate_for(...)` 之后）；测试直接调用真实 `_validated_draft_attention_read_inputs` / `_validated_eagle3_read_inputs`（`:398-409`） |
| 观测点是"日志模拟"还是真实调用链 | **真实调用链** | manager 级测试用 `__new__` 构造真实 `DFlashAclGraphManager` / `AutoRegressiveAclGraphManager`，仅 monkeypatch **上游** `super().capture/run_fullgraph` 与 context manager（`:557-561`、`:614-619`、`:680-689`、`:754-764`），观测点本身走真实 Ascend 代码 |

## 3. Ownership

| 问题 | 独立结论 | 证据 |
|---|---|---|
| Graph backing 真正归谁？ | **P3 `DraftWindowWorkspace`**（speculator 实例所有），P5 provider **不拥有 tensor** | `DraftWindowGraphBindingProvider.__init__` 只持有 `runtime_state`（`:254-256`）；descriptor 直接引用 `workspace.window_block_table` 等（`:349-353`） |
| capture 绑定地址是否稳定？是否 temporary/clone？ | **稳定且非 clone** | descriptor 持有 workspace 本体的 5 个 tensor（无 slice/clone）；`_workspace_backing_identity` 记录 identity-address（`:206-217`）；`observe` 每次比对当前地址/几何（`:377-379`）；测试 `test_backing_address_is_stable_while_contents_and_generation_change` 断言跨 generation `backing_identity` 相同而内容不同（`:448-451`） |
| replay 是否可能指向过期 storage？ | **无法静默指向过期 generation** | `observe` 先 `inputs.validate_for`（lease 必须 current），再比对 generation_id / mapping_epoch（`:372-376`），并在 lease 已 RETIRED 时抛错；`bind` 拒绝覆盖仍 active 的绑定（`:281-282`）；测试 `test_retired_or_stale_generation_cannot_be_observed`（`:480`） |
| 是否 per-call 新建 backing？ | **否** | `bind` 不创建 tensor ✓（`:280` docstring 明示 "without allocating or cloning tensors"） |
| 是否与 canonical FullSource alias？ | **不 alias，且硬拒绝** | `_shares_storage` 检查 5 个 graph tensor × (canonical tables + gpu counts + cpu counts)（`:312-317`）；测试断言 storage_data_ptr 不同（`:453-455`） |

## 4. Identity（字段是否被真正"消费"）

`DraftWindowGraphBindingIdentity`（`:92-110`）携带 15 字段。**全部被消费**，不是仅存在字段名：

- `_validate_expectation`（`:400-434`）逐字段比较 15 个 identity 字段 + consumer_kind + metadata_owner + backing_identity（任一不一致 → `RuntimeError`）；
- `observe` 额外比对 `generation_id`、`mapping_epoch`（`:373-376`）与 backing identity（`:377-379`）；
- `_validate_route`（`:226-240`）把 `method`/`phase`/`step` 与 route 强绑定（Eagle3 first-pass 必须 `PROPOSAL/step==0`；AR step 必须 `STEP/step>0`）；
- 参数化负例测试 `test_expected_identity_mismatch_fails_closed`（`:256-287`）与 `test_expected_transport_mismatch_fails_closed`（`:289-316`）覆盖各字段。

覆盖清单核对：generation ✔ / mapping_epoch ✔ / request fingerprint ✔ / gid ✔ / phase ✔ / step ✔ / lane ✔ / route ✔（method+route 双列）。**无 "存在但未消费" 的字段。**

## 5. Target / write

| 风险 | 独立结论 |
|---|---|
| 写 Target store | **否**。P5 无任何对 `model_state.attn_metadata` 的写入；descriptor 不含 Target 字段 |
| 写 canonical FullSource | **否**。`bind`/`observe` 只读；唯一 action 是 `_shares_storage` 拒绝 alias |
| 改 slot mapping / positions | **否**。descriptor 字段集只有 window table + 3 个 length + valid counts；无 slot/positions/query |
| alias Target metadata | **否**。descriptor 引用的是 P3 workspace（Draft-only）；测试 `test_binding_is_immutable_and_has_no_target_or_write_side_fields`（`:238-253`） |

## 6. OFF

| 要求 | 独立结论 | 证据 |
|---|---|---|
| Window OFF：zero allocation | **成立** | CONFIG_OFF/FORCED_OFF 不创建 P3 runtime → `install_*` 直接 RuntimeError 且不留 attribute（`:451-453`；测试 `:523-527`）；`test_draft_window.py:396/442/1904` 断言 baseline/owner 无 `_draft_window_graph_binding_provider` |
| Window OFF：zero graph descriptor | **成立** | 无 provider → `observe` no-op（`:467-469`）；测试 `test_graph_manager_without_provider_is_an_exact_observation_noop`（`:628-645`）对真实 manager 断言 |
| Window OFF：exact baseline dispatch | **成立** | 观测调用点均为纯函数式 no-op，不改变参数、不改变分支；`tests/ut/spec_decode` 全量 `507 passed`（见 §9） |

## 7. Source spy 的能力边界

可区分 **LIVE / CAPTURE / REPLAY / UPDATE / CONSUMER** ✔（`test_spy_distinguishes_...:318-345` 断言 5 个 stage 的 stage/sequence/identity/backing/fingerprint 全部正确），且 manager 级测试证明这些 stage 由**真实 manager 代码路径**产生，不是日志模拟 ✔。

但必须明确记录两项**未被观测**的入口（见 M-01）：

1. **capture-time dummy metadata**（上游 `dflash/cudagraph.py` / `cudagraph_utils.prepare_inputs_to_capture`）：不属 Ascend 代码，P5 未观测（在 R-REPO-01 下也观测不到）。
2. **replay-time metadata rebuild**（Ascend 自有 `build_draft_attn_metadatas`）：这是 graph 路径把 read carrier 交给 `update_full_graph_params(draft_attn_metadatas=...)` 的**唯一通道**，P5 未插观测点。

## 8. Scope / Gate

| 问题 | 独立结论 |
|---|---|
| Graph user Gate 是否仍 fail closed？ | **仍是**。P5 未触碰 `draft_window.py`；P2 gate 仍在（`:878-880` `graph_mode != "NONE"` → failure）；测试 `test_graph_window_user_gate_remains_fail_closed`（`:776-795`）断言 `FULL` 恰好返回那条 Graph 拒绝；P4a/P4b 的 live eager guard（`cudagraph_runtime_mode != CUDAGraphMode.NONE` → raise）仍在（`autoregressive/speculator.py:461,512,548`） |
| 是否已打开 Graph user Gate？ | **没有**（因此不触发 Critical） |
| Notes/Plan 是否把 Graph 写成已支持？ | **没有**。Notes §0/§9/§11 与 Plan §31.6/§31.7 均写 `GRAPH WINDOW ON: STILL FAIL-CLOSED`、`P6: BLOCKED`、`NPU capture/replay address oracle: OPEN`、`L5: OPEN` ✔ 与事实一致 |

## 9. 独立测试执行（NOT RUN 均如实记录）

环境：`VLLM_VERSION=0.29.0`，`PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm`（**未修改的原版 vLLM checkout**），
`/Users/wenqingzhang/Desktop/vllm/vllm-ascend/.venv/bin/python -m pytest -q`。

| Scope | 我的结果 | 与 Notes 对比 |
|---|---|---|
| P5 targeted `test_draft_window_graph_binding.py` | **35 passed, 1 warning** | 一致 ✔ |
| full `tests/ut/spec_decode` | **507 passed, 13 skipped, 7 failed, 2 subtests passed** | 一致 ✔ |
| P1–P5 combo（draft_window / runtime / eager / eagle3 / graph_binding / dflash2 / dspark） | **297 passed** | 组合范围不同，不计入对比 |
| attention_v1 + attn_utils_v2 + v2_block_table | **94 passed, 2 subtests** | — |
| P1–P5 + attention_v1 + attn_utils_v2（= Notes 的 383 名单去掉 v2_block_table） | **383 passed**（由 297+86 推得，逐项复算一致） | 一致 ✔ |

7 个失败全部为 `tests/ut/spec_decode/test_speculators_vwn_eagle3.py` 的 `ValueError: Invalid attention backend for None`（host 无 Ascend backend），与 P4 冻结报告同组，栈不经过 P5 文件。**不作为 PASS。**

| 未执行项 | 状态 |
|---|---|
| NPU capture/replay address oracle | **NOT RUN**（本机无 NPU） |
| ACL graph 真实 capture/replay（非 monkeypatch 上游 super） | **NOT RUN**（CPU 不可执行） |
| L5 physical read-set / profiler | **NOT RUN** |
| Ruff / format / mypy / compileall | **NOT RUN by me**（不复制 Codex 结论；见 §11 结论措辞限制） |
| actionlint / gitleaks | **NOT RUN**（Notes 亦记为 environment-blocked） |

## 10. Findings

### M-01 — replay 侧 read-carrier 通道既未接线也未观测，P5 的 REPLAY/CONSUMER/UPDATE 观测点不覆盖真正决定 attention operand 的路径

- **ID**: M-01
- **Severity**: **Major**
- **Claim**: P5 声称建立了 graph binding foundation，可追踪 "which stable P3 backing is seen by live execution, graph capture, replay, graph-task update, and the eventual attention consumer"（`draft_window_graph.py:3-13`；Plan §31.3；Notes §1.4/§1.5）。
- **Exact file/line**:
  - `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:153`（`draft_attn_metadatas = self.speculator.build_draft_attn_metadatas(...)`）、`:197`（`update_full_graph_params(..., draft_attn_metadatas=...)`）
  - `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py`（`build_draft_attn_metadatas`，其函数体首行 `attn_metadata = self.model_state.attn_metadata`，随后按 `draft_attn_layer_names` 过滤）
  - `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:97`
- **Observed behaviour**: Ascend 的 `build_draft_attn_metadatas()` **没有任何 window 分支**：它直接过滤 **Target store**（`model_state.attn_metadata`）并用 `_update_decode_attn_metadata` 生成 per-step metadata，然后交给 `update_full_graph_params(draft_attn_metadatas=...)` 做 graph-task rebind。因此 graph 路径上真正决定 attention operand 的 read carrier **仍然来自 Target store**，P5 的 provider/descriptor/backing 在该路径上**没有任何消费点**（provider 只被 observe，不被消费）；同时 P5 未在该通道插入任何 stage（无 REPLAY_METADATA/REBUILD 观测）。capture 侧同理：`prepare_inputs_to_capture`/`dflash/cudagraph.py` 的 dummy 表不在 Ascend 代码内，P5 也无法观测（R-REPO-01 限制，Notes 未明确写出这一点）。
- **Why it violates Design/Plan**: Final Design 的核心不变量要求 Window ON 的 Draft metadata 必须独立构建、不得由 Target store 过滤得到（R-02 污染通道）；Plan 的 C6 条目要求 "upstream DFlash/generic AR optional capture provider/sink" + "Target sink isolation" + "三入口 spy"。P5 交付了 identity/spy/seam，但**三个 metadata 入口中只有 live 入口被覆盖**，replay 入口（Ascend 自有、可覆盖）既未接线也未观测；Plan §31.2 把 "historical upstream `DraftCaptureBindingProvider`/generic sink 路线不再实现" 记为 scope 变更，但未说明"replay 侧读取通道改由 P6 新建"这一后果。
- **How to reproduce**:
  ```bash
  grep -n "_eagle3_window_is_active\|draft_window" \
      vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py \
    | sed -n '1,40p'      # build_draft_attn_metadatas 内无 window 分支
  grep -n "build_draft_attn_metadatas\|update_full_graph_params" \
      vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py
  ```
  （亦可对 graph 路径做 call-graph 追踪：`run_fullgraph` → `build_draft_attn_metadatas` → 过滤 `model_state.attn_metadata`。）
- **Required correction**: 二选一并落到 Plan/Notes：
  1. 在 Ascend `build_draft_attn_metadatas()`（AR/DFlash/DSpark）与 `update_full_graph_params` 调用点各加一个显式 source point（例如 `DraftWindowGraphStage.REPLAY_METADATA` 或在现有 `UPDATE` 前记录 `draft_attn_metadatas` 来源 identity），使 graph read-carrier 通道可被 spy 区分；并让该通道的 window 分支在 provider 存在时**显式 fail closed**（当前是"静默走 Target 过滤"，而不是"拒绝"）；或
  2. 明确把 "graph replay read-carrier 注入点" 列为 P6 的第一项交付，并在 §11 P6 prerequisites 中加一条对应验收（含 "capture dummy metadata 由上游产生、Ascend 无法观测" 这条限制的显式记录）。
- **Architecture escalation needed?** **否**（在既有 Ascend manager 内新增观测/拒绝分支即可，不改变 Frozen 架构）；但需要 owner 确认 P6 范围显式包含该注入点。

### m-01 — graph binding identity 不含 canonical source tensor pointers，`observe` 不复查 canonical owner binding

- **ID**: m-01
- **Severity**: **Minor**
- **Claim**: Notes §4 称 "任何 ... backing identity 不一致都 hard fail"，§5 列出 7 项 observation 复查。
- **Exact file/line**: `draft_window_graph.py:107`（`source_owner_id` 只取 `generation.source_identity.block_tables_owner_id`）；`:359-398`（`observe` 只比对 backing identity 与 `inputs.validate_for`）
- **Observed behaviour**: `DraftWindowSourceIdentity` 里的 `input_block_table_ptrs` / `persistent_num_blocks_ptr` **未进入** `DraftWindowGraphBindingIdentity`；`observe` 也不调用 `FullDraftKVSource.validate_owner_bindings()`。因此在 bind 之后若 canonical `input_block_tables[gid]` 被**同 owner 内的新 tensor 替换**（object id 不变、tensor 换对象），graph observation 不会察觉；`bind` 时的 alias 检查读的是替换后的 tensor，也不构成"变化检测"。
- **Why it matters**: descriptor 的权威性声明包含 "backing must not alias canonical FullSource"（`:312-317`）。该性质在 bind 时被验证，但在后续 CAPTURE/REPLAY/UPDATE/CONSUMER 时不再复查；eager 路径每步都会 `validate_owner_bindings()`（P2/P3 契约），graph 观测面缺了这一层。
- **How to reproduce**: 在 `test_draft_window_graph_binding.py` 的 `_runtime_fixture` 之后执行
  `block_tables.input_block_tables[0] = torch.zeros_like(block_tables.input_block_tables[0])`，
  再 `provider.observe(stage, expected=descriptor.expectation)` → 当前**不会**报错（而 eager 的 `provider.describe()` / `gather_valid_num_blocks_cpu` 会报 "canonical input block table 0 was replaced"）。
- **Required correction**: 在 `DraftWindowGraphBindingIdentity` 中增加 canonical pointer 集合（`input_block_table_ptrs`、`persistent_num_blocks_ptr`），或在 `observe` 中调用 `full_source.validate_owner_bindings()`。
- **Architecture escalation needed?** 否。

### m-02 — `consumer_kind` / `metadata_owner` 为声明式枚举，未与真实 backend 实例绑定

- **ID**: m-02
- **Severity**: **Minor**
- **Claim**: Notes §1.7 建立 `DIRECT_CAPTURED / TASK_REBOUND / BACKEND_DERIVED` 三分类，并说 "P5 只建立三类 typed vocabulary 和 source trace；不据此自动批准任何 backend"（诚实）。
- **Exact file/line**: `draft_window_graph.py:277-288`（`bind(..., consumer_kind=..., metadata_owner=...)` 由 caller 直接传入）；`:429-432`（只比较枚举相等）
- **Observed behaviour**: 分类既不来自 backend class、也不与实际 `update_graph_params()` 行为关联；binding identity 中**没有 backend 身份字段**。任何 caller 都可以为任意 backend 声明 `TASK_REBOUND`。测试中的 provider 也全部使用同一个 `TASK_REBOUND` 常量（`:189, 394, 547, 603, 667, 742`）。
- **Why it matters**: P6 报告若引用 `consumer_kind` 作为"该 backend 通过 graph-task rebind 消费"的证据，则该证据不可归因（无 backend identity、无断言）。Notes 的措辞已避免过度声明，但接口本身缺少归因字段。
- **Required correction**: 在 `bind` 时记录 `backend_impl_class` / `builder_class`（可从 `speculator.attn_backends` 或 P2 inventory 取），并在 UPDATE 观测点断言与当前 `update_full_graph_params` 使用的 backend 一致。
- **Architecture escalation needed?** 否。

### Q-01 — binding 是 generation-scoped，而 graph capture 是 generation-agnostic；foundation 尚不能表达 capture-time identity

- **Severity**: **Question / insufficient evidence（需 P6 决策，Notes 已列为 open question #1）**
- **Exact file/line**: `draft_window_graph.py:281-282`（`bind` 要求上一绑定已 RETIRED）、`:290-298`（要求 `workspace.bound_identity == generation`、lease current）、`:372`（`observe` 要求 lease 仍 current）
- **Observed behaviour**: 任何 observation 都要求"当前存在 active 且未 retire 的 generation"。而 graph capture 发生在 startup（尚无 request/epoch），replay 跨多个 generation。因此**"capture 时绑定、跨 generation replay"这一 graph 的核心语义当前无法表达**：capture 时无处 `bind`；一旦 generation retire，旧 descriptor 的所有 observation 都抛错（这是正确的 fail-closed，但意味着 P6 必须引入 capture-scoped identity，而不是复用 proposal generation）。
- **Why it matters**: 这是 P6 是否能安全打开 Gate 的核心，而 P5 的 foundation 没有为它留出 typed 扩展点（只有 15 字段的 proposal-generation identity）。
- **Required correction**: 在 P6 design 中显式引入 capture-scope identity（例如 `CaptureIdentity` + "capture 绑定 → 每 generation 内容更新"的 lease 关系），或明确 P5 契约只覆盖 per-generation 观测、capture 语义由 P6 从零定义（并给出对应 NPU 证据要求）。
- **Architecture escalation needed?** **是（一层）**：需要 owner 决定 capture-scope identity 是否进入 P6 的最小交付，否则 P6 只能停留在"记录而不可消费"。

### Q-02 — "P5 SOURCE SPY: PASS" 的确切含义

- **Severity**: **Question（措辞边界，非缺陷）**
- P5 的 spy 证据全部是 **CPU/static integration test**：manager 级测试 monkeypatch 了上游 `super().capture()` / `super().run_fullgraph()`，因此证明的是 **Python 观测点与 stage 顺序**，不证明 capture 时 operator 真实绑定的地址、也不证明 replay 实际使用的 address。Notes/Plan 的措辞（`CPU/static spy`、§10 的 7 项缺失 NPU 证据）与此一致 ✔；本节仅固定该措辞边界，供 P6 引用时避免外推。

### 补充（非 P5 缺陷，供 owner 追踪）：mixed prefill/decode 仍是 service-wide abort

- P4b review 中我提的"pure-prefill 导致 abort"已在 `1011e2c` 修复（classifier 改为对**任意 pure-prefill** batch 走 baseline bypass，`_requires_prefill_baseline_bypass`）。
- 但**mixed prefill/decode** 仍 `NotImplementedError`；`P0_P4_Final_Gate_Status.csv` 已将其记为 `G-MIXED: OBSERVED_ABORT … leads EngineDeadError and service stop`，next action "Support mixed or reject before admission"，状态 `BLOCKED` ✔ 已被记录，且 `P5_P8_Entry_Baseline.md` §6/§11 要求 P5 不得忽略该产品风险 ✔ P5 未触碰该路径 ✔。此项属 owner 范围决定（Option A/B），不是 P5 finding。

## 11. 结论（不得由我扩大的表述）

**P5 事实上满足的**：在 R-REPO-01 与 P5–P8 Entry Baseline §5 定义的"foundation"范围内（identity 协议 + instance-scoped provider + source spy + 只读 backing 复用 + fail-closed 保持），P5 **成立**：

- 无 vLLM 修改、无私有 API、无 site-packages hack、无 global/ContextVar、无 shared-owner/Target mutation；
- 观测点是真实 Ascend manager / 真实 validation boundary 的调用点，5 个 stage 可区分；
- backing 是 P3 workspace 本体（非 clone、地址稳定、内容 generation-scoped），且不 alias canonical FullSource；
- identity 15 字段**全部被消费**；stale / mismatch / active-overwrite 全部 hard fail；
- OFF 路径零 allocation、零 descriptor、exact baseline；
- Graph user Gate **仍未打开**（无 Critical 触发条件）。

**P5 不满足的（本 Review 的核心保留）**：作为 "Graph **Binding** Foundation"，它**尚未在 graph 路径上建立 read-carrier 的消费/观测点**（M-01），因此目前交付的是"binding 的**身份与记录**"，而不是"binding 的**通路**"；capture-scope 语义缺 typed 扩展点（Q-01）。

## 12. 必须回答的四个问题

1. **P5 是否事实满足 Graph Binding Foundation？**
   **部分满足。** 满足 "identity + instance seam + source spy + 只读 backing 契约 + Gate 保持"；**不满足** "graph 路径上的 read-carrier 通路与观测"（M-01）与 "capture-scope 语义表达"（Q-01）。按 Plan §31.3 / Notes §1 的自我定义它是 foundation 而非 enablement，此点如实；但按 Plan §C6 的原始条目（capture provider/sink + Target sink isolation + 三入口 spy），P5 只覆盖了 live 入口。
2. **是否存在 Critical？** **否。** 未发现 vLLM 修改、私有依赖、site-packages hack、global/ContextVar、shared Target owner mutation、capture backing 不稳定、replay 静默使用 stale generation、或 Graph Gate 被提前打开。
3. **Graph user Gate 是否被打开？** **没有被打开。** 保持 fail-closed（source gate + 测试断言 + 未移除任何 FULL/FULL_DECODE_ONLY/PIECEWISE Gate）。
4. **是否可进入 P6？** **可以进入 P6 design，但必须在 P6 计划中先写入 M-01 与 Q-01 的交付项**（graph replay read-carrier 注入点 + capture-scope identity + Target-sink isolation for the graph path），否则 P6 会在"有 identity 无通路"的基础上做 enablement 决策。

---

## P5 REVIEW VERDICT

```
APPROVE WITH REQUIRED FIXES
```

> Required fixes 为 **M-01**（graph replay read-carrier 通道的显式注入/观测点与 fail-closed 语义）与 **Q-01** 的书面化（capture-scope identity 归属 P6，并写入 P6 prerequisites）。
> 在 M-01 书面关闭前，P5 的表述应限定为 "identity/observation foundation"；不得表述为 "graph binding 已具备消费通路"。

## GRAPH USER GATE SHOULD REMAIN

```
FAIL-CLOSED
```
