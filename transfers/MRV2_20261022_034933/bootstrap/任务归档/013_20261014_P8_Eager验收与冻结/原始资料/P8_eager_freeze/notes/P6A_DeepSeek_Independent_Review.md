# P6A Independent Review — Ascend-owned Pre-Capture Seam

- Reviewer: DeepSeek（独立 Reviewer，非 P6A 实现者，未修改任何 production 代码）
- Date: 2026-10-14
- Scope: 独立判定 Codex 在 P6A 中宣称的 Outcome B（“当前源码中没有符合约束的既有 Ascend-owned pre-capture injection seam”）是否成立
- 事实源：真实 checkout 的 source / diff / tree / 本地独立测试。Codex 的 Search Ledger 与 Investigation Notes 仅用于 §5 的“搜索面是否覆盖”核查，不作为事实依据。

## 0. 结论摘要（Mandated Verdicts）

| 判定项 | 结论 |
|---|---|
| `ASCEND-OWNED PRE-CAPTURE SEAM` | **NOT_FOUND_AFTER_REVIEW** |
| `GRAPH FREEZE` | **JUSTIFIED** |
| `P7 EAGER TRACK` | **SAFE TO PROCEED** |

一句话理由：**Codex 的 Outcome B 在操作性层面成立**——当前源码中不存在任何“能改变真正被捕获 Draft read table/length”的既有 Ascend-owned 注入接缝；但 Codex 给出的**首要论据不准确**（见 F-01）：Eagle3 AR decode 的 capture 中，最终 operator 读到的 attention metadata 对象**恰恰是 Ascend 自己构建的**。真正的阻断原因不是“上游把 Ascend 挡在 metadata 之外”，而是“现有能触达该 metadata 的接口只有 module-global 替换（违反 global/owner swap 约束）或 generation-scoped 的 Window 状态（capture 期不存在），要打通必须新建 capture-scoped transport”。该结论不改变 Outcome B，但会影响 Owner 对“技术不可能” vs “本轮未授权”的判断，故必须更正。

Findings：**0 Critical / 1 Major / 3 Minor / 2 Question**。

---

## 1. Baseline 独立验证（VERIFIED）

我自行执行并核对（非引用 Codex 陈述）：

