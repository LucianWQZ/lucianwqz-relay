# MRV2 Speculative Draft Sliding Window — Final Design

> 状态：**待人工设计 Review**。本阶段不进入实现，不改生产代码。
> 日期：2026-10-09
> 源码基线：`/Users/wenqingzhang/Desktop/vllm/vllm-ascend`、`/Users/wenqingzhang/Desktop/vllm/vllm`（本机 checkout；两个目录均无 `.git` 元数据，故不声称任何 commit）
> 输入材料：Stage 1–7 事实研究（`Sliding window原理_gpt.md`、`Sliding window源码_codex.md`）；Codex v2、DeepSeek v2、GPT v2 三份设计；以及各自对应的攻击式 Review。
> 行号约定：本文所有 `file:line` 均为本机逐条核对；Ascend 写 `vllm_ascend/...`，上游写 `vllm/v1/...`。

## 0. 如何阅读本文（证据等级）

每一处论断标注等级，Review 时请按等级索取证据：

| 标记 | 含义 |
| --- | --- |
| **[V]** | **已在当前 checkout 源码中核实**，附 `file:line`。可直接引用。 |
| **[M]** | **数学推导**，附条件与反例。可用计算复核。 |
| **[D]** | **设计决策**（取舍），不是事实。可在 Review 中挑战。 |
| **[OQ]** | **Open Question**：未验证，不得当作事实使用。已集中列在 §29。 |
| **[A]** | 由其他 Agent 材料引入、**我未逐行核实**的引用。仅作线索。 |

本文遵循三条取证据优先级：**源码事实 > Agent 推断；当前 checkout > 通用知识；两份材料一致 ≠ 正确**（§附录 A 记录了一处"两份材料一致但被第三份用反例推翻"的关键案例）。

---

## 1. Executive Summary

`draft_window_size` 是一个 **MRV1 已有、MRV2 缺失** 的 feature：它把 **Draft Attention 可读到的历史 KV** 限制在最近 `W` 个 token，而 Target 始终读全上下文（`vllm_ascend/spec_decode/utils.py:83-169`、`llm_base_proposer.py:415-452,1119-1127` [V]）。`grep draft_window_size` 在 `vllm_ascend/worker/` 下**零命中** [V]，MRV2 的 speculator 体系（`worker/v2/spec_decode/`）完全不消费该配置。

**核心结论**：MRV2 不能照搬 MRV1 的 `apply()`。原因是三条结构性差异 [V]：

1. **没有单一可变 metadata 边界**。MRV1 改的是 proposer 私有的 `common_attn_metadata`；MRV2 的表与长度分散在 `BlockTables`（与 Target **共享**同一对象，`vllm/v1/worker/gpu/spec_decode/speculator.py:287`）、speculator 的 `InputBuffers`、以及 Ascend 漏斗 `worker/v2/attn_utils.py:220-378` 的 per-group 构造里。
2. **窗口可见性的表达方式因 backend 而异**：GQA/MLA 是"表 + 长度"；DSA 非因果是 `ori_sparse_indices`（其**生成器**读表，最终 op 读索引，`worker/v2/spec_decode/dflash/speculator.py` 无关；见 `attention/dsa_v1.py:420-461` [V]）；SFA 是 top-k 索引且其 native window 参数被**关闭**（`attention/sfa_v1.py:114-119` [V]）。
3. **metadata 有三个构建入口**，其中 capture 期的入口**不在** speculator 的控制之下（`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:36,55`；`vllm/v1/worker/gpu/cudagraph_utils.py` → Ascend `worker/v2/model_states/default.py:95-121`）[V]。这决定了一切 graph 相关设计。

**推荐架构**（§10）：

> **Speculator-owned Draft Window Read Plane**：在 each method 的最后 full-state 点，由 speculator 从 canonical full source 构造一个 proposal-scoped、visibility-domain 一致、per-consumer-group 物化、**capture-bound**、lane/lease 保护的 **Draft-only KV read plane**（`DraftAttentionView`），经**显式参数**送入 **Draft-only metadata 入口**。Target、absolute positions、slot mapping、真实 KV allocation 全程留在 full physical world 且 **不可变**。

**首期可交付范围**（capability-gated，§9）：`{dflash, dspark（非 DeepSeek-V4 target）} × {GQA, MLA} × eager`，FULL 在 capture binding 落地后开放；AR/Eagle3、PIECEWISE、DSA 非因果/SFA、全部 CP/DCP、310P 在其专属 gate 关闭前 **fail closed**。MTP 与 `DeepSeek-V4 target + DSpark` 是 **policy-forced Window OFF**，不进入上述 enablement 集合。

**权威 method policy（maintainer，2026-10-09）** [D]：

- MTP：仅当用户配置 Window 时 warning once，并强制 Window OFF；原因是 draft 与主模型一起训练。该分支在任何 `W` 数值校验、layout/capability inventory、planner 或 workspace 之前返回。
- Eagle3：严格跟随 Window 开关；OFF 保持当前 baseline，ON 才进入本文数学与 capability/runtime gates。
- 并行 speculative：`DeepSeek-V4 target + DSpark` 在用户配置 Window 时 warning once，并因 draft 与主模型一起训练而强制 OFF；其余并行 method/model 严格跟随开关，ON 时仍不得绕过任何原有 backend/graph/runtime gate。

**本设计相对三份 v2 材料的关键修正**（详见 §附录 A）：

| # | 修正 | 来源 | 影响 |
| --- | --- | --- | --- |
| F1 | **对齐单位不得默认取 lcm**；MRV1 的锚是"第一个 draft layer 的 kernel block size"，只有**当所有 consumer span 都整除它**时才可逐位兼容；非整除时 lcm 可能把窗口**放大到失效** | GPT v2 §6.2 的反例（Codex v2 与我此前都主张 lcm 优先，**双方均被反例推翻**） | Critical（会静默放大可见历史） |
| F2 | **窗口表用窄表 + 显式 capture binding**（而非 full-width 同形） | Codex v2 D05/R-11；我 v2 的 full-width 方案被其"同形不解决地址"论证推翻，且 full-width 有 `O(R×Σfull_width)` 显存代价 | 架构 |
| F3 | **DSA 非因果不需要额外 clamp 绝对 start**；把表与长度一起 rebase 后，其 native 选择器在相对坐标里**自然**求交 | Codex v2 R-17（我此前"只裁表无效"的结论错误），本文复核了 `build_dspark_swa_indices` 的坐标自洽性 [V] | 简化 |
| F4 | **padding 行不需要与 active 行的 block id 不相交**；正确契约是"读可任意（输出被裁掉）、写必须为零" | `attention/attention_v1.py:340-360` 的源码注释 [V]；Codex v2 R-08 | 删除一条过强约束 |
| F5 | **物理保留上限**必须参与语义：recycling KV spec（sliding-window/chunked-local）会**物理释放**窗口外块 | `vllm/config/vllm.py:602-609` 注释 + `vllm/v1/kv_cache_interface.py:811,909,1316` [V]（三份材料中仅 DS v2 提出） | 新增约束 |
| F6 | **`W ≥ K` 是必要且充分的配置条件**（不是"几乎不可达"） | 我在两份 review 中曾给错结论，GPT v2 §6.4 与 Codex v2 R-m3 均给出正确反例 [M] | 校验策略 |
| F7 | **源码引用不得要求 pointer 恒等于 `input_block_tables[g]`**，且 `x[:n]` 的 `storage_offset` 不随 descriptor 漂移 | Codex v2 R-04/R-10（我此前两条断言过强/有误） | 断言口径 |
| F8 | **method policy 先于数值与能力解析**：MTP、DeepSeek-V4+DSpark 强制 OFF；Eagle3 与其他并行组合跟随开关 | maintainer 产品策略（2026-10-09）[D] | 产品范围；不修改数学或放宽 backend gate |

---

## 2. Problem Statement

Draft model 通常在短上下文（4–8k）上训练。当运行上下文远超训练长度时，draft 的 attention 变成 out-of-distribution，acceptance 崩塌（文档给出的观测：GLM-5.2 + early DSpark draft 在 32k 处 mean acceptance 从 ~5 掉到 ~1，投机成为净损失）[V，`docs/source/developer_guide/Design_Documents/speculative_kv_sliding_window.md:3-15`]。

`draft_window_size` 通过把 **draft attention 的历史可见范围** 限制到最近 `W` 个 token 来恢复 acceptance，同时**不改变** Target 的计算（Target 始终 full context）⇒ 输出分布不变、只有 draft 的 proposal 质量改变 [V，同上 `:10-15`]。

MRV1 已实现并验证（Eagle3 / DSpark 有 E2E [V，`tests/e2e/pull_request/one_card/spec_decode/test_dspark.py:80-158`、`tests/e2e/pull_request/two_card/spec_decode/test_spec_decode.py:370-434`]）。MRV2 未实现，且 MRV2 的运行时结构与 MRV1 有实质差异（§7）。

**本文要解决的问题**：给出一个**可多人 review、可长期维护、可安全 fail-closed** 的 MRV2 架构，使 `draft_window_size` 在 eligible ON 组合上具备与 MRV1 等价的窗口语义，并明确哪些组合尚不可用。method 产品范围以 2026-10-09 maintainer 策略为准；它可以把当前 MRV1 code-reachable 组合强制留在 OFF baseline，但不改变任何窗口数学。

---

## 3. Scope

**覆盖**：

- 配置契约与兼容策略（MTP 与 DeepSeek-V4+DSpark policy-forced OFF；Eagle3/其他并行组合 follow-config）；[D，maintainer 2026-10-09]
- Draft Attention read plane 的构造：window 数学、per-consumer-group 物化、长度语义、backend 可见性表达；[V]
- method × backend × graph mode 的 capability 矩阵与 fail-closed 规则；[D]
- capture / replay / live 三个 metadata 入口的一致性与地址契约；[V]
- 长度类型系统（device exact / CPU exact? / CPU upper / capacity / backend-derived max）与 DCP local 语义；[V]
- async 生命周期（host ring + device slot + lease/event）；[V]
- BlockTable / SlotMapping / positions / Target 的隔离不变式；[V]
- 测试矩阵、性能验收、Window OFF 回归；[D]
- Week4 扩展点（Flashcomm、SP/DSA-CP、更深 async）。[D][OQ]

**明确不在本文范围**：不写生产代码、不做实现拆分到 PR 粒度（仅给顺序）、不承诺 acceptance/延迟数值。

---

## 4. Non-goals

1. 不改变 Scheduler/KV Cache Manager 的 block 分配、释放、复用、prefix cache 与 resume 语义。[V，`vllm/v1/worker/gpu/block_table.py:112-146` 是唯一写入点，本文不动]
2. 不改变 Target forward / verification / rejection sampling / 最终输出分布。
3. 不把 `draft_window_size` 扩展成 Target sliding window。
4. 不改变 real positions、RoPE 语义、query layout、`idx_mapping`、request ordering。
5. 不把 DSA 原生 `dspark_swa_indices`、模型自身 native SWA 与本 feature 合并成一个配置。
6. 不为 Ascend MRV2 新增 `draft_model`/ngram/suffix/medusa/custom_class 等 method；不改 MRV2 factory 的 `NotImplementedError`。[V，`worker/v2/spec_decode/__init__.py:72`]
7. 不改变 DFlash2 当前 eager-only 约束。[V，`worker/v2/spec_decode/dflash2/speculator.py:121-139`]
8. **第一版不修改 MRV1 的 `SlidingWindowAdapter`**（`vllm_ascend/spec_decode/utils.py`）。对 eligible ON 组合，MRV1 作为窗口数学 golden oracle；policy-forced OFF 组合只与 Window-OFF baseline 对拍。"数学只有一份"的重构另立 PR。[D]
9. 不借本 feature 扩张 Ascend MRV2 的 method 支持面；也不把 MRV1 中"未读取配置"的方法在 MRV2 改成新行为（§22.4）。
10. 不在未验证组合上"静默启用"——所有未声明能力的组合必须 fail closed（§23）。

---

## 5. Terminology

| 术语 | 定义 | 关键源码 |
| --- | --- | --- |
| **Full physical world** | Scheduler 分配 + `BlockTables.block_tables[g].gpu`（authoritative）+ gathered `input_block_tables[g]` + `slot_mappings` | `vllm/v1/worker/gpu/block_table.py:53-110` [V] |
| **Draft read plane** | 本 feature 新增的、只被 Draft Attention 读取的窗口化表/长度（`DraftAttentionView`） | 本文 §11 [D] |
| **`W`** | `draft_window_size`（`additional_config` 字段） | `vllm_ascend/ascend_config.py:497` [V] |
| **`L`** | apply-time 的 **full exact** 绝对长度（draft device `seq_lens`） | `vllm/v1/worker/gpu/spec_decode/speculator.py:355` [V] |
| **`U`** | apply-time 的 **CPU upper bound**（允许 > L） | `vllm/v1/worker/gpu/spec_decode/speculator.py:326-334` [V] |
| **`K`（future_offset）** | apply 时窗口右边界需要越过 `L` 的未来 token 数；**是 apply timing 的函数，不是常数** | `llm_base_proposer.py:445` [V] |
| **`B_legacy`** | MRV1 使用的**单一**对齐量 = 第一个 draft attention layer 的 `kernel_block_size` | `llm_base_proposer.py:406-408,446-452` [V] |
| **`span_g`** | consumer group `g` 的 **table 列 token span**；`cp_size==1` 时 = `kernel_block_size_g`；DCP 布局下 = `kernel_block_size_g × cp_size` | `worker/v2/spec_decode/dflash/speculator.py:264`（`query_pos // (block_size * CP_SIZE)`）[V] |
| **`A`（alignment）** | visibility domain 的对齐单位（§16.2 的三支规则，**默认 `B_legacy`**） | [D] |
| **`S`** | proposal 级**冻结**的窗口绝对起点 | [D] |
| **visibility domain** | 必须共享同一逻辑 origin 的 consumer group 集合 | Codex v2 D03/D16；本文 §11.3 [D] |
| **`window_consumer_group_ids`** | 其可见性/派生索引依赖窗口的 group 集合（**含 SFA indexer 等派生依赖组**，不只是 draft attention 组） | Codex v2 D16；本文 §16.1 [D] |
| **`valid_num_blocks[g][row]`** | 本轮该 row 在该 group 的有效表列数（**源侧有效性的唯一权威**） | `vllm/v1/worker/gpu/block_table.py:61,170-171,263-272` [V] |
| **capture binding** | capture 期 dummy metadata 与 runtime view 使用**同一 backing**的绑定对象 | Codex v2 D05/§11.2；本文 §19.3 [D] |
| **T1 / T2** | 本文件中：**T1** = "表 + 长度"表达的 backend；**T2** = "显式索引"表达的 backend（本文已合并处理，见 §21.2） | [D] |

---

## 6. MRV1 Feature Contract 与已批准迁移策略

### 6.1 当前 MRV1 源码事实与权威迁移策略

下表把当前 MRV1 code-reachable 行为 [V] 与本次已经批准的 MRV2 产品策略 [D] 分开。后者由 maintainer 于 2026-10-09 明确给出，**覆盖**旧的 method 范围；不得把旧源码分支自动升级为 MRV2 产品契约。

| 条件 | 当前 MRV1 源码事实 [V] | MRV2 权威策略 [D] | 证据 |
| --- | --- | --- | --- |
| `draft_window_size is None` | OFF，零开销 | OFF baseline；不 warning、不分配、不重建 | `llm_base_proposer.py:415` |
| Eagle3 | 公共 apply 点；`future_offset = K` | **严格 follow-config**：OFF 走 baseline；ON 才进入原数学与全部 capability/runtime gates | `:437-452,1119-1127`；maintainer 2026-10-09 |
| Eagle（非 Eagle3） | 代码路径同样启用 | 保留既有 E2/capability 决策；本次策略不扩大其支持面 | `:437` |
| DFlash / DFlash2 | 公共 apply 点；`future_offset = 0` | **follow-config**；ON 受原 gates，DFlash2 仍 eager-only | `:445`；`:437`（DFlash2 的 `method` 仍是 `"dflash"`） |
| DSpark（非 DeepSeek-V4 target） | **per-group** apply | **follow-config**；ON 受原 gates | `:2588-2605` |
| DSpark + DeepSeek-V4 target | 当前源码存在旧 warning 分支 | 配置 Window 时 **warning once + 强制 OFF**；原因是 draft 与主模型一起训练；不进入数值校验/planner/workspace | `:420-435`；maintainer 2026-10-09 |
| 全部 normalized `mtp`（含 Gemma4/Step3.5/multi-KV 变体） | warning + ignore，不构造 adapter | 配置 Window 时 **warning once + 强制 OFF**；原因是 draft 与主模型一起训练；不进入数值校验/planner/workspace | `:423-429,437`；maintainer 2026-10-09 |
| `draft_model` | 代码路径可达但文档未承诺 | 不扩张 MRV2 支持面，保留 factory error | `:437` |
| ngram / ngram_gpu / suffix / medusa / extract_hidden_states | 不经过 base proposer ⇒ **静默未读取** | 保持现状 | `spec_decode/__init__.py:41-70` |
| mlp_speculator / custom_class | Ascend factory 本身不可实例化 | 保持 factory error | 同上 |

