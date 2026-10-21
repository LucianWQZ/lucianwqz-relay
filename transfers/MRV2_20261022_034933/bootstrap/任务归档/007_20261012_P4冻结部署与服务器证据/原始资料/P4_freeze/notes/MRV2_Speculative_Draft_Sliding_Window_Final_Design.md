# MRV2 Speculative Draft Sliding Window — Final Architecture Consolidation & Design Freeze

> 文档日期：2026-10-09（Asia/Shanghai）  
> 适用 checkout：`/Users/wenqingzhang/Desktop/vllm/{vllm,vllm-ascend}` 当前文件快照  
> 文档性质：唯一最终架构设计；不是实现记录，也不是 NPU 验证报告  
> Architecture Freeze：**CONDITIONAL**  
> Required Delivery Coverage：**NOT YET ESTABLISHED**
> 2026-10-09 Policy Amendment：MTP与DeepSeek-V4 co-trained DSpark forced OFF；Eagle3与其他eligible并行route跟随配置开关。

> **2026-10-10 Repository Boundary Addendum（当前实施约束）**  
> `R-REPO-01`：本Feature的production交付只允许修改`vllm-ascend`；
> vLLM必须保持精确baseline
> `84030bbe3d74d99bad477a3d2e37a973ccd8865c`且工作区干净。任何需要修改
> vLLM、私有patch或新upstream API的路径均不可交付。历史upstream live-hook
> prototype `040346928…`只证明技术可行性，不是依赖。P4a必须以Ascend-owned、
> instance-scoped、typed read path完成；Window OFF直接保持upstream super path，
> Window ON若局部复现metadata assembly，必须用strict parity与
> `UPSTREAM_DRIFT_GUARD`约束。该附录只收紧repository/implementation boundary，
> 不改变本文Frozen Window数学、Target/write-side full-context、Draft-only read
> visibility、forced-OFF policy或Graph/Async/backend Gates。  
> 新Gate：`G-ASCEND-ONLY-INTEGRATION`。其static closure证据记录于
> `P4a_Ascend_Only_Eager_Integration_Implementation_Notes.md`；真实
> `G-GQA-EAGER`仍需NPU physical-read oracle与profiler。

本文使用 **MUST / MUST NOT / SHOULD / MAY** 表示规范强度。状态只使用：

- **Frozen**：源码或数学依据可复核，架构取舍已明确；不表示代码或 NPU 测试已经完成。
- **Conditional**：方向确定，但指定 runtime/backend/graph Gate 通过前不得启用对应组合。
- **Open / Blocker**：尚缺产品决定、入口可行性或正确性证据；仅阻塞表中注明的范围。

---

## 1. Executive Summary

本设计以 Codex Final Design 的 **Speculator-owned Draft Window Read Plane** 为骨架，形成唯一数据边界：

```text
Canonical Full State
  -> Proposal-scoped Window Plan
  -> Draft-only Persistent Read View
  -> Backend-specific Derived Metadata / Graph Binding
  -> Draft Forward
```

最终裁决如下。

1. Target attention、绝对 positions、query layout、完整 block tables、物理 `slot_mapping` 始终保持 full/global；窗口只改变 Draft 的 **read visibility**。
2. `S_legacy` 必须先按 MRV1 的 legacy anchor 算出并在一次 proposal 内冻结；不得为了适配 group span 无条件改成 LCM 对齐。
3. 多 KV group 共享同一个绝对语义起点 `S_legacy`，但 table layout、first-token offset、容量、valid block count、native visibility、resident set 和 backend-derived state 必须逐 group 提供。
4. 2026-10-09 maintainer 产品策略冻结应用范围：MTP在请求配置窗口时 warning once并强制OFF；Eagle3严格跟随窗口开关；并行 speculative 中，DeepSeek-V4 co-trained DSpark在请求配置窗口时warning once并强制OFF，其他组合跟随窗口开关。两个forced-OFF分支都必须在窗口数值校验、inventory与workspace分配前短路。
5. Window ON 的 AR/Eagle3 metadata 必须进入 speculator-owned `DraftMetadataStore`，不得复用或改写 Target 的 `model_state.attn_metadata`。Window OFF 保留当前过滤/复用路径。
6. live、capture-time dummy、replay/update 三个入口必须显式接入同一个 typed Draft read contract。当前 helper 没有该参数通道，因此 FULL/PIECEWISE 不是默认 ready；若最小显式 hook 不被接受，Graph Window ON 必须 fail closed。
7. Graph 正确性由实际 operator/task operand 决定，不由 Python metadata 或“同一个 workspace 地址”单独证明。每种 consumer 必须分类为 `DIRECT_CAPTURED`、`TASK_REBOUND` 或 `BACKEND_DERIVED`，并通过实际 operand trace 与 A/B/A replay。
8. Host generation、device execution lane、backend-owned derived buffer 是三种不同生命周期。`max_concurrent_batches` 只能作为 host pool 下界，不能等同 device slot 数。
9. DSA generator 的局部代数、SFA top-k、compressor/QLI/SAS、native SWA 与物理 recycling 不能互相代替。总可见集合为集合交；没有 operator 级证据的组合保持 Gate。
10. DeepSeek Final Design §16.3 的容量上界在限定前提下可用，但其化简 `ceil((W+B-1)/B)=ceil(W/B)` 是错误的，本文已删除该证明。
11. 当前 checkout 没有 `.git` 元数据，且材料没有唯一指定本次 Required Delivery 的 model/backend/group/graph/parallel 清单。因此可开始 Week3 公共基础设施与 gated eager 实现，但不能宣称本次真实验收覆盖已经建立。

本轮没有修改 `vllm/`、`vllm-ascend/`、配置或既有测试；也没有执行任何 NPU 实验。所有 NPU、Graph、Async 结论均保持为待执行 Gate，而非“已通过”。

---

## 2. Source Baseline & Evidence Convention

### 2.1 输入完整性

六份强制材料均存在、可读取；没有缺失 Review：

| ID | Material | SHA-256 |
|---|---|---|
| DOC-C | `MRV2_Speculative_Draft_Sliding_Window_Final_Design_Codex.md` | `b11e4f7fb19c8df0d17ac79c26c8c0148e5c85e5d351c012a7d8526430dcfd27` |
| DOC-D | `MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md` | `6540fe78bdae6062c9d15291c6ea1250e71aa2e5544995d02842e6144c9867a2` |
| REV-DC | `MRV2_Final_Design_Codex_Review_By_DS.md` | `676a753cf4c413e7b395b9185de11853e6717b300a33537ba7d5307b39f769e7` |
| REV-CD | `MRV2_Final_Design_DS_Review_By_Codex.md` | `7d6ba78dd1777819152a6e462691e263dc1e44e11ba9e836f86e63b08af8ec14` |
| STAGE-G | `Sliding window原理_gpt.md` | `99b97a64d17a06bb5851ad29e18ee20acc50656c5f65da5ba6ab9711f3ae2796` |
| STAGE-C | `Sliding window源码_codex.md` | `29ea0faf45ebe01180bffb52c2260b891bd10210059d7efc51bcffa4eda75e35` |

上述文件均位于 `/Users/wenqingzhang/Desktop/Note/MRV2/`。DOC-C与DOC-D已按P01同步产品策略；两份Review与Stage材料保持原始内容。

### 2.2 Maintainer产品策略补充

| Evidence | Decision |
|---|---|
| P01（2026-10-09） | MTP：配置窗口时warning once并强制OFF；Eagle3：跟随窗口开关；并行 speculative：DeepSeek-V4 co-trained DSpark配置窗口时warning once并强制OFF，其他组合跟随窗口开关。 |

P01是应用范围与enablement policy的最新owner裁决，覆盖S22及旧Final中与该范围冲突的历史表述；它不改变Window数学、Target full-context语义或backend Gate。实现时必须用normalized method与集中定义的target identity predicate识别co-trained DSpark。当前checkout已有的精确predicate是target `hf_config.model_type.startswith("deepseek_v4")`（S24）；它应封装为policy capability，禁止在planner/backend中散落类名或模糊model-name判断。

### 2.3 Checkout 基线限制

`/Users/wenqingzhang/Desktop/vllm`、`vllm/` 与 `vllm-ascend/` 中未发现 `.git` 元数据，故不能诚实给出 commit SHA。本设计以2026-10-08读取的源码快照及2026-10-09 P01策略为基线；后续实现前 MUST 重新跑source-anchor drift check。没有commit身份并不改变源码证据优先级，但阻止把本文引用理解成跨版本保证。

### 2.4 核心源码证据索引

| Evidence | Current checkout source fact |
|---|---|
| S01 | MRV1 adapter 数学、单 clone、三种 CPU length 重算：`vllm-ascend/vllm_ascend/spec_decode/utils.py:83-169` |
| S02 | MRV1 取第一 draft layer kernel block size、method policy 与 `future_offset`：`vllm-ascend/vllm_ascend/spec_decode/llm_base_proposer.py:390-452` |
| S03 | MRV1 通用 apply 与 full table 计算 slot：同文件 `:1119-1127, 2058-2123` |
| S04 | MRV1 DSpark per-group shallow copy/repeated apply：同文件 `:2553-2618` |
| S05 | 动态 K 在 proposal 入口覆盖 `self.num_speculative_tokens`，adapter offset 未同步：同文件 `:950-989` 对照 `:437-452` |
| S06 | MRV2 speculator factory：`vllm-ascend/vllm_ascend/worker/v2/spec_decode/__init__.py:23-72` |
| S07 | Ascend metadata funnel 共享 lengths、逐 group table/slot：`vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:220-378` |
| S08 | 当前 wrapper/factory monkeypatch：同文件 `:1240-1281` |
| S09 | upstream speculator 从 full gathered tables/length 构建 draft metadata：`vllm/vllm/v1/worker/gpu/spec_decode/speculator.py:271-369, 514-533` |
| S10 | upstream AR prefill 直接复用 Target metadata；decode 逐 step 重建：`vllm/vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:303-344, 501-549` |
| S11 | Ascend AR FULL 从 Target store 起步、DSA/SFA updater no-op、CPU per-step update：`vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:654-776` |
| S12 | DFlash capture helper 内部直接取 full dummy tables，且没有 binding 参数：`vllm/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:24-71, 78-120` |
| S13 | AR/DFlash replay 的 metadata rebuild、replay/update 路径：`vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:132-207` 与 `vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:86-138` |
| S14 | Target `prepare_attn()` 把结果写入 `model_state.attn_metadata`：`vllm-ascend/vllm_ascend/worker/v2/model_states/default.py:44-121` |
| S15 | Graph updater 当前只选第一个 executable backend：`vllm-ascend/vllm_ascend/worker/v2/aclgraph_utils.py:122-135` |
| S16 | `enable_enpu` 改变 generic wrapper update/replay 顺序：`vllm-ascend/vllm_ascend/compilation/acl_graph.py:284-320` |
| S17 | `UvaBufferPool` 是盲 round-robin 且要求 reader retire：`vllm/vllm/v1/worker/gpu/buffer_utils.py:19-26, 61-106` |
| S18 | `max_concurrent_batches` 由 PP/async 决定；recycling 会保留 in-flight blocks：`vllm/vllm/config/vllm.py:589-610` |
| S19 | persistent BlockTables 拥有 per-group `num_blocks`，gather 会清 padded row：`vllm/vllm/v1/worker/gpu/block_table.py:41-75, 112-187` |
| S20 | DSA v1 non-causal DSpark physical/logical index generator：`vllm-ascend/vllm_ascend/attention/dsa_v1.py:420-503` |
| S21 | DeepSeek-V4.1 DSpark 使用 logical indices 并把长度交给 SMLA metadata：`vllm-ascend/vllm_ascend/attention/dsa_v41.py:823-891` |
| S22 | 公共 MRV1 文档只声明 EAGLE3/DFlash/DSpark，MTP ignore：`vllm-ascend/docs/source/developer_guide/Design_Documents/speculative_kv_sliding_window.md:17-30` 与 `vllm-ascend/docs/source/user_guide/feature_guide/speculative_decoding.md:462-507` |
| S23 | config 当前只有 `int \| None`，无正数或 `W>=K` validator：`vllm-ascend/vllm_ascend/ascend_config.py:482-498` |
| S24 | MRV1当前用target `hf_config.model_type.startswith("deepseek_v4")`识别DeepSeek-V4，并仅发DSpark advisory后继续构造adapter：`vllm-ascend/vllm_ascend/spec_decode/llm_base_proposer.py:415-448`；P01将该pair改为warning+forced OFF。 |

路径中省略的 `docs/...` 均以 `/Users/wenqingzhang/Desktop/vllm/vllm-ascend/` 为根。

### 2.5 证据标记

