# P7-X Graph Base A3 Repair3 — Implementation and Readiness

日期：2026-10-20（Asia/Shanghai）。仅本地候选；未 push、未创建 PR、未登录服务器。

## 1. 最终结论

`LOCAL_REPAIR_HOST_VERIFIED`；`READY_FOR_PUBLICATION_REVIEW=YES`。
发布且验证 exact source 后可以开始 A3 smoke，不代表 G1–G5 全闭合。
`NEW_SHA_DEVICE_VERIFICATION=NOT_RUN`；`PUBLIC_GRAPH_GATE=STILL_FROZEN`。

| 身份 | 值 |
|---|---|
| branch | fix/p7x-graph-base-a3-repair3 |
| base | 8198ab7a6df6a163316f5d4ed2126242bbeb4aa8 |
| base tree | 27eee84d06ec60461be7471d7c2ff941ad6d27ea |
| final | 10cbf4c014fc6cc48a6fea611bb605cecdd54cfd |
| final tree | 28dddd6d1fc19e67270ee71b7b9e7fcd410ab3c9 |
| parent | 8198ab7a6df6a163316f5d4ed2126242bbeb4aa8 |
| vLLM | 84030bbe3d74d99bad477a3d2e37a973ccd8865c |
| vLLM tree | f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee |
| driver SHA256 | 7e6f2e5984430bc5231511960da2fdc9b073ddc58cfed8bfaed796498b70660d |
| fixture manifest SHA256 | 1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4 |

只有六个 source/test/tool 文件改动。Pinned vLLM clean、零 diff。Graph 数学、FullSource、slot/position/query、backend ExternalEvent wait/reset/record、REPLAY→CONSUMER→UPDATE、生产 lease/backing 复用均未修改。没有 Batch A、性能优化、eager fallback 或 public Gate 放开。

## 2. 原始证据与完整性

只读输入目录：
`/Users/wenqingzhang/Desktop/中转/private-file-relay/transfers/2026-10-20/MRV2_P7X_A3_Repair2/20261019T065743Z_8198ab7a/return`

| 包 | bytes | SHA256 | 校验 |
|---|---:|---|---|
| review.zip | 577782 | 726bbf44393da3dd316c9252728e7a59c13e7e1c29b8d21a9b0d3d4d9649d959 | CRC通过，163 entries；161项包内 hash通过 |
| raw.zip（part001+part002按顺序恢复） | 179215014 | ffe1b1581707509c13aaa100d1b0157aad96ece5423ae7f893025100be995f08 | CRC通过，207 entries；205项 hash通过 |

原 ZIP/part/manifest 均未修改。安全检查拒绝路径越界和 symlink。临时解析位置：`/private/tmp/p7x-repair3.BV5NUG/review`、`raw`；交付辅助目录 `evidence_verification.json` 保留原路径、哈希、排除项，可用附带 verify_evidence.py 重建，不把重新序列化的 JSON hash 当原始 hash。

ARTIFACT_INDEX 声明 file_count=205，实际 files 数组207项：额外两项是明确 self_excluded 的 ARTIFACT_INDEX/SHA256SUMS，没有循环 hash。review 缺42个 .pt与2个大型head比较JSON，恰是声明的raw-only文件；不是损坏。review 51份JSON、raw 53份JSON全部可解析。205个indexed有效文件bytes/hash匹配。38条ledger CMD-0001–0038完整。

9个 import_provenance Python module hash 对应 exact git blob 均匹配；native .so donor仅有记录，不宣称本机执行或重新校验服务器未交付本体。evidence refs 两个是源码符号引用（`draft_window_graph_characterization.py:664/678`、`tools/p7x_graph_repair2.py audit_campaign`），其余实际文件可解析。旧 runtime env/sitecustomize/overlay 构建配方没有随包完整交付；下一轮要求作为文本单独打包。

读取并重新解析：两份 partial、A0/A1/B-observer-off/B-boundaries/G4-A0/G4-B campaign，两个target-boundary，Gate Decisions/Next Local Input/中文报告/Gap报告，source/import manifest、campaign_plan、ledger、trace_probe、B0/B_crashpin stderr、query_trace，以及旧 compare_g4.py/run_official_g4_compare.py/g4_comparison/g3_oracle_partial。没有执行从服务器报告复制的脚本。

## 3. Finding Resolution

