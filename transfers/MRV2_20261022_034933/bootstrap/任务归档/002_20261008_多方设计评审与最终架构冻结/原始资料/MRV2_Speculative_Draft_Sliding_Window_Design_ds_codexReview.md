# MRV2 Speculative Draft Sliding Window 设计严格审查（Codex Review）

> Review 对象：`MRV2_Speculative_Draft_Sliding_Window_Design.md`  
> 事实基线：`Sliding window原理_gpt.md`、`Sliding window源码_codex.md`，以及 2026-10-08 本地当前 checkout 的 vLLM / vLLM-Ascend 源码  
> Review 性质：失败模式审查；不修改生产代码，也不重写原设计

## Review Verdict

**结论：Request Changes / 当前不具备进入生产实现的条件。**

原设计提出的几条顶层原则是正确的，尤其是：Target 必须保持 full、`positions` 必须保持绝对坐标、`slot_mapping` 必须基于完整物理 KV、Window 只构造 Draft-visible read view、graph 下 buffer 必须持久且地址稳定。

问题在于，推荐的 “Candidate C + Candidate A” 从原则落到具体接口后，仍存在若干相互矛盾或未闭合的契约。按文档当前文字直接实现，至少有以下四类可构造的静默正确性错误：

1. 窗口表按 KV group 计算，但 device/CPU/local length 与 interval 只有一份；不同 block size 时不存在一份长度能同时匹配所有 group。
2. DSA/SFA T2 路径把 absolute interval、window-relative `seq_lens` 和左移后的 table 列号混在一起，索引坐标会直接算错。
3. W1 只保证 capture/replay 的 shape 相同，没有保证 tensor 地址、builder instance、派生 metadata 和更新时序相同；对 `update_graph_params()` 为 no-op 的 SFA/DSA 尤其危险。
4. 单一 mutable plane 没有 async lease/event；active-row source tail 又没有按真实 `num_blocks` 掩码，动态 batch、preemption 和 request slot 复用时可能搬入已释放或已归属其他请求的 block id。

本 review 对用户列出的 25 个攻击面全部给出结论。风险分级含义：

- **Critical**：可能造成静默读错 KV、跨请求数据污染、Target 被误改、graph replay 使用旧状态，或核心数学无法同时成立；设计未修正前应阻止实现合入。
- **Major**：明确的兼容性、模式覆盖、性能、显存或扩展性缺口；可通过 fail-closed 缩小首期范围，但不能宣称已支持。
- **Minor**：文档内部矛盾、验证口径不足或容易误导实现者的问题。

## 25 项攻击面覆盖索引

| # | 攻击面 | 结论 | 详细编号 |
|---:|---|---|---|
| 1 | Target 是否可能被误 Window | Critical | C1 |
| 2 | positions 是否可能被改变 | Critical | C2 |
| 3 | slot_mapping 是否可能读到 windowed table | Critical | C3 |
| 4 | full block table 是否可能被覆盖/污染 | Critical | C4 |
| 5 | seq_lens 是否可能被重复 Window | Critical | C5 |
| 6 | Window OFF 是否零回归 | Major | M1 |
| 7 | per-group block size | Critical | C6 |
| 8 | padding rows | Critical | C7 |
| 9 | CPU upper bound 与 device exact | Critical | C8 |
| 10 | graph capture 地址稳定 | Critical | C9 |
| 11 | capture/replay metadata 一致 | Critical | C10 |
| 12 | eager / PIECEWISE / FULL 差异 | Major；Eagle F3 子项为 Critical | M2 |
| 13 | async 生命周期 | Critical | C11 |
| 14 | contextvar/context 跨请求、线程、async 泄漏 | Critical | C12 |
| 15 | Eagle3 / DFlash / DSpark timing | Critical | C13 |
| 16 | unsupported methods 被错误启用 | Major | M3 |
| 17 | native model SWA 与 `draft_window_size` 双重计算 | Critical | C14 |
| 18 | DCP / PCP / SP / CP local length | Critical | C15 |
| 19 | Flashcomm interaction | Major | M4 |
| 20 | model-specific assumptions | Major | M5 |
| 21 | hidden performance regressions | Major | M6 |
| 22 | persistent buffer memory overhead | Major；极端配置可 OOM | M7 |
| 23 | multi-request / dynamic batch | Critical | C16 |
| 24 | preemption / request removal | Critical | C17 |
| 25 | graph padding / different batch shapes | Critical | C18 |

# Critical Issues

## C1. Target 仍可能被误 Window：所谓“显式 view”最终仍依赖进程级 monkeypatch

- **风险等级**：Critical
- **对应设计章节**：P1/P3/P11、Candidate C、§5.4、§5.5 F3、§8.4
- **为什么可能发生**：
  - 设计声明不用隐式全局/contextvar，但推荐路径仍要求扩展 `build_draft_attn_metadata_factory()`。该 factory 并不是显式参数链；它会临时替换模块级 `_BUILD_ATTN_METADATA_MODULE.build_attn_metadata`，并通过 closure 注入参数。[`attn_utils.py:1240`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:1240)
  - 两个 speculator scope 嵌套或跨线程交错时，后进入者会覆盖前者的函数，退出顺序不同还可能恢复成错误 closure。此时另一个 draft、甚至恰好调用该模块符号的非 draft build，都可能拿到错误 `draft_window_view`。
  - AR 首步当前直接复用 Target metadata：eager/PIECEWISE 在 [`autoregressive/speculator.py:305`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:305)，FULL 在 [`Ascend autoregressive/speculator.py:654`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:654)。仅过滤字典不会复制 metadata 对象或内部 tensor。
  - F3 虽然提出“重建 draft metadata”，却没有把 eager/PIECEWISE 和 FULL capture 两个入口都定义成同一套 draft-only builder/storage，也没有禁止以 Target metadata 做 shallow copy。
- **需要什么源码证据证明安全**：
  - 证明任意 Target metadata build 都不可能在 window factory 生效期间调用被替换的模块符号；需要覆盖 async、PP、多实例和异常退出，而非只看单线程正常路径。
  - eager、PIECEWISE、FULL 首步分别证明：draft metadata dict、每层 metadata 对象、内部可变 tensor storage、builder-owned persistent state 均与 Target 不同。
  - Target forward 前后对 `input_block_tables`、slot mappings、metadata 内容与对象 identity 做快照比对。
- **建议修改**：
  - 不要用现有 module monkeypatch factory 传 window view。新增实例级、显式参数的 draft metadata build API，view 由 speculator/graph manager 直接传入。
  - F3 必须升级为完整的 `build_windowed_draft_prefill_metadata(...)` 契约，eager/PIECEWISE/FULL capture/replay 共用，并且只接收 `draft_attn_layer_names` 对应的 builder。
  - 运行时断言 draft layer 集与 Target-only layer 集不交叉；禁止以 Target metadata 为模板做 shallow copy。

