# P6A Ascend-owned Pre-Capture Seam Investigation Notes

## Document Status

| Item | Value |
|---|---|
| Phase | P6A，P6的有界补充调查，不是P7 |
| Owner direction | 只调查A：当前架构中是否已有但尚未利用的Ascend-owned pre-capture seam |
| Investigation date | 2026-10-13（Asia/Shanghai） |
| Independent review adjudication | 2026-10-14（Asia/Shanghai） |
| vLLM baseline | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| vLLM tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |
| vLLM state | clean，zero diff，未修改 |
| vLLM-Ascend P6 Final | `7599497ab2694c4cf343f61f82f449980d8bad93` |
| P6 Final tree | `b4f7d12bd24b0a7632f9e606b29703a7c96278de` |
| vLLM-Ascend branch | `feature/p6-graph-read-carrier` |
| vLLM-Ascend state | clean，未修改production/test |
| New production commit | 无 |
| Canonical search ledger | `P6A_Ascend_Capture_Seam_Search_Ledger.md` |
| Final P6A outcome | **NOT_FOUND_AFTER_REVIEW** |

### Authority Inputs Read

本轮以完整P0–P6演进链为约束，而不是只按关键词搜索源码。读取的权威材料为：

1. `MRV2_Speculative_Draft_Sliding_Window_Final_Design.md`
2. `MRV2_Draft_Window_Implementation_Plan.md`
3. `P1_Policy_Math_Types_Implementation_Notes.md`
4. `P2_Inventory_FullSource_Provider_Implementation_Notes.md`
5. `P3_Lease_Workspace_Transport_Store_Implementation_Notes.md`
6. `P4_Draft_Attention_Eager_Integration_Implementation_Notes.md`（SUPERSEDED prototype，仅作历史）
7. `P4a_Ascend_Only_Eager_Integration_Implementation_Notes.md`
8. `P4b_Eagle3_StaticK_Eager_Integration_Implementation_Notes.md`
9. `P5_Ascend_Only_Graph_Binding_Implementation_Notes.md`
10. `P5_DeepSeek_Independent_Review.md`
11. `P6_Capture_Runtime_Identity_Spec.md`
12. `P6_Graph_Consumer_Matrix.md`
13. `P6_Graph_Read_Carrier_Per_Consumer_Implementation_Notes.md`
14. `P6_Replay_Update_Timeline.md`
15. `P6_Route_Fingerprint_Spec.md`
16. `P6_DeepSeek_Independent_Review.md`

这些材料用于固定P1–P4 read/write boundary、P5 ownership/source-spy边界、P6 replay/update
carrier与CaptureIdentity事实，以及R-REPO-01；当前exact source仍高于文档中的旧路径或旧行号。

## 1. 为什么有P6A

P5建立了instance-owned provider、稳定backing、完整identity和source spy。P6又把明确的Window read carrier接到了replay/update侧：provider存在时不能静默回退Target metadata，Draft metadata必须private，真实backend attribution在`update_full_graph_params`入口解析。

但P6 review确认了一条不可绕开的断链：P6 replay/update carrier没有进入startup
capture实际绑定的operand。独立Review进一步纠正了原论据：这不是所有route都由pinned vLLM
独占metadata构建。Eagle3 AR decode的真实per-step metadata由Ascend override构建；断点在于
现有Window分支依赖live proposal/P3 generation，capture期不存在该read source，并且Graph硬闸
仍关闭。DFlash的dummy metadata才完全由upstream helper构建。P6因此诚实地保留：

```text
P6 GRAPH READ CARRIER: PASS on replay/update static path
P6 CAPTURE IDENTITY: PASS
P6 CAPTURE PATH: BLOCKED
GRAPH WINDOW USER GATE: STILL FAIL-CLOSED
```

Owner随后给出有界决策：Graph最终Required，但当前只允许穷尽A——寻找已经存在、P6尚未发现的Ascend-owned pre-capture seam。如果A不存在，不批准B（vendor-local capture assembly），也不批准C（修改vLLM）；冻结Graph Track，P7/P8转Eager Track。

## 2. 本轮问题与合法性标准

