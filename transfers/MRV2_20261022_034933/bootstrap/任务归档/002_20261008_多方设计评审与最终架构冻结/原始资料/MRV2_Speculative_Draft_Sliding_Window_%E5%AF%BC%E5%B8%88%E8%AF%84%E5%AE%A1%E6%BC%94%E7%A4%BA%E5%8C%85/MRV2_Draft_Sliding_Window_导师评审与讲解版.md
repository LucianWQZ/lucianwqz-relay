# MRV2 Speculative Draft Sliding Window（`draft_window_size`）

## 面向导师的架构设计讲解与评审稿

> **用途**：现场讲设计 / 对照 MRV1–MRV2 源码 / 评审实施边界 / 作为开发与测试的导航。
>
> **设计基线**：`MRV2_Speculative_Draft_Sliding_Window_Final_Design.md`（2026-10-08，28 章）。本稿是**表达与组织重排**，不是重新决策的 v2：关键语义、架构取舍、证据状态、能力门槛、开放问题应与基线一致。冲突时**原 Final Design 为规范性准则**；本稿新增的“讲解语句/代码风格建议”不自动升级为 Frozen 决策。
>
> **当前状态**：`Architecture Freeze = CONDITIONAL`；`Required Delivery Coverage = NOT YET ESTABLISHED`。原文尚未报告本特性的 NPU/Graph/Async Window-ON 验证已通过。**可以进入有门禁的公共基础实现，不能宣布 Feature 全部完成。**
>
> **证据区分**：`[S]`=基线文档列出的 checkout 源码证据；`[M]`=数学论证；`[D]`=选定的架构决策；`[R]`=待运行时验证；`[G]`=能力 Gate。本文并未直接重新读取用户 Mac 上的源码文件；所列本地 `file:line` 是最终设计已记录的锚点，真正实施前仍需检查当前 checkout 的漂移。

---

# 第一部分｜给师傅讲的前 5 分钟

## 1. 一句话汇报：任务、问题、方案

**任务**：把 MRV1 中已有的 `draft_window_size` 特性迁移到 Ascend **ModelRunner V2（MRV2）**，覆盖公开的 `Eagle3 / DFlash / DSpark` Feature Contract，并保留 MTP `warning + ignore` 等行为。

**要优化的是什么？** 长上下文下，Draft Attention 读完整历史可能令 Draft proposal 质量下降。窗口化后，Draft 只读取最近一段 **block-aligned KV**；**Target、绝对位置、真实 KV 写地址及分配策略都不变化**。理论上的最终采样分布由原有 Target 验证机制维持；实际结果正确性仍要用适当测试验证。

**迁移难点**：MRV1 的 `SlidingWindowAdapter` 可修改 proposer 私有 Attention Metadata；MRV2 的表、长度、group、Graph Buffer 分属于多个 owner，且完整物理表可能被 Target/slot 计算共享，不能直接原地裁剪。

**核心设计**：

> Speculator 从 **Full State** 计算一次 Proposal Window Plan，再根据每个 KV group 的布局生成一份 **独立、持久、仅供 Draft Attention 读取的 View**；通过显式 Draft-only Metadata 输入进入 Backend。Full KV 写入路径和 Target 保持不变。

![图1：Full 物理世界与 Draft 读取世界](img/01_full_vs_draft.svg)

### 我希望师傅这次 Review 帮我确认什么？

1. **必交组合**：本次真实模型、Draft Backend、KV Groups、Graph Mode、并行方式到底是什么；这决定 DSA/SFA/FULL 是否必须前移。
2. **MRV1 兼容边界**：异构 group 的 legacy 缺陷是否按 canonical-S 修复语义，而非复制 defect；动态 K、`W<=0` / `W<K` 的策略谁拍板。
3. **MRV2 接入边界**：能否通过最小、显式、instance-scoped typed hook 接入 live/capture/replay；若 upstream hook 不可行，Graph ON 暂时拒绝。
4. **实施阶段**：先做 Policy/Planner/单 group eager 的可测纵向闭环，再按真实 Required Delivery 关闭 DSA/SFA、Graph、Async Gate。

## 2. MRV1 和 MRV2：与这个需求有关的差异

| 问题 | MRV1 | MRV2 | 对此次开发的意义 |
|---|---|---|---|
| 谁负责 Draft 推理 | `Proposer` 体系 | `Speculator` / `ModelRunner V2` 体系 | 新特性由 speculator 组织，不在旧 proposer 硬接 |
| 可修改的读取状态 | proposer 内较集中的 `common_attn_metadata` | 共享 `BlockTables` + Draft `InputBuffers` + per-group builder | 不能直接复用旧 `apply()` 的原地修改模式 |
| Block Table | Draft 私有 read metadata 更易替换 | full authoritative/gathered tables 是共享物理状态 | 必须建立独立 Draft read backing |
| 写入 `slot_mapping` | 旧实现确保从 Full Table 计算 | AR / DFlash/DSpark 的 slot 计算入口不同 | 所有物理 slot 必须先按 Full State 算好 |
| 多 KV Group | 旧 DSpark 路径有重复窗口/alias 缺陷风险 | builder 明确按 global gid 构造 | 单一绝对 S + per-group layout provider |
| CPU / Device 长度 | adapter 会改多个长度视图，但可出现不一致 | device exact / CPU exact / CPU upper / DCP local 消费者更分散 | 同源推导，禁止 Window 下隐式 full-length fallback |
| Graph | 旧 Metadata 可在 proposer 侧修改 | capture dummy、live、replay/update 分入口 | 必须验证实际 operator operand，不只看 Python metadata |
| Async | 旧迁移逻辑不能直接保证新生命周期 | host generation、device lane、backend-owned buffer | 需 generation lease + consumer-complete 才复用 |

![图2：MRV1 与 MRV2 的核心差异](img/02_mrv1_mrv2.svg)

### MRV1 目前可以依赖什么，不能盲目复刻什么？

- **继承**：Target 始终 full；只裁 Draft read；Full Slot Mapping 不变；proposal 级 anchor；`None=OFF`；MTP warning+ignore；公开 method 是 Eagle3/DFlash/DSpark。[S：最终稿 §4]
- **不把缺陷当合同**：MRV1 DSpark 的异构 multi-group 可对已 windowed 状态再次 apply、共享浅拷贝和 clone；动态 K 的 adapter offset 可能与运行时 K 不同步；Eagle3 后续跨 block 的 future column 可能未拷贝。[S：§4.4、§9.8]
- **政策尚未决定**：`W<=0`、`W<K` 的收紧要 maintainer 批准；plain Eagle 与动态 K 的 Window-ON 是局部 Open；这些不能因为某条旧代码能走通就视作正式兼容支持。

---

# 第二部分｜从一个请求贯穿整个设计

## 3. 先弄清楚五种容易混淆的数据

| 数据 | 通俗理解 | Window 是否改变 |
|---|---|---|
| Full Block Table | “历史 KV 在哪些真实物理块” | **绝不修改** |
| Window Read Table | “只让 Draft 从哪些物理块读取” | **新建独立视图** |
| `seq_lens` / 各种 Read Length | “本次 Draft 认为能读多少 token” | **Window 专用版本**，和读表统一起点 |
| `slot_mapping` | “新 K/V 应写到哪个物理槽位” | **绝不修改**，继续 Full/absolute |
| `positions` / `query_start_loc` | “模型真实 token 绝对位置与 query 形状” | **绝不改变其语义** |

一句话：**只改 Draft 的读取目录与读取长度，不改物理世界。**

### 3.1 数值例子：200 个 token，W=64，block size=16

假设当前 full end 为 `E=200`，DFlash/DSpark 在此 apply 点 `K=0`：

