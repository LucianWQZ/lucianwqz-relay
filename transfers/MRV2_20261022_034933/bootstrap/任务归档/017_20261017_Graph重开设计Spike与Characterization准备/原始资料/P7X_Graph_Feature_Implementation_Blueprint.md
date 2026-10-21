# P7-X Graph Feature Implementation Blueprint

## Common Rules

所有feature必须叠加在同一个公共架构上：P3 generation → P6 provider → persistent carrier → method-specific capture adapter。不得新增global/ContextVar/owner swap，不得修改vLLM，不得改变`metadata rebuild → REPLAY → CONSUMER → UPDATE`。

所有实现都必须保持full slot、absolute positions、query layout、canonical FullSource、Target metadata和physical KV write。未满足typed contract时必须在FullSource/workspace前fail closed。

## FEATURE: Base DFlash

**CURRENT EAGER OWNER**

`worker/v2/spec_decode/dflash/speculator.py::AscendDFlashSpeculator`与`DraftWindowEagerMixin`。query width固定`K+1`。

**GRAPH EXTRA REQUIREMENT**

Startup persistent operand、runtime same-generation refresh、FIA task rebinding与G1–G5 evidence。

**EXACT FILES / FUNCTIONS**

- `dflash/capture.py::draft_window_dflash_capture_scope`
- `dflash/capture.py::ascend_prepare_dflash_inputs_to_capture`
- `dflash/aclgraph.py::DFlashAclGraphManager.capture/run_fullgraph`
- `draft_window_graph_characterization.py::*parallel*`
- `attention/attention_v1.py::AscendAttentionBackendImpl.update_graph_params`
- `compilation/acl_graph.py::update_full_graph_params`

**NEW/REUSED STATE**

Reuse P3 runtime、P6 provider、CaptureIdentity、persistent carrier；new bounded recorder/session only。

**CAPTURE / RUNTIME / UPDATE**

Capture由Draft-private InputBuffers context选择carrier。runtime在builder前绑定real P3 generation。UPDATE沿existing FIA task-rebind。

**FAIL-CLOSED**

非base topology/backend/mode/identity直接拒绝。

**UNIT TESTS / NPU TEST**

已有candidate 65 tests；NPU执行G1–G5、A/B/A、slot/Target、profiler。

**PRODUCTION RISK**

UPDATE effective generation与stream completion仍未知。

## FEATURE: Eligible DSpark

**CURRENT EAGER OWNER**

`worker/v2/spec_decode/dspark/speculator.py::AscendDSparkSpeculator`。query width由draft checkpoint的`sample_from_anchor`决定：K或K+1。

**GRAPH EXTRA REQUIREMENT**

同DFlash，但fingerprint必须锁定actual query width、static K和capture bucket。

**EXACT FILES / FUNCTIONS**

共享DFlash graph manager/helper；DSpark特有metadata factory为`worker/v2/attn_utils.py::build_draft_attn_metadata_factory`。

**NEW/REUSED STATE**

复用base provider；无新的transport。

**CAPTURE / RUNTIME / UPDATE**

capture descriptor和runtime descriptor双向核对K/K+1；builder scope继续注入positions/is_prefilling。

**FAIL-CLOSED**

DeepSeek-V4 co-trained DSpark仍FORCED_OFF，dynamic K拒绝。

**UNIT TESTS / NPU TEST**

分别跑K与K+1，不能用DFlash结果替代。

**PRODUCTION RISK**

checkpoint-derived width错误会造成bucket与query layout错配。

## FEATURE: TP / TP16

**CURRENT EAGER OWNER**

`draft_window_eager_capability.py::P7EagerTopologyFingerprint`和每rank本地`BlockTables/FullSource`。

**GRAPH EXTRA REQUIREMENT**

每rank独立provider、manager和persistent carrier；same logical `[S,E)`，rank-local physical table。绝不`V/TP`。

**EXACT FILES / FUNCTIONS**

- `draft_window_eager_capability.py::build_p7_eager_topology_fingerprint`
- `draft_window_graph.py::DraftWindowGraphRouteFingerprint`
- `draft_window_graph_characterization.py::install_parallel_draft_window_graph_characterization`
- `dflash/aclgraph.py::run_fullgraph`

**NEW/REUSED STATE**

在Graph fingerprint/capture identity加入`tensor_parallel_rank`、`parallel_read_semantics`；provider仍instance-owned。