| ID | Server claim / 原始实证 | Source fact / 裁决 | Action / Test | Remaining |
|---|---|---|---|---|
| R3-01 | 两次observer-on native SIGSEGV；query_trace call3进入UPDATE query无EXIT；NPUEvent::query / rtEventQueryStatus | ACCEPTED：直接触发调用已定位；不能推断所有ExternalEvent/版本不支持query | 删除observer query helper；记录类型/Host identity，completion=null；禁止调用fake-event红绿测试 | A3同配置重跑确认不再在该点崩溃；native底层根因未证明 |
| R3-02 | record一次query，snapshot/write_artifact再次query | ACCEPTED：导出隐式设备访问是代码缺陷 | snapshot纯Host序列化，采样时间不变；重复导出全等；无事件强引用、weakref可回收 | 设备trace/completion仍OPEN |
| R3-03 | 15/15 capture layer_name=null | ACCEPTED：普通forward不填layer-aware缓存且未把layer传到FIA；原测试预填答案 | 实际forward在已挂载capture context时绑定instance execution layer name；与KV owner分离；真实forward链及5层三descriptor测试 | 新SHA每bucket真实层集合需A3核验 |
| R3-04 | 报告摘要有“update operator not reached” | PARTIALLY_ACCEPTED：持久化update=0属实；未到达UPDATE的归因不成立 | 修正文档，按source/内存/持久化/device四层分类；无功能时序改动 | 不据Python返回推断设备完成 |
| R3-05 | observer-off三bucket功能完成、G4 head-only一致 | PARTIALLY_ACCEPTED：完成输出/inventory属实；不能证明每bucket replay/task；G4仅短smoke | 全集严格比较，raw 21对独立复算通过；max position/exact=27；FULL_TARGET保持OPEN | 长上下文S>0、真实replay与KV对齐另测 |

旧两份 partial 都是10 events /15 operand /1 G4 /1 lifecycle；全部capture operand层名为null，不补填。历史Gate不被新checker或本机green改成PASS。

## 4. 根因、真实调用链和测试漏洞

### 4.1 原生事件

```text
DFlashAclGraphManager.run_fullgraph
  → update_full_graph_params
  → AscendAttentionBackendImpl.update_graph_params
  → graph_task_update_begin / FIA.out / graph_task_update_end / event.record
  → record_parallel_graph_update_operator_operand
  → record_update_operand: _append_operand(...)  [仅内存]
  → record_lifecycle: _query_event_without_sync(event)
  → NPUEvent::query → rtEventQueryStatus → SIGSEGV
```

query_trace: call1 replay event=False，call2导出重查同event=False，call3 UPDATE event无返回。Python except RuntimeError无法捕获native SIGSEGV。

| 层 | 本次旧证据能证明什么 |
|---|---|
| SOURCE_DERIVED_CALL_REACHABILITY | 到达observer之前backend update调用顺序已经执行到event.record返回 |
| IN_MEMORY_RECORD_REACHABILITY | 按exact source，在query调用前已执行_append_operand；无独立内存dump，不冒充durable证据 |
| DURABLE_ARTIFACT | 上次已刷盘的partial仍只有15 capture，0 update；finally在SIGSEGV下未执行 |
| DEVICE_COMPLETION | 未证明；record/return/id(handle)/Host timestamp都不是设备完成 |

### 4.2 逐层身份

真实builder对一个group构建一个metadata对象，再把同对象分配给多个layer key。Repair2按对象去重挂载是正确的，保留预验证、幂等、冲突/Target拒绝、setattr失败回滚和closure固定CaptureIdentity。

普通链是 `Attention layer → impl.forward(layer,...) → forward_impl → forward_fused_infer_attention → full_graph_fia(layer=None) → observer`。构造时 `_layer_name=None`，只有 `_use_layer_aware_fia_graph_replay=True` 才赋值。普通Base为False。原测试用 `impl._layer_name=layer_name` 再直接调full_graph_fia，因此掩盖了真实数据缺口。KV sharing时 `_graph_metadata_layer_name` 表达metadata owner，不等于executing layer。

本次最小绑定：backend实例新增独立 `_capture_observer_layer_name`，仅实际forward遇到已挂capture context的metadata时，从真实 `layer.layer_name` 设置；FIA observer优先使用显式layer参数，否则读取该instance执行身份。没有从共享metadata反推唯一layer、没有按dict轮询名称、没有修改layer-aware策略或KV-sharing replay key。普通无observer路径不设置观测身份；None metadata原行为继续通过。

这不是新增Graph支持范围。backend实例归属于Attention layer；capture closure再次执行真实forward时重新携带实际layer，metadata context仍携带对应descriptor/provider/backing。Host测试替代NPU primitive，但不替代builder/forward/FIA/observer链。

## 5. 核心diff（完整diff另附）

```diff
- self._completion_tokens[event_identity] = event
- event_complete=_query_event_without_sync(event)
+ event_complete=None
+ event_type=None if event is None else _class_path(type(event))
- result['event_complete'] = _query_event_without_sync(token)
- result['query_host_monotonic_ns'] = time.monotonic_ns()
+ result['query_host_monotonic_ns'] = None
+ result['completion_source'] = None
+ result['completion_status'] = 'UNPROVEN'
```

