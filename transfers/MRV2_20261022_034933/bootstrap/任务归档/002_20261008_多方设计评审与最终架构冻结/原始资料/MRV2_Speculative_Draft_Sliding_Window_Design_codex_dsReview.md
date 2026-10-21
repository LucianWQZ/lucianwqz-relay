# Review：Codex《MRV2 Speculative Draft Sliding Window Architecture Design》

> **Corrigendum（2026-10-08，事后自纠）** — 本文 **m3** 里我给出的"负 `windowed_len` 几乎不可达"的推导**是错的**，请以 `MRV2_Speculative_Draft_Sliding_Window_Design_DS_v2.md` 附录 C 为准：
> - 正确条件是 `K - W ≥ b - (L mod b)`（不是"必须 `b ≤ 15`"）。当 `L mod b = b-1` 时退化为 `K ≥ W + 1`；
>   反例：`W=0, K=7, b=64, L=250`（`L mod 64 = 58`）⟹ `7 ≥ 6` ⟹ `windowed_len = -6`，**可达**。
> - 因此 **Codex 建议的 `W ≥ K` 校验是必要且充分的**（`K-W ≤ 0 < b-(L mod b)`），我当时的驳回理由不成立。
> - 另外 `W=0` 不是"静默无效"：`start = floor(L/b)*b`，`W=0,L=250,b=64 ⟹ start=192, windowed_len=58`（窗口收缩到最后一个 block 边界）。
> 其余结论（含 C1 与捕获入口的三条链路、per-group 覆盖等）不受影响。

> 评审对象：`/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Design_Codex.md`（1508 行，Stage 8 设计稿）
> 评审人：Claude（独立设计方，已产出 `MRV2_Speculative_Draft_Sliding_Window_Design.md`）
> 日期：2026-10-08
> 源码基线：`/Users/wenqingzhang/Desktop/vllm/vllm-ascend`、`/Users/wenqingzhang/Desktop/vllm/vllm`
> 行号：本文所有 `file:line` 都在本机核对过。引用 Ascend 仓库写全路径，引用上游写 `vllm/v1/...`。

## 0. 评审方法与结论摘要

### 0.1 方法

按「**先验证它依赖的源码事实，再看它自己的推理是否闭合**」两步走。对每个设计论断问三个问题：

1. 它引用的源码事实是否成立（行号、语义）？
2. 从该事实到该结论的推理是否唯一？
3. 如果实现者严格按这份文档写，会在哪里**静默出错**（不报错、只是结果变差或读错数据）？

我刻意避免用「我的方案更好」作为判据，只认同可由源码证伪/证实的部分。

### 0.2 总体评价

这是一份**质量显著高于平均水平**的设计稿。它对 MRV2 的结构性困难看得准，且在三处关键判断上**比我的独立设计更正确**（见 §0.3）。它的推荐架构（Candidate B：speculator-owned workspace + typed draft read view）在方向上是对的。

但它有**一个致命缺口**：它把「capture 期 metadata 从哪来」这条链路数漏了，而这直接决定它的窗口表形状选择是否可实现（§2 Critical C1）。此外有 4 个 Major 会改变 feature 语义或引入静默错误，以及一批需要收口的小问题。

### 0.3 必须承认：它在三处比我的设计正确

| 点 | Codex 的判断 | 为什么它对 | 影响 |
| --- | --- | --- | --- |
| **DCP local 长度** | 「DCP local length = `local_prefix(end) - local_prefix(start)`；**禁止**把 `prefix(window_len)` 当成 `prefix(end)-prefix(start)`」（§Design Invariants 9、§Buffer 3、R5） | 我核实了 `vllm/v1/attention/backends/utils.py:1088-1133` 的实现：`local(L) = floor(floor(L/i)/d)*i + clip(L - floor(floor(L/i)/d)*d*i - r*i, 0, i)`，**不是 L 的线性函数**，所以 `local(end)-local(start) ≠ local(end-start)`。反例：`i=1,d=2,r=1` 时 `local(4)-local(1)=2-0=2`，而 `local(3)=1`。 | **我的设计文档在 §5.4「由 windowed global 派生 local」这一句是错的**，Codex 是对的。这条必须按 Codex 写。 |
| **gather 的 stale tail** | 「full source 不能只是一张有固定 row width 的 tensor；gather kernel 只保证写 `[0, num_blocks)`，row tail 可能保留旧值，因此必须携带 per-row `full_valid_num_blocks`」（§MRV2 Constraints 1、Invariant 12、R16） | `vllm/v1/worker/gpu/block_table.py` 的 gather kernel 对 active row 只覆盖 `[0, num_blocks)`，不清 tail；而 window 裁剪会从任意 `start_col` 起读，正好会把「看起来有值」的 tail 当有效块。 | 我的设计只做了「列 ≥ needed 清零」，漏了「源列可能本身就是 stale」。Codex 这条更严格，应采纳。 |
| **CPU upper 的 canonical origin** | MRV1 对每个 CPU mirror **各自**套公式；若 async 下 upper > exact，两者可能落到**不同的 block-aligned start**。MRV2 应统一用 exact 算出的 `canonical_start` 去平移 upper（§MRV1 CPU upper-bound 一节、Invariant 8） | MRV1 代码 `vllm_ascend/spec_decode/utils.py:165-169` 确实对三个字段各自 `- ((src + k_future - w).clamp(min=0) // b) * b`。Device `seq_lens` 与 `seq_lens_cpu`（`optimistic_seq_lens_cpu`，见 `llm_base_proposer.py:1095`）在 async 下可以不等 → 两个 origin。 | 我的设计把这个风险列为一条 failure mode，但**没有给出 remedy**；Codex 给了。应采纳。 |

（同时说明：我的设计在「窗口表必须与 full 表同 shape」这一点上的结论**独立地**指向 Codex 的窄表选择的致命问题，见 §2 C1；这不是「谁更好」，而是同一份源码证据的必然推论。）

### 0.4 结论清单

- **Critical：1 条**（C1，capture 期 metadata 链路遗漏 → 窄表在 FULL 下不可实现）
- **Major：5 条**（M1 AR first-pass 重建缺 layout 不变式；M2 per-group `start` 改变 feature 语义；M3 `seq_lens_cpu` fallback 未收口；M4 native SWA 组合语义仍是风险项而非 spec；M5 preemption/row 复用未覆盖）
- **Minor：11 条**
- **需要源码验证：12 条**（含 Codex 自己列的 10 条里我追加/修正的）
- **推荐设计修改：8 条**（其中 3 条是「删掉」——降低范围）

---

## 1. 25 项攻击面逐条评估

格式：**风险等级 / 对应设计章节 / 为什么会发生 / 需要什么源码证据证明安全 / 建议修改**。

### 1. Target 是否可能被误 Window

- **风险：中**
- **章节**：§Design Invariants 1、§Recommended plumbing、§Runtime Data Flow「Target 路径」、§Buffer 1、§Graph Strategy 3
- **为什么可能发生**：Codex 的隔离机制是「独立 owner + 显式参数 + debug assert」。但落地位置恰恰是 **Target 与 Draft 共用的那一个函数**：`build_attn_metadata()`。Target 侧入口是 `vllm_ascend/worker/v2/model_states/default.py:95-121` 的 `AscendModelState.prepare_attn()`，它调用的就是同一个 `vllm_ascend/worker/v2/attn_utils.py:220`。Python 没有类型屏障，`draft_window_view` 只是一个 `None`-默认的 kwarg——**任何一处调用点写错参数就会静默窗口化 Target**。Codex 唯一的防线是「debug/assert build 中直接拒绝」，且它自己留了 `ContextVar` 作为「运输层」，而 ContextVar 在嵌套作用域（capture 包在 draft scope 内）会天然泄漏。
- **需要的源码证据**：① 列出所有调用 `vllm_ascend/worker/v2/attn_utils.py:220` 的调用点（已知至少 3 类：`model_states/default.py`、`build_attn_metadata_wrapper` 作用域内的上游 speculator、`dflash/cudagraph.py:55` 的导入期重绑定）；② 证明每个 Target 调用点都不会拿到 view。
- **建议修改**：不要用「共享函数 + 可选参数」。**给 Draft 用一个独立的入口函数**（例如 `build_draft_attn_metadata(...)`，内部再调共享实现），使 Target 路径在类型/函数名上就无法传入 view。若坚持共享入口，则强化断言：view 必须携带 `draft_only_layer_names`，funnel 断言本次 `attn_groups` 展开出的每个 layer 都属于该集合，否则直接抛。

### 2. positions 是否可能被改变

- **风险：低**
- **章节**：§Design Invariants 2、§Component Responsibilities「DraftAttentionView」（明确不拥有 positions）
- **为什么可能发生**：基本不会。`positions` 在 Draft 路径上来自 `build_draft_attn_metadata_factory` 注入的 `self.input_buffers.positions`（`vllm_ascend/worker/v2/attn_utils.py:1269`），Window 不碰它；capture 路径不传 positions → funnel 合成 zeros（`attn_utils.py:287-288`），也与 window 无关。
- **需要的源码证据**：一条 identity/值断言即可（Draft forward 前后 `positions.data_ptr()` 与内容不变）。
- **建议修改**：把「positions 不在 view 里」升级为「window 物化后断言 `positions` 与 `slot_mappings` 的 `data_ptr()` 及内容与物化前逐位相同」，写进 workspace 的 debug 自检（Codex 的 §Test 2 已有类似项，补 positions/slot 两项）。

### 3. slot_mapping 是否有机会读到 windowed block table

- **风险：低（结构上已被排除）**
- **章节**：§Design Invariants 3、§MRV2 Constraints「Full physical plane 与 Draft read plane 必须分离」、§Buffer 4 最后一条
- **为什么可能发生**：结构上不会。公共 slot kernel 读的是 authoritative 指针：`vllm/v1/worker/gpu/block_table.py:93-97`（`block_table_ptrs` 绑定 `self.block_tables[g].gpu`）→ `:190-221 compute_slot_mappings`；Ascend override 同源（`vllm_ascend/worker/v2/block_table.py:82-114`）。DFlash/DSpark 的 query slot 也是从 **full** gathered table 生成的，且发生在 window 物化之前（`vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:375-409`）。残余风险只有一个：**实现时把 window 表误写回 `input_block_tables`**，Codex 已显式禁止（§Buffer 4）。
- **需要的源码证据**：workspace 的 debug 自检里加「任何 workspace buffer 与 `input_block_tables[*]`/`slot_mappings` 的 `data_ptr()` 不重叠」；再加一条「开/关 window 的 slot mapping 逐位相同」的测试。
- **建议修改**：无需改设计，把这两条断言写进 §Test 2 的必测项即可（Codex 的测试清单里目前没有 slot-mapping 不变式的显式断言）。

