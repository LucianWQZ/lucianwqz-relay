# MRV2 Draft Window P2：Inventory + FullSource + Valid Counts + Provider 实现说明

## 文档状态

- 权威设计：`MRV2_Speculative_Draft_Sliding_Window_Final_Design.md`
- 实施计划：`MRV2_Draft_Window_Implementation_Plan.md`
- vLLM 固定基线：`84030bbe3d74d99bad477a3d2e37a973ccd8865c`
- vLLM-Ascend P2 父提交：`c58daea0df34d1a6253dc34221d2a084b13affd5`
- P2/C2 提交：`83579675a997a44b293ff0ee1cb088a2eef0ed13`
- Commit title：`feat(spec-decode): add MRV2 draft-window source inventory`
- P2 review-fix 提交：`fac84121ddf84fe5a76cd739432cea3b61365a9b`
- Review-fix title：`fix(spec-decode): address P2 draft-window review findings`
- 文档最终核对时间：`2026-10-10T10:21:31+08:00`（Asia/Shanghai）
- 当前结论：`P2 FINAL: PASS`；P3 尚未开始，`P3 READY TO START`。

这份说明只解释 P2。P2 的“provider”是只读投影描述器，不是已经交给 Attention 的
Window table。文中所有测试结论均为 CPU/static contract；没有把它们升级成 NPU、Graph、
Async 或真实 Window ON correctness。

## 1. P2 解决什么问题

### 1.1 为什么 P1 算出 S/E 仍然不够

P1 已经能从完整上下文计算绝对窗口：

```text
E = 当前 exact full end
H = E + method future offset K
S = B * floor(max(H - W, 0) / B)
V = E - S
```

这些变量回答“语义上应该看哪一段 token”，却没有回答“这一段在当前真实 Draft
Attention 的哪张 block table、哪一列、哪种 block 粒度中”。MRV2 可以有多个 global KV
cache group；同一 group 内也可能因 backend 或 head 配置拆出多个 executable
`AttentionGroup`。MLA、DSA、SFA、native/recycling layout 也不能套用 dense GQA 的列公式。

因此 P2 必须先观察当前 `set_attn()` 真正构造出的 consumer，而不是根据 model name、
Target backend 或 speculator class 猜测。

### 1.2 什么是 runtime inventory

Inventory 是对当前 Draft read consumers 的不可变快照。它逐个记录：

- global cache-group id；
- group 内 local consumer index；
- layer names；
- 实际 backend class 与 builder class；
- logical/kernel block size 与已证明的 table span；
- causal/non-causal；
- layout category；
- 不能成为当前 provider candidate 的具体原因。

它的作用不是“看到某 backend 就自动 enable”，而是给后续阶段一个可审查、可失败、不会
silent fallback 的 capability boundary。

### 1.3 什么是 canonical full source

Canonical full source 是现有 `BlockTables` owner 中已经服务于 baseline MRV2 的完整状态：

- `input_block_tables[gid]`：为本轮 forward 准备的 gathered-full table buffer；
- `num_blocks.gpu[gid]`：每个 persistent request slot 的真实有效 block 数；
- logical/kernel block geometry；
- 与本轮 gather 完全相同的 `idx_mapping`。

P2 只借用这些对象的引用，不复制、裁剪、替换或原地修改它们。

### 1.4 什么是 valid block count

block-table row 的物理宽度是容量，不是当前 request 实际拥有的 block 数。旧请求留下的
tail 可能仍含非零 id；物理 block id `0` 本身也可能合法。因此不能扫描 table 内容猜
valid count。唯一权威值是 `BlockTables.num_blocks.gpu`，再通过当前 batch 的同一个
`idx_mapping` 从 request-slot order gather 成 batch-row order。

### 1.5 什么是 provider

P2 provider 接收 P1 scalar plan、single dense group inventory、FullSource geometry 和该
batch row 的 valid count，输出“以后应该从 full row 的哪几列读”的 descriptor。它还证明：

```text
source_start_column + required_columns <= valid_num_blocks
```

P2 到这里停止。它没有创建窄 table，也没有把 descriptor 交给 metadata builder 或
Attention operator。

## 2. P2 不解决什么

P2 明确没有做以下事情：

- 真实 Draft Attention 仍读取 baseline full metadata/table；
- 没有 Window tensor backing、crop/clone table 或 persistent narrow view；
- 没有 workspace、lease、generation pool、device lane 或 event retirement；
- 没有 `DraftMetadataInputs`、`DraftWindowWorkspace`、`DraftMetadataStore`；
- 没有修改 `seq_lens`、CPU lengths、positions、query layout 或 causality；
- 没有修改、替换或重新计算 `slot_mapping`；
- 没有修改 Target metadata、Target store、Target logits 或 acceptance；
- 没有接入 Attention builder/backend；
- 没有 upstream vLLM hook；
- 没有 ACL Graph capture/replay/update 接线；
- 没有启用 DFlash2、MLA、DSA、V4.1、SFA、recycling、multi-group、Async 或 parallel；
- 没有运行 NPU Window ON、Graph A/B/A、prefix-cache、function/chunked prefill或性能测试；
- 没有进入 P3 或 P4。

P2 对配置了 Window 的 unsupported route 会在 `set_attn()` capability build 中明确报错；
这不是 Attention 已经使用 Window，而是按设计在进入 forward 前 fail closed。

## 3. 修改文件总览

