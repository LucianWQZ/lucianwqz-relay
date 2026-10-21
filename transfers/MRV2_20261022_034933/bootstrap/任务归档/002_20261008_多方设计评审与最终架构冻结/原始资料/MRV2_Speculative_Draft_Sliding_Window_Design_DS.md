# MRV2 Speculative Draft Sliding Window（`draft_window_size`）架构设计

> 状态：设计提案（未写生产代码）
> 作者：Claude（独立设计）
> 日期：2026-10-08
> 代码基线：`/Users/wenqingzhang/Desktop/vllm/vllm-ascend`（#14596 之后的 main）、`/Users/wenqingzhang/Desktop/vllm/vllm`（同仓库 checkout）
> 行号约定：本文所有 `file:line` 均在本机逐条核对过；引用 Ascend 仓库时省略前缀 `vllm_ascend/`，引用上游时写全 `vllm/v1/...`。

## 0. 独立性与方法论声明

- 本文**独立设计**。没有阅读同目录下的
  `MRV2_Speculative_Draft_Sliding_Window_Design_Codex.md`（另一 Agent 的设计稿），
  以避免与既有方案收敛。
- 参考过的材料只有：`Sliding window原理_gpt.md`（MRV1 窗口数学讲解）、
  `Sliding window源码_codex.md`（Stage 1–7 源码研究笔记）、
  以及仓库自带的 `docs/source/developer_guide/Design_Documents/speculative_kv_sliding_window.md`。
  这些材料一律当作**待核实的线索**，本文引用的每条事实都在本机源码里重新核对过；
  凡未被我自己核实的，显式标注「待核实」。
- 本文与 MRV1 的关系是**功能契约继承**，不是实现移植：MRV2 的 Metadata 组装方式、
  reader/writer 的所有权、graph 契约都与 MRV1 不同，直接搬运 MRV1 的 apply 位置会错。

---

## 1. 事实基线（设计的地基，全部已核实）

### 1.1 MRV1 的 Feature Contract

| 事实 | 证据 |
| --- | --- |
| 配置来自 `additional_config.draft_window_size`，类型 `int \| None`，**没有正数范围校验** | `ascend_config.py:497`；示例见 `ascend_config.py:355` |
| Adapter 构造处：单一 `block_size = kernel_block_size`（取第一个 draft attn layer） | `llm_base_proposer.py:406-408`、`llm_base_proposer.py:446-452` |
| `future_offset = 0 if method in ("dflash","dspark") else num_speculative_tokens` | `llm_base_proposer.py:445` |
| MTP：warning + **不构造 adapter**（`method != "mtp"` 才构造） | `llm_base_proposer.py:423-429`、`llm_base_proposer.py:437` |
| DSpark + `deepseek_v4*` target：warning，但**仍然启用** | `llm_base_proposer.py:430-435`、`llm_base_proposer.py:437` |
| 公共 apply 点：`draft_window_size is not None and method not in ("dspark","mtp")` | `llm_base_proposer.py:1119-1127` |
| DSpark 的 apply 点在 `build_draft_attn_metadata()` 的 per-group 循环内，且**在** `cad.block_table_tensor` 被换成该 group 的 full table **之后** | `llm_base_proposer.py:2588-2605` |
| 窗口数学：`start=floor(clamp(seq_lens+K-W,0)/b)*b`，`windowed_len=seq_lens-start`，gather `start_block+[0,max_window_blocks)`，无效列置 0 | `spec_decode/utils.py:120-147` |
| apply 同时改：`block_table_tensor`（换成 clone 视图）、device `seq_lens`、以及存在时的 `seq_lens_cpu` / `_seq_lens_cpu` / `seq_lens_cpu_upper_bound` | `spec_decode/utils.py:149-169` |
| **不改** `slot_mapping`；后续 draft step 的 slot 计算显式改用 `self.sliding_window.full_block_table` | `llm_base_proposer.py:2104-2112` |
| apply 之后，窗口化结果被拷进 per-step persistent buffer（`seq_lens_group[0]` / `slot_mapping_group[0]`），再传给 `build_draft_attn_metadata()` | `llm_base_proposer.py:1147-1165` |
| DSpark 侧已经存在 per-group persistent block table buffer 概念（`_per_group_block_table_buffers`）与 per-group slot buffer | `dspark_proposer.py:103-104`、`dspark_proposer.py:253-256`、`dspark_proposer.py:270-307` |
| 文档口径：只覆盖 MRV1；MTP 强制忽略；「draft 自带 native SWA 时 `draft_window_size` 应 ≥ training window」 | `docs/.../speculative_kv_sliding_window.md:20-30,89-99`；`docs/source/user_guide/feature_guide/speculative_decoding.md:462-522` |

### 1.2 MRV2 的现状：feature 完全不存在

`grep -rn draft_window_size` 在 `vllm_ascend/worker/` 下**零命中**；
`SlidingWindowAdapter` 在 `worker/v2/` 下**零命中**。
`worker/v2/spec_decode/__init__.py:23-72` 只做 speculator 选择，不读该字段。
MRV1 的 contract（MTP warning、DSV4 warning）在 MRV2 也**一律不存在**。

### 1.3 MRV2 draft read plane 的所有权（这是设计的关键约束）

| 对象 | owner | 与 Target 的关系 | Graph 契约 |
| --- | --- | --- | --- |
| `BlockTables.block_tables[gid].gpu` | 共享 `BlockTables` | authoritative，读写同一对象 | `block_table_ptrs` 在 init 绑定（`vllm/v1/worker/gpu/block_table.py:93-97`） |
| `BlockTables.input_block_tables[gid]` | 共享 `BlockTables` | **与 Target 同一份 buffer**（`block_table.py:73-74`；`gather_block_tables` `:148-175`） | `get_dummy_block_tables()` 要求 capture/runtime 同地址（`block_table.py:177-187`） |
| `BlockTables.slot_mappings` | 共享 `BlockTables` | 真实 KV 写地址，DFlash/DSpark 直接写它 | `get_dummy_slot_mappings()` 同址要求（`block_table.py:223-232`） |
| Speculator `input_buffers.seq_lens` / `query_start_loc` / `dcp_local_seq_lens` | speculator | 独立 buffer | persistent，capture 直接引用（`vllm/v1/worker/gpu/spec_decode/speculator.py:144-163`） |
| `target_input_buffers` | Target runner | **共享引用** | `speculator.py:271-293` |
| Draft metadata 组装 | `DraftModelSpeculator._build_attn_metadata()` | 只对 draft 生效 | `vllm/v1/worker/gpu/spec_decode/speculator.py:295-369` |

**结论（P0 级约束）**：`input_block_tables` 与 `slot_mappings` 是 **Target 与 Draft 共享的 persistent buffer**，
任何 window 变换都**不能原地改写它们**——MRV1 能原地改，是因为 MRV1 的
`common_attn_metadata.block_table_tensor` 是 proposer 私有的 per-step 对象。
MRV2 必须产出 **speculator 私有的 persistent window buffer**。

### 1.4 MRV2 的 length 生产者是「一对多」的（设计成败点）

上游的公共组装箱只把少量参数传下去，Ascend 侧在此之上又有多个**独立**的 length 生产者：

| # | 生产者 | 位置 | 谁消费 |
| --- | --- | --- | --- |
| L1 | Draft device `seq_lens` | 漏斗 `seq_lens=self.input_buffers.seq_lens[:n]`（`vllm/.../speculator.py:355`） | `AscendCommonAttentionMetadata.seq_lens` → 各 backend |
| L2 | Draft CPU upper | `draft_seq_lens_cpu_upper_bound = target_upper + step`（`vllm/.../speculator.py:326-334`） | `seq_lens_cpu_upper_bound` |
| L3 | `seq_lens_cpu` | Ascend 漏斗的 **fallback**：`seq_lens_np is None` 时 `np.full(num_reqs, max_seq_len)`（`worker/v2/attn_utils.py:256-260`） | MLA / DSA / SFA 的 CPU 优先分支（`attention/utils.py:553-587`、`attention/mla_v1.py:504-505`） |
| L4 | AR 每步 CPU 向量 | `_get_seq_lens_cpu()` 读 **Target** 的 `target_input_buffers.seq_lens_cpu`（`worker/v2/spec_decode/autoregressive/speculator.py:824-835`），`_calc_next_seq_lens_cpu()` `+step` 并清零 padded 行（同文件 `:815-822`） | `_update_decode_attn_metadata()` 写进 `metadata.seq_lens_cpu` 与 `seq_lens_list`（同文件 `:733-776`）→ FIA / MLA |
| L5 | AR per-step persistent CPU buffer | `input_buffers.draft_seq_lens_cpus[step]`，仅 FULL 初始化（同文件 `:103-109`），由 `_init_decode_draft_attn_metadatas()` 绑定（同文件 `:719-729`） | FULL merged multi-step decode 的 graph 参数 |
| L6 | AR graph-param KV 列表 | `build_fia_params()` 从 `input_batch.seq_lens_np[:num_reqs] + step` **重新算一份**（同文件 `:778-813`） | `UpdatableGraph.resolve_tasks(SharedSource(fia_params))`（`autoregressive/aclgraph.py:196-208`） |
| L7 | DCP local（device） | `prepare_dcp_local_seq_lens()` 从 **draft device** global 派生（`vllm/.../speculator.py:335-345`） | DCP-aware backend |
| L8 | DCP local（CPU） | Ascend 漏斗从 `seq_lens_cpu` 派生（`worker/v2/attn_utils.py:265-273`） | MLA/SFA/DSA 的 CP 分支 |
| L9 | DCP/CPU（DSpark 专用） | `DCPManager.prepare_draft_dcp_metadata_inputs(target_seq_lens_cpu=..., step=Q)`（`worker/v2/spec_decode/dspark/speculator.py:137-151`） | 作为 `seq_lens_np` 注入工厂（`worker/v2/attn_utils.py:1273-1274`） |
| L10 | draft 绝对长度（DFlash/DSpark） | Ascend kernel 写 `out_seq_lens = min(last_valid_pos+1+num_query_per_req, max_model_len)`（`worker/v2/spec_decode/dflash/speculator.py:287-290`） | L1 |

**结论**：只把 L1 窗口化 = 必然错。AR 路径上至少 L1/L3/L4/L5/L6 五处必须同源；
这决定了「在哪里 apply」不能只考虑 metadata 漏斗。

### 1.5 MRV2 的调用时序与重复构建

`build_attn_metadata`（Ascend 漏斗）的调用者不止 live propose：

| 时机 | 证据 |
| --- | --- |
| AR live decode（每步） | `autoregressive/speculator.py:573-609`（override 内 `super()._build_uniform_attn_metadata`）→ 上游 `vllm/.../speculator.py:346-368` |
| AR FULL replay 入口 | `autoregressive/aclgraph.py:132-152` 先 `build_draft_attn_metadatas()`，再 replay + `update_full_graph_params()` |
| AR FULL prefill | `build_draft_attn_metadatas(is_draft_model_prefill=True)` → `_prepare_replicated_prefill_attn()`（`autoregressive/speculator.py:654-684`） |
| DFlash/DSpark live | `worker/v2/spec_decode/dflash/speculator.py:144-162` 包 `build_attn_metadata_wrapper()` 后 `super().propose()` → 上游 `vllm/.../dflash/speculator.py:453` |
| DFlash/DSpark FULL replay 入口 | `dflash/aclgraph.py:86-98` **再次**调用 `build_draft_attn_metadatas()` |
| Ascend DFlash graph 辅助 | `dflash/speculator.py:27-46` 用 padded req 数重建 metadata 并改 `actual_seq_lengths_q` |
| DSpark graph 辅助 | `dspark/speculator.py:153-186` |
| **Capture 期（第三条通道）** | `build_attn_metadata_wrapper()` 只替换 `vllm.v1.worker.gpu.spec_decode.speculator` 模块里的符号（`worker/v2/attn_utils.py:1240-1251`）；DFlash 的 capture 走的是**另一个模块**的符号，由 `patch/worker/patch_v2/patch_dflash_speculator.py:28` 在**导入时**直接绑定（`cudagraph_module.build_attn_metadata = build_attn_metadata`），调用点在 `vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:55`。AR 侧 capture 也另走一层（`autoregressive/speculator.py:378-381`） |

**结论**：同一次 draft forward 里窗口变换可能被触发**多次**（live + graph manager rebuild），
所以窗口变换必须**幂等**，且**必须以 full state 为源**。
另外，capture 期的 metadata 构建**不经过** `build_attn_metadata_wrapper()` 的作用域，
因此「capture 时的 attention 形状」与「replay 时的输入形状」之间的一致性
必须由设计保证（见 §5.4 的宽度不变式决策）。

