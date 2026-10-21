# MRV2 Draft Window P1：Policy + Pure Math + Types 实现说明

## 文档状态

- 权威设计：`MRV2_Speculative_Draft_Sliding_Window_Final_Design.md`
- 实施计划：`MRV2_Draft_Window_Implementation_Plan.md`
- vLLM 基线：`84030bbe3d74d99bad477a3d2e37a973ccd8865c`
- vLLM-Ascend 实施父提交：`841dc6ccdb134eab7ad09008859834d0572ee83f`
- P1/C1 提交：`b12399ad915415ce45105df5b0601848e7b70f6f`
- C1 标题：`feat(spec-decode): add MRV2 draft-window policy and math`
- P1 Review-fix 提交：`c58daea0df34d1a6253dc34221d2a084b13affd5`
- Review-fix 标题：`fix(spec-decode): address P1 draft-window review findings`
- 当前结论：`P1 FINAL: PASS`；P2 尚未开始，等待用户确认。

这份说明只解释 P1。凡是涉及真实 Attention、KV read view、NPU、Graph、workspace、
lease 或 metadata store 的内容，都不是本提交已经支持的能力。

## 1. P1 解决的问题

### 1.1 为什么不能直接裁 block table

`draft_window_size` 不是“看到一个整数就把 block table 左边删掉”这么简单。MRV2 的
Target 与 Draft 共享多条基础设施：full block table、绝对 position、slot mapping、
metadata builder 和 Graph 路径。若先裁表再补规则，很容易同时发生以下错误：

- MTP 复用 Target layer，Draft Window 会误伤 Target full-context 语义；
- DeepSeek-V4 co-trained DSpark 本应按产品策略 forced OFF，却可能先因 `W=-1` 报数值错；
- 把 read table 与 write slot 一起改掉，KV 写入位置不再是绝对地址；
- plain Eagle、dynamic-K、DFlash2 或尚未验证 backend 因共享 class 而被误当成已通过
  runtime capability Gate；DFlash2 继承 P1 policy receiver 本身不是 runtime support；
- P2/P3 尚未建立 ownership/lifetime 时，临时 tensor 可能被 Graph 或异步 reader 继续引用。

因此 P1 先建立“谁有资格进入 Window 路径”的唯一入口，并保证任何真实数据面改动发生
在它之后。

### 1.2 为什么先有 Policy

Policy 把“配置存在”与“功能可进入”分开：

- `CONFIG_OFF`：用户没有请求 Window，必须完全保持 baseline；
- `FORCED_OFF`：用户配置了 W，但该 method/model 按 Frozen 产品策略必须回到 baseline；
- `ELIGIBLE_ON`：只表示可以继续做数值与后续 capability Gate，不表示 Attention 已支持。

这三个状态使 forced-OFF precedence 可以测试，而不是散落在多个 speculator 的 if 分支中。

### 1.3 为什么先有纯数学

Window 的 anchor、exact visible length、capacity 与 block projection 都是整数语义。先把它们
做成无 Torch、无 NPU、无 mutable runtime state 的 pure functions，有三个好处：

1. 可用硬编码整数 oracle 在 CPU 上验证边界；
2. P2 provider、P3 workspace 和 P4 Attention 使用同一公式，不各写一份；
3. 数学错误与 backend/Graph/lifetime 错误可以分层定位。

### 1.4 为什么需要 typed value objects

裸 tuple 如 `(3584, 512, 527)` 无法告诉读者三个数分别是 anchor、exact length 还是容量。
P1 用 frozen dataclass 表达 full/window/policy 语义，使字段名成为契约，也阻止后续阶段原地
改写 P1 决策。

## 2. P1 不解决的问题

P1 没有做以下任何事情：

- Attention 尚未读取 Window；
- KV visibility 尚未改变；
- 没有真实 Window tensor、裁剪后的 block table 或 valid-count tensor；
- 没有修改 `seq_lens`、`slot_mapping`、positions、query layout；
- 没有修改 Target metadata、Target store 或 Target logits；
- 没有 persistent workspace、lease、event retirement 或 `DraftMetadataStore`；
- 没有 Graph capture/replay hook；
- 没有打开 Async、prefix cache、function/chunked prefill、parallel、MLA、DSA、SFA、
  recycling、heterogeneous multi-group 或 DFlash2；
- 没有 NPU Window ON，也没有 NPU runtime correctness 结论；
- 没有修改 MRV1 `SlidingWindowAdapter`、Scheduler 或 KV allocation。

P1 的 `ELIGIBLE_ON` 是“允许继续做后续 Gate”的资格，不是“功能已经生效”。

## 3. 修改文件总览

| File | Class/Function | Before | After | Why |
|---|---|---|---|---|
| `vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window.py` | policy enum、frozen dataclass、pure functions | 文件不存在 | 新增 3 类 policy/scalar 类型、1 个 projection 类型和纯函数 | 给 P2–P4 一个唯一、无设备依赖的语义源 |
| `vllm-ascend/vllm_ascend/worker/v2/spec_decode/__init__.py` | `init_speculator()` | 直接按 method dispatch | 先 resolve policy；baseline body 原样提取到 `_init_speculator_baseline()` | 保证 OFF parity 与 forced-OFF precedence |
| 同上 | `_configure_eligible_draft_window()` | 不存在 | 将 frozen decision 交给 eligible owner | 不改 constructor/MRO，不创建 runtime Window |
| `vllm-ascend/vllm_ascend/worker/v2/spec_decode/autoregressive/speculator.py` | `AscendAutoRegressiveSpeculator._configure_draft_window()` | 不存在 | 一次性保存 eligible decision | Eagle3 的 instance-scoped P1 接收点；MTP/plain Eagle 不可达 |
| `vllm-ascend/vllm_ascend/worker/v2/spec_decode/dflash/speculator.py` | `AscendDFlashSpeculator._configure_draft_window()` | 不存在 | 一次性保存 eligible decision | DFlash 的 P1 接收点；DFlash2 仅继承方法，不代表能力开放 |
| `vllm-ascend/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py` | `AscendDSparkSpeculator._configure_draft_window()` | 不存在 | 一次性保存 eligible decision | eligible 非 DeepSeek-V4 DSpark 的 P1 接收点 |
| `vllm-ascend/tests/ut/spec_decode/test_draft_window.py` | 34 个 test functions，参数化后 75 个 cases | 文件不存在 | 新增 policy/order/baseline/owner/math/projection contracts，并补齐 Review regression | test-first 固化 P1 边界与整数 oracle |
| `vllm-ascend/tests/ut/spec_decode/test_dflash2_v2.py` | factory/MRO tests | factory 测试不提供 AscendConfig | 显式 Window OFF，并区分 receiver/policy contract 与 runtime enablement | 新 policy 入口下仍保持 DFlash/DFlash2 baseline dispatch |
| `vllm-ascend/tests/ut/worker/test_extract_hidden_states_speculator_v2.py` | dispatch test | factory 测试不提供 AscendConfig | 显式 Window OFF | 证明非 Window route 的既有 dispatch 不变 |