| File | Class / function | Before | After | Why |
|---|---|---|---|---|
| `vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window.py` | `DraftWindowLayoutCategory`、runtime/inventory/source/descriptor dataclasses；inventory/source/gather/provider builders | 只有 P1 policy/math/types | 新增 P2 只读 source plane contracts | 将实际 backend/group/layout 与 P1 绝对窗口关联起来 |
| 同上 | `FullDraftKVSource.bind_batch()` | 不存在 | 返回绑定 exact mapping 引用的新 frozen view | DFlash/DSpark 不能安全复用 `self.idx_mapping` 假设 |
| 同上 | `gather_valid_num_blocks()` | 不存在 | `index_select(..., out=...)` gather；padding 清零；alias/owner 检查 | 建立 request-slot → batch-row 的权威 valid counts |
| 同上 | `SingleGroupDirectPrefixProvider.describe()` | 不存在 | 只返回 `DraftWindowReadDescriptor` | 证明 projection/capacity/source coverage，不物化 Window |
| `vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py` | `_initialize_draft_window_source_capability()`；`set_attn()` 尾部调用 | eligible owner 只保存 P1 policy | actual groups 建立后附加 P2 capability | Eagle3 增量接线，不改原 set-attn 主流程 |
| `vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py` | 同名 helper；`set_attn()` 尾部调用 | 同上 | 使用 actual `_speculator_name` 与 `_group_causal` | 区分 DFlash 与继承它的 DFlash2 |
| `vllm-ascend/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py` | 同名 helper；`set_attn()` 尾部调用 | 同上 | 使用实际 DSpark attention groups/builders | 不从 Target SFA/DSA 或 model name 推断 Draft layout |
| `vllm-ascend/tests/ut/spec_decode/test_draft_window.py` | C2 原始 29 个 P2 test functions / 48 cases；review 后 33 functions / 53 cases | P1 的 34 functions / 75 cases | 最终总计 67 functions / 128 cases | inventory/source/reorder/padding/T10/provider/gate regression |
| `vllm-ascend/tests/ut/spec_decode/test_dflash2_v2.py` | MRO contract | 只确认 P1 receiver 继承 | 同时确认 P2 initializer 继承 | 继承入口不等于 runtime support |

本提交没有修改 `/Users/wenqingzhang/Desktop/vllm/vllm`，也没有修改 production
`BlockTables`、attention metadata builder 或 backend。

## 4. 修改前数据流

### 4.1 两种排列

```text
Persistent request slots

BlockTables.block_tables[gid].gpu
BlockTables.num_blocks.gpu[gid]
              |
              | current input_batch.idx_mapping
              v
BlockTables.gather_block_tables(...)
              |
              v
BlockTables.input_block_tables[gid]
    current batch-row order; padded rows cleared
              |
              v
baseline metadata builder -> Draft Attention full read
```

关键区别：

- `input_block_tables[gid][batch_row]` 已经是当前 batch row 顺序；
- `num_blocks.gpu[gid][request_slot]` 仍是 persistent request slot 顺序。

若直接用 `num_blocks.gpu[gid][:num_reqs]`，request reorder、remove/add 后就会把 A 的 count
配给 B，或读取已离开 batch 的 stale slot。

### 4.2 write slot 是另一条路径

```text
persistent BlockTables.block_tables pointers
  + exact idx_mapping
  + absolute positions/query_start_loc
              |
              v
BlockTables.compute_slot_mappings()
              |
              v
full/global physical write slots
```

slot kernel 读取的是 canonical persistent table pointers，不是 P2 将来要描述的 narrow
read projection。P2 前后这条路径完全不变。

## 5. 修改后 P2 数据流

```text
P1 policy decision
        |
        +-- CONFIG_OFF / FORCED_OFF --------------------> baseline; no P2 object
        |
        `-- ELIGIBLE_ON
                |
                v
existing speculator.set_attn()
build actual attn_groups/builders first
                |
                v
DraftWindowInventory + runtime/topology gates
                |
                +-- unsupported ------------------------> explicit diagnostic
                |
                `-- one dense direct-prefix candidate
                        |
                        v
              static FullDraftKVSource
       (borrow existing full buffers/count owner)
                        |
          future proposal binds exact idx_mapping
                        |
                        v
              gather valid counts by batch row
                        |
                        v
P1 plan + valid count -> read-only DraftWindowReadDescriptor
                        |
                       STOP

No Window table
No metadata replacement
No Attention binding
```

`DraftWindowSourceCapability` 只是把 inventory、static FullSource 和 provider 放在 eligible
speculator 实例上。它不在 proposal/forward 中被消费，因此真实 attention visibility 仍是
full。

## 6. Inventory 详解

### 6.1 一个具体例子

测试构造两个 global cache groups：gid 0 没有 active Draft layer，gid 1 有两个共享同一
backend/spec/head 配置的 layer。upstream `init_attn_backend()` 会把这两个 layer 合并成
gid 1 内的一个 `AttentionGroup`：

| Field | Example value | Meaning |
|---|---|---|
| `global_group_id` | `1` | 用它索引 BlockTables、block sizes 与 persistent counts |
| `local_consumer_index` | `0` | 只是 `attn_groups[1]` 内的位置，不能索引 BlockTables |
| `layer_names` | layer 4、layer 5 self-attn | 该 builder/backend 服务的真实 Draft layers |
| `backend_class` | `AscendAttentionBackend` | 从 runtime `AttentionGroup.backend` 读取 |
| `builder_class` | `AscendAttentionMetadataBuilder` | 从已创建的 metadata builder 实例读取 |
| logical block size | `64` | KV manager/cache spec 的 block 粒度 |
| kernel block size | `64` | `BlockTables` 声明并用于 table expansion/slot kernel 的列粒度 |
| `block_span_tokens` | `64` | P2 direct-prefix 投影采用的静态 span；FIA operator 实际 read-set 仍须 P4 NPU oracle |
| `causal` | `False` | 来自 speculator 实际 group causal contract |
| layout | `DENSE_GQA_DIRECT_PREFIX` | 当前唯一 P2 provider candidate layout |

Inventory 同时记录 `empty_global_group_ids=(0,)`，但 provider 使用 gid 1，不会把“第一个
non-empty local element”误当 gid 0。

### 6.2 为什么不能根据 model name 猜

同一 target family 可以选择不同 Draft checkpoint/backend；Target SFA 不代表 Draft 也是
SFA，DSpark class 也不代表每个 layer 都使用某一固定 backend。当前源码会按真实 layer、
KV spec、backend 和 per-rank query heads 拆 group。只有 `set_attn()` 完成后的
`AttentionGroup` 与 builder 才是权威证据。

### 6.3 layout 分类与失败

当前分类顺序先识别 DSA、MLA、SFA，再识别 native/recycling spec，最后才允许 exact
`FullAttentionSpec` + Ascend dense builder 成为 dense direct-prefix。unknown/mixed/empty
均带诊断；多 gid 与同 gid 多 executable consumers 都拒绝。分类可见不等于支持：MLA、
DSA、SFA 只是被准确标注，provider 不会为它们构造。

## 7. FullSource 详解

### 7.1 谁创建、谁拥有