- **[S] Source**：当前 checkout 可直接复核的事实。
- **[M] Math**：列出前提、可复算的证明或穷举。
- **[R] Runtime assumption**：静态源码不足，必须由 trace/NPU 实验关闭。
- **[D] Design decision**：在多个可行方案间的明确取舍。
- **[P] Product policy**：maintainer/owner对应用范围的显式裁决。

实现事实的优先级为：当前源码 > 数学证明 > Stage 1–7 > Review > 本文推断。应用范围由最新[P]裁决；P01不被旧文档或code-reachable路径反向覆盖。两份Final一致仍不能取代[S]/[M]/[P]。

---

## 3. Scope / Non-goals

### 3.1 Scope

本文定义：

- MRV1 公共 Feature Contract 如何迁移到 MRV2；
- proposal anchor、长度、per-group table 与 capacity 数学；
- speculator、metadata builder、backend、Graph manager 与 async pool 的职责；
- Eager、PIECEWISE、FULL 的开放 Gate；
- Eagle3、DFlash、DSpark的契约覆盖，以及P01定义的MTP/DeepSeek-V4 co-trained DSpark forced-OFF策略；
- GQA/FIA、MLA、DSA-v1、DeepSeek-V4.1 DSA、SFA、native SWA/recycling 的组合边界；
- Week3 实现入口、Week4 扩展点、测试与真实 Delivery 验收矩阵。

必须区分：

| Concept | Meaning |
|---|---|
| Feature Contract | MRV1 对外已经承诺、设计必须解释的行为 |
| Implementation Readiness | 某 method/backend/mode 是否已有足够实现和 runtime 证据可打开 |
| Required Delivery | 本次项目 owner 真正验收的 model/backend/group/graph/parallel 组合 |

### 3.2 Non-goals

- 本文不写生产代码，不改配置与既有测试。
- 不重新定义 Target full-context 语义、绝对 position、query layout 或 KV 写地址。
- 不把 draft window 变成 KV eviction/recycling policy。
- 不借本迁移修正 acceptance algorithm、rejection accounting 或 native SWA 训练策略。
- 不承诺尚未执行的 NPU、Graph、Async 或性能结果。
- 不把 MRV1 已识别的异构 group、动态 K、aliasing 缺陷升级为公共契约。

---

## 4. MRV1 Feature Contract

### 4.1 对外契约

S22记录了历史公共契约；P01进一步冻结本次MRV2应用范围：

| Normalized route | `draft_window_size=None` | 配置非None窗口值 |
|---|---|---|
| MTP（含落入Eagle class的特殊route） | baseline OFF | warning once + **forced OFF** |
| Eagle3 | baseline OFF | Window ON，继续执行数值/capability/runtime Gates |
| DeepSeek-V4 co-trained DSpark | baseline OFF | warning once + **forced OFF** |
| 其他并行 speculative route | baseline OFF | Window ON，继续执行数值/capability/runtime Gates |
| plain Eagle | baseline OFF | 仍为Open / Blocker，不因Eagle3策略自动开放 |

forced OFF是显式产品策略，不是unsupported错误，也不是普通Window ON的silent fallback。它必须在Window数值校验、backend inventory、plan/workspace与Graph binding前返回baseline。DeepSeek-V4 co-trained route必须由显式model/training capability识别，不能依赖类名或模糊字符串。`plain eagle`虽在代码路由可达，但没有同等公开声明，不能仅凭共享AR类自动升级为公共契约。

Feature 语义是：

```text
Target read      = full context
Draft read       = recent, block-aligned visibility view
Draft/Target KV write = absolute physical slot from full table
positions/query layout = absolute and unchanged
```

### 4.2 Legacy anchor 与 method horizon

设 `W=draft_window_size`，`B_legacy` 为 MRV1 adapter 构造时选择的 kernel block size，`K` 为 `future_offset`：

```text
H[r]        = method-specific frozen proposal horizon
D[r]        = max(H[r] - W, 0)
S_legacy[r] = floor(D[r] / B_legacy) * B_legacy
```

- **Eagle3（静态 K）**：`H=L0+K`。`L0` MUST 精确定义为 `prepare_prefill_inputs` 写入 draft `input_buffers.seq_lens` 的 proposal-entry device 值，即**尚未扣本轮 rejection** 的绝对 end；动态 K 时究竟沿用 configured K 还是本轮 scheduled K 尚未形成可靠 MRV1 contract，组合先按 §27 fail closed。
- **DFlash / DSpark**：`future_offset=0`，因为 method-specific preparation 已把 query stretch 放入 apply-time `seq_lens`；`H=E_prepared`。
- proposal 内 `S_legacy` 冻结。后续实际 end `E_s` 变化时，read interval 是 `[S_legacy,E_s)`；不得逐 step 重新滑动 anchor。

这些结论来自 S01–S05 与 Stage 1/6。它们不证明当前 MRV1 对动态 K 或所有 rejection 边界都实现正确；相关组合见 §27。

### 4.3 保持 full 的数据

Window MUST NOT 修改：

- Target metadata 或 Target read visibility；
- `positions`、`query_start_loc`、query token count、causality；
- canonical/persistent full block tables；
- 由 full table 与绝对 position 计算的 `slot_mapping`；
- scheduler/request 长期长度；
- native cache allocation/recycling policy。

S03 明确显示 MRV1 即使裁剪 read table，仍取 `full_block_table` 计算 slot。

### 4.4 MRV1 不能充当 golden 的边界

MRV1 DSpark 多 group 路径在 S04 中：循环内对上一次已 windowed 的 `common_attn_metadata` 做 shallow copy；复用同一 adapter 与同一 `_block_table_clone`；`B_legacy` 来自第一 draft layer（S02）。因此异构 group 可能出现：

1. 后续 group 对已裁过的 length 再裁；
2. 早先 group metadata alias 的 clone 被下一 group 覆盖；
3. `start_block=S/B_legacy` 被错误用于不同 group span；
4. “逐位复制 MRV1”与“一个绝对可见集合”互相矛盾。

最终规则：单 group或所有 consumer 共享可证明相同 direct-prefix layout 时，MRV1 是 golden；异构 multi-group 的**缺陷输出不是 contract**。本文冻结 canonical `S_legacy` 语义，但异构 enablement 在 maintainer 批准“修 defect 而非复刻 defect”前为 Open / Blocker，并 fail closed。

### 4.5 Window OFF 与数值边界

- `None` 是唯一已确认的 OFF 表达。
- 公共文档说“any positive value works”，但当前 config 只做 `int | None`；`W<=0` 的既有行为并未形成可靠契约。
- method/model policy resolution MUST先发生：MTP与DeepSeek-V4 co-trained DSpark即使携带window值，也分别warning once并强制OFF，不进入数值验证、inventory、workspace或Window Graph路径。
- Eagle3和其他eligible并行route严格跟随开关：`None`走baseline，非None才进入Window ON Gate；不得把配置ON静默改成OFF。
- 对支持 method，`W<=0` 与 `W<K` 的最终产品政策尚需 maintainer 确认；在确认前 MRV2 MUST fail closed，绝不能把 `0` 偷换为 OFF，也不能 clamp。

---

## 5. MRV2 Existing Architecture

### 5.1 公共 funnel

S06 的 factory 分为 extract、DSpark、DFlash/DFlash2、普通 MTP、`use_eagle()`。S07 的 Ascend `build_attn_metadata()` 接收一份共享 `seq_lens`、CPU exact/upper、DCP local length，再逐 KV group 选各自 block table、slot mapping 和 builder。这是 Window read inputs 的唯一自然公共漏斗，但当前没有 typed Window input。

S09 显示 upstream `_build_attn_metadata()` 总是从 `self.block_tables.input_block_tables` 与 `self.input_buffers.seq_lens` 读取 full state，再为 upper 加 `step`。直接原地修改这些 owner 会污染 Target/slot/下一 step，故不可接受。

### 5.2 Method 分叉

- **AR/Eagle3**：非 FULL prefill 当前直接复用 Target metadata（S10）；decode 每 step 重新算 full slot 并 build metadata。Ascend FULL replay 又从 `self.model_state.attn_metadata` 过滤起步（S11）。Window ON 必须打破这个 alias。
- **DFlash/DSpark**：先解析P01 policy。eligible route才在full world准备query、context KV write与slot，再build draft metadata；DeepSeek-V4 co-trained DSpark在进入这些Window动作前forced OFF。
- **MTP**：有普通与特殊 factory 分支；method字符串不能代替normalized capability，所有MTP route均forced OFF。

### 5.3 Graph 的三个入口

1. capture-time dummy metadata；
2. live proposal metadata；
3. replay-time rebuild / graph task update。

S12 证明 DFlash capture helper 内部直接调用 `get_dummy_block_tables()`，签名没有 Window binding。AR generic capture 也通过 Target `prepare_attn()` 生成并存储 metadata（S14）。S13 的 replay 在 Python 层 rebuild metadata，但 actual operator 可能使用 captured pointer、task rebound 参数或 backend-owned derived buffer。三个入口任一未接通，对应 Graph mode 必须 fail closed。

### 5.4 当前已存在但不能滥用的机制

- S08 的 module monkeypatch 是 baseline Ascend transport；Window OFF 必须保留它，不能按 DeepSeek Final §27 的原文绕过。
- 新 Window state 不得再通过新增 module-global/context monkeypatch 隐式运输；这不携带 generation，也不能证明 async ownership。
- persistent full gathered tables 是 Target/公共输入，不是 Draft 私有窄 backing。

---

## 6. Final Design Goals

1. 逐位保持可证明的 MRV1 anchor/method timing，而不继承已识别 defect。
2. Target/full/write state 与 Draft/read state 在类型、owner 和存储上隔离。
3. 对每个 global KV group 表达同一个绝对 visibility domain。
4. 所有 length representation 有类型与 canonical origin；禁止 silent fallback。
5. live/capture/replay 使用显式、instance-scoped transport。
6. Graph 以 actual consumer operand 与 event 时序验收。
7. Async 以 generation lease 和 completion event 验收，而非地址稳定或 slot 数猜测。
8. backend/method/graph/parallel 能力逐维 gate；失败时在 forward/capture 前给出可诊断错误。
9. P01应用策略先于所有Window校验与分配；forced-OFF route有一次性warning但保持baseline数据路径。
10. Window OFF 在对象、调用链、Graph descriptor、输出与性能上保持 baseline identity。
11. 公共基础设施可扩展到 Week4，但 Week3 不预先打开未经验证的 DSA/SFA/CP/SP/Async。

---

## 7. Architecture Overview

```text
                         Canonical Full Source
             full seq / full tables / valid counts / positions
                                  |
                 normalized method + model/training policy
                       /                         \
        configured/forced OFF                eligible ON
          baseline path                          |
                                                 v
                         Proposal WindowPlan
                   S_legacy, E_s, generation, rows
                                  |
                +-----------------+-----------------+
                |                                   |
       Per-group LayoutProvider             Full slot mapping path
  map(S), offset, resident/native sets       (unchanged, absolute)
                |
        DraftWindowGenerationLease
 host exact/upper + device lengths + narrow tables
        + backend-owned derived buffers
                |
         DraftMetadataInputs (typed)
                |
     live build / capture binding / replay update
                |
          DraftMetadataStore (Window ON)
                |
      actual Draft attention operator/task
                |
         consumer completion -> retire lease
```

### 7.1 逻辑职责，不强制类爆炸

以下是职责边界，不要求每项都成为独立 Python class：

| Responsibility | Required abstraction | Owner |
|---|---|---|
| Policy/capability | pure decision先返回configured OFF / forced OFF / eligible ON；仅eligible ON继续inventory | speculator initialization |
| Proposal math | immutable `WindowPlan` value | speculator/planner |
| Full source | references only; never mutated | existing `BlockTables` / input buffers |
| Per-group layout | `LayoutProvider` protocol or pure functions | backend/layout registry |
| Lifetime | one generation lease pool | speculator |
| Transport | typed `DraftMetadataInputs` | optional upstream/private hook |
| Backend derived state | provider-owned but attached to same lease | backend builder/provider |
| Metadata sink | `DraftMetadataStore` when ON | speculator |
| Capture binding | descriptor/phase/step/lane lookup | graph manager using speculator provider |

### 7.2 Typed transport

规范上的 `DraftMetadataInputs` 至少携带：

```text
generation identity
descriptor / phase / step / execution-lane identity
per-global-gid narrow table binding
per-gid valid source count snapshot and provider version
DeviceWindowExact (proposal/step appropriate)
CpuWindowExact or explicit Absent
CpuWindowUpper (apply-time)
LegacyCpuMirror policy
DcpLocalWindowExact/Upper when applicable
actual/padded request counts and ordered request fingerprint
```

它 MUST NOT 携带或改写 positions、query layout 或 slot mapping。`None` MUST 表示 baseline path，并使 Window OFF 的函数参数、owner、Graph descriptor 和 metadata sink 与当前 checkout 等价。