移除只为观测创建的replay completion token，REPLAY_SUBMITTED只记Host提交/stream身份，event=null；不再为日志保留event对象。backend真正ExternalEvent对象仍由原graph params拥有，wait/reset/record一行未改。没有新增queryable=True、sync或新的completion协议。

```diff
+ if getattr(attn_metadata, '_draft_window_graph_capture_operand_context', None) is not None:
+     self._capture_observer_layer_name = layer.layer_name
- layer_name=self._graph_metadata_layer_name(layer)
+ layer_name=layer.layer_name if layer is not None else self._capture_observer_layer_name
```

capture callback依旧只做Host记录，不D2H、不写文件、不query。snapshot复制Host事实，不刷新Host采样时间。已存在的safe flush点保留；没有承诺所有native crash均可保存最后一条内存事件。外部launcher另存identity/stdout/stderr/真实returncode/signal，driver progress.json记录BEFORE_STARTUP/STARTUP_COMPLETE/BEFORE_GENERATE/AFTER_GENERATE；不伪造campaign.json。

## 6. 逐文件说明

| 文件 | 改动 |
|---|---|
| vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py | 被动生命周期、纯导出、无event强引用/重复query；recorder_revision=repair3-passive |
| vllm_ascend/attention/attention_v1.py | 实际执行layer与KV metadata owner分离；无算法/任务协议改动 |
| tools/p7x_graph_repair2.py | duplicate task/layer检查；独立case-id；progress；launch；combined requests；analyze全序列/边界；compare-probes全集 |
| tests/ut/spec_decode/test_draft_window_capture_observer.py | 真实forward红测、shared/KV owner、三descriptor/warmup/closure、禁止event访问与weakref释放 |
| tests/ut/spec_decode/test_draft_window_graph_characterization.py | replay观测不创建event，不把False当已知completion |
| tests/ut/spec_decode/test_graph_repair2_campaign.py | 新入口、signal、全集缺项/shape/dtype/NaN/重复hash/未送raw、缺层错层重复关联、早期ABA候选回归 |

## 7. RED → GREEN

环境：macOS arm64，repo `.venv` Python3.12；`VLLM_VERSION=0.29.0 PYTHONPATH=../vllm`。无NPU。

修改production前：

```bash
VLLM_VERSION=0.29.0 PYTHONPATH=../vllm .venv/bin/pytest -q \
 tests/ut/spec_decode/test_draft_window_capture_observer.py \
 -k 'real_builder_to_shared_metadata_to_real_fia or lifecycle_and_export'
```

exit1，3 failed：普通路径 `[None,None] != [draft.layers.0.self_attn,draft.layers.1.self_attn]`；KV owner路径两个`kv.shared.owner`错误；`AssertionError: backend event query forbidden`。另外新driver三个入口先以AttributeError记录RED（不是生产根因复现，明确区别）。

最终命令：

```bash
VLLM_VERSION=0.29.0 PYTHONPATH=../vllm .venv/bin/pytest -q \
 tests/ut/spec_decode/test_draft_window_capture_observer.py \
 tests/ut/spec_decode/test_graph_repair2_campaign.py \
 tests/ut/spec_decode/test_draft_window_graph_characterization.py \
 tests/ut/spec_decode/test_draft_window_graph_carrier.py \
 tests/ut/spec_decode/test_draft_window_graph_binding.py \
 tests/ut/spec_decode/test_draft_window_graph_oracle.py \
 tests/ut/spec_decode/test_dspark_graph_contract.py \
 tests/ut/attention/test_attention_v1.py
```

最终 exit0：**270 passed，0 failed，0 skipped，另2个subtest passed，1个缺vllm._version警告**。重复迭代执行次数不累计为独立test数。保留中间失败：新增context读取曾影响None metadata baseline，已改为仅检查attached metadata；signal测试Popen替身曾误截获git subprocess，已把该测试的git身份读取单独stub，最终全部通过。未把这些真实回归标成环境问题。

保留F1–F4、Python -O、wrong generation/backing/scope、alias/canonical sharing、observer OFF/provider成立、公共Gate、attachment原子回滚/旧closure、普通attention/KV-sharing回归。

测试替代：torch.npu graph/task/event/FIA执行由Host stub替代，设备kernel/stream未执行。真实Ascend builder、上游capture closure工厂、真实forward/FIA函数、P3/Graph carrier、recorder与checker执行。真实recorder→checker例只有(4,8) Host bucket，因此仍OPEN complete smoke，绝不降低三个真实bucket要求。