`build_draft_window_source_capability()` 在 eligible speculator 的 `set_attn()` 尾部调用
`build_full_draft_kv_source()`。真正的 Tensor owner 仍是原 `BlockTables`；FullSource 只保存
borrowed references。

### 7.2 字段与含义

| Field | Ownership / meaning |
|---|---|
| `logical_block_sizes` | immutable Python tuple；从 owner geometry 读取 |
| `kernel_block_sizes` | immutable Python tuple；用于 table span proof |
| `source_identity.block_tables_owner_id` | owner Python identity；不是 generation id |
| `source_identity.input_block_table_ptrs` | 绑定时 full gathered buffers 的 data pointers |
| `source_identity.persistent_num_blocks_ptr` | persistent count tensor pointer |
| `source_identity.idx_mapping_ptr` | static source 为 `None`；batch-bound view 为 exact mapping pointer；只证明 allocation identity，不证明内容 freshness |
| `_block_tables_owner` | private borrowed owner，用于检测 tensor replacement |
| `_input_block_tables` | private borrowed full buffers；没有 public writable accessor |
| `_persistent_num_blocks` | private borrowed request-slot counts |
| `_idx_mapping` | private optional exact batch mapping reference |

### 7.3 引用还是 copy

table、count 与 mapping 都不 copy。`bind_batch(mapping)` 创建的是新的 frozen Python value，
内部继续引用同一 tables/counts，并引用传入的**同一个 mapping Tensor**。API 名称
`references_same_idx_mapping_tensor()` 刻意只承诺对象 identity；测试还固定了“原地改写后
identity 仍为真、gather 读取新内容”的现状，避免把 pointer 错当 freshness guard。

### 7.4 为什么 mapping 不能在 set_attn 时固定

`set_attn()` 发生在具体 request batch 之前。更重要的是，AR 会把 mapping copy 到
`self.idx_mapping`，而 DFlash/DSpark prepare kernel 直接读取
`input_batch.idx_mapping`。因此不存在一个在所有 method 上都可于 `set_attn()` 读取的统一
current-batch member。P2 把 batch binding 明确留给 proposal scoped caller，避免猜测或
拿上一轮 mapping。

### 7.5 生命周期与只读防线

P2 source 的静态引用跟随 speculator/BlockTables owner 生命周期。它在使用前验证 owner
仍指向同一 tables/count tensor；若 owner 替换对象则硬错误。valid-count output 也不得与
table/count/mapping 的底层 storage alias，否则 `zero_()` 可能破坏 source。

P2 没有 generation id、lane 或 retirement event。mapping buffer 可在原地址原地改写，
所以 batch-bound source 只对调用者定义的**单个当前 batch/proposal scope**有效，禁止跨
proposal 缓存。P3 必须在任何缓存或异步消费前加入 caller-owned monotonic mapping epoch，
并把它纳入 generation identity；在此之前不能把 P2 对象解释成 Async/Graph-safe lifetime。

### 7.6 后续谁消费

- P3 将基于 FullSource/provider 建立 generation-scoped workspace、typed transport 和
  lifetime ownership；
- P4 才会在 gated eager route 中绑定 exact current mapping、gather counts、materialize
  caller-owned Window backing 并交给 Draft metadata；
- Target、slot mapping 与 canonical owner不会改由 FullSource 管理。

## 8. Valid Counts 完整例子

### 8.1 Persistent rows

假设 persistent request slots 中：

```text
request slot 17 = request A, num_blocks = 3
request slot 93 = request B, num_blocks = 8
request slot  4 = request C, num_blocks = 5
```

当前 batch 只包含 `[B, A]`，且顺序与 persistent slot 完全不同：

```text
batch row 0 -> request slot 93 (B)
batch row 1 -> request slot 17 (A)

idx_mapping = [93, 17]
```

P2 gather 必须做：

```text
num_blocks.gpu[gid] = persistent request-slot order
index_select(indices=[93, 17])
                         |
                         v
batch-row valid counts = [8, 3]
```

若 padded request count 是 4，结果必须是：

```text
[8, 3, 0, 0]
```

padding tail 每次确定性清零，不能保留上一个大 batch 的 count。

### 8.2 Reorder、subset 与 stale tail

下一轮 batch 若变成 `[C, B]`，mapping 变成 `[4, 93]`，同一个 batch-bound mapping reference
被更新后 gather 得到 `[5, 8]`。不会沿用旧 `[8, 3]`，也不会把已移除 A 的 tail 当 active
source。

### 8.3 为什么不能数非零 table 元素

以下 row 的 valid count 是 2：

```text
block ids = [0, 9, 0, 0, ...]
valid_num_blocks = 2
```

第一个 `0` 可以是合法物理 block id；第三、第四列虽也是 `0`，却是 invalid tail。数
nonzero 会错误得到 1，寻找最后 nonzero 又会把合法 0 与 padding 混淆。只有 persistent
`num_blocks` 能表达边界。

## 9. Provider 数学实例

Provider 除了 plan 本身，还保存从真实 `vllm_config.speculative_config` 解析出的
`expected_future_offset`。Eagle3 使用 configured static K；DFlash/DSpark 固定为 0。
因此它会先比较 `H-E` 与独立配置来源，不能再用 plan 内的 offset 自证正确。

统一示例使用：

```text
W = 128
legacy B = 64
window capacity tokens = W + B - 1 = 191
block span = 64
```

### 9.1 正常 non-boundary case

DFlash/DSpark 的 future offset 为 0。取：

```text
E = H = 257
S = 64 * floor((257 - 128) / 64) = 128
V = 257 - 128 = 129

start_col = floor(128 / 64) = 2
offset = 128 mod 64 = 0
required_columns = ceil((0 + 129) / 64) = 3
source_end = 2 + 3 = 5
```

若 valid count 为 6，`5 <= 6`，descriptor 合法。

### 9.2 Equality boundary

沿用上例，valid count 恰为 5：

```text
source_end = valid_num_blocks = 5
```

最后一列刚好存在，允许读取。测试还覆盖 Eagle3 风格的 `E=192, K=64, H=256,
S=128, V=64`，其 `start_col=2, needed=1, end=3, valid=3`。

### 9.3 Source shortage

仍用 `start_col=2, required=3`，若 valid count 为 4：

```text
2 + 3 = 5 > 4
```

provider 抛出 `draft-window source shortage`。它不会把第五列补 0、缩短 visible length、
向左扩大历史或读 null block。