### 4. full block table 是否可能被覆盖/污染

- **风险：低**
- **章节**：§Design Invariants 4、§Buffer 1/4
- **为什么可能发生**：Codex 明确要求「authoritative tables、shared `input_block_tables` 与 canonical `InputBuffers` 只能作为 source」。风险点是实现纪律，而非设计缺陷。
- **需要的源码证据**：`full source table 与 full seq lens 逐bit不变`（§Test 2 已列 ✓）。
- **建议修改**：无。补一条：`refresh` 前置断言 source 的 `data_ptr()` == `BlockTables.input_block_tables[g]` 的 `data_ptr()`（防「以 window 表为源」）。

### 5. seq_lens 是否可能被重复 Window

- **风险：中高**
- **章节**：§Design Invariants 11（幂等）↔ §Method Integration Matrix「Eagle / Eagle3」第 4 条（增量补列）；§Graph Strategy 6（双构建入口）；§推荐设计「状态机」SEALED 多 reader
- **为什么可能发生**：Codex 同时写了两条**互相冲突**的更新纪律：
  - Invariant 11：「每次都严格执行 `canonical full source -> window destination`；没有 API 接受 Window view 作为下一次 source」；
  - §Eagle 集成第 4 条：「若 proposal 开始时 authoritative full table 已经包含 planned-final blocks，**可预填**这些 block id…若尚未有效分配，则保持 table origin/address 不变、**在每个 AR step 从 full source 补齐新变为 valid 的列**」。
  第二条是**增量填充**，不是「每次都严格执行 full→window 全量覆盖」。增量方案下：(a) 同一 step 被 live builder 与 graph-manager builder 各调一次时，第二次不会重写已填列——只有当「填过的列不会因为 source 变化而变化」时才是幂等的；(b) 一旦 proposal 的 anchor 变了（或 request 顺序变了）而没有 epoch 变更，残列会把**上一个 proposal 的 block id** 留在窗口表里。Codex 的 epoch 语义没有明确把「anchor」纳入 key，也没有「(epoch, step) → 内容已确定」的 memo 规则。
- **需要的源码证据**：① epoch 的定义是否包含 `(proposal_id, anchor_start, request_order_version, step)`；② 是否存在「同一 epoch 内重复 build 必然产生相同表内容」的可证明链条。
- **建议修改**：**v1 只保留一条纪律**——「每次 build 都把该 group 的窗口表整行重写（`copy_` 全量），永远不做增量补列」。全量重写的成本是 `R × C_g` 个 int32 的拷贝（Codex 自己算的 17 KiB/group，见 §Buffer 2），微不足道；换来的是幂等性可由构造保证、且与 Invariant 11 自洽。若将来确需增量（为省拷贝），必须给「列有效性」加 generation 计数并把 anchor 纳入 epoch。

### 6. Window OFF 是否真的零回归

- **风险：中**
- **章节**：§Design Invariants 14、§Config/Compatibility Policy 4、§Expected File Changes Patch 1
- **为什么可能发生**：两个具体泄漏点：
  1. **Codex 提议把 MRV1 的 `SlidingWindowAdapter` 改为委托公共数学**（§核心决策 1、§Expected File Changes「`vllm_ascend/spec_decode/utils.py` | 让 MRV1 `SlidingWindowAdapter` 委托公共数学，保留公开行为与调用点；先用差分测试锁定」）。这是**为了「数学只有一份」而改动一个已上线的、有 E2E 基线的 MRV1 feature**。风险面很具体：MRV1 的 adapter 除了数学还承担**副作用契约**——`self.start_tokens_in_window_rounding` 与 `self._windowed_seq_lens` 被后续代码读到（device `seq_lens` 被换成 `self._windowed_seq_lens`，见 `spec_decode/utils.py:163`），并且 MRV1 的 CPU mirror 是**各字段独立重算**的（`:165-169`），而 Codex 推荐 MRV2 用 canonical start（§MRV1 CPU upper-bound 一节）——两者语义不同，共享一个 primitive 就必须加开关，否则要么改 MRV1 语义、要么让 MRV2 退化成 MRV1 的旧行为（而后者正是 Codex 认定要修的 R3）。
  2. 现有 MRV1 window 测试的覆盖不足以兜住这种重构：`tests/ut/spec_decode/test_utils.py:192-214` 只覆盖 host mirror；**adapter 的 block-table 裁剪没有直接单测**（这一点我核实过：`tests/ut/spec_decode/test_eagle_proposer.py:311-330` 覆盖 apply 的基础路径，但没有逐列/逐边界断言 clone buffer）。
- **需要的源码证据**：一个「MRV1 golden 值」测试：给定 `(W,b,K,seq_lens)` 的固定输入，断言 device `seq_lens`、clone buffer 内容、三个 CPU mirror 的**具体数值**，以及 `full_block_table` 的引用语义。没有这个，重构无从验证。
- **建议修改**：**Patch 1 删掉**。本 feature 不要动 MRV1。把「数学只有一份」降级为「MRV2 的数学单测与 MRV1 的 goldens 对拍」（Codex 的 §Test 1 最后一条已经在做这件事）。若将来确要合并，单独 PR、单独回归。这同时符合 `AGENTS.md` 对 patch 的「minimal and focused」要求。

### 7. per-group block size 是否处理正确

- **风险：高（既是最强项，也是最危险的语义变更）**
- **章节**：§Design Invariants 7/8、§MRV2 Constraints「Per-group 不是『同一 tensor 放进 list』」、§Buffer 2（`C_g` 公式）、R4
- **为什么可能发生**：
  - **正确的一面**：Codex 坚持 `start` 必须对齐**每个 group 自己的** column token span，并指出 `tokens_per_table_column` 未必等于物理 block size（§DraftWindowLayout）。这是对的——`vllm/v1/worker/gpu/block_table.py` 的 `blocks_per_kv_block = block_size // kernel_block_size` 展开确实让「table 列」的 token span 与 storage block size 解耦。
  - **危险的一面**：Codex 让 `start_tokens` **逐 group 不同**（`gid -> {start_tokens, ...}`，§MRV2 Constraints 2；`DraftWindowGroupView.start_tokens_device` 每组一份）。而 MRV1 的契约是**一个窗口**：`SlidingWindowAdapter(self.draft_window_size, self.kernel_block_size, ...)` 只取一个 `kernel_block_size`（`vllm_ascend/spec_decode/llm_base_proposer.py:406-408, 446-452`），且 DSpark 的 per-group 循环复用的是**同一个** `self.block_size`（同文件 `:2604-2605`）。也就是说 **MRV1 下所有 group 共享同一个绝对窗口起点**。
  因此 Codex 的设计在 hybrid multi-group draft 上会让**不同 attention group 看到不同长度的历史**——这会改变 draft 的 acceptance 行为，是 **feature 语义变更**，不是实现细化。更棘手的是它与 Codex 自己的 Invariant 8（「同一 group 的 table、exact、CPU mirror、upper、local length 都以同一个 `start_tokens` 为坐标原点」）在精神上冲突：Invariant 8 要防的正是「多个 origin」，而 per-group start 恰恰是**有意制造多个 origin**。
- **需要的源码证据**：① 目标 DSpark draft 实际有几个 draft attention group、各自 `kernel_block_size` 是多少（决定这条是理论风险还是现实风险）；② MRV1 在 hybrid multi-group + window 下是否有测试（据我核实：没有——MTP 是唯一明确的多 group 用例，而 MTP 被 window 忽略）。
- **建议修改**：把语义收敛为**「一个 proposal 一个绝对窗口，per-group 只体现在列映射」**：
  ```text
  start = align_down(max(F - W, 0), L)      # L = lcm{kernel_block_size_g}（或最细粒度）
  start_col_g = start / kernel_block_size_g # 整数，必然整除
  needed_g    = ceil(visible_len / kernel_block_size_g)
  ```
  这样每个 group 的 `start` 相同（保留 MRV1 的「一个窗口」语义与 Invariant 8 的单一 origin），`start_col_g`/`needed_g` 逐 group 不同（满足 per-group 布局正确性）。代价是窗口起点可能比最优情况早至多 `L-1` 个 token（多看一点历史，无害）。**若产品确实想要 per-group 独立窗口，必须显式写成一条 contract 变更并补 MRV1 对照实验，不能作为实现细节混入。**

### 8. padding rows

- **风险：低（这是 Codex 覆盖最好的部分）**
- **章节**：§Design Invariants 12、§Buffer 2（`window_num_blocks`）、§Buffer 4、R16、§Test 2
- **为什么可能发生**：Codex 把两类「尾部」都点了：`[num_reqs, num_reqs_padded)` 的 padding rows，和 active row 的 `[num_blocks, row_width)` stale tail，并要求用 per-row `full_valid_num_blocks` 限制 gather。这一点它比我的设计更严格（见 §0.3）。
- **需要的源码证据**：各 backend 的 padding 约定是**不一致**的，Codex 只说「沿用当前 backend 约定」而没有枚举。已核实的一例：GQA/FIA 会把 `seq_lens_list` / `seq_lens` 用 **1** 补齐并追加零表行（`vllm_ascend/attention/attention_v1.py:361-365`），即 padding row 的 kv_len=1 且指向 block 0——它之所以安全，仅因为该 row 是丢弃的 dummy request，**不是**因为「inert」。这对 window 表的含义是：**padding row 的 block id 不能指向任何一个 active row 会用到的 block**，而不只是「要为零」。
- **建议修改**：在 §Buffer 4 增加一张 per-backend padding 约定表（GQA/MLA/SFA/DSA 各一行：length 填什么、table 行填什么、谁丢弃该行），并补一条断言：任意 padding row 的 block id 集合与任意 active row 的 block id 集合不相交。

### 9. CPU upper bound 与 device exact length 是否一致