唯一问题：当前exact checkout是否已经存在一个合法接缝，使speculator instance可以在startup capture时把P6 persistent Window table/length显式送入最终operator/task？

合法接缝必须全部满足：

1. production只改`vllm-ascend`；
2. 不改vLLM、不依赖历史prototype；
3. 不是module global、ContextVar或import-time monkeypatch；
4. 不临时swap Target/full owners；
5. 不伪造request、generation、mapping_epoch；
6. 不复制整个upstream graph/capture manager；
7. instance-scoped；
8. 真正影响startup capture最终operator/task绑定的table/length或其backend carrier；
9. Window OFF严格baseline/no-op；
10. ownership、descriptor/bucket与Target/write isolation可由source/test证明。

只打日志不算；只在replay/update重绑不算；“这里未来可以新加hook”也不算“已经存在”。

## 3. Exact Baseline Audit

调查开始和结束均验证：

```text
vLLM HEAD  = 84030bbe3d74d99bad477a3d2e37a973ccd8865c
vLLM tree  = f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
vLLM status= clean

vLLM-Ascend HEAD  = 7599497ab2694c4cf343f61f82f449980d8bad93
vLLM-Ascend tree  = b4f7d12bd24b0a7632f9e606b29703a7c96278de
vLLM-Ascend status= clean
```

P6 lineage仍为：

```text
0702c89  P5 review-fix
  ↓
20673a1  P6 implementation
  ↓
7599497  P6 review-fix / Final
```

本轮没有branch、production/test改动或commit。

## 4. Source Preflight：真实Capture链

### 4.1 Eagle3 first-pass

```text
AscendAutoRegressiveSpeculator.capture
  → prefill_cudagraph_manager.capture
  → AutoRegressiveAclGraphManager.capture
  → observe_draft_window_graph_capture
  → model_capture_wrapper
  → pinned vLLM SpeculatorCudaGraphManager.capture
  → upstream local create_forward_fn(desc)
  → pinned vLLM prepare_inputs_to_capture
       → InputBatch.make_dummy
       → block_tables.get_dummy_block_tables
       → block_tables.get_dummy_slot_mappings
       → model_state.prepare_attn
  → AscendModelState.prepare_attn
       → Ascend build_attn_metadata
       → writes model_state.attn_metadata
  → draft prefill forward
  → AscendAttentionBackendImpl.full_graph_fia/full_graph_fia_v2
       → resolve block_table + KV lengths from attn_metadata
       → graph_task_group_begin
       → FIA operator
       → graph_task_group_end
```

关键事实：标准非replicated-PCP route的`draft_prefill_attn_groups`返回`target_attn_groups`，`model_state`也是Target model state。直接把Window参数送进这条baseline builder会写Target-owned `model_state.attn_metadata`，不能作为合法read-only seam。

### 4.2 Eagle3 AR multi-step capture

```text
AscendAutoRegressiveSpeculator.capture
  → decode_cudagraph_manager.capture(_multi_step_decode, ...)
  → AutoRegressiveAclGraphManager.capture
  → Ascend-owned local create_forward_fn(desc)
       → pinned prepare_inputs_to_capture(...)
          （返回AttentionState，但当前代码丢弃该返回值）
       → lambda calls _multi_step_decode(...)
  → _multi_step_decode
       → speculator._build_draft_attn_metadata per step
       → model forward
       → Ascend backend operator capture
```

这条链揭示manager参数proxy为何不成立：`prepare_inputs_to_capture`中代理出来的metadata不是实际AR model consumer；真实metadata由Ascend
`_build_draft_attn_metadata`从speculator自己的`self.input_buffers/self.block_tables`重新构造，
且外层wrapper使其使用Ascend builder。Ascend在位置上能触达真实operand metadata，但现有
Window分支要求live proposal context、mapping epoch和generation-scoped P3状态，startup capture
没有这些runtime身份。若要注入P6 carrier，必须新增capture-scoped speculator transport/state或
Draft-private capture assembly，或临时swap owners。前两者属于当前未授权的新B工作，后者明确禁止。

### 4.3 DFlash capture