### 9.4 Padding row

padding row 的 gathered valid count 是 0，且后续 P3/P4 不应为它创建 active descriptor。
即使误把有 `required_columns>0` 的 active plan 用到 padding，coverage 也会因
`source_end > 0` 硬失败，不能把 padding 伪装成有上下文。

### 9.5 Proven smaller span

若 logical block size 为 64、kernel/table span 为 32，`32` 整除 legacy `B=64`，所有
legacy-aligned S 都同时 span-aligned。例：`E=129, K=64, H=193, S=64, V=65`：

```text
start_col = 64 / 32 = 2
offset = 0
required_columns = ceil(65 / 32) = 3
```

该 geometry 在 P2 可证明，允许 descriptor。

### 9.6 Forbidden geometry 与禁止 per-group realign

若 `B=64, span=48`，则 `48` 不整除 `64`。canonical S 可能是 64，此时：

```text
offset = 64 mod 48 = 16
```

当前 dense direct-prefix consumer 尚无 nonzero-offset operator contract，所以 provider
构造即拒绝。它不会把 S 改成 48 或 96；多 group 共享的绝对 canonical anchor 不得按
group 重对齐。

provider 还会从 `E/H/W/B` 重新计算 P1 anchor，拒绝一个虽然对 span 对齐、却不是
canonical P1 S 的手工 plan。例如 `E=H=96, W=128, B=64` 的正确 S 是 0；伪造
`S=32` 即使对 `span=32` 的 offset 为 0，也仍被拒绝。

## 10. Global gid / local index

当前 upstream 数据结构是：

```text
attn_groups[global_kv_cache_group_id][local_attention_group_index]
```

- 外层 index 对应 `kv_cache_config.kv_cache_groups`、`BlockTables`、logical/kernel sizes、
  `input_block_tables` 与 `num_blocks` 的 global gid；
- 内层 index 是同一 global gid 内因 backend/spec/head 差异拆出的 consumer；
- `AttentionGroup.kv_cache_group_id` 应与外层 gid 一致，P2 会显式核对；
- DFlash 的 `draft_kv_cache_group_ids` 是 non-empty global gid 列表；
- DFlash 的 `_layer_group_idx` 则是 layer 到上述列表位置的 local mapping，不能拿来索引
  canonical BlockTables。

最容易出现的错误是遍历过滤后的 non-empty groups 后用 `enumerate()` 结果索引 BlockTables。
例如 gid 0 empty、gid 1 active 时，本地第 0 个 active consumer 仍属于 global gid 1。P2
保存两者，provider 只用 global gid 访问 source。

第一版要求 exactly one executable `AttentionGroup`。一个 global gid 内有两个 consumer
也拒绝；“same gid”不代表它们的 backend/metadata operand 可以共用一个未经证明的
Window view。

## 11. Slot Mapping 为什么完全不受 P2 影响

真实源码中两条分支的 owner 不同：

```text
WRITE branch
-----------
BlockTables.block_tables[*].gpu (persistent full tables)
 + exact idx_mapping + absolute positions
        -> compute_slot_mappings()
        -> full/global physical write addresses

READ-understanding branch added by P2
------------------------------------
BlockTables.input_block_tables[*] (gathered full read buffers)
 + persistent num_blocks + exact idx_mapping
        -> FullSource / valid counts
        -> descriptor only
        -> STOP
```

P2 没有调用、patch 或替换 `compute_slot_mappings()`，也没有写
`BlockTables.slot_mappings`。测试保存 slot buffer 前后内容，并以 spy 证明 P2 source/provider
操作没有触发 slot kernel。

未来 P4 即使 materialize Draft read Window，也必须继续让 write branch 使用 canonical full
table。read visibility 与 physical write address 是两个不同契约。

## 12. Method 差异

### 12.1 Eagle3

- P1 只允许 normalized `eagle3`，plain Eagle/dynamic-K 已 fail closed；
- Ascend AR 在既有 `set_attn()` 建立 actual groups、选择 graph update backend 后调用 P2
  initializer；
- inventory causal 目前为 AR 的 `True` contract；
- provider 从 `num_speculative_tokens` 独立保存 configured static K，并拒绝 `H-E` 与 K
  不一致的 plan；P2 不在 proposal 中绑定 mapping，也不处理 first-pass Target metadata
  reuse、多 step refresh 或 rejection；这些属于 P4b；
- Graph 仍拒绝。

### 12.2 DFlash

- runtime route 从实际 `_speculator_name.lower()` 取得，不只看 P1 method；
- causal 来自 `_group_causal`，可以是 bool 或 per-global-gid mapping；
- capability 在 baseline `set_attn()`、context slot buffers 与 actual backend enumeration
  完成后建立；
- P2 不介入 `prepare_dflash_inputs()`、context KV write、slot mapping 或 metadata build；
- future offset 仍为 0。

### 12.3 DSpark

- DeepSeek-V4 co-trained DSpark 在 P1 已 forced OFF，绝不进入 P2；
- eligible non-DeepSeek route 使用真实 DSpark groups/builders 与 `_group_causal`；
- Target 是 SFA/DSA 不会被拿来推断 Draft backend；
- `sample_from_anchor`、actual query width、context KV 和 derived backend state都未在 P2
  改动；真正 read-plane 接线属于 P4/扩展 Gate。

### 12.4 DFlash2

- factory 的 policy method 仍是 `dflash`，但 actual instance route 是 `dflash2`；
- DFlash2 继承 DFlash 的 policy receiver 与 P2 initializer；
- inventory 会记录 actual group/backend/layout，并明确加入
  `DFlash2 runtime Window remains gated`；
- capability build 随后抛出 `NotImplementedError`，不会附加可运行 P2 capability，更不会
  enable Attention；
- Window OFF 的 DFlash2 baseline 和既有 eager-only约束不变。

## 13. Unsupported / Gate

以下组合在 P2 结束时仍 fail closed：