```text
W = 64，B_legacy = 16
H = E = 200
S = floor(max(H-W, 0)/B) * B
  = floor(136/16)*16
  = 128
Window read interval = [128, 200)
Window exact length  = 72
```

请注意 `72 > 64` **不是 bug**：legacy 语义要求 block 向下对齐，最多额外可见 `B-1` 个 token；这里额外 8 个。

比如 Full table（每列为一个 16-token block）：

```text
绝对 Block Index:  0  1  2  3  4  5  6  7 |  8  9 10 11 12
Full Physical ID:   11 25  7 40  6 18 31  9 | 55  8 29 43 62
                                               └─ Window ─────┘
Draft Window ID:                              [55,8,29,43,62]
```

`WindowTable` 不是把 KV 数据移动到了新地址，而是**复制 block id 读取目录**。原有物理 KV 仍原地存在。写入第 200 个 token 的 `slot_mapping` 仍应由绝对位置 200 与 Full Table/真实 KV allocation 计算，**不能**因为 Window 长度是 72 就把写入位置当成 72。

> **讲解时纠错点**：窗口的 `[S,E)` 是逻辑上 Draft 能看到的历史范围；在 native SWA / sparse / recycling Backend 上最终算子真正看到的集合还要与本地约束相交：`V_final = V_draft ∩ V_native ∩ V_resident`。不能只说“裁表就一定限住 DSA/SFA”。

## 4. 一份 Request 的 MRV2 完整执行路径

![图3：MRV2 Window ON 完整数据流](img/03_runtime_architecture.svg)

按图走，一次 Draft proposal 可以拆成这几步：

| 步骤 | 谁做 | 输入 → 输出 | 实际意义 |
|---|---|---|---|
| 0. `Policy + Inventory` | Speculator 初始化 | normalized method、W、actual backend/group/mode → 支持决策 | 先决定是否允许启用，不是靠 model name 猜 |
| 1. Full preparation | 当前 speculator/method | full seq、full table、positions → full slots/context writes | **先把该写的 KV 位置确定** |
| 2. `FullDraftKVSource` | 对现有 owner 的只读封装 | full table + length + valid count + request identity | 不改变原数据；来源有 generation 归属 |
| 3. `WindowPlan` | 纯数学 Planner | method horizon + W + legacy block alignment → `S,E,V` | 冻结一次 proposal 的窗口绝对起点 |
| 4. `LayoutProvider(gid)` | 每组 Backend/Layout | `[S,E)` → 该 group 的 read table、offset、indices/derived inputs | 统一语义但不强迫所有 backend 同布局 |
| 5. `GenerationLeasePool` | Speculator | 申请 backing → 拷入 narrow table/length/derived state | 数据独立、持久且不会被提前覆盖 |
| 6. `DraftMetadataInputs` | Typed transport | 每 gid read binding + typed lengths → Draft builder | **只能进 Draft**；Target 不接收 view |
| 7. `DraftMetadataStore` | Speculator | 新的 Draft layer metadata | AR Window ON 不复用 Target mutable metadata |
| 8. Draft Attention | 当前 Backend operator | 实际 `block_table`/length/indices → Draft outputs | Eager/Graph 最终消费者必须真的读当前代 |
| 9. Retire | Lease owner | consumer-complete event → 可安全复用 | async/Graph 不读到新一轮数据 |

这九步是逻辑职责，不意味着必须新写九个 Python 类。最终设计 §7.1 特别强调：**必要的边界应清晰，但不要 class 爆炸**。

### 4.1 为什么 `FullDraftKVSource` 必须有 generation / valid count？

举例：persistent table 行是 `[5,9,12,44,77,88,91]`，本轮 `valid_num_blocks=4`。最后三列有数字不代表本请求有这些 KV；可能是之前请求的尾巴。只按 tensor width 裁表会错误读取 stale block。

更难的是：同一个 batch row 在 finish/preempt 后，可能被新 request 复用，甚至 `valid_num_blocks` 一样。**所以仅靠 row index 或 block count，无法证明这是同一请求。**

必要原则：

```text
batch_valid_num_blocks[gid, row]
    ← persistent_num_blocks[gid, idx_mapping[row]]
    // 与 gather full table 同一 mapping、同一 generation

assert start_col + needed_cols <= min(source_row_width, valid_num_blocks)
```

如果 source 覆盖不到 `[S,E)`：**fail closed**。写几个 `0` 到缺失列虽然能避免越界，却不能补出语义上不存在的历史 KV。

### 4.2 为什么 Plan 必须与 Materialization 分开？

Planner 只决定“读哪个绝对区间”，不应知道 physical block id；Provider 和 Workspace 才将它翻译成真正的物理读表。这样：

- Eagle3/DFlash/DSpark 共用一份数学契约；
- 不同 Backend 可以独立提供 table/index/offset；
- Window OFF 不用经过额外物化；
- 后续 Graph/Async 可以复用同一个 Plan，但不能把已经窗口化的数据再次当 full 输入重复裁剪。

---

# 第三部分｜数学与方法差异：现场需要能讲清的细节

## 5. Window 核心数学（与规范性最终设计 §9 等价）

### 5.1 参数和公式

| 名称 | 含义 |
|---|---|
| `W` | `draft_window_size` |
| `B` | MRV1 从首个 Draft attention layer 选择的 `B_legacy` |
| `L0` | Eagle3 proposal 入口、**未扣本轮 rejection** 的 full device length |
| `K` | Eagle3 静态 speculative horizon；DFlash/DSpark 此 apply 语义用 0 |
| `H` | 一个 proposal 的冻结 horizon；Eagle3 为 `L0+K`，DFlash/DSpark 为 `E_prepared` |
| `S` | 一个 proposal 内**冻结不变**的 legacy window origin |
| `E_s` | step `s` 的 absolute full exact end |
| `V_s` | 本 step window exact，即 `E_s-S` |

```text
S   = B * floor(max(H - W, 0) / B)
V_s = E_s - S
0 <= S <= E_s <= H  // 每个 active row、每个 step 的运行时条件
```

**为什么 capacity ≠ runtime exact？** 只要 `E_s<=H`，窗口最长不超过 `W+B-1` 个 token，这是 Workspace 的安全容量**上界**；某一步真正有效的 `V_s` 可以更短。不能把 graph capture 时的 shape/capacity 误传给实际 Attention 作为 exact read length。

### 5.2 Short-context 分支

若 `H<=W`，`S=0`：短上下文下没有必要丢历史。此时的 `V_initial=L0`（对于 Eagle3），不是“窗口始终恰好 W”。

若 `H>W`，有余数 `ρ=(H-W) mod B`：

```text
H - S = W + ρ,   0 <= ρ < B
V_initial = (H - S) - K = W - K + ρ   // Eagle3 初始值
```

注意区分**proposal horizon**与**当前 step 的 E_s**。

### 5.3 Eagle3 的冻结起点与 rejection 反例

比如静态 `L0=203,K=4,W=64,B=16`：

```text
H = 207
S = align_down(207-64,16) = 128
```

后续 step 应始终用相同的 `S=128`，只变 `E_s`/`V_s`。不能每 step 带固定 `K` 重算 S，否则窗口会移动，改变 legacy proposal 语义。

**还必须考虑 rejection 后 `E_s` 下降**：

```text
B=64, W=K=4, L0=64
H=68, S=64
rejected=2, step=1: E_s=63 → V_s=-1
```

所以即使配置政策要求 `W>=K`，运行时仍必须检查 `S<=E_s`；不能只在初始化时做一次合法性检查。最终稿对此标记为 Frozen runtime invariant。

`W>=K` 需要明确量词：对于**固定 L**，它是 `V_initial>=0` 的充分但非必要条件；对于**所有可能 L/对齐余数**，它是保证非负的必要充分条件。是否统一拒绝 `W<K` 属于 maintainer 待批的兼容性政策。[Final §9.3、§18.4]