- **风险：中高（Major M3）**
- **章节**：§MRV1 CPU upper-bound 与 MRV2 的语义强化点、§Design Invariants 8、§Buffer 3、§DraftWindowGroupView、R20、R21
- **为什么可能发生**：Codex 的 canonical-origin 规则本身是对的（见 §0.3）。**缺的是它没有把 Ascend funnel 的两个兜底路径列进「必须收口」的清单**：
  - `vllm_ascend/worker/v2/attn_utils.py:256-258`：`seq_lens_np is None` 时 `seq_lens_np = np.full(num_reqs, max_seq_len, dtype=np.int32)`；
  - 同文件 `:259-260`：`seq_lens_cpu_upper_bound is None` 时直接等于 `seq_lens_cpu`。
  而 `max_seq_len` 在 Draft 路径上传的是 `self.draft_max_seq_len`（`vllm/v1/worker/gpu/spec_decode/speculator.py:361`），是 **full 量级**。
  Codex 在 §DraftWindowGroupView 里把 `seq_lens_cpu_exact` 标为**有条件能力**（「未证明前该字段是有条件能力，不是既定事实」）。如果实现按此把 CPU exact 留空，funnel 的兜底就会给 backend 一个**full 量级的 CPU 长度**，而表已被窗口化 → 正好是最高危的「表窗口化、长度 full」：kernel 会去读 `[needed, row_width)` 列（被置 0）→ block id 0 → **读到 cache 第 0 块**（可能是别的 request 或已释放的块）。这条路径可达，因为 MLA 是 **CPU 优先**：`vllm_ascend/attention/utils.py:573-576` + `attention/mla_v1.py:504-505`。
  另一个相关的**存储别名**变化：AR 现在依赖 `torch.from_numpy(np.full(...))` 得到的 `seq_lens_cpu`，并在事后 `metadata.seq_lens_cpu.copy_(next_seq_lens_cpu)`（`vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:776`）。一旦 window 通过 `seq_lens_np = windowed.numpy()` 注入，`seq_lens_cpu` 变成 **NumPy 共享存储**的 tensor，上述 `.copy_()` 会写进 window 的 CPU mirror（或 pin 住的缓冲）——隐藏的跨对象写。
  还有一条：MRV2 当前**没有** `_seq_lens_cpu` 的生产者（`vllm_ascend/worker/v2/attn_utils.py:309-330` 不赋该字段），所以 `_select_seq_lens` 会落到 `seq_lens_cpu` 或 device；但一旦将来有人填了 `_seq_lens_cpu` 为 full 值，`_select_seq_lens` 会**优先**取它（`attention/utils.py:573-574`）。
- **需要的源码证据**：列出所有会从 `AscendCommonAttentionMetadata` 取 length 的 backend 分支，并逐个标注它取的是 `_seq_lens_cpu` / `seq_lens_cpu` / `seq_lens` / list / max。至少覆盖 GQA(`_select_seq_lens`)、MLA(`mla_v1.py:504-505`)、SFA(`sfa_v1.py:644-647`)、DSA(`dsa_v1.py:852-855`)。
- **建议修改**：把「**window view 存在时必须同时覆盖 `seq_lens_np` 与 `seq_lens_cpu_upper_bound`**」写成硬不变量；funnel 在 `draft_window_view is not None and seq_lens_np is None` 时**直接抛**（而不是走兜底）。同时明确 CPU 向量的存储 owner 与事后 `.copy_()` 是否仍是更新机制（若仍是，则 window 的 CPU mirror 必须是那块被 `copy_` 的目标，不能让 `from_numpy` 引入新别名）。

### 10. graph capture 地址稳定

- **风险：中（地址本身设计正确；但被 §11 的链路遗漏破坏）**
- **章节**：§Design Invariants 10、§Graph Strategy 1/3、§Buffer 2
- **为什么可能发生**：Codex 的地址纪律写得很好（capture 前分配、replay 只写内容、不依赖 pointer rebind、DSA/SFA no-op updater 也安全）。真正的问题不在纪律，而在**它假设 capture 与 replay 走同一份 metadata 契约**——见 §11。
- **需要的源码证据**：per-descriptor 的 `(data_ptr, storage_offset)` 对。Codex 的 §Test 2 写的是「capture 前后每个 persistent tensor `data_ptr()` 不变」——对 slice view 不够，因为 funnel 会做 `x[:num_reqs_padded]`（`vllm/v1/worker/gpu/spec_decode/speculator.py:322-324`），offset 随 descriptor 变。
- **建议修改**：断言改成比对 `(data_ptr, storage_offset, shape)` 三元组，且**逐 capture descriptor** 比。

### 11. capture / replay metadata 是否一致

- **风险：致命（Critical C1）**
- **章节**：§Graph Strategy 3/6、§Expected File Changes（`dflash/aclgraph.py`「capture/live 两条路径显式消费同一 view contract」）、§Compare「Graph capture」行
- **为什么可能发生**：Codex 全文只承认**两个** metadata 构建入口（live build + graph-manager replay rebuild，见 §Graph Strategy 6「DFlash 双构建入口」）。实际上**至少有三条**，而且第三条在它没有提到的上游文件里：

  | # | 入口 | 源码 | 传给 funnel 的 block table |
  | --- | --- | --- | --- |
  | 1 | live propose | `vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:453`；`vllm/v1/worker/gpu/spec_decode/autoregressive/*` | 窗口表（设计里） |
  | 2 | graph-manager replay 前 rebuild | `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:86-98`；`autoregressive/aclgraph.py:132-152` | 窗口表（设计里） |
  | 3 | **capture 期的 dummy metadata** | DFlash/DSpark：`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:24-71`，`get_dummy_block_tables(num_reqs)` 在 `:36`，`build_attn_metadata(...)` 在 `:55`；AR/Target：`vllm/v1/worker/gpu/cudagraph_utils.py` 的 `prepare_inputs_to_capture()` → `model_state.prepare_attn(...)`（约 `:820`）→ Ascend `vllm_ascend/worker/v2/model_states/default.py:95-121` | **full 宽度的零表**（`vllm/v1/worker/gpu/block_table.py:177-187` 对 `input_block_tables` 行 `zero_()`） |

  关键事实：**capture 期没有任何地方能拿到 window view**。
  - DFlash 的 `dflash/cudagraph.py:55` 调用的是该模块的**模块级符号**，它由 `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26` 在**导入期**重绑定（`cudagraph_module.build_attn_metadata = build_attn_metadata`），**不经过** `build_attn_metadata_wrapper()` 那套 ctx 管理（后者的 patch 目标是 `vllm.v1.worker.gpu.spec_decode.speculator`，见 `vllm_ascend/worker/v2/attn_utils.py:1240-1251`）。
  - AR 侧 capture 走 `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:111` 的 `prepare_inputs_to_capture(...)` → 上游 `cudagraph_utils.prepare_inputs_to_capture()` → `model_state.prepare_attn()` → Ascend funnel，传入的也是 dummy full 表。
  - 要把 view 送进 capture，只有三条路：(a) 改上游 `cudagraph_utils.py` / `dflash/cudagraph.py` 的签名；(b) 改 Ascend `prepare_attn` 签名并让它自己知道「现在是 draft capture」；(c) 用隐式 context（capture 期间 `_EXTRA_CTX.is_draft_model` 确实被 `model_capture_wrapper` 置 True，见 `autoregressive/aclgraph.py:90`）。

  **后果**：Codex 的窗口表是**窄表**（`window_block_tables[g] : [R, C_g]`，`C_g = ceil(W/block_size_g)+1`，§Buffer 2）。capture 时记录进 graph 的是 **full 宽度**的 `block_table` 参数；replay 时设计要喂**窄表**。这产生形状/参数不一致。而对 **SFA / DSA** 这更严重：两者的 `update_graph_params()` 都是 no-op（`vllm_ascend/attention/sfa_v1.py:885-896`；`AscendDSAImpl.update_graph_params`），captured op 读的就是 capture 期那块 storage 的地址，**既不能换 pointer 也不能换 shape**。
  这与 Codex 自己的 §Graph Strategy 1「capture uses workspace slot N addresses / metadata object keeps references to exactly those addresses」和它「§核心决策 9：第一版优先保持改动在 vllm-ascend 内，不要求修改上游 vLLM」构成**直接冲突**：窄表 + 不改上游 + 不用隐式 context ⇒ 三者不能同时成立。

  附带发现（同一处证据）：`max_seq_len` 在 capture 与 replay 间**本来就不同**——capture 传 `max_model_len`（`dflash/cudagraph.py:64`；Ascend `model_states/default.py` 的 `max_seq_len=self.max_model_len`），replay 传 `self.draft_max_seq_len`（`vllm/v1/worker/gpu/spec_decode/speculator.py:361`）。Codex 的 Invariant 9「`max_seq_len` … 从 Window view 派生」会**放大**这个既有分歧：captured op 的 tiling/plan 按 `max_model_len` 定，replay 却给窗口量级的值。

- **需要的源码证据**：① 确认 AR/Eagle 与 DFlash/DSpark 的**全部** capture 入口与其 block table 来源（上面已核出 3 条）；② 确认各 backend 在 `for_cudagraph_capture=True` 时把 `block_table` 的 shape 固化到哪里（SFA `SparseMLAMetadataState` 的 buffer、DSA 的 req metadata、GQA/MLA 的 graph param pool）。
- **建议修改**（任选其一，必须显式选）：
  1. **（推荐）窗口表与 full 表同 shape**：只改内容（左移 + 右侧显式清零），宽度 = full table 宽度。capture 的 dummy（全 0）与 replay 的窗口表形状一致；SFA/DSA 的 builder-owned buffer 布局不变；不需要动上游。代价是每步多写 `row_width - needed` 列 0、多占 `O(R × G × full_width)` 内存（`R=256, width=1024, 4B, G≈4` ≈ 4 MiB，可接受）。
  2. 保持窄表，但**接受改上游**：给 `dflash/cudagraph.py` 的 `_prepare_dflash_inputs_to_capture` 与 `cudagraph_utils.prepare_inputs_to_capture` 加显式 view 参数。这推翻 §核心决策 9 的「不改上游」，需要更新 Non-goals。
  3. 保持窄表 + 用隐式 context 在 capture 期取 view。这与 §Async 4「不采用隐式全局上下文」冲突，且正是 Codex 用来否决 Candidate A 的理由（§Candidate A 风险）——等于把 A 的失败模式搬到 B 里。
  **无论选哪条，都必须把「capture 期 metadata」写进 design 的入口清单**，并补一条测试：断言 capture 与 replay 传给 backend 的 `block_table` 的 `(data_ptr, storage_offset, shape, dtype)` 一致。

### 12. eager / PIECEWISE / FULL 差异