- MTP：P1 warning once + forced OFF；
- DeepSeek-V4 family co-trained DSpark：P1 warning once + forced OFF；
- plain Eagle 与 unknown method；
- dynamic-K；
- DFlash2 runtime Window；
- zero/negative W 与 P1 interim `W<K`；
- zero executable consumer；
- 同 global gid 多 executable consumers；
- homogeneous multi-global-group 与 heterogeneous multi-group；
- backend/builder unknown 或不匹配；
- MLA；
- DSA，包括 V4/V4.1 的 derived paths；
- SFA 与 indexer；
- native sliding/chunked/local/circular/RSWA/recycling layout；
- non-prefix-resident `FullAttentionSpec`；
- nonzero first-token offset；
- `span ∤ legacy B` 的非默认 geometry；
- inventory/source gid 或 logical/kernel geometry 不一致；
- Graph：FULL、FULL_DECODE_ONLY、PIECEWISE 以及其他非-NONE draft mode；
- async scheduling；
- TP>1、DP>1、PP>1、PCP>1、DCP>1；
- sequence parallel、DSA-CP、FlashComm；FlashComm 同时读取经过 bool validation 的
  `additional_config.enable_flashcomm1` 与 `VLLM_ASCEND_ENABLE_FLASHCOMM1` 环境入口；
- source shortage、valid count 大于 row width、stale/replaced owner；
- batch mapping 未绑定或 mapping/count 位于不同 device；
- valid-count output alias canonical source/mapping storage。

仍未关闭的后续核心 Gate：G-LIVE-HOOK、G-GQA-EAGER、G-AR-STEP、G-GRAPH、G-ASYNC、
G-PARALLEL、G-MLA、G-DSA1、G-V41、G-RECYCLING、G-DFLASH2，以及 owner Required
Delivery manifest O-01。

Prefix cache、function/chunked prefill 在 OFF 时没有新代码路径；Window ON 必须在后续
Attention integration 中获得独立测试，不能由 P2 的“只读 source 可表达”推断为支持。

## 14. Tests

### 14.1 Test-first 证据

以下是本开发会话的**历史 test-first 记录**，不是从 final tree 单独运行即可重建的状态：
P2 imports/types 尚不存在时，新增 tests 首次 collection 以 missing P2 symbols 失败；C2
差异审计随后先增加 7 个 regression cases，并在当时旧实现上暴露：

- policy/runtime route 错配未拒绝；
- inventory 与 FullSource geometry 可错配；
- output 可 alias persistent counts、input table 或 idx mapping；
- provider 可接受非 canonical P1 plan；
- owner table 替换后 descriptor 仍可生成。

修复 production 后这 7 个 regression 全部通过。P2 review 又先增加/改造 7 个 selected
cases；在原 C2 production 上结果为 `5 failed, 2 passed`。其中四个行为失败分别证明
FlashComm env bypass、Eagle3 K 自证、mapping API 误导与异常类型差异；另一个失败是 real
AscendBlockTables 测试在无完整 Triton host 上缺 `next_power_of_2`，测试用 CPU shim 修正，
未改 production。int64 与 real-class contract 属覆盖补强，旧 production 本应通过。最终
同一 selected set 为 `7 passed`。

### 14.2 Inventory tests

| Test family | Protects | Failure means |
|---|---|---|
| global gid + actual classes + empty gid | outer gid、layers/backend/builder/geometry/causal事实 | local index 被误当 global gid，或在猜 backend |
| mixed consumers / same gid | exactly-one consumer Gate | 未证明的 builder operands可能被共用 |
| homogeneous multi-group | multi-group仍关闭 | P2 被误当成 per-group runtime materializer |
| MLA/DSA/SFA/native/unknown | exhaustive classification + fail closed | unsupported layout可能错误进入 dense provider |
| DFlash2 actual route | eligibility与enablement分离 | 继承 DFlash 被误认为 supported |
| graph/async/topology matrix | runtime Gate逐项生效 | 未验证 mode可能静默打开 |
| route mismatch | method/instance identity一致 | 错 owner wiring可能被接受 |

### 14.3 FullSource / valid-count tests

| Test family | Protects | Failure means |
|---|---|---|
| canonical reference identity | 不 copy、不替换 source | P2 可能创建 shadow state或写 owner |
| real `AscendBlockTables` contract | production owner 保持 P2 所需字段 | upstream/Ascend owner 字段漂移而 SimpleNamespace 测试不知情 |
| owner replacement | stale binding hard error | descriptor/count可能引用旧 generation object |
| exact mapping bind | 引用同一 mapping，无 copy/guess；identity 不冒充 freshness | reorder 后可能与 gathered table不一致，或 P3 错把 pointer 当 epoch |
| source geometry mismatch | inventory/source一致 | span/column数学建立在错误 gid/size 上 |
| reorder/subset/stale tail，int32/int64 | production dtype 与兼容 dtype 都保持 request-slot → batch-row正确 | count 会错配 request或只在 synthetic dtype 下工作 |
| padding clear | 每轮 deterministic zero | 小 batch 继承旧 active tail |
| physical block id 0 | 不扫描 table 猜 count | 合法 block 0 被当 sentinel |
| output alias matrix | FullSource只读 | gather 的 `zero_()` 可破坏 table/count/mapping |

### 14.4 Provider / T10 tests

| Test family | Protects | Failure means |
|---|---|---|
| exact equality boundary | `source_end == valid` 可用 | off-by-one 拒绝合法最后一列 |
| non-boundary visible length | ceil column math | 少列或多列 |
| smaller proven span | `span ∣ B` geometry | 过度限制正确 direct-prefix layout |
| forbidden geometry | nonzero offset不偷开 | provider 可能读错首 block token |
| noncanonical plan | 不按 group 偷换 S | P1 Frozen anchor被绕过 |
| configured Eagle3 K mismatch | `H-E` 必须等于独立 configured static K | plan 用自身 offset 自证，错误 proposal horizon 可进入 P4 |
| shortage and stale tail | T10 source coverage | padding/stale id被当有效 source |
| owner replacement before describe | descriptor与当前 owner一致 | 描述的是已失效 buffer |

### 14.5 实际命令和结果

```bash
env VLLM_VERSION=0.29.0 \
  PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm:/Users/wenqingzhang/Desktop/vllm/vllm-ascend \
  .venv/bin/python -m pytest -q \
  tests/ut/spec_decode/test_draft_window.py \
  tests/ut/spec_decode/test_dflash2_v2.py
```

结果：`134 passed, 1 warning`。warning 是本地 editable vLLM 缺 `_version`，与 P2 无关。