没有修改 upstream vLLM。新增生产文件位于 MRV2 Ascend worker 内部包，不在
`vllm_ascend` 顶层导出，因此不是新的用户 public API。

## 4. 修改前执行流程

```text
VllmConfig.speculative_config
        |
        v
MRV2 Ascend init_speculator()
        |
        +-- extract_hidden_states
        +-- DSpark
        +-- DFlash / DFlash2
        +-- ordinary MTP
        `-- use_eagle() fallback
                |
                v
        existing speculator instance
```

这里没有 MRV2 `draft_window_size` policy。factory 只负责既有 class dispatch。

## 5. 修改后执行流程

```text
AscendConfig.draft_window_size
        |
        v
normalize method + target hf_config.model_type
        |
        v
resolve_draft_window_policy()
        |
        +-- CONFIG_OFF ----------------------> existing baseline factory
        |
        +-- FORCED_OFF -> baseline ----------> per-created-speculator warning
        |
        `-- ELIGIBLE_ON
                |
                v
        resolve static method horizon
                |
                v
        numeric validation / dynamic-K Gate
                |
                v
        existing baseline factory
                |
                v
        attach immutable policy decision once

Later P2/P3/P4 code may call the pure scalar planner.
P1 factory 本身没有 request length/block span，因此不会虚构一个 runtime plan。

              这里仍未进入 Attention
```

关键点是 `_init_speculator_baseline()` 中的分支顺序和 constructor 参数与父提交相同。
新增代码包在它外面，而不是重写各 method 的主要执行流程。这就是“在现有流程中增量接线”
的具体实现。

## 6. Policy 详细解释

### Example A：`draft_window_size=None`

输入：method 可以是 MTP、plain Eagle、Eagle3、DFlash 或 DSpark。

结果：`CONFIG_OFF`。factory 立即调用 `_init_speculator_baseline()`；不做 eligible 数值
校验、不 warning、不调用 owner receiver，也不创建 `_draft_window_policy` 属性。plain Eagle
在 OFF 时仍正常走原 baseline，并不会因为它的 Window ON 契约未开放而报错。

### Example B：MTP + `W=512`

结果：`FORCED_OFF(reason="mtp")`。factory 先验证 reason，成功构造原 MTP baseline
speculator，然后在该唯一构造入口发一次普通 warning。不能使用
`logger.warning_once()`，因为它通过进程级 LRU cache 去重，会吞掉同进程内后续
engine/speculator 实例应收到的 warning。原因是 MTP 复用 Target layer，不能把 Draft
read window 与 Target full context 安全分开。

### Example C：MTP + `W=-1`

结果仍然先是 `FORCED_OFF`，不是 `ValueError`。`-1` 不会进入
`validate_eligible_window_numbers()`。这是 policy precedence 的核心：forced-OFF 是
method/product contract，不能被一个对该 route 根本不会生效的数值校验抢先。

### Example D：DeepSeek-V4 co-trained DSpark + `W=512`

factory 从 Target `model_config.hf_config.model_type` 读取并 normalize identity；明确的
`deepseek_v4*` family（包括当前源码中的 `deepseek_v4` 与 `deepseek_v41`）与 DSpark
组合得到 `FORCED_OFF(reason="deepseek_v4_cotrained_dspark")`，成功创建 baseline 后按
engine/speculator 实例 warning 一次。识别依据不是 Python class 名或 draft model 名。

### Example E：DFlash / Eagle3 / eligible DSpark + `W=512`

结果先是 `ELIGIBLE_ON`：

- Eagle3 static K：future offset 是 configured K；
- DFlash / DSpark：future offset 是 0；
- dynamic-K 立即 `NotImplementedError`；
- `W<=0` 或 Eagle3 `W<K` 按 interim contract fail closed；
- valid values 通过后构造原 speculator，再保存一份 frozen policy decision。

`ELIGIBLE_ON` 不代表 Feature 已真正支持。P1 没有让任何 backend 看见 Window table 或
Window length；P2 inventory、P3 lifetime、P4 read-plane integration 仍未实现。

## 7. 新增 Enum / Dataclass

源码导航：
`vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window.py:14-58`。

### 7.1 `DraftWindowPolicyState`

| Value | 人话含义 |
|---|---|
| `CONFIG_OFF` | 用户没有配置 W；完全不进入 Window 基础设施 |
| `FORCED_OFF` | 用户配置了 W，但 method/model 策略要求忽略它并回到 baseline |
| `ELIGIBLE_ON` | policy 允许继续过 numeric/capability/runtime Gates；尚未启用 Attention Window |

创建者是 `resolve_draft_window_policy()`；factory 消费它；生命周期只覆盖 config/factory
decision，随后 eligible owner 持有对应 frozen decision。

### 7.2 `DraftWindowPolicyDecision`

| Field | 物理/产品含义 |
|---|---|
| `state` | 上表三个 policy 状态之一 |
| `requested_window_size` | 用户原始请求；`None` 是唯一 OFF 表达，invalid 数值也原样保留供诊断 |
| `effective_window_size` | 只有 `ELIGIBLE_ON` 才非 `None`；forced OFF 明确没有 effective W |
| `normalized_method` | trim/lower 后的 method identity，例如 `eagle3` |
| `target_model_type` | normalize 后的 Target `hf_config.model_type`，不是 draft class 名 |
| `reason` | forced-OFF 的机器可判别原因；当前是 `mtp` 或 `deepseek_v4_cotrained_dspark` |

它由 policy resolver 创建，由 factory、三个 private owner receiver 与未来 inventory Gate
消费。`frozen=True, slots=True` 防止后续阶段把同一个决策对象原地改成另一种策略。

### 7.3 `DraftWindowScalarPlan`

| Field | 含义 |
|---|---|
| `full_exact_end` | 当前真实绝对 end `E`；不是 planning upper |
| `full_horizon_end` | method horizon `H=E+K` |
| `window_start` | Frozen legacy block-aligned anchor `S` |
| `window_visible_length` | 当前 exact read length `V=E-S` |
| `window_capacity_tokens` | workspace/layout 上界 `W+B-1`；不是本轮实际 read length |

它由 pure planner 创建。P1 tests 消费；未来 P2 provider/P3 workspace 使用，但它不持有
Tensor、Target object 或 mutable block table。