### 1.6 AR first prefill 直接复用 Target metadata（MRV2 独有的隔离难题）

上游 `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:306-322`：
非 FULL 时 `_prefill(..., attn_metadata, slot_mappings, ...)` 收到的就是 **Target 的** metadata dict 与 slot mappings，
注释明确写「identical batch shape and KV cache layout」。
Ascend 侧 FULL prefill 的 `build_draft_attn_metadatas(is_draft_model_prefill=True)` 也是「过滤 Target metadata」（`autoregressive/speculator.py:654-675`）。

**结论**：AR 第一个 draft step 目前**没有 draft-scope metadata**。要在这里上游窗口，
要么改为构建 draft-scope metadata（放弃复用），要么对 target metadata 做 draft-layer 的视图替换（含污染风险）。

### 1.7 Native SWA × `draft_window_size` 是两套东西

- FIA 的 native SWA 来自 attention layer 自身的 `sliding_window`（`attention/attention_v1.py:502-525`），
  运行时映射为 `sparse_mode=4 / pre_tokens=sliding_window / next_tokens=0`（同文件 `:602-604`）。
- `is_draft_model` 会改变 block_table 是否传入 FIA：`FIAParamProvider.resolve()` 在
  `is_draft_model or not sliding_window` 时传 `block_table`，否则不传（同文件 `:453-472`）。
- DSpark/DSA 另有一套 **model-native** sparse 可见性：`build_dspark_swa_indices()` 读 `hf_config.sliding_window`
  并写进 builder-owned persistent buffer（`attention/dsa_v1.py:410`、`:420-501`、`:600-652`、`:1105-1125`）。

**结论**：`draft_window_size` 是「按序列尾裁剪历史」；native SWA 是「按 query 的带宽掩码」。
两者叠加的正确语义是**取交集**（在窗口化坐标系上算带宽，天然取更紧者），
但绝不能互为实现（尤其不能拿 `dspark_swa_indices` 冒充本 feature）。

---

## 2. Design Principles

> 这 12 条是本设计的「宪法」。后面所有方案取舍都以它们为判据。

**P1 — 只改 read plane。**
Window 只改变 Draft Attention 能读到的历史 KV。物理 KV 分配、`slot_mapping`、
`positions`、`query_start_loc`、Scheduler 状态、Target 计算**一律不变**。
继承 MRV1 的两条不变式（`spec_decode/utils.py:149-169`、`llm_base_proposer.py:2104-2112`）。

**P2 — Window 是 full state 的纯函数。**
`window = f(full_tables, full_lengths, W, block_size_of_group, future_offset)`。
任何一次变换都必须以 full state 为输入；**禁止 window-of-window**。
实现上要有可断言的来源标识（见 §4 的 `epoch`）。

**P3 — 共享对象只读，产物必须私有且 persistent。**
`BlockTables.input_block_tables[*]`、`.slot_mappings`、`.block_tables[*]`、
`target_input_buffers`、AR prefill 复用的 target metadata 都**只读**。
Window 产物写在 speculator-owned 的 persistent buffer 里（MRV1 的
`SlidingWindowAdapter._block_table_clone`（`spec_decode/utils.py:114-118`）是同类物，
但 MRV2 必须**逐 group**）。

**P4 — 同一 attention 调用消费的所有 length 表示必须同源。**
即 §1.4 的 L1–L10 必须全部由**同一个** windowed length 派生。
不允许「device 窗口化、CPU list 仍 full」或反之。

**P5 — Graph-stable。**
Window 产物必须地址稳定：capture 与 replay 读同一 storage；
每步只更新**内容**（`copy_`），不替换 metadata 里的 tensor 引用——
除非该参数确实落在 `UpdatableGraph` 注册的 task kwargs/provider 里。

**P6 — Per-group 正确性。**
窗口数学逐 KV group 使用该 group 的 `kernel_block_size` 与 row width。
不得以 group 0 的 block size 推所有 group（MRV1 的单一 `kernel_block_size`
在 MRV2 hybrid cache 下不再成立，见 `llm_base_proposer.py:406-408`）。

**P7 — Padding 显式化。**
Window buffer 的 (a) request padding rows `[num_reqs, num_reqs_padded)`、
(b) active row 的无效列 `[needed, max_window_blocks)` **每步显式写 0**。
不得依赖 stale 内容——stale block id 可能已被释放并分配给别的 request。

**P8 — 幂等 + 可检测的重复。**
同一步内多次构建必须得到相同结果；用来源断言（传入的 table 必须是
`BlockTables.input_block_tables[gid]`/authoritative table 本身）阻断二次窗口。

**P9 — 配置契约与 MRV1 一致，且不静默扩张。**
MTP = warn + ignore（**不能**因为 MRV2 MTP 复用 AR 基类就自动获得 window）；
DSpark + `deepseek_v4*` = warn 但仍启用；
不经过 base proposer 的方法在 MRV1 是「静默未读取」，MRV2 应把它显式化为
**一条 warning + ignore**（这是有意的行为升级，见 Q11）。

**P10 — 与 native SWA 是叠加而非替代。**
两者取交集；`draft_window_size` 小于 draft 自带 training window 时应提示。

**P11 — 单一 fan-in，显式传参。**
Window 的落地通道必须收敛到**一个**地方（Ascend 漏斗），
并且通过**显式参数**传递（不用隐式全局 / contextvar），以保证 async 与多实例安全。

**P12 — 不引入热路径同步。**
窗口数学全部在 device 上做（MRV1 已是如此：`spec_decode/utils.py:131-147`）。
CPU 侧只做「从已有 CPU 向量派生的算术」，不新增 D2H。

**P13 — AR 的窗口起点在 proposal 级冻结。**
AR 的「apply 时机」是 **proposal 级**而不是 builder 调用级：
`horizon = L0 + K` 在 proposal 开始冻结，每步 `future_offset = horizon - L_s`（从 K 递减到 0），
使 `L_s + future_offset = horizon` 恒定 ⟹ `start` 与裁剪后的表在 proposal 内不变，只有长度递增。
这与 MRV1 一致（见 §5.3 的推导）；若改成每步按当前 exact end 重算 `start`，
窗口会逐步右移、可见长度恒为 `W-K`（语义变更），且每步表 origin 变化（graph 成本上升）。
`future_offset` 因此**不是常数**，而是 `horizon - L_s`。

---

## 3. Architecture Options

三个候选方案的差别在于**「谁拥有窗口状态」**与**「变换在哪落地」**这两个正交问题。

### 3.1 Candidate A — Speculator-owned `DraftWindowPlane`（显式状态 + 显式 plumbing）

**形态**

- 新增共享基础设施（一个模块，例如 `worker/v2/spec_decode/draft_window.py`）：
  - `DraftWindowPolicy`：`resolve(method, target_model_type, draft_hf_config) -> WindowDecision`，
    封装 §1.1 的 method policy（enabled / future_offset / warning / scope）。
  - `DraftWindowMath`：纯 device 算术，逐 group 版本（`start` / `windowed_len` / `needed` / gather+mask），
    数学与 MRV1 `compute_sliding_window_block_table` 等价。
  - `DraftWindowPlane`：speculator 持有的 persistent 状态（每 group 的 `[cap_reqs, max_window_blocks_g]`
    int32 表；windowed device `seq_lens`；windowed CPU `seq_lens_cpu` / upper；`dcp_local_seq_lens`），
    外加 `epoch`。
  - `DraftAttentionView`：frozen value object，承载「本次 draft forward 的窗口可见读平面」。
- 每个 speculator 家族在**自己的 window boundary** 刷新 plane，然后把 view 显式交给
  漏斗与所有 length producer。

**ownership**：speculator。
**glue**：AR / DFlash / DSpark 各一处 boundary + 各自 length producer 的改写（AR 最多）。

**优点**：语义清晰；窗口状态一处持有；不依赖 backend。
**缺点**：AR 的 length producer 分散在 5 处（§1.4 L1/L3/L4/L5/L6），改写面大且容易漏。

---

### 3.2 Candidate B — Draft Window as a metadata/backend capability（下推到 builder）

**形态**

- `AscendCommonAttentionMetadata` 增加一个只读描述 `draft_window: DraftWindowSpec | None`
  （`window_size`、`block_size_of_group`、`future_offset`），**不携带** full state 的副本。
- 每个 attention metadata builder（GQA/FIA、MLA、SFA、DSA）在自己的
  `build()` / `build_for_cudagraph_capture()` / `update_graph_params()` 里
  用 common metadata 已有的 full table + full seq_lens 派生窗口化 table/length，
  写进**builder 自己的 persistent buffer**（SFA 已有 `block_table_buffer`、
  DSA 已有 `dspark_swa_indices_buffer` 这一套先例，`attention/sfa_v1.py:297-327`、`attention/dsa_v1.py:600-652`）。
- Speculator 侧只需把 `W` 放进 metadata，并让几个 speculator 侧的 CPU 向量
  （L4/L5/L6）改为窗口语义。

**ownership**：attention backend（builder）。
**glue**：N 个 backend × 3 条路径（build / capture / graph param update）。

**优点**：复用 backend 已有的 persistent derived buffer；
capture 与 replay 天然在同一处产生，地址稳定性最容易证明；
对新增 backend 是「能力」而非「散落改动」。
**缺点**：
1. backend 数量 × 路径数量 = 改动面最大，且 hybrid multi-group 下每个 group 都要正确；
2. speculator 侧仍必须单独处理 L4/L5/L6 → **双 ownership**（一半在 speculator、一半在 backend）；
3. Backend 层拿到的是 `AscendCommonAttentionMetadata`，其中 `seq_lens_cpu` 可能是
   `worker/v2/attn_utils.py:256-260` 的 fallback（uniform `max_seq_len`），
   在 backend 里无法判断它是否 exact → 容易出现「按 upper 当 exact 用」；
4. 与上游 hook 演进（#56181 反复改名）耦合更紧。

---

### 3.3 Candidate C — Scope interception（在既有 draft-scope 机制上做单点纯函数变换）

**形态**

- 复用 MRV2 **已经存在**的 draft-scope 机制：
  `build_attn_metadata_wrapper()`（`worker/v2/attn_utils.py:1243-1251`）+
  `build_draft_attn_metadata_factory()`（同文件 `:1254-1281`，已用 `seq_lens_np` 注入先例）。
- 扩展工厂注入一个显式 kwarg（例如 `draft_window_view=`）；
  Ascend `build_attn_metadata()` 在构造 `AscendCommonAttentionMetadata` **之前**
  用 view 替换 `block_tables[i]`、`seq_lens`、`seq_lens_np`（→ `seq_lens_cpu`）、
  `seq_lens_cpu_upper_bound`，并从 windowed device global length 派生
  `dcp_local_seq_lens`、从 CPU global length 用**绝对区间前缀差**派生 `dcp_local_seq_lens_cpu`（见 §5.4）。
- 因为替换发生在 `attn_utils.py:294-330` 之前，所有 backend 的**派生状态**
  （MLA `seq_lens_list`、FIA `actual_seq_lengths_kv`、DSA `start_pos` /
  `dspark_swa_indices`、SFA `SMLA plan`）自动从窗口化数据派生 → 天然满足 P4/P6。

**ownership**：变换由「scope + view」承担，view 由一个持久的 plane 产生（可与 A 组合）。
**glue**：漏斗一处；但 speculator 侧 L4/L5/L6 仍需 method-specific 改写。

**优点**：
1. **单一 fan-in**：一次覆盖所有 group / layer / backend（P11）；
2. 对 attention backend **零改动**；
3. 顺带修掉一个现存陷阱：把 `seq_lens_cpu` 从
   `np.full(num_reqs, max_seq_len)` 的 fallback 换成真实窗口向量（P4 的必要条件）；
4. 落地位置在 backend 派生之前，天然满足「derived state 必须由窗口化数据重建」。
**缺点**：
1. 需要显式传递 view（若偷懒用隐式 context，async/multi-instance 会踩坑）；
2. **不覆盖** AR first prefill（复用 Target metadata，根本不进这个漏斗，§1.6）；
3. **不覆盖** L5/L6（`draft_seq_lens_cpus`、`build_fia_params`）——它们绕过漏斗自行算长度。

---

## 4. Trade-offs

评分：★=差 … ★★★★=好。判据见 §2 的原则。