```bash
env VLLM_VERSION=0.29.0 PYTHONPATH=... \
  .venv/bin/python -m pytest -q tests/ut/spec_decode \
  --ignore=tests/ut/spec_decode/test_speculators_vwn_eagle3.py
```

结果：`360 passed, 13 skipped, 2 subtests passed, 1 warning`。

```bash
env VLLM_VERSION=0.29.0 PYTHONPATH=... \
  .venv/bin/python -m pytest -q \
  tests/ut/worker/v2/test_v2_block_table.py \
  tests/ut/worker/test_attn_utils_v2.py \
  tests/ut/worker/test_extract_hidden_states_speculator_v2.py
```

结果：`52 passed, 1 warning`。

完整 `tests/ut/spec_decode` 结果为
`362 passed, 13 skipped, 7 failed, 2 subtests passed`。7 个失败全部在
`test_speculators_vwn_eagle3.py`，共同报 upstream selector
`ValueError: Invalid attention backend for None`；本次又在 P1-final
`c58daea0df34d1a6253dc34221d2a084b13affd5` detached worktree 对同一文件复现完全相同的
`7 failed, 2 passed` stack。本次调用链也未进入 P2 文件，所以这是
本机无 Ascend platform/backend 的环境限制，不记录为 PASS，也不当作 P2 regression。

### 14.6 Lint / type / static

- changed files Ruff check：PASS；
- changed files Ruff format check：PASS；
- `draft_window.py` targeted Mypy（`--follow-imports skip --check-untyped-defs`）：PASS；
- 三个 owner files targeted Mypy：DFlash/DSpark 无新 error；AR 仍有 4 个父基线已有的
  `issubclass(type[Any] | None)` errors，P2 新增行没有 error；
- compileall：PASS；
- `git diff --check`：PASS；
- `format.sh ci` 中 Ruff、format、codespell、typos、clang-format、PNG、filename、package、
  logger、forbidden imports、boolean context manager、long-function、symbolic-meta、
  suggestion hooks：PASS；
- markdownlint 环境被本机 npm `EALLOWGIT` 阻断；actionlint 的 Go dependencies 被
  `proxy.golang.org` timeout 阻断；gitleaks/shellcheck 本机无 binary。这四项是未执行或
  环境失败，不写成 PASS。

## 15. Runtime Effect

### P2 之前

```text
Window OFF: baseline full Attention
Window configured + P1 ELIGIBLE_ON: 只有 policy/scalar资格，Attention仍full
```

### P2 之后

| 配置结果 | P2 当前行为 | 是否可作为 Feature 发版行为 |
|---|---|---|
| Window OFF / FORCED_OFF | 完整 baseline；不创建 P2 capability | 是；forced-OFF 保留规定 warning |
| eligible + unsupported mode/backend/layout | `set_attn()` capability Gate 明确报错，不进入 forward | 是；符合 fail-closed |
| eligible + supported CPU/static candidate | `set_attn()` 附加只读 capability；Attention 仍读 full table/full lengths | **否；仅为内部 staged infrastructure** |

因此 C1/C2/C3 可以独立 review，却不能把仅含 P1～P3 的构建作为“MRV2 Window 已支持”发版。
在 P4 真正接通前，发布分支必须继续 hold；如果 maintainer 要单独发布这些中间 commit，必须
另行选择并测试临时 hard rejection/signal。当前实现任务已经冻结为连续 feature branch
阶段，不需要为开始 P3 增加临时 runtime warning，也不存在本轮 architecture escalation。

新增的 runtime state 只有 immutable Python contracts 与 borrowed tensor references。唯一
P2 tensor operation是按需 gather valid counts；当前 production proposal 尚未调用它。

因此 P2 没有改变：

- Target logits/read context；
- Draft 实际 read set；
- acceptance/rejection；
- positions/query shape；
- physical KV writes；
- slot mappings；
- prefix cache、function prefill、Graph 或 Async 的既有 OFF path。

## 16. 与 P1 / P3 / P4 关系

```text
P1
policy + Frozen scalar math + immutable plan
        |
        v
P2  <-- 本提交
actual inventory + canonical FullSource
+ exact-mapping valid counts + descriptor provider
        |
        v
P3  <-- 尚未开始
workspace backing + generation lease + lane/event lifetime
+ typed transport + speculator-owned DraftMetadataStore
        |
        v
P4  <-- 尚未开始
gated dense eager materialization
+ Draft-only metadata + actual Attention consumer
```

P1 决定“是否有资格、绝对窗口是什么”；P2 决定“真实 full source 是谁、这个 layout 能否
表达该窗口”；P3 才保证 backing 在并发/reader 生命周期内安全；P4 才让 Attention 真正
读取 Window。P3 的 generation identity 必须含 caller-owned monotonic mapping epoch，不能
使用 `idx_mapping_ptr`、row id 或 block count 代替。跳过任何一层都会把数学、ownership 或
operator correctness 混在一起。

Graph 不从 P4 eager 自动继承。它还需要 capture/live/replay typed hook、actual operand
fingerprint 与 NPU A/B/A replay Gate。

## 17. 开发者阅读指南

建议按以下顺序阅读 C2：

1. 先看 `tests/ut/spec_decode/test_draft_window.py:1051-1962`，从硬编码 group、mapping、
   integer oracle 和错误场景理解外部 contract；
2. 看 `draft_window.py:85-175` 的 layout/runtime/inventory types 与 exhaustive diagnostic；
3. 对照 upstream
   `vllm/v1/worker/gpu/attn_utils.py` 的 `init_attn_backend()`，确认外层 index 是 global gid、
   内层是 local consumer；
4. 看 upstream `vllm/v1/worker/gpu/block_table.py:41-213`，区分 persistent table/count、
   gathered input tables 与 slot mapping；
5. 看 `draft_window.py:192-291,942-1089`，理解 borrowed source、batch binding、valid-count
   gather、alias和geometry检查；
6. 看 `draft_window.py:312-482`，逐行对应 provider 的 configured-K、P1-plan validation、
   projection、capacity 和 T10 coverage；
7. 看 `draft_window.py:798-939,1092-1178`，理解 inventory/runtime Gate 到 capability 的
   总装流程；
8. 最后看 AR/DFlash/DSpark 三个 `_initialize_draft_window_source_capability()` 与
   `set_attn()` 尾部，确认只是增量 seam；