### 7.4 `DirectPrefixProjection`

| Field | 含义 |
|---|---|
| `source_start_column` | 绝对 anchor 落在 source row 的起始列 `floor(S/span)` |
| `first_token_offset` | anchor 在首列内的 token offset `S mod span` |
| `required_columns` | 覆盖 exact `V` 所需列数；`V=0` 时为 0 |
| `safe_extent_tokens` | 从真实 first token 起，这些列可安全表达的 token extent |
| `source_end_column` | property；exclusive `start + required` |

它只描述 projection；不拥有 source/destination tensor。P2 provider 必须再证明 operator 能
消费非零 offset，不能看到这个对象就默认 backend 已支持。

## 8. 新增 pure functions

全部位于
`vllm-ascend/vllm_ascend/worker/v2/spec_decode/draft_window.py`，不导入 Torch/NPU。

| Function | Input -> Output | 调用者与存在理由 | 简例 |
|---|---|---|---|
| `_normalize_method()` | raw method -> lowercase/trim string | policy private helper；避免大小写/空格造成分叉 | `" DSPARK " -> "dspark"` |
| `_normalize_model_type()` | raw model type -> trim/lowercase，保留 separator | policy private helper；统一 canonical case，但不发明 MRV1 predicate 原本不匹配的 identity | `"DeepSeek-V4" -> "deepseek-v4"` |
| `_is_deepseek_v4_target()` | normalized model type -> bool | 只按明确 Target `hf_config.model_type` family 识别 forced-OFF route | `deepseek_v41 -> True` |
| `resolve_draft_window_policy()` | requested W + method + target type -> frozen decision | factory 在任何 eligible numeric/runtime 工作前调用 | MTP + `-1 -> FORCED_OFF` |
| `resolve_static_future_offset()` | normalized method + configured K + dynamic flag -> K/0 或错误 | 冻结 Eagle3 与 DFlash/DSpark horizon；dynamic-K 不猜 | Eagle3 K=3 -> 3；DFlash -> 0 |
| `validate_eligible_window_numbers()` | W + future offset -> `None` 或 `ValueError` | 只允许 eligible route 调用；实现 interim fail-closed contract | W=2,K=3 -> error |
| `compute_legacy_anchor()` | `E,K,W,B -> S` | 复用 MRV1 Frozen anchor，禁止 LCM | `4096,3,512,16 -> 3584` |
| `compute_visible_length()` | `E,S -> V` | 独立检查 `S<=E`，避免负 read length | `4096,3584 -> 512` |
| `compute_window_capacity_tokens()` | `W,B -> W+B-1` | exact 与 allocation capacity 分离 | `512,16 -> 527` |
| `compute_draft_window_scalar_plan()` | exact scalars -> frozen plan | 聚合上述公式；未来 request-level planner 的核心 | 上例得到 `S=3584,V=512,C=527` |
| `project_direct_prefix()` | `S,V,span -> projection` | 保持同一绝对 anchor，按 consumer span 投影；不重对齐 | `S=63,V=64,span=64 -> start=0,offset=63,needed=2` |
| `compute_direct_prefix_capacity()` | `W,B,span -> columns` | 仅用于默认 `span ∣ B` 的 zero-offset geometry；否则立即拒绝；P2 仍要做 capability proof | `W=100,B=64,span=64 -> 3` |

这些函数的异常也是 contract：负 exact length、非正 block/span、negative visible interval、
dynamic-K 与 unsupported method 都 fail closed，不 clamp、不猜测。

## 9. Window 数学

### 9.1 完整数值例子

给定：

```text
W = 512
E = L0 = 4096
K = 3
B = 16
```

Eagle3 static-K 的步骤：

```text
H = E + K
  = 4096 + 3
  = 4099

raw_start = max(H - W, 0)
          = max(4099 - 512, 0)
          = 3587

S = B * floor(raw_start / B)
  = 16 * floor(3587 / 16)
  = 16 * 224
  = 3584

V = E - S
  = 4096 - 3584
  = 512

capacity = W + B - 1
         = 512 + 16 - 1
         = 527
```

若 direct-prefix consumer 的 `span=16`：

```text
start_col = floor(3584 / 16) = 224
offset    = 3584 mod 16       = 0
needed    = ceil((0 + 512) / 16) = 32
safe_extent = 32 * 16 - 0 = 512
```

这里的 527 是跨所有 block residue 的 token capacity 上界，512 是本轮 exact visible
length；两者不能混用。

### 9.2 Short-context 例子

`E=100,K=3,W=128,B=64`：`H=103<=W`，因此 `raw_start=0`、`S=0`、
`V=100`。短上下文保留全部历史，不为了“凑 W”制造负起点。

### 9.3 `K=0` 例子

DFlash/DSpark：`E=130,K=0,W=64,B=64`。

```text
H=130
raw_start=66
S=64
V=66
capacity=127
```

`V` 可以大于 W，因为 anchor 向左对齐到 legacy block boundary；这正是 `W+B-1`
capacity slack 存在的原因。

### 9.4 Exact block boundary

`E=189,K=3,W=64,B=64`：`H-W=128` 正好在 block boundary，故 `S=128`、
`V=61`。

### 9.5 Non-block boundary

`E=190,K=3,W=64,B=64`：`H-W=129`，向下按 B 对齐后仍是 `S=128`，
`V=62`。不能向上对齐，否则可能出现 `S>E`。

### 9.6 为什么不是 LCM alignment

`E=1000,K=0,W=128,B=64`：Frozen 公式给 `raw_start=872`、`S=832`。若错误地按
`lcm(W,B)=128` 对齐会得到 768，改变 MRV1 Frozen anchor 和可见集合。UT 对 832 使用
硬编码 oracle，防止未来“优化”成 LCM。

### 9.7 Pointwise `W<K` 与配置 Gate

纯数学允许研究任意整数，例如 `E=100,K=4,W=3,B=64` 仍得到 `S=64,V=36`；但
产品 contract 尚未批准 `W<K`。因此 factory 的 eligible numeric Gate 仍统一拒绝
Eagle3 `W<K`。数学事实与产品 enablement 是两层，不应通过删掉数学 case 来混为一谈。

### 9.8 Zero-offset capacity 的 geometry 前提

`compute_direct_prefix_capacity()` 是默认 direct-prefix provider 的容量函数，不是通用
offset-aware 容量函数。它要求 `block_span_tokens ∣ legacy_block_size`，从而保证所有按
legacy B 对齐的 anchor 也按 span 对齐。

