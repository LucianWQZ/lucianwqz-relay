# MRV2 Draft Sliding Window — P6 Graph Read Carrier & Per-Consumer Binding Implementation Notes

## Document Status

| Item | Value |
|---|---|
| Phase | P6 Review Adjudication / Fix / Freeze |
| Date | 2026-10-13（Asia/Shanghai） |
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c`，clean，zero diff |
| vLLM-Ascend parent | P5 Final `0702c89d2aa41d47ae2379fc6de883140277fbef` |
| P5 Final tree | `2b8fecda15ca57c0062bbfe5eec62ecd0a4c99ac` |
| P6 branch | `feature/p6-graph-read-carrier` |
| P6 commit | `20673a1ced10160d8f8d1aaa79230e6ce0409d3c` |
| P6 tree | `153458a4fbb21e8284ceb6b5290b10295a6b877d` |
| Review-fix commit | `7599497ab2694c4cf343f61f82f449980d8bad93` |
| Final tree | `b4f7d12bd24b0a7632f9e606b29703a7c96278de` |
| Repository boundary | `R-REPO-01`：只修改 `vllm-ascend` |
| Graph user Gate | **STILL FAIL-CLOSED** |
| NPU Graph | **NOT VERIFIED** |

本文记录P6真正落地的静态生产基础，以及在固定仓库边界下无法诚实关闭的capture和NPU
timeline问题。它不是Graph支持声明，也不覆盖P1–P5 Notes。

## 1. P6解决的问题

P5能观察“某个generation希望在LIVE/CAPTURE/REPLAY/UPDATE/CONSUMER处使用某个P3 backing”，
但它没有让Graph metadata consumer真正使用该backing。P6新增：

1. 与request generation不同namespace的startup capture identity；
2. per-consumer persistent graph read backing；
3. 从P3 generation复制到稳定carrier，再用显式builder构造Draft-private metadata的通道；
4. `build_draft_attn_metadatas()`的强约束：provider存在时只能返回显式carrier metadata；
5. replay前metadata identity/bucket/mode二次验证；
6. 在真实`update_full_graph_params -> backend.get_impl_cls/get_builder_cls`入口派生backend事实；
7. 明确表示`REPLAY -> CONSUMER -> UPDATE`下effective generation仍需NPU timeline，而不猜同次或下一次；
8. Eagle3 K=3 per-step carrier bank和Host A/B/A静态oracle。
9. Review-fix后，显式`DraftWindowGraphWriteSideReference`把full slot mapping、positions、
   query layout、attention state、actual token count和causal contract与同一carrier build绑定；
10. DFlash/DSpark graph route只由provider持有的P2 normalized inventory method解析，
    不再信任`_speculator_name`调试字符串。

P6没有做：

- 没有改变P2 Graph capability Gate；
- 没有自动安装provider、capture identity或carrier；
- 没有让用户配置进入FULL/FULL_DECODE_ONLY/PIECEWISE Window；
- 没有证明startup capture operator绑定了P6 backing；
- 没有证明UPDATE影响replay N还是N+1；
- 没有证明NPU physical read-set、stream happens-before或性能。

## 2. Source Preflight

### 2.1 Eagle3 live/eager

```text
AscendAutoRegressiveSpeculator.propose
  -> P4b proposal scope / mapping_epoch
  -> first pass: _prefill
       -> P3 materialize
       -> _build_eagle3_private_attn_metadata
       -> DraftMetadataStore
       -> Draft forward
  -> AR: _multi_step_decode / _build_draft_attn_metadata
       -> each step refreshes from canonical FullSource
       -> P3 materialize_serialized_step
       -> Draft-private metadata
       -> Draft forward
```

P6不改这条eager路径。

### 2.2 Eagle3 capture

```text
AscendAutoRegressiveSpeculator.capture
  -> AutoRegressiveAclGraphManager.capture
     first pass:
       -> upstream SpeculatorCudaGraphManager.capture
          -> upstream prepare_inputs_to_capture
          -> upstream dummy/full metadata
          -> captured model forward
     AR decode:
       -> Ascend create_forward_fn
       -> upstream prepare_inputs_to_capture
       -> generic CudaGraphManager.capture
       -> captured model forward
