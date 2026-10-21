# MRV2 Speculative Draft Sliding Window — DeepSeek Final Design 攻击式 Review

> Review 对象：[MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md)
>
> 交叉比较：[MRV2_Speculative_Draft_Sliding_Window_Final_Design_Codex.md](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_Codex.md)
>
> 源码基线：当前本地 checkout；Review 日期：2026-10-08。
>
> 本文只做设计与源码审查，不修改 Final Design 原文件，不修改生产代码。

## Review 口径

本文中的结论状态含义如下：

| 状态 | 含义 |
| --- | --- |
| **Accepted** | 攻击成立；DeepSeek 文档必须修改，或必须撤回对应 Frozen/Confirmed 表述。 |
| **Rejected** | 在明确前提和限定范围内，攻击不成立；保留 DeepSeek 结论。 |
| **Needs Verification** | 静态 Python 源码无法证明真实 NPU operator、ACL Graph 或并发时序；必须保持 capability gate，不能伪装成 Confirmed。 |

Severity 表示“如果照当前文字指导实现”的后果，不表示该路径今天已经启用。DeepSeek 已将部分高风险 backend 放在 E2，这能降低首期运行时风险，但不能把错误或未闭合的 Frozen Decision 变成可冻结事实。

# 1. Overall Verdict

## 1.1 总裁决

**DeepSeek Final Design 不能直接冻结。结论为 NO-GO，修订后重新 Review。**

它已经非常接近一个可执行的“第一阶段工程计划”，尤其是：

- 把 capture-time dummy metadata 提升为一级设计对象；
- 采用窄表、proposal epoch、lease、capability gate；
- 区分 E1/E2、eager/FULL；
- 把 AR anchor、rejection、per-step length 写得比多数方案更具体；
- 首期只开放 aligned、eager、GQA/MLA，未把 DSA/SFA 的未知行为静默当成支持。

但当前文档仍有五类冻结阻塞项：

1. **Feature Contract 未闭合**：文档声称异构多 group 与 MRV1 “逐位相同”，但当前 MRV1 实际存在重复 Window、统一 legacy block size 索引异构表、共享 clone 被后组覆盖等 code-reachable 行为。
2. **存在明确的 Window-OFF 回归指令**：§27 错误地要求“不套 build_draft_attn_metadata_factory”，而 AR 与 DSpark 当前 baseline 已经依赖该 factory。
3. **一个 Frozen 数学式的证明错误，若干量词和边界条件互相冲突**：容量公式本身可成立，但化简错误；W ≥ K 的 pointwise 与全域量词混在一起；W > 0 尚是 Open policy 却被写成 invariant。
4. **Backend 集合语义未闭合**：一般 resident KV 不能化简为 min(W, retention)；DSA 只证明了 generator-level 恒等式；SFA 的额外长度没有生产者/消费者契约；当前 checkout 的 DeepSeek-V4.1 DSA/DSpark 路径被两份 Final Design 都遗漏。
5. **Graph/Async 接口未闭合**：同一个 Python workspace backing 不是 graph 正确性的充分条件；显式 Draft view 没有现成的 source-level transport；capture helper 还拿不到 binding；mixed-backend updater、padding 扩容、backend-owned buffer lease 都没有闭环。

## 1.2 对四个核心问题的明确回答

### DeepSeek 的最终设计能否直接冻结？

**不能。** aligned eager GQA/MLA 的方向可以保留并继续细化，但整份文档不能作为 FULL Graph、async、DSA/SFA、recycling KV 或异构多 group 的冻结实现规范。

### 哪些数学推导错误，哪些只是表达不清？

- **公式可保留、证明错误**：C_g = ceil((W + A - 1) / span_g) 在 zero-offset、span_g 整除 A、K ≥ 0、S ≤ L 的前提下是安全上界；但 §16.3 的 ceil((W+B-1)/B) = ceil(W/B) 是错误等式。
- **量词错误**：W ≥ K 对固定 L 只是充分非必要；对所有允许的 L/residue 保证非负长度时，是必要且充分。文档两处各说一半，形成内部矛盾。
- **缺少前提**：visible ∈ [W-K, W-K+A) 只在窗口已启动，即 L+K-W>0 时成立。
- **结构未闭合**：first-token-offset 非零、PCP/DCP/SFA replicated layout 不能继续使用 zero-offset 的 needed/C_g 通式。
- **Feature Contract 错误，不只是措辞**：异构多 group 的 MRV1 parity 声明与真实调用链不符。

### 它是否比 Codex 更接近可实施方案？

**局部更工程化，整体不更可冻结。**

- 对 eager GQA/MLA、AR 时序、实现顺序、证据等级和测试安排，DeepSeek 更具体。
- 对 actual graph operand、resident KV 集合、padding、host ring、first-token-offset、DSA/SFA fail-closed 边界和 Window-OFF baseline，Codex 更安全。
- 两份设计都缺少：DeepSeek-V4.1 backend inventory、异构 MRV1 legacy defect 决策、显式 Draft view 到当前 upstream builder 的具体桥、mixed-backend FULL gate。

### 是否需要改变 Codex 当前 Frozen Decisions？

**需要补强，但不需要推翻其主架构方向。** 至少应新增或修改：

1. 明确 MRV1 异构多 group 行为是要兼容还是作为 legacy defect 修复；MRV1 golden 只可无条件用于单 group/同 span。
2. 增加 DSA-v1 physical-index 与 DSA-v4.1 logical-index 两种独立 capability。
3. 将 shared CPU upper 定义为逐 row、跨 consumer/provider 的安全材料化范围；先审计它究竟是 planning bound 还是 read length。
4. direct-prefix provider 增加 required source coverage 断言，不能只把缺失列写 inert。
5. 冻结一个可调用的 DraftMetadataInputs/Draft-only builder bridge。
6. mixed-backend FULL 在 updater 聚合实现前 fail closed；capture builder 不得写共享 Target model_state.attn_metadata。
7. 吸收 DeepSeek 已证明的 DSA generator-level rebase 恒等式，但保持最终 NPU op gate。

# 2. Confirmed Agreements

下列攻击在“设计原则层面”被拒绝；DeepSeek 的方向是正确的。它们仍需实现测试，但不是当前设计错误。

| ID | 结论 | 状态 | 源码/数学依据 |
| --- | --- | --- | --- |
| A-01 | Window 只能建立 Draft read plane；Target、positions、slot mapping、authoritative block table 必须保持 full。 | **Rejected**：没有证据表明 DeepSeek 有意修改它们。 | slot mapping 从 authoritative block-table pointers 计算，而非 gathered/window table：[BlockTables.compute_slot_mappings()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:190)。DeepSeek I1–I4 也在类型边界上排除了 positions/slot_mapping。 |
| A-02 | zero-offset/aligned 域内，C_g = ceil((W+A-1)/span_g) 可以作为安全容量上界。 | **Rejected**：公式本身不是错；错的是 §16.3 的化简证明。 | 由整数 visible < W+A 得 visible ≤ W+A-1，再取列 ceiling。K=0 且最大 residue 可达时它可以取紧；K>0 时通常保守。MRV1 的 needed 也是 ceil(visible/B)：[SlidingWindowAdapter.compute_sliding_window_block_table()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/utils.py:120)。 |
| A-03 | DSA build_dspark_swa_indices 的 rebase 恒等式在其局部前提下成立。 | **Rejected**：generator-level 数学没有反例；端到端 backend 仍 Needs Verification。 | [build_dspark_swa_indices()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:420) 用 relative seq/table 计算 prefix、start、slot。 |
| A-04 | “每 proposal 一个 epoch 是否足够”的攻击不能忽略 DeepSeek 已写出的 lease。 | **Rejected**：文档并非只依赖 epoch。 | DeepSeek I15/I16 与 §20.3 同时要求 identity、reader、graph update、consumer completion。真正缺口是 backend-owned buffer 尚未接入该 lease。 |
| A-05 | DeepSeek 没有把 device slot=1 写成无条件事实。 | **Rejected**：它明确列了 stream/event/retire 前提，并把多 lane 设为 OQ。 | 当前源码只证明 host 可重叠，不证明多个 Draft device lane：[VllmConfig.max_concurrent_batches](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/config/vllm.py:589)。 |
| A-06 | normalized method 优先、MTP warning-and-ignore、DFlash2 eager-only 的方向正确。 | **Rejected**：factory 事实支持。 | [init_speculator()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/__init__.py:23)、[SpeculativeConfig.use_eagle()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/config/speculative.py:1936)、[AscendDFlash2Speculator](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash2/speculator.py:121)。 |
| A-07 | 不新增 ContextVar/module-global/thread-local 运输 Window view 是正确约束。 | **Rejected**：DeepSeek 的禁令应保留。 | 当前 wrapper 本来就是模块符号临时替换：[attn_utils.py](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:1240)；新异步状态不应继续叠加隐式全局运输。 |
| A-08 | E1/E2 分级和未验证组合 fail closed 是合理交付模型。 | **Rejected**：不能因为 E2 尚未实现就判整个分级错误。 | 但 E1 必须与真实验收模型 backend manifest 对齐，见 M-13。 |
| A-09 | apply timing 与 future_offset 必须由 method adapter 提供，而不是塞进公共 builder。 | **Rejected**：DeepSeek 对 AR 与 parallel drafting 的分叉方向正确。 | MRV1 已区分 Eagle 的 K 与 DFlash/DSpark 的 0，并把 DSpark 放到 per-group table 装入之后：[llm_base_proposer.py lines 437–452,2578–2605](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/llm_base_proposer.py:437)。MRV2 DFlash 也先逐 group执行 [prepare_dflash_inputs()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:375)。 |

# 3. Critical Findings

## C-01 — 异构多 group 的 “MRV1 逐位兼容”不是源码事实

- **Severity**：Critical
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：
  - [§16.2 lines 626–632](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:626)：“span_g | B_legacy ⇒ 与 MRV1 的 start 逐位相同 ⇒ 无任何语义变化。”
  - [T1/T2 lines 1030–1035](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1030) 要求多种 span 与 MRV1 逐位对拍。
- **当前源码证据**：
  - MRV1 全 proposer 只有一个 adapter 和一个 clone：[SlidingWindowAdapter.__init__()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/utils.py:101)，clone 在 lines 114–118。
  - legacy block size 取第一个 draft layer：[llm_base_proposer.py lines 403–452](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/llm_base_proposer.py:403)。
  - DSpark group loop 对同一个 adapter 逐组 apply：[llm_base_proposer.py lines 2578–2609](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/llm_base_proposer.py:2578)。
  - builder 可保留 block-table tensor 别名，而不是复制：[AscendDSAMetadataBuilder.build()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:821)，具体赋值在 lines 890–898。
  - 当前 UT 明确允许 group kernel sizes 为 128/64：[test_dspark_proposer.py lines 993–1034](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/tests/ut/spec_decode/test_dspark_proposer.py:993)。
- **事实**：
  1. 第一个 group apply 后，局部 common metadata 的 seq_lens 已经变成 relative/windowed。
  2. 下一轮 group 对这个已窗口化的 seq_lens 再 apply。
  3. 两个 group 共用同一 clone backing；后组 refresh 可覆盖前组 metadata 所引用的表。
  4. adapter 的 start block 单位固定为 B_legacy，不是每组真实 span。
- **推论与最小反例**：
  - B_legacy=128，spans=[128,64]，L=1000，W=256，K=0。
  - 正确 absolute plan：S=640；两组 start_col 分别 5 和 10。
  - 当前 MRV1 第 0 组得到 S=640、visible=360；第 1 组看到 L=360，再算得 S=0、start_col=0。
  - 即使假设每组都从原 L 独立算，MRV1 也用 S/B_legacy=5 索引 span=64 表，对应物理 origin=320，而不是 640。
  - 所以“一个 absolute S + per-group mapping”是更合理的修复方向，但它不是异构路径的 raw MRV1 bit parity。
- **是否同样影响 Codex Final**：**是。** Codex 的 provider/absolute interval 更正确，但也没有显式冻结“这是修复 MRV1 legacy defect”，且 MRV1 golden 的适用范围写得过宽。
- **最小设计修改**：
  1. Decision Log 新增明确决策：异构多 group 的 repeated-window、统一列单位、共享 clone 覆盖被视为 MRV1 legacy defect，不继承；或明确要求兼容。建议选择“修复”，但需 maintainer 批准。
  2. MRV1 golden oracle 只用于单 group 或所有 group 同 span、且不存在 clone alias 影响的路径。
  3. 异构组使用 absolute visible-slot-set oracle，不使用 raw MRV1 输出作为真值。
- **关闭条件**：
  - 128/64 双组 UT 同时记录真实 MRV1 输出、预期 absolute set 和 MRV2 输出；
  - 验证每 group backing 独立；
  - maintainer 对 legacy defect 兼容政策书面确认；
  - 目标模型 acceptance/E2E 无非预期变化。

## C-02 — Window OFF 规则会删除当前 baseline factory