| 项 | 我的实测值 | 与 Codex 声称的一致性 |
|---|---|---|
| vLLM HEAD | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | 一致 |
| vLLM tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` | 一致 |
| vLLM `git status --porcelain` | 空 | 一致（clean / zero diff） |
| vLLM-Ascend HEAD | `7599497ab2694c4cf343f61f82f449980d8bad93` | 一致（P6 Final） |
| P6 Final tree | `b4f7d12bd24b0a7632f9e606b29703a7c96278de` | 一致 |
| vLLM-Ascend `git status --porcelain` | 空 | 一致 |
| P6A branch / production commit | `git log --all --grep=P6A` 为空；现存分支仅 `feature/p6-graph-read-carrier` 等 8 个既有分支 | 一致（无 P6A commit） |

结论：Codex 关于“仓库保持不变、无 P6A production commit”的陈述**全部为真**，可作为本轮裁定的可信前提。

---

## 2. 独立 capture 路径追踪（不使用 Codex Search Ledger 作为事实源）

### 2.1 三条 route 的捕获链（逐条自源码读出）

**(a) Eagle3 first-pass capture**
`AscendAutoRegressiveSpeculator.capture()` → `prefill_cudagraph_manager.capture(self._prefill, self.model_state, self.target_input_buffers, self.block_tables, self.draft_prefill_attn_groups, ...)`
（`vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:400-408`）
→ Ascend `AutoRegressiveAclGraphManager.capture()` 的 `is_draft_model_prefill` 分支直接转交上游
（`vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:95-109`）
→ 上游 `SpeculatorCudaGraphManager.capture` 的 `create_forward_fn` 调 `prepare_inputs_to_capture(...)` 并把返回的 `attn_metadata` **传入** `forward_fn`
（`/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/autoregressive/cudagraph_utils.py:51-69`）
→ `forward_fn` = **Ascend** `_prefill`（`autoregressive/speculator.py:532`），它在 window 分支里用 `_build_eagle3_private_attn_metadata(...)` **整体替换** 传入 metadata 后再调 `super()._prefill`
（`autoregressive/speculator.py:549-583`）。

**(b) Eagle3 AR decode capture**
`autoregressive/speculator.py:417-425` → Ascend 自己的 `create_forward_fn`
（`autoregressive/aclgraph.py:111-136`）：**Ascend manager 自己**调 `prepare_inputs_to_capture(...)` 并**丢弃其返回值**
（`aclgraph.py:119-128`），然后调 `forward_fn` = **Ascend** `_multi_step_decode`
（`aclgraph.py:130-136`；`speculator.py:499`）
→ `_multi_step_decode` 走 `super()._multi_step_decode(...)`
（`speculator.py:530`）→ 上游 `Speculator._multi_step_decode` 在**每个 step 内**调用 `self._build_draft_attn_metadata(...)`
（`/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:511`）→ 动态派发到 **Ascend override** `AscendAutoRegressiveSpeculator._build_draft_attn_metadata`
（`autoregressive/speculator.py:605`）→ 其 baseline 分支在 `build_draft_attn_metadata_factory(...)` 内调用 `super()._build_draft_attn_metadata(...)`，而该上游 builder 调用的 `build_attn_metadata` 已被外层 `build_attn_metadata_wrapper()` 换成 **Ascend 的 `build_attn_metadata`**
（`speculator.py:645-655`；`vllm_ascend/worker/v2/attn_utils.py:1251, 1255-1262`；patch 目标是 `vllm.v1.worker.gpu.spec_decode.speculator` 这一 module 名）。

**(c) DFlash capture**
`DFlashSpeculator.capture()` 传 `self._generate_draft` 给 `DFlashCudaGraphManager.capture`
（`/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:143-158`）
→ Ascend `DFlashAclGraphManager.capture` 直接 `super().capture(...)`
（`vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:65-92`）
→ 上游 `DFlashCudaGraphManager.capture` 调 `_prepare_dflash_inputs_to_capture(...)`，**在上游内部**建 dummy table 与 `build_attn_metadata(..., for_cudagraph_capture=True)`，再把 `attn_metadata` 传给 `forward_fn`
（`/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:24-70, 112-119`）。
我确认 `AscendDFlashSpeculator` **没有** override `capture()` / `_generate_draft` / `_build_draft_attn_metadata`
（`vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:38-554` 的方法清单中不存在这三者）——即 DFlash capture 期 metadata 完全由上游构建，Ascend 无入口。

### 2.2 dummy table / metadata 的创建时刻与拥有者

- dummy 输入在**图外**准备：`CudaGraphManager.capture` 明确要求 “prepare inputs (OUTSIDE graph)”，`create_forward_fn(desc, warmup)` 在图外调用、返回的 lambda 才在图内执行
  （`/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/cudagraph_utils.py:347-360, 393, 412`）。
- dummy table 由 **upstream** 创建：`block_tables.get_dummy_block_tables(num_reqs)` / `get_dummy_slot_mappings(num_tokens)`
  （`cudagraph_utils.py:693, 697`；DFlash 对应 `dflash/cudagraph.py:36-37`）。
- metadata 的**存储槽**是 Target 的 `ModelState` 实例：`prepare_inputs_to_capture` 调 `model_state.prepare_attn(...)`
  （`cudagraph_utils.py:735`），而 speculator 在 `set_attn` 中绑定的是 **Target 的 model_state 实例**
  （`/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/speculator.py:228-248`，其中 `self.model_state = model_state` 在 :235；`vllm/v1/worker/gpu/model_runner.py:699-707` 传入 `self.model_state`）。
  该实例是 Ascend 子类 `AscendModelState`，其 `prepare_attn` 无条件写 `self.attn_metadata` 并返回
  （`vllm_ascend/worker/v2/model_states/default.py:44-121`，写入在 :97、返回在 :120）。
- 因此“谁拥有 metadata”分三种情形：
  - **Eagle3 first-pass**：upstream 构建（用 Draft 侧的 `draft_prefill_attn_groups`），**Ascend `_prefill` 有权整体替换**（`speculator.py:549-583`）。
  - **Eagle3 AR decode**：**Ascend 构建**（`_build_draft_attn_metadata` override + Ascend `build_attn_metadata`），请见 §2.1(b)。
  - **DFlash**：upstream 构建，Ascend 无入口。

### 2.3 实际被捕获的 operand 最终从哪里来

`full_graph_fia` / `full_graph_fia_v2` 在捕获期从 `attn_metadata` 取 operand：
`key, value, block_size, block_table, actual_seq_lengths_kv = self._get_fia_params(key, value, attn_metadata)`
（`vllm_ascend/attention/attention_v1.py:943-947`；v2 进一步 `actual_seq_lengths_kv = attn_metadata.seq_lens`，:1115-1120）。

捕获时该函数同时做两件事：在 `torch.npu.graph_task_group_begin/end` 内记录 FIA 算子
（`attention_v1.py:1085-1112`），并把本次的参数元组（含 `block_table` / `actual_seq_lengths_kv` 的 weak ref）**追加进 `graph_params.attn_params[num_tokens]`**
（`attention_v1.py:1083-1084, 1113-1114`）。
后续 replay 通过 `update_full_graph_params`（`vllm_ascend/compilation/acl_graph.py:304`）更新这些已注册的 graph task 参数。
Draft 侧的参数池在 **capture 之前**注册：`AutoRegressiveAclGraphManager.__init__` 调 `set_draft_graph_params(self.capture_sizes)`（`autoregressive/aclgraph.py:75-79`；`acl_graph.py:350-404`），但该池只含 `workspaces` / `attn_params` / `handles`，**不含任何 read table / length 决策**。

**结论**：capture 期“选定 Draft read table/length”的动作发生在 `attn_metadata` 被送进 `full_graph_fia*` 之前，而该 metadata 的构建者按 route 分别是 Ascend（AR decode）、Ascend 可替换（first-pass）、upstream（DFlash）。这**推翻**了“Ascend 完全无法触达被捕获 operand”的强表述，但**不推翻** Outcome B（见 §3）。

### 2.4 “已经太晚”的时间点

- 对 DFlash：在 `_prepare_dflash_inputs_to_capture` 内 `build_attn_metadata(...)` 返回时（`dflash/cudagraph.py:54-70`），Draft read table 已由 upstream 固定，Ascend 无入口。
- 对 Eagle3 AR decode：在 `AscendAutoRegressiveSpeculator._build_draft_attn_metadata`（`speculator.py:605`）返回时 metadata 已定；但由于该函数**本身就是** Ascend 代码且在图内被调用，判断点不是“太晚”，而是“**没有可用的捕获期状态/读源**”。
- 对 Eagle3 first-pass：`AscendAutoRegressiveSpeculator._prefill`（`speculator.py:532`）内部，window 分支被两道硬闸挡住：`_eagle3_window_is_active()` 为假（capture 期无 P3 generation），且 `cudagraph_runtime_mode != NONE` 直接 `NotImplementedError`（`speculator.py:549-557`）。
- 对应 AR decode 的两道同类硬闸：`speculator.py:464-466`（`_generate_draft`）、`:515-517`（`_multi_step_decode`）、`:617+`（`_build_draft_attn_metadata` 的 window 分支）。

---

## 3. 对 Codex 五条关键事实的独立裁决

| # | Codex 陈述 | 我的核验 | 裁决 |
|---|---|---|---|
| 1 | “Ascend graph manager 只能在 upstream dummy metadata 构建前传递传统 owner 参数。” | **不准确**。AR decode 路径中 `prepare_inputs_to_capture` 由**Ascend manager 自己**调用（`aclgraph.py:119`），随后在图内由 **Ascend** `_build_draft_attn_metadata` 重建每步 metadata（`speculator.py:605` + `attn_utils.py:1251/1259` 的 module-global 替换）。Ascend 不只“传 owner 参数”，它**就是**捕获 operand 的 metadata 构建者。 | **F-01 (Major)** |
| 2 | “Eagle3 first-pass 使用 Target ModelState；直接替换输入会污染 Target metadata。” | **成立**。`set_attn` 绑定 Target 的 `model_state` 实例（`speculator.py:235`、`model_runner.py:703`），`AscendModelState.prepare_attn` 无条件写 `self.attn_metadata`（`model_states/default.py:97`）。 | 成立（措辞上属“反对稻草人”，但事实无误） |
| 3 | “Eagle3 AR capture 中 `prepare_inputs_to_capture()` 的 metadata 返回值没有成为真正的 per-step consumer。” | **成立但结论不完整**。返回值确被丢弃（`aclgraph.py:119-128`）；然而真正的 per-step consumer metadata 由 **Ascend** 构建（见 #1）。“所以此路不可用”的正确理由是“缺捕获期状态 + 硬闸”，不是“返回值被丢弃”。 | **F-01 的同一更正**（Minor 表述） |
| 4 | “`full_graph_fia*` 是 operator 前最后一个 Ascend 控制点，但没有 provider / CaptureIdentity / descriptor / step ordinal 接口；利用它需新建 backend transport，属未授权 B 方案。” | **成立**。签名为 `full_graph_fia(self, query, key, value, attn_metadata, output, layer=None)`（`attention_v1.py:943-947`），无任何 window/provider 形参；operand 全部来自 `attn_metadata`（`_get_fia_params`）。 | 成立 |
| 5 | “`update_full_graph_params` 及 task update 只能作用于 replay/update 侧，不是 pre-capture seam。” | **成立**。该调用只在 `run_fullgraph` 内（`autoregressive/aclgraph.py:218-233`、`dflash/aclgraph.py:142-161`）；`set_draft_graph_params` 虽在 `__init__` 期注册，但只注册 workspace/handle 桶，不含 read 决策（`acl_graph.py:350-404`）。 | 成立 |

---

## 4. §3 十项 VALID_SEAM 判据——逐个候选接缝套用

判据：(1) 位于实际 capture operand 确定之前；(2) 非 observe-only；(3) 非 replay/update-only；(4) 可改变真正捕获的 Draft read table/length；(5) 不改 Target/写侧；(6) 不依赖 vLLM 修改；(7) 无 global/ContextVar/owner swap；(8) instance-scoped；(9) OFF 严格 baseline；(10) 不是把整个 upstream builder 复制进 Ascend。

| 候选接缝 | 位置 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 判定 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `AutoRegressiveAclGraphManager.capture/create_forward_fn` | `autoregressive/aclgraph.py:81-142` | ✓ | ✓ | ✓ | ✗（只能传 `forward_fn/model_state/input_buffers/block_tables/attn_groups`；dummy 由上游造） | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 不足：4 不满足 |
| `AscendModelState.prepare_attn` | `model_states/default.py:44-121` | ✓ | ✓ | ✓ | 理论 ✓ | ✗（实例属 Target，写 `self.attn_metadata`） | ✓ | ✗（同一实例被 Target 与 Draft 共用，需 in-instance 判别器 → ContextVar/owner swap） | ✗（与 Target 共享实例） | ✓ | ✓ | 不足：5/7/8 |
| `_prefill` window 分支 | `autoregressive/speculator.py:532-583` | ✓ | ✓ | ✓ | 结构上 ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **被硬闸关闭**：`speculator.py:549-557`（`_eagle3_window_is_active()` 为假 + `runtime_mode != NONE` raise） |
| `_multi_step_decode` / `_generate_draft` window 分支 | `speculator.py:499-530` / `:452-497` | ✓ | ✓ | ✓ | 结构上 ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **被硬闸关闭**：`:515-517`、`:464-466`；且依赖 P3 store/generation |
| `_build_draft_attn_metadata` window 分支（**Ascend** 构建者） | `speculator.py:605-661` | ✓ | ✓ | ✓ | 结构上 ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 同上：分支需 `_eagle3_window_is_active()` + `_materialize_eagle3_decode_step`（需 live proposal） |
| 模块函数 `build_attn_metadata_wrapper` | `attn_utils.py:1251-1262` | ✓ | ✓ | ✓ | ✗（无 instance 形参，无法区分 Draft/Target 与 window 几何） | ✓ | ✓ | ✗（module-global 替换） | ✗（module 级） | ✓ | ✓ | 不足：4/7/8 |
| Backend `full_graph_fia*` | `attention_v1.py:943/1115` | ✓（capture 期被调用） | ✓ | ✓ | 理论 ✓ | ✓ | ✓ | 需新增 backend transport（=B） | — | ✓ | ✓ | 不足：需新建 transport（未授权） |
| Compilation layer `update_full_graph_params` / `set_draft_graph_params` | `acl_graph.py:304/350-404` | ✗（replay/update 侧） | ✓ | ✗（replay-only） | 仅改 update | ✓ | ✓ | ✓ | ✗（module-global 池） | ✓ | ✓ | 不足：1/3 |
| graph task 注册（`graph_task_group_begin/attn_params`） | `attention_v1.py:1083-1114` | ✓（capture 期写入） | ✓ | ✓ | ✗（记录的是已由 metadata 决定的 tensor，不能反推语义） | ✓ | ✓ | ✓（属既有机制） | ✗ | ✓ | ✓ | 不足：4 |
| `model_capture_wrapper` | `aclgraph_utils.py:298-304` | ✓ | ✗（仅换 model） | ✓ | ✗ | ✗（改 `speculator.model`） | ✓ | ✓ | ✓ | ✓ | ✓ | 不足：2/4 |

**任选一行都至少缺一项** → 按 §3“缺任何一项：不能判 FOUND”，当前源码中**不存在**符合约束的 Ascend-owned pre-capture injection seam。

---

## 5. §4 搜索面完整性核查（判定 Codex 是否真的搜过）

我自行覆盖了 §4 点名的全部六个面：Ascend manager（AR 与 DFlash 两个 `aclgraph.py` 通读）、Ascend backend（`full_graph_fia` / `_v2` 定义、调用点、参数记录）、compilation layer（`update_full_graph_params` / `GraphParams` / draft 参数池）、graph task / capture resource registration（`graph_task_group_*` + `attn_params` + `__init__` 期 `set_draft_graph_params`）、既有项目 patch 架构（`build_attn_metadata_wrapper` / `build_draft_attn_metadata_factory` / `model_capture_wrapper` / PCP / 310P）、以及 metadata 构建者本体（`AscendModelState.prepare_attn`、AR/DFlash speculator 的 `_build_draft_attn_metadata` / `_prefill` / `_generate_draft`）。

我**未能找到第七个**明显可疑入口。逐一比对 Codex 的 Search Ledger/Notes：其中的行已覆盖 AR `create_forward_fn`、`AscendModelState.prepare_attn`、`model_capture_wrapper`、`build_attn_metadata_wrapper`，Notes 的追踪图亦列出 `_multi_step_decode → speculator._build_draft_attn_metadata per step`。**未发现遗漏的明显可疑入口** → 按 §4 规则，允许 `SEARCH EXHAUSTED / NOT FOUND`。

需要单独指出的一点（不是“遗漏搜索”，而是分类边界）：Codex 对最近的一条技术路径（扩展既有 Ascend-owned override + 新增 capture-scoped speculator state/builder）标注为 `REQUIRES_VENDOR_CAPTURE_ASSEMBLY`，即在“未授权 B 方案”一侧。这在本轮约束下成立，但它是一个**授权边界判定**而非技术不可能性判定。Owner 的 Freeze 决策若依赖“B 不可行”，与依赖“B 未授权”，含义不同；建议 Owner 明确以“未授权”为准入依据（见 Q-01）。

---

## 6. §5 独立测试与 fail-closed 行为复现

P6A 没有实现代码，因此不存在“新接缝”的 red/green 可跑；我改为复现 Codex 的测试声明与现存的三类 fail-closed 保证：

**6.1 测试数量（精确复现）**

```
env VLLM_VERSION=0.29.0 PYTHONPATH=<vllm>:<vllm-ascend> .venv/bin/python -m pytest -q \
  tests/ut/spec_decode/test_draft_window_graph_binding.py \
  tests/ut/spec_decode/test_draft_window_graph_carrier.py