## C2. `positions` 虽在原则上“不动”，F3 与 capture 路径仍可能传入 0 或 stale padding

- **风险等级**：Critical
- **对应设计章节**：P1、§5.4、§5.5、§8.1、T3/T7
- **为什么可能发生**：
  - Ascend 公共 builder 在调用者不传 `positions` 时会直接创建全 0 tensor。[`attn_utils.py:286`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:286)
  - 当前 AR override 的注释已明确说明：如果未注入真实 positions，capture 会把 position-0 RoPE 烘进图，acceptance 会崩。[`autoregressive/speculator.py:573`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:573)
  - `prepare_prefill_inputs` 只复制 active query positions，却只清 padded `seq_lens`，没有清 padded positions。[`autoregressive/speculator.py:742`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:742) factory 又按 `pad` 整段切片注入，导致大 batch 后的小 batch可能携带旧 positions。
  - DFlash capture 使用直接绑定的 Ascend `build_attn_metadata`，不经过 draft factory；capture 路径见 [`dflash/cudagraph.py:55`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:55) 和绑定点 [`patch_dflash_speculator.py:28`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/patch/worker/patch_v2/patch_dflash_speculator.py:28)。F3 新路径若未显式传 positions，会命中全 0 fallback。
- **需要什么源码证据证明安全**：
  - 每个 method × mode 下，最终 builder 收到的 active positions 与 model.forward 收到的 positions 必须逐位相等，且都是真实绝对位置。
  - 证明 padded position 不会被 RoPE gather、SFA indexer 或 captured op 当成有效行；只验证 active 输出不够。
- **建议修改**：
  - 将参数命名为 `absolute_positions`，从类型/接口上禁止减 window origin。
  - F3、DFlash/DSpark live、capture 和 replay 均显式传该 tensor；不得依赖 `positions=None` fallback。
  - 为 padded positions 定义明确的清零或 mask 规则，并测试大 batch→小 batch、不同 graph bucket 连续 replay。

## C3. `slot_mapping` 仍有机会读到 windowed table，且 AR 与 DFlash/DSpark 的物理写路径并不相同

- **风险等级**：Critical
- **对应设计章节**：P1/P3、§5.3、§5.4、§7.2
- **为什么可能发生**：
  - AR `compute_slot_mappings()` 读取 authoritative `block_table_ptrs`，不会读取传给 attention 的局部 list。[`block_table.py:190`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:190)
  - DFlash/DSpark 不同：`prepare_dflash_inputs()` 直接接收并读取 `BlockTables.input_block_tables[gid]`，用绝对 position 计算 context/query slots。[`dflash/speculator.py:375`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:375) [`Ascend dflash/speculator.py:255`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:255)
  - 设计只用文字规定“先 slot、后 window”。如果实现者为方便把 `self.block_tables.input_block_tables` 替成 plane，或在 per-group prepare 完成前刷新/覆盖，就会直接写错物理 KV 地址。
  - `build_attn_metadata()` 接口同时接收 `block_tables` 与 `slot_mappings`，目前没有类型阻止 window table 被再次传给物理写地址计算。
- **需要什么源码证据证明安全**：
  - DFlash/DSpark 每个 active gid 调用 prepare kernel 时，block-table storage 必须等于 full gathered `input_block_tables[gid]`。
  - 所有 physical slot 计算完成后才允许创建 read view；window 前后 slot mapping 必须逐位不变。
- **建议修改**：
  - 把顺序编码进 API：`prepare_physical_writes(FullBlockTables)` 返回完成标志/immutable result 后，才能创建 `DraftReadView`。
  - 明确禁止重新赋值 `BlockTables.input_block_tables`；公共漏斗只能替换局部的 attention read 参数。
  - 引入语义类型 `PhysicalFullBlockTable` 与 `DraftReadBlockTable`，避免两个裸 `Tensor`/`Sequence[Tensor]` 混用。

## C4. full block table 可能因 alias、局部 list 修改或 backend in-place 操作被污染

- **风险等级**：Critical
- **对应设计章节**：P2/P3/P8、§5.2、§5.4、§8.3、F3
- **为什么可能发生**：
  - 设计以 `data_ptr()` 不同作为“输出不等于 full table”的主要断言；但带 offset 的 slice/view 可以有不同 `data_ptr()`，仍共享 underlying storage，对其 `copy_`/`zero_` 会污染 full storage。
  - `DraftAttentionView(frozen=True)` 只冻结 Python 字段，不能让 tensor 只读。
  - 公共漏斗提议“替换 `block_tables[i]`”。若直接修改调用者传入的 list，会污染后续 builder 或 Target 仍持有的容器；如果输入是 tuple，又会迫使实现者绕路改共享对象。
  - 某些 builder 会原地清 padded table 行，例如 DSA 在 [`dsa_v1.py:1095`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1095)。如果这一引用意外仍是 full table，污染立即发生。
- **需要什么源码证据证明安全**：
  - plane 的 storage 与 authoritative `block_tables[*].gpu`、gathered `input_block_tables[*]`、slot mappings 全部不别名。
  - refresh、所有 builder build、capture/replay 后，full authoritative/gathered table 内容逐位保持不变。
- **建议修改**：
  - plane 只能通过独立 `torch.empty/zeros` 分配，禁止由 full tensor slice/view 派生。
  - 漏斗按 gid 构造新的局部 metadata 参数，不修改调用者 list，不修改 shared common object。
  - alias 检查使用 storage 范围/正式 alias API，而不是只比较当前 view 的 `data_ptr()`。

## C5. repeated Window 防线不足：`epoch += 1` 既不能证明 full 来源，也不能阻止 AR 重复推进

- **风险等级**：Critical
- **对应设计章节**：P2/P8、§5.3、§6 F4、§8.3
- **为什么可能发生**：
  - epoch 只是计数，不能证明 table/length 是 full，也不能标识 proposal、request ordering、step 或 source generation。
  - DFlash live path先 build 一次，FULL manager replay 前又 build 一次。[`dflash/speculator.py:451`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:451) [`dflash/aclgraph.py:86`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:86) 若第二次误用第一份 windowed CPU length，table pointer断言也检测不到。
  - 更严重的是，设计要求 AR 每个 decode step refresh，却每次固定使用 `future_offset=K`。当前 AR device `seq_lens` 会在 step 间递增。[`autoregressive/speculator.py:853`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:853) [`autoregressive/speculator.py:954`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:954) 因此实际 anchor 变成 `L+s+K`，窗口每步额外右移。
- **需要什么源码证据证明安全**：
  - 同 proposal 的 live build、manager rebuild 必须从同一 full-generation source 重算，结果逐位相同且不重复 materialize。
  - K≥3 时逐 step 对比 MRV1：proposal-level end、start、visible length、最终可见 block 集完全一致。
