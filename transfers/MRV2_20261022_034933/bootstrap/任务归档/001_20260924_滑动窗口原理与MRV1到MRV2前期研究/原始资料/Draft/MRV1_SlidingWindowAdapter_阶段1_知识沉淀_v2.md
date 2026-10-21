# 阶段 1：`SlidingWindowAdapter`——吃透 MRV1 窗口数学

> 目标：不是背 MRV1 源码，而是建立一套以后能迁移到 MRV2 的“行为模型”。
>
> 本阶段要做到：
> 1. 看懂 Sliding Window 的数学。
> 2. 知道 `seq_lens / block_table / slot_mapping` 分别代表什么。
> 3. 明白为什么 read 可以 window，而 write 必须保持 global。
> 4. 知道 Adapter 在 MRV1 中何时创建、何时 apply、最终被谁消费。
> 5. 能把 DSpark 的完整数据流画出来。
> 6. 能回答迁移 MRV2 时必须保持哪些不变式。

---

## 1. 三个最重要的对象

### 1.1 Proposer

`Proposer` 是草稿推理的总控制器。

```text
NPUModelRunner
    │
    ▼
Proposer
    ├─ Draft Model
    ├─ 输入准备
    ├─ Attention metadata builder
    ├─ KV / slot mapping
    ├─ draft forward
    ├─ draft sampling
    └─ SlidingWindowAdapter
```

记忆：

```text
Proposer = 草稿推理“老板”
Draft Model = 真正做神经网络 forward 的“工人”
SlidingWindowAdapter = 在窗口场景下改 metadata 的“工具”
```

### 1.2 Draft Model

真正执行：

```python
self.model(...)
```

负责 Attention、MLP、hidden states 等模型计算。

### 1.3 SlidingWindowAdapter

它不是模型，只负责：

```text
完整 sequence metadata
        ↓
滑动窗口局部 metadata
```

它不会预测 token，也不会替代 Attention kernel。

---

## 2. `SlidingWindowAdapter.__init__`

```python
def __init__(
    self,
    window_size: int,
    block_size: int,
    max_num_reqs: int,
    future_offset: int,
    device: torch.device,
) -> None:
    self.window_size = window_size
    self.block_size = block_size
    self.window_blocks = (window_size + block_size - 1) // block_size
    self.max_window_blocks = self.window_blocks + 1
    self._future_offset = future_offset
    self._block_table_clone = torch.zeros(
        (max_num_reqs, self.max_window_blocks),
        dtype=torch.int32,
        device=device,
    )
```

| 参数 | 含义 |
|---|---|
| `window_size` | Sliding Window 最多保留多少 token |
| `block_size` | 一个 KV block 包含多少 token |
| `max_num_reqs` | 最大 request 数 |
| `future_offset` | 为得到正确窗口逻辑右边界，当前 `seq_lens` 还差多少 position |
| `device` | 工作 tensor 所在设备 |

### 2.1 `window_blocks`

```python
(window_size + block_size - 1) // block_size
```

就是：

```text
ceil(window_size / block_size)
```

例如：

```text
window_size = 32
block_size = 16
→ window_blocks = 2
```

### 2.2 为什么 `max_window_blocks = window_blocks + 1`

逻辑窗口通常不和 block 边界对齐。

```text
逻辑窗口：
72 ---------------- 103

KV block：
Block 4: 64~79
Block 5: 80~95
Block 6: 96~111
```

虽然窗口只有 32 token，却横跨 3 个 block，所以最坏情况需要多 1 个 block。

### 2.3 `_block_table_clone`

预分配：

```text
[max_num_reqs, max_window_blocks]
```

保存每个 request 当前窗口对应的小型 block table。

```text
完整：
[10,11,12,13,14,15,16]

窗口：
[14,15,16]
```

---

## 3. `future_offset`：最容易误解的变量

### 3.1 它不代表“未来 token 已经存在”

例如：

```text
seq_lens = 100
future_offset = 4
```

未来：

```text
position:
100 101 102 103

token value:
 ?   ?   ?   ?
```

程序知道的是位置，不知道内容。

所以：

> 提前知道未来位置 ≠ 提前知道未来内容。

它不会让当前 token 看见未来 KV，也不会破坏 causal attention。

### 3.2 最准确的定义

> `future_offset` = 为了得到正确的窗口逻辑右边界，当前 `seq_lens` 还差多少 position。

不同 proposer 的 `seq_lens` 语义不同：