### 5.4 Window 表容量和非对齐 offset

对单 group、direct paged table 且每列连续覆盖 `span_g` token：

```text
start_col = floor(S / span_g)
offset    = S - start_col * span_g
needed    = 0, if V=0
            ceil((offset + V)/span_g), otherwise
```

若 offset 非 0，只有 Backend **实际消费该 offset**，才可以声称 `[S,E)` 没有额外暴露前面的 token；否则这一 geometry 不支持，必须换可证明的表达方式或 fail closed。

对 zero-offset 的容量上界：

```text
C_g >= ceil((W+B-1)/span_g)
```

对 offset-aware：至少覆盖 `offset + V_capacity`；具体上界由 Provider 给出。`needed<=capacity` 不够，还必须满足 **source coverage**。

```text
start_col + needed <= min(source_row_width, valid_num_blocks_g)
```

**别用错的恒等式**：`ceil((W+B-1)/B) = ceil(W/B)` 一般不成立；例如 `W=64,B=64`，左边为 2、右边为 1。[Final §9.5]

### 5.5 多 group 为什么不能统一拿 LCM？

假设所有组都要表达同一个绝对 Window 起点，不能让 group 0 从 128 开始、group 1 从 192 开始，否则不同 layer 的 Draft Attention 看见不同语义。

```text
L=300, W=128, K=0
B_legacy=64, group span=48
legacy S=align_down(172,64)=128 -> visible=172
LCM(64,48)=192
LCM S=align_down(172,192)=0 -> visible=300
```

“为了让列号整数化”而换成 LCM，反而使窗口多暴露 128 token，改变 MRV1 对外语义。**因此冻结的是 legacy S，是否能表达由每组 Provider 判断；表达不了就拒绝，不悄悄改数学。**[Final §9.7]

异构 MRV1 的旧缺陷若在 MRV2 修复，也需要 maintainer 决策，不应把故障字节级结果当 golden。[Final §4.4、§27 O-02]

### 5.6 Device / CPU length 为什么强调“同一个起点”？

假设 `full exact L=150`，CPU upper `U=200`，`W=100`，`B=64`：

```text
从 exact 决定唯一 S = floor((150-100)/64)*64 = 0
Window exact = 150-0 = 150
```

如果把 upper **独立**当作 exact 套一次 Window 数学，就会得到 `S_upper=64`、`U_window=136`；CPU upper 反而比 Device exact 150 小，明显不一致。

因此：**exact、upper、legacy CPU mirror 全部使用 canonical S；upper 是 planning bound 还是实际 read length，要由 Backend Consumer 的真实字段语义决定。**

规范形式：

```text
raw_upper = max(U_apply_time-S, V_s)
safe_cap  = min_g safe_materialized_extent_g
CpuWindowUpper = min(raw_upper, safe_cap)
require safe_cap >= V_s
```

另外，`_seq_lens_cpu` 若被 backend 选择器优先消费，不能留一份 Full 旧值；必须为 None 或与 CpuWindowExact 同源。Window ON 禁止掉入用 `max_seq_len` 填 full 大小的默认 CPU fallback。[Final §9.6、§8 I09–I11]

---

## 6. Method-specific：公共什么、特殊什么？

![图4：DFlash/DSpark 与 Eagle3 的不同接入时机](img/04_method_timelines.svg)

### 6.1 DFlash：Full Slot 先于 Window

```
Target hidden states
 → prepare_dflash_inputs(full gathered table)
 → full query/context positions、slot mappings
 → context KV write 所需准备完成
 → E_prepared 已包含 parallel query stretch（K=0）
 → WindowPlan / FullSource / LayoutProvider / Draft Read View
 → Draft-only build_attn_metadata
 → Draft forward
```

**禁止**把 Window table 预先写回 `input_block_tables[g]`，再调用 `prepare_dflash_inputs`：该 kernel 仍要依靠 Full Table 计算真实 KV slot。[S：`vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:375-409`，路径见源稿 S09/§12.3]

DFlash2：沿用并行准备/K=0 的概念，但保持当前 **eager-only**；Window 特性不能顺便宣称 DFlash2 FULL 已支持。

### 6.2 DSpark：时机相似，Backend 更复杂

DSpark 同样必须在所有相关 full table、物理 slots、context write 语义稳定后再构造 Window；但它的 **global KV group 与实际 Backend inventory** 可能涉及 DSA / SFA / DeepSeek-V4.1 逻辑索引和 derived buffer。不能用 `if model_name == ...` 代替实际能力检查。

更具体的阻塞例子：最终设计发现 `sample_from_anchor=False` 的 query width 可达 `K+1`，而现有 DSA index buffer 某路径按 `W+K`，该组合的 **non-causal DSA/V4.1 Window ON** 必须先修复并通过容量测试，否则不开放。[Final §12.4、§17.3]

### 6.3 Eagle3 / AR：先冻结 Horizon，再每 step 刷新 View

```
prepare_prefill_inputs（获取尚未扣 rejection 的 L0）
 → H=L0+static K → 算 S 并冻结
 → Window ON：新建 Draft-only first-pass Metadata Store
               不能继续复用 Target mutable store
 → first Draft forward
 → each subsequent step:
     full slots from absolute state
     apply rejection correction → E_s
     assert S<=E_s<=H
     从 Full Source 更新 Window table / length（不从上次 Window 再裁）
     新的 Draft metadata → Draft forward
```

**为何每 step 要刷新？** 即使 S 冻结，E_s 可能跨过一个新的 block boundary。旧 MRV1 clone 只在 proposal 入口复制当时已可见列，后续可能缺未来列；MRV2 要刷新自 Full Source 或在 proposal 起点预物化覆盖 horizon。[Final §9.8、§12.2]

动态 K：当前源稿发现旧 adapter captured configured K 与本轮 scheduled K 不一致的可能，因此 **Eagle3 dynamic-K Window ON 是 Open/Blocker**；不能自行“选择看起来更合理的一种 K”偷偷开通。

### 6.4 MTP 和其他方法

| 类别 | Window 配置行为 | 不要做的事 |
|---|---|---|
| MTP（含特殊 factory 路由） | 按 normalized method 先 warning+ignore，走 baseline | 不能因为实例落到 Eagle 类就启用 Window；不能先拒绝非法 W 再 ignore |
| plain Eagle | OFF 回归；ON 待产品合同决定 | 不因复用 Eagle3 类就声称支持 |
| Extract / token-only 等 | 依已有行为，不扩 Feature | 不凭空产生 Draft Attention view |
| DFlash2 | eager 按独立 gate，FULL 维持现有拒绝 | 不扩大既有图支持面 |

---

# 第四部分｜数据安全、Graph、Async：师傅会追问的三组问题

## 7. Ownership：到底谁能改什么？

| 对象 | Owner / 权限 | 关键约束 |
|---|---|---|
| Full `BlockTables`、Target state | Existing ModelRunner / shared owner | 只读观察；不得窗口化、不得被 Draft 持久指针覆盖 |
| `WindowPlan` | Speculator/Planner | 纯值，proposal scope；不可重复从 Window 数据生成 |
| `LayoutProvider(gid)` | 每 KV group 的 layout/backend | 负责坐标翻译、first-offset、native/resident 证明，不算全局 S |
| `GenerationLeasePool` | Speculator | 独立持久 read backing、host/device/derived buffer 的统一 retire |
| `DraftMetadataInputs` | 显式 typed 参数 | 只包含 Window read carrier；不替换 positions、query、slot_mapping |
| `DraftMetadataStore` | Speculator（Window ON） | 不 alias Target 的 mutable store；Window OFF 不改当前复用路径 |
| Graph `CaptureBindingProvider` | Graph manager 查询；Backing 由 speculator 拥有 | 用 descriptor/phase/step/lane 映射稳定 carrier；不自行拥有 full state |