`warning once` 的 owner 是 engine/speculator 实例；同一实例不得按 proposal 重复打印。MTP 与 DeepSeek-V4+DSpark 的 forced-OFF 返回必须发生在任何 Window 数值校验、backend/layout inventory、planner、workspace/capture binding 之前，因此即使用户给出 `W<=0`，也只执行对应 policy warning + OFF，不触发 Window 数值错误。

### 6.2 窗口数学（MRV1 原式）[V]

```text
start        = floor(max(L + K - W, 0) / b) * b          # b = B_legacy
windowed_len = L - start
start_block  = start / b
max_cols     = ceil(W / b) + 1                            # MRV1 的容量（保守）
```
被改写对象：`block_table_tensor`（换成 persistent clone 的视图）、device `seq_lens`、以及存在时的 `seq_lens_cpu` / `_seq_lens_cpu` / `seq_lens_cpu_upper_bound`（三者各自独立重算同一公式）[V，`spec_decode/utils.py:149-169`]。

### 6.3 五条必须继承的不变式 [V]

1. **只改 read plane**：`slot_mapping` 不被修改；后续 draft step 的 slot 计算显式改用 `self.sliding_window.full_block_table`（`llm_base_proposer.py:2104-2112`）。
2. **absolute positions 不变**（`apply()` 不碰 positions）。
3. **`start` 在 proposal 级冻结**：`_propose` 只 apply 一次（`:1119-1127`），之后每步只把**长度**递增（`:2073-2077`、`:2134-2136`），裁剪过的 clone 全程不变。
4. **可见长度可以超过 `W`**（block 对齐的自然结果，最大 `W + b - 1`）。
5. **OFF 时零行为变化**。

### 6.4 MRV1 的两处已知缺陷（本文不继承）

| 缺陷 | 证据 | 本文处理 |
| --- | --- | --- |
| CPU mirror 与 device exact **各自独立**套公式 ⇒ async 下可能落在不同 start（表 origin 与 upper origin 不一致） | `spec_decode/utils.py:165-169` + `llm_base_proposer.py:1095`（CPU 用 `optimistic_seq_lens_cpu`） | §17.2 用 **canonical start**（由 exact 决定）平移 upper，并夹紧到容量 |
| 无 `W ≤ 0` 范围校验 | `ascend_config.py:497`；`_validate_user_input_ranges()`（`:568-586`）不覆盖它 | §22.2：收紧需 maintainer 批准（[OQ]） |

---

## 7. MRV2 Existing Architecture

### 7.1 与 Target 共享的物理世界 [V]

| 对象 | Owner | 与 Target 的关系 | 证据 |
| --- | --- | --- | --- |
| `BlockTables.block_tables[g].gpu` | 共享 `BlockTables` | 同一份 authoritative | `vllm/v1/worker/gpu/block_table.py:53-59` |
| `BlockTables.input_block_tables[g]` | 共享 `BlockTables` | **与 Target 同一 buffer**（每步按 `idx_mapping` gather） | `:71-75,148-175` |
| `BlockTables.slot_mappings` | 共享 `BlockTables` | 真实 KV 写地址 | `:77-81` |
| `BlockTables.num_blocks` | 共享 `BlockTables` | per-group/per-req 有效列数（**UVA 张量**） | `:61,170-171` |
| speculator `input_buffers.seq_lens` | speculator | 独立 | `vllm/v1/worker/gpu/spec_decode/speculator.py:144-163` |
| speculator `input_buffers.positions` | speculator | 独立（AR 首步由 Target 复制） | 同上；`autoregressive/speculator.py:742-747` |
| `target_input_buffers` / `target_attn_groups` | Target runner | **共享引用**（Draft prefill 复用之故，见注释） | `spec_decode/speculator.py:287-293` |
| `speculator.block_tables` | 共享同一 `BlockTables` 对象 | 非拷贝 | `:287` |

**推论（P0 级）**：任何 window 变换都**不能原地改写** `input_block_tables` / `slot_mappings`（MRV1 能原地改，是因为那是 proposer 私有对象）。

### 7.2 metadata 的三个构建入口 [V]

| # | 入口 | 源码 | 传入的 block table |
| --- | --- | --- | --- |
| 1 | live propose | `vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:453`；AR 路径 `speculator.py:346` | Draft 侧（设计可替换） |
| 2 | graph-manager replay 前 rebuild | `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:86-98`；`autoregressive/aclgraph.py:132-152` | Draft 侧 |
| 3 | **capture 期 dummy metadata** | DFlash：`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:36,55`（符号由 `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26` 在**导入期**重绑定，**绕过** `build_attn_metadata_wrapper()`）；AR/Target：`autoregressive/aclgraph.py:111` → `vllm/v1/worker/gpu/cudagraph_utils.py`（dummy 表约 `:785`、`model_state.prepare_attn` 约 `:820`）→ Ascend `worker/v2/model_states/default.py:95-121` | **full 宽度零表**（`block_table.py:177-187`） |

**这是本文最重要的源码事实**：入口 3 决定 captured 算子的 tensor 身份，且**不在** speculator 的显式控制之下（见 §19）。

### 7.3 Ascend 漏斗 [V]

`vllm_ascend/worker/v2/attn_utils.py:220-378`：按 KV-cache group 循环，取 `block_tables[i]` / `slot_mappings[i]`，构造 `AscendCommonAttentionMetadata`，再交给该 group 的 builder。两处关键兜底：

- `:253-260`：`seq_lens_np is None` ⇒ `np.full(num_reqs, max_seq_len)`；`seq_lens_cpu_upper_bound is None` ⇒ 等于 `seq_lens_cpu`。
- `:294-330`：`seq_lens` 在循环**外**算好、**所有 group 共用**（这是 §16 的核心约束）。

Draft 路径的 `max_seq_len` 是 `self.draft_max_seq_len`（`vllm/v1/worker/gpu/spec_decode/speculator.py:361` [V]）⇒ 兜底会填出 **full 量级**的 CPU 长度（§17.3 的危险路径）。

### 7.4 长度选择的既有优先级 [V]

- `_select_seq_lens`（`vllm_ascend/attention/utils.py:553-587`）：`_seq_lens_cpu` → `seq_lens_cpu` → device D2H；`parallel_drafting` 强制 device，**例外**是 `use_dspark() and _is_glm_model()` 保留 CPU。
- MLA 独立实现 CPU 优先（`attention/mla_v1.py:500-509`）。
- SFA/DSA 另有 CPU 辅助消费者（`attention/sfa_v1.py:641-655`、`attention/dsa_v1.py:837` 附近）。

### 7.5 Graph 与 async 的既有事实 [V]

| 事实 | 证据 |
| --- | --- |
| `ACLGraphWrapper` 只检查 **positional args** 的地址；metadata 内嵌 tensor 不在检查范围 | `vllm_ascend/compilation/acl_graph.py:186` |
| update 与 replay 的先后**取决于 `enable_enpu`**：`enable_enpu=True` 先 update 再 replay，否则先 replay 再 update | `compilation/acl_graph.py:292-320` |
| async/MT 下可能"iteration i 的 update 早于 iteration i-1 的 replay"，代码显式要求 `synchronize`；**FULL + EAGLE merge 路径不需要该 barrier** | 同上（注释原文） |
| GQA 的 FIA 调用 `register_task(..., {"block_table": ...})` ⇒ **可重绑指针** | `attention/attention_v1.py:652-660` |
| `use_updatable_graph()` 仅对 `AscendAttentionBackend` 为真 | `vllm_ascend/utils.py:1769-1775` |
| SFA / DSA 的 `update_graph_params()` 都是 `pass` | `attention/sfa_v1.py:885-897`；`attention/dsa_v1.py:1619-1631` |
| DSA 的 op 在 **capture 时捕获 `ori_sparse_indices` 的 data pointer** | `attention/dsa_v1.py:420-436`（docstring 原文） |
| MRV2 + async ⇒ `max_concurrent_batches = pp_size + 1 ≥ 2` | `vllm/config/vllm.py:589-598` |
| UVA pool 深度由 `set_default_max_concurrency` 设置；复用前要求 GPU reader retire | `vllm/v1/worker/gpu/buffer_utils.py:24,19,61` |

---

## 8. Design Invariants

> 实施与 Code Review 的强制检查表。任一条不满足 ⇒ 不得合入。

| # | 不变量 | 判据 |
| --- | --- | --- |
| **I1** | **Target-full**：Target 的 builder / metadata / verification 永远使用 full state；Target 调用的公开入口在**签名上无法接收** window view | 对象 identity + 内容快照逐位不变；签名审查 |
| **I2** | **Absolute positions**：positions 的值、storage 与 RoPE 语义不因窗口改变 | 物化前后 `positions` 逐位与 `data_ptr` 不变；`positions` 不出现在 view 的可写字段 |
| **I3** | **Full write mapping**：所有 slot mapping / context slot / 真实 KV 写地址都从 full authoritative table 计算 | 开/关窗口的 `slot_mappings` 逐位相同 |
| **I4** | **No full-state mutation & no alias**：authoritative 表、gathered 表、canonical lengths 只读；窗口产物与其**storage 区间不重叠** | 用 storage 区间判别名（不得只比 `data_ptr()`：带 offset 的 view 共享 storage） |
| **I5** | **One origin per visibility domain**：domain 内所有 group 共享同一绝对 `S`；`start/gid` 由布局整除性保证为整数 | 逐 group 断言 `S % span_g == 0` |
| **I6** | **Proposal-frozen anchor**：proposal 内 `S` 不变（`L_s + future_offset` 恒定）；`future_offset` **不是常数** | 逐 step 断言；与 MRV1 差分 |
| **I7** | **Length coherence**：device exact / CPU exact? / CPU upper / DCP local / backend-derived max 全部由同一 `S` 派生且 `upper ≥ exact` | §17 的公式 + 断言 |
| **I8** | **No fallback under Window**：view 存在时任何必需 CPU 字段缺失 ⇒ 报错；**禁止**落到 `np.full(max_seq_len)` | 负向测试（缺 CPU 字段必须抛错） |
| **I9** | **Capacity clamp**：任何被 backend 当作 KV 长度的值 ≤ `needed_g × span_g`（即已写入列能覆盖的最大长度） | 闭包断言（**不只是"≤ windowed_len"**） |
| **I10** | **DCP interval semantics**：`local_exact = local_prefix(E) - local_prefix(S)`，**不是** `local_prefix(E - S)` | 非线性反例测试（见 §17.4） |
| **I11** | **Idempotence + single source**：每次 refresh 从 canonical full source **全量重写**目标容量；不接受 view 作为下一次 source | 同 step N 次调用结果逐位相同；把 view 当 source 抛错 |
| **I12** | **Stale-tail safety**：源读取同时受 `row_width` 与 per-row `valid_num_blocks` 约束 | 预填 stale block id 的负向测试 |
| **I13** | **Padding = no-observable-side-effect**：padding 行**读**的内容可任意（输出被裁掉/不写），但**写**必须为零（slot 为 PAD/inert），且每步确定性重写 | §18.3；`attention/attention_v1.py:340-360` |
| **I14** | **Capture identity**：同一 `(descriptor, lane, phase, step, gid)` 的 capture / live / replay 使用**同一 backing** 且 shape/stride/dtype 兼容 | §19.3 的签名比对（`data_ptr, shape, stride, dtype`；`storage_offset` 仅作诊断） |
| **I15** | **Epoch identity**：每个 proposal **无条件**新建 epoch；epoch 含 ordered request identity、`idx_mapping`、valid counts、source generation、layout version、descriptor、lane | §15.2 |
| **I16** | **Lease safety**：最后一个 reader + graph task update + device consumer completion event 之前不得覆盖 slot | §20.3 |
| **I17** | **Method policy by semantics**：按 normalized method + target identity 判定；MTP、DeepSeek-V4+DSpark forced-OFF 早于数值/能力/资源动作，不得因 concrete class 或 backend capability 重新启用 | §22.1/§22.3 |
| **I18** | **Native visibility intersection**：native SWA / top-k / DSA selector 必须与窗口在**同一坐标系**内派生，禁止双重 origin 平移 | §21；集合级测试 |
| **I19** | **Eligible AR ON legal domain**：`W > 0` 且 `W ≥ K`；运行时仍断言 `visible_len ≥ 0`；policy-forced OFF 不进入该合法域 | §16.4、§22.1 |
| **I20** | **Fail closed**：未声明能力的 backend / layout / graph / parallel 组合 ⇒ 拒绝窗口，不得静默使用可疑 view | §23；负向测试 |
| **I21** | **Physical retention**：`effective_window_g = min(W, spec 保留量_g)`；recycling spec 下更大的 `W` 无效 | §21.4 |
| **I22** | **Window OFF identity**：显式 OFF 与 policy-forced OFF 均无 workspace、materialize、metadata 重建或 graph key/数量变化；forced-OFF 仅允许一次去重 warning | §27 |

---

## 9. Method Support / Compatibility Matrix

### 9.1 支持等级

| 等级 | 含义 |
| --- | --- |
| **E1（首期）** | 设计闭合、可通过 fail-closed gate 的路径；实现顺序靠前 |
| **E2（后续）** | 设计已给出，但依赖尚未关闭的 gate（[OQ]）；gate 关闭后自动升级为 E1 |
| **P-OFF（策略强制关闭）** | 用户即使配置 Window 也 warning once + 强制 OFF；不得进入数值校验、planner、workspace 或 backend gates |
| **X（不可达）** | factory error 或本 feature 不提供该 method |
| **N/A** | 无 draft attention read plane |

### 9.2 Method × 支持等级 × 前置 gate

| Method | MRV1 行为 [V] | MRV2 v1 等级 | 前置 gate | `K` | Graph |
| --- | --- | --- | --- | ---: | --- |
| `dflash` | 启用（公共 apply） | **E1**（eager）→ E2（FULL）；严格 follow-config | capture binding（§19.3） | 0 | eager / FULL_DECODE_ONLY（当前无 PIECEWISE [V `dflash/speculator.py:122-146`]） |
| `dspark`（非 DeepSeek-V4 target） | 启用（per-group apply） | **E1**（eager，GQA/MLA）→ E2（FULL、DSA/SFA）；严格 follow-config | backend 可见性审计（§21.2）、capture binding | 0 | eager / FULL |
| `dspark` + DeepSeek-V4 target | 当前源码有旧 warning 分支 | **P-OFF**（warning once + 强制 OFF） | **不进入 gate** | — | 保持 Window-OFF baseline |
| `dflash` + DFlash2 arch | 继承 DFlash | **E1**（仅 eager） | — | 0 | eager only [V `dflash2/speculator.py:121-139`] |
| `eagle3` | 启用（公共 apply） | **E2**；严格 follow-config：OFF baseline，ON 进入原 gates | AR first-pass 重建 + FULL per-step device length（§12.2） | `K` | eager / PIECEWISE / FULL |
| `eagle` | **代码路径同样启用** [V `:437`] | **E2**（与 eagle3 同契约） | 同上 | `K` | 同上 |
| `draft_model` | 代码路径启用，但 MRV2 factory 不支持 | **X**（保留 factory error） | — | — | — |
| `mtp`（全部变体） | warn + ignore | **P-OFF**（warning once + 强制 OFF） | **不进入 gate** | — | 保持 Window-OFF baseline |
| `extract_hidden_states` | 不适用 | **N/A** | — | — | 保持现状 |
| ngram / ngram_gpu / suffix / medusa | 静默未读取 | **N/A**（保持现状，不升级为 warning） | — | — | — |
| mlp_speculator / custom_class | Ascend 不可实例化 | **X**（factory error 原样） | — | — | — |

**注意（易错）**：MRV2 Ascend factory 用 `speculative_config.use_eagle()` 作为**兜底分支**（`worker/v2/spec_decode/__init__.py:68-71` [V]），而 `use_eagle()` 的成员是 `("eagle","eagle3","mtp","dflash","dspark")`（`vllm/config/speculative.py:1936-1940` [V]）。因此 Gemma4/Step3.5 MTP 会落到 `AscendEagleSpeculator` ⇒ **policy 绝不允许按 concrete class 推断**。

**Policy-before-capability 不变量**：`P-OFF` 在 layout/backend 建立前即可由 normalized method + target model identity 判定；一旦命中，不得以“backend 已支持”或“W 数值合法”为由重新开启。Eagle3 和其余 eligible parallel 组合则相反：policy 只决定是否进入 ON 路径，不能替代后续 capability/runtime gate。

### 9.3 Backend × 可见性表达 × 首期门禁

本表只描述 `FOLLOW_CONFIG + Window ON` 的 eligible 组合；`P-OFF` method 在 backend inventory 之前已返回，不能因下表某 backend 标为 E1/E2 而重新启用。

