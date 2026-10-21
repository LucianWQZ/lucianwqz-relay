# MRV2 Speculative Draft Sliding Window — Design v2

> 版本：v2（在 v1 `MRV2_Speculative_Draft_Sliding_Window_Design_DS.md` 基础上，逐条裁决 `MRV2_Speculative_Draft_Sliding_Window_Design_ds_codexReview.md` 后修订）
> 日期：2026-10-08 ｜ 性质：架构设计 + Review 裁决，**不含生产代码**
> 源码基线：`/Users/wenqingzhang/Desktop/vllm/vllm-ascend`、`/Users/wenqingzhang/Desktop/vllm/vllm`（本机 checkout）
> 行号约定：本文所有 `file:line` 均在本机逐条核对过；引用 Ascend 写 `vllm_ascend/...`，引用上游写 `vllm/v1/...`。
> 裁决口径：**Accepted** 必须改设计；**Rejected** 必须给当前源码依据；**Needs Verification** 必须先查 checkout 再定。

---

## 0. 本版说明

### 0.1 v1 → v2 的实质变化（8 条）

| # | 变化 | 触发 | 严重度 |
| --- | --- | --- | --- |
| 1 | **单一 `start`（对齐 `lcm{col_span_g}`）取代 per-group `start_g`** | Review C6（接受其"数学不兼容"的发现，但改其 remedy） | **Critical（v1 数学不自洽）** |
| 2 | **材料化分两条路线**：Route P（可重绑指针的 backend，漏斗平面）/ Route B（no-op updater，写进 builder 自己的持久 buffer） | Review C9 + 我核出的 SFA/DSA 源码事实 | Critical |
| 3 | **v1 的 W1（"capture 用 unwindowed dummy 定形状"）被限定为 Route P 专用**；Route B 不需要也不允许 W1 | Review C9 | Critical |
| 4 | **v1 的"单 plane"改为 lane/ring，深度 = `max_concurrent_batches`** | Review C11（我核到 `vllm/config/vllm.py:589-598` 与 `buffer_utils.py:24`） | Critical（v1 在 async 下不安全） |
| 5 | **新增"物理保留上限"约束**：`effective_window = min(W, KV spec 的保留量)` | Review C14 第 4 点（我核到 recycling-aware spec 注释） | Critical（语义） |
| 6 | **`valid_num_blocks` 成为材料化的一等输入**（源侧掩码） | Review C7/C17（我核到 `num_blocks` 已是 device/UVA tensor） | Critical |
| 7 | **长度类型系统 + canonical-origin + 容量夹紧**：`windowed_upper = clamp(U - start, min=exact', max=needed_g*col_span_g)` | Review C8（我复算了其反例，成立） | Critical |
| 8 | **范围收缩**：v1 的 SFA/DSA 全部"零 backend 改动"承诺作废；v1 的"非 base-proposer 方法显式 warning"行为升级撤回 | Review C9/C14/M3 | 范围/兼容 |

### 0.2 v1 中被本轮**推翻**的具体表述（须逐条核对）

| v1 位置 | v1 原文（摘要） | 判定 | 依据 |
| --- | --- | --- | --- |
| §6 F13 | 「`W=0` 或负值：`clamp(...)` 后 `start=0` → `windowed_len=seq_lens` → 静默无效」 | **错误** | `start = floor(max(L+K-W,0)/b)*b`。`W=0, L=250, b=64, K=0 ⟹ start=192, windowed_len=58`（不是 0、不是"无效"，而是"只剩一个 block"）。Review m1 正确。 |
| §11 Q13 附近 / 对 Codex·GPT 两份 review 的 m3 | 「`K ≥ W + b - (L mod b)` 在 `K ≤ 15`、`b ≥ 16` 下几乎不可达」 | **错误（推导用错了特例）** | 正确条件是 `K - W ≥ b - (L mod b)`。取 `L mod b = b-1` 时退化为 `K ≥ W + 1`：`W=0, K=7, b=64, L=250 (mod 58)` ⟹ `7 ≥ 6` 成立 ⟹ `windowed_len = -6`。**可达**。故 `W ≥ K` 是真正的充分条件（`K-W ≤ 0 < b-(L mod b)`），必须校验。我在那两份 review 里的相反结论要加 corrigendum（见附录 C）。 |
| §5.3 表格 "AR decode / `future_offset` = `K`" | 每步固定 `K` | **与 P13 自相矛盾** | P13 已规定 `future_offset = horizon - L_s`。表格是残留旧文字。Review C5/C13 在这一点上对的是**文档一致性**，不是数学（P13 的数学是对的）。 |
| §3.1 Candidate A / §5.2 | `tables[gid] : int32[cap_reqs, max_window_blocks_g]`（窄表）vs §5.4.1 的 full row width | **内部矛盾** | 已统一，见 §4.3。Review m2 正确。 |
| §5.7 | 「非 base-proposer 方法在 MRV1 静默未读取，MRV2 应显式化为 warning + ignore」 | **撤回** | 这是用户可见行为变更，不属本 feature。本版保持 MRV1 现状（静默），见 §8.4。Review M3 正确。 |
| §5.4.2/§5.4.3 | 「T2 档：夹紧 `start_pos`」 | **不完整** | v1 没说清 T2 必须**同时放弃 T1 的裁表/缩短长度**，否则坐标系双算。见 §4.4。Review C14 正确。 |
| §5.4 表 | `dcp_local_seq_lens` 「由窗口化后 global 派生」 | 已在 v1 中修正（改为区间前缀差） | 见 v1 §5.4；本版保留。 |

### 0.3 裁决统计

- **Accepted：29 条**（C1–C18 全部或部分、M1–M7 全部或部分、m1–m4 全部）
- **Rejected：4 条**（见 §3.2，均附源码依据）
- **Needs Verification：13 条**（已实查 checkout，见 §3.3 的逐条结论；其中 5 条的实查结果**改变了设计**，已并入 §0.1）

---

## 1. Decision Log

> 记录本 feature 的**设计决策**（不只本轮的 Review 响应）。每条：决策 / 依据 / 影响 / 状态。

| ID | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| **D1** | Window 只改 Draft Attention 的 read plane；物理 KV 分配、`slot_mapping`、`positions`、`query_start_loc`、Scheduler 状态、Target 全部不变 | 继承 MRV1 不变式：`spec_decode/utils.py:149-169`（apply 只改表与长度）、`llm_base_proposer.py:2104-2112`（slot 用 full table） | 冻结 |
| **D2** | Window 是 full state 的**纯函数**，禁止 window-of-window | P2；MRV1 `spec_decode/utils.py:120-147` 每次从 `full_block_table` 重算 | 冻结 |
| **D3** | Window 产物必须是 speculator-owned 的**独立 persistent buffer**；sharing 对象只读 | `vllm/v1/worker/gpu/block_table.py:73-74`（`input_block_tables` 与 Target 共享）、`speculator.py:287`（speculator 持同一 `BlockTables` 引用） | 冻结 |
| **D4** | **窗口起点在 proposal 级冻结**（`L_s + future_offset` 恒定）；`future_offset` 不是常数 | MRV1 一次 apply + 之后长度递增：`llm_base_proposer.py:1119-1127,2073-2077,2134-2136`；v1 P13（GPT review §8.4 指出） | 冻结 |
| **D5** | **单一绝对 `start`，对齐 `lcm{col_span_g}`**；per-group 只体现在 `start_col_g / needed_g`；**保留单一 length 契约** | Review C6 的发现成立（见 §3.1 C6），但 remedy 改为 lcm 对齐：这样 `windowed_len = L - start` 对全组一致，一份 `seq_lens` 自洽 | **本轮新增（Critical）** |
| **D6** | `col_span_g` = 该 group **table 列的 token span**；`cp_size=1` 时 = `kernel_block_size_g`；DCP 布局下 = `kernel_block_size_g × cp_size` | `vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:264`：`q_block_num = query_pos // (block_size * CP_SIZE)` | 冻结 |
| **D7** | 材料化分 **Route P**（GQA/MLA：漏斗替换 + 平面，指针可重绑）与 **Route B**（SFA/DSA：写进 builder 自己的持久 buffer） | `sfa_v1.py:296-307,703-706`（SFA NoPE 每次 build 把 common 表复制进 `block_table_buffer`）、`dsa_v1.py:420-436`（`dspark_swa_indices` 已是 capture-stable persistent buffer）、`dsa_v1.py:884-890`（DSA 的 block_table 是 common 的**别名**，无自己的 buffer） | **本轮新增（Critical）** |
| **D8** | Route P 的平面**与共享表同 shape**（宽度不变式），仅内容变化 → capture 期无需注入 view 即可保证 shape 一致 | Review C9（指出 same shape ≠ same address）+ 我核到 capture 入口传 full-wdummy 表（`dflash/cudagraph.py:36,55`、`model_states/default.py:95-121`） | 冻结 |
| **D9** | Route P 中**指针重绑**依赖 backend 的 graph-task 能力；GQA 的 FIA 调用已 `register_task`（kwargs 含 `block_table`）→ 可重绑；MLA 走 legacy update（用本轮 metadata 的 `decode.block_table`）→ 可重绑 | `vllm_ascend/attention/attention_v1.py:652-660`（`register_task(..., {"block_table": block_table, ...})`）、`utils.py:1769-1775`（`use_updatable_graph` 仅对 `AscendAttentionBackend` 真） | 冻结 |
| **D10** | **不得依赖 `build_draft_attn_metadata_factory()` 传 view**；view 必须走实例方法/真实函数参数 | Review C1/C12；且 v1 自身 P11 就要求显式传参。现有 factory 是模块级函数替换（`attn_utils.py:1240-1281`） | **本轮修订** |
| **D11** | 长度必须是**类型化**的：`DeviceExact` / `CpuExact?` / `CpuUpper` / `capacity` / backend-derived max；upper 用 canonical start 平移并夹紧容量 | Review C8；我复算其反例（见 §3.1 C8） | **本轮新增** |
| **D12** | 材料化的**源侧**必须同时受 `row_width` 与 per-row `valid_num_blocks` 约束 | Review C7/C17；`vllm/v1/worker/gpu/block_table.py:251-272`（gather 只写 `[0,num_blocks)`，padded 行清零） | **本轮新增（Critical）** |
| **D13** | `valid_num_blocks` 从设备取得，**不新增 D2H**：`BlockTables.num_blocks` 已是 UVA 张量，gather kernel 已在用 | `vllm/v1/worker/gpu/block_table.py:61`（`num_blocks = UvaBackedTensor(...)`）、`:170-171`（gather 传 `num_blocks.gpu`） | **本轮新增** |
| **D14** | 每步只重写/清零**有界活动列区** `[0, C_g)`，`C_g = ceil((W + lcm) / col_span_g) + 1` 为静态上界 → 单步成本与 context 长度无关 | Review M6；推导见 §4.3 | **本轮新增** |
| **D15** | **lane/ring 从第一版就有**，深度 = `max_concurrent_batches`；view 携带 `lane/generation` | Review C11；`vllm/config/vllm.py:589-598`（MRV2+async → `pp_size+1`）、`buffer_utils.py:24`（`set_default_max_concurrency`）、`:19,61`（retire 要求） | **本轮新增（Critical）** |
| **D16** | **物理保留上限**参与语义：`effective_window = min(W, group 的 KV spec 保留量)`；若 group 的 spec 是 recycling/sliding-window，更大的 W 无法恢复已释放的块 | Review C14；`vllm/config/vllm.py:602-609` 注释（"Recycling-aware KV cache specs (sliding-window, chunked-local) reserve for this because **out-of-window blocks are freed**"）+ `vllm/v1/kv_cache_interface.py:811,909,1316` + `vllm_ascend/core/kv_cache_interface.py:236` | **本轮新增（Critical）** |
| **D17** | AR first pass（Window ON）必须**新造 draft-scope metadata**，禁止浅改 Target 对象；且重建结果除 read view 外与 Target **逐位等价** | v1 F3 + Review C1/C10/C15；上游 `autoregressive/speculator.py:233-238,306-322` | 冻结（本版补"逐位等价"约束与 capture 一致性） |
| **D18** | v1 的 W1 仅适用于 Route P；**capture strategy 是 backend capability**，写成矩阵 | Review C9/C10 | **本轮修订** |
| **D19** | `W ≥ K`（AR）为**校验要求**，并运行时断言 `windowed_len ≥ 0` | Review m1；正确条件 `K - W ≥ b - (L mod b)` 可达（`W=0,K=7,b=64,L=250 ⟹ -6`） | **本轮新增（Critical）** |
| **D20** | 配置校验的**收紧必须标注为兼容性变更**；`W ≤ 0` 的处理由 maintainer 决定，不静默改变 MRV1 行为 | Review m1/M1；v1 的 `ascend_config.py:497` 只有类型 | **本轮修订** |
| **D21** | v1 的"非 base-proposer 方法 warning + ignore"**撤回**，保持 MRV1 静默；v1 只实现两条已文档化策略（MTP warn+ignore、DSpark+DSV4 warn+启用），且 policy **不得吞掉** factory 的 `NotImplementedError` | Review M3；`vllm_ascend/worker/v2/spec_decode/__init__.py:72`、`spec_decode/__init__.py:41-70` | **本轮修订** |
| **D22** | 首期范围：**只允许经 capability gate 的 `{dflash, dspark} × {GQA, MLA} × {eager, FULL}`**；AR/Eagle3、PIECEWISE、DSA-causal、SFA-non-NoPE、所有 CP/DCP、SP/DSA-CP、310P **fail closed** | Review 的收尾建议 + A 的 backend 矩阵（§9） | **本轮新增（范围）** |