### 7.3 最小显式接入方向

[D] 接入路线固定为 **可选、instance-scoped typed hook**：

- upstream live `_build_attn_metadata()` / `_build_uniform_attn_metadata()` 接收可选 read inputs；
- DFlash capture helper 与 generic AR capture helper接收可选 capture binding provider；
- Window ON 的 AR capture 使用 Draft-only builder/sink，不调用会写 Target store 的 `AscendModelState.prepare_attn()`；
- graph manager 已持有 speculator reference，由它按 descriptor/phase/step/lane 请求 binding；speculator 拥有 backing 与 lease；
- default `None` 保持现行行为。

这一定义冻结架构方向；精确 upstream signature 与可合并性仍是 Conditional Gate G-HOOK。若 hook 被拒绝，不允许退回新增全局 monkeypatch；Eager 可沿显式 speculator override 继续，Graph Window ON 被阻塞。

---

## 8. Invariants

| ID | Invariant | Status |
|---|---|---|
| I01 | Target metadata、Target table、Target length 不被 Window ON 修改。 | Frozen |
| I02 | `positions` 与 `query_start_loc` 保持绝对/full 语义。 | Frozen |
| I03 | 所有 KV writes/`slot_mapping` 从 full table 计算。 | Frozen |
| I04 | Draft read table 与 Draft read length 必须来自同一个 plan generation。 | Frozen |
| I05 | 一次 proposal 的 `S_legacy` 冻结；每 step 只改变 `E_s`/visible length。 | Frozen |
| I06 | 多 group 共享绝对 `[S_legacy,E_s)`，但不共享未经证明的列映射。 | Frozen |
| I07 | 不得以 LCM 改写 legacy anchor；无法表达时 fail closed。 | Frozen |
| I08 | `WindowPlan` 只能从 canonical full state 计算一次；rebuild 不得对 windowed 值二次窗口化。 | Frozen |
| I09 | `DeviceWindowExact` 是 read length canonical origin；CPU/list/max 值必须有明确 exact/upper 类型。 | Frozen |
| I10 | `_seq_lens_cpu` 必须为 `None` 或与 `CpuWindowExact` 同源；full 值不得赢得 backend priority。 | Frozen |
| I11 | apply-time upper 必须包含该 method 的 step/query stretch；不得从 proposal-entry full upper 直接裁。 | Frozen |
| I12 | `needed_g` 必须同时受 workspace capacity 与真实 `valid_num_blocks_g` source coverage 约束；缺源即报错。 | Frozen |
| I13 | active tail 与 padded row 每 generation 确定性重写；inert 值由 backend 合同定义。 | Frozen |
| I14 | Window ON 的 mutable Draft metadata store 与 Target store 不同一对象。 | Frozen |
| I15 | capture/live/replay 三入口都绑定同一 typed contract；遗漏任一入口即禁用该 mode。 | Frozen |
| I16 | Graph 验证对象是 actual operator/task operand 和 event timeline，不是 Python metadata identity。 | Frozen |
| I17 | `V_final(q)=V_draft(q) ∩ V_native(q) ∩ V_resident(q)`。 | Frozen |
| I18 | host generation、device lane、backend-derived buffer 分别计数，但共享一个 lease retirement。 | Frozen |
| I19 | lease 在最后 consumer completion event 前不得复用、扩容替换或改写。 | Frozen |
| I20 | row index、block count、固定地址均不能单独充当 generation identity。 | Frozen |
| I21 | pool exhaustion 必须等待安全 retirement、使用 capture 前预留容量，或 fail closed；不得覆盖 in-flight 数据。 | Frozen |
| I22 | Window OFF 不分配 Window workspace、不建 Window plan、不改现行 factory/store/graph key。 | Frozen |
| I23 | capability缺失在capture/forward前报出method/backend/gid/mode/gate；除P01两个显式warning+forced-OFF策略外，eligible Window ON不得静默降级。 | Frozen |
| I24 | `S_legacy <= E_s` 必须逐 active row/step 成立；配置级条件不能代替运行时断言。 | Frozen |
| I25 | P01 policy resolver先于W数值验证、backend inventory、workspace与Graph binding；forced-OFF route不得产生任何Window state。 | Frozen |

---

## 9. Window Mathematics & Visibility Domain

### 9.1 术语与 canonical 公式

对 request `r`、proposal step `s`：

| Symbol | Meaning |
|---|---|
| `W` | configured Draft window size |
| `B` | `B_legacy`，MRV1 第一个排序 draft attention layer 的 kernel block size |
| `L0[r]` | AR proposal 入口、未扣本轮 rejection 的 device full length |
| `K` | 静态 proposal horizon；动态 K 的来源仍为 Open，见 §27 |
| `H[r]` | 冻结右端：AR 为 `L0+K`；DFlash/DSpark 为 `E_prepared` |
| `S[r]` | `S_legacy`，proposal 内冻结的绝对窗口起点 |
| `E_s[r]` | step `s` 实际 full-coordinate exact end |
| `V_s[r]` | `E_s-S`，DeviceWindowExact |

```text
S[r]   = B * floor(max(H[r]-W, 0) / B)
V_s[r] = E_s[r] - S[r]
```

运行时 MUST 检查：

```text
0 <= S[r] <= E_s[r] <= H[r]
```

AR 中 rejection 后 `E_s` 可小于 `L0`，所以 `W>=K` 不能替代这条逐 step 断言。

### 9.2 short branch 与 active branch

对初始 `H=L+K`：

```text
H <= W:
    S = 0
    V_initial = L <= W-K

H > W:
    rho = (H-W) mod B, 0 <= rho < B
    H-S = W+rho
    V_initial = W-K+rho
```

由于 proposal 生命周期内 `E_s<=H`：

```text
0 <= V_s <= V_capacity = W+B-1
```

这是 workspace/layout capacity 上界，不是实际 read length。

### 9.3 `W >= K` 的两个量词

若固定一个具体 `L`，`W>=K` 是 `V_initial>=0` 的充分条件，但不是必要条件。对 `W<K`，令 `d=K-W>0`、`L=qB+r`：

```text
V_initial >= 0  iff d < B-r
V_initial <  0  iff d >= B-r
```

例：`L=100,B=64,W=3,K=4` 仍有 `S=64,V=36`。但 `L=63,B=64,W=1,K=2` 得 `S=64,V=-1`。

若量词是“对所有合法 `L`/所有 residue 都保证初始 `V>=0`”，则 `W>=K` 必要且充分。即便如此，rejection 后仍可能失败：

```text
B=64, W=K=4, L0=64
H=68, S=64
rejected=2, s=1 -> E_s=63 -> V_s=-1
```

因此：数学定理 Frozen；配置是否统一拒绝 `W<K` 为 Conditional 产品政策；逐 step `V_s>=0` 是 Frozen runtime invariant。

### 9.4 Per-group direct-prefix projection

仅对均匀 direct-paged provider，令 `span_g` 表示一列覆盖的连续 token 数：

```text
start_col_g = floor(S/span_g)
o_g         = S - start_col_g*span_g       # first-token offset
V           = E-S
needed_g    = 0                             if V=0
              ceil((o_g+V)/span_g)          otherwise
safe_extent_g = needed_g*span_g-o_g
```

若 operator 不能实际消费 `o_g`，则非零 offset 不可表达。provider 只能选择：

1. 证明该 row `S % span_g == 0`；
2. 使用 absolute-indexed/backend-derived 表达；
3. fail closed。

`span_g | B` 是所有 legacy anchor 都 zero-offset 的静态充分条件，不是一般必要条件。`span_g` 不能从 `kernel_block_size*cp_size` 一条公式推广到 PCP/DCP/SP/DSA/SFA；它由 provider 给出并由 operator oracle 验证。

### 9.5 Capacity、exact、upper 的关系

对 zero-offset provider，可选最小安全容量：

```text
C_g >= ceil((W+B-1)/span_g)
```

一般 offset-aware provider：

```text
C_g >= max_r ceil((o_max_g[r] + W+B-1)/span_g)
```

MRV1 的单 group allocation 是 `ceil(W/B)+1`，它是安全但不总是最紧。DeepSeek §16.3 的 `ceil((W+B-1)/B)=ceil(W/B)` 化简错误：

```text
W=100,B=64: ceil(163/64)=3 != ceil(100/64)=2
W=64, B=64: ceil(127/64)=2 != ceil(64/64)=1
```

对每 row、group：

```text
0 <= needed_g <= C_g <= destination_row_width_g
start_col_g + needed_g
    <= min(source_row_width_g, valid_num_blocks_g)
```

`valid_num_blocks_g` MUST 从 S19 的 canonical `BlockTables.num_blocks` 按同一 `idx_mapping`/generation gather。source 不足必须报错；把缺失列写成 inert 只保证不 OOB，不证明语义完整。

### 9.6 CPU exact、CPU upper 与 shared cap

长度类型：

| Type | Definition | Rule |
|---|---|---|
| `DeviceFullExact` | `E_s` | full owner，只读 |
| `DeviceWindowExact` | `E_s-S` | Draft read canonical origin |
| `CpuWindowExact` | 同一 `E_s-S` 的 CPU producer | 不存在则明确 Absent |
| `LegacyCpuMirror` | `_seq_lens_cpu` | `None` 或与 `CpuWindowExact` 同源 |
| `CpuWindowUpper` | planning/tiling upper | 不能冒充 exact |
| `CaptureCapacity` | backing shape limit | 不能冒充 read length |
| `BackendEffectiveMax` | backend 经证明的 max field | 由 consumer contract 决定 |

令 `U` 是**apply-time** full upper，已经包含 AR step 或 DFlash/DSpark query stretch：

```text
raw_upper[r] = max(U[r]-S[r], V_s[r])
safe_cap[r]  = min_g safe_materialized_extent_g[r]
CpuWindowUpper[r] = min(raw_upper[r], safe_cap[r])
require safe_cap[r] >= V_s[r]
```

若 backend 把 upper 当真实 read length而不是 planning bound，则必须提供 exact 或 fail closed。MRV1 对 full upper 独立重新算 anchor 会出现 `upper<exact`：`L=150,U=200,W=100,B=64` 时 exact 为 150，而独立变换 upper 为 136；MRV2 禁止该模式。

### 9.7 LCM 反例

不得将 anchor quantum 自动改为 `lcm(B,span_g)`：

```text
L=300,W=128,K=0,B=64,span=48
D=172
S_legacy=128, visible=172
lcm=192 -> S_lcm=0, visible=300
```

LCM 额外暴露 128 token，改变 MRV1 alignment。`LCM>W` 也不意味着 `S=0`；还需 `D<LCM`。例 `L=1000,W=128,LCM=192` 时 `S=768`。

### 9.8 AR future-column legacy defect

MRV1 用 `H=L0+K` 算 `S`，却只按 apply-time `L0-S` 复制列；后续 `E_s` 跨 block 时 clone 可能缺未来列。例如 `B=16,W=64,K=3,L0=64`：apply 只复制 4 列，后续 `E=65` 需 5 列。MRV2 MUST 每 step 从 immutable full source refresh，或预先 materialize 到 horizon capacity并用 exact length约束读取。该修复不改变 anchor/slot，但 AR readiness 需 maintainer 确认与 semantic slot-set golden。

---

## 10. Module Ownership & API Boundaries

| Module boundary | Owns | MUST NOT own/do |
|---|---|---|
| Product Policy | normalized method、W是否配置、显式model/training capability、configured/forced/eligible decision | 不物化tensor；forced OFF后不得启动inventory |
| Capability Inventory | eligible route的backend/group/mode enable decision | 不覆盖Product Policy，不把forced OFF重新打开 |
| Planner | `H,S,E_s,V_s` 与 generation | 不懂物理 block id，不重算 slots |
| FullSource | references to full tables/lengths/valid counts | 不接受 Window 写入 |
| LayoutProvider(gid) | layout mapping、offset、capacity、resident/native predicates、padding contract | 不改 global anchor |
| GenerationLeasePool | host/device/backend buffers与最后 consumer event | 不按 row index 推断代际 |
| DraftMetadataInputs | typed transport | 不含 positions/query/slots 的替代值 |
| DraftMetadataStore | Window ON draft layer metadata | 不 alias Target mutable entries |
| BackendDerivedState | indices/SAS/QLI/compressor/top-k 等 | 不脱离 generation lease |
| CaptureBindingProvider | descriptor/phase/step/lane -> persistent binding | 不拥有 canonical data |

建议 API 形状（名称可在实现 PR 中按项目规范调整，语义不可改）：