| Backend | 可见性如何表达 [V] | window 落点 | 首期 |
| --- | --- | --- | --- |
| GQA / FIA | `block_table` + `actual_seq_lengths_kv`；native SWA 另有 band（`sparse_mode=4 / pre_tokens`）`attention_v1.py:602-604` | 表 + 长度（rebase 后 native band 在相对坐标继续收紧） | **E1**（需 CPU/device 长度同源证明） |
| MLA | `decode.block_table` + CPU 优先长度（`mla_v1.py:500-509`） | 表 + 长度；**CPU exact 必须可用** | **E1**（缺 CPU exact ⇒ fail closed） |
| DSA（causal） | `block_table` + `seq_lens` + `ori_win_left` | 表 + 长度 | **E2**（需 derived state 审计） |
| DSA（non-causal、eligible DSpark） | 显式 `ori_sparse_indices`；**其生成器读表**（`dsa_v1.py:420-461`） | 表 + 长度 rebase ⇒ 生成器在相对坐标自然求交（§21.2） | **E2**（需 §21.2 的审计 gate） |
| SFA（sparse MLA / NoPE） | top-k 索引 + 自有 `block_table_buffer`；**native window 参数被关闭**（`sfa_v1.py:114-119`） | 表 + 长度 + **额外的 window-relative visible count**（top-k 长度由**绝对** positions 派生：`indexer.get_topk_lengths`） | **E2**（需专用 provider） |

---

## 10. Architecture Overview

### 10.1 总架构图

```text
                        ┌─────────────────── FULL PHYSICAL WORLD（全程只读） ───────────────────┐
                        │                                                                       │
  Scheduler/KV Mgr ───► BlockTables.block_tables[g].gpu  (authoritative, persistent)          │
                        │        │                                                              │
                        │        ├─ gather(idx_mapping) ─► input_block_tables[g]  (persistent)  │
                        │        │                              │                               │
                        │        └─ block_table_ptrs ──┐        │                               │
                        │                              ▼        │                               │
                        │                    compute_slot_mappings()                            │
                        │                              │        │                               │
                        │                              ▼        │                               │
                        │        slot_mappings[g] (physical KV write) ─────► reshape_and_cache  │
                        │                                       │                               │
                        │   positions(abs) / query_start_loc ───┼───────────────┐               │
                        └───────────────────────────────────────┼───────────────┼───────────────┘
                                                                │               │
  ┌── TARGET PATH（不经 window）─────────────────────────────────┼───────────────┼──────────────┐
  │  input_batch ──► Ascend build_attn_metadata(full 参数) ──► Target metadata ──► Target fwd  │
  └────────────────────────────────────────────────────────────┼───────────────┼──────────────┘
                                                                │               │
  ┌── DRAFT PATH ───────────────────────────────────────────────┼───────────────┼──────────────┐
  │                                                             │               │              │
  │  [1] method 的最后 full-state 点（§13）                      │               │              │
  │      · AR: prepare_prefill_inputs / 每 step full slot 后      │               │              │
  │      · eligible DFlash/DSpark: 所有 consumer group prepare 后 │               │              │
  │                          │                                   │               │              │
  │                          ▼                                   │               │              │
  │  [2] DraftWindowPlanner  (纯数学, 无 tensor)  §11.2           │               │              │
  │      S = align_A(max(L+K-W,0)); visible = L-S; needed_g       │               │              │
  │                          │                                   │               │              │
  │                          ▼                                   │               │              │
  │  [3] DraftWindowWorkspace (speculator-owned, persistent)      │               │              │
  │      ├─ window_block_tables[g][R, C_g]        ← 窄表          │               │              │
  │      ├─ window_seq_lens / start / cpu_upper   ← 同 origin     │               │              │
  │      ├─ dcp_local_lens                        ← prefix 差      │               │              │
  │      └─ lane ring + epoch/lease/events                        │               │              │
  │                          │  materialize from FULL source      │               │              │
  │                          │  (mask: needed × row_width × valid_num_blocks)       │              │
  │                          ▼                                   │               │              │
  │  [4] DraftAttentionView  (immutable descriptor, per gid) ─────►│               │              │
  │                          │                                   │               │              │
  │                          ▼                                   ▼               ▼              │
  │  [5] Draft-only metadata 入口  build_draft_attn_metadata(view) ──► backend builders          │
  │      · GQA/MLA: 表+长度替换                                    │               │              │
  │      · DSA non-causal: 表+长度 rebase（生成器自然求交）        │               │              │
  │      · SFA: 额外 window-relative visible count                │               │              │
  │                          │                                   │               │              │
  │                          ▼                                   │               │              │
  │  [6] draft model.forward ──► Draft tokens ──► Target verification（full）                     │
  │                                                                                              │
  │  [7] DraftWindowCaptureBinding ──► capture 期 dummy metadata（与 [3] 同一 backing）          │
  └──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**图上三个必须成立的关系**：
- `[3] → [5]` 与 `[3] → [7]` 必须是**同一 backing**（I14）；这是 graph 正确性的全部内容。
- `[1] → [3]` 必须晚于"所有物理 slot 计算"（§13.1）。
- Target 路径与 `[3]` 之间**没有任何箭头**（I1）。

### 10.2 分层与职责边界

| 层 | 拥有 | 不拥有 |
| --- | --- | --- |
| Config/Policy Resolver | 先解析 normalized method/target identity；处理 forced-OFF warning once；仅对 eligible ON 路径做 `W>0`/`W≥K`、`effective_window` 与 capability 校验 | 窗口数学；不得让 forced-OFF method 进入任何数值校验 |
| ModelRunner / BlockTables | full request state、authoritative 表、`num_blocks`、Target 执行 | 任何 window 逻辑 |
| Speculator（实例） | `DraftWindowPlanner`、`Workspace`、view 的产生/传递、lane 归属、method timing | 复制窗口数学 |
| Draft-only metadata 入口 | 按 gid 选择 read 输入；**不**决定 timing、**不**算 S、**不**写 workspace | 接收 Target 调用 |
| Backend（builder/provider） | 自己的派生状态（SFA top-k、DSA indices、DCP local）在**同一坐标系**下重建 | 决定 method 是否支持窗口 |
| Graph Manager | capture binding、update/replay 时序、retire event | 从 method 名推断窗口语义 |

---

## 11. Common Sliding Window Infrastructure

### 11.1 组件清单

| 组件 | 形态 | 职责 |
| --- | --- | --- |
| `DraftWindowPolicy` | 纯值对象 | `support ∈ {FOLLOW_CONFIG, FORCE_OFF_WITH_WARNING, NOT_APPLICABLE, FACTORY_ERROR}`；forced-OFF reason；`timing ∈ {AR_PROPOSAL, PARALLEL_QUERY_READY}`、`future_offset` 来源（仅 FOLLOW_CONFIG+ON 有效） |
| `DraftWindowMath` | 纯函数（无 tensor） | `align`、`S`、`visible`、`needed_g`、`C_g`、合法域断言 |
| `DraftWindowLayout` | 每 consumer group 的只读描述 | `span_g`（table 列 token span）、`B_g`、row width、`C_g`、padding inert 值、`valid_num_blocks` 取法、CP/SP projection capability |
| `FullDraftKVSource` | 只读**描述**（不是固定 pointer） | tables_by_gid、`L`、`U`、`CPU exact?`、`valid_num_blocks`、ordered req ids、`idx_mapping`、source generation |
| `DraftWindowPlanner` | 纯函数 | 由 source 生成 `DraftWindowPlan`（§11.2） |
| `DraftWindowWorkspace` | speculator-owned + persistent | 分配、materialize、清理、epoch/lease、返回 view |
| `DraftAttentionView` | immutable（Python 层）**描述** | per-gid 的 read 输入；**不含** positions / slot_mapping / query_start_loc |
| `DraftWindowCaptureBinding` | 由 speculator/graph manager 持有 | 让入口 3 的 dummy metadata 使用与 runtime **同一 backing** |

> 说明：`DraftAttentionView` 的 `frozen` 只冻结 Python 字段，**不冻结 tensor**。因此文档统一称它为"**borrowed mutable storage, single writer**"，而不是"只读对象"。 [D]

### 11.2 窗口数学（最终版）

```text
输入：L（full exact, device）、U（apply-time CPU upper, U ≥ L）、W、K、A、各 g 的 span_g

# (1) 对齐单位 A：见 §16.2 的三支规则（默认 A = B_legacy）
# (2) 冻结起点（proposal 级）
D  = max(L + K - W, 0)
S  = floor(D / A) * A                      # 每个 request 各自一行；proposal 内冻结
# (3) 长度
window_exact = L - S
window_upper = clamp(U - S, min=window_exact, max=needed_g_max * span_g)
# (4) 每组列映射
start_col_g = S / span_g                   # 整数：由 A % span_g == 0 保证
needed_g    = ceil(window_exact / span_g)
C_g         = ceil((W + A - 1) / span_g)   # 容量上界（window_exact < W + A 时成立，见 §16.3）
```

**[M] 两个必须标注的性质**：

1. **可见长度会超过 `W`**：`window_exact ∈ [W - K, W - K + A)`。当 `K=0` 时即 `[W, W + A)`。这是 MRV1 的既有语义（`max_cols = ceil(W/b)+1`），不是回归。
2. **`visible_len` 可以为负，条件是 `K - W ≥ B - (L mod B)`**（推导见 §16.4）。这不等于 `W < K`。

### 11.3 Visibility Domain 与 consumer group 集合

- **一个 proposal = 一个 domain**（默认）[D]。理由：DSA 的 request-level metadata 与 SFA 的 top-k 索引存在跨 group/跨 layer 共享（`dsa_v1.py:349-351` 的 `cache_group_key` 注释 [V]；`sfa_v1.py:703-706` 的 per-draft-index state [V]），拆 domain 必须逐 backend 证明隔离。
- **`window_consumer_group_ids` 是 `draft_attn_group_ids` 的超集**：凡"其派生状态依赖窗口可见性"的 group 都必须在集合内（典型是 SFA 的 indexer 组）。 [D，采纳 Codex v2 D16]
- **非 consumer group 显式为 `None`**，view 用 **global gid** keyed；不得用 dense draft index 猜 global gid。 [D]

### 11.4 共享与不共享（防止第 4 份"半套 adapter"）

| 职责 | 共享 | method-specific |
| --- | --- | --- |
| 窗口数学 / `align` / 容量 / 合法域 | ✅ | ❌ |
| per-group 表物化与清理 | ✅ | ❌ |
| persistent buffer 与 lane/lease | ✅ | ❌ |
| capture binding 契约 | ✅ | 提供 phase/step/lane |
| method policy / timing / `K` 来源 | 公共 registry | method 提供 capability |
| query layout / positions / physical slot | ❌（保持既有实现） | ✅ |
| backend 派生可见性（SFA top-k / DSA indices / DCP local） | 公共协议 | ✅ backend 实现 |

---

## 12. Method-specific Integration

所有 method flow 之前先执行 §22 的 policy resolver。MTP 与 `DeepSeek-V4 target + DSpark` 命中 `FORCE_OFF_WITH_WARNING` 后直接走现行 Window-OFF baseline；以下 ON 流程对它们不可达。

### 12.1 AR（Eagle / Eagle3）

Eagle3 严格跟随配置开关：`W is None` 时不重建 first-pass metadata、不创建 planner/workspace，完全走当前 baseline；只有显式配置 `W` 且通过 §22 数值及 capability gates 后，才执行下列 ON 流程。plain Eagle 保留 §9.2 的既有 E2 决策，本次策略不扩大其产品支持面。

```text
Target fwd ─► prepare_prefill_inputs ─► [L0 = draft device seq_lens（未扣 rejection，§12.3）]
   ├─ optional PCP/global gather
   ├─ full positions / full slots / full seq state 定型
   ├─ planner.begin_ar_proposal(L0, K)  ⇒ S 冻结
   ├─ Window ON：用 Target 本轮 query layout + Draft read view **新建** draft metadata
   │  Window OFF：原样复用 Target metadata（零回归路径）
   ├─ draft first forward → 采样 token 0
   └─ for s = 1..K-1:
        compute_slot_mappings(full authoritative)
        refresh(step=s, L_s, U_s, 同一 S)        # 全量重写，不增量
        build_draft_attn_metadata(view)
        draft forward
```

**first-pass 重建的硬约束（I1 的落地）**：重建出的 metadata 必须与 Target 本轮在下列字段上**逐位等价**，只允许 read table 与同-origin length 不同 [D，三份材料一致]：

```text
query_start_loc / query_start_loc_cpu(NumPy 源)
num_tokens / num_input_tokens / actual 与 padded 的 num_reqs
is_prefilling
metadata-builder 使用的 positions
slot_mapping
rejected-tail padding
active layer mapping
```
理由 [V]：上游 AR propose 明确说首步复用 Target metadata 的原因是"把每个请求的 query 长度补齐到包含 rejected positions，从而 shape 与 KV layout 一致"（`vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:233-238,306-322`）。若重建时用"扣掉 rejected 的紧缩 draft query shape"，会静默改变算子输入。

**FULL merged decode**：必须有 **per-step** 的 capture-stable device window length（或等价的图内更新）。现有实现只为 FULL 准备了 per-step **CPU** buffer（`worker/v2/spec_decode/autoregressive/speculator.py:103-109` 的 `draft_seq_lens_cpus`），device `seq_lens` 是在图内被逐 step 推进的（上游 `:954-964`）[V] ⇒ 单份 device window length 会让整段 merged graph 读到同一静态值。

### 12.2 Parallel（DFlash / DSpark / DFlash2）

`DeepSeek-V4 target + DSpark` 不进入本节 ON 流程：配置了 Window 时 warning once 并强制 OFF。其余 parallel method/model 严格 follow-config；OFF 走 baseline，ON 才在不放宽任何 backend/graph/runtime gate 的前提下执行：

```text
Target hidden states
  ├─ for each consumer gid: prepare_dflash_inputs(full table, absolute positions)
  │      ⇒ full context/query positions 与 physical slots 定型
  ├─ precompute_and_store_context_kv(full slots)
  ├─ full device exact length 定型（kernel 写出）
  ├─ planner.begin_parallel_proposal(K=0)
  ├─ materialize consumer group views
  ├─ backend derived visibility（DSpark: DSA indices / SFA top-k）
  └─ build_draft_attn_metadata(view) → eager forward 或 FULL replay
```

**顺序约束**：窗口物化**不得早于** `prepare_dflash_inputs`——该 kernel 读 full gathered table 计算真实 query/context slots（`vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:375-409` [V]）。

### 12.3 AR 的 `L0` 取值（决定 anchor）

[V] `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:700-770` 的 prefill kernel：`seq_len = load(seq_lens)` 在 `query_len -= num_rejected` **之前**读出并原样写入 draft 缓冲 ⇒ **`L0` = Target 本轮 device `seq_lens`（未扣 rejection）**。这与 MRV1 在 apply 时点取的值一致（MRV1 的 `seq_lens` 即 target 的）。

后续 step 的 `L_s = (L0 - r) + s`（`r` = 本轮被拒数）。因此：
```text
horizon   = L0 + K                       # proposal 内恒定
step s:  future_offset_s = horizon - L_s # 从 K+r-1 递减；不是常数 K
```
只要用 `horizon` 表达，`S` 对全 proposal 恒定（I6 的落地形式）。 [D]

---

## 13. Runtime Data Flow

### 13.1 Timing bracket（每个 method 各一次）

| Family | **最早**（不得早于） | **最晚**（不得晚于） |
| --- | --- | --- |
| AR first pass | Target 本轮 query layout / full slots 定型之后；PCP 的 re-gather 之后（`autoregressive/speculator.py:329-332` [V]） | 进入 draft metadata 构建之前 |
| AR later step | 该 step 的 `compute_slot_mappings()` 完成之后 | 该 step 的 metadata 构建之前 |
| DFlash / eligible DSpark | **所有** consumer group 的 `prepare_dflash_inputs()` 完成之后（含 context KV 预写） | uniform metadata 构建之前；DSA/SFA 派生状态之前 |
| MTP / DeepSeek-V4+DSpark | 不存在合法 Window 边界（policy-forced OFF） | — |

### 13.2 一轮的完整时序（含 capture/replay 分支）

```text
[每次 proposal]
0. policy.resolve(W, normalized_method, target_model)：
   - W is None → OFF baseline
   - MTP / DeepSeek-V4+DSpark → warning once + forced OFF baseline
   - Eagle3 / 其他 eligible parallel → FOLLOW_CONFIG；继续 ON 校验
   forced-OFF 分支到此返回，绝不执行数值校验/planner/workspace
1. SchedulerOutput → ModelRunner 更新 full state（authoritative 表、num_blocks）
2. Target prepare_inputs / prepare_attn（gather + full slot mapping）
3. Target forward / verification（full）
4. speculator.propose()：eligible method full-state 准备（§12）
5. planner：S / visible / needed_g（proposal 级一次）
6. workspace.refresh(epoch)：从 full source 全量重写（§15.3 的掩码规则）
7. seal view(epoch)
8. Window ON  → 入口 1 构建 Draft metadata
   Window OFF → 现行路径（AR 复用 Target metadata / DFlash/DSpark 现行 wrapper）