```text
AscendDFlashSpeculator.capture/proposal graph setup
  → DFlashAclGraphManager.capture
  → observe_draft_window_graph_capture
  → model_capture_wrapper
  → pinned vLLM DFlashCudaGraphManager.capture
  → upstream local create_forward_fn(desc)
  → upstream _prepare_dflash_inputs_to_capture
       → InputBatch.make_dummy
       → block_tables.get_dummy_block_tables
       → block_tables.get_dummy_slot_mappings
       → upstream module build_attn_metadata（被Ascend import-time patch指向Ascend builder）
  → _generate_draft forward
  → Ascend backend operator capture
```

对DFlash这一route，Ascend manager在调用`super().capture`前只能传传统owners；upstream helper
签名没有provider/read carrier/descriptor sink。该结论不能外推到Eagle3 AR decode。

### 4.4 DSpark capture

DSpark复用DFlash graph manager和capture helper。它覆盖runtime metadata build细节，但没有独立pre-capture入口。因此DFlash结论原样适用；不能把继承关系误写成一条新seam。

## 5. Source Preflight：最后Ascend控制点

### 5.1 Route-specific metadata控制点

不能把所有route统一描述成“Ascend manager只在upstream dummy build之前传owner”：

- Eagle3 first-pass：upstream先构造initial dummy metadata，但Ascend `_prefill`在operator前结构上
  可以整体替换；当前Window分支因capture期没有live P3 generation且Graph mode硬闸而不可用。
- Eagle3 AR decode：generic prepare返回值被丢弃，真实per-step metadata动态派发到Ascend
  `_build_draft_attn_metadata`；当前缺少capture-scoped read source/identity，而非metadata不可达。
- DFlash/DSpark：`DFlashAclGraphManager.capture`进入upstream helper前只能传传统owners；helper
  没有P6 provider/read carrier/descriptor sink。

参数proxy看似可行，实际无法同时满足：

- Eagle3 first-pass Target metadata owner不被写；
- Eagle3 AR真实per-step metadata consumer被控制；
- DFlash/DSpark descriptor/bucket与P6 CaptureIdentity绑定；
- read table改变而full slot/positions/query/write state不变；
- OFF exact baseline；
- 多manager/多实例无共享泄漏。

补齐这些要求本身就是新的vendor-local capture adapter/assembly，所以属于B，而不是A。

### 5.2 Operator前的最后点

`AscendAttentionBackendImpl.full_graph_fia`和`full_graph_fia_v2`是实际`graph_task_group_begin`与FIA operator前最后的Ascend点。它们从`attn_metadata`提取table/length，记录弱引用并调用operator，因此在技术上最接近“注入点”。

但当前exact source中没有现成的：

- speculator/P6 provider引用；
- CaptureIdentity；
- capture descriptor/bucket；
- route和global gid；
- Eagle3 first-pass/AR step ordinal；
- write-side reference；
- provider缺失carrier时的hard fail协议。

在backend中新加这些字段、注册方法、session与consumer排序可以成为未来设计，但这正是一个新Ascend-owned backend transport。Owner本轮只批准寻找已有seam，不批准实现B，所以该候选判为`REQUIRES_VENDOR_CAPTURE_ASSEMBLY`，不是`VALID_SEAM`。

### 5.3 Route-specific不可控边界

对Eagle3 first-pass与DFlash，按`BatchExecutionDescriptor`创建initial/dummy inputs、table和metadata
的代码位于pinned vLLM manager的local `create_forward_fn`/helper中；这些closure不接受Ascend
callback/provider。对Eagle3 AR decode，metadata本身由Ascend构建，但当前没有capture-scoped
Window source可供builder读取。修改upstream helper属于C；在Ascend override/backend中新增
capture-scoped transport或assembly属于B。两者当前均未授权。

## 6. 分层搜索结果

### A. Ascend Graph Manager层

检查了AR、DFlash、DSpark、base model graph manager、model wrapper、communicator scope、descriptor
creation和breakable graph wrapper。没有发现能把instance-owned P6 table/length接到各route真实
capture operand的现有callback/provider/descriptor slot。