静态：Ruff/format、targeted Mypy（tool+recorder两模块）、compileall六文件、diff-check、本地python-init/forbidden-imports/boolean-context/long-functions/symbolic-meta/logger通过。完整pre-commit runner exit3：actionlint Go依赖下载 proxy.golang.org 网络超时，ENVIRONMENT_BLOCKED；已安装ruff-check/ruff-format/codespell/typos hooks独立全部exit0；gitleaks staged scan exit0/no leaks。完整命令、exit及日志见辅助目录check_results.json/static_checks。

## 8. 新driver合同及入口

继续使用 `tools/p7x_graph_repair2.py`，不另起服务器框架。

| 入口 | 输入/输出 | 证据级别/边界 |
|---|---|---|
| run --case B --case-id B0 --run-id R --attempt 01 | campaign/progress/partial | --case仍是A0/A1/B/B-observer-off功能mode；case-id是真实用例；旧命令默认case-id=mode兼容 |
| launch --run-id R --case-id B0 --mode B --attempt 01 --output L --timeout 1800 -- python ... run ... | 独立launcher.json/stdout.log/stderr.log | 子进程实际exit、负signal、timeout；不经echo/tee；不等于设备completion |
| make-requests --profile smoke/boundaries/combined | tokenizer-local requests JSON | 默认combined：1/2/4后32/1024/1025/1151/1152/1153/2049/32；请求长度不是实际E/H |
| check campaign.json --output ... | 原四namespace | 三bucket完整smoke要求不变；task/physical/completion始终需独立证据 |
| analyze campaign.json --output ... | 保留official_check；runtime H/E/S/V、未触达边界、全序列ABA候选source sequence IDs | 只扫描同record scope/descriptor/backing；严格单调；100000对搜索上限明确scan_complete=false；HOST_CANDIDATE不是设备PASS |
| compare-probes left/target-boundary.json right/target-boundary.json --output ... | write_semantics/head_only_numeric/full_target_numeric分别输出 | 非zip截断；完整层集合；重复hash按有序样本保留；缺raw=OPEN；weights_only=True；每tensor shape/dtype/finite/hash验证；FULL_TARGET永远OPEN |
| trace-probe --output ... | 安装/帮助/所需export fields | CAPABILITY_UNVERIFIED，不依赖已有observer记录即可先探测 |

`compare-probes`两个JSON旁边需要各自.pt；不会自动读取旧服务器绝对path。跨进程只比语义、非数字指针；单进程canonical对象身份继续由carrier validator验证。exact tolerance atol=rtol=0仅用于identical hidden input的head诊断，不是通用BF16精度阈值。所有样本通过才给全集head PASS；出现missing/extra/layer/NaN/shape/dtype不完整不会靠一个成功样本通过。

## 9. 历史数值重新裁决

RAW_NUMERIC_RECOMPUTATION=PASS_HEAD_ONLY：从验证过的42个.pt用weights_only加载，21对原始hidden hash各自唯一，所有dtype/shape/finite/实际input hash匹配，hidden_states与logits均torch.equal。21对完整write记录的before和after均语义相同；缺失层不忽略，比较全层集合。源文件/输入/输出hash保存在raw_numeric_recomputation.json。

因此旧脚本的zip截断、字典覆盖、any(pass)是未来数据的漏检风险，但不能据此否定本次实际全部相同的21对。最大Target exact/position=27，所以仅短场景。旧observer-off输出成功不证明三bucket逐次设备replay，Python query_trace不是NPU timeline。

## 10. 未闭环项与具体seam设计

| 项目 | 状态 | 本轮处理/下一步 |
|---|---|---|
| GAP-R2-001/002/003 | LOCAL_HOST_FIXED | 被动event、纯导出、真实layer；A3 B0复测 |
| GAP-R2-004 trace | TOOL_CAPABILITY_REQUIRED | 已读包内msprof --help；支持application/runtime-api/task-time/export选项；导出字段能力未知 |
| GAP-R2-005 FULL_TARGET | FIXTURE_REQUIRED | 下述控制设计，未改scheduler/KV owner |
| GAP-R2-006 ABA | DEVICE_REQUIRED/FIXTURE_REQUIRED | 全序列候选扫描已实现；自然A′不存在则OPEN，不伪造allocator |
| GAP-R2-007 abort | NEEDS_TEST/DEVICE_REQUIRED | 未找到已证明安全in-flight注入点；不随机kill正在用backing的consumer |
| GAP-R2-008 三bucket | DEVICE_REQUIRED | B0固定请求+真实inventory和records验证；不得以输出请求数推定 |
| GAP-R2-009 checker空证据 | PRESERVED | 四namespace仍分开，空集合不PASS |
| GAP-R2-010 resources | DEVICE_REQUIRED | 上轮后来有空闲die不是本轮空闲证明；服务器先获授权资源 |