- **风险：中**
- **章节**：§Design Invariants 18、§Graph Strategy 2 表、§Graph Strategy 3
- **为什么可能发生**：Codex 的 §Graph Strategy 2 对 PIECEWISE 只写了「在进入对应 piece 前」，太含糊。上游对 PIECEWISE 的行为是明确的、且与 FULL 不同：`cudagraph_utils.prepare_inputs_to_capture()` 的注释（约 `:793-818`）说明 **PIECEWISE 也会构建 attention metadata（`for_capture=False`）**，因为 attention-like op（sconv、DSV4 compressor）可能不是断点、需要在 capture 期间真实执行；而作为断点的标准 attention op 则在 capture 时**eager 执行**。这意味着 PIECEWISE 下**capture 期就有真实的 attention 执行**，window view 必须在那一刻也有效——不只是 FULL 的「绑定地址」。
- **需要的源码证据**：PIECEWISE 下哪些 attention 被 eager 执行、哪些进 graph；`attention_v1.py:1214` 一类 `and self.sliding_window is None` 的 FIA 可用性分支在 window 下是否会改变取值。
- **建议修改**：把 §Graph Strategy 2 的 PIECEWISE 行改成明确的「capture 期与每个 piece replay 都必须提供同一 epoch 的 view」；并加一条 PIECEWISE 专项测试（当前 §Test 6 只说「eager、PIECEWISE、FULL 分别覆盖当前真实支持组合」，没有断言 capture 期的 view 有效性）。
- 另外：`GQA/FIA` 的 legacy `update_graph_params()` 直接抛 `NotImplementedError`（要求 UpdatableGraph，`vllm_ascend/attention/attention_v1.py:572-581`），所以 eager/PIECEWISE/FULL 的可用性取决于 backend，而不是 method——Codex 的 §Graph Strategy 5 说对了，但没有把它连到 Invariant 18（graph-mode parity）：**对 GQA 而言 parity 是由 UpdatableGraph 保证的，不是由设计保证的**。

### 13. async 生命周期

- **风险：中**
- **章节**：§Design Invariants 13、§Async 1-5、§Buffer 5、R11
- **为什么可能发生**：Codex 的「两级存储 + epoch/lease」设计合理，但两处假设需要收紧：
  1.它说「如果当前 runtime 保证同一 runner 的 device proposal 严格串行，一个 graph lane 的 device buffer 可以复用……否则按 `max_concurrent_batches` 预分配」。仓库里已有反证信号：`vllm/v1/worker/gpu/buffer_utils.py` 的 `UvaBufferPool` **默认至少两个 round-robin slot**，并要求调用方在 reuse/growth 前确保 GPU reader 已 retire——说明「重叠」在当前系统里是被预期存在的，而不是理论可能。因此「首版单 slot」不能作为默认安全假设，至少要 `lane_id` 参数化（Codex 说了 ✓）并在 debug 下断言。
  2. **release 时点**：legacy 路径的 graph 参数更新发生在 **replay 之后**（`vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:154-194`：`super().run_fullgraph(desc)` 先、`update_full_graph_params(...)` 后；`dflash/aclgraph.py:100-138` 同）。所以「replay 已提交」不足以作为 release 条件；必须绑定到「最后一个消费者（含参数更新）完成」的 device 事件。
- **需要的源码证据**：`update_stream` 与 current stream 的 happens-before；`UpdatableGraph` 分支 `graph.update(update_stream, tasks)`（`autoregressive/aclgraph.py:196-208`）之后是否有同步点。
- **建议修改**：把 lease 的释放条件从「reader 提交」改为「reader + graph-param update 完成」；在 §Async 1 里把「UvaBufferPool 已有多 slot」列为「重叠是既定事实」的证据，而不是「待验证」。

### 14. contextvar / context object 是否跨请求、跨线程、跨 async execution 泄漏

- **风险：中**
- **章节**：§Async 4、§Recommended plumbing（「若为了兼容当前 wrapper 必须短期使用 scope，只能用 `ContextVar` + token reset」）、§Candidate A 风险
- **为什么可能发生**：真正的泄漏通道不是 async task 嵌套，而是 **capture 入口在不同的模块**（见 §11）：speculator 在自己 propose 作用域里 set 的 ContextVar，在 `dflash/cudagraph.py:55` 执行时**不一定仍然生效**（capture 由 graph manager 驱动，且 `model_capture_wrapper` 是另一套机制）。同时，Codex 一边否决 Candidate A 的「scope 泄漏」，一边为 B 保留 ContextVar 作为运输层——这两者在失败模式上是同一个东西。
  另外，代码库里已有的隐式上下文正是 `_EXTRA_CTX`（`vllm_ascend/ascend_forward_context.py`），且 `model_capture_wrapper` 在 capture 期间就设置 `is_draft_model` / `is_draft_model_prefill` / `capturing`（`vllm_ascend/worker/v2/aclgraph_utils.py`、`autoregressive/aclgraph.py:90`）。也就是说：**如果走隐式路线，正确做法是复用 `_EXTRA_CTX` 而不是新造 ContextVar**；如果走显式路线，就必须承认要改上游 API。
- **需要的源码证据**：capture 的实际执行线程/作用域；`_EXTRA_CTX` 在 capture 与 replay 期间的生命周期。
- **建议修改**：在文档里**二选一并写死**，不要留「必要时可用 ContextVar」这种活口：
  - **显式路线**：view 作为参数一路下传，接受需要修改上游 `cudagraph_utils.py` / `dflash/cudagraph.py`；相应更新 §Non-goals。
  - **隐式路线**：明确复用 `_EXTRA_CTX`（新增一个 `draft_window_view` 字段），并规定作用域 = 一次 draft metadata build，且在 Target-scoped 路径上断言该字段为 `None`。
  两条路线都要有「Draft build 发生在 scope 之外」的负向测试。

### 15. Eagle3 / DFlash / DSpark 的 timing 差异

- **风险：中高（Major M1）**
- **章节**：§Method Integration Matrix、§Runtime Data Flow「Eagle / Eagle3 eager 与 PIECEWISE」、§推荐设计「Canonical start 与 AR proposal anchor」、R1
- **为什么可能发生**：Codex 的 timing 矩阵基本正确（含「Eagle first pass 不能复用 Target metadata，必须重建 draft metadata」这一关键决策——这与 MRV1 行为一致，因为 MRV1 的 apply 发生在 `build_draft_attn_metadata()` 之前，覆盖 step 0 与后续步骤）。**缺的是一条 normative 约束**：重建出来的 first-pass metadata 的 **query layout 必须与 Target 的逐位相同**。
  证据：上游 AR propose 明确说「we pad each request's query length to include any rejected positions. By doing so, we can also reuse the attention metadata (e.g., query_start_loc, seq_lens) of the target model」（`vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:233-238`，以及 `:311-313` 的复用注释）。而 `prepare_prefill_inputs` 的 kernel 会按 `num_rejected` 裁掉无效 query 尾部（同文件 `:719-721`）。如果「重建」时用 draft 自己的裁剪后 layout，first-pass 的 batch shape 就与 Target 的 hidden states 不再对齐 → **第一个 draft token 静默算错**，而 acceptance 只是变差、不会报错。
  Codex 的 R1 只说「做对象身份和值测试」，没有把「layout 除 read view 外必须完全等价」写成要求。
- **需要的源码证据**：`input_buffers.query_start_loc` / `positions` / `num_tokens` 在 first pass 与 Target 的对应关系（`prepare_prefill_inputs` kernel `:690-770`）。
- **建议修改**：在 §Method Integration Matrix 的 Eagle 行增加一条硬约束：**Window ON 时重建的 first-pass metadata 必须满足 `query_start_loc`、`query_start_loc_cpu`、`positions`、`num_tokens`、`is_prefilling` 与 Target 本轮逐位相同，只允许 `block_table_tensor` 与全部 length 字段不同**；并补一条差分测试（同样的输入，重建 metadata 与 Target metadata 在这五个字段上比对）。

### 16. unsupported methods 是否被错误启用

- **风险：低**
- **章节**：§Design Invariants 15/16、§Method Integration Matrix、§Config/Compatibility Policy 1/2、R17
- **为什么可能发生**：Codex 处理得很好，尤其是「Gemma4/Step3.5 MTP 当前 factory 落到 `AscendEagleSpeculator`，也不能误继承 Eagle 的 Window」——这与源码事实一致（`vllm_ascend/worker/v2/spec_decode/__init__.py:58-71`，`use_eagle()` 对 `mtp`/`dflash`/`dspark` 都返回 true，所以绝不能按 concrete class 判 policy）。
  一个措辞问题：矩阵里 token-only 方法写「no-op / 当前 factory 行为」。MRV1 是**静默未读取**（这些 proposer 不继承 base，见 `vllm_ascend/spec_decode/__init__.py:41-70`），MRV2 则是 **factory 直接 `NotImplementedError`**（`worker/v2/spec_decode/__init__.py:72`）。两者混写会让后来读者以为应当实现一个「silent no-op」。
- **需要的源码证据**：无（已核实）。
- **建议修改**：把该行拆成两列（MRV1 行为 / MRV2 行为），避免把「MRV1 silent no-op」误读成 MRV2 应实现的行为。

### 17. native model SWA 与 `draft_window_size` 是否双重计算错误

- **风险：高（Major M4）**
- **章节**：§Design Invariants 17、R8、§Method Integration Matrix「metadata backend 消费矩阵」SFA 行、§Week4 §2（native sliding-attention provider）
- **为什么可能发生**：Codex 把这条列为「风险」并说「backend capability 定义交集/优先级；未验证组合 fail fast」，但**没有给出三种 backend 的实际组合语义**。而事实是三种 backend 的行为**互不相同**，且其中一种根本不能靠「裁剪表 + 缩短长度」实现：

  | backend | native SWA 如何生效（已核实） | 与 `draft_window_size` 的正确组合 |
  | --- | --- | --- |
  | GQA/FIA | `sparse_mode=4 / pre_tokens=sliding_window / next_tokens=0`（`vllm_ascend/attention/attention_v1.py:602-604`），且 `is_draft_model=True` 时仍传 `block_table`（`:459-472`） | **真交集**：band 在窗口化坐标系上计算（basis = `actual_seq_lengths_kv`），与窗口取更紧者。语义正确。 |
  | DSA（non-causal DSpark） | 可见性由**显式索引集合**表达：`build_dspark_swa_indices()` 用 `hf_config.sliding_window` 算 `start_pos = clamp(prefix_lens - window_size, 0)`（`attention/dsa_v1.py:410, 448-461, 1107, 1108-1125`），op 消费 `ori_sparse_indices`（`:2265-2270`) | **两者是同一条派生式**：`draft_window_size` 只能通过把这里的 `start_pos` 夹紧来生效。**只裁 block table 对这条路径完全无效**（op 不读表）。注意 `dsa_v1.py:1107` 直接做 `hf_config.sliding_window - 1`，**没有 None 检查** → DSA-backed draft 必然带 native window。 |
  | SFA（sparse MLA） | **native window 在该路径不生效**：`ori_mask_mode=0`、`ori_win_left=ori_win_right=-1`，注释「Only ori_mask_mode 4 may carry a bounded window on this product line」（`vllm_ascend/attention/sfa_v1.py:114-119`）；可见性来自 top-k 索引（`:198-219`） | 只有窗口（或窗口 + top-k 交集）一个来源；不能假定 native SWA 在做交集。 |

  因此 Codex 的 Invariant 17（「模型原生 SWA/DSA index 与外部 `draft_window_size` 分属不同对象和生命周期」）**在 DSA 路径上是错的**：它们必然汇聚到同一段派生代码里，必须「合并」而不是「分离」。