| 维度 | A（speculator plane） | B（backend capability） | C（scope interception） |
| --- | --- | --- | --- |
| 改动面（越小越好） | 中（3 家族 + 1 模块） | **大**（N backend × 3 路径） | **小**（漏斗 1 处 + method glue） |
| ownership 清晰度 | ★★★★ 单一 owner（speculator） | ★★ 双 owner（speculator + backend） | ★★★ view 由谁产生需明确，否则含糊 |
| 覆盖完整度（能否覆盖 L1–L10） | ★★★★ 可以，但靠自觉 | ★★★ 覆盖 backend 侧，speculator 侧仍缺 | ★★ 只覆盖漏斗侧（L1/L2/L3/L7/L8），漏 L4/L5/L6 + AR prefill |
| Graph-stable 可实现性 | ★★★ 需自建 persistent buffer | ★★★★ 复用 backend 既有 buffer | ★★★★ view 指向 persistent buffer 即可 |
| Per-group 扩展性 | ★★★★ 天然逐 group | ★★★ 取决于各 backend 实现 | ★★★★ 漏斗循环内天然逐 group |
| 新增 backend 成本（P6） | ★★★★ 零 | ★ 必须重写 window 逻辑 | ★★★★ 零 |
| CP/DCP 可扩展性 | ★★★ 需显式处理 | ★★★ 需各 backend 处理 | ★★★★ 漏斗内统一派生 local |
| 可测试性 | ★★★ 分散 | ★★ 需逐 backend | ★★★★ 可对 view 做单点契约测试 |
| 重复窗口风险（P8） | ★★★ 自建 epoch 必需 | ★★★★ capture/replay 同点产生，天然幂等 | ★★★★ 纯函数 + 来源断言 |
| 与上游 hook 演进耦合 | ★★★ 依赖 `_build_*` 签名 | ★★ 更深（builder 接口多变） | ★★★ 依赖 `build_attn_metadata` kwargs |
| 与 MRV1 数学可对拍性 | ★★★★ 直接复用 | ★★★ 分散后难对拍 | ★★★★ 单点对拍 |
| capture/replay 形状风险 | ★★ 需自行保证（多入口） | ★★★★ builder 内同点产生 | ★★★ 需 §5.4.1 的宽度不变式兜底 |
| 首期（DSpark-first）落地速度 | ★★ | ★ | ★★★★ |

补充一条贯穿三者的约束（不构成方案差异，但影响所有方案的可行性）：
**窗口表**不能**照搬 MRV1 的窄表**，因为 capture 期 metadata 走的是另一条模块符号
（`patch/.../patch_dflash_speculator.py:28`），且 SFA/DSA 的 `update_graph_params()` 是 no-op
（见 §5.4.1）。三者都因此需要「形状不变」这条兜底。

**读法**：B 在 graph 与「新 backend 成本」两项上占优，但改动面与双 ownership 是硬伤，
且它在 MRV2 当前阶段**不能独立完成任务**（speculator 侧的长度生产者无论如何都得改）。
C 在「单点、零 backend 改动、per-group、可测」上明显占优，但覆盖面不完整。
A 覆盖面完整但没有单点。

---

## 5. Recommended Architecture

### 5.1 决策

**以 C 作落地通道、以 A 作状态载体与 ownership、以 B 的「派生状态必须在 window 之后重建」作为规则。**

一句话：**speculator 持有 window plane；每个 draft forward 在一个明确的 window boundary
把 plane 刷成 `DraftAttentionView`；view 通过显式参数进入 Ascend 漏斗，
在 `AscendCommonAttentionMetadata` 构造前完成替换；speculator 侧所有非漏斗的长度生产者
一律改为从 view 派生；对「用显式索引而非 表+长度 表达可见性」的 backend，
view 另外提供一个后端无关的绝对 window interval，由该 backend 的索引派生处夹紧。**

（最后一条是 B 的必需子集：见 §5.4.2 / §5.4.3 的能力矩阵。
T1 档零 backend 改动；T2 档每 backend 一处，且该处**必须有**。）

不采用 B 的实现理由（明确记录）：
1. MRV2 speculator 侧的 L4/L5/L6 不在 backend 视野内，B 无法独立闭合；
2. 双 ownership 会制造「device 窗口化、CPU list 未窗口化」这类最难查的错；
3. hybrid multi-group × N backend 的组合数使改动面与验证成本失控。

保留 B 的两条洞见：
- 「derived state 必须由窗口化输入重建」——这正是 C 把替换放在
  `attn_utils.py:294-330` **之前**的理由；
- 「capture 与 replay 应在同一处产生 window 内容」——通过 P5 的 persistent buffer 制度落实。

### 5.2 组件与职责

```
DraftWindowPolicy     配置契约解析（method × model type -> decision）
                      ├─ enabled: bool
                      ├─ future_offset: int
                      ├─ scope: NONE | AR_PREFILL | AR_DECODE | PARALLEL_BLOCK
                      ├─ forced_off_reason: str | None   (MTP)
                      └─ soft_warnings: list[str]        (DSV4+DSpark, native-window 提示)

DraftWindowMath       纯 device、逐 group：
                      start[b]      = floor(clamp(lens[b] + future - W, 0) / b_g) * b_g
                      win_len[b]    = lens[b] - start[b]
                      start_block[b]= start[b] // b_g
                      needed[b]     = ceil(win_len[b] / b_g)
                      out[row, c]   = full[row, start_block[row] + c] if c < needed[row] and src < full_cols else 0
                      （c 遍历 [0, row_width_gid)，即与 full 同宽；§5.4.1）
                      逐 group 用该 group 的 b_g（P6）

DraftWindowPlane      speculator 持有，persistent：
                      tables[gid]: int32[cap_reqs, row_width_gid]   ← 与 full 表同 shape（§5.4.1）
                      seq_lens:    int32[cap_reqs]
                      seq_lens_cpu / seq_lens_cpu_upper_bound: int32 CPU[cap_reqs]
                      dcp_local_seq_lens: int32[cap_reqs]
                      epoch: int                      ← P2/P8 的来源断言
                      def refresh(full_tables, full_lens, full_cpu_lens, num_reqs, future) -> DraftAttentionView
                      def view() -> DraftAttentionView  ← 幂等读

DraftAttentionView    frozen:
                      block_tables: list[Tensor]（per group，均指向 plane 的 persistent buffer）
                      seq_lens / seq_lens_cpu / seq_lens_cpu_upper_bound / dcp_local_seq_lens
                      intervals: (start_pos[num_reqs], end_pos[num_reqs])   ← 后端无关的绝对窗口
                      max_seq_len_hint: int
                      epoch: int
```

**关键不变量实现方式**：
`refresh()` 只接受 `full_tables`（必须是 `BlockTables.input_block_tables` 的元素本身，
用 `data_ptr()` 比对断言）与 `full_lens`（draft exact device `seq_lens`），
并把 `epoch` 加一；`view()` 返回同一 epoch 的同一组 buffer 引用（P2/P8）。

### 5.3 Window boundary（唯一刷新点）

| 家族 | boundary 位置 | future_offset | 依据 |
| --- | --- | --- | --- |
| AR（Eagle/Eagle3）**decode** | 每步 `compute_slot_mappings()`（用 full table）**之后**、`_build_uniform_attn_metadata()`/`_build_attn_metadata()` **之前** | `K` = `num_speculative_steps` | MRV1 `llm_base_proposer.py:445`；AR 的 `seq_lens` 在该时刻是 corrected target + 已进入 KV 的 draft token 数（`vllm/.../autoregressive/speculator.py:335-344`） |
| AR **prefill（step 0）** | 见 §5.5（特例） | `K` | 同上 |
| DFlash / DFlash2 / DSpark | `propose()` 内**所有** per-group `prepare_dflash_inputs()`（用 full table 算 context/query slot）完成**之后**、`_build_uniform_attn_metadata()` **之前**（`vllm/.../dflash/speculator.py:380,424,453`） | `0` | MRV2 kernel 已把整块 query 折进 `seq_lens`（`worker/v2/spec_decode/dflash/speculator.py:287-290`），与 MRV1 同语义 |
| MTP | 无（policy 强制 off + warning） | — | `llm_base_proposer.py:423-429` |
| extract_hidden_states | 无（复用 Target metadata，无独立 draft read plane） | — | `vllm/.../extract_hidden_states.py` |

**最早边界**（不能早于）：所有需要 full state 的物理 slot 计算完成之后
（`compute_slot_mappings()` / `prepare_dflash_inputs()`）。
**最晚边界**（不能晚于）：任何 backend 派生状态开始之前（即进 `build_attn_metadata()` 之前）。

**AR 的 horizon 必须冻结在 proposal 级（P13）**——这条容易漏，且漏了会静默改变语义：

- MRV1 在 `_propose` 里**只 apply 一次**，`start` 由首步的 `seq_lens + K` 决定一次，
  之后每步只把**长度**递增（`llm_base_proposer.py:2073-2077` 的 `+1`、`:2134-2136`），
  裁剪过的 `self._block_table_clone` 全程不变 → **窗口起点冻结、可见长度从 `W-K` 长到约 `W`**。
- 若实现改成「每个 AR step 都用当前 exact end 重新算 start」（即 `future_offset=K` 逐步套用），
  则 `start_s = align(L_s + K - W)` 会随 `L_s` 一起右移 → **窗口每步向前滑动，可见长度恒为 `W-K`**，
  与 MRV1 语义不同，而且每步的表 origin 都变（graph 参数/缓冲区成本更高）。
- 正确形式：把「逻辑右边界」`horizon = L0 + K` 在 proposal 开始**冻结**，
  之后 `future_offset = horizon - L_s`（逐步从 K 递减到 1，末步为 0），
  于是 `L_s + future_offset = horizon` 恒定 ⟹ `start` 恒定。这就是 Codex 的
  「canonical start 与 AR proposal anchor」，也解释了为什么它的 `future_offset` 不是常数。

### 5.4 漏斗落地点（C 的通道）

在 `worker/v2/attn_utils.py:220` 的 `build_attn_metadata()` 增加一个**显式**可选参数：

```
build_attn_metadata(..., draft_window_view: DraftAttentionView | None = None)
```

在 `worker/v2/attn_utils.py:256` 之前（即任何 fallback 与派生之前）做替换：

| 原参数 | 有 view 时替换为 | 说明 |
| --- | --- | --- |
| `block_tables[i]` | `view.block_tables[i]` | per-group，见 `attn_utils.py:295` |
| `seq_lens` | `view.seq_lens` | 决定 `AscendCommonAttentionMetadata.seq_lens`（`attn_utils.py:314`） |
| `seq_lens_np`（→`seq_lens_cpu`） | `view.seq_lens_cpu.numpy()` | **同时消除 `attn_utils.py:256-258` 的 uniform fallback 陷阱** |
| `seq_lens_cpu_upper_bound` | `view.seq_lens_cpu_upper_bound` | 保持 exact ≤ upper |
| `dcp_local_seq_lens` | `view.dcp_local_seq_lens` | **必须**由「绝对区间前缀差」派生：`local(end) - local(start)`。**不可**用 windowed global 直接套 `get_dcp_local_seq_lens()`（即 `local(end - start)`）——该函数对 L 非线性（`vllm/v1/attention/backends/utils.py:1088-1133`：`local(L) = floor(floor(L/i)/d)*i + clip(L - floor(floor(L/i)/d)*d*i - r*i, 0, i)`），反例：`i=1,d=2,r=1` 时 `local(4)-local(1)=2`，而 `local(3)=1`。CPU 版（`attn_utils.py:265-273`）同理会继承此错误，必须一起改。 |
| `slot_mappings` | **不动** | P1 |
| `query_start_loc*` / `num_tokens*` / `positions` / `max_seq_len` | **不动** | P1；`max_seq_len` 作为容量上界保留 |

`draft_window_view` 的注入复用既有工厂：扩展
`build_draft_attn_metadata_factory()`（`worker/v2/attn_utils.py:1254-1281`）
增加 `draft_window_view=` 透传，AR / DSpark 的 override 已经在用它；
DFlash 的 live path 目前只用 `build_attn_metadata_wrapper()`
（`worker/v2/spec_decode/dflash/speculator.py:144`），需要同样加一层工厂或显式传参。

#### 5.4.1 决策：窗口表**保持与 full 表相同的形状**（宽度不变式）

**这是本设计最重要的一条实现决策。** MRV1 的做法是「窄表」：gather 成
`[max_num_reqs, window_blocks + 1]`（`spec_decode/utils.py:111-118`）。
MRV2 **不能**照搬窄表，理由是一条链路的三个事实：

