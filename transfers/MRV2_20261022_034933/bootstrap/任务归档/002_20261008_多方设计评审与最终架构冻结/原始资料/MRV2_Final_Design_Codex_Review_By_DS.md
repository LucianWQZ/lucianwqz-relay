# Attack Review：Codex Final Design（by DeepSeek）

> 被评审文档：`/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_Codex.md`（1535 行）
> 交叉参考：`..._Final_Design_DS.md`（我自己，1396 行）；Stage 1–7 事实笔记
> 源码基线：`/Users/wenqingzhang/Desktop/vllm/vllm`、`/Users/wenqingzhang/Desktop/vllm/vllm-ascend`（2026-10-08 快照，无 `.git`）
> 评审方式：**每条发现都在当前 checkout 里核过**；无法静态证明的一律标 `Needs Verification` 并给出关闭证据。
> 本文不改任何生产代码，也不改写两份 Final Design。

---

## 1. Overall Verdict

**结论：Codex Final Design 是目前三份材料里治理结构最好、最适合作主文档底稿的一份；但它的"默认 capture 路线"与"AR 首步 metadata 存储"两处存在未闭合的结构性缺口，不能按当前文字直接冻结。**

具体判定：

| 维度 | 判定 |
| --- | --- |
| 架构方向（speculator-owned read plane + Draft-only 入口 + 显式传参） | **成立**，与源码事实一致 |
| 数学（legacy anchor / capacity / upper clamp / `W≥K` / 非整除处理） | **基本正确**，个别定义有歧义（R-03/R-05），一处容量上界表述需要收紧 |
| Graph capture 的**可实施性** | **未闭合**（R-01）：默认路线 `DIRECT_CAPTURE_BOUND` 需要的注入点在 upstream 文件里、没有参数通道；同一文档自己把它列为 Open（OQ-17），却在 §19.2/§31.1 写成"默认推荐" |
| AR 首步与 FULL replay 的 metadata **存储归属** | **未覆盖**（R-02）：现有实现从 **Target 的 `model_state.attn_metadata`** 里过滤出 draft metadata；文档全文只出现 1 次 `model_state`，没有分析这个别名通道 |
| 交付可启用性 | **未证明**（R-07）：仓库自身动机文档点名 GLM-5.2 / DeepSeek-V4，而当前唯一被测试的 DSpark 路径是 **Qwen3-8B（GQA dense）**；若交付目标是 DSA-backed draft，现有 gate 会让"已承诺必须支持"的 DSpark 无法启用 |
| 治理（决策状态、OQ 关闭标准、冲突表、负向测试） | **优于我的设计**，应保留 |
| 与我设计的比较 | 见 §9/§10；我的设计在 R-01/R-02/R-07 上**同样有问题**，其中 R-01 我的框架比 Codex **更差**（详见 §10.3） |

**能否作为最终主文档**：**可以作主干**（骨架、invariants、OQ 表、决策日志、测试矩阵），但必须把 R-01/R-02 的处理写进正文、把 R-03/R-05 的定义收紧、把 R-07 升级为冻结前交付物。在此之前的"Frozen"标记不能覆盖 capture 路线与 AR metadata 存储。

---

## 2. Shared Architecture Agreement

两份 Final Design 在以下各点上一致，并且**我逐条核过源码、认定为正确**——这些应视为已收敛部分，不再重复争论：

| # | 共识 | 源码依据 |
| --- | --- | --- |
| A1 | Draft 与 Target **共享** `BlockTables` 对象；`input_block_tables[g]`/`slot_mappings` 与 Target 同源，**不可原地窗口化** | `vllm/v1/worker/gpu/spec_decode/speculator.py:287`；`block_table.py:71-81` |
| A2 | slot mapping 由 authoritative `block_table_ptrs` 或 **full gathered table** 产生，窗口不得进入写路径 | `block_table.py:93-97,190-221`；`vllm_ascend/worker/v2/block_table.py:82-114`；DFlash 的 `dflash/speculator.py:375-409` |
| A3 | 窗口必须在"所有物理 slot 计算完成之后、backend 派生状态之前"应用 | `dflash/speculator.py:375,451`；`autoregressive/speculator.py:515` |
| A4 | 窗口起点必须在 proposal 级**冻结**；`future_offset` **不是常数** | MRV1 一次 apply + 之后长度递增：`llm_base_proposer.py:1119-1127,2073-2077,2134-2136` |
| A5 | 不对齐 span 时**不得默认用 lcm**；不可表达则 fail closed | 反例 `L=300,W=128,B_legacy=64,span=48` ⇒ lcm=192 ⇒ `S=0`、visible 172→300 |
| A6 | CPU length 兜底必须收口；`visible_upper` 用**同一** canonical `S` 平移并夹到容量 | `worker/v2/attn_utils.py:253-260`（`np.full(max_seq_len)`）；`min(max(U-S,exact),capacity)` 的反例：`L=150,U=200,W=100,b=64` |
| A7 | 每个 step 从 canonical full source **全量重写**，不做增量、禁止 window-of-window | gather 只写 `[0,num_blocks)`：`block_table.py:251-272` |
| A8 | 源侧必须受 per-row `valid_num_blocks` 约束（不能只看 row width） | 同 A7；`num_blocks` 是 UVA 张量且 kernel 已在用：`block_table.py:61,170-171` |
| A9 | 不用 ContextVar / module-global / `_EXTRA_CTX` 运输 view | `_EXTRA_CTX.is_draft_model` 直到 forward 才设置：`worker/v2/spec_decode/autoregressive/aclgraph.py:179-180` |
| A10 | DSA/SFA 的 `update_graph_params()` 是 **no-op** ⇒ 不能依赖 replay 换 pointer；capture 期 op 会捕获 index buffer 的 data pointer | `sfa_v1.py:885-897`；`dsa_v1.py:1619-1631`；`dsa_v1.py:420-436`（docstring） |
| A11 | MTP 必须按 **normalized method** 判定 warn+ignore；不能因落到 Eagle 类而启用 | `worker/v2/spec_decode/__init__.py:68-71`；`vllm/config/speculative.py:1936-1940` |
| A12 | 第一版不重构 MRV1 adapter；MRV1 作 golden oracle | scope 控制，三份一致 |
| A13 | Flashcomm 不是 block-table layout owner；DCP local 必须用 `prefix(E)-prefix(S)` | `ascend_config.py:639-657`；`vllm/v1/attention/backends/utils.py:1088-1133`（非线性） |
| A14 | padding 契约 = "无可观察副作用"（读被裁掉、写为零），**不要求** dummy block id 与 active 不相交 | `attention_v1.py:340-360` 注释原文："So any valid positive KV length / zero block row is fine" |

---

## 3. Critical Findings

### R-01 — `DIRECT_CAPTURE_BOUND` 被写成"默认"，但其注入点在 upstream 且没有参数通道；可行性正是文档自己的 Open 项

- **Severity：Critical**
- **Codex 章节与原文**
  - §19.2 表格："`DIRECT_CAPTURE_BOUND` … capture 时直接让真实 backend operand 引用 dedicated narrow persistent backing；replay 只更新内容 | **默认地位：默认推荐**"
  - §19.2 末句："'capture 时 full shape、replay 时 narrow shape' 不允许 …；**同 shape 但不同地址也不等价**"
  - §19.4："capture dummy 也必须通过同一 provider/capture binding 构造合法 Window carrier，而不是先 capture full table 再期待 runtime 自动变窄"
  - §31.1 冲突表："**narrow direct-capture 默认**；full-width/task-rebind 仅条件 fallback"
  - §29 OQ-17："Ascend override 可承载多数 plumbing → **原型证明无需改 upstream；若不能，评审最小显式 hook**"（未关闭行为：**不用隐式 duplicate/monkeypatch 绕过**）
- **当前 checkout 证据（capture 期 metadata 的三个入口与它们的表来源）**
  - DFlash/DSpark：`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:36` 取 `input_block_tables = block_tables.get_dummy_block_tables(num_reqs)`，`:55` 调模块级 `build_attn_metadata(...)`。**表来源写在 upstream 函数 `_prepare_dflash_inputs_to_capture(num_reqs, num_tokens, input_buffers, block_tables, attn_groups, kv_cache_config, max_model_len, skip_attn, causal)` 内部**（`:24-34`），**签名里没有任何 binding / workspace / view 参数**。
  - Ascend 现有的接入方式是**导入期符号重绑定**：`vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26`（`cudagraph_module.build_attn_metadata = build_attn_metadata`），它替换的是 **builder**，**不是表来源**。
  - AR/Target：`vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:111` 调 upstream `prepare_inputs_to_capture(...)` → `vllm/v1/worker/gpu/cudagraph_utils.py`（dummy 表约 `:785`、`model_state.prepare_attn` 约 `:820`）→ Ascend `worker/v2/model_states/default.py:95-121`；同样没有 view 参数。
- **为什么该设计不成立（或前提未证明）**
  1. 要让 capture 期 metadata 用 workspace 的窄表，必须改变**表的来源**，而不是 builder。可用的手段只有三条：
     - (i) 在 Ascend 侧重绑定 upstream 的 `_prepare_dflash_inputs_to_capture` / `cudagraph_utils.prepare_inputs_to_capture` 为 Ascend 版本 —— 但这两个函数是**模块级自由函数**，拿不到 speculator/workspace 实例；要把 binding 传进去只能靠**模块级可变状态**，这被文档自己的 D03（§10.3/§20.1）**明确禁止**；
     - (ii) 修改 upstream 签名，显式增加 binding/view 参数 —— 这就是 OQ-17 未关闭项，且与 §30.3"首批不修改 upstream"、§30.3 末句"若最终证明必须增加上游 vLLM hook，应先记录 OQ-17 关闭证据"冲突：**文档一边把"不改 upstream"写成边界，一边把依赖它的路线写成默认**；
     - (iii) 在 Ascend 的 `DFlashAclGraphManager.capture()`（`worker/v2/spec_decode/dflash/aclgraph.py:62-84`）里**整体重实现** upstream 的 capture 循环（warmup/descriptor/逐 descriptor 捕获），因为 `super().capture()` 内部会调用那个自由函数。这是一个不小的 fork，文档没有把它列为工作量。
  2. 同一问题在 AR 侧更隐蔽：capture 走的是 **Target 与 Draft 共用**的 `model_states/default.py:prepare_attn`，只能靠 `_EXTRA_CTX.is_draft_model`（capture 期由 `model_capture_wrapper` 置位，`autoregressive/aclgraph.py:90`）区分 Draft/Target —— 而 **`_EXTRA_CTX` 正是 D03 禁止的隐式通道**。
  3. 因此 §19.2 的"默认推荐"在**没有任何一条被证明可用的注入路径**的前提下被给出；能证明的三条路要么违反 D03，要么违反"不改 upstream"，要么是未评估的 fork。OQ-17 把这件事标为 Open 是对的，但 §19.2/§31.1 把它写成默认是不自洽的。