- **建议修改**：
  - refresh 唯一输入改为不可混用的 `FullDraftState`；`DraftAttentionView` 不能传回 refresh API。
  - generation key 至少包含 `proposal_generation`、`request_order_generation`、`gid`、`anchor`、`descriptor/lane`。
  - AR 使用 proposal-level 固定 `proposal_end = corrected_base_len + K`；每个 group 的 start 一次确定，step s 只更新 `current_full_len(s)-start_g`。若使用 remaining offset，则必须是严格定义的 `K-s`，不能每步继续加完整 K。

## C6. per-group block size 与单一 length/interval 在数学上不兼容

- **风险等级**：Critical
- **对应设计章节**：P4/P6、§5.2、§5.4、§10 T6
- **为什么可能发生**：
  - 设计给每个 group 独立 `tables[gid]`，却只定义一份 `seq_lens`、`seq_lens_cpu`、upper、DCP local 和 intervals。
  - `start_g = floor((L+K-W)/b_g)*b_g` 随 `b_g` 变化，因此 `windowed_len_g=L-start_g` 也随 group 变化。例：`L=190,W=100,K=0`，`b=64` 得 `start=64,len=126`；`b=128` 得 `start=0,len=190`。不存在一份 length 能同时匹配两张表。
  - 当前 Ascend 漏斗虽逐 group 循环，却给所有 group 传同一份 device/CPU/local length。[`attn_utils.py:294`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:294)
  - `BlockTables` 明确允许每组不同 `kernel_block_size` 和 row width。[`block_table.py:48`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:48)
  - DSA 还缓存/跨 group 共享 request-level metadata；窗口后“seq_lens group-invariant”不再天然成立。[`dsa_v1.py:1058`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1058)
- **需要什么源码证据证明安全**：
  - 要么证明所有可达 draft group 的 kernel block size 永远相同；当前源码和设计目标都没有该保证。
  - 要么逐层证明最终 metadata 读取的是 gid 对应的 table、device exact、CPU exact/upper 和 local length，并且跨组 cache 不复用首组结果。
- **建议修改**：
  - view 改为 `groups[global_gid] -> DraftWindowGroupView`，整套 table/length/interval/origin 全部 per-group。
  - 替换逻辑必须位于 `build_attn_metadata()` 的 per-group 循环内部。
  - DSA shared cache key 加入 gid/window origin，或只共享真正与 group 无关的 query 数据。
  - 若首期不支持异 block size，配置阶段 fail closed；不能默默使用 group 0。

## C7. padding 设计漏掉 active-row stale tail，也没有区分 actual req 与 graph-padded req

- **风险等级**：Critical
- **对应设计章节**：P7、§5.2、§5.4.1、F6、T5
- **为什么可能发生**：
  - 设计的 refresh 签名只有 `num_reqs`，没有 `num_reqs_padded`/descriptor，无法精确定义需要清理的 graph rows。
  - 当前 gather kernel只会把 padded row 全清零；active row只复制 `[0,num_blocks)`，不会清其余列。[`block_table.py:255`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:255)
  - 设计 materializer 的 mask 只有 `src < full_cols`，没有 `src < valid_num_blocks[row,gid]`。因此 stale block id 可能落在 `needed` 以内并被复制到 window table；清 destination tail 无法修复这种 source 污染。
  - graph query padding 与 KV padding 不是同一语义：padded KV length/table 应为 0，但某些 FIA query cumulative lengths 仍必须覆盖 descriptor 的 padded token 数。
- **需要什么源码证据证明安全**：
  - 每 group、每 batch-order row 的真实 valid block count；actual req 与 padded req 两个计数。
  - 连续覆盖：8→3、同 row 长→短、request permutation、不同 FULL descriptor、K 跨 block 边界；最终 source load 必须不超过 valid count。
- **建议修改**：
  - refresh 强制接收 `actual_num_reqs`、`padded_num_reqs`、`valid_num_blocks_by_gid`、descriptor/generation。
  - valid count 必须按本轮 `idx_mapping` gather 到 batch order；source mask 使用 `src_col < valid_count[row]`。
  - 只清 KV read plane 的 padded rows/lengths/intervals/derived indices；不要把 query-side graph padding一并归零。

## C8. CPU upper 与 device exact 无法按当前方案保持同源，独立窗口化甚至会破坏“upper”性质

- **风险等级**：Critical
- **对应设计章节**：P4/P12、§5.2、§5.4、§5.6、F8/F9、Q1–Q4
- **为什么可能发生**：
  - DFlash/DSpark 的 device exact length 由 NPU kernel 使用 device `num_rejected` 修正并写入 `input_buffers.seq_lens`。[`Ascend dflash/speculator.py:286`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:286) 当前 CPU helper 只按 target CPU + step 估算，并没有等价 rejection correction。
  - 设计同时要求“CPU exact 与 device exact 同源”和“不新增 D2H”，但当前 parallel path 没有这样的 CPU exact producer。
  - `seq_lens_np=None` 时 Ascend 漏斗会把所有 CPU length填成统一 `max_seq_len`。[`attn_utils.py:253`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:253) 某些 builder会优先 CPU字段。
  - 对 exact 和 optimistic upper 分别套块对齐函数，不保证转换后的 upper 仍 ≥ exact。反例 `W=100,b=64,K=0`：exact `L=150 -> 150`，upper `U=200 -> 136`，结果 upper 反而更小。
- **需要什么源码证据证明安全**：
  - 逐 backend 证明 CPU字段究竟是 exact、capacity upper，还是会直接成为算子 `actual_seq_lengths_kv`。
  - 找到无同步的 rejection-corrected CPU exact producer，或证明相关 backend完全改用 device exact。
  - 对任何 `L<=U` 给出 window 变换后 `exact'<=upper'` 的数学证明。
- **建议修改**：
  - 类型上拆分 `DeviceExactLength`、`CpuExactLength | None`、`CpuUpperBound`，禁止一套函数盲算。
  - upper 必须使用保守解析上界，或由 exact 的同一个 start 派生；不能独立按自己的 rounded start 计算。
  - 需要 CPU exact 的组合若没有生产者，应选择：异步 D2H host ring + event、backend 改用 device-derived metadata，或 fail closed。

## C9. graph capture 地址稳定性未成立：same shape 不等于 same address

- **风险等级**：Critical
- **对应设计章节**：P5、§5.4.1、§5.4.4 W1、§8.2
- **为什么可能发生**：
  - W1 capture 使用原 input buffer/full dummy table，replay 使用另一块 plane storage；表宽相同只解决 shape，不解决 pointer。
  - SFA/DSA builder会直接 alias common `seq_lens`，而两者的 `update_graph_params()` 当前是 no-op。[`sfa_v1.py:641`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:641) [`sfa_v1.py:885`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:885) [`dsa_v1.py:1621`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1621)
  - ACLGraphWrapper 只检查 positional tensor args 的地址，metadata 内嵌 tensor 不在 debug 检查范围内。[`acl_graph.py:186`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/compilation/acl_graph.py:186)
  - 文档自身也矛盾：Candidate A/§8.2 写按 `max_window_blocks_g` 分配，§5.4.1 又要求 full row width；两种实现有完全不同的 capture contract。