9. eager：draft forward；FULL：graph manager 在 replay 前做入口 2 的 rebuild 并等 consumer event
10. draft tokens → 下一轮 Target 验证
11. lease retire（最后的 reader + graph update + consumer event 之后）
```

---

## 14. Full State vs Draft Window View

| 数据 | 归属 | Window 可否改 | 说明 |
| --- | --- | --- | --- |
| authoritative `block_tables[g].gpu` | full | ❌ | 真实分配 |
| gathered `input_block_tables[g]` | full（但与 Target 共享） | ❌ | 只作 source |
| `slot_mappings` | full | ❌ | 真实写地址 |
| `num_blocks` | full | ❌ | **只读**，作为源有效性掩码 |
| Target metadata / 对象 identity | full | ❌ | I1 |
| `positions` / `query_start_loc` | full | ❌ | I2 |
| Draft `input_buffers.seq_lens` | Draft full（exact） | ❌（仅作 source） | 窗口长度写在独立 buffer |
| ⟶ `window_block_tables[g]` | Draft read plane | ✅（workspace 自有） | 窄表 `[R, C_g]` |
| ⟶ windowed device exact / CPU upper / start | Draft read plane | ✅ | 同 origin |
| ⟶ `dcp_local` window 长度 | Draft read plane | ✅ | prefix 差 |
| ⟶ backend 派生（SFA top-k / DSA indices） | backend 自有 persistent buffer | ✅ | 同一坐标系 |
| `DraftAttentionView` | 描述对象 | — | 引用 workspace buffer；**不含** positions/slot_mapping |

**判定 alias 的口径（I4）**：比较 **storage 区间**（`untyped_storage().data_ptr()` + `storage_offset` + `nbytes`），不得只比 tensor 的 `data_ptr()`——带 offset 的 view 可以有不同的 `data_ptr()` 而共享底层 storage。 [D，采纳 Codex v2 §6]

---

## 15. Buffer Ownership / Lifetime

### 15.1 三层生命周期

| 层 | 内容 | Owner | 释放点 |
| --- | --- | --- | --- |
| Runtime | workspace、layout、`C_g`、lane ring | speculator（实例） | runner 生命周期 |
| Capture binding | 每个 `(descriptor, lane, phase, step)` 绑定的 backing | workspace + graph manager | 与 graph 同生命周期 |
| Execution generation | 一轮 view、lane slot、retire event | workspace + graph manager | reader + update + consumer event 之后 |

### 15.2 Device buffer 规划

设 `R` = 最大请求数；`G_c` = consumer group 集合；`Lanes` = 已验证的设备执行 lane 数（首期 1，§20）。

| Buffer | dtype / shape | 生命周期 | 地址要求 |
| --- | --- | --- | --- |
| `window_block_tables[g]` | source dtype，`[R, C_g]` | speculator × lane | **capture-stable** |
| `window_seq_lens` | `int32[R]` | lane；AR 为 per-step slot | capture-stable |
| `window_start_tokens` | `int32[R]` | lane | capture-stable |
| `window_cpu_{exact,upper}`（pinned） | `int32[R]` | lane | 覆盖所有 host reader |
| `valid_num_blocks` 快照（batch order） | `int32[R]` | epoch | reader 完成前保活 |
| `dcp_local` window 长度 | `int32[R]` | lane/step | backend 需要时固定 |
| backend 派生 scratch（SFA/DSA） | backend 定义 | lane/step | capture-stable |
| AR per-step device length | `[K-1, R]` 或等价 slots | graph 生命周期 | 每 captured step 固定 |

**内存公式** [D]：

```text
table_bytes  = sizeof(t) × Lanes × Σ_{g∈G_c} ( R × C_g )
total_bytes  = table_bytes + AR step slots + backend derived + host ring + (SFA/DSA 既有 buffer)
其中 C_g = ceil((W + A - 1)/span_g)
```

**相对 v1 的改进**：窄表使 `C_g` 只随 `W`（而非 `max_model_len`）增长。例：`W=2048, A=128, span=128 ⟹ C_g=17`；`R=256, Lanes=1, int32` ⟹ 单 group ≈ 17 KiB。**禁止**按 graph descriptor 数量重复分配——不同 descriptor 捕获同一最大容量 backing 的不同 prefix 视图。 [D]

### 15.3 状态机与 epoch

```text
DISABLED ──(OFF / ignored)──► 无 workspace
CONFIGURED ──(set_attn 后 layout 可知)──► ALLOCATED（capture 前完成）
ALLOCATED ──(refresh)──► PREPARING(epoch, step) ──► SEALED(epoch, step, fingerprint)
SEALED ──(readers acquire)──► IN_FLIGHT(readers, events) ──► RETIRED ──► 可复用
```

`epoch` **至少**包含 [D，采纳 Codex v2 §7.3 的超集]：

```text
proposal_id / step_id
ordered_req_ids fingerprint      # 必须含 request identity，不能只记 idx_mapping 数字（I15）
idx_mapping snapshot
valid_num_blocks snapshot/version
source_generation
layout_version
absolute start S
descriptor / lane
```

**每 proposal 无条件新建 epoch**：runner 在同一步内会先移除 finished/preempted 再处理新增（`vllm/v1/worker/gpu/model_runner.py:1085,1152` [A→V 方向一致]），新请求可立即复用同一 persistent row ⇒ 仅靠 `idx_mapping` 数字无法识别替换。 [OQ]：具体 free-list 复用时机需在目标 checkout 上确认（§29 OQ-8）。

### 15.4 单步成本

每次 refresh **只重写 `[0, C_g)`**（`O(num_reqs_padded × Σ C_g)`），与 `max_model_len` 无关。列 `[C_g, row_width_g)` 从不写、也从不被读（所有长度被 I9 夹紧到 `needed_g × span_g ≤ C_g × span_g`）。

**不做跨 step 增量补列**：增量会破坏 I11 的幂等性（同一 step 被 live build 与 graph-manager rebuild 各触发一次时会产生歧义）。 [D，采纳 Codex v2 D07]

---

## 16. Per-KV-Cache-Group Handling

### 16.1 为什么需要 per-group

[V] `vllm/v1/worker/gpu/block_table.py:48-57` 允许每组不同的 `kernel_block_size` 与 row width（`blocks_per_kv_block` 展开）；而 Ascend 漏斗的 `seq_lens` 是**所有 group 共用**的一份（`worker/v2/attn_utils.py:294-330`）。因此：

- 表可以（必须）per-group；
- 长度**不能**per-group（否则违反现有漏斗契约，且让同一 draft 的不同 layer 看到不同历史长度）。

⇒ **必须让"窗口起点"与"组"解耦：`S` 全组一致，per-group 只体现在列映射**。这正是 §16.2 要解决的问题。

### 16.2 对齐单位 `A` 的三支规则（**本设计最关键的一处修正**）

MRV1 的锚是 `B_legacy` = **第一个** draft attention layer 的 `kernel_block_size`（`llm_base_proposer.py:406-408,446-452` [V]）。对多 group：

```text
规则 1（默认，兼容路径）：
    若 ∀g ∈ G_c, span_g | B_legacy   ⟹   A := B_legacy
    ⇒ 与 MRV1 的 start 逐位相同 ⇒ 无任何语义变化（含 "窗口比一个 block 还小" 的既有行为，
      即有效可见历史退化为一个 B_legacy 块：这是 MRV1 已继承的性质，不是新偏差）。

规则 2（非整除时的唯一候选，需显式批准）：
    若存在 span_g 不整除 B_legacy，则能整除**全部** span 的最小 A 是 lcm{span_g}，
    而 lcm ≥ 任一 span ⇒ 此时必有 A > B_legacy（因为 B_legacy 不是公共倍数）。
    ⇒ 窗口的 overshoot 上界从 "B_legacy - 1" 变成 "lcm - 1"，并可能超过 W（见下反例）。
    ⇒ 必须标注为「可见历史变宽的 Feature 语义变更」，附 acceptance/质量实测对比；
      不得称之为向后兼容。默认**不启用**。

规则 3（默认行为）：
    不满足规则 1、又未获规则 2 的批准  ⟹  **fail closed**，
    报错信息须包含 "unsupported group geometry"、具体的 span_g 与 B_legacy 值。

统一断言：A ≤ B_legacy      # 规则 1 自动满足；不满足即说明走到了规则 2/3
```

**[M] 为什么不能默认取 lcm（反例，来自 GPT v2 §6.2，我独立复算通过）**：

```text
L = 300, W = 128, K = 0, B_legacy = 64, span_other = 48
legacy:  S = align_64(172)  = 128  ⇒ visible = 172     （MRV1 行为）
lcm:     A = lcm(64,48) = 192
         S = align_192(172) = 0    ⇒ visible = 300     ← 窗口被放大到几乎失效
```
注意 `A = 192 > W = 128`：当对齐单位超过窗口尺寸时，`S` 只能取 0 或 A，而 A > D = 172 ⇒ 直接掉到 0。

**[M] 通用条件**：`visible = L - S ∈ [W - K, W - K + A)`。因此

- `A = B_legacy`（规则 1）时，overshoot 最多 `B_legacy - 1`，与 MRV1 完全相同；
- `A = lcm > W` 时，`S` 只能在 `{0, A, 2A, …}` 中取值，而 `D = F - W < A` ⇒ **`S` 必为 0 ⇒ 窗口失效**（即上面反例的机制，与 `W` 的具体大小无关）。

⇒ 断言 `A ≤ B_legacy`；当唯一候选 A（= lcm）超过它时，走规则 2（需批准）或规则 3（fail closed）。
（本设计**不采用**"取 `min(span_g)`"：对较大 span 的组会落在块内，没有意义。Codex v2 与我 v1 的"无条件 lcm 默认"被上述反例推翻。）

### 16.3 每组容量

```text
C_g = ceil((W + A - 1) / span_g)         # [M] visible < W + A（K ≥ 0 时更小）
```
仅当 `A == span_g` 时退化为 MRV1 的 `ceil(W/b)+1`（因为 `ceil((W+B-1)/B) = ceil(W/B)`，与 MRV1 的 `ceil(W/B)+1` 差 1 列——MRV1 是保守上界，本式更紧且安全）。若 `row_width_g < C_g` ⇒ 该 group 无法窗口化 ⇒ **整个 domain fail closed**（不做"部分 group 窗口化"）。

### 16.4 合法域 `W ≥ K`（以及负 `visible_len` 的真条件）

**[M] 推导**（`L = qB + r`，`0 ≤ r < B`，`L + K - W > 0`）：
```text
S = floor((L+K-W)/B) * B
visible < 0 ⟺ S > L ⟺ K - W ≥ B - r
```
- **`W ≥ K` ⟹ `K - W ≤ 0 < B - r` ⟹ 永不出现负长度** ⇒ `W ≥ K` 是**充分**条件；
- 但 `W ≥ K` **不是必要**的：`L=100, B=64, W=3, K=4` ⇒ `S=64, visible=36 > 0`；
- 而 `W < K` **确实可以触发**：`L=63, B=64, K=2, W=1` ⇒ `S=align_64(64)=64 > 63` ⇒ `visible=-1`；更极端 `W=0, K=7, B=64, L=250 (r=58)` ⇒ `K-W=7 ≥ 6` ⇒ `visible=-6`。

**政策**：AR 在配置期要求 `W ≥ num_speculative_tokens`（并在文档中标注这是对 MRV1 的**兼容性收紧**，需 maintainer 批准，§22.2）；运行时**无条件**断言 `visible ≥ 0`（对所有 method，包括 `K=0` 的 parallel family）。 [D]

> **勘误**：我在更早两份 Review 中曾写"该条件在 `K ≤ 15`、`B ≥ 16` 下几乎不可达"，**那是错的**（把 `r = 0` 的特例外推）。正确条件即上式；两份 review 已加 Corrigendum。

### 16.5 特殊说明：`W = 0` 不是"窗口关闭"

[M] `W=0, L=250, B=64` ⇒ `S = 192`，`visible = 58` ⇒ 窗口收缩到**最后一个 block 边界**（不是"无效"也不是"全量"）。因此 `W=0` 需要显式政策（§22.2），不能当作 OFF。

---

## 17. seq_lens / CPU Upper Bound Strategy

### 17.1 长度的类型系统（**禁止一套函数盲算**）

| 类型 | 定义 | 来源 | 缺失时 |
| --- | --- | --- | --- |
| `DeviceExact` | `L` | AR：`L0 - r + s`；DFlash/DSpark：prepare kernel 用 device `num_rejected` 写出（`worker/v2/spec_decode/dflash/speculator.py:287-290` [V]） | 不可能缺失 |
| `CpuExact?` | 无 D2H 可重建的 exact | 需逐 method 证明；**当前 DFlash/DSpark 无此生产者**（`_calc_next_seq_lens_cpu` 明确不减 rejection，`autoregressive/speculator.py:815-822` [V]） | **fail closed**（若该 backend 需要） |
| `CpuUpper` | `U ≥ L` | 上游 `target_upper + step`（`spec_decode/speculator.py:326-334` [V]） | 不可缺失（I8） |
| `capacity_g` | `needed_g × span_g` | 由 `S` 与 `span_g` 派生 | 不可缺失 |
| `backend_max` | `max_seqlen_kv` 等 | 由窗口 CPU upper 派生 | — |

### 17.2 Canonical origin（修正 MRV1 的独立重算）

```text
S            由 DeviceExact 决定（唯一）
window_exact = L - S
window_upper = clamp(U - S, min=window_exact, max=capacity_g)     # 公共同一 S
```
**[M] 为什么必须用同一个 `S`**：若对 upper 独立套公式会**破坏 `upper ≥ exact`**。反例：`W=100, B=64, K=0`，`L=150 ⇒ S=align_64(50)=0 ⇒ exact'=150`；`U=200 ⇒ S'=align_64(100)=64 ⇒ upper'=136 < 150` ✗。

### 17.3 禁止 fallback（I8）

[V] 漏斗在 `seq_lens_np is None` 时用 `np.full(num_reqs, max_seq_len)`（`worker/v2/attn_utils.py:253-260`），而 Draft 的 `max_seq_len = draft_max_seq_len`（full 量级，`spec_decode/speculator.py:361`）。**窗口 ON 时**：必须同时提供 `seq_lens_np` 与 `seq_lens_cpu_upper_bound`；否则由 Draft-only 入口**直接抛错**，绝不落到该 fallback（否则会读 `[needed, C_g)` 之后的零列 ⇒ block id 0 ⇒ 读到 cache 第 0 块）。 [D]

**[M] 夹紧到 `capacity_g` 而不是 `window_exact`**：列 `[0, needed_g)` 是有效 full-table 块，所以读 `window_exact … capacity_g` 之间的额外 token 是**窗口内的真实 KV**（安全）；但**不能**超过 `capacity_g`（那是未写入列）。

### 17.4 DCP / CP local 长度

```text
local_exact_g = local_prefix(E) - local_prefix(S)          # E = window 的绝对右端（= L_s）
local_upper_g = local_prefix(U) - local_prefix(S)
```
**[M] 反例证明不能写成 `local_prefix(E - S)`**：`get_dcp_local_seq_lens`（`vllm/v1/attention/backends/utils.py:1088-1133` [V]）为
```text
local(L) = floor(floor(L/i)/d)*i + clip(L - floor(floor(L/i)/d)*d*i - rank*i, 0, i)
```
对 `L` **非线性**。取 `i=1, d=2, rank=1`：`local(4)-local(1)=2-0=2`，而 `local(3)=1` ✗。

**首期**：`cp_size > 1` 的**所有**组合 fail closed（§24.2），因为除长度外，**表列坐标也会变**：CP 下取列用 `query_pos // (block_size * CP_SIZE)`（`worker/v2/spec_decode/dflash/speculator.py:264` [V]）⇒ `span_g` 必须含 `cp_size`；且 SFA-DCP 的 replicated 视图片射假定"列号 == 逻辑块号"（`attention/context_parallel/sfa_cp.py:601-611`、`sfa_dcp_utils.py:66-80` [A]），左移表会破坏它。

---

## 18. BlockTable / SlotMapping Strategy

### 18.1 读侧：窗口表的物化规则

对每个 `(g, row)`：

```text
start_col = S[row] / span_g
needed    = ceil(window_exact[row] / span_g)
for dst_col in [0, C_g):
    src_col = start_col + dst_col
    valid = (dst_col < needed)
          and (src_col < row_width_g)
          and (src_col < valid_num_blocks[row, g])      # ← I12：源侧有效性
    out[row, dst_col] = full_g[row, src_col] if valid else INERT_g
# padded rows（row ∈ [actual_num_reqs, padded_num_reqs)）整行写 INERT_g，每步确定性重写
```
`INERT_g` 是 backend 约定的 inert 值（GQA/FIA 用 0；其它 backend 按其契约，§18.3）。

**[V] 为什么必须有 `valid_num_blocks` 这一项**：gather kernel 对 active row **只写 `[0, num_blocks)`**，不清 tail；只有 padding row 被整行清零（`vllm/v1/worker/gpu/block_table.py:251-272`）。因此"看起来有值的列"可能是上一个更长请求留下的 stale block id（可能已被回收/重新分配给别的请求）。`valid_num_blocks` 是**设备侧已有**的权威（`num_blocks` 是 `UvaBackedTensor`，`block_table.py:61`；gather 已在用 `num_blocks.gpu`，`:170-171`）⇒ **不需要新增 D2H**。取 batch order 的方式：按 `idx_mapping` gather 到小 persistent buffer（或让物化 kernel 直接索引）。

### 18.2 写侧：slot mapping 永不受影响（I3）