反例：`W=32,B=16,span=48,S=64,V=47`。此时 `offset=16`，真实需要
`ceil((16+47)/48)=2` 列；若错误套用 zero-offset 公式，只会得到
`ceil((32+16-1)/48)=1` 列。P1 现在对该 geometry 直接 `ValueError`；P2 在没有
offset-aware provider/operator proof 前必须继续 fail closed。

## 10. Factory / Speculator 发生了什么改变

### 10.1 Policy 在哪里解析

`vllm-ascend/vllm_ascend/worker/v2/spec_decode/__init__.py:41` 的
`init_speculator()` 先从已验证的 AscendConfig singleton 读取 W，再读取
`speculative_config.method` 与 Target `hf_config.model_type`。policy resolution 位于
任何 speculator class dispatch 之前。

这是显式 lifecycle precondition：正常 serving 中，`AscendPlatform.check_and_update_config()`
在 `platform.py:455-509` 初始化 singleton，worker 在 `worker.py:149` 再初始化，随后
`NPUModelRunner.__init__()` 在 `model_runner.py:96` 先读取 singleton、在 `:149` 调用
factory。直接单测或 standalone caller 必须先初始化或 mock `get_ascend_config()`。

### 10.2 为什么必须早于 class dispatch / Window allocation

MTP 的特殊 Gemma4/Step3.5 route 会落入 `use_eagle()` class fallback；若靠 class
类型判断，会把它误当 Eagle eligible。按 normalized method 在 dispatch 前决策，所有 MTP
变体都一致 forced OFF。DeepSeek-V4 DSpark 同理，必须在未来 inventory/planner/workspace
入口之前返回。

### 10.3 OFF 如何保持 baseline

父提交中 `init_speculator()` 的原 body 被逐分支提取为
`_init_speculator_baseline()`，顺序仍是：

```text
extract -> DSpark -> DFlash/DFlash2 -> ordinary MTP -> use_eagle
```

`CONFIG_OFF` 直接调用它。P1 没有在各 branch 内重写 constructor 或参数。

### 10.4 Forced-OFF 如何回到 baseline

`_forced_off_warning_message()` 对两个合法 reason 显式分支，未知 reason 在 constructor
前报错。合法 route 调用同一个 baseline helper；构造成功后由 factory 唯一入口调用一次
`logger.warning()`。这实现按 engine/speculator 实例一次，而不是
`vllm.logger.warning_once()` 的进程级 once-ever。它不会调用 numeric validator、owner
receiver，更不存在 P2/P3 对象。

### 10.5 Eligible path 当前多了什么

只多了三件事：

1. method-specific static future offset；
2. interim numeric/dynamic-K fail-closed Gate；
3. speculator 构造后，一次性保存 frozen `DraftWindowPolicyDecision`。

三个 owner receiver 都拒绝非 `ELIGIBLE_ON` decision 和重复配置。它们不调用 backend，
不分配 tensor，不改 `set_attn()`/`propose()`。DFlash2 的既有 MRO 可以找到 DFlash receiver
并持有 P1 decision；这是 Plan §6.3/§7.3 要求的 P2 inventory 入口。它没有
inventory/workspace/store，且 G-DFLASH2 仍未关闭，所以不构成 runtime Window support。

## 11. Runtime Effect

```text
P1 之前：
真实模型没有 MRV2 Draft Window。

P1 之后：
真实模型仍然没有 MRV2 Draft Window。
```

P1 的实际 runtime 效果只有：

- OFF route 多做一次无设备依赖的 policy decision，然后进入相同 baseline helper；
- forced-OFF route 在每个成功创建的 engine/speculator 实例发一次规定 warning；
- eligible route 在 invalid/dynamic 情况下更早 fail closed；valid 情况保存一个小型 frozen
  scalar decision，模型 forward/Attention 仍走 baseline。

没有任何 query 的 KV read set、write slot、position 或 Target output 因 P1 改变。

## 12. 测试说明

P1 主测试：
`vllm-ascend/tests/ut/spec_decode/test_draft_window.py`。