- **Severity**：Critical
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[§27 lines 1127–1134](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1127) 条件 2 写“不套 build_draft_attn_metadata_factory”，条件 4 又写 DFlash/DSpark 保持现行 wrapper。
- **当前源码证据**：
  - AR baseline 的 uniform/non-uniform 路径已经使用 factory：[autoregressive/speculator.py lines 573–642](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:573)。
  - 注释明确说明不注入 positions 会把 position-0 RoPE 烘进图：[同文件 lines 583–592](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:583)。
  - DSpark baseline 同时套 wrapper 与 factory：[dspark/speculator.py lines 153–186](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py:153)。
  - factory 无条件注入 positions/is_prefilling/attn_state/parallel_config：[attn_utils.py lines 1254–1281](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:1254)。
- **事实**：factory 不是本 feature 新增的 Window wrapper；它是当前 AR/DSpark 正确路径的一部分。
- **具体失败路径**：按 DS §27 字面实现 OFF 短路并移除 factory，AR capture 得到 positions=None，Ascend funnel 创建全零 positions，RoPE 错误；DSpark 还会失去当前 attn_state/parallel context 注入。
- **是否同样影响 Codex Final**：**否。** Codex 明确把 OFF 定义为“不新增 Window 副作用，但保留现有 wrapper/factory”。
- **最小设计修改**：把条件 2 改为：“OFF 不进入新增 window-aware 入口；不得新增、删除、重排当前任何 wrapper/factory。AR/DSpark 保持 factory，DFlash 保持 wrapper。”
- **关闭条件**：
  - method-by-method 调用 spy 锁定 wrapper/factory 次数与参数；
  - OFF 前后 positions、metadata 类型/identity、graph descriptor/key 数量一致；
  - AR capture RoPE 回归；
  - Window OFF 性能与显存阈值测试。

## C-03 — effective_window = min(W, retention) 不是一般 resident KV 公式

- **Severity**：Critical
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：
  - [I21 line 249](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:249)；
  - [§21.4 lines 920–931](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:920)；
  - [D20 line 1264](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1264)。
- **当前源码证据**：
  - SlidingWindowSpec 还包含 extra_retained_tokens、in-flight tokens、block overhang：[kv_cache_interface.py lines 811–846](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/kv_cache_interface.py:811)。
  - 回收把区间块替换为 null block，并按 processed tokens 发生：[SingleTypeKVCacheManager._remove_blocks_in_range()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/core/single_type_kv_cache_manager.py:657)。
  - SWA skipped 公式包含 extra-retained：[lines 1169–1185](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/core/single_type_kv_cache_manager.py:1169)。
  - Chunked-local 的 origin 是 floor(computed/chunk)×chunk，而不是 trailing retention：[ChunkedLocalAttentionManager.get_num_skipped_tokens()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/core/single_type_kv_cache_manager.py:1394)。
- **事实**：resident KV 是 request/step/layout 相关的集合，可能含 block overhang、null block、extra retention、chunk origin，甚至不是简单连续 trailing suffix。
- **最小反例**：block_size=1、chunk=8、E=10、W=6。Draft tail=[4,10)，当前 chunk resident/native=[8,10)，真实交集=[8,10)。min(6,8)=6 若解释为 trailing window，仍得到 [4,10)，包含已释放的 4..7。
- **是否同样影响 Codex Final**：**否。** Codex 已冻结 V_final = DraftInterval ∩ NativeVisibility ∩ PhysicallyResident，并明确拒绝通用 min 化简。
- **最小设计修改**：
  - 撤回 I21/D20 的标量 Frozen 公式；
  - 改为 resident-set capability/provider；
  - 仅当 provider 证明 resident 永远是与 E 对齐的连续 suffix 时，min 才能作为局部优化化简；
  - warning 依据集合包含关系，不依据 W > 一个配置标量。
- **关闭条件**：从真实 manager block/null layout 生成 resident oracle，覆盖 SlidingWindowSpec 的 extra retention/in-flight/first-page offset、ChunkedLocal、AscendSlidingWindowMLASpec 和 V4.1。

## C-04 — “workspace 同一 backing”不是 Graph 正确性的充分条件

- **Severity**：Critical
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[架构图 lines 349–355](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:349) 称同一 backing 是“graph 正确性的全部内容”；[I14 line 242](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:242) 与 [§19.3 lines 797–814](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:797) 只 fingerprint Python view。
- **当前源码证据**：
  - GQA builder 在 padding 时可能 torch.cat 出新 block table：[attention_v1.py lines 341–373](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/attention_v1.py:341)。
  - SFA 将 common table copy 到 builder-owned persistent buffer：[SparseMLAMetadataState.prepare()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:297)。
  - DSA 最终可消费 builder-owned dspark_swa_indices：[dsa_v1.py lines 2262–2280](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:2262)。
  - MLA graph padding也可能 torch.cat：[mla_v1.py lines 695–739](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/mla_v1.py:695)。
  - UpdatableGraph 注册和替换的是 task kwargs，不是任意 Python metadata identity：[updatable_graph.py lines 120–174](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/compilation/updatable_graph.py:120)。
- **事实**：实际 operator operand 可能是 workspace、task-rebound tensor、builder-owned derived buffer 或 padding 后新 tensor。
- **最小失败路径**：SFA 的 workspace B 在 live/replay/capture 三入口指针都一致，检查全部通过；但 captured op 实际绑定 builder-owned C，而 runtime 没刷新 C 或 refresh/consumer 时序错，仍读旧 generation。
- **是否同样影响 Codex Final**：**否，主原则不影响。** Codex 已要求 DIRECT/TASK_REBIND/BACKEND_DERIVED route 与 actual operator/task operand；但具体 runtime trace 仍未完成。
- **最小设计修改**：
  - 将 I14 改为 route-specific graph binding；
  - DIRECT：真实 operator operand 同 backing；
  - TASK_REBIND：本 generation 的参数已安装且 replay 读本次值；
  - BACKEND_DERIVED：真实 sink buffer 地址稳定、内容属于同 epoch；
  - fingerprint 增加 device、physical owner、route、实际 task operand，而不是只检查 DraftAttentionView。
- **关闭条件**：抓取实际 operator kwargs/task handle；A/B/A origin replay；覆盖 enable_enpu true/false、GQA、MLA、DSA、SFA；证明无 one-step lag。

## C-05 — 显式 Draft view 的 live/capture 运输接口尚不存在

- **Severity**：Critical
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：
  - [§10 lines 338–345](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:338) 假定 build_draft_attn_metadata(view)；
  - [§19.3 lines 799–812](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:799) 假定 Ascend-local capture helper 能拿到 binding；
  - [Expected File Changes lines 1195–1216](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1195) 没有冻结 bridge 的实际签名。
- **当前源码证据**：
  - upstream Speculator 直接从 self.block_tables.input_block_tables 和 self.input_buffers.seq_lens 读取，函数签名没有 view：[Speculator._build_attn_metadata()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/speculator.py:295)。
  - Ascend 当前运输机制是 module-level wrapper/factory：[attn_utils.py lines 1240–1281](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:1240)。
  - DFlash capture helper在 builder 前已经固定调用 get_dummy_block_tables，且函数签名无 speculator/view：[dflash/cudagraph.py lines 24–70](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:24)。
  - Ascend patch 只替换 build_attn_metadata 符号，没有替换输入来源：[patch_dflash_speculator.py lines 18–29](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:18)。
  - AR capture 仍调用 upstream prepare_inputs_to_capture：[autoregressive/aclgraph.py lines 90–130](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:90)。
  - speculator 保存的 model_state 是 Target state：[Speculator.set_attn() lines 271–293](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/speculator.py:271)；若 window-aware capture 复用其 prepare_attn 写入口，可能污染 Target metadata。
- **事实**：当前没有一条显式、实例作用域、async-safe 的路径，把 view 同时送到 live、replay rebuild、capture dummy 三入口。
- **具体失败路径**：
  1. 保持 super()：builder 继续读取 full buffers，Window view 未被消费。
  2. 继续用 closure monkeypatch：跨实例/线程/async 泄漏，并违反 DeepSeek 自身 §20.4。
  3. capture helper只改 builder：输入仍是 full dummy。
  4. AR capture 用 window args 调共享 model_state.prepare_attn：Target metadata 被 Window dummy 覆盖。
- **是否同样影响 Codex Final**：**是。** Codex 提出了 Draft-only funnel，但没有冻结 upstream bridge 的具体调用边界，也没有明确写出 capture builder 禁止写 Target model_state。
- **最小设计修改**：
  - 冻结一个具体 DraftMetadataInputs 或等价 typed 参数对象；
  - 明确选择：小型 upstream signature hook，或 Ascend-local direct builder；若选择后者，列出复制的 upstream 逻辑和 parity drift test；
  - graph manager 持有显式 capture_binding_provider(desc, phase, step, lane)；
  - Window ON capture 使用独立 draft metadata holder，绝不写共享 Target model_state.attn_metadata；
  - Window OFF 完整保留现有 wrapper/factory。
- **关闭条件**：
  - source-level spy 证明每 gid binding 到达 Ascend builder；
  - 两个 speculator/线程交错无全局状态；
  - capture 前后 Target metadata identity/content 不变；
  - DFlash/AR 每 phase/descriptor 的 actual operand A/B/A NPU trace。

# 4. Major Findings

## M-01 — §16.3 容量公式可用，但化简证明错误

- **Severity**：Major
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[§16.3 lines 666–671](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:666) 声称 ceil((W+B-1)/B) = ceil(W/B)，再称与 MRV1 差一列。
- **源码证据**：MRV1 分配 ceil(W/B)+1：[SlidingWindowAdapter.__init__()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/utils.py:101)，lines 111–118；needed 为 ceil(visible/B)：[lines 145–146](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/utils.py:145)。
- **事实与数学**：
  - C=ceil((W+B-1)/B) 在限定域内安全；
  - 等式本身通常不成立。
- **最小反例**：
  - W=100、B=64：左式=3，ceil(W/B)=2，MRV1=3；不是“差一列”。
  - W=65、B=64：左式=2，ceil(W/B)=2，MRV1=3；此时才少一列。
  - 对 B>1，紧式只在 W mod B=1 时比 MRV1 少一列；其它余数与 MRV1 容量相同。退化的 B=1 情况也比 MRV1 少一列。
- **是否影响 Codex Final**：**否。** Codex 使用 V_capacity=W+B_legacy-1，并明确 MRV1 clone 可能保守多列。
- **最小修改**：保留 C_g 公式；删除错误等式；写出 zero-offset/alignment/S≤L/K≥0 前提和余数分段；不要称“退化为 MRV1 容量”。
- **关闭条件**：property test 覆盖 W mod B={0,1,2,B-1}、short context、K>0，验证 needed≤C。

## M-02 — W ≥ K、W > 0 的量词和政策状态互相冲突

- **Severity**：Major
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：
  - [F6 line 50](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:50) 称 W≥K 必要且充分；
  - [§16.4 lines 673–684](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:673) 又称“充分但不必要”；
  - [I19 line 247](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:247) 把 W>0/W≥K 写成强制 invariant；
  - [OQ-3 lines 1177](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1177) 又承认兼容政策未获批。
- **源码证据**：当前 AscendConfig 只定义 int|None，无正值 range check；MRV1 机械接受 0：[ascend_config.py line 497](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/ascend_config.py:497)、[SlidingWindowAdapter](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/utils.py:101)。
- **事实与数学**：
  - 对固定 L，W≥K 是充分但非必要；DS 的 L=100、B=64、W=3、K=4 例子成立。
  - 对“所有整数 L/所有 residue 均保证 visible≥0”，W≥K 是必要且充分。
  - 如果 L 被限制到有限 reachable domain，必要性取决于该域。
  - 对 parallel K=0，W=0 并不必然产生负长度；W>0 是产品政策，不是数学安全定理。
- **最小反例**：
  - pointwise 非必要：L=100、A=64、W=3、K=4，visible=36。
  - uniform 必要：若 δ=K-W>0，取足够大的 L≡A-1 mod A，则 S>L。
- **是否影响 Codex Final**：**部分。** Codex 对全域条件和 W>0 Conditional 的处理更正确，但也应明确 reachable L domain。
- **最小修改**：
  - 分开写 pointwise theorem、uniform configuration theorem、finite-domain policy；
  - Frozen runtime invariant 只保留 S≤E/visible≥0；
  - W>0 与 AR W≥K 标成 Conditional policy，等待 maintainer；
  - 明确 W=0 的 legacy 行为是否属于兼容合同。
- **关闭条件**：对全部 L mod A 做 property test；maintainer 决定 0/负 W 的兼容政策；测试锁定批准结果。

## M-03 — LCM 分支、first-token-offset 与一般映射没有闭合

- **Severity**：Major
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：
  - [§16.2 lines 624–664](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:624) 称 lcm 是非整除时“唯一候选”，同时写统一断言 A≤B_legacy；
  - [§11.2 lines 390–403](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:390) 把 start_col=S/span 与 needed=ceil(visible/span) 当公共式。
- **源码证据**：
  - 普通 BlockTables 会按 kernel block size 展开：[BlockTables.__init__()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:17)，lines 48–59。
  - DCP/SFA 有独立 local/replicated view，不能由一个整数 span 完整表示：[indexer.py lines 680–739](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/indexer.py:680)。