1. **capture 期的 metadata 不由同一 scope 产生。** DFlash 的 capture 走
   `vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:55` 的模块符号，
   由 `patch_dflash_speculator.py:28` 在导入时绑定，**不经过**
   `build_attn_metadata_wrapper()`。因此 capture 时的表宽度无法自动跟随 replay 变成窄表。
2. **多个 backend 的 `update_graph_params()` 是 no-op。** SFA（`attention/sfa_v1.py:885-896`）
   与 DSA（`attention/dsa_v1.py` 的 `AscendDSAImpl.update_graph_params`）当前都是空实现，
   意味着这两条路径**不靠 graph 参数更新来换 pointer**——captured op 读的是
   **builder 自己持久 buffer 的地址**。既然 pointer 不能换，形状更必须一致。
3. **builder 会把 common 表复制进自己定长的 persistent buffer。**
   SFA 的 `SparseMLAMetadataState.prepare()` 把 common block table 换算到 operator page 粒度
   写进 `block_table_buffer`；如果源的列数变化，目标 buffer 的布局/形状就不再与 capture 时一致。

**做法**：`DraftWindowPlane` 的 per-group 表**与 `BlockTables.input_block_tables[gid]` 同 shape/dtype**：
- 列 `[0, needed)` ← `full[row, start_block + c]`
- 列 `[needed, row_width)` ← 显式写 0
- row `[num_reqs, num_reqs_padded)` ← 显式写 0

**代价与收益**：
- 代价：每步多写 `row_width - needed` 列的 0，多占 `[cap_reqs, row_width]` 的显存
  （例如 `row_width=1024`、`cap_reqs=256`、`num_groups=4`、int32 ≈ 4 MB，可接受）。
- 收益：**capture/replay、SFA/DSA 的 builder-owned buffer、`UpdatableGraph` 未注册参数
  三类形状风险一次性消失**；窗口对下游只表现为「内容不同、形状相同」，
  这也让 P5（地址稳定）与 P7（padding 清零）可以用最简单的形式证明。

**窄表作为后续优化**（不在首期）：若确实需要窄表，则必须同时做到
(a) capture 期的 `build_attn_metadata` 也被注入同一个 view（需要额外 hook
`patch_dflash_speculator.py` 绑定的那个模块符号），且 (b) SFA/DSA 的 builder
按窗口宽度定长分配其 persistent buffer。这两条都要逐 backend 验证，
不适合作为首期目标。

#### 5.4.2 关键限制：并非所有 backend 都用「表 + 长度」表达可见性

C 方案的前提是「backend 从 `block_table` + `seq_lens` 推出可见 KV」。
这个前提**对 GQA/MLA 成立，对 SFA/DSA 不成立**：

| backend | 可见性如何表达（已核实） | 窗口能否靠「裁剪表 + 缩短长度」实现 |
| --- | --- | --- |
| GQA / FIA | `block_table` + `actual_seq_lengths_kv`（`attention/attention_v1.py:316,386,822`） | ✅ 可以 |
| MLA | `decode.block_table` + `decode.seq_lens_list` / `actual_seq_lengths_kv`（`attention/mla_v1.py:512-513,1787`） | ✅ 可以 |
| SFA（sparse MLA / NoPE） | **显式 top-k 索引**：`ori_sparse_indices` + `ori_topk_length`；且该路径强制 `ori_mask_mode=0` / `ori_win_left=ori_win_right=-1`（`attention/sfa_v1.py:114-119`，注释写明「Only ori_mask_mode 4 may carry a bounded window on this product line」） | ⚠️ 需要改索引派生；native SWA 在这条路径**根本不生效** |
| DSA（causal） | `ori_mask_mode=4` + `ori_win_left=sliding_window-1` + `ori_block_table`（`attention/dsa_v1.py:952-955,1107,2255-2257`） | ✅ 可以（与 native band 取交集） |
| DSA（**non-causal DSpark**） | **显式可见 slot 索引** `ori_sparse_indices`，宽度 `window_size + num_speculative_tokens`，`start_pos = clamp(prefix_lens - window_size, 0)`（`attention/dsa_v1.py:448-461`、`:1108-1125`、`:2265-2270`） | ❌ **不可以**：op 读的是索引集合，不是表；必须改 `start_pos` 派生 |

另有一个 DCP 特有的陷阱：SFA-DCP 的 builder 会**在 build 期间临时把
`common_attn_metadata.block_table_tensor` 换成它自己派生的 replicated 视图、事后还原**
（`attention/context_parallel/sfa_cp.py:818-838`），其映射
（`attention/context_parallel/sfa_dcp_utils.py:66-80`）**假定列号 == 逻辑块号**。
一旦把窗口表做成「左移 + 右侧清零」，这个假定就不成立
（`BlockTable only owns the DCP-local physical layout`，`sfa_cp.py:601-611`）。

#### 5.4.3 决策：以「绝对 window interval」作为公共契约，按 backend 能力落地

为了让上面两类 backend 用同一份契约，`DraftWindowView` 除携带替换用的张量外，
必须同时携带**后端无关的语义表示**（这也是唯一能让 DSA 索引路径复用的形式）：

```
window_view.intervals: (start_pos[num_reqs], end_pos[num_reqs])   # 逻辑 token 绝对位置，[start, end)
其中 end_pos[b]   = full_lens[b] + future_offset
     start_pos[b] = floor(clamp(end_pos[b] - W, 0) / b_g) * b_g
```

落地分两档（**backend 能力矩阵**，由 `DraftWindowView` + `DraftWindowPolicy` 决定）：

| 档 | 适用 backend | 落地方式 | 改动面 |
| --- | --- | --- | --- |
| **T1（表 + 长度）** | GQA / MLA / DSA-causal | 漏斗内替换 `block_tables[i]` / `seq_lens` / `seq_lens_cpu` / upper / `dcp_local_seq_lens`（§5.4 的表） | 零 backend 改动 |
| **T2（索引派生）** | DSA-non-causal-DSpark、SFA sparse | 这些 builder 在派生索引时读 `window_view.intervals`，把自身公式里的 `start_pos` 从 `prefix_lens - native_window` 改成 `max(prefix_lens - native_window, interval_start)` | 每 backend 一处 |

**这也修正了 §4 的判断**：C 方案对 T1 档是「零 backend 改动」，
但对 T2 档必须新增一个**窄扩展点**（读 interval、夹紧自身 `start_pos`）——
即 B 方案「可见性属于 backend 能力」这一洞见在 T2 档是**必须**的，
只是不需要 B 那种「整条链路由 builder 负责」的全面下推。

#### 5.4.4 决策：捕获期 metadata 是否窗口化

三种可能：
- **W1（推荐）**：capture 用 **unwindowed** 的 dummy（全 0 表 + dummy 长度）构建形状，
  replay 用**同形状**的窗口表。依赖 §5.4.1 的宽度不变式。
  优点：不需要新增 capture 期 hook；dummy 数据本身 inert（全 0 表 → 窗口化后仍全 0）。
- **W2**：capture 也走窗口化（形状与窗口一致）。
  需要给 capture 路径单独注入 view；收益仅在被 §5.4.1 排除的窄表方案下才存在。
- **W3**：capture 用 window 宽度但内容为 dummy。与 W2 同风险。

首期取 **W1**。

### 5.5 AR first prefill 的特殊处理（必须显式决策）

现状（§1.6）：AR 第一个 draft step 在非 FULL 时直接复用 Target metadata/slot mappings，
FULL prefill 时也只在 `build_draft_attn_metadatas(is_draft_model_prefill=True)` 里
过滤 Target metadata。**这条路径上不存在 draft-scope metadata**，因此窗口无处安放。

三个选项：

| 选项 | 做法 | 代价 | 判断 |
| --- | --- | --- | --- |
| F1 | **首步不窗口化**（window 从第 1 个 draft step 起生效） | 功能打折：draft 的第一个（最关键的）token 仍看 full context | 若第一 token 主导 acceptance，收益被显著削弱；**不推荐** |
| F2 | 首步对 Target metadata 做 **draft-layer 视图替换**（逐 layer shallow copy + 换 table/length） | 必须证明不污染 Target（`metadata` 可能是同名对象、SFA/DSA 可能持 builder-owned buffer） | 风险高 |
| F3 | 首步**放弃复用**，改走漏斗构建 draft-scope metadata | 失去一次优化；需保证 FULL prefill 的 capture 也用同一条路径 | **推荐**，与 P3（隔离）一致，最可证明 |

推荐 F3，且**只在 window 启用时**切换（window 关闭时保留现有复用路径，避免无谓回归）。
需要注意：draft 侧的 `input_buffers.seq_lens` / `query_start_loc` 在
`prepare_prefill_inputs()`（`vllm/.../autoregressive/speculator.py:255-265`）
之后已经写好，具备构建 draft-scope metadata 的输入；MRV1 在首步也是用
「target 长度 + future_offset=K」算窗口，语义可对齐。

### 5.6 AR 的 length producer 改写（P4 的必做项）

在 window 启用时，把下列位置统一改为「从 view 派生」：

| 位置 | 现在 | 改为 |
| --- | --- | --- |
| `_calc_next_seq_lens_cpu()`（`autoregressive/speculator.py:815-822`） | `clamp(target_cpu + step)` | `windowed(clamp(target_cpu + step))`，即先得 full exact 再套窗口算术，padded 行写 0 |
| `_update_decode_attn_metadata()`（同文件 `:733-776`） | 直接写 `seq_lens_list` / `seq_lens_cpu` | 同上值来源；`seq_lens_list` 必须等于窗口化后的 CPU 向量 |
| `_init_decode_draft_attn_metadatas()` / `draft_seq_lens_cpus[step]`（同文件 `:103-109,719-729`） | Target CPU + step | 窗口化后写入**同一批 persistent buffer**（P5：`copy_`，不换引用） |
| `build_fia_params()`（同文件 `:778-813`） | `input_batch.seq_lens_np + step` | 同上值来源（这是 FULL + `UpdatableGraph` 路径的真实 kv 长度来源） |
| `_prepare_draft_dcp_metadata_inputs()`（`dspark/speculator.py:137-151`；AR 对应 `:509-518`） | Target CPU + step | 窗口化后、以**绝对区间前缀差**派生 DCP local（不是套 `get_dcp_local_seq_lens(windowed_len)`，见 §5.4） |

### 5.7 MTP / 其它方法的 contract 复刻

- MTP（含 Gemma4 / Step3.5 / multi-KV 变体，runtime 均归一为 `method="mtp"`）：
  `DraftWindowPolicy` 返回 `enabled=False, forced_off_reason="mtp_reuses_target_layers"`，
  在 speculator 初始化处 **warning 一次**（复刻 `llm_base_proposer.py:423-429` 的措辞语义）。
- DSpark + `deepseek_v4*` target：warning 一次，**继续启用**（复刻 `:430-435`）。
- `extract_hidden_states`：无独立 draft attention read plane → 不适用，静默（与 MRV1 一致）。
- 经 Ascend MRV2 factory 无法实例化的方法（`ngram` / `suffix` / `medusa` / `draft_model` /
  `mlp_speculator` / `custom_class`）：factory 本身 `NotImplementedError`
  （`worker/v2/spec_decode/__init__.py:72`），window 不可达 → 与 MRV1 的「静默未读取」不同，
  需在文档/CR 中明确写清（见 Q11）。

---

## 6. Failure Modes

按严重度排序。「静默正确性错误」一律最高优先级，因为它不会报错、只会让输出变差或读到别的请求的 KV。

