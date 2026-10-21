# SUPERSEDED PROTOTYPE — depended on modified upstream vLLM; not deliverable under repository boundary

> 本文完整保留为历史技术实验记录。其 vLLM commit
> `0403469280c3d0f19c55cd1768e7e9d9e566a719` 与依赖该 API 的
> vLLM-Ascend commit `e0dd8e8d14a287e4d5a69c54d7a617a6ae160529`
> 均不得成为 production delivery dependency。可交付实现改由
> `P4a_Ascend_Only_Eager_Integration_Implementation_Notes.md` 说明。

# P4 Draft Attention Eager Integration Implementation Notes

## 1. Document Status

| 项目 | 值 |
|---|---|
| 权威设计 | `MRV2_Speculative_Draft_Sliding_Window_Final_Design.md` |
| 实施计划 | `MRV2_Draft_Window_Implementation_Plan.md` |
| vLLM 固定 baseline | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| vLLM P4 live-hook commit | `0403469280c3d0f19c55cd1768e7e9d9e566a719` |
| live-hook title | `feat(spec-decode): allow explicit draft attention read inputs` |
| live-hook time | 2026-10-10 13:31:41 +0800 |
| vLLM-Ascend P3 Final / C4 parent | `16727882744c935d9e899f7775353b57738852bc` |
| vLLM-Ascend P4a / C4 commit | `e0dd8e8d14a287e4d5a69c54d7a617a6ae160529` |
| C4 title | `feat(spec-decode): enable gated MRV2 draft windows for dense eager` |
| C4 time | 2026-10-10 13:37:16 +0800 |
| C4 upstream dependency | requires vLLM `0403469280c3d0f19c55cd1768e7e9d9e566a719` |
| P4a implementation state | **IMPLEMENTED；CPU/static contract complete；waiting for independent review** |
| `G-LIVE-HOOK` | **CLOSED** by upstream commit `04034692…` |
| `G-GQA-EAGER` | **OPEN**；尚无真实 NPU physical-read oracle |
| NPU runtime status | **NOT RUN** |
| P4b Eagle3 | **NOT STARTED** |
| Graph / Async | **BLOCKED / fail closed** |
| Feature release | **HOLD** |
| 文档更新时间 | 2026-10-10 13:40:07 +0800 |

P4a 是第一阶段真正改变 Draft Attention read visibility 的实现。它不是整个 P4，也不是
release 完成点。只有精确通过 policy、source、runtime 和 eager gates 的 DFlash / eligible
DSpark route 才会构造 Window read metadata；Target 和 KV write path 仍保持 full context。
因为本机没有 NPU，本文不会把 CPU/static 证据写成 `G-GQA-EAGER CLOSED`。

## 2. P4 Implementation Review 结论

在修改 production source 前重新核查了四个启动条件；没有 Architecture Escalation。

| Review item | 当前源码事实 | 决策 | 结果 |
|---|---|---|---|
| A. Epoch provenance | upstream `gather_batch_req_state()`先生成 ordered `req_ids`，再按同一顺序从`req_id_to_index`生成`idx_mapping_np`；Ascend `prepare_inputs()`把该 mapping复制到device并放入同一`AscendInputBatch`；DFlash/DSpark outer `propose()`是真实proposal边界 | speculator-owned epoch source在每个outer proposal只发一个严格递增epoch，并冻结batch object、ordered req IDs与CPU mapping fingerprint | **UNBLOCKED** |
| B. Single validate boundary | P3 workspace view可在下一代原地复用，borrowed Tensor本身不能撤销 | 唯一正式入口`_validated_draft_attention_read_inputs()`先且只先调用一次`validate_for(expected_identity)`，再收窄为upstream read-only type | **UNBLOCKED** |
| C. Hot D2H policy | baseline Ascend parallel-drafting builder最终会把device lengths转为host list；P3 debug validation含额外`.cpu()`/device `count_nonzero()` | production只在prepared full lengths处做一次受控CPU snapshot；host端同源计算descriptor/exact/upper；P3 production materialize走`device_window_exact=None`同源路径，跳过debug D2H与device-tail validator；explicit CPU exact使builder不再从device做第二次length copy | **UNBLOCKED for implementation；NPU trace仍是runtime gate** |
| D. G-LIVE-HOOK | baseline `_build_draft_attn_metadata()`直接读取full block tables、full seq lens和canonical slot mappings，无等价explicit hook | 增加最小vendor-neutral `DraftAttentionReadInputs`、optional keyword和protected adapter；None path保持baseline | **CLOSED** |

Review过程中由测试发现并修正两点：

1. upstream None path最初把切片后的`seq_lens`传给DCP helper，改变了baseline buffer/capacity
   语义；None-parity测试先失败，随后恢复为原始`self.input_buffers.seq_lens`。
2. Ascend最初在builder前有两次`validate_for()`；single-boundary spy先失败，随后改为materialize
   后立即登记outer proposal为唯一cleanup owner，只在transport adapter调用一次正式validation。