**CAPTURE**

每rank用自己的`_capture_descs`注册，不跨rank共享Python owner或address。

**RUNTIME**

global scalar S/E一致，各rank从其canonical source materialize对应物理块。

**UPDATE**

每rankFIA task独立update，所有rank必须属于同proposal/mapping epoch。

**FAIL-CLOSED**

rank缺失、重复、fingerprint drift、world size变化、FlashComm mode不一致均在bind前拒绝。

**UNIT TESTS**

2/4/16 rank fake owners；rank错绑；same logical V但不同physical tables；证明错误`V/TP`不被采用；partial-rank submission失败。

**NPU TEST**

TP16逐ranktable/exact/address/read-set、all-rank slot/write、collective ordering、A/B/A和profiler。

**PRODUCTION RISK**

rank间generation skew与单rank早覆盖。

## FEATURE: Async

**CURRENT EAGER OWNER**

`draft_window_async.py::DraftWindowEagerAsyncPool`和`DraftWindowEagerAsyncState`。

**GRAPH EXTRA REQUIREMENT**

`descriptor × lane × consumer` persistent carrier bank；真实Graph replay completion token；允许reverse completion。

**EXACT FILES / FUNCTIONS**

- `draft_window_async.py::acquire_with_backpressure/materialize/bind/submit/retire/release/abort`
- `draft_window_graph.py::DraftWindowGraphBindingProvider`
- `dflash/aclgraph.py::run_fullgraph`
- backend-specific graph event/task APIs under`compilation/acl_graph.py`

**NEW/REUSED STATE**

Reuse generation/mapping/request/topology identity；new Graph submission id、lane carrier bank、device completion event、pending retirement owner。

**CAPTURE**

每lane必须预注册stable backing，或证明同一capture task通过间接参数安全选择lane；不得临时换地址。

**RUNTIME**

FREE→ACQUIRED→MATERIALIZED→BOUND→SUBMITTED→CONSUMER_COMPLETE→RETIRED→FREE。

**UPDATE**

UPDATE结束不等于consumer complete；carrier在event完成前不可覆盖。

**FAIL-CLOSED**

无device event、lane不匹配、pool pressure无法安全回收、abort-after-submit无owner时拒绝。

**UNIT TESTS**

2+ inflight、delayed/reverse completion、pressure、stale handle、abort before/after submit、exception、descriptor/lane drift。

**NPU TEST**

并发A/B、reverse completion、stream event trace、backing overwrite guard、latency。

**PRODUCTION RISK**

最高风险是把Python return/UPDATE误当device consumption complete。

## FEATURE: Prefix Cache

**CURRENT EAGER OWNER**

`draft_window_nongraph.py::build_prefix_resident_snapshot`与`build_phase_aware_materialization_plan`。

**GRAPH EXTRA REQUIREMENT**

resident epoch/owner进入identity；eviction/block reuse在Graph consumer完成前受保护；derived backend state同步刷新。

**EXACT FILES / FUNCTIONS**

- `draft_window_nongraph.py::build_prefix_resident_snapshot`
- `draft_window_nongraph.py::build_phase_aware_materialization_plan`
- `draft_window_eager.py::_materialize_draft_window_read_inputs`
- `draft_window_graph.py` fingerprint/binding validation

**NEW/REUSED STATE**

resident fingerprint、cache generation/epoch、eviction hold token；可能的per-gidresident counts。

**CAPTURE**

capture只绑定capacity/address，不假设启动dummy residency等于runtime。

**RUNTIME**

每proposal计算`V_draft ∩ V_native ∩ V_resident`，刷新table/length与相关derived buffers。

**UPDATE**

FIA可task-rebind；DSA/SFA需原地refresh其derived state。

**FAIL-CLOSED**

resident snapshot stale、evicted block仍被active carrier引用、row reuse无epoch时拒绝。

**UNIT TESTS**

hit/miss/evict/reorder/finish-add/recycled block/stale resident/prefix+tail/gap/overhang。

**NPU TEST**

真实cache hit→evict→reuse A/B/A，physical read与slot/write。

**PRODUCTION RISK**

KV residency lifetime可能跨越Graph replay返回。

## FEATURE: Chunked Prefill

**CURRENT EAGER OWNER**

`draft_window_nongraph.py::classify_draft_window_batch_phase`和row-wise phase plan。

**GRAPH EXTRA REQUIREMENT**

