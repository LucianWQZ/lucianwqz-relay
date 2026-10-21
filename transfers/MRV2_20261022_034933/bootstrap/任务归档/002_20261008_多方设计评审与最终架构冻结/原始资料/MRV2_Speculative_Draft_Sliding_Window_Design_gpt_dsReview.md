# Review：GPT《Stage 8：MRV2 Speculative Draft Sliding Window 公共架构设计》

> **Corrigendum（2026-10-08，事后自纠）** — 本文 **QG-G / §3 G-M5 第 3 点**里我断言"负 `windowed_len` 需要 `K_f ≥ W + B - (L mod B)`，而 `K_f ≤ 15` + `B ≥ 16` ⟹ 正常配置不可达"**是错的**（我把 `L mod B = 0` 的特例外推了）。正确结论见 `MRV2_Speculative_Draft_Sliding_Window_Design_DS_v2.md` 附录 C：
> - 该条件在 `L mod B = B-1` 时退化为 `K_f ≥ W + 1`；反例 `W=0, K=7, B=64, L=250` ⟹ `windowed_len = -6`，**可达**。
> - 所以原设计（GPT 文档）提出的 `W ≥ K_f` 校验方向是对的，只是它给的"`W < K_f` 时可能为负"这一表述不够精确（应写成 `K_f - W ≥ B - (L mod B)`）；我此前对它的批评过重。
> - `W=0` 也**不是**"生效与否"的问题：`start = floor(L/B)*B`，`W=0, L=250, B=64 ⟹ start=192`，窗口收缩到最后一个 block 边界。
> 其余结论（含 G-C1 捕获入口、G-C2 AR 首步无落点、G-M1 per-group 语义、G-M2 funnel CPU 兜底等）不受影响。

> 评审对象：`/Users/wenqingzhang/Desktop/Note/MRV2/Draft/Stage8_MRV2_Draft_Sliding_Window_Architecture/MRV2_Speculative_Draft_Sliding_Window_Design_GPT.md`（1252 行）
> 评审人：Claude（已独立产出设计 `MRV2_Speculative_Draft_Sliding_Window_Design.md`，并已评审过 Codex 方案 `..._codex_dsReview.md`）
> 日期：2026-10-08
> 源码基线：`/Users/wenqingzhang/Desktop/vllm/vllm-ascend`、`/Users/wenqingzhang/Desktop/vllm/vllm`
> 行号：本文所有 `file:line` 都在本机核对过。引用 Ascend 仓库写全路径，引用上游写 `vllm/v1/...`。

## 0. 评审方法与结论摘要

### 0.1 方法

沿用上一份评审的两步法：**先验证它依赖的事实，再看结论是否唯一、是否会被实现成静默错误**。额外增加一步，因为这份文档有独特的证据问题：

**第 0 步：先判定它的"事实"是什么级别的事实。** 本文档在 §"本次设计的证据边界" 里自己把结论标为 `[S]`（来自你提供的 **Codex Stage 1–7 笔记**）、`[U]`（公开文档 / 网页检索）、`[D]`（作者自己的架构判断）。我核对了它的引用形式：**所有 `<FileCite ref="turn0file0" line_range_start=... line_range_end=.../>` 指向的都是 `Sliding window源码_codex.md` 的行号，没有一处指向仓库源码**；`<Cite refs={['turn0searchN']}/>` 指向公开网页。也就是说，这份设计**与真实代码隔了一层笔记**。

这一点重要，因为笔记本身会有错、会漏。我实际核过：**本文档在若干处继承了笔记与自身推导的偏差**（见 §1.7、§1.9、§1.17、§3 G-M4、G-M5），而它**漏掉的恰是决定架构的几个源码事实**（见 §2 G-C1、G-C2）。所以它的自我定位（"Stage 8 可以形成架构决策，但还不能声称已完成代码级验收"）是**诚实的**；但它随后又声称"可以冻结总体架构方向 Candidate B"，这两者不能同时成立（见 §2 G-C1）。

### 0.2 总体评价

| 维度 | 评价 |
| --- | --- |
| 工程判断与结构 | **好**。分层（policy / manager / backend adapter）、不变式表、graph-aware buffer 状态机、测试分层都很清晰 |
| 语义直觉 | **好且有一处特别锋利**（见 §0.3 第 1 条，它指出的是另外两份文档都没说清的语义陷阱） |
| 与真实代码的结合度 | **差**。没有任何仓库函数/入口被点名；关键决策（表形状、注入点、capture 入口）因此无从验证 |
| 可实现性 | **当前不可实现**。没有 plumbing 路径，实施者无法从这份文档开始写第一行 |

一句话：**这是一份"架构散文"，不是一份低层设计。** 它的方向（Candidate B）正确，但它对 A/B 的取舍理由（"A 的作用域容易泄漏"）不依赖源码，而它自己的 B 之所以能规避 A 的失败模式，**完全依赖源码层的事实**——而它没有那些事实。文中最后自己也承认了这一点，并把源码定位工作外包给后续评审。

### 0.3 必须承认：它在四处比另外两份更清晰（有一处直接指出我的缺陷）

| 点 | GPT 的判断 | 为什么它对 |
| --- | --- | --- |
| **1. AR 的 horizon 必须冻结，不能每步重算** | §8.4：「不能简单地将 Eagle3 的 MRV1 `K_f=K` 改为每一步 `K_f=0`。前者是面向整个 draft horizon 的窗口，后者可能产生**每一步移动的窗口**，属于语义改变」；并给出正解「proposal 开始时冻结 horizon；per-step 使用当前 exact end materialize read length」 | MRV1 在 `_propose` **只 apply 一次**（`llm_base_proposer.py:1119-1127`），`start` 由首步 `seq_lens + K` 决定一次，之后**只把长度递增**（`:2073-2077` 的 `+1`、`:2134-2136`），裁剪过的 `self._block_table_clone` 全程不变 → **起点冻结、可见长度从 `W-K` 长到约 `W`**。若每步用当前 exact end 重算 `K_f=K`，则 `start_s=align(L_s+K-W)` 随 `L_s` 右移 → **窗口每步向前滑动、可见长度恒为 `W-K`**，语义不同，且每步表 origin 变化（graph 参数成本更高）。**我的设计文档正好犯了这个错**（我写的"AR 每个 decode step 各自 apply，`future_offset=K`"会导致滑动窗口），已按此修正并新增原则 P13。Codex 用「canonical start / proposal anchor」得到了同样的结论，但没有说明失败模式。 |
| **2. 验证 graph binding 不能只看 `data_ptr()`** | §8.6：「不能只关注 `Tensor.data_ptr()`。还要证明其 `shape / stride / row layout / valid length / operator binding` 与对应 Graph Descriptor 一致」 | 这比 Codex 的「`data_ptr()` 不变」更完整。funnel 会做 `x[:num_reqs_padded]`（`vllm/v1/worker/gpu/spec_decode/speculator.py:322-324`）——非零起点切片保持 `data_ptr` 但改变 `storage_offset`；改变列容量则改变 `shape/stride`。只断言 `data_ptr` 会漏掉 F15 类错误。 |
| **3. 绝对坐标与窗口局部坐标是两个坐标系** | §3.3 把它提升为**独立不变式**，并要求 Read View 同时携带 `absolute_end / visible_start_abs / visible_length` | 这是对的方向，而且它点出了机制：对 GQA 局部长度+窗口表够用，但对 DSA/SFA 的索引生成会读 absolute positions 或算 `start_pos`，「不能把 `seq_lens=300` 换成 `172` 却让依赖长度算绝对位置的逻辑不变」。这与我从另一条路径得到的 T2（索引型可见性）是同一个问题。 |
| **4. 明确不采用 contextvar，且给出理由** | §9.3：四条理由（Python task 上下文 ≠ 设备执行生命周期；replay 可能晚于 context 结束；async callback / graph update 在不同执行边界消费；隐式读取难追踪 owner/generation） | 比 Codex 更彻底（Codex 保留了 `ContextVar` 作为"运输层"的活口，因而在失败模式上与它否决的 Candidate A 同源）。这条判断我完全同意。 |

此外 §14.2 的「不应简单地执行 `local_seq_len = global_window_seq_len / CP_size`」与「Global Visible Interval → CP Layout Transform → Local Visible State」也正确——与源码事实一致（`get_dcp_local_seq_lens` 对 L 非线性，见 §1.18）。

---

## 1. 25 项攻击面逐条评估

格式：**风险等级 / 对应设计章节 / 为什么会发生 / 需要什么源码证据 / 建议修改**。

### 1. Target 是否可能被误 Window

- **风险：高**（经由 §2 G-C2 的机制）
- **章节**：§3.1、§3.3（"Target metadata 不得被 Draft Window 修改"）、§10.2 Activation Point、§12.2 流程图、R1
- **为什么可能发生**：文档的不变式写得对，但**它的激活模型在 MRV2 上有一个不存在的落点**。§10.1 把 Eagle3 的激活点写成 "AR first pass / per-step 的 Last Full-State Point"，§10.2 写成 "Full slot mapping → AR Window activation → Draft metadata"。**MRV2 的 AR first pass 根本不构建 draft metadata**：它直接把自己收到的 Target `attn_metadata` 与 Target `slot_mappings` 传给 `_prefill()`（上游 `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:306-322`，注释明确写 "we can also reuse the attention metadata (e.g., query_start_loc, seq_lens) of the target model"）。因此实现者去找这个"激活点"时会发现没有 draft-scope metadata 可改，**最自然的做法就是就地改它拿到的那份 Target metadata**——而这正是文档 R1 声称"架构必须天然禁止"的事。文档对此完全无感：全文没有提到 first-pass 复用（对照：Codex 把这条列为 R1 并给出"Window ON 显式重建"的决策）。
- **需要的源码证据**：① `autoregressive/speculator.py:306-322` 的复用路径；② `prepare_prefill_inputs` 是否会按 `num_rejected` 裁 query（同文件 `:719-721`）；③ 是否存在能承载 draft-scope metadata 的调用点。
- **建议修改**：在 §10.2 明确写出：**AR first pass 在 MRV2 没有 draft metadata 构建点**；Window ON 时必须新造 draft-scope metadata（不得浅改 Target 对象），且重建结果除 read view 外必须与 Target 等价（见 §3 M1）。这条应升级为 Critical 级的 spec 条目。