## 3. P4 与 P1 / P2 / P3 的区别

```text
P1: policy + scalar math
    谁有资格；Window起点、exact、block span怎样算
        ↓
P2: source + provider
    canonical full source是谁；真实gid/backend/geometry是什么；应读取哪些列
        ↓
P3: ownership + lifetime + typed transport
    backing由谁拥有；generation/epoch怎样防串批；reader完成前怎样防覆盖
        ↓
P4a: live consumer
    validated Window table/length第一次进入真实Draft metadata builder和Draft Attention
```

P1/P2/P3都没有改变Attention物理read input；P4a才把P3 transport接到live metadata
assembly。P4a没有改变P1 frozen math、P2 direct-prefix语义或P3 lease/store模型。

## 4. P4a Scope / Non-goals

P4a只实现以下交集：

- normalized method为DFlash，或非DeepSeek-V4 co-trained的eligible DSpark；
- MRV2；single executable group；Ascend dense GQA FIA direct-prefix；
- serialized eager；Draft graph mode `NONE`；async=false；
- TP=DP=PP=PCP=DCP=1；sequence parallel=false；
- DSA-CP=false；FlashComm=false；prefix cache=false；
- decode-only proposal；没有mixed/chunked/function prefill；
- static K；有效正数`draft_window_size`；
- P2 source coverage与P3 fixed-capacity workspace均通过。

明确不在本阶段：

- Eagle3 / `G-AR-STEP`；plain Eagle；DFlash2 runtime；
- FULL、FULL_DECODE_ONLY、PIECEWISE Graph；capture/replay；
- Async multi-lane或真实NPU completion event；
- MLA、DSA、SFA、V4.1、native/recycling、multi-group；
- TP>1及任何DP/PP/PCP/DCP/SP/DSA-CP/FlashComm组合；
- Window ON + prefix cache；mixed/chunked/function prefill；
- NPU correctness结论、性能结论或feature release。

## 5. Before P4 Data Flow

```text
P1 WindowPlan
    ↓
P2 FullSource + ReadDescriptor
    ↓
P3 Generation / Lease / Workspace
    ↓
P3 DraftMetadataInputs + DraftMetadataStore
    ↓
STOP

Draft Attention metadata ───────────────→ full block table + full lengths
KV write / slot mapping ────────────────→ canonical full path
Target metadata ────────────────────────→ full context
```

P3结束时transport虽已安全存在，但没有production consumer。

## 6. After P4a Data Flow

```text
canonical FullSource
    ↓
P1 scalar plan (future_offset=0)
    ↓
P2 direct-prefix descriptor + valid-count snapshot
    ↓
production proposal epoch + ordered req IDs + idx_mapping fingerprint
    ↓
P3 lease + workspace materialize
    ↓
DraftMetadataInputs
    ↓
_validated_draft_attention_read_inputs()
    │  validate_for(expected_identity) exactly once
    ↓
upstream DraftAttentionReadInputs
    ↓
_build_draft_attn_metadata(read_inputs=...)
    ↓
Ascend protected builder adapter adds CPU exact
    ↓
independently built Draft metadata
    ↓
DraftMetadataStore publish/read
    ↓
Draft Attention forward
```

独立且不变的write path：

```text
canonical full block table
    ↓
baseline prepare_dflash_inputs / positions / query layout
    ↓
canonical self.block_tables.slot_mappings
    ↓
KV cache write
```

Target path仍使用Target full table/full lengths。Window只改变Draft read table与Draft read
lengths。

## 7. Upstream Minimal Live Hook

### 7.1 Type

vLLM新增frozen、slotted、vendor-neutral：

```python
DraftAttentionReadInputs(
    block_tables,
    seq_lens,
    seq_lens_cpu_exact,
    seq_lens_cpu_upper_bound,
    max_seq_len,
    dcp_local_seq_lens=None,
)
```

字段只表达一次Draft metadata build的read state：

| Field | Meaning | Owner |
|---|---|---|
| `block_tables` | 每global gid的Draft read table；P4a只替换唯一eligible gid | caller/P3 workspace |
| `seq_lens` | device exact Window lengths | P3 workspace |
| `seq_lens_cpu_exact` | CPU exact Window lengths | P3 workspace |
| `seq_lens_cpu_upper_bound` | 已完成step处理的CPU upper；upstream不得再加step | P3 workspace |
| `max_seq_len` | active upper最大值 | validated adapter |
| `dcp_local_seq_lens` | vendor-neutral optional read length seam | 当前P4a gate下为None |

它明确没有：slot mapping override、positions、query_start、query layout、policy、Ascend type、
workspace、lease或Target state。

### 7.2 None parity

`read_inputs is None`时：