```text
EAGLE3:
seq_lens 只包含 context
未来 K 个位置尚未计入
→ future_offset = K

DFlash / DSpark:
input preparation 已把 query stretch 加入 seq_lens
→ future_offset = 0

MTP:
复用 target layer，不直接创建该 Adapter
```

---

## 4. 窗口数学

核心公式：

```python
start = (
    (seq_lens + future_offset - window_size).clamp(min=0)
    // block_size
) * block_size
```

拆开：

```text
seq_lens
   │
   │ + future_offset
   ▼
logical_right
   │
   │ - window_size
   ▼
logical_start
   │
   │ clamp(min=0)
   ▼
非负 logical_start
   │
   │ // block_size * block_size
   ▼
block-aligned actual start
```

### 4.1 完整数值例子

```text
seq_lens = 100
future_offset = 4
window_size = 32
block_size = 16
```

逻辑右边界：

```text
100 + 4 = 104
```

逻辑窗口：

```text
[72, 104)
```

即 token：

```text
72 ~ 103
```

block 对齐：

```text
72 // 16 * 16 = 64
```

因此实际从 absolute token 64 所在 block 开始取。

### 4.2 为什么窗口必须向右推进？

Sliding Window 的定义：

```text
当前位置向右移动
→ 可见历史窗口也向右移动
```

如果实际会走到 127，却仍按旧 `seq_lens=120`：

```text
错误窗口：
88~119

正确窗口：
96~127
```

窗口会整体落后。

---

## 5. `compute_sliding_window_block_table()`

一句话：

> 从 full block table 中裁出当前 window 真正需要的 block。

流程：

```text
seq_lens
  ↓
算 block-aligned start token
  ↓
start_block_index
  ↓
构造 [0,1,2,...]
  ↓
得到每个 req 的 src_cols
  ↓
torch.gather(full_block_table)
  ↓
valid_mask
  ↓
windowed block table
```

### 5.1 完整例子

```text
window_size = 32
block_size = 16
future_offset = 4
seq_len = 100

full block table:
[10,11,12,13,14,15,16]
```

逻辑起点：

```text
100 + 4 - 32 = 72
```

block 对齐：

```text
72 // 16 * 16 = 64
```

起始列：

```text
64 // 16 = 4
```

最多取 3 个 block：

```text
cols = [0,1,2]
```

真实 source columns：

```text
src_cols = [4,5,6]
```

gather：

```text
full:
[10,11,12,13,14,15,16]
             ↑  ↑  ↑

window:
[14,15,16]
```

窗口局部长度：

```text
_windowed_seq_lens
= 100 - 64
= 36
```

注意：

```text
start_block_indices
```

是 block table 的列索引；真正物理 KV block id 是 table 中的值。

---

## 6. `apply()`：把 metadata 变成窗口视图

`apply()` 核心做三件事。

### 6.1 保存 full table

```python
self.full_block_table = common_attn_metadata.block_table_tensor
```

因为后面仍需要 full table 做绝对坐标相关计算。

### 6.2 替换 block table

```text
full:
[10,11,12,13,14,15,16]

→

window:
[14,15,16]
```

### 6.3 替换 `seq_lens`

```text
global seq_len = 100
window-aligned start = 64
windowed seq_len = 36
```

真实 sequence 没变短，只是 Attention 局部坐标变成：

```text
global:
64 65 ... 99

local:
0  1  ... 35
```

同时同步：

```text
seq_lens_cpu
_seq_lens_cpu
seq_lens_cpu_upper_bound
```

避免 NPU/CPU 认知不一致。

一句话：

> `apply()` 把 Attention metadata 从“全局 sequence 视角”改成“滑动窗口局部视角”。

---

## 7. MRV1 初始化链

```text
NPUModelRunner._set_up_drafter()
    ↓
根据 speculative method
创建 Proposer
    ↓
此时还没有 SlidingWindowAdapter


NPUModelRunner.load_model()
    ↓
加载 Target Model
    ↓
drafter.load_model(target_model)
    ↓
加载 Draft Model
    ↓
识别 Draft Attention Runtime Layers
    ↓
得到 backend / KV spec / metadata builder / kernel block size
    ↓
读取 draft_window_size
    ↓
决定 future_offset
    ↓
创建 SlidingWindowAdapter
```

### 7.1 为什么 Proposer 可以先创建？

因为它已经知道：

```text
method
K
device
runner
draft model config
```

### 7.2 为什么 Adapter 必须后创建？

因为需要等 Draft Attention backend 确定后才能知道：

```text
kernel_block_size
```

---