### 2. positions 是否可能被改变

- **风险：低**
- **章节**：§3.3（"Absolute positions 不因 Window 转换为局部位置"）、§8.3（`positions` 和 `slot_mapping` **不应出现在这个对象的可修改字段里**）
- **为什么可能发生**：基本不会，而且 §8.3 的类型边界（view 不含这两个字段）比 Codex 的写法更干净。
- **需要的源码证据**：一条 identity/值断言（window 物化前后 `positions` 逐位相同）。
- **建议修改**：把这条断言写进 §15.2；另外注意它自己 §3.3 提出的"两个坐标系"在实现上有一个陷阱——**只把 `seq_lens` 换成局部值、却让 backend 仍用绝对 positions 去算 `start_pos`**，这正是 §1.17 的问题。

### 3. slot_mapping 是否有机会读到 windowed block table

- **风险：低**
- **章节**：§3.3、§8.6（"不参与 Full KV allocation 或 physical slot computation"）、§12.3（"Slot mapping 仍按 Full BlockTable 计算"）
- **为什么可能发生**：结构上被排除。公共 slot kernel 读 authoritative 指针（`vllm/v1/worker/gpu/block_table.py:93-97,190-221`；Ascend override `vllm_ascend/worker/v2/block_table.py:82-114`），DFlash/DSpark 的 query slot 也从 full gathered table 生成且发生在窗口物化之前（`vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:375-409`）。
- **需要的源码证据**：workspace 自检断言「窗口 buffer 与 `input_block_tables[*]`/`slot_mappings` 的 storage 无重叠」；以及「开/关 window 的 slot mapping 逐位相同」。
- **建议修改**：这两条断言文档里没有（§15.2 只写了 Full 状态不变），补上。

### 4. full block table 是否可能被覆盖/污染

- **风险：低中**
- **章节**：§3.3、§8.6（per-group dedicated persistent buffer）、R1
- **为什么可能发生**：设计上分了独立 persistent buffer ✓，所以存储层是隔离的。但 R1 写"架构必须天然禁止"这个论断**缺论证**：真正决定"是否天然禁止"的是**窗口 view 会不会被误当 full source 或被写回共享表**，而这取决于注入点与刷新纪律——文档两者都没写（§2 G-C1）。换句话说：结论方向对，但"天然"二字无据。
- **需要的源码证据**：`refresh` 前置断言 source 的 `data_ptr()` == `block_table.input_block_tables[g].data_ptr()`；以及"不写回 `input_block_tables`"的负向测试。
- **建议修改**：把 R1 从"架构天然禁止"降级为"架构提供隔离 + 必须由以下两条断言保证"，并补断言。

### 5. seq_lens 是否可能被重复 Window

- **风险：中**
- **章节**：§8.6（"始终从 Full Read Source refresh"）、§15.2（"`Window(Window(Full))` 不应该成为实际运行的数据流"）、§11.2 状态机 `Refresh(N) ≺ Consume(N) ≺ Refresh(N+1)`
- **为什么可能发生**：它的原则写得对，也有 `generation` 概念（§11.6 `ExecutionBinding`）。风险点在于**它没有枚举"谁在一步里会调用几次 refresh"**。MRV2 已知有 live build 与 graph-manager rebuild 两次（`vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:86-98`、`autoregressive/aclgraph.py:132-152`），且 (§2 G-C1) 还有第三次 capture 期。若 refresh 语义是"从 full source 覆盖写"，两次调用幂等 ✓；若实现成"按 step 增量填充"，则第二次会重复。文档没有指定"每次 refresh 都整行重写"这条纪律（它在 §8.6 只写了"始终从 Full Read Source refresh"，方向对但可被实现成增量）。
- **需要的源码证据**：一次 proposal 内 refresh 的调用次数与位置；`generation` 如何随 proposal 前进。
- **建议修改**：明确写"**每次 refresh 都把该 group 的窗口表整行从 full source 重写**（不做增量补列）"，并给 `generation` 一个明确 key（`proposal_id` + `anchor/horizon` + `request_order_version` + `step`）。

### 6. Window OFF 是否真的零回归

- **风险：中高**（见 §3 G-M5）
- **章节**：§12.1（"Window OFF 时不应创建不必要的大型 persistent device buffers"）、§13.2、§9.1 初始化流程
- **为什么可能发生**：三个具体问题：
  1. **§9.1 的初始化流程没有 OFF 短路**：它列的是 `Discover Active KV Groups → Resolve per-group kernel geometry → Initialize DraftWindowManager → Allocate Persistent Window Buffers → Capture Graphs`。窗口 OFF 时必须在这条链的最前面短路；文档只在 §12.1 一句带过。而这正是"零回归"最容易被破坏的地方（多出来的 geometry 解析/分配）。
  2. **它承诺不了 OFF 的必要条件**：因为不知道 AR first pass 复用 Target metadata（§1.1），所以无法写出 Codex 那条「Window OFF 保留 Eagle first-pass 的 Target metadata 复用零回归路径」。
  3. **config 收紧未标注**（见 G-M5）。
- **需要的源码证据**：`AscendConfig.draft_window_size` 为 `None` 时各初始化路径是否完全短路（对照 `llm_base_proposer.py:415` 的 MRV1 读取点）。
- **建议修改**：把"OFF 短路"写成 §9.1 的第一条分支，并要求一条「OFF 时不新增任何 device 分配 / 不进入任何新分支」的测试（用 `torch.npu.memory_allocated` 或分配计数断言）。

### 7. per-group block size 是否处理正确

- **风险：高（正确实现了 per-group 对齐，但因此改变了 feature 语义）**
- **章节**：§3.2（`B_g`、`S_g`）、§12.3 数值例、§8.6、§10.2
- **为什么可能发生**：它的 per-group 数学**本身算对了**。我按它的例子复算：`W=128, L=300, K_f=0`，group0 `B=64`：`ideal=172`、`aligned=128`、`start_block_index=2`、`windowed=172`、`needed=ceil(172/64)=3` ✓；group1 `B=32`：`aligned=160`、`start_block_index=5`、`windowed=140`、`needed=5` ✓。全部正确。
  问题在于它把这个结果当作正面结论推广：**"不同 group 的 aligned start 和 windowed length 也可能不同"→ 每组一个 `WindowState[group_id]`**。而 **MRV1 的契约是一个窗口、一个对齐量**：`SlidingWindowAdapter(self.draft_window_size, self.kernel_block_size, ...)` 只取**第一个 draft attention layer** 的 `kernel_block_size`（`vllm_ascend/spec_decode/llm_base_proposer.py:406-408, 446-452`），DSpark 的 per-group 循环复用的也是同一个 `self.block_size`（`:2604-2605`）。在 MRV1 下，两个 group 共享**同一个绝对起点** `start`（因为它是 64 的倍数 ⇒ 也是 32 的倍数），两个 group 的可见区间相同，只是列数不同。GPT 的设计让 group1 的区间变成 `[160, 300)` 而 group0 是 `[128, 300)` → **同一个 draft 模型的不同 attention layer 看到不同长度的历史**（140 vs 172）——这是 acceptance 行为的改变，且与它自己的 §3.3 不变式（"Window lengths 与 Window table 表达同一个有效读取区间"）在跨 group 维度上失去意义。
- **需要的源码证据**：① 目标 DSpark/Eagle3 的 draft 实际有几个 attention group、各自 `kernel_block_size`；② MRV1 在 hybrid multi-group + window 下有无测试（我核实：**没有**——MTP 是唯一明确的多 group 用例，而 MTP 被 window 忽略；所以这是 MRV1 的未验证区域）。
- **建议修改**：把语义收敛为**一个 proposal 一个绝对窗口**，对齐到 `lcm{kernel_block_size_g}`（或最细粒度）以保证每组列索引整除；per-group 只体现在 `start_col_g` 与 `needed_g`。这样既保留 MRV1 的「一个窗口」语义，又满足 per-group 布局正确性，代价是起点可能比最优早至多 `lcm-1` 个 token（多看历史，无害）。若产品确实要 per-group 独立窗口，必须写成显式 contract 变更并补 MRV1 对照实验。

### 8. padding rows

