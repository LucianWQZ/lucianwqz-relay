# DSpark 投机推理 KV 滑动窗口:MRV1 逻辑梳理 → MRV2 适配落点

> 仓库:`/Users/wenqingzhang/Desktop/vllm/vllm-ascend`(本地 checkout 已是 `#14596` 之后的 main)
> 参考实现(上游 vLLM,本地 checkout):`/Users/wenqingzhang/Desktop/vllm/vllm/vllm/`
> 术语约定:变量/函数/字段名保留英文原文,其余中文讲解。
> 所有行号均在本机上逐条核对过。

---

## 0. 任务确认

你师傅给的三个编号是 vllm-ascend 上**同一条 feature 线**,作者都是 `YzTongNiar`:

| PR | 标题 | 状态 / 合并时间 | head 分支 | 关键改动 |
|---|---|---|---|---|
| [#10021](https://github.com/vllm-project/vllm-ascend/pull/10021) | `[Feature] Add sliding windows for eagle3 to conquer long sequence scenario` | closed | — | 这条线的起点(Eagle3) |
| [#10023](https://github.com/vllm-project/vllm-ascend/pull/10023) | `[Feature] Add kv sliding window for Eagle3 and DFlash` | merged 2026-07-13 | `sw_eagle3_blk_table` | 新增 `vllm_ascend/spec_decode/utils.py` (+92 → `SlidingWindowAdapter`)、`llm_base_proposer.py` (+39/-1)、UT (+33) |
| [#12103](https://github.com/vllm-project/vllm-ascend/pull/12103) | `[BugFix][CI] Add E2E for kv sliding window; fix block size input bug` | merged 2026-07-16 | `qwen3.6_sw_draft` | 修 hybrid attention 模型(Qwen3.6)的 `kernel_block_size` 初始化;补双卡 E2E |
| [#14596](https://github.com/vllm-project/vllm-ascend/pull/14596) | `[Spec Decode] [Doc] Support speculative decode KV slidng window for Dspark` | merged 2026-08-31 | `sw-dspark-pr` | **DSpark 支持** + 新增设计文档 `speculative_kv_sliding_window.md` (+118)、`test_dspark_kv_sliding_window`、`llm_base_proposer.py` (+47/-6,dspark 应用点)、`utils.py` (+10/-13,`future_offset` 表) |

**结论:是这个任务,可以继续。**

理由:
1. 你师傅给的"增益测试"数字与这三个 PR 正文里的表一一对应 —— `#10023` 的 Eagle3(mean acceptance 1.3358 → 1.8809)/DFlash 表、`#12103` 的 `dflash win 2048 → 4.49` 与 ×1.7~2.15 吞吐表、`#14596` 的 DSpark 段。
2. 三个 PR **全部只覆盖 MRV1**。`#14596` 新增的设计文档里专门有一节 `## MRV2 status`,原文:

   > Model Runner V2 is not yet covered by this feature. The MRV2 speculator system bakes `seq_lens` / block tables into the final per-layer metadata inside `build_attn_metadata` - there is no shared `common_attn_metadata` to mutate after the build, so porting the window requires applying it to the **builder inputs** (windowed `input_buffers.seq_lens`, gathered per-group block-table clones, capped `seq_lens_cpu_upper_bound`) around the `_build_draft_attn_metadata` call in `vllm_ascend/worker/v2/spec_decode/dspark/speculator.py`. The window math and the two invariants above carry over unchanged.

   位置:`docs/source/developer_guide/Design_Documents/speculative_kv_sliding_window.md:89-99`

所以你的任务 = 这条线的**下一步**:把 `draft_window_size` 这套投机 KV 滑窗从 MRV1 适配到 MRV2(DSpark 路径切入)。

### 两条相关但**不等于**本任务的线索(避免撞车)

- [#14594](https://github.com/vllm-project/vllm-ascend/pull/14594)(open,同作者 `YzTongNiar`):`[Spec Decode][MRV2] Support DFlash2 in MRV2` —— 同一个人在推 MRV2 侧的 spec decode 移植,注意跟他协调 MRV2 上的改动面。
- [#15823](https://github.com/vllm-project/vllm-ascend/pull/15823)(closed)/ [#15826](https://github.com/vllm-project/vllm-ascend/pull/15826)(open,`Tflowers-0129`):把 `draft_window_size` 从"只限制 draft attention 读的范围"升级为**物理 KV 逐出**(draft 独立 cache group + scheduler 回收窗口外 block + Mooncake 注册)。方向不同、仍是 MRV1 侧,但会改 `spec_decode/dspark_proposer.py`、`patch/platform/patch_kv_cache_utils.py`,以及设计文档本身 —— 你读文档时若发现和本文不一致,优先怀疑是这两个 PR 合并进来了。

---

## 1. 先分清三个都叫 "window" 的东西(最容易踩的坑)

仓库里有三样东西共享 "window" 这个词,语义完全无关。**先把它们分开,再读代码**,否则一定会绕晕。

| | **A. `draft_window_size`(本任务)** | **B. DSpark 原生 SWA 索引** | **C. `BLOCK_TABLE_WINDOW_SIZE`** |
|---|---|---|---|
| 谁设定 | 用户 `additional_config["draft_window_size"]` | 模型 HF config 的 `sliding_window`(如 DeepSeek-V4.1 = 128) | triton kernel 的 `tl.constexpr` |
| 语义 | 把 **draft 模型**能读到的 KV 裁到最近 `W` 个 token | draft block 的**非因果**稀疏可见槽位列表(显式 slot id) | 一个 tile 内要读几列 block table |
| 载体 | `SlidingWindowAdapter` 改写 `common_attn_metadata` | `dspark_swa_indices` / `ori_win_left` / `ori_mask_mode` | kernel 内寄存器窗口 |
| 代码 | `vllm_ascend/spec_decode/utils.py:83-169` | `vllm_ascend/attention/dsa_v1.py:408-503` | `ops/triton/compute_slot_mapping.py`;`worker/v2/block_table.py:62-69` |
| 影响 target 模型? | **否**,只影响 draft | 否 | 否 |
| v2 是否已支持 | **否(本任务)** | 部分(DSA builder 内部自建) | 是(与 spec decode 无关) |

补充:`dsa_v1.py:408` 的 `get_dspark_sparse_sas_window()` 返回 `(window_size + block_size - 1, 0)`,这里 `window_size` 是 **B**(模型原生 SWA),`block_size`(= `num_speculative_tokens`)是 draft block 长度。它的"加 N-1"是 A 里 `future_offset` 的另一种体现,别和 A 的窗口数学混在一起。

---

## 2. 建议的阅读顺序

### Tier 1 —— v1 滑窗主线(按序读)

1. **`docs/source/developer_guide/Design_Documents/speculative_kv_sliding_window.md`**(119 行,权威 spec)
   - `:3-15` 动机:GLM-5.2 + 早期 DSpark draft 在 32k 上下文下 mean acceptance 从 ~5 掉到 ~1,投机变成净亏损
   - `:17-30` 配置(`{"draft_window_size": 2048}`)+ 与 MTP 的不兼容
   - `:32-43` **窗口数学**(本文第 4 章逐行展开)
   - `:45-51` **`future_offset` 表**(最容易搞错的一处)
   - `:59-67` **两条不变式**
   - `:69-88` MRV1 两个应用点
   - `:89-99` **`## MRV2 status`** ← 你的任务说明书
2. **`vllm_ascend/spec_decode/utils.py:83-169`** —— `SlidingWindowAdapter` 本体(含 `DynamicSpecScheduler` 在同一文件 `:208-588`,但那是自适应验证预算,与窗口无关,先跳过)
3. **`vllm_ascend/spec_decode/dspark_proposer.py`**(423 行)—— DSpark v1 的入口;`:226-357` `set_inputs_first_pass()` 是 draft 布局的心脏,`:313-340` 是 `future_offset=0` 的成因
4. **`vllm_ascend/ops/triton/spec_decode/utils.py:69-204`** —— `copy_and_expand_dflash_and_dspark_inputs_kernel`:`input_ids` / `positions` / `query_slot_mapping` / `token_indices` 到底怎么摆
5. **`vllm_ascend/spec_decode/dflash_proposer.py`**(317 行)—— DSpark 的父类,看清 DSpark 覆盖了什么

### Tier 2 —— base proposer(`llm_base_proposer.py`,2685 行,只读这几段)

- `:410-452` adapter 的**构造与校验**(含 `future_offset` 决策)
- `:1119-1127` **应用点 A**(Eagle3/DFlash,显式排除 dspark/mtp)
- `:2085-2129` **slot_mapping 用未裁剪表**(第 2 条不变式的落点)
- `:2547-2630` **应用点 B**(dspark 分支 + `:2604-2605`)

### Tier 3 —— runner 与验证

- `vllm_ascend/worker/model_runner_v1.py`:`_set_up_drafter` / `propose_draft_token_ids` / `_calc_spec_decode_metadata`
- `vllm_ascend/sample/rejection_sampler.py`:`:156-266` `AscendRejectionSampler.forward`
- `vllm_ascend/attention/utils.py:553-587` `_select_seq_lens()` —— **决定 built metadata 携带哪个 length 张量**

### Tier 4 —— config 与测试

- `vllm_ascend/ascend_config.py:497`(字段)、`:355`(默认值)
- `tests/ut/spec_decode/test_utils.py:192-214`、`tests/ut/spec_decode/test_eagle_proposer.py:311+`(`TestSlidingWindowAdapter`)、`tests/ut/spec_decode/test_llm_base_proposer.py:196-231`
- `tests/e2e/pull_request/one_card/spec_decode/test_dspark.py:82-158`(`test_dspark_kv_sliding_window`)

---

## 3. v1 数据流总览

```text
NPUModelRunner.execute_model()                        worker/model_runner_v1.py
 └─ _prepare_inputs()
     ├─ _calc_spec_decode_metadata()                  → SpecDecodeMetadata
     └─ drafter.set_per_group_attn_metadata(gid, cm.block_table_tensor, cm.slot_mapping)
 └─ sample_tokens()
     ├─ _sample() → AscendRejectionSampler.forward()   sample/rejection_sampler.py:156
     │     (用 draft_probs + target logits 做拒绝采样;窗口不参与)
     └─ propose_draft_token_ids()                      model_runner_v1.py:1839
         └─ drafter._propose(...)                      spec_decode/llm_base_proposer.py:950
             ├─ set_inputs_first_pass(...)             ← DSpark 覆盖版 dspark_proposer.py:226
             │    ├─ 每个 kv-cache-group 跑 inputs kernel(:270-307)
             │    └─ 把 query stretch 烘进 cad.seq_lens(:313-340)   ← future_offset=0 的成因
             ├─ build_draft_attn_metadata(...)         llm_base_proposer.py:2547
             │    └─ dspark 分支 :2588-2610
             │         ├─ copy.copy(cad) → 换成 per-group block table / slot_mapping
             │         ├─ self.sliding_window.apply(cad)        ← 应用点 B :2604-2605
             │         └─ builder.build_for_drafting(cad, draft_index=1, ...) :2608
             ├─ for draft_index in 1..K-1: attn_update_stack_num_spec_norm(...)  :1952
             └─ 模型 forward(draft)→ 得到 draft_token_ids
```

对照 EAGLE3 / DFlash(**非 DSpark**)路径:应用点在 `:1119-1127`(应用点 A),在 `_propose` 里对共享的 `common_attn_metadata` 应用一次,然后 `build_draft_attn_metadata` 走非 dspark 分支 `builder.build(0, cad, ...)`。

**谁产出 / 谁消费(窗口视角)**:

| tensor | 谁写 | 谁读 | 窗口是否改 |
|---|---|---|---|
| `cad.seq_lens`(NPU) | `dspark_proposer.py:318`(+`num_query_per_req`) | FIA 的 KV length | **改**(截到 `windowed_len`) |
| `cad.block_table_tensor` | dspark 分支换成 per-group 表 | FIA 的 block table | **改**(裁到窗口块) |
| `cad._seq_lens_cpu` / `seq_lens_cpu` | `dspark_proposer.py:322-330` | DSA/MLA builder 的 CPU 镜像(经 `_select_seq_lens`) | **改**(同幅截断) |
| `cad.slot_mapping` | per-group query slot_mapping buffer | `reshape_and_cache` 写 KV | **绝不改** |

---

## 4. `SlidingWindowAdapter` 逐行拆解(核心)

文件:`vllm_ascend/spec_decode/utils.py:83-169`

### 4.1 构造(`:101-118`)

```python
def __init__(self, window_size, block_size, max_num_reqs, future_offset, device):
    self.window_size = window_size            # W
    self.block_size = block_size              # b,是 kernel_block_size 不是逻辑 block_size
    self.window_blocks = (window_size + block_size - 1) // block_size      # ceil(W/b)
    self.max_window_blocks = self.window_blocks + 1                        # +1!
    self._future_offset = future_offset       # K,见 4.3
    self._block_table_clone = torch.zeros(
        (max_num_reqs, self.max_window_blocks), dtype=torch.int32, device=device)
```

三个要点:

1. **`block_size` 用 `kernel_block_size`**(`llm_base_proposer.py:406-408` → `:448`),因为 block table 的列是 kernel block(`:2096-2102` 注释明确说明了这一点)。`#12103` 修的就是 hybrid attention 模型上这个值的初始化。
2. **为什么 `+1`**:窗口起点向**下**做块对齐(`floor`),对齐后实际覆盖长度可达 `W + b - 1`,即可能跨 `ceil(W/b) + 1` 个块。
3. **`_block_table_clone` 是持久 buffer**,不是每次新分配 —— 一是避免每步分配,二是 ACL graph 场景下地址必须稳定(v1 侧 DSpark 本身是 eager,`dspark_proposer.py:73` `use_cuda_graph = False`,所以 v1 这条约束较松;**v2 是 FULL graph,这条会变成硬约束**,见第 8 章)。

### 4.2 窗口数学与裁剪(`:120-147`)

```python
# :132-134
self.start_tokens_in_window_rounding = ((common_attn_metadata.seq_lens + k_future - w).clamp(min=0) // b) * b
self._windowed_seq_lens = common_attn_metadata.seq_lens - self.start_tokens_in_window_rounding
start_block_indices = self.start_tokens_in_window_rounding // b

# :136-147
cols = torch.arange(self.max_window_blocks, device=...).unsqueeze(0)   # 0 基网格
src_cols = start_block_indices.unsqueeze(1) + cols
src_cols_clamped = src_cols.clamp(max=full_cols - 1)                   # 防 OOB
gathered = torch.gather(self.full_block_table, 1, src_cols_clamped)
needed = torch.clamp((self._windowed_seq_lens + b - 1) // b, max=self.max_window_blocks).unsqueeze(1)
valid_mask = (cols < needed) & (src_cols < full_cols)
out[:num_reqs].copy_(gathered * valid_mask.to(gathered.dtype))
```

对应设计文档 `:38-43` 的公式:

```text
start        = floor(clamp(seq_lens + K - W, min=0) / b) * b   # 块对齐的窗口起点
windowed_len = seq_lens - start                                # <= W + b - 1
start_block  = start // b
needed       = ceil(windowed_len / b)  (capped by max_window_blocks = ceil(W/b) + 1)
```

**全程在 device 上做算术**(`.clamp` / `//` / `*`),没有任何 `.item()` 或 D2H —— 这是设计上刻意为之(AGENTS.md 里也点名了 `tensor.item()` 在 NPU 上的同步代价)。

用单测 `tests/ut/spec_decode/test_utils.py:192-214` 验算一遍(W=128, b=64, K=0, seq_lens=300):
`start = floor(clamp(300-128,0)/64)*64 = floor(172/64)*64 = 2*64 = 128`;`windowed_len = 300-128 = 172` ⇒ 断言 `expected = 172`。✅ 对得上。

`gather` 后为什么可以**置零**而不影响正确性:被置零的列(`cols >= needed` 或 `src_cols` 越界)**永远不会被 FIA 读到**,因为同一幅 `windowed_len` 已经把 FIA 的 KV length 截断了。这条推理是整套机制的基石,由第 4.4 节的第 2 条不变式保证。

### 4.3 `future_offset`(= K):整条线最容易错的一个数

`llm_base_proposer.py:437-452`:

```python
# EAGLE3: seq_lens is context-only, K draft positions lie beyond it
#   -> future_offset = K.
# DFlash / DSpark: set_inputs_first_pass bakes the query stretch into
#   seq_lens (dspark_proposer adds num_query_per_req at cad.seq_lens),
#   so the window end must not add K again -> future_offset = 0.
future_offset = 0 if self.method in ("dflash", "dspark") else self.num_speculative_tokens
```

| method | `future_offset` | 为什么 |
|---|---|---|
| EAGLE3 | `num_speculative_tokens` | `seq_lens` 只含 context,K 个 draft 位置在它**之外**,窗口末端必须覆盖到 `seq_lens + K` |
| DFlash / DSpark | `0` | `set_inputs_first_pass` 已把 query stretch 烘进 `seq_lens`,`final = seq_lens` |

DSpark 侧的烘入点 `dspark_proposer.py:313-340`:

```python
cad.query_start_loc = self.arange_dflash[: batch_size + 1] * self.num_query_per_req
cad.seq_lens = effective_seq_lens + self.num_query_per_req        # ← +N
if cad._seq_lens_cpu is not None:
    draft_seq_lens_cpu = cad._seq_lens_cpu.clone()
    draft_seq_lens_cpu[:batch_size].add_(self.num_query_per_req) # ← CPU 镜像同幅 +N
    cad._seq_lens_cpu = draft_seq_lens_cpu
    ...
```

其中 `num_query_per_req = num_speculative_tokens`(当 `sample_from_anchor=True`)否则 `1 + num_speculative_tokens`(`dspark_proposer.py:39-43`)。

**v2 里的对应物**:上游 prepare-inputs kernel 里 `out_seq_lens_ptr` 的写入(`vLLM`:`vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:640-648`):

```python
# seq_lens is the absolute sequence length the draft attention
# reads up to (context + query), not just the count of accepted
# tokens this step.
tl.store(out_seq_lens_ptr + req_idx,
         tl.minimum(last_valid_pos + 1 + num_query_per_req, max_model_len))
```

语义一致(已含 query stretch)⇒ **v2 移植时 `future_offset` 同样取 0**。如果错取成 K,窗口末端会多算 N 个 token,窗口整体后移,final 结果与 v1 不一致。

### 4.4 `apply()`(`:149-169`)—— 一次 `apply` 改写 5 个东西

```python
def apply(self, common_attn_metadata):
    self.full_block_table = common_attn_metadata.block_table_tensor   # 保存全量表(供 slot_mapping 用)
    num_reqs = common_attn_metadata.seq_lens.shape[0]
    self.compute_sliding_window_block_table(common_attn_metadata, self._block_table_clone)
    common_attn_metadata.block_table_tensor = self._block_table_clone[:num_reqs]  # ①
    common_attn_metadata.seq_lens = self._windowed_seq_lens                       # ②
    for name in ("seq_lens_cpu", "_seq_lens_cpu", "seq_lens_cpu_upper_bound"):
        src = getattr(common_attn_metadata, name, None)
        if src is not None:
            _windowed = src - ((src + k_future - w).clamp(min=0) // b) * b        # ③④⑤
            setattr(common_attn_metadata, name, _windowed)
```

对应设计文档 `:59-67` 的两条不变式:

- **不变式 1:slot_mapping 永不被裁剪。** draft KV 的写入仍走**全量** block table 的绝对位置,缓存对 target 模型和"运行中改窗口大小"都保持自洽。落点在 `llm_base_proposer.py:2104-2112`:

  ```python
  if self.sliding_window is not None:
      block_table_for_slot = self.sliding_window.full_block_table
  else:
      block_table_for_slot = old_common_metadata.block_table_tensor
  ```

  再往下 `:2118-2123` 用 `clamped_positions // block_size` 取块号算 `slot_mapping`。旁证:inputs kernel 里 query 的 slot 是从 `effective_seq_len + q_idx` 推出的绝对位置(`ops/triton/spec_decode/utils.py:170-190`),而不是从裁剪后的窗口起点推。

- **不变式 2:只有 FIA 会读的 KV-length 被截。** FIA 的 KV length 输入有 NPU `seq_lens` 加三个 CPU 镜像(`seq_lens_cpu`、`_seq_lens_cpu`、`seq_lens_cpu_upper_bound`),`apply()` 把它们用**同一套算式**一起窗口化,"so no path can read past the window"。

  顺带说明:**实际被 metadata 携带的是哪一个张量由 `attention/utils.py:553-587` `_select_seq_lens()` 决定** —— 默认走 CPU 镜像 `_seq_lens_cpu`,但 `parallel_drafting`(DFlash/DSpark)会覆盖成 **NPU `seq_lens`**,唯一例外是 GLM5.2 家族的 DSpark(保留 CPU 镜像以省一次 `seq_lens.tolist()` 同步)。所以对 DSpark 来说,**②(NPU `seq_lens`)才是真正影响 FIA 的那个**,③④⑤ 是配套兜底。这点在 v2 移植时要保持一致:v2 里可能压根没有 `_seq_lens_cpu` 这套镜像,而有 `AscendInputBuffers.seq_lens_cpu` / `seq_lens_np`,见第 8 章。

---

## 5. v1 的两个应用点,以及"DSpark 为什么要单开一处"

### 5.1 应用点 A —— Eagle3 / DFlash(`llm_base_proposer.py:1119-1127`)

```python
if self.draft_window_size is not None and self.method not in ("dspark", "mtp"):
    # DSpark's draft attention reads the per-group block_table assembled
    # in build_draft_attn_metadata (which overwrites this table), so the
    # window is applied there instead. Applying here would window a table
    # that gets discarded and leave seq_lens windowed against an unwindowed
    # table -> FIA reads the oldest blocks. See sw-dspark-flow-analysis.md.
    # MTP is excluded: it reuses the target's own layers, so windowing
    # it would also window the target model.
    self.sliding_window.apply(common_attn_metadata)
```

注意这里在 `_propose` 里,位于"graph padding 之后、模型 forward 之前",且**显式排除 `dspark` 和 `mtp`**。

### 5.2 应用点 B —— DSpark(`llm_base_proposer.py:2588-2610`)

```python
if self.method == "dspark":
    gid = attn_group.kv_cache_group_id
    common_attn_metadata = copy.copy(common_attn_metadata)                      # ① 浅拷贝
    block_table = getattr(self, "_per_group_block_table_buffers", {}).get(gid)
    if block_table is not None:
        common_attn_metadata.block_table_tensor = block_table[: common_attn_metadata.num_reqs]  # ② 换成 per-group 全量表
    slot_mapping = self._per_group_query_slot_mapping_buffers[gid]
    if slot_mapping is not None:
        common_attn_metadata.slot_mapping = slot_mapping[:num_input_tokens]     # ③ per-group query slot_mapping
    # Apply the sliding window to the per-group block_table + seq_lens
    # that DSpark's draft FIA actually reads. This branch overwrites
    # common_attn_metadata.block_table_tensor with the full per-group
    # table, so the window applied earlier (line 922) is bypassed; we
    # skipped it there for dspark and re-apply here on the per-group
    # table so FIA reads the recent-blocks clone instead of block 0.
    # (dspark only - self.sliding_window is None for MTP.)
    if self.sliding_window is not None:
        self.sliding_window.apply(common_attn_metadata)                         # ④ 在 per-group 表上做窗口
    if dcp_manager is not None:
        dcp_manager.prepare_common_attn_metadata(common_attn_metadata)
    attn_metadata = builder.build_for_drafting(
        common_attn_metadata, draft_index=1, **extra_attn_metadata_args)        # ⑤ 之后才建 metadata
```

### 5.3 为什么必须单开一处(把因果讲透)

DSpark 的 KV cache 是**按 kv-cache-group 分开管理**的(`_per_group_block_table_buffers`,在 `dspark_proposer.py:253-256` 每步填充)。`build_draft_attn_metadata` 的 dspark 分支会**用 per-group 全量表覆盖** `common_attn_metadata.block_table_tensor`。

于是:
- 若在应用点 A 就 `apply()`:窗口裁的是那张**随后会被丢弃**的表,但 `seq_lens` 已经被裁了。结果是 `seq_lens`(窗口化)与 block table(全量、块 0 开始)**不一致** → FIA 从**最老的块**开始读,窗口语义完全反向。这就是注释里 "FIA reads the oldest blocks" 那句话的含义。
- 正确做法:左侧(应用点 A)跳过 dspark,在右侧(**per-group 表已就位之后、`build_for_drafting` 之前**)重做一次 `apply()`。

另外两点:
- `copy.copy(cad)`(`:2590`)是**浅拷贝**,所以 `apply()` 对 `cad.seq_lens` / `block_table_tensor` 的**重新绑定**不会泄漏到调用方;而 `_seq_lens_cpu` 等若是原地操作则需注意(本 PR 里是 `setattr` 重绑定,安全)。
- MTP 被排除两次(`:423-429` 只告警不生效,`:1125-1126` 再次排除),原因: MTP 复用 target 自己的层,窗口化 draft 等于窗口化 target。

---

## 6. 配置面

| 位置 | 内容 |
|---|---|
| `vllm_ascend/ascend_config.py:497` | `draft_window_size: int | None = None`(在 `AscendConfig` 里,`extra="forbid"`) |
| `vllm_ascend/ascend_config.py:355` | 默认值 `"draft_window_size": null` |
| `vllm_ascend/spec_decode/llm_base_proposer.py:415` | `self.draft_window_size = get_ascend_config().draft_window_size`(从已验证的配置单例读,不走 `additional_config` 裸读) |
| 用法 | `--additional-config '{"draft_window_size": 2048}'` |
| 字符串强转 | `tests/ut/test_ascend_config.py`(`"4096" -> 4096`) |

已知缺口(写代码/写文档时可以顺手修,但不是本任务主线):

1. **没有正值/下界校验**:`int | None` 裸字段,没有检查 `W > 0`,也没有检查 `W >= draft 模型原生 sliding_window`。设计文档 `:108-111` 明确建议"窗口不要设得比 draft 训练/原生窗口还小,否则会掉接受率",但代码只在 dspark + DeepSeek-V4 target 时给一条 warning(`:430-435`)。
2. `docs/source/user_guide/configuration/additional_config.md` **未收录** `draft_window_size`(而 `dynamic_spec_config` 等兄弟键有)。
3. 设计文档 `speculative_kv_sliding_window.md` **未加入 `mkdocs.yml` 的 nav**,在仓库里只被自己的 `.po` 引用 —— 也就是说它不会出现在文档站上。

---

## 7. MRV2 现状(移植的起点)

### 7.1 抽象换了一套

| | MRV1 | MRV2 |
|---|---|---|
| 抽象名 | **Proposer** | **Speculator** |
| 入口 | `vllm_ascend/spec_decode/dspark_proposer.py` → `AscendDSparkProposer(AscendDflashProposer)` | `vllm_ascend/worker/v2/spec_decode/dspark/speculator.py` → `AscendDSparkSpeculator(DSparkSpeculator)` |
| base 来源 | 本仓库 `spec_decode/llm_base_proposer.py` | 上游 `vllm/v1/worker/gpu/spec_decode/dspark/speculator.py` |
| metadata 载体 | 共享的 `common_attn_metadata`(可原地改) | **没有共享对象** —— 直接算成 per-layer metadata |
| 分派 | `spec_decode/__init__.py:41-70` | `worker/v2/spec_decode/__init__.py:23-72` |
| 开关 | — | 纯 `VLLM_USE_V2_MODEL_RUNNER` 环境变量(`patch/platform/patch_use_v2_model_runner.py:26`),默认 **False**(即默认走 v1) |
| DSpark 图模式 | **eager only**(`dspark_proposer.py:73`) | **FULL ACL graph**(`init_cudagraph_manager`) |

### 7.2 必须看懂的三层 wrapping(移植全靠它)

v2 的 speculator 通过**临时替换上游模块变量**来接入 Ascend 的 attention metadata:

```python
# vllm_ascend/worker/v2/attn_utils.py:1240-1251
_BUILD_ATTN_METADATA_MODULE = vllm.v1.worker.gpu.spec_decode.speculator

@contextmanager
def build_attn_metadata_wrapper():
    """Context manager to override attention metadata building for Ascend NPUs."""
    original_func = _BUILD_ATTN_METADATA_MODULE.build_attn_metadata
    try:
        _BUILD_ATTN_METADATA_MODULE.build_attn_metadata = build_attn_metadata   # ← Ascend 版,attn_utils.py:220-378
        yield
    finally:
        _BUILD_ATTN_METADATA_MODULE.build_attn_metadata = original_func
```

```python
# vllm_ascend/worker/v2/attn_utils.py:1254-1281
def build_draft_attn_metadata_factory(positions, pad, is_prefilling, seq_lens_cpu=None, *, attn_state=None, parallel_config=None):
    """Wrap build_attn_metadata with Ascend draft-model context."""
    raw = _BUILD_ATTN_METADATA_MODULE.build_attn_metadata
    def build_attn_metadata(*args, **kwargs):
        kwargs["positions"] = positions[:pad]
        kwargs["is_prefilling"] = is_prefilling
        kwargs["attn_state"] = attn_state
        kwargs["parallel_config"] = parallel_config
        if seq_lens_cpu is not None:
            kwargs["seq_lens_np"] = seq_lens_cpu.numpy()
        return raw(*args, **kwargs)
    ...
```

两层的叠加顺序:`build_attn_metadata_wrapper()` 先装 Ascend 版,`build_draft_attn_metadata_factory()` 再在它外面包一层注入 Ascend 特有参数(注释里明确要求**必须**在 wrapper 内部使用)。

`AscendDSparkSpeculator` 里两处进入这个上下文:

- `build_draft_attn_metadatas()`(`speculator.py:153-186`)—— 图捕获/批处理用
- `_build_draft_attn_metadata()`(`:188-268`)—— 兼容旧 hook 名的转发入口
- `_build_uniform_attn_metadata()`(`:270-304`)—— 重建 `actual_seq_lengths_q` 以适配 FIA 的 TND 布局要求
- `propose()`(`:316-371`)—— 把整套上下文包在上游 `super().propose()` 外面

### 7.3 **唯一可改的面**:上游 `_build_attn_metadata` 读什么

上游 `vllm/v1/worker/gpu/spec_decode/speculator.py:295-369`:

```python
block_tables = [x[:num_reqs_padded] for x in self.block_tables.input_block_tables]     # :322-324
slot_mappings = self.block_tables.slot_mappings[:, :num_tokens]                        # :325
draft_seq_lens_cpu_upper_bound = torch.zeros(num_reqs_padded, dtype=torch.int32, device="cpu")
torch.add(seq_lens_cpu_upper_bound[:num_reqs], step,
          out=draft_seq_lens_cpu_upper_bound[:num_reqs])                               # :326-334
draft_seq_lens_cpu_upper_bound[:num_reqs].clamp_(max=self.max_model_len)
...
attn_metadata = build_attn_metadata(                                                  # :346(已被 ascend 版替换)
    ...,
    seq_lens=self.input_buffers.seq_lens[:num_reqs_padded],                           # :355  ← 窗口要改的 NPU seq_lens
    block_tables=block_tables,                                                        # :362  ← 窗口要改的 block table
    slot_mappings=slot_mappings,                                                      # :363  ← 绝对不许动
    seq_lens_cpu_upper_bound=draft_seq_lens_cpu_upper_bound,                          # :366  ← 还要截的 CPU upper bound
    is_prefilling=self.draft_is_prefilling[:num_reqs_padded],
)
```

**这四个输入就是设计文档所说的 "builder inputs"**,也就是移植的全部改动面。

### 7.4 Ascend 侧的两个差异点

- **`AscendBlockTables`**(`worker/v2/block_table.py`):`input_block_tables` 来自上游基类(每 group 一个 `[max_num_reqs, max_num_blocks]` int32 device tensor);Ascend 额外维护 `block_table_ptrs` / `block_table_strides` 给 triton 的 slot-mapping kernel 用。**关键点**:`slot_mappings` 由 `compute_slot_mappings()`(`:82-114`)从**全量** block table 独立算出,与 attention metadata 解耦 —— 也就是说 **MRV2 天然满足"slot_mapping 不裁剪"这条不变式**,你不需要像 v1 那样专门保留 `full_block_table` 给 slot 用。
- **`AscendInputBuffers`**(`worker/v2/input_batch.py:55-62`):比上游多了 `seq_lens_cpu`(int32, **CPU**)和 `seq_lens_np`(与前者共享内存的 numpy 视图)。这就是 v2 里用来替代 v1 三个 host mirror 的东西。

---

## 8. v1 → v2 适配落点(照这张表改代码)

### 8.1 映射表

| # | v1 改的东西(位置) | v2 对应物(位置) | 落点 / 注意 |
|---|---|---|---|
| 1 | `common_attn_metadata.block_table_tensor` 换成裁过的 clone(`utils.py:160`) | `self.block_tables.input_block_tables[g]`(`input_batch` 上游 `block_table.py:73`) | 必须在上游 `_build_attn_metadata:322-324` **读到之前**改;需要 **per-group 持久 clone buffer**(对应 v1 的 `_block_table_clone`),因为 v2 走 FULL graph、地址必须 capture/replay 一致 |
| 2 | `common_attn_metadata.seq_lens`(NPU,`utils.py:163`) | draft `self.input_buffers.seq_lens`(上游 `:355` 读) | **同一 buffer 每步复用**,所以要在 `_build_attn_metadata` 之前改写、之后**还原**(或改成"只写进 per-layer metadata,不还原"),否则会污染后续步骤 |
| 3 | `seq_lens_cpu` / `_seq_lens_cpu`(`utils.py:165-169`) | `self.input_buffers.seq_lens_cpu` / `seq_lens_np`(`AscendInputBuffers:55-62`) | 同幅截断;注意 v2 里 `seq_lens_np` 才是 builder 真正拿到的(`build_draft_attn_metadata_factory` 里 `kwargs["seq_lens_np"] = seq_lens_cpu.numpy()`) |
| 4 | `seq_lens_cpu_upper_bound`(`utils.py:165-169`) | `draft_seq_lens_cpu_upper_bound`(上游 `:326-334` 里现算的局部变量) | 它在函数内部构造,**无法从外面改**,所以要么在 Ascend 覆盖版 `_build_attn_metadata` 里重算/截断,要么绕开上游实现自己组 kwargs |
| 5 | `get_ascend_config().draft_window_size`(`llm_base_proposer.py:415`) | 同名字段已存在(`ascend_config.py:497`) | v2 目前**静默忽略**该配置(不报错、不告警)。要在 `AscendDSparkSpeculator.__init__` 里读取并构造 adapter,否则用户以为生效了其实没有 |
| 6 | `SlidingWindowAdapter` 本体(`spec_decode/utils.py:83-169`) | 可直接复用 / 或抽出"纯张量版" | 它内部只依赖"一个带 `seq_lens` / `block_table_tensor` 的鸭子类型对象"(`apply` 用 `getattr` 逐字段探),v2 里没有 `common_attn_metadata`,**建议抽出纯张量函数**(输入 `seq_lens` + `block_table` + 输出 buffer,返回 `windowed_seq_lens` / `windowed_block_table`),再让 v1 的类去调它 —— 这样两份实现不会漂移 |

### 8.2 落点位置(对照设计文档 `MRV2 status` 那句话)

设计文档原文说落在 "around the `_build_draft_attn_metadata` call in `vllm_ascend/worker/v2/spec_decode/dspark/speculator.py`"。展开成 v2 的具体位置:

```text
AscendDSparkSpeculator.build_draft_attn_metadatas()            speculator.py:153-186
 ├─ self._prepare_draft_dcp_metadata_inputs(...)               :156  (DCP 时才有 seq_lens_cpu)
 ├─ with build_attn_metadata_wrapper(), build_draft_attn_metadata_factory(...):  ← 上下文入口 :159-169
 ├─ self._build_uniform_attn_metadata(..., causal=self._group_causal)          :177-184
 │   └─ super()._build_uniform_attn_metadata()                 上游 speculator.py:514-533
 │       └─ self._build_attn_metadata()                        上游 :295-369
 │           ├─ block_tables = [... input_block_tables ...]    :322-324   ← ★ 落点 1(裁 clone)
 │           ├─ self.input_buffers.seq_lens                    :355       ← ★ 落点 2(NPU 窗口化)
 │           ├─ draft_seq_lens_cpu_upper_bound                 :326-334   ← ★ 落点 3(截断)
 │           └─ build_attn_metadata(...)  ← 被替换成 Ascend 版  :346
 └─ (BuildAttnMetadata)  → Ascend builder.build()  attn_utils.py:367-371
```

因为落点 1/2/3 都在**上游函数体内**,两种可行做法:

- **做法甲(推荐,改动最小)**:在 `AscendDSparkSpeculator` 里重写 `_build_attn_metadata`,先按上游逻辑算出 `block_tables` / `draft_seq_lens_cpu_upper_bound`,插入窗口化,再调用 Ascend 版 `build_attn_metadata`。缺点是复制了一段上游逻辑,需要跟随上游 PR 维护(参考 `autoregressive/speculator.py:611` 已有的同类覆盖写法)。
- **做法乙**:在 `_build_uniform_attn_metadata` / `build_draft_attn_metadatas` 这一层先把 `self.input_buffers.seq_lens` 和 per-group block-table clone 改好再进 super(),并额外处理 `draft_seq_lens_cpu_upper_bound`(它内部现算,需要另想办法,例如在 Ascend `build_attn_metadata` 内部再截一次 —— 它已经有 `seq_lens_cpu_upper_bound` 这个入参,见 `attn_utils.py:238`)。

### 8.3 不变式在 v2 怎么保持

- **slot_mapping 不裁剪**:v2 里**不用管** —— `AscendBlockTables.compute_slot_mappings` 从全量 block table 算完再作为 `slot_mappings` 传进 metadata,**不要**去 `apply` 它。
- **只截 FIA 会读的 KV-length**:v2 里要覆盖 `input_buffers.seq_lens`(NPU)+ `seq_lens_cpu` / `seq_lens_np` + `draft_seq_lens_cpu_upper_bound` 三处。

### 8.4 移植的**主要技术难点**:ACL graph 下的地址稳定性

这一点必须先想清楚,否则代码能跑但不一定对:

1. v1 的 DSpark 是 **eager only**(`dspark_proposer.py:73` `use_cuda_graph = False`),所以 v1 里 `SlidingWindowAdapter` 只要"持久 buffer 复用"就够。
2. v2 的 DSpark 走 **FULL ACL graph**(`AscendDSparkSpeculator.init_cudagraph_manager` → `self.query_cudagraph_manager.speculator = self`),capture 时冻结张量地址。因此:
   - per-group 窗口化 block table **必须是预分配的持久 buffer**(每个 group 一个),在 capture 前分配好、replay 时只做 `copy_` / `gather` 写入;不能每步 `torch.gather` 出新张量。
   - 参考仓库里已有的同类处理:`dsa_v1.py:491-501`(`buffer` 参数 + 注释 "ACL graph capture freezes tensor addresses")与 `dsa_v1.py:639-652`(`dspark_swa_indices_buffer` 持久化)。
3. 由此推出一条实现约束:**adapter 需要按 kv-cache-group 各持一份 clone**,数量在 `set_attn()`(`speculator.py:94-135`)拿到 `kv_cache_config.kv_cache_groups` 之后才能确定,所以 buffer 分配要放在 `set_attn` 之后。

---

## 9. 已知坑与注意点(读代码时会撞上)

1. **悬空文档引用**:`llm_base_proposer.py:1124` 和 `:2602` 里提到的 `sw-dspark-flow-analysis.md` **不在仓库中**(全仓 `find` 无结果)。别去找,理解上面第 5.3 节的推理就够。
2. **过期行号**:`llm_base_proposer.py:2600` 注释写 "the window applied earlier (line 922)",真实跳过点在 `:1119`(line 922 是 `dummy_run` 里的代码)。
3. **注释与代码不一致(无害)**:`utils.py:136` 注释说列网格是 `[1, max_window_blocks]`,但 `torch.arange(self.max_window_blocks)` 是 **0 基**。代码自洽(`valid_mask` / `needed` 都按 0 基写),只有注释错 —— 若照注释理解会以为漏了第一个块。上界仍然是够的:`max_window_blocks = ceil(W/b) + 1 >= ceil((W + b - 1)/b)`。
4. **`full_block_table` 是可变 side-channel**:`utils.py:153` 每次 `apply` 都重新绑定。dspark 分支里它是**按 group 循环**被覆盖的(`:2578-2610`),循环结束后指向**最后一个 group** 的表。当前唯一读者(`:2109-2112`)在 dspark 路径上不会执行到,所以现在没出问题;但如果以后有人在 dspark 路径上读 `sliding_window.full_block_table`,会拿到错的 group。
5. **draft step ≥ 2 时窗口不会重新对齐**:`attn_update_stack_num_spec_norm`(`:1952-2115`)只对**已窗口化**的 `seq_lens` 做自增、并复用**已裁剪**的 block table(在 `:1187-1198` 处 clone 过一次,该段注释写的就是 "Clone the data so that ... it does not affect position 1"),**不会重跑块对齐的窗口数学**。结果是:FIA 侧自洽(KV length 与 block table 同步),但窗口起点会随拒绝采样的修正量漂移几个 token,窗口尾部的块在后面的 draft step 可能读不到。**v2 移植时要明确这是不是期望语义** —— 如果期望是"每个 draft step 都看到最新的 W 个 token",v1 这里就需要重新对齐(或者说这是一个潜在缺陷)。
6. **v1 DSpark 是 eager only;v2 是 FULL graph** —— 见 8.4,这是移植难度的主要来源。
7. **v2 下 `draft_window_size` 静默失效**:不报错、不告警。移植时顺手加一条 warning(至少在 `VLLM_USE_V2_MODEL_RUNNER=1` 且该配置非空时提示)会省掉很多 debug 时间。

---

## 10. 怎么自测

### 10.1 v1(理解校验 / 回归对照)

```bash
# 单测:窗口数学 + 四个 host mirror 一起被窗口化
pytest -sv tests/ut/spec_decode/test_utils.py

# 单测:adapter 的 apply 行为(含 block table clone 地址不变的断言)
pytest -sv tests/ut/spec_decode/test_eagle_proposer.py::TestSlidingWindowAdapter

# 单测:proposer 里 adapter 的构造参数
pytest -sv tests/ut/spec_decode/test_llm_base_proposer.py
```

```bash
# 端到端:greedy 逐位置接受率对拍 golden(W=512,prompt 长于窗口)
pytest -sv tests/e2e/pull_request/one_card/spec_decode/test_dspark.py::test_dspark_kv_sliding_window
# Eagle3 的对应 e2e
pytest -sv tests/e2e/pull_request/two_card/spec_decode/test_spec_decode.py::test_eagle3_sliding_window
```

验收基线在 `tests/e2e/pull_request/one_card/spec_decode/utils.py:43-49`:

```python
"dspark":                 [1.0,  0.8,  0.6,  0.6,  0.6,  0.6,  0.6],
"dspark_dynamic":         [0.68, 0.54, 0.46, 0.38, 0.22, 0.11, 0.11],
"dspark_sliding_window":  [0.88, 0.88, 0.88, 0.88, 0.75, 0.75, 0.62],
```

有意思的一点:窗口把 pos 3-6 的接受率**抬到高于无窗口基线**(`0.75/0.75/0.62` vs `0.6/0.6/0.6`),因为单 block 的 DSpark drafter 本来就依赖最近上下文。这也解释了为什么"窗口"有时是增益、有时是损失(见设计文档 `:101-113` 的 expected behavior)。

### 10.2 v2 该补什么

1. **纯张量层的 UT**(不依赖 NPU):窗口数学 + `needs` / `valid_mask` 的边界(seq_lens < W、seq_lens 恰好 = W、跨 `max_window_blocks` 上限、`src_cols` 越界)。
2. **metadata 一致性断言**:`seq_lens` / `block_table` / `seq_lens_cpu_upper_bound` 三者被**同幅**截断,而 `slot_mappings` **逐元素不变**(这是第 2 条不变式的可测形式)。
3. **图模式回归**:至少一次 `VLLM_USE_V2_MODEL_RUNNER=1` 下的 DSpark + `draft_window_size` 端到端接受率对拍(可复用 `test_dspark_kv_sliding_window` 的 golden)。
4. **配置生效性测试**:v2 下设置 `draft_window_size` 而 speculator 未接线时,要么报错要么告警(对应第 9 章第 7 条)。

---

## 11. 一句话总结

`draft_window_size` 的本质是**只改 draft 模型能读到的 KV 范围**(块对齐的最近 W 个 token),target 模型完全不动;它的实现约束只有两条 —— **slot_mapping 永远走全量 block table**、**所有 FIA 会读的 KV-length 用同一套算式截断**。MRV1 用 `SlidingWindowAdapter` 原地改写共享的 `common_attn_metadata`(DSpark 因为 per-group 表覆盖,必须把应用点挪到 `build_for_drafting` 之前);MRV2 没有这个共享对象,所以要把同一套窗口数学施加到 `_build_attn_metadata` 的四个 builder inputs 上,并且必须满足 ACL graph 的地址稳定性要求。