## 8. 为什么 `drafter.load_model(target_model)` 需要 Target Model？

不只是为了 block size。

Draft 与 Target 可能共享：

```text
embedding
lm_head
多模态 token config
部分 runtime state
MTP / EAGLE 结构资源
```

所以 target model 是 Draft Runtime 建立的一部分输入。

---

## 9. 为什么要“找 Draft Attention Layers”？

不是找权重，而是在 vLLM Runtime 中找：

```text
AttentionLayerBase
```

这些对象携带：

```text
attention backend
KV cache spec
metadata builder
kernel block size
attention group
```

典型做法：

```text
加载 Draft 前：
registry = Target attention layers

加载 Draft 后：
registry = Target + Draft attention layers

集合差：
Draft attention layers
```

本质：

> 建立 Draft Attention Runtime。

---

## 10. MRV1 DSpark 最终纵向调用链

```text
NPUModelRunner.execute_model()
        │
        ▼
Target model forward
        │
        ├─ token
        ├─ positions
        ├─ hidden states
        └─ full common metadata
        │
        ▼
sample_tokens()
        │
        ▼
propose_draft_token_ids()
        │
        ▼
drafter._propose()
        │
        ▼
DSpark.set_inputs_first_pass()
        │
        ├─ 修正 rejected tail
        ├─ 生成 DSpark query positions
        ├─ 更新 seq_lens
        ├─ 用 FULL per-group block table
        │   计算 query slot_mapping
        └─ 准备 draft inputs
        │
        ▼
build_draft_attn_metadata()
        │
        ├─ 当前 group FULL block table
        ├─ 当前 group query slot_mapping
        │
        ▼
SlidingWindowAdapter.apply()
        │
        ├─ FULL block_table
        │     ↓
        │   WINDOW block_table
        │
        └─ global seq_lens
              ↓
            windowed seq_lens
        │
        ▼
AscendDSAMetadataBuilder.build_for_drafting()
        │
        ├─ windowed block_table
        ├─ windowed seq_lens
        └─ full-table-based slot_mapping
        │
        ▼
AscendDSAReqMetadata
        │
        ▼
set_ascend_forward_context()
        │
        ▼
draft model.forward()
        │
        ├─ KV READ
        │   → window table + window len
        │
        └─ KV WRITE
            → absolute slot_mapping
```

---

## 11. 三类关键数据：一定不要混

### 11.1 `seq_lens`

回答：

> Attention 当前认为有效 KV 长度是多少？

DSpark 生命周期：

```text
Target seq_len
    ↓
减 rejected tail
    ↓
+ num_query_per_req
    ↓
得到 DSpark 本轮绝对 KV 终点
    ↓
SlidingWindowAdapter
    ↓
变成 window-local seq_len
    ↓
Attention read length
```

### 11.2 `block_table`

回答：

> 逻辑 block 对应哪个物理 KV block？

```text
InputBatch full block table
    ↓
per-group full block table
    ↓
先用于计算 absolute slot_mapping
    ↓
当前 group 进入 apply()
    ↓
windowed block table
    ↓
Attention read
```

### 11.3 `slot_mapping`

回答：

> 新 token 的 KV 到底写到哪个物理 slot？

```text
absolute_kv_position
    ↓
column = position // block_size
    ↓
block_id = full_block_table[column]
    ↓
slot = block_id * block_size + offset
```

它必须基于 full table。

---

## 12. 最重要的不变式：READ windowed，WRITE global

### READ

Attention 只需要最近的可见 KV：

```text
windowed block_table
+
windowed seq_lens
```

### WRITE

新 token 的 KV 必须写到真实全局物理位置：

```text
full-table-based slot_mapping
```

一句话：

> **Sliding Window 改的是“Draft Attention 可以回头看多远”，不是“新产生的 KV 在整个 KV Cache 世界里写到哪里”。**

---

## 13. 一个完整数字例子：Target → DSpark → Sliding Window → Attention

假设：

```text
Target metadata seq_len = 100
rejected = 2
num_query_per_req = 4
window_size = 32
block_size = 16
```

### 第一步：有效 Target 长度

```text
100 - 2 = 98
```

### 第二步：DSpark query positions

```text
98
99
100
101
```

所以：

```text
cad.seq_lens
= 98 + 4
= 102
```

这不代表 4 个 draft token 内容已存在，只代表本轮 KV 布局规划的逻辑终点。

### 第三步：先算 WRITE 地址

对 position 100：

```text
100 // 16 = 6
```

去 full block table column 6 查物理 block id：