```

startup capture没有request、proposal、mapping_epoch。upstream在内部创建dummy input、dummy
block table和metadata。固定vLLM没有可传入P6 carrier的hook。

### 2.3 Eagle3 replay/update

```text
AutoRegressiveAclGraphManager.run_fullgraph
  -> AscendAutoRegressiveSpeculator.build_draft_attn_metadatas
  -> P6 consume explicit carrier metadata（provider存在时mandatory）
  -> P6 replay bucket/mode/metadata identity validation
  -> wait update stream
  -> REPLAY observation
  -> super().run_fullgraph(desc)
  -> CONSUMER observation
  -> set Draft forward context
  -> create typed update binding
  -> update_full_graph_params
       -> attn_backend.get_impl_cls()
       -> attn_backend.get_builder_cls()
       -> P6 backend attribution/metadata revalidation
       -> impl_cls.update_graph_params(...)
```

### 2.4 DFlash live/capture/replay

live/eager继续使用P4a proposal scope、P3 materialize、Ascend-only builder和Draft store。

```text
DFlashAclGraphManager.capture
  -> upstream DFlashCudaGraphManager.capture
  -> upstream dummy/full metadata capture

DFlashAclGraphManager.run_fullgraph
  -> AscendDFlashSpeculator.build_draft_attn_metadatas
  -> P6 explicit DFlash carrier（provider存在时mandatory）
  -> replay validation
  -> REPLAY -> super replay -> CONSUMER
  -> typed update binding
  -> update_full_graph_params -> actual backend UPDATE
```

### 2.5 DSpark relationship

DSpark拥有自己的`build_draft_attn_metadatas()`，但capture/replay manager继承DFlash query graph。
P6因此给DSpark独立route fingerprint和consumer identity，同时复用DFlash manager中的真实
replay/update seam。DeepSeek-V4 co-trained DSpark仍在P1 forced-OFF，不能创建P2/P3/P6状态。

### 2.6 update_graph_params真实消费者

`vllm_ascend.compilation.acl_graph.update_full_graph_params()`在current config scope中解析真实
backend implementation/builder。当前唯一静态关闭的dense GQA consumer为精确
`AscendAttentionBackendImpl.update_graph_params`：standard FIA分支从每个Draft metadata读取
`block_tables`和`seq_lens_list`，在`torch.npu.graph_task_update_begin/end`内重绑task operand。

这个事实支持`TASK_REBOUND`分类；它不证明重绑影响已经完成的replay N。

## 3. SOURCE DRIFT

旧设计中的`enable_enpu`/“update先于replay”假设不符合current checkout。真实顺序是：

```text
metadata build
-> REPLAY
-> CONSUMER
-> UPDATE
```

P6按真实源码锁定顺序，没有修改Frozen read/write语义。旧upstream
`DraftCaptureBindingProvider`/generic hook路线继续被`R-REPO-01`取代。

## 4. Chosen Ascend-only Seam

```text
P3 DraftMetadataInputs
  -> DraftWindowGraphBindingProvider（instance-owned）
  -> bind_read_carrier
       validate generation/epoch/request/gid/phase/step/lane
       copy into per-consumer persistent backing
       explicit metadata_builder(read_inputs)
       nested Target isolation oracle
       P3 DraftMetadataStore publish/read
  -> method build_draft_attn_metadatas consumes exact carrier metadata
  -> graph manager validates exact objects + bucket + mode before replay
  -> replay
  -> typed update binding
  -> actual update_full_graph_params backend attribution
  -> AscendAttentionBackendImpl.update_graph_params