| Test | 测什么 | 为什么必须测 / 失败含义 |
|---|---|---|
| `test_extracted_baseline_factory_preserves_dispatch_order` | DSpark、DFlash、ordinary/special MTP、Eagle3 constructor 路由 | 失败表示为加 policy 改坏原 factory 主流程 |
| `test_public_config_off_factory_reaches_real_baseline_dispatch` | public wrapper 到真实 baseline helper/constructor 的 DSpark、MTP、Eagle3 联通 | 失败表示“wrapper parity”只在两个互不相连的 mock half 中成立 |
| `test_none_resolves_config_off_without_validating_method` | 所有主要 method 的 None -> OFF | 失败表示开关关闭时不再是 baseline |
| `test_mtp_forced_off_precedes_numeric_validation` | MTP 的 valid/0/negative/`W<K` 均 forced OFF | 失败表示 numeric precedence 错误或 MTP 被误启用 |
| `test_deepseek_v4_dspark_forced_off_precedes_numeric_validation` | DeepSeek-V4 DSpark 的同类 precedence | 失败表示 co-trained route 进入 Window infra |
| `test_deepseek_v41_model_type_is_in_forced_off_family` | 当前 upstream `deepseek_v41` identity | 失败表示 V4.1 family 被错误当 eligible DSpark |
| `test_supported_route_resolves_eligible` | Eagle3/DFlash/eligible DSpark | 失败表示合法候选 route 被错误关闭 |
| `test_plain_eagle_with_window_fails_closed` | plain Eagle ON rejection | 失败表示共享 AR class 偷开产品契约 |
| `test_policy_normalizes_method_and_explicit_model_family` | method/model canonical case/trim | 失败表示 canonical HF identity 不稳定 |
| `test_model_type_normalization_does_not_rewrite_separators` | 不把 `deepseek-v4` 改写成 MRV1 predicate 可命中的 `deepseek_v4` | 失败表示 policy invent 了新的 model family match |
| `test_unknown_configured_method_fails_closed` | 未知 ON route | 失败表示未知 method silent fallback |
| `test_policy_decision_is_immutable` | frozen decision | 失败表示后续阶段可原地篡改 policy |
| `test_config_off_factory_preserves_baseline_and_emits_no_warning` | OFF 无 validator/configure/warning | 失败表示 OFF 有额外 Window 副作用；state 由 public dispatch 与真实 owner rejection tests 证明 |
| `test_forced_off_factory_skips_all_window_downstream_work` | forced OFF 的 validator/configure spy 与 warning | 失败表示 forced route 穿透到下游 |
| `test_forced_off_warning_is_emitted_once_per_created_speculator` | 两次 factory construction 各收到一次 warning，且禁止调用 process-global `warning_once` | 失败表示后续 engine 实例 warning 被进程 cache 吞掉 |
| `test_unknown_forced_off_reason_fails_closed` | 未登记 reason 在 baseline constructor 前报错 | 失败表示未来 reason 会误报为 DeepSeek-V4 |
| `test_eligible_factory_validates_then_configures_speculator` | Eagle3 K、DFlash/DSpark K=0 与调用顺序 | 失败表示 method horizon 或 factory 次序错误 |
| `test_invalid_eligible_numbers_fail_before_speculator_construction` | `W<=0`、`W<K` 早于 constructor | 失败表示构造了半初始化对象或 invalid 值被接受 |
| `test_dynamic_k_fails_before_speculator_construction` | dynamic-K fail closed | 失败表示代码猜 configured/scheduled K |
| `test_speculator_owner_accepts_one_eligible_policy` | 三 owner 一次性 attach | 失败表示 state owner/lifetime 边界不清 |
| `test_speculator_owner_rejects_noneligible_policy` | OFF decision 不得产生 state | 失败表示 forced/OFF 可误入 P2 |
| `test_scalar_plan_matches_explicit_integer_oracles` | short、boundary、non-boundary、K=0、static K、pointwise W<K | 失败表示 Frozen 公式或 off-by-one 改变 |
| `test_negative_visible_length_fails_closed` | `S>E` runtime invariant | 失败表示负 read length 可下沉到 backend |
| `test_anchor_uses_legacy_block_alignment_not_lcm` | anchor 只按 B 对齐 | 失败表示错误改为 LCM 或其他 alignment |
| `test_direct_prefix_projection_handles_nonzero_offset` | offset-aware exact projection | 失败表示列数/offset 少算，可能漏 KV block |
| `test_empty_direct_prefix_projection_has_zero_extent` | `V=0` 不复制列且 extent=0 | 失败表示空 read 产生负/伪 capacity |
| `test_direct_prefix_capacity_preserves_alignment_slack` | `ceil((W+B-1)/span)` | 失败表示重复旧设计中的错误化简 |
| `test_direct_prefix_capacity_covers_zero_offset_projection` | `span ∣ B` 时 projection 列数不超过 capacity | 失败表示 default geometry 仍可能少分配列 |
| `test_direct_prefix_capacity_rejects_non_default_geometry` | `span ∤ B` 的具体 offset counterexample 必须拒绝 | 失败表示 zero-offset API 可被误用于 offset-aware layout |
| `test_same_absolute_anchor_projects_per_group_without_realigning` | 同 S 对不同 span 各自投影 | 失败表示 per-group 重算了 canonical anchor |
| `test_scalar_plan_uses_exact_end_not_planning_upper_bound` | plan 输入是 exact E | 失败表示 upper 被冒充 exact read length |
| `test_static_future_offset_is_method_specific` | Eagle3 K；DFlash/DSpark 0 | 失败表示 query stretch 被重复加入 |
| `test_dynamic_future_offset_fails_closed` | pure horizon helper 也拒绝 dynamic | 失败表示绕过 factory 可猜 K |
| `test_numeric_validation_rejects_invalid_eligible_values` | interim numeric contract | 失败表示 invalid eligible W 未 fail closed |

既有回归还覆盖：

- `test_dflash2_v2.py`：OFF 的 DFlash/DFlash2 dispatch、receiver MRO，以及 configured
  DFlash2 只有 P1 decision、没有 inventory/workspace/store；
- `test_extract_hidden_states_speculator_v2.py`：OFF 时 extract route 不变。

### 12.1 Final Design test ID 映射

| ID | P1 实际测试 | P1 状态 / 后续 owner |
|---|---|---|
| T01 | `test_scalar_plan_matches_explicit_integer_oracles` | PASS；显式覆盖 `W mod B = 0,1,2,B-1`、short/active |
| T02 | 同上 `(E=100,K=4,W=3,B=64)` | PASS；pointwise 数学与产品 `W<K` Gate 分离 |
| T03 | `test_negative_visible_length_fails_closed` | PASS |
| T04 | P1 由 T03 固化 `S<=E` primitive | proposal 内 rejection crossing 属 P4 Eagle3 runtime；P1 不伪称已执行 |
| T05 | `test_anchor_uses_legacy_block_alignment_not_lcm`、`test_direct_prefix_capacity_rejects_non_default_geometry` | PASS；anchor 不改，unsupported direct-prefix geometry 拒绝 |
| T06 | `test_anchor_uses_legacy_block_alignment_not_lcm` | PASS |
| T07 | `test_direct_prefix_projection_handles_nonzero_offset` | PASS；provider capability 尚未开放 |
| T08 | `test_direct_prefix_capacity_preserves_alignment_slack` | PASS |
| T09 | `test_scalar_plan_uses_exact_end_not_planning_upper_bound` | PASS；upper validation 属 P3 typed transport |
| T10 | 无 P1 provider/source | P2 source-coverage test；NOT STARTED |
| T11 | `test_same_absolute_anchor_projects_per_group_without_realigning` | PASS pure projection；multi-group enablement 仍 blocked |
| T12 | `test_dynamic_k_fails_before_speculator_construction`、`test_dynamic_future_offset_fails_closed` | PASS：policy 未决即拒绝 |
| T18A | `test_mtp_forced_off_precedes_numeric_validation`、`test_forced_off_factory_skips_all_window_downstream_work`、instance-warning test | PASS CPU/static；NPU output identity 后续矩阵未执行 |
| T18B | DeepSeek-V4 DSpark 对应 policy/factory tests | PASS CPU/static；NPU output identity 后续矩阵未执行 |
| T18C | CONFIG_OFF、supported-route、eligible factory、DFlash2 P1-only contract tests | PASS P1 contract；真实 Window Gate 尚未开放 |

原 Plan 把 T01–T12 整体写成 P1 exit criterion 过宽。Review 后按实际 owner 修正：T04
request/proposal runtime 归 P4，T10 source shortage 归 P2；其余 P1 可表达的 scalar/policy
部分已完成。这是 test ownership 修正，不改变 Final Design 的 read-plane 架构。

### 12.2 实际命令与结果

测试 checkout 是 untagged main SHA；测试环境设置 `VLLM_VERSION=0.29.0` 仅为了让当前
Ascend version gate 选择 fixed vLLM SHA 中存在的 `vllm.v1.attention.ops.pcp` 路径，
不是生产版本声明。

```bash
env VLLM_VERSION=0.29.0 \
  PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm:/Users/wenqingzhang/Desktop/vllm/vllm-ascend \
  .venv/bin/python -m pytest -q \
  tests/ut/spec_decode/test_draft_window.py \
  tests/ut/spec_decode/test_dflash2_v2.py \
  tests/ut/worker/test_extract_hidden_states_speculator_v2.py
```