AR decode的manager和Ascend speculator能触达真实per-step metadata，但没有现成capture-scoped
read source；first-pass和DFlash仍由upstream initial/dummy路径决定输入。已有manager override提供
传统owner参数、capture flags、communicator scope、模型wrapper和观察点，不提供完整P6 capture
carrier。结论仍是没有A类seam。

### B. Ascend Attention Backend层

检查了metadata builder、FIA/PA full graph paths、GraphParams、graph-task registration、update provider和attention layer/module注册。Backend能看到最终operand，但没有现成P6 provider/capture identity接口；GraphParams为module-global capture结果存储，不是instance-owned注入通道。结论：没有A类seam；backend点只构成未来B候选。

### C. compilation / acl_graph层

`ACLGraphWrapper`文档明确说明其不保存persistent input buffer，外部必须提前准备；它只capture/replay收到的model args，而attention metadata通过ForwardContext/attention layer消费。`BreakableACLGraphWrapper`只设置capture flag和workspace lifetime。`update_full_graph_params`及`graph_task_update_*`位于replay后，只能是`REPLAY_ONLY`。结论：没有A类seam。

### D. Existing project patch architecture

检查了：

- `build_attn_metadata_wrapper`和`build_draft_attn_metadata_factory`；
- `patch_eagle_speculator.py`、`patch_dflash_speculator.py`；
- PCP对`prepare_inputs_to_capture`的module symbol替换；
- 310P custom capture；
- attention module buffer registry；
- DeviceMetadataExecutor；
- LoRA/MoE capture callbacks。

其中metadata wrapper、PCP和import-time patches均依赖module/class shared mutation，违反本轮明确禁令；310P复制/改写capture并临时替换`AscendInputBatch.make_dummy`，属于不同device route和B类assembly；buffer registry只分配stable storage，不选择operator operand；DeviceMetadataExecutor和task update是runtime/replay阶段；LoRA/MoE callbacks不在Draft Attention table/length数据链。结论：没有A类seam。

### E. Pinned vLLM read-only

完整追踪generic、AR和DFlash capture helper后确认：dummy block table、slot mapping和initial
length由upstream local closure/helper组装；DFlash metadata也由upstream helper构建。Eagle3 AR
decode是例外：真实per-step metadata由Ascend override构建，但该override没有capture-scoped P6
read source，现有Window分支只接受live generation。没有optional provider/sink能同时表达
CaptureIdentity、descriptor/bucket、Draft-only read override与Target/write isolation。结论：当前
授权边界下断链成立，但不能再表述成Ascend技术上完全无法触达metadata。

## 7. 被拒绝方案与原因

| 方案 | 为什么不采用 |
|---|---|
| 在manager前后打日志/source spy | 只能观察，不能改变capture operand |
| 依赖P6 replay/update carrier | 发生在startup capture以后，不是pre-capture seam |
| BlockTables/InputBuffers proxy | 无法覆盖AR真实consumer和first-pass Target isolation；完成它需要新assembly |
| 在`ModelWithContext`中替换metadata | dummy metadata已建立；需使用ForwardContext/隐式状态，违反hidden transport/ContextVar边界 |
| 在metadata builder上挂provider | 当前没有该接口；builder可能属于Target；新增即B |
| 在`full_graph_fia*`查provider | 当前没有attachment/identity/ordinal协议；新增即B |
| 使用GraphParams全局表 | module-global，不instance-scoped，而且是capture结果存储 |
| PCP式patch `prepare_inputs_to_capture` | shared module mutation，明确禁止 |
| import-time patch upstream module | 明确禁止 |
| 310P方案移植到910 | vendor-local capture assembly且包含shared mutation；B未授权 |
| 修改pinned vLLM helper签名 | C未授权，违反R-REPO-01 |

## 8. Source Drift

没有发现能推翻Final Design Frozen语义的新source事实。独立Review纠正了Eagle3 AR metadata
ownership，但没有发现符合全部A判据的既有seam；因此freeze结论保留、支撑理由收紧。

本轮补充的精确事实是：