```

没有module global、ContextVar、monkeypatch、Target/shared-owner swap或vLLM修改。

## 5. Rejected Alternatives

| Alternative | Verdict | Reason |
|---|---|---|
| 修改vLLM capture builder | REJECTED | 违反R-REPO-01 |
| import-time monkeypatch | REJECTED | 隐式跨实例状态与上游漂移 |
| module global / ContextVar | REJECTED | 不能证明多实例/并发隔离 |
| 临时替换Target/full block table | REJECTED | 污染write/Target world |
| 用generation_id=0冒充capture | REJECTED | startup没有request generation |
| provider存在但继续Target-derived metadata | REJECTED | P6在replay前hard fail |
| 声称post-replay UPDATE作用于当前replay | REJECTED | source顺序不足，需NPU timeline |
| 复制整段upstream capture manager | REJECTED | drift面过大且违反最小Ascend seam |

## 6. Capture Identity vs Runtime Generation

`DraftWindowGraphCaptureIdentity`只包含graph program和stable backing事实：route fingerprint、
lane、consumer ordinal、schema version、backing identity。它明确没有：

- request id；
- proposal id；
- generation id；
- mapping_epoch；
- ordered request fingerprint。

`DraftWindowGraphBindingIdentity`继续表达runtime generation。`bind_read_carrier()`只接受真正
`DraftWindowGraphCaptureIdentity`，并逐项验证runtime method/gid/padded geometry/lane以及route
phase/step。错误namespace直接TypeError，不能静默转换。

## 7. Stable Backing / Ownership

每个capture consumer ordinal拥有独立`_DraftWindowGraphCarrierBacking`：

| Buffer | Device | Owner | Address | Content |
|---|---|---|---|---|
| `window_block_table` | P3 workspace device | provider carrier | stable | per generation mutable |
| `valid_num_blocks` | P3 workspace device | provider carrier | stable | per generation mutable |
| `device_window_exact` | P3 workspace device | provider carrier | stable | per generation mutable |
| `cpu_window_exact` | CPU | provider carrier | stable | per generation mutable |
| `cpu_window_upper` | CPU | provider carrier | stable | per generation mutable |

carrier backing不是P3 workspace alias，也不aliascanonical FullSource或Target。它按capture bucket
一次分配，以`copy_`更新内容；不会用per-call clone替换owner。provider仅显式安装/注册时分配，
所以CONFIG_OFF/FORCED_OFF和当前Graph user Gate路径均是zero P6 allocation。

## 8. Carrier State Machine

```text
EMPTY
  -> bind_read_carrier
BOUND
  -> consume_metadata (exact consumer set)
SUBMITTED
  -> actual backend attribution at UPDATE
UPDATED
  -> next generation may rebind same stable backing