- **需要什么源码证据证明安全**：
  - 按 GQA/MLA/SFA/DSA 列出 captured operator实际消费的 table、device length、indices、plan、host op param 的地址。
  - 对每个 tensor证明：capture/replay同地址，或明确进入当前 replay 的 graph update task，而非下一 replay。
- **建议修改**：
  - 放弃“W1 对所有 backend 通用”。capture strategy 必须成为 backend capability。
  - no-op backend必须在 capture 时就绑定 window persistent storage，或绑定 builder-owned 唯一 storage并保证 replay 前原地刷新。
  - 可 update backend才允许 runtime rebind；对每个 descriptor做 pointer contract测试。

## C10. capture/replay 的 builder、派生 metadata 与更新时间不一致

- **风险等级**：Critical
- **对应设计章节**：§1.5、§5.4.4、§5.5 F3、§8.1、T8、Q17/Q18
- **为什么可能发生**：
  - capture dummy 的 length/positions/causal 会触发 SFA/DSA 派生 plan、indices 与分支；same table shape不能证明这些 derived metadata 与 runtime window一致。
  - Eagle F3 runtime要重建 draft metadata，但当前 AR prefill capture使用 `target_input_buffers`，且非 replicated PCP 时使用 target attention groups。若 capture 写 Target builder-owned storage，而 replay写 draft builder storage，no-op backend会一直读取 capture 的旧地址。
  - DFlash live 与 FULL manager各 build 一次；值幂等不代表使用同一个 builder instance 或同一 persistent storage。
  - graph manager与底层 ACL wrapper多处是“先 replay、后 update”。例如 DFlash manager [`dflash/aclgraph.py:100`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:100)，UpdatableGraph内部 [`acl_graph.py:304`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/compilation/acl_graph.py:304)。不能仅凭 Python 书写顺序判定本轮还是下一轮参数生效。
- **需要什么源码证据证明安全**：
  - method × backend × mode 的 capture builder identity 与 replay writer identity相同。
  - 交替 A/B 两组完全不同 window origin连续 replay，证明没有 capture-stale 或 one-step lag。
  - F3 capture与runtime走同一 draft-only metadata producer及同一 builder-owned buffer。
- **建议修改**：
  - 定义统一 `prepare_draft_window_attention_state(descriptor, capture_or_replay, lane)`，capture/replay共用相同 group、plane与builder state。
  - 将 graph update 的“为当前 replay还是下一 replay”写成显式时序契约并用 event/交替值测试证明。
  - F3 capture改造完成前，Eagle FULL/PIECEWISE window应明确 unsupported。

## C11. async 生命周期没有所有权证明；单一 plane 从第一版起就不安全

- **风险等级**：Critical
- **对应设计章节**：P5/P11、F10、§8.4
- **为什么可能发生**：
  - MRV2 async 明确允许多个 in-flight batch；`max_concurrent_batches` 为 `pp_size+1`。[`config/vllm.py:589`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/config/vllm.py:589)
  - 上游 UVA pool明确要求复用 slot 前所有 GPU reader retire，并按并发深度轮转。[`buffer_utils.py:19`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/buffer_utils.py:19) [`buffer_utils.py:61`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/buffer_utils.py:61)
  - frozen view不会冻结底层 tensor。下一 batch refresh单一 plane时，上一个 graph/update stream可能仍在读，导致一个 forward混合两个 epoch。
  - “若实测存在并发再双缓冲”不是正确性证明；PP>1 时两路也可能不够。
- **需要什么源码证据证明安全**：
  - 每一类 CPU/NPU metadata reader 的 retire点与 happens-before关系。
  - 如果声称单 slot可行，必须证明同 runner 的所有 reader都在同一 stream严格串行且 Python不会进入下一 refresh；当前源码没有这份证明。
- **建议修改**：
  - 第一版即定义 lane/ring，深度至少与 `max_concurrent_batches` 或正式 workspace 并发槽一致。
  - view携带 `lane_id + generation`；refresh前等待该 lane retire event，replay/update完成后记录 reader event。
  - CPU exact/upper/UVA buffer同样按 lane管理；显存预算乘真实 lane数。

## C12. contextvar/context object 无法解决泄漏；当前推荐路径仍是 process-global 状态

- **风险等级**：Critical
- **对应设计章节**：P11、Candidate C、§5.4、§8.4
- **为什么可能发生**：
  - 当前 factory 是模块级函数替换，不是 context-local。[`attn_utils.py:1240`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/attn_utils.py:1240)
  - `ForwardContext` 当前也不是可作为安全 lifetime owner 的机制；即使改成 Python `ContextVar`，它只能隔离 task-local Python引用，不能阻止同一 plane storage被下一步覆盖，也不能延长 NPU async reader 生命周期。
  - nested scope、异常退出、两个 speculator实例或两个线程交错时，函数恢复顺序与“当前 view”都可能串味。
- **需要什么源码证据证明安全**：
  - 不存在模块级可变“当前 builder/current view”；多线程 barrier交错、嵌套scope、异常退出、多实例测试全部通过。
  - device storage lifetime另有 lane/event证明，不能以 context isolation替代。
- **建议修改**：
  - window view必须是真实函数参数/实例方法参数，并显式传到 graph manager；现有 wrapper仅作为旧兼容层，window不能依赖它。
  - 不建议用 contextvar补丁掩盖接口问题；contextvar最多保存不可变标量上下文，不能持有共享 mutable plane作为正确性机制。

## C13. Eagle3、DFlash、DSpark 的 timing 不能由一个固定 boundary/future_offset 规则覆盖

- **风险等级**：Critical
- **对应设计章节**：§5.3、§5.5、§5.6、§8.1
- **为什么可能发生**：
  - DFlash/DSpark kernel在 metadata build前已把完整 parallel query折进 `seq_lens`，所以 `future_offset=0` 是合理的。[`Ascend dflash/speculator.py:286`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:286)
  - AR 的 `seq_lens` 则随 draft step推进。设计写“每步 refresh + K”，会重复把整个未来 horizon 加到已推进的长度上，见 C5。
  - fused/FULL AR metadata只构建一次，图内多 step推进的是现有 `input_buffers.seq_lens`；新 plane 的 length若未被 captured update kernel更新，会在整个 merged graph中保持静态。[`autoregressive/speculator.py:565`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py:565) [`Ascend autoregressive/speculator.py:438`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py:438)
  - DSpark还有 per-group prepare、non-causal indices、DSA/SFA device metadata任务；其“最后安全点”与 DFlash GQA并不相同。