9. 看 `test_dflash2_v2.py`，确认继承 receiver 不等于 runtime enablement；
10. 依次看 `git show 83579675a997a44b293ff0ee1cb088a2eef0ed13` 与
    `git show fac84121ddf84fe5a76cd739432cea3b61365a9b`，确认 C2 与 review-fix 都没有
    upstream、BlockTables production、Attention builder、Graph 或 P3 文件修改。

## 18. P2 心智模型

1. `DraftWindowInventory`：当前真实 Draft consumers 的事实表，不是 model-name capability。
2. `global_group_id`：索引 canonical BlockTables；`local_consumer_index` 绝不能替代它。
3. `FullDraftKVSource`：借来的 full owner references；不是 copy，也不是 Window。
4. `input_block_tables`：当前 batch-row order；`num_blocks.gpu`：persistent request-slot order。
5. `bind_batch(idx_mapping)`：绑定与 full-table gather 相同的当前 mapping，不猜、不复制；
   pointer/object identity 不是 freshness，跨 batch 必须重绑并由 P3 epoch 防缓存。
6. `valid_num_blocks`：真实 source 边界；block id 0、row width、非零元素数都不能替代它。
7. `DraftWindowReadDescriptor`：只描述 `[start_col, end_col)`，不拥有 tensor。
8. `expected_future_offset`：来自独立配置；Eagle3 plan 的 `H-E` 不能自证 K。
9. `span ∣ legacy B`：当前 zero-offset direct-prefix 的静态证明；不满足就拒绝，不重对齐 S。
10. `source_end <= valid`：T10 语义 coverage；padding 0 不能掩盖 source shortage。
11. P2 后 Attention 仍 full；看到 capability 不等于 Feature 已 runtime enabled或可单独发版。

`P2 FINAL: PASS`

`P3 READY TO START`

# P2 Review Resolution

## Review metadata and counts

- Review：DeepSeek Independent Source Review，用户提供于 2026-10-10；原文未给单独版本号。
- Review 内容 SHA-256：`6ebe7b29b1719173b9e1015943a5298af2041026247f3b8bffd14cad8f0beefe`。
- 裁决基线：vLLM `84030bbe3d74d99bad477a3d2e37a973ccd8865c`；P1 Final
  `c58daea0df34d1a6253dc34221d2a084b13affd5`；P2
  `83579675a997a44b293ff0ee1cb088a2eef0ed13`。
- 裁决时间：`2026-10-10T10:21:31+08:00`（Asia/Shanghai）。
- 统计：18 项（F-01～F-10 + 8 项 documentation findings）；`ACCEPTED=10`，
  `PARTIALLY_ACCEPTED=5`，`OPTIONAL_STYLE_ONLY=3`，其余分类均为 0。
- Review-fix commit：`fac84121ddf84fe5a76cd739432cea3b61365a9b`。
- Architecture escalation：`NO`；未解决 P2 blocker：`NONE`。

## Resolution table

| ID | Severity | DeepSeek finding | Codex re-check / evidence | Resolution | Action |
|---|---|---|---|---|---|
| F-01 | Major | env FlashComm 可绕过 runtime Gate | 原 C2 `build_draft_window_runtime_context()` 只读 additional config；`ascend_config.py:606-615,1536-1540` 还接受 `VLLM_ASCEND_ENABLE_FLASHCOMM1` | **ACCEPTED** | production 按同一 bool validator + env 语义解析，SP 回到 `use_sequence_parallel_moe` 权威字段；env=1 → inventory FlashComm hard reject regression |
| F-02 | Major / contract | supported candidate 无 Window、无 signal | “Attention 仍 full”属 P2 明确 phase contract；P2 任务禁止 Attention binding，Final phase table也把首次 enablement放 P4。但若把 C1～C3 单独发版，确实会违反 Final I23/§18.2 | **PARTIALLY_ACCEPTED** | 接受 release-risk，拒绝把 staged C2 本身判成 runtime bug；Plan/Notes 增加“P1～P3 不可作为 Feature 单独发版”Gate。当前无需临时 warning，也无 architecture escalation |
| F-03 | Major / latent | mapping pointer 不能检测原地改写 | upstream mapping buffer复用；原测试原地改写后 gather读取新 batch，`is`/`data_ptr` 仍不变 | **PARTIALLY_ACCEPTED** | API 改名为 `references_same_idx_mapping_tensor()`；docstring/test 固定 one-batch 语义；P3 必须加入 monotonic mapping epoch。拒绝在 P2 越界实现 lease/generation |
| F-04 | Minor | Eagle3 offset check 用 plan offset 自证 | 原 C2 对 Eagle3 调 `resolve_static_future_offset(configured_k=future_offset)` 恒等成立 | **ACCEPTED** | provider 新增独立 `expected_future_offset`；production 从 configured K 解析；K=64/plan offset=0 regression 在旧实现不报错、修后拒绝 |
| F-05 | Minor / test | 只测 SimpleNamespace，未测真实 BlockTables contract | production 所需字段来自 upstream `BlockTables`，`AscendBlockTables` 继承并调整 slot buffer；原 P2 UT 确无 real-class contract | **ACCEPTED** | 用 CPU storage/Triton shim 执行真实 `AscendBlockTables.__init__`，再走真实 FullSource builder；production 无改动 |
| F-06 | Minor / test | 未覆盖 production int64 mapping | `_validate_idx_mapping` 与 `index_select` 支持 int64；原 cases 只有 int32，属于 coverage gap | **ACCEPTED** | reorder/subset/stale-tail oracle 参数化为 int32/int64；旧 production 的 int64 case通过 |
| F-07 | Minor | `AssertionError` 是 production signal且 `-O` 会消失 | 原代码是显式 `raise AssertionError`，不会被 `python -O` 删除；但对可伪造的不一致 frozen value，用 RuntimeError 语义更合适 | **PARTIALLY_ACCEPTED** | 拒绝 `-O` 事实前提，接受 exception hygiene；改为 RuntimeError并加 forged-inventory regression |
| F-08 | Minor / maintainability | pure-math module 被 P2 backend coupling | Final Design §10 明确允许 math/provider/workspace 同一 `draft_window.py`；P0/P2 Plan也选择该文件，拆分无 correctness收益 | **OPTIONAL_STYLE_ONLY** | 不做机械拆分；module docstring继续明确 P1/P2边界 |
| F-09 | Suggestion | failure formatting if-chain重复 | 当前 group reason 与 inventory/runtime reason分层，最终只在 require 时统一拼 identity；没有错误或丢字段 | **OPTIONAL_STYLE_ONLY** | 不改，避免无行为收益 churn |
| F-10 | Suggestion | runtime failure 使用 synthetic `gid=none` | 确为统一 diagnostics schema 的 synthetic context，不对应 gid 0 | **OPTIONAL_STYLE_ONLY** | Notes 明确 `none` 是 synthetic，不改 wire text |
| DOC-01 | Doc | P2 test function count写成30，实际新增29 | parent 34 → C2 63 functions；review 后67；collect 75 → 123 → 128 | **ACCEPTED** | §3 改为原 C2 29 functions/48 cases，final 33/53；总计67/128 |
| DOC-02 | Doc | kernel span被写成已证明 operator列粒度 | P2只证明 BlockTables/KV spec声明 geometry；不能静态证明 FIA actual read set | **ACCEPTED** | §6.1 降准为 declared projection span；P4 NPU physical-slot oracle仍开放 |
| DOC-03 | Doc | 未说明 pointer identity 对原地 rewrite盲区 | 源码与 mutation test支持该结论 | **ACCEPTED** | §7.2～§7.5、§16与心智模型加入 one-batch scope / P3 epoch要求 |
| DOC-04 | Doc | 未说明 supported-silent / unsupported-loud 不对称 | 中间阶段确有该观察；将其推成已发布产品行为则不成立 | **PARTIALLY_ACCEPTED** | §15 增 outcome table 与 release Gate；不增加临时 runtime行为 |
| DOC-05 | Doc | 缺 eligible path何时用户可见 | P4才接真实 consumer是既有 phase事实，但旧 Notes不够醒目 | **ACCEPTED** | §15/§16 明确 P4前不可宣称或发布 Feature ON |
| DOC-06 | Doc | exception split未解释 | capability rejection用 NotImplementedError；owner/source/runtime invariant用 RuntimeError；输入值/类型用 ValueError/TypeError | **ACCEPTED** | 本节固化 split，F-07 消除唯一不一致 AssertionError分支 |
| DOC-07 | Doc | 旧实现先红的过程声明不可从 final tree验证 | 历史运行真实存在，但 DeepSeek从 final tree无法独立复现的批评成立 | **PARTIALLY_ACCEPTED** | §14.1标成开发会话历史记录；新增 review red run给出精确 `5 failed, 2 passed` 与原因，不冒充 final-tree test |
| DOC-08 | Doc | 未说明 `gid=none backend=none` 是 synthetic | `_runtime_capability_failures()` 明确在无具体 consumer前生成 runtime reason | **ACCEPTED** | 本节与 Gate说明注明 synthetic，不把它解释为真实 group 0 |