- block tables仍取`self.block_tables.input_block_tables`；
- device lengths仍取`self.input_buffers.seq_lens`；
- DCP helper仍看到baseline full input buffer；
- CPU upper仍由caller upper + step并clamp；
- max仍是`self.draft_max_seq_len`；
- slot mappings无条件仍取`self.block_tables.slot_mappings`。

### 7.3 Explicit path

`read_inputs is not None`只替换block tables、read lengths、max read length与必要的DCP-local
read lengths。query start、causal、positions注入、slot mappings和KV write state不变。CPU upper
已经是final value，不会二次加step。

### 7.4 Protected adapter

base `_call_draft_attn_metadata_builder()`仍只执行`build_attn_metadata(**builder_kwargs)`。
Ascend mixin override仅在explicit path复制kwargs并增加：

```python
seq_lens_cpu = read_inputs.seq_lens_cpu_exact
```

既有`build_attn_metadata_wrapper()`与DSpark
`build_draft_attn_metadata_factory(positions, ..., is_prefilling)`仍包围原调用，因此positions和
`is_prefilling` passthrough没有丢失。

## 8. Epoch Provenance

真实source chain是：

```text
GPUModelRunner.gather_batch_req_state()
    ordered req_ids
    ↓ same order
req_states.req_id_to_index[req_id]
    ↓
idx_mapping_np
    ↓ Ascend prepare_inputs() copy
idx_mapping device + AscendInputBatch(req_ids, idx_mapping_np, idx_mapping)
    ↓
DFlash / DSpark outer propose(input_batch, ...)
    ↓
DraftWindowProposalEpochSource.begin(input_batch)
```

`DraftWindowProposalEpochSource`由speculator持有，不接受外部任意整数：

- 每个真实outer proposal发一个`mapping_epoch`；
- 同一proposal里多次读取复用同一个epoch，不错误增代；
- next proposal无条件严格递增，即使请求集合相同；
- begin时冻结`id(input_batch)`、ordered request IDs和active CPU mapping内容；
- materialize前后都重新验证这三项；
- 同一Tensor pointer原地rewrite也会因mapping fingerprint变化失败；
- reorder、finish/add、same-row new request在下一proposal获得新epoch；若在同一proposal中突变则
  立即fail closed；
- proposal结束后旧context不能finish或冒充active generation。

因此epoch与真实proposal boundary绑定，而不是由caller传入一个“看起来递增”的值。

## 9. Single Validate Boundary

唯一正式read consumption入口是：

```text
DraftMetadataInputs
    ↓
DraftWindowEagerMixin._validated_draft_attention_read_inputs(
    inputs, expected_identity
)
    ↓ inputs.validate_for(expected_identity) exactly once
DraftAttentionReadInputs
    ↓
upstream metadata builder
```

规则：

- P4a builder不接受外部构造的`read_inputs`；非None直接拒绝；
- materialize成功后立即把`inputs`登记为outer proposal cleanup owner；
- adapter validation失败时不能进入upstream builder；
- stale/wrong identity不能构造upstream transport；
- 其他call site不手写正式pre-builder `validate_for()`；
- store publish/read仍可做P3自身的generation validation，那不是第二个Attention consumption
  boundary。

spy回归验证builder前恰好一次validation，stale regression验证builder调用次数保持0。

## 10. Hot D2H / Device Sync Policy

最终策略是“一个受控同源snapshot + production绕开P3 debug validators”：

1. baseline `prepare_dflash_inputs`先在device得到真实prepared full exact lengths。
2. `_snapshot_prepared_draft_seq_lens()`只对active+padded slice做一次
   `to(device="cpu", dtype=int32, copy=True)`。
3. CPU snapshot与canonical `num_blocks.cpu` owner共同产生descriptor、Window exact和upper。
4. P3 materialize传`device_window_exact=None`，由同一个CPU exact H2D写入stable workspace。
5. production同源路径不执行P3 debug `.cpu()` exact cross-check，也不执行device
   `count_nonzero()` tail validator。
6. Ascend builder得到explicit CPU exact；parallel-drafting backend的`tolist()`读取CPU tensor，
   不再从device exact做第二次D2H。

CPU unit tests仍保留严格cross-check路径。静态spy证明production不进入debug validators；真实
NPU profiler仍需确认每proposal同步点、stream和延迟，所以这里不关闭runtime gate，也不宣称
Graph-safe。

## 11. DFlash Timing

真实调用顺序：

```text
AscendDFlashSpeculator.propose()
    set self.input_batch
    enter build_attn_metadata_wrapper
    enter _draft_window_proposal_scope
        epoch.begin(input_batch)
        upstream DFlashSpeculator.propose()
            baseline prepare_dflash_inputs
                positions/query/full slot mapping/full KV prepared state
            Ascend build_draft_attn_metadatas()
                _build_draft_attn_metadata(step=num_query_per_req)
                    snapshot prepared full exact
                    P1 plan (future_offset=0)
                    P2 descriptors/valid counts
                    P3 materialize + lease
                    single validate adapter
                    upstream live hook
                    Ascend metadata builder with CPU exact
                    Target alias isolation
                    Draft store publish/read
            Draft forward / sample
        proposal scope retire or abort
        epoch.finish
```