---

## 2. Review Resolution Table

> 一句话裁决 + 证据指引。详述见 §3。`A`=Accepted（改设计）、`R`=Rejected（附源码）、`NV`=Needs Verification（已实查）。

| Review | 攻击面 | 裁决 | 一句话结论 | 落到 v2 的位置 |
| --- | --- | --- | --- | --- |
| C1 | Target 误 Window（依赖 monkeypatch） | **A（部分）** | 接受"view 不得经 factory 传"；**驳回**"现有 factory 单线程内即不安全" | D10、§4.5、§6 |
| C2 | positions 被传 0/stale | **A** | 接受为硬要求：draft 全路径必须显式传真实绝对 positions；禁止 `positions=None` fallback | §5 I6、§12 T7/T12 |
| C3 | slot_mapping 读到 window 表 | **A** | 接受"把顺序编码进 API + 语义类型"；驳回"funnel 改调用者 list"作为主要风险 | §5 I3、§4.5 |
| C4 | full table 被 alias/in-place 污染 | **A（部分）** | 接受"`data_ptr()` 不足以判别名"；**驳回**其 DSA 例子（那是 builder 自有 buffer） | §5 I4、§7.4 |
| C5 | repeated window / AR 重复推进 | **A** | 接受 generation key 扩展、CPU 向量也要来源断言；AR 一项 v1 已由 P13 修正（表格残留文字需同步） | §4.3、§5 I9/I10 |
| C6 | per-group block size 与单一 length 不兼容 | **A（改 remedy）** | **接受发现（v1 数学确实不自洽）**；**驳回**"整套 per-group" remedy，改单一 start + lcm 对齐 | D5、§4.3 |
| C7 | padding stale tail / actual vs padded | **A** | 接受；且已核到 `valid_num_blocks` 可从设备取得，无需 D2H | D12/D13、§4.6 |
| C8 | CPU upper 与 device exact 不同源；独立窗口化破坏 upper 性质 | **A** | 接受；反例复算成立；给出精确公式与"无生产者则 fail closed" | D11、§4.7 |
| C9 | capture 地址：same shape ≠ same address | **A** | 接受"capture strategy 必须是 backend capability"；W1 降级为 Route P 专用 | D7/D8/D18、§9 |
| C10 | capture/replay builder、派生 metadata、更新时序不一致 | **A** | 接受；已核到 `enable_enpu` 决定 update 在 replay 前/后，async 下存在跨迭代竞态 | §9.3、§12 T9 |
| C11 | async：单 plane 从第一版就不安全 | **A** | 接受（v1 此处实质缺陷）；已核到 MRV2+async → `pp_size+1 ≥ 2` | D15、§10 |
| C12 | contextvar 无法解决泄漏；仍是 process-global | **A** | 同 C1；接受"ContextVar 只能隔离引用，不能延长设备生命周期" | D10、§10.4 |
| C13 | timing 不能由固定 boundary/offset 覆盖；FULL merged 静态 length | **A** | 接受"FULL merged AR 必须有 per-step device length buffer"（v1 只有 CPU 侧） | §8.2、§9.4 |
| C14 | native SWA 不"天然取交集"；物理保留 | **A** | 接受全部四点；**物理保留一条我核实成立**（recycling spec 会释放窗口外块） | D16、§4.4、§8.5 |
| C15 | DCP/CP 还会改变列坐标与 first-page offset | **A** | 接受：`col_span_g` 必须含 `cp_size`；CP 组合 v1 fail closed | D6、§4.3、§11.2 |
| C16 | row 语义随 batch order 变，epoch 绑不了 request identity | **A** | 接受 view 携带 order generation/actual/padded/descriptor，禁跨请求行缓存 | §4.5、§10.2 |
| C17 | preemption/removal 触发 stale 复制 | **A** | 接受；`valid_num_blocks` 一等输入 + 不复用跨 generation 的 request identity | D12、§4.6 |
| C18 | graph padding：只固定列宽不够 | **A** | 接受 descriptor-aware view + 单独传 actual count | §4.5、§9.5 |
| M1 | Window OFF 零回归不可证 | **A** | 接受 OFF 短路 + 校验顺序；"零额外 branch"改为可测阈值 | §8.4、§12 T13 |
| M2 | mode matrix 过度概括 | **A** | 接受 per-method × mode capability + 分阶段门禁 | §8.3、§9.1 |
| M3 | unsupported 被误启用 + 行为升级 | **A** | 接受撤回行为升级；policy 不吞 factory 错误 | D21、§8.4 |
| M4 | "Flashcomm 无需处理"过强 | **A（措辞）** | 接受改述为"控制面正交、数据面未验证、fail closed"；驳回其强版本 | §11.1 |
| M5 | model-name / first-backend 假设 | **A（部分）** | 接受 per-group capability、global-gid keyed；**驳回**"去掉 model_type 判断" | §3.2 R4、§8.1 |
| M6 | materialization 成本随 max context | **A** | 接受；用 D14 的有界活动列区解决，并给出按 generation 缓存 | D14、§7.5 |
| M7 | 显存预算严重低估 | **A** | 接受；给出公式 + 纳入 memory planning + 拒绝阈值；Route B 消掉 SFA/DSA 这份开销 | §7.3、§7.3.1 |
| m1 | `W≤0`/`W<K` 描述有事实错误 | **A** | **v1 错了**，已复算并修正；接受 `W≥K` 校验 + 断言 | D19/D20、附录 C |
| m2 | buffer width 内部矛盾 | **A** | 已统一为 full-width（Route P） | D8、§4.3 |
| m3 | 测试计划漏关键反例 | **A** | 全部采纳（含 A/B 交替 origin replay） | §12 |
| m4 | `frozen`/`epoch`/`max_seq_len_hint` 语义不完整 | **A** | 改为 "borrowed mutable storage, single writer" + generation/lease；hint 只从 host 派生 | §5 I11、§7.2 |

---

## 3. 逐项裁决详述

### 3.1 Accepted（29 条中改变设计的部分，按重要性）

#### C6（最重要）— per-group block size 与单一 length 不兼容：接受发现，改写 remedy

**发现成立。** v1 给每个 group 独立 `tables[gid]`（§5.2），却只有一份 `seq_lens`/`seq_lens_cpu`/upper/`dcp_local_seq_lens`（§5.2/§5.4），并且 §4/§5.4.1 让 `start` **逐 group** 用各自的 `b_g` 计算。若 `start_g` 逐组不同，则 `windowed_len_g = L - start_g` 也逐组不同 → **不存在一份长度能同时匹配所有表**。review 的反例我复算通过：`L=190, W=100, K=0`，`b=64 ⟹ start=64, len=126`；`b=128 ⟹ start=0, len=190`。

源码依据（漏斗确实共享一份长度）：`vllm_ascend/worker/v2/attn_utils.py:294-330`——循环内只按 group 取 `block_tables[i]` / `slot_mappings[i]`，而 `seq_lens` 在循环外算好并对所有 group 复用（`:314`）。每组可不同 block size 见 `vllm/v1/worker/gpu/block_table.py:48-57`（`blocks_per_kv_block` 展开）。

**Remedy 改为单一 `start` + lcm 对齐**（不是"整套 per-group"）：

```text
col_span_g = 该 group table 列的 token span（cp_size=1 时 = kernel_block_size_g；DCP 时 × cp_size）
lcm_col    = lcm{col_span_g : 该 draft 的所有 active group}
start      = align_down(max(L + future_offset - W, 0), lcm_col)     # 全组同一绝对值
windowed_len = L - start                                            # 全组同一值（← 一份长度自洽）
start_col_g  = start / col_span_g                                   # 整数，因为 start 是 lcm 的倍数
needed_g     = ceil(windowed_len / col_span_g)
```