```

active BOUND/SUBMITTED carrier不能覆盖。metadata对象、route、bucket、mode在replay前锁定；
actual UPDATE再次验证对象identity、layer group、table/length storage和backend/builder。

## 9. Draft-private Metadata / Target Isolation

metadata builder仍只从`DraftWindowGraphReadInputs`取得Window read table/length；它同时由
调用方显式绑定一个独立的`DraftWindowGraphWriteSideReference`，该reference必须来自稳定的
full-state owner，不能从Window read carrier推导。builder输出必须：

- 非空Mapping；
- `block_tables`使用carrier table storage；
- device/CPU lengths使用carrier storage；
- `seq_lens_list`与carrier CPU exact一致；
- `slot_mapping`保持canonical Draft `BlockTables.slot_mappings`的full storage/view；
- `query_start_loc`、`actual_seq_lengths_q`、`attn_state`、`num_actual_tokens`和`causal`
  与显式full-state reference一致；
- positions owner在build前后地址、geometry与Tensor mutation version不变；标准
  `AscendMetadata`本身没有positions字段，若backend metadata扩展包含该字段则还要求identity一致；
- full slot/positions/query tensors在build与UPDATE二次校验之间不得被原地改写；
- layer key属于P2 inventory layer group；
- 与真实Target在root、nested object、Tensor storage、NumPy owner上全部不alias。

P6将P3的nested isolation oracle提取为共享
`validate_draft_metadata_isolation()`；P3 store语义不变。

## 10. Backend Identity

P5 caller声明的`consumer_kind`仍只保留为历史expected-binding接口，不作为P6证明。P6 carrier
在UPDATE前标为`UNRESOLVED`。只有真实`update_full_graph_params()`解析出：

- backend class；
- exact implementation class；
- builder class；
- update function identity；
- P2 global gid/layer group；
- exact metadata/backing；

并确认implementation精确为source-verified `AscendAttentionBackendImpl`后，才派生
`TASK_REBOUND`。未知implementation、subclass、builder或layer group全部fail closed。

## 11. Capture Dummy Limitation / Architecture Boundary

P6能定义capture identity和persistent backing，却不能证明upstream startup capture使用它。
`observe_draft_window_graph_capture()`因此在provider存在时总是hard fail；provider不存在时是
exact no-op，baseline Graph capture不变。

关闭这个阻塞需要以下之一：

1. 一个现有但尚未发现的Ascend-owned pre-capture operand injection seam；或
2. owner批准vendor-local最小capture assembly及其drift成本；或
3. 修改vLLM的vendor-neutral hook（当前repository boundary禁止）。

在此之前：

```text
P6 CAPTURE IDENTITY: implemented/static verified
P6 CAPTURE PATH: ARCHITECTURE/REPOSITORY BLOCKED
```

## 12. Replay / Consumer / Update Timeline

P6 typed timeline记录：

- `materialized_generation_ids`；
- `submitted_replay_generation_ids`（希望提交的source）；
- `consumer_generation_ids=None`；
- `update_source_generation_ids`；
- `update_effective_generation_ids=None`；
- status=`NEEDS_NPU_TIMELINE`。

`assert_update_effective_for()`在没有NPU证据时必定拒绝。这样既不声称same-replay，也不声称
one-step-lag。详见`P6_Replay_Update_Timeline.md`。

## 13. Eagle3 Per-step Contract

K=3测试注册三个独立consumer ordinal/backing：

```text
proposal=10, mapping_epoch=10
step1: generation g0, E1=65, carrier0
step2: generation g1, E2=66, carrier1
step3: generation g2, E3=67, carrier2
```

三步保持同proposal/mapping/request/gid，step严格递增；每步从P3 canonical-source
materialization复制到不同稳定backing。测试使用不同source start并验证三个metadata exact length
不同，防止table更新而length lag、length更新而table lag和window-of-window。

这是host/state contract，不是NPU graph correctness。

## 14. Host A/B/A

CPU test执行：

```text
A  epoch=10, requests=[A,B], source-start=0
B  epoch=11, requests=[C,A], source-start=1
A' epoch=12, requests=[A,B], source-start=0
```

证明：

- carrier address三次相同；
- A/B内容不同；
- A'语义内容等于A但generation不同；
- stale A generation被拒绝；
- canonical FullSource不变；
- Target/write fields不变。

结论命名严格为`P6 HOST A/B/A`，不是NPU A/B/A。

## 15. Files Changed

| File | P6 change |
|---|---|
| `worker/v2/spec_decode/draft_window_graph.py` | capture identity、route fingerprint、persistent carrier bank、timeline、backend attribution；review-fix增加typed full write/query reference、mutation guard及P2-inventory route resolver |
| `worker/v2/spec_decode/draft_window.py` | 复用P3 nested Target isolation oracle |
| `worker/v2/spec_decode/autoregressive/speculator.py` | Eagle3 graph metadata entry优先消费显式carrier |
| `worker/v2/spec_decode/dflash/speculator.py` | DFlash graph metadata entry优先消费显式carrier |
| `worker/v2/spec_decode/dspark/speculator.py` | DSpark graph metadata entry优先消费显式carrier |
| `worker/v2/spec_decode/autoregressive/aclgraph.py` | capture fail-closed、replay前验证、typed update binding |
| `worker/v2/spec_decode/dflash/aclgraph.py` | DFlash/DSpark同等carrier验证和update binding；review-fix移除`_speculator_name`字符串route heuristic |
| `compilation/acl_graph.py` | 在真实backend impl/builder解析后执行P6 attribution |
| `tests/ut/spec_decode/test_draft_window_graph_carrier.py` | P6 32项核心与manager integration测试；新增canonical write-side、query/position/state parity、mutation与inventory-route regressions |
| `tests/ut/spec_decode/test_draft_window_graph_binding.py` | P5 capture观察假设升级为P6 fail-closed事实 |

## 16. Tests

| Command/scope | Result | Meaning |
|---|---|---|
| P5+P6 graph targeted | `69 passed` | identity/carrier/backend/timeline/A-B-A/write-side/manager contracts |
| P1–P6 + graph + attn/block table targeted | `432 passed, 23 subtests passed` | 受影响回归无新增失败 |
| full `tests/ut/spec_decode` | `541 passed, 13 skipped, 7 failed, 2 subtests passed` | 7项为既有VWN host platform/backend环境失败；full suite不记PASS |
| Ruff check / format | PASS | changed Python/tests |
| targeted Mypy | PASS，2个本次production files | review-fix文件无错误；原P6的7-file结果仍保留为历史证据 |
| full changed-file Mypy | BASELINE-LIMITED | 仅AR speculator 4项自`841dc6c`已存在的`issubclass(Optional[type])`错误；不是P6 PASS |
| compileall | PASS | spec_decode、graph helper与P6 tests |
| `git diff --check` | PASS | whitespace clean |
| executable repository hooks | PASS | Ruff/format/codespell/typos/filename/init/logger/import/boolean/long-function/symbolic-meta |
| actionlint | ENVIRONMENT BLOCKED | Go dependencies从`proxy.golang.org`下载超时；不是PASS |
| gitleaks | ENVIRONMENT BLOCKED | 本机无`gitleaks`且无`wget`；不是PASS |

CPU测试不能证明：captured operator address、NPU task update effective replay、physical read-set、
stream lifetime、性能。

上述`432 passed`的精确文件清单为：

```text
tests/ut/spec_decode/test_draft_window.py
tests/ut/spec_decode/test_draft_window_runtime.py
tests/ut/spec_decode/test_draft_window_eager.py
tests/ut/spec_decode/test_draft_window_eagle3.py
tests/ut/spec_decode/test_draft_window_graph_binding.py
tests/ut/spec_decode/test_draft_window_graph_carrier.py
tests/ut/spec_decode/test_autoregressive_draft_metadata.py
tests/ut/spec_decode/test_dflash2_v2.py
tests/ut/spec_decode/test_dspark_graph_contract.py
tests/ut/spec_decode/test_eagle_aclgraph_source_regression.py
tests/ut/worker/test_attn_utils_v2.py
tests/ut/attention/test_attention_v1.py
tests/ut/worker/test_block_table.py
tests/ut/worker/v2/test_v2_block_table.py
```

## 17. Invariant Audit

- vLLM exact baseline、clean、zero diff；
- only vllm-ascend changed；
- no module global Window transport；
- no ContextVar；
- no monkeypatch/site-packages hack；
- no Target/shared owner swap；
- canonical FullSource untouched；
- full slot mapping untouched；
- positions/query layout untouched；
- carrier builder必须携带并验证显式full write/query reference；
- DFlash/DSpark route来自P2 inventory而非class-name字符串；
- Target root/content/nested storage untouched；
- carrier address stable/content mutable/generation explicit；
- provider + baseline metadata hard fails before replay；
- unknown backend/builder hard fails；
- capture/runtime namespace mismatch hard fails；
- effective generation remains unknown without NPU；
- CONFIG_OFF/FORCED_OFF zero P6 state；
- FULL/FULL_DECODE_ONLY/PIECEWISE user Gate unchanged；
- no Async/parallel/backend extension；
- no P7 implementation。

## 18. Remaining Evidence / P7 Entry Seam

P6 leaves an explicit seam rather than enabling Graph：

1. owner must resolve startup capture carrier injection underR-REPO-01；
2. NPU trace must prove captured and replayed operand address；
3. NPU A/B/A must establishUPDATE effective generation；
4. NPU operator oracle must provephysical read-set；
5. stream event must proveworkspace/carrier rewrite happens-after consumer；
6. recapture/bucket/lane pressure必须验证；
7. only then can a later phase consider one exact Graph route；
8. Async/parallel/complex backend remain separate future inventory。

## 19. Final Local Status

```text
P6 CAPTURE IDENTITY: PASS (CPU/static)
P6 CAPTURE PATH: BLOCKED under current R-REPO-01 seam
P6 GRAPH READ CARRIER: PASS (replay/update-side static contract)
P6 BACKEND ATTRIBUTION: PASS (exact standard FIA update path)
P6 HOST A/B/A: PASS
P6 STATIC PER-CONSUMER CONTRACT: PARTIAL
P6 NPU GRAPH: NOT VERIFIED
GRAPH WINDOW USER GATE: STILL FAIL-CLOSED
```

# Independent Review Resolution

## Review Metadata

| Item | Value |
|---|---|
| Independent review | `P6_DeepSeek_Independent_Review.md`，2026-10-13 |
| Original P6 | `20673a1ced10160d8f8d1aaa79230e6ce0409d3c` |
| Review-fix | `7599497ab2694c4cf343f61f82f449980d8bad93` |
| Final tree | `b4f7d12bd24b0a7632f9e606b29703a7c96278de` |
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c`，clean，zero diff |