```text
policy.resolve(config, normalized_method, model_training_capability)
    -> CONFIG_OFF | FORCED_OFF_CO_TRAINED | WINDOW_ON_ELIGIBLE
capability_inventory.validate(...)  # only for WINDOW_ON_ELIGIBLE
planner.begin_proposal(full_state, method_state) -> WindowPlan
planner.for_step(plan, full_exact_end) -> WindowStep
provider.materialize(full_source, valid_counts, step, lease) -> GroupReadView
speculator.build_draft_metadata(inputs: DraftMetadataInputs | None) -> DraftMetadataStore
graph_manager.capture_binding_provider(desc, phase, step, lane) -> DraftMetadataInputs
lease.retire(consumer_completion_event)
```

Window plan、provider与workspace可以在一个 `draft_window.py` 模块中实现；本文不要求人为拆成多个类。

---

## 11. Per-group Layout / Backend Capability

### 11.1 Inventory 必须先于 enablement

`set_attn()` 后生成 immutable inventory，按 global gid/layer记录：backend class、KV spec、storage/kernel block size、causal、native visibility、recycling/resident semantics、CP/SP/DCP mapping、graph updater、padding contract、CPU exact需求、actual operator route。

同一 method 名不能替代 inventory；尤其 DeepSeek-V4、V4.1、GLM 路径会产生不同 backend/derived state。

### 11.2 Capability 维度

每个 group 必须分别回答：

1. `S` 能否表示；first-token offset 谁消费？
2. `[S,E)` 所需物理 source 是否 resident？
3. native visibility 如何与 Draft interval 求交？
4. exact/upper 的最终 consumer 是谁？
5. padding/tail 的 inert 合同是什么？
6. Eager 实际 operand 是谁？
7. Graph route 是 direct、task rebound 还是 backend derived？
8. derived buffer 是否 capture-stable且 generation-safe？

### 11.3 Readiness 表

| Backend/layout | Static evidence | Implementation readiness | Window ON behavior before Gate |
|---|---|---|---|
| Dense GQA/FIA direct prefix | builder/funnel与 direct table 可见 | Conditional；Week3 first candidate | fail closed until eager slot-set tests |
| MLA direct prefix | legacy updater可重绑，但 CPU exact/padding/derived state需证实 | Conditional | fail closed |
| DSA-v1 | index generator局部代数可证（S20） | Conditional；完整 op 同时消费 table/length/SAS/native/indices/compressor | fail closed |
| V4.1 DSA backend（仅eligible、非P01 forced-OFF route） | logical indices与SMLA metadata为独立路径（S21） | Conditional，独立 gate | fail closed；当前DeepSeek-V4 co-trained DSpark不进入该Gate |
| SFA + indexer | absolute-position top-k、builder-owned buffer、updater no-op | Open / Blocker for Window ON | fail closed |
| Recycling/chunked/R-SWA | resident set可能非连续、带 gap/overhang | Conditional provider proof | fail closed |
| Mixed executable backends | updater当前只选第一个（S15） | Conditional aggregation | FULL fail closed |

---

## 12. Method Integration

### 12.1 Feature Contract

| Method | Contract | Horizon/timing | Policy |
|---|---|---|---|
| Eagle3 | Yes | proposal entry `L0`, static `H=L0+K`, frozen S | 严格跟随配置开关；ON逐mode gated |
| DFlash | Yes | full prepare/slots 完成后，`future_offset=0` | 并行route，严格跟随配置开关；ON逐mode gated |
| DSpark（非DeepSeek-V4 co-trained route） | Yes | full prepare/per-group inventory后，`future_offset=0` | 严格跟随配置开关；ON逐backend gated |
| DeepSeek-V4 co-trained DSpark | Forced OFF by P01 | 不进入Window timing | 配置非None时warning once + baseline |
| MTP（含特殊 factory 分支） | Forced OFF by P01 | 不创建 plan/workspace | 配置非None时warning once + baseline |
| plain Eagle | No public proof | shares AR mechanics only | Window ON Open；OFF regression |
| DFlash2 | DFlash method family variant | eager only in current source | eager Conditional；Graph保持现有拒绝 |
| extract/token-only/other | Not applicable/current factory policy | none | 不扩展支持 |

### 12.2 Eagle3 / AR

1. full prefill preparation完成后，从未扣 rejection 的 device `L0` 形成一次 proposal plan。
2. Window ON first-pass必须重建 Draft-only metadata并写 `DraftMetadataStore`；不得复用 Target entry。
3. rejection correction 后每 step计算 `E_s`，验证 `S<=E_s<=H`，从 full source刷新 view。
4. `slot_mapping` 按 full table/absolute positions 计算。
5. FULL merged graph必须为每 step提供不同 `DeviceWindowExact`：图内从 evolving full length和 frozen S派生，或每 step独立 capture-stable carrier。单份静态 device length 禁止。
6. 动态 K + Window 在 K 来源裁决前 fail closed。

### 12.3 DFlash

full rejection correction、query stretch、positions、context KV writes与slot mapping先完成；随后用 `E_prepared` 建plan并仅替换read inputs。Graph capture helper必须拿到相同persistent binding。DFlash2只继承该 read语义，不继承 Graph readiness。

### 12.4 DSpark

DSpark首先执行P01 policy。若显式model/training capability表明它是DeepSeek-V4 co-trained DSpark，则配置非None时warning once并forced OFF；直接回到baseline，不进行W校验、Window backend inventory、plan/workspace或Graph binding。该分支不是error，也不得因DSA/V4.1 Gate未来通过而自动打开。

其他eligible DSpark严格跟随窗口开关：OFF走baseline；ON才完成实际`num_query_per_req`、per-group tables/slots与backend inventory，再materialize。`sample_from_anchor=False`时query width为`K+1`，而当前DSA index buffer按`W+K`；修复并证明实际宽度前，eligible DSA/V4.1 non-causal组合为Open / Blocker。

DSA、SFA、V4.1、recycling不是“DSpark一个gate”；分别按§17关闭，但只对policy判定为eligible Window ON的route执行。若Required Delivery inventory命中其中之一且不是P01 forced-OFF route，该gate必须从Week4前移到验收前。

### 12.5 MTP

normalized method为MTP时，Window状态无条件为OFF；如果用户配置了非None window值，warning once并在`W`范围校验前返回baseline。不做Window inventory、不分配workspace、不改变metadata/graph key。普通MTP、Gemma4/Step3.5等特殊route都必须用normalized capability验证，而非concrete speculator class。“与主模型一起训练”是forced-OFF产品原因，不能被backend capability覆盖。

---

## 13. Runtime Data Flow

### 13.1 Window OFF

```text
resolve normalized method + explicit model/training capability
-> configured OFF: baseline
-> MTP with configured window: warning once + forced OFF
-> DeepSeek-V4 co-trained DSpark with configured window:
     warning once + forced OFF
-> current input preparation
-> current Ascend build_draft_attn_metadata_factory/wrapper
-> current Target/Draft metadata store behavior
-> current capture descriptors and graph updater
```

不得因Window代码存在而绕过S08 factory、创建额外tensor或改变capture数量。

### 13.2 Window ON

```text
1. policy.resolve(method, model/training capability, configured switch)
2. only an eligible Window ON result continues to inventory validation
3. prepare full query/positions/tables/valid counts
4. compute full slot mappings/writes
5. planner.begin_proposal -> frozen S and generation
6. acquire generation lease
7. for each step and global gid:
     derive E_s/V_s
     validate S<=E_s<=H
     validate source coverage/resident/native set
     deterministically rewrite active rows, tails, padding
     build backend-derived state in same lease
8. assemble typed DraftMetadataInputs
9. build into DraftMetadataStore
10. bind live/capture/replay actual consumer
11. draft forward
12. record last consumer completion; retire lease
```

每次materialize从full source开始；metadata rebuild只能重复消费同一plan，不能将window view再次作为full输入。

### 13.3 Reorder / finish / preempt / resume

generation fingerprint至少包含：proposal id、step、ordered request IDs、`idx_mapping` generation、actual/padded counts、per-gid valid-count hash、source/layout provider version、descriptor/phase/lane。finish后同一步加入的新request即使复用同row和相同block count也必须生成新identity并完全重写。

---

## 14. Buffer Lifetime

### 14.1 唯一生命周期 owner

使用speculator-owned `DraftWindowGenerationLeasePool` 作为唯一retirement owner。它可复用/扩展S17的UVA allocation/copy机制，但不能调用blind round-robin而不检查reader；必须提供显式 `acquire -> bind readers -> retire(event)`。不得再建立第二套独立event账本。

### 14.2 Lease 内容

一个generation lease覆盖：

- host exact/upper、request order、valid counts、plan staging；
- per-gid narrow device tables；
- device exact/upper与AR per-step carriers；
- backend-owned copied/derived tables、SAS/QLI/compressor/index buffers；
- graph resolved task引用与completion event。

`max_concurrent_batches`只作为host初始深度下界。实际深度由未退休generation trace决定；device lanes由实际并发stream/graph consumer决定，不能令 `device_slots=max_concurrent_batches`。

### 14.3 分配与耗尽

- Graph capture前为所有descriptor/phase/step/lane预分配固定shape。
- capture后不得通过替换storage来“扩容”已捕获operand。
- Eager可在无reader时安全扩容。
- 耗尽时等待最老completion、安全选择预分配lane，或fail closed；绝不覆盖in-flight。
- active tail与padded rows每代全量确定性写入backend声明的inert状态。

---

## 15. Graph Capture / Replay Strategy

### 15.1 三入口同一 binding

| Entry | Owner | Requirement |
|---|---|---|
| Live proposal | speculator builder | typed inputs覆盖table/length，不碰slots |
| Capture dummy | graph manager + provider | descriptor-specific persistent Window backing；Draft-only sink |
| Replay rebuild/update | graph manager | refresh generation/derived state，绑定actual consumer，completion后retire |

任一入口缺失，对应method/backend/mode报错。仅live正确不能开放PIECEWISE/FULL。

### 15.2 Consumer route taxonomy

| Route | Definition | Pass evidence |
|---|---|---|
| `DIRECT_CAPTURED` | operator捕获persistent operand地址 | capture/replay实际operand签名相同，内容随generation改变 |
| `TASK_REBOUND` | replay前task/provider重绑当前tensor | resolved/applied task kwargs与当前generation一致，event顺序正确 |
| `BACKEND_DERIVED` | builder/backend复制或派生到自有persistent sink | sink地址稳定、内容/代际更新且由同lease保护 |

GQA/MLA padding可能`cat`出新storage；FIAv2 provider可能只更新length；DSA/SFA updater为no-op。这些事实禁止把“narrow backing地址稳定”写成充分证明。

### 15.3 Operand fingerprint

对每个layer/gid/phase/step记录：storage base ptr、tensor `data_ptr`、storage offset、shape、stride、dtype、device、physical owner/resource key、route、descriptor、lane、generation、task handle/provider index，以及边界值/checksum。Python object identity不算actual operand证据。

### 15.4 `enable_enpu` 与 timeline

S16中generic wrapper：`enable_enpu=True` 是 update→replay；false是 replay→update并依赖captured event wait。DFlash/AR method manager当前固定先submit replay再update。Gate必须分别trace：

```text
materialize complete
update begin/end
ExternalEvent record/wait
replay submit
attention begin/end
last consumer completion
lease retire/reuse
```

未进入generic wrapper的组合标N/A，不能声称测试了另一顺序。

### 15.5 A/B/A replay Gate

同一captured descriptor下构造A、B、A′：shape/query width/padding相同；A/B使用互不相交的合法block-id集合、不同origin/length；A′语义等于A但generation不同。以eager A/B为oracle，在同一graph执行A→B→A′。每次先用generation-specific sentinel污染tail/padding/derived scratch。

通过条件：actual op只见当前代；B不读A；A′复现eager A且无one-step lag；Target metadata identity/content不变；lease仅在最后consumer结束后复用。必须覆盖batch shrink/grow、最大batch+dummy row、reorder、preempt/resume、same-step row reuse、人工延迟update/consumer、超过初始host深度、AR K≥3每step。

### 15.6 Mode 开放

| Mode | Window ON condition |
|---|---|
| Eager/NONE | live typed path、slot-set oracle、length/source/padding tests通过 |
| PIECEWISE | Eager gate + 实际piecewise consumer binding/descriptor trace通过 |
| FULL | 三入口 + route-specific A/B/A + timeline + per-step/device lane gate通过 |
| FULL_DECODE_ONLY | 分别验证prefill eager/piecewise与decode FULL；不能用名称推断两段均安全 |

---

## 16. Async Strategy

### 16.1 Generation 状态机

```text
FREE -> ACQUIRED -> MATERIALIZED -> BOUND -> SUBMITTED
     -> CONSUMER_COMPLETE -> RETIRED -> FREE
```

异常只能在未SUBMITTED时直接回收；已提交generation必须等待实际consumer event。epoch用于检测stale reference，不承担ownership。

### 16.2 必测竞争

