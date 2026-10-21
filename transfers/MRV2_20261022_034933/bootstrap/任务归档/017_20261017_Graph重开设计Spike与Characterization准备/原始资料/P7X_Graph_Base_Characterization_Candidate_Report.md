# P7-X Graph Base Characterization Candidate Report

## 1. Status

```text
Commit: 8cb4bed670f395c257c1233db944395159916009
Parent: c43989aabd9b40a561987d39f4ba4516934f2f5b
Pinned vLLM: 84030bbe3d74d99bad477a3d2e37a973ccd8865c
Activation: default OFF, internal only
Product Graph Gate: unchanged / fail closed
NPU: not run
```

本候选只为公司NPU上的 G1–G5 取证提供受控路径，不是用户可见功能。

## 2. Exact Supported Characterization Route

必须同时满足：

- policy 为 `ELIGIBLE_ON`；
- `VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1`；
- normalized method 为 DFlash 或 eligible non-DeepSeek-V4 DSpark；
- static K；
- STANDARD hardware family；
- single executable group；
- dense GQA/FIA direct-prefix；
- effective/configured Graph context为 FULL 或 FULL_DECODE_ONLY；
- synchronous scheduling；
- TP=DP=PP=PCP=DCP=1；
- SP、DSA-CP、FlashComm关闭；
- prefix cache关闭。

PIECEWISE runtime、Async、parallel、prefix、complex backend、multi-group、Eagle3、DFlash2均在FullSource/workspace前拒绝或根本不进入此候选。

## 3. Activation and Zero-state Contract

`vllm_ascend/envs.py` 使用项目已有 `_strict_binary_env` 注册：

```text
VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH
```

只接受`0`或`1`。unset/0 时：

- 不建立 characterization context；
- 不安装 `DraftWindowGraphBindingProvider`；
- 不注册 capture identity；
- eager继续原路径；
- CONFIG_OFF/FORCED_OFF 因没有 eligible policy owner，零P2/P3/P6状态；
- capture helper无显式context时逐行委托已保存的upstream helper。

该env仅是内部实验闸，不改变`draft_window_size`的公开Graph capability判定。

## 4. Startup Capture

真实调用链：

```text
model_runner.set_attn
→ AscendDFlash/DSpark._initialize_draft_window_source_capability
→ validate actual Graph context
→ P2/P3 source/runtime
→ init_cudagraph_manager
→ install_parallel_draft_window_graph_characterization
→ iterate query_cudagraph_manager._capture_descs
→ provider.register_capture_identity
→ DFlashAclGraphManager.capture
→ draft_window_dflash_capture_scope(Draft-private InputBuffers)
→ upstream manager calls patched _prepare_dflash_inputs_to_capture
→ Ascend metadata builder consumes persistent Window table/length
```

Capture identity不包含fake request、fake epoch或generation 0。它包含method、route、graph mode、backend/builder、gid、layout、descriptor/bucket、query width、static K、W、block geometry、topology和stable backing identity。

LoRA等导致同一个 `(mode, num_reqs, num_tokens)` 无法唯一解析的capture descriptor当前直接拒绝，避免绑定错carrier。

## 5. Runtime Bind

真实proposal链：

```text
P4 _build_draft_attn_metadata
→ P7-X materialize from canonical FullSource
→ _draft_window_live_inputs = real DraftMetadataInputs
→ eager metadata temporarily published by existing call chain
→ DFlashAclGraphManager.run_fullgraph
→ prepare_parallel_draft_window_graph_characterization
→ validate same real generation/mapping_epoch/request bucket
→ discard exact unused eager metadata entry
→ provider.bind_read_carrier
→ copy table/valid/exact/upper into stable capture backing
→ build Draft-private graph metadata
→ consume_draft_window_graph_metadata
→ replay/consumer/update
```

没有第二次materialize、没有新epoch、没有window-of-window。source始终为canonical FullSource。metadata builder前只有一个正式prepare/bind边界。

## 6. Ownership and Lifetime