**正确性证明（逐组）**：`start` 是 `col_span_g` 的倍数 ⟹ 对任意 token `start + x`，其列号 `(start+x)//col_span_g = start//col_span_g + x//col_span_g`；表列 0 即绝对 `start`；核读列 `[0, needed_g)` 覆盖 `windowed_len` ⟹ 每组都正确。**同时**保留了单一 `L`/`windowed_len`/upper/local → 漏斗改动收敛为"仅 `block_tables[i]` 逐组 + 一份长度"，与 review 期望的"整套 per-group"相比改动更小、且保住 MRV1 的"所有 group 共享同一窗口"语义（MRV1 只用一个 `kernel_block_size`：`llm_base_proposer.py:406-408,446-452`；DSpark per-group 循环复用同一 `self.block_size`：`:2604-2605`）。

**代价**（须写入文档）：`start` 会比最优点早至多 `lcm_col - 1` 个 token ⟹ 实际可见历史可能比 `W` 大最多 `lcm_col - 1`。这与既有语义（"Block Alignment 后可见长度可超过 W"）一致，不构成新偏差。若 `lcm_col` 过大（例如各 group 的 col_span 互质），**fail closed**。

**不采纳 review remedy 的理由**：per-group `start_g` 会让同一 draft 模型的不同 attention layer 看到**不同长度**的历史（组 0 见 126、组 1 见 190），这与 v1 §7.2 的"Window lengths 与 Window table 表达同一个有效读取区间"跨组失效，也是相对 MRV1 的语义变更，需要产品决策；而 lcm 对齐不需要。

#### C9 + C10 + C13 — capture/replay 契约：接受"capture strategy 是 backend capability"

我核对的三条事实决定了这条必须接受：

1. **capture 期的 metadata 不由 speculator 产生**（v1 已识别，但只当成"形状"问题）：
   - DFlash/DSpark：`vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:36` 取 `get_dummy_block_tables(num_reqs)`（**full 宽度零表**，`vllm/v1/worker/gpu/block_table.py:177-187`），`:55` 调**模块级** `build_attn_metadata`（由 `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26` 在**导入期**重绑定，绕过 `build_attn_metadata_wrapper()`，后者只替换 `vllm.v1.worker.gpu.spec_decode.speculator` 模块：`worker/v2/attn_utils.py:1240-1251`）。
   - AR/Target：`worker/v2/spec_decode/autoregressive/aclgraph.py:111` → 上游 `prepare_inputs_to_capture()` → Ascend `worker/v2/model_states/default.py:95-121`，同样传 dummy full 表。
2. **有两个 no-op updater 的 backend**：`vllm_ascend/attention/sfa_v1.py:885-897`（`pass`，注释"sfa does not need to update graph params"）、`vllm_ascend/attention/dsa_v1.py:1619-1631`（`pass`，同）。而 DSA 明确**在 capture 时绑定 `ori_sparse_indices` 的 data pointer**：`dsa_v1.py:420-436` 的 docstring 原文——"the per-token slots are copied into its leading rows and the returned tensor is a slice view of `buffer`. This keeps the address stable across async ACL-graph replays, where the DSA operator captures `ori_sparse_indices`'s data pointer at capture time."
3. **指针能否重绑是 backend 属性**：GQA 的 FIA 调用带 `register_task(torch_npu.npu_fused_infer_attention_score.out, {... "block_table": block_table ...})`（`vllm_ascend/attention/attention_v1.py:652-660`）⟹ 可通过 `UpdatableGraph.resolve_tasks` 换指针；而 `use_updatable_graph()` 仅对 `AscendAttentionBackend` 为真（`vllm_ascend/utils.py:1769-1775`）；MLA 走 legacy `update_graph_params`，其实现按本轮 metadata 的 `decode.block_table` 重建算子参数。

**结论（D7/D8/D18）**：v1 的"W1 统一适用"作废，改为

| Route | 适用 backend | 材料化位置 | capture 需要注入 view? | 新增大块显存? |
| --- | --- | --- | --- | --- |
| **P** | GQA/FIA、MLA | 漏斗替换（平面，**与共享表同 shape**） | 不需要（shape 由宽度不变式保证一致；指针在 replay 经 graph task 重绑） | 是（见 §7.3） |
| **B** | SFA（NoPE）、DSA（non-causal DSpark） | **backend 自己的持久 buffer 内**：SFA 写 `block_table_buffer`（`sfa_v1.py:296-307`，每次 build 都复制）+ 缩 top-k；DSA 只夹紧 `dspark_swa_indices` 的 `start_pos`（`dsa_v1.py:449-461`） | 不需要（地址本就不变） | 否（buffer 已存在） |
| **fail closed** | DSA-causal、SFA-non-NoPE、所有 CP/DCP 组合、310P | — | — | — |

Route B 的依据是源码事实：SFA NoPE 路径**每次 build 都把 common 表复制进自己的持久 buffer**（`SparseMLAMetadataState.prepare()`：`:296-307` 用 `torch.div(..., out=table)` 写入 `self.block_table_buffer` 并把 `metadata.block_table` 指向该 buffer；调用点 `:703-706`）⟹ 窗口只需在这份拷贝里生效，**地址完全不变**；DSA 的 `dspark_swa_indices` 也已是 capture-stable 持久 buffer ⟹ 窗口只需改其派生式。

#### C11 — async：单 plane 从第一版就不安全（v1 实质缺陷）

证据链：`vllm/config/vllm.py:589-598`——`max_concurrent_batches = pp_size + 1 if (async_scheduling and use_v2_model_runner) else ...`；**MRV2 + async scheduling 下即使 `pp=1` 也是 2**。`vllm/v1/worker/gpu/buffer_utils.py:24` 的 `set_default_max_concurrency(n)` 说明 UVA pool 的深度就是按它设的；`:19`、`:61` 要求"reuse 前所有 GPU reader 已 retire"。故声明式的"若实测存在并发再双缓冲"不是正确性证明。**接受**：lane/ring 进第一版（D15）。

#### C12/C1 — 不得依赖 factory 传 view（但驳回其强版本）

接受：view 必须经实例方法/显式参数传递（D10）。**驳回**"现有 factory 在单线程内即不安全"这一更强暗示：`build_attn_metadata_wrapper()` 在入口缓存 `original_func`、在 `finally` 恢复（`worker/v2/attn_utils.py:1243-1251`）；`build_draft_attn_metadata_factory()` 同理缓存 `raw`（`:1266,1281`）⟹ **LIFO 嵌套是安全的**，交错/跨线程才不安全。而且该 factory 已经在承载**正确性关键**数据（positions——见 C2 的 AR 注释），所以 v2 的改动是"把 view 从脆弱通道挪到显式通道"，而不是"修一个原本就错的机制"。

#### C8 — 长度类型系统（反例复算通过）

review 的反例我复算通过：`W=100, b=64, K=0`，exact `L=150` → `start=floor(50/64)*64=0` → `exact'=150`；upper `U=200` → `start=floor(100/64)*64=64` → `upper'=136 < 150` ⟹ **独立窗口化会破坏 `upper ≥ exact`**。接受 D11，并给出精确公式（两式共用**同一个** canonical `start`）：

```text
start           = align_down(max(L + future_offset - W, 0), lcm_col)   # 由 device exact 决定，见 D5
windowed_exact  = L - start
windowed_upper  = clamp(U - start, min=windowed_exact, max=needed_g_max * col_span_g)
```
（`needed_g_max` 是该 proposal 内该 group 会用到的最大列数；上界保证不会去读未写过的列 → 直接封堵"upper 越窗"→ 读 block 0 的失败模式。）

同时接受 review 的"无生产者则 fail closed"：我已核实 **DFlash/DSpark 当前没有 rejection-corrected 的 CPU exact 生产者**——device exact 由 kernel 用 device `num_rejected` 写成（`vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:287-290`），而 CPU 侧 helper 只做 `target_cpu + step`（`worker/v2/spec_decode/autoregressive/speculator.py:815-822` 的注释明确"不减 rejection"；`DCPManager.prepare_draft_dcp_metadata_inputs` 同）。因此 v2 规定：**只消费 CPU 长度的 backend 组合（MLA-CPU 优先、DSpark+GLM 的 CPU 分支）在 v1 fail closed**，除非能证明其 CPU 值被夹紧到容量内。

#### C7/C17/C16/C18 — padding / stale / request identity / graph bucket

接受全部。关键可实施性证据：**`valid_num_blocks` 已在设备侧**——`BlockTables.num_blocks` 是 `UvaBackedTensor`（`vllm/v1/worker/gpu/block_table.py:61`，含 `.np`/`.gpu`/`copy_to_uva()`），而 gather kernel 已经在按它限界（`:170-171` 传 `num_blocks.gpu`；`:263-272` 用 `tl.load(group_num_blocks_ptr + req_idx)`）。故材料化 kernel 只需 `src_col < valid_num_blocks[row, gid]`，**无需新增 D2H**（回应 review 的 Q12）。另外 DSA 对 padded 行的处理确实依赖 `num_actual_reqs`（`dsa_v1.py:1088-1100`：`start_pos_prefill` 是 builder 自有 capture-stable buffer，`[num_actual_reqs, num_reqs)` 被清零）⟹ view 必须携带并转发准确的 actual/padded 计数。

#### C5/C13 — generation key 与 FULL merged AR 的 device length

接受：
- generation key 扩为 `(proposal_id, request_order_generation, anchor/horizon, step, gid, descriptor/lane)`；
- **CPU 向量也要有来源/代际校验**（v1 §8.3 只断言了 device 张量的 `data_ptr`）；
- **FULL merged AR 必须有 per-step device length buffer**：现有实现只为 FULL 准备了 per-step **CPU** buffer（`worker/v2/spec_decode/autoregressive/speculator.py:103-109` 的 `draft_seq_lens_cpus`），而 device `seq_lens` 在图内被 `update_draft_inputs` 逐 step 推进（上游 `autoregressive/speculator.py:954-964`）；新 plane 的 device 长度若不进图或不做 per-step，整段 merged graph 会读到**同一个静态值** ⟹ 后续 step 越界/漏读。v2 采用 `[K-1, cap_reqs] int32` 的 per-step device buffer（成本可忽略）。

#### M6/M7 — 性能与显存

接受 M6：v1 的 full-width 每步全行复制是 `O(num_reqs * Σ row_width_g)`，与 W 无关。v2 用 D14 的**有界活动列区**：静态上界 `C_g = ceil((W + lcm_col) / col_span_g) + 1`（因为 `windowed_len ≤ W + lcm_col - 1`），每步只重写/清零 `[0, C_g)`；列 `[C_g, row_width)` 在分配时置零后**永不触碰**，且任何长度都被夹紧到 `needed_g * col_span_g ≤ C_g * col_span_g` ⟹ 永不被读。这样单步成本与 context 长度解耦，且活动区仍是**全量重写**（保持 P2/P8 的幂等性，不引入增量语义）。