- async scheduling与PP队列；
- graph update stream晚于下一host prepare；
- preemption/resume；
- request reorder；
- finish/add同step row reuse；
- 相同row和valid count但不同request；
- backend-derived buffer晚读；
- AR merged steps共用/分离device carrier；
- pool压力超过`max_concurrent_batches`。

在device lane数量被trace证明前，serialized eager可用一个lane并等待completion；这不阻塞基础实现。Async Window ON、Graph或多stream不得据此自动开放。

---

## 17. Native SWA / DSA / SFA / Recycling Interaction

### 17.1 集合语义

对query `q`：

```text
V_final(q) = V_draft(q) ∩ V_native(q) ∩ V_resident(q)
```

`effective_window=min(W,retention)`不是一般公式：native band可能只是计算mask而不回收；recycling可能保留extra/in-flight overhang；R-SWA可保留prefix+tail并形成gap。只有provider证明同一右端、连续suffix时才可化简为min。

### 17.2 DSA-v1

S20的generator在其输入坐标内计算 `query_lens -> prefix_lens -> start -> visible -> physical/logical indices`，这项局部代数Frozen。但完整NPU op还消费block table、seq length、SAS、native band、explicit indices、compressor/QLI状态；局部推导不能升级为operator正确性。

Gate：逐query physical-slot-set oracle；native左右边界；`start_pos_prefill`；C4/C128/compressor/QLI/SAS；padding；capture route；derived buffer lease；A/B/A NPU trace。

### 17.3 V4.1 DSA backend

V4.1使用logical indices、`ori_topk_length`和SMLA/QLI多种derived state（S21），是独立capability，不得沿用DSA-v1“已验证”。另需修复/证明`sample_from_anchor=False`的`K+1`宽度；修前eligible non-causal Window ON fail closed。当前DeepSeek-V4 co-trained DSpark由P01在该Gate之前forced OFF；本节只约束其他明确eligible的consumer，或未来经新产品决策重新开放的route。

### 17.4 SFA

SFA top-k count来自absolute positions，builder复制到自有persistent table/length buffer且graph updater no-op。Window适配不能只改scalar length：必须定义每token window-visible count，过滤/翻译logical indices，保持absolute positions，覆盖main+indexer groups，并把自有buffer纳入lease。没有该typed接口与operator oracle前为Open / Blocker。

### 17.5 Resident KV

direct-prefix `valid_num_blocks`只适用于prefix-resident layout。recycling/chunked layout必须由provider证明 `[S,E)` 的每个物理slot resident且未被重分配；不足时不得通过扩大可见历史、读取null block或静默缩短窗口修复。

---

## 18. Compatibility & Fail-closed Policy

### 18.1 初始化顺序

```text
normalize method + resolve explicit model/training capability
  -> None/OFF: baseline
  -> MTP + configured window: warning once + forced-OFF baseline
  -> DeepSeek-V4 co-trained DSpark + configured window:
       warning once + forced-OFF baseline
  -> Eagle3 or another eligible parallel route: validate W/policy
  -> inventory all groups/backends/modes
  -> require every consumer capability
  -> allocate plan/workspace
```

policy resolver的返回值必须区分`CONFIG_OFF`、`FORCED_OFF_CO_TRAINED`与`WINDOW_ON_ELIGIBLE`。两个OFF状态都走同一baseline数据路径，但只有forced-OFF且用户配置非None时发出去重warning。forced-OFF不得创建Window planner、workspace、DraftMetadataInputs或新Graph descriptor。

规范性伪代码：

```python
def resolve_draft_window_policy(config, method, model_caps):
    if config.draft_window_size is None:
        return CONFIG_OFF
    if method == MTP:
        warn_once("MTP is co-trained; draft window is forced off")
        return FORCED_OFF_CO_TRAINED
    if method == DSPARK and model_caps.is_deepseek_v4_cotrained_dspark:
        warn_once("DeepSeek-V4 DSpark is co-trained; draft window is forced off")
        return FORCED_OFF_CO_TRAINED
    if method == EAGLE3 or method in ELIGIBLE_PARALLEL_METHODS:
        return WINDOW_ON_ELIGIBLE
    return UNSUPPORTED
```

`model_caps.is_deepseek_v4_cotrained_dspark`表示policy resolver集中导出的capability；它不是建议的最终字段名。当前可复用S24的target `model_type.startswith("deepseek_v4")`精确predicate，但不得退化为`"deepseek" in model_name.lower()`，也不得把该判断复制进planner/backend。

### 18.2 Fail closed

eligible Window ON遇到unsupported组合，MUST在capture/forward前抛出带`method, model, gid, backend, KV spec, graph mode, parallel mode, failed gate`的异常。不得自动回退full Draft attention，因为那会把“配置已生效”变成假象。P01的MTP与DeepSeek-V4 co-trained DSpark是显式warning+forced-OFF产品策略，不属于silent fallback，也不进入unsupported Gate。

### 18.3 Window OFF regression contract

OFF必须：不分配Window state；不进入planner/provider；保留现行Ascend factory/wrapper；AR保持现行Target metadata过滤/复用；graph descriptors/counts/keys不变；输出、acceptance与性能在受控输入下回归等价。P01 forced-OFF路径还必须验证warning按engine/speculator实例去重，并且除了该warning外与configured OFF走相同数据路径。

### 18.4 参数政策

| Input | Interim behavior | Status |
|---|---|---|
| `None` | OFF | Frozen |
| MTP + configured nonNone value | warning once + forced OFF；数值校验前短路 | Frozen |
| Eagle3 + configured nonNone value | Window ON；继续执行static/dynamic K及mode Gates | Frozen policy / gated implementation |
| DeepSeek-V4 co-trained DSpark + configured nonNone value | warning once + forced OFF；inventory/workspace前短路 | Frozen |
| 其他eligible并行route + configured nonNone value | Window ON；继续执行backend/graph/parallel Gates | Frozen policy / gated implementation |
| supported + `W<=0` | fail closed；不当作OFF | Conditional maintainer approval |
| static K + `0<W<K` | fail closed，以保证全L域；固定L数学可能安全不改变政策 | Conditional maintainer approval |
| dynamic K | Window ON fail closed | Open / Blocker |

---

## 19. Week4 Extension Points

Week3只建立policy/inventory/planner、typed transport、single-group dense eager provider、独立Draft store与OFF回归。Week4在同一边界扩展：

- Flashcomm：验证通信前后read set及lane/event；
- SP/PCP/DCP/DSA-CP：provider输出rank-local mapping，不能套通用span公式；DCP local length必须用prefix projection `local(E)-local(S)`；
- DSA-v1/V4.1/SFA/recycling：仅对P01判定为eligible的route分别关闭§17 gate；DeepSeek-V4 co-trained DSpark不在Week4 Window enablement范围；
- Async：依据runtime trace定device lanes并纳入backend-owned buffers；
- FULL/PIECEWISE：按§15逐consumer开放；
- heterogeneous multi-group：需maintainer批准修legacy defect后，以canonical S + per-group provider实现。

若Required Delivery inventory命中Week4项，它即刻变成pre-acceptance mandatory，不得以“Week4”标签推迟。

---

## 20. Test Matrix

下表是实现后必须执行的测试设计；本轮均**未执行**。

### 20.1 Math / planner / layout

| ID | Case | Expected oracle |
|---|---|---|
| T01 | `W mod B = 0,1,2,B-1`，short/active分支 | `S,V,V_capacity` 与整数reference逐元素相等 |
| T02 | pointwise safe `L=100,B=64,W=3,K=4` | 固定L允许 `V=36`；证明不误写必要条件 |
| T03 | uniform fail `L=63,B=64,W=1,K=2` | `V=-1` 被拒绝 |
| T04 | rejection crossing `B=64,W=K=4,L0=64,r=2,s=1` | runtime invariant fail closed |
| T05 | LCM expansion `L=300,W=128,B=64,span=48` | anchor仍128；不得改0 |
| T06 | LCM nonzero `L=1000,W=128,A=192` | 驳斥“LCM>W则S=0” |
| T07 | offset `span=64,o=63,V=64` | `needed=2`；无offset consumer则拒绝 |
| T08 | DS capacity `W=64/100,B=64` | 2/3列，不采用错误化简 |
| T09 | upper inversion `L=150,U=200,W=100,B=64` | canonical S；upper不得小于exact |
| T10 | source shortage `start=4,needed=2,valid=5` | fail，不用inert补语义 |
| T11 | multi-group `B=128,spans=128/64,L=1000,W=256` | shared absolute S=640，列5/10；policy未批则拒绝 |
| T12 | dynamic `Kcfg=8,Krun=2,B=64,W=128,L0=185` | policy未决时拒绝 |

### 20.2 State isolation / method timing

| ID | Case | Required assertion |
|---|---|---|
| T13 | Window ON Draft build | Target table/length/metadata identity与content不变 |
| T14 | full slot mapping | ON/OFF所有writes指向同一absolute slot |
| T15 | Eagle3静态K | L0取未扣rejection值；proposal内S不变 |
| T16 | AR future block `B=16,W=64,K=3,L0=64` | E=65时第五列来自full source，不是stale zero |
| T17 | DFlash/DSpark | prepared horizon不二次加K |
| T18A | MTP普通/特殊route + configured window | warning once、policy=`FORCED_OFF_CO_TRAINED`、无数值校验/inventory/workspace、输出等同OFF |
| T18B | DeepSeek-V4 co-trained DSpark + configured window | warning once、forced OFF、无Window plan/metadata/Graph descriptor、输出等同OFF |
| T18C | Eagle3与其他eligible并行route开关 | None走baseline；非None进入Window Gates，不得误走forced OFF |
| T19 | `_seq_lens_cpu` | None或Window exact；注入full mirror立即断言失败 |
| T20 | rebuild/replay | 同一plan多次build不产生repeated-window |

### 20.3 Per-group/backend

| ID | Case | Gate |
|---|---|---|
| T21 | GQA/FIA single-group eager | semantic token/physical-slot set与CPU oracle相等 |
| T22 | MLA eager | exact/upper/padding/actual operand oracle |
| T23 | DSA-v1 non-causal | table+length+indices+SAS/native/compressor最终slot set |
| T24 | DSA `sample_from_anchor=False` | `q_max=K+1`容量边界，不少一列 |
| T25 | eligible V4.1 backend route | logical indices、topk length、SMLA/QLI逐代一致；P01 forced-OFF route不得运行本测试 |
| T26 | SFA | per-token visible count、index filter/translate、absolute position不变 |
| T27 | recycling/R-SWA | `V_draft∩V_native∩V_resident`，gap不被min公式吞掉 |
| T28 | padding R+1/shrink/grow | active tail与padded row无stale read/write |

### 20.4 Graph / Async

| ID | Case | Gate |
|---|---|---|
| T29 | live/capture/replay source spy | 三入口每gid均看到同generation inputs |
| T30 | route-specific A/B/A | actual operand无stale/one-step lag，A′复现eager A |
| T31 | `enable_enpu=True/False/N/A` | timeline分别满足实际路径，不混写 |
| T32 | AR merged FULL K≥3 | 每step distinct DeviceWindowExact，S冻结 |
| T33 | mixed backend FULL | 未聚合时报错；聚合后每actual backend均更新 |
| T34 | async pressure | 延迟consumer并超过初始pool深度，无覆盖 |
| T35 | reorder/preempt/resume | generation/order/valid-count hash正确 |
| T36 | finish+add same row | 新request不能读旧tail/derived buffer |

### 20.5 E2E / Regression / Performance

| ID | Case | Acceptance |
|---|---|---|
| T37 | Window OFF完整MRV2矩阵 | 受控seed/tokenizer/config下输出、acceptance、graph数量、峰值memory/perf基线 |
| T38 | Window ON long prompt > W | 与CPU visibility oracle一致，Target logits在完全相同输入/seed下不变 |
| T39 | MRV1/MRV2 single-group golden | S、每step visible set、slots逐元素一致；不比较已知legacy defect bytes |
| T40 | boundary fuzz | batch/method/K/W/B/length/rejection组合，无silent fallback |
| T41 | performance拆账 | planner、copy、metadata、graph update、draft forward、acceptance、E2E分别报告 |

---

## 21. Delivery Acceptance Matrix

材料能恢复公共契约与现有测试，但不能唯一恢复owner指定的Required Delivery组合。`TBD — Owner Confirmation Required` 不是虚构组合；它是本次coverage无法宣布完成的直接原因。