**讲解重点**：Window 不是在 Target 和 Draft 公用的 `build_attn_metadata` 里根据某个全局 `is_draft` 标记偷偷运行。新的输入沿 **实例级显式参数**传给 Draft-only 构建路径；不能为了省改动新增 module-global/ContextVar/`_EXTRA_CTX`/thread-local 传 Window 数据。[Final §7.3、§10]

## 8. Graph：为什么同一个 Tensor 地址还不够？

![图5：Capture/Live/Replay 绑定与 Async Lease](img/05_graph_async.svg)

MRV2 至少要覆盖三个元数据入口：

| 入口 | 现有位置（基线锚点） | ON 时目标 |
|---|---|---|
| Live build | speculator / Ascend metadata funnel | 使用当前 generation 的 Draft-only read binding |
| Capture dummy | DFlash capture helper、AR/generic capture helper | capture 就看到合法的 Draft-only carrier，而非默认 Full Dummy Table |
| Replay/update | AR/DFlash ACLGraphManager | 更新/重绑真正 operator 读取的 carrier，且时序安全 |

当前源码没有直接携带完整 Window typed binding 的 capture 参数，所以 **Graph Window ON 当前不是 Ready**。最终设计建议最小 `default=None`、instance-scoped 的 upstream hook；具体 signature/可合并性是 `G-HOOK` 条件门禁。若不能提供可靠显式 hook：eager 路线继续，PIECEWISE/FULL Window ON 仍 fail closed，**不可退回新增全局 monkeypatch**。

Backend 实际取数方式必须逐个识别：

- `DIRECT_CAPTURED`：operator 直接 capture 了某块 backing 地址；检查捕获指针及数据代际。
- `TASK_REBOUND`：Graph task 参数在 replay 前重绑；检查真正生效的 kwargs/更新时序。
- `BACKEND_DERIVED`：Backend 把输入复制/派生到自己的持久 buffer；检查其 owner、更新及生命周期。

特别注意：Python 里的 metadata 已经指向新的 Window Tensor，**不证明 NPU 算子没有继续读旧的 capture backing**。混合 Backend 的 FULL updater 若只更新首个 executable backend，也不能声称所有层都正确。[Final §15]

### 8.1 A/B/A Graph 测试怎么讲？

选择三个代际 `A, B, A′`：Graph descriptor、形状、query width 保持相同，但 A/B 使用不同的合法 origin/物理 block id；A′语义上与 A 相同但代际不同。按 **A → B → A′** 连续 replay，和 eager oracle 比较。

它能揭露：B 还在读 A；A′还在读 B；任务更新晚一个 step；backend-owned buffer 未刷新；Graph 只绑定对了 table 却忘了 length/indices。还需结合实际 operand trace 和 event timeline，不能只比较输出就假定完全覆盖。[Final §15.5]

### 8.2 `enable_enpu` 不是一句“update 总在 replay 前”

通用 Graph wrapper 的 update/replay 顺序随 `enable_enpu` 变化；method-specific DFlash/AR graph manager 也有自己的固定时序。因此本特性必须**按实际消费路径**追踪 materialize、update、ExternalEvent、replay、attention、completion、retire。不在某条 wrapper 中执行的配置要标 N/A，不应为了“覆盖率”声称测试了它。[Final §15.4]

## 9. Async：Lease 是什么，为什么不能盲用一个 Persistent Tensor？

模拟：proposal A 已把 Window Table 写到 buffer X，NPU 尚在读；CPU 线程已经开始准备 B。若立刻把 B 覆盖到 X，A 的 NPU 就可能读到 B。地址固定并不能避免这一类错误。

因此数据有受控生命周期：

```text
FREE → ACQUIRED → MATERIALIZED → BOUND → SUBMITTED
     → CONSUMER_COMPLETE → RETIRED → FREE
```

`generation` 是“这份数据属于谁”的身份；`lease` 是“这块内存何时可以复用”的所有权。必须在最后 consumer completion 后才允许复用；Graph task update、backend-owned buffer 也纳入同一个 retirement 合同。

- Host generation/UVA pool 深度：`max_concurrent_batches` 只能当**下界**，最大未 retire reader 数需要 trace。
- Device lane 数：以实际执行流并发为准，不能直接令其等于 host 并发数。
- Graph capture 后已绑定的地址：不得用 realloc / `torch.cat` 等替换 backing 然后仍以为旧 Graph 会自动更新；有 TASK_REBOUND 机制的走独立验证。
- 缓冲池耗尽：**等待 retire / 使用 capture 前预留的合法 lane / fail closed**，不能覆盖 in-flight 数据。

最小阶段可以验证 **serialized eager** 且只有受控的一条 device lane；这不能自动解锁 async、多 stream 或 graph。[Final §14、§16]

## 10. DSA / SFA / 原生 SWA 与 Recycling：为什么不是公共裁表就够了？

最终可见的**绝对物理 KV 集合**满足：

```text
V_final(query) = V_draft(query)
               ∩ V_native(query)
               ∩ V_resident(query)
```

| Backend / KV 语义 | 不能假设什么 | 实际验证门槛 |
|---|---|---|
| Dense GQA/FIA | table 和长度正确就等于算子必然读取正确 | physical-slot oracle、padding、upper/exact 真实 operand |
| MLA | CPU exact 可以被 CPU upper 代替 | exact producer、legacy mirror、tiling/read consumer、Eager NPU oracle |
| DSA-v1 non-causal | rebase generator 数学自洽就等于完整算子自洽 | SAS/QLI/compressor/native/index/table、最终 slot set、graph/derived lease |
| DeepSeek-V4.1 DSA | 与旧 DSA-v1 的 index contract 完全一样 | logical indices、top-k length、SMLA/QLI 独立 Gate |
| SFA + indexer | 只改 `seq_lens` 或标量 top-k 数量就够 | per-token visible count、index translate/filter、absolute positions、两组 derived state |
| Recycling / chunked / R-SWA | `min(W, retention)` 是普适公式 | Resident KV 可为 prefix+tail/gap；按真正 physical resident set 集合证明 |
| DCP/CP/SP | 一列跨度普遍等于 `kernel_block_size*cp_size` | 每 rank 的 layout projection、local prefix diff、slot-set oracle |

**SFA Window ON** 目前是明确的局部 Open/Blocker，不是代码里加个 `if` 就能“支持”；实际 Delivery 若使用它，需要优先处理其 typed index/count 接口。

---

# 第五部分｜实施落点：哪些文件、怎么迭代、按什么标准合入

## 11. 预期源码修改地图（不是已修改文件）

下面的路径均相对当前基线对应的仓库根；行号以 2026-10-08 Final Design 记录为准，不是“跨版本稳定 API”。