- **最小反例 / 可复现场景**
  ```text
  场景：Window ON + DFlash + FULL_DECODE_ONLY + 任意 backend
  1) capture: upstream _prepare_dflash_inputs_to_capture 用 BlockTables.get_dummy_block_tables() 的
     full 宽度零表 → builder 收到的 block_table.shape = [num_reqs, full_row_width]
  2) replay: 按 §19.2 要求传 workspace 窄表 [R, C_g]，C_g = ceil((W+B_legacy-1)/span)
  3) 二者 shape 不同（违反 §19.2 自己的"不允许"）；即使强行同 shape，
     captured op 读的是 capture 期那块 storage（DSA/SFA updater 是 no-op，A10）→ 窗口内容永远不生效
  结论：在不改 upstream、不用隐式状态的前提下，§19.2 的默认路线无法落地。
  ```
- **我的设计是否犯同样问题：犯了，而且框架更差。**
  我的 `DS Final` §19.3 把 `W1`（capture 用 unwindowed dummy 定形状）保留为 Route P 的做法，理由写的是"形状由宽度不变式保证一致"——**这正是 Codex 的 R-11 已经反驳的论证**（同 shape 不解决 no-op updater 的地址问题）。我虽然在 §9.1 的矩阵里把 SFA/DSA 划到 Route B（写进 builder 自有 buffer），但**Route P 本身对 GQA/MLA 仍然依赖 pointer rebind**（= Codex 的 `TASK_REBIND`，Codex 标为条件、非默认），我却把它当作首期默认。也就是说：**同一件事，Codex 标"Conditional"，我标"默认"**。这一条我的设计比 Codex 更差。
- **Resolution：Accepted（对 Codex）；同时修正我自己**
- **替代方案（架构层，二选一，必须写进正文并二值化）**
  - **方案 α（推荐先做）**：把 `DIRECT_CAPTURE_BOUND` 降级为 `Conditional`，并显式接受 **upstream 最小显式 hook**：给 `_prepare_dflash_inputs_to_capture` 与 `prepare_inputs_to_capture` 各加一个**可选** `draft_view: DraftAttentionView | None = None` 参数（默认 None 即完全等价现状），由 Ascend 的 graph manager 传入。这样 (a) 不需要隐式状态，(b) upstream 改动是**可选的、默认 off 的、零行为变化**的，符合 OQ-17 的"最小显式 hook"，(c) capture 与 replay 天然同 backing、同 shape。
  - **方案 β**：若 upstream 不接受改动，则首期只启用**不依赖 capture 变化**的组合：即只做 **eager**，FULL 全部 fail closed，并把这一点写进 §9 的 readiness（不是 OQ）。
  - 无论 α/β，都要把 OQ-17 从"Open"改为"**冻结前必须关闭**"，并在 §19.2 表格里把三条路线的"是否已证明可用"列出来（当前三条都未证明）。

### R-02 — AR 的 draft metadata 存在 Target 的 `model_state.attn_metadata` 里；文档未分析这条别名通道，会导致 FULL prefill 静默不带窗口 / 或反向污染 Target

- **Severity：Critical**
- **Codex 章节与原文**
  - §12.1 first pass："必须：1. 保留 Target metadata 和 Target forward 完全不变；…5. 通过 Draft-only builder 重建 Draft first-pass metadata"
  - §19.1："每个 Window-enabled graph 组合都必须覆盖：1. capture-time dummy metadata；2. eager/live metadata build；3. replay-time metadata rebuild / graph parameter update"
  - §14 表格："Target metadata | ModelRunner/model state | 否 | **禁止** | Target forward/verification"
  - 全文 `model_state` 只出现 **1** 次（`grep -c` 结果），且不是在讨论这个别名。
- **当前 checkout 证据**
  - `vllm_ascend/worker/v2/model_states/default.py:94-95`：
    ```python
    # attn_metadata is needed when update_full_graph_params, but no way can get it now.
    # Temporarily store it in model_state.
    self.attn_metadata = build_attn_metadata(...)
    ```
    ⇒ **Target 的 per-layer metadata dict 被存在 `model_state.attn_metadata`**，并且它同时是 Target 侧 **graph 参数更新**的数据来源。
  - `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:661-664`（`build_draft_attn_metadatas`，即 AR FULL replay 的入口）：
    ```python
    attn_metadata = self.model_state.attn_metadata
    attn_metadata = {name: metadata for name, metadata in attn_metadata.items()
                     if name in self.draft_attn_layer_names}
    ```
    ⇒ **AR 的 draft metadata 是从 Target 的那份 dict 里"过滤 draft layer 名"得到的**。
  - 同一函数的两条分支：`is_draft_model_prefill=True` → `_prepare_replicated_prefill_attn(attn_metadata, ...)`（继续基于**过滤后的 Target metadata**，`:666-675`）；decode → `_init_decode_draft_attn_metadatas`，而后者对 **GQA/MLA 会重建**（`:702-710` 调 `_build_draft_attn_metadata`），对 DSA/SFA 直接 `return []`（`:691-694`）。
- **为什么该设计不成立（或前提未证明）**
  1. **FULL prefill 会静默丢失窗口**：窗口 ON 时 §12.1 要求"重建 Draft first-pass metadata"，但 **FULL replay 期并不走重建**，而是走"过滤 `model_state.attn_metadata`"这条路径。除非有人把窗口化的 draft metadata **写进** `model_state.attn_metadata` 的对应 key，否则 replay 拿到的是**用 Target full 输入构建的** metadata ⇒ **eager 有窗口、FULL prefill 无窗口**，两者语义不一致，且不报错。
  2. **写进去就是 Target 污染通道**：`model_state.attn_metadata` 是 Target 侧 `update_full_graph_params` 与 Target graph capture 依赖的对象（同注释）；把窗口化的 draft 层条目写进去，等于在一个被 Target 侧读的 dict 里放入 Draft-only visible 语义。虽然 layer key 不相交（`draft_attn_layer_names` vs target 层），但 dict **同一个对象**、并且下游是按"整份 metadata"使用的（例如 `set_forward_context(attn_metadata, ...)` 与 `update_full_graph_params(..., forward_context)`），是否安全需要显式证明，而不是默认。
  3. 文档的 I01（§8）与 §14 都只声明"Window view 不可达 Target"，但**没有为"Draft 的重建 metadata 存在哪里"指定 owner**，也没有覆盖"FULL replay 从 Target 的 dict 里取 draft metadata"这条既有事实。OQ-06 只是把"AR first pass 字段级 parity + graph 验证"作为门禁，没有暴露这个存储别名问题——门禁是对的，但**不够，它证明不了"存在一处可以安全存放重建结果的地方"**。
- **最小反例 / 可复现场景**
  ```text
  配置：Eagle3 + Window ON + FULL_DECODE_ONLY，K≥2，单请求长上下文
  - eager 路径：§12.1 重建 → draft 首步读 [S,L0) ⇒ 窗口生效
  - FULL 路径：run_fullgraph → build_draft_attn_metadatas(is_draft_model_prefill=True)
               → 过滤 model_state.attn_metadata（Target 构建，full）
               → 若无人替换该 key，draft 首步读 full context ⇒ 窗口不生效
  外部表现：同一配置下 eager 与 FULL 的 acceptance 明显不同；不报错、不告警。
  ```
- **我的设计是否犯同样问题：犯了。** 我的 `DS Final` §19.3/§12.1 讨论了"首步必须重建、且与 Target 字段逐位等价"，但**从未提到 `model_state.attn_metadata` 是 draft metadata 的既有存放处**，也没有指定重建结果存在哪里。这一条是我的遗漏，Codex 也没有覆盖——**属于两份设计共同的盲点**。
- **Resolution：Accepted（两份设计都要改）**
- **替代方案**
  1. 在 `DraftWindowWorkspace` 之外，为 AR 增加一个 **`draft_metadata_store`**（speculator-owned，`dict[str, Any]` 或等价的 per-layer 容器），并让"FULL replay 的 draft metadata 来源"显式指向它：
     - `build_draft_attn_metadatas()` 不再从 `self.model_state.attn_metadata` 过滤，而是 `self._draft_metadata_store`（Window OFF 时该 store 可以**直接引用** Target dict 的过滤结果，保持零回归）；
     - 该 store 的内容在 Window ON 时由 §12.1 的重建结果填充；在 Window OFF 时保持现有过滤语义。
  2. 增加一条负向测试：**断言 Window ON 且 FULL prefill 时，draft 层 metadata 的 `block_table_tensor`/`seq_lens` 与 Target dict 中同层 entry 不同**（即证明窗口真的进去了），并断言 Target 侧 `update_full_graph_params` 看到的 Target 层 entry 未被改动。
  3. 把这条写进 invariants：**I01′ — Draft 重建 metadata 的存储不得与 Target 的 metadata store 是同一可变对象**（允许 Window OFF 时复用）。

---

## 4. Major Findings

### R-03 — `L0` 的定义有歧义：必须钉死为"未扣本轮 rejection"的 draft device `seq_lens`，否则 anchor 偏早一个 legacy 块、窗口被静默削弱