Finding statistics：`ACCEPTED=3`、`PARTIALLY_ACCEPTED=1`、`REJECTED=0`、
`INSUFFICIENT_EVIDENCE=0`、`DEFERRED_TO_NPU=1`、`ARCHITECTURE_BLOCKER=1`。

## Resolution Table

| ID | Severity | Reviewer finding | Reproduction | Resolution | Evidence | Code action |
|---|---|---|---|---|---|---|
| Q-01 | Architecture / repository blocker | pinned vLLM startup capture内部生成dummy metadata，Ascend没有安全carrier注入点 | 重新追踪AR/DFlash `capture -> super().capture`及upstream dummy builder；provider存在时capture hard fail | `ARCHITECTURE_BLOCKER` | CaptureIdentity与generation已正确分层，但actual capture binding不存在；R-REPO-01禁止改vLLM，Frozen invariant禁止global/context/owner swap | 不写hack；明确`P6 CAPTURE BINDING: REPOSITORY-BOUNDARY BLOCKED`，Graph Gate保持关闭 |
| m-01 | Minor correctness | carrier只校验read table/length，未保护full write/query parity | 在原P6上加入“window table充当slot mapping”负例，结果`DID NOT RAISE RuntimeError` | `PARTIALLY_ACCEPTED` | parity缺口真实；但review把positions当作每个metadata固有字段不准确，标准`AscendMetadata`无positions字段 | 新增typed write-side reference；canonical slot owner、query/state/token/causal、positions owner mutation均校验；metadata若带positions再校验identity；9项负例转绿 |
| m-02 | Minor correctness | DFlash/DSpark route依赖`_speculator_name`字符串 | 删除test speculator的该属性后，原实现会在manager入口报错 | `ACCEPTED` | provider已持有P2 `inventory.method`，这是authoritative normalized method | 新增`resolve_parallel_draft_window_graph_route()`；manager只使用P2 inventory，未知method hard fail |
| m-03 | Minor lifecycle/documentation | 安装provider与未解决的startup capture互斥 | DFlash和Eagle manager startup negative tests真实触发hard fail | `ACCEPTED` | 当前production无installer caller，故无现网回归；API耦合必须固定 | 扩充installer docstring和本Notes，禁止capture seam解决前安装 |
| m-04 | Minor documentation | `423 passed`缺精确文件清单，无法复现 | 按真实最终命令重跑14个文件 | `ACCEPTED` | review-fix后结果为`432 passed, 23 subtests passed` | 本节列出全部14个文件和最终计数 |
| Q-02 | Evidence boundary | manager spy不能证明device-effective update generation | static source仅能证明typed binding到达manager/真实update入口，不能证明NPU task消费 | `DEFERRED_TO_NPU` | `consumer_generation_ids`和`update_effective_generation_ids`继续为`None`；`assert_update_effective_for()`继续hard fail | 不改事件名称、不猜N/N+1；保留`NEEDS_NPU_TIMELINE` |