- **风险：中高**（见 §3 G-M3）
- **章节**：§3.3（"Padding | 无效行/列不得暴露旧请求的物理块"）、§8.6（"对 active row 的无效尾列进行显式 mask/清理；对 padded row 采用 backend 认可的 inert 表达"）、§15.4（"Batch 从大变小"、"Long → Short requests"）
- **为什么可能发生**：它的**目标**表述正确，但**漏了源侧的一半**。窗口裁剪会从任意 `start_col` 起读，而 `BlockTables` 的 gather kernel 对 active row **只覆盖 `[0, num_blocks)`**、不清 tail（`vllm/v1/worker/gpu/block_table.py` 的 gather，配合 `:177-187` 的 dummy 只清 `[:num_reqs]`）。因此"看起来有值的列"可能本身就是**上一步/上一个更长请求留下的 stale block id**。只做"列 ≥ needed 清零"（这是文档的表述）不足以防住：真正要检查的是 `src_col < 本轮该 row 的有效块数`。Codex 把这条写成了 `full_valid_num_blocks` 硬约束（Codex §MRV2 Constraints 1 / Invariant 12 / R16）；我自己的设计也漏了，GPT 同样漏了。
- **需要的源码证据**：gather 的实际写入范围；`num_blocks`（authoritative CPU/device 边界）如何按本轮 request order 对齐；各 backend 的 padding 约定（例：GQA/FIA 把 `seq_lens_list`/`seq_lens` 用 **1** 补齐并追加零表行，`vllm_ascend/attention/attention_v1.py:361-365`）。
- **建议修改**：把窗口表的源侧约束写成"三个同时成立"：`src_col < full_table_width`、`src_col < full_valid_num_blocks[row]`、`dst_col < needed[row]`；并补"padding row 的 block id 与任何 active row 的 block id 不相交"的断言。

### 9. CPU upper bound 与 device exact length 是否一致

- **风险：高**（见 §3 G-M2）
- **章节**：§8.5、§3.3、R5、§16.2 Q9
- **为什么可能发生**：§8.5 的原则是对的（"不建议将 Target CPU Mirror 当成 Window exact 的权威来源"；"Upper bound 不能为了方便直接冒充 exact length"），它甚至列了一张"inplace / 临时 tensor / view / dedicated persistent buffer"的取舍表，结论（dedicated persistent buffer）也对。
  但它缺了**机制层的那一步**：Ascend 最终 funnel 在 `seq_lens_np is None` 时会**自己造一个 full 量级的 CPU 长度**——`vllm_ascend/worker/v2/attn_utils.py:256-258`：`seq_lens_np = np.full(num_reqs, max_seq_len, dtype=np.int32)`，而 Draft 路径的 `max_seq_len` 是 `self.draft_max_seq_len`（上游 `vllm/v1/worker/gpu/spec_decode/speculator.py:361`）；紧接着 `:259-260` 在 `seq_lens_cpu_upper_bound is None` 时令其等于 `seq_lens_cpu`。于是：**如果窗口 view 只提供 device 长度与 upper，而没提供 CPU exact（文档正是把 CPU exact 当成"需要时再派生"），funnel 会给出 full 长度的 CPU 向量，而表已被窗口化** → 最高危失败模式（kernel 去读 `[needed, row_width)` 列，读到 block id 0 = cache 第 0 块）。这条路径可达，因为 MLA 是 CPU 优先（`vllm_ascend/attention/utils.py:573-576`；`attention/mla_v1.py:504-505`），且 `_select_seq_lens` 也优先 CPU（`:573-576`）。
  另外 R5 把风险描述成"Optimistic CPU upper 被当成 exact"，方向对但**指错了对象**：真正的机制是 funnel **凭空合成**一个 full 长度，而不是把 upper 当 exact。
- **需要的源码证据**：GQA(`_select_seq_lens`)/MLA/SFA/DSA 各自最终取哪个 length 字段；`_seq_lens_cpu` 在 MRV2 是否恒为 `None`（若有生产者，它优先级最高，`attention/utils.py:573-574`）。
- **建议修改**：把"**窗口 view 存在时必须同时覆盖 `seq_lens_np` 与 `seq_lens_cpu_upper_bound`，否则 fail fast**"写成硬不变量；并在 §8.5 增补"funnel 级兜底"这一节，明确 CPU 向量的存储 owner 与它如何避免 `from_numpy` 引入的别名（AR 会事后 `metadata.seq_lens_cpu.copy_(...)`，`vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:776`）。

### 10. graph capture 地址稳定

- **风险：中**（外加 §2 G-C1 的形状问题）
- **章节**：§8.6、§11.2 状态机、§11.4、R3
- **为什么可能发生**：原则层面它写得比 Codex 更好（"不能只关注 `data_ptr()`…",见 §0.3 第 2 条；以及 §11.2 的 `Refresh(N) ≺ Consume(N) ≺ Refresh(N+1)`）。
  真正的问题不在地址纪律，而在**它从未定义窗口表的形状/容量**：§8.6 只说"per-KV-group dedicated persistent buffer"和"对 active row 的无效尾列进行显式 mask/清理"（暗示存在一个固定的列容量），但**没有任何容量公式**（对照 Codex 给了 `C_g=ceil(W/b)+1` 与 17 KiB 的算例；MRV1 是 `window_blocks+1`，`spec_decode/utils.py:111-112`）。因此"capture 与 replay 用兼容 shape"这句要求**无法被实施或验证**——见 §2 G-C1。
- **需要的源码证据**：各 group 的 row width / kernel block size；capture descriptor 集合；backend 是否把 `block_table` 的 shape 固化进 graph 参数。
- **建议修改**：补一条容量公式（并显式选择"窄表"或"与 full 同宽"），见 §2 G-C1。

### 11. capture / replay metadata 是否一致

- **风险：致命**（见 §2 G-C1）
- **章节**：§11.4、§8.6、§9.1、§16.2 Q5、R3
- **为什么可能发生**：文档只承认"live build 与 graph manager rebuild"这条二元链路（§16.2 Q5 的措辞是"DFlash/DSpark live build 与 graph-manager rebuild 中，哪一处实际更新 captured storage？"）。**capture 期自身的 metadata 构建不在它的视野里**，而它恰恰是决定 captured shape 的那一次。见 §2 G-C1 的完整证据链。
- **需要的源码证据**：draft 侧 metadata 构建入口的完整清单（已知 ≥3 条）。
- **建议修改**：见 §2 G-C1。

### 12. eager / PIECEWISE / FULL 差异

- **风险：中**
- **章节**：§11.3（"推荐统一 Data Contract，而不是强迫三种模式采用完全相同的 Python 调用链"）、§11.4、§15.4
- **为什么可能发生**：它的立场（统一数据契约、不统一调用链）是合理的，避免了我与 Codex 都强调过的"必须完全同构"的过度约束。风险在两处：
  1. **PIECEWISE 下 capture 期就有真实 attention 执行**：上游 `cudagraph_utils.prepare_inputs_to_capture()` 的注释（约 `:793-818`）说明 PIECEWISE 也会构建 metadata（`for_capture=False`），而作为断点的标准 attention 在 capture 时 eager 执行、attention-like op（sconv / DSV4 compressor）会被捕获并真实执行。因此 PIECEWISE 的"窗口 view 有效性"必须在 **capture 期**成立，不只是 replay。文档 §11.3 只说"遵守被捕获区域的输入约束"，太笼统。
  2. **GQA 的 parity 是 UpdatableGraph 给的，不是设计给的**：GQA/FIA 的 legacy `update_graph_params()` 直接抛 `NotImplementedError`（`vllm_ascend/attention/attention_v1.py:572-581`），只有 `use_updatable_graph()`（仅对 `AscendAttentionBackend` 为真，`vllm_ascend/utils.py:1769-1775`）才可用。所以"三种 mode 语义相同"在 backend 维度上并非设计保证，文档未把这条 capability 显式纳入。
- **建议修改**：§11.3 增加"capture 期也必须有有效 view"的要求；capability 表增加 `supports_updatable_graph`。

### 13. async 生命周期

- **风险：中**
- **章节**：§11.6、§11.2、§12.2（Retire 的说明）、§15.6、R8
- **为什么可能发生**：§11.6 的 `Persistent address stability ≠ Async lifetime safety` 与"不要直接假设两份 buffer 就一定够"都是好判断（与 Codex 同级）。两处需要收紧：
  1. **release 时点**：legacy 更新路径是**先 replay、后 update**（`vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:154-194`；`dflash/aclgraph.py:100-138`），所以"replay 已提交"不足以作为 release 条件，必须绑到"最后一个消费者（含 graph 参数更新）完成"。文档说 `Retire` "可以是记录 event、放入待回收队列，或依赖现有 stream ordering"——偏软，且没有指出 legacy 路径的 update 在 replay 之后。
  2. **单 in-flight 假设**：§14.3 说"Week3 即使使用单 in-flight generation，也应预留 `generation_id / completion_event / pool_slot / graph_binding_id`" ✓ 这是对的姿态；但仓库里已有 `UvaBufferPool` 默认 ≥2 round-robin slot 并要求 reader retire 才复用（`vllm/v1/worker/gpu/buffer_utils.py`），说明重叠是被预期的。文档的"待验证"（Q8）正确，但应把该证据写进风险描述，而不是把单 in-flight 当默认。
- **需要的源码证据**：`update_stream` 与 current stream 的 happens-before；`UpdatableGraph` 分支 `graph.update(update_stream, tasks)` 之后是否有同步点。
- **建议修改**：把 release 条件写清为"最后 reader + graph-param update 均完成"；把 `UvaBufferPool` 的多 slot 作为"重叠是既定事实"的证据。

### 14. contextvar / context object 是否跨请求、跨线程、跨 async execution 泄漏

- **风险：低（这条是它的强项）**
- **章节**：§9.3、§11.6
- **为什么可能发生**：它**明确不采用** contextvar，改用显式 `DraftWindowExecutionContext`，并给出四条理由；同时保留既有的 `set_ascend_forward_context()` 作为"交付最终 metadata"的机制。这个区分（**显式 context 传递 Window 执行状态 / 用已有 Forward Context 交付最终 attention metadata**）是清晰且正确的。
  残余风险：它没有说明这个显式 context 必须**穿透到 capture 入口**（§2 G-C1）。如果实现时发现 capture 路径拿不到显式参数，很容易就退回隐式方案——而它恰好否决了隐式方案。所以它需要一个"若必须隐式则如何"的明确立场（哪怕是"因此必须改上游签名"）。