## Exception contract after review

- `NotImplementedError`：配置为 eligible ON，但当前 method/backend/layout/mode Gate 未关闭；
- `RuntimeError`：已建立的 capability/source owner/inventory 内部不一致、source shortage或 stale owner；
- `ValueError` / `TypeError`：caller 提供的 scalar、dtype、shape、configured-K contract无效；
- P1 的 forced-OFF 不属于以上 rejection，继续 warning + baseline、且零 P2 state。

## Final verification

| Command / scope | Final result | Limitation |
|---|---|---|
| Review regression selected set | `7 passed` | 修复前原 C2 production为 `5 failed, 2 passed`；其中1个失败是测试 host shim问题 |
| `test_draft_window.py` + `test_dflash2_v2.py` | `134 passed, 1 warning` | CPU/static；warning为 editable vLLM无 `_version` |
| `tests/ut/spec_decode` excluding VWN | `360 passed, 13 skipped, 2 subtests passed, 1 warning` | 无 NPU backend |
| relevant BlockTables / attn-utils / extract-hidden-state UT | `52 passed, 1 warning` | CPU/static |
| full `tests/ut/spec_decode` | `362 passed, 13 skipped, 7 failed, 2 subtests passed` | 7个 VWN环境失败；P1-final父基线同文件为 `2 passed, 7 failed`，栈相同且不经过P2 |
| Ruff check / format-check | PASS | review changed files |
| targeted Mypy | PASS | `--follow-imports skip --check-untyped-defs` |
| compileall / `git diff --check` | PASS | review changed files |
| locally executable repository hooks | PASS | Ruff、format、codespell、typos、clang-format、PNG、filename、package、logger、forbidden-import、boolean-context、long-function、symbolic-meta、suggestion |
| markdownlint / actionlint / gitleaks / shellcheck | NOT PASS / NOT RUN | npm `EALLOWGIT`；Go proxy timeout；后两项本机无 binary |

## Final P2 invariant audit

- P1 policy preserved；CONFIG_OFF / forced-OFF 仍在 owner helper 前返回，零 P2 state；
- FullSource 仍是 canonical owner references，production BlockTables/table/slot path未改；
- valid count 仍用同一 `idx_mapping` 从 persistent request slot gather到 batch row；
- block id 0 仍为合法 id，padding每轮清零，source shortage硬失败；
- global gid与local index、canonical S、zero-offset geometry均保持原证明；
- provider 现在还要求独立 configured static K，不再对 Eagle3 tautological；
- FlashComm env/additional-config、SP/CP/topology/Graph/Async仍 fail closed；
- 没有 workspace、lease、Window backing、typed transport、DraftMetadataStore、Attention binding或Graph hook；
- Target、positions、query、slot mapping、full block tables均未触碰；
- P3 mapping epoch 是下一阶段强制输入，不是 P2 已实现能力。

## Final phase status

| Area | Status |
|---|---|
| P1 | **FINAL PASS** |
| P2 | **FINAL PASS**；C2 `83579675...` + review-fix `fac84121...` |
| P3 | **NOT STARTED；READY TO START**；必须先实现 monotonic mapping epoch / generation identity |
| P4 | **CONDITIONAL；NOT STARTED**；Attention仍 full |
| Graph | **BLOCKED / FAIL CLOSED FOR WINDOW ON** |
| Backend extensions | **BLOCKED PER ROUTE**：MLA、DSA/V4.1、SFA、recycling、multi-group、parallel、Async、DFlash2 |

`P2 FINAL: PASS`

`P3 READY TO START`
