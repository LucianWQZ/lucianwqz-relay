# P6A Ascend-owned Pre-Capture Seam Search Ledger

## 1. 文档状态

| 项 | 值 |
|---|---|
| 调查日期 | 2026-10-13（Asia/Shanghai） |
| 独立Review裁决日期 | 2026-10-14（Asia/Shanghai） |
| 调查性质 | Owner 授权的 P6 有界补充探索；仅调查已有 Ascend-owned pre-capture operand injection seam |
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c`，clean，zero diff |
| vLLM tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |
| vLLM-Ascend | `7599497ab2694c4cf343f61f82f449980d8bad93`，clean |
| vLLM-Ascend tree | `b4f7d12bd24b0a7632f9e606b29703a7c96278de` |
| P6 已知事实 | CaptureIdentity PASS；replay/update carrier static PASS；startup capture BLOCKED；Graph user Gate fail closed |
| Production 修改 | 无 |
| 新 commit | 无 |
| 最终结论 | `NOT_FOUND_AFTER_REVIEW`；Graph freeze成立，但理由按F-01修正为“无既有合法seam且新capture-scoped transport未获授权”，不是“Ascend技术上无法触达metadata” |

本台账中的 `VALID_SEAM` 判定必须同时满足：只改 `vllm-ascend`、已存在、instance-scoped、能在 startup capture 真正改变 table/length 或后端 carrier、OFF 为严格 no-op、无 Target/full owner 临时替换、无 module global、无 ContextVar、无 import-time monkeypatch、无虚假 generation，并可从源码/测试证明 ownership。仅能观察、仅能 replay/update 重绑、或需要新增 capture assembly/transport 的候选均不算。

## 2. 判定枚举

- `VALID_SEAM`：当前 exact checkout 已存在且满足全部约束的注入接缝。
- `OBSERVATION_ONLY`：只能看见 capture 或记录状态，不能改变实际 capture operand。
- `REPLAY_ONLY`：只在 capture 已完成后的 replay/update 生效。
- `SHARED_MUTATION`：依赖 module/class/global/shared owner 的临时替换，违反约束。
- `REQUIRES_VLLM_CHANGE`：必须改 pinned vLLM API/实现。
- `REQUIRES_VENDOR_CAPTURE_ASSEMBLY`：Ascend 可以新写适配，但这属于 owner 尚未批准的 B，而不是已有 A。
- `NOT_RELEVANT`：不处于 Draft Attention capture table/length 数据链。

## 3. Search Ledger

| Candidate | Exact source | Before/after dummy build | Can affect actual capture operand? | Instance-owned? | Target mutation? | vLLM change? | Verdict |
|---|---|---|---|---|---|---|---|
| AR manager outer capture override | `vllm_ascend/worker/v2/spec_decode/autoregressive/aclgraph.py::AutoRegressiveAclGraphManager.capture` | first-pass转给upstream closure；AR decode由Ascend local `create_forward_fn`发起，并进入Ascend `_multi_step_decode` | AR decode的真实per-step metadata可经动态派发触达Ascend override；但现有manager接口不提供capture-scoped P6 source/identity | manager/speculator可instance-owned | first-pass传统prepare仍写Target ModelState；AR owner swap已禁止 | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| Eagle3 first-pass `super().capture` + Ascend `_prefill` | upstream先建dummy metadata，再把对象传给Ascend `_prefill` | metadata初始值在upstream closure构造；Ascend `_prefill`位于operator前并可整体替换 | 结构上可替换，但现有Window分支要求live P3 proposal且对graph mode硬拒绝；没有capture-scoped read source | speculator method是instance-owned | 初始prepare写Target `model_state.attn_metadata`；安全替换需Draft-private capture状态 | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| Eagle3 AR decode local `create_forward_fn` | `vllm_ascend/.../autoregressive/aclgraph.py:111-138` | `prepare_inputs_to_capture`返回值被丢弃；随后真正metadata由每步Ascend `_build_draft_attn_metadata`构建 | **能触达实际capture operand metadata**，但现有Window分支依赖generation-scoped P3 state，capture期无proposal/generation且Graph硬闸关闭；需新增capture-scoped state/transport | manager/speculator可instance-owned | 合法新设计可保持Target隔离；当前不存在该transport | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| Ascend Eagle3 `_build_draft_attn_metadata` Window分支 | `vllm_ascend/.../autoregressive/speculator.py:605-666` | During actual AR capture forward, before FIA operator | 结构上具备table/length替换能力；但仅在`_eagle3_window_is_active()`时进入，而该条件要求live proposal context/P3 generation | speculator instance-owned | eager实现已有isolation | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| DFlash manager outer capture override | `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py::DFlashAclGraphManager.capture` | Before upstream `_prepare_dflash_inputs_to_capture` | 只能替换整套 `input_buffers/block_tables/attn_groups`；无 operand/provider 参数 | manager 有 speculator ref；upstream helper无 provider | 代理必须额外保证 full slot/write owner，当前无现成协议 | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| DSpark inherited DFlash capture | `vllm_ascend/worker/v2/spec_decode/dspark/speculator.py` + DFlash manager | 与 DFlash 相同 | 无 DSpark 专属 pre-capture seam | 与 DFlash 相同 | 与 DFlash 相同 | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| Manager argument proxy for `BlockTables` | AR/DFlash capture signatures；upstream `get_dummy_block_tables/get_dummy_slot_mappings` | Before dummy build | 理论上 table proxy 可改变 dummy read table；但 AR decode真实 metadata不消费其返回值，first-pass又写 Target | proxy可 instance-owned | 很容易把 slot mapping或Target metadata一并改变；完整隔离需新 adapter | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| Manager argument proxy for `InputBuffers` | 同上；upstream `InputBatch.make_dummy` | Before dummy build | 理论上可改变 seq lengths；不能单独完成 table+length+descriptor+Target isolation | proxy可 instance-owned | first-pass仍通过 Target ModelState；AR decode仍读 speculator owners | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| Pinned vLLM AR dummy builder | `vllm/v1/worker/gpu/spec_decode/autoregressive/cudagraph_utils.py::SpeculatorCudaGraphManager.capture` | first-pass的initial dummy metadata build；Ascend AR decode不使用这里的返回metadata | 对first-pass是initial source，但Ascend `_prefill`仍位于operator前；对AR decode不是最终metadata source | upstream manager-owned closure | 当前直接调用supplied Target ModelState/owners | 是 | `REQUIRES_VLLM_CHANGE`（若选择upstream hook方案C） |
| Pinned vLLM generic dummy builder | `vllm/v1/worker/gpu/cudagraph_utils.py::prepare_inputs_to_capture` | Actual dummy build | 直接选择 dummy table/slot/length并调用 `model_state.prepare_attn`；无 hook | 否 | 写 supplied `model_state.attn_metadata` | 是 | `REQUIRES_VLLM_CHANGE` |
| Pinned vLLM DFlash dummy builder | `vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py::_prepare_dflash_inputs_to_capture` | Actual dummy build | 直接创建 dummy batch/table/slot并调用 builder；无 hook | 否 | 由传统 owners/builders决定 | 是 | `REQUIRES_VLLM_CHANGE` |
| `AscendModelState.prepare_attn` | `vllm_ascend/worker/v2/model_states/default.py::AscendModelState.prepare_attn` | During dummy build | 能根据传入 table/length建 metadata，但没有 Window provider/descriptor/capture identity | ModelState instance-owned | 无条件写 `self.attn_metadata`；Eagle3 first-pass 的该实例属于 Target | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| `build_attn_metadata` | `vllm_ascend/worker/v2/attn_utils.py::build_attn_metadata` | During dummy build | 能消费显式 table/length，但调用者没有传入 P6 carrier；函数无 provider入口 | 函数本身无 owner | 不自行找 Target，但 caller决定slot/positions/query | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| `AscendAttentionMetadataBuilder.build_for_graph_capture` | `vllm_ascend/attention/attention_v1.py::AscendAttentionMetadataBuilder.build_for_graph_capture` | After common dummy metadata assembly, before operator | 只有 common metadata参数；无 speculator/provider/route/descriptor入口 | builder instance-owned | Eagle3 first-pass常使用 Target builders；挂 provider会混淆 ownership | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| `ModelWithContext` | `vllm_ascend/worker/v2/aclgraph_utils.py::ModelWithContext.forward` | After dummy metadata build, before model/operator | 只设置 `_EXTRA_CTX` capture flags；不持有 table/length，也不替换 ForwardContext metadata | wrapper instance-owned | 若借 ForwardContext 隐式换 metadata将成为 hidden ContextVar/shared transport | 否 | `OBSERVATION_ONLY` |
| `model_capture_wrapper` | `vllm_ascend/worker/v2/aclgraph_utils.py::model_capture_wrapper` | Around capture | 只临时包装 speculator.model；没有 metadata operand API | context与speculator关联 | 临时改 `speculator.model` 是已有行为，但无法注入table/length | 否 | `OBSERVATION_ONLY` |
| `AscendAttentionBackendImpl.full_graph_fia` | `vllm_ascend/attention/attention_v1.py::AscendAttentionBackendImpl.full_graph_fia` | Last Ascend point immediately before graph-task registration/operator | **能**决定实际 `block_table`/KV length；但当前没有 provider attachment、capture identity、route/bucket或consumer ordinal接口 | Attention impl instance-owned | 直接改成查外部 state需新 instance transport和Target/Draft区分 | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| `AscendAttentionBackendImpl.full_graph_fia_v2` | 同文件 `full_graph_fia_v2` | Last Ascend point immediately before operator | 与上项相同；当前只从 `attn_metadata`取 operand | instance-owned | 同上 | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| Attention layer/module persistent buffer registry | `vllm_ascend/attention/utils.py::get_or_register_attention_buffer` | 可在capture前分配稳定buffer | 只解决storage ownership，不决定 capture metadata/operator选择哪个buffer | module-owned，非speculator-owned | 不直接污染Target；但无route/provider绑定 | 否 | `NOT_RELEVANT` |
| `static_forward_context` attention lookup | `VllmConfig.compilation_config.static_forward_context` consumers | Before/during capture | 只能定位module；无 Draft Window operand callback | model-wide shared registry | 容易跨Target/Draft/layer泄漏 | 否 | `NOT_RELEVANT` |
| FIA `graph_task_group_begin/end` | `vllm_ascend/attention/attention_v1.py` full-graph functions | At actual operator capture | 记录的就是现有 metadata解析出的 operand；无 pre-begin parameter-provider callback | task lists存入module-global GraphParams | 不改变Target，但新增传输需改backend协议 | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| `GraphParams.attn_params/handles/events` | `vllm_ascend/compilation/acl_graph.py::GraphParams` 及 `_draft_graph_params*` | Filled during/after task capture | 可记录已捕获operand；不能在dummy build前选择operand | module-global，而非instance-scoped | 无直接Target写；跨实例共享 | 否 | `SHARED_MUTATION` |
| `ACLGraphWrapper` | `vllm_ascend/compilation/acl_graph.py::ACLGraphWrapper` | Around compiled model capture/replay | 明确不保存persistent input buffers，假设外部准备；只看model args和ForwardContext | wrapper instance-owned | 无 table/length参数；新增hook属于新assembly | 否 | `OBSERVATION_ONLY` |
| `BreakableACLGraphWrapper` | `vllm_ascend/compilation/breakable_aclgraph.py` | Around breakable graph capture | 仅设置capture flag/维护workspace；无Draft operand入口 | wrapper instance-owned | 否 | 否 | `OBSERVATION_ONLY` |
| `update_full_graph_params` | `vllm_ascend/compilation/acl_graph.py::update_full_graph_params` | After replay in current manager order | P6 carrier已能到达此处；只能更新captured task，不能证明startup binding | 调用参数显式；backend task state全局 | 不污染Target；但不是pre-capture | 否 | `REPLAY_ONLY` |
| backend `update_graph_params` | `vllm_ascend/attention/attention_v1.py::AscendAttentionBackendImpl.update_graph_params` | After replay | 能rebind task参数；P6已静态接通；不是startup operand injection | static method + GraphParams | 否 | 否 | `REPLAY_ONLY` |
| `DeviceMetadataExecutor` | `vllm_ascend/worker/device_metadata.py` | Runtime side-stream | 运行时提交metadata task；没有speculator startup capture注册或table/length provider | executor instance-owned | 否 | 否 | `REPLAY_ONLY` |
| PCP capture adaptation | `vllm_ascend/worker/v2/aclgraph_utils.py::ModelAclGraphManager.capture` | Before generic dummy build | 通过重写 upstream module symbol改变capture helper | 否，module-level mutation | 可改变共享capture路径 | 否 | `SHARED_MUTATION` |
| `build_attn_metadata_wrapper` / factory | `vllm_ascend/worker/v2/attn_utils.py` | Around metadata build | 通过临时替换 upstream module函数提供Ascend builder/positions | 否，module-global function mutation | 存在跨实例/并发风险，不可作为新Window transport | 否 | `SHARED_MUTATION` |
| import-time speculator patches | `vllm_ascend/patch/worker/patch_v2/patch_eagle_speculator.py`、`patch_dflash_speculator.py` | Import/startup | 能替换manager class/function，但明确属于import-time monkeypatch | 否 | 共享module行为 | 否 | `SHARED_MUTATION` |
| 310P custom capture manager | `vllm_ascend/_310p/worker/v2/spec_decode/aclgraph.py` | Own capture implementation | 证明vendor可以复制/改写capture流程；但这是不同hardware route且包含class monkeypatch、vendor-local assembly | manager部分instance-owned | 含 `AscendInputBatch.make_dummy` 临时class mutation；非标准910 route | 否 | `REQUIRES_VENDOR_CAPTURE_ASSEMBLY` |
| Routed-experts capture callback | `vllm_ascend/patch/worker/patch_routed_experts_capture.py` 及 upstream MoE router | Before/during MoE capture | 只捕获expert IDs，与Draft Attention table/length无关 | model/layer scoped | 否 | 否 | `NOT_RELEVANT` |
| LoRA capture hook | generic model graph manager capture signature | Before generic model capture | 仅更新LoRA capture state；speculator manager接口不暴露等价attention operand hook | 非Draft carrier | 否 | 需要扩展上游speculator接口 | `NOT_RELEVANT` |
| P5/P6 source spy | `draft_window_graph.py::observe_draft_window_graph_*` | Before/after capture/replay/update | 记录identity/source；`observe_draft_window_graph_capture`在provider存在时故意hard fail | provider instance-owned | 无 | 否 | `OBSERVATION_ONLY` |

## 4. 关键否决证明

### 4.1 Manager 参数不是完整 seam

Manager与speculator override是最容易误判的候选。独立Review确认：不能把它们概括为
“Ascend只能在upstream dummy build之前传传统owner”。Eagle3 AR decode的真实per-step
metadata确实由Ascend override构建。仍然不存在合法A的原因是：

1. Eagle3 first-pass 传入的是 Target `model_state`、`target_input_buffers` 和通常的 `target_attn_groups`；`AscendModelState.prepare_attn` 会写 `self.attn_metadata`。用 Window 参数直接调用会污染 Target，违反 Frozen read/write boundary。
2. Eagle3 AR decode 的 Ascend manager调用 `prepare_inputs_to_capture` 后丢弃其返回metadata；真正forward在`_multi_step_decode`内动态派发到Ascend `_build_draft_attn_metadata`。因此Ascend在位置上能触达真实operand metadata；但现有Window分支要求live proposal context、mapping epoch和generation-scoped P3 state，startup capture不存在这些runtime身份，且Graph mode被显式硬闸拒绝。
3. DFlash/DSpark helper在upstream local closure内按descriptor自建dummy metadata；参数proxy既拿不到完整P6 capture fingerprint，也没有现成机制将每个bucket绑定到P6 CaptureIdentity。

要补齐这些缺口，必须增加独立capture-scoped identity/read source与speculator/backend transport，
或增加Draft-private capture assembly。技术上并非证明“不可实现”；它们是新的Ascend-owned
设计工作，超出只寻找已有A seam的授权，并落入当前未授权的B侧。

### 4.2 Backend是最后控制点，但不是现成seam

`full_graph_fia*` 确实在 `graph_task_group_begin` 前读取 `attn_metadata` 并把 `block_table`/length交给FIA operator，也把它们记录进GraphParams。它是“最后一个Ascend可修改点”，但当前函数签名和实例状态中没有：

- Draft Window provider引用；
- CaptureIdentity/descriptor/bucket；
- Eagle3 first-pass与AR step consumer ordinal；
- DFlash/DSpark route identity；
- P6 write-side reference；
- provider存在但carrier缺失的hard-fail协议。

因此利用此点需要新增backend-level provider attachment与capture session/ordinal协议，并证明Target与Draft layer隔离。这是一个可能的未来B类设计方向，但 owner本轮未授权，不能标为 `VALID_SEAM`。

### 4.3 Replay update不等于pre-capture

`update_full_graph_params -> AscendAttentionBackendImpl.update_graph_params -> graph_task_update_*` 已被P6静态接通。但当前manager顺序是 `REPLAY -> CONSUMER -> UPDATE`。它既不控制startup dummy operand，也不能仅靠源码证明UPDATE(N)影响replay N还是N+1。因此所有update候选均为 `REPLAY_ONLY`。

## 5. 最后可控点与不可控边界

```text
Eagle3 first-pass:
upstream initial dummy metadata
  → Ascend _prefill (structurally can replace metadata)
  → current Window branch needs live P3 generation and rejects graph mode