[V] 公共 slot kernel 读 `block_table_ptrs`，它绑定 `self.block_tables[g].gpu`（`block_table.py:93-97,190-221`；Ascend override 同源 `worker/v2/block_table.py:82-114`）。DFlash/DSpark 额外的 context/query slot 也从 **full** gathered table 生成，且发生在窗口物化**之前**（`vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:375-409`）。⇒ 窗口与写地址无关。

**禁止**：重新赋值 `BlockTables.input_block_tables`；把窗口表交给任何可能写表的 builder。若发现必须修改这些组件，先回到设计评审（§30.3）。

### 18.3 Padding 契约（**修正**：不是"block id 与 active 不相交"）

[V] `vllm_ascend/attention/attention_v1.py:340-360` 的源码注释是权威依据：

> "the dummy request points at block 0, and its output is harmless because: (1) read side: the attention output for padding tokens is trimmed … (2) write side: reshape_and_cache slices key/value/slot_mapping to `[:num_actual_tokens]` … **So any valid positive KV length / zero block row is fine.**"

⇒ 正确契约是 **"读可任意（输出被裁掉）+ 写必须为零"**，而**不是**"block id 集合与 active 不相交"（后者无源码依据，且可能没有 reserved null block 可用）。本文采纳该契约，并要求每步**确定性重写** padding 行（I13）。

| Backend | padding 事实 [V/A] | 本文契约 |
| --- | --- | --- |
| GQA/FIA | 补 `seq_len=1` + zero table row；dummy 输出被裁、不写 KV（`attention_v1.py:340-368`） | 保持；不要求 disjoint |
| MLA | graph 路径补 zero table / padding positions / slots，长度由 builder 控制 | capture/live 使用同一确定性 padding |
| DSA | `start_pos_prefill` 为 builder 自有 buffer，按 `num_actual_reqs` 清 padded（`dsa_v1.py:1088-1100`） | 必须传准确的 actual/padded 计数 |
| SFA | padding token 的 top-k 长度置 0，按 `num_actual_tokens` 屏蔽 | 表、top-k 长度与索引同时清理 |

---

## 19. Graph Capture / Replay

### 19.1 三个入口必须同时覆盖（§7.2）

原设计与后续材料都出现过"只修 live"的错误。本文把"入口 3（capture 期 dummy metadata）"列为**一级设计对象**。

### 19.2 为什么"同 shape"不够（**修正**）

**[M/D]** 若 capture 期绑定地址 A（共享 full dummy 表），replay 期提供地址 B（workspace 表），则：

- 对 **GQA/FIA**：`block_table` 是注册在 `register_task` kwargs 里的参数（`attention/attention_v1.py:652-660` [V]）⇒ 可在 update 时**换指针**，只要 shape 兼容；
- 对 **MLA**：走 legacy `update_graph_params`，实现用本轮 metadata 的 `decode.block_table` 重建算子参数 [A] ⇒ 也可换指针；
- 对 **SFA/DSA**：`update_graph_params()` 是 `pass`（`sfa_v1.py:885-897`、`dsa_v1.py:1619-1631` [V]），且 DSA 的 op **在 capture 时捕获 `ori_sparse_indices` 的 data pointer**（`dsa_v1.py:420-436` [V]）⇒ **换指针无效**，captured op 永远读 capture 期那块 storage。

⇒ **正确条件是"capture 与 replay 使用同一 backing"**，而不是"shape 相同"。

### 19.3 Capture binding（最终方案）

```text
Window ON:
  · workspace 在 capture 之前完成分配（set_attn 之后，§15.3）
  · capture 期的 dummy metadata 由 **Ascend-local window-aware capture helper** 构造，
    table/length 取自 workspace 的同一 backing（内容为确定性 inert/padding 值）
  · live / replay-rebuild / capture 三者引用同一 backing
  · 逐 (descriptor, lane, phase, step, gid) 记录并比对签名：
        (data_ptr, shape, stride, dtype)          # storage_offset 仅作诊断（prefix slice 恒为 0）
  · 不通过 module-global 新 monkeypatch / ContextVar / _EXTRA_CTX 字段运输 view
Window OFF:
  · 完整 delegate 现有 capture 路径（`DFlashAclGraphManager.capture()` / AR 的 `prepare_inputs_to_capture`）
```

**可行性路径** [V]：DFlash 的 capture 入口符号已在导入期被 Ascend 重绑定（`vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26`：`cudagraph_module.build_attn_metadata = build_attn_metadata`），Ascend 可以在此基础上替换为 window-aware 版本；AR 侧的 capture 助手调用点在 **Ascend 代码**内（`worker/v2/spec_decode/autoregressive/aclgraph.py:111` 调 `prepare_inputs_to_capture`，其内部走 Ascend 的 `model_states/default.py`），因此 Ascend 可在自己的层做显式 plumbing。两处都**不需要修改上游仓库**。 [OQ]：具体改造点与"目标 capture helper 是否能拿到 speculator 实例"需在实现前 spike 确认（§29 OQ-1）。

**注意 FIA 的一个细节** [V]：`attention_v1.py:365-368` 在需要补 dummy request 时会对 `block_table` 做 `torch.cat`（**产生新 tensor**）。这对 GQA 无害（该参数可重绑），但对 no-op backend **绝不允许**——它们必须是 slice/copy 语义。审计时按 backend 逐一确认。

### 19.4 `max_seq_len` 的语义拆分（**采纳 Codex v2 §11.5**）

| 概念 | 用途 | capture/replay 关系 |
| --- | --- | --- |
| `capture_capacity_max_seq_len` | capture 期容量/workspace | capture 与 replay **相同** |
| `runtime_window_exact_max` | 运行时窗口 exact 上界 | 每 step 可变 |
| `runtime_window_upper_max` | 运行时 upper 上界 | 每 step 可变 |
| `backend_effective_max_seqlen_kv` | backend plan/tiling | 由窗口 upper 派生 |

**[V] 现状**：capture 传 `max_model_len`（`dflash/cudagraph.py:64`；Ascend `model_states/default.py` 的 `max_seq_len=self.max_model_len`），replay 传 `self.draft_max_seq_len`（`spec_decode/speculator.py:361`）。⇒ **两者本来就不同**，不能用一个变量混合表达。**本文不承诺**通过缩小 `max_seq_len` 获得 kernel 侧收益；若某 backend 的 tiling 不消费窗口 upper，必须显式记录"该 backend 无 tiling 收益"，而不是谎称已缩小。

### 19.5 Eager / PIECEWISE / FULL

| Family / mode | 规则 |
| --- | --- |
| eager | materialize 后直接 build；仍使用 persistent workspace |
| AR PIECEWISE | capture 期仍会构建 metadata 且部分 attention-like op 真实执行（`cudagraph_utils.py` 注释约 `:793-818` [A]）⇒ **capture 与每个 piece replay 都必须拿到有效 view** |
| AR FULL prefill | Window ON：用 Target 本轮 query layout + Draft capture view；OFF：沿用 Target dummy metadata |
| AR FULL decode（merged） | `S` 固定；**每 step 必须有独立的 device length slot**（§12.1） |
| eligible DFlash/DSpark FULL | live / capture / replay-rebuild 使用同一 binding；当前无 PIECEWISE [V] |
| DFlash2 | 仅 eager [V] |

### 19.6 update / replay 的设备时序（**采纳 Codex v2 §11.6，配本文 T9 验证**）

```text
main stream: materialize window buffers
update_stream: wait(producer)
main stream: submit replay
captured ExternalEvent.wait: 阻塞 replay 的 consumer
update_stream: 安装 graph task 参数并 record event
replay 被解锁并读取 window buffers
main stream: record consumer-complete event
→ release lease
```
**[V] 依据与风险**：`compilation/acl_graph.py:292-320` 显示 update 与 replay 的先后**取决于 `enable_enpu`**；且注释明确 async/MT 下"iteration i 的 update 可能早于 iteration i-1 的 replay"并需要 `synchronize`；**FULL + EAGLE merge 路径不需要该 barrier**。因此该协议是**待验证的假设**，必须用"**A/B 两组完全不同 window origin 连续 replay**"实验排除 one-step lag（§25 T9）。 [OQ]

---

## 20. Async Safety

### 20.1 已核实的并发事实 [V]

| 事实 | 证据 |
| --- | --- |
| MRV2 + async ⇒ `max_concurrent_batches = pp_size + 1 ≥ 2` | `vllm/config/vllm.py:589-598` |
| UVA pool 深度由该值设定；复用前要求 GPU reader retire | `vllm/v1/worker/gpu/buffer_utils.py:24,19,61` |
| 现有 `input_block_tables` / `slot_mappings` 是**单份** persistent buffer 且已被 MRV2 正常使用 | §7.1 |

**结论**：**host 侧重叠是既定事实**（CPU metadata 可能提前准备）；**device 侧是否并行执行两个 draft proposal 未被静态源码证明**。 [D]

### 20.2 两级策略（采纳 Codex v2 §12.2 的更保守版本）

```text
Host staging ring:  depth ≥ max_concurrent_batches        # 必须
Device workspace:   首期 1 个 slot，前提是全部满足：
   (a) materialize 与 consumer 在同一 main stream，或有显式 event 排序；
   (b) debug 断言：上一 epoch 的 consumer-complete event 已 fire 才允许 refresh；
   (c) 下一 host epoch 只能准备到 host ring，不得提前覆盖 device slot。
若 runtime trace 证明存在多个 device lane（[OQ]）：
   每 lane 独立 workspace；每 lane 的图必须 capture 该 lane 的地址（或 backend 支持 pointer update）；
   未完成 lane-specific capture 前 fail fast，不得 round-robin 到未 capture 的地址。
```
> 相对我 v1 的"device lane 深度 = max_concurrent_batches"：这里改为**先证明、后扩展**——因为"host 重叠"与"device 并行"是两件事，而现有单份 `input_block_tables` 能正常工作说明 device 侧至少在当前配置下是串行的。 [D]

### 20.3 Lease（I16）

释放条件（三者**全部**满足）：最后一个 metadata reader + graph task update + device consumer completion event。**不得**以"replay 已提交"作为释放条件（`autoregressive/aclgraph.py` / `dflash/aclgraph.py` 的路径都可能把 update 排在 replay 之后 [V, §19.6]）。

### 20.4 禁止的隐式运输 [D]

module-global 可变状态、`build_attn_metadata_wrapper()` 之上再叠一层 monkeypatch、`_EXTRA_CTX` 新字段、thread-local、ContextVar —— 全部禁止用于运输 view。**理由** [V]：`_EXTRA_CTX` 在部分路径直到 model forward 才设置 draft flag（`worker/v2/spec_decode/autoregressive/aclgraph.py:179-180`），早于 forward 的 metadata build 无法可靠读取；且隐式状态无法保证 async 隔离。

---

## 21. Native SWA Interaction

### 21.1 三种表达方式是不同的 [V]

| Native 约束载体 | 证据 |
| --- | --- |
| GQA/FIA band：`sparse_mode=4 / pre_tokens=sliding_window / next_tokens=0`；draft 层仍传 block_table | `attention/attention_v1.py:602-604`、`:459-472` |
| DSA：`build_dspark_swa_indices` 用 `hf_config.sliding_window` 派生 `start_pos`；`dsa_v1.py:1107` 直接做 `hf_config.sliding_window - 1`（**无 None 检查** ⇒ 该路径必然存在 native window） | `attention/dsa_v1.py:410,449-461,1107,1108-1125` |
| SFA：**native window 参数被关闭**：`ori_mask_mode=0`、`ori_win_left=ori_win_right=-1`，注释"Only ori_mask_mode 4 may carry a bounded window on this product line"；可见性来自 top-k | `attention/sfa_v1.py:114-119`、`:198-219` |

### 21.2 组合语义：以"rebase 后自然求交"为默认（**修正**）

**[M] 结论**：把表与长度**一起** rebase 到窗口坐标系后，native 选择器在**相对坐标**里执行，其结果自动等于交集：

```text
设绝对窗口起点 S，rebase 后：table' 的列 0 = 绝对 S；长度 L' = L - S
DSA 的生成器：prefix' = L' - q = (L - q) - S
             start_pos' = max(prefix' - native_W, 0)
             absolute   = S + start_pos' = max(S, prefix - native_W)   ← 交集 ✓
```
因此**不需要**、而且**不应该**再把绝对 `S` clamp 进 relative start（那会重复应用 origin）。 [D，采纳 Codex v2 R-17；我 v1 的"只裁表无效、必须 clamp 绝对 start"是错误的]

**但必须设一道审计 gate（[OQ]）**：DSA 路径上是否还有别的派生状态把**绝对 positions** 与（已 rebase 的）表混用？候选：`compressor`（C4/C128 压缩 KV 的 slot/table，`dsa_v1.py:884-890` 注释提到 "C4/C128 physical slots are generated later from the logical block table by compressor_metadata"）、`QLI`、`SAS` metadata、以及 `start_pos_prefill` 的绝对值语义。**审计通过前，DSA 组合保持 E2（不启用）**。

**SFA 是唯一需要额外输入的 backend**：其 top-k 长度由**绝对 positions** 派生（`indexer.get_topk_lengths(positions) = (positions+1).clamp(max=topk_tokens)`，`attention/indexer.py` 附近 [A]），而 positions 必须保持绝对（RoPE）⇒ 必须**额外**传入 `window_relative_visible_count`（或等价量），并在自己的 `block_table_buffer` 里完成表映射（[V] `sfa_v1.py:296-307` 每次 build 都复制进自有 buffer）。审计/实现完成前 SFA 组合不启用。

### 21.3 不能用 acceptance 变化代替正确性

正确性判据必须是**集合级**：最终可见的绝对 KV 集合 `= 窗口集合 ∩ native 集合 ∩ 物理保留集合`（§25 T11）。acceptance 只作质量指标。 [D，三份材料一致]

### 21.4 物理保留上限（**本文新增，I21**）

[V] `vllm/config/vllm.py:602-609`（`max_in_flight_tokens` 的注释原文）：

> "**Recycling-aware KV cache specs (sliding-window, chunked-local)** reserve for this because **out-of-window blocks are freed** on the processed-token basis, so in-flight steps transiently keep their blocks."

配合 `vllm/v1/kv_cache_interface.py:811`（`SlidingWindowSpec`）、`:909`（`SlidingWindowMLASpec`）、`:1316`（recycling 注释）与 Ascend 的 `vllm_ascend/core/kv_cache_interface.py:236`（`AscendSlidingWindowMLASpec`）⇒ **若某 consumer group 的 KV spec 是 recycling 类型，窗口外的块会被物理释放，比它更大的 `draft_window_size` 无法恢复不存在的 KV**。

```text
effective_window_g = min(W, spec_retention_g)
```
配置期必须校验/告警；`W > retention` 时窗口"设了也无效"必须显式告知用户。 [OQ]：目标模型的 consumer group 是否使用 recycling spec，需枚举（§29 OQ-5）。

---

## 22. Config / Validation / Warning Policy

### 22.1 解析顺序

```text
读取 AscendConfig.draft_window_size
  → W is None：OFF baseline，立即返回（§27）
  → normalize method semantics + target model identity（不按 concrete class）
  → MTP：warning once（draft 与主模型一起训练）+ 强制 OFF，立即返回
  → DSpark + DeepSeek-V4 target：warning once（draft 与主模型一起训练）+ 强制 OFF，立即返回
  → Eagle3 / 其他 eligible parallel：FOLLOW_CONFIG，继续 ON 路径
  # 上述 forced-OFF 返回早于 W 数值校验、layout/capability inventory、planner/workspace
  → 校验 W 数值域
  → set_attn 之后：枚举 consumer groups 与 layout（span_g / row_width / spec retention）
  → 计算 A（§16.2 三支规则）与 C_g
  → 校验各能力（backend 可见性表达、graph mode、CP、CPU length 可得性）
  → 分配 workspace，或 fail closed 并给出明确原因
```

### 22.2 参数校验

| 输入 | 处理 | 依据/状态 |
| --- | --- | --- |
| `None` | OFF baseline；不 warning，不进入 method capability | [V] |
| 非 None + MTP | warning once + 强制 OFF；**不检查该 W 的数值** | maintainer 2026-10-09 |
| 非 None + DSpark + DeepSeek-V4 target | warning once + 强制 OFF；**不检查该 W 的数值** | maintainer 2026-10-09 |
| eligible method 的 `W > 0` | 进入 method/capability 检查 | — |
| eligible AR：`W ≥ num_speculative_tokens` | **要求**（兼容性收紧，需 maintainer 批准） | [M] §16.4；[OQ] §29 OQ-3 |
| eligible parallel（`K=0`） | 无额外 `W ≥ K` 约束，但运行时断言 `visible ≥ 0` | [M] |
| eligible method 的 `W ≤ 0` | **建议配置错误**（兼容性收紧，需批准）；不静默继承 MRV1 未定义行为 | [V] `ascend_config.py:497`；[OQ] §29 OQ-3 |
| `A` 不可得 / `row_width_g < C_g` / 任一 consumer group 不支持 | **整个 domain fail closed**（不做部分 group 窗口化） | [D] |
| `W > spec_retention_g` | 告警并**显式记录该上限**（I21） | [V] §21.4 |

### 22.3 method policy（唯一一处允许出现 model_type 镜像）