- **事实与反例**：
  1. rule 2 允许 A=lcm>B_legacy，随后统一断言 A≤B_legacy，状态机自相矛盾。
  2. “lcm>W ⇒ S=0”只在 D<A 时成立；A=192、W=128、L=1000、K=0 时 D=872、S=768。
  3. 若 provider 有 explicit first-token-offset carrier，lcm 不是唯一候选，可以保留 legacy S。
  4. span=64、offset=63、visible=64 时需要 2 列；ceil(visible/span)=1，少一列。
- **是否影响 Codex Final**：**否，主模型不影响。** Codex 已将 first-token-offset/provider 显式建模。
- **最小修改**：
  - 将 zero-offset 公式限定为 RELATIVE_PAGED_ZERO_OFFSET；
  - start_col=floor(S/span)，needed=ceil((offset+visible)/span) 作为一般式；
  - offset 必须由最终 operator 消费；
  - 当前 E1 无 carrier 时继续要求 S%span=0，其他 geometry fail closed；
  - 删除 rule2/统一断言冲突。
- **关闭条件**：non-zero offset reference test、operator absolute slot-set oracle、跨多个 LCM bucket 的测试。

## M-04 — shared CPU upper 与 per-group capacity 不一致

- **Severity**：Major；若某 backend 把 upper 当实际可读长度，可升级为 Critical
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：
  - [§11.2 line 399](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:399) 使用未定义清楚的 needed_g_max×span_g；
  - [§17.2 lines 706–719](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:706) 又按单个 capacity_g clamp，并称 exact 到 capacity 之间是“真实 KV”。
- **当前源码证据**：Ascend funnel 在 group loop 外生成一份 seq_lens_cpu/upper，再把同一 tensor 传给所有 group：[build_attn_metadata() lines 253–330](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:253)。
- **事实**：当前 upper 是 shared row-vector，不是 per-group field；不同 span 的 ceil-rounding capacity 可以不同。
- **最小反例**：同一 row exact=65，spans 64/32，则 copied extent 分别为 128/96；若 U-S=120，按 64 组 clamp 为 120 会超过 32 组的 96。对不同 row，使用 batch max needed 还会越过短 row 的已写 tail。
- **关键推论**：如果 upper 只控制 tiling/capacity，它可以大于 exact，但必须证明 exact mask 决定真实 read set；不能把 [exact,capacity) 笼统叫“真实历史 KV”。如果任何 consumer 把 upper 当实际 read length，则必须跨 group 取安全最小范围或增加 per-group field。
- **是否影响 Codex Final**：**是，部分影响。** Codex 有 provider capacity 兜底文字，但 Frozen D12 没明确逐 row、跨 group 的 domain safe extent。
- **最小修改**：
  - 定义 safe_cap[row]=min over all consumer/provider safe_materialized_extent(row)；
  - 先断言 safe_cap[row]≥exact，否则该 domain fail closed；再令 shared upper=min(max(U-S, exact), safe_cap[row])；
  - 若 backend 需要 per-group upper，增加强类型字段或 fail closed；
  - 区分 PlanningUpper 与 ReadLength。
- **关闭条件**：逐 backend 追到最终 consumer；证明 upper 不扩大 read set，或改为 per-group；覆盖多 group 不同 span、多 row 不同 needed。

## M-05 — valid_num_blocks mask 防越界，但不能代替 source coverage

- **Severity**：Major
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[I12 line 240](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:240)、[§18.1 lines 739–756](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:739) 在 src_col≥valid count 时写 INERT 并继续。
- **源码证据**：full gather 对 active row 只写 [0,num_blocks)，tail 不清；padding row 才整行清零：[gather kernel lines 235–272](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:235)。
- **事实**：mask 是 memory safety 必需条件；它阻止复制 stale/reallocated block。
- **最小失败路径**：direct-prefix full table 中 start_col=4、needed=2、valid_num_blocks=5。设计复制 1 列、第二列写 INERT，却仍把 exact length 宣称为 2 列覆盖，静默丢失必需历史。这通常意味着 generation、source 或 scheduler invariant 已坏，应 fail fast。
- **是否影响 Codex Final**：**是。** Codex 的 resident capability 可承载正确规则，但 direct-prefix coverage 断言不够显式。
- **最小修改**：
  - direct-prefix provider 对 active row 断言 start_col+needed≤min(row_width,valid_num_blocks)；
  - recycling/non-prefix provider 使用 resident-set inclusion，不能只用 prefix count；
  - mask 继续保留作 OOB/stale 防护，但不作为语义成功条件。
- **关闭条件**：故意缩短 valid count 时必须报错；preemption/row reuse generation test；recycling 路径使用集合 oracle。

## M-06 — DSA “自然求交”只在 generator 层被证明

- **Severity**：Major；若据此开放 DSA FULL，则是 Critical
- **结论状态**：**Needs Verification**
- **DeepSeek 位置与原文**：[F3 line 47](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:47)、[§21.2 lines 900–912](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:900)、[D12 line 1256](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1256) 将“自然求交”写成较确定结论。
- **当前源码证据**：
  - generator 的 relative 数学：[build_dspark_swa_indices()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:420)。
  - builder 同时构造 SAS metadata、seqused_kv、native band：[build_req_metadata_for_drafting() lines 1349–1495](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1349)。
  - 最终 op 同时收到 ori_block_table、seqused_kv、ori_win_left、SAS metadata 和可选 ori_sparse_indices：[dsa_v1.py lines 2237–2280](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:2237)。
- **事实**：恒等式 S+max((L-S-q)-N,0)=max(S,L-q-N) 成立；这是 generator-level Confirmed。
- **不能静态证明的推论**：vendor op 对 explicit indices、mask mode、native window 和 table 的优先级；是否再次解释 relative coordinate；graph 中 SAS/indices 是否属于本 generation。
- **最小失败路径**：S>0 时，op 在 physical indices 外再次按 ori_win_left 对 relative 序号裁剪，产生 double-origin 或多丢 token。
- **是否影响 Codex Final**：**否，当前安全边界不影响。** Codex 已 fail closed；但应吸收 generator-level 已证明部分，缩小 OQ。
- **最小修改**：D12 拆为“Confirmed: generator algebra”与“Conditional: end-to-end DSA provider”；集合级设备测试前 DSA 保持 UNSUPPORTED。
- **关闭条件**：实际 physical slot oracle，覆盖 S=0/S>0、W 与 native window 的小于/等于/大于、padding、eager/FULL、A/B origin。

## M-07 — SFA window_relative_visible_count 没有闭合的数据契约

- **Severity**：Major
- **结论状态**：**Needs Verification**
- **DeepSeek 位置与原文**：[backend matrix line 290](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:290)、[§21.2 line 914](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:914)、[OQ-6 line 1180](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1180)。
- **当前源码证据**：
  - indexer top-k length 来自 absolute positions：[Indexer.get_topk_lengths()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/indexer.py:130)。
  - SFA builder保留 absolute positions/table/seq：[AscendSFAMetadataBuilder._build()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:618)。
  - NoPE state据此构造 persistent plan：[SparseMLAMetadataState.prepare()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:297)。
  - 最终 op 同时消费 indices、table、seq length、top-k length：[sparse_mla()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:157)。
- **事实与推论**：源码确认 SFA 同时存在 absolute positions、top-k length、indices和 persistent plan；“增加一个 relative visible count就足够”只是未证明推论，因为这些字段是否要同步平移/过滤尚无契约。
- **最小反例**：E=4096、S=3968、window visible=128、topk=2048。absolute position 给 count=2048，但 shifted table/seq 最多只有 128 个合法 logical indices。普通 rows 数相等时，sparse_mla 不会进入“按 indices 重算长度”的 fallback，plan 仍可能被告知 2048。
- **未闭合字段**：per-token 还是 per-request；causal p-S+1 与 DSpark non-causal E-S；logical index 是否减 S；shared/skip-topk cache 的 generation；indexer group 与 main group 是否共享 S。
- **是否影响 Codex Final**：**否，当前 gate 不影响。** Codex 已将 SFA 标成 OQ/UNSUPPORTED；应吸收本反例。
- **最小修改**：定义 typed PerTokenVisibleCount、token→request mapping、index coordinate；indexer/main provider 同时接入；filter/subtract 后重算 valid count/plan。
- **关闭条件**：CPU logical-index oracle + NPU op；覆盖 causal/non-causal、prefill/decode、skip-topk、eager/FULL、padding；断言 topk_length=count(indices≥0)。

## M-08 — 当前 DeepSeek-V4.1 DSA/DSpark backend 被两份 Final Design 漏掉

- **Severity**：Major；若 V4.1 是验收模型则 Critical
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[§9.3 backend matrix lines 282–290](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:282) 只列 GQA/MLA/DSA-v1/SFA；全文无 dsa_v41。
- **当前源码证据**：
  - config normalization 将 V4.1 draft architecture 设为 DeepseekV41DSparkModel：[patch_speculative_config.py lines 110–150](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/patch/platform/patch_speculative_config.py:110)。
  - 模型注册：[models/__init__.py lines 55–57](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/models/__init__.py:55)。
  - Draft SWA cache 使用 AscendSlidingWindowMLASpec + DeepseekV41CacheBackend：[models/deepseek_v41/dspark.py lines 77–103](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/models/deepseek_v41/dspark.py:77)。
  - V4.1 builder 的 noncausal path 使用 use_logical_indices=True，并另建 ori_topk_length：[dsa_v41.py lines 824–890](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v41.py:824)。
  - AscendDSparkSpeculator 只把 AscendMLABackend/AscendAttentionBackend 归类为 MLA/GQA，其他为 None：[dspark/speculator.py lines 118–135](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py:118)。
- **事实**：V4.1 是当前 checkout 的真实 DSpark/backend 路径，且 index coordinate 与 dsa_v1 不同。
- **具体失败路径**：若按普通 MLA/DSA-v1 provider 开放，会把 logical index 当 physical；若只靠当前 attn_architecture=None 委托 upstream，则 Draft Window view 没有 provider，只能 fail closed。
- **是否影响 Codex Final**：**是。** Codex Final 同样无 V4.1。
- **最小修改**：
  - backend inventory 拆成 DSA_V1_PHYSICAL_INDEX 与 DSA_V41_LOGICAL_INDEX；
  - 首期可明确 fail closed V4.1，但 Contract、Expected Files、OQ、Test Matrix 必须出现；
  - capability 以真实 backend class/cache_kind 判，不以“DSA”大类猜。
- **关闭条件**：factory/model-load UT；V4.1 logical slot-set oracle；V4.1 native recycling + W ON/OFF E2E；若为验收模型则提升为 E1 blocker。

## M-09 — padding 契约从 FIA 特例泛化到了所有 backend

- **Severity**：Major；若“写必须为零”被实现成 slot id 0，则 Critical
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[F4 line 48](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:48)、[I13 line 241](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:241)、[§18.3 lines 764–777](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:764)。
- **当前源码证据**：
  - 被引用的注释只证明 GQA/FIA dummy row：[attention_v1.py lines 341–373](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/attention_v1.py:341)。
  - DFlash padding slot 使用 PAD_SLOT_ID=-1，不是 0：[dflash/speculator.py lines 655–688](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:655)。
  - SFA indexer scatter 对整份 slot mapping 调 NPU scatter，没有 num_actual_tokens slice：[indexer.py lines 249–285](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/indexer.py:249)。
  - 通用 device helper 明确说不能假设 fast op 自动过滤负 slot：[device_op.py lines 40–48](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/device/device_op.py:40)。
- **事实**：FIA 的“zero table + positive len + output trimmed + write prefix sliced”不能证明所有 backend 可任意读，也不能证明负 slot/slot 0 的写侧安全。
- **最小失败路径**：
  - 将“写为零”误解为 slot=0，会覆盖合法物理 block 0。
  - padding table 使用 stale/OOB id，即使输出最终丢弃，kernel 仍可能先非法读。
  - SFA indexer 的 -1 scatter 是否被 vendor op忽略，静态源码不能证明。
- **是否影响 Codex Final**：**部分。** Codex 已使用 backend-defined inert/no-observable-side-effect，但仍需补 SFA indexer/V4.1 的逐 consumer 写侧证据。
- **最小修改**：每 backend 分别定义 table/index/length/slot 的 inert；read 地址必须合法且 in-bounds；write 必须“无写副作用”，不是数值等于 0；无法证明则 fail closed。
- **关闭条件**：各 backend eager/FULL sentinel test；active block 0 放哨兵；padding 后所有 active KV 不变且无 OOB；覆盖 SFA 两种 scatter、DSA、MLA、GQA、V4.1。

## M-10 — Graph padding row capacity 与 mixed-backend updater 未闭合

- **Severity**：Major
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：
  - [§15.2 lines 558–576](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:558) 固定 window table 为 [R,C_g]；
  - [§19](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:781) 以单一 updater family 描述 FULL。
- **当前源码证据**：
  - GQA 满 batch 时 query-derived batch 可比 max_num_reqs 多一行，并通过 torch.cat 补 row：[attention_v1.py lines 341–373](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/attention_v1.py:341)。
  - graph update backend 只返回第一个 executable backend：[aclgraph_utils.py lines 122–135](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/aclgraph_utils.py:122)。
  - DFlash graph 更直接取 attn_backends.values() 的第一个：[dflash/aclgraph.py lines 86–98](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:86)。