FULL_TARGET具体设计：现有probe包装的是spec.propose前后与model.compute_logits，只能看到head输入及write snapshot；upstream GPUModelRunner.execute_model负责准备Target input/metadata，sample_tokens有拒绝/采样状态。Graph重放时Python model.forward wrapper不能作为每次Target前向输入证据。后续应在execute_model准备完成、Target launch之前取得token IDs/absolute positions/query/request layout与**对应可见KV内容和版本**，在相同phase匹配后比较Target输出；需要证明这个快照与实际launch对应、冻结容差、处理rank/版本、禁用异步重写。当前没有已证明的完整KV快照+alignment接口，因此只提供设计，未添加重放控制或owner swap。模型/seed/prompt相同不够，head-only保持分列。

G5：Host source顺序保留，event来源类名/Host ID只是关联信息；不要把Python id当device task ID，也不要跨时钟域按数值排序证明happens-before。需要task提交/重绑定/launch/completion/下代backing rewrite的同代关联；API不足时OPEN，不自动引入双缓冲或global synchronize。

## 11. 下一轮固定A3方案

固定fixture不再重新寻找：Target `/mnt/share/wql/Qwen3-8B`，Draft `/mnt/share/dspark_qwen3_8b_block7`；沿用inputs/fixture_manifest.json十项hash。
DSpark K=7/query=7/sample_from_anchor=true，W=1024，block128，capacity1151 **不等于** max_model_len。
driver实际max_model_len=4096/max_num_batched_tokens=4096/max_num_seqs=4/gpu_memory_utilization=.80/seed0/temp0/max_tokens16/ignore_eos=true。
FULL_DECODE_ONLY、actual FULL、capture[7,14,28]；single STANDARD dense GQA/FIA；所有parallel=1，async/prefix/SP/DSA-CP/FlashComm关闭。

辅助目录 `Repair3_Server_Commands.md` 与 `Repair3_A3_Rerun_Plan.json` 给出真实CLI、依赖、输入/输出/timeout/PASS/STOP。源码未发布，服务器必须等待发布审查+GitHub exact clone校验，不能拿旧8198的结果继承。

顺序：P0→A0→A1→B0→B1→O0→G4短/长→G2分析→R0；T0工具探测可独立于B0开展。B0必须无原query崩溃、完整三bucket实际records、实际Draft layer非空且匹配、capture/bound/G4/update同代；不能硬编码“总共5条update”。callback重复以helper/descriptor/generation/layer/task handle关联，不把合法warmup当缺陷。

先对最小可运行O0使用msprof --application、--runtime-api=on、--task-time=on。采集和export分别记录退出码；有帮助选项不等于采集成功、有文件不等于字段足够。要求导出device task/stream IDs、launch/update/completion关联及operand描述；Memory/MemoryAccess命名不证明physical block read-set。失败保持CAPABILITY_UNVERIFIED/OPEN并提交验收问题。

observer-off=实验flag1+OBSERVE0，provider/carrier仍成立；不能用experimental0导致GRAPH_FROZEN冒充observer-off实验。

## 12. 交付、风险与回退

交付主报告、handoff、辅助ZIP及所有脚本/RED/GREEN/static/diff/解析摘要；不打包模型、native环境或原服务器大ZIP。最终辅助包先固定文件再生成ARTIFACT_INDEX/SHA256SUMS，ZIP hash在包外manifest生成，校验解压/JSON/成员hash，无循环hash。

风险：Host stub不能证明native不崩；没有新增设备completion采样；layer身份仍需真实A3验证；full Target/KV fixture和trace字段有明确缺口；long-context可能触发其他integration defect；public Gate始终冻结。完整Graph Base acceptance仍未满足。

回退：选旧已发布8198的独立checkout作诊断对照，不reset用户工作区，不amend新提交；**不要**在已知崩溃的observer-on旧版反复跑设备。上线前单独review和普通push。下一步仅A3 P0/A0/A1/B0，不开始Batch A或性能测试。

## 13. Final status

```text
REPAIR3_LOCAL_IMPLEMENTATION=LOCAL_REPAIR_HOST_VERIFIED
R3-01_EVENT_QUERY=DEFAULT_QUERY_ZERO_HOST_VERIFIED
R3-02_PURE_SNAPSHOT=HOST_VERIFIED
R3-03_CAPTURE_LAYER_IDENTITY=HOST_VERIFIED
RECORDER_TO_CHECKER_INTEGRATION=HOST_VERIFIED
LONG_CONTEXT_G4_PREPARATION=REQUESTS_AND_COLLECTION_READY / FULL_TARGET_FIXTURE_OPEN
ABA_ANALYSIS_PREPARATION=IMPLEMENTED_HOST_VERIFIED
TRACE_PREPARATION=COMMAND_PLAN_READY / CAPABILITY_UNVERIFIED
PUBLICATION=NOT_PUBLISHED
READY_FOR_PUBLICATION_REVIEW=YES
READY_FOR_A3_SMOKE_AFTER_PUBLICATION=YES (conditional)
READY_FOR_ALL_G1_G5_CLOSURE=NO
NEW_SHA_DEVICE_VERIFICATION=NOT_RUN
PUBLIC_GRAPH_GATE=STILL_FROZEN
```