| # | 失败模式 | 触发点（本设计相关的具体位置） | 后果 | 对策 |
| --- | --- | --- | --- | --- |
| F1 (P0) | **表已窗口化、长度仍 full** | 只改漏斗不改 L4/L5/L6；或 MLA 走 CPU 优先分支拿到 full `seq_lens_cpu` | kv_len 大于窗口 → 读 `[needed, max_window_blocks)` 列（已置 0）→ block id 0 → 读到 **cache 第 0 块**（可能是别的 request 或已释放块） | P4；漏斗内替换 `seq_lens_np`（消掉 `attn_utils.py:256-258` 的 fallback）；AR 侧改 L4/L5/L6 并用「长度闭包」UT 断言 |
| F2 (P0) | **长度已窗口、表未窗口化** | DSpark 的 per-group 覆盖顺序搞错（MRV1 正是为此在 group 内 apply，`llm_base_proposer.py:2588-2605`） | 读到窗口起点之前的旧块 | boundary 定义在「所有 full-table slot 计算之后、任何 backend 派生之前」（§5.3） |
| F3 (P0) | **原地改写共享 buffer** | 直接对 `BlockTables.input_block_tables[gid]` / `slot_mappings` 做 in-place 裁剪 | Target attention / 下一 step slot 计算 / graph replay 读到窗口表；worst case **写错物理 KV 位置** | P3；`refresh()` 只读输入 + 只写 plane 私有 buffer；用 `data_ptr()` 断言「输出 ≠ 共享 buffer」 |
| F4 (P0) | **window-of-window** | live `propose()` 已 build，FULL replay 前 `aclgraph.run_fullgraph()` 又 build（`dflash/aclgraph.py:86-98`；`autoregressive/aclgraph.py:132-152`） | 二次左移，仅 graph 模式复现 | P2/P8；`refresh()` 断言输入是 full table（来源）+ `epoch` 语义；UT 断言「连调两次结果相同」 |
| F5 (P0) | **FULL graph 里换引用而非 copy** | 每步 `metadata.block_tables = new_tensor` 之类 | capture 冻结旧地址 → eager 正确、FULL 静默读错 | P5；产物是 persistent buffer，每步只 `copy_`；沿用 `block_table.py:177-187` 的 dummy 同址制度 |
| F6 (P1) | **padding / stale tail** | plane buffer 未清 `[num_reqs, num_reqs_padded)`；未清 active 行 `[needed, max_window_blocks)`；gather 只覆盖 `[0, num_blocks)`（`block_table.py` gather kernel 行为） | 小 batch 复用大 batch 的旧 block id → 可能命中已重新分配的块 | P7；每步显式清零两处；UT 覆盖「batch 由大变小的连续两步」 |
| F7 (P1) | **假定所有 group block size 相同** | 复用 MRV1 的单一 `kernel_block_size`（`llm_base_proposer.py:406-408`） | 某些 group 列起点/列数错，multi-group DSpark 出现 layer 相关不一致 | P6；`max_window_blocks_g = ceil(W/b_g)+1` 逐 group 计算，plane 逐 group 分配 |
| F8 (P1) | **upper 当 exact / exact 当 upper** | L2 的 `target_upper + step` 被 backend 当 decode 精确长度；或反过来用 upper 去裁窗口 | tiling/plan 与真实范围不一致 → 越界或形状错 | 窗口必须由 **device exact** `seq_lens` 决定；upper 只作为上界并被 clamp；CPU exact 单独给 |
| F9 (P1) | **DCP/PCP local 用 full global 派生** | L7/L8/L9 | rank-local 可见范围超出窗口 | 在漏斗内先替换 global 再派生 local（§5.4）；DSpark 的 DCP helper 用窗口化输入 |
| F10 (P2) | **async 覆盖竞态** | 单一 plane buffer 在上一 step/kernel 尚未读完时被下一 step 覆盖 | 读到混合两 step 的数据 | 与既有 `input_block_tables` 同级的生命周期纪律；必要时按上游 `UvaBufferPool` 的 ≥2 slot 思路做两路 plane |
| F11 (P2) | **把 native SWA 当成本 feature 实现** | 用 `build_dspark_swa_indices()`（`attention/dsa_v1.py:420`）来"实现" `draft_window_size` | 语义错、owner 错、覆盖的 method 错 | P10；两者在同一坐标系上取交集；测试里对「只开 native SWA」与「只开 window」分别建基线 |
| F12 (P2) | **AR 首步污染 Target metadata** | 选 F2 且逐 layer copy 不彻底（SFA/DSA 持 builder-owned buffer） | Target verification / 下一步请求状态被污染 | 选 F3（首步改走漏斗），从根上避免 |
| F13 (P2) | **W 未校验** | `ascend_config.py:497` 只有类型，无 `gt=0` | `W=0` 或负值：`clamp(...)` 后 `start=0` → `windowed_len=seq_lens` → **静默无效**；`W < b` 时 `max_window_blocks=2` | 在 config 处补 `gt=0` 校验 + 建议下界；UT 覆盖 `W ∈ {0, -1, 1, b-1, b, b+1}` |
| F14 (P2) | **首期改动面失控** | 一次把 AR / DFlash / DFlash2 / DSpark 全铺开 | 组合爆炸，graph 回归难定位 | 分阶段（§10.4）；首期只 DSpark，与 MRV1 的 `test_dspark.py` 对拍 |
| F15 (P0) | **capture 与 replay 的表形状不一致**（若照搬 MRV1 窄表） | capture 走 `vllm/.../dflash/cudagraph.py:55`（由 `patch_dflash_speculator.py:28` 绑定，不在 `build_attn_metadata_wrapper` 作用域内），replay 走窗口表 | captured op 的 KV table 形状与 replay 输入不符；DSA/SFA 因 `update_graph_params()` 是 no-op 而无法靠参数更新兜底 → 形状错或读错 | §5.4.1 宽度不变式（窗口表与 full 表同 shape）；W1 捕获策略 |
| F16 (P1) | **窗口把 narrow 表写进 builder 定长 buffer** | SFA `SparseMLAMetadataState.prepare()` / DSA req metadata 的 persistent buffer 按 full 宽度定长 | 形状/布局错位 | 同上；并在 UT 中对 SFA/DSA 单独断言 buffer 布局不变 |
| F17 (P0) | **在 DSA-non-causal / SFA 上「只裁表」而可见性其实来自显式索引** | DSpark+DSA 非因果走 `ori_sparse_indices`（`attention/dsa_v1.py:1108-1125,2265-2270`）；SFA sparse 走 `ori_sparse_indices` + `ori_topk_length`（`attention/sfa_v1.py:198-219`） | **窗口完全无效**（op 不读表）；或更糟：只缩短了 `seq_lens` 而索引仍指向窗口外 → 越界/读错 | §5.4.2/§5.4.3 的能力矩阵：T2 档必须在索引派生处夹紧 `start_pos`；UT 里对这两条路径**必须**验证索引集合本身变短 |
| F18 (P1) | **窗口表列号不再等于逻辑块号，破坏 SFA-DCP 的 replicated 视图片射** | `sfa_cp.py:818-838` 临时换表、`sfa_dcp_utils.py:66-80` 按列号推 rank | 派生视图错位 → 读错 rank 的块 | SFA + DCP 组合走 T2 档（用 interval 夹紧 `local_key_lens` / `start_pos`），**不要**用列裁剪 |

---

## 7. Compatibility Matrix

### 7.1 Method × 窗口支持

| method | MRV1 行为（已核实） | MRV2 现状 | 目标：window support | apply boundary | `future_offset` | draft graph |
| --- | --- | --- | --- | --- | --- | --- |
| `eagle3` | 启用，公共 apply 点 | 无 | 启用 | AR prefill（F3）+ AR per-decode-step | `K` | eager / PIECEWISE / FULL |
| `eagle` | **代码路径同样启用**（条件只看 `method != "mtp"`，不是 `== "eagle3"`） | 无 | 启用（与 eagle3 同契约） | 同 eagle3 | `K` | 同 eagle3 |
| `dflash` | 启用 | 无 | 启用 | parallel block（per-group prepare 之后） | `0` | eager / FULL（`FULL_DECODE_ONLY`） |
| `dflash` + `DFlash2DraftModel` | 继承 DFlash | 无 | 启用（同 DFlash） | 同 DFlash | `0` | **Ascend 当前仅 eager**（`dflash2/speculator.py:121-139` 要求 `enforce_eager`，否则 `NotImplementedError`） |
| `dspark` | 启用（per-group apply） | 无 | **首期目标** | 同 DFlash（per-group 循环之后、metadata 之前） | `0`（Ascend kernel 已把 query 折进 `seq_lens`，`dflash/speculator.py:287-290`） | eager / FULL + DSA/SFA/DCP 派生状态 |
| `dspark` + `deepseek_v4*` target | warn 但启用 | 无 | 同 MRV1：warn 但启用 | 同 dspark | `0` | 同 dspark |
| `mtp`（含 Gemma4 / Step3.5 / multi-KV 变体） | warn + **ignore**（不构造 adapter） | 无（连 warning 都没有） | **warn + ignore**，且**不得**因继承 AR 基类而被动启用 | 不适用 | — | 现状不变 |
| `extract_hidden_states` | 不经过 base → 静默未读取 | 无 | 明确不适用（复用 Target metadata，无独立 draft read plane） | 不适用 | — | 强制 eager |
| `ngram` / `ngram_gpu` / `suffix` / `medusa` / `draft_model` / `mlp_speculator` / `custom_class` | MRV1：前者静默未读取；后两者 factory `ValueError` | Ascend MRV2 factory 直接 `NotImplementedError`（`worker/v2/spec_decode/__init__.py:72`） | window 不可达；**需在文档中写明与 MRV1 的差异** | 不适用 | — | — |

### 7.2 数据 × 是否可窗口化

| 数据 | 是否可窗口化 | 说明 |
| --- | --- | --- |
| Draft per-group attention block table | ✅ | 换成 plane 的 persistent window buffer |
| Draft exact device `seq_lens` | ✅ | 由 full exact 套窗口算术 |
| Draft CPU exact / upper | ✅ | 同上；upper 必须 ≥ exact |
| `dcp_local_seq_lens`（device/CPU） | ✅（派生） | 必须由**绝对区间前缀差**派生 `local(end)-local(start)`；**不是**把窗口长度套 `get_dcp_local_seq_lens()`（该函数非线性，见 §5.4） |
| `max_seq_len`（容量 scalar） | ❌ | 保持容量上界；不需要缩小 |
| `query_start_loc` / `num_tokens` / `positions` | ❌ | P1 |
| `slot_mapping` | ❌ | P1（真实 KV 写入地址） |
| `BlockTables.block_tables[*]`（authoritative） | ❌ | 真实分配 |
| Target 的任何状态 | ❌ | P3 |
| Backend 派生状态（FIA `seq_lens_list`、MLA `decode.*`） | ✅（重建） | **T1**：由窗口化输入自动重建（C 的落地位置保证） |
| DSA `start_pos` / `dspark_swa_indices`（**non-causal**）、SFA SMLA top-k plan | ⚠️（T2） | 这些 backend 的可见性来自**显式索引集合**，不是表+长度；必须由索引派生处读 `view.intervals` 夹紧 `start_pos`（§5.4.2/§5.4.3） |

### 7.3 配置契约

| 项 | MRV1 | 目标 MRV2 |
| --- | --- | --- |
| 读取位置 | `get_ascend_config().draft_window_size`（`llm_base_proposer.py:415`） | speculator 初始化时读取同一 singleton |
| 默认 | `None`（关闭） | 同 |
| 值域校验 | **仅类型**（`ascend_config.py:497`） | 建议补 `gt=0`（且 `W < 2*b_g` 时给提示） |
| MTP | warn + ignore | warn + ignore |
| DSpark + `deepseek_v4*` | warn + 启用 | 同 |
| window 关闭时 | 零开销、行为完全不变 | **同**（强约束：关闭路径不得引入任何额外 tensor/branch） |

---

## 8. Graph / Async Analysis

### 8.1 Capture / Replay 路径与窗口的接触点