| ID | Model | Spec Method | Attention Backend | KV Cache Groups | Graph Mode | Parallel Mode | Required / Optional | Implementation Status | Verification Gate |
|---|---|---|---|---|---|---|---|---|---|
| M-01 | **TBD — Owner Confirmation Required**；Qwen3-8B为现有MRV1 oracle候选；若实际模型为DeepSeek-V4 co-trained route则只能验forced OFF | DSpark | **TBD by inventory** | TBD | 精确mode TBD | TBD | Mandatory delivery scenario | Not implemented；exact deployment未建立 | owner manifest；eligible route才做W=512/semantic golden/Graph A/B/A；forced-OFF route做warning+baseline identity |
| M-02 | **TBD — Owner Confirmation Required** | Eagle3 | TBD by inventory | TBD | Mandatory modes TBD | TBD | Public-contract mandatory coverage | Not implemented | AR first-pass独立store、静态K、多step、每要求mode binding |
| M-03 | **TBD — Owner Confirmation Required** | DFlash | TBD by inventory | TBD | Mandatory modes TBD | TBD | Public-contract mandatory coverage | Not implemented | prepared full slots、K=0、每要求mode binding |
| R-01 | Qwen3-8B；Qwen3.5-9B | Eagle3 | GQA | single | NONE / FULL_DECODE_ONLY | TP1/TP2，async variants | Mandatory regression | Existing OFF tests；Window ON unimplemented | OFF调用链/输出/acceptance/perf；来源 `test_qwen3_8B.py:25-88`, `test_qwen3_5_eagle3.py:31-97` |
| R-02 | Llama3.1-8B | plain Eagle | GQA | single | NONE/FULL/PIECEWISE variants | TP1，async | Mandatory regression | OFF supported；ON Open | OFF unchanged；ON明确拒绝；`test_llama3_1_8b_eagle.py:28-87` |
| R-03 | Qwen3-8B；Qwen3.6-35B-A3B | DFlash | GQA | single | current default/FULL | TP1/TP2，async | Mandatory regression | Existing OFF tests | OFF unchanged；`test_qwen3_8b_dflash.py:28-88`, `test_qwen3_6_dflash.py:31-95` |
| R-04 | Qwen3-8B；Qwen3.6-27B | DSpark | GQA | single | current default/FULL | TP1/TP2，async/adaptive variants | Mandatory regression | Existing OFF tests | OFF unchanged；`test_qwen3_8b_dspark.py:28-173`, `test_qwen3_6_dspark.py:31-97` |
| R-05 | DeepSeek-V4 co-trained + DSpark | DSpark | DSA SWA + derived state | multi/derived | FULL/default | TP/DP/PP/PCP，async | Mandatory policy regression | P01 forced OFF；尚未执行本轮测试 | 配置非None时warning once；无Window state/Graph变化；结果等同OFF；`model_runner_v2/test_deepseek_v4.py:103-170`等 |
| R-06 | GLM-5.2 + separate DSpark checkpoint | DSpark | target SFA；**draft backend TBD by inventory** | multi TBD | target FULL/draft eager and eager | TP8/DP2，async/KVPP | Mandatory regression | OFF tests exist；ON inventory unknown | 不把target SFA推断成draft SFA；`weekly/.../test_kvpp_dspark.py:10-87` 与 nightly config |
| R-07 | Qwen3.8-27B | DFlash2 | GQA | single | NONE | TP2 | Mandatory regression | Eager-only baseline | OFF/eager unchanged；Graph保留NotImplemented；`two_card/spec_decode/test_spec_decode.py:645-699` |
| R-08 | DeepSeek MTP；Gemma4/Step3.5/multi-KV variants | MTP | various | various | existing modes | existing | Mandatory policy regression | P01 forced OFF；尚未执行本轮测试 | 配置非None时warning once、无Window state、等同OFF |
| W4-01 | inventory-confirmed eligible non-DeepSeek-V4-co-trained route | DSpark | DSA-v1/V4.1/recycling | multi | Eager then FULL | TP/DP/PP/PCP | Optional unless owner makes mandatory | Conditional | policy eligibility + physical slot set、K+1 width、resident、derived-state、binding |
| W4-02 | GLM-5.2 or an inventory-confirmed SFA draft | DSpark | SFA + indexer | multi | Eager then FULL | TP/DCP/DSA-CP | Optional unless owner makes mandatory | Open / Blocker | per-token count、index translation、buffer lease、operator oracle |
| W4-03 | contract methods | verified backend | verified | multi | verified | Flashcomm/SP/DCP/DSA-CP/async ON | Week4 extension | Conditional | rank projection、comm read set、lane/event stress |
| X-01 | all | MTP | any | any | any | any | Explicitly forced OFF | Frozen policy | configured value => warning once；baseline identity；zero Window allocation |
| X-02 | all | DFlash2 | any | any | PIECEWISE/FULL | any | Explicitly unsupported today | Baseline rejection | preserve current error until separate graph support |
| X-03 | all | plain Eagle | any | any | any | any | Owner decision required | Open / Blocker | maintainer contract decision + MRV1/MRV2 golden |
| X-04 | all | Eagle3 dynamic-K | any | any | any | any | Owner decision required | Open / Blocker | decide configured-K vs scheduled-K；boundary golden |
| X-05 | DeepSeek-V4 co-trained route | DSpark | any | any | any | any | Explicitly forced OFF | Frozen policy | configured value => warning once；不得进入DSA/V4.1/SFA/Graph Window Gate |

### 21.1 Week3 minimum deliverable

Week3可以进入实现的最小集：

1. normalized policy、inventory与fail-closed diagnostics；
2. pure planner/math、typed lengths、valid-count gather与single-group direct-prefix provider；
3. speculator-owned lease/read view、Draft metadata store；
4. Window OFF identity regression；
5. dense GQA serialized eager路径，只有在T01–T22相应gate通过后才打开；
6. graph hook spike，但不得因“能传tensor”直接开放FULL。

Week3不等于Required Delivery已经覆盖。M-01–M-03的owner manifest必须在对外验收前关闭；只有policy判定为eligible且backend是DSA/SFA/V4.1时，相关Window Gate才自动前移。若M-01是DeepSeek-V4 co-trained DSpark，验收目标是P01 forced-OFF regression，不得实现或测试Window ON作为交付要求。

---

## 22. Expected File Changes

这是预期实现面，不是本轮已修改文件。

### 22.1 vLLM-Ascend

| File/area | Expected change |
|---|---|
| `vllm_ascend/worker/v2/spec_decode/draft_window.py`（建议新增） | policy、plan、typed length、provider protocol、lease/workspace；可合并为少量dataclass/functions |
| `worker/v2/spec_decode/__init__.py` / speculator base integration | normalized method + explicit model/training policy；MTP与DeepSeek-V4 co-trained DSpark在数值校验/inventory前forced OFF |
| `worker/v2/attn_utils.py` | typed Draft inputs进入group funnel；OFF继续现有factory；CPU exact/upper不fallback |
| `worker/v2/spec_decode/autoregressive/speculator.py` | proposal plan、first-pass rebuild、independent store、per-step view/device carrier |
| `worker/v2/spec_decode/dflash/speculator.py` | prepared-state后的view/materialize与replay store |
| `worker/v2/spec_decode/dspark/speculator.py` | 先消费resolved policy；仅eligible route进入per-gid provider/inventory与DSA/SFA/V4.1 gates |
| `.../{autoregressive,dflash}/aclgraph.py` | capture binding provider、replay generation、completion retirement、trace hooks |
| relevant attention builders/providers | actual operand route declaration、padding/derived buffer lease、capability probe |
| `ascend_config.py` / docs | approved W policy、method/mode support；owner未批前不声称支持 |
| new UT/E2E files | §20与§21测试，不覆盖既有测试 |

### 22.2 vLLM upstream minimal hook

| File/area | Expected optional hook |
|---|---|
| `vllm/vllm/v1/worker/gpu/spec_decode/speculator.py` | live `_build*metadata` 可选 typed read inputs，default None |
| `.../dflash/cudagraph.py` | capture helper/provider可选参数 |
| `vllm/vllm/v1/worker/gpu/cudagraph_utils.py` | generic AR capture可选Draft-only build/sink，不写Target store |
| optional neutral types module | vendor-neutral protocol/dataclass，避免upstream依赖Ascend |

若upstream hook不可接受，必须重新评估显式instance-scoped替代；不得复制整段upstream builder或新增module-global Window transport。该情况只阻塞受影响Graph模式，不阻塞纯planner与可显式接入的serialized eager。

### 22.3 明确不修改

Target attention语义、scheduler canonical lengths、persistent full tables、KV physical slot算法、model weights、既有MRV1实现（除非另立bugfix任务）均不在本迁移PR范围。

---

## 23. Implementation Phases

| Phase | Deliverable                                                 | Exit criterion                                                                     |
| ----- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| P0    | owner acceptance manifest + drift check                     | M-01–M-03每列有明确值；source anchors仍有效                                                  |
| P1    | pure policy/math/types                                      | T01–T12与T18A–T18C；MTP/DeepSeek-V4 co-trained DSpark forced-OFF分支无Window allocation |
| P2    | inventory、FullSource、valid counts、single-group provider     | 每gid映射/coverage可诊断；unsupported早失败                                                  |
| P3    | lease/workspace、typed transport、Draft store                 | isolation/lifetime UT；无global state                                                |
| P4    | eligible dense GQA serialized eager DFlash/DSpark；Eagle3静态K | 开关策略、method timing与semantic slot oracle通过；forced-OFF route未进入planner               |
| P5    | optional upstream capture hook spike                        | live/capture/replay source spy通过；OFF无变化                                            |
| P6    | PIECEWISE/FULL per consumer                                 | route fingerprint、A/B/A、timeline、AR per-step通过                                     |
| P7    | Week4 backend/parallel/async                                | 仅eligible route的DSA/SFA/V4.1/recycling/CP/SP/Flashcomm逐gate开放                      |
| P8    | delivery acceptance                                         | owner mandatory矩阵全绿；OFF回归和性能报告完成                                                   |

P0的未知不阻止P1–P3和gated P4开发，但阻止“Required Delivery complete”和可能影响P4/P7优先级。

---

## 24. Risk Register

| Risk | Failure mode | Scope | Mitigation / Gate |
|---|---|---|---|
| RK-01 | narrow table + full/excess length读null/stale block | all | typed lengths、source coverage、actual op oracle |
| RK-02 | Target metadata被Draft窗口污染 | AR/FULL | independent store + identity/content assertion |
| RK-03 | capture绑定full/different storage | Graph | explicit hook、fingerprint、A/B/A |
| RK-04 | replay→update one-step lag | Graph | event timeline、A/B/A、enable_enpu分支测试 |
| RK-05 | second group二次窗口/clone alias | multi-group | canonical plan、per-gid independent backing；policy approval |
| RK-06 | LCM放大历史 | heterogeneous | legacy-first anchor；禁止自动LCM |
| RK-07 | nonzero offset未被operator消费 | layout | capability check + fail closed |
| RK-08 | valid row tail被当真实source | all | gathered valid counts + hard coverage inequality |
| RK-09 | CPU upper小于exact或被当exact | MLA/FIA | apply-time U、typed consumer contract |
| RK-10 | AR future block列仍为zero | Eagle3 | per-step refresh/horizon materialize + boundary test |
| RK-11 | dynamic K选择错误anchor | Eagle3 | combination blocked until owner/golden |
| RK-12 | DSA K+1 width少一列 | DSpark DSA | actual q_max capacity；修前blocked |
| RK-13 | native/recycling被错误化成min | DSA/SFA/recycling | set intersection + resident oracle |
| RK-14 | host ring或device lane过早复用 | async | unified lease/completion event；pressure test |
| RK-15 | backend自有buffer脱离lease | DSA/SFA/MLA | provider registration + derived-buffer trace |
| RK-16 | mixed backend只更新第一个 | FULL hybrid | updater aggregation；修前fail closed |
| RK-17 | Window OFF因新factory路径漂移 | regression | None fast-path/call snapshot/perf baseline |
| RK-18 | 实际Required eligible model是DSA/SFA但计划只做GQA | delivery | P0 owner manifest；eligible Gate前移；forced-OFF route只做policy regression |
| RK-19 | checkout无commit导致line drift | all | implementation前hash/anchor recheck |
| RK-20 | acceptance变化掩盖错读 | all | physical/token set oracle优先，acceptance只作E2E指标 |
| RK-21 | 用类名/字符串误判MTP或DeepSeek-V4 co-trained DSpark，导致forced-OFF route进入planner | policy/all | normalized method + explicit model/training capability；T18A–T18C；Window allocation spy |

---

## 25. Conflict Resolution Table

位置引用采用原文 section 与 Review finding；最终状态的 `Frozen` 表示该冲突已关闭，`Conditional/Open` 表示方向或范围仍受对应Gate约束。