1. AR decode manager虽拥有local `create_forward_fn`，`prepare_inputs_to_capture`返回的metadata没有
   成为真实AR decode consumer；真实consumer metadata由Ascend `_build_draft_attn_metadata`
   构建。但现有Window分支依赖live P3 generation，故它仍不是现成capture seam。
2. `full_graph_fia*`是operator前最后Ascend点，但缺少任何现成P6/capture identity transport；它是潜在B方向，不是A。
3. 当前工程中确有多种patch/capture特例，但都属于shared mutation、不同route或vendor-local assembly，不能拿它们规避owner边界。

## 9. 为什么没有写Red Test或Production

如果找到合法A，要求先在P6 Final上写能证明dummy/full operand仍被capture的red test，再实现seam。穷尽搜索没有找到A，因此不存在一个合法production入口可供实现和测试。

为了“做出commit”而新增backend hook、proxy或capture builder会越过B；为了让test变红而安装provider只会复现P6已有的startup hard fail，不会证明存在seam。故本轮正确工程行为是：不修改source/test、不建空commit，并保留Graph Gate。

## 10. Static Regression Evidence

执行：

```bash
env VLLM_VERSION=0.29.0 \
  PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
  .venv/bin/python -m pytest -q \
  tests/ut/spec_decode/test_draft_window_graph_binding.py \
  tests/ut/spec_decode/test_draft_window_graph_carrier.py
```

结果：

```text
69 passed, 1 warning in 0.10s
```

warning只是pinned checkout没有生成`vllm._version`，不代表P6A或Graph PASS。因为production未变，不重跑全P1–P6套件；P6 Final的完整测试证据仍以P6 Notes和review resolution为准。

## 11. Ownership与Invariant Audit

| Invariant | P6A结果 |
|---|---|
| vLLM exact/clean/no diff | 保持 |
| vLLM-Ascend P6 Final exact/clean | 保持 |
| production只改vllm-ascend | 本轮零production修改 |
| no module-global Window transport | 保持 |
| no ContextVar Window transport | 保持 |
| no import-time Window monkeypatch | 保持 |
| no Target/full owner swap | 保持 |
| no fake capture generation/epoch | 保持 |
| Target metadata/full slot/positions/query untouched | 保持；本轮无runtime行为变化 |
| OFF/forced-OFF baseline | 保持 |
| P6 replay/update carrier | 未改，host/static PASS边界保持 |
| startup capture carrier | 仍BLOCKED |
| Graph user Gate | 仍fail closed |
| NPU Graph evidence | 未提供/未验证 |

## 12. Owner Direction — Graph vs Eager Track

### Graph Track

- Graph仍是最终Required方向，不因本轮失败而从产品目标删除。
- 当前A已按exact source穷尽，没有找到合法seam。
- B（vendor-local capture assembly）未授权。
- C（修改vLLM）未授权。
- 因此Graph Track冻结；P7/P8不得静默删除P1/P2的Graph fail-closed gate或把replay/update static carrier写成Graph支持。
- 所有依赖Graph Window的route继承`GRAPH_BLOCKED`。

### Eager Track

- Owner明确允许P7/P8优先继续Eager Track。
- P4a/P4b已有eager基础与各自NPU/open gate边界；Graph冻结不应让非Graph工作停滞。
- 本文不开始P7，只记录其进入资格。

### 重新打开Graph Track的触发条件

满足以下任一条件后，由owner重新立项：

1. owner批准B，并接受vendor-local capture assembly的drift/维护成本；
2. R-REPO-01改变，允许设计并推动vendor-neutral vLLM hook；
3. pinned/upstream vLLM出现可用的pre-capture read carrier hook；
4. Ascend/backend团队指出一个此前未知、且能通过Search Ledger全部判据的现有seam。

重新打开后仍必须单独完成NPU capture address、A/B/A、timeline/effective generation、physical read-set、stream lifetime和performance验证；本次静态调查不能替代这些证据。

## 13. Files and Git Result

本轮只生成/更新外部Notes：

- `P6A_Ascend_Capture_Seam_Search_Ledger.md`
- `P6A_Ascend_Owned_Pre_Capture_Seam_Investigation_Notes.md`
- `P6A_Codex_Final_Review_Adjudication_and_Graph_Track_Freeze.md`
- `MRV2_Draft_Window_Implementation_Plan.md`尾部Owner Addendum