- **Severity：Major（正确性/兼容性，静默）**
- **Codex 章节与原文**：§5 Terminology："`L0[r]` | AR proposal 开始时请求 `r` 的 **full context end**"；§11.1："`H[r] = L0[r] + K`；`S_legacy = align_down(max(H-W,0), B_legacy)`"；§11.1："AR 的 `S_legacy` 在 proposal 开始时计算一次"。
- **当前 checkout 证据**
  - `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:700-770`（`prepare_prefill_inputs` kernel）：
    ```python
    seq_len = tl.load(seq_lens_ptr + req_idx)          # ← 先读，未扣 rejection
    num_rejected = tl.load(num_rejected_ptr + req_idx)
    query_len -= num_rejected                           # ← 只裁 query
    ...
    tl.store(draft_seq_lens_ptr + req_idx, seq_len)     # ← draft 缓冲拿到的是未扣版本
    ```
  - MRV1 侧同一语义：`llm_base_proposer.py:1174-1178` —— apply **之后**才为"下一步"扣 rejection（`next_step_seq_lens.sub_(num_rejected_tokens_gpu)`），说明 apply 用的是**未扣**的 `seq_lens`。
- **为什么该设计不成立（或前提未证明）**："full context end"既可以读成"本轮 scheduled 的绝对 end"（未扣，= draft 缓冲里的值），也可以读成"rejection 修正后的有效 context end"（= `L0 - r`）。若实现者取后者，`S` 会**偏早**（恰好一个 `B_legacy`），可见集合**变大** ⇒ **窗口被削弱**（不是"少看历史"）；外部表现是"开了窗口但收益不如预期"，比报错更难发现，也使 MRV1/MRV2 的 acceptance 不可直接比较；`visible_s` 的逐 step 递推起点同样随之偏移。文档没有任何一句话排除这种读法。
- **最小反例（精确条件与偏差方向）**
  ```text
  令 D = L0 + K - W，B = B_legacy
  S_ok  = floor(D / B) * B                 # 未扣（正确）
  S_bad = floor((D - r) / B) * B           # 先扣 r（错误）
  二者不等 ⟺ r > (D mod B)；不等时必有 S_bad = S_ok - B（恰好早一个 legacy 块）

  可复现最小例：B=64, W=128, K=0
    L0=190, r=5: D=62  → 62 mod 64 = 62 > 5 ⇒ 相同（S=0）      # 差异并非必然出现
    L0=204, r=5: D=76  → 76 mod 64 = 12 > 5 ⇒ 相同（S=64）
    L0=193, r=5: D=65  → 65 mod 64 = 1  < 5 ⇒ **不等**
        S_ok  = floor(65/64)*64 = 64  → visible = 193-64 = 129
        S_bad = floor(60/64)*64 = 0   → visible = 193-0  = 193   # 多读 64 个 token
  触发概率约 r / B_legacy（r < B_legacy），不是罕见事件。
  ```
  ⇒ 差异**不是必然出现**（取决于 `(L0+K-W) mod B_legacy` 与 `r` 的相对大小），因此必须**定义级钉死 + 差分测试**，不能靠"通常相同"或"端到端 acceptance 看起来还行"。
- **我的设计是否犯同样问题：没有（我的 `DS Final` §12.3 明确写"`L0` = Target 本轮 device `seq_lens`（未扣 rejection）"并给了 kernel 依据），但我的表述**没有**给出"跨边界才分离"的分析，也没有配差分测试。**
- **Resolution：Accepted**
- **替代方案**：把 Terminology 的 `L0` 改写为"**AR proposal 开始时 draft `input_buffers.seq_lens` 的值（`prepare_prefill_inputs` 写入的、未扣本轮 rejection 的绝对 end）**"，并在 `H=E_prepared`（DFlash）处补一句"DFlash 的 `E_prepared` 是 kernel 扣完 rejection 再补 query 之后的值"。测试：`L0 ∈ [B_legacy-1, B_legacy, B_legacy+1]` 附近、`r>0`、`K>0` 的 golden 对拍。

### R-04 — `_seq_lens_cpu` 缺席长度类型系统：一个未来的生产者会用 **full** 值赢下 priority

- **Severity：Major（静默正确性）**
- **Codex 章节与原文**：§17.1 的类型表列出 `DeviceFullExact / DeviceWindowExact / CpuFullExact / CpuWindowExact / CpuFullUpper / CpuWindowUpper / CaptureCapacity / BackendEffectiveMax / DcpLocal*` —— **没有 `_seq_lens_cpu`**；§17.2 只给 `visible_exact/upper` 的派生。全文 `_seq_lens_cpu` 出现 1 次且非本议题。
- **当前 checkout 证据**
  - `vllm_ascend/attention/utils.py:569-576`：
    ```python
    if common_attn_metadata._seq_lens_cpu is not None:
        seq_lens = common_attn_metadata._seq_lens_cpu[:num_reqs]      # ← 最高优先级
    elif common_attn_metadata.seq_lens_cpu is not None:
        seq_lens = common_attn_metadata.seq_lens_cpu[:num_reqs]
    else:
        seq_lens = common_attn_metadata.seq_lens[:num_reqs].to("cpu")
    ```
  - MRV1 的 adapter **会**窗口化 `_seq_lens_cpu`（`spec_decode/utils.py:165-169` 的三个字段之一）；MRV2 的漏斗当前**不写**该字段（`worker/v2/attn_utils.py:309-330` 只赋 `seq_lens_cpu` / `seq_lens_cpu_upper_bound`）⇒ 今天为 `None`，所以暂时安全。
- **为什么该设计不成立（或前提未证明）**：类型系统若不含该字段，就没有任何规则约束它；一旦后续（例如为了修 MRV2 的 CPU 长度问题）有人给漏斗或 metadata 填上 `_seq_lens_cpu`，`_select_seq_lens` 会**优先**取它——如果那是 full 值，就构成 Codex 自己列为 Critical 的"narrow table + full length"错配（§7.4/§23.1 明令禁止）。缺一个"必须为 None 或必须被窗口化"的显式约定，等于把最危险的路径留给未来。
- **最小反例**：任何未来 PR 在 `worker/v2/attn_utils.py` 里加一行 `_seq_lens_cpu=<full 值>`（例如为了对齐 MRV1 语义），则 MLA/GQA 的 draft attention 立刻按 full 长度读取窗口表 ⇒ 读 `[needed, C_g)` 之后的零列 ⇒ block id 0 ⇒ 读到 cache 第 0 块。**全程不报错。**
- **我的设计是否犯同样问题：部分犯。** 我的 `DS Final` §17 也没有把 `_seq_lens_cpu` 列为类型化字段，只在 §17.3 讨论了 `seq_lens_np`/`upper` 的 fallback。两份都需要补。
- **Resolution：Accepted**
- **替代方案**：在 §17.1 增一行 `LegacyCpuMirror(_seq_lens_cpu)`，规则为"**必须为 `None`，或必须与 `CpuWindowExact` 同源**"，并加一条调试断言：`view is not None ⇒ metadata._seq_lens_cpu is None or windowed`。同时加一条静态检查（对象构造处）防止未来写入 full 值。

### R-05 — `U`（CPU upper）的推导未绑定"apply-time 的 step/query stretch"，会给出过小上界

- **Severity：Major**
- **Codex 章节与原文**：§17.1 表格："`CpuFullUpper` | full optimistic upper `U` | runner/input owner | 当前路径按需"；§17.2："`raw_upper = max(U - S, visible_exact)`; `visible_upper = min(raw_upper, V_capacity)`"。**没有**任何一句要求 `U` 必须包含"当前 draft step / parallel query"的增量。
- **当前 checkout 证据**
  - AR 的 draft CPU 长度生产者会**加 step**：`worker/v2/spec_decode/autoregressive/speculator.py:815-822`（`_calc_next_seq_lens_cpu`：`clamp(seq_lens_cpu + step)`）。
  - Draft 公共 builder 的 upper 也是"target upper + step"：`vllm/v1/worker/gpu/spec_decode/speculator.py:326-334`（`draft_seq_lens_cpu_upper_bound = target_upper + step`）。
  - DFlash/DSpark 的 `step` 等于 `num_query_per_req`。
- **为什么该设计不成立（或前提未证明）**：若实现的 `U` 取自 **未加增量** 的 Target upper（例如直接读 `input_batch.seq_lens_cpu_upper_bound`），那么 `visible_upper` 会比"现有 builder 在该 apply time 实际使用"的值小 `step`（AR）或 `num_query_per_req`（DFlash/DSpark）。而 upper 是 backend 的 **tiling/plan 上界**（例如 `max_seqlen_kv`），过小会造成 tiling 不足/形状不匹配；在 FULL 下还可能让 captured plan 与 runtime 不符。反之，若误用了**别的 step 的** upper，则会过宽。文档此前版本（Codex v2）写过这条要求（"CPU upper 输入必须是现有 draft builder 在该 apply time 使用的完整 upper 语义（包括对应 step/parallel query stretch）"），**Final 版把它删掉了**，属于回归。
- **最小反例**：`K=7`、AR 第 3 步；Target upper = 4000、`visible_exact = 900`；正确 upper = `min(max(4003 - S, 900), capacity)`，若误用 4000 则 upper 少 3；在 `capacity = ceil((W+B-1)/B)*B` 恰好卡在边界时会让 `needed_g` 少一列 ⇒ 最后一列未写而被读（读 inert 值，attention 输出错，不报错）。
- **我的设计是否犯同样问题：没有。** 我的 `DS Final` §17.2/§17.3 明确写了 `U` 是 apply-time upper 且必须与现有 builder 的增量一致（并给了 `capacity_g` 夹紧）。这一条 Codex 应向我的设计靠。
- **Resolution：Accepted**
- **替代方案**：在 §17.1 的 `CpuFullUpper` 行加约束："**必须是该 apply-time 的 upper（含 step / parallel query stretch），并由与现有 builder 相同的表达式生成**"；测试：AR 每 step、DFlash `Q=K+1`、SAMPLE_FROM_ANCHOR `Q=K` 三种情形下逐一断言 `window_upper` 与"现有 builder 的 upper − S"逐位相等。