- **需要的源码证据**：capture 的执行入口能否携带显式参数。
- **建议修改**：补一句"若某条入口无法携带显式参数（例如 capture），则必须修改该入口的签名，**不得**退回隐式 context"，与 §9.3 保持一致。

### 15. Eagle3 / DFlash / DSpark 的 timing 差异

- **风险：中高**
- **章节**：§10.1、§10.2、§8.4、§12.2、§11.5
- **为什么可能发生**：**它的 horizon 设计是三者里最清晰的**（§0.3 第 1 条，含正解"冻结 horizon + per-step 用当前 exact end materialize length"）；§11.5 对 "Eagle3 FULL merged multi-step 每步 length 不同" 的判断与正解（per-step capture-stable state 基线）也对。
  两处缺口：
  1. **AR first pass 没有 draft metadata 构建点**（§1.1 / §2 G-C2）——这是 timing 矩阵里最实质的一条，文档反而把它当成一个正常激活点。
  2. **重建后的 first-pass 必须与 Target 的 query layout 逐位相同**（见 §3 M1）。文档 §8.4 只说 "per-step 使用当前 exact end materialize read length"，没有约束 first pass 的 query layout；而 MRV2 首步的 layout 是 Target 的、包含 rejected 尾部 padding（上游 `autoregressive/speculator.py:233-238`）。若重算成 draft 的裁剪后 layout，第一个 draft token 会静默算错。
- **建议修改**：§10.2 增加 first pass 的专门条目（新造 metadata + layout 不变式）；§15.3 增加"重建 first-pass metadata 与 Target metadata 在 `query_start_loc(_cpu)/positions/num_tokens/is_prefilling` 上逐位一致"的差分测试。

### 16. unsupported methods 是否被错误启用

- **风险：低**
- **章节**：§10.1、§13.2、R9
- **为什么可能发生**：处理得好，且它的措辞比 Codex 更谨慎：把 `Eagle` 与 `draft_model` 标为 "Legacy implicit，需审计 / 不能预设"，而不是断言。这与事实一致（MRV1 的构造条件只看 `method != "mtp"`，`llm_base_proposer.py:437`，所以 `eagle`/`draft_model` 事实启用但文档未承诺；MRV2 factory 则直接 `NotImplementedError`，`worker/v2/spec_decode/__init__.py:72`）。
  唯一需要精确化的地方：§10.1 表格里 token-only 方法写 "N/A 或现有 unsupported"，把 MRV1 的"静默未读取"与 MRV2 的"factory 报错"合在一格，容易让实现者以为应该做 silent no-op。
- **建议修改**：拆成两列（MRV1 实际行为 / MRV2 实际行为）。

### 17. native model SWA 与 `draft_window_size` 是否双重计算错误

- **风险：高**（见 §3 G-M4）
- **章节**：§8.7、§3.3、R4、Q7
- **为什么可能发生**：它把这个问题单独立节（§8.7），方向正确，且有两处很准：
  - "**不能在已经重排的 Window Table 上直接复用按 Full Absolute 坐标生成的 sparse indices**" ✓ —— 这正是 rebase 问题，与我从源码得到的 T2 一致；
  - 引用官方文档的"`draft_window_size` 不小于 native window"指导，并强调"这项建议属于性能与模型行为指导，**不应代替数据面正确性验证**" ✓ 这句很专业。
  但它的核心断言**表述有误**：「**不能直接对两个窗口大小取 `min()`**」。就可见集合本身而言，两者都是**同一序列上的后缀区间**：窗口 = `[S, L+K)`，native SWA = `[max(prefix-native,0), end)`，交集恰好等于**从末端量取的更紧者**，即 `min` 是正确的组合（差别只在坐标基准与索引重建）。对 GQA 更是如此：FIA 的 band（`sparse_mode=4 / pre_tokens=sliding_window / next_tokens=0`，`vllm_ascend/attention/attention_v1.py:602-604`）在窗口化坐标系上计算 basis，两者自然取交集。把"不能 min"作为结论，可能把实现引向一个不必要的 `Absolute Coordinate Adapter`，并且会掩盖真正的实现点（把 `start_pos` 夹紧）。
  更要紧的是**三态未枚举**——三种 backend 的行为互不相同，而文档把它们当成一种"native SWA"：

  | backend | native SWA 在源码里如何生效 | 与 `draft_window_size` 的组合 |
  | --- | --- | --- |
  | GQA/FIA | band：`sparse_mode=4`、`pre_tokens`（`attention_v1.py:602-604`）；`is_draft_model=True` 时仍传 `block_table`（`:459-472`） | **真交集**，`min` 语义成立 |
  | DSA（non-causal DSpark） | **根本不读 block table**：可见性来自显式索引 `ori_sparse_indices`（`attention/dsa_v1.py:448-461, 1108-1125, 2265-2270`），由 `hf_config.sliding_window` 派生 `start_pos` | 二者**必然汇聚到同一段派生代码**；窗口只能通过夹紧 `start_pos` 生效。注意 `dsa_v1.py:1107` 直接 `hf_config.sliding_window - 1`，**无 None 检查** ⇒ 该路径必然存在 native window |
  | SFA（sparse MLA） | **native window 不生效**：强制 `ori_mask_mode=0`、`ori_win_left=ori_win_right=-1`，注释"Only ori_mask_mode 4 may carry a bounded window on this product line"（`vllm_ascend/attention/sfa_v1.py:114-119`）；可见性来自 top-k 索引（`:198-219`） | 只有一个来源（窗口 + top-k 交集）；不能假定 native SWA 在做组合 |

- **需要的源码证据**：目标 draft 实际激活的 backend；DSpark 的 `cad.causal`（MRV1 从 `model.get_draft_attn_causal()[0]` 取，`vllm_ascend/spec_decode/dspark_proposer.py:343-347`），它决定走"表+长度"还是"显式索引"。
- **建议修改**：把 §8.7 从"风险 + 原则"升级为**spec**：① 逐 backend 写明可见性表达方式与窗口的落地点；② 把"不能取 min"改为"**区间层面取交集（=末端更紧者）；但不能在 rebase 后的表上复用绝对坐标索引**"；③ DSA 上明确实现为夹紧 `start_pos`；④ 增补"只裁表对 DSA 非因果路径完全无效"这条陷阱（否则实现者会做出一个静默无效的 feature）。

### 18. DCP / PCP / SP / CP local length

- **风险：低（结论正确）**
- **章节**：§14.2、§3.3、Q3、R10
- **为什么可能发生**：它的结论对，而且理由说得比 Codex 更早一步："不应简单地执行 `local_seq_len = global_window_seq_len / CP_size`"，并要求"`Global Visible Interval → CP Layout Transform → Local Visible State`"。我核实了源码支持这个结论：`get_dcp_local_seq_lens`（`vllm/v1/attention/backends/utils.py:1088-1133`）对 L **非线性**——`local(L) = floor(floor(L/i)/d)*i + clip(L - floor(floor(L/i)/d)*d*i - r*i, 0, i)`；反例：`i=1,d=2,r=1` 时 `local(4)-local(1)=2`，而 `local(3)=1`。所以必须用**区间前缀差** `local(end)-local(start)`。
  它 §14.2 里"需要证明 logical-to-physical translation 没有因为 Window Rebase 和 CP Sharding 而出现两次偏移"也是很锐的一句 ✓。
  残余：Ascend funnel 还会从 `seq_lens_cpu` 派生 CPU local（`vllm_ascend/worker/v2/attn_utils.py:266-273`），因此若窗口只给 upper 不给 exact，CPU local 会继承 upper 精度（MLA DCP decode 直接消费它，`attention/context_parallel/mla_cp.py:202-219`）。文档没有把这条派生链写进"必须同 origin"的清单。
- **建议修改**：把 funnel 的 CPU-local 派生链纳入 §3.3 的不变式；若窗口无法提供 CPU exact，则 DCP + MLA 组合下 fail fast。

### 19. Flashcomm interaction

- **风险：低**
- **章节**：§14.1、§14.4
- **为什么可能发生**：它只说"扩展在 Backend Metadata Adapter / Execution Adapter 层""Flashcomm 不应该重新实现 Window 数学，也不应该成为 Window Buffer 的物理 Owner""需要单独验证 stream/event ordering"。**这些都没有错**，比 Codex 的 `FlashcommWindowLayoutProvider`（暗示 Flashcomm 会影响布局）更保守。
  事实补充（供文档收口）：Flashcomm 在 Ascend 上就是 **SP-MoE 开关**（`vllm_ascend/ascend_config.py:639-657`），`enable_sp()` 返回 `use_sequence_parallel_moe`（`utils.py:916-928`），并在 SFA 里只被赋值、之后没有改 block table 的分支（`attention/sfa_v1.py:869`）⇒ **布局无关**。真正相关的是它带出的 DSA-CP（互锁见 `ascend_config.py:694-698`），而 DSA-CP 切的是 token 流（`attention/context_parallel/dsa_cp.py:1133-1138`），也不重排 block table。
- **建议修改**：§14.1 明确写"Flashcomm 对本 feature 是布局无关的；相关布局风险来自 DSA-CP"，把扩展点从"Flashcomm 适配器"改名为"CP/DSA-CP 适配器"，避免误导实现者去构造一个不存在布局耦合的 provider。

### 20. model-specific assumptions