| 路径 | 入口 | 窗口需要满足什么 |
| --- | --- | --- |
| Target FULL | `ModelAclGraphManager.run_fullgraph()`（`worker/v2/aclgraph_utils.py`） | **不接触**：window 不进入 Target scope |
| AR draft prefill（FULL） | `build_draft_attn_metadatas(is_draft_model_prefill=True)`（`autoregressive/speculator.py:654-684`）→ `_prepare_replicated_prefill_attn()` | 现有实现过滤 Target metadata；若选 F3 则此处必须改为构建 draft-scope metadata（**capture 与 replay 必须走同一实现**） |
| AR draft decode（FULL，merged multi-step） | `autoregressive/aclgraph.py:132-152` → `build_draft_attn_metadatas()` → `_init_decode_draft_attn_metadatas()`；之后 legacy `update_full_graph_params()` 或 `UpdatableGraph.resolve_tasks(SharedSource(fia_params))`（`aclgraph.py:196-208`） | 每个 step 的窗口长度都必须落在 **capture 时已存在的 persistent buffer** 里（`draft_seq_lens_cpus[step]` 这一制度，`autoregressive/speculator.py:103-109`），且 `build_fia_params()` 的 kv 列表必须窗口化 |
| DFlash/DSpark live | `dflash/speculator.py:144-162` → 上游 `propose()` → `_build_uniform_attn_metadata()`（`vllm/.../dflash/speculator.py:453`） | 此时所有 per-group physical slot 已算完（`:380`、`:424`），窗口安全 |
| DFlash/DSpark FULL replay | `dflash/aclgraph.py:86-98` **再次** `build_draft_attn_metadatas()`，再 `_graph_replay` / `_updatable_graph_replay` | 幂等（P8）；两路都要窗口化（legacy 走 metadata，UpdatableGraph 走 metadata 的 `ContextSource(draft_attn_metadatas[0])`，`aclgraph.py:134`） |
| Capture 期（DFlash/DSpark） | `DFlashCudaGraphManager.capture()`；metadata 由 `vllm/.../dflash/cudagraph.py:55` 的模块符号构建，符号由 `patch_dflash_speculator.py:28` 在导入时绑定，**绕过** `build_attn_metadata_wrapper()`；dummy 表来自 `BlockTables.get_dummy_block_tables()`（`block_table.py:177-187`） | 取 **W1**（§5.4.4）：capture 用 unwindowed dummy 定形状，replay 用**同 shape** 的窗口表。dummy 全 0 表在窗口化后的结果仍是全 0（inert），但本设计的 W1 选择连这一步都不依赖 |
| Capture 期（AR） | `autoregressive/speculator.py:348-390` 的 prefill / decode capture（各自包 `build_attn_metadata_wrapper()`） | 与 DFlash 同理：形状必须与 replay 的窗口表一致 |

（Target 侧的 capture 见本表第 1 行：`ModelAclGraphManager` 由
`worker/v2/model_runner.py:917-946` 装入，窗口不进入其 scope。）

### 8.2 地址稳定性（P5）的三条硬规则

1. **产物是 persistent buffer**：plane 在 speculator 初始化时按 `max_num_reqs_padded` 与
   `max_window_blocks_g` 分配；capture 与 replay 引用同一 storage。
2. **每步只 `copy_`**：`refresh()` 内部把 gather 结果 `copy_` 进 plane buffer
   （沿用 MRV1 的做法，`spec_decode/utils.py:147`；以及
   `block_table.py:177-187`「必须返回同一 persistent tensor 地址」的制度）。
3. **不换 metadata 引用**：给漏斗的 `draft_window_view` 里的 tensor 本身就是 plane buffer 的
   slice/view；每步内容变、地址不变。若某 backend 走 `UpdatableGraph` 注册参数（GQA 家族，
   `use_updatable_graph()` 只对 `AscendAttentionBackend` 为真），仍需保证未注册的 tensor 地址稳定。

**注意**：`ACLGraphWrapper` 的 debug 断言只检查 positional tensor args
（`compilation/acl_graph.py`），「通过 metadata / forward context 引用到的 tensor」
同样在 capture 时被算子记录——不能被断言出来，所以不能以「debug 没报错」作为地址安全的证据。

**哪条路径能换 pointer，哪条不能**（决定「必须靠 `copy_` 还是可以靠 graph param 更新」）：

| backend 家族 | replay 参数更新机制 | 窗口能否换 pointer |
| --- | --- | --- |
| GQA / FIA（`AscendAttentionBackend`） | `use_updatable_graph()` 只为它返回 true → `UpdatableGraph`；legacy `update_graph_params()` 直接 `NotImplementedError`（`attention/attention_v1.py:572-581`） | 可以（参数在 registered task kwargs/provider 里） |
| MLA | legacy `update_graph_params()`，从本轮 metadata 取 `block_table` / `seq_lens_list` / `actual_seq_lengths_q` 重建算子参数（`attention/mla_v1.py:887-1004`） | 可以（但 pointer 的 lifetime 必须覆盖 graph task update） |
| SFA | `update_graph_params()` 当前 **no-op**（`attention/sfa_v1.py:885-896`） | **不可以**：captured op 读 builder-owned persistent buffer → 必须「内容变、地址不变、形状不变」 |
| DSA | `AscendDSAImpl.update_graph_params()` 当前 **no-op** | 同上 |

这张表就是 §5.4.1「宽度不变式」的直接依据：SFA/DSA 无法换 pointer，
所以窗口表必须与 capture 时**同址同形**，唯一安全的做法是把窗口内容 `copy_`
进一个与 full 表同 shape 的 persistent buffer。

### 8.3 重复窗口（P8）的具体防线

```
refresh(full_tables) 前置断言：
    for gid: full_tables[gid].data_ptr() == block_tables.input_block_tables[gid].data_ptr()
    （或在 AR 的 PCP 分支下 == PCPManager 的 local persistent table）
    seq_lens.data_ptr() == input_buffers.seq_lens.data_ptr()
输出断言：
    所有 plane buffer 的 data_ptr 不属于 {input_block_tables[*], slot_mappings}
epoch：
    plane.epoch += 1；view 携带 epoch；单步内多次 refresh 得到相同值（幂等）
```

### 8.4 Async 生命周期

现有 MRV2 已经把 async 的三类并发处理好了，窗口只需要**跟随同一套纪律**：

| 既有机制 | 位置 | 窗口的对应做法 |
| --- | --- | --- |
| Target CPU exact mirror 等待上一轮 D2H correction | `worker/v2/model_runner.py:818-839` | 窗口不新增 D2H；窗口输入只用**已经就绪**的 draft device `seq_lens` 与 CPU mirror |
| optimistic `seq_lens_cpu_upper_bound` 与 device exact 的漂移 | 上游 contract（`vllm/v1/attention/backend.py` 的 upper-bound 语义） | 窗口由 **device exact** 决定；upper 只做上界。若某 backend 只拿到 upper，必须证明它只用于 capacity/plan |
| `UvaBufferPool` ≥2 轮转 slot，要求复用前 reader 已 retire | `vllm/v1/worker/gpu/buffer_utils.py` | 若实测存在多 in-flight step，plane 需要两路 slot（首期可先用单路并在设计里预留接口） |
| ACL graph 的 `update_stream` / stream wait | `worker/v2/spec_decode/dflash/aclgraph.py:100-138`、`autoregressive/aclgraph.py:154-208` | 窗口刷新必须在同一 stream 语义下早于 replay 消费；**不**依赖 Python 语句顺序推断设备生效时刻 |

**明确不采用**：隐式全局 / contextvar 传递「当前窗口」。理由：多个 speculator 实例、
DP 多实例、async 多 step 都会让隐式上下文串味；P11 要求显式参数。

---

## 9. Extension Analysis（Week4：Flashcomm / SP / DSA-CP / Async Scheduling）

设计对 Week4 组合的**预留**与**待证**：

1. **Flashcomm / SP（序列并行）— 已核实：不改变 block table 布局**
   - Flashcomm 在 Ascend 上就是 **SP-MoE 开关**（`ascend_config.py:639-657`：
     「FlashComm remains the SP MoE switch on Ascend」），
     `enable_sp()` 返回 `use_sequence_parallel_moe`（`utils.py:916-928`），
     在 SFA 里只被赋值一次、没有后续用它改 block table 的分支（`attention/sfa_v1.py:869`）。
   - **但它与 DSA-CP 是绑定的**：DSA-CP 要求 SP-MoE 打开，否则自动关闭
     （`ascend_config.py:694-698`），且 DSA-CP 打开时会自动打开 Flashcomm（同文件 `:641-657`）。
   - 对本 feature 的含义：SP/Flashcomm 本身不需要特殊处理；
     真正的坑在它带出来的 DSA-CP（下一条）。

2. **DSA-CP / DCP（含 `cp_kv_cache_interleave_size`）**
   - **DCP**（`decode_context_parallel_size`）是真正的 KV 分片：
     slot mapping kernel 按 `cp_size/cp_rank/cp_interleave` 把绝对位置映射到 rank-local 槽位
     （`vllm/v1/worker/gpu/block_table.py:326-339`，Ascend 复用并传参
     `worker/v2/block_table.py:105-108`），local 长度由 `get_dcp_local_seq_lens` 从 global 派生
     （Ascend 调用点 `worker/v2/attn_utils.py:266-273`）。
     → 设计上与 §5.4 一致：**先把 global 替换成窗口化值，再派生 local**，即可自动正确。
   - **DSA-CP** 另有一层：它把 token 流按 TP rank 切成 contiguous slice
     （`attention/context_parallel/dsa_cp.py:1133-1138,1166-1168`），
     block table **不**重排，只重算 query/local 长度；
     它与 PCP 互斥（`attention/dsa_v1.py:259-260`：「Legacy DSACP and PCP cannot be enabled at the same time.」）。
     → 窗口仍作用在 global 语义上，但要确认 DSA-CP 的 local metadata cache
     （`dsa_cp.py:931-947` 的 `cpu_cache`）在窗口化输入进来后会重建。
   - **SFA-DCP** 是最难的一处：indexer cache 复制、SFA KV 保持 DCP-local、
     builder 按需派生 **replicated** block table view（`sfa_cp.py:601-611,818-838`、
     `sfa_dcp_utils.py:66-80`），其映射假定「列号 == 逻辑块号」。
     → 该组合必须走 **T2 档**（§5.4.3），不能用列裁剪。这是 F18。

3. **Async Scheduling**
   - 现状：`optimistic_seq_lens_cpu` 假设 draft 全接受，需要 D2H 修正
     （`worker/v2/model_runner.py:818-839`）。
   - 设计：窗口的窗口末端必须由 **device exact** `seq_lens` 决定（P4/F8），
     upper 只作为上界。这样即使 CPU mirror 乐观，窗口也不会读越界。
   - 待核实：Q4（`seq_lens_cpu_upper_bound` 在 draft 路径上究竟被哪些 backend 当 exact 用）。

4. **PCP / replicated PCP**
   - 现状：Ascend 侧 PCP spec decode **恒为 replicated**——
     `AscendPCPManager.prepare_draft_prefill` 是显式 no-op（`worker/v2/pcp_manager.py:383-392`，
     docstring 写着「Ascend PCP spec decode is always replicated, so skip the partition」），
     而 `disable_target_pcp_for_replicated_draft()`（`spec_decode/pcp_utils.py:24-45`）
     在 `propose()` 期间把 PCP manager 从 model_state 上摘掉。
     因此 **draft 看到的是 global batch / global table**——这对窗口是好消息（窗口作用在 global 语义上）。
   - 但 AR 仍会在 PCP 分支**再次** `gather_block_tables()`（`vllm/.../autoregressive/speculator.py:329-332`），
     Ascend 的 `_prepare_replicated_prefill_attn()` 也会重算 slot 并重建 metadata
     （`worker/v2/spec_decode/autoregressive/speculator.py:189-238`）。
   - 设计：window boundary 必须定义在「最后一次 full-table gather **之后**」，
     否则 view 会被后续 re-gather 变成 stale。
   - 待核实：Q8。

7. **310P**
   - 现状：310P 有独立的 `AscendMTPSpeculator310`
     （`_310p/worker/v2/spec_decode/mtp_speculator.py`，由 `patch_spec_decode_310.py:39-63` 选中），
     自带 host 侧 slot mapping 与 per-step decode graph，并且**同样有**
     `_calc_next_seq_lens_cpu`（同文件 `:146`）这一 length producer。
   - 建议：**首期不在 310P 上启用 window**（`DraftWindowPolicy` 显式返回 disabled + 一条 info/warning），
     因为它的 graph/length 路径与 800I/A2 分支不同，需要单独验证。
   - 待核实：Q16。

5. **Hybrid KV cache（multi-group，不同 block size / causality）**
   - 设计已按 per-group 处理（P6/F7）。DFlash/DSpark 只对
     `draft_kv_cache_group_ids` 里的 group 做 attention，但 `BlockTables` 含全部 group
     （`dflash/speculator.py:94-99` 的 `_context_slot_mappings` 只按 draft group 分配）。
   - 待核实：Q5。

6. **PP / EPLB / 其它**
   - speculator 只在最后一个 PP rank 创建（`worker/v2/model_runner.py:150-164`）；
     窗口是纯 per-step 张量变换，与 PP 正交。

---

## 10. Test Strategy

### 10.1 分层

**T1 — 数学等价性（对拍 MRV1）**
- 用与 MRV1 `SlidingWindowAdapter` UT 相同的输入（`tests/ut/spec_decode/test_eagle_proposer.py:311-330`、
  `tests/ut/spec_decode/test_utils.py:192`）逐位对拍：`start_tokens` / `windowed_len` /
  `needed` / windowed table / zero padding。