DFlash upstream定义`num_query_per_req = K + 1`且不允许`sample_from_anchor=True`。P4a不复制
这个规则，而是读取真实`self.num_query_per_req`，并要求apply-time `step`与它一致。

## 12. Eligible DSpark Timing

DSpark复用同一个mixin与P1/P2/P3路径，但保留其既有Ascend wrapper和positions /
`is_prefilling` factory。真实query width来自upstream DSpark初始化：

| Route | Upstream setting | `num_query_per_req` | P4a upper increment |
|---|---|---:|---:|
| DSpark default | `sample_from_anchor=True` | `K` | `K` |
| DSpark explicit | `sample_from_anchor=False` | `K+1` | `K+1` |
| DFlash | fixed no-anchor | `K+1` | `K+1` |

DeepSeek-V4 / V4.1 co-trained DSpark在P1 factory warning-once后forced OFF，不创建P2/P3/P4
state。Target使用SFA/DSA不被当作Draft backend证据；只有P2 inventory确认Draft consumer是
single dense GQA direct-prefix才可进入P4a。

## 13. Read vs Write Boundary

| State | Window ON value | Window OFF value | Changed? | Why |
|---|---|---|---|---|
| Draft read block table | P3 materialized direct-prefix Window table | canonical full table | **Yes** | P4a功能本体 |
| Draft device read length | Window exact | full prepared exact | **Yes** | 限制Draft visible tokens |
| Draft CPU exact | Window exact | baseline CPU/full-derived value | **Yes** | Ascend host metadata一致性 |
| Draft CPU upper | Window upper，已含真实query width | baseline full upper + step | **Yes** | 同generation safe upper |
| Draft max read length | active Window upper max | `draft_max_seq_len` | **Yes** | builder read bound |
| slot mapping | canonical `self.block_tables.slot_mappings` | same | **No** | write-side frozen |
| positions | baseline prepared positions | same | **No** | query semantics frozen |
| query start/layout | baseline builder output | same | **No** | query semantics frozen |
| canonical FullSource | unchanged | unchanged | **No** | read-only owner |
| physical KV allocation | unchanged | unchanged | **No** | no KV compaction/recycling |
| Target metadata/lengths | original full state | same | **No** | Target correctness frozen |
| Target logits for identical state/input | expected identical | baseline | **Must not change** | 需NPU oracle最终确认 |

## 14. DraftMetadataStore Production Use

P4a不从Target metadata过滤/原地改写生成Draft metadata。流程是：

1. upstream + Ascend builder独立构造Draft metadata；
2. 读取真实`self.model_state.attn_metadata`，不得传None或空dict绕过；
3. `_isolate_draft_metadata_from_target()`递归检查/隔离：
   - top-level object；
   - dict/list/set/tuple；
   - dataclass（包括shared mutable dataclass root）；
   - `__dict__`与MRO `__slots__`对象；
   - Tensor object和underlying storage；
4. `runtime_state.publish_metadata(inputs, metadata, target_metadata=real_target)`执行P3
   mandatory disjointness check；
5. 返回`runtime_state.read_metadata(inputs.identity)`，所以production确实经过独立Draft store。

测试不仅检查`draft is not target`，还对nested container、shared dataclass、Tensor storage、
Target identity和Target content做不变性断言。

## 15. Lifecycle / Retirement

P4a只允许serialized eager lane 0：

```text
proposal begin
    ↓ epoch active
materialize
    ↓ lease ACQUIRED / workspace generation-bound
validate + build + publish
    ↓ Draft forward and sampling enqueued on current stream
super().propose returns
    ↓ proposal scope retire_generation()
store invalidated + lease retired/reclaimable
    ↓ epoch finish
next serialized proposal may reuse workspace
```

异常路径：

- materialize前异常：无lease；scope清除epoch；
- materialize后validation/builder/isolation/store/forward异常：`abort_generation()`是唯一cleanup
  owner；
- successful proposal却没有消费Window inputs：hard error；
- wrong/stale/double lifecycle操作由P3 fail closed。

没有把CPU fake completion token带入production。当前源码证据是eager proposal没有stream
切换，forward、sampling以及下一次workspace写入按同一current stream顺序入队；所以serialized
route可用同流顺序复用。这个结论不覆盖Async/multi-stream，也不能代替真实NPU event/timing
验证；若NPU trace显示stream切换或异步reader越过scope，runtime gate必须保持OPEN并增加真实
completion机制。

### 15.1 P4发现的FullSource owner事实

`block_tables.num_blocks.gpu`在当前Ascend实现中是rotating UVA transport view，不是稳定owner。
P4a因此把`FullDraftKVSource`的persistent valid-count identity收紧为
`block_tables.num_blocks.cpu`：