Review-fix 后最终结果：`85 passed, 1 warning`。warning 是 source checkout 没有生成
`vllm._version`，与 P1 逻辑无关。

```bash
env VLLM_VERSION=0.29.0 PYTHONPATH=... \
  .venv/bin/python -m pytest -q tests/ut/spec_decode \
  --ignore=tests/ut/spec_decode/test_speculators_vwn_eagle3.py
```

结果：`307 passed, 13 skipped, 2 subtests passed`。

```bash
env VLLM_VERSION=0.29.0 PYTHONPATH=... \
  .venv/bin/python -m pytest -q tests/ut/worker/test_extract_hidden_states_speculator_v2.py
```

结果：`4 passed`。

完整 `tests/ut/spec_decode` 也执行过，最终结果为
`309 passed, 13 skipped, 7 failed, 2 subtests passed`。7 个失败全部来自
`test_speculators_vwn_eagle3.py`，共同失败点是 upstream selector：
`ValueError: Invalid attention backend for None`。本机没有 Ascend platform/backend，调用链
未经过本次 P1 文件。为满足 Review 要求，另在父基线 `841dc6cc` 的 detached 临时
worktree 运行同一文件，得到完全相同的 `7 failed, 2 passed` 与同一 stack；因此记录为
机器环境限制，不伪报通过，也不把它解释成 P1/NPU correctness。临时 worktree 已删除。

### 12.3 Lint / type / static check

```bash
.venv/bin/ruff check <8 changed files>
.venv/bin/ruff format --check <8 changed files>
env MYPYPATH=... .venv/bin/mypy --follow-imports skip \
  --check-untyped-defs --python-version 3.12 <7 directly relevant files>
.venv/bin/python -m compileall -q <8 changed files>
```

结果：最终 review-fix 文件与全部 P1 相关文件的 Ruff、format、targeted Mypy、compileall
全部通过。将完整既有 AR 文件纳入 targeted Mypy 时会命中其未改动的
`issubclass(type[Any] | None)` baseline errors（原行 327/329/331/333）；P1 新增行无 error。

仓库规范命令：

```bash
bash format.sh ci
```

最终运行中，Ruff check/format、codespell、typos、clang-format、actionlint、PNG、
filename、Python package、logger、forbidden imports、boolean context manager、long
function、symbolic meta 与 suggestion 全部通过。markdownlint 的 Node 环境安装被本机
`npm 11.9.0 EALLOWGIT` 阻断；gitleaks 与 shellcheck 本机无二进制，因此三项明确记为
未执行，不标记为 PASS。C1 时同一文档记录的 markdownlint 曾通过；本次 production
review-fix 不含仓库内 Markdown。hooks 没有改动无关文件。

## 13. P1 核心不变量

1. **Target untouched**：不读写 Target metadata/store/logits。
2. **Slot mapping untouched**：没有新增 slot override，也不调用 slot kernel。
3. **Full block table untouched**：不裁、不 clone、不替换 production `BlockTables`。
4. **Positions/query layout untouched**：不改 position、query count、causality。
5. **Scheduler/KV allocation untouched**：Window 不是 eviction/recycling policy。
6. **Policy before numeric**：MTP 与 DeepSeek-V4 DSpark 的任意 configured W 先 forced OFF。
7. **OFF zero Window state**：None 无 warning、无 owner attach、无 Window tensor/object graph；
   由 public CONFIG_OFF dispatch test 与真实 owner rejection test 联合证明。
8. **Forced-OFF zero downstream infrastructure**：每个成功创建的 speculator 一次 warning +
   baseline；validator/configure spies 为零，P2/P3 类型尚不存在。
9. **Eligible is not enabled**：只保存 frozen scalar decision，Attention read set仍 full。
10. **Dynamic-K blocked**：不选择 configured K 或 scheduled K 作为猜测。
11. **Canonical anchor**：只按 legacy B 向下对齐，不用 LCM，不按 consumer group 重对齐。
12. **Exact/capacity 分离**：`V=E-S` 与 `W+B-1` 不混用；negative V fail closed。

### 13.1 对照 Final Design 的 P1 自审

| Final invariant | P1 证据 | 结论 |
|---|---|---|
| Target full context 不变 | 无 Target/attention 文件修改；owner method 只赋 frozen decision | 满足 |
| write slot 使用 full table | P1 无 slot/block-table 修改 | 满足 |
| forced-OFF 早于 numeric/inventory/workspace | factory spy tests；P2/P3 类型不存在 | 满足 |
| None 完整 baseline | public wrapper → real helper/constructor 联通 test、baseline helper parity、existing factory regressions | 满足 |
| plain Eagle/dynamic-K fail closed | 两组显式 UT | 满足 |
| DFlash/DSpark future offset 0 | pure helper + factory call-record UT | 满足 |
| Eagle3 static K | configured K oracle；dynamic K 拒绝 | 满足 |
| 不提前开放 Graph/backend | 无 Graph/attention hook；文档 Gate 不变 | 满足 |

P1 CPU/static 功能 exit criterion：**SATISFIED**。T04 runtime crossing、T10 source shortage
已按 owner 分别归回 P4/P2；标准 CI/NPU 主机仍需补跑缺失的全局二进制 hooks与
NPU/runtime matrix。这不会把 P1 的 CPU/static 证据提升成 Window ON 支持。

## 14. 与 P2 / P3 / P4 的关系

```text
P1  [DONE]
Policy + pure math + immutable scalar types
        |
        v
P2  [NOT STARTED]
FullSource + inventory + valid counts + single-group provider
        |
        v
P3  [NOT STARTED]
Workspace + lease + typed transport + DraftMetadataStore
        |
        v
P4  [CONDITIONAL / NOT STARTED]
真实 Draft Attention 开始消费 Window read inputs
```

具体输出映射：

| P1 output | 后续消费者 |
|---|---|
| `DraftWindowPolicyDecision` | P2 `set_attn()` inventory Gate；P3 runtime owner；P4 mode/backend Gate |
| `DraftWindowPolicyState` | 所有阶段的 OFF/forced/eligible 分流；不得由 class inheritance 代替 |
| `DraftWindowScalarPlan` | P2 provider 的 request-level plan；P3 workspace sizing/exact lengths |
| `compute_legacy_anchor()` | Eagle3 proposal anchor 与 DFlash/DSpark prepared-end anchor 的共同 Frozen math |
| `compute_visible_length()` | P3/P4 每 step exact length 与 `S<=E` runtime assertion |
| `compute_window_capacity_tokens()` | P3 allocation 上界，不是 P4 exact read length |
| `DirectPrefixProjection` / `project_direct_prefix()` | P2 single-group direct-prefix provider；backend 必须另证 offset 可表达 |
| `compute_direct_prefix_capacity()` | P2/P3 zero-offset table width planning；不能替代 valid-count/source-coverage proof |