- 边界矩阵：`seq_len ∈ {0, W-1, W, W+1, W+b, 2W}`、`b ∈ {16, 64, 128}`、
  `W ∈ {1, b-1, b, b+1, 2b}`、`future_offset ∈ {0, K}`。
- 断言：`windowed_len ≤ W + b - 1`；`needed ≤ max_window_blocks`。

**T2 — Policy resolver 契约**
- `mtp` → disabled + 产生 warning（断言 warning 文案关键字）；
- `dspark` + `deepseek_v4*` target → enabled + warning；
- `eagle` / `eagle3` / `dflash` / `dflash2` → enabled + `future_offset` 正确；
- `extract_hidden_states` → 明确 not-applicable；
- window 关闭时 → **任何路径都不分配 plane**（断言不新增 tensor，守 §7.3 的强约束）。

**T3 — 漏斗替换契约（C 的核心）**
- 构造 fake `AscendCommonAttentionMetadata` 输入，断言：
  - 有 view 时 `block_tables[i]` / `seq_lens` / `seq_lens_cpu` / `seq_lens_cpu_upper_bound` /
    `dcp_local_seq_lens` 全被替换；
  - `slot_mappings` / `query_start_loc*` / `positions` / `max_seq_len` **完全未变**（P1）；
  - `dcp_local_seq_lens_cpu` 由**绝对区间前缀差**派生（`local(end)-local(start)`），不是把窗口长度套 `get_dcp_local_seq_lens()`（该函数非线性，见 §5.4；F9）；
  - 无 view 时行为与改动前**逐位一致**（回归护栏）。
- **长度闭包断言**（防 F1）：构造一个「窗口应生效」的 request，断言所有 backend 实际消费的
  kv 长度（FIA `actual_seq_lengths_kv` / MLA `decode.seq_lens_list` /
  DSA `seq_lens` / SFA `seq_lens`）**全部 ≤ windowed_len**。
- **可见集合断言（T2 档，防 F17）**：对 DSA-non-causal-DSpark 与 SFA sparse 两条路径，
  断言**派生索引集合本身**（`dspark_swa_indices` / `ori_sparse_indices`）的所有设备
  都落在 `[start_pos, end_pos)` 内——只断言长度是不够的，因为这些 op 不读 block table。

**T4 — 幂等与来源（防 F4）**
- 同一步内连续调用两次 refresh（模拟 live + graph manager rebuild），断言两次 view 逐位相同；
- 传入非 full table（例如传入上一次的 window buffer）时断言报错或返回相同结果（取决于实现的
  断言强度）；`epoch` 单调。

**T5 — Padding / stale（防 F6）**
- 连续两步：`num_reqs` 由 8 → 3，断言 plane 的 `[3, 8)` 行全 0、`[needed, max_window_blocks)` 列全 0；
- `num_reqs_padded` 的 graph 形状下，padded 行的 table 全 0、length 为 0。

**T6 — Per-group（防 F7）**
- 构造两个 group，`b = 64` 与 `b = 128`，断言各自 `start_block` / `max_window_blocks` 独立正确；
- DSpark 的 DSA group + GQA group 混合时，断言两组各自一致。

**T7 — 隔离（防 F3/F12）**
- 快照 Target 侧的 `input_block_tables` / `slot_mappings` / `attn_metadata`（对象 identity + 内容），
  跑一次带 window 的 draft propose，断言 Target 侧**逐位不变**；
- AR 首步（F3 方案）断言 draft 用的 metadata **不是** Target 的同一对象。

**T8 — Graph**
- 对 FULL capture + 多个 batch descriptor 连续 replay，断言每次 replay 的 kv 长度随 step 正确
  （不是 capture 时的旧值）；
- 分别覆盖 legacy `update_full_graph_params` 与 `UpdatableGraph.resolve_tasks` 两条路径
  （GQA 家族走 UpdatableGraph；MLA 走 legacy graph param update）；
- 覆盖 SFA / DSA 的 `update_graph_params()` no-op 路径（`attention/sfa_v1.py`、`attention/dsa_v1.py`），
  确认窗口化派生 buffer 由 builder 自己承载；
- capture 用 dummy table（全 0）跑通无异常。

**T9 — Async**
- async scheduling 打开时，断言窗口末端跟 device exact 走（构造 upper > exact 的场景，
  断言不会按 upper 读越界）；
- 连续多 step 无数据竞争（复用既有 `UvaBufferPool` 相关 UT 的思路）。

**T10 — E2E**
- 与 MRV1 同配置对拍：`draft_window_size=512` 下 Eagle3（对齐
  `tests/e2e/pull_request/two_card/spec_decode/test_spec_decode.py:370-410`）与 DSpark
  （对齐 `tests/e2e/pull_request/one_card/spec_decode/test_dspark.py:80-142`）的
  **mean acceptance length** 与输出一致性；
- MRV2 专用：`tests/e2e/pull_request/*/model_runner_v2/spec_decode/` 下的
  DSpark / DFlash / Eagle3 / MTP 用例加 window 变体；
- contract 用例：`mtp` + `draft_window_size` → 期望 warning 且**行为与不开 window 逐位一致**；
  `dspark` + `deepseek_v4*` → 期望 warning 且**确实启用**（可通过 acceptance 变化或断言内部状态）；
- native SWA 叠加：同一 draft 分别跑「只开 native SWA」「只开 window ≥ native」
  「只开 window < native」，断言第三种 acceptance 下降（复现文档口径，
  `docs/source/user_guide/feature_guide/speculative_decoding.md:515-522`）。

**T11 — 性能**
- 断言窗口路径不新增 D2H（检查 `_calc_next_seq_lens_cpu` 之类位置是否引入新的
  `.cpu()` / `.item()` / `.tolist()` 频次）；
- 量化 draft 侧 KV read 的下降（窗口应减少 FIA 的 kv_len）。

### 10.2 建议的测试文件布局

```
tests/ut/spec_decode/
  test_draft_window_math.py          # T1、T6（纯数学 + 逐 group）
  test_draft_window_policy.py        # T2
  test_draft_window_metadata_v2.py   # T3、T4（漏斗替换 + 幂等）
  test_draft_window_isolation.py     # T7
  test_draft_window_graph.py         # T8
  test_draft_window_padding.py       # T5
tests/e2e/pull_request/one_card/model_runner_v2/spec_decode/
  test_qwen3_8b_dspark_window.py     # T10（首期）
tests/e2e/pull_request/two_card/model_runner_v2/spec_decode/
  test_qwen3_5_eagle3_window.py      # T10
```

### 10.3 验收门槛（首期 DSpark）

1. `test_dspark.py` 的 MRV1 window 用例与 MRV2 新用例在相同配置下 acceptance 差异 < 阈值；
2. T4 幂等、T7 隔离、T8 graph 三条同时通过——这三条是最容易在真实回归里出问题的；
3. window 关闭时，现有 MRV2 spec decode 测试**全部逐位不变**。

### 10.4 分阶段建议

| 阶段 | 范围 | 交付 |
| --- | --- | --- |
| S1 | `DraftWindowPolicy` + `DraftWindowMath` + 纯 UT（T1/T2，不接入 runtime） | 可与 MRV1 对拍的数学 |
| S2 | `DraftWindowPlane` + 漏斗替换（T3/T5/T7），先只接 DSpark eager | DSpark eager 端到端 |
| S3 | AR 家族（含 F3 首步改造、L4/L5/L6 改写）+ T4/T6 | Eagle/Eagle3 |
| S4 | Graph（T8）+ async（T9） | FULL 覆盖 |
| S5 | DFlash / DFlash2、E2E 对拍与性能（T10/T11） | 全 method |

---

## 11. Questions that must be verified in source before implementation

> 编号 Q1–Q16。每一条都给出「在哪里看」与「为什么它决定设计」。

**Q1 — `seq_lens_cpu` 在 draft 路径上到底是 exact 还是 fallback？**
在 MRV2 draft 漏斗里，`seq_lens_np` 普遍为 `None`
（`worker/v2/spec_decode/autoregressive/speculator.py:595-599`、
`worker/v2/spec_decode/dspark/speculator.py:345-371` 都未传），
因此 `attn_utils.py:256-260` 会填 `np.full(num_reqs, max_seq_len)`。
但 MLA builder 是 **CPU 优先**（`attention/mla_v1.py:504-505`）。
→ 必须确认：MLA draft layer 实际拿到的 `seq_lens` 是 AR 事后 `copy_` 进去的值
（`autoregressive/speculator.py:776`）还是 fallback；DFlash/DSpark 是否有等价的事后修正。
**为什么决定设计**：如果是 fallback，窗口必须无条件注入真实 `seq_lens_cpu`（§5.4 的替换项）；
如果没有事后修正，那么这是**现存缺陷**，要在本 feature 里一并修。

**Q2 — `_seq_lens_cpu` 在 MRV2 是否有生产者？**
`attention/utils.py:278` 保留字段、`_select_seq_lens()` 注释称其「always available」
（`attention/utils.py:561-570`），但 MRV2 的漏斗（`worker/v2/attn_utils.py:309-330`）
没有赋值。仓库内 `_seq_lens_cpu=` 的赋值点都在 MRV1 / MRV1 proposer。
→ 确认 MRV2 是否真的全程为 `None`。
**为什么决定设计**：决定窗口是否需要同时填 `_seq_lens_cpu`；也决定 backend 的
「优先 CPU」分支在 MRV2 是否等于「优先 fallback」。

**Q3 — DSpark + GLM 的 CPU 分支拿的是哪个向量？**
`_select_seq_lens()` 对 `use_dspark() and _is_glm_model()` **保留 CPU**
（`attention/utils.py:585`），而 DSpark 的 draft `seq_lens_cpu` 来源是
`DCPManager.prepare_draft_dcp_metadata_inputs(target_seq_lens_cpu=...)`
（`dspark/speculator.py:145`），非 DCP 时该 helper 直接返回 `None`（同文件 `:141-142`）。
→ 必须确认非 DCP 的 DSpark+GLM 到底读到什么长度。
**为什么决定设计**：这正是 F1（表窗口化、长度 full）最可能发生的组合。

**Q4 — `seq_lens_cpu_upper_bound` 在 draft 路径被谁当 exact 用？**
上游 `_build_attn_metadata()` 传 `target_upper + step`
（`vllm/.../speculator.py:326-334`），Ascend 漏斗原样转发（`attn_utils.py:313`）。
→ 逐 backend 确认它是 capacity/plan 还是真实长度。
**为什么决定设计**：决定窗口是否需要同时产出 windowed upper，
以及 async 下窗口末端由 exact 决定这一条是否足够。

**Q5 — 目标 DSpark draft 的实际 active backend 集合与 per-group block size？**
是 GQA / MLA / SFA / DSA 中的哪些；各组 `blocks_per_kv_block = block_size // kernel_block_size`
是否相等（`vllm/v1/worker/gpu/block_table.py` 的 `append_block_ids` 展开逻辑）。
**为什么决定设计**：P6/F7 的实现方式；以及窗口列数是否需要 per-group 形状。

**Q6 — MRV2 DSpark 的 DSA `dspark_swa_indices` 与窗口的叠加点在哪？**
`attention/dsa_v1.py:420-501` 用 `hf_config.sliding_window` 与 `num_speculative_tokens`
从 block table / query layout / seq_lens 派生 indices，并写 builder-owned persistent buffer
（`:600-652`），且 non-causal DSpark 分支每步重建（`:1105-1125`）。
→ 确认在给了窗口化 table/length 之后，它是否会正确重建（预期会，因为每步重建）。
**为什么决定设计**：决定是否需要在 DSA 侧额外改动，还是「零 backend 改动」成立。

**Q7 — FULL prefill 的 draft metadata 来源（F3 的可行性）**
`build_draft_attn_metadatas(is_draft_model_prefill=True)`
（`autoregressive/speculator.py:654-684`）→ `_prepare_replicated_prefill_attn()`
（同文件 `:189-238`）的具体行为：它是否**总是**基于 Target metadata？
若改为 F3，capture 与 replay 能否走同一条新路径（capture 用的是
`model_capture_wrapper` / `_prepare_..._to_capture` 那一套）。
**为什么决定设计**：AR 首步是 F1/F2/F3 三选一的唯一依据。

**Q8 — PCP / replicated PCP 下 window boundary 是否被 re-gather 覆盖？**
`vllm/.../autoregressive/speculator.py:329-332` 的 prefill 后 re-gather、
`worker/v2/spec_decode/autoregressive/speculator.py:189-238` 的 replicated prefill、
以及 `worker/v2/pcp_manager.py` 的 local persistent table。
→ 确认 draft 侧 attention 用的是 global 还是 PCP-local table。
**为什么决定设计**：boundary 的「最早不能早过」边界；以及 plane 的表宽度应对齐哪一套 layout。