| 实际文件/目录 | 本特性改造目标 | 禁止的捷径 | 对应源稿 |
|---|---|---|---|
| `vllm_ascend/worker/v2/spec_decode/draft_window.py`（建议新增） | policy、plan、typed lengths、layout-provider contract、workspace/lease（最初可少量数据类/纯函数） | 为每一职责造一个大类，或混入 ModelRunner 全局状态 | §22.1 |
| `worker/v2/spec_decode/__init__.py` | normalized method、OFF/MTP early path、Backend capability | 按 Python concrete class 猜 MTP / Eagle | §12.5、§18 |
| `worker/v2/attn_utils.py` | 新的 typed **Draft-only** Metadata Inputs、per-gid read binding、Window ON 不 fallback full lengths | 在 Target 通用入口新增隐式 Window 分支 | §7.3、§22.1 |
| `worker/v2/spec_decode/dflash/speculator.py` | Full prepare/slot 之后注入 view，K=0 | Window 提前替换 full gathered table | §12.3 |
| `worker/v2/spec_decode/dspark/speculator.py` | group inventory、真实 backend/derived gate、window view | DSpark 一律假设 dense paged table | §12.4 |
| `worker/v2/spec_decode/autoregressive/speculator.py` | Eagle3 `L0/H/S`、rejection、first-pass Draft Store、multi-step view | Window ON 继续 alias Target Store；每 step 重算 S | §12.2 |
| `worker/v2/spec_decode/{dflash,autoregressive}/aclgraph.py` | capture/replay binding、generation/lease/timeline | 只修 live builder，Graph 默读 Full Dummy | §15、§22.1 |
| 对应 Backend attention builder/provider | 声明 direct/rebound/derived、source/offset、padding、native/resident | 通过 model-name if 硬编码偏移或稀疏索引 | §11、§17 |
| Upstream `vllm/v1/worker/gpu/spec_decode/speculator.py`（**条件**） | 可选 `default=None` typed live metadata hook | 改变 OFF 默认行为 | §7.3、§22.2 |
| Upstream `.../dflash/cudagraph.py` / `.../cudagraph_utils.py`（**条件**） | 可选 capture-binding provider / Draft-only sink | 复制大段 builder 或新增全局 patch | §15、§22.2 |

**明确不改**：MRV1 `SlidingWindowAdapter`（除非独立 bugfix PR）、Scheduler/KV Cache Manager、Target Attention/验证/采样语义、真实 `slot_mapping` 算法、positions/RoPE、完整 KV cache allocation。[Final §22.3]

### 11.1 最小的接口形态（架构伪代码，非生产实现）

```python
# 示意：类型与职责优先，实际签名必须按当前 checkout 审查。

policy = resolve_policy(config, normalized_method, backend_inventory)
if policy.window_off_or_ignored:
    return run_existing_baseline()  # OFF/MTP路径不创建 Window Buffer

full = FullDraftKVSource.borrow_from_existing_owners(...)  # read-only view
plan = planner.begin_proposal(full, method_horizon)       # immutable S

# 注意：slot mapping / context KV write 的真正计算仍用 FULL 表、绝对位置。
full_slots = prepare_method_full_slots(...)

lease = window_pool.acquire(generation_identity)
per_gid = [provider.materialize(full, plan, lease) for provider in consumers]
inputs = DraftMetadataInputs(plan=plan, read_by_gid=per_gid,
                             lengths=typed_window_lengths, lease=lease)
draft_metadata = build_draft_only_metadata(inputs, original_query_layout,
                                           original_positions, full_slots)
execute_draft_forward(draft_metadata)
lease.retire_after_last_consumer_event()
```

上段只是解释“数据从哪来、归谁管”的结构示意，**不表示可以不顾 Full preparation 顺序直接照顺序运行**。真正的 Full Slot 时机见 §6；在 ON/OFF 两条路径中要保留原有 wrapper/factory/graph 行为。

## 12. 开发阶段与验收出口

![图6：从架构到实现的门槛路线](img/06_implementation_phases.svg)

| 阶段 | 开发内容 | 交付证明/退出条件 |
|---|---|---|
| **P0** | 与 owner 明确实际 Mandatory model/backend/gid/graph/parallel；检查源码漂移 | M-01～M-03 明确；具体接入点还有效 |
| **P1** | normalized policy + Window 数学/typed lengths | 纯数学 UT：short/active、LCM、W/K、AR rejection、MTP/OFF |
| **P2** | `FullSource`、有效块 gather、single-group direct-paged Provider | per-gid source coverage、不 alias、Stale tail 必被拒绝 |
| **P3** | Narrow persistent workspace、generation lease、Draft-only transport/store | 隔离/生命周期 UT；OFF 现有路径无漂移 |
| **P4** | 先做能通过 Gate 的 dense GQA serialized eager DFlash/DSpark 与静态 Eagle3 接入 | 真正 Attention 读取集合与 oracle 一致；Target full/write 不变 |
| **P5** | Graph typed hook 可行性 spike | live/capture/replay 可显式传递相同语义的 read binding；OFF 不变 |
| **P6** | 各 Backend Eager→PIECEWISE/FULL 的逐 consumer 开放 | actual operand fingerprint、A/B/A、event timeline、AR per-step |
| **P7** | 必需 Backend/Week4：DSA/SFA/V4.1、CP/DCP/SP/Flashcomm、Async | 每组合通过自身 slot-set、resident、parallel/lease Gate |
| **P8** | Owner Required Delivery、Window OFF、性能验收 | Mandatory Matrix 全绿，性能基线单独汇报 |

**现实优先级**：P0 未关闭不妨碍 P1～P3，但可能颠覆 P4/P7 的顺序。比如实际验收 Draft 是 SFA/DSA/FULL，就不能拿 GQA eager 的成功等同当前任务完成。[Final §21、§23]

## 13. Delivery Acceptance Matrix：用一张表防止“设计很美但交不了付”

> 以下不是我编造的已验证清单，是**最终设计中的状态重排**。原文 M-01～M-03 的 Required model/backend/group/graph/parallel 仍待 Owner Confirmation。

| 类别 | 组合 | 目前状态 | 师傅需要确认/后续验证 |
|---|---|---|---|
| **Mandatory TBD** | M-01 DSpark 所需主模型/Backend | **NOT ESTABLISHED** | 真实模型、Draft Backend、KV Groups、Graph/parallel |
| **Public contract** | M-02 Eagle3 | 未实现 Window ON | 要求的 eager/PIECEWISE/FULL；静态 K 及 first-pass store |
| **Public contract** | M-03 DFlash | 未实现 Window ON | 本次具体 Graph Mode 与目标 Backend |
| Regression | Qwen3/3.5 Eagle3、plain Eagle | OFF 必须保持现状 | plain Eagle ON 不自动支持 |
| Regression | Qwen3/Qwen3.6 DFlash/DSpark | OFF 必须保持现状 | single-group GQA eager 可作为初始候选 |
| Regression | DeepSeek-V4 DSpark | DSA ON 未过 Gate | native/index/resident/Graph |
| Regression | GLM-5.2 + DSpark | **Draft Backend 待 inventory** | Target SFA 不等于 Draft 一定 SFA |
| Regression | DFlash2 | eager-only baseline | Graph 路径继续按当前拒绝政策 |
| Regression | MTP 全系列 | warning+ignore | 无 plan/workspace，等同 OFF 行为 |
| Week4 / conditional | DSA-v1、V4.1、SFA、recycling、CP/DCP/SP/Async | 尚未过各独立 Gate | **若属于 Mandatory 就从 Week4 前移** |

即使已有这些 Regression 模型的测试，也不能代替师傅指定的 Required Delivery；真正的 acceptance 行应完整列出 **Model / Spec Method / Draft Backend / global gid / Graph Mode / parallel mode / 必测点 / Owner**。[Final §21]

## 14. 测试设计：哪些条件证明窗口真的生效？

| 测试层 | 核心断言 | 验证失败会怎样 |
|---|---|---|
| 数学 UT | `S/V` 与参考公式；rejection/LCM/容量/offset 边界 | 不能接入 NPU |
| Source/Provider UT | `start_col+needed<=valid`；不存在 Window-of-Window；Tail/Padding 安全 | 禁止该布局 |
| 状态隔离 | Full table、Target metadata、positions、slot mapping 在受控输入下不变 | 整个 Feature 不合格 |
| Dense eager | Backend **实际读取的物理 KV slot 集合**与 oracle 一致 | 该 backend 不开放 ON |
| CPU/Device 长度 | exact、legacy mirror、upper、capacity 同 origin；无 silent fallback | 该 backend 不开放 ON |
| Eagle3 | proposal 起点冻结；first-pass store 不 alias；跨 block future columns；rejection | AR ON 不开放 |
| DSpark sparse | DSA/SFA/QLI/SAS/top-k/index 与 native/resident 集合交 | 对应 Backend ON 不开放 |
| Graph A/B/A | Capture/Live/Replay actual operand 读的是**本代**；没有 one-step lag | 该 Graph mode ON 不开放 |
| Async stress | finish/add same-row、preemption、pool exhaustion、derived buffer last-reader | Async ON 不开放 |
| Window OFF 回归 | 既有 wrapper/factory/graph、输出和性能基线未产生新副作用 | 不能合入 |
| 性能 | 独立记录 materialize overhead、CPU sync、KV read、acceptance、延迟、吞吐、峰值显存 | 不得只报 acceptance 就宣称加速 |