### R-06 — DSA/SFA 的 gate 是"必要的"，但**欠分解**：无法增量关闭，且会阻塞契约上"必须支持"的 DSpark

- **Severity：Major（gate 粒度 + 交付阻塞）**
- **Codex 章节与原文**：§21.3："两种实现理论上都可能成立 … 但**不能把两种坐标混合，也不能再应用两次 S**。在真实算子优先级、index 坐标和可见 slot 集合测试闭合前，DSA provider 保持 `UNSUPPORTED`；设计**不宣称**'只提高 start_pos'或'只裁表'已经被源码证明。"§31.1："**不接受任一未证实公式**；采用 backend provider 边界，集合级设备测试前 fail closed。"§29 OQ-03/OQ-04。
- **当前 checkout 证据（可据以**分解** gate 的源码）**
  - `attention/dsa_v1.py:420-461`（`build_dspark_swa_indices`）：输入是 `block_table / num_speculative_tokens / window_size / block_size / query_start_loc / seq_lens`；内部 `query_lens = diff(qsl)`、`prefix_lens = seq_lens - query_lens`、`start_pos = (prefix_lens - window_size).clamp(0)`、`visible_lens = seq_lens - start_pos`、`pos = start_pos + cols`，随后（默认）`pos // block_size` → 查表得 physical slot。**该函数在其输入坐标系内是自洽的**：若表与 `seq_lens` 同时 rebase，则 `prefix/start_pos/pos` 全部是窗口相对量，查表正确。
  - 真正未证的风险是**混用**：同一条 DSA 路径上还有其它"从绝对量派生"的状态与（rebase 后的）表一起进入算子：
    - compressor 相关：`dsa_v1.py:884-890` 注释明确"C4/C128 physical slots are generated later from the logical block table by `compressor_metadata`"（`:1240-1260` 的 `req_metadata` 里带 `start_pos` / `sas_metadata` / `qli_*`）；
    - `dsa_v1.py:1088-1100`：`start_pos_prefill` 由 `seq_lens - query_len` 派生并写 builder 自有 buffer；
    - `dsa_v1.py:1107`：`ori_win_left, ori_win_right = self.model_config.hf_config.sliding_window - 1, 0` —— **没有 None 检查** ⇒ 该路径必然存在 native window（这同时把审计范围收窄到"有 native window 的模型"）。
  - SFA 侧：`sfa_v1.py:296-307`（top-k 长度由 `indexer.get_topk_lengths(positions)` 用**绝对** positions 派生）+ `:198-219`（算子消费 explicit indices + table + topk length）；native window 参数在 `:114-119` 被关闭。⇒ SFA 需要的不是"坐标 rebase"，而是"额外一个 window-relative visible count"。
- **为什么该设计不成立（或前提未证明）**：gate 本身**必要**（混用风险真实存在，且 `mix` 的后果是读错物理块）。但 Codex 把它写成**黑箱**"在闭合前 UNSUPPORTED"，没有给出：
  (a) 需要审计的**具体子路径清单**（上述 compressor/QLI/SAS/`start_pos_prefill`）；
  (b) 哪些子路径**已经可以**从静态源码判定为安全（`build_dspark_swa_indices` 的坐标自洽性）；
  (c) 一个可执行的 **slot-set oracle** 规格（用什么输入、比对什么集合）。
  结果是 gate 无法增量关闭——团队只能"要么全不信、要么冒险全信"。同时 §9 把 DSpark 标为"必须支持"而 §21.3 把 DSpark 最可能的 sparse backend 标为 UNSUPPORTED，**交付面与支持面在同一份文档里正面冲突**（见 R-07）。
- **是否过度保守**：**不是过度保守，而是粒度错误**。把"必须审计子路径 + oracle 规格"写清后，DSA 的 gate 可以在一次专项里关闭；反之按现在的写法，它只会长期悬置。
- **我的设计是否犯同样问题：犯了一半。** 我的 `DS Final` §21.2 给出了"shifted table + shifted length 自然求交"的**机制**，并加了 OQ-4 的审计 gate（点名 compressor/QLI/SAS）——比 Codex 更可执行；但我写"自然求交"的语气偏肯定，而 Codex 拒绝宣称任一公式已被证明，**在证据纪律上 Codex 更稳妥**。正确做法 = Codex 的措辞纪律 + 我的可审计分解。
- **Resolution：Accepted（采用 Codex 的结论纪律 + 我的分解）**
- **替代方案**：把 §21.3 改写为
  ```text
  DSA 审计清单（缺一即 fail closed）：
  A. build_dspark_swa_indices 的坐标自洽性（可静态判定：已核，见证据）
  B. 与 rebase 后的表同用的、由绝对量派生的状态：compressor C4/C128 slot、QLI、SAS、start_pos_prefill
  C. native window 与 draft window 的右边界差异（dsa_v1.py:1107 暗示 native 必然存在）
  D. slot-set oracle：给定 (S,E,native window,positions) 断言算子实际读到的物理 slot 集合
     == V_draft ∩ V_native ∩ V_resident
  ```
  并给出"关闭后 DSA 从 UNSUPPORTED → Conditional"的路径。

### R-07 — 交付可启用性未被证明：仓库动机模型与当前被测试模型不是同一个

- **Severity：Major（计划/交付）**
- **Codex 章节与原文**：§9 表格把 EAGLE3/DFlash/DSpark 的 `首期 readiness` 全部写成 **Conditional**，并说"DSA/SFA/多 group capability 逐项开放"；§1 说"目标支持面是 MRV1 公开契约中的 EAGLE3、DFlash、DSpark"。**没有任何一句说明"若交付目标落在 DSA/SFA/MLA-CPU 上，本设计首期会启用 0 个组合"**。
- **当前 checkout 证据**
  - 仓库自身动机文档点名 GLM-5.2 + DSpark（及 DeepSeek-V4 advisory）：`docs/source/developer_guide/Design_Documents/speculative_kv_sliding_window.md:3-15`、`:26-30`。
  - 而当前 checkout 里**唯一被 E2E 覆盖**的 DSpark 组合是 Qwen3-8B：`tests/e2e/pull_request/one_card/spec_decode/utils.py:29-34` → `"main": "Qwen/Qwen3-8B"`, `"spec": "deepseek-ai/dspark_qwen3_8b_block7"`（Qwen3-8B 是 dense GQA 模型 ⇒ 该路径是 GQA/dense）。
  - DSpark 的 `attn_architecture` 判定只区分 MLA / GQA / **None**：`worker/v2/spec_decode/dspark/speculator.py:131-136`（`issubclass(backend, AscendMLABackend) → "MLA"`；`AscendAttentionBackend → "GQA"`；否则 `None`）⇒ 若 draft 落 DSA/SFA，该字段为 `None`，而 DSA/SFA 恰好是 gate 关闭的两类。
  - 另外 MLD/MLA 是 **CPU 优先**：`vllm_ascend/attention/mla_v1.py:500-509` + `attention/utils.py:569-576`；而 DFlash/DSpark **没有** rejection-corrected CPU exact 生产者（`autoregressive/speculator.py:815-822` 注释明确"不减 rejection"）⇒ 按 §17.2"若 backend 需要 CPU exact 而 method 不能在无 hot-path D2H 下生产，则该组合 fail closed"，**MLA 组合首期会被关闭**。
- **为什么该设计不成立（或前提未证明）**
  1. 把 DSA/SFA 与 MLA 都 fail closed 之后，首期"已承诺必须支持"的三个 method 中，**可能只剩下 GQA-dense 一条路**（DFlash/DSpark × GQA）。这与"支持既定 speculative methods"的目标差距很大，而文档没有把这一后果写出来供决策。
  2. 该问题的关闭只需要一份**可执行证据**：在交付模型上运行 capability inventory（文档 §22.4 已经写了要记录 inventory，但没有把它列为**冻结前**交付物，而是留在 OQ-08/OQ-05 里）。这意味着团队可能在实现完捕获绑定之后才发现"没有可启用的组合"。
- **最小反例 / 可复现场景**：交付目标是 GLM-5.2/DSV4-family DSpark（动机文档所指），其 draft 走 DSA（`dsa_v1.py:1107` 说明该路径必然带 native window ⇒ sparse 家族）⇒ 按当前 gate：DSA UNSUPPORTED、native/recycling 未证明 ⇒ **Window 无法启用**。而 Qwen3-8B 的 GQA 组合可以启用——**测试通过 ≠ 交付可用**。
- **我的设计是否犯同样问题：犯了，而且更糟。** 我的 `DS Final` §9.2 直接给出"E1（首期）：dflash/dspark × {GQA, MLA} × eager"——其中 **MLA 的 E1 是虚的**（CPU exact 不可得 ⇒ 按我自己的 §17 也必须 fail closed），等于我给出了一个**可能为空或只剩 GQA** 的"首期集合"，却没有标注该风险。Codex 用"全部 Conditional"至少没有制造这种错觉。
- **Resolution：Accepted（两设计都要改）**
- **替代方案**：把"**在交付模型上产出 capability inventory（gid × backend × causal × KV spec × native window × column span × CP）并据此写出首期可启用集合**"提升为**冻结前必须完成的第一项工作**（不是 OQ），并据此重排实现顺序：
  - 若交付目标是 DSA/SFA/MLA-CPU ⇒ 先把 R-06 的审计（DSA）与 CPU-exact 生产者（MLA）放到 Graph 之前；
  - 若交付目标就是 Qwen3-8B 这类 GQA-dense ⇒ 明确写下"首期只承诺 GQA-dense"，并把 DSA/SFA 作为 Week4+。

### R-08 — Host ring 与既有 `UvaBufferPool` 的关系未定义，存在双重记账/双重退休的风险