接受 M7：给出预算公式并要求纳入 memory planning（§7.3），同时用 **Route B 消掉 SFA/DSA 的这份开销**（它们本来就有 builder-owned buffer）。

#### M1/M2/M3/M4/M5 — 兼容性与 capability

- M1 **接受**：OFF 必须在初始化最前面短路；为传 view 而给 DFlash live 套 factory 会连带注入 `positions/is_prefilling/attn_state/parallel_config`（`worker/v2/attn_utils.py:1268-1275` 无条件注入）⟹ 确实改变 OFF 路径输入。把"关闭路径不得引入任何 branch"改成**可测阈值**（语义逐位一致 + p50/p99/显存不退化超过阈值）。
- M2 **接受**：per-method × mode capability + 分阶段门禁。源码依据：`dflash2/speculator.py:121-139`（eager-only）、`dflash/speculator.py:122-146`（DFlash 不支持 draft PIECEWISE → 收敛 `NONE`/`FULL_DECODE_ONLY`）、`autoregressive/speculator.py:123-141`（AR decode 的 PIECEWISE → `NONE`）。
- M3 **接受**（撤回行为升级，见 D21）。
- M4 **接受措辞**：改为"Flashcomm 控制面近似正交（它是 SP-MoE 开关：`ascend_config.py:639-657`、`utils.py:916-928`，且在 SFA 中只被赋值一次、无布局用途：`sfa_v1.py:869`）；Flashcomm+SP+DSA-CP 的**数据面未验证**，v1 fail closed。"**驳回**"Flashcomm 会改变 rank-local 布局因此 window 必须处理"的强版本——rank-local 布局改变来自 DSA-CP/SP 的 **token 切分**（`attention/context_parallel/dsa_cp.py:1133-1138`），与 block table 布局无关；v1 对 CP 组合整体 fail closed 已经覆盖该风险。
- M5 **部分接受**：接受 per-group capability（不用"第一个 backend"推断全局 `attn_architecture`——现状确实如此，如 `dspark/speculator.py:130-135`），接受 view 用 **global gid** keyed 且非 draft group 显式为 identity/None。

#### m1–m4

m1 见 §0.2（**v1 错误，已改**）；m2 已统一；m3 全部采纳（§12）；m4 接受（改称"borrowed mutable storage with a single writer"，单独定义 generation/lease，`max_seq_len_hint` 只从 host upper 或静态容量派生——否则 `device.max().item()` 会违反本设计自己的 P12）。

### 3.2 Rejected（4 条，附当前源码依据）

**R1 — 驳回 C1 的强版本："现有 factory 在单线程内即不安全、必须视为错误机制"。**
依据：`vllm_ascend/worker/v2/attn_utils.py:1243-1251`（`build_attn_metadata_wrapper` 在入口缓存 `original_func`、`finally` 恢复）与 `:1254-1281`（factory 缓存 `raw`、`finally` 恢复）。二者都满足 LIFO 语义 ⟹ 单线程顺序嵌套（live → capture 各自成对进入退出）是安全的；只有交错/跨线程/异常路径下的**恢复顺序**才会串味。v2 仍然采纳"view 不走 factory"（因为它是显式性/可测性问题，且 v1 的 P11 本就要求显式），但不接受"该机制本身有缺陷"的定性——它同时还在承载 positions 这一正确性关键数据（见 C2 的 AR 注释 `worker/v2/spec_decode/autoregressive/speculator.py:583-592`）。

**R2 — 驳回 C4 用来证明"builder 会原地污染共享表"的例子（`dsa_v1.py:1095`）。**
依据：`vllm_ascend/attention/dsa_v1.py:1088-1100` 的原地清零作用于 `self.start_pos_prefill`，且紧邻注释写明"**start_pos_prefill is a per-builder buffer with a capture-stable address, so the shared start_pos is copied in rather than aliased**. Only the tail past num_reqs needs zeroing; [:num_reqs] is overwritten." ⟹ 那是 **builder 自有 buffer**，不是 common/full table。C4 关于"`data_ptr()` 不足以判别名"的主论断仍然接受（见 §5 I4），但这条具体证据不成立。

**R3 — 驳回 C6 的 remedy 方向（"整套 table/length/interval/origin 全部 per-group"）。**
依据与证明见 §3.1 C6。核心：per-group `start_g` 会迫使 length 也随之 per-group，从而(a)把同一 draft 的不同 layer 置于不同历史长度下（相对 MRV1 的语义变更，MRV1 单一对齐量见 `llm_base_proposer.py:406-408,446-452`），(b)使"一份 device/CPU/local length"的漏斗契约（`attn_utils.py:294-330`）必须整体重写。lcm 对齐同时满足"数学自洽 + MRV1 语义 + 漏斗小改动"。

**R4 — 驳回 M5 的"应去掉 `model_type` 判断、改用语义 capability enum"。**
依据：要保留的 MRV1 contract 本身**就是**基于模型名的——`vllm_ascend/spec_decode/llm_base_proposer.py:420-422` 用 `getattr(hf_config, "model_type", "").startswith("deepseek_v4")` 决定是否发 DSpark advisory。若删除该判断就无法保持契约。v2 的折中是：该判断**只允许出现一次**（在 policy resolver 内），必须文档化为"MRV1 条件的精确镜像"，并有单测锁定；不得扩散到 runner / window 数学 / backend builder。（这同时满足 review 的真实关切：不要让 model-name 分支散落。）

### 3.3 Needs Verification（13 条：已实查，给出结论）

| # | Review 问题 | 实查结果 | 对设计的影响 |
| --- | --- | --- | --- |
| NV1 | Q1 AR proposal anchor 的 base length | `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:700-770` 的 kernel：`seq_len = tl.load(seq_lens_ptr + req_idx)` 在 `query_len -= num_rejected` **之前**读出并原样写入 draft 缓冲 ⟹ **L0 = Target 本轮 device `seq_lens`（未扣 rejection）**，与 MRV1 的 apply 时点取值一致 | anchor = `L0 + K`；后续 step `L_s = (L0 - r) + s`，用 `future_offset = horizon - L_s`（`horizon ≡ L0+K`）保证 `start` 恒定 |
| NV2 | positions 是否会被清 padded 行 | 同 kernel：positions 只复制 `[0, query_len)`；`[query_len, query_end)` 与 padded 行**不清**。`seq_lens` 的 padded 行则显式清 0 | 接受 C2：draft 路径必须显式传 positions；padded positions 必须有明确规则（清 0 或 mask） |
| NV3 | Q2 FULL merged AR 读哪个 device length | ascend 侧 `_multi_step_decode` FULL 直接 `decode_cudagraph_manager.run_fullgraph()` 一次（`worker/v2/spec_decode/autoregressive/speculator.py:438-458`）；图内逐 step 推进的是 `input_buffers.seq_lens`（上游 `:954-964`） | 接受 C13：plane 的 windowed device length 必须 per-step（D14 之外的额外 buffer，见 §8.2） |
| NV4 | Q8 capture 绑定 common tensor 还是 builder 自有 | DFlash/DSpark：`dflash/cudagraph.py:36,55` 用 full dummy 表；AR：`autoregressive/aclgraph.py:111` → `cudagraph_utils` → `model_states/default.py:95-121`。SFA-NoPE：**builder 自有** `block_table_buffer`（`sfa_v1.py:296-307,703-706`）。DSA：`block_table` 是 **common 的别名**（`dsa_v1.py:884-890` → `:1248-1250`），但 `dspark_swa_indices` 是**自有持久 buffer**（`:420-436`） | 直接产出 D7 的 Route P/Route B 划分 |
| NV5 | Q9 graph update 是给本轮还是下一轮 replay | `vllm_ascend/compilation/acl_graph.py:292-320`：`enable_enpu=True` → **先 update 再 replay**；否则 **先 replay 再 update**。且注释明确 async/MT 下"iteration i 的 update 可能早于 iteration i-1 的 replay"，因此需要 `synchronize`；FULL+EAGLE merge 路径**不需要**该 barrier | 接受 C10：必须写成显式时序契约 + A/B 交替 origin replay 测试（§12 T9） |
| NV6 | Q11 async 真实并发深度 | `vllm/config/vllm.py:589-598`：MRV2 + async → `pp_size + 1`（≥2）；`vllm/v1/worker/gpu/buffer_utils.py:24` 以该值设 UVA pool 深度 | 接受 C11 → D15（lane 深度 = `max_concurrent_batches`） |
| NV7 | Q12 `valid_num_blocks` 来源 | `vllm/v1/worker/gpu/block_table.py:61`（`UvaBackedTensor`）、`:170-171`（gather 传 `num_blocks.gpu`）、`:263-272`（kernel 按它限界） | 无需新增 D2H；材料化 kernel 直接消费（D13） |
| NV8 | Q14 native 物理保留 | `vllm/config/vllm.py:602-609` 的 `max_in_flight_tokens` 注释："**Recycling-aware KV cache specs (sliding-window, chunked-local)** reserve for this because **out-of-window blocks are freed** on the processed-token basis"；`vllm/v1/kv_cache_interface.py:811`（`SlidingWindowSpec`）、`:909`（`SlidingWindowMLASpec`）、`:1316`（recycling 注释）；Ascend 有 `vllm_ascend/core/kv_cache_interface.py:236`（`AscendSlidingWindowMLASpec`） | **成立** → D16：`effective_window = min(W, spec 保留量)`，且若 group 的 spec 是 recycling，必须显式声明该上限（否则更大的 W 无效） |
| NV9 | Q4 DSA/SFA 索引坐标 | `dsa_v1.py:420-461`：默认返回**physical slot**，`use_logical_indices=True` 时返回**序列内 logical position**；`start_pos = (prefix_lens - window_size).clamp(0)`，`visible_lens = seq_lens - start_pos` | T2 的正确实现：**不裁表、不缩长度，只把 `start_pos` 抬高到窗口绝对起点**（单一绝对坐标系），避免 rebase 双算 |
| NV10 | Q5 DCP 的列坐标 | `worker/v2/spec_decode/dflash/speculator.py:264`：`q_block_num = query_pos // (block_size * CP_SIZE)` ⟹ 列的 token span 含 `cp_size` | 直接影响 D6（`col_span_g` 必须含 `cp_size`）；CP 组合 v1 fail closed |
| NV11 | Q6 CPU exact producers | DFlash/DSpark：device exact 由 kernel 用 device `num_rejected` 写（`dflash/speculator.py:287-290`）；CPU 侧 `_calc_next_seq_lens_cpu` 明确**不减 rejection**（`autoregressive/speculator.py:815-822` 注释），`DCPManager.prepare_draft_dcp_metadata_inputs` 同 | 接受 C8：只消费 CPU 长度的组合在 v1 fail closed |
| NV12 | Q10 Eagle F3 capture 的 builder identity | `vllm/v1/worker/gpu/spec_decode/speculator.py:287-293`：speculator 保存 `target_input_buffers` 与 `target_attn_groups`，注释写明"draft prefill reuses the target model's attention metadata, so **its cudagraph capture must build dummy metadata through the same builders and buffers**" | F3 必须显式规定 capture 期改用 **draft** groups/buffers，且与 runtime 共用同一 builder-owned storage（§8.2、§9.4） |
| NV13 | Q16 unsupported policy 顺序 | `worker/v2/spec_decode/__init__.py:72`（factory `NotImplementedError`）、`llm_base_proposer.py:437`（MRV1 条件 `!= "mtp"`）、`dflash2/speculator.py:121-139`（eager-only）、`_310p/.../patch_spec_decode_310.py`（310P 独立 MTP speculator） | policy 必须在 factory 之后、且不吞错误；310P v1 fail closed（D21/D22） |