- **风险：中低**
- **章节**：§13.3、R10、Q2/Q3
- **为什么可能发生**：§13.3"不要引入 model name hardcode"是对的，并且它给的方向（`AttentionBackendCapability + ModelAttentionSpec + MethodPolicy`）比 Codex 的"semantic capability"更具体一点 ✓。它还正确引用了 Stage 5 关于 GLM-specific length 选择的发现，并要求"针对真实差异做兼容测试，但不把更多模型名分支写进公共 Window Runtime" ✓。
  漏掉的四个具体假设（与我在 Codex 评审里列的一致）：
  1. MRV2 speculator 同时有 `self.vllm_config`（Target）与 `self.draft_vllm_config`；DeepSeek-V4 advisory 属于 **Target**（MRV1 读的是 `self.vllm_config.model_config.hf_config.model_type`，`llm_base_proposer.py:420-422`），用错字段会判反。
  2. `use_updatable_graph()` 只对 `AscendAttentionBackend` 为真（`vllm_ascend/utils.py:1769-1775`）——被设计隐含依赖，应显式列入 capability。
  3. DSA 路径假设 `hf_config.sliding_window` 非 None（`attention/dsa_v1.py:410, 1107`）。
  4. "每个 group 窗口化"还是"只对 draft attention 的 group 窗口化"——后者才对（`self.draft_kv_cache_group_ids`，`worker/v2/spec_decode/dflash/speculator.py:94-99`）。
- **建议修改**：把这四条写进 §13.3 与 capability 字段。

### 21. hidden performance regressions

- **风险：中**
- **章节**：§1 目标 P2、§15.5、§11.5
- **为什么可能发生**：它的原则（"禁止高频无意义分配、CPU/NPU 同步和重复计算"）与性能对照组设计 ✓，但**没有任何机制级分析**：
  1. **`max_seq_len` 是否窗口化未讨论**。capture 用 `max_model_len`（`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:64`；Ascend `model_states/default.py` 的 `max_seq_len=self.max_model_len`），replay 用 `self.draft_max_seq_len`（上游 `spec_decode/speculator.py:361`）。这个值驱动 workspace/tiling，若不窗口化则 kernel 侧工作量不降 → **"开了窗口但不加速"**会被误判为 kernel 问题。必须明确它是容量上界、不窗口化。
  2. **`tolist()`/CPU list 频次**：AR 现在每 step 构造 `seq_lens_list = next_seq_lens_cpu.tolist()`（`vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:756`）；窗口不应引入新的 `.numpy()`/pinned 拷贝/D2H。
  3. §11.5 说"不是说必须无条件分配 K 份所有 Tensor" ✓，但没有量化 per-step buffer 在多个 capture descriptor 下的重复分配成本（Codex 至少把它列为 R15）。
- **建议修改**：§15.5 增加"窗口开启后 device kernel 侧 KV 读长度确实下降"的可量化断言；明确 `max_seq_len` 不窗口化。

### 22. persistent buffer memory overhead

- **风险：中**
- **章节**：§8.6、§11.5、§12.1
- **为什么可能发生**：它只给了定性约束（"一组一份，必要时一组多个 graph-generation slot"；"Window OFF 时不应创建不必要的大型 persistent device buffers"），**没有容量公式、没有内存量级**。Codex 至少给了 `C_g = ceil(W/b)+1` 与 `[256,17] int32 ≈ 17 KiB` 的算例。
  这不是纯"文档不够细"：**容量公式恰恰是 capture/replay 形状一致性的输入**（见 G-C1）。没有它，"shape 与 graph descriptor 一致"这条要求无法落地。
- **建议修改**：补容量公式与两种选择（窄表 / 与 full 同宽）各自的内存量级与形状后果。

### 23. multi-request / dynamic batch

- **风险：低**
- **章节**：§3.2（`L` 是"输入 Window Transform 时的 exact seq_lens"，隐含 per-row）、§12.3（单请求示例）、§15.4
- **为什么可能发生**：基本覆盖（"Batch 从大变小"、"Long → Short requests"、多 descriptor 都在 §15.4）。但 §12.3 的数值例只用**单请求**，而 `absolute_end`、`start`、`needed` 都是 per-row 张量；文档没有指出"`S_g` 是 `[R]` 而不是标量"。这一点在 Codex 与我这里都是显式的（`window_start_tokens[g]: int32[R]`；我的 `intervals` 也是 per-row）。建议补一个多请求不同长度的算例，避免实现者把 `S_g` 当标量。
- **建议修改**：§12.3 增加 per-row 版本。

### 24. preemption / request removal

- **风险：中高**（与 Codex 同）
- **章节**：§15.6（"多请求交替进入/退出"）、§3.3（padding 行）
- **为什么可能发生**：只在测试层提了一句，**没有设计层规则**。抢占会释放该请求的 block、收缩 `num_blocks`，并可能让请求行被新请求复用；窗口表里残留的 block id 配上任何"允许读"的长度，就会读到**已经归属另一个请求的物理块**——比多看历史严重得多（静默读到无关请求的 KV）。这与 §1.8 的 stale-tail 问题是同一族，但更严重（源是真实但已重新分配的块）。
- **需要的源码证据**：MRV2 的 request add/remove/row 复用路径（`vllm_ascend/worker/v2/model_runner.py`）；抢占是否会在同一 step 内复用行。
- **建议修改**：增加不变式"**`idx_mapping` 或 `num_blocks` 任何变化都使窗口 view 失效（generation 前进）**，并把 `(row → request_id)` 纳入 generation 校验"；补"抢占 + 行复用"专项测试。

### 25. graph padding / different batch shapes

- **风险：中**
- **章节**：§11.4、§8.6、§15.4
- **为什么可能发生**：§8.6 明确要求"证明 `shape / stride / row layout / valid length / operator binding` 与对应 Graph Descriptor 一致"——**这条比 Codex 的 `data_ptr()` 断言更完整，是本文档的亮点**。但配套的两件事没做：
  1. **形状/容量未定义**（§1.22）⇒ 这条要求无法验证；
  2. **多 descriptor 的切片 offset**：funnel 会做 `x[:num_reqs_padded]`（`vllm/v1/worker/gpu/spec_decode/speculator.py:322-324`），offset 随 descriptor 变；断言必须逐 descriptor 比对 `(data_ptr, storage_offset, shape, dtype)`。
- **建议修改**：断言改成四元组、逐 descriptor 比；容量按 §1.7 的"单一 start + lcm 对齐"重算。

---

## 2. Critical Issues

### G-C1 — 窗口表的形状/容量从未定义，且 capture 期的 metadata 入口不在视野内 ⇒ capture/replay 一致性不可证，SFA/DSA 路径下 feature 可能完全不可用

**风险等级：致命 / 阻塞实现。**

**对应章节**：§8.6、§11.4、§9.1、§16.2 Q5、R3；以及全文（无一处定义表宽度）。

**为什么可能发生**（源码证据）：

1. **形状未定义**：§8.6 只要求"per-KV-group dedicated persistent buffer"并提到"无效尾列"（暗示存在列容量），但**没有容量公式**。因此 §11.4 的"使用与 Capture 兼容的 shape 和地址"是一个**无法执行的要求**：既不能判断该选多宽，也不能判断 capture 期会记录什么形状。
2. **capture 期 metadata 构建不在文档视野内**。draft 侧 metadata 至少有**三个**构建入口，文档只承认两个（§16.2 Q5）：

   | # | 入口 | 源码 | 传入 funnel 的 block table |
   | --- | --- | --- | --- |
   | 1 | live propose | `vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:453`、上游 AR 路径 | 若设计生效则为窗口表 |
   | 2 | graph-manager replay 前 rebuild | `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:86-98`；`autoregressive/aclgraph.py:132-152` | 同上 |
   | 3 | **capture 期的 dummy metadata** | DFlash/DSpark：`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:36`（`get_dummy_block_tables`）与 `:55`（`build_attn_metadata`）；该模块级符号由 `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26` 在**导入期**重绑定，**绕过** `build_attn_metadata_wrapper()`（后者只替换 `vllm.v1.worker.gpu.spec_decode.speculator` 模块，`worker/v2/attn_utils.py:1240-1251`）。AR/Target：`autoregressive/aclgraph.py:111` → 上游 `cudagraph_utils.prepare_inputs_to_capture()` → Ascend `vllm_ascend/worker/v2/model_states/default.py:95-121` | **full 宽度的零表**（`vllm/v1/worker/gpu/block_table.py:177-187`） |

3. **后果**：capture 把 **full 宽度**的 `block_table` 参数固化进 graph；replay 若按设计喂一个**窄**窗口表，形状/参数不一致。对 **SFA/DSA** 尤其致命：两者 `update_graph_params()` 是 **no-op**（`vllm_ascend/attention/sfa_v1.py:885-896`；`AscendDSAImpl.update_graph_params`），captured op 读的就是 capture 期那块 storage，**pointer 与 shape 都换不了**。
4. 于是"设计可以冻结 Candidate B"这一结论**不成立**：B 相对 A 的核心优势之一是 graph 安全，而这一点是否成立取决于一个 document 未定义的形状决策，以及一个未枚举的入口。文档自己在 §0.1 声明"不能声称完成代码级验收"，却在 §"设计冻结条件"声称可冻结架构方向——这两句话矛盾。

**需要什么源码证据证明安全**：① draft 侧全部 metadata 构建入口；② 每个 backend 在 `for_cudagraph_capture=True` 时把 `block_table` 的 shape 固化到何处（SFA `SparseMLAMetadataState` 的 buffer、DSA req metadata、GQA/MLA 的 graph param pool）；③ `max_seq_len` 在 capture 与 replay 之间是否必须一致。