确认FULL_DECODE_ONLY下chunk step不进入Draft query Graph；chunk完成后下一decode generation重新snapshot source/residency。

**EXACT FILES / FUNCTIONS**

- pinned vLLM `dflash/speculator.py::propose/_generate_draft`
- `draft_window_nongraph.py::classify_draft_window_batch_phase`
- `dflash/aclgraph.py::run_fullgraph`

**NEW/REUSED STATE**

row phase fingerprint、proposal epoch；Graph侧增加phase/bucket compatibility。

**CAPTURE / RUNTIME / UPDATE**

chunk自身走合法baseline/eager；decode proposal才bindGraph carrier。若源码实际选择Graph，必须有专用descriptor而不能冒充decode。

**FAIL-CLOSED**

phase无法唯一分类或descriptor与row phase不兼容时，replay前拒绝。

**UNIT TESTS**

continuing chunk、terminal chunk、decode-after-chunk、source长度更新、epoch递增。

**NPU TEST**

long prompt多chunk→decode，验证first Graph replay使用最终FullSource。

**PRODUCTION RISK**

把prefill变量名误作bypass或复用旧decode carrier。

## FEATURE: Mixed Prefill/Decode

**CURRENT EAGER OWNER**

P7-X row-wise phase plan；产品scope仍需owner确认。

**GRAPH EXTRA REQUIREMENT**

明确mixed batch是专用FULL descriptor、分裂执行，还是安全eager fallback。不能让decode-onlycapture隐式承载prefill row。

**EXACT FILES / FUNCTIONS**

- `draft_window_nongraph.py::classify_draft_window_batch_phase`
- `draft_window_eager.py::_draft_window_proposal_scope`
- DFlash/DSpark manager descriptor selection in pinned vLLM

**NEW/REUSED STATE**

per-row phase fingerprint、mixed descriptor schema、consumer masks（若支持）。

**CAPTURE / RUNTIME / UPDATE**

若无专用capture schema，必须在任何Window allocation/replay前走明确fallback/拒绝。

**FAIL-CLOSED**

当前Graph product保持拒绝；不得让EngineCore在中途因意外mixed metadata abort。

**UNIT TESTS**

decode+continuing prefill、decode+terminal prefill、reorder、finish/add、bucket mismatch。

**NPU TEST**

仅在owner选择support/fallback contract后执行。

**PRODUCTION RISK**

服务级abort和row phase污染。

## FEATURE: Multi-request Lifecycle

**CURRENT EAGER OWNER**

P3 generation/mapping_epoch/request fingerprint与P7-X row lifecycle。

**GRAPH EXTRA REQUIREMENT**

固定storage、动态row语义；每次bind核对ordered fingerprint和mapping epoch。

**EXACT FILES / FUNCTIONS**

- `draft_window.py::DraftWindowGenerationIdentity`
- `draft_window_eager.py::DraftWindowProposalEpochSource`
- `draft_window_graph.py::_validate_runtime_capture_compatibility`

**NEW/REUSED STATE**

无需新global state；可增加active row mask/phase fingerprint至Graph runtime identity。

**CAPTURE / RUNTIME / UPDATE**

capture只定义padded geometry；runtime每次刷新active rows和tail zeroing。

**FAIL-CLOSED**

reorder、same-row replacement、ABA、request count/bucket drift未被identity表达时拒绝。

**UNIT TESTS**

A/B→C/A→A/B'、finish/add、row reuse、padding/tail、stale expectation。

**NPU TEST**

batch>1纯decode + finish/add + true row reuse。

**PRODUCTION RISK**

把capture row号误当request identity。

## FEATURE: DSA

**CURRENT EAGER OWNER**

`attention/dsa_v1.py::AscendDSAMetadataBuilder.build_for_drafting`。

**GRAPH EXTRA REQUIREMENT**

Window common metadata派生SAS、SWA indices、formatted slot和seq state；`AscendDSAImpl.update_graph_params`是no-op，因此captured derived buffers必须stable且pre-replay refresh。

**EXACT FILES / FUNCTIONS**

- `attention/dsa_v1.py::build_for_drafting`
- `attention/dsa_v1.py::build_req_metadata_for_drafting`
- `attention/dsa_v1.py::AscendDSAImpl.update_graph_params`
- `worker/v2/attn_utils.py::build_attn_metadata`

**NEW/REUSED STATE**