---

## 4. 最终 Architecture

### 4.1 总原则（v1 P1–P13 保留，新增/修订 3 条）

保留：P1 只改 read plane；P2 纯函数；P3 共享对象只读；P4 长度同源；P5 graph-stable；P6 per-group（**修订**：per-group 体现在列映射与 capability，不体现在 `start`，见 D5）；P7 padding 显式；P8 幂等；P9 契约一致（**修订**：不扩张行为，见 D21）；P10 native SWA 与窗口是两套配置（**修订**：组合语义按 backend 分档，见 §4.4）；P11 单一 fan-in + 显式传参（**强化**：不得用 factory/contextvar 传 view，见 D10）；P12 不引入热路径同步；P13 AR 起点在 proposal 级冻结。

**新增 P14 — 材料化路线由 backend capability 决定**（Route P / Route B / fail closed，§4.2）。
**新增 P15 — 只消费由 exact 决定的长度，并夹紧到有效列容量**（§4.7）。
**新增 P16 — lane/ring 是正确性的一部分**，不是性能优化（§10）。

### 4.2 两条材料化路线（D7）

```
Route P（GQA/FIA、MLA）
  window plane (speculator-owned, 与共享表同 shape)
        │  content-only update, 每步只重写 [0, C_g)
        ▼
  漏斗替换 block_tables[i] + 一份 windowed lengths（start 全组一致，见 D5）
        │
        ▼
  backend builder → op
  capture 期：不需要注入 view（shape 相同）；replay 期：指针经 graph task 重绑

Route B（SFA-NoPE、DSA-non-causal-DSpark）
  view 只携带「绝对区间 / origin / actual+padded 计数 / valid_num_blocks」
        │
        ▼
  backend 在**自己的持久 buffer**里材料化（SFA: block_table_buffer + top-k 长度；DSA: dspark_swa_indices 的 start_pos）
        │
        ▼
  op 读的地址/形状自 capture 起不变 ⟹ 不需要 pointer rebind，也不需要额外大显存
```

Route B 的判据（写入 capability）：**该 backend 是否存在"每次 build 都被重写、且地址被 captured op 持有"的持久 buffer**。SFA-NoPE 有（`sfa_v1.py:296-307`），DSA 的 `dspark_swa_indices` 有（`dsa_v1.py:420-436`）；DSA 的 `block_table` 没有（是 common 别名）⟹ **DSA-causal 走不了 Route B**，v1 fail closed。

### 4.3 单一 `start`、`col_span_g`、容量（D5/D6/D14）

```text
col_span_g    = kernel_block_size_g × (cp_size if DCP else 1)          # D6
lcm_col       = lcm{ col_span_g : active draft groups }
start         = align_down(max(L + future_offset - W, 0), lcm_col)     # 全组同一绝对起点（D5）
windowed_len  = L - start                                             # 全组同一值 → 一份长度契约
start_col_g   = start // col_span_g
needed_g      = ceil(windowed_len / col_span_g)
C_g           = ceil((W + lcm_col) / col_span_g) + 1                    # 静态容量上界（D14）
```
- 若某 group 的 `row_width_g < C_g` → 该 group 不可窗口化 → **fail closed**（不得只窗口化部分 group）。
- 若 `lcm_col` 超过阈值（建议 `≤ 512`）→ **fail closed**（避免窗口被对齐推到远超 W）。
- 单步成本：只重写/清零 `[0, C_g)`（`O(num_reqs_padded × Σ C_g)`），与 `max_model_len` 无关。

### 4.4 可见性与 native SWA 的分档（P10 修订，Review C14）

三种 backend 的 native 约束与窗口的组合**互不相同**，必须逐档声明：

| 档 | backend | native 约束载体（源码） | 窗口的实现位置 | 组合语义 |
| --- | --- | --- | --- | --- |
| N1 | GQA/FIA | 算子 band：`sparse_mode=4 / pre_tokens=sliding_window / next_tokens=0`（`attention_v1.py:602-604`） | Route P：表+长度 | **真交集**（band 在窗口化坐标系上算 basis；`is_draft_model=True` 时 block_table 仍传入，`:459-472`） |
| N2 | DSA（non-causal DSpark） | 显式索引：`build_dspark_swa_indices` 的 `start_pos = (prefix_lens - window_size).clamp(0)`（`dsa_v1.py:449-461`），op 读 `ori_sparse_indices`（`:2265-2270`），**不读 block table** | Route B：把 `start_pos` 抬到 `max(prefix - native, window_start_abs)` | 区间取交集（=末端更紧者），但**必须只在一套绝对坐标里做** |
| N3 | SFA（NoPE） | native window **不生效**：`ori_mask_mode=0`、`ori_win_left=ori_win_right=-1`，注释"Only ori_mask_mode 4 may carry a bounded window on this product line"（`sfa_v1.py:114-119`）；可见性来自 top-k（`:198-219`） | Route B：缩 top-k / 在自己的 `block_table_buffer` 里裁表 | 只有窗口一个来源；不得假定 native 在做交集 |

**关键禁令（Review C14 的实质）**：对 N2/N3，**不得同时**套用 Route P 的表左移与长度的缩短——那会让"索引在绝对坐标里算、表列号已左移"两套坐标混用（`pos // col_span` 会拿到错的列）。Route B 的契约就是：**表与长度保持 full，只缩最终的可见集合**。

**额外上限（D16，Review C14 第 4 点）**：若某 group 的 KV spec 是 recycling（sliding-window / chunked-local），窗口外块会被**物理释放**（`vllm/config/vllm.py:602-609` 的注释），故
```text
effective_window_g = min(W, spec_retention_g)
```
必须显式算出并在配置期校验/告警（`W` 大于保留量时窗口"设了也没用"）。

### 4.5 View 契约（D10/D12/D16）

```text
DraftWindowView                       # 实例级显式参数，不走 factory / contextvar
  generation: { proposal_id, request_order_generation, anchor/horizon, step, descriptor_id, lane_id }
  counts:     { actual_num_reqs, padded_num_reqs }
  origin:     { window_start_abs, window_end_abs }        # 全组一致
  groups:     { global_gid -> DraftWindowGroupView | None }   # key = global gid；非 draft group = None
  lane:       { ring_slot, retire_event }

DraftWindowGroupView
  table            (Route P：与共享表同 shape 的 plane slice；Route B：backend 自有 buffer 的 slice 或 None)
  windowed_len_device / windowed_len_cpu_upper / windowed_len_cpu_exact?
  dcp_local_len?   # local(end) - local(start)，见 §4.7
  needed_g / C_g / col_span_g
  valid_num_blocks (batch order，见 D12/D13)
  effective_window_g
```
硬规则：`table` 必须**逐位**是 `TableLayout` 描述的 gid 对应表；`None` 表示该 group 不窗口化（不得用"dense draft index"猜 global gid——Review M5）。view **不含** `positions` / `slot_mapping` / `query_start_loc`（P1）。

### 4.6 材料化的源侧约束（D12/D13）

```text
对每个 (row, dst_col)：
  src_col = start_col_g + dst_col
  允许复制 ⟺ (dst_col < needed_g[row]) and (src_col < row_width_g) and (src_col < valid_num_blocks[row, gid])
  否则写 0
row ∈ [actual_num_reqs, padded_num_reqs) ⟹ 整行写 0（显式，每步）
```
`valid_num_blocks` 取 batch order（按 `idx_mapping` gather 到计划中的小 persistent buffer；`num_blocks` 已是 UVA 张量，`block_table.py:61,170-171`，**不新增 D2H**）。

### 4.7 长度类型系统（D11，Review C8）

```text
DeviceExact      = L                      # 由 device 决定（AR: L0 - r + s；DFlash: kernel 写出的 seq_lens）
CpuExact?        = 只在该 method 能无 D2H 重建时才存在；否则 None（不得伪造）
CpuUpper         = U                      # optimistic，允许 > exact
capacity_g       = needed_g × col_span_g  # 该 group 允许被读到的最大长度（因为列 [needed_g, C_g) 未写）
windowed_exact   = L - start                         # 全组一致
windowed_upper   = clamp(U - start, min=windowed_exact, max=capacity_g)
dcp_local_len    = local_prefix(end) - local_prefix(start)     # 绝不写成 local_prefix(end - start)
```
`local_prefix` 对 L 非线性（`vllm/v1/attention/backends/utils.py:1088-1133`：`local(L) = floor(floor(L/i)/d)*i + clip(L - floor(floor(L/i)/d)*d*i - r*i, 0, i)`），因此前缀差是唯一正确形式；反例 `i=1,d=2,r=1`：`local(4)-local(1)=2` 而 `local(3)=1`。

---

## 5. Invariants（v2 修订版，实施与 review 的强制检查表）