| ID | Topic | Codex Position | DeepSeek Position | Review Finding | Source / Math Evidence | Final Resolution | Status |
|---|---|---|---|---|---|---|---|
| CR-01 | Graph默认binding | Codex §19.2把`DIRECT_CAPTURE_BOUND`作为默认推荐 | DS §19.3认为同backing/capture view即可 | REV-DC R-01；REV-CD C-04/C-05 | S12–S16；GQA/MLA可`cat`，DSA/SFA updater no-op | 接受显式typed hook，但按actual consumer分`DIRECT_CAPTURED/TASK_REBOUND/BACKEND_DERIVED`；未过A/B/A不得开Graph。拒绝“workspace地址即证明”。 | Conditional |
| CR-02 | AR Target metadata alias | Codex §12.1要求重建但未指定独立sink | DS §12.1也未完全闭合store | REV-DC R-02 | S10、S11、S14 | Window ON必须speculator-owned `DraftMetadataStore`；capture/live/replay不写Target store。OFF可沿用过滤/复用。 | Frozen |
| CR-03 | Eagle3 `L0` | Codex §5/§11.1称full context end，存在歧义 | DS §12.3明确未扣rejection | REV-DC R-03 | upstream AR kernel与MRV1 apply timing；§9.1 | 采纳DS：`L0`是proposal-entry未扣rejection device length；静态K下冻结。拒绝用`L0-r`重算。 | Frozen |
| CR-04 | `_seq_lens_cpu` | Codex §17类型表遗漏 | DS §17同样遗漏 | REV-DC R-04 | MRV1 S01会裁该字段；backend selector可能优先它 | 增`LegacyCpuMirror`类型：None或与CpuWindowExact同源。 | Frozen |
| CR-05 | CPU upper来源 | Codex §17从U派生但apply-time定义偏软 | DS §17强调禁止fallback但未闭合shared cap | REV-DC R-05；REV-CD M-04 | S09 upper会加step；§9.6反例 | U必须是apply-time；用canonical S；`upper=min(max(U-S,exact),min_g safe_extent)`；每backend证明consumer语义。 | Conditional |
| CR-06 | DSA/SFA gate粒度 | Codex §21分别提出gate但仍较粗 | DS §21称自然求交并给统一gate | REV-DC R-06；REV-CD M-06/M-07 | S20/S21；最终op消费多个derived state；P01 | 对eligible Window ON route拆成DSA-v1、V4.1、SFA、compressor/QLI/SAS、resident、graph、async独立gate。DeepSeek-V4 co-trained DSpark先forced OFF，不进入这些gate。 | Conditional |
| CR-07 | Required Delivery | Codex §9/§25给设计范围，未绑定真实模型 | DS E1/测试矩阵亦未绑定owner验收 | REV-DC R-07；REV-CD M-13 | 当前测试矩阵比Reviews更新；任务资料未给唯一manifest | M-01–M-03标`TBD — Owner Confirmation Required`；不编造。阻塞coverage声明，不阻塞公共infra。 | Open / Blocker |
| CR-08 | Host ring vs UVA | Codex §15.3按未retire代际定容，未说明UVA关系 | DS §20.2曾直接用max concurrency | REV-DC R-08；REV-CD M-11 | S17/S18；same-step row reuse | 唯一GenerationLeasePool复用/扩展UVA分配并共享一个retirement source；max concurrency仅下界。 | Conditional |
| CR-09 | 异构multi-group MRV1 parity | Codex §11.2/§16坚持legacy anchor+provider/fail closed | DS §16.2声称可通过alignment分支兼容 | REV-CD C-01/M-03 | S01/S02/S04；128/64 UT；§4.4反例 | canonical S+per-group projection是修复方向；raw MRV1不是golden。maintainer批准“修defect”前异构ON拒绝。 | Open / Blocker |
| CR-10 | Window OFF factory | Codex §13.1/§27保留当前baseline | DS §27写“不套factory” | REV-CD C-02 | S08；AR/DSpark baseline需要factory注入 | 采纳Codex并修DS：OFF完整走现有factory/wrapper/store，None fast-path不加新行为。 | Frozen |
| CR-11 | native/resident公式 | Codex §21.1用集合交 | DS §21.4用`min(W,retention)` | REV-CD C-03；REV-DC M13自我纠正 | FullAttentionSpec计算window未必回收；R-SWA可有gap | 采纳Codex集合交；仅provider证明连续同端suffix时才允许min。 | Frozen |
| CR-12 | DS §16.3容量 | Codex §11.3给上界/不强调错误等式 | DS §16.3公式后作错误化简 | REV-CD M-01 | §9.5反例及整数枚举 | 保留有前提的`C>=ceil((W+B-1)/span)`；删除恒等式；offset用一般式。 | Frozen |
| CR-13 | `W>0`,`W>=K` | Codex §22.3区分数学/政策，保留owner decision | DS §16.4/§22.2一度写成硬合法域 | REV-CD M-02 | §9.3 fixed-L/forall-L证明；S23无validator | 两种量词分开；interim fail closed；配置兼容政策需maintainer批准；逐step invariant独立。 | Conditional |
| CR-14 | LCM / first-token-offset | Codex §11.2禁止LCM，offset不可表达则拒绝 | DS §16.2含LCM三支 | REV-CD M-03 | §9.4/§9.7反例 | 禁止LCM改anchor；offset-aware provider公式Frozen，具体operator消费能力需Gate。拒绝“折中对齐”。 | Conditional |
| CR-15 | valid block count | Codex §18.3要求source validity | DS §18.1以mask/inert为主 | REV-CD M-05 | S19；`start+needed<=valid` | valid count是语义coverage硬断言；缺源报错，inert只处理tail/padding。 | Frozen |
| CR-16 | DSA自然求交证明范围 | Codex §21.3保留operator gate | DS §21.2把generator rebase提升为默认 | REV-CD M-06 | S20只证明generator；op还消费SAS/native/compressor | generator algebra Frozen；完整DSA enablement Conditional。 | Conditional |
| CR-17 | SFA scalar contract | Codex §21.4要求visible-count/index协议 | DS以window-relative count概念表达但无接口 | REV-CD M-07 | absolute position top-k、builder-owned buffer、no-op updater | SFA必须有per-token count+index filter/translate+lease；缺失时ON fail closed。 | Open / Blocker |
| CR-18 | DeepSeek-V4.1/backend | Codex/DS原Final均未单列当前路径 | 同左 | REV-CD M-08 | S21与V4.1 model cache backend；P01 | V4.1 backend仍是eligible route的独立capability/Gate；当前DeepSeek-V4 co-trained DSpark在此前forced OFF，不能因Gate通过而开启。 | Conditional |
| CR-19 | Padding泛化 | Codex §17.4要求backend声明 | DS §18.3把FIA经验扩成一般inert规则 | REV-CD M-09 | backend可能复制/cat/自有buffer | 只冻结“确定性重写”；具体inert/read/write合同逐backend验证。 | Conditional |
| CR-20 | Graph padding/mixed updater | Codex §19提capacity/fingerprint，未完全解first-backend | DS §19同样以统一binding描述 | REV-CD M-10 | S15只取首个backend；R+1/padding实际operand可能不同 | mixed FULL在updater aggregation前拒绝；R+1 actual operand纳入A/B/A。 | Conditional |
| CR-21 | DSA query width | Codex/DS均按K近似 | 同左 | REV-CD M-12 | `sample_from_anchor=False`实际`q=K+1`，buffer按W+K | eligible Window ON route的capacity用actual q_max；修前fail closed。P01 forced-OFF route不触发该buffer。 | Open / Blocker |
| CR-22 | `span_g`推广 | Codex §16由provider定义 | DS若干处使用block×CP表达 | REV-CD M-14 | PCP/DCP/SP/DSA layout不同 | 采纳provider contract；禁止单公式跨backend推广。每parallel mode需rank-local oracle。 | Conditional |
| CR-23 | plain Eagle | Codex §9列Open，默认拒绝 | DS §12把Eagle/Eagle3并列 | REV-CD M-15；REV-DC兼容审计 | S22公共文档不含plain Eagle；MRV2 OFF测试存在 | OFF必回归；ON需maintainer明确产品契约与golden，之前拒绝。 | Open / Blocker |
| CR-24 | short-context branch | Codex §11数学包含clamp分支 | DS可见区间表述偏向active branch | REV-CD m-01 | §9.2直接推导 | 正文明确short/active两支，capacity统一覆盖。 | Frozen |
| CR-25 | compressor/QLI可达性 | Codex把DSA derived states列Gate | DS OQ混合当前可达/不可达路径 | REV-CD m-02 | inventory决定实际consumer；V4/V4.1差异 | 不删除Gate，但只对inventory实际可达consumer执行；报告N/A而不伪测。 | Conditional |
| CR-26 | Target logits oracle | Codex §13.3要求Target不变 | DS T31写与OFF一致但控制条件不足 | REV-CD m-03 | sampling/seed/batch不同会改变输出 | 只在完全相同input/seed/schedule/Target state下比较；核心oracle是Target metadata/slots/logits。 | Frozen |
| CR-27 | 状态标签 | Codex Frozen/Conditional/Open较严格 | DS把部分政策/runtime写Confirmed/Frozen | REV-CD m-04 | 无NPU实验；acceptance manifest缺失 | 全文只用三状态；runtime/owner未闭合项不得Frozen。 | Frozen |
| CR-28 | Expected File Changes | Codex §30含upstream hook open | DS §30低估capture/store接入 | REV-CD m-05 | S09–S14显示三入口及store | 明列Ascend模块、三speculator、两graph manager与upstream optional hooks；精确signature仍Gate。 | Conditional |
| CR-29 | Eagle3 dynamic K（独立发现） | 两Final未识别 | 两Final未识别 | Reviews未关闭 | S05：adapter捕获K后proposal改K | static K contract不变；dynamic K需owner选择configured/scheduled K与golden，前拒绝。 | Open / Blocker |
| CR-30 | AR未来跨block列（独立发现） | Codex要求per-step view但未指出MRV1 clone缺列 | DS强调per-step length但未指出source列缺失 | Reviews未关闭 | S01按initial V写needed；后续E增长 | MRV2从full source逐step刷新或预物化horizon；需semantic golden确认legacy defect repair。 | Conditional |
| CR-31 | public method/application policy | Codex §6.1/§9：Eagle3/DFlash/DSpark，MTP ignore | DS方法表包含更多code-reachable分支 | 双Review均要求区分contract/readiness | S22、S06、P01 | P01冻结最终应用策略：MTP和DeepSeek-V4 co-trained DSpark warning+forced OFF；Eagle3及其他eligible并行route跟随开关；DFlash2/plain Eagle仍分别治理。 | Frozen |
| CR-32 | 目标模型是否DSA/SFA | Codex gate但无delivery inventory | DS基于动机模型推测backend | REV-DC R-07；REV-CD M-08 | DeepSeek-V4确为DSA；GLM target SFA不证明draft SFA；P01 | DeepSeek-V4 co-trained DSpark无需Window backend Gate，只验forced OFF；其他mandatory route仍由runtime inventory决定，若eligible且命中DSA/SFA则Gate前移。 | Conditional |

Conflict统计：本表32项；**11 Frozen（已关闭）/ 15 Conditional / 6 Open / Blocker**。`Frozen`为已关闭，`Conditional`为已裁定方向但需Gate，`Open / Blocker`为仍需外部决定/新接口。

---

## 26. Final Decision Log