- source bind记录稳定CPU owner；
- 每次使用验证CPU owner未被替换；
- 当前GPU transport view只做geometry检查，不作为freshness/owner identity；
- valid counts按`idx_mapping_np`从CPU owner gather；
- rotating GPU view不会误报owner replacement；真实CPU owner replacement会fail closed。

这是当前checkout的新source fact和必要correctness修正，不改变Frozen direct-prefix架构。

## 16. Fail-closed Matrix

| Combination | Behavior before P3/P4 workspace | Reason / owner |
|---|---|---|
| `draft_window_size=None` | baseline；零P2/P3/P4 state | CONFIG_OFF |
| MTP | warning once + forced OFF；零state | P1 forced policy |
| DeepSeek-V4/V4.1 co-trained DSpark | warning once + forced OFF；零state | P1 forced policy |
| plain Eagle | explicit unsupported error | P1 policy |
| Eagle3 | 不进入P4a | P4b / `G-AR-STEP` |
| unknown method | explicit unsupported error | P1 policy |
| dynamic K | explicit unsupported error | P1 static-K gate |
| DFlash2 | inventory可观察；runtime source capability拒绝 | P2/P4 gate |
| multi-group / multiple consumers | inventory failure | P2 source gate |
| MLA / DSA / SFA / native/recycling / V4.1 layout | inventory failure | unverified provider |
| non-Ascend dense FIA builder/backend | inventory failure | P2 exact backend identity |
| source shortage / unsupported geometry | descriptor/provider failure | P2 coverage gate |
| Graph FULL/FULL_DECODE_ONLY/PIECEWISE | inventory failure | graph mode must beNONE |
| async scheduling | inventory failure | serialized only |
| TP/DP/PP/PCP/DCP > 1 | inventory failure | topology unverified |
| sequence parallel / DSA-CP / FlashComm | inventory failure | parallel/communication unverified |
| prefix cache | inventory failure | Window ON combination unverified |
| mixed/chunked/function prefill | proposal-scope error beforematerialize | P4a decode-only |
| dummy/profile eligible Window proposal | proposal-scope error | no fake capture semantics |
| stale epoch/identity | error beforebuilder | P3/P4 validation |

任何拒绝都不会通过静默关闭用户的Graph、Async、parallel、prefix cache或prefill设置来继续。

## 17. 修改文件总览

### 17.1 vLLM commit `04034692…`

| File | Class / Function | Before | After | Why |
|---|---|---|---|---|
| `vllm/v1/worker/gpu/spec_decode/speculator.py` | `DraftAttentionReadInputs` | 无explicit Draft read type | vendor-neutral frozen read-only type | 为vendor提供最小live seam |
| 同上 | `_build_draft_attn_metadata(..., read_inputs=None)` | 只能读full owner | optional替换read table/length；slot/query/write不变 | P4 live hook |
| 同上 | `_call_draft_attn_metadata_builder()` | 直接调用builder | protected adapter，base完全baseline | vendor可加CPU exact而不复制assembly |
| `.../dflash/speculator.py` | DFlash override | 不接收read inputs | keyword透传到base | 保持DFlash override兼容 |
| `tests/v1/spec_decode/test_eagle_draft_attn_metadata.py` | 8 tests | 既有upper tests | 增type boundary、None parity、read override、slot freeze、DCP recompute | 保护vendor-neutral contract |

### 17.2 vLLM-Ascend commit `e0dd8e8d…`

| File | Main change | Why |
|---|---|---|
| `vllm_ascend/worker/v2/spec_decode/draft_window_eager.py` | epoch source、host plan、single adapter、live builder/store/lifecycle、Target alias isolation | P4a主接线 |
| `.../draft_window.py` | stable `num_blocks.cpu` owner与same-source production materialize seam | owner correctness + no debug D2H |
| `.../dflash/speculator.py` | mixin、real proposal scope、metadata call接入 | DFlash P4a |
| `.../dspark/speculator.py` | mixin、real proposal scope、保留positions/prefill wrapper | eligible DSpark P4a |
| `worker/v2/attn_utils.py` | optional explicit `seq_lens_cpu`，shape/dtype/upper validation | CPU exact seam；default None parity |
| `attention/utils.py` | `seq_lens_cpu_is_explicit`及unpadded propagation | 区分explicit seam与legacy mirror |
| `attention/attention_v1.py` | parallel-draft builder优先explicit CPU exact | 避免第二次device length D2H |
| `tests/ut/spec_decode/test_draft_window_eager.py` | 16 functions / 25 cases | epoch、math、single boundary、DFlash/DSpark、invariants、cleanup |
| `tests/ut/spec_decode/test_draft_window.py` | rotating count view、gates、owner regressions | P1/P2/P3/P4边界 |
| `tests/ut/spec_decode/test_draft_window_runtime.py` | same-source no-D2H与runtime regressions | hot path contract |
| `tests/ut/worker/test_attn_utils_v2.py` | CPU exact seam/pass-through/validation | shared funnel contract |
| `tests/ut/attention/test_attention_v1.py` | explicit vs default builder source | backend metadata contract |