没有修改：

- `vllm` production/test；
- `vllm-ascend` production/test；
- Final Design Frozen内容；
- P1–P6历史commit。

没有创建`feature/p6a-ascend-capture-seam`，因为只有找到VALID_SEAM并实际实现时才应建分支/commit。

## 14. Final Verdict

```text
P6A ASCEND-OWNED CAPTURE SEAM: NOT FOUND
P6 CAPTURE PATH: FROZEN BLOCKED
B/C: NOT AUTHORIZED
GRAPH USER GATE: STILL FAIL-CLOSED
GRAPH TRACK: FROZEN
P7 EAGER TRACK: READY BY OWNER DIRECTION
```

这不是“Graph不需要做”，也不是“P6 replay/update实现无效”，更不是“Ascend技术上永远无法
构建capture metadata”。准确含义是：在当前pinned vLLM、R-REPO-01和owner只批准已有A的共同
边界内，没有已存在的pre-capture operand injection seam；继续写代码将不可避免地进入尚未批准
的新capture-scoped B设计或C。

## 15. Independent Review Resolution

Review：`P6A_DeepSeek_Independent_Review.md`，裁决日期：2026-10-14。

| ID | Severity | Reviewer finding | Codex reproduction | Resolution | Evidence | Action |
|---|---|---|---|---|---|---|
| F-01 | Major | 原报告称Ascend manager只能在upstream dummy metadata前传传统owner；Eagle3 AR真实metadata其实由Ascend构建 | 已复现 | `ACCEPTED` | Ascend manager丢弃generic prepare返回；upstream AR loop动态调用Ascend `_build_draft_attn_metadata`；wrapper切换到Ascend builder | 重写route-specific call chain和freeze理由；Outcome B不变 |
| F-02 | Minor | “prepare返回被丢弃”与“无seam”之间漏写真正consumer来源 | 已复现 | `ACCEPTED` | 真正consumer为Ascend override；其Window分支需要live proposal/P3 generation，startup capture没有 | 补齐consumer链和capture-scoped state缺口 |
| F-03 | Minor | P6 production docstring对Eagle3 AR ownership表述过宽 | 已复现 | `ACCEPTED` | `observe_draft_window_graph_capture`的概括适用于DFlash/initial dummy，不适用于AR per-step metadata | P6 Final保持冻结、不改production SHA；本Notes与最终报告记录勘误，未来获授权源码修改时收紧注释 |
| F-04 | Minor | P7 Eager必须显式要求Graph NONE，不能暗示自动降级 | 已复现 | `ACCEPTED` | capability inventory对`graph_mode != NONE`记录failure，进入Gate时抛`NotImplementedError`；AR另有三处runtime硬闸 | Plan固定`graph_mode=NONE`/等价`enforce_eager`前置 |
| Q-01 | Question | Freeze应基于新capture-scoped transport未授权而非技术不可能，并询问该形态是否属于B | 授权与技术事实分别复核 | `PARTIALLY_ACCEPTED` | 技术区分成立；但本轮owner只授权寻找“已存在A”，A失败后明确不批准B/C | 以authorization boundary冻结；本轮不再次替owner选择B/C |
| Q-02 | Question | host/static无法证明captured地址、effective generation和NPU timeline | 已复现 | `ACCEPTED` | P6 typed timeline仍将effective generation置为unknown/`NEEDS_NPU_TIMELINE` | 保持`P6 NPU GRAPH: NOT VERIFIED` |

裁决统计：`ACCEPTED=5`，`PARTIALLY_ACCEPTED=1`，`REJECTED=0`，
`INSUFFICIENT_EVIDENCE=0`。没有假阳性seam需要撤销；撤销的是“Ascend被upstream结构性
排除在metadata构建之外”的过强论据。

```text
P6 STATIC FINAL: PARTIAL
P6 CAPTURE PATH: FROZEN BLOCKED
GRAPH TRACK: FROZEN
P7 EAGER TRACK: READY BY OWNER DIRECTION
```