- **需要的源码证据**：目标 draft 模型实际激活哪些 attention backend（GQA/MLA/SFA/DSA）；DSpark 的 `cad.causal` 取值（MRV1 从 `model.get_draft_attn_causal()[0]` 取，见 `vllm_ascend/spec_decode/dspark_proposer.py:343-347`），它决定走「causal + 表/长度」还是「non-causal + 索引」。
- **建议修改**：① 把 Invariant 17 改写为「两个配置来源，一份可见性派生」；② 在 §Method Integration Matrix 增加一张 **backend × 可见性表达** 表（GQA=表+长度；MLA=表+长度；DSA-causal=表+长度；**DSA-non-causal=索引**；SFA=索引+top-k），并把「窗口在该 backend 上如何生效」逐行写清；③ 明确 `draft_window_size` 在 DSA 路径上是**夹紧 `start_pos`**（即 `min(native_window, draft_window_size)`），并加一条测试断言派生出的索引集合整体落在 `[start,end)` 内（只断言长度不够）。

### 18. DCP / PCP / SP / CP local length

- **风险：低（Codex 在这条上比朴素做法正确）**
- **章节**：§Design Invariants 9、§Buffer 2（DCP/local 行）、§Buffer 3、R5、R7、§Method Integration Matrix「DCP/CP」行
- **为什么可能发生**：见 §0.3 —— Codex 的「`local_prefix(end) - local_prefix(start)`」是对的，且它明确禁止「`prefix(window_len)`」这种朴素做法（后者会让 rank-local 可见范围错位）。这是我核实后确认的重要正确点。
  残余问题：Ascend funnel 会**从 `seq_lens_cpu` 派生 `dcp_local_seq_lens_cpu`**（`vllm_ascend/worker/v2/attn_utils.py:266-273`）。如果窗口只提供 upper 而不提供 CPU exact，那么 CPU local 会继承 upper 精度（即「upper 当 exact」），而 MLA DCP decode 是直接消费它的（`vllm_ascend/attention/context_parallel/mla_cp.py:202-219`）。Codex 没有把这条 CPU-local 派生链写进「必须同 origin」的清单。
- **需要的源码证据**：`cp_kv_cache_interleave_size` 的实际取值（稀疏 + DCP 时被强制为 `cache_config.block_size`，见 `vllm_ascend/platform.py:1322-1329`）与 `start` 的对齐粒度是否整除关系；`AscendPCPManager.prepare_draft_prefill` 的 no-op 语义（`vllm_ascend/worker/v2/pcp_manager.py:383-392`，评论「Ascend PCP spec decode is always replicated」）是否覆盖所有路径。
- **建议修改**：把 `dcp_local_seq_lens_cpu` 的派生链（funnel `:266-273`）加入 Invariant 9 的清单；如果窗口无法提供 CPU exact，则在 DCP + MLA 组合下**fail fast**，而不是让 CPU local 继承 upper。

### 19. Flashcomm interaction

- **风险：低（但方向建议修正）**
- **章节**：§Week4 §2（`FlashcommWindowLayoutProvider`）、§Week4 §5（`supports_flashcomm`）
- **为什么可能发生**：已核实 Flashcomm 在 Ascend 上**就是 SP-MoE 开关**（`vllm_ascend/ascend_config.py:639-657`：注释「FlashComm remains the SP MoE switch on Ascend」），`enable_sp()` 返回 `use_sequence_parallel_moe`（`vllm_ascend/utils.py:916-928`），并且在 SFA 里只被赋值一次、之后没有任何用它改 block table 的分支（`vllm_ascend/attention/sfa_v1.py:869`）。也就是说 **Flashcomm 不改变 block table 布局**，为一个布局无关的开关设计 `xxxLayoutProvider` 会误导实现者。
  真正相关的是它带出来的 **DSA-CP**（DSA-CP 要求 SP-MoE 打开，否则自动关闭，`ascend_config.py:694-698`；打开 DSA-CP 时会自动打开 Flashcomm，同文件 `:641-657`），而 DSA-CP 切的是 **token 流**（`vllm_ascend/attention/context_parallel/dsa_cp.py:1133-1138, 1166-1168`），不改 block table。
- **需要的源码证据**：`enable_sp()` 的其它消费点（确认无布局影响）。
- **建议修改**：删掉 `FlashcommWindowLayoutProvider`，把 §Week4 §5 的 `supports_flashcomm` 改为 `supports_dsa_cp`；新增 `DSACPWindowLayoutProvider`，其职责写清是「求 window ∩ 本 rank token slice 的绝对区间，并派生该区间对应的 local length」（而不是「重排 block table」）。

### 20. model-specific assumptions

- **风险：中**
- **章节**：§Design Invariants 16、§Config/Compatibility Policy 2、R17、§Expected File Changes（target model/config capability 声明位置）、§open questions 7
- **为什么可能发生**：把「共享代码不检查模型名」写成不变量是对的，且把 DeepSeek-V4 advisory 归到 **target** model/config 也对（MRV1 就是在 `AscendSpecDecodeBaseProposer.load_model` 里用 `self.vllm_config.model_config.hf_config.model_type.startswith("deepseek_v4")` 判 target，见 `llm_base_proposer.py:420-422`）。但有四个具体假设没被点名：
  1. MRV2 speculator 同时有 `self.vllm_config`（target）与 `self.draft_vllm_config`；用错一个就会把 advisory 判反。文档应指名用哪个字段。
  2. `use_updatable_graph()` 只对 `AscendAttentionBackend` 为真（`vllm_ascend/utils.py:1769-1775`）——这是一个被设计隐含依赖的 capability，应显式列入 capability 字段。
  3. DSA 路径假设 `hf_config.sliding_window` 非 None（`attention/dsa_v1.py:410, 1107`）。
  4. 「每个 group 都窗口化」还是「只对 draft attention 的 group 窗口化」：`self.draft_kv_cache_group_ids` / `draft_attn_layer_names` 存在（`vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:94-99`），对 cache-only group 也分配窗口是纯浪费。
- **需要的源码证据**：目标 draft 的 group → backend 映射；哪些 group 有 draft attention layer。
- **建议修改**：① 在 §Config 2 指名 `speculator.vllm_config.model_config`（target）；② capability 表加 `supports_updatable_graph`；③ 明确窗口只对 `draft_kv_cache_group_ids` 分配。

### 21. hidden performance regressions

- **风险：中**
- **章节**：§Test 8（验收指标）、§Buffer 2（内存公式）、R15、§E2E
- **为什么可能发生**：Codex 的验收指标写得对（「materialization 开销不抵消 Draft Attention 节省」），但它在文档里**假定的收益来源与 §11 的发现冲突**：
  1. **`max_seq_len` 如果被窗口化，在 FULL 下可能不生效**：capture 用 `max_model_len`（`dflash/cudagraph.py:64`、Ascend `model_states/default.py`），captured op 的 tiling/workspace 是按那个值定下来的。replay 给窗口量级的值→要么无用、要么与捕获形状不符。因此 **`max_seq_len` 应当保持「容量上界」语义（不窗口化）**，收益只能来自 table/length 路径；这一点必须写清，否则 E2E 会看到「窗口开了但没加速」而误判为 kernel 问题。
  2. `seq_lens_list` 的构造目前是 `next_seq_lens_cpu.tolist()`（`vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:756`）——每 step 一次 host list；窗口不应引入额外的 `.numpy()` / pinned 拷贝 / D2H。建议在 window 路径上加「不新增 `.item()` / `.cpu()` / `.numpy()`（除既有 per-step list）」的静态检查或断言。
  3. AR FULL merged decode 的 per-step 长度需要 `[K-1, G, R]` 额外 buffer，且 Codex 自己在 R15 承认可能**按 capture size/lane 重复分配**——这是内存随 descriptor 数线性增长，需要量化。
- **需要的源码证据**：capture descriptor 数量（`collect_sorted_captured_token_sizes`，`vllm_ascend/worker/v2/aclgraph_utils.py`）；FIA/MLA/DSA 的 tiling 是否真的由 `max_seqlen_kv` 决定。
- **建议修改**：① 明确 `max_seq_len` 不窗口化并说明原因；② §Buffer 2 增加「窗口表按 full 宽度（若采纳 §11 建议 1）」后的内存重算；③ §Test 8 增加「窗口开启后 device kernel 侧的 KV 读长度确实下降」的可量化断言，而不只是端到端吞吐。

### 22. persistent buffer memory overhead

- **风险：低**
- **章节**：§Buffer 2、R15
- **为什么可能发生**：公式与例子都对（`C_g = ceil(W/b)+1`；`R=256, C_g=17, int32` ≈ 17 KiB），且它正确指出内存由 `W` 而非 `max_model_len` 决定 ✓（这点很关键，应保留）。
  但 §11 建议的「同 shape 宽表」会把这个结论改成 `O(R × G × full_width)`（例：`256 × 1024 × 4 B × 4 group` ≈ 4 MiB）。两版都要在文档里各给一份数字，并说明这是「为了 capture/replay 形状一致」付的价。
- **需要的源码证据**：`max_num_reqs`、各 group 的 `max_num_blocks` 实际量级。
- **建议修改**：§Buffer 2 增加「宽表方案」的内存一栏，并注明 R15（per-descriptor 重复）在宽表方案下会放大 descriptor 倍。

### 23. multi-request / dynamic batch