- **事实与推论**：R+1 padding row 与“只选一个 updater”是源码事实；因此固定 [R,C_g] 一定覆盖 actual operand、一个 updater足够覆盖 mixed consumers，都是尚不成立的设计推论。
- **最小反例**：
  1. num_reqs=R=max_num_seqs，再加 TND dummy row，真实 operand 变成 R+1，并因 torch.cat 脱离 capture backing。
  2. visibility domain 同时含 GQA+MLA 或 GQA+DSA，首 backend 选择的 updater 不能证明其他 backend 的 graph params 被更新。
- **是否影响 Codex Final**：**是，mixed-backend gate 也遗漏；** row capacity 方面 Codex 的 R_capacity(binding) 更好。
- **最小修改**：
  - provider 声明 operator_row_capacity(desc)，内存公式用 R_capture；
  - inventory 聚合所有 executable consumer 的 updater route；
  - mixed-updater FULL 在逐 backend 更新实现前 fail closed。
- **关闭条件**：最大 batch+dummy row actual operand trace；构造/真实 hybrid group 逐层检查 task/legacy updater，不只测首层。

## M-11 — Async ring/lease 原则正确，但数量和 backend-owned 生命周期未闭合

- **Severity**：Major
- **结论状态**：**Needs Verification**
- **DeepSeek 位置与原文**：[§20.1–20.3 lines 854–882](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:854)、[D14 line 1258](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1258)。
- **当前源码证据**：
  - async MRV2 的 max_concurrent_batches=pp+1：[vllm.py lines 589–599](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/config/vllm.py:589)。
  - UVA pool 文档只给 concurrent in-flight 下界，并要求 reader retire：[buffer_utils.py lines 19–26,61–97](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/buffer_utils.py:19)。
  - DSA indices、SFA block/length 是 backend-owned 单例 persistent buffers：[dsa_v1.py lines 420–445](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:420)、[sfa_v1.py lines 255–295](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:255)。
- **事实**：max_concurrent_batches 是已知 host overlap 下界，不是所有 metadata reader/graph task 的最长生命周期证明；一个 epoch id 本身不能保护 backend-owned tensor。
- **最小失败路径**：proposal i replay 已提交但 update/consumer 未完成；host 已准备 i+1 并 refresh 单 device/backend slot；若 retire 只看 submitted 而不是 completion event，旧 graph 读到新内容。
- **是否影响 Codex Final**：**部分。** Codex 已改为最大未 retire generation，但具体 lane 数仍需 trace。
- **最小修改**：
  - host ring 按 maximum simultaneously unretired host generations 定容，max_concurrent_batches 只是初始下界；
  - 明确 pool exhaustion：等待 retire 或安全预分配，不得 overwrite；
  - provider 返回 BackendBorrowedBinding，包含 owner/lane/retire dependency；
  - backend 不 lane 化时强制 event 串行。
- **关闭条件**：NPU stream/event trace、人工延迟 consumer/update、超过 max_concurrent_batches 的读者压力、双 epoch 内容/指针检查。

## M-12 — DSA sparse-index width 在 sample_from_anchor=False 时可能少一列

- **Severity**：Major
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[§21.2 lines 900–914](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:900) 只审了 origin/rebase，没有审 index capacity 与真实 query width。
- **当前源码证据**：
  - DSpark 的 num_query_per_req 在 sample_from_anchor=False 时是 K+1：[DSparkSpeculator.__init__() lines 46–55](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dspark/speculator.py:46)。
  - DSA index_width 却按 native_window+K 分配/校验：[dsa_v1.py lines 415–450](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:415)。
  - 实际 visible_lens 使用 seq-query 推导，可达到 native_window+q：[lines 458–480](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:458)。
- **事实与推论**：K与真实 query count分离是源码事实；任何按 future_offset直接推断 index width的设计都是不安全推论。
- **最小反例**：native_N=4092、K=4、sample_from_anchor=False、q=5。align_128(N+K)=4096，但真实 visible 可为 4097，最后一个可见 token 没有 index column。
- **是否影响 Codex Final**：**是，未来 DSA provider 同样需要修；**目前 fail closed，未形成已承诺路径 bug。
- **最小修改**：layout 携带 max_query_tokens_per_req；capacity 用 native_window+q_max；runtime assert visible_lens.max≤index_width；不要把 future_offset K 当 query count。
- **关闭条件**：sample_from_anchor 两支、对齐边界、adaptive q、padding 的 UT；每 query visible set 完整。

## M-13 — E1 范围与真实验收目标没有绑定

- **Severity**：Major delivery risk
- **结论状态**：**Needs Verification**
- **DeepSeek 位置与原文**：[Executive line 39](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:39)、[§9.2–9.3 lines 265–290](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:265)、[P5 line 1229](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1229)。
- **当前源码证据与事实**：method 只先决定 concrete speculator：[init_speculator()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/__init__.py:23)；DSpark 随后才按真实 attention backend 区分 GQA/MLA/other：[AscendDSparkSpeculator.__init__()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py:118)；V4.1 还有独立 config/model/backend入口：[patch_speculative_config.py](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/patch/platform/patch_speculative_config.py:110)。静态源码无法得知项目验收 checkpoint 最终解析到哪个 backend/graph mode。
- **推论**：E1 作为基础设施里程碑是诚实的；如果真实验收模型是 DeepSeek-V4 DSA、V4.1 或要求 FULL，它不能被称为“feature 首期交付完成”。
- **具体失败路径**：测试只跑 DSpark+GQA eager 并标记 E1 完成；验收 checkpoint 加载后实际选择 V4.1 logical-index backend或 DSA FULL，capability gate拒绝运行，导致“基础设施 milestone通过”却“目标 feature不可用”。
- **是否影响 Codex Final**：**是。** Codex 同样需要真实 acceptance manifest。
- **最小修改**：冻结前增加“验收模型 → method → concrete backend → KV spec → graph mode → parallel mode”清单；将实际必验组合提升为 must-have gate。
- **关闭条件**：人工确认验收清单，并由 model-load capability dump 生成可审计记录。

## M-14 — PCP/DCP/SP 的 span_g 不能从一个 DFlash 公式泛化

- **Severity**：Major
- **结论状态**：**Needs Verification**
- **DeepSeek 位置与原文**：[Terminology line 111](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:111) 把 DCP span 定为 kernel_block_size×cp_size 并标 [V]；[§17.4 lines 721–733](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:721) 又把真实映射列为 gate。
- **当前源码证据**：
  - DFlash prepare 的确有 query_pos//(block_size×CP_SIZE)：[dflash/speculator.py lines 375–409](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:375)。
  - 公共 slot kernel还应用 cp rank/interleave：[BlockTables.compute_slot_mappings()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:190)。
  - SFA另建 DCP local/replicated view：[indexer.py lines 680–790](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/indexer.py:680)。
- **事实**：一个 DFlash slot 取列式不能证明所有 backend 的 table column semantics；PCP、DCP、SP 也不能混成同一 cp_size 概念。
- **具体失败路径**：把 DFlash 的 global `query_pos//(block_size×CP_SIZE)` 套到 SFA replicated/local table，得到的 source column属于 global compact layout；当前 rank 的 replicated view却可能使用另一列序/offset，结果复制错误块，随后 slot_mapping仍写入 full物理地址，形成“读错历史、写对位置”的隐蔽错误。
- **是否影响 Codex Final**：**否，主方向不影响。** Codex 已要求 provider-declared mapping，但仍需实际 projector。
- **最小修改**：span 改成 provider-declared mapping descriptor；首期分别 gate PCP/DCP/SP；不把乘积当公共事实。
- **关闭条件**：逐 rank absolute interval→source columns/offset/local lengths oracle，覆盖 interleave、PCP global/local、SFA replicated view。

## M-15 — plain Eagle 的“同 Eagle3 contract”只有路由证据，没有产品契约证据

- **Severity**：Major compatibility risk
- **结论状态**：**Needs Verification**
- **DeepSeek 位置与原文**：[§9.2 lines 272–278](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:272) 把 eagle 设为 E2 且“与 eagle3 同契约”。
- **当前源码证据**：
  - MRV1 adapter 条件是 method != mtp，plain eagle 机械进入：[llm_base_proposer.py lines 415–452](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/llm_base_proposer.py:415)。
  - MRV2 factory use_eagle 也含 eagle/eagle3：[SpeculativeConfig.use_eagle()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/config/speculative.py:1936)、[init_speculator()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/__init__.py:68)。
- **事实与推论**：路由/代码可达已确认；“公开支持合同完全相同”和验收承诺没有 dedicated docs/E2E 证据。将其放 E2 是合理的，将其写成已确认 contract 则过强。
- **具体失败路径**：只依据共同 factory route复用 Eagle3 的 future_offset/timing并开放 plain Eagle；若 plain Eagle输入准备或验收模型的 query horizon不同，Window会在错误时刻或以错误 K裁剪，而现有测试矩阵没有 plain Eagle用例发现它。
- **是否影响 Codex Final**：**否。** Codex 已把 plain Eagle 标为 Open/product decision。
- **最小修改**：区分 Code-reachable compatibility 与 Public supported contract；保留 E2，不自动升级。
- **关闭条件**：maintainer 确认 + plain Eagle Window E2E；MTP special variants 继续按 normalized method ignore；DFlash2 eager-only 保持。

# 5. Minor Findings

## m-01 — visible 区间遗漏 short-context 分支

- **Severity**：Minor
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[§11.2 lines 406–409](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:406) 无条件写 visible∈[W-K,W-K+A)。
- **事实/反例**：L=10、W=100、K=0、A=64 时 S=0、visible=10，不在 [100,164)。该区间只在 L+K-W>0 时成立；上界仍安全。
- **源码证据**：[MRV1 floor/clamp math](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/utils.py:131)。
- **Codex 影响**：Codex 应同样在 theorem 中显式分支 short context。
- **最小修改与关闭条件**：写成 inactive/active 两支；property test 覆盖 L+K≤W、等号和刚越界。

## m-02 — DSA OQ 把当前不可达的 compressor/QLI 与真实 draft 路径混在一起

- **Severity**：Minor
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[§21.2 line 912](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:912)、[OQ-4 line 1178](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1178) 将 compressor C4/C128、QLI、SAS 一起列为当前 DSA gate。
- **源码事实**：dsa_v1 build_for_drafting assert compressor_ratio≤1：[dsa_v1.py lines 1296–1304](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1296)，draft metadata 明确 qli_metadata=None：[lines 1474–1495](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1474)。
- **推论**：当前 dsa_v1 Draft 真正要审的是 generator、SAS、final op、absolute RoPE/full slot；compressor/QLI 属 target/未来 compressed draft。与此同时 V4.1 真实路径反而漏掉。
- **具体失败路径**：实现计划把 compressor/QLI审计列为当前 DSA的关闭条件并据此延期，但实际可达的 V4.1 logical-index path未登记；最终关闭了不可达分支，却对真实目标 backend无 capability结论。
- **Codex 影响**：Codex 也应拆分 OQ。
- **最小修改与关闭条件**：拆成 DSA-v1 SWA draft、DSA-v4.1 logical draft、future compressed draft 三条 call graph，各自关闭。

## m-03 — T31 的 “Target logits 与 OFF 一致”缺少受控输入前提

- **Severity**：Minor
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[T31 lines 1087–1091](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1087) 要求“Target logits 与不开窗口一致”。
- **当前源码证据与事实**：[ModelRunner.sample()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/model_runner.py:1536) 在有 draft tokens时把 Target logits送入 rejection sampler；随后新 Draft 又由 [speculator.propose()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/model_runner.py:2180) 生成。Window ON 可以改变 Draft candidates/acceptance，下一轮 Target验证的 token batch也会改变；自然运行的逐步 logits tensor没有直接逐位可比性。
- **最小失败路径**：ON 在 step t 提前拒绝一个 candidate，OFF 接受它；step t+1 两边 Target输入 token已不同。直接比较 logits逐位相等会错误地把合法的 Draft行为差异判为 Target污染。
- **Codex 影响**：**否。** Codex 已限定“固定相同 Target tokens/candidates 的受控输入”。
- **最小修改**：在相同 token/query/slot输入下比较 Target metadata/logits；自然 E2E只比较最终输出正确性/分布并单列 acceptance。
- **关闭条件**：受控 A/B证明 Target positions、slot、metadata与 logits一致；非受控 E2E不要求中间 logits逐位相等。

## m-04 — “Confirmed/Frozen”标签混入尚未关闭的政策与运行时假设