**建议修改**（必须显式选一条并写进 §8.6/§11.4）：
1. **（推荐）窗口表与 full 表同 shape**，只改内容（列 `[0,needed)` 放真实块、`[needed,row_width)` 显式清零、row 尾部按本轮有效块数约束）。capture 的 dummy 与 replay 的窗口表形状自然一致；SFA/DSA 的 builder-owned buffer 布局不变；**不需要改上游**。代价是每步多写若干列 0、多占 `O(R × G × full_width)`（数量级 MiB）。
2. 保持窄表（需给出 `C_g` 公式），但**接受修改上游** `cudagraph_utils.prepare_inputs_to_capture` / `dflash/cudagraph.py` 的签名以携带 view；相应更新 §2 Non-goals。
3. 保持窄表 + capture 期走隐式上下文——**与 §9.3 明确否决 contextvar 的立场冲突**，等于把它用来否决 Candidate A 的失败模式搬进 B。
4. 无论选哪条：把 capture 入口写进"metadata 构建入口清单"；补测试断言 capture 与 replay 传给 backend 的 `(data_ptr, storage_offset, shape, dtype)` 一致；明确 `max_seq_len` 作为容量上界**不窗口化**。

### G-C2 — AR first pass 在 MRV2 没有 draft metadata 落点，而文档把它列为激活点；朴素实现会原地修改复用的 Target metadata（正是它自己 R1 禁止的事）

**风险等级：致命 / 阻塞**（对 Eagle3 这条主线而言）。

**对应章节**：§10.1（"Eagle3 | AR first pass / per-step 的 Last Full-State Point"）、§10.2（"Full slot mapping → AR Window activation → Draft metadata"）、§12.2 流程图、R1。

**为什么可能发生**：

1. 文档的激活模型是"**method 在自己的最后 full-state 点激活 → Manager 生成 view → builder 消费**"。这个模型对 DFlash/DSpark 成立（`prepare_dflash_inputs` 之后确实有一次 draft metadata build），对 **AR first pass 不成立**。
2. MRV2 的 AR first pass **不构建 draft metadata**：它把自己收到的 Target `attn_metadata` 与 Target `slot_mappings` 直接传给 `_prefill()`（上游 `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:306-322`；注释："The target model's attention metadata and slot mappings can directly be used for draft prefill, because of the identical batch shape and KV cache layout"，配合 `:233-238` 说明为何 shape 相同）。FULL 路径同样只是"过滤 Target metadata"（Ascend `autoregressive/speculator.py:654-675`）。
3. 因此实现者按文档去找"AR first pass 的激活点"时会发现**没有可改的 draft-scope metadata**；最自然的做法是就地改它拿到的那份 Target metadata——而这正是 R1 声称"架构必须天然禁止"的污染。而 Target 那份 metadata 对象在同一个 `sample_tokens()` 里还服务于 Target verification / 下一步请求状态，污染后果是静默的正确性错误。
4. 文档对 first-pass 复用**完全无感**：全文没有出现"复用 Target metadata"这件事（对照：Codex 把它列为 R1 并给出"Window ON 显式重建 Draft metadata"的决策；我的设计给了 F1/F2/F3 三选一并推荐 F3）。
5. 顺带：这一步恰恰是**最重要的 draft token**（第 0 枚）。因此"首步不窗口化"（最省事的规避）会让 feature 收益显著打折，而文档没有任何地方提示这个权衡。

**需要什么源码证据证明安全**：① `autoregressive/speculator.py:306-322` 的复用路径与 `_prefill` 的调用契约；② `prepare_prefill_inputs`（`:690-770`）写出的 `input_buffers.seq_lens/query_start_loc/positions` 与 Target 的对应关系；③ 是否存在可承载 draft-scope metadata 的调用点（Ascend 侧 `autoregressive/speculator.py` 的 `_build_uniform_attn_metadata`/`_build_attn_metadata` override 可作为落点）。

**建议修改**：
1. §10.2 增加 first pass 的专门条目：**Window ON 时必须新造 draft-scope metadata，禁止浅改 Target 对象**（Window OFF 保留复用路径，以维持零回归）；
2. 同时把「重建后的 metadata 必须与 Target 在 `query_start_loc(_cpu)`/`positions`/`num_tokens`/`is_prefilling` 上逐位相同，只允许 read view 不同」写成硬约束（见 §3 M1）；
3. 把这一条从 §10.2 的普通表格行升级为与 G-C1 同级的 spec 条目，因为它决定了 feature 在主线 method 上的有效性。

---

## 3. Major Issues

### G-M1 — per-group 的独立 `start` / `windowed_len` 改变了 feature 语义（MRV1 是"一个窗口、一个对齐量"）

**风险：acceptance 行为变更，且与自身不变式冲突。**
**章节**：§3.2（`B_g`、`S_g`）、§8.6、§12.3、§10.2。
**为什么**：per-group 数学算得对（我复算了 §12.3 的两组数字，全部正确），但 MRV1 只有**一个**对齐量——`SlidingWindowAdapter(W, self.kernel_block_size, ...)`，其中 `kernel_block_size` 取第一个 draft attention layer 的（`vllm_ascend/spec_decode/llm_base_proposer.py:406-408, 446-452`），DSpark 的 per-group 循环复用同一个 `self.block_size`（`:2604-2605`）。所以在 MRV1 下两个 group 共享同一个绝对起点（64 的倍数 ⇒ 也是 32 的倍数），可见区间相同、只有列数不同；而本文档让 group1 的区间变成 `[160,300)`、group0 是 `[128,300)` → **同一个 draft 的不同 layer 看到不同长度的历史**。这与 §3.3 不变式"Window lengths 与 Window table 表达同一个有效读取区间"在跨 group 维度上自相矛盾。
**需要的证据**：目标 draft 的 group 数/各自 kernel block size；MRV1 在 hybrid multi-group + window 下的测试（据核实：**没有**；MTP 是唯一明确的多 group 用例，而 MTP 被 window 忽略 ⇒ 这是 MRV1 的未验证区域）。
**建议**：改为"**一个 proposal 一个绝对 `start`**，对齐到 `lcm{kernel_block_size_g}`；per-group 只体现在 `start_col_g = start/B_g` 与 `needed_g`"。既保住 MRV1 语义与单一 origin，又保证每组列映射正确。若产品要 per-group 独立窗口，写成显式 contract 变更 + MRV1 对照实验。

### G-M2 — 未收口 Ascend funnel 的 CPU 长度兜底（会直接触发最高危失败模式）

**风险：表窗口化而 CPU 长度仍是 full 量级 → 读到 cache 第 0 块。**
**章节**：§8.5、§3.3、R5、Q9。
**为什么**：`vllm_ascend/worker/v2/attn_utils.py:256-258` 在 `seq_lens_np is None` 时用 `np.full(num_reqs, max_seq_len)` 兜底，而 Draft 路径的 `max_seq_len = self.draft_max_seq_len`（上游 `spec_decode/speculator.py:361`）是 full 量级；`:259-260` 又令 `seq_lens_cpu_upper_bound = seq_lens_cpu`。文档把 CPU exact 当成"需要时再派生"，一旦留空 → funnel 给出 full 长度的 CPU 向量，而表已窗口化 → kernel 会读 `[needed,row_width)`（被置 0）→ block id 0 → **cache 第 0 块**。路径可达：MLA 与 `_select_seq_lens` 都是 CPU 优先（`vllm_ascend/attention/utils.py:573-576`、`attention/mla_v1.py:504-505`）。
另外 R5 的描述（"Optimistic CPU upper 被当成 exact"）**指错了机制**——真正的问题是 funnel **凭空合成**一个 full 长度。
**需要的证据**：GQA/MLA/SFA/DSA 各自最终消费的 length 字段；`_seq_lens_cpu` 在 MRV2 是否恒为 `None`。
**建议**：把"view 存在时必须同时覆盖 `seq_lens_np` 与 `seq_lens_cpu_upper_bound`，否则 fail fast"写成硬不变量；§8.5 增补"funnel 级兜底"小节；明确 CPU 向量的存储 owner（避免 `from_numpy` 让 AR 事后 `metadata.seq_lens_cpu.copy_(...)`（`worker/v2/spec_decode/autoregressive/speculator.py:776`）写进窗口的 CPU mirror）。

### G-M3 — padding/stale 只处理到"列"一级，缺少 per-row 有效块数约束

**风险：从 Full table 的 stale tail 复制出已失效的 block id（可能已被回收/重新分配）。**
**章节**：§3.3、§8.6、§15.4。
**为什么**：gather kernel 对 active row 只覆盖 `[0, num_blocks)`、不清 tail（`vllm/v1/worker/gpu/block_table.py` 的 gather；dummy 只在 `:177-187` 清 `[:num_reqs]`）。窗口从任意 `start_col` 起读，正好会把"看起来有值"的 tail 当有效块。文档只写了"对 active row 的无效尾列进行显式 mask/清理"——那只覆盖 `dst_col ≥ needed`，不覆盖 `src_col` 本身 stale。Codex 用 per-row `full_valid_num_blocks` 处理了这条（Invariant 12 / R16），GPT 与我早先的设计都漏了。
**需要的证据**：gather 的实际写入范围；`num_blocks` 与本轮 request order 的对齐；各 backend 的 padding 约定（例：GQA/FIA 用 **1** 补齐 `seq_lens_list` 并追加零表行，`vllm_ascend/attention/attention_v1.py:361-365`）。
**建议**：源侧三条同时成立——`src_col < full_table_width`、`src_col < full_valid_num_blocks[row]`、`dst_col < needed[row]`；补"padding row 的 block id 与任何 active row 的 block id 不相交"断言。

### G-M4 — native SWA 的组合语义：核心断言（"不能取 min"）表述有误，且 GQA/DSA/SFA 三态未枚举