- **风险：低**
- **章节**：§Buffer 2（`[R, C_g]`、per-row 有效列）、§Test 2/6（reorder、shrink）
- **为什么可能发生**：基本覆盖。`window_start_tokens[g]` 是 `[R]`、容量公式用 `planned_needed_columns[row]`，都是 per-row 语义 ✓。
  一个细节：Codex 的 `window_block_tables[g]` 列容量 `C_g` 是 per-group 标量，而**同一 group 内不同 row 的 needed 不同** —— 这是对的（容量取最大），但「`needed_g[row]` 之外列清零」这条（防 stale）在 §Buffer 4 写了 ✓。补一条：请求在 prefill 阶段（chunked prefill）时 `W > seq_len` → `start=0`，窗口等于全量，此时表内容应等于 full 表（Codex 的 §Test 1 覆盖 `seq <= W - K` ✓）。
- **建议修改**：无实质问题。建议在 §Test 2 增加「同一 group 内不同 row 的 needed 不同」的断言。

### 24. preemption / request removal

- **风险：中（Major M5）**
- **章节**：§Test 7（「request 完成、移除、row 复用时旧 window 数据不可见」）、R16
- **为什么可能发生**：Codex 只在测试清单里提了一句，**设计层面没有覆盖 preemption 的特有风险**：request 被抢占后 Scheduler 会释放它的 block，`num_blocks` 收缩、`idx_mapping` 的 row 可能被**新请求复用**。如果此时窗口表里仍留着旧 row 的 block id，而某个长度/valid-count 又恰好允许读取，kernel 会读到**已经归属另一个 request 的物理块**——这比「多看几个历史 token」严重得多（静默读到无关请求的 KV）。Codex 的 `full_valid_num_blocks` + 「inactive row 每次写确定值」能缓解，但前提是「row 的有效性边界每次都与本轮 `idx_mapping`/`num_blocks` 对齐」——这需要显式规则，而不是隐含在测试里。
- **需要的源码证据**：MRV2 的 request add/remove/row 复用路径（`vllm_ascend/worker/v2/model_runner.py` 的 `add_requests`/`update_requests`/`stale` 处理）；preemption 是否会在同一 step 内复用 row。
- **建议修改**：在 §Design Invariants 增加一条：**任何 `idx_mapping` 或 `num_blocks` 的变化都必须使窗口 view 失效（epoch 前进），且 preview 的 (`row → request_id`) 映射必须纳入 epoch 校验**。补一条「抢占 + row 复用」的专项测试（不只是「旧数据不可见」）。

### 25. graph padding / different batch shapes

- **风险：低中**
- **章节**：§Graph Strategy 3、R15、§Test 6
- **为什么可能发生**：Codex 覆盖了「capture dummy 与 runtime batch 不同」。两个具体收口项：
  1. funnel 会对表做 `x[:num_reqs_padded]`（`vllm/v1/worker/gpu/spec_decode/speculator.py:322-324`），这是**非零起点 slice**：地址不变但 `storage_offset` 变，且每个 descriptor 不同。Codex 的「`data_ptr()` 不变」断言不足以覆盖（见 §3.10 建议）。
  2. `window_block_tables[g]` 的**列容量**必须覆盖所有 capture descriptor 下需要的 `needed` 最大值；Codex 用 `max_visible_span_over_one_proposal ≤ W + alignment_slack_g` ✓，但 `alignment_slack_g` 需要与 `lcm` 对齐方案（§3.7 建议）一起重算。
- **建议修改**：断言改为 `(data_ptr, storage_offset, shape, dtype)` 四元组、按 descriptor 比；容量公式在采纳「单一 start + lcm 对齐」后重新给出。

---

## 2. Critical Issues

### C1 — capture 期 metadata 链路被完整漏掉，导致窄窗口表在 FULL 下不可实现

**风险等级：致命 / 阻塞实现。**

**对应章节**：§Graph Strategy 3、§Graph Strategy 6、§Expected File Changes、§Comparison「Graph capture」行、§核心决策 9。

**为什么可能发生**（源码证据，全部本机核实）：

1. Codex 只承认两个 metadata 构建入口（live build + graph-manager replay rebuild）。实际有**三个**，第三个是 **capture 期的 dummy metadata**：
   - DFlash/DSpark：`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:36` 取 `block_tables.get_dummy_block_tables(num_reqs)`，在 `:55` 调 `build_attn_metadata(...)`。该符号由 `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26` 在**导入期**重绑定模块全局（`cudagraph_module.build_attn_metadata = build_attn_metadata`），**不经过** `build_attn_metadata_wrapper()`（后者只替换 `vllm.v1.worker.gpu.spec_decode.speculator` 模块，见 `vllm_ascend/worker/v2/attn_utils.py:1240-1251`）。
   - AR/Target：`vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:111` 调 `prepare_inputs_to_capture(...)` → 上游 `vllm/v1/worker/gpu/cudagraph_utils.py`（约 `:785` 取 dummy 表、约 `:820` 调 `model_state.prepare_attn(...)`）→ Ascend `vllm_ascend/worker/v2/model_states/default.py:95-121` → Ascend funnel。
   - 两者传入的 block table 都是 **full 宽度的零表**（`vllm/v1/worker/gpu/block_table.py:177-187`：`block_table[:num_reqs].zero_()`）。
2. capture 期**没有任何显式通道**能拿到 `DraftAttentionView`：DFlash 的 capture 在上游文件里、签名没有 view 参数；AR 的 capture 走的是 Target 与 Draft 共用的 `prepare_attn`。
3. Codex 的窗口表是**窄表**：`window_block_tables[g] : [R, C_g]`，`C_g = ceil(W / block_size_g) + 1`（§Buffer 2）。
4. 于是 capture 会把 **full 宽度**的 `block_table` 参数固化进 graph，replay 却要传**窄表** → 形状/参数不一致。对 **SFA / DSA** 尤其致命：`update_graph_params()` 是 no-op（`vllm_ascend/attention/sfa_v1.py:885-896`；`AscendDSAImpl.update_graph_params`），captured op 读的就是 capture 期那块 storage，**既不能换 pointer 也不能换 shape**。
5. 这与 Codex 自己的三个约束同时冲突：窄表（§Buffer 2）、「capture 使用与 runtime 完全相同 shape」（§Graph Strategy 3）、「第一版不改上游 vLLM」（§核心决策 9）、「不用隐式全局上下文」（§Async 4）——**四者不可能同时成立**。
6. 附带（同一处证据）：`max_seq_len` 在 capture/replay 间**本来就不同**（capture：`max_model_len`，`dflash/cudagraph.py:64` 与 Ascend `prepare_attn` 的 `max_seq_len=self.max_model_len`；replay：`self.draft_max_seq_len`，`vllm/v1/worker/gpu/spec_decode/speculator.py:361`）。Codex 的 Invariant 9「`max_seq_len` 从 Window view 派生」会把这个既有分歧放大，且可能让捕获到的 tiling 与实际输入不符。

**需要什么源码证据证明安全**：
- 完整枚举 draft 侧所有 metadata 构建入口（含 capture）；
- 每个 backend 在 `for_cudagraph_capture=True` 时把 `block_table` 的 shape 固化到何处（SFA 的 `SparseMLAMetadataState` buffer、DSA 的 req metadata、GQA/MLA 的 graph param pool）；
- `max_seq_len` 在 capture descriptor 与 replay 之间是否必须一致（影响 tiling/workspace）。

**建议修改**（必须显式选一条并写进文档）：
1. **（推荐）窗口表与 full 表同 shape**：只改内容——列 `[0, needed)` 放窗口内真实块、列 `[needed, row_width)` 显式清零、row 尾部按 `full_valid_num_blocks` 约束。这样 capture 的 dummy（全 0）与 replay 的窗口表形状一致，SFA/DSA 的 builder-owned buffer 布局不变，**不需要改上游**。代价是每步多写若干列 0、多占 `O(R × G × full_width)`（数量级 MiB，可接受）。
2. 保持窄表，但**接受改上游**：给 `_prepare_dflash_inputs_to_capture` 与 `cudagraph_utils.prepare_inputs_to_capture` 加显式 view 参数，并更新 §Non-goals。
3. 保持窄表 + 在 capture 期走隐式上下文（复用 `_EXTRA_CTX`，capture 期 `is_draft_model` 已被 `model_capture_wrapper` 置 True，见 `autoregressive/aclgraph.py:90`）。这需要放弃 §Async 4 的立场，并承认与 Candidate A 相同的失败模式。
4. **无论选哪条**：把 capture 入口写进「metadata 构建入口清单」，并把 `max_seq_len` 明确为**容量上界、不窗口化**；补测试断言 capture/replay 传给 backend 的 `block_table` 的 `(data_ptr, storage_offset, shape, dtype)` 一致。

---

## 3. Major Issues

### M1 — AR first-pass 重建缺少「query layout 必须与 Target 逐位相同」的硬约束

**风险：静默算错第一个 draft token。**
**章节**：§Method Integration Matrix（Eagle 行）、§Runtime Data Flow（Eagle eager）、R1。
**为什么**：上游明确说明 AR first pass 复用 Target metadata 的**原因**是「把每个请求的 query 长度补齐到包含 rejected positions」，从而 shape 与 KV layout 一致（`vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:233-238`、`:311-313`）；而 `prepare_prefill_inputs` 的 kernel 会按 `num_rejected` 裁掉无效 query 尾部（同文件 `:719-721`）。若「重建」用裁剪后的 draft layout，first-pass 的 batch shape 就与 Target hidden states 不对齐 → 结果只是 acceptance 变差，不报错。
**需要的证据**：`prepare_prefill_inputs` kernel（`:690-770`）写出的 `query_start_loc` / `positions` / `seq_lens` 与 Target 的对应关系。
**建议**：写成硬不变量——**重建后的 first-pass metadata 与 Target 相比，`query_start_loc(_cpu)`、`positions`、`num_tokens`、`is_prefilling` 必须逐位相同，只允许 `block_table_tensor` 与 length 字段不同**；补差分测试。

### M2 — per-group `start_tokens` 改变了 feature 语义（从「一个窗口」变成「每 group 一个窗口」）