## Appendix A — 下一轮可直接执行的服务器命令

# Repair3 A3 rerun — exact commands and stop rules

本文件是计划，不是设备执行结果。候选未发布。先 independent review，再由 owner 授权普通发布；服务器 clean fetch 后才运行。禁止本地包替代 GitHub source 身份，禁止偷偷改 capture sizes。所有命令在 bash 中执行，每项退出码独立保留。

## P0 — 必填路径与 exact source

以下四个路径由服务器 Agent 从实际部署/旧 command ledger 解析，不猜 Python/native 环境；必须指向新 clean checkout 和现有已审核 fixture manifest。不要创建假的模型路径。

```bash
export REPAIR3_REPO=/absolute/path/to/new-clean-vllm-ascend
export REPAIR3_VLLM=/absolute/path/to/pinned-clean-vllm
export REPAIR3_PYTHON=/absolute/path/to/approved/python
export REPAIR3_FIXTURE=/absolute/path/to/original/inputs/fixture_manifest.json
export REPAIR3_OUT=/absolute/path/to/new-empty-artifact-directory
export REPAIR3_RUN_ID=2026xxxxTxxxxxxZ_10cbf4c0
export REPAIR3_ATTEMPT=01
export REPAIR3_SHA=10cbf4c014fc6cc48a6fea611bb605cecdd54cfd
```

`REPAIR3_OUT`须不存在；`mkdir`失败就停止，不能覆盖旧证据。

```bash
set -euo pipefail
cd "$REPAIR3_REPO"
test "$(git rev-parse HEAD)" = "$REPAIR3_SHA"
test "$(git rev-parse HEAD^{tree})" = 28dddd6d1fc19e67270ee71b7b9e7fcd410ab3c9
test -z "$(git status --porcelain --untracked-files=all)"
test "$(git -C "$REPAIR3_VLLM" rev-parse HEAD)" = 84030bbe3d74d99bad477a3d2e37a973ccd8865c
test "$(git -C "$REPAIR3_VLLM" rev-parse HEAD^{tree})" = f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
test -z "$(git -C "$REPAIR3_VLLM" status --porcelain --untracked-files=all)"
test "$(sha256sum "$REPAIR3_FIXTURE" | cut -d ' ' -f1)" = 1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4
test "$(sha256sum tools/p7x_graph_repair2.py | cut -d ' ' -f1)" = 7e6f2e5984430bc5231511960da2fdc9b073ddc58cfed8bfaed796498b70660d
mkdir "$REPAIR3_OUT"
mkdir "$REPAIR3_OUT/inputs" "$REPAIR3_OUT/runtime-recipes" "$REPAIR3_OUT/analysis" "$REPAIR3_OUT/traces"
cp "$REPAIR3_FIXTURE" "$REPAIR3_OUT/inputs/fixture_manifest.json"
```

保存实际执行的 runtime env脚本、sitecustomize、overlay构建脚本、diagnostic wrapper 到 runtime-recipes/（仅文本，勿带token/native环境）。沿用 repair2 已审核 MRV2 overlay 的构建规则，但重新以新SHA生成；不能复用旧Python .py缓存。记录Python/CANN/torch/torch_npu/vLLM版本、每个import `__file__`和sha256、native donor版本、device UUID/rank和空闲资源。`PYTHONPATH`必须由该已审核环境配方给出，不能在这里猜一个不含native环境的路径。driver会再校验fixture各文件实际hash。

检查实际 runner=NPUModelRunner、speculator=AscendDSparkSpeculator、method=dspark、K/query=7、sample_from_anchor=true、single STANDARD dense FIA；A3 TP/DP/PP/PCP/DCP=1，其余async/prefix/SP/DSA-CP/FlashComm关闭。资源不足记RESOURCE_BLOCKED，不记expected Gate。

## 请求准备与统一 launcher

```bash
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py make-requests --target-model /mnt/share/wql/Qwen3-8B --profile smoke --output "$REPAIR3_OUT/inputs/smoke.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py make-requests --target-model /mnt/share/wql/Qwen3-8B --profile combined --output "$REPAIR3_OUT/inputs/combined.json"
```

combined在一个engine里先1/2/4 smoke，再32、1024、1025、1151、1152、1153、2049、32 token刺激。必须按actual H/E/S/V判覆盖，不根据prompt长度补造exact。