## Red-to-Green Evidence

1. Red：在原P6实现上运行新增
   `test_carrier_rejects_window_table_as_write_side_slot_mapping`，结果为
   `Failed: DID NOT RAISE RuntimeError`。
2. Green：review-fix后P6 carrier文件`32 passed`；P5+P6合并`69 passed`。
3. 新增回归还拒绝：clone/noncanonical slot owner、query/positions identity漂移、
   query endpoints、attention state、actual token count、causal漂移及build期间原地mutation。

## Final Test Evidence

| Scope | Final result | Limitation |
|---|---|---|
| P6 carrier | `32 passed` | CPU/static only |
| P5 + P6 graph | `69 passed` | 不证明capture/NPU |
| 14-file affected regression | `432 passed, 23 subtests passed` | host contract |
| full spec_decode | `541 passed, 13 skipped, 7 failed, 2 subtests passed` | 7项均停在pinned vLLM `selector.py:208`的已知VWN host backend环境错误；不记PASS |
| Ruff / format / targeted Mypy / compileall / diff-check | PASS | 本次changed files |
| codespell / typos / repository local Python hooks | PASS | locally executable hooks |
| actionlint | ENVIRONMENT BLOCKED | Go dependencies下载超时；不是PASS |
| gitleaks | ENVIRONMENT BLOCKED | 无本机binary且无`wget`；不是PASS |

## Freeze Decision

```text
P6 CAPTURE IDENTITY: PASS
P6 GRAPH READ CARRIER: PASS (replay/update static path only)
P6 BACKEND ATTRIBUTION: PASS
P6 HOST A/B/A: PASS
P6 CAPTURE BINDING: REPOSITORY-BOUNDARY BLOCKED
UPDATE EFFECTIVE GENERATION: NEEDS NPU / TASK TRACE
P6 STATIC FINAL: PARTIAL
P6 NPU GRAPH: NOT VERIFIED
GRAPH WINDOW USER GATE: STILL FAIL-CLOSED
P7 ENTRY: BLOCKED pending owner capture-seam decision
```