P2 不得因为 P1 已有 projection 就直接修改 Attention；P3 不得因为已有 capacity 就省略
lease/event lifetime；P4 不得因为 policy 是 eligible 就跳过 live hook 与 NPU physical-slot oracle。

## 15. 开发者阅读指南

建议按以下顺序读本次 C1：

1. 打开 `tests/ut/spec_decode/test_draft_window.py:165-604`，先看 OFF、forced-OFF、
   eligible、numeric/dynamic 与 owner tests，理解外部行为。
2. 打开 `vllm_ascend/worker/v2/spec_decode/draft_window.py:14-162`，对应阅读 enum、decision、
   policy resolver、method horizon 和 numeric Gate。
3. 回到 `vllm_ascend/worker/v2/spec_decode/__init__.py:41-158`，确认 policy 如何包在原
   dispatch 外，以及 `_init_speculator_baseline()` 的分支顺序未变。
4. 分别看 AR `:81`、DFlash `:30`、DSpark `:48` 的 `_configure_draft_window()`；确认它们
   只保存 frozen decision，没有 tensor/backend 调用。
5. 打开 `tests/ut/spec_decode/test_draft_window.py:607-847`，先用硬编码 oracle 理解数学边界。
6. 再读 `draft_window.py:181-299`，把每个公式与测试数字逐项对应。
7. 看 `test_dflash2_v2.py` 与 `test_extract_hidden_states_speculator_v2.py`，确认 OFF 的既有
   factory route 没被新入口破坏。
8. 最后依次执行 `git show b12399ad` 与 `git show c58daea` 阅读 C1 和独立 review-fix；
   不要从 P2/P3 架构图反推 P1 已经实现 runtime data plane。

## 16. P1 完成后的心智模型

1. 看到 `requested_window_size=None`，想到“完全 baseline，零 Window state”。
2. 看到 `FORCED_OFF`，想到“先于数值 Gate；成功创建的每个 speculator warning 一次”。
3. 看到 `ELIGIBLE_ON`，想到“只有资格，没有 Attention support”。
4. 看到 `effective_window_size=None`，想到“该 decision 绝不能进入 provider/workspace”。
5. 看到 `future_offset`，想到“Eagle3=static K；DFlash/DSpark=0；dynamic 拒绝”。
6. 看到 `window_start`，想到“一个绝对 canonical anchor，只按 legacy B 向下对齐”。
7. 看到 `window_visible_length`，想到“exact `E-S`，必须非负，不是 capacity”。
8. 看到 `window_capacity_tokens`，想到“`W+B-1` allocation 上界，不是可见 token 数”。
9. 看到 `first_token_offset`，想到“backend 必须证明能表达；不能自动把 offset 丢掉”。
10. 看到 `_draft_window_policy`，想到“P1 instance contract；P2/P3/P4 尚未开始”。

至此停止。下一步只有在 P1 Review 通过并收到明确确认后，才进入 P2。

# P1 Review Resolution

## Review 元数据与统计

- Review：`Code Review — MRV2 Draft Window P1 (b12399ad)`（DeepSeek independent
  source review；附件正文没有独立版本号或生成时间，故不虚构）。
- Codex 事实裁决时间：`2026-10-10T04:38:50+08:00`。
- 固定基线：vLLM `84030bbe3d74d99bad477a3d2e37a973ccd8865c`；
  vLLM-Ascend parent `841dc6ccdb134eab7ad09008859834d0572ee83f`；C1
  `b12399ad915415ce45105df5b0601848e7b70f6f`。
- 裁决范围：10 条编号 finding + 8 条 documentation observation，共 18 条。
- 结果：9 `ACCEPTED`、4 `PARTIALLY_ACCEPTED`、1 `REJECTED`、4
  `OPTIONAL_STYLE_ONLY`；0 `DEFERRED_TO_LATER_PHASE`、0 `NEEDS_TEST`、0
  `NEEDS_SOURCE_VERIFICATION`、0 `ARCHITECTURE_ESCALATION`。
- 最终代码提交：`c58daea0df34d1a6253dc34221d2a084b13affd5`，父提交仍是 C1；没有
  amend/rewrite C1。

## 逐条事实裁决