```
实测 **69 passed**（binding 37 + carrier 32），与 Codex 声称的 69 完全一致。此项同时也解决了我此前指出的“文件清单未声明”问题：上述两份文件即为该数字的来源。

**6.2 provider 缺失 → 严格 baseline（VERIFIED，静态）**
`observe_draft_window_graph_capture` / `consume_draft_window_graph_metadata` / `assert_...` / `build_...update_binding` 在 provider 缺失时全部 `return`（`draft_window_graph.py:1512-1528, 1530-1546, 1548-1570, 1572-1588`），OFF 行为不被扰动。

**6.3 provider 存在 → capture 硬失败（VERIFIED，静态 + 测试）**
`observe_draft_window_graph_capture` 在 provider 存在时无条件 `raise RuntimeError("P6 has no safe Ascend-only capture carrier seam in the pinned vLLM; Graph Window capture remains fail closed")`（`draft_window_graph.py:1520-1528`），AR decode capture 开头即调用它（`autoregressive/aclgraph.py:93`）；对应测试 `test_startup_capture_with_runtime_provider_fails_instead_of_faking_generation`（`tests/ut/spec_decode/test_draft_window_graph_carrier.py:845`）通过。

**6.4 provider 存在但 carrier 缺失 → 硬失败，无 baseline 回退（VERIFIED）**
`consume_metadata` 在 carrier 数量/序号/世代不匹配时 `raise RuntimeError`（`draft_window_graph.py:795-845`，docstring 即 “baseline metadata is forbidden”）；测试 `test_provider_exists_without_explicit_carrier_fails_before_baseline_metadata_can_win`（carrier 测试 :434）通过。

**6.5 Graph Gate 仍关闭（VERIFIED，且比 Codex 陈述更强）**
两层关闭：(i) 运行期硬闸 `NotImplementedError`（`autoregressive/speculator.py:466, 517, 553`）；(ii) **配置期**能力闸：`graph_mode != "NONE"` 被列为 capability failure（`draft_window.py:878-881`），`require_single_group_direct_prefix()` 对任何 failure 直接 `NotImplementedError`（`draft_window.py:150-172`）。
此外我发现一个 Codex 未陈述的更强事实：**P6 的 provider 机制在生产代码中根本没有安装点**——`install_draft_window_graph_binding_provider` 仅被 tests 调用（`draft_window_graph.py:1443` 定义；`grep` 全仓非测试目录无调用者），因此 carrier / 更新绑定在运行时完全惰性。测试 `tests/ut/spec_decode/test_draft_window.py:396, 442, 1904` 亦断言 baseline 对象上没有该属性。

---

## 7. Findings

### F-01 — **Major**（理由准确性；不改变 Outcome B）
**Codex 的首要论据“Ascend graph manager 只能在 upstream dummy metadata 构建前传递传统 owner 参数”不成立。**
- 证据：AR decode 的 dummy 准备由 **Ascend** manager 自己执行（`vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:119-128`，返回值被丢弃），随后图内每一步的 metadata 由 **Ascend** `_build_draft_attn_metadata` 构建（`autoregressive/speculator.py:605-661`），其 baseline 分支经 `build_attn_metadata_wrapper()` 把上游 speculator 模块的 `build_attn_metadata` 换成 Ascend 版本（`vllm_ascend/worker/v2/attn_utils.py:1251, 1255-1262`；patch 挂在 `aclgraph` 之外、由 `speculator.py:417-425` 在 decode capture 前安装）。即：**被捕获的 Draft operand metadata 就是 Ascend 构建的**。
- 影响：同一事实对 Owner 的 Freeze 决策有两种截然不同的含义。以“Ascend 被上游结构性挡在外”为据 → Freeze 是技术必然；以“Ascend 在位置上已拥有该 metadata，但缺 capture-scoped 状态、且现有传输手段违反约束”为据 → Freeze 是**本轮授权边界**的结果。后者才是事实。
- 要求更正：把理由改写为“能触达被捕获 metadata 的既有接口只有 (i) 上层 speculator 的**图模式硬闸**（`speculator.py:464-466 / 515-517 / 549-557`）与 (ii) 依赖 generation-scoped P3 状态的 window 分支，或 (iii) 违反 global/owner-swap 约束的 `module-global` 替换（`attn_utils.py:1251-1262`）；P6 的 `register_capture_identity` 虽定义了地址契约，但明确声明‘startup capture 未使用该地址’，且在 production 无调用者（`draft_window_graph.py:594-608, 1443`）”。

### F-02 — **Minor**（同源表述）
Codex 事实 #3 只指出 `prepare_inputs_to_capture` 的返回值被丢弃，未指出真正的 per-step consumer 是 Ascend 的 `_build_draft_attn_metadata`。作为“为什么不能走这条”的论证，该条**论据与结论之间缺一环**，建议与 F-01 合并修订。

### F-03 — **Minor**（P6 Final 代码注释措辞）
`observe_draft_window_graph_capture` 的 docstring 称 “The pinned upstream capture path builds private dummy metadata internally”（`draft_window_graph.py:1516-1518`）。对 DFlash 与“dummy **tables**”而言成立；对 Eagle3 AR decode 的 metadata **对象**不成立（由 Ascend 构建，见 F-01）。建议在 P6 后续修订中收紧措辞，避免后续 Reviewer 据注释得出“Ascend 未参与捕获 metadata”的错误前提。此项属于 P6 Final 的表达问题，不影响 P6A 裁定。

### F-04 — **Minor**（P7 前置条件应显式化）
配置期关闭是**硬失败**而非静默降级：`graph_mode != "NONE"` 触发 `NotImplementedError`（`draft_window.py:878-881` + `:150-172`）。P7 若走 eager track，须在文档/发布说明中明确“Window 要求 `cudagraph_mode=NONE`（或 `enforce_eager`）”，否则用户会看到启动期异常而非自动回退。

### Q-01 — **Question**（给 Owner 的决策问题，非缺陷）
Codex 把“扩展既有 Ascend-owned override + 新增 capture-scoped speculator state/builder”归入未授权 B 方案。技术判据上，该路径**不违反** §3 的 (1)(2)(3)(5)(6)(7)(8)(9)(10)，唯一需要放宽的是现有三处“eager-only”硬闸。请 Owner 确认：本轮“B 不授权”是否覆盖“在既有 Ascend-owned override 内增加 capture-scoped 状态”这一形态？该确认直接决定 GRAPH FREEZE 的理由是“未授权”而非“不可实现”。

### Q-02 — **Question**（可验证性边界）
本次（以及 P6A 全部结论）都是**静态 + host 侧单测**结论：capture 期“哪个 tensor 地址最终被 graph task 记录并按 replay 更新”只能在 NPU 上由 timeline/trace 证明。`consume_metadata` 自身也把 `update_effective_generation_ids` 置为 `None` 并标记 `NEEDS_NPU_TIMELINE`（`draft_window_graph.py:839-845`）。建议在 P7 的计划中保留该 NPU 验证项，避免把 host 侧绿测当作捕获语义已证。

---

## 8. 最终裁定

```
ASCEND-OWNED PRE-CAPTURE SEAM: NOT_FOUND_AFTER_REVIEW
  （搜索面已覆盖且有独立复核；不存在符合 §3 十项判据的既有 Ascend-owned 注入接缝。
    注意：这不是“Ascend 无法触达被捕获 metadata”——Eagle3 AR decode 的 metadata 正是 Ascend 构建的（F-01）。
    阻断点是缺 capture-scoped 状态与既有接口违反约束，而非上游结构性排除。）