- **Severity：Major**
- **Codex 章节与原文**：§15.3："host-side CPU exact、upper、request-order fingerprint、valid counts/plan staging **使用 ring**。容量必须覆盖'同时仍被 metadata、graph update task 或 device consumer 引用、尚未 retire 的 host generations'最大值"；§20.2 同上。全文 `UvaBufferPool` 出现 **0** 次（`grep -c`）。
- **当前 checkout 证据**：`vllm/v1/worker/gpu/buffer_utils.py:19-26`（`UvaBufferPool` 默认 ≥2 round-robin slot，要求 reader retire 后方可复用）、`:24`（`set_default_max_concurrency`，由 `vllm/config/vllm.py:589-598` 的 `max_concurrent_batches` 驱动）、`:61` 附近（复用/增长前的 retire 约定）。
- **为什么该设计不成立（或前提未证明）**：窗口的 host 侧状态（CPU exact/upper/fingerprint/valid counts）与既有 UVA 机制**共享同一份 host 事实**；如果新增第二个 ring，则：(a) 两套退休账本必须保持一致，否则一边认为可复用、另一边仍在读；(b) 既有 pool 的深度由 `max_concurrent_batches` 设定，而窗口 ring 的深度按"最大未 retire generation"——两者若不挂钩，就会出现"UVA 池深度 2、窗口 ring 深度 1"这类不匹配，直接导致提前覆盖。文档没有说清是复用还是并列。
- **最小反例**：async scheduling（`max_concurrent_batches=2`）下，step N 的窗口 CPU upper 仍被 graph task update 引用，而 step N+1 已进入 `PREPARING`；若窗口 ring 深度按 1 分配，则 N+1 覆盖 N 的 upper ⇒ graph 参数更新读到错值（**不报错**）。
- **我的设计是否犯同样问题：犯了（不同形式）。** 我的 `DS Final` §20.2 直接把 host ring 深度定为 `≥ max_concurrent_batches`，同样没有说明与 `UvaBufferPool` 的关系，也没有指出该值是**下界**而非充分条件（AR 多 step / graph task 延迟退休可能超出）。Codex 至少把"按最大未 retire generation 定容"写上去了，**这一点 Codex 更好**。
- **Resolution：Accepted**
- **替代方案**：明确二者关系，二选一：(i) 窗口 host 状态**复用** `UvaBufferPool`（把窗口的 generation 映射为 pool 的 slot，并让 pool 的 retire 语义覆盖窗口 reader）；或 (ii) 独立 ring，但深度由**同一** `max_concurrent_batches` 下界 + 运行时 trace 决定，并**共享同一退休事件源**（不允许两套 event）。无论哪种，都要加一条断言："同一 generation 的 host 状态在被标记 free 前，其对应的 device reader/graph task 已完成"。

---

## 5. Minor Findings

| ID | Severity | 问题 | Codex 原文/位置 | 源码证据 | 修复 |
| --- | --- | --- | --- | --- | --- |
| R-09 | Minor→Major | `Expected File Changes` 只到文件级，没给**函数级接入点**，P1 无法直接开工 | §30.2"AR/Eagle speculator 文件：first-pass 独立 Draft metadata、proposal anchor、per-step view" | 实际锚点是具体函数：`worker/v2/spec_decode/autoregressive/speculator.py:573/611`（两个 override）、`:654-684`（replay 入口）、`worker/v2/attn_utils.py:1240-1281`（wrapper/factory）、`worker/v2/spec_decode/dflash/speculator.py:144`（propose wrapper）、`patch_dflash_speculator.py:26`（capture 模块符号） | §30 增加"接入点表"：文件 → 函数 → 现有行号 → 改动性质（新增参数/替换/包装） |
| R-10 | Minor | 引用偏移：native band 的行号 | §21.2 引 `attention_v1.py:595` | band 实际在 `vllm_ascend/attention/attention_v1.py:602-604`（`sparse_mode = 4 if self.sliding_window else 3 if attn_metadata.causal else 0`；`pre_tokens = self.sliding_window or SWA_INT_MAX`）；`:595` 是 `_get_fia_params(...)` 调用行 | 改成 `:602-604` |
| R-11 | Minor | 引用不支撑论断：`states.py:88` | §7.6 引 `states.py:88` 证明"free row 可在同一步复用" | `vllm/v1/worker/gpu/states.py:88` 是 `def num_reqs(self) -> int: return len(self.req_id_to_index)`，与 row 复用无关；row 生命周期的证据在 `model_runner.py:1085/1152`（文档也引了 ✓） | 删 `states.py:88`，或改引 `add_request`/`remove_request` 的实际行 |
| R-12 | Minor | 命名与既有类名不一致 | §7.2"Target 由 `DefaultModelState.prepare_attn()` 调用 Ascend `build_attn_metadata()`"，文件指 Ascend 的 `model_states/default.py:44` | 该文件里是 **`AscendModelState`**（由 `patch_model_state.py` 的 `init_asecnd_model_state` 装入）；`:44` 确实是 `def prepare_attn(` ✓ | 写成"Ascend 的 `AscendModelState.prepare_attn()`（对应 upstream `DefaultModelState`）" |
| R-13 | Minor | 布局 hook 的命名不精确 | §7.2"Draft 的公共基类从 `_build_draft_attn_metadata()` 进入 builder" | upstream #56181 已把该 hook 拆为 `_build_uniform_attn_metadata()` / `_build_attn_metadata()`（`spec_decode/speculator.py:295/514`）；`_build_draft_attn_metadata` 是 Ascend 保留的**兼容入口**（`dspark/speculator.py:188-207` 的 docstring 明确说明） | 改成"上游 live 入口是 `_build_uniform_attn_metadata`/`_build_attn_metadata`；`_build_draft_attn_metadata` 是 Ascend 兼容/图路径入口" |
| R-14 | Minor | upper 的"可材料化容量"是软表述 | §17.2"如果实际 provider 的本 generation 可材料化容量更小，则用其 domain capacity 替代 `V_capacity`" | 列数是每 step 由 `needed_g` 决定的；未写列被读的后果是读 inert（`attention_v1.py:340-360` 说 dummy 读是安全的，但**真实 active row** 读到未写列不是 dummy 语义） | 改为强制：`visible_upper ≤ needed_max_g × span_g`（本 generation 实际写入列数×span），不满足即 fail fast |
| R-15 | Minor | `provider 负责写入` 的**写入者**未指定 | §11.5 描述 provider "maps (S[r], c) -> source column / offset / logical index"，但未说谁执行 copy | 若由 provider 自己写，则每个 backend 都要实现 materialize kernel（与"公共层只有一份数学"冲突）；若由公共 materializer 写，则 provider 只提供映射描述 | 明确"**公共 materializer 执行 copy，provider 只提供映射/容量/验证**"，避免 N 份实现 |
| R-16 | Minor | recycling 证据不全 | §21.5 引 `kv_cache_interface.py:811` | 最强证据是 `vllm/config/vllm.py:602-609` 的 `max_in_flight_tokens` 注释原文："**Recycling-aware KV cache specs (sliding-window, chunked-local)** reserve for this because **out-of-window blocks are freed** on the processed-token basis"（`max_in_flight` 在文档中出现 0 次） | 补该引用，并把"in-flight 期间 resident 集合可能大于名义窗口"写入 §21.5 |
| R-17 | Minor | 呈现层面的内部张力 | §19.2/§31.1 把 narrow direct-capture 写成"默认"，而 D05/D06 是 `Conditional`、OQ-01/OQ-17 未关闭 | 同上 | 统一为"**目标默认**（待 OQ-01/17 关闭）"，并在 §19.2 表格加"是否已证明可用"列 |

---

## 6. Mathematical and Invariant Audit

> 逐条复算 Codex FD 的公式与不变式。除标注外，均判定**成立**。