- **Severity**：Minor documentation / Major governance risk
- **结论状态**：**Accepted**
- **DeepSeek 位置与原文**：[Decision Log lines 1239–1269](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1239) 中 D11、D12、D14、D20、D22 使用 Confirmed/Revised/New，但其依据仍含 OQ 或错误通式。
- **当前源码证据与事实**：graph 的 update/replay顺序会受 enable_enpu影响：[AclGraphWrapper.forward()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/compilation/acl_graph.py:284)；DSA updater甚至是 no-op：[AscendDSAImpl.update_graph_params()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1621)。设计决策可以 Frozen，但不能因为三份 Agent材料一致就变成源码事实。D12 的 NPU端语义、D14 的 lane数、D20 的 resident formula、W>0 policy都未关闭。
- **最小失败路径**：把 D12 标 Confirmed后直接开放 DSA FULL；Python metadata更新正确，但 no-op updater下 captured op仍读旧 derived indices。状态标签本身使应有的 runtime gate被跳过。
- **Codex 影响**：Codex 的 Frozen/Conditional/Open 分类更清晰，但仍需加入本 Review 暴露的新 Open 项。
- **最小修改**：每个 decision 分成 Source Fact、Math Theorem、Policy Decision、Runtime Assumption四列；有 OQ的支持状态只能 Conditional。
- **关闭条件**：Decision Log每条都可追到源码/证明/批准者/运行时测试之一；缺任一所需证据不得升级。

## m-05 — Expected File Changes 低估了真实接入面

- **Severity**：Minor；若坚持“不改 upstream 也不复制 bridge”则 Major
- **结论状态**：**Needs Verification**
- **DeepSeek 位置与原文**：[§30 lines 1191–1220](/Users/wenqingzhang/Desktop/Note/MRV2/MRV2_Speculative_Draft_Sliding_Window_Final_Design_DS.md:1191) 只新增 `draft_window.py`、`draft_window_capture.py`，并把其余列为 Ascend-local“最小集”。
- **当前源码证据与事实**：上游 [Speculator._build_attn_metadata()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/speculator.py:295) 无 view参数；[DFlash prepare_inputs_to_capture()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:24) 无 binding参数；[get_graph_update_backend()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/aclgraph_utils.py:122) 只选一个 backend；V4.1 有独立 builder [DeepSeekV41DSparkAttentionMetadataBuilder](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v41.py:713)。当前文件表不足以解释这些接口由谁修改。
- **具体失败路径**：实现者严格只改 §30 列出的 Ascend-local文件，无法把 view送进 upstream live/capture入口，于是选择临时 module monkeypatch；功能在单线程 eager通过，却在两个 speculator或 async capture交错时泄漏。
- **是否影响 Codex Final**：**是。** Codex 的逻辑组件也尚未映射成具体 bridge 文件。
- **最小修改**：在不写代码的设计中先冻结接口与 owner，再重算文件清单；若需要 upstream hook，应坦诚列出，不能以“Ascend-local”代替调用边界。
- **关闭条件**：文件表中的每个 bridge都有 caller/callee/owner签名；live、capture、replay三入口均有 source-level调用图，且不依赖新增全局状态。

# 6. Mathematical Audit

## 6.1 可冻结的定理必须写全前提

令：

- L：apply 前、包含本次 draft query 语义的 exact KV length；
- W：draft_window_size；
- K：method-specific future_offset；
- A：选择 start 的 anchor quantum；
- span_g：第 g 个 KV cache group 的一个表列所覆盖的 token 数；
- S：canonical absolute start。

在 L、W、K、A 均为整数，L≥0、K≥0、A>0，并且采用

S = 0，当 L + K ≤ W；否则 S = floor((L + K - W) / A) × A

时，可证明：

1. short-context 分支：S=0，visible=L≤W-K；
2. active-window 分支：令 D=L+K-W>0，则 0≤D-S<A，因而
   visible=L-S=W-K+(D-S)，即 W-K≤visible<W-K+A；
3. 若要求对所有非负 L 和所有可达 residue 都满足 visible≥0，则 W≥K 是必要且充分条件；
4. 对某个固定 L，W≥K 只是充分条件，不是必要条件；
5. 若 start 对 group g 的列边界对齐，即 first-token-offset o_g=0，则
   needed_g=ceil(visible/span_g)；
6. 在 K≥0 前提下，active 分支的整数最大 visible 不超过 W+A-1，因此
   C_g=ceil((W+A-1)/span_g)
   是安全容量上界，但通常不是最紧上界。

这一定理不能直接用于非零 first-token-offset、非均匀/replicated table layout、resident-set 非连续、或 start 不是 group 列边界的 provider。那些场景必须由 provider 给出 projector 和容量函数。

## 6.2 §16.3：公式与证明必须分开裁决

DeepSeek 将 A=B、span=B 的式子写成：

C=ceil((W+B-1)/B)=ceil(W/B)。

右侧等式错误。对整数 W>0、B>0，恒等式应写成：

ceil((W+B-1)/B)=floor((W+B-2)/B)+1。

当 B>1 时，若 W mod B=1，它等于 ceil(W/B)；否则它等于 ceil(W/B)+1。B=1 时两边当然都等于 W。它不能无条件化简为 ceil(W/B)。

| W | B | ceil((W+B-1)/B) | ceil(W/B) | 结论 |
| ---: | ---: | ---: | ---: | --- |
| 100 | 64 | 3 | 2 | 直接反例 |
| 65 | 64 | 2 | 2 | 偶然相等，不能证明恒等 |
| 64 | 64 | 2 | 1 | 边界反例 |

因此：

- 对“C_g 是安全容量公式”的攻击：**Rejected，但附带前提**；
- 对“它可以化简成 ceil(W/B)”的攻击：**Accepted**；
- 对“这证明它逐位等于 MRV1 clone 宽度”的攻击：**Accepted**，因为 MRV1 初始化本身使用 ceil(W/B)+1；紧式仅在特定余数下少一列，且异构 group 另有 C-01。

源码锚点是 [SlidingWindowAdapter.__init__()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/utils.py:101)：`window_blocks=ceil(W/B)`，随后 `max_window_blocks=window_blocks+1`。这说明文档应分别描述 legacy allocation 与新架构的数学上界，不应靠错误恒等式把二者合并。

## 6.3 最小反例集

| ID | 被攻击的不变式 | 最小/具体取值 | 结果 |
| --- | --- | --- | --- |
| MX-01 | C 可化简为 ceil(W/B) | W=64，B=64 | 左式 2，右式 1 |
| MX-02 | visible 区间无条件成立 | L=10，W=100，K=0，A=64 | visible=10，不在 [100,164) |
| MX-03 | 固定 L 时 W≥K 必要 | L=1，W=1，K=2，A=64 | S=0、visible=1，仍非负 |
| MX-04 | 全域时 W≥K 可省略 | W=1，K=2，A=64，L=63 | D=64、S=64、visible=-1 |
| MX-05 | ceil(visible/span) 适用于任意 offset | visible=64，span=64，o=63 | 实际跨 2 列，不是 1 列 |
| MX-06 | 一份 upper 可同时表达所有 group | exact=65，S=0，capacity 分别 128/96 | 同一个 120 对后一 group 超容量 |
| MX-07 | valid_num mask 可补齐缺失源列 | source_start=4，needed=2，valid_num=5 | 只有 1 个有效源列；第二列没有语义来源 |
| MX-08 | MRV1 异构多 group 可直接作 golden | L=1000，W=256，legacy B=128，group span=128/64 | 后一次 apply 从已 window 的 seq_len 再算 start，且共享 clone 被覆盖 |
| MX-09 | DSA 宽度只需 native_window+K | native=4092，K=4，sample_from_anchor=False | q=5，最大相对宽度 4097；4096 少一列 |

MX-04 的目的不是建议允许 W<K，而是把“固定输入可运行”与“对所有输入安全的配置政策”区分开。最终产品完全可以规定 W≥K；但它应被标记为全域配置政策，并明确其量词。

## 6.4 C_g、needed_g、row_width_g、valid_num_blocks 的联合约束

容量安全不能只检查某一个数。对 direct-prefix provider，至少需要同时满足：

1. 0≤needed_g≤C_g；
2. C_g≤destination_row_width_g；
3. source_start_col_g≥0；
4. source_start_col_g+needed_g≤valid_num_blocks_g；
5. 对非零 first-token-offset，needed_g=ceil((o_g+visible)/span_g)；
6. destination 尾部 [needed_g,C_g) 被清零或由显式 valid count 使其不可读；
7. padding row 不得继承上一 proposal 的 source/destination row。

其中 4 是语义覆盖断言，不能用把缺失列写 0 来替代；0 只能表示“无效尾部”，不能凭空生成应该可见的历史 KV。

## 6.5 Legacy Anchor、LCM 与真实列语义

把 A 选为所有 span_g 的 LCM，仅在以下条件同时成立时足以令 o_g=0：每组是从 token 0 起始的均匀连续分块、列宽固定、无 replicated/interleaved layout、无 first-block partial offset、无 recycling hole。当前 checkout 的 DCP/SFA 路径已经出现 local/replicated view，因此 LCM 只能是 direct-prefix provider 的一个实现选项，不能成为公共 Frozen invariant。

MRV1 的真实事实是单个 adapter 接收一个 legacy block_size，并在多组循环中被重复 apply；见 [SlidingWindowAdapter.apply()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/utils.py:150) 和 [legacy group loop](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/spec_decode/llm_base_proposer.py:2089)。因此“Legacy Anchor”应被分成：

- 单 group/同 span 的已验证 Feature Contract；
- 异构 group 的 current legacy behavior，需要 maintainer 决定是严格复现还是显式修 defect；
- provider-declared mapping，不承诺由 LCM 自动解决。

## 6.6 数学审计结论

| 项目 | 裁决 | 冻结前动作 |
| --- | --- | --- |
| canonical S 公式 | Rejected attack / 可保留 | 写全 short/active 分支与量词 |
| C_g 上界公式 | Rejected attack / 条件成立 | 加 K≥0、zero-offset、uniform span 前提 |
| C 化简为 ceil(W/B) | Accepted | 删除错误等式与由此推出的 parity |
| W≥K | Accepted，需要重写 | 标记为全域配置政策；固定 L 不声称必要 |
| W>0 | Accepted policy gap | Frozen policy 或明确定义 0=OFF，二选一 |
| valid_num mask | Accepted 不充分 | 增加 source coverage 断言 |
| LCM 统一所有 group | Needs Verification | 限 direct-prefix；其他走 provider projector |
| first-token-offset=0 | Needs Verification | 首期 capability gate；非零时使用 offset-aware 容量 |
| shared CPU upper | Accepted | 按 row×consumer 定义安全范围，不从单一 group 推导 |

# 7. Backend / Source Integration Audit

## 7.1 Target、positions、slot_mapping 三条硬边界

当前源码支持继续冻结以下原则，但 DeepSeek 必须补上实际接口保证：

1. **Target metadata 永远 full**：Target 与 Draft 的 metadata 构建必须有不同 owner；不得通过共享 model_state.attn_metadata 暂存 Window view。
2. **positions 永远是原始 absolute positions**：Ascend draft wrapper把真实 positions 注入 builder，[build_draft_attn_metadata_factory()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:1253)；Window 只能改变 KV 可见性，不能 rebase RoPE position。
3. **slot_mapping 永远从 full table 计算**：上游 [BlockTables.compute_slot_mappings()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:190) 读取 positions 与 block table，生成真实 KV 写地址。Window table 只能在此之后进入 Draft metadata builder。

静态设计仍需冻结一个类型/调用签名，使 full_slot_mapping 不可能接收 DraftWindowView；仅靠文字约定无法阻止 C-05 的 accidental plumbing。

## 7.2 Backend 裁决矩阵

| Backend / layout | 当前真实 consumer | DeepSeek 主张 | 裁决 | Freeze gate |
| --- | --- | --- | --- | --- |
| GQA / paged attention | generic draft metadata → FIA/PA metadata | aligned direct-prefix 可 window | **条件 Accepted** | eager A/B；offset=0；source coverage；padding sentinel |
| MLA | generic/MLA builder，positions 用于 cos/sin | aligned direct-prefix 可 window | **条件 Accepted** | positions/slot full；eager A/B；MLA padding 契约 |
| DSA-v1 Draft | [build_for_drafting()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1296) → sparse indices → NPU op | table/length rebase 后自然求交 | **Needs Verification** | generator oracle + actual op A/B + sample_from_anchor 两支 |
| SFA / indexer | top-k indices、indexer KV scatter、DCP local/replicated state | window_relative_visible_count | **Needs Verification** | 冻结 producer/consumer/coordinate contract 后端到端验证 |
| DSA-v4.1 | [DeepSeekV41DSparkAttentionMetadataBuilder](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v41.py:713)，logical indices | 文档未覆盖 | **Accepted omission** | 独立 provider；logical/physical 不能复用 DSA-v1 结论 |
| Native SWA / recycling KV | scheduler manager 维护 resident allocation | effective_window=min(W,retention) | **Rejected** | resident-set intersection oracle；不支持则 fail closed |
| DCP/PCP/SP | rank-local/interleaved/replicated mapping | 公共 span 乘法 | **Needs Verification** | provider projector + per-rank oracle |

## 7.3 DSA：已经证明什么，尚未证明什么

DeepSeek 比 Codex 更强的一点，是识别并写出了 DSA sparse-index generator 在“统一平移”下的代数不变性。对所有由 seq_len、block table 和相对 index 一致 rebase 的纯生成逻辑，这个证明值得吸收。

但当前静态证据只到 generator：