```text
slot = block_id * 16 + 100 % 16
```

得到 `slot_mapping`。

### 第四步：再裁 READ window

```text
102 - 32 = 70
70 // 16 * 16 = 64
```

窗口局部长度：

```text
102 - 64 = 38
```

Adapter 后：

```text
seq_lens:
102 → 38

block_table:
FULL → absolute 64 开始的 WINDOW table

slot_mapping:
保持不变
```

### 第五步：Attention

```text
KV READ:
window table + window len

KV WRITE:
slot_mapping
```

---

## 14. 为什么 DSpark 的 apply 比 EAGLE/DFlash 晚？

DSpark 有 per-group full block table。

如果过早：

```text
FULL
↓
apply
↓
WINDOW
```

后面 DSpark 又：

```text
block_table_tensor = per_group_full_table
```

就会把窗口表覆盖回 FULL。

更糟的是：

```text
seq_lens 已 windowed
+
block_table 又 FULL
```

坐标系不一致。

所以必须：

```text
先选当前 group FULL table
↓
装入当前 group query slot_mapping
↓
apply()
↓
立刻 builder
```

本质：

> DSpark 不是窗口数学不同，而是 per-group block table 的选择时机更晚。

---

## 15. Metadata Builder 是干什么的？

Adapter 只是改：

```text
common_attn_metadata
```

Builder 把：

```text
seq_lens
block_table
slot_mapping
```

翻译成 backend 真正认识的：

```text
AscendDSAReqMetadata
```

即：

> 通用 metadata → DSA kernel metadata。

---

## 16. `set_forward_context()` 是干什么的？

`self.model(...)` 并没有显式传 `attn_metadata`。

所以系统先：

```text
set_ascend_forward_context()
```

把 per-layer metadata 放到执行上下文。

模型内部 Attention 层：

```text
get_forward_context()
↓
按 layer_name 取 metadata
```

可以理解为：

> “先把 Attention 参数放桌面上，model.forward 内部的 Attention 层自己来取。”

---

## 17. 阶段 1 最核心的 6 条结论

1. `future_offset` 是**为了得到正确窗口右边界，当前 `seq_lens` 还差多少 position**。
2. DSpark 进入 Adapter 前已把 `num_query_per_req` 加入 `seq_lens`，所以 `future_offset=0`。
3. DSpark 必须先用 full per-group block table + absolute KV position 算 `slot_mapping`。
4. `SlidingWindowAdapter` 修改 read 侧：`block_table + seq_lens`；不改 `slot_mapping`。
5. DSpark 必须在选定当前 per-group full block table 后再 apply。
6. 最终 Attention：
   - READ → windowed table + windowed length
   - WRITE → full-table-based slot mapping

---

## 18. 阶段 1 停止条件

进入 MRV2 前，只需能回答：

```text
1. Target output 怎么进入 drafter？
2. DSpark input_ids / positions 怎么生成？
3. common_attn_metadata 从哪里来？
4. apply 前 seq_lens 的准确语义是什么？
5. full block table 从哪里来？
6. slot_mapping 为什么必须提前用 full table 生成？
7. SlidingWindowAdapter.apply() 在哪里调用？
8. windowed metadata 被哪个 builder 消费？
9. set_forward_context 起什么作用？
10. Draft model.forward 内 READ / WRITE 最终分别消费什么？
```

能回答这些：

> 阶段 1 就够了，不需要继续横向学习 MRV1。

---

## 19. 下一阶段：MRV2 推荐阅读路径

```text
阶段 2：MRV2 architecture

2.1 MRV2 ModelRunner → Speculator 总入口
2.2 AscendDSparkSpeculator
2.3 _build_attn_metadata / builder inputs
2.4 AscendBlockTables
    - full table
    - kernel table
    - slot_mapping
2.5 AscendInputBuffers / request state
    - NPU seq_lens
    - CPU seq_lens
    - NumPy mirror
    - authoritative state

阶段 3：
先设计 Eager sliding-window path

阶段 4：
ACL Graph / persistent buffer / static address

阶段 5：
边界、精度、eager/graph、性能验证
```

---

## 20. 后续增量维护约定

后续继续讨论时：

- 新 MRV1 细节：补到“阶段 1”对应小节。
- 进入 MRV2：新增“阶段 2：MRV2 调用链和映射”。
- 开始修改代码：新增“阶段 3：设计与修改点”。
- 完成测试：新增“阶段 4：验证、性能、问题与结论”。

本文件保持“看一遍就能重新建立完整心智模型”的结构化风格。