## 18. CPU / Static Tests

### 18.1 Contract matrix

| Test / group | Proves | Failure meaning |
|---|---|---|
| upstream type-field test | hook不能携带slot/query/write override | vendor-neutral boundary扩张 |
| upstream None parity | full table/full lengths/slot/DCP baseline source不变 | OFF regression |
| explicit read override | 只替换Draft table/length；upper不二次加step | live hook错误 |
| production epoch tests | one proposal one epoch；reorder/finish-add/row replacement/rewrite被检测 | freshness provenance错误 |
| plan parameter cases | short、boundary、non-boundary、long和source shortage | Window math/provider接线错误 |
| single-boundary spy | builder前恰好一次validate；stale永不进builder | borrowed workspace可越权 |
| hot-sync spy | production只做controlled snapshot；P3 debug sync不运行 | 每proposal新增未批准sync |
| frozen-invariant test | slot/positions/query/Target/full table不变 | read/write边界破坏 |
| query-width test | DSpark K、DSpark K+1、DFlash K+1 | upper或timing错误 |
| builder-adapter test | CPU exact加入且positions/is_prefilling保留 | Ascend wrapper语义丢失 |
| Target alias tests | nested Tensor/storage/container/dataclass不污染Target | Draft/Target isolation破坏 |
| exception cleanup | builder异常abort且下一proposal可复用 | lease leak |
| rotating valid-count view | GPU UVA view轮换不误报；CPU owner替换拒绝 | canonical owner错误 |

### 18.2 Commands and results

以下Ascend命令在`/Users/wenqingzhang/Desktop/vllm/vllm-ascend`运行，均使用：

```bash
VLLM_VERSION=0.29.0 PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm
```

| Command / scope | Result | Limitation |
|---|---|---|
| `.venv/bin/pytest -q tests/ut/spec_decode/test_draft_window_eager.py` | `25 passed, 1 warning` | CPU/static |
| eager + `test_attn_utils_v2.py` + `test_attention_v1.py` | `110 passed, 1 warning, 2 subtests passed` | no NPU kernel |
| P1/P2/P3/P4 + DFlash2 + DSpark targeted | `214 passed, 1 warning` | CPU/static |
| final focused Window runtime/eager/DFlash2 | `196 passed, 1 warning` | CPU/static |
| `test_v2_block_table.py` + `test_block_table.py` + attn-utils + attention-v1 | `99 passed, 1 warning, 23 subtests passed` | no NPU kernel |
| `.venv/bin/pytest -q tests/ut/spec_decode` | `424 passed, 13 skipped, 7 failed, 2 subtests passed` | 7 failures are existing VWN host backend-selection failures；不是PASS |
| same suite with `test_speculators_vwn_eagle3.py` excluded | `422 passed, 13 skipped, 1 warning, 2 subtests passed` | locally runnable scope |

7个full-suite failures都在既有`test_speculators_vwn_eagle3.py`，错误为
`ValueError: Invalid attention backend for None`，stack不经过P4文件。临时worktree在Ascend
P3 Final `167278…` + upstream baseline `84030…`上运行同一文件得到完全相同的
`7 failed, 2 passed`。因此它们记录为baseline-equivalent environment failures，不能写成PASS。

upstream在`/Users/wenqingzhang/Desktop/vllm/vllm`运行：

```bash
PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
  /Users/wenqingzhang/Desktop/vllm/vllm-ascend/.venv/bin/pytest -q \
  --confcutdir=tests/v1/spec_decode \
  tests/v1/spec_decode/test_eagle_draft_attn_metadata.py
```

结果：`8 passed, 1 warning`。不加`--confcutdir`时root conftest因本机缺`tblib`无法collection；
这不是测试PASS，也不影响上述test module通过isolated targeted collection。

静态检查：

| Check | Result | Scope / limitation |
|---|---|---|
| Ruff check | PASS | 两仓changed Python files |
| Ruff format `--check` | PASS | 两仓changed Python files |
| targeted Mypy | `Success: no issues found in 7 source files` | `--follow-imports=skip --check-untyped-defs` |
| compileall | PASS | changed source/tests |
| `git diff --check` | PASS | both final commits/worktrees |
| selected relevant pre-commit hooks | PASS | ruff-check、ruff-format、codespell、typos、python-init、logger、forbidden-imports、boolean-context-manager、long-functions、symbolic-meta、filenames |
| full pre-commit | NOT COMPLETED | actionlint尝试下载Go依赖并网络超时；不是PASS |
| gitleaks hook | NOT RUN | 本机无`gitleaks`且hook依赖的`wget`也不存在；不是PASS |

## 19. NPU Runtime Test Plan

### 19.1 固定环境