per-descriptor/per-step persistent`spec_sas_metadata`、`dspark_swa_indices_buffer`、formatted slot/index state；generation binding。

**CAPTURE**

capture每个derived operand真实地址；不能只记录common block table。

**RUNTIME**

从Window table/length重建derived buffers，full slot输入保持不变。compressor ratio>1继续拒绝。

**UPDATE**

no-op意味着DIRECT_CAPTURED/BACKEND_DERIVED；刷新必须在REPLAY前完成且有stream ordering。

**FAIL-CLOSED**

无stable buffer、buffer capacity不足、derived generation mismatch、compressor/QLI未建模时拒绝。

**UNIT TESTS**

SAS/SWA index address稳定、content变化、wrong generation、slot full、buffer pressure。

**NPU TEST**

operator operands、physical read、SAS/indices、A/B/A、lifetime。

**PRODUCTION RISK**

derived table/length同代性和no-op update造成的stale capture。

## FEATURE: DSA-CP

**CURRENT EAGER OWNER**

`attention/context_parallel/dsa_cp.py::AscendDSACPMetadataBuilder`。

**GRAPH EXTRA REQUIREMENT**

global logical `[S,E)`在builder层投影为rank-local query/seq/index/SAS；per-rank stable derived bank。

**EXACT FILES / FUNCTIONS**

- `build_for_drafting`
- `build_req_metadata_for_drafting`
- `_build_local_token_metadata`
- `AscendDSACPImpl`

**NEW/REUSED STATE**

global generation identity + CP rank/world/geometry + local query_start/seq/cos/sin/SAS/index buffers。

**CAPTURE / RUNTIME / UPDATE**

capture local persistent operands；runtime先验证global plan，再由builder投影local。slot/write仍使用full physical owner契约。

**FAIL-CLOSED**

global/local identity不同代、rank projection不完整、group cache跨generation复用时拒绝。

**UNIT TESTS**

global interval→local exact、boundary、padding、multiple groups、rank mismatch、stale cache。

**NPU TEST**

逐CP rank local read-set、global union、slot/write、SAS/index。

**PRODUCTION RISK**

错误地在P1/P2做`V/world`或跨group共享stale derived cache。

## FEATURE: SFA / Indexer / QLI

**CURRENT EAGER OWNER**

`attention/sfa_v1.py::AscendSFAMetadataBuilder.build_for_drafting`；indexer在`models/deepseek_v4/indexer.py`和`attention/indexer_kpool.py`。

**GRAPH EXTRA REQUIREMENT**

SFA main与NoPE/indexer/top-k/QLI/compressed cache state都必须有typed generation和stable capture backing。`AscendSFAImpl.update_graph_params`是no-op。

**EXACT FILES / FUNCTIONS**

- `sfa_v1.py::_build/build_for_drafting/update_graph_params`
- `models/deepseek_v4/indexer.py`
- `attention/indexer_kpool.py`

**NEW/REUSED STATE**

separate SFA carrier adapter；main/indexer consumer ordinals；top-k/index/QLI buffers与resident source version。

**CAPTURE / RUNTIME / UPDATE**

所有derived operand逐一capture；runtime原地刷新；不能依赖FIA update。

**FAIL-CLOSED**

任一main/indexer/QLI consumer未归因或无stable owner即拒绝。

**UNIT TESTS**

main/indexer same generation、top-k translation、NoPE lengths、QLI source、stale index、storage alias。

**NPU TEST**

main与indexeroperator read-set、top-k结果、Target/logits、A/B/A。

**PRODUCTION RISK**

多consumer部分刷新导致语义分裂；属高风险独立adapter。

## FEATURE: MLA

**CURRENT EAGER OWNER**

`attention/mla_v1.py::AscendMLAMetadataBuilder`及`AscendMLAImpl.update_graph_params`。

**GRAPH EXTRA REQUIREMENT**

构造MLA-specific Window metadata，明确decode block table、seq_lens、CPU upper、padding、chunk state与实际operator字段。

**EXACT FILES / FUNCTIONS**

- `attention/mla_v1.py::AscendMLAMetadataBuilder`
- `attention/mla_v1.py::AscendMLAImpl.update_graph_params`
- `worker/v2/attn_utils.py::build_attn_metadata`

**NEW/REUSED STATE**

MLA adapter和schema-specific read carrier；P6 commonidentity可复用。

**CAPTURE / RUNTIME / UPDATE**