- **需要什么源码证据证明安全**：
  - 每 method分别画出 full seq、query已计入程度、physical slot完成点、table最后覆盖点、builder消费点。
  - eager/PIECEWISE/FULL逐 step对拍最终可见绝对 token集合，而不只是比较 `seq_lens` 数值。
- **建议修改**：
  - `DraftWindowPolicy`只返回 method contract，不直接返回一个可到处复用的 K。
  - AR使用 proposal-level fixed anchor；DFlash/DSpark使用当前 parallel endpoint且 offset 0。
  - FULL merged AR必须拥有 per-step persistent device lengths，或让 captured update kernel同步维护 window-relative length；仅有 CPU step buffers不足。

## C14. native model SWA 与 `draft_window_size` 并不会“天然取交集”

- **风险等级**：Critical
- **对应设计章节**：§1.7、P10、§5.4.2/5.4.3、§7.2、T10
- **为什么可能发生**：
  - FIA native SWA由算子 mask/window参数表达；DSpark DSA non-causal native SWA则由显式 `dspark_swa_indices` 表达。[`dsa_v1.py:420`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:420)
  - 推荐 T2 先把 common table/seq_len窗口化，再把 backend start与 absolute interval start取 max。这会比较两个不同坐标系；随后 `pos//block_size` 还会拿 absolute列号去索引左移后的 table。
  - SFA `ori_mask_mode=0`，窗口完全依赖显式 top-k indices；仅缩 table/length不能形成交集。[`sfa_v1.py:81`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:81) [`sfa_v1.py:198`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:198)
  - native `SlidingWindowSpec` 还可能在物理层已经释放旧块，配置更大的 draft window无法恢复不存在的 KV。
- **需要什么源码证据证明安全**：
  - 对每 backend直接验证最终可见绝对集合等于 `draft_window_set ∩ native_swa_set ∩ physically_retained_set`。
  - 明确 indices 是 absolute logical position、window-relative position还是physical slot，并验证 table origin转换。
- **建议修改**：
  - T2后端应选择一种一致坐标：保留 full table/full absolute seq并用 absolute interval过滤最终 indices；或显式携带 `window_origin`，所有 lookup都先减 origin。
  - SFA/DSA索引集合本身必须做集合级 UT；acceptance变化不能作为正确性证明。
  - 从真实 layer/backend/KV spec读取 native window capability，不用单一 HF scalar代表全模型。

## C15. DCP/PCP/SP/CP 不只是 local length：table 列坐标与 first-page offset 也会改变

- **风险等级**：Critical
- **对应设计章节**：§5.2、§5.4、F9/F18、§9.2/§9.4
- **为什么可能发生**：
  - 设计已经正确指出 local count应为 `local(end)-local(start)`，但仍用 global `start/b_g` 左移 table。
  - DCP block table列是 rank-local/virtual坐标：slot kernel先把 absolute position映射到 local position再选列；DFlash/DSpark prepare甚至直接用 `query_pos // (block_size * CP_SIZE)` 查表。[`cp_utils.py:53`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/cp_utils.py:53) [`Ascend dflash/speculator.py:264`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:264)
  - 即使改成 `local(start)//b`，当 start位于rank-local page中间时，只有“左移 table + 缩短 length”仍表达不了 first-page token offset。
  - DSA-CP会从 full `seq_lens-query_len` 派生 local metadata；SFA-DCP按“列号==逻辑块号”构造 replicated view。左移 table会破坏这个假设。
  - PCP replicated path还会在较晚位置 re-gather/rebuild，早创建的 view可能 stale。
- **需要什么源码证据证明安全**：
  - 对每 backend/table layout给出 absolute `[start,end)` 到 `(source_col, first_page_offset, local_visible_len)` 的正式映射。
  - 证明 MRV1 block alignment在每个 CP rank上恰好 page-aligned；当前没有。
  - PCP global/local table的最后 gather点以及 capture/replay来源必须明确。
- **建议修改**：
  - 引入 `BlockTableLayout/WindowPartitioner` capability，view携带 per-gid/per-rank `table_origin` 与 `first_token_offset`。
  - 若 backend接口无法表达非零 offset，就按 CP super-page对齐并明确这是语义变化，或该组合首期 fail closed。
  - DCP、DSA-CP、SFA-DCP不能被“公共 T1 自动支持”覆盖。

## C16. multi-request / dynamic batch 下 row 语义会变化，epoch/data_ptr 无法绑定 request identity

- **风险等级**：Critical
- **对应设计章节**：P7/P8、F6/F10、§8.4、T5/T9
- **为什么可能发生**：
  - plane row按“本轮 batch order”解释，而不是 persistent request row；`idx_mapping` 每 step按当前 request order重建。
  - batch从 8→3、request排序变化、DP/graph padding变化时，相同 plane row可立即代表另一请求。
  - frozen view和整数 epoch没有 request IDs、order generation、descriptor或lane，不能证明某 row 的 table/length属于当前请求。
  - 同一 source gathered table active tail还可能保留前一 request的 block id，见 C7。
- **需要什么源码证据证明安全**：
  - request order交换、8→3→8、同 req prefill→decode、不同 graph bucket、两个 in-flight batch交错时，每个 metadata row都与当轮 `idx_mapping` 一致。
- **建议修改**：
  - view携带 `request_order_generation`、`actual_num_reqs`、`padded_num_reqs`、descriptor、lane；按当前 batch order每次重建，不做跨 request row缓存。
  - debug/test中保存 batch row→persistent req index或 req-id hash，用于发现错配。

## C17. preemption / request removal 会真实触发 stale block 复制与异步复用

- **风险等级**：Critical
- **对应设计章节**：P7、F6、§8.4；原设计缺少独立 preemption contract
- **为什么可能发生**：
  - request被移除后，persistent request index可被新请求复用；新短请求只覆盖 block table前缀。
  - authoritative table更新与 gathered active row都不会自动清除所有尾列；因此“旧长请求→删除→同 slot新短请求”正是 stale tail 的直接触发器。[`block_table.py:112`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:112) [`block_table.py:269`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:269)
  - scheduler延迟释放 physical block并不能代替 source validity mask，也不能保证旧 plane的 device reader已经 retire。
- **需要什么源码证据证明安全**：
  - 长请求preempt/finish后，同slot加入短请求，旧block id立即分配给别的请求；最终 window source load只覆盖新请求 valid count。
  - abort、resume、request remove/add与 async graph replay组合测试。
- **建议修改**：
  - `valid_num_blocks`成为 read-plane的一等输入，所有 source load都按它mask。
  - plane不缓存跨 generation的 request identity；scheduler block free与plane lane retirement分别建模。