| # | 公式 / 不变式（Codex FD 位置） | 复算 | 判定 |
| --- | --- | --- | --- |
| M1 | `S_legacy = align_down(max(H-W,0), B_legacy)`，`H = L0+K`（AR）/ `H = E_prepared`（DFlash）（§11.1） | 与 MRV1 `utils.py:132` 同式；DFlash 的 `E_prepared` 等价于 MRV1 apply 时的 `seq_lens`（已含 query） | ✅ 成立（**前提**：`L0` 定义见 R-03） |
| M2 | 每 step `visible_exact_s = E_s - S`，`S` 冻结（§11.1） | 与 MRV1"一次 apply + 长度递增"（`llm_base_proposer.py:1119-1127,2073-2077`）逐位等价：MRV1 的 `seq_lens_group[1] = windowed - r`，再每步 `+1` ⇒ `visible_s = (L0-r)+s-S` ✓ | ✅ 成立 |
| M3 | 禁止"每 step 用固定 `K` 重求起点"；若用 offset 则应是 `H-E_s`（§11.1） | 若每步用固定 K：`S_s = align(L_s+K-W)` 随 `L_s` 右移 ⇒ 窗口滑动、visible 恒为 `W-K`，与 MRV1 不同 | ✅ 成立（这条是三份材料中表述最清楚的） |
| M4 | `V_capacity = W + B_legacy - 1`（§11.3） | `visible = L - S`，`S ≤ L+K-W` 且 `S > L+K-W-B_legacy` ⇒ `visible < W-K+B_legacy ≤ W+B_legacy` ⇒ `visible ≤ W+B_legacy-1` ✓ | ✅ 成立 |
| M5 | `C_g = ceil(V_capacity / span_g)`（§11.3） | `needed_g = ceil(visible/span_g) ≤ ceil(V_capacity/span_g)` ✓（仅当 `first_token_offset = 0`，文档已声明该前提 ✓） | ✅ 成立 |
| M6 | `C_g = ceil((first_token_offset_max + V_capacity)/span_g)`（§11.3） | 当 origin 不落在 span 边界时，第 0 列要覆盖 `offset` 前缀 ⇒ 上式 ✓ | ✅ 成立 |
| M7 | `visible_upper = min(max(U-S, exact), V_capacity)`（§17.2） | 保证 `exact ≤ upper` 且 `upper ≤ 容量` ✓；反例（独立求两个 start 会得到 `upper < exact`）已被排除 ✓ | ✅ 成立（但 `U` 的语义见 R-05；容量应为**本 generation 写入列数**见 R-14） |
| M8 | `0 ≤ visible_exact ≤ visible_upper ≤ materialized_capacity`（I09） | 与 M7 一致 ✓ | ✅ 成立 |
| M9 | `local_window_len = local_prefix(E) - local_prefix(S)`（§17.3） | `get_dcp_local_seq_lens`（`vllm/v1/attention/backends/utils.py:1088-1133`）对 L 非线性；取 `i=1,d=2,rank=1`：`local(4)-local(1)=2-0=2` 而 `local(3)=1` ⇒ 必须用前缀差 ✓ | ✅ 成立（我的设计同结论，已独立复算） |
| M10 | `W ≤ 0` 为配置错误；AR 要求 `W ≥ K`；"任意 `W<K` 都存在 block remainder 令长度非正"（§22.3） | 令 `L=qB+r`，`visible<0 ⟺ S>L ⟺ K-W ≥ B-r`；对给定 `W<K`（`K-W = d ≥ 1`），取 `r ≥ B-d`（即 `L mod B ≥ B-(K-W)`）即可触发 ⇒ 断言成立 ✓ | ✅ 成立（与我的勘误后结论一致；例 `L=63,B=64,K=2,W=1` ⇒ `S=64 > 63`） |
| M11 | 非整除时不得默认 LCM（§11.2） | 反例 `L=300,W=128,B_legacy=64,span=48`：legacy `S=128`（visible 172）vs lcm=192 ⇒ `S=0`（visible 300）✓ | ✅ 成立（**这条是 Codex 从 GPT 处吸收的正确修正**） |
| M12 | `can_represent_origin(S)` + `first_token_offset` 必须被最终算子消费（§16.4） | 若 offset 未被算子消费而 provider 声称可表达，则窗口起点实际被拉回列边界 ⇒ 可见集合变大 | ✅ 成立（表述严谨，优于我的 `min(W,retention)`） |
| M13 | `V_final = V_draft ∩ V_native ∩ V_resident`（I17/§21.1） | 三者都是同一序列上的"后缀区间 + 掩码"类约束，交集是唯一正确语义 ✓ | ✅ 成立（**优于我的** `effective_window = min(W, retention)`：`FullAttentionSpec` 也带 `sliding_window` 字段但只是计算层 band，不做物理回收，见 §7.2 证据） |
| M14 | I11"每 step 完整重写 active capacity、active tail 与 padded rows"（§11.5） | 与 gather kernel 只写 `[0,num_blocks)` 的事实一致 ✓ | ✅ 成立 |
| M15 | I12"No repeated Window：materializer 只接受 typed full source"（§11.4/I12） | 与 MRV1 的 `apply` 每次从 `full_block_table` 重算一致 ✓ | ✅ 成立 |
| M16 | I08"若 backend 为索引映射保留 full-coordinate length，必须使用不同类型并证明它不能扩大最终 read set"（§8） | 这是对"混用坐标系"的正确防御 ✓（同时说明作者意识到 §21.3 的风险） | ✅ 成立 |
| M17 | §11.5 的 copy 有效性三条件（`c < needed_g[r]`、源列 < row width、源列 < `batch_valid_num_blocks`） | 与 gather kernel 只写 `[0,num_blocks)` 的事实一致 ✓ | ✅ 成立 |

**结论**：Codex FD 的数学与不变式部分**没有发现错误**（M4/M5/M7 的边界条件都正确；M9/M10/M11 与我独立复算一致）。需要修的是**定义歧义**（R-03 的 `L0`、R-05 的 `U`）与**一处软表述**（R-14 的容量），不是公式本身。

---

## 7. Source-Level Integration Audit

> 逐个核实 Codex FD 引用的源码位置与语义。

| Codex 引用 | 实际内容 | 判定 |
| --- | --- | --- |
| `spec_decode/__init__.py:23`（§7.1 factory） | Ascend MRV2 `init_speculator()` 的显式分支，末尾 `raise NotImplementedError` | ✅ 正确（我的独立核对一致） |
| `worker/v2/model_states/default.py:44`（§7.2 Target 入口） | `def prepare_attn(self, input_batch, cudagraph_mode, block_tables, slot_mappings, attn_groups, ...)` 的定义行；其内部 `:94-95` 写 `self.attn_metadata = build_attn_metadata(...)` | ✅ 行号正确；但**类名应为 `AscendModelState`**（R-12），且**未提及 `self.attn_metadata` 的存储语义**（R-02） |
| `vllm/v1/worker/gpu/spec_decode/speculator.py:295` + `attn_utils.py:1240`（§7.2 Draft 入口） | upstream `_build_attn_metadata`；Ascend 的 module-symbol 替换 ctx manager | ✅ 正确；建议补 `_build_uniform_attn_metadata`（R-13） |
| `block_table.py:17/148/190`（§7.3） | `BlockTables` 构造；`gather_block_tables(out=...)` 支持 caller-provided destination；`compute_slot_mappings` 读 `block_table_ptrs` | ✅ 正确。**`out=` 支持是"独立 workspace"的关键接口**，Codex 用对了 |
| `dflash/speculator.py:375,513`（§7.3） | `:375-409` 用 `input_block_tables[gid]` 算 context/query slot；`:513` 在 kernel 中 | ✅ 正确 |
| `attn_utils.py:220/253`（§7.4） | Ascend funnel；`seq_lens_np is None ⇒ np.full(num_reqs, max_seq_len)`，`upper is None ⇒ = seq_lens_cpu` | ✅ 正确 |
| `vllm/v1/attention/backends/utils.py:1088`（§7.4） | `get_dcp_local_seq_lens`（非线性） | ✅ 正确 |
| `block_table.py:177`（§7.5） | `get_dummy_block_tables`（返回 persistent 零表） | ✅ 正确 |
| `dflash/cudagraph.py:24`（§7.5） | `_prepare_dflash_inputs_to_capture`（**表来源在这里，是 upstream，无 view 参数**） | ✅ 引用正确，但**未指出这正是 R-01 的阻塞点** |
| `cudagraph_utils.py:766`（§7.5） | `prepare_inputs_to_capture` | ✅ 存在（`grep` 命中） |
| `autoregressive/aclgraph.py:132` / `dflash/aclgraph.py:86`（§7.5） | 两个 Ascend graph manager 的 `run_fullgraph` | ✅ 正确 |
| `attention_v1.py:652`（§7.5） | `register_task(torch_npu.npu_fused_infer_attention_score.out, {... "block_table": block_table ...})` | ✅ 正确（GQA 可重绑的证据） |
| `dsa_v1.py:1621` / `sfa_v1.py:885`（§7.5） | 两者的 `update_graph_params` 都是 `pass` | ✅ 正确 |
| `model_runner.py:1085` + `states.py:88`（§7.6） | `model_runner.py:1085` ✓（remove finished/preempted 后再 add）；`states.py:88` ✗（是 `num_reqs` 属性） | ⚠️ 见 R-11 |
| `vllm.py:589` + `buffer_utils.py:19`（§7.6） | `max_concurrent_batches = pp_size+1`（MRV2+async）；UVA pool retire 要求 | ✅ 正确 |
| `attention_v1.py:595`（§21.2） | 是 `_get_fia_params(...)` 调用；band 在 `:602-604` | ⚠️ 见 R-10 |
| `dsa_v1.py:420` + `:2246`（§21.3） | `build_dspark_swa_indices` 定义；`:2246` 附近是 op kwargs（`ori_kv/ori_block_table/cu_seqlens_q/seqused_kv`） | ✅ 正确（支持"op 同时收 table 与 indices"） |
| `sfa_v1.py:297` + `:1898`（§21.4） | `SparseMLAMetadataState.prepare`（把 common table 复制进自有 buffer）；`:1898` 附近是 indexer 统一调用注释 | ✅ 正确 |
| `kv_cache_interface.py:811`（§21.5） | `class SlidingWindowSpec(AttentionSpec)` | ✅ 正确；建议补 `vllm.py:602-609`（R-16）与 `FullAttentionSpec.sliding_window`（`kv_cache_interface.py:545`，证明"compute-band 不等于 recycling" ✓ 这正是 Codex §21.5 的区分依据） |
| `updatable_graph.py:79`（§19.6） | `class UpdatableGraph(torch.npu.NPUGraph)`（其 tasks/events 机制在 `:79-85` 及上方 `GraphUpdateTask`） | ✅ 可接受（指向类定义） |
| `test_dspark_proposer.py:1015`（§11.2"已测试的异构组合是 128/64"） | 该测试：`kernel_block_sizes=[128, 64]`、`assert proposer._per_group_kernel_block_sizes == {0: 128, 1: 64}`、`assert proposer.kernel_block_size == 128`（`:1027,1031,1033`） | ✅ **完全正确**（这条引用很扎实，且印证"legacy anchor 取首个 layer 的 block size"与"现有异构组合可整除"） |

**审计结论**：Codex FD 的源码引用**绝大多数准确**，2 处行号/语义小错（R-10/R-11），1 处类名不一致（R-12），1 处 hook 命名滞后（R-13）。**没有发现"引用了不存在的机制"这类硬错误**——这比一般 Agent 文档好很多。

---

## 8. Method / Backend / Graph Compatibility Audit