| ID | Decision | Rationale / Trace | Status |
|---|---|---|---|
| DL-01 | 采用speculator-owned Draft Window Read Plane作为唯一主架构。 | Codex §10；双方共享共识；Target/Draft边界清晰。 | Frozen |
| DL-02 | Target/full tables/positions/query/slot mapping永远不窗口化。 | S01/S03/S07；MRV1 contract。 | Frozen |
| DL-03 | `None`为OFF，完整保留现行factory/store/graph path。 | S08；CR-10。 | Frozen |
| DL-04 | P01应用策略：Eagle3和其他eligible并行route跟随开关；DeepSeek-V4 co-trained DSpark配置窗口时warning+forced OFF。 | P01；CR-31/CR-32。 | Frozen |
| DL-05 | normalized MTP配置窗口时在数值验证前warning+forced OFF，无Window state。 | S02/S06/S22/P01。 | Frozen |
| DL-06 | static-K AR使用`S=align_down(max(L0+K-W,0),B)`并proposal内冻结。 | S01、MRV1 timing、§9。 | Frozen |
| DL-07 | `L0`定义为未扣本轮rejection的proposal-entry device length。 | REV-DC R-03与kernel证据。 | Frozen |
| DL-08 | DFlash/DSpark `future_offset=0`。 | S01/S02与method prepare。 | Frozen |
| DL-09 | 禁止用LCM改写legacy anchor。 | §9.7反例。 | Frozen |
| DL-10 | 多group共享absolute S，layout由global-gid provider分别投影。 | CR-09/CR-14。 | Frozen |
| DL-11 | 异构multi-group修复legacy defect需maintainer批准；此前ON拒绝。 | S04与具体反例。 | Open / Blocker |
| DL-12 | `V_capacity=W+B-1`；capacity与exact分离。 | §9.2/§9.5。 | Frozen |
| DL-13 | 非零first-token offset只有actual operator消费后才可启用。 | §9.4。 | Conditional |
| DL-14 | `W<=0`、`W<K` interim fail closed；最终配置兼容政策待批。 | S23与量词证明。 | Conditional |
| DL-15 | 每active row/step硬检查`0<=S<=E_s<=H`。 | rejection反例。 | Frozen |
| DL-16 | Device exact、CPU exact、legacy mirror、CPU upper、capacity均类型化。 | CR-04/CR-05。 | Frozen |
| DL-17 | `valid_num_blocks`参与source coverage，不只是mask。 | S19与§9.5。 | Frozen |
| DL-18 | Window ON使用独立DraftMetadataStore；OFF可复用Target过滤结果。 | S11/S14；REV-DC R-02。 | Frozen |
| DL-19 | Window transport必须typed、instance-scoped；禁止新增global monkeypatch。 | Async/generation要求。 | Frozen |
| DL-20 | 采用default-None的最小upstream live/capture hook。 | 当前helper无参数通道。 | Conditional |
| DL-21 | Graph consumer逐项标记direct/task-rebound/backend-derived并fingerprint。 | S12–S16与backend源码。 | Frozen |
| DL-22 | PIECEWISE/FULL均需三入口与A/B/A；当前不默认开启。 | §15。 | Conditional |
| DL-23 | AR merged FULL必须有per-step DeviceWindowExact。 | S11与captured device increment。 | Conditional |
| DL-24 | host/device/backend buffer由同一generation lease在last consumer后退休。 | S17/S18；same-step reuse。 | Frozen |
| DL-25 | host depth/device lanes由trace确定；max concurrency仅下界。 | S17/S18。 | Conditional |
| DL-26 | native/recycling组合采用集合交，不用通用min。 | CR-11。 | Frozen |
| DL-27 | eligible dense GQA serialized eager是首个enablement候选，不是已验证支持；P01 forced-OFF route不参与。 | 最小consumer面与P01。 | Conditional |
| DL-28 | MLA需CPU exact/upper与actual operand gate。 | CR-05与builder差异。 | Conditional |
| DL-29 | eligible route中DSA-v1仅generator数学Frozen，完整ON仍需operator gate。 | S20与CR-16/P01。 | Conditional |
| DL-30 | V4.1 backend作为eligible route的独立capability；当前DeepSeek-V4 co-trained DSpark先forced OFF。 | S21/P01。 | Conditional |
| DL-31 | SFA缺typed index/count接口前ON拒绝。 | CR-17。 | Open / Blocker |
| DL-32 | plain Eagle OFF回归、ON待产品决定。 | S22与CR-23。 | Open / Blocker |
| DL-33 | Eagle3 dynamic-K + Window在K来源决策前拒绝。 | S05。 | Open / Blocker |
| DL-34 | DSA/V4.1 `K+1` width修复前对应non-causal组合拒绝。 | CR-21。 | Open / Blocker |
| DL-35 | Required Delivery exact manifest必须由owner确认。 | §21无唯一证据。 | Open / Blocker |
| DL-36 | Week3可开始policy、公共infra与eligible gated dense eager；不能宣称feature complete。 | P0未知不影响P1–P3；P01先行。 | Conditional |
| DL-37 | Week4扩展继续复用同一provider/lease/typed binding边界，并只接收policy判定为eligible的route。 | 避免第四套adapter；P01。 | Frozen |

Decision Log统计：**20 Frozen / 11 Conditional / 6 Open / Blocker**，共37项。

---

## 27. Conditional Gates & Open Blockers

### 27.1 Conditional Gates

| Gate | Missing evidence | Validation | Consumer | Failure behavior | State update rule |
|---|---|---|---|---|---|
| G-HOOK | optional typed hook的可合并signature/完整入口 | source spike + OFF call snapshot + live/capture/replay spy | upstream speculator/capture helpers | affected Graph fail closed；不得global workaround | hook合并且三入口UT通过后更新相关DL，不自动开放backend |
| G-GQA-EAGER | actual FIA read set与padding/upper语义 | CPU token/physical-slot oracle，boundary/reorder | dense GQA/FIA op | Window ON拒绝 | eager NPU矩阵通过后DL-27可Frozen |
| G-MLA | CPU exact producer、upper consumer、padding/derived operand | eager oracle + operand trace，无hot D2H | MLA op/builder | MLA ON拒绝 | 每具体backend/version记录证据 |
| G-OFFSET | nonzero `o_g` actual consumer | offset=1/span-1 slot-set tests与op trace | layout/backend | offending gid拒绝 | provider capability变为verified |
| G-UPPER | upper究竟planning还是read length | instrument final args/tiling/read set | each backend | exact缺失则拒绝 | consumer contract与tests入库 |
| G-AR-STEP | rejection与future-column refresh | T04/T16、多step semantic golden | Eagle3 | 边界proposal拒绝/组合关闭 | maintainer确认defect repair + tests |
| G-GRAPH | actual binding/timeline | §15 A/B/A，三入口，enable_enpu variants | each method/backend/mode | mode拒绝，eager不受影响 | 按route逐组合开放 |
| G-MIXED | updater aggregation覆盖所有executable backend | provider/task inventory + per-op fingerprint | hybrid FULL | FULL拒绝 | aggregation与A/B/A通过 |
| G-ASYNC | 未retire generation数、device lanes、derived buffer readers | delayed streams、pressure、preempt/reuse trace | async/PP/Graph | serialized/wait或拒绝 | trace确定容量并通过stress |
| G-DSA1 | eligible route的DSA完整可见集合 | physical slot oracle + SAS/QLI/compressor/native/graph | DSA-v1 | eligible DSA ON拒绝；P01 forced-OFF不进入 | 每实际derived state全通过 |
| G-V41 | eligible route的logical index/topk/SMLA/QLI与resident | 独立operator oracle+A/B/A | V4.1 DSA | eligible V4.1 ON拒绝；P01 forced-OFF不进入 | 不继承G-DSA1结果 |
| G-RECYCLING | `[S,E)` resident集合/slot稳定 | resident-set snapshot与reuse stress | recycling spec | gid拒绝 | provider证明集合包含关系 |
| G-PARALLEL | eligible route的rank-local span/projection/comm read set | TP/DP/PP/PCP/DCP/SP per-rank oracle | parallel paths | 对应mode拒绝；不得覆盖P01 forced-OFF | 每mode独立记录 |
| G-CONFIG | `W>0`,`W>=K`兼容政策 | maintainer decision + negative tests/docs | policy | interim fail closed | decision落配置/docs/tests |

### 27.2 Open / Blockers

| Blocker | Why not Frozen | Scope blocked | Closing evidence / owner | Until closed |
|---|---|---|---|---|
| O-01 Required Delivery manifest | 没有唯一model/backend/group/graph/parallel清单 | coverage/acceptance声明；可能改变backend优先级 | project owner填写M-01–M-03并提供启动/测试入口 | 只做公共infra；Required Delivery=`NOT YET ESTABLISHED` |
| O-02 heterogeneous multi-group policy | raw MRV1有重复window、错列、clone alias；修复不bit-parity | 异构multi-group Window ON | maintainer批准canonical-S defect repair + semantic golden | fail closed；single-group不受影响 |
| O-03 plain Eagle product contract | 仅代码可达，无公开Feature承诺 | plain Eagle Window ON | maintainer决定支持/拒绝 + MRV1/MRV2 golden/docs | ON拒绝；OFF回归 |
| O-04 Eagle3 dynamic K source | MRV1 adapter捕获configured K，proposal使用scheduled K | dynamic-K + Window | maintainer选择语义；跨proposal K变化/边界golden | ON拒绝；static K不受影响 |
| O-05 SFA Window interface | 缺per-token visible count与index translation typed contract | eligible SFA Window ON | backend owner设计接口、operator slot oracle、lease/graph tests | fail closed；P01 forced-OFF route不进入 |
| O-06 DSA/V4.1 K+1 width | current index width可能少一列 | eligible non-causal DSpark `sample_from_anchor=False` | backend owner按actual q_max修容量并跑边界oracle | fail closed；P01 forced-OFF route不进入 |
| O-07 upstream hook rejected | 无安全capture输入通道；替代global state不接受 | affected PIECEWISE/FULL | vLLM/Ascend maintainers接受hook或提出同等显式instance方案 | Graph fail closed；serialized eager可继续 |

Open项不是全部阻塞整个Feature：O-01阻塞delivery结论；O-02/O-03/O-04/O-05/O-06各自只阻塞对应组合；O-07只阻塞Graph transport。

---

## 28. Design Freeze Assessment

### 28.1 可冻结范围

以下架构已足够进入实现：P01三分支policy（configured OFF / forced OFF / eligible ON）；Draft-only read plane；Target/full/write隔离；static-K legacy anchor；eligible DFlash/DSpark K=0；canonical plan；typed length；per-gid provider；valid source coverage；independent Draft store；instance-scoped transport方向；actual-consumer Graph taxonomy；unified generation lease；set-intersection native语义。

### 28.2 不能宣称已冻结/已通过的范围

- 精确upstream hook signature与Graph接入尚未实现；
- 任何NPU Window ON backend尚未在本轮验证；
- PIECEWISE/FULL/Async/parallel尚未过trace；
- eligible Window ON route的MLA/DSA/V4.1/SFA/recycling尚未过各自Gate；DeepSeek-V4 co-trained DSpark按P01不进入这些Gate；
- 异构group、dynamic K、plain Eagle、DSA K+1 width仍有局部Blocker；
- Required Delivery manifest未给出。

### 28.3 最终裁决

**Architecture Freeze：CONDITIONAL**

理由：唯一架构、数学、不变量、ownership、fail-closed边界已确定，可进入Week3公共基础实现；但Graph explicit hook、backend actual binding以及若干局部产品/legacy-defect决策仍有明确Gate，不能写成无条件YES。

**Required Delivery Coverage：NOT YET ESTABLISHED**

理由：M-01–M-03的真实model/backend/groups/graph/parallel未由owner唯一确认。现有测试只能建立Regression surface，不能替代验收manifest。若目标是DeepSeek-V4 co-trained DSpark，Required行为已由P01定义为warning+forced OFF；若目标是其他eligible V4.1/SFA draft，对应复杂backend Gate必须前移。

**Can enter Week3 base implementation：YES，受Gate约束。** 可以先实现P01 policy与P1–P3，再做eligible single-group dense serialized eager候选；不得让MTP或DeepSeek-V4 co-trained DSpark进入Window planner，也不得默认开启Graph/Async/MLA/DSA/SFA/V4.1/recycling/heterogeneous/dynamic-K/plain-Eagle。

### 28.4 文档完整性审计要求

交付前对目标文件执行：

1. 28个核心章节均存在；
2. Conflict表每项含双方位置、Review、证据、裁决、状态；
3. Decision Log只使用三种状态并自动计数；
4. 每个Conditional/Open都有consumer、关闭证据与fail-closed行为；
5. Delivery Acceptance Matrix存在且Mandatory/Regression/Week4/Unsupported分明；
6. Frozen决策与正文无反向表述；
7. 搜索“已通过”等措辞，确保没有虚构NPU测试；
8. 路径存在性、原始材料hash与最终文件hash可复核；
9. production source/tests与四份原设计/Review未被覆盖。

---

## Appendix A. Implementation-time Assertions

```text
assert window_off or draft_store is not target_store
assert all(active: 0 <= S <= E_s <= H)
assert all(gid: needed <= capacity <= destination_width)
assert all(gid: start_col + needed <= min(source_width, valid_blocks))
assert legacy_cpu_mirror is None or same_origin_as_cpu_window_exact
assert planning_upper >= device_window_exact
assert every_graph_consumer_has_declared_route
assert every_bound_operand_generation == current_generation
assert lease.last_consumer_completed before lease.reuse
assert target_positions_slots_tables_unchanged
```

## Appendix B. Final Handoff Summary

- 主干：Codex Final Design 的 Speculator-owned Draft Window Read Plane。
- 吸收：DeepSeek的`L0`定义、数学/容量审计、per-step Graph长度、DSA generator分析、A/B/A与分阶段Gate；并采纳DS对Codex的AR store、UVA关系、delivery gap等有效Review。
- 纠正：DeepSeek §16.3错误化简、`min(W,retention)`、OFF factory、heterogeneous MRV1 parity、Graph同backing充分性；同时纠正Codex的capture默认可行性、AR metadata alias、长度mirror/upper与delivery不闭合。
- 运行准则：任何未过Gate的组合都在capture/forward前fail closed；不以acceptance或Python metadata替代actual operator证据。