## C18. graph padding / different batch shapes 只固定列宽不够

- **风险等级**：Critical
- **对应设计章节**：§5.4.1、§5.4.4、§8.1、T5/T8
- **为什么可能发生**：
  - 设计只固定 table列宽，没有定义首维 slice、actual/padded request数、token padding与每 descriptor metadata。
  - FULL descriptor可把实际 req向上 pad；PIECEWISE通常没有相同的 request padding语义。view若总暴露 `[cap_reqs,row_width]`，capture/replay看到的 shape仍可能不同。
  - DSA依赖 `num_actual_reqs`显式清 padded request；若只把 length清0却把 actual count留成 padded count，builder可能走错分支或生成错误 indices。[`dsa_v1.py:1095`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/dsa_v1.py:1095)
- **需要什么源码证据证明安全**：
  - 每个 captured bucket下，table/length/interval/indices/plan的shape、地址和 `num_actual_reqs` 均与 capture一致。
  - 从大 bucket切小 bucket再切回，且窗口 origin不同，不能出现旧row/旧plan。
- **建议修改**：
  - 定义 `DraftAttentionView.for_descriptor(desc, actual_num_reqs)`，返回与 descriptor精确一致的 slice，并单独传 actual count。
  - 测试所有 capture buckets、1/3/边界请求数、FULL prefill/decode两个 manager、动态 batch和不同 K。

# Major Issues

## M1. Window OFF 不能按当前设计证明“零回归”

- **风险等级**：Major
- **对应设计章节**：P9、§5.4、§5.5、§7.3、T2/T3/T7
- **为什么可能发生**：
  - 为了传 view，设计要求 DFlash增加 factory；当前 DFlash live只有 `build_attn_metadata_wrapper()`。[`dflash/speculator.py:116`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py:116)
  - 现有 factory不只可能注入 window，还会注入 positions、is_prefilling、attn_state、parallel_config；若无条件套用，`view=None` 也已改变 OFF 路径输入。
  - 公共 builder新增 optional branch本身与文档“关闭路径不得引入任何 branch”的绝对表述矛盾。
  - 全局补 `gt=0` 校验还可能改变 MTP/unsupported method原本 warn-ignore或原 factory错误的顺序。
- **需要什么源码证据证明安全**：
  - OFF时每个 method走与当前 checkout完全相同的 context manager、调用签名、metadata对象结构、capture key与builder路径。
  - OFF before/after 的输出、acceptance、p50/p99、throughput与显存对比。
- **建议修改**：
  - speculator初始化时分派 window-enabled专用路径；OFF保留原方法，不进入window-aware factory/plane。
  - “零回归”改为可测试的语义与性能阈值，不写“零额外 branch”这种不可实现约束。

## M2. eager / PIECEWISE / FULL 不是同一路径，当前 mode matrix 过度概括

- **风险等级**：Major；Eagle F3 capture不一致部分按 C10 视为 Critical
- **对应设计章节**：§5.3、§7.1、§8.1、T8
- **为什么可能发生**：
  - DFlash/DSpark当前主要是 eager/FULL，upstream会对不支持的 PIECEWISE做模式降级；DFlash2 Ascend又只允许 eager。不能用一个公共 graph hook代表所有 method。
  - AR PIECEWISE、FULL merged multi-step和 eager逐step rebuild拥有不同 request padding、metadata build频率与 length producer。
  - PIECEWISE capture的 attention-like op与 eager breakpoint可能读取不同 metadata来源；原设计没有指定 view在哪一侧生效。
- **需要什么源码证据证明安全**：
  - method × mode矩阵逐项给出：view创建时刻、actual/padded count、metadata producer、capture builder、replay updater与tensor lifetime。
- **建议修改**：
  - 每个 method capability显式声明 `NONE/PIECEWISE/FULL/FULL_DECODE_ONLY` hook；unsupported mode禁用或报错，不能 fall-through。
  - 分阶段门禁：DSpark eager→DSpark FULL→Eagle eager→Eagle PIECEWISE/FULL；每阶段独立验收。

## M3. unsupported methods 与 MTP 可能被误启用，且设计主动改变了兼容行为

- **风险等级**：Major
- **对应设计章节**：P9、§5.7、§7.1/§7.3
- **为什么可能发生**：
  - 设计把 MRV1 某些方法的“静默未读取”改成 warning+ignore，这不是“保留 MRV1 behavior”，而是单独的用户可见行为变化。
  - MRV2 factory对不支持方法直接 `NotImplementedError`。[`spec_decode/__init__.py:23`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/worker/v2/spec_decode/__init__.py:23) window policy不应先吞掉或改写这个错误。
  - Gemma4/Step等 normalized method仍为 `mtp`，但可能实例化 `AscendEagleSpeculator`；若按 concrete class或“AR family”启用，就会错误 window Target复用层。
- **需要什么源码证据证明安全**：
  - 对 factory所有分支验证 policy执行顺序；MTP必须在任何 class/backend判断前强制 off。
- **建议修改**：
  - 先按 normalized method判定 MTP；unsupported method保持当前 MRV2原始异常。
  - warning策略变化单独评审，不混入本 feature；`draft_model`/ngram/suffix等不可达路径不创建plane。

## M4. “Flashcomm/SP 本身无需处理”的结论过强

- **风险等级**：Major
- **对应设计章节**：§9.1/§9.2
- **为什么可能发生**：
  - Flashcomm开关本身可能不直接重排 block table，但会与SP/DSA-CP组合，改变draft token的rank-local布局、通信和metadata lifetime。
  - 从“不改block table”无法推出“window data plane无需处理”；absolute interval仍需映射到每 rank local query/indices，尤其要处理非整除token与graph padding。
- **需要什么源码证据证明安全**：
  - 明确 window view在SP shard前还是后创建；每 rank最终indices只落在global interval；通信完成与plane refresh之间存在event顺序。
- **建议修改**：
  - 文档改为“Flashcomm control plane近似正交，但 Flashcomm+SP+DSA-CP data plane未验证”。
  - 增加SP-only、SP+DSA-CP、不同TP、padding/非整除token E2E；在证据完成前 capability fail closed。

## M5. policy 与 integration 仍依赖 model-name / first-backend 假设

- **风险等级**：Major
- **对应设计章节**：Candidate A `DraftWindowPolicy`、§5.2、§5.4 capability matrix、§9.5
- **为什么可能发生**：
  - `DraftWindowPolicy(method, target_model_type, ...)` 直接解析 `deepseek_v4*`，与“不要 model-name hardcode”的目标冲突。
  - 当前部分 speculator只用第一个 backend推断一个全局 `attn_architecture`；hybrid group可同时有 GQA/MLA/SFA/DSA，不能按首组选择T1/T2。
  - `draft_kv_cache_group_ids`可能是全局 group集合的稀疏子集；`view.block_tables[i]` 未定义 i是global gid还是dense draft index，存在错位风险。