| method（normalized） | 行为 |
| --- | --- |
| `dflash` / DFlash2 | 严格 follow-config；ON 按 capability 启用（§9.2），DFlash2 不改变 eager-only 约束 |
| `dspark` + 非 `deepseek_v4*` target | 严格 follow-config；ON 按 capability 启用（§9.2） |
| `eagle3` | 严格 follow-config；OFF baseline，ON 按 E2 gates；Window 开关本身不得绕过或预先判定 backend 支持 |
| `eagle` | 保留既有 E2/capability 决策；本次策略不扩张公开支持面 |
| `mtp` 全部变体 | 配置 Window 时 **warning once + 强制 OFF**，原因是 draft 与主模型一起训练；判定必须在任何数值校验、class/backend 分支、planner/workspace 之前（否则 `use_eagle()` 兜底会误启用） |
| `dspark` + `deepseek_v4*` target | 配置 Window 时 **warning once + 强制 OFF**，原因是 draft 与主模型一起训练；读取 **target** `model_type.startswith("deepseek_v4")`（`llm_base_proposer.py:420-422` [V]），并在任何数值校验、inventory、planner/workspace 前返回 |
| `extract_hidden_states` | 不适用（无独立 draft attention read plane） |
| factory 不支持的方法 | **保持 `NotImplementedError`**；policy 不得抢先吞掉错误（`worker/v2/spec_decode/__init__.py:72` [V]） |

上述两个 forced-OFF 分支是已冻结产品策略，不是 capability downgrade，也不是 Open Question；不能通过关闭某个 backend gate把它们重新开启。warning 必须按 engine/speculator 实例去重，并包含“draft 与主模型一起训练，因此忽略 `draft_window_size`、Window 已强制关闭”的原因。

### 22.4 关于 MRV1 "静默未读取" 的处理（**撤回 v1 的行为升级**）

MRV1 对 ngram/suffix/medusa/extract 是**静默未读取**（不经过 base proposer）。我 v1 曾提议在 MRV2 改成"warning + ignore"。**本设计撤回该提议**：这是用户可见的行为变更，不属本 feature；是否统一化应由 maintainer 单独立项。 [D]

---

## 23. Error Handling

**总原则：fail closed，且错误信息必须指出"哪个 group/哪个能力/为什么"**（便于长期维护与用户自助）。

| 条件 | 行为 | 触发点 |
| --- | --- | --- |
| `A` 不满足 §16.2 规则 1 | 启动期报错（"unsupported group geometry: span_g=… 不整除 B_legacy=…"） | 配置解析 |
| `visible_len < 0` | 运行时断言失败（不 clamp、不静默） | planner |
| 必需 CPU length 缺失且 backend 需要它 | 启动或运行时**抛错**，禁止 `np.full(max_seq_len)` fallback | Draft-only 入口 |
| workspace 与 full storage **区间重叠** | debug/assert 模式抛错 | materialize |
| `epoch`/`generation` 不匹配（跨代复用） | assert 抛错 | view acquire |
| 未声明能力的 backend / graph mode / CP 组合 | 启动期报错并列出缺失 capability | capability 解析 |
| no-op updater backend 且未完成 capture binding | **拒绝 FULL**（可退化为 eager，但必须显式告知） | graph 初始化 |
| Target build 收到 `DraftAttentionView` | assert 抛错（类型/签名层面本应不可能，§10.1 I1） | Draft-only 入口的反向检查 |
| 非 consumer group 被要求窗口化 | 启动期报错（不要静默忽略） | capability 解析 |
| `W > spec_retention_g` | **warning**（不报错），并记录 effective window | 配置解析 |
| MTP / DeepSeek-V4+DSpark | warning once + policy-forced OFF；不运行本表其它 Window error check | policy resolver（最早） |
| 不可实例化 method | 原样抛 factory error | factory |

---

## 24. Week4 Feature Extension

### 24.1 Flashcomm

- **已核实**：Flashcomm 在 Ascend 上是 **SP-MoE 开关**（`ascend_config.py:639-657` 注释 "FlashComm remains the SP MoE switch on Ascend"），`enable_sp()` 返回 `use_sequence_parallel_moe`（`utils.py:916-928`），且在 SFA 中只被赋值一次、之后无布局用途（`attention/sfa_v1.py:869`）[V] ⇒ **对窗口 read plane 近似正交**。
- **结论（措辞修正）**：不得写"Flashcomm 无需处理"；应写"**控制面近似正交；Flashcomm + SP + DSA-CP 的数据面未验证**"。首期该组合 fail closed。
- **扩展点**：不建立 `FlashcommWindowLayoutProvider`；改为通用 `ParallelWindowProjector`（§24.2），Flashcomm 只作为通信/event 生命周期与性能测试维度。

### 24.2 SP / DSA-CP / DCP

```text
project_interval(layout, S, E, rank)     → 该 rank 的可见子区间
derive_local_lengths(...)                → local_prefix(E) - local_prefix(S)（§17.4）
derive_sparse_indices(...)               → 该 rank 的索引/plan（与表同一坐标系）
bind_capture_buffers(...)                → capture binding
```
- **[V]** CP 会改变表列坐标（`span_g` 含 `cp_size`，§17.4）与 replicated 视图片射假设（SFA-DCP）⇒ **不能假设"公共 T1 自动覆盖 CP"**。
- **首期**：所有 `cp_size > 1` 组合 fail closed。
- **capability flags**：`supports_dcp_interval_projection`、`supports_dsa_cp_token_projection`、`supports_pcp_replicated_layout`、`supports_sp_token_sharding`、`supports_full_graph`、`supports_async_device_lanes`。

### 24.3 Async Scheduling

- host ring 深度已参数化（§20.2）；
- **不改变窗口数学**：更深的并发只需扩大 ring 与 event 管理；
- **[OQ]** 真实 device lane 数需 runtime trace（§29 OQ-2）。

---

## 25. Testing Matrix

> 原则：**先数学与数据不变式，再 method/graph，最后 E2E/性能**。任何 graph E2E 都不能替代数据单测；**错误必须能被负向测试捕获**。

### 25.1 数学与合法域

| ID | 目标 | 关键用例 | 通过判据 |
| --- | --- | --- | --- |
| T1 | MRV1 对拍 | 同一输入的 MRV1 `SlidingWindowAdapter` vs `DraftWindowMath`；`L∈{<W,=W,超W,恰好对齐,不对齐}`、`span∈{16,32,64,128}` | `S`/`visible`/`start_col_g`/`needed_g` 逐位一致 |
| T2 | 对齐规则 | `B_legacy=64, span=64`（嵌套，A=64）；`B_legacy=64, span=48`（非嵌套） | 嵌套时 A=64 且与 MRV1 逐位相同；**非嵌套时 fail closed**（不得取 lcm=192 而把 visible 从 172 变 300） |
| T3 | 容量 | property：`C_g ≥ ceil(window_exact/span_g)` 对全部随机 `L,W,K,A` | 无越界；`C_g = ceil((W+A-1)/span_g)` |
| T4 | eligible ON 路径合法域 | `W∈{0,-1,1}`,`K∈{1,2,4,7,15}`，构造 `L mod B = B-1`（**必含 `L=63,B=64,K=2,W=1` 与 `L=100,B=16,W=1,K=20`**） | 配置期拒绝 `W<K`（eligible AR）；运行时 `visible<0` 断言触发；forced-OFF method 不运行本测试逻辑 |
| T5 | `W=0` 语义 | `L=250,B=64,W=0,K=0` | `S=192, visible=58`（**不是**"OFF"、**不是**"无效"） |
| T6 | exact/upper 同 origin | 反例集：`L=150,U=200,W=100,B=64` | 同一 `S`；`upper' ≥ exact'`；`upper' ≤ capacity_g` |

### 25.2 隔离与数据不变式

| ID | 目标 | 输入/场景 | 通过判据 |
| --- | --- | --- | --- |
| T7 | Full 状态逐位不变 | — | authoritative 表、gathered 表、`slot_mappings`、Target metadata（identity + 内容）在窗口物化前后逐位相同 |
| T8 | **无 alias** | — | workspace 与 full/`slot_mappings` 的 **storage 区间不重叠**（含带 offset 的 view 情形） |
| T9 | positions 不变 | — | 物化前后 `positions` 逐位与 `data_ptr` 不变；且 builder 收到的 positions == model.forward 的 positions |
| T10 | 幂等 | — | 同 `(epoch, step)` 调 N 次结果逐位相同；把 view 当 source 抛错；连续 100 次变化长度后等于"从 full 重算" |
| T11 | 源有效性(stale) | active row 的 `[num_blocks, row_width)` 预填"看起来有效"的 block id | 窗口表内该列写 inert，**不复制** stale；8→3 缩小后 padded 行确定性清零 |
| T12 | 同组不同 row | 同一 group 内不同 row 的 `needed` 不同 | 逐 row 独立正确 |
| T13 | OFF 身份 | 显式 OFF 与 policy-forced OFF 均不分配、不物化、不重建 Eagle first-pass metadata、graph key/数量不变；输出逐位一致 | 见 §27 |

### 25.3 Method × Backend × Timing

| ID | 目标 | 通过判据 |
| --- | --- | --- |
| T14 | Eagle3 开关与 AR first-pass 等价 | OFF：baseline identity；ON：重建 metadata 与 Target 在 §12.1 的字段列表上逐位相同，只允许表/长度不同，并继续受全部 AR gates |
| T15 | AR per-step | `K≥3` 时逐 step 对比 MRV1：`S` 固定、`visible_s` 一致；FULL merged 的**每 step device length** 正确 |
| T16 | eligible DFlash/DSpark timing | 对 DFlash 与非 DeepSeek-V4 DSpark，materialize **晚于**所有 `prepare_dflash_inputs` 与 context KV 预写；eager 与 FULL 结果一致 |
| T17 | 每 consumer group | 逐 gid 断言最终 layer metadata 消费的长度/表来自该 gid 的 view；跨组不串用 |
| T18 | 长度闭包 | GQA/MLA 实际消费的 KV 长度 ≤ `capacity_g`（**不只是 ≤ windowed_len**）；CPU 长度不落回 `max_seq_len` |
| T19 | DCP local | device/CPU 均为 prefix 差；`i=1,d=2,r=1` 反例 |
| T20 | forced-OFF / follow-config / unsupported | MTP 与 DeepSeek-V4+DSpark：warning once、行为与不开窗口逐位一致、planner/workspace/capability inventory 调用计数均为 0；用 `W∈{-1,0,合法值}` 证明 forced-OFF 早于数值校验。Eagle3 与其他 eligible parallel：OFF baseline，ON 必须进入且不得绕过原 gates。factory 不支持的方法仍是原 `NotImplementedError` |

### 25.4 Graph

| ID | 目标 | 输入/场景 | 通过判据 |
| --- | --- | --- | --- |
| T21 | **capture 三入口一致** | — | live / replay-rebuild / capture-dummy 三者的 `(data_ptr, shape, stride, dtype)` 在同一 `(descriptor, lane, phase, step, gid)` 上一致 |
| T22 | **A/B 交替 origin（关键）** | 两组完全不同 window origin 连续 replay（覆盖 `enable_enpu∈{T,F}`、GQA 与 MLA） | 每次 replay 的可见集合等于该次应得集合；**无 one-step lag** |
| T23 | no-op backend | — | SFA/DSA 的 captured consumer 读的是窗口 backing（不是 full `input_block_tables`） |
| T24 | PIECEWISE | — | capture 期真实执行的 attention-like op 拿到有效 view |
| T25 | 多 descriptor | — | 不同 descriptor 不互相污染；capture capacity ≥ runtime effective max |
| T26 | padding 无副作用 | — | padded 行的**写**为零（slot inert）、**读**输出被裁掉；不要求 block id 不相交 |

### 25.5 Async / Preemption

| ID | 目标 | 输入/场景 | 通过判据 |
| --- | --- | --- | --- |
| T27 | host ring | — | 两个 epoch 交错 prepare，旧 CPU metadata 不被覆盖 |
| T28 | **同 step row 复用** | preempt/remove 后新请求复用同一 persistent row（且 `num_blocks` 恰好相同） | 窗口源只覆盖新请求的 valid count；不出现其他请求的 block id |
| T29 | leak/lease | — | consumer 未完成时复用 slot 触发断言；缺 event 的负向测试能被捕获 |
| T30 | device lane | — | 若启用多 lane，每个 lane 的图绑定各自 capture 地址 |

### 25.6 E2E 与性能

| ID | 目标 | 输入/场景 | 通过判据 |
| --- | --- | --- | --- |
| T31 | MRV2 vs MRV1 | `draft_window_size=512` 下 dflash / 非 DeepSeek-V4 dspark（对齐 `tests/e2e/pull_request/one_card/spec_decode/test_dspark.py:80-158` 的做法） | eligible ON 组合 acceptance 与 MRV1 基线同量级；Target logits 与不开窗口一致；DeepSeek-V4+DSpark 另按 T20 验证强制 OFF，不进入 acceptance-on 对拍 |
| T32 | native SWA 交集（集合级） | N1/N2/N3 档各构造 native + window 组合 | 最终可见**绝对 KV 集合** == `窗口 ∩ native ∩ 物理保留`（不得用 acceptance 代替） |
| T33 | 物理保留 | 构造 recycling spec 的 group，`W > retention` | 告警并记录 `effective_window`；集合不超过 retention |
| T34 | 性能 | 长 context（`L ≫ W`） | materialization 成本与 `L` 解耦（只随 `Σ C_g`）；不新增 D2H（`.item()/.tolist()/.cpu()` 频次不增） |
| T35 | 内存 | 目标模型 worst-case（lane × group × host ring × backend buffer × graph pool） | 与 §15.2 公式吻合；纳入 memory planning；超阈值拒绝 |

---

## 26. Performance Validation

### 26.1 预期收益与成本

| 项 | 预期 | 备注 |
| --- | --- | --- |
| Draft attention KV read | **下降**（长度从 `L` 降到 `≤ W+A`） | 需实测 kernel 侧真实读数，而不只是端到端吞吐 |
| materialization | 新增 cost：`O(num_reqs_padded × Σ C_g)` | 与 `max_model_len` **解耦**（§15.4）；`C_g ≈ ceil(W/span)+1` |
| CPU 侧 | **不应新增** D2H / `.item()` / `.tolist()` | AR 现有每 step `seq_lens_list = ....tolist()`（`worker/v2/spec_decode/autoregressive/speculator.py:756` [V]）是既有的；窗口不得增加频次 |
| `max_seq_len` 缩小 | **不承诺** | §19.4：某 backend 的 tiling 若不消费窗口 upper，则无收益，必须显式记录 |
| 其它 | SFA/DSA 的 derived state 每 step 重建（既有行为）、AR per-step length buffer | 一并计入 |

### 26.2 性能报告必须分项

```text
1. materialization kernel 时间/带宽
2. CPU exact 的获取方式（是否有同步）
3. DSA/SFA derived state
4. table payload 内存
5. host ring + device lane 内存
6. Draft attention 的 KV read 下降
7. 端到端 acceptance / latency / throughput
8. Window OFF 的 before/after 基线（含 p50/p99 与峰值显存）
```
**break-even 判据**：只有当 `(acceptance 收益 + KV read 节省) > (materialization + CPU 同步 + derived state)` 时才建议用户开启；否则文档应给出"该组合不宜开启"的结论。

---

## 27. Rollback / Window-OFF Regression

**OFF 必须满足的身份条件**（I22）：

这里的 OFF 同时包含用户未配置 `W` 与 policy-forced OFF（MTP、DeepSeek-V4+DSpark）。forced-OFF 只允许多一个去重后的 policy warning；除此之外必须与未配置 Window 的执行路径一致。

| # | 条件 | 验证 |
| --- | --- | --- |
| 1 | policy 在任何 Window 数值校验、capability inventory、planner 与 workspace 分配之前返回；forced-OFF warning once | 代码审查 + validator/inventory/planner/分配调用计数断言 |
| 2 | 不进入 window-aware 入口；不套 `build_draft_attn_metadata_factory`（该 factory 会**无条件**注入 positions/is_prefilling/attn_state/parallel_config，`worker/v2/attn_utils.py:1268-1275` [V] ⇒ 会改变 OFF 输入） | 调用链快照比对 |
| 3 | AR first pass 继续**复用 Target metadata**（§12.1） | 对象 identity 断言 |
| 4 | DFlash/DSpark 继续走现行 wrapper 与 capture 路径；DeepSeek-V4+DSpark 不进入任何 window-aware DSpark hook | 同上 |
| 5 | graph descriptor key 与数量不变 | graph 计数断言 |
| 6 | 不新增 device kernel / host copy / Python 包装 | 分配/拷贝计数 |
| 7 | 输出、acceptance 逐位/统计等价；latency/throughput/峰值显存回退 ≤ 阈值 | E2E + 性能 |

**关于"零额外 branch"**：本设计要求的是**可测的语义/性能阈值**，而不是字面上的"零分支"（任何读配置的代码都至少有一个分支）。 [D]