| # | 不变量 | 判据 |
| --- | --- | --- |
| I1 | **Target-full**：Target metadata / verification / block-table view 永远 full | Target 侧快照（对象 identity + 内容）逐位不变 |
| I2 | **绝对坐标**：`positions` / RoPE / query layout 不被改写 | 窗口物化前后 `positions` 逐位与 `data_ptr` 不变 |
| I3 | **Full-slot**：所有物理写 slot 在窗口之前由 full table 定；`slot_mapping` 逐位不变 | 开/关窗口的 slot mapping 逐位相同；plane 与 `slot_mappings` storage 不重叠 |
| I4 | **只读源 + 非别名**：共享表只能作为源；plane/后端 buffer 与 authoritative `block_tables[*].gpu`、`input_block_tables[*]`、`slot_mappings` **storage 不别名** | 用 storage 区间判定（不是只比 `data_ptr()`），覆盖带 offset 的 view |
| I5 | **单一 `start`**：一个 proposal 内 `start` 全组一致（`lcm_col` 对齐），`L_s + future_offset` 恒定 | 逐 step 断言；MRV1 对拍 |
| I6 | **positions 显式**：draft 全路径必须显式传真实绝对 `positions`；禁止 `positions=None` fallback | 断言注入的 positions 与 model.forward 收到的一致 |
| I7 | **长度同源 + 类型化**：exact/upper/local/capacity 全部由同一 `start` 派生；`windowed_upper ≤ capacity_g` 且 `≥ windowed_exact` | 数学断言 + 逐 backend 消费者清单 |
| I8 | **长度夹紧**：任何被 backend 当作 kv 长度的值 ≤ `capacity_g` | 闭包断言（不是"≤ windowed_len"） |
| I9 | **幂等**：每步活动区 `[0, C_g)` 全量重写；refresh 只接受 full 源 | 同 step 内 N 次调用结果逐位相同；传回 view 报错 |
| I10 | **代际**：generation 含 `proposal/order/anchor/step/descriptor/lane`；CPU 向量也做代际校验 | 跨代复用触发断言 |
| I11 | **借出可变存储**：view 是"borrowed mutable storage, single writer"；lease 由 lane+event 定义 | 单一 writer 断言；无未释放即改写 |
| I12 | **Padding/有效性**：padded 行、padded 列、以及 `src ≥ valid_num_blocks` 的源**全部**显式处理 | 见 §4.6 的三条件 |
| I13 | **路径隔离**：Route P 与 Route B 不得同时作用于同一 gid；N2/N3 档禁止表左移 | capability 断言 |
| I14 | **native/物理上限**：`effective_window_g = min(W, spec_retention_g)`；N1/N2/N3 语义逐档声明 | 组合矩阵测试（集合级） |
| I15 | **capture 契约**：Route P 依赖 shape 不变 + 指针经 graph task 重绑；Route B 依赖地址不变 | 见 §9.2 矩阵；逐 descriptor 的 `(data_ptr, storage_offset, shape, dtype)` 断言 |
| I16 | **更新时序**：update 与 replay 的先后按 `(backend, mode, enable_enpu)` 显式声明，并用交替 origin 实验证明无 one-step lag | §9.3 |
| I17 | **FULL merged AR**：每个 captured step 有**自己的** device windowed length | per-step buffer 断言 |
| I18 | **lane**：深度 = `max_concurrent_batches`；refresh 前等本 lane 的 retire event | §10 |
| I19 | **Window OFF**：初始化最前面短路；语义逐位一致 + 性能/显存不超阈值 | §12 T13 |
| I20 | **capability fail closed**：未声明组合一律拒绝，绝不静默回退 | §9.1 矩阵 |

---

## 6. OwnerShip

| 模块 / Owner | 拥有 | 不拥有 |
| --- | --- | --- |
| Config Resolver | 读 `draft_window_size`、method policy（**唯一一处** model_type 镜像）、`W ≥ K`、`W > 0`、`lcm_col` 阈值、`effective_window` 校验与告警 | Window 数学 |
| `ModelRunner` | full request state、`BlockTables`/`num_blocks`、Target 执行 | method-specific window 逻辑 |
| `Speculator`（实例） | `DraftWindowPlane`、`DraftWindowView` 的产生与传递、lane 归属、method timing | 复制 window 数学 |
| `DraftWindowMath`（公共纯函数） | `col_span_g`/`lcm`/`start`/`windowed_len`/`needed_g`/`C_g`；`align_down`；合法域断言 | 持有 tensor |
| `DraftWindowPlane`（speculator 持有） | Route P 的持久 table/length/upper/local buffer、lane ring、generation | 决定 method 时机 |
| Route B 的 backend（SFA/DSA builder） | 自己的持久 buffer 与索引派生（`start_pos` / top-k） | 决定是否支持窗口（由 capability 声明） |
| Graph Manager | capture/replay 的绑定、update 时序、retire event | 从 method 名推断窗口语义 |
| `num_blocks`（`BlockTables`） | per-row/per-group valid block count（源侧掩码的权威） | 被窗口修改 |

---

## 7. Buffer Lifetime

### 7.1 三层生命周期

| 层 | 内容 | Owner | 释放点 |
| --- | --- | --- | --- |
| Runtime | `DraftWindowPlane`、group geometry、`C_g`、lane ring | speculator | runner 生命周期 |
| Capture binding | 每个 descriptor 绑定的 plane slice / Route B 的 backend buffer | plane + graph manager | 与 graph 同生命周期 |
| Execution generation | 某 step 的 view、lane slot、retire event | speculator + graph manager | lane reader + update 完成后 |

### 7.2 Generation 与 lease

```text
generation = (proposal_id, request_order_generation, anchor/horizon, step, descriptor_id, lane_id)
lease      = { ring_slot, retire_event }        # 不用裸 epoch 计数（Review m4）
```
view 只是"带 single-writer 契约的 borrowed storage"（不宣称 tensor 只读；`frozen=True` 只冻结 Python 字段）。

### 7.3 显存预算（D14/M7）

```
Route P: bytes = dtype_size × num_lanes × cap_reqs × Σ_{g∈draft} row_width_g
         其中 row_width_g = ceil(max_model_len / col_span_g) × blocks_per_kv_block_g
Route B: 0 新增（复用 builder 既有 buffer）
CPU 侧:  windowed lengths/upper 每 lane 一份（小）
```
- **必须纳入 memory planning**：group shape 直到 `set_attn()` 才可知（`worker/v2/spec_decode/dflash/speculator.py:94-99` 等），若此时 KV cache 规划已完成，必须显式预留/校验；超预算则**拒绝配置**。
- 示例（用于设阈值）：`max_model_len=1M, col_span=16, cap_reqs=256, 4 groups, 2 lanes` ≈ `4B × 2 × 256 × 4 × 65536 ≈ 512 MiB`（与 Review M7 的量级一致）⟹ 这是**必须**做预算而不是"可接受的几 MB"。此时应优先评估把该 group 移到 Route B，或拒绝该配置。

### 7.4 Alias 纪律

plane 只能由 `torch.empty/zeros` 分配，**禁止**由 full tensor 的 slice/view 派生；判别名用 storage 区间重叠判定（`untyped_storage().data_ptr()` + `storage_offset` + `nbytes`），不能只比 `data_ptr()`（Review C4 的主论断，接受）。

### 7.5 单步成本与增量

每步只重写/清零活动区 `[0, C_g)`（§4.3）；列 `[C_g, row_width)` 分配时置零后永不触碰。**不做跨 step 增量补列**（保持 I9 幂等）；若后续实测需要，必须引入"列有效性 generation"并把 anchor 纳入 generation。

---

## 8. Method Integration

### 8.1 Policy（D21，唯一一处 model_type 镜像）

| method（normalized） | MRV1 行为（已核实） | v2 行为 |
| --- | --- | --- |
| `eagle3` | 启用，公共 apply，`future_offset = K` | **v1 不启用**（D22；Eagle3/FULL merged 的 per-step device length 与 F3 capture identity 未闭合前 fail closed） |
| `eagle` | **代码路径同样启用**（条件只看 `method != "mtp"`，`llm_base_proposer.py:437`） | 同 eagle3 |
| `dflash` / `dflash2` | 启用，公共 apply，`future_offset = 0` | 启用（eager / FULL_DECODE_ONLY；DFlash2 因 eager-only 而只支持 eager，`dflash2/speculator.py:121-139`） |
| `dspark` | 启用，per-group apply，`future_offset = 0` | 启用（首期目标） |
| `dspark` + `deepseek_v4*` target | warn + 启用（`llm_base_proposer.py:430-435`） | 同（warn 仅发一次） |
| `mtp` 全部变体 | warn + ignore（`:423-429,437`） | 同（**按 normalized method 判定，早于任何 class/factory 分支**；不得因落到 `AscendEagleSpeculator` 而启用） |
| `extract_hidden_states` | 不适用 | 同 |
| token-only / 不可实例化 | MRV1 静默未读取 / factory `ValueError`；MRV2 factory `NotImplementedError`（`worker/v2/spec_decode/__init__.py:72`） | **保持现状**（D21，撤回 v1 的行为升级）；policy 不得吞掉 factory 错误 |

### 8.2 AR（Eagle/Eagle3）——v1 不启用，但契约先定

- anchor：`horizon = L0 + K`，`L0` = `prepare_prefill_inputs` 写入的 draft device `seq_lens`（= Target 本轮未扣 rejection 的长度，NV1）。
- 每步：`L_s = (L0 - r) + s`，`future_offset = horizon - L_s` ⟹ `start` 恒定（D4）。
- 首步：F3——新造 draft-scope metadata；**除 read view 外与 Target 逐位等价**（`query_start_loc(_cpu)`/`positions`/`num_tokens`/`is_prefilling`）；capture 期必须改用 draft groups/buffers 并与 runtime 共用同一 builder-owned storage（NV12）。
- FULL merged：per-step device windowed length buffer（NV3/D14）。

### 8.3 各 method × mode

| method | eager | PIECEWISE | FULL / FULL_DECODE_ONLY |
| --- | --- | --- | --- |
| dflash | ✅ 首期 | ❌（上游本就收敛为 NONE，`dflash/speculator.py:122-146`） | ✅ 首期（Route P 或 B 取决于 group 的 backend） |
| dspark | ✅ 首期 | ❌ 同上 | ✅ 首期 |
| dflash2 | ✅ 首期 | ❌ | ❌（`dflash2/speculator.py:121-139` 要求 `enforce_eager`） |
| eagle/eagle3 | ⏸ v1 不启用 | ⏸ | ⏸ |
| mtp | ❌（warn+ignore） | ❌ | ❌ |

### 8.4 Window OFF 的强约束（M1）

- OFF 在初始化**最前面**短路：不解析 geometry、不建 plane、不进 window-aware 路径、不改 OFF 的 builder 输入（**不套 factory**——`worker/v2/attn_utils.py:1268-1275` 会无条件注入 positions 等）。
- 校验只对 `enabled && supported` 的组合执行，以免改变 MTP/unsupported 的原有顺序。
- OFF 的验收改为**可测阈值**（语义逐位一致 + 延迟/吞吐/显存回退 ≤ 阈值），不写"零额外 branch"。

### 8.5 native SWA 组合