**风险：acceptance 行为变更，且与 Invariant 8 自相矛盾。**
**章节**：§MRV2 Constraints 2、Invariant 7/8、§Buffer 2、§DraftWindowGroupView。
**为什么**：MRV1 只有一个对齐量——`SlidingWindowAdapter(W, self.kernel_block_size, ...)`，其中 `kernel_block_size` 取**第一个 draft attention layer** 的（`vllm_ascend/spec_decode/llm_base_proposer.py:406-408, 446-452`），DSpark 的 per-group 循环复用的也是这同一个 `self.block_size`（`:2604-2605`）。所以 MRV1 下所有 group 共享**同一个绝对窗口起点**。Codex 让 `start_tokens` 逐 group 不同，会让 hybrid multi-group draft 的不同 group 看到不同长度的历史——这需要产品决策，且正是 Invariant 8 想防的「多个 origin」。
**需要的证据**：目标 draft 的 group 数、各自 `kernel_block_size`；MRV1 在 hybrid + window 下是否有测试（据核实：没有；MTP 是唯一多 group 用例而它被忽略）。
**建议**：改为「一个 proposal 一个绝对 `start`，对齐到 `lcm{kernel_block_size_g}`；per-group 只体现在 `start_col_g = start / b_g` 与 `needed_g`」。这样保留 MRV1 语义与单一 origin，同时 per-group 列映射仍然正确。

### M3 — 未收口 Ascend funnel 的 CPU length 兜底（会直接触发最高危失败模式）

**风险：表窗口化而 CPU 长度仍是 full → 读到 cache 第 0 块。**
**章节**：§MRV1 CPU upper-bound 一节、Invariant 8、§Buffer 3、§DraftWindowGroupView、R20。
**为什么**：`vllm_ascend/worker/v2/attn_utils.py:256-258` 在 `seq_lens_np is None` 时用 `np.full(num_reqs, max_seq_len)` 兜底，而 Draft 路径的 `max_seq_len` 是 full 量级的 `draft_max_seq_len`（`vllm/v1/worker/gpu/spec_decode/speculator.py:361`）。Codex 把 CPU exact 标为「有条件能力」，若实现据此留空，兜底就会给出 full 长度；MLA 是 CPU 优先（`vllm_ascend/attention/utils.py:573-576`、`attention/mla_v1.py:504-505`），路径可达。另有 `seq_lens_cpu_upper_bound is None ⇒ seq_lens_cpu`（`attn_utils.py:259-260`）与 `_seq_lens_cpu` 的优先分支（`attention/utils.py:573-574`）两个次生风险；以及通过 `from_numpy` 注入会改变 `seq_lens_cpu` 的存储别名，影响 AR 事后 `metadata.seq_lens_cpu.copy_(...)`（`worker/v2/spec_decode/autoregressive/speculator.py:776`）。
**需要的证据**：GQA(`_select_seq_lens`)/MLA/SFA/DSA 各自最终取的 length 字段清单。
**建议**：把「view 存在时必须同时覆盖 `seq_lens_np` 与 `seq_lens_cpu_upper_bound`」写成硬不变量；funnel 在 `view is not None and seq_lens_np is None` 时**抛错**而非兜底；明确 CPU 向量的存储 owner 与事后 `copy_` 机制；补「窗口开启时任何 backend 拿到的 CPU 长度都 ≤ 窗口容量」的断言。

### M4 — native SWA × `draft_window_size` 仍是「风险」而非 spec，且 Invariant 17 在 DSA 路径上是错的

**风险：窗口在 DSA 路径上完全无效（只裁表），或与 native window 双重/矛盾计算。**
**章节**：Invariant 17、R8、§Method Integration Matrix（SFA 行）、§Week4 §2。
**为什么**：三种 backend 行为不同（见 §1.17 表）。DSA non-causal DSpark 的可见性由显式索引集合表达（`vllm_ascend/attention/dsa_v1.py:448-461, 1108-1125, 2265-2270`），**op 不读 block table**；`dsa_v1.py:1107` 还直接 `hf_config.sliding_window - 1`（无 None 检查），即该路径必然存在 native window，二者必然汇到同一段派生代码。SFA 路径则相反：`sfa_v1.py:114-119` 强制 `ori_mask_mode=0 / ori_win_left=-1`，**native window 不生效**，可见性来自 top-k。GQA 才是真正的「交集」（`attention_v1.py:602-604`）。
**需要的证据**：目标 draft 的 backend 与 `cad.causal`（决定走表/长度还是索引）。
**建议**：把 Invariant 17 改为「两个配置来源、一份可见性派生」；补 backend × 可见性表达 表；明确 DSA 上 `draft_window_size` 的实现是**夹紧 `start_pos`**（`min(native, draft)`），并测试断言派生索引整体落在 `[start,end)`。

### M5 — preemption / row 复用没有设计层规则

**风险：读到已被重新分配给他人的物理块。**
**章节**：§Test 7（仅测试层提及）、R16。
**为什么**：抢占会释放 block、收缩 `num_blocks`，并可能让 `idx_mapping` 的 row 被新请求复用。窗口表里残留的 block id 配上任何「允许读」的长度/valid-count，就会读到**属于另一个请求的块**——比多看历史严重。
**需要的证据**：MRV2 的 request add/remove/row 复用路径（`vllm_ascend/worker/v2/model_runner.py`）。
**建议**：增加不变量——**`idx_mapping` 或 `num_blocks` 任何变化都使窗口 epoch 前进**，并把 `(row → request_id)` 纳入 epoch 校验；补「抢占 + row 复用」专项测试。

---

## 4. Minor Issues

| # | 问题 | 章节 | 建议 |
| --- | --- | --- | --- |
| m1 | 数据_ptr 断言不足以覆盖 slice view（funnel 做 `x[:num_reqs_padded]`，offset 随 descriptor 变） | §Test 2、§Graph 3 | 断言改为 `(data_ptr, storage_offset, shape, dtype)` 四元组，逐 descriptor 比 |
| m2 | Patch 1「让 MRV1 adapter 委托公共数学」无用户收益、却动已上线 feature，且 MRV1 CPU mirror 是各字段独立重算（`spec_decode/utils.py:165-169`）与 MRV2 canonical-origin 语义不同 | §核心决策 1、§Expected File Changes | 删掉该 patch；先补 MRV1 golden 值测试再谈合并 |
| m3 | R19 的触发条件算错了：负 `visible_len` 需要 `K - W ≥ b`（即窗口 + 一个 block 跨度都不够），**不是** `W < K`；而 `K ≤ 15`（`assert decode_threshold <= 16`，`attention/attention_v1.py:248`、`dsa_v1.py:654`、`mla_v1.py:299`、`sfa_v1.py:524`）且 `b ≥ 16`，所以正常配置下**不可达**（仅 `b ≤ K - W` 的极端组合可达） | §窗口数学、R19 | 把「要求 `W >= K`」换成「计算后断言 `visible_len >= 0`，否则 fail fast」；`W >= K` 的配置收紧没有依据，会误伤 |
| m4 | padding 约定未枚举；GQA/FIA 其实把 `seq_lens_list`/`seq_lens` 用 **1** 补齐并追加零表行（`attention/attention_v1.py:361-365`），安全性的真正条件是「padding row 的 block id 不与任何 active row 相交」 | §Buffer 4、Invariant 12 | 补 per-backend padding 约定表 + 上述不相交断言 |
| m5 | `window_num_blocks[g]` 标了「若 kernel 需要」，但当前 funnel 没有这条通道（length 走 `actual_seq_lengths_kv`/`max_seqlen_kv`） | §Buffer 2 | 说明它只作 workspace 内部 / debug 用途，避免实现者去找不存在的消费方 |
| m6 | 只说「for every supported gid」，未限定 draft attention 的 group | Invariant 7、§Buffer | 限定为 `draft_kv_cache_group_ids`，避免给 cache-only group 浪费内存 |
| m7 | token-only 方法在 MRV1 是「静默未读取」，在 MRV2 是 factory `NotImplementedError`，两者被混写成「no-op / 当前 factory 行为」 | §Method Integration Matrix | 拆成两列，防止后来实现一个不该存在的 silent no-op |
| m8 | `FlashcommWindowLayoutProvider` 方向错误：Flashcomm = SP-MoE 开关，不改 block table 布局（`ascend_config.py:639-657`、`utils.py:916-928`、`sfa_v1.py:869`） | §Week4 §2/§5 | 换成 `DSACPWindowLayoutProvider` + `supports_dsa_cp` |
| m9 | AR FULL merged decode 的 per-step buffer 会按 capture descriptor 重复分配（R15），内存随 descriptor 数线性增长 | R15、§Buffer 2 | 量化 descriptor 数，给出「最大容量复用」的具体复用粒度 |
| m10 | `max_seq_len` 被列入「从 Window view 派生」，但它其实是 capture/replay 间已被固化的容量参数 | Invariant 9、§Buffer 2 | 明确不窗口化，并解释为何（见 C1 附带发现） |
| m11 | lease release 时点在 legacy 路径上偏早：参数更新发生在 replay **之后**（`autoregressive/aclgraph.py:154-194`、`dflash/aclgraph.py:100-138`） | §Async 3/§Buffer 5 | release 条件改为「最后一个 reader + graph-param update 均完成」 |

---

## 5. Questions Requiring Source Verification

> Codex 自己在 §Risks §2 列了 10 条待关闭问题，方向大多正确。以下是我**追加或修正**的，按优先级排列。