**回滚**：对于 follow-config method，OFF 与 ON 是两条在 policy 处分支的路径，回滚手段是"移除配置"或降级 capability（不需要回退代码）。MTP 与 DeepSeek-V4+DSpark 的 forced-OFF 是冻结产品策略，不是可通过 capability 升级解除的临时回滚。**未完成 capture binding 的 eligible backend 一律先以 eager 交付**，FULL 在其 binding 完成后才开放——不允许"eager 正确、graph 静默读旧地址"。

---

## 28. Risks

| ID | 风险 | 等级 | 缓解 |
| --- | --- | --- | --- |
| R1 | 对齐单位取错（默认 lcm）导致窗口被放大到失效 | **Critical** | §16.2 三支规则 + T2 反例测试；`A ≤ B_legacy` 断言 |
| R2 | capture 与 replay 使用不同 backing，no-op backend 静默读旧地址 | **Critical** | §19.3 capture binding + T21/T22/T23 |
| R3 | 表已窗口化而某个 CPU 长度仍是 full 量级 ⇒ 读到 cache 第 0 块 | **Critical** | I8/I9 + §17.3 fail fast + T18 |
| R4 | 把 stale block id 当有效源复制 | **Critical** | I12 `valid_num_blocks` 掩码 + T11 |
| R5 | 窗口-relative 与 absolute 坐标混用（DSA/SFA/DCP） | **Critical** | §21.2 审计 gate + T32 集合级验证；未审计 ⇒ fail closed |
| R6 | preemption/row 复用导致跨请求数据泄漏 | **Critical** | I15 epoch 含 request identity + T28 |
| R7 | AR 首步重建元数据时改变了 query layout | **Critical** | §12.1 逐位等价 + T14 |
| R8 | AR FULL merged：单份 device length 被多 step 共享 | **Critical** | §12.1 per-step device buffer + T15 |
| R9 | async：host 重叠被误认为 device 串行 | High | §20.2 分层 + 断言 + T27/T29 |
| R10 | update/replay 顺序假设错误导致 one-step lag | High | §19.6 协议 + T22 交替 origin 实验 |
| R11 | 物理保留上限被忽略（recycling spec） | High | I21 + T33 |
| R12 | 显存超预算（多 group × lane × descriptor） | High | §15.2 公式 + 纳入 memory planning + T35 |
| R13 | 未验证 backend 组合被静默启用 | High | I20 fail closed + T20/T23 |
| R14 | eligible ON 路径的配置收紧（`W≤0`、`W≥K`）造成用户可见回归 | Medium | §22.2 标注 + maintainer 批准（[OQ]）；forced-OFF 路径不执行这些校验 |
| R15 | method policy 按 class 推断，或 forced-OFF 晚于数值/capability 解析（MTP 落到 Eagle、DeepSeek-V4+DSpark 被重新启用） | **High** | §22.1/§22.3 normalized method + target identity 优先；T20 调用计数与 warning-once 单测 |
| R16 | materialization 成本抵消收益 | Medium | §26 break-even + T34 |
| R17 | MRV2 与 MRV1 的 acceptance 基线不可直接比较（MRV1 DSpark 强制 eager） | Medium | §25 T31 明确对拍口径 |

---

## 29. Open Questions

> 未验证 ⇒ 不得当作事实。每条给出"要什么证据才能关闭"。

| ID | 问题 | 关闭证据 | 影响 |
| --- | --- | --- | --- |
| **OQ-1** | capture 期的 Ascend-local window-aware helper 能否拿到 speculator 的 capture binding（DFlash 经模块符号重绑定；AR 经 Ascend 的 capture 助手） | 在目标 checkout 上做最小 spike；或给出等价显式传递路径 | 决定 FULL 能否开放（E2→E1） |
| **OQ-2** | 同一 runner 是否存在**多个 device execution lane**（而不只是 host 多 in-flight） | 910 NPU runtime trace（stream/event 时序） | 决定 device slot 数（§20.2） |
| **OQ-3** | eligible ON 路径的 `W ≤ 0` 与 AR `W ≥ K` 收紧是否获批（相对 MRV1 是兼容性变更） | maintainer 决策 | 配置政策（§22.2）；不影响 forced-OFF 的已冻结顺序 |
| **OQ-4** | DSA 路径是否存在"绝对 positions × rebase 后表"的混用点（compressor C4/C128、QLI、SAS、`start_pos_prefill` 语义） | 逐字段源码审计 + 集合级 reference 测试 | 决定 DSA 组合能否启用（§21.2） |
| **OQ-5** | 目标模型 consumer group 的完整清单：global gid、backend、causal、native window、KV spec 是否 recycling | 在 `set_attn()` 后输出 capability inventory 并落日志 | A 的计算、`effective_window`、fail-closed 判定 |
| **OQ-6** | SFA 的 `window_relative_visible_count` 的确切公式与索引平移（`use_logical_indices` 两支） | 源码 trace + 与 `block_table[req, token_indices]` 的 reference 对拍 | SFA 组合能否启用 |
| **OQ-7** | CP/DCP 下"绝对区间 → (source_col, first_token_offset, local_len)"的正式映射；`S` 是否在所有 rank 上 page-aligned | 多 rank reference 测试 | CP 组合能否启用 |
| **OQ-8** | runner 在同一步内 remove→add 的 row 复用时机（free-list 立即复用？） | 源码 trace（`vllm/v1/worker/gpu/model_runner.py` 的 add/remove 路径） | epoch 的 request identity 快照策略 |
| **OQ-9** | device/CPU exact 的完整消费者清单（每个 backend 最终把哪个字段当 `actual_seq_lengths_kv`） | 逐 backend 代码审计 + UT | 长度类型系统（§17.1）的必需字段 |
| **OQ-10** | 是否存在无需 D2H 的 rejection-corrected CPU exact 生产者；若没有，哪些组合必须 fail closed | 源码 + runtime 断言 | MLA / DSpark+GLM 的 CPU 优先路径 |
| **OQ-11** | AR PIECEWISE 的 capture 期哪些 attention-like op 真实执行 | 源码（`cudagraph_utils.py` 注释）+ runtime | PIECEWISE 支持条件（§19.5） |
| **OQ-12** | 310P 的独立 capture/speculator 实现是否需要单独接入 | 源码（`_310p/worker/v2/...`） | 310P 是否 fail closed |
| **OQ-13** | `update_graph_params` 的 update 对"本次 vs 下次" replay 生效（按 backend/enable_enpu） | T22 的 A/B 实验 + NPU trace | §19.6 协议的确定性 |

**已关闭、不得重新列为 OQ 的产品策略**：MTP 与 DeepSeek-V4+DSpark 强制 Window OFF；Eagle3 和其他 eligible parallel 组合 follow-config。剩余 OQ 只决定 eligible ON 组合的 backend/graph/runtime enablement，不能推翻 forced-OFF 策略。

---

## 30. Expected File Changes

> 仅列预期范围与顺序；**本文不修改任何代码**。

### 30.1 新增

| 文件 | 职责 |
| --- | --- |
| `vllm_ascend/worker/v2/spec_decode/draft_window.py` | policy、`DraftWindowMath`、`DraftWindowLayout`、visibility domain、`FullDraftKVSource`、workspace、view、epoch/lease |
| `vllm_ascend/worker/v2/spec_decode/draft_window_capture.py` | `DraftWindowCaptureBinding` 与 Ascend-local window-aware capture helper |
| 对应 UT | math / workspace / method / backend / graph / async / preemption |

### 30.2 修改（最小集）

| 文件 | 修改 |
| --- | --- |
| `worker/v2/attn_utils.py` | **保留**现有 Target/general 入口（签名不变）；**新增** view 必填的 Draft-only 入口；Window ON 时禁用 CPU fallback |
| `worker/v2/spec_decode/__init__.py` | normalized method + target identity policy；MTP、DeepSeek-V4+DSpark forced-OFF 判定早于数值/class/backend 分支；Eagle3/eligible parallel follow-config |
| `worker/v2/spec_decode/autoregressive/speculator.py` | AR plan/anchor、first-pass 重建、per-step refresh、FULL per-step device length |
| `worker/v2/spec_decode/dflash/speculator.py` | parallel timing hook + typed view |
| `worker/v2/spec_decode/dspark/speculator.py` | 仅 eligible DSpark ON 路径接入 consumer groups、backend derived visibility；DeepSeek-V4 target 不可到达该 hook |
| `worker/v2/spec_decode/autoregressive/aclgraph.py` | prefill/decode capture binding 与 lease |
| `worker/v2/spec_decode/dflash/aclgraph.py` | eligible DFlash/DSpark capture binding 与 event lifecycle；forced-OFF 路径保持现状 |
| `attention/sfa_v1.py`（或窄 provider hook） | window-relative visible count + 索引平移 |
| `attention/dsa_v1.py`（或窄 provider hook） | **仅在 OQ-4 审计失败时**才需要；优先不改 |
| `ascend_config.py` | 仅在 §22.2 的数值范围政策获批后增加 value validation；不得把 validation 放到 forced-OFF policy 之前 |

### 30.3 明确不修改

`vllm_ascend/spec_decode/*`（MRV1）、Scheduler / KV Cache Manager、Target ModelRunner 主链、`BlockTables` 的 authoritative owner 与 slot kernel、positions 的生成、Target sampler / verification。**若实现发现必须改这些组件，先回到设计评审解释边界为何不足。**

### 30.4 实现顺序（每步都必须可独立验证且 fail closed）

```text
P1  MRV2 纯数学 + MRV1 golden 对拍（不改 MRV1 生产代码）
P2  policy / capability + Window OFF 身份测试（MTP、DeepSeek-V4+DSpark forced-OFF；Eagle3/其他 eligible parallel follow-config）
P3  visibility domain + 窄 workspace + full-source 全量重写（含 valid_num_blocks 掩码）
P4  Draft-only metadata 入口 + 长度一致性 + CPU fallback 收口
P5  DFlash / eligible DSpark eager（GQA / MLA；排除 DeepSeek-V4 target）
P6  explicit capture binding + FULL
P7  AR / Eagle3 eager（first-pass 重建 + per-step device length）
P8  AR PIECEWISE / FULL merged
P9  DSA / SFA / DCP projectors（按 OQ-4/OQ-6/OQ-7 的 gate）
P10 async / preemption / E2E / 性能 / 文档
```

---

## 31. Design Decision Log

> 合并三份 v2 材料的决策项；标注状态与依据。`Confirmed` = 三份材料一致且已核实；`Revised` = 有冲突并已裁决；`New` = 本文新增。

| ID | 决策 | 状态 | 依据 |
| --- | --- | --- | --- |
| D01 | 采用 speculator-owned Draft read plane + typed view（Candidate B 方向） | Confirmed | 三份材料一致；[V] §7 |
| D02 | **Draft-only metadata 入口**：Target 入口在签名上无法接收 view | Revised | 采纳 Codex v2 D02；[V] §7.2 的三入口 |
| D03 | 一个 proposal = 一个 visibility domain，domain 内共享单一绝对 `S` | Confirmed | 三份材料一致；[V] `attn_utils.py:294-330` 共用长度 |
| D04 | **对齐单位默认 `A = B_legacy`**；仅当 `∀g: span_g \| B_legacy`；否则 fail closed | **Revised（本文关键修正）** | GPT v2 §6.2 反例 + [M] §16.2；推翻 Codex v2 与我 v1 的"lcm 默认" |
| D05 | 保留**窄表** `[R, C_g]`；用**显式 capture binding** 让 capture 与 replay 同 backing | Revised | 采纳 Codex v2 D05；[V] no-op updater + DSA 捕获 `ori_sparse_indices` 指针 |
| D06 | 不新增 ContextVar / `_EXTRA_CTX` / module-global 运输 view | Confirmed | 三份材料一致；[V] §20.4 |
| D07 | 每 step 从 full source **全量重写** `[0, C_g)`；不做增量补列 | Revised | 采纳 Codex v2 D07；保 I11 幂等 |
| D08 | Window ON 时 CPU exact/upper **必填**；缺失即报错，禁止 `np.full(max_seq_len)` fallback | Confirmed | 三份材料一致；[V] `attn_utils.py:253-260` |
| D09 | 拆分 `capture_capacity` 与 `runtime_effective_max`（4 个不同语义） | Revised | 采纳 Codex v2 §11.5；[V] capture 与 replay 传不同值 |
| D10 | 第一版**不修改 MRV1** adapter | Confirmed | 三份材料一致；scope 控制 |
| D11 | eligible AR ON 路径要求 `W ≥ K`，并保留运行时 `visible ≥ 0` 断言；forced-OFF method 不进入该校验 | Confirmed（含我的勘误） | [M] §16.4；GPT v2 §6.4 / Codex v2 R-m3；maintainer policy 2026-10-09 |
| D12 | native SWA 与窗口 = **可见集合交集**；表与长度一起 rebase 后由 backend 在相对坐标自然求交；**不重复 clamp 绝对 start** | **Revised（本文关键修正）** | 采纳 Codex v2 R-17；[V] `build_dspark_swa_indices` 坐标自洽；推翻我 v1 的"只裁表无效" |
| D13 | padding 契约 = **"读可任意 + 写必须为零"**，不要求 block-id 不相交 | **Revised** | 采纳 Codex v2 R-08；[V] `attention_v1.py:340-360` 注释原文 |
| D14 | host ring 深度 ≥ `max_concurrent_batches`；**device slot 数由已验证 lane 决定**（首期 1 + 严格断言） | Revised | 采纳 Codex v2 D14/§12.2；[V] `vllm.py:589-598`、`buffer_utils.py:24` |
| D15 | 每 proposal 无条件新建 epoch；epoch 含 ordered request identity 与 valid counts | Confirmed | 三份材料一致；[V] 同 step row 复用 |
| D16 | consumer 集合 = `window_consumer_group_ids`（含派生索引依赖组，不只是 draft attention 组） | Revised | 采纳 Codex v2 D16 |
| D17 | unsupported 保持 factory error；MRV1 静默未读取的方法不升级 warning | Revised | 采纳 Codex v2 D17 + 我 v2 的撤回 |
| D18 | 不建立 Flashcomm layout provider；改用 `ParallelWindowProjector` | Confirmed | 三份材料一致；[V] Flashcomm 是 SP-MoE 开关 |
| D19 | `A` 不可得、`row_width_g < C_g`、任一 consumer group 不支持 ⇒ **整个 domain fail closed** | New | [D] 避免"部分 group 窗口化"造成语义分裂 |
| D20 | `effective_window_g = min(W, spec 保留量_g)`（recycling spec 会物理释放窗口外块） | **New** | [V] `vllm/config/vllm.py:602-609` 注释 + KV spec 类型 |
| D21 | 长度必须类型化（device exact / CPU exact? / upper / capacity / backend max），禁止一套函数盲算 | Revised | 采纳 Codex v2 D08 基础 + 本文 §17 的显式表 |
| D22 | `visible_upper` 用 canonical `S` 平移并**夹紧到 `capacity_g`** | New | [M] §17.2 反例；修正 MRV1 的独立重算 |
| D23 | 首期范围：`{dflash,dspark（非 DeepSeek-V4 target）} × {GQA,MLA} × eager`；FULL/AR/DSA/SFA/CP/310P 按 gate **fail closed**；Eagle3 ON 保留完整设计路径 | Revised | capability 门禁框架 + maintainer policy 2026-10-09 + 本文 §9.2 |
| D24 | 判别名用 **storage 区间**，不比 `data_ptr()`；且不要求 source pointer 恒等于 `input_block_tables[g]`；prefix slice 的 `storage_offset` 不漂移 | Revised | 采纳 Codex v2 R-04/R-10（修正我 v1 的两条过强/有误断言） |
| D25 | `max_seq_len` 不承诺通过窗口缩小获得 kernel 收益；无收益的 backend 必须显式记录 | New | [V] §19.4 的既有分歧 |
| D26 | **权威 method policy**：MTP、DeepSeek-V4+DSpark 配置 Window 时 warning once + 强制 OFF，原因是 draft 与主模型一起训练，并在任何数值校验/planner/workspace 前返回；Eagle3 与其他 eligible parallel 严格 follow-config，ON 不放宽任何 gate | **New / Frozen policy** | maintainer 产品策略，2026-10-09 |

---

## 附录 A：三份 v2 材料的冲突清单与裁决

> 这是本文最重要的 Review 材料：**冲突必须显式列出，并说明采用哪一方、为什么**。