公司服务器Agent必须记录：

- NPU型号、驱动/CANN、PyTorch、torch_npu；
- vLLM commit `0403469280c3d0f19c55cd1768e7e9d9e566a719`；
- vLLM-Ascend commit `e0dd8e8d14a287e4d5a69c54d7a617a6ae160529`；
- exact model/revision、draft model/revision、tokenizer revision；
- method（DFlash或eligible DSpark）、K、DSpark `sample_from_anchor`；
- TP=1、DP=PP=PCP=DCP=1、single card、single gid、dense GQA；
- `enforce_eager=true`、async=false、prefix cache=false；
- fixed seed、dtype、max model len、max batch size；
-完整启动命令与环境变量。

每个case只改变一个配置：

```text
A = draft_window_size omitted (Window OFF)
B = --additional-config '{"draft_window_size": <W>}' (Window ON)
```

不得通过关闭一个本来启用的Graph/Async/prefix/prefill/parallel feature来让B继续；那些组合应
单独验证为显式fail closed。

### 19.2 Case matrix

| ID | Method / width | Batch transition | Context relation | Expected focus |
|---|---|---|---|---|
| NPU-01 | DFlash `K+1` | stable single request | `L < W` | Window read-set等于full visible set |
| NPU-02 | DFlash `K+1` | stable single request | `L = W` | exact boundary，无off-by-one |
| NPU-03 | DFlash `K+1` | stable single request | `L > W`，block boundary | aligned first source block/offset |
| NPU-04 | DFlash `K+1` | stable single request | `L > W`，non-boundary | direct-prefix safe extent与mask正确 |
| NPU-05 | DFlash `K+1` | two requests `[A,B]→[B,A]` | long | epoch/fingerprint/reorder |
| NPU-06 | DFlash `K+1` | A finish，C add并复用persistent row | long | stale A不能污染C |
| NPU-07 | DFlash `K+1` | stable | very long | capacity、source coverage、performance |
| NPU-08 | DSpark default anchor `K` | stable | short + long | actual width K |
| NPU-09 | DSpark explicit no-anchor `K+1` | stable | short + long | actual width K+1 |
| NPU-10 | eligible route | source-shortage fixture if constructible | boundary | deterministic fail beforeforward |
| NPU-11 | forced-off DSV4 co-trained DSpark | stable | long | warning once、zero Window state、baseline full |
| NPU-12 | unsupported combinations | Graph/Async/prefix/mixed prefill/topology one at a time | any | explicit fail closed beforeworkspace |

### 19.3 每个ON/OFF pair必须采集

1. CPU oracle token interval与expected visible token/block set；
2. ordered request IDs、CPU/device mapping、proposal epoch；
3. P1 scalar plan；
4. P2 descriptor、valid block count、global gid/source identity；
5. P3 materialized Window table、device/CPU exact、CPU upper；
6. canonical full table前后hash/content；
7. Window ON/OFF slot mapping、positions、query start；
8. backend最终metadata中的block table、seq lengths和actual physical read-set；
9. Draft logits/proposals/acceptance（能采集则记录）；
10. Target metadata identity/content、Target logits与最终outputs；
11. NPU stream/profiler：D2H/H2D次数、同步点、workspace rewrite与attention kernel顺序；
12. exception、lease retire/abort和下一proposal复用状态。

### 19.4 Pass criteria

- ON physical Draft read-set精确等于CPU Window oracle，不能只看metadata shape；
- OFF read-set与baseline一致；
- slot mapping、positions、query layout、canonical full table、Target metadata与Target logits在controlled
  identical state下不变；
- reorder/finish-add没有stale generation或cross-request read；
- DFlash/DSpark width符合表格；
- profiler没有额外未批准D2H或跨stream use-after-retire；
- unsupported route在workspace/materialize/forward前失败；
- repeated fixed-seed runs稳定，无NPU error或memory corruption。

只有这些真实NPU oracle通过，才可把`G-GQA-EAGER`改为CLOSED。

## 20. Runtime Evidence

当前只有CPU/static和source-level证据：

```text
G-LIVE-HOOK = CLOSED
G-GQA-EAGER = OPEN
NPU runtime experiment = NOT RUN
Feature release = HOLD
```

不能声称：NPU physical read-set正确、NPU logits已比较、无性能回退、Async-safe、Graph-safe或
feature release ready。

## 21. Runtime Effect

```text
P3 Final:
Attention still reads baseline full context.

P4a eligible Window ON candidate:
Draft Attention now receives Window block tables and Window read lengths.
Target Attention and all KV write-side state remain full-context.
```

这个runtime effect只适用于通过全部P4a gates的DFlash / eligible DSpark serialized eager
candidate。OFF/forced-OFF保持baseline；所有未证明组合fail closed。

## 22. Target / Slot Invariant Audit