**两个容易误用的 oracle**：

1. **不能仅因为 acceptance 提高，就证明 Draft 读取的物理 KV 集合正确**；需要 attention operand/slot-set 校验。
2. **不能用不同 Draft proposal 的两次自然生成过程直接比较 Target logits**；必须固定相同 Target 输入、候选、调度条件，才能有可比性。

---

# 第六部分｜MRV2 编码风格与 Code Review 注意事项

## 15. 这部分是什么性质？

本节是在 Final Design 的不变量、Expected File Changes、OFF/Graph/Async 门禁基础上提炼的 **MRV2 Feature 代码组织与可维护性建议**；不是声称 vLLM upstream 已规定这些 Python 风格。**现有项目的 lint/type/test 规则优先**，实际落地前应检查本地 `pyproject.toml`、同目录代码、已有测试风格。

### 15.1 不要把“抽象职责”机械变成“类的数量”

**推荐**：少量 pure function + 小型数据类/typed container + Backend provider 接口。先让单组 direct-paged eager 跑通，再因实际 Backend 差异扩展 Protocol。

**不推荐**：为了对应每个设计名词，创建 `PlanManagerFactoryRegistryAdapterFacadeContext` 等堆叠抽象；同一公式在 Eagle3、DFlash、DSpark 复制三份。

### 15.2 不要在公共 Full Owner 上做 in-place Window 修改

```python
# ❌ 反例，仅用于 Review 说明：会污染 shared full state
self.block_tables.input_block_tables[gid].copy_(window_table)
self.input_buffers.seq_lens -= window_start

# ✅ 设计方向：full source 只读；窗口落在独立 backing
full_source = borrow_full_source(...)
window_view = materialize_draft_read_view(full_source, ...)
```

- 不通过 `tensor.data`/原地 slice 把共享 full 表“临时改短再恢复”；async/Graph 下这种恢复顺序不可证明。
- `positions`、`slot_mapping`、scheduler canonical length 不归 Window 功能拥有。
- Window 源需要具有**source identity 和 valid count**，不能简单约束 source `.data_ptr()==某个 input_block_tables`：合法 caller-provided gather destination 也可能出现。

### 15.3 保持 Window OFF 的早返回，且必须保留现有 Ascend baseline wrapper/factory

```python
# ✅ 思路：在分配/构造 Window 之前先做行为决策
method = normalized_speculative_method(...)
if window_size is None:
    return baseline_path(...)
if method == "mtp":
    warn_and_ignore_once(...)
    return baseline_path(...)
```

重点不是“完全没有任何新 Python 分支”，而是：**OFF 不额外分配 Tensor、不建 Window Plan、不重建 AR first-pass Metadata、不增加 Graph key / kernel、不绕过已存在的 Ascend wrapper/factory**。最终设计专门纠正了“为了 Feature OFF 去删除旧 wrapper”的错误。[Final §18.3，CR-10]

### 15.4 区分 exact / upper / capacity；名称和接口别混

```text
DeviceFullExact       # full absolute E_s，只读
DeviceWindowExact     # E_s-S，供Draft read
CpuWindowExact        # 同一E_s-S的合法CPU exact producer
LegacyCpuMirror       # None或同源
CpuWindowUpper        # 规划上界，不一定可当真实KV长度
CaptureCapacity       # 静态 buffer 形状容量
BackendEffectiveMax   # 实际Backend消费的有效上界
```

**严禁**使用一个模糊的 `max_seq_len` 同时承载 CPU read length、graph capacity 和 backend tiling。对 Unknown/Absent 的 CPU exact，应由当前 Backend 契约决定是否拒绝；**不要偷偷 `.cpu()`/`.item()`/`.tolist()` 在热路径造 D2H 同步**（如果已有 D2H 基线，至少不能因 Feature 新增或放大）。

### 15.5 global gid、request row、step、generation 不要互相替代

```python
# ❌ 错误方向：认为draft_idx就是global gid，或batch row就是persistent request id
view = views_by_group[draft_layer_index]
num_blocks = persistent_num_blocks[gid, batch_row]

# ✅ 设计约束：global gid + same-generation idx_mapping
view = views_by_global_gid[gid]
request_row = idx_mapping[batch_row]
num_blocks = persistent_num_blocks[gid, request_row]
```

真实代码中要遵循当前 `BlockTables` gather 机制；伪代码只是强调坐标和身份。所有 active tail/padded rows 必须按 generation 重新写合法 inert 值；**不允许用“上次留下的数据应该没事”作为不变量。**

### 15.6 每一个 Backend capability 声明都要有消费者证据

不要这样做：

```python
# ❌ 过宽：只按模型名决定所有group/backend都能裁表
if model_name.startswith("DeepSeek"):
    enable_window = True
```

应做：配置 normalize → 完整 inventory（global gid、backend、KV spec、native/resident、causal、graph route、parallel mode） → per-consumer capability check → required group 全满足才启用。对不支持的组合给清晰错误（method/model/gid/backend/mode/failed gate），而不是配置看似生效、实际上静默切回全历史。

### 15.7 流水线接入保持现有代码最小侵入

- **不要**为了 Window 改 Scheduler、Target 或 slot kernel；用已有 method 的 full preparation、metadata builder hook。
- Shared upstream live/capture 改动只用最小的可选 `default=None` typed hook，保持 Window OFF 行为；**hook 精确签名在 G-HOOK 之前是 Conditional，不应当成已验证接入点**。
- 优先局部独立函数、小数据类和清晰的类型签名，不修改全局 ContextVar/module monkeypatch 运输新的 view；既有 Ascend patch 属于 baseline，不要误删。
- 在 PR 中把数学、source/layout、metadata、graph/async 拆成可独立测试、可回滚的变更；不要第一笔 PR 就跨所有 Backend 大改。

### 15.8 Persistent Buffer 的 Tensor 风格注意事项

- Workspace 初始化/graph capture 前分配已知容量；Window ON 每 generation 按**实际 active + padding 范围**确定性刷新，不依赖旧 tail。
- NPU Device Buffer 的写入与 consumer 读取须由流/Event/Lease 约束；不因为 Python 对象仍在就认为内存安全。
- 避免 graph-captured 路径的隐式 `torch.cat` / `.clone()` / 重新分配（可能改变实际 operand backing）；若 Backend 必须生成新的 derived tensor，要有匹配的 `TASK_REBOUND` 或 `BACKEND_DERIVED` 实测证明。
- 不要只比 `.data_ptr()` 判断 alias：不同 view 可共享 storage；需要检查底层 storage 区间的重叠关系。
- 对 source coverage 用硬断言 / 明确诊断；**不能**把不存在的物理 KV 用填 0 冒充已完成 Window 功能。

### 15.9 测试和日志风格

- UT 优先纯整数参考实现（数学测试不需要 NPU）；再逐步扩到 Device/Backend 的真实 slot set。
- 添加**负向测试**：非法 origin、source 缺块、缺 CPU exact、rejection 负长、错误 generation、Graph stale、提前 lease reuse 应能明确失败。
- 日志中打印 method、gid、`W/B/H/S/E/V`、source valid/needed、gate、descriptor/lane/generation；量大时做可控 debug，不在高频热路径无限输出。
- 不泄露用户 prompt、请求私有内容或绝对 KV payload；日志只记录必要的形状、索引和统计。
- 使用与项目一致的 import、命名、linter/formatter、test parametrization；不凭这份演示稿声称某条工具链或导入规范是“官方 MRV2 专用风格”。