- **需要什么源码证据证明安全**：
  - 实际 active draft group、每组 backend/causal/native-window/index mode、global gid映射全量枚举。
- **建议修改**：
  - method policy只处理 enable/timing；read-plane能力由每个 group的 builder/backend声明。
  - 使用语义 capability enum替代model字符串；view使用 global-gid keyed mapping，非draft group显式为 identity/None。

## M6. hidden performance regression：materialization 成本随 max context，而不是随 W

- **风险等级**：Major
- **对应设计章节**：§5.4.1、§8.2、T11
- **为什么可能发生**：
  - full-width plane每 step复制window前缀并清 `[needed,row_width)`，复杂度是 `O(num_reqs * Σ full_row_width_g)`，与W无关。
  - SFA随后还会把 common table再次转换到自己的 persistent buffer。[`sfa_v1.py:297`](/Users/wenqingzhang/Desktop/vllm/vllm-ascend/vllm_ascend/attention/sfa_v1.py:297)
  - DFlash live/FULL manager重复build时，若每次都refresh，materialization kernel成本可翻倍；“幂等”不等于“不重复执行”。
  - F3为window ON放弃Target metadata复用，也会新增完整builder开销。
- **需要什么源码证据证明安全**：
  - 真实长context下测materialization kernel bandwidth、proposal p50/p99、throughput、acceptance与KV read下降，覆盖L/W/R/G/mode。
- **建议修改**：
  - plane初始清零后维护每row `prev_needed`，只覆盖新prefix并清 `[new_needed,prev_needed)`，避免每步清整行。
  - 用 `(batch_generation, phase, lane)` 缓存本轮materialization，第二次metadata build只取view。
  - T11必须同时包含 Window OFF baseline与明确可接受回退阈值。

## M7. persistent buffer 显存预算严重低估，且分配时序未闭合

- **风险等级**：Major；长上下文/多group/async lane下可升级为 Critical OOM
- **对应设计章节**：§5.2、§5.4.1、§8.2
- **为什么可能发生**：
  - full-shape table plane的额外显存为 `4 * cap_reqs * Σ row_width_gid * lanes` bytes，不是固定约4MB。
  - 例如 max context约1M、kernel block 16、256 req时，单group约64MiB；4组约256MiB；两lane约512MiB，且尚未包含SFA/DSA已有persistent buffers和graph pool。
  - 每组真实row width还会乘 `blocks_per_kv_block`。[`block_table.py:48`](/Users/wenqingzhang/Desktop/vllm/vllm/vllm/v1/worker/gpu/block_table.py:48)
  - group shape直到 `speculator.set_attn()` 才完整可得；此时KV cache规划可能已经完成，额外大buffer可能未计入available-memory模型。
- **需要什么源码证据证明安全**：
  - 对目标模型的worst-case bytes，包含group、lane、CPU mirror、derived buffers、capture pool；证明纳入内存规划并设OOM阈值。
- **建议修改**：
  - 设计加入正式预算公式、分配位置和拒绝阈值；只为active draft group分配。
  - 优先评估固定窄persistent buffer + capture同址方案。若必须full width，则做增量清理并在超预算时拒绝配置，不能笼统称“可接受”。

# Minor Issues

## m1. `W<=0` 与 `W<future_offset` 的失败模式描述有事实错误

- **风险等级**：Minor（若不校验，运行结果可升级为 Critical）
- **对应设计章节**：§5.2 数学、F13、§7.3、T1
- **问题**：F13写“W=0 时 clamp 后 start=0、静默无效”，与公式不符。实际 `start=floor((L+K)/b)*b`；例如 `L=250,K=0,b=64,W=0` 得 `start=192,windowed_len=58`。负W可能让start超过L；`W<K`也可能产生负 `windowed_len`。
- **建议修改**：method-aware校验至少覆盖 `W>0` 与 AR 的 `W>=future_offset`，并断言 `0<=start<=full_exact`、`windowed_len>=0`、`needed>=0`。若要复刻MRV1未定义行为，必须明确写成兼容决策。

## m2. buffer width 决策在文档内部自相矛盾

- **风险等级**：Minor；实现选错会升级为graph Critical
- **对应设计章节**：Candidate A、§5.2、§5.4.1、§8.2
- **问题**：部分章节写 `[cap_reqs,max_window_blocks_g]`，推荐方案又要求与 full table相同 `row_width_gid`。实现者无法判断首期真实contract。
- **建议修改**：只保留一种明确结构，并对 capture source、builder-owned destination、shape和address分别说明；不要把“source plane同形”和“backend destination同形”混成一句话。

## m3. 现有测试计划会漏掉关键反例

- **风险等级**：Minor
- **对应设计章节**：§10 T3/T6/T8/T11
- **问题**：
  - T6只测每组start/max blocks，不一定检查每层最终length是否按gid匹配。
  - T8没有明确A/B不同window origin交替replay，无法发现one-step lag。
  - T10用acceptance变化推断native SWA交集，不能证明集合正确。
  - T11只查D2H/KV read，没有Window OFF延迟、materialization成本与峰值显存门槛。
- **建议修改**：加入最终layer metadata闭包、集合级indices检查、交替origin replay、OFF before/after性能、长context峰值内存与preemption slot复用测试。

## m4. `frozen view`、`epoch` 与 `max_seq_len_hint` 的语义不完整

- **风险等级**：Minor
- **对应设计章节**：§5.2、§8.3/§8.4
- **问题**：frozen不代表tensor只读；epoch不代表lease/generation；`max_seq_len_hint`未定义来源，若从device `.max().item()`产生会违反P12并引入同步。
- **建议修改**：文档改称“borrowed mutable storage with single writer”；单独定义generation/lease；hint只能从已有host upper或静态容量派生。

# Questions Requiring Source Verification

以下问题不能继续以“Open Question”状态带入实现；每一项都应在设计评审前获得源码trace或最小实验答案。