GRAPH FREEZE: JUSTIFIED
  （支撑：① 无符合约束的既有接缝（§4）；② 现有 Window 分支对图模式三处硬闸 fail-closed；
   ③ 配置期 `graph_mode != NONE` 即能力失败（draft_window.py:878-881）；
   ④ P6 provider/carrier 在 production 无安装点，运行时完全惰性（draft_window_graph.py:1443 仅测试调用）；
   ⑤ P6 自述 `register_capture_identity` 的地址契约面向“future safe capture seam”，且明确不 attest startup capture 使用该地址。
   唯一需 Owner 明确的：Freeze 的正当性依据应写作“未授权 B”而非“不可实现”（Q-01、F-01）。）

P7 EAGER TRACK: SAFE TO PROCEED
  （eager 路径已落地并有测试覆盖；图模式用户在配置期即被 fail-closed 拒绝，不会静默出错；
   与图轨道冻结无耦合依赖。前置待办见 F-04 与 Q-02。）
```

---

## 9. 已记录但本轮**未授权**的未来选项（不作为修复建议）

以下仅作台账记录，本轮不得作为修复要求：

- **B（vendor-local capture assembly）**：在既有 Ascend-owned speculator override 内增加 capture-scoped 状态与 read source，使被捕获 metadata 直接引用 carrier backing。技术上最近，但本轮未授权（Owner 明确 B/C 暂不授权）。
- **C（修改 vLLM hook）**：在 `vllm/v1/worker/gpu/cudagraph_utils.py::prepare_inputs_to_capture` 或 `speculator/cudagraph_utils.py` 增加 provider 形参。受 R-REPO-01 约束（vLLM 必须保持 `84030bbe` 且 clean），本轮不可行。

---

## 附录 A — 复现命令

```bash
# baseline
cd /Users/wenqingzhang/Desktop/vllm/vllm && git rev-parse HEAD HEAD^{tree} && git status --porcelain
cd /Users/wenqingzhang/Desktop/vllm/vllm-ascend && git rev-parse HEAD HEAD^{tree} && git status --porcelain
git log --all --oneline --grep=P6A   # 空

# tests（69 passed）
cd /Users/wenqingzhang/Desktop/vllm/vllm-ascend
env VLLM_VERSION=0.29.0 PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm:/Users/wenqingzhang/Desktop/vllm/vllm-ascend \
  .venv/bin/python -m pytest -q \
  tests/ut/spec_decode/test_draft_window_graph_binding.py \
  tests/ut/spec_decode/test_draft_window_graph_carrier.py

# 生产代码中 provider 安装点（应只有定义处，无调用者）
grep -rn "install_draft_window_graph_binding_provider" --include="*.py" . | grep -v "^./tests"
```