### 15.10 给师傅的 Code Review Checklist

| 检查项 | 通过标准 |
|---|---|
| OFF 路径 | 原 factory、wrapper、graph、Target store 不变；Window 不分配 |
| 语义边界 | Target/full/slots/positions 不被窗口化 |
| Planner | 静态 K/parallel K=0；proposal S 冻结；逐步 S<=E<=H |
| Provider | global gid、offset、valid blocks、resident/native 校验 |
| 长度 | Device exact、CPU exact/mirror/upper、capacity 同源正确 |
| Metadata | Draft-only typed transport；Window ON 独立 Draft store；无隐式全局状态 |
| Graph | 三入口、actual operand 和 timeline，失败组合不开放 |
| Async | last consumer 完成后才 reuse，不以 host 并发猜 device lane |
| Backend | DSA/SFA/V4.1 独立测试，未过 Gate fail closed |
| 测试 | oracle 不只看 acceptance，含负向边界与 OFF 回归 |

---

# 第七部分｜实际评审会议怎么讲

## 16. 12–15 分钟讲解路线（可以直接照着讲）

| 时长 | 给师傅展示 | 重点说什么 | 要得到什么反馈 |
|---|---|---|---|
| 0:00–1:30 | §1、图1 | 只裁 Draft Attention read，不改 Target 和物理 KV 写地址 | 需求理解一致？ |
| 1:30–3:00 | §2、图2 | MRV1 私有 metadata，MRV2 共享 full state；旧 `apply()` 不能照搬 | 边界方向合理？ |
| 3:00–5:00 | §3–§4、图3 | FullSource → WindowPlan → per-group Provider → Workspace → Draft-only Metadata | 模块 Ownership 是否清楚？ |
| 5:00–7:00 | §5、数值例子 | S 对齐、S 冻结、CPU 上界同源、多 group 禁止 LCM | Legacy contract 是否要调整？ |
| 7:00–9:00 | §6、图4 | DFlash/DSpark 在 Full slots 后；Eagle3 首步特殊且逐步刷新 | Method 接入点是否认可？ |
| 9:00–11:00 | §8–§10、图5 | Graph 三入口/operand；Async lease；DSA/SFA 按 Gate | 必须的 Graph/Backend 是哪些？ |
| 11:00–13:00 | §11–§14、图6 | 预计改哪些文件、按什么顺序实施和验收 | 排期/代码边界是否可接受？ |
| 13:00–15:00 | §13 / §17 | owner 先确认真正 Required Delivery 与局部 Blocker | 关闭关键决策与评审结论 |

### 可以直接读的开场白（约 60 秒）

> 师傅，这次设计的核心不是把 MRV1 的 SlidingWindowAdapter 在 MRV2 再调用一次。MRV1 裁的是 proposer 自己的 Draft metadata；MRV2 里物理 BlockTables 与 Target、KV slot 计算存在共享，并且 Attention Metadata 由多个 Group/Backend 构造，Graph 还有 capture 和 replay 两个额外入口。所以我把它拆成 Full Physical State 与 Draft Read Plane 两层：前者不动，后者由 Speculator 基于一次 proposal 固定的窗口起点生成，每个 group 根据真实 layout 投影到自己的读取表或索引，再通过 Draft-only metadata 交给算子。这样可以保证 Target 和真实 KV 写入不受影响，也能为后续 Graph/Async 加上持久 Buffer 和生命周期保护。当前公共架构可以开始落地，DSA/SFA、Graph、异构 group 等仍有明确验证 Gate，最重要的是先确认本次验收模型的真实 Draft Backend 和 Graph 组合。

## 17. 师傅可能会问的 12 个问题（答题卡）

**Q1：这个是不是只有一个窗口裁剪操作，为什么要设计这么多层？**

A：窗口公式简单，但 MRV2 的 Full Table、query/slot、per-group builder 与 Graph/Async 属于不同 owner。Planner/Provider/Store/Lease 是职责边界，可以少类实现，但数据隔离不可省。

**Q2：为什么不能在 `_build_attn_metadata` 直接对 table/seq_lens 做 in-place？**

A：这些 Full 数据有共享消费者，slot_mapping/DFlash prepare 仍需要完整物理表；Window 只属于 Draft read path。in-place 无法证明 Target、未来 step 或 Graph consumer 不受污染。

**Q3：真实 KV Block 会不会被搬动？**

A：不会。Window 物化的是读取目录/长度/必要的 Backend 派生索引，不改变 KV allocator、cache residency 或物理写位置。

**Q4：为什么窗口设 64 却可能读 72？**

A：MRV1 的 block-aligned 起点向下取整，legacy overshoot 上限为 B-1；不能为了“刚好 W”擅改算法。

**Q5：不同 block size 取 LCM 不更容易吗？**

A：LCM 可能使窗口起点过早，例 `64/48` 对齐从 128 变 0、实际读历史大幅扩张。应保持 canonical legacy S，由 Provider 声明能否表达；不能表达则 Gate。

**Q6：为什么 Eagle3 和 DSpark 不同？**

A：Eagle3 AR 在 proposal 初始取 `L0+K` 计算 S，之后每步 E 变化而 S 冻结；DSpark/DFlash parallel preparation 已把 query stretch 包含在 E，apply offset 是 0。

**Q7：Eagle3 first-pass 为什么不继续复用 Target metadata？**

A：Window ON 后 Draft read table/length 必须与 Target 不同；复用/修改 Target store 有污染风险，所以 ON 要有独立 Draft Store。OFF 仍保留既有复用逻辑。

**Q8：Graph 里只保持 Tensor 地址固定还不行吗？**

A：不够。Backend 可能 capture 了另一个 tensor、task rebind 到其他参数或复制到 derived buffer；必须验证 actual consumer operand 和 A/B/A replay、event timeline。

**Q9：为什么 persistent buffer 还要 lease？**

A：同一地址也可能被下一轮提前写入；最后一个 NPU reader 完成前不能覆盖。host concurrency 与 device lanes 不是一个概念。

**Q10：DSA/SFA 不是裁了 table 就完成吗？**

A：DSA 可能通过 native sparse indices、SAS/QLI/compressor 真实取数，SFA 有 top-k logical indices；必须验证最终可读物理 slot 集合，不能只看 CPU 长度或 acceptance。

**Q11：本次是不是要求一次支持所有方法所有模式？**

A：架构覆盖公开 contract（Eagle3/DFlash/DSpark），具体启用按 Backend/Graph/Parallel Gate；但 Owner 实际 Mandatory 的组合必须优先完成，不能把必交推到以后。

**Q12：先实现什么、怎么证明完成？**

A：先确认 Mandatory Matrix + 实现纯数学/来源/布局/隔离，再做一条真实 eager slot-set 对拍；Graph/DSA/SFA/Async 逐消费者关闭 Gate，最终以真实 Delivery Matrix 和 OFF Regression 为准。

---

# 第八部分｜严格保持与 Final Design 的等价关系

## 18. Frozen / Conditional / Open：不是一张“所有都支持”的表

| Status | 含义 | 当前实际行动 |
|---|---|---|
| **Frozen** | 数学/架构边界和设计取舍已经确定；**不是已经写完代码** | 允许按约束开发 |
| **Conditional** | 实施路径已选，但对应 Backend/Graph/Async Runtime Gate 未通过 | 可以做不依赖的部分；该组合不能宣称 Window ON 可用 |
| **Open / Blocker** | 缺少产品决策、Operator 契约或可用入口 | 只阻塞明确受影响的 method/backend/mode 或 Delivery 结论 |