| Method × mode | Codex FD 声明 | 源码事实 | 判定 |
| --- | --- | --- | --- |
| EAGLE3 eager | Conditional（等 OQ-06） | eager 路径可重建（`autoregressive/speculator.py:573` override 已是窗口注入的自然锚点） | ✅ 声明合理；但**存储归属未解**（R-02） |
| EAGLE3 PIECEWISE prefill | Conditional | PIECEWISE capture 期会构建 metadata 且 attention-like op 可能真实执行（`cudagraph_utils.py:793-818` 注释） | ✅ 声明合理（我同结论） |
| EAGLE3 FULL prefill | Conditional | replay 从 Target dict 过滤（R-02） | ❌ **该路径存在静默 bypass**，仅靠"Conditional"不足以表达 |
| EAGLE3 FULL decode（merged） | Conditional，需 frozen anchor + 每 step binding | decode 会对 GQA/MLA **重建**（`autoregressive/speculator.py:702-710`）⇒ 有可注入点 ✓；但**必须每 step 独立 device length**，文档未给机制 | ⚠️ Major（机制缺失）：建议明确"per-step device length buffer（或图内更新）" |
| DFlash eager/FULL | Conditional | live/rebuild/capture 三入口齐全（§7.5 引用 ✓） | ✅ 声明合理 |
| DSpark × GQA | Conditional | Qwen3-8B 的 E2E 路径即该类 ✓ | ✅ 可达 |
| DSpark × MLA | Conditional | MLA CPU 优先（`mla_v1.py:500-509`）+ 无 rejection-corrected CPU exact ⇒ 按 §17.2 自身规则应 fail closed | ⚠️ 与 §9"必须支持 DSpark"冲突（R-07） |
| DSpark × DSA/SFA | UNSUPPORTED（§21.3/§21.4） | `dsa_v1.py:1107` 无 None 检查 ⇒ sparse 家族必有 native window；compressor/QLI/SAS 混用风险未证 | ⚠️ gate 必要但欠分解（R-06） |
| DFlash2 | eager only | `dflash2/speculator.py:121-139`：非 eager 直接 `NotImplementedError` | ✅ 正确 |
| MTP（含 Gemma4/Step3.5） | warn+ignore，按 normalized method | `worker/v2/spec_decode/__init__.py:58-71` + `vllm/config/speculative.py:1936-1940`（`use_eagle()` 含 mtp/dflash/dspark） | ✅ 正确且必要 |
| plain Eagle | Open product decision，默认 fail closed | MRV2 factory 支持它（`use_eagle` 分支）⇒ MRV1 能跑的配置在 MRV2 会**报错** | ✅ 声明为 Open 合理，但应显式写出"**这是 MRV1→MRV2 的兼容性缺口**" |
| ngram/suffix/medusa/custom | 不误启用、不吞原错误 | Ascend factory 对它们抛 `NotImplementedError`（`worker/v2/spec_decode/__init__.py:72`） | ✅ 正确 |

---

## 9. What Codex Does Better Than My Design

1. **`V_final = V_draft ∩ V_native ∩ V_resident`（I17/§21.1）** 优于我的 `effective_window = min(W, retention)`。证据：`vllm/v1/kv_cache_interface.py:545` 显示 **`FullAttentionSpec` 也带 `sliding_window: int | None`**——那是**计算层 band**，不做物理回收；把它简化成 `min(W, retention)` 会错误地把"计算层窗口"当成"物理保留上限"。Codex 的区分是对的，我错在把两类 spec 混为一谈。**我的 `DS Final` D16 需要按此改写。**
2. **backend-owned buffer 也必须受 lane/lease 约束（§20.3/D14）。** 我的 `DS Final` 假设 SFA/DSA 的 builder 自有 buffer（`sfa_v1.py:296-307`、`dsa_v1.py:420-436`）"地址不变 ⇒ 天然 async 安全"，这是过度推断：地址不变不代表只有一个 reader lane。Codex 这条修正成立。
3. **host ring 深度按"最大未 retire generation"而非 `max_concurrent_batches`（§15.3/D13）。** `max_concurrent_batches` 是下界（`vllm/config/vllm.py:589-598`），而 AR 多 step、graph task 延迟 retire 都可能超出它。我的 `DS Final` §20.2 把它当充分条件，Codex 更保守也更正确。
4. **决策状态化（Frozen/Conditional/Open/Rejected）+ 每条 OQ 带"关闭标准 + 未关闭行为"（§29）。** 这直接服务于"多人 Review 与长期维护"：读者可以立刻区分"已定"与"待证"，并且每条未闭合项都有默认安全行为。我的文档是叙述式的，治理性明显弱。
5. **拒绝宣称任一 DSA 坐标方案已被证明（§21.3）。** 我在 `DS Final` §21.2 写"rebase 后自然求交"语气偏肯定（虽然加了审计 gate）。Codex 的措辞纪律更安全：**它把"两种都理论上可能"作为待证状态**，从而不把未证结论写进主方案。
6. **§22.4"不应只 warning 后静默变更执行模式，而应明确 error 或要求用户显式选择"。** 这是一条我没写的、很有价值的用户可见契约（避免"配置了 FULL 但被静默降级"）。
7. **`first_token_offset` 的一等地位 + "若最终算子未消费则该 provider 不得声称可表达"（§16.4）。** 我的文档只把非零 offset 作为 OQ 提及，Codex 把它提升为 provider 契约字段并要求"消费证明"。

---

## 10. What My Design Does Better Than Codex

1. **`L0` 的定义被钉死并给出 kernel 证据（我的 §12.3）**：`vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:700-770` 的 `seq_len` 在 `query_len -= num_rejected` 之前读出 ⇒ `L0` 必须是**未扣 rejection** 的值。Codex 的 "full context end" 有歧义（R-03）。
2. **三个 capture 入口被点名、并指出 DFlash 的 capture 模块符号在导入期被重绑定**（`patch_dflash_speculator.py:26`）。这是任何实现者都必须知道的具体机制；Codex §19.1 只说"三个入口"，没有给出符号重绑定这一事实，因此也就没有暴露 R-01 的阻塞点。
3. **CPU 长度注入的两个字段都写死了，并给出"view 存在但字段缺失即抛错"的硬规则 + `from_numpy` 的存储别名风险**。补充证据：AR 会在事后 `metadata.seq_lens_cpu.copy_(next_seq_lens_cpu)`（`worker/v2/spec_decode/autoregressive/speculator.py:776`）；若窗口注入用 `torch.from_numpy(windowed.numpy())`，该 `.copy_()` 会写进 NumPy 共享存储 ⇒ 隐式改窗口 mirror。Codex 未提这条。
4. **AR FULL merged graph 的机制被写实**（我的 §12.1）：per-step **device** length buffer。Codex 只把该情形列为 OQ-07（"需闭合"），没给机制，使实现者无法判断工作量。
5. **物理保留的**最强证据**被引用**：`vllm/config/vllm.py:602-609` 的 `max_in_flight_tokens` 注释原文"Recycling-aware KV cache specs (sliding-window, chunked-local) … out-of-window blocks are freed"。Codex 只引了 `kv_cache_interface.py:811`（类型定义），证据强度弱于注释原文（R-16）。
6. **`A ≤ B_legacy` 这一"可断言"的守卫被写成显式断言**（我 §16.2）。Codex 用更一般的 `can_represent_origin()`，但**没有给出 overshoot 上界与守卫**，读者不易判断"非整除时到底会宽多少"。
7. **诚实标注自身勘误**：我的文档把"我在两份 review 中写错过的 `W<K` 结论"显式挂 Corrigendum；Codex FD 没有这类自纠章节（因为它没经历同样的错误——但也因此少了一个可追溯的纠错记录）。

**10.3 我的设计在 R-01 上比 Codex 更差（必须承认）**：Codex 把 narrow direct-capture 标为 `Conditional`（D05/D06）并把 OQ-17 列为 Open；我在 `DS Final` §19.3 把"capture 用 unwindowed dummy 定形状、靠宽度不变式保证一致"当作 **Route P 的既定做法**，而这个论证已被 Codex 的 R-11（同 shape ≠ 同地址）反驳。我的 Route P 实际上等价于 Codex 的 `TASK_REBIND`（依赖 pointer rebind），**却被我写成首期默认**。因此：**在 R-01 这一条上，Codex 的证据纪律优于我。**

---

## 11. Required Changes Before Freeze

> 按"必须改 / 必须补 / 必须降级"三类。CI = 冻结前必须完成。

| # | 变更 | 类型 | 对应发现 |
| --- | --- | --- | --- |
| C1 | §19.2/§31.1 把 `DIRECT_CAPTURE_BOUND` 从"默认"改为"**目标默认（待 OQ-01/OQ-17 关闭）**"，并新增"三条路线是否已证明可用"列 | 降级表述 | R-01/R-17 |
| C2 | 明确 capture 注入路径并二值化：**α** 给 upstream `_prepare_dflash_inputs_to_capture` / `prepare_inputs_to_capture` 加**可选** `draft_view=None` 参数（默认零行为变化）；**β** 首期只做 eager、FULL 全 fail closed。二选一写进 §19 与 §27 | 补机制 | R-01 |
| C3 | 给 AR 的重建 metadata 指定**独立存储**（`draft_metadata_store`），并让 FULL replay 从它取；Window OFF 时允许引用 Target 过滤结果；加 I01′ 不变式与"ON 时 draft 层 entry ≠ Target dict 同层 entry"的测试 | 补机制 | R-02 |
| C4 | Terminology 的 `L0` 改写为"未扣本轮 rejection 的 draft `input_buffers.seq_lens`"，并配跨对齐边界的差分测试 | 收紧定义 | R-03 |
| C5 | §17.1 增 `LegacyCpuMirror(_seq_lens_cpu)` 行 + "必须 None 或窗口化"断言 | 补字段 | R-04 |
| C6 | §17.1 的 `CpuFullUpper` 增加"必须是 apply-time upper（含 step/query stretch）"约束 + 三情形测试 | 收紧定义 | R-05 |
| C7 | §21.3/§21.4 把 gate 分解为 A–D 四项（坐标自洽性 / 绝对量派生状态清单 / native 右边界 / slot-set oracle 规格），给出"关闭后 Unsupported → Conditional"的路径 | 补可执行性 | R-06 |
| C8 | 把"**在交付模型上产出 capability inventory 并写出首期可启用集合**"提升为冻结前**第一项交付物**（不是 OQ），并据此重排 §30.4/§27.2 顺序 | 补交付物 | R-07 |
| C9 | §15.3/§20.2 明确与 `UvaBufferPool` 的关系（复用或独立 + 共享退休事件源） | 补机制 | R-08 |
| C10 | §30 增"接入点表"（文件 → 函数 → 现有行号 → 改动性质） | 补可执行性 | R-09 |
| C11 | 修正 §21.2 行号（`:602-604`）、删或改 §7.6 的 `states.py:88`、类名 `AscendModelState`、hook 名 `_build_uniform_attn_metadata` | 修正引用 | R-10/R-11/R-12/R-13 |
| C12 | §17.2 的容量夹紧改为**强制**：`visible_upper ≤ needed_max_g × span_g`（本 generation 实际写入列数×span），不满足 fail fast | 收紧 | R-14 |
| C13 | §11.5 明确"**公共 materializer 执行 copy，provider 只提供映射/容量/验证**"（避免 N 份实现） | 补职责 | R-15 |
| C14 | §21.5 补 `vllm/config/vllm.py:602-609` 证据 + "in-flight 期间 resident 集合可能大于名义窗口" | 补证据 | R-16 |