| ID | DeepSeek claim / Codex re-check | Evidence | Resolution | Action |
|---|---|---|---|---|
| F-01 | Claim：DFlash2 得到 `ELIGIBLE_ON` 是 false eligibility。Re-check：policy decision 是 P2 inventory 资格，不是 runtime enable signal；DFlash2 正是 Plan 指定要进入 inventory、再由 G-DFLASH2 拒绝 enable 的 route。 | Final Design §12.1/§12.3：DFlash2 eager Conditional；Plan §6.3 明定继承 receiver，§7.3 明定“只完成 inventory，不自动 enable”，§9.7/G-DFLASH2 默认拒绝；源码调用链 `init_speculator()` → `_init_speculator_baseline()` architecture discriminator → `AscendDFlash2Speculator` → inherited private receiver，未调用 `set_attn()`/Attention。 | **REJECTED** | 不加入 architecture-aware forced rejection；新增 `test_configured_dflash2_receives_only_p1_policy_contract`，同时断言没有 inventory/workspace/store，消除“eligible=enabled”歧义。 |
| F-02 | 原 test 名称声称“不 enable”，实际只断言 MRO inheritance。 | 原 `test_dflash2_v2.py:45-46`；新测试位于 `:45` 与 `:85`。 | **ACCEPTED** | 将原测试改名为 `test_dflash2_inherits_dflash_policy_receiver`，另加 P1-only contract test。 |
| F-03 | CONFIG_OFF test 的 `hasattr(SimpleNamespace)` 是测试自造事实，不能证明 production state absence。 | `_patch_factory()` 同时替换 baseline 与 configure helper；真实 owner rejection 在 `test_speculator_owner_rejects_noneligible_policy`；新增 public wrapper → real baseline dispatch test 使用无 receiver 的 `object()`，若误进 configure 会立即失败。 | **ACCEPTED** | 删除 CONFIG_OFF 与 forced-OFF 两条 vacuous `hasattr`；新增 DSpark/MTP/Eagle3 public parity test；文档 state 证据改为联合引用。 |
| F-04 | Factory 新增对已初始化 Ascend singleton 的硬前置条件。该 coupling 真实；但“正常 serving 的 extract path 可能被意外抢先”不成立，因为平台/worker 初始化先发生。 | `ascend_config.py:1689-1693`；`platform.py:455-509` 在 `:488` 初始化；`worker.py:149` 初始化；`model_runner.py:96` 先读取且 `:149` 才调用 factory。 | **PARTIALLY_ACCEPTED** | production module docstring 与本说明显式记录 standalone/test precondition；不改变 config owner 或 factory 主流程。 |
| F-05 | `- -> _` 会让 MRV1 raw predicate 原本不匹配的 identity 被 forced OFF；case/trim normalization 是否保留是独立问题。 | MRV1 `llm_base_proposer.py:409` 使用 `startswith("deepseek_v4")`；Final §18.1 禁止模糊 model-name match，同时要求 normalized identity。 | **PARTIALLY_ACCEPTED** | 删除 separator rewrite；保留 trim/lower；新增 `DeepSeek-V4 -> deepseek-v4 -> ELIGIBLE_ON` regression，canonical `deepseek_v4*` 仍 forced OFF。 |
| F-06 | binary `if/else` 会把未来第三个 reason 错报为 DeepSeek-V4。 | C1 factory `else` 无 exhaustiveness；user-facing diagnostic 是 Frozen contract 的一部分。 | **ACCEPTED** | 新增 exhaustive `_forced_off_warning_message()`；未知 reason 在 baseline constructor 前 `RuntimeError`；新增 regression。 |
| F-07 | offset 非零时 zero-offset capacity 可能少算；但 supported default geometry 下公式本身正确。 | 反例 `W=32,B=16,span=48,S=64,V=47`：offset 16、required 2、旧 capacity 1；Final/Plan default direct-prefix 要求 `span ∣ B`。 | **PARTIALLY_ACCEPTED** | 明确 API 为 default zero-offset contract，并强制 `span ∣ B`；增加 valid geometry inequality 与反例拒绝 tests；offset-aware provider 仍未开放。 |
| F-08 | wrapper 与 baseline helper 只被分半测试，没有 public end-to-end dispatch parity。 | 原测试分别 mock helper或直接调 private helper。 | **ACCEPTED** | 新增 parametrized public `init_speculator()` → real helper → DSpark/MTP/Eagle3 constructor test。 |
| F-09 | `_configure_eligible_draft_window()` 是 pass-through。 | helper 是单一 policy-to-owner seam，当前 tests 可 spy，删除与保留语义等价。 | **OPTIONAL_STYLE_ONLY** | 不改；不是 correctness 或 maintainability blocker。 |
| F-10 | `full_context_length` / `full_exact_end` 命名不统一。 | 一个是 legacy formula 参数名，一个是 typed plan 字段；值传递一致且所有 oracle 通过。 | **OPTIONAL_STYLE_ONLY** | 不做无行为收益的 rename。 |
| DOC-01 | §15 line ranges 漂移、logger 路径措辞别扭。 | 最终源码行号重新枚举；实际 import 是 `from vllm.logger import logger`。 | **OPTIONAL_STYLE_ONLY** | 随本次文档刷新修正，不视为 P1 blocker。 |
| DOC-02 | Notes 同时说要防止 DFlash2 shared-class auto-support，又说它继承 receiver。 | P1 state 是资格；Plan 另有 G-DFLASH2 runtime Gate。原措辞没有清楚区分两层。 | **PARTIALLY_ACCEPTED** | 重写 §1.1/§10.5；保留有意的 receiver inheritance，不接受 F-01 production guard。 |
| DOC-03 | `P1 exit criterion: SATISFIED` 过宽。 | 原 Plan 把 T01–T12 整体放在 P1，但 T04 是 proposal runtime、T10 是 provider source coverage。 | **ACCEPTED** | 增加 ID mapping；T04 归 P4、T10 归 P2；P1 只声明 CPU/static criterion PASS。 |
| DOC-04 | CONFIG_OFF “无 state”引用了 vacuous test。 | 同 F-03。 | **ACCEPTED** | 改为 public dispatch + owner rejection 联合证据。 |
| DOC-05 | 缺少 T01–T12/T18A–T18C 到真实测试名映射。 | Plan exit criterion 以 ID 表达，旧 Notes 只列 test name。 | **ACCEPTED** | 新增 §12.1 mapping；并补齐 T01 的 `W mod B=0/1/2/B-1` 四个 hard-coded oracle。 |
| DOC-06 | warning dedup scope 未说明；实现是 process-global once-ever。 | Final Design §18.3 明定按 engine/speculator 实例去重；upstream `vllm/logger.py:75-90,136-145` 的 `warning_once` 使用进程级 `lru_cache`。 | **ACCEPTED** | 改为每个成功 factory construction 调一次普通 `logger.warning()`，无 module global/marker state；两次 construction regression 期望两条 warning。 |
| DOC-07 | invariants 7–8 应给出可失败的 assertions。 | 原 CONFIG_OFF `hasattr` 不可失败；forced path 有 validator/configure spies。 | **ACCEPTED** | §13 明确引用 integrated public dispatch、owner rejection、validator/configure spies 和 P2/P3 类型不存在。 |
| DOC-08 | 建议 cross-link flow、增加非整除例子与 one-screen summary。 | 都是可读性建议，不改变 behavior。 | **OPTIONAL_STYLE_ONLY** | 增加 `span ∤ B` 数值反例；其余现有 §5/§16 已承担 flow/one-screen 功能，不重复扩写。 |

## Review-fix 前后与测试证据

- Test-first red：在 C1 上新增 regression 后为 `8 failed, 69 passed`；失败精确覆盖
  separator rewrite、process-global warning API、unknown reason fall-through 与
  non-default geometry 未拒绝。
- 修复后 targeted P1/factory：`85 passed, 1 warning`。
- locally runnable `spec_decode`（排除无平台 backend 的 VWN 文件）：
  `307 passed, 13 skipped, 2 subtests passed`。
- 完整 `spec_decode`：`309 passed, 13 skipped, 7 failed, 2 subtests passed`；7 个失败与
  parent baseline 的同文件 `7 failed, 2 passed`、stack 完全一致。
- Ruff check、Ruff format check、targeted Mypy、compileall、`git diff --check` 通过。
- repository hooks 的本机可执行部分通过；markdownlint/gitleaks/shellcheck 的环境限制见
  §12.3，不写成 PASS。

## 最终 Gate

- 未解决 P1 blocker：**无**。
- Architecture escalation：**NOT REQUIRED**。没有改写 Frozen read-plane、owner isolation、
  phase ordering 或 fail-closed architecture。
- `P1 FINAL: PASS`
- `P2 READY TO START`，但本轮严格停止，尚未创建 inventory、FullSource、provider、
  workspace、lease、DraftMetadataStore、Attention binding 或 Graph hook。