- [x] upstream type没有slot mapping override字段；
- [x] upstream builder无条件从`self.block_tables.slot_mappings`取slot mappings；
- [x] positions仍由既有Ascend wrapper/factory注入；
- [x] query start和causal仍由baseline builder构造；
- [x] canonical FullSource不被materialize修改；
- [x] physical KV allocation和full table shape不变；
- [x] P4 source owner改为稳定`num_blocks.cpu`，不把rotating GPU view当identity；
- [x] Target metadata真实传入store检查且identity/content不被Draft隔离操作修改；
- [x] Draft metadata独立build，不从Target原地过滤；
- [x] Window upper不会二次加step；
- [x] CONFIG_OFF、FORCED_OFF、unsupported route无P4 epoch/workspace消费；
- [x] no module global、ContextVar、`self.block_tables` swap或`self.input_buffers` swap；
- [x] no Eagle3、Graph、Async、complex backend或parallel enablement；
- [ ] real NPU Target logits/physical read-set：等待NPU oracle。

## 23. Remaining Gates

| Gate | Status | Close condition |
|---|---|---|
| `G-LIVE-HOOK` | **CLOSED** | upstream `04034692…` + parity tests |
| `G-GQA-EAGER` | **OPEN** | section 19真实NPU read-set/logit/lifecycle oracle |
| `G-AR-STEP` / P4b | **OPEN / NOT STARTED** | Eagle3 method-specific first-pass/AR-step design + tests |
| Graph | **BLOCKED / fail closed** | capture/replay stable-address typed hook + graph oracle |
| Async | **BLOCKED / fail closed** | real multi-lane/event retirement protocol + NPU tests |
| prefix cache | **BLOCKED / fail closed** | read/write/source interaction proof |
| mixed/chunked/function prefill | **BLOCKED / fail closed** | phase-specific lengths/query timing proof |
| parallel | **BLOCKED / fail closed** | TP/DP/PP/PCP/DCP/SP/DSA-CP/FlashComm projection proof |
| backend extensions | **BLOCKED per route** | MLA/DSA/SFA/native/recycling/multi-group provider + oracle |
| Delivery manifest/release | **HOLD** | P4a independent review + NPU gate + required later gates |

## 24. Developer Reading Guide

按下面顺序阅读可以最快建立完整调用链：

1. upstream `vllm/v1/worker/gpu/spec_decode/speculator.py::DraftAttentionReadInputs`；
2. upstream同文件`_build_draft_attn_metadata()`与`_call_draft_attn_metadata_builder()`；
3. upstream DFlash `.../dflash/speculator.py::_build_draft_attn_metadata()`；
4. Ascend `draft_window.py::resolve_draft_window_policy()`与
   `build_draft_window_source_capability()`；
5. Ascend `draft_window.py::FullDraftKVSource`、`gather_valid_num_blocks_cpu()`和P3 runtime types；
6. Ascend `draft_window_eager.py::DraftWindowProposalEpochSource`；
7. 同文件`build_eager_window_materialization_plan()`；
8. 同文件`DraftWindowEagerMixin._draft_window_proposal_scope()`；
9. 同文件`_materialize_draft_window_read_inputs()`、
   `_validated_draft_attention_read_inputs()`和`_build_draft_attn_metadata()`；
10. DFlash / DSpark Ascend speculator的`set_attn()`、`build_draft_attn_metadatas()`、`propose()`；
11. `worker/v2/attn_utils.py::build_attn_metadata()`；
12. `attention/attention_v1.py`的parallel-drafting metadata builder分支；
13. `tests/ut/spec_decode/test_draft_window_eager.py`；
14. upstream `tests/v1/spec_decode/test_eagle_draft_attn_metadata.py`。

## 25. Mental Model

1. P4a只让Draft“少读”，不让Target少读，也不改变KV“写到哪里”。
2. 一个outer proposal只对应一个caller-owned production epoch。
3. request IDs和CPU mapping来自同一个InputBatch；epoch不是裸整数API。
4. Window exact、upper、table和valid counts来自同一prepared-generation snapshot。
5. borrowed workspace tensor只有通过single adapter validation后才有消费权。
6. upstream seam只携带read data，结构上不能改slot/position/query。
7. Ascend CPU exact seam避免metadata builder再从device取length；default None保持baseline。
8. Draft metadata独立build并经真实Target做nested/storage isolation。
9. 当前retirement只由serialized same-stream source semantics支持，不代表Async。
10. CPU tests证明contract；只有NPU physical-read oracle才能关闭`G-GQA-EAGER`。

## 26. P4a Review Resolution

本节预留给DeepSeek Independent Review之后的逐条事实裁决。本次交付尚未进行P4a独立
Review，因此：

- review finding count：N/A；
- review-fix commit：无；
- Architecture Escalation：无；
- 当前结论：implementation complete，等待independent review与NPU runtime evidence；
- 不得写`P4 FINAL PASS`。

`P4a IMPLEMENTED — G-GQA-EAGER RUNTIME GATE OPEN`