| Object | Owner | Address | Content | Lifetime |
|---|---|---|---|---|
| canonical FullSource | BlockTables/P2 | stable by existing owner | full | model/runtime |
| P3 workspace | speculator runtime | stable per lane | generation mutable | lease |
| Graph carrier backing | P6 provider | capture-stable | generation mutable | provider/capture identity |
| CaptureIdentity | provider | immutable | no request generation | graph bucket |
| RuntimeIdentity | bound carrier | immutable per bind | real generation/epoch/request | proposal |
| Draft graph metadata | P3 store + carrier | object per bind | carrier-backed reads | proposal/update |
| Target metadata | Target ModelState | unchanged | full | Target lifecycle |

成功proposal仍由既有P3 proposal scope退休。失败时：candidate先释放bound/submitted provider state；外层proposal scope作为唯一P3 lease retirement owner。新增回归验证recorder异常后下一generation可重新绑定。

## 7. Read/Write Boundary

| State | Candidate | Frozen invariant |
|---|---|---|
| Draft block table | persistent Window backing | allowed change |
| Draft device/CPU lengths | Window exact/upper | allowed change |
| slot mapping | canonical full row | unchanged |
| positions | existing Draft full absolute positions | unchanged |
| query_start_loc | existing full query layout | unchanged |
| canonical tables | never mutated/aliased by carrier | unchanged |
| Target metadata | real non-empty owner, isolated recursively | unchanged |
| physical KV writes | full slot contract | unchanged |

## 8. G1–G5 Recorder Schema

每个bounded event记录：

- sequence和stage；
- route、capture descriptor；
- generation_id/mapping_epoch（capture时必须为空）；
- persistent table address；
- table values；
- exact/upper lengths；
- slot mapping address+values；
- positions address+values；
- query layout address+values。

Stage：

```text
CAPTURE
MATERIALIZED
BOUND
LIVE
REPLAY
CONSUMER
UPDATE
```

Snapshots包含显式device→host copy，仅用于内部表征。它们会改变时序，不能作为无同步性能证据，也不能单独证明kernel physical read-set。

## 9. Source Files

| File | Function |
|---|---|
| `vllm_ascend/envs.py` | strict flag registry |
| `worker/v2/spec_decode/draft_window.py` | `_build_draft_window_source_capability_for_context` |
| `worker/v2/spec_decode/draft_window_graph_characterization.py` | all candidate/session/recorder functions |
| `worker/v2/spec_decode/draft_window_eager.py` | `_validated_draft_attention_read_inputs` |
| `worker/v2/spec_decode/dflash/speculator.py` | source bootstrap + manager install |
| `worker/v2/spec_decode/dspark/speculator.py` | source bootstrap + manager install |
| `worker/v2/spec_decode/dflash/aclgraph.py` | `run_fullgraph` prepare boundary |
| `worker/v2/spec_decode/dflash/capture.py` | capture snapshot hook |

## 10. Tests

`tests/ut/spec_decode/test_draft_window_graph_characterization.py`覆盖：

- strict/default-off env；
- unsupported context在P2前拒绝；
- OFF zero provider/session；
- eligible DFlash/DSpark install；
- real manager descriptor registration；
- same real P3 generation reuse；
- Draft-private metadata与Target隔离；
- capture persistent address和full write oracle；
- wrong mapping_epoch；
- active carrier overwrite拒绝；
- recorder exception RED→GREEN cleanup；
- host A/B/A'同址内容刷新；
- stale generation拒绝；
- manager在metadata builder前prepare。

最终结果：candidate + P6 carrier `65 passed`。完整spec_decode为`654 passed, 13 skipped, 7 failed`；7项VWN用例均在无NPU host的upstream attention selector失败，未进入candidate代码，故不是PASS也不是回归证据。

## 11. NPU Exit Criteria

必须全部满足：

1. capture operator绑定地址等于CaptureIdentity backing地址；
2. A/B/A' replay看到各自刷新后的table/exact，无stale；
3. physical read-set等于CPU oracle；
4. slot/write/Target state与OFF一致；
5. replay/update effective generation通过task trace确定；
6. completion前不能覆盖backing；
7. profiler量化characterization snapshot与真实feature hot-path开销；
8. env关闭后行为与c439/P7-X baseline一致。

## 12. Verdict

```text
BASE CHARACTERIZATION CANDIDATE: LOCAL STATIC PASS
G1-G5: READY FOR COMPANY NPU CAMPAIGN
NPU GRAPH CORRECTNESS: NOT VERIFIED
PUBLIC GRAPH WINDOW: STILL FAIL-CLOSED
DO NOT PUSH
```