- sparse indices 在 [AscendDSAMetadataBuilder.build_for_drafting()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1296) 构造；
- 最终把 block table、sparse indices、长度等送入 NPU op 的位置在 [dsa_v1.py lines 2237–2280](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:2237)；
- `sample_from_anchor=False` 时 DSpark query 长度是 K+1，不是 K，见 [DSpark Speculator initialization](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dspark/speculator.py:46) 和 [DSA index generation](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:420)。

尚不能由静态源码确认：operator 是否把 indices 当 logical token offset、physical slot、block-relative coordinate，native SWA/SAS 是否再次裁剪，以及 padding/inert index 是否绝不触碰非法地址。因此 M-06/M-12 维持 Needs Verification，而不是把 generator theorem 错判为无价值。

## 7.4 SFA：额外 scalar 还不是一个设计接口

SFA 中 top-k indices 与 KV scatter 保留绝对/物理含义：[indexer.py lines 249–285](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/indexer.py:249)。现有 SFA metadata 的建立和消费位于 [sfa_v1.py lines 100–219](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:100)、[618–707](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:618) 与 [885–895](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:885)。当前没有名为 window_relative_visible_count 的端到端字段契约。

冻结它之前必须回答：

- 谁用 absolute start 和 exact length 计算它；
- 单位是 global token、local token、rank-local visible count 还是 padded length；
- top-k indices 是重编号还是保留绝对坐标；
- DCP replicated index buffer 如何截断；
- 写路径仍使用 full slot_mapping 的类型边界；
- capture/replay 时它属于 direct tensor、task-rebound scalar 还是 backend-derived state。

在这些问题关闭前，正确状态是 fail-closed 的 E2 provider，而非 Frozen 字段。

## 7.5 Native SWA / recycling KV：必须使用集合交，不是长度取 min

`retention` 只能描述一个连续后缀时，min(W,retention) 才可能表达交集。当前 KV manager 支持 sliding-window/spec-aware block 回收；resident KV 可以包含 sink/prefix、循环块、非连续有效段，相关接口见 [kv_cache_interface.py lines 811–846](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/kv_cache_interface.py:811) 和 [single_type_kv_cache_manager.py lines 657–722](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/core/single_type_kv_cache_manager.py:657)。

最小失败路径：resident set={0…127}∪{896…1023}，Draft window=[768…1023]。二者交集只有 [896…1023]；取 min(256,256)=256 会错误地暗示连续 256 token 均 resident。正确抽象是：

DraftReadableKV_g = FullResidentKV_g ∩ DraftWindowInterval

若 provider 无法把这个集合投影成安全 table/view，则该 KV spec 必须在 Window ON 时 fail closed。

## 7.6 Padding：只能按 backend 契约逐一确认

当前 GQA 路径对 padding slot 有明确处理，[attention_v1.py lines 341–373](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/attention_v1.py:341) 和 [652–670](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/attention_v1.py:652)；MLA 也有自己的 padding metadata，[mla_v1.py lines 695–739](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/mla_v1.py:695)。这不能推出所有 DSA/SFA/未来 backend 都满足“读值任意，写地址必须 0”。

公共设计应冻结的是：每个 provider 必须声明 padding row 的 read/write contract；不声明就不支持 graph padding。对于 graph batch R 的额外 sentinel row，host snapshot、device workspace、valid count、CPU upper 都必须有 R+1 的已初始化容量，并在每 proposal 重置。

## 7.7 Source Integration 的未闭环点

现有 live funnel [build_attn_metadata()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:220) 与 [build_draft_attn_metadata_factory()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:1253) 没有接受 DraftWindowView 的正式参数；upstream draft builder也没有该类型。因而 Final Design 必须在冻结前选定一个真实桥：

- 增加显式 draft-only builder 参数；或
- 建立 task-local、词法作用域严格限定的 Draft metadata input context，并证明 capture/async 不泄漏；或
- 在 speculator 层构造完整 dedicated draft inputs，并让 wrapper 显式传递。

三者均可讨论，但“由 helper 自然看到 binding”不是当前源码事实。

# 8. Graph / Async Audit

## 8.1 三类 metadata 入口必须分别接通

最终实现不能只改 live eager builder。至少有三类入口：

1. **live/replay 前每 step metadata**：普通 speculator propose 调用 draft builder；
2. **capture-time dummy metadata**：DFlash、AR/DSpark manager 创建 dummy positions/length/table 并捕获 graph；
3. **backend-owned derived metadata/task parameters**：UpdatableGraph provider、legacy graph updater、no-op updater内部保存或更新的参数。

DeepSeek 提出 Narrow Capture Binding 是正确方向，但当前 capture helper 的参数表并没有 binding，且 factory 是动态 monkey-patch wrapper。因此它目前是架构意图，不是已验证接入点。

## 8.2 实际 graph operand，而非 Python 引用，决定地址稳定性

同一 backing workspace 只解决“地址可能稳定”，不证明 captured operator 读的是它。必须为每个 tensor/scalar 分类：

| 类别 | 例子 | 必须证明的行为 |
| --- | --- | --- |
| DIRECT_CAPTURED | block table / seq_lens tensor直接作为 captured op 输入 | replay 前原地址内容已更新；captured pointer 等于 workspace pointer |
| TASK_REBOUND | UpdatableGraph task 的 host-side kwargs/provider 参数 | provider 在 replay 时返回本 proposal 的参数；update/replay 顺序正确 |
| BACKEND_DERIVED | DSA/SFA indices、max_seq、workspace、handle | backend updater确实重算；no-op 时 captured state 本身必须可安全原地更新 |

[UpdatableGraph.register_task()/resolve_tasks()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/compilation/updatable_graph.py:120) 证明 task 参数可以重绑；[ACL graph replay path](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/compilation/acl_graph.py:284) 则显示 enable_enpu 会改变 update/replay 顺序。它们不能证明没有注册 task 的直接 captured tensor会自动切到新引用。

最小失败路径：proposal A 捕获 op(pointer=P0)；proposal B 的 Python metadata 指向 P1，即使 P1 属同一逻辑 workspace，op 仍读 P0。更隐蔽的版本是 P0 与 P1 都来自大 backing，但偏移不同；底层 captured pointer仍不会跟着 Python slice 改变。

## 8.3 Updater 选择与 mixed backend

当前 [get_graph_update_backend()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/aclgraph_utils.py:122) 返回遇到的第一个 executable backend。若一个 model/KV group 组合包含不同 updater 语义，单一 backend 不能证明所有 DraftWindow-derived 参数都被更新。DSA-v1 还提供 no-op [update_graph_params](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1621)，其含义不能从名字推断为“所有参数已安全 direct-captured”。

冻结政策应为：

- E1 eager 不依赖 updater；
- FULL 只允许 manifest 中已审计的单一 provider/backend 组合；
- mixed backend 在聚合 updater 或逐 backend 更新表实现前 fail closed；
- no-op updater必须通过 A/B/A replay 证明参数不会 stale。

## 8.4 Capture-time dummy 与 replay-time view 一致性

capture 与 replay 必须使用相同：

- Tensor shape、dtype、device、stride、storage offset；
- row capacity（含 padding sentinel）；
- per-group provider/layout descriptor；
- query width、future_offset、valid count dtype；
- updater route；
- backend capability decision。

仅在 replay 时构造 window view，而 capture 用 full dummy metadata，会让 captured descriptor、workspace、op参数形状与实际 replay 语义不一致。DFlash upstream graph入口在 [dflash/cudagraph.py lines 24–122](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:24)，Ascend patch与 manager分别在 [patch_dflash_speculator.py](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:18) 和 [dflash/aclgraph.py lines 62–138](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:62)。AR/DSpark 有独立 manager：[autoregressive/aclgraph.py lines 90–207](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py:90)。三者都需要逐入口闭合，不能只改公共 live wrapper。

## 8.5 Async ownership：epoch 是校验手段，不是内存所有权

每 proposal epoch 可以检测“这是不是本 proposal 的 view”，但不能阻止上一 proposal 的 NPU/graph仍在读取同一 lane。安全性至少需要：

- host snapshot lane：直到 H2D 或 device-side view build 完成前不可复用；
- device workspace lane：直到所有 draft kernels、graph replay和 derived-metadata consumer 完成前不可复用；
- backend-owned buffer：若 DSA/SFA/indexer 在 workspace 外持有 indices/handles/events，必须加入同一 lease；
- row generation：request removal/preemption/same-step row reuse 时清除旧 row；
- descriptor generation：graph rebuild/capture size改变时旧 binding 不可误配新 descriptor。

当前 async scheduling 可让多个 batch同时 in flight，[VllmConfig async validation](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/config/vllm.py:589)；上游已有 buffer ring 抽象，[buffer_utils.py lines 19–97](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/buffer_utils.py:19)。DeepSeek 的 ring/lease 思路应保留，但 lane 数不能静态写成固定双缓冲或“三份”；正确最小值是系统允许的最大未退休 proposal 数，并受所有 consumer completion event 约束。

### 8.5.1 eager / PIECEWISE / FULL 不是同一 transport 路径

| Mode | 当前路径事实 | 对 Window 的要求 |
| --- | --- | --- |
| eager / NONE | 每 proposal由 Python构造 live metadata，最适合先验证数学与 provider | view可为 per-step slice，但 backing/owner仍需防 async复用 |
| PIECEWISE | AR prefill可进入 PIECEWISE compiled region，但 draft decode不作为独立 PIECEWISE graph；上游注释见 [autoregressive/speculator.py lines 132–153](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:132)。DFlash也明确不支持 PIECEWISE draft，[dflash/speculator.py lines 123–137](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:123) | 不能把 Target/AR prefill的 PIECEWISE support外推成 Draft Window support；按实际 runtime descriptor走 baseline或fail closed |
| FULL / FULL_DECODE_ONLY | 独立 capture dummy、persistent operand、replay updater/event路径 | 必须关闭 C-04/C-05、padding R+1、actual operand和 A/B/A replay |

所以三种模式可以共享 Window math和 provider contract，不能共享未经区分的 metadata transport结论。

## 8.6 Window ON/OFF 与 graph descriptor

Window OFF 的最强回归要求不是“新对象值等于旧对象”，而是：

- 不构造 Window binding/workspace；
- 不改变当前 wrapper/factory 安装关系；
- 不改变 Target metadata owner；
- 不改变 graph capture descriptor、候选 shape、updater route；
- 不改变 block table/seq_lens/slot_mapping 地址或引用；
- 不增加每-step copy、同步或 Python context 操作。

因此 C-02 是冻结阻塞项。当前 baseline 的 DSpark 和 AR 都依赖 [build_draft_attn_metadata_factory()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:1253)；Window OFF 应完全走 baseline，而非“不套 factory”。

## 8.7 Graph / Async 裁决

| DeepSeek 决策 | 裁决 | 原因 |
| --- | --- | --- |
| Narrow Capture Binding | 方向 Accepted，接入 Needs Verification | dummy builder当前无 binding 参数 |
| 同一 backing 即地址安全 | Accepted attack | 必须验证 actual captured operand/offset |
| UpdatableGraph 可覆盖全部路径 | Needs Verification | legacy/no-op/mixed-backend不同 |
| proposal epoch 足够 | Accepted attack | 不能替代 completion-based lease |
| Host Ring + Device Workspace | 条件 Accepted | 数量由 max in-flight 与 backend-owned consumer决定 |
| ContextVar 不跨 async 泄漏 | Rejected as assumption | ContextVar会被异步上下文继承；即使 task-local也需严格 scope/reset，不宜作为隐式 payload |
| eager/PIECEWISE/FULL 同一逻辑即可 | Accepted attack | 数据数学可共用，transport/capture/update路径不同 |

# 9. Compatibility and Delivery Scope Audit

## 9.1 当前 method/backend 交付矩阵

| Method / variant | 当前 MRV2 路由事实 | MRV1 Window 行为 | DeepSeek 建议 | 本 Review 裁决 |
| --- | --- | --- | --- | --- |
| DFlash | concrete DFlash speculator；有独立 graph manager | 支持，timing/future_offset依 method | E1 eager GQA/MLA | **条件可行**，但需 acceptance model绑定 |
| DFlash2 | factory按 dflash 家族路由，当前能力以 eager为主 | 需按当前 config/测试限定 | eager only | **保留 Conditional**，不能由 DFlash 自动继承 FULL |
| DSpark | `init_speculator` 路由到 AscendDSparkSpeculator | 支持；MRV1 timing特殊 | E1 eager GQA/MLA | **条件可行**；若真实模型落 DSA/V4.1则不算 feature完成 |
| Eagle3 | use_eagle 路由 AR speculator | MRV1 adapter支持，future_offset非 0 | E2 | **合理**；需 AR horizon/rejection property tests |
| plain Eagle | 与 Eagle3共享 MRV2 route | code-reachable | 与 Eagle3同契约 | **产品支持 Needs Verification** |
| MTP | 单独路径/归一化 method | MRV1 warning/ignore | 保持 unsupported/ignore | **Accepted**，需精确复现 warning 与 no-op |
| DeepSeek-V4.1 DSpark/DSA | 当前 config patch、模型、metadata builder均存在 | Stage 1–7未完整覆盖 | 文档遗漏 | **冻结阻塞 inventory gap** |
| 其他 special variants | 取决于当前 normalized method/factory | 不可按 model name猜测 | capability gate | **Accepted 原则**；逐 factory 证据登记 |