源稿 **Conflict Resolution：32 项，其中 11 Frozen / 15 Conditional / 6 Open**；**Decision Log：37 项，其中 20 Frozen / 11 Conditional / 6 Open**。下表摘录其中最影响代码走向的结论；完整 ID、原文证据与状态保留于 ZIP 内的规范性原文件（§25–§27），请 Review 时按 ID 逐条对照。

| 原始决策 ID | 本稿对应论点 | 结论/状态 |
|---|---|---|
| DL-01/02/03 | Speculator-owned read plane；Full/Target 不动；OFF baseline | Frozen |
| DL-04/05 | Eagle3/DFlash/DSpark 合同、MTP warning+ignore | Frozen |
| DL-06/07/08/09 | Static-K/Eagle L0/K、DFlash/DSpark K=0、禁止 LCM | Frozen |
| DL-10/11 | 单一 S、per-group 投影；异构 MRV1 defect 处理 | 前者 Frozen；后者 Open |
| DL-12/13/14/15 | 容量上界/offset/W/K/逐步 E 校验 | 数学与 runtime invariant Frozen；offset/policy Conditional |
| DL-16/17/18/19 | Typed length、valid source、Draft store、显式 transport | Frozen |
| DL-20/21/22/23 | Optional hook、graph route、Graph mode、AR per-step length | Graph route原则 Frozen；具体 hook/mode Conditional |
| DL-24/25 | unified generation lease、host vs device lanes | 原则 Frozen；资源数量/trace Conditional |
| DL-26～30 | Native 集合交、GQA/MLA/DSA/V4.1 分别启用 | 集合交 Frozen；实际 Backend Conditional |
| DL-31～35 | SFA/plain Eagle/dynamic K/DSA K+1/Required Delivery | Open / Blocker（局部） |
| DL-36/37 | Week3 有 Gate 的公共实现；Week4 延展架构 | 分别 Conditional / Frozen |

## 19. 条件 Gate / Blocker 的“师傅评审问题清单”

| Gate / Blocker | 现在不知道什么 | 怎么关闭 / 由谁决定 | 未关闭时 |
|---|---|---|---|
| O-01 Required Delivery | 必交模型/Draft Backend/gid/Graph/Parallel | **师傅/项目 Owner** 明确验收配置清单 | 不宣布 Required Delivery Covered |
| O-02 Heterogeneous group | 修复 MRV1 旧缺陷是否改变承诺 | Maintainer 确认 canonical-S semantic repair | 异构 ON 拒绝 |
| O-03 plain Eagle | 是否是公开 Window 合同 | Maintainer policy + golden | Eagle ON 拒绝；OFF 回归 |
| O-04 Dynamic K | configured K 还是本轮 scheduled K | Maintainer + boundary golden | Dynamic-K ON 拒绝 |
| O-05 SFA interface | per-token count/index 如何传给最终消费算子 | Backend Owner + operator oracle | SFA ON 拒绝 |
| O-06 DSA K+1 | 非 causal query width / indices 容量错配 | Backend Owner + actual q_max/slot oracle | 对应 DSA/V4.1 ON 拒绝 |
| O-07 Upstream hook | capture 是否能显式接收 Draft Binding | vLLM/Ascend Owner + hook spike | 受影响 Graph ON 拒绝；eager 可继续 |
| G-GQA-EAGER / G-MLA | Backend 真实读哪些 slots/lengths | Backend test、NPU oracle、CPU exact audit | 分别不开放 ON |
| G-GRAPH / G-MIXED | 三入口、任务指针、first-backend updater | trace + A/B/A，必要时聚合 updater | 对应 FULL/PIECEWISE 拒绝 |
| G-ASYNC | 最后 reader、pool 深度、device lane | Stream/event stress | async Window ON 不开放 |
| G-DSA1 / G-V41 | index/SAS/QLI/resident 全链 | 逐 query physical-slot oracle | DSA/V4.1 ON 不开放 |
| G-RECYCLING / G-PARALLEL | Resident set / rank-local mapping | resident 快照、rank-by-rank oracle | 对应 KV/并行组合拒绝 |
| G-CONFIG | `W<=0` / `W<K` 兼容政策 | maintainer + tests/docs | 暂按 Final Design interim fail closed |

## 20. 保留的架构不变量（适合师傅一屏审核）

| 组别 | 核心必须满足 |
|---|---|
| **不变的 Full 世界** | Target/full tables/positions/query/slot mapping 不被 Window 改动；Window OFF 保持原调用链 |
| **Window 数学** | proposal S 只算一次；所有 gid 同绝对区间；Legacy B 而非 LCM；`0<=S<=E_s<=H` |
| **数据来源** | 每代从 canonical Full Source 刷新；不能 Window-of-Window；需要 valid-count coverage；不以 inert 填补缺 KV |
| **Read Metadata** | table/Device exact/CPU exact/CPU mirror/upper/derived state同一 Plan；不能 full fallback；Draft Store 不 alias Target |
| **Graph** | capture/live/replay 三入口；actual operator route + event 证明当前 generation |
| **Async** | host/device/backend buffer 同 lease；最后 consumer 完成才 retire，pool exhausted 不覆写 |
| **Native** | 最终绝对物理可见集合 = Draft ∩ native ∩ resident |
| **Fail closed** | 不支持的组合在 capture/forward 前报带 method/backend/gid/mode/gate 的错误；MTP 既有 ignore 除外 |

## 21. 规范性章节快速索引（可在会议中直接跳到原稿）

| 演示稿章节 | 对照最终设计章节 |
|---|---|
| §1–§2 背景 / MRV1-MRV2 | 原 §1、§4–§6 |
| §3–§4 一次请求 / 架构主链 | 原 §7、§8、§10、§13 |
| §5 Window 数学 / length / multi-group | 原 §9、§11 |
| §6 Method-specific | 原 §12 |
| §7 Ownership | 原 §7.1–§7.3、§10 |
| §8 Graph | 原 §15 |
| §9 Async / Lease | 原 §14、§16 |
| §10 DSA / SFA / native / recycling | 原 §11、§17 |
| §11–§14 改动位置、排期、交付与测试 | 原 §18–§23 |
| §15 MRV2 编码风格建议 | 从原 §7–§16、§18、§22 的架构约束整理，**新增的讲解/可维护性建议** |
| §16–§17 讲稿 / 问答 | 源稿 §1、§7–§28 的讲解式重排 |
| §18–§20 决策 / Gate / Invariants | 原 §8、§25–§28 |

---

## 结束语：请师傅确认的最终结论

这次设计的核心 **不是搬运一个旧 Adapter**，而是迁移其可证明的 Feature Contract，并让 Window 在 MRV2 中成为**由 Speculator 拥有、可跨 Backend、可与 Graph/Async 正确对接的 Draft-only KV Read Plane**。

**设计当前允许做什么**：可以启动 FullSource / Pure Planner / Per-group Provider / Typed Metadata / Workspace 的受控实现，并以单组 dense eager 做首个实际 NPU 纵向验证。

**设计当前不声称什么**：不声称 Graph、Async、DSA/SFA/V4.1、异构多 group、动态 K 均已可用；更不声称 Required Delivery 已达标。

**希望师傅拍板**：真实 Required Delivery Matrix、异构 MRV1 repair policy、W/K 数值策略、是否接受最小 upstream typed hook。这些决定 Week3/Week4 的优先级和最终验收面。

> **唯一规范基线**：请同时查看压缩包中的 `reference/MRV2_Speculative_Draft_Sliding_Window_Final_Design.md`，其中保留了原始 32 项 Conflict Resolution、37 项 Final Decision Log、各 Gate 及详细源码证据。演示稿不覆盖或替代原始冻结决策。