见 §4.4 的 N1/N2/N3 分档 + D16 的 `effective_window`。测试用**集合级**判据（最终可见绝对 KV 集合 = 窗口 ∩ native ∩ 物理保留），不得用 acceptance 变化代替。

---

## 9. Graph Strategy

### 9.1 Capture/replay 契约矩阵（D18）

| backend | 可见性载体 | Route | capture 绑定谁 | replay 如何生效 | 未验证项 |
| --- | --- | --- | --- | --- | --- |
| GQA/FIA | 表+长度+band | P | 共享 full dummy 表（同 shape） | 指针经 `resolve_tasks` 重绑到 plane（`attention_v1.py:652-660` 已 `register_task`） | 重绑是否接受 shape 变化（v2 用同 shape 规避） |
| MLA | 表+长度（CPU 优先！） | P | 同上 | legacy `update_graph_params` 用本轮 `decode.block_table` | CPU 长度夹紧（I8） |
| SFA-NoPE | top-k 索引 + 自有表 buffer | B | builder 自有 `block_table_buffer`（`sfa_v1.py:296-307`） | 每次 build 重写自己的 buffer（地址不变） | top-k 长度的窗口化公式 |
| DSA-non-causal-DSpark | `dspark_swa_indices`（自有持久 buffer，`dsa_v1.py:420-436`） | B | 同上 | 每次 build 重写 `start_pos`/indices（地址不变） | `use_logical_indices` 分支的坐标 |
| DSA-causal / SFA-non-NoPE | 表+长度（表是 common 别名，`dsa_v1.py:884-890`） | — | — | — | **v1 fail closed** |
| 任意 CP/DCP 组合 | `col_span` 含 `cp_size`（NV10） | — | — | — | **v1 fail closed** |

### 9.2 地址/形状断言

逐 descriptor 断言 `(data_ptr, storage_offset, shape, dtype)` 一致（不能只比 `data_ptr()`——Review C4/M6 采纳）。`ACLGraphWrapper` 的 debug 只覆盖 positional args（`vllm_ascend/compilation/acl_graph.py:186`），不能作为元数据内嵌张量的地址安全证据。

### 9.3 更新时序（NV5，Review C10）

- `enable_enpu=True` → **update 先于 replay**；否则 **replay 先于 update**（`compilation/acl_graph.py:292-320`）。
- async/MT 下存在跨迭代竞态（同处注释明确要求 `synchronize`）；FULL+EAGLE merge 路径不需要该 barrier。
- ⟹ 每条 `(backend, mode, enable_enpu)` 必须**显式声明**"本次 update 作用于本次还是下次 replay"，并用 **A/B 两组完全不同 window origin 的连续 replay** 实验排除 one-step lag（§12 T9）。lease 的 retire 必须晚于 update 完成。

### 9.4 capture 期必须注入 view 的情形

Route P **不需要**（shape 一致）；但若 Route P 的 plane 需要参与 capture（例如为了地址而非形状），则必须走**显式参数**改造上游 `cudagraph_utils.prepare_inputs_to_capture` / `dflash/cudagraph.py`，并同步更新 §2 式的"不改上游"表述——v2 明确：**首期选择不需要捕获注入的 Route P/B 组合**。

### 9.5 Graph bucket / padding

view 必须 `for_descriptor(desc, actual_num_reqs)`：返回与 descriptor 精确一致的 slice，并**单独**传 actual/padded 计数（Review C18；DSA 的 padded 行处理依赖它，`dsa_v1.py:1088-1100`）。每 bucket 的 `C_g` 与 capacity 必须覆盖该 bucket 的最大 need。

---

## 10. Async Strategy

### 10.1 并发事实（NV6）

MRV2 + async scheduling ⟹ `max_concurrent_batches = pp_size + 1 ≥ 2`（`vllm/config/vllm.py:589-598`）；UVA pool 深度按它设置（`vllm/v1/worker/gpu/buffer_utils.py:24`）。⟹ **lane/ring 是第一版的正确性需求**（D15）。

### 10.2 两级存储

```
Host:   CPU length/upper 的 per-lane ring（深度 = max_concurrent_batches）
Device: Route P 的 plane 每 lane 一份；Route B 由 backend buffer 的 generation 保护
每次 refresh：等本 lane 的 retire event → 写 → 记 read event（replay+update 完成）
```

### 10.3 Generation 即所有权

`generation` 含 `proposal_id / request_order_generation / anchor / step / descriptor / lane`（D15/I10）。**不做跨代 request identity 缓存**：row 每次按当轮 `idx_mapping` 重建（Review C16）。

### 10.4 不用隐式机制

不使用 module-global / contextvar 承载 view（D10）；ContextVar 至多承载不可变标量上下文，且**不能**替代 lane/event 的存储生命周期（Review C12）。

### 10.5 rejection / correction

proposal epoch N 只消费 N 的 full snapshot；Target 验证结果只影响 N+1 的 full state（`worker/v2/model_runner.py:818-839` 的 D2H 修正路径），窗口**不预测**该结果。

---

## 11. Week4 Extension

### 11.1 Flashcomm / SP（M4 措辞修正）

- 事实：Flashcomm 是 SP-MoE 开关（`ascend_config.py:639-657`），`enable_sp()` = `use_sequence_parallel_moe`（`utils.py:916-928`），SFA 中只赋值一次、无布局用途（`sfa_v1.py:869`）⟹ **对窗口 read plane 近似正交**。
- 结论改为：**控制面近似正交；Flashcomm+SP+DSA-CP 的数据面未验证，v1 fail closed**。不得写"无需处理"。

### 11.2 CP / DCP / DSA-CP

- 列坐标已变（`col_span_g` 含 `cp_size`，NV10）；SFA-DCP 的 replicated 视图片射假定"列号 == 逻辑块号"（`sfa_cp.py:601-611`、`sfa_dcp_utils.py:66-80`），左移表会破坏该假设 ⟹ 必须走 Route B 的"只缩可见集合"或 fail closed。
- local 长度用前缀差（§4.7）。
- **v1 全部 CP 组合 fail closed**；扩展点：`WindowPartitioner` capability，携带 `table_origin` / `first_token_offset`（若对齐到 `cp_size × col_span` 可省去 offset，见 D5 的 lcm 对齐）。

### 11.3 Async 更深并发

lane 深度已参数化；未来只需扩大 ring 与 event 管理，不改 window 数学。

### 11.4 责任分界

v1 完成：窗口数学（含 lcm/容量）、Route P/B、长度类型系统、lane、OFF 短路、capability fail closed。
Week4 补：CP/SP 的坐标映射、AR/Eagle3 与 PIECEWISE 的组合、Route B 的更多 backend、更深的 async。

---

## 12. Test Matrix

| ID | 类别 | 目标 | 方法 | 通过判据 |
| --- | --- | --- | --- | --- |
| T1 | 数学 | 与 MRV1 对拍 | 相同输入跑 v2 数学与 MRV1 `SlidingWindowAdapter`；边界 `L∈{<W, =W, 超W, 恰好对齐, 不对齐}`、`col_span∈{16,32,64,128}`、多组 lcm | `start`/`windowed_len`/`needed_g` 逐位一致；`start % lcm_col == 0`；`windowed_len ≥ 0` |
| T2 | 数学 | `W ≥ K` 与非法域 | `W ∈ {0,-1,1,b-1,b,b+1}`、`K ∈ {1,7,15}`、构造 `L mod b = b-1`（**必含 `W=0,K=7,b=64,L=250`**） | `W<K` 组合被配置校验拒绝，或断言 `windowed_len ≥ 0` 失败并 fail fast（不得静默） |
| T3 | 隔离 | Full/Window 不相干 | 快照 `input_block_tables`/`slot_mappings`/Target metadata（identity+内容）→ 跑 window → 再快照 | 逐位不变；plane 与共享 storage **区间不重叠**（I4） |
| T4 | 幂等 | 同 step 多次 refresh | 同 proposal/step 调 N 次；再把 view 当源调一次 | 前 N 次结果逐位相同；最后一次报错（I9） |
| T5 | 源有效性 | stale tail | 构造 active row 的 `[num_blocks, row_width)` 有旧 block id，且窗口 need 覆盖该区间 | 窗口表内该列全 0（不得复制 stale）；8→3 缩小 batch 后 padded 行全 0 |
| T6 | per-group | `lcm` 与容量 | 组 `b∈{32,64}`（lcm=64）与 `b∈{64,96}`（lcm=192）；断言每组 `start_col_g` 整除、`needed_g` 与最终 layer metadata 的长度匹配 | 每层最终 kv 长度 ≤ `capacity_g`（**不只是 ≤ windowed_len**，Review m3） |
| T7 | positions | 绝对性 | 逐 method × mode 断言 builder 收到的 positions == model.forward 的 positions；大 batch→小 batch 连续 replay | 逐位相等；padded positions 不被 RoPE/indexer 当有效行（I6） |
| T8 | 长度 | 闭包与 upper 性质 | 逐 backend（GQA/MLA）取最终消费的长度 | 全部 `≤ capacity_g`；`windowed_upper ≥ windowed_exact`；DCP 用前缀差（含 `i=1,d=2,r=1` 反例） |
| T9 | Graph | one-step lag / 交替 origin | **A/B 两组完全不同 window origin 连续 replay**；覆盖 `enable_enpu ∈ {T,F}`、GQA(UpdatableGraph) 与 MLA(legacy) | 每次 replay 的可见集合等于该次应得集合；无 one-step lag；逐 descriptor `(ptr, offset, shape, dtype)` 一致 |
| T10 | Graph | Route B 地址不变 | SFA-NoPE / DSA-non-causal 的 builder buffer 在 capture/replay 的 `data_ptr` 与内容 | 地址恒定；内容按 generation 正确刷新 |
| T11 | native SWA | 集合级正确性 | N1/N2/N3 档各构造 native + window 组合 | 最终可见**绝对 KV 集合** == `窗口 ∩ native ∩ 物理保留`（不得用 acceptance 代替，Review m3）；SFA 档验证"只缩 top-k"生效 |
| T12 | 物理保留 | `effective_window` | 构造 recycling spec 的 group，`W > retention` | 配置期告警/拒绝；实际可见集合不超过 retention（D16） |
| T13 | Window OFF | 阈值回归 | OFF before/after：输出、acceptance、p50/p99、吞吐、峰值显存 | 语义逐位一致；性能/显存回退 ≤ 阈值；不进入 window-aware 路径（M1） |
| T14 | capability | fail closed | 枚举未声明组合（DSA-causal、SFA-non-NoPE、CP、310P、AR） | 初始化即拒绝并给出明确原因；无静默回退 |
| T15 | Async | lane/retire | 交错两个 epoch 的 prepare；`max_concurrent_batches=2` 下交替 refresh | generation N 在 reader+update 完成前不被 N+1 覆盖；debug 断言捕获缺失 event |
| T16 | Preemption | slot 复用 | 长请求 preempt/finish → 同 slot 加短请求（旧块立即分配给别的请求） | 窗口源只覆盖新请求 valid count；不出现其他请求的 block id（Review C17） |
| T17 | 性能 | materialization 成本 | 长 context（L ≫ W）下测单步 materialize kernel 的时间/带宽 | 与 L 解耦（只随 `Σ C_g` 线性）；不新增 D2H（`.item()/.cpu()/.numpy()` 频次不增加） |
| T18 | 内存 | 预算 | 目标模型 worst-case（group × lane × CPU mirror × builder buffer × graph pool） | 与 §7.3 公式吻合；纳入 memory planning；超阈值拒绝 |
| T19 | E2E | MRV2 vs MRV1 | `draft_window_size=512` 下 dflash/dspark（对齐 `tests/e2e/.../test_dspark.py:80-158` 与 `.../test_spec_decode.py:370-434` 的做法） | acceptance 与 MRV1 基线同量级；Target logits 与不开窗口一致 |
| T20 | 契约 | MTP / 不可实例化 | `mtp` + `draft_window_size`；不支持 method | MTP：warn 一次且行为与不开窗口逐位一致；不支持 method：仍是 factory 的 `NotImplementedError`（policy 不吞） |