Eagle3 AR decode:
Ascend manager discards generic dummy metadata
  → upstream loop dynamically dispatches to Ascend _build_draft_attn_metadata
  → current Window branch needs live P3 generation and has no capture-scoped source

DFlash / DSpark:
upstream _prepare_dflash_inputs_to_capture fixes dummy metadata
  → no existing Ascend method-level carrier seam

All routes:
AscendAttentionBackendImpl.full_graph_fia*
  → operator前最后Ascend点；当前无provider/capture identity/ordinal协议
  → graph_task_group_begin → FIA operator → graph_task_group_end
```

上述route中没有一个点同时具备“**当前已存在**、instance-scoped、P6-aware、能在startup
capture获得合法read source、Target隔离、descriptor/bucket可验证”全部条件。Eagle3 AR的
metadata ownership纠正了原论据，但不产生一个现成合法A seam。

## 6. Search Completeness

本次检查覆盖：

- `AutoRegressiveAclGraphManager`、`DFlashAclGraphManager`、DSpark继承关系；
- base Ascend model graph manager、model capture wrapper、breakable graph wrapper；
- pinned vLLM AR、DFlash和generic capture helpers及其local closures；
- Ascend `ModelState.prepare_attn`、generic metadata builder、per-backend metadata builder；
- `AscendAttentionBackendImpl` FIA/PA capture和update入口；
- `graph_task_group_*`、`graph_task_update_*`全部vLLM-Ascend生产引用；
- `ACLGraphWrapper`、GraphParams、workspace/resource管理；
- DeviceMetadataExecutor、attention buffer registry；
- PCP capture改写、metadata builder wrapper、import-time patches；
- 310P自定义capture、LoRA/MoE capture callbacks；
- module-global、ContextVar、callback/provider/resource/descriptor关键词全仓搜索；
- P5/P6 source spy与provider的所有production引用。

未发现此前遗漏的合法 callback/provider/descriptor slot/resource handle，可以在 startup dummy metadata/operator capture前由speculator instance显式提供P6 table/length。

## 7. Verification

未修改production，因此没有人为制造red/green实现测试。为确认P5/P6当前静态基线未漂移，执行：

```bash
env VLLM_VERSION=0.29.0 \
  PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
  .venv/bin/python -m pytest -q \
  tests/ut/spec_decode/test_draft_window_graph_binding.py \
  tests/ut/spec_decode/test_draft_window_graph_carrier.py