---

## 12. Open Questions With Exact Closing Evidence

> 只列 Codex FD **未列**、或**列了但关闭标准不够操作化**的项。每条给"要什么证据、由谁、如何判定通过"。

| ID | 问题 | 关闭证据（具体到可执行） | 未关闭行为 |
| --- | --- | --- | --- |
| **N-01** | capture 期 view 的注入路径（R-01） | ① 在 910 上跑一次 Window ON + DFlash FULL，dump capture 期与 replay 期传给 FIA/MLA/DSA/SFA 的 `block_table` 的 `(data_ptr, storage_offset, shape, stride, dtype)`；② 若不等，给出 α（upstream 可选参数）或 β（仅 eager）的落地结论 | FULL fail closed；只允许 eager |
| **N-02** | AR 重建 metadata 的存储位置（R-02） | 一条 UT：Window ON + Eagle3 + FULL prefill，断言 `build_draft_attn_metadatas()` 返回的 draft 层 metadata 的 `block_table_tensor` **不等于** `model_state.attn_metadata[draft_layer]` 的值，且 Target 层 entry 未被修改 | EAGLE3 全模式 fail closed |
| **N-03** | `L0` 的取值（R-03） | 一条 golden UT：`L0` 取在 `B_legacy` 边界附近、`r>0`、`K>0`，断言 `S` 与 MRV1 `SlidingWindowAdapter` 逐位相等（把 MRV1 当 oracle） | 用未扣值（保守正确），但必须补测 |
| **N-04** | `U` 的 apply-time 语义（R-05） | 三情形（AR step≥1、DFlash `Q=K+1`、`SAMPLE_FROM_ANCHOR` `Q=K`）下断言 `window_upper == clamp(现有 builder 的 upper − S, min=exact, max=capacity)` | 采用"与现有 builder 同式"生成，禁止直接取 `input_batch` 的 upper |
| **N-05** | DSA slot-set oracle（R-06） | 写出 `oracle(inputs) -> set[physical_slot]` 并构造 ≥4 组用例（causal/non-causal × native/无 native × W<native/W>native），与设备实跑逐 slot 比对；输出四子项 A–D 的逐项结论 | DSA 组合 Unsupported |
| **N-06** | SFA index/filter/top-k 转换（R-06） | 同 N-05，另需证明 absolute positions 未被修改且 top-k 长度 ≤ 窗口可见量 | SFA 组合 Unsupported |
| **N-07** | 交付模型的 backend inventory（R-07） | 在**交付模型**上跑一次 inventory（§22.4 已定义字段）并输出：gid→backend/causal/KV spec/column span/native window/CP；据此写出"首期可启用集合" | 冻结前必须完成；未完成不得宣布首期范围 |
| **N-08** | MLA 的 CPU exact 生产者（R-07 的根因） | 列出 MLA 路径实际消费的 length 字段（`mla_v1.py:500-509`），并证明存在无 hot-path D2H 的 rejection-corrected CPU exact；否则确认 MLA fail closed 并写入 readiness | MLA 组合 fail closed |
| **N-09** | host ring 与 UVA pool 的关系（R-08） | 画出 async（`max_concurrent_batches=2`）下窗口 host 状态的 generation 生命周期图，并给出"未 retire 的最大 generation 数"实测 | 按 `max_concurrent_batches` 下界 + 耗尽时等待 |
| **N-10** | AR FULL decode 的 per-step length 机制（§19.5 缺机制） | 给出实现选择（per-step device buffer 或图内更新）并做 A/B/A 交替 origin replay | AR FULL decode fail closed |
| **N-11** | plain Eagle 的兼容性政策（OQ-12） | maintainer 决策 + 一条 MRV1/MRV2 golden 对比（MRV1 `method="eagle"` 能启用窗口，MRV2 当前会报错 ⇒ 决策是"报错"还是"启用"） | 报 unsupported |

---

## 13. Final Recommendation

### 13.1 Codex Final Design 是否可作为最终主文档？

**可以作为主干（main document），但不能按当前文字冻结。** 理由：它的骨架/invariants/OQ 治理/冲突裁决/测试矩阵都优于另两份；数学（§6）经我复算无错；源码引用除 2 处小错外准确。但它有两处**结构性未闭合**（R-01 capture 注入路径、R-02 AR metadata 存储别名）被写在"默认/应该成立"的位置，还有一处**交付阻塞未显式化**（R-07）。

**建议做法**：以 Codex FD 为主干，并入本 Review 的 C1–C14 与 N-01–N-11；我的 `DS Final` 作为**补充材料**并入以下章节（不是替换）：§12.3 的 `L0` 钉死、§19.3 的三入口与模块符号重绑定、§17.3 的 CPU 长度注入与 `from_numpy` 别名风险、§12.1 的 AR FULL per-step device length 机制、§16.2 的 `A ≤ B_legacy` 断言、§21.4 的 recycling 证据原文。

### 13.2 哪些内容必须保留（不得在合并中丢失）

1. §8 的 18 条 invariants（I01–I18）与 §10.4 的状态机；
2. §29 的 OQ 表结构（"关闭标准 + 未关闭行为"两列）与 §31 的决策状态（Frozen/Conditional/Open/Rejected）；
3. §11.2 的"legacy anchor 优先、禁止默认 LCM"及其反例；
4. §11.3 的容量公式与 `first_token_offset` 分支；
5. §11.5 的 copy 三条件 + 每 step 全量重写；
6. §19.3 的 **actual-consumer fingerprint**（比 `data_ptr` 更强，且明确"Python metadata 里 tensor 正确只是辅助证据"）；
7. §21.1 的 `V_draft ∩ V_native ∩ V_resident`（并补 recycling 证据，见 C14）；
8. §22.4 的"不得 warning 后静默降级执行模式"；
9. §25 的测试矩阵与 §26.2 的 A/B 基线口径（"metadata 变短 ≠ feature 有效"）；
10. §31.1 的三方冲突裁决表（这是多 Agent 协作的治理资产）。

### 13.3 哪些内容必须修改

即 §11 的 C1–C14。其中**冻结前必须完成**的是：C1、C2（二值化 capture 路线）、C3（draft metadata 存储）、C4（`L0` 定义）、C5（`_seq_lens_cpu`）、C6（`U` 语义）、C8（交付模型 inventory）、C14（recycling 证据）。

### 13.4 哪些内容需要等 runtime 验证、不应提前冻结

- **capture/replay 的真实 operand 绑定**（含 `enable_enpu` 两分支的 update/replay 顺序）：`vllm_ascend/compilation/acl_graph.py:292-320` 已证明顺序随配置变化 ⇒ 必须 NPU trace + A/B/A 交替 origin replay，**不得**按 Python 语句顺序冻结（Codex §19.6 已正确标注为需 trace ✓）。
- **device execution lane 数量**：静态源码只能证明 host 多 in-flight（`vllm/config/vllm.py:589-598`、`buffer_utils.py:19`）⇒ lane 数必须 trace。
- **DSA/SFA 的最终可见 slot 集合**：必须设备级 slot-set oracle。
- **recycling spec 的 resident 区间**：必须 runtime API 或 trace。
- **性能门槛数值**（§26.3）：Codex 正确写明"禁止在本文伪造"✓ 保留该纪律。

### 13.5 我的 DeepSeek Final Design 是否存在同样或更严重的问题

**存在，且在三处更严重：**

| # | 我的问题 | 与 Codex 的比较 |
| --- | --- | --- |
| 1 | **R-01 的框架更差**：我把"capture 用 unwindowed dummy + 宽度不变式"当作 Route P 的既定做法（已被 Codex 的 R-11 反驳），并把依赖 pointer rebind 的路线写为首期默认 | Codex 标 Conditional + OQ-17；**Codex 更稳** |
| 2 | **R-07 的表述更危险**：我给出了"E1：dflash/dspark × {GQA, MLA} × eager"的具体首期集合，而其中 MLA 依据我自己的 §17 也必须 fail closed ⇒ 该集合可能只剩 GQA，但文档没标风险 | Codex 用"全部 Conditional"避免制造错觉；**Codex 更稳** |
| 3 | **R-02 同样遗漏**：我完全没提 `model_state.attn_metadata` 是 draft metadata 的既有存放处 | 双方都缺；**并列** |
| 4 | R-04（`_seq_lens_cpu` 缺席类型系统）同样存在 | 并列 |
| 5 | R-08（host ring 与 UVA pool 关系未定义）：我把深度直接等于 `max_concurrent_batches`，未说明它只是下界 | Codex 明确"下界之一"；**Codex 更稳** |
| 6 | R-03（`L0` 定义）**我的更好**：已钉死并给 kernel 证据 | 我更好 |
| 7 | R-16（recycling 证据强度）**我的更好**：引用了 `vllm.py:602-609` 注释原文 | 我更好 |
| 8 | R-05（`U` 的 apply-time 语义）**我的更好**：明确了 step/query stretch | 我更好 |

⇒ 结论：**我的设计不是更安全的替代品**；它在"证据纪律/表述克制"上弱于 Codex，在"关键定义钉死/证据强度"上强于 Codex。合并时应以 Codex 为主干、以我的定向补充为补丁，并由**独立第三方**按本 Review 的 N-01–N-11 逐项关闭。

### 13.6 冻结建议（一句话）

**先关 N-01/N-02/N-03/N-05/N-07 五项（capture 注入路径、AR metadata 存储、`L0` 定义、DSA oracle、交付模型 inventory），再谈冻结；其余 C 项可在实现 PR 内并行关闭。** 在 N-01 与 N-02 关闭之前，这份设计**不具备进入实现的资格**——不是因为方向错，而是因为这两条决定了"FULL 能不能做"和"eager 与 FULL 是否同一语义"。