**风险：实现者要么做出静默无效的 feature（只裁表），要么构造不必要的坐标适配层。**
**章节**：§8.7、§3.3、R4、Q7。
**为什么**：见 §1.17 的完整表。要点：(a) 两个约束都是**同一序列上的后缀区间**，区间层面**取交集 = 末端更紧者 = min**，因此"不能取 min"作为结论是错的（真正的限制是"不能在 rebase 后的表上复用绝对坐标索引"，这半句它说对了）；(b) DSA non-causal 的可见性**完全不读 block table**（`attention/dsa_v1.py:448-461, 1108-1125, 2265-2270`），只裁表无效，必须夹紧 `start_pos`（`:1107` 用的是 `hf_config.sliding_window - 1`，**无 None 检查** ⇒ 该路径必然有 native window）；(c) SFA 的 native window **不生效**（`sfa_v1.py:114-119`），可见性来自 top-k；(d) 只有 GQA 是真交集（`attention_v1.py:602-604`）。
**建议**：把 §8.7 升级为 spec：逐 backend 写明可见性表达方式与窗口落地点；把"不能取 min"改为"区间取交集，但不得复用绝对坐标索引"；DSA 上明确实现为 `start_pos = max(prefix - native, S)`；补"只裁表对 DSA 非因果无效"的陷阱说明与测试。

### G-M5 — Window OFF 的零回归无法承诺；配置校验是对 MRV1 的未标注收紧；`W<K_f` 的前提算错

**风险：用户可见行为变化 + 一条基于错误前提的校验决策。**
**章节**：§12.1、§13.1、§13.2、§3.2、§15.1。
**为什么**（三件事，都可核实）：
1. **OFF 的必要条件缺失**：§12.1 只写了"不创建不必要的 buffer"，但 §9.1 的初始化链没有 OFF 短路分支；更重要的是，它无法写出 Codex 那条关键条件——"**Window OFF 必须保留 Eagle first-pass 复用 Target metadata**"——因为它不知道这个复用存在（G-C2）。缺了这条，OFF 的正确性就没有可验证的表述。
2. **配置收紧未标注**：§13.1/§13.2 写"W 非正整数 → 配置错误，不启动"。而 MRV1 只做类型转换、无范围校验（`vllm_ascend/ascend_config.py:497`；`_validate_user_input_ranges()`（`:568-586`）不覆盖它），`draft_window_size=0` 在 MRV1 下会静默退化（`start=0`，窗口≈全量）。对 MRV1 已接受的配置改判为启动失败，是**用户可见的兼容性收紧**，Codex 明确把它留作"产品决定"（其 Non-goals 有专条），GPT 直接断言而未标注。
3. **`W<K_f` 的前提算错**：§3.2 说"尤其当 `W<K_f` 时，现有公式可能得到负的 `windowed_seq_len`"。以 `S=floor(max(L+K_f-W,0)/B)*B`、`L_win=L-S` 推导：`L_win<0 ⟺ S>L`，进一步要求 `K_f ≥ W + B - (L mod B)`；**不是** `W<K_f`。而四处 `assert self.decode_threshold <= 16`（`vllm_ascend/attention/attention_v1.py:248`、`mla_v1.py:299`、`sfa_v1.py:524`、`dsa_v1.py:654`）给出 `K_f ≤ 15`，kernel block size 通常 ≥16，所以正常配置下**不可达**（仅当 `B ≤ K_f - W`、即 B 很小 时才可达）。基于错误前提去收紧或设计边界用例，会得到错误的结论（§15.1 的"`W<K_f` 的非法/边界组合"应改为"`L_win ≥ 0` 的断言"）。
**建议**：① §9.1 增加 OFF 短路为第一条分支，并补"OFF 时零新增分配/零新分支"的测试；② 把配置收紧明确标注为"相对 MRV1 的兼容性变更，待 maintainer 批准"，或改为 warn + ignore；③ 把 `W<K_f` 换成"计算后断言 `L_win ≥ 0`，否则 fail fast"，并保留 `visible_len` 可能超过 W 的既有语义说明（这一条它写对了）。

---

## 4. Minor Issues

| # | 问题 | 章节 | 建议 |
| --- | --- | --- | --- |
| m1 | 符号 `C_g` 被定义为"**起始列索引**"（`S_g/B_g`），但未定义**列容量**，与常见"容量"含义冲突；容量缺失见 G-C1 | §3.2、§8.6 | 用 `start_col_g` 表示起点，另加 `cap_cols_g`（容量）并给出公式 |
| m2 | §12.3 的数值例是单请求，而 `S_g`/`needed` 是 per-row；文档未说明 | §12.3 | 补一个多请求不同长度的算例（Codex 与我都是 per-row 表述） |
| m3 | "不能只关注 `data_ptr()`"（§8.6）是对的，但配套断言未写出四元组 | §8.6、§15.4 | 断言改为 `(data_ptr, storage_offset, shape, dtype)` 且**逐 capture descriptor** 比较 |
| m4 | "不能直接对两个窗口大小取 min()"表述有误（见 G-M4） | §8.7 | 改为"区间取交集；不得复用绝对坐标索引" |
| m5 | §10.1 把 token-only 方法的 MRV1"静默未读取"与 MRV2"factory 报错"合在一格 | §10.1 | 拆成两列，避免实现 silent no-op |
| m6 | §14.1 把 Flashcomm 当作布局相关扩展点（虽未断言，但会误导）；事实是布局无关 | §14.1 | 改写为"Flashcomm 布局无关；相关风险来自 DSA-CP"，扩展点更名 CP Adapter |
| m7 | 未按 `draft_kv_cache_group_ids` 限定窗口范围（对 cache-only group 会浪费分配） | §8.6、§10.2 | 限定到有 draft attention 的 group |
| m8 | §16.1 R5 的机制描述指错（真正机制是 funnel 合成 full 长度，见 G-M2） | R5 | 改写风险描述并把 funnel 兜底纳入 |
| m9 | per-step window buffer 在多 capture descriptor 下的重复分配成本未量化 | §11.5 | 补量化（Codex 至少列为 R15） |
| m10 | 未讨论 `max_seq_len` 是否窗口化（影响收益能否兑现） | §15.5、§8.x | 明确保持容量语义、不窗口化，并解释原因 |
| m11 | lease/release 未指出 legacy 更新路径是"先 replay 后 update" | §11.6、§12.2 | release 条件写为"最后 reader + graph-param update 均完成" |
| m12 | 证据分级很好，但 `<FileCite>` 全部指向笔记行号而非仓库；读者无法自行验证 | §"证据边界"、全文 | 关键论断补仓库 `file:line`（或明确标注"未在 checkout 核实"） |

---

## 5. Questions Requiring Source Verification

> 文档 §16.2 自带 Q1–Q10，方向大多正确（Q2/Q4/Q5/Q6/Q7/Q8 是它自己认为最优先的六项，我同意 Q2/Q5/Q6/Q7/Q8）。以下是**追加、修正或重新表述**的，按优先级排列。

1. **QG-A（阻塞 G-C1）**：draft 侧 metadata 构建入口的完整清单——live / graph-manager rebuild / **capture-time dummy**，各自的 block table 来源与 `max_seq_len` 来源。已核出三条（`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:36,55`；`dflash/aclgraph.py:86-98`；`vllm/v1/worker/gpu/cudagraph_utils.py` → Ascend `model_states/default.py:95-121`），需确认是否还有第四条（DP/PP/310P 变体）。
2. **QG-B（阻塞 G-C1 的形状选择）**：各 backend 在 `for_cudagraph_capture=True` 时把 `block_table` 的 shape 固化到哪里；`max_seq_len` 是否必须 capture/replay 一致。
3. **QG-C（阻塞 G-C2）**：AR first pass 是否在所有路径都复用 Target metadata（含 FULL prefill，Ascend `autoregressive/speculator.py:654-675`）；Ascend 的 `_build_uniform_attn_metadata`/`_build_attn_metadata` override 能否直接作为重建落点。
4. **QG-D（阻塞 G-M1）**：目标 draft 的 group 数与各组 `kernel_block_size`；MRV1 在 hybrid multi-group + window 下是否有测试（若没有，per-group 语义变更需要产品决策）。
5. **QG-E（阻塞 G-M2）**：GQA/MLA/SFA/DSA 各自最终消费的 length 字段；`_seq_lens_cpu` 在 MRV2 是否恒为 `None`。
6. **QG-F（阻塞 G-M4）**：目标 draft 激活的 backend 集合；DSpark 的 `cad.causal` 取值（`dspark_proposer.py:343-347`）——它决定窗口走"表+长度"还是"显式索引"。
7. **QG-G**：`W<K_f` 是否真能产生负 `L_win`。我的推导是"需要 `K_f ≥ W + B - (L mod B)`，而 `K_f ≤ 15`（四处 decode_threshold 断言）+ `B ≥ 16` ⇒ 正常配置不可达"。请复核（文档据此设计边界用例）。
8. **QG-H**：`draft_window_size ≤ 0` 的正式政策（MRV1 无校验；收紧为用户可见变更需 maintainer 批准）。
9. **QG-I**：`update_stream` 与 graph-param update 的 happens-before（决定 release 时点；现有 legacy 顺序是"先 replay 后 update"）。
10. **QG-J**：async 下真实 in-flight 深度（仓库已有 `UvaBufferPool` ≥2 slot 的先例，倾向"重叠存在"）。
11. **QG-K**：抢占是否会在同一 step 内复用请求行（决定 §1.24 的严重度）。
12. **QG-L**：DeepSeek-V4 advisory 由哪个字段暴露、MRV2 speculator 应读 `self.vllm_config`（Target）还是 `self.draft_vllm_config`。
13. **QG-M（证据链）**：文档引用的笔记行号（`turn0file0`）对应的论断是否与当前 checkout 一致——尤其是 §4.2 的 MRV2 差异列表与 §3.2 的数学。建议把关键论断补上仓库 `file:line` 后再冻结。