```

结果：`69 passed, 1 warning`。warning为pinned vLLM checkout缺少生成的`vllm._version`，不经过P6A数据路径。

## 8. Verdict

```text
P6A ASCEND-OWNED SEAM SEARCH:
EXHAUSTED — NONE FOUND

P6 CAPTURE PATH:
FROZEN BLOCKED

REASON:
no existing Ascend-owned pre-capture operand injection seam exists in the pinned baseline;
the closest Eagle3 Ascend overrides require a new capture-scoped transport/state design.

B — vendor-local capture assembly:
NOT AUTHORIZED

C — vLLM change:
NOT AUTHORIZED

GRAPH TRACK:
FROZEN UNTIL OWNER REOPENS
```

恢复Graph Track的触发条件仅有：owner批准B；R-REPO-01改变；upstream出现可用hook；或Ascend/backend团队指出一个能通过本台账全部判据的新合法seam。

## 9. Independent Review Resolution（2026-10-14）

| ID | Severity | Finding | Resolution | Evidence | Action |
|---|---|---|---|---|---|
| F-01 | Major | 原报告把AR decode概括为Ascend只能传传统owner，遗漏实际metadata由Ascend override构建 | `ACCEPTED` | Ascend manager丢弃generic prepare返回；upstream per-step loop动态调用Ascend `_build_draft_attn_metadata`；Ascend wrapper把builder切到Ascend版本 | 重写AR call chain、Search Ledger和freeze理由；Outcome B不变 |
| F-02 | Minor | “prepare返回被丢弃”到“无seam”之间缺少真正consumer来源 | `ACCEPTED` | 真正consumer metadata由Ascend override构建，但Window分支依赖live P3 generation/capture期不存在 | 补齐该中间链并明确阻断是capture-scoped state缺失/未授权，不是metadata不可达 |
| F-03 | Minor | P6 production docstring对Eagle3 AR metadata ownership表述过宽 | `ACCEPTED` | `draft_window_graph.py::observe_draft_window_graph_capture`称upstream内部build private dummy metadata；只对DFlash/initial dummy普遍成立 | 本轮冻结production SHA，不改代码；本台账和最终裁决显式勘误，未来获授权源码修改时同步收紧注释 |
| F-04 | Minor | Eager Track必须明确Graph配置是启动期hard fail而非自动降级 | `ACCEPTED` | `draft_window.py` inventory记录`graph_mode != NONE`失败，`require_single_group_direct_prefix()`抛`NotImplementedError`；Eagle3还有三处runtime硬闸 | Plan/final报告明确P7 Eager仅允许`graph_mode=NONE`/等价`enforce_eager`，不能依赖fallback |
| Q-01 | Question | Freeze理由应是新capture-scoped transport未授权，而不是技术不可能；询问该形态是否属于B | `PARTIALLY_ACCEPTED` | 技术区分成立；但本轮owner已明确只允许“已有A seam”，A失败后不批准B/C，因此任何新增capture-scoped transport都超出授权 | 将freeze依据修正为authorization boundary；无需在本轮重新请求owner选择B/C |
| Q-02 | Question | host/static不能证明实际captured地址、timeline或effective generation | `ACCEPTED` | P6 timeline保留`NEEDS_NPU_TIMELINE`，本轮无NPU证据 | 保持`P6 NPU GRAPH: NOT VERIFIED`；Graph恢复后仍需独立NPU campaign |

Review后最终裁定：`NOT_FOUND_AFTER_REVIEW`。不存在需要撤销的假阳性seam；需要撤销的是原报告中
“Ascend被upstream结构性排除在metadata构建之外”的过强理由。Graph freeze由“无既有合法A +
新增transport/assembly未授权”支撑。