1. **AR proposal anchor**：Eagle/Eagle3的正确base length究竟取prefill前corrected length、`input_batch.seq_lens`，还是decode preparation后的length？需要K≥3逐step trace。
2. **FULL merged AR device length**：captured attention实际读取哪个tensor作为KV length？若换成plane tensor，谁在图内逐step更新它？
3. **Per-group真实组合**：目标DSpark/Eagle/DFlash配置的active draft groups、global gid、kernel/storage block size、causal与backend分别是什么？
4. **DSA/SFA坐标**：各显式index到底是absolute logical、window-relative还是physical slot；与table列号如何转换？
5. **DCP layout**：absolute interval到rank-local source column/first-page offset/local count的正式映射是什么？窗口起点是否在所有rank上page-aligned？
6. **CPU exact来源**：DFlash/DSpark rejection-corrected CPU exact是否存在无同步producer；MLA与DSpark+GLM最终消费哪个length字段？
7. **CPU upper消费者**：各backend/graph task将`seq_lens_cpu_upper_bound`仅作capacity还是作exact值？
8. **Capture pointer**：GQA/MLA/SFA/DSA分别capture common tensor还是builder-owned copy；每个参数是同址还是通过update task重绑？
9. **Graph update时序**：当前NPU实现中的`graph.update`是给本轮replay还是下一轮；必须用A/B origin交替实验排除one-step lag。
10. **Eagle F3 builder identity**：capture能否从target groups切换到draft groups，并与runtime复用同一builder-owned storage？
11. **Async进入条件**：worker是否可能在上一graph/update-stream reader结束前进入下一propose；真实最大并发深度是多少？
12. **valid_num_blocks来源**：如何按当前`idx_mapping`、per gid在device侧获得batch-order valid counts且不新增D2H？
13. **PCP最后gather点**：replicated PCP + FULL下draft最终消费global还是local table，view应在哪次re-gather后创建？
14. **Native physical retention**：使用`SlidingWindowSpec`的group是否已释放旧块；最终可见集合的物理上限是什么？
15. **Flashcomm/SP/DSA-CP**：window interval在SP shard前后哪个坐标系，rank-local cache/metadata何时失效和重建？
16. **Unsupported policy顺序**：MTP/Gemma4/Step3.5/DFlash2/310P及不可实例化methods的正式warning/error行为是什么？
17. **内存规划**：plane、lane、CPU mirrors、SFA/DSA已有buffer与graph pool总量如何计入KV cache memory planning？
18. **配置边界**：`W<=0`、`W<K`、W小于native window分别是拒绝、warning还是复刻MRV1未定义行为？

# Recommended Design Changes

以下是使原设计达到“可实现、可证明”所需的最小设计级修改，不是生产代码方案。

## 1. 将单一 view 改为 per-global-gid 的完整 bundle

建议的设计契约应表达为：

```text
DraftWindowView
  generation / proposal_id / request_order_generation
  descriptor / actual_num_reqs / padded_num_reqs
  lane_id / retire_event
  groups[global_gid] -> DraftWindowGroupView
      table
      device_exact_len
      cpu_exact_len?        # 可缺失，不伪造
      cpu_upper_bound
      dcp/cp local state
      absolute_interval
      table_origin / first_page_offset
      valid_num_blocks
```

所有length、interval和layout信息均须per-group；漏斗在group循环内部取对应bundle。非draft group显式identity/None，不使用dense draft index猜global gid。

## 2. 把“表+长度”提升为带坐标与layout能力的read-plane contract

- T1仅适用于已证明可用相对 table+length表达的backend。
- T2保留full absolute state生成/过滤indices，或显式携带origin并统一转成relative；禁止两种坐标混用。
- DCP/DSA-CP/SFA-DCP通过`WindowPartitioner`处理rank-local column、first-page offset与local count；证据不足时fail closed。

## 3. 建立真正的 length type system

- 明确区分device exact、CPU exact optional、CPU upper、graph capacity与backend-derived max。
- upper不能独立套rounded window函数；必须保持数学上的上界。
- 不存在CPU exact时，不得用uniform `max_seq_len`冒充；按backend capability选择device-derived路径、异步host mirror或拒绝组合。

## 4. 取消window对模块级 factory monkeypatch的依赖

- window view通过实例方法和真实函数参数传递。
- graph manager、capture builder与replay builder显式接收view/lane。
- F3定义为draft-only metadata API，覆盖eager/PIECEWISE/FULL，并禁止复用Target metadata/storage。

## 5. graph strategy 改成 backend capability matrix

对每个backend分别回答：capture绑定哪块storage、runtime是否可rebind pointer、derived metadata由谁刷新、update为当前还是下一replay。

- no-op backend：capture即绑定plane或builder-owned唯一persistent storage。
- updatable backend：只有正式注册的参数才可换pointer。
- 每个descriptor必须有shape/address/actual-count契约；W1不能继续作为全backend统一答案。

## 6. 从第一版定义 async lane 与 retirement

- lane数依据`max_concurrent_batches`或已证明的更小并发上界，不以“实测后再双缓冲”为正确性策略。
- device/host buffer均跟随lane；refresh前等待retire event，consumer提交后记录read event。
- generation不仅是数字，还必须绑定proposal、request order、descriptor、group与lane。

## 7. materializer 必须消费真实 valid block count

- 按`idx_mapping`和gid gather `num_blocks`。
- source load同时mask row width与per-row valid count。
- active tail、padded rows、interval、exact/upper/local lengths、T2 indices都按actual/padded语义清理。
- 增加preemption、slot复用、block立即重分配的安全测试。

## 8. method timing 分开定义

- Eagle/Eagle3：proposal-level fixed anchor；每step只推进visible length。FULL merged graph必须有per-step device window length更新。
- DFlash/DSpark：所有per-group full-table physical slot准备结束后，offset 0，再创建read view。
- MTP：normalized method优先判定，warn+ignore；不能因继承Eagle class而启用。
- unsupported/DFlash2/310P：保持当前行为或明确fail closed，不由公共policy静默扩张。

## 9. 重写 native SWA 与并行组合的声明

- 不再写“天然取交集”或“Flashcomm无需处理”。
- 用`method × group backend × visibility mode × native KV spec × parallel layout × graph mode`矩阵声明已证明组合。
- 正确性验收比较最终可见绝对KV集合；acceptance只作为质量指标。

## 10. 给 full-width plane 加硬预算与性能门禁

- 写出内存公式并乘group、lane、builder已有buffer与graph pool。
- 规定分配阶段、计入memory planning的方法和拒绝阈值。
- 优先增量写/清而非每step全宽清零；评估固定窄persistent capture方案。
- Window OFF需有语义、延迟、吞吐和显存基线；Window ON需有长context break-even与峰值内存门槛。

## 建议的重新评审门槛

原设计至少完成下列证据后，才建议从“Request Changes”转为“Approved for implementation”：

1. per-group length/view contract闭合，异block size反例通过；
2. DSA/SFA/DCP坐标与最终indices集合验证通过；
3. CPU exact/upper语义逐backend闭合；
4. capture/replay pointer与builder identity矩阵闭合；
5. AR fixed anchor及FULL graph逐step length更新闭合；
6. explicit plumbing替代window相关global monkeypatch；
7. async lane/event、dynamic batch、preemption、graph bucket压力测试通过；
8. Window OFF基线与full-width显存/性能预算通过。

在这些门槛完成之前，最安全的首期范围不是“公共架构全method接入”，而是**只允许经过明确 capability gate 的单method、单backend、eager、非DCP组合进行实验性验证；其余组合必须fail closed**。