当前 factory 证据是 [vllm_ascend.worker.v2.spec_decode.init_speculator()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/__init__.py:23)；Eagle family 判断来自 [SpeculativeConfig.use_eagle()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/config/speculative.py:1936)。DeepSeek-V4.1 的实际入口可见 [patch_speculative_config.py lines 110–150](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/patch/platform/patch_speculative_config.py:110)、[models/__init__.py lines 55–57](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/models/__init__.py:55) 与 [deepseek_v41/dspark.py lines 77–103](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/models/deepseek_v41/dspark.py:77)。

### 9.1.1 Method timing 审计

DeepSeek §12.1–§12.4 对 timing 的主方向优于把 Window 塞进 shared metadata漏斗，裁决为 **Confirmed Agreement A-09**：

| Method | 当前源码中的最后一个 full-state 准备点 | 可建立 Draft view 的语义时刻 | Review 结论 |
| --- | --- | --- | --- |
| Eagle / Eagle3 AR | Target query/full slot固定后；每 draft step会重建 metadata，[AscendARSpeculator._build_draft_attn_metadata()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:494) | proposal anchor冻结后、每 step metadata build前；K由 horizon与本 step L_s决定 | 方向正确；E2仍需 first-pass等价与 graph测试 |
| DFlash | 每个 draft group执行 `prepare_dflash_inputs`并生成 query/context slot；见 [DFlashSpeculator.propose()](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:330) | 所有 consumer group准备与 context KV预写完成后、draft metadata builder前 | 方向正确；不能提前到公共 slot mapping前 |
| DSpark | 复用 parallel input准备，但有自己的 metadata override与特殊 derived state：[AscendDSparkSpeculator._build_draft_attn_metadata()](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py:188) | per-group full table/length准备完后、DSA/SFA derived metadata生成前 | 方向正确；backend provider不能由 DFlash结论代替 |
| MTP | factory/policy独立，MRV1为 warning-and-ignore | 不建立 Window view | 保持现有 unsupported/ignore合同 |

因此，本 Review 不接受“DeepSeek忽略了三种 timing差异”这一攻击；真正问题是 capture入口、typed bridge与 backend derived state尚未接通，而不是其 method timing模型本身错误。

## 9.2 E1 是基础设施 milestone，不自动等于验收 scope

首期 `{DFlash, DSpark} × {GQA, MLA} × eager` 是合理的降风险切片，但必须在文档首页明确：

- 它是 E1 capability scope；
- 它是否是用户当前任务的正式 acceptance scope，要由目标模型/运行配置证明；
- 若验收模型实际选择 DSA-v1、DSA-v4.1、SFA、FULL/PIECEWISE、DCP/PCP/SP，则对应路径仍是 release blocker，不能用 E1 通过宣称 feature 完成。

冻结前必须输出运行时 capability manifest，至少包含 method、concrete speculator class、attention backend、KV cache spec、graph mode、async flag、parallel layout、sample_from_anchor、native SWA/recycling 标记。

## 9.3 Unsupported/compatibility 不能由公共 infra 自动启用

公共 Window math 的存在不等于所有 method 获得支持。config validation必须根据 method policy明确三态：

- supported：进入 provider/capability 检查；
- warning-and-ignore：严格复现 MRV1，例如当前 MTP policy；
- hard-incompatible：配置期失败，避免运行时静默 fallback。

不能使用 model-name hardcode；但也不能因为 speculator继承同一基类就默认支持。route fact、source capability与产品支持契约必须分栏。

## 9.4 是否重新引入旧错误

至少两处是旧问题回流：

1. Window OFF 删除 factory，重新引入了之前设计 Review 已纠正的 baseline wrapper误解；
2. “MRV1 parity” 未先隔离 legacy异构 multi-group defect，又把旧实现偶然行为提升成新架构 invariant。

另外，min(W,retention) 把 Stage 7 已强调的“物理 resident 世界与 Draft-visible 世界分离”重新压缩成单一长度，属于抽象倒退。

## 9.5 是否足以指导实现

**还不够。** 它能指导 common math、workspace原型、E1 property tests，但以下接口未闭合，开发者会被迫自行做架构决策：

- DraftWindowView 如何传入当前 live builder；
- capture-time helper 如何获得同一 binding；
- Target 与 Draft metadata owner如何类型隔离；
- shared CPU upper如何按多个 provider/consumer定义；
- mixed backend updater如何聚合；
- DSA-v4.1/SFA/recycling provider是否存在；
- first-token-offset/source coverage失败如何报错；
- async backend-owned buffers如何纳入 lease。

这些不是实现细节，而是决定正确性和所有权的 Architecture API，必须在 Final Freeze 前解决。

# 10. DeepSeek Advantages Worth Adopting

DeepSeek 的方案并非整体错误。以下内容比 Codex Final 更具体或更利于多人实现，建议实质吸收，而不是只在 Review 中致意。

## 10.1 证据等级与 fail-closed 门槛

把源码事实、数学推导、运行时假设和 Open Question显式分层，是很好的治理框架。Codex 应吸收其 evidence-level 表，但修正 m-04：任何依赖 runtime operator/graph行为的项，即使设计团队认同，也不能标 Confirmed source fact。

## 10.2 Narrow Capture Binding

“只把 Window 所需的窄输入绑定进 capture helper，而不让整个 request state 泄漏进去”是优于宽 ContextVar/全局状态的方向。应吸收为：显式、实例作用域、descriptor-scoped 的 capture_binding_provider。需要补的是 C-05 的真实签名和 Target metadata 隔离。

## 10.3 AR/Eagle 时序拆分

DeepSeek 对 L0、query horizon、rejection后长度、每 proposal epoch 的区分更细，能防止“future_offset是一个静态常数，所以所有 step都同一语义”的误解。Codex 应把这一时序写入 method adapter contract，并用 property tests 覆盖 draft accepted/rejected、sample_from_anchor 与变化 query width。

## 10.4 DSA generator-level 证明

DSA sparse-index generator 的统一 rebase 恒等式是有效进展。Codex 原设计过于保守，只说“DSA 需 backend hook”，没有保留已经可以静态证明的部分。应吸收成两层门槛：

- generator-level theorem：可 Confirmed；
- final NPU consumer/native SWA/SAS/coordinate interpretation：Needs Runtime Verification。

## 10.5 Staged E1/E2 与实现顺序

E1 先做 eager GQA/MLA、E2 再开 graph/DSA/SFA/复杂并行，是风险可控的工程顺序。应吸收，但不能让 milestone 名称替代真实 acceptance scope，见 M-13。

## 10.6 typed max-seq 概念

把 exact length、CPU mirror、planning upper、backend padded max、local length分成不同类型/字段，是必要的。Codex 已有语义分层，但 DeepSeek 的命名和检查更接近可实现接口。应吸收并补上 M-04：共享 upper 必须对每个 provider/consumer安全，不能由某一 group cap 推导。

## 10.7 valid_num 与 stale-tail 防护

每 proposal snapshot valid_num、清空未用尾部、防止 removed/preempted row读取上轮列，是正确的防 stale 机制。应吸收，同时增加 M-05 的 source coverage断言；mask只能屏蔽尾部，不能代替缺失源数据。

## 10.8 A/B/A Graph 测试与性能拆账

用 A/B/A origin replay 专门捕捉 one-step lag，比只比较一次 capture/replay更强；把 host planning、H2D、device copy、metadata build、graph update、kernel时间分别测量，也比笼统吞吐指标更有诊断性。这两项应完整进入 Codex Test Matrix。

## 10.9 不夸大 kernel 收益

DeepSeek 没有把“减少可见 KV”自动写成所有 backend/kernel都会线性加速，并单列 workspace内存与 copy成本。这种表述更适合正式设计文档，应保留。

# 11. Codex Design Weaknesses Revealed

本 Review 不能因为 Codex 是评审方就把它当成基准真理。DeepSeek 与源码交叉后，Codex Final 至少暴露出以下缺口：

1. **MRV1 异构多 group defect 未定性**：Codex 的 absolute interval/provider方向较安全，但仍把 MRV1 golden适用范围写得过宽，没有明确这是兼容还是修 defect。
2. **DeepSeek-V4.1 inventory 遗漏**：当前 checkout 有独立 config、model、metadata builder和 logical-index语义；Codex 也没有把它列成独立 capability。
3. **shared CPU upper 仍不够具体**：缺少 row×provider×consumer 的安全范围定义，以及“planning bound”与“kernel read length”的类型隔离。
4. **source coverage assertion 缺失**：Codex 强调 valid count，却没有冻结 source_start+needed≤valid_num 的直接断言。
5. **Draft-only builder bridge 未签名化**：提出了 funnel，却没有决定 current upstream `_build_attn_metadata` 如何接收 typed view，也没有列清复制/patch的 drift成本。
6. **mixed-backend updater gate 不够明确**：没有指出当前实现只选择第一个 executable backend；FULL 应先 fail closed。
7. **capture holder 与 Target state 隔离未写死**：独立 Draft metadata holder必须成为不变式，不能让 capture helper临时复用 Target model_state。
8. **DSA width边界不完整**：`sample_from_anchor=False` 的 K+1 query需要进入容量推导与测试。
9. **验收 manifest 缺失**：Codex 的 matrix覆盖面广，但未把用户真实目标模型会选到的 concrete backend/graph/parallel模式固定下来。
10. **对 DSA generator过度保守**：可以接受 DeepSeek 的局部代数证明，无需把所有 DSA 内容都留成完全未知。

因此，以 Codex 为主文档并不等于“保持不变”。上述 1–9 是合并冻结前的实质修订项。

# 12. Review Resolution Table

## 12.1 Finding 决议总表

| ID | Severity | 状态 | DeepSeek 决策如何处理 | 是否影响 Codex | Freeze 状态 |
| --- | --- | --- | --- | --- | --- |
| A-01 | Agreement | Rejected | 保留 full Target/positions/slot/full table不变式 | 补 typed boundary | 可保留 |
| A-02 | Agreement | Rejected with preconditions | 保留 C_g 上界，删错误化简 | 是，补定理前提 | 修文后可冻 |
| A-03 | Agreement | Rejected at generator level | 保留 DSA generator theorem，final op仍 gate | 是，吸收 | 部分可冻 |
| A-04 | Agreement | Rejected | 保留 epoch+lease，不把 epoch单独使用 | 否 | 原则可冻 |
| A-05 | Agreement | Rejected | 不把 device lane=1当无条件事实 | 否 | 保持 Open |
| A-06 | Agreement | Rejected | 保留 normalized method、MTP、DFlash2政策 | 否 | 路由可冻，产品范围另审 |
| A-07 | Agreement | Rejected | 保留禁止隐式全局/ContextVar transport | 否 | 可冻 |
| A-08 | Agreement | Rejected | 保留 E1/E2，但绑定验收 manifest | 是 | 修文后可冻 |
| A-09 | Agreement | Rejected | 保留 method-specific timing/future_offset；公共 builder只消费 view | 否 | 原则可冻，路径分别 gate |
| C-01 | Critical | Accepted | 撤回异构 MRV1 bit parity；决定 legacy defect政策 | **是** | Blocked |
| C-02 | Critical | Accepted | 修正 OFF：保留当前 wrapper/factory | 否 | Blocked |
| C-03 | Critical | Accepted | min 改 resident-set intersection/provider | 否 | Blocked |
| C-04 | Critical | Accepted | 改为 actual-operand route/fingerprint | 否，Codex方向较好 | Blocked for graph |
| C-05 | Critical | Accepted | 冻结显式 live/capture bridge和独立 Draft holder | **是** | Blocked |
| M-01 | Major | Accepted | 删除错误 ceiling 化简 | 是，补证明 | Blocked until edit |
| M-02 | Major | Accepted | 分开全域 W≥K 与 W>0产品政策 | 是 | Blocked until policy |
| M-03 | Major | Accepted | 删除互相冲突的 LCM规则；LCM限 direct-prefix，offset由 provider处理 | 是 | Nonzero offset blocked |
| M-04 | Major | Accepted | shared upper改为多 consumer安全范围 | **是** | Blocked |
| M-05 | Major | Accepted | valid count之外增加 source coverage | **是** | Blocked |
| M-06 | Major | Needs Verification | DSA generator可冻，final op不开放 | 是 | DSA blocked |
| M-07 | Major | Needs Verification | 先定义 SFA producer/consumer/坐标 | 否 | SFA blocked |
| M-08 | Major | Accepted | 补 DSA-v4.1 provider/inventory | **是** | V4.1 blocked |
| M-09 | Major | Accepted | 撤回跨 backend 泛化；padding改 provider-declared contract | 是 | Graph/backend逐项 gate |
| M-10 | Major | Accepted | R+1容量；mixed backend FULL fail closed | **是** | FULL blocked |
| M-11 | Major | Needs Verification | ring由 max in-flight+completion决定；纳入 backend buffers | 是 | Async blocked |
| M-12 | Major | Accepted | DSA宽度按实际 query width推导 | **是** | DSA blocked |
| M-13 | Major | Needs Verification | E1必须与尚待确认的真实验收模型绑定 | **是** | Delivery blocked |
| M-14 | Major | Needs Verification | PCP/DCP/SP用 provider mapping，不用公共乘法 | 否 | Parallel modes blocked |
| M-15 | Major | Needs Verification | plain Eagle区分 route与public contract | 否 | Product decision open |
| m-01 | Minor | Accepted | visible theorem增加 short分支 | 是 | 文档修正 |
| m-02 | Minor | Accepted | DSA-v1/V4.1/future compressed分开 | 是 | 文档修正 |
| m-03 | Minor | Accepted | Target logits只做受控同输入比较 | 否 | 测试修正 |
| m-04 | Governance | Accepted | decision分 Source/Math/Policy/Runtime | 是 | Freeze governance |
| m-05 | Minor/Major | Needs Verification | 先冻结 bridge，再列真实文件 | 是 | 文件表未冻 |