```bash
run_repair3_case() {
  local case_id="$1" driver_mode="$2" profile="$3"
  shift 3
  "$REPAIR3_PYTHON" tools/p7x_graph_repair2.py launch \
    --run-id "$REPAIR3_RUN_ID" --case-id "$case_id" --mode "$driver_mode" \
    --attempt "$REPAIR3_ATTEMPT" --timeout 1800 \
    --output "$REPAIR3_OUT/${case_id}-launcher" -- \
    "$REPAIR3_PYTHON" tools/p7x_graph_repair2.py run \
    --case "$driver_mode" --case-id "$case_id" --run-id "$REPAIR3_RUN_ID" \
    --attempt "$REPAIR3_ATTEMPT" --expected-sha "$REPAIR3_SHA" \
    --vllm-repo "$REPAIR3_VLLM" --fixture-manifest "$REPAIR3_FIXTURE" \
    --target-model /mnt/share/wql/Qwen3-8B --draft-model /mnt/share/dspark_qwen3_8b_block7 \
    --requests "$REPAIR3_OUT/inputs/${profile}.json" --output "$REPAIR3_OUT/$case_id" "$@"
}
```

launcher身份在模型启动前落盘；SIGSEGV child returncode=-11/signal=11，shell139，不伪造campaign。Host monotonic仅进程内时钟。独立工具输出和真实子进程exit不得被echo/tee覆盖。每个case执行后先审核结果再继续：

```bash
run_repair3_case A0 A0 smoke
run_repair3_case A1 A1 smoke
run_repair3_case B0 B smoke
run_repair3_case B1 B combined
run_repair3_case O0 B-observer-off smoke
```

A1 driver只有捕获到预期GRAPH_FROZEN才expected；检查campaign exception/callsite，不将任意启动错误算成功。A0无provider/session。B0/B1 provider存在且bound/publish真实到达，observer-on；O0保留experimental1但observe0，不能experimental0。固定图配置`FULL_DECODE_ONLY`/actualFULL/capture[7,14,28]不变；max_model_len4096、capacity1151是两个不同概念。

## B0/B1严格判定

```bash
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py check "$REPAIR3_OUT/B0/campaign.json" --output "$REPAIR3_OUT/analysis/B0-check.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py analyze "$REPAIR3_OUT/B0/campaign.json" --output "$REPAIR3_OUT/analysis/B0-analysis.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py check "$REPAIR3_OUT/B1/campaign.json" --output "$REPAIR3_OUT/analysis/B1-check.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py analyze "$REPAIR3_OUT/B1/campaign.json" --output "$REPAIR3_OUT/analysis/B1-analysis.json"
```

check exit2可以是OPEN或INVALID，必须读取四namespace；不能把它改成shell PASS。无campaign时不要用empty JSON顶替，保留partial/progress/launcher。B0要求实际capture/bound/replay/update的(1,7)/(2,14)/(4,28)，预期层集来自spec.draft_attn_layer_names、非null、无缺层错层重复task/layer、同generation/source/backing。不能硬编码5次UPDATE总量。nativequery零是新source合同，A3不崩是待检验结果。TASK_BINDING/PHYSICAL_READ/COMPLETION不因Host check PASS升级。

B1要求runtime oracle至少S=0和S>0、非block-end、变化active/padded rows、多generation。未精确触达E=1024等时标NOT_REACHED；允许据真实观察设计下一轮fixture，但不能把期待值改成观察值。出现source shortage、identity mismatch、alias、Gate错误，停止依赖该路径的后续case并保留first divergence。

## G4短/长分列

```bash
run_repair3_case G4-A0-short A0 smoke --target-probe
run_repair3_case G4-B-short B smoke --target-probe
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py compare-probes "$REPAIR3_OUT/G4-A0-short/target-boundary.json" "$REPAIR3_OUT/G4-B-short/target-boundary.json" --output "$REPAIR3_OUT/analysis/G4-short.json"
run_repair3_case G4-A0-long A0 combined --target-probe
run_repair3_case G4-B-long B combined --target-probe
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py compare-probes "$REPAIR3_OUT/G4-A0-long/target-boundary.json" "$REPAIR3_OUT/G4-B-long/target-boundary.json" --output "$REPAIR3_OUT/analysis/G4-long.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py analyze "$REPAIR3_OUT/G4-B-long/campaign.json" --output "$REPAIR3_OUT/analysis/G4-long-boundaries.json"
```

所有.pt须留在对应target-boundary.json旁边。完整有序样本/层集合/shape/dtype/有限值/源hash/数值都检查，重复hash不覆盖。不对齐时FAIL_ALIGNMENT/OPEN，不说明Window数学一定错。atol=rtol=0仅identical hidden input的head诊断。cross-process不要求数字ptr相等；same-process canonical identity由live validator验证。长case未实际S>0不得宣称long G4。probe含D2H，NOT_PERFORMANCE_REPRESENTATIVE。