1. **Q-A（阻塞 C1）**：draft 侧 metadata 构建入口的完整清单——live、graph-manager rebuild、**capture-time dummy**，以及各自的 block table 来源与 `max_seq_len` 来源。已核出三条（`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:55`；`vllm_ascend/.../dflash/aclgraph.py:86-98`；`vllm/v1/worker/gpu/cudagraph_utils.py` → Ascend `model_states/default.py:95-121`），需确认是否还有第四条（PP/DP 变体、`_310p`）。
2. **Q-B（阻塞 M4）**：目标 draft 模型实际激活的 attention backend 集合，以及 DSpark 的 `cad.causal`。DSA-non-causal 与 causal 对应两套完全不同的实现路径。
3. **Q-C（阻塞 M2）**：目标 draft 是单 group 还是 multi-group；各组 `kernel_block_size`/`tokens_per_table_column`。这决定 per-group start 是理论风险还是现实风险。
4. **Q-D（阻塞 M3）**：GQA / MLA / SFA / DSA 各自最终消费的 length 字段（device / `seq_lens_cpu` / `_seq_lens_cpu` / list / `max_seqlen_kv`），以及 `_seq_lens_cpu` 在 MRV2 是否仍恒为 `None`。
5. **Q-E**：capture 期 `for_cudagraph_capture=True` 时，各 backend 把 `block_table` 的 shape 固化到哪里（SFA `SparseMLAMetadataState` 的 buffer / DSA req metadata / GQA-MLA graph param pool）——决定 C1 只能选哪条路。
6. **Q-F**：`max_seq_len` 是否必须 capture/replay 一致（影响 FIA/MLA tiling 与 workspace）——若必须一致，则 Invariant 9 必须修正。
7. **Q-G**：`update_stream` 与 graph-param update 的 happens-before（决定 lease 的 release 时点，见 m11）。Codex 的 §Graph Strategy 4 排出的顺序（materialize → update → replay）与现有 legacy 代码顺序（replay → update）相反，需要确认设备侧真实生效时刻，而不是按 Python 语句顺序推断。
8. **Q-H**：async scheduling 下是否存在多个 in-flight device epoch。仓库已有 `UvaBufferPool` ≥2 slot 的先例，倾向「存在」，需确认 draft 侧的具体并发深度。
9. **Q-I**：preemption 是否会在同一 step 内复用 row（决定 M5 的严重度）。
10. **Q-J**：`dcp_local_seq_lens_cpu` 的实际派生链在 window 下的精度（`attn_utils.py:266-273` 从 `seq_lens_cpu` 派生）+ `cp_kv_cache_interleave_size` 与 `start` 对齐粒度的整除关系（决定是否必须 fail fast，见 §1.18）。
11. **Q-K（修正 Codex 的 open question 6）**：Codex 提议批准 `W >= K` 的 AR 校验。我的推导表明该条件的**真正**必要形式是 `K - W < b`（即只要窗口加一个 block 跨度足以覆盖未来），而 `W < K` 本身不构成问题；请复核我的推导（`start = align_down(max(L+K-W,0), b)`，`visible = L - start < 0 ⟺ align_down(L+K-W,b) > L ⟺ K-W ≥ b`）。
12. **Q-L**：DeepSeek-V4 advisory 由 target 的哪个字段暴露（MRV1 用 `self.vllm_config.model_config.hf_config.model_type`，见 `llm_base_proposer.py:420-422`），以及 MRV2 speculator 里应读 `self.vllm_config` 还是 `self.draft_vllm_config`。

---

## 6. Recommended Design Changes

按「先解除阻塞、再收敛范围」排序。

1. **解除 C1：显式选定 capture/replay 形状策略。** 推荐「窗口表与 full 表同 shape、只改内容」，并把 capture 入口写进设计清单。同时把 `max_seq_len` 明确为不窗口化的容量上界。若坚持窄表，则必须在文档里承认需要修改上游 `cudagraph_utils.py` / `dflash/cudagraph.py`（更新 §Non-goals）。
2. **补一条 AR first-pass 的 layout 不变式**（M1）：重建 metadata 与 Target 在 `query_start_loc(_cpu)` / `positions` / `num_tokens` / `is_prefilling` 上逐位相同；只许 read view 不同。
3. **把 per-group `start` 收敛为 per-proposal 单一 `start`**（M2），对齐到 `lcm{kernel_block_size_g}`，per-group 只保留列映射；若产品确要 per-group 窗口，写成独立 contract 变更。
4. **收口 CPU length 兜底**（M3）：view 存在时强制覆盖 `seq_lens_np` 与 `seq_lens_cpu_upper_bound`，否则 fail fast；明确 CPU 向量存储 owner。
5. **把 native SWA 组合从「风险」升级为 spec**（M4）：写 backend × 可见性表达表；DSA 上实现为夹紧 `start_pos`；SFA 上明确 native window 不生效。
6. **增加 preemption/row 复用的失效规则**（M5）：`idx_mapping`/`num_blocks` 变化 ⇒ epoch 前进 + `(row → request_id)` 校验。
7. **收缩首期范围，删掉三件事**：
   - 删 Patch 1（不动 MRV1 adapter，m2）；
   - 删 `FlashcommWindowLayoutProvider`（m8）；
   - 删 `W >= K` 的配置收紧，换成 `visible_len >= 0` 的运行时断言（m3）。
   并给出**明确的 MVP 支持矩阵**（建议：`{dspark, dflash} × {GQA, MLA} × {eager, FULL}`，其余由 capability 解析 fail fast），把 `DraftWindowLayoutProvider` 可插拔框架、`DraftWindowLease` 多 lane、SP/DSA-CP provider 放到后续 PR。理由：当前设计新增 10 个对象、改 10 个文件，而 MRV1 的同类实现只有约 90 行（`vllm_ascend/spec_decode/utils.py:83-169`），`AGENTS.md` 要求 patch「minimal and focused」且需有长期上游计划。
8. **把 12 条待验证问题列为实现前的门禁**：未关闭的组合一律 fail fast，绝不允许「静默回退到可能错误的窗口 view」——这一点 Codex 已经写明（§Risks §2 末段），需要在采纳上述修改后扩表。

---

## 附录 A：本次评审新核实的源码事实（可直接引用）

| 事实 | 位置 |
| --- | --- |
| DFlash/DSpark 的 capture 期 dummy metadata：`get_dummy_block_tables`（full 宽度零表）→ 模块级 `build_attn_metadata` | `vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:24-71`（`:36`、`:55`） |
| 该模块符号由 patch 在**导入期**重绑定，绕过 wrapper | `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26`（`cudagraph_module.build_attn_metadata = build_attn_metadata`） |
| wrapper 只替换 `vllm.v1.worker.gpu.spec_decode.speculator` 模块 | `vllm_ascend/worker/v2/attn_utils.py:1240-1251`（`_BUILD_ATTN_METADATA_MODULE`） |
| AR/Target capture 走 `model_state.prepare_attn(...)`，dummy 表 + `max_seq_len=max_model_len` | `vllm/v1/worker/gpu/cudagraph_utils.py`（`get_dummy_block_tables` 约 `:785`；`prepare_attn` 约 `:820`）；Ascend `vllm_ascend/worker/v2/model_states/default.py:95-121` |
| AR draft decode capture 调用 `prepare_inputs_to_capture` | `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:103-128`（`:111`） |
| capture 期 `is_draft_model` 由 `model_capture_wrapper` 置位 | `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:90` |
| replay 路径的 `max_seq_len` 是 `self.draft_max_seq_len` | `vllm/v1/worker/gpu/spec_decode/speculator.py:361` |
| Ascend funnel 的 CPU 兜底 | `vllm_ascend/worker/v2/attn_utils.py:256-260` |
| MLA 的 CPU 优先选择链 | `vllm_ascend/attention/utils.py:573-576`；`vllm_ascend/attention/mla_v1.py:504-505` |
| `_select_seq_lens` 的 parallel-drafting 覆盖与 DSpark+GLM 例外 | `vllm_ascend/attention/utils.py:582-587` |
| `get_dcp_local_seq_lens` 的非线性（证明 `local(end)-local(start) ≠ local(end-start)`） | `vllm/v1/attention/backends/utils.py:1088-1133` |
| FIA 给 dummy request 补 `seq_lens_list`/`seq_lens` 用的是 **1** | `vllm_ascend/attention/attention_v1.py:361-365` |
| DSA non-causal 的显式可见索引（`start_pos = clamp(prefix - window, 0)`） | `vllm_ascend/attention/dsa_v1.py:410, 448-461, 1107, 1108-1125, 2265-2270` |
| SFA 强制 `ori_mask_mode=0` / `ori_win_left=-1`（native window 不生效） | `vllm_ascend/attention/sfa_v1.py:114-119` |
| GQA 的 native SWA → `sparse_mode=4` + `pre_tokens` | `vllm_ascend/attention/attention_v1.py:602-604`；draft 仍传 `block_table` 见 `:459-472` |
| `decode_threshold <= 16` 断言（⇒ `K ≤ 15`） | `vllm_ascend/attention/attention_v1.py:248`、`mla_v1.py:299`、`sfa_v1.py:524`、`dsa_v1.py:654` |
| Flashcomm = SP-MoE 开关；DSA-CP 与其互锁 | `vllm_ascend/ascend_config.py:639-657, 694-698`；`vllm_ascend/utils.py:916-928`；`vllm_ascend/attention/sfa_v1.py:869` |
| DSA-CP 切 token 流，不重排 block table | `vllm_ascend/attention/context_parallel/dsa_cp.py:1133-1138, 1166-1168` |
| PCP draft 恒为 replicated（`prepare_draft_prefill` no-op） | `vllm_ascend/worker/v2/pcp_manager.py:383-392` |
| SFA/DSA 的 `update_graph_params()` 是 no-op | `vllm_ascend/attention/sfa_v1.py:885-896`；`AscendDSAImpl.update_graph_params` |
| GQA legacy `update_graph_params()` 抛 NotImplementedError（要求 UpdatableGraph） | `vllm_ascend/attention/attention_v1.py:572-581` |
| legacy replay 顺序是「先 replay 再 update」 | `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:154-194`；`dflash/aclgraph.py:100-138` |
| dummy block table 是 full 宽度的零表 | `vllm/v1/worker/gpu/block_table.py:177-187` |
| MRV1 单一对齐量（`kernel_block_size` 取第一个 draft layer） | `vllm_ascend/spec_decode/llm_base_proposer.py:406-408, 446-452`；DSpark 复用同一值 `:2604-2605` |

## 附录 B：Codex 方案中应当原样保留的优点

评审的目的不是否定。以下判断我核对后确认正确，且**优于**或**补足**了我的独立设计，应原样保留：

1. **CRITICAL**：DCP local 长度必须用绝对区间前缀差、禁止用 `prefix(window_len)`（§0.3）。**我自己的文档在这一点上是错的，Codex 是对的。**
2. **CRITICAL**：window gather 必须受 per-row `full_valid_num_blocks` 约束，只查 tensor 列宽不足以防 stale block id（§0.3）。
3. **CRITICAL**：CPU upper 必须用 exact 算出的 canonical start 平移，而不是各自独立套公式（§0.3）。
4. **Candidate A vs B 的取舍理由**：把 transform 放在共享 funnel 会让 method timing 隐藏在 scope 里；AR first-pass 与 capture helper 的 scope 覆盖脆弱。这个论证成立，方向正确。
5. **不按 concrete class 判 policy**（MTP 落到 `AscendEagleSpeculator` 也不能启用）——与 `vllm_ascend/worker/v2/spec_decode/__init__.py:58-71` 的事实一致。
6. **Window OFF 的强约束写得具体**（不分配 buffer、不跑 kernel、保持 Eagle metadata 复用、graph key 数量不变）——这正是最容易在实现中悄悄破坏的地方。
7. **「未验证组合 fail fast，绝不静默回退」**——这条门禁纪律应写进最终 contract。
8. **显式拒绝把 DSA 原生 `dspark_swa_indices` 与本 feature 混为一谈**（§Non-goals），方向正确（但组合语义仍需按 M4 补 spec）。