## 12.2 用户指定的 25 个攻击面覆盖表

| # | 攻击面 | 结论 | 对应 Finding / 章节 |
| ---: | --- | --- | --- |
| 1 | 容量公式与化简 | 公式条件成立，化简错误 | M-01、§6.2 |
| 2 | W≥K 的必要/充分性 | 固定 L 充分非必要；全域必要且充分 | M-02、§6.1 |
| 3 | C/needed/width/valid/offset | 需联合约束与 coverage | M-03/04/05、§6.4 |
| 4 | Legacy anchor/group/LCM/PCP-DCP | 异构 parity错误；LCM仅限简单 layout | C-01、M-03/14 |
| 5 | 最小反例 | 已给 9 个 | §6.3 |
| 6 | DSA non-causal/rebase | generator成立，真实 consumer未证 | M-06/08/12、§7.3 |
| 7 | SFA visible count | 无闭合生产者/消费者 | M-07、§7.4 |
| 8 | min(W,retention) | 一般错误，必须集合交 | C-03、§7.5 |
| 9 | padding读/写安全 | 只能 backend-specific | M-09、§7.6 |
| 10 | Narrow Capture Binding入口 | 方向正确，接口不存在 | C-05、§8.1 |
| 11 | Updatable/legacy/no-op | actual operand与mixed updater未证 | C-04、M-10、§8.2–8.3 |
| 12 | Host Ring/Device Workspace | 原则可取，数量与lease未闭 | M-11、§8.5 |
| 13 | ON/OFF baseline | OFF条款会破坏现状 | C-02、§8.6 |
| 14 | epoch覆盖复用/重建 | epoch不等于ownership，必须completion lease | A-04、M-11 |
| 15 | Expected File Changes | bridge/updater/provider缺失 | m-05 |
| 16 | E1交付与真实验收 | 未绑定 acceptance manifest | M-13、§9.2 |
| 17 | Eagle/MTP/DFlash2依据 | 路由多已确认；plain Eagle产品契约未证 | A-06、M-15、§9.1 |
| 18 | Conditional写成Frozen | 多处存在 | m-04 |
| 19 | 旧错误回流 | OFF factory、legacy parity、scalar retention | C-01/02/03、§9.4 |
| 20 | 是否足以指导实现 | 所有权/bridge/data flow尚未闭合 | C-05、§9.5 |
| 21 | Target误 Window | 原则正确；capture共享 state仍有失败路径 | A-01、C-05 |
| 22 | positions被改变 | 原则正确；必须保留现有 factory | A-01、C-02、§7.1 |
| 23 | slot_mapping读 Window table | 设计禁止；需 typed boundary和顺序测试 | A-01、§7.1 |
| 24 | full table污染/重复 Window | 新架构意图正确；MRV1异构路径证明真实风险 | C-01、C-05 |
| 25 | multi-request/preemption/graph shapes | generation reset、R+1与lease不完整 | M-09/10/11、§8.4–8.5 |

# 13. Must Fix Before Final Freeze

以下不是“未来优化”，而是 Final Architecture Freeze 的前置条件。

## P0：所有范围都必须修复

1. 撤回/重写异构 multi-group 的 MRV1 bit-parity 声明；由 maintainer决定 legacy defect政策。
2. 修正 Window OFF 条款，明确现有 wrapper/factory、Target metadata、graph descriptor完全保持 baseline。
3. 删除 min(W,retention) 一般公式，替换为 Draft interval与 resident/native可见集合的 provider交集。
4. 冻结显式 `DraftMetadataInputs`/`DraftWindowView` 到 live builder和 capture dummy builder的真实接口。
5. 明确 capture 使用独立 Draft metadata holder，不得写共享 Target model state。
6. 修正 §16.3 ceiling 化简；把 W≥K 全域政策、W>0产品政策、short-context分支写清。
7. 给 direct-prefix provider加入 destination capacity、source coverage、first-offset、padding row的联合检查。
8. 定义 shared CPU upper 的确切消费者、单位与跨 group安全范围；若无法共享则改为 per-provider字段。
9. 补齐 DeepSeek-V4.1 inventory；在 provider完成前 fail closed。
10. 冻结 acceptance manifest；确认 E1 是否覆盖真实验收模型。

## P1：开放 FULL/Async/复杂 backend 前必须修复

1. actual operator operand按 DIRECT/TASK_REBIND/BACKEND_DERIVED分类并有 runtime trace。
2. mixed-backend updater聚合前，FULL fail closed。
3. capture/replay的 view shape、capacity、padding row、provider descriptor完全一致。
4. host/device/backend-owned buffer都纳入 completion-based lease。
5. DSA-v1 final op、DSA-v4.1 logical indices、SFA top-k/index scatter分别完成 runtime gate。
6. PCP/DCP/SP各自实现和验证 absolute interval projector；不得共享未经证明的 span乘法。
7. 每个 backend声明 padding read/write contract；未声明则禁止 graph padding。

## P2：文档治理必须修复

1. Decision Log 每项标注 Source Fact / Math Theorem / Policy Decision / Runtime Assumption。
2. 所有 Open/Conditional capability不得以 Confirmed/Frozen事实表述。
3. Expected File Changes在 bridge签名冻结后重写。
4. MRV1 golden、absolute set oracle与runtime A/B测试的适用边界写入 Test Matrix。

# 14. Needs Runtime Verification

静态 Python 源码无法关闭下列问题。它们必须继续标记 Needs Verification，不能在修改文字后直接升级为 Accepted/Rejected。

| Test ID | 要验证的真实行为 | 最小测试方法 | 通过条件 |
| --- | --- | --- | --- |
| RV-01 | captured operator实际读取哪个 block/length buffer | 对 actual op kwargs/pointer做 A/B/A origin trace | B replay读B，第三次读A；无 one-step lag |
| RV-02 | enable_enpu true/false 的 update/replay时序 | 两模式注入递增 generation与event trace | consumer generation与proposal一致 |
| RV-03 | DSA-v1 indices的最终坐标含义 | 小型 exact KV oracle，对比 full vs window NPU op | 可见 slot集合精确相同于 oracle；无非法读 |
| RV-04 | DSA sample_from_anchor 两支宽度 | K、K+1 query与边界长度 | 无截断；最大 index在workspace内 |
| RV-05 | DSA-v4.1 logical-index rebase | 独立 V4.1 model/backend A/B | logical/physical映射与full oracle一致 |
| RV-06 | SFA top-k absolute index与visible-count交互 | 固定 top-k、跨 window origin、DCP ranks | 只裁读取，不重编号错误，不污染写地址 |
| RV-07 | padding row内存安全 | 每 backend使用毒值/guard page/sentinel row | padding不读非法源、不写真实 slot |
| RV-08 | mixed backend graph updater | 至少两个不同 updater语义的 groups | 每组参数均更新；否则 capability拒绝 |
| RV-09 | async lane与backend-owned buffer retire | 多请求、preemption、row reuse、延迟event | 复用前所有consumer完成，无 generation错配 |
| RV-10 | native SWA/recycling resident集合 | 从真实 manager导出 blocks/null blocks | Draft读取集合等于 resident∩window |
| RV-11 | capture shape/padding变化 | 多 graph size、动态 batch、R与R+1切换 | 无重捕获误配、越界、stale row |
| RV-12 | Target/positions/slot完全不变 | 固定相同 Target token/candidates做 ON/OFF | Target metadata、positions、slot、logits一致 |
| RV-13 | Window OFF零回归 | eager/PIECEWISE/FULL、各 method调用 spy | wrapper/factory/descriptor/address/perf均为 baseline |
| RV-14 | 验收模型真实 backend选择 | model load打印 capability manifest | 命中已支持组合；未命中则显式拒绝 |
| RV-15 | H2D/device copy与kernel收益 | 分段 profile | 无隐藏同步；收益/开销达到冻结阈值 |

特别说明：RV-01、RV-02、RV-03、RV-05、RV-06、RV-07、RV-09 不能由纯 Python UT替代；必须运行目标 NPU/ACL Graph路径。静态 review最多证明参数构造的意图，不能证明算子内部 interpretation。

# 15. Final Recommendation

## 15.1 最终结论

**不批准 DeepSeek Final Design 直接冻结。** 建议状态为：`NO-GO — revise, then architecture re-review`。

分范围裁决：

| 范围 | 当前建议 |
| --- | --- |
| common math + aligned direct-prefix planner | 修复 M-01/M-02/M-04/M-05 后可条件批准 |
| eager GQA/MLA infrastructure | 修复 C-01/C-02/C-05/M-09，并绑定 acceptance manifest后条件批准 |
| FULL / PIECEWISE graph | 在 C-04/C-05/M-10 与 RV-01/02/07/11关闭前不批准 |
| async scheduling | 在 M-11 与 RV-09关闭前不批准 |
| DSA-v1 | generator theorem可批准；最终 backend在 M-06/M-12 与 RV-03/04关闭前不批准 |
| DSA-v4.1 | inventory/provider与 RV-05关闭前不批准 |
| SFA | 字段契约与 RV-06关闭前不批准 |
| recycling/native SWA | C-03 与 RV-10关闭前不批准 |
| PCP/DCP/SP | M-14 的逐 rank projector验证前不批准 |

## 15.2 DeepSeek 是否比 Codex 更接近可实施方案

**对 E1 工程拆解：是；对完整可冻结架构：否。** DeepSeek 给了更具体的实现顺序、capture窄绑定概念、AR时序、证据分级和性能测试，所以更像工程执行计划。但它在 Window OFF、resident集合、异构 MRV1 parity、actual graph operand和未闭合 bridge上存在冻结级错误。Codex 的 full-state/draft-view边界更安全，适合作为主文档；同时必须修复 §11 列出的自身缺口。

## 15.3 Codex Frozen Decisions 是否改变

主方向不变：Target/positions/slot/full state不可变，Window只产生 Draft-visible view，provider声明映射，Graph使用地址稳定persistent workspace，async使用显式ownership。

但以下决策必须新增或改写：

1. 异构 multi-group 不再无条件引用 MRV1输出为 golden；明确 legacy defect决策。
2. DSA 拆成 v1 physical-index、v4.1 logical-index、SFA/indexer三类 capability。
3. CPU upper 与 valid/source coverage成为 provider/consumer契约的一部分。
4. Draft-only live/capture bridge和独立 metadata holder成为 Frozen API。
5. mixed backend FULL在聚合 updater前 fail closed。
6. DSA generator theorem从 Open升级为条件 Confirmed，但 final op维持 runtime gate。
7. acceptance manifest成为 release scope的唯一依据，而不是抽象 method名称。

## 15.4 若以 Codex 为主文档，最少吸收 DeepSeek 的实质内容

必须吸收以下八项：

1. evidence-level/decision-category治理表；
2. Narrow Capture Binding，但改为显式实例/descriptor-scoped provider；
3. E1/E2 staged rollout与fail-closed capability matrix；
4. AR 的 L0、future horizon、rejection、per-proposal时序契约；
5. DSA generator-level rebase证明及 sample_from_anchor分支测试；
6. typed exact/CPU/planning-upper/backend-padded/local length模型；
7. valid_num stale-tail清理、epoch+lease以及 A/B/A graph测试；
8. 分阶段性能账本和persistent workspace内存预算。

吸收时不得照搬三项错误：错误的 ceiling 化简、min(W,retention) 通式、Window OFF 不套现有 factory。

## 15.5 建议的冻结流程

1. 先合并本文 Accepted finding 到主设计，不写生产代码。
2. 对 C-01、W>0、plain Eagle公开支持、真实验收模型四项做 maintainer policy确认。
3. 冻结 Draft-only builder/capture bridge签名、ownership和错误模型。
4. 完成静态 source gates与数学 property tests。
5. 在目标 NPU 上关闭 §14 的必需 runtime tests。
6. 再召开一次 Final Architecture Review；只对已关闭 capability标 Frozen，其他保持 Conditional/Open。

在这之前，DeepSeek 文档可以作为重要候选设计和 E1工作分解参考，但不能作为“已冻结、可覆盖全部 MRV2 speculative draft sliding window”的实现规范。