---

## 6. Recommended Design Changes

按"先解除阻塞、再收敛范围"排序。

1. **解除 G-C1**：给出窗口表的**容量公式**并显式选择形状策略。推荐"与 full 表同 shape、只改内容"（不需要改上游、SFA/DSA 的 builder-owned buffer 布局不变）；同时把 capture 入口写进"metadata 构建入口清单"，并把 `max_seq_len` 明确为**容量上界、不窗口化**。若坚持窄表，则必须接受修改上游签名并更新 §2 Non-goals。
2. **解除 G-C2**：把"AR first pass 在 MRV2 没有 draft metadata 落点"写成 spec 条目，规定 **Window ON 时新造 draft-scope metadata、禁止浅改 Target 对象**，Window OFF 保留复用；并加"重建 metadata 与 Target 在 `query_start_loc(_cpu)`/`positions`/`num_tokens`/`is_prefilling` 上逐位一致"的硬约束。
3. **把 per-group `start` 收敛为 per-proposal 单一 `start`**（对齐 `lcm{B_g}`），per-group 只保留列映射；若产品确要 per-group 独立窗口，写成独立 contract 变更（G-M1）。
4. **收口 CPU 长度**（G-M2）：view 存在时强制覆盖 `seq_lens_np` 与 `seq_lens_cpu_upper_bound`，否则 fail fast；补 funnel 兜底小节；明确 CPU 向量存储 owner。
5. **补源侧有效性约束**（G-M3）：`src_col` 必须同时受 `full_valid_num_blocks[row]` 限制；padding row 的 block id 与 active row 不相交。
6. **把 native SWA 从"风险"升级为 spec**（G-M4）：逐 backend 写明组合语义；DSA 实现为夹紧 `start_pos`；SFA 明确 native window 不生效；纠正"不能取 min"的表述。
7. **修 OFF 与配置策略**（G-M5）：§9.1 增加 OFF 短路；配置收紧标注为兼容性变更或改回 warn+ignore；`W<K_f` 换成 `L_win ≥ 0` 断言。
8. **补一条 plumbing 章节**：本文档当前没有任何真实函数入口，实施者无法起步。建议在 §8/§11 之间增加"注入点与调用链"一节，逐条列出：live 路径、graph-manager rebuild 路径、capture 路径、AR first pass 路径分别在哪里拿到 view（对照 Codex 的 §Expected File Changes 表格形式）。
9. **收敛首期范围**：给出明确的 MVP 支持矩阵（建议 `{dflash, dspark} × {GQA, MLA} × {eager, FULL}`，其余 capability 解析后 fail fast），把 `BackendWindowAdapter`、多 graph-generation slot、CP/Flashcomm Adapter 放到后续。理由：文档自身提议了 6 个抽象、3 层结构、7 个 owner，而 MRV1 的同类实现只有约 90 行（`vllm_ascend/spec_decode/utils.py:83-169`）；`AGENTS.md` 要求 patch "minimal and focused" 且有长期上游计划。文档自己也写了"不要为了架构统一重写公共父类"——这条自律值得贯彻到抽象数量上。
10. **修正"可冻结架构方向"的表述**：G-C1 说明架构选择本身依赖源码（形状策略），因此应改为"可冻结设计目标与分层；形状策略、注入点、AR first-pass 策略三个决策待源码验证后冻结"。

---

## 附录 A：本次评审用到的源码事实（均为本机核对）

| 事实 | 位置 |
| --- | --- |
| AR propose 在非 FULL 时复用 Target `attn_metadata` 与 Target `slot_mappings` | `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:306-322`（注释 `:311-313`） |
| 复用成立的原因（query 长度补齐到含 rejected 位置） | 同文件 `:233-238` |
| capture 期 metadata：dummy full 宽度零表 + 模块级 `build_attn_metadata` | `vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:36,55` |
| 该模块符号由 patch 导入期重绑定，绕过 wrapper | `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26` |
| wrapper 只替换 `spec_decode.speculator` 模块 | `vllm_ascend/worker/v2/attn_utils.py:1240-1251` |
| AR/Target capture 走 `prepare_inputs_to_capture` → Ascend `prepare_attn` | `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:111`；上游 `cudagraph_utils.py`（约 `:785,:820`）；Ascend `worker/v2/model_states/default.py:95-121` |
| dummy block table 是 full 宽度零表 | `vllm/v1/worker/gpu/block_table.py:177-187` |
| funnel 的 CPU 兜底 | `vllm_ascend/worker/v2/attn_utils.py:256-260` |
| Draft 路径 `max_seq_len = draft_max_seq_len` | `vllm/v1/worker/gpu/spec_decode/speculator.py:361` |
| capture 期 `max_seq_len = max_model_len` | `dflash/cudagraph.py:64`；Ascend `model_states/default.py` |
| CPU 优先选择链 | `vllm_ascend/attention/utils.py:573-576`；`attention/mla_v1.py:504-505` |
| SFA/DSA 的 `update_graph_params()` no-op | `vllm_ascend/attention/sfa_v1.py:885-896`；`AscendDSAImpl.update_graph_params` |
| GQA legacy `update_graph_params()` 抛 NotImplementedError；只有 UpdatableGraph 可用 | `vllm_ascend/attention/attention_v1.py:572-581`；`vllm_ascend/utils.py:1769-1775` |
| SFA 强制 `ori_mask_mode=0` / `ori_win_left=-1`（native window 不生效） | `vllm_ascend/attention/sfa_v1.py:114-119` |
| DSA non-causal 走显式索引；`hf_config.sliding_window - 1` 无 None 检查 | `vllm_ascend/attention/dsa_v1.py:410, 448-461, 1107, 1108-1125, 2265-2270` |
| GQA native SWA → `sparse_mode=4` + `pre_tokens`；draft 层仍传 block_table | `vllm_ascend/attention/attention_v1.py:602-604`、`:459-472` |
| `decode_threshold <= 16`（⇒ `K ≤ 15`） | `attention_v1.py:248`、`mla_v1.py:299`、`sfa_v1.py:524`、`dsa_v1.py:654` |
| FIA 给 dummy request 补 `seq_lens_list`/`seq_lens` 用 **1** | `vllm_ascend/attention/attention_v1.py:361-365` |
| MRV1 单一对齐量（取第一个 draft layer 的 kernel block size） | `vllm_ascend/spec_decode/llm_base_proposer.py:406-408, 446-452`；DSpark 复用同一值 `:2604-2605` |
| MRV1 一次 apply + 之后长度递增、表不变 | `llm_base_proposer.py:1119-1127`、`:1147-1158`、`:2073-2077`、`:2134-2136` |
| `get_dcp_local_seq_lens` 对 L 非线性 | `vllm/v1/attention/backends/utils.py:1088-1133` |
| Flashcomm = SP-MoE 开关（布局无关）；DSA-CP 与其互锁 | `vllm_ascend/ascend_config.py:639-657, 694-698`；`utils.py:916-928`；`attention/sfa_v1.py:869` |
| DSA-CP 切 token 流，不重排 block table | `vllm_ascend/attention/context_parallel/dsa_cp.py:1133-1138` |
| PCP 下 draft 恒 replicated（`prepare_draft_prefill` no-op） | `vllm_ascend/worker/v2/pcp_manager.py:383-392` |
| legacy replay 顺序：先 replay 后 update | `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:154-194`；`dflash/aclgraph.py:100-138` |
| MRV1 无 `draft_window_size` 范围校验 | `vllm_ascend/ascend_config.py:497`；`_validate_user_input_ranges()` `:568-586` |

## 附录 B：应当原样保留的优点（我核对后确认正确）

1. **CRITICAL**：AR horizon 必须冻结、不能每步重算 —— §8.4 是三者中对这个语义陷阱讲得最清楚的，并且它**指出了我的设计里的一个真实缺陷**（我已据此修正，新增 P13 与 §5.3 的推导）。
2. **CRITICAL**：graph binding 不能只看 `data_ptr()`，还要证明 `shape/stride/row layout/valid length/operator binding` —— 比 Codex 更完整，也是 G-C1 的动机之一。
3. **CRITICAL**：绝对坐标 vs 窗口局部坐标是两个坐标系，Read View 必须同时携带 `absolute_end / visible_start_abs / visible_length` —— 与我从源码得到的"索引型可见性必须用绝对区间夹紧"是同一结论，且它把机制说清了。
4. **CRITICAL**：明确不采用 contextvar，并给出四条理由；区分"显式 context 传 Window 执行状态"与"用已有 Forward Context 交付最终 metadata"。
5. §14.2 的 CP 判断正确：不得用 `/CP_size`，必须做"绝对区间 → CP 布局变换 → local 状态"；并指出要证明 logical→physical 没有双重偏移。
6. §11.6 的 `Persistent address stability ≠ Async lifetime safety` 与"不要假设两份 buffer 就够"。
7. §8.5 的四方案取舍表（inplace / 临时 tensor / view / dedicated persistent buffer）与"upper 不能冒充 exact"。
8. §15.2 把 `Window(Window(Full))` 明确列为**不应存在的数据流**（repeated-window 的负向测试）。
9. §16.1 的风险优先级把 R1–R4、R8 标为 Critical，方向正确（只是 R1 的"天然禁止"缺论证）。
10. **证据分级（[S]/[U]/[D]）与"设计冻结条件"的自我约束** —— 这是本次三份文档里唯一主动声明证据等级的，值得保留为团队习惯；建议再加一档：**[V] 已在当前 checkout 的源码中核实（附 `file:line`）**，并把关键论断升到该档。