---

## 13. 仍未关闭（需源码/产品决策）

| # | 事项 | 类型 | 关闭方式 |
| --- | --- | --- | --- |
| O1 | Route B 的 SFA top-k 窗口化公式（`get_topk_lengths(positions) = (positions+1).clamp(max=topk_tokens)`，`attention/indexer.py:127-131` 附近） | 源码 | 写出"窗口化 top-k"的确切公式并集合级验证 |
| O2 | DSA `use_logical_indices` 分支（SparseFlashMLA 自带 block-table lookup）在窗口下是否需要 origin 变换 | 源码 | 逐分支 trace；无法证明则 fail closed |
| O3 | AR/Eagle3 的 F3 与 FULL merged 完整闭合（含 capture 用 draft groups） | 源码 + 实现 | 按 §8.2 落地后再启用 |
| O4 | `cp_size > 1` 时的 `first_token_offset` 是否真的可用 lcm 对齐消除 | 源码 | 在 DSA-CP/SFA-DCP 上验证；否则 CP 保持 fail closed |
| O5 | `draft_window_size ≤ 0` 的正式政策（拒绝 / warn+ignore / 复刻 MRV1 未定义行为） | **产品** | maintainer 决定（D20） |
| O6 | `W ≥ K` 校验是否可接受为兼容性收紧（MRV1 无此校验） | **产品** | 同上 |
| O7 | 目标模型的 group/backend/KV spec 全量枚举（是否有 recycling spec、lcm_col 实际值） | 配置 | 在目标配置上跑 capability 枚举脚本/日志 |
| O8 | Route P 的 route 选择是否需要"同一 model 内混用 P/B" | 设计 | 若混用，I13 需要按 gid 记录 route |

---

## 附录 A：本轮新核实的源码事实（均为本机核对，可直接引用）

| 事实 | 位置 |
| --- | --- |
| MRV2 + async ⟹ `max_concurrent_batches = pp_size + 1 ≥ 2` | `vllm/config/vllm.py:589-598` |
| recycling KV spec 会**释放窗口外块**（sliding-window / chunked-local） | `vllm/config/vllm.py:602-609`（`max_in_flight_tokens` 注释） |
| `SlidingWindowSpec` / `SlidingWindowMLASpec`；Ascend `AscendSlidingWindowMLASpec` | `vllm/v1/kv_cache_interface.py:811,909,1316`；`vllm_ascend/core/kv_cache_interface.py:236` |
| `num_blocks` 是 UVA 张量，gather kernel 已按它限界 | `vllm/v1/worker/gpu/block_table.py:61,170-171,263-272` |
| UVA pool 深度由 `set_default_max_concurrency` 设定；复用需 reader retire | `vllm/v1/worker/gpu/buffer_utils.py:24,19,61` |
| AR prefill kernel：`L0` 取未扣 rejection 的 `seq_lens`；positions 只复制 `[0,query_len)`；padded `seq_lens` 清 0、positions 不清 | `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:700-770` |
| DFlash capture 用 full dummy 表、不传 positions、`max_seq_len=max_model_len` | `vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:24-71`（`:36,55,64`） |
| DFlash 的 capture 模块符号由 patch 在导入期重绑定 | `vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:26` |
| speculator 保存 `target_input_buffers`/`target_attn_groups`（因 draft prefill 复用 Target metadata ⟹ capture 必须用同一 builder/buffer） | `vllm/v1/worker/gpu/spec_decode/speculator.py:287-293` |
| SFA-NoPE 每次 build 把 common 表复制进**自有** `block_table_buffer` | `vllm_ascend/attention/sfa_v1.py:296-307`（`prepare`）、`:703-706`（调用点） |
| SFA/DSA 的 `update_graph_params()` 是 `pass` | `vllm_ascend/attention/sfa_v1.py:885-897`；`vllm_ascend/attention/dsa_v1.py:1619-1631` |
| DSA 的 `block_table` 是 common 的**别名**（无自有 buffer） | `vllm_ascend/attention/dsa_v1.py:884-890`、`:1248-1250` |
| DSA `dspark_swa_indices` 是 capture-stable 持久 buffer；indices 默认 physical slot、`use_logical_indices` 时为 logical position；`start_pos = (prefix_lens - window_size).clamp(0)` | `vllm_ascend/attention/dsa_v1.py:420-461` |
| DSA `start_pos_prefill` 是 builder 自有 buffer（拷贝而非别名），按 `num_actual_reqs` 清 padded | `vllm_ascend/attention/dsa_v1.py:1088-1100` |
| CP 下取列用 `query_pos // (block_size * CP_SIZE)` | `vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:264` |
| GQA 的 FIA 调用 `register_task` 中含 `block_table`（可重绑） | `vllm_ascend/attention/attention_v1.py:652-660` |
| `use_updatable_graph()` 仅对 `AscendAttentionBackend` 为真 | `vllm_ascend/utils.py:1769-1775` |
| update/replay 顺序由 `enable_enpu` 决定；async 下存在跨迭代竞态（注释要求 synchronize）；FULL+EAGLE merge 不需 barrier | `vllm_ascend/compilation/acl_graph.py:292-320` |
| `ACLGraphWrapper` 只检查 positional tensor args 的地址 | `vllm_ascend/compilation/acl_graph.py:186` |
| funnel：`seq_lens` 在 group 循环外算好、所有 group 共用；`np.full(num_reqs, max_seq_len)` 兜底 | `vllm_ascend/worker/v2/attn_utils.py:253-260,290-330` |
| factory 无条件注入 positions/is_prefilling/attn_state/parallel_config | `vllm_ascend/worker/v2/attn_utils.py:1268-1275` |
| wrapper / factory 均在入口缓存并在 `finally` 恢复（LIFO 安全） | `vllm_ascend/worker/v2/attn_utils.py:1243-1251,1266-1281` |
| FULL merged AR 只 replay 一次；per-step **CPU** buffer 已存在（device 无） | `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:438-458,103-109` |
| `_calc_next_seq_lens_cpu` 明确不减 rejection | `vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:815-822` |
| DFlash/DSpark device exact 由 kernel 用 device `num_rejected` 写出 | `vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:287-290` |
| MRV1 单一对齐量；`method != "mtp"` 即构造；DSV4 advisory 用 `model_type.startswith("deepseek_v4")`；冻结 start + 长度递增 | `vllm_ascend/spec_decode/llm_base_proposer.py:406-408,420-422,437,445,446-452,1119-1127,2073-2077,2134-2136` |

## 附录 B：v1 段落 → v2 位置的对照

| v1 位置 | v2 处置 |
| --- | --- |
| §2 P1–P13 | 保留并新增 P14/P15/P16（§4.1） |
| §5.2 `DraftWindowPlane`（窄表） | 改为 full-width + 有界活动区（§4.3），并区分 Route P/B（§4.2） |
| §5.3 boundary 表的 AR 行（`future_offset=K`） | 改为 horizon 语义（§8.2） |
| §5.4 漏斗替换表 | 保留，但补充：`start` 全组一致（§4.3）、CPU 长度夹紧（§4.7）、view 不走 factory（D10） |
| §5.4.1 宽度不变式 | 保留，但限定为 Route P（D8） |
| §5.4.2/§5.4.3 T1/T2 | 重写为 N1/N2/N3 分档 + "Route B 不裁表不缩长度"（§4.4） |
| §5.4.4 W1 | 降级为 Route P 专用（D18/§9.1） |
| §5.6 AR length producer 改写 | 保留，并新增 per-step **device** buffer（§8.2） |
| §5.7 MTP/其它方法 contract | 撤回行为升级（D21/§8.1） |
| §6 F13 | 修正（附录 C） |
| §8.1/§8.2 graph | 重写为 capability 矩阵 + 时序契约（§9） |
| §8.4 async | 升级为 lane/ring（§10） |
| §9 Extension | Flashcomm 措辞修正；CP fail closed（§11） |
| §10 Test | 扩充为 T1–T20（§12） |

## 附录 C：需要回填的 corrigendum（我的两份 review 文档）

本轮核实发现我在下面两处写了**错误的数学结论**，需要回填更正（否则会误导实现者把 `W<K` 当作"几乎不可达"）：

- `MRV2_Speculative_Draft_Sliding_Window_Design_codex_dsReview.md` 的 **m3**（"R19 的触发条件算错了…正常配置下不可达"）：结论方向对（Codex 的 `W<K` 判据不精确），但我给出的"需要 `K ≥ W + b - (L mod b)` 且 `b ≥ 16` 时不可达"是错的——该式在 `L mod b = b-1` 时退化为 `K ≥ W + 1`，例如 `W=0, K=7, b=64, L=250` 得 `windowed_len = -6`。因此 **Codex 建议的 `W ≥ K` 校验是必要且充分的**，我当时的"驳回理由"不成立。
- `MRV2_Speculative_Draft_Sliding_Window_Design_gpt_dsReview.md` 的 **QG-G**：同上。
- 两处的 `W=0` 描述也需修正：`W=0` 不是"静默无效"，而是"窗口收缩到最后一个 block 边界"（`start = floor(L/b)*b`）。

建议在两份 review 的标题下各加一段 `> Corrigendum (2026-10-08)`，指向本附录。