FULL_TARGET/KV fixture当前**未实现**。禁止将head-only PASS改为FULL_TARGET PASS；需要Target实际token/positions/query/request layout与KV内容/版本/phase同态，再固定dtype容差。本轮无安全控制seam就输出FIXTURE_REQUIRED，不修改scheduler/owner。

## T0独立能力探测与有界采集

T0 help发现不依赖B0成功。采集仅在P0/A0通过、设备和最小O0路径可用时运行；若B0失败仍可独立检查O0，不能拿它覆盖B0失败。

```bash
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py trace-probe --output "$REPAIR3_OUT/traces/trace_probe.json"
msprof --help
```

repair2真实帮助包含`--application/--output/--runtime-api/--task-time/--export/--summary-format/--type`。先核对本机help；不存在就CAPABILITY_UNVERIFIED，不替换为未经核对的选项。最小采集命令（路径不含空格；有空格须正确shell quoting）：

```bash
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py launch \
 --run-id "$REPAIR3_RUN_ID" --case-id T0 --mode B-observer-off --attempt "$REPAIR3_ATTEMPT" \
 --timeout 1800 --output "$REPAIR3_OUT/T0-launcher" -- \
 msprof --output="$REPAIR3_OUT/traces/msprof" --runtime-api=on --task-time=on --export=on --type=text --summary-format=csv \
 --application="$REPAIR3_PYTHON $REPAIR3_REPO/tools/p7x_graph_repair2.py run --case B-observer-off --case-id T0 --run-id $REPAIR3_RUN_ID --attempt $REPAIR3_ATTEMPT --expected-sha $REPAIR3_SHA --vllm-repo $REPAIR3_VLLM --fixture-manifest $REPAIR3_FIXTURE --target-model /mnt/share/wql/Qwen3-8B --draft-model /mnt/share/dspark_qwen3_8b_block7 --requests $REPAIR3_OUT/inputs/smoke.json --output $REPAIR3_OUT/T0"
```

区分profiler wrapper退出与被测进程真实status，解析其stderr和campaign；两者任一缺失就OPEN。若导出自动失败，保留采集目录与错误，按本机help可用的export模式单独执行/保存exit，不编造命令。

导出所需字段：device/process/task/stream/correlation IDs、task create/update/launch/completion、descriptor与真实operand地址/length关联。Host id(handle/event)非设备ID。`Memory/MemoryAccess`指标**不等于**physical block read-set。列installed/help/capture/export-fields/sufficient五阶段；每个缺口提交确切验收问题，不重引入unsafe event query。

## G2、Abort、R0

G2复用B1-analysis全序列候选。只有同run/engine/provider/descriptor/backing且generation/epoch递增，A与A′ table/exact/upper和source-lineage一致，B不同才HOST_CANDIDATE。没有候选或scan_complete=false就OPEN。即使Host候选通过，需task/stream trace关联replay/update/rewrite，才能设备裁决；不可重写活跃allocator伪造A′。

Abort无安全的in-flight注入/观测seam，当前NOT_RUN / FIXTURE_REQUIRED。不要用kill进程当无early-overwrite证明，或用Host假event当device completion。只在owner确认具体seam后新增case，本轮不自动执行。

R0保存：新source/import identity，device/topology，fixture hashes，完整command+exit ledger，各case launcher/progress/campaign/partial/原stderr，checker四namespace，原始trace，runtime文本配方，target-boundary与引用.pt。空数据不是功能PASS。使用交付的`package_repair3_return.py`生成review/raw两个包，raw数字结论明确RAW_REQUIRED；最终ZIP固定后在包外计算DOWNLOAD_MANIFEST。上传接收后再次核对bytes/hash/CRC/member-hash，才RECEIVED_VERIFIED。本机产物校验不等于用户已收到。

停止规则：不自动重试native crash；保存first divergence。P0 identity/fixture错误阻止所有模型测试；B0失败阻止B1/G4-B/G2，允许独立T0 help/O0资源许可诊断；T0失败不改功能路径；G4不对齐不能删样本凑PASS。全程无Batch A、性能测量或public Graph enable。

## Appendix B — 交付脚本边界

辅助packager已用合成文件测试review/raw分离、member hash/CRC、拒绝nested output和symlink；不计入270个production UT，未打包任何新设备结果。分析脚本保留原执行时的Mac路径，需要重跑时使用原输入哈希定位；只写派生输出。完整pre-commit环境阻塞不被单独hooks通过替代。最终提交后同一270例和所有可运行静态命令又执行一次，均对应此SHA。