capture MLA decode metadata；runtime builder生成Window decode view；existing MLA task rebind接入typed binding。

**FAIL-CLOSED**

prefill/chunk/PCP/NoPE未验证或actual operator字段无法归因时拒绝。

**UNIT TESTS**

exact/upper/padding、decode block table、task update identity、Target isolation。

**NPU TEST**

actual MLA operand/read-set、D2H、lifetime、logits。

**PRODUCTION RISK**

不能继承FIA字段假设；metadata schema drift。

## FEATURE: Multi-group

**CURRENT EAGER OWNER**

`worker/v2/attn_utils.py::build_attn_metadata`按cache group构建；P2 inventory能识别group但P6 provider当前只允许single direct-prefix。

**GRAPH EXTRA REQUIREMENT**

one logical generation/anchor + N per-gid carriers；每gid独立block geometry、valid count、backend/builder和consumer ordinal。

**EXACT FILES / FUNCTIONS**

- `draft_window.py` inventory/provider abstractions
- `draft_window_graph.py::DraftWindowGraphBindingProvider`
- `worker/v2/attn_utils.py::build_attn_metadata`
- each backend adapter

**NEW/REUSED STATE**

group set fingerprint、per-gid backing bank、atomic submission barrier。

**CAPTURE / RUNTIME / UPDATE**

capture每gid每consumer；runtime共享absolute S/E，按gid投影；一次性验证同generation后提交。

**FAIL-CLOSED**

缺任一gid、heterogeneous adapter缺失、LCM/repeated-window、shallow alias均拒绝。

**UNIT TESTS**

homogeneous 2-group、heterogeneous FIA+MLA/DSA、不同block geometry、partial bind、cross-gid generation mismatch。

**NPU TEST**

每gid operand/read-set、同一logicalwindow、Target/write。

**PRODUCTION RISK**

最易发生partial generation和错误anchor重对齐。

## FEATURE: Eagle3

**CURRENT EAGER OWNER**

`worker/v2/spec_decode/autoregressive/speculator.py::AscendAutoRegressiveSpeculator`和P4b per-step integration。

**GRAPH EXTRA REQUIREMENT**

独立AR capture adapter；first-pass + static K step consumers；proposal-frozen S、per-step E_s、canonical refresh。

**EXACT FILES / FUNCTIONS**

- `autoregressive/aclgraph.py::AutoRegressiveAclGraphManager.capture/run_fullgraph`
- `autoregressive/speculator.py::_multi_step_decode/build_draft_attn_metadatas`
- `draft_window_eagle3.py` P4b math/lifecycle

**NEW/REUSED STATE**

Reuse provider core；new Eagle3 CaptureIdentity route、first-pass carrier、step-indexed carrier bank。

**CAPTURE / RUNTIME / UPDATE**

first-pass与每step各注册consumer；runtime一次proposal identity下刷新每step table/exact；metadata list顺序与consumer ordinal一致。

**FAIL-CLOSED**

plain Eagle、dynamic K、step缺失/重复、S漂移、table/length lag、previous Window source均拒绝。

**UNIT TESTS**

K=3 step0/1/2、future column、rejection、stale step、Target first-pass isolation、A/B/A。

**NPU TEST**

first-pass→multi-step actual operand/read-set、rejection、cross-boundary、timeline。

**PRODUCTION RISK**

AR graph一次合并多step，与DFlash one-shot adapter不同。

## FEATURE: DFlash2

**CURRENT EAGER OWNER**

`worker/v2/spec_decode/dflash2/speculator.py::init_cudagraph_manager`。

**GRAPH EXTRA REQUIREMENT**

当前selector路径自身明确不支持Graph，要求`enforce_eager`；不存在可复用的Graph manager/capture consumer。

**EXACT FILES / FUNCTIONS**

`dflash2/speculator.py::init_cudagraph_manager`及其selector/operator owner。

**NEW/REUSED STATE**

NO EXISTING OWNER for a Graph Window carrier。

**CAPTURE / RUNTIME / UPDATE**

必须先完成DFlash2 method-level Graph设计；不能因继承DFlash词汇而复用helper。

**FAIL-CLOSED**

继续在method Graph初始化时拒绝。

**UNIT TESTS / NPU TEST**

先有DFlash2 baseline Graph test，再谈Window；当前只测不会误enable。

**PRODUCTION RISK**

把DFlash2误路由到DFlash manager会绕过selector语义。