**Q9 — DSA-CP 的 local metadata cache 是否会缓存 full-state 结果？**
`attention/context_parallel/dsa_cp.py:390-398,513-514,633-644,931-947` 有
`_build_local_token_metadata` 与 `cpu_cache`。
→ 确认窗口化输入进入后 cache 是否失效/重建。
**为什么决定设计**：Week4 的 CP 组合正确性；F9 的验证点。
（注：Flashcomm/SP 本身已核实**不**改 block table 布局，见 §9.1；真正的风险来自 DSA-CP。）

**Q10 — T2 档到底有几个 backend / 几条路径？**
需要在**目标模型**上确认：DSpark 的 draft layer 走 DSA 时 `cad.causal` 的实际取值
（MRV1 从 `model.get_draft_attn_causal()[0]` 取，`dspark_proposer.py:343-347`）；
若为 non-causal，则 `attention/dsa_v1.py:1108-1125` 的 `dspark_swa_indices` 是唯一可见性来源，
窗口必须改那里；若为 causal，则表+长度（T1）就够。
另外确认 draft 是否可能落到 SFA（sparse MLA）路径。
**为什么决定设计**：决定首期 DSpark 的工作量是「漏斗一处」还是「漏斗 + DSA 索引一处」，
也决定 F17 的风险等级。

**Q11 — 非 base-proposer 方法收到 `draft_window_size` 时，正式行为是什么？**
MRV1 是「静默未读取」（`ngram`/`suffix`/`medusa`），`mlp_speculator`/`custom_class`
在 Ascend factory 直接报错；MRV2 则全部 `NotImplementedError`
（`worker/v2/spec_decode/__init__.py:72`）。
→ 需要 feature owner 决定：静默、warning、还是配置错误。
**为什么决定设计**：P9 的落地形态；也是 compatibility matrix 的一列。

**Q12 — `draft_window_size <= 0` 的正式校验规则？**
`ascend_config.py:497` 只有类型注解（UT 只验证了字符串 `"4096"` 的转换，
`tests/ut/test_ascend_config.py:1351-1358`）。
**为什么决定设计**：F13；也决定是否把校验从 proposer 上移到 config。

**Q13 — `eagle`（非 eagle3）与 `draft_model` 是否正式属于支持集合？**
MRV1 的构造条件是 `method != "mtp"`（`llm_base_proposer.py:437`），
所以 `eagle` 与 `draft_model` **事实上**都会启用窗口，但文档与专项测试只覆盖 eagle3/dspark
（`docs/.../speculative_kv_sliding_window.md:20`、`:89-99`）。
→ 需要确认这是有意的还是条件过宽。
**为什么决定设计**：compatibility matrix 的「支持集合」定义。

**Q14 — DSpark 非 causal（`cad.causal = False`）与窗口的组合语义？**
`dspark_proposer.py:343-347` 从模型取 `get_draft_attn_causal()[0]`。
**为什么决定设计**：非 causal 下「窗口右端」是否还等于序列尾；影响窗口算术的 upper 端。

**Q15 — AR 的 `advance_draft_positions` 变体（Gemma4 类）在 Ascend MRV2 是否可达？**
Ascend factory 把 Gemma4/Step3.5 排除出普通 MTP 后落到 `AscendEagleSpeculator`
（`worker/v2/spec_decode/__init__.py:58-71`），没有实例化上游 `Gemma4Speculator`。
**为什么决定设计**：若可达，`seq_lens` 的推进规则不同，窗口的 full length 来源也随之不同。

**Q16 — 现有 UT 是否覆盖「batch 由大变小 / seq 由长变短 / FULL 连续 replay」的 stale 场景？**
目前 `tests/ut/spec_decode/` 下有 `test_dspark_graph_contract.py`、
`test_eagle_aclgraph_source_regression.py` 等契约测试，但需确认覆盖度。
**为什么决定设计**：F6 的回归护栏是否存在；没有就要在本 feature 里补。

**Q17 — capture 期的 KV table 形状究竟由谁决定，能否与 replay 不同？**
DFlash capture 的 metadata 由 `vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:55`
的模块符号构建，该符号在导入时被 `patch/.../patch_dflash_speculator.py:28` 直接绑定，
**不经过** `build_attn_metadata_wrapper()`（后者只替换
`vllm.v1.worker.gpu.spec_decode.speculator` 模块，`worker/v2/attn_utils.py:1240-1251`）。
→ 必须确认：capture 时传给 FIA/graph 的 `block_table` 形状与 replay 时
（窄表 vs 宽表）不同会怎样；以及 `DFlashCudaGraphManager.capture()` 里
每个 descriptor 用的是哪一份 `input_block_tables`。
**为什么决定设计**：这是 §5.4.1（宽度不变式）与 §5.4.4（W1/W2）的唯一依据。

**Q18 — SFA / DSA 的窗口化派生数据由哪块 persistent buffer 承载？**
两个 backend 的 `update_graph_params()` 都是 no-op，
意味着 captured op 读的是 builder-owned persistent storage
（SFA：`SparseMLAMetadataState.block_table_buffer` / `metadata_buffer` / `length_buffer`；
DSA：`spec_sas_metadata[step]`、`dspark_swa_indices_buffer`）。
→ 确认这些 buffer 在**每次 `build()`**（含 replay 前那次）都会被当前输入重写，
以及它们的形状是否按 full 宽度定长。
**为什么决定设计**：F15/F16；也是「零 backend 改动」能否成立的关键。

**Q19 — 310P 是否纳入本 feature 的 scope？**
`AscendMTPSpeculator310`（`_310p/worker/v2/spec_decode/mtp_speculator.py:37-259`）
有独立的 host slot mapping 与 `_calc_next_seq_lens_cpu`（同文件 `:146`）。
**为什么决定设计**：决定 `DraftWindowPolicy` 是否需要一条 310P 的 disabled 分支。

**Q20 — draft 侧 `seq_lens` 的「绝对值 vs 窗口相对值」在 FIA 里到底按哪种理解？**
MRV1 之所以能「裁剪表 + 同步缩短 `actual_seq_lengths_kv`」而仍正确，
说明 FIA 在 paged + 无 atten_mask（`sparse_mode=3`）下按**窗口相对坐标**解释 KV 位置。
→ 在 Ascend 的 FIA 实现上确认这一点（尤其是 `sparse_mode=4` 的 native SWA band
与窗口叠加时 band 的基准是窗口长度还是绝对长度）。
**为什么决定设计**：F11（native SWA 叠加语义）与 §7.1 的「交集」论断。

---

## 附录 A：本设计的「最小可证明」主张清单

如果实现只做到下面 7 条，feature 就是正确的；其余都是实现细节。

1. 任何时刻，Draft Attention 消费的 KV 都落在绝对区间 `[start_pos[b], end_pos[b])` 内：
   - **T1 档（GQA/MLA/DSA-causal）**：KV 长度 ≤ `W + b_g - 1`，且表列 0 = 窗口起点的物理块；
   - **T2 档（DSA-non-causal / SFA）**：派生的可见索引集合本身被夹紧到该区间内。
2. `slot_mapping`、`positions`、`query_start_loc`、Scheduler 状态、Target 全部逐位不变。
3. Window 产物全部位于 speculator-owned persistent buffer，capture/replay 同址**同形**。
4. Window 变换是 full state 的纯函数（同一步调 N 次结果相同）。
5. Padded rows 与 padded columns 每步显式置 0。
6. `draft_window_size` 关闭时，MRV2 的行为与改动前逐位一致。
7. 每个 KV group 各自用自己的 `kernel_block_size` 与 row width 计算（不得跨 group 复用）。

## 附录 B：与 MRV1 的「同 / 异」速查

| 维度 | MRV1 | MRV2（本设计） |
| --- | --- | --- |
| 窗口数学 | `spec_decode/utils.py:120-147` | 复用同一数学，改为逐 group |
| 被改对象 | proposer 私有的 `common_attn_metadata` | speculator 私有的 `DraftAttentionView` |
| block table 源 | per-step 的 `block_table_tensor`（可原地改） | **共享** persistent `input_block_tables`（只读，须另建 buffer） |
| slot mapping 源 | `self.sliding_window.full_block_table`（`llm_base_proposer.py:2109-2110`） | 不变（`compute_slot_mappings` 直接用 authoritative `block_table_ptrs`） |
| length 生产者 | 集中：`apply()` 一处改所有镜像（`utils.py:162-169`） | **分散**：L1–L10，至少 5 处要同源（§1.4） |
| apply 次数/step | 1 次（DSpark 为 per-group 1 次） | ≥2 次（live + graph manager rebuild），必须幂等 |
| 首步 | 无特殊（proposer 自己造 metadata） | **特殊**：复用 Target metadata（§1.6），需 F3 改造 |
| padding | `out[:num_reqs]` 即够（无 graph padded 读） | 必须覆盖 `num_reqs_padded` 行 + 两处清零 |
| native SWA | FIA `sparse_mode=4` + `is_draft_model` 传 block_table | 同（`attention/attention_v1.py:453-472,502-525,602-604`） |

## 附录 C：MRV1 侧的已知缺口 / 坑（读代码时容易浪费时间的地方）

这些与 MRV2 移植无关，但会影响「什么才算契约一致」的判断，故记录：

1. **配置范围完全没有校验。** `ascend_config.py:497` 只有 `int | None`；
   `_validate_user_input_ranges()`（`ascend_config.py:568-586`）只覆盖
   `weight_nz_mode` / `enable_mc2_hierarchy_comm` / `enable_fused_mc2`，
   不涉及 `draft_window_size`。因此 `0` / 负数会被接受并静默退化（F13）。
2. **MTP 的 `draft_window_size` 从未被清空**——只是不构造 adapter 且两处 apply 都被
   `method != "mtp"` 挡住。所以「force-disable」是行为上的，不是字段上的。
3. **两条显式 policy 之外的方法静默无效：** `ngram` / `ngram_gpu` / `suffix` / `medusa` /
   `extract_hidden_states` 都不继承 `AscendSpecDecodeBaseProposer`，
   因此既不读配置也不告警（`spec_decode/__init__.py:41-70` 的 factory 也没有相关分支）。
4. **文档与实际支持集合不一致：** 构造条件只看 `method != "mtp"`，
   所以 `eagle`（非 eagle3）与 `draft_model` **事实上也会启用**，
   但设计文档只宣传 Eagle3/DFlash/DSpark（`speculative_kv_sliding_window.md:20`）；
   发布说明 `docs/source/user_guide/release_notes.md:35` 又只写了 Eagle3 + DFlash。
5. **过期行号注释：** `llm_base_proposer.py:2600` 写「the window applied earlier (line 922)」，
   实际早期 apply 在 **1127** 行（922 行是 forward context / MOE index 重置）。
6. **悬空文档引用：** `llm_base_proposer.py:1124` 引用 `sw-dspark-flow-analysis.md`，
   该文件在仓库中不存在。
7. **`set_inputs_second_pass` 不存在**（全仓 grep 无命中）；MRV1 的第二步是
   `prepare_inputs_padded` / `attn_update_stack_num_spec_norm`。

### 现有测试与基线（作为 MRV2 对拍的锚点）

| 内容 | 位置 |
| --- | --- |
| adapter 数学单测（含 host mirror 同步） | `tests/ut/spec_decode/test_utils.py:192-214` |
| 构造参数契约（`assert_called_once_with(4096, 16, 8, 4, "cpu")`） | `tests/ut/spec_decode/test_llm_base_proposer.py:196-232` |
| 配置类型转换（`"4096"` → `4096`） | `tests/ut/test_ascend_config.py:1346-1358` |
| DSpark window E2E | `tests/e2e/pull_request/one_card/spec_decode/test_dspark.py:80-158` |
| DSpark window acceptance 基线 | `tests/e2e/pull_request/one_card/spec_decode/utils.py:44-51`（`dspark_sliding_window: [0.88, 0.88, 0.88, 0.88, 0.75, 0.75, 0.62]`） |
| Eagle3 window E2E | `tests/e2e/pull_request/two_card/spec_decode/test_spec_decode.py:370-434` |

**注意**：adapter 的 block-table 裁剪本身**没有**直接单测（只有 host mirror 那个用例），
MRV2 若重写数学，建议补一个与 MRV1 逐位对拍的数学单测（§10.1 T1）。