| # | 冲突点 | Codex v2 | DeepSeek v2（我） | GPT v2 | **本文裁决** | 理由 |
| --- | --- | --- | --- | --- | --- | --- |
| X1 | 对齐单位 | `A = lcm(span_g)` 默认 | `A = lcm(col_span_g)` 默认 | **反驳无条件 lcm**：嵌套时 `A = B_legacy`；非嵌套需标注语义变更或 fail closed | **采纳 GPT v2**：默认 `B_legacy`，非整除 fail closed | `L=300,W=128,B_legacy=64,span=48` ⇒ lcm=192 ⇒ `S=0`、visible 从 172 变 300 [M]（两份材料**一致**却都被第三份用反例推翻——正是"一致 ≠ 正确"的实例） |
| X2 | 窗口表形状 | 窄表 + 显式 capture binding | full-width（追求 shape 不变） | 默认 full-width private buffer | **采纳 Codex v2（窄表）** | [V] no-op updater 无法换指针 ⇒ 同 shape 不解决问题；且 full-width 显存为 `O(R×Σfull_width)`（可达百 MiB 级） |
| X3 | DSA 非因果的窗口落点 | 表+长度一起 rebase ⇒ 生成器自然求交；**不要**再 clamp 绝对 S | "只裁表无效"⇒ 必须 clamp 绝对 `start_pos` | 仅裁表可能无效；须审计绝对/相对混用 | **采纳 Codex v2 的机制 + GPT v2 的审计 gate** | [V] `build_dspark_swa_indices` 的 `prefix/start_pos/pos` 全在输入坐标系内自洽；但 compressor/QLI 等是否存在绝对混用未验证（OQ-4） |
| X4 | device lane 数 | host ring = `max_concurrent_batches`；device slot 由已验证 lane 决定（首期 1） | device lane 深度 = `max_concurrent_batches` | 不预设 2 或 K；依真实 in-flight | **采纳 Codex v2** | [V] 现有单份 `input_block_tables` 能工作 ⇒ device 串行是现状；"host 重叠"与"device 并行"必须分开建模 |
| X5 | 首期范围与产品策略 | 用 capability 门禁，**不按 method 砍掉** | 明确砍到 `{dflash,dspark}×{GQA,MLA}` | 未表态 | **capability 框架 + 2026-10-09 maintainer policy**：eligible method 按 gate 分级；MTP、DeepSeek-V4+DSpark 是 policy-forced OFF；Eagle3 follow-config 并保留完整 ON 设计 | 产品策略与 capability gate 是正交层：forced-OFF 不等待 backend gate，eligible ON 也不因 follow-config 而跳过 gate |
| X6 | padding 行 block id | 不要求与 active 不相交（无 observational side effect 即可） | 我早先要求"不相交" | 未表态 | **采纳 Codex v2** | [V] `attention_v1.py:340-360` 注释明示"any valid positive KV length / zero block row is fine" |
| X7 | source pointer 约束 | 不要求等于 `input_block_tables[g]`；用 typed source + no-alias | 我要求 pointer 相等 | 未表态 | **采纳 Codex v2** | [V] `gather_block_tables` 支持 caller-provided `out` ⇒ PCP/capture provider 是合法 source |
| X8 | 分片 view 的 offset | `x[:n]` 恒从 row 0 起，offset 不漂移 | 我说"offset 随 descriptor 变" | 未表态 | **采纳 Codex v2** | [V] `x[:n]` 的 `storage_offset == 0`；变化的是 shape |
| X9 | update/replay 顺序 | 给出具体设备协议（materialize→wait→submit→event→update→release） | "写成显式契约 + A/B 实验" | 明确"不能静态推断，需 trace" | **三者合成**：以 Codex v2 协议为假设，用我 T22 的 A/B 交替 origin 实验 + GPT v2 要求的 trace 确认 | [V] `acl_graph.py:292-320` 顺序随 `enable_enpu` 变化 |
| X10 | `max_seq_len` | 拆成 4 个语义 | "保持容量语义、不窗口化" | 未表态 | **采纳 Codex v2** | [V] capture 与 replay 本就传不同值，拆开更清晰 |
| X11 | MRV1 重构 | 第一版不动 | 第一版不动 | 未表态 | 一致 | scope 控制 |
| X12 | `W ≥ K` | 必须保留 | 必须保留（我勘误后） | 必须保留，且断言 `visible ≥ 0` | 一致 | [M] §16.4 |
| X13 | 物理保留上限 | 未提 | **提出** | 未提 | **采纳 DeepSeek v2** | [V] `vllm/config/vllm.py:602-609` 注释 |
| X14 | consumer 集合 | `window_consumer_group_ids`（含派生依赖组） | draft attention 组 | 未提 | **采纳 Codex v2** | [V] SFA indexer 等派生依赖组会决定可见性 |

---

## 附录 B：已核实源码事实总表（Review 时按此索取证据）

| 事实 | 位置 |
| --- | --- |
| MRV1：配置读取、MTP 与 DSV4 的旧 warning 分支、adapter 构造与 `future_offset`（**仅为当前源码事实，不覆盖 2026-10-09 权威迁移策略**） | `vllm_ascend/spec_decode/llm_base_proposer.py:415,423-429,430-435,437-452` |
| MRV1：公共 apply 点；DSpark per-group apply；冻结 start + 长度递增 | `llm_base_proposer.py:1119-1127,2588-2605,2073-2077,2134-2136` |
| MRV1：单一对齐量（第一个 draft layer 的 kernel block size） | `llm_base_proposer.py:406-408,446-452`；DSpark 复用同一值 `:2604-2605` |
| MRV1：DSV4 识别使用 **target** 的 `model_type.startswith("deepseek_v4")`；MRV2 复用该识别但执行 forced-OFF policy | `llm_base_proposer.py:420-422`；§22.3 |
| MRV1：slot 计算用 full table | `llm_base_proposer.py:2104-2112` |
| MRV1：`apply()` 改三处 CPU mirror（各自独立重算） | `vllm_ascend/spec_decode/utils.py:149-169` |
| 配置字段类型只有 `int \| None`，无范围校验 | `vllm_ascend/ascend_config.py:497`；`_validate_user_input_ranges()` `:568-586` |
| Draft 与 Target 共享同一 `BlockTables` 对象 | `vllm/v1/worker/gpu/spec_decode/speculator.py:287` |
| speculator 保存 `target_input_buffers` / `target_attn_groups`（首步复用 Target metadata 之故） | `spec_decode/speculator.py:287-293` |
| AR 首步复用 Target metadata 的理由（query 补齐含 rejected 位置） | `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:233-238,306-322` |
| AR prefill kernel：`L0` 取未扣 rejection 的 `seq_lens`；positions 只复制 `[0,query_len)`；padded `seq_lens` 清 0、positions 不清 | 同文件 `:700-770` |
| 上游 draft builder 传入 `seq_lens` / 上游层不传 positions | `spec_decode/speculator.py:346,355`；`dflash/speculator.py:453` |
| DFlash/DSpark device exact 由 kernel 用 device `num_rejected` 写出 | `vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:287-290` |
| DFlash capture：full dummy 表、不传 positions、`max_seq_len=max_model_len` | `vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:36,55,64` |
| DFlash capture 模块符号由 patch 导入期重绑定 | `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26` |
| AR decode capture 走 `prepare_inputs_to_capture` | `worker/v2/spec_decode/autoregressive/aclgraph.py:111` |
| Ascend funnel：CPU fallback；group 循环共享一份 `seq_lens` | `worker/v2/attn_utils.py:253-260,290-330` |
| wrapper/factory 均为模块级替换（`finally` 恢复；LIFO 安全） | `worker/v2/attn_utils.py:1240-1251,1266-1281` |
| factory 无条件注入 positions/is_prefilling/attn_state/parallel_config | `worker/v2/attn_utils.py:1268-1275` |
| funnel 全 0 positions fallback | `worker/v2/attn_utils.py:286-288` |
| AR override 注释：不注入 positions 会把 position-0 RoPE 烘进图 | `worker/v2/spec_decode/autoregressive/speculator.py:583-592` |
| AR per-step **CPU** buffer（device 无） | `worker/v2/spec_decode/autoregressive/speculator.py:103-109` |
| `_calc_next_seq_lens_cpu` 明确不减 rejection | 同文件 `:815-822` |
| FULL merged AR 只 replay 一次 | 同文件 `:438-458` |
| SFA：强制 `ori_mask_mode=0` / `ori_win_left=-1`（native window 不生效）；top-k 路径 | `vllm_ascend/attention/sfa_v1.py:114-119,198-219` |
| SFA：每次 build 把 common 表复制进**自有** `block_table_buffer` | `sfa_v1.py:296-307,703-706` |
| SFA：`update_graph_params()` 是 `pass` | `sfa_v1.py:885-897` |
| DSA：`build_dspark_swa_indices` 的坐标自洽（`prefix/start_pos/pos`）、indices 默认为 physical slot、`use_logical_indices` 支、persistent buffer 保持 capture 地址 | `vllm_ascend/attention/dsa_v1.py:420-461` |
| DSA：`block_table` 是 common 的**别名**；`dspark_swa_indices` 是自有持久 buffer | `dsa_v1.py:884-890,1248-1250,420-436` |
| DSA：`start_pos_prefill` 为 builder 自有 buffer，按 `num_actual_reqs` 清 padded | `dsa_v1.py:1088-1100` |
| DSA：`update_graph_params()` 是 `pass` | `dsa_v1.py:1619-1631` |
| DSA：`hf_config.sliding_window - 1` 无 None 检查 | `dsa_v1.py:1107` |
| GQA：native SWA → `sparse_mode=4/pre_tokens`；draft 层仍传 block_table | `attention/attention_v1.py:602-604,459-472` |
| GQA：dummy request 补 `seq_len=1`+zero row；"any valid positive KV length / zero block row is fine"；可能 `torch.cat` 表 | `attention/attention_v1.py:340-368` |
| GQA：FIA 调用 `register_task(..., {"block_table": ...})` ⇒ 可重绑 | `attention/attention_v1.py:652-660` |
| GQA legacy `update_graph_params()` 抛 `NotImplementedError`（要求 UpdatableGraph） | `attention/attention_v1.py:572-581` |
| `use_updatable_graph()` 仅对 `AscendAttentionBackend` 真 | `vllm_ascend/utils.py:1769-1775` |
| `_select_seq_lens`：`_seq_lens_cpu` → `seq_lens_cpu` → device；parallel_drafting 强制 device，DSpark+GLM 例外 | `vllm_ascend/attention/utils.py:553-587` |
| MLA CPU 优先 | `vllm_ascend/attention/mla_v1.py:500-509` |
| `get_dcp_local_seq_lens` 对 L 非线性 | `vllm/v1/attention/backends/utils.py:1088-1133` |
| CP 下取列用 `query_pos // (block_size * CP_SIZE)` | `vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:264` |
| `num_blocks` 是 UVA 张量；gather kernel 按它限界；active row 只写 `[0,num_blocks)`、padded 行清零 | `vllm/v1/worker/gpu/block_table.py:61,170-171,251-272,177-187` |
| slot mapping 读 authoritative `block_table_ptrs` | `vllm/v1/worker/gpu/block_table.py:93-97,190-221`；`vllm_ascend/worker/v2/block_table.py:82-114` |
| `ACLGraphWrapper` 只检查 positional args 的地址 | `vllm_ascend/compilation/acl_graph.py:186` |
| update/replay 顺序随 `enable_enpu` 变化；async 跨迭代竞态需 `synchronize`；FULL+EAGLE merge 免 barrier | `vllm_ascend/compilation/acl_graph.py:292-320` |
| legacy replay 顺序"先 replay 后 update" | `worker/v2/spec_decode/dflash/aclgraph.py:100-138`、`autoregressive/aclgraph.py:154-194` |
| MRV2 + async ⇒ `max_concurrent_batches = pp_size + 1` | `vllm/config/vllm.py:589-598` |
| recycling KV spec 会**释放窗口外块** | `vllm/config/vllm.py:602-609`（注释） |
| `SlidingWindowSpec` / `SlidingWindowMLASpec` / recycling 注释；Ascend `AscendSlidingWindowMLASpec` | `vllm/v1/kv_cache_interface.py:811,909,1316`；`vllm_ascend/core/kv_cache_interface.py:236` |
| UVA pool 深度与 retire 要求 | `vllm/v1/worker/gpu/buffer_utils.py:24,19,61` |
| `use_eagle()` 成员含 mtp/dflash/dspark ⇒ 不能按 class 判 policy | `vllm/config/speculative.py:1936-1940`；`vllm_ascend/worker/v2/spec_decode/__init__.py:68-71` |
| MRV2 factory 对不支持方法抛 `NotImplementedError` | `worker/v2/spec_decode/__init__.py:72` |
| DFlash2 要求 `enforce_eager`，否则 `NotImplementedError` | `worker/v2/spec_decode/dflash2/speculator.py:121-139` |

---

## 附录 C：Method Integration Matrix（最终版）

| Method | MRV1 contract | MRV2 等级 | Timing（最后 full-state 点 → view） | `K` | consumer groups | `A` / 容量 | Graph | 前置 gate |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| `dflash` | 支持（公共 apply） | **E1** eager → E2 FULL；follow-config | 所有 consumer group 的 `prepare_dflash_inputs` + context KV 预写之后 | 0 | `window_consumer_group_ids` | 规则 1（`A=B_legacy`） | eager / FULL_DECODE_ONLY | capture binding（OQ-1） |
| `dflash` + DFlash2 | 继承 DFlash | **E1**（仅 eager）；follow-config | 同 DFlash | 0 | 同上 | 同上 | eager only | — |
| `dspark`（非 DeepSeek-V4 target） | 支持（per-group apply） | **E1** eager(GQA/MLA) → E2（FULL、DSA/SFA）；follow-config | 所有 consumer group prepare 之后、DSA/SFA derived state 之前 | 0 | 同上（含 SFA indexer 组） | 同上 | eager / FULL | OQ-4（DSA）、OQ-6（SFA） |
| `dspark` + DeepSeek-V4 target | 当前源码有旧 warning 分支 | **P-OFF** | 不创建 view；现行 Window-OFF baseline | — | — | — | 保持 baseline | warning once；早于任何数值/capability/planner/workspace |
| `eagle` | 代码路径支持 | **E2** | Target query layout/full slots 定型后建 anchor；每 step full slot 后 refresh | `K` | 同上 | 同上 | eager / PIECEWISE / FULL | AR first-pass 重建 + FULL per-step device length（OQ-11） |
| `eagle3` | 支持（公共 apply） | **E2；follow-config** | OFF 不创建 view；ON 同 Eagle 且 hidden-state 选择不变 | `K` | 同上 | 同上 | 同上 | ON：AR first-pass 重建 + FULL per-step device length（OQ-11） |
| `mtp`（含 Gemma4/Step3.5/multi-KV） | warn + ignore | **P-OFF** | 不存在合法 Window 边界；现行 baseline | — | — | — | 保持 baseline | warning once；早于任何数值/class/backend/planner/workspace |
| `draft_model` | 代码路径支持；MRV2 factory 不支持 | **X** | — | — | — | — | 保持 factory error | — |
| `extract_hidden_states` | 不适用 | **N/A** | — | — | — | — | 保持现状 | — |
| ngram / ngram_gpu / suffix / medusa | 静默未读取 | **N/A** | — | — | — | — | 保持现状 | 不升级为 warning（D17） |
| mlp_speculator / custom_class | Ascend 不可实例化 | **X** | — | — | — | — | 保持 factory error | — |

**所有 eligible ON method 共同的硬约束**：Target / positions / slot_mapping / authoritative block state 全程不可变；Window 只改 Draft 的 read 侧；未声明能力的组合 fail closed。`P-OFF` method 不创建 Window read plane。

---

## 附录 D：本文与三份 v2 材料的差异索引（便于逐条 Review）

| 本文位置 | 相对材料的变化 | 材料出处 |
| --- | --- | --- |
| §16.2 | 对齐单位从"lcm 优先"改为"`B_legacy` 优先、非整除 fail closed" | GPT v2 §6.2 反例 |
| §16.3 | 容量公式改为 `ceil((W+A-1)/span_g)`；不再用 `+1` 宽松式 | Codex v2 §4.3 |
| §16.4 | 负 `visible` 的严格条件与 `W ≥ K` 的充分性；附勘误 | GPT v2 §6.4 + Codex v2 R-m3 |
| §17.2 | `window_upper` 明确夹紧到 `capacity_g` | 本文新增（结合 Codex v2 D08） |
| §18.1 | 源侧三个条件（含 `valid_num_blocks`），并给出设备侧取法 | Codex v2 §3.3/Inv 11 + 本文的 UVA 证据 |
| §18.3 | padding 契约改为"读可任意 + 写必须为零" | Codex v2 R-08 + `attention_v1.py:340-360` |
| §19.2/§19.3 | 从"full-width 同形"改为"窄表 + 同 backing" | Codex v2 R-11/D05 |
| §19.4 | `max_seq_len` 四语义拆分；不承诺 kernel 收益 | Codex v2 §11.5 + 本文的谨慎表述 |
| §20.2 | device slot 从"= max_concurrent_batches"改为"先证明 lane" | Codex v2 §12.2 |
| §21.2 | DSA 从"必须 clamp 绝对 start"改为"rebase 后自然求交 + 审计 gate" | Codex v2 R-17 + GPT v2 §10.3 |
| §21.4 | 新增物理保留上限约束 | 本文（DS v2 D16） |
| §22.4 | 撤回 v1 的"unsupported 方法 warning 升级" | Codex v2 §2.6/我 v2 的撤回 |
| §9.2 | 从"砍掉 AR"改为"契约覆盖 + capability 分级" | Codex v2 §2.6 |
| §1/§6.1/§9.2/§12/§22/§25/§27/§30/§31/附录 C | MTP、DeepSeek-V4+DSpark forced-OFF；Eagle3 与其他 eligible parallel follow-config；forced-OFF 早于所有数值与资源动作 | maintainer 产品策略，2026-10-09 |
| §附录 A | 14 条冲突的显式裁决 | 本文 |

---

**本文档到此结束。等待人工设计 Review；在 Review 通过前不进入实现。**
