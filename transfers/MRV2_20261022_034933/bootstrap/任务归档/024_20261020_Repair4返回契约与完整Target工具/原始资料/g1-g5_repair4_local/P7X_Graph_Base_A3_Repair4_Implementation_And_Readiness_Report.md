# 最终身份：aaa4632612503adb34d90b55c36eedcaf0848979

# P7-X Graph Base A3 Repair4 — Implementation & Readiness

EAGER/PUBLIC GRAPH SUPPORT DOES NOT CHANGE. PUBLIC_GRAPH_GATE=STILL_FROZEN.
本报告区分本地 Python 合同、受控诊断 fixture 与真实 MRV2/NPU 集成证据；不将任何 Host PASS 升级为 G1–G5 PASS。当前提交只在本地，未 push/PR/merge/tag。

## 1. 输入身份、恢复与独立裁决

输入 RUN_ID 为 `20261019T185701Z_10cbf4c0`。原始返回目录：
`/Users/wenqingzhang/Desktop/中转/private-file-relay/transfers/2026-10-20/MRV2_P7X_A3_Repair3/20261019T185701Z_10cbf4c0/return`。

原始输入保持只读；raw 两分片在独立 `/private/tmp/repair4/evidence` 合并。review 整包 SHA256 `633664dee2062f654162e71e9da04c745940b34d2ee33b183351d71cee57f164`，raw 整包 SHA256 `9625b9eab9b4baf2400700bb127ab40de63896915ba7e89e96d6a44efcd74031`。按原 manifest 校验 bytes、ZIP CRC、安全成员路径、ARTIFACT_INDEX 每项 bytes/hash：review **335** 项，raw **382** 项，raw **47** 个 `.pt`。含 index/checksum 的 ZIP 成员数分别337/384，不是统计冲突。源 manifest 没有单独的 shard hash；本地只补记录原始分片自身摘要，不伪称存在服务器分片签名。47个 tensor 用 `weights_only=True` 本地载入，shape/dtype/finite 检查成功，全部来自 OFF。

逐项读取：Server Final Report、NEXT_LOCAL_CODEX_INPUT、Mandatory Gap、G5 Timeline、TRACE_CAPABILITY_REPORT、source/import/fixture/environment manifests、campaign/launcher/partial、runtime recipes、command ledger、T0 op_summary/task_time。9个实际 import 文件的 hash 还与相应固定 Git blob 对照；不是仅信服务器说明。

原始模型 manifest hash：`1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4`。模型不重新选择：Target `/mnt/share/wql/Qwen3-8B`；Draft `/mnt/share/dspark_qwen3_8b_block7`。复制原 manifest/请求 JSON，不复制权重、不重新序列化 manifest。

|服务器事实|本地裁决|不能推出|
|---|---|---|
|A0正常；A1 GRAPH_FROZEN|保持，检查实际 campaign/launcher|新SHA成功|
|15个 capture_operator：3 buckets × 5真实层|成立；层36–40，与KV sharing owner不同|三个runtime bucket都执行|
|B0 generation0/epoch0，(1,7)，5 UPDATE operator记录|成立|UPDATE设备完成、backing可复用|
|B0输出hash收到None，Python TypeError，rc2/signal=null|确定 observer 代码缺陷|allocator/Graph core必然错误|
|本次路径无旧 ExternalEvent.query 崩溃|已覆盖路径上消除|所有设备event安全|
|O0/O1短/长/混合完成|真实局部功能证据|observer ON长/混合通过|
|47个OFF tensor|独立校验成功|OFF/ON或FULL_TARGET比较|
|T0真实trace：op_summary13676行、task_time23215行|导出确实存在|task operand/physical read/generation completion|

完整原始复核结果在包内 `evidence/verification.json`、`evidence/independent_audit.json`。B0关键栈：

```text
DFlashAclGraphManager.run_fullgraph
  ret = super().run_fullgraph(desc)  # legal None
  record_parallel_graph_output(self.speculator, ret)
DraftWindowGraphCharacterizationRecorder.record_output_hashes
  _hash_tensor_tree(None)
TypeError: unsupported graph output hash type: NoneType
```

## 2. 真实返回契约与根因

固定 upstream `vllm/v1/worker/gpu/cudagraph_utils.py::CudaGraphManager.run_fullgraph` 仅检查FULL/descriptor、`sync_prev_onload()`、`graphs[desc].replay()`，没有返回 Tensor。DFlashCudaGraphManager未覆盖该方法。不能与返回hidden_states的ModelCudaGraphManager混同。

`DFlashSpeculator._generate_draft` / `DSparkSpeculator._generate_draft` 在Graph内写 `self.draft_tokens`；`DFlashSpeculator.propose`忽略manager返回值，最后返回`self.draft_tokens[:num_reqs]`。Ascend manager继承的合法返回是None，但旧注解/docstring和observer错误地假设有Tensor。

```text
propose / full prepare / frozen generation
  → P3 materialize + P6 carrier bind/publish
  → Ascend DFlashAclGraphManager.run_fullgraph
  → upstream CudaGraphManager.run_fullgraph → native replay → None
  → host submission / CONSUMER
  → update_full_graph_params → backend UPDATE submission
  → optional output evidence (None explicitly missing)
  → propose returns persistent draft_tokens slice
  → success: P3 host retirement + retirement record
  → next proposal/generation
```

旧测试曾把上游manager mock为返回`"replayed"`，同时mock掉output observer，因而不能覆盖真实接口。本轮保留框架`run_fullgraph`方法，只替换Host无法执行的native replay/stream/FIA等原语，另建立连续代回归。

## 3. 实际修复

1. manager `run_fullgraph`注解改为None，文档解释真实persistent输出契约；不改变其运行顺序或返回值。
2. observer新增显式`draft_output_status/reason`及Target对应字段。None→`OUTPUT_NOT_CAPTURED / GRAPH_MANAGER_RETURNS_NONE`；空Tensor/空容器/非Tensor树→missing，不生成占位hash。Target未提供→`TARGET_OUTPUT_NOT_SUPPLIED`。
3. 合法非空Tensor树仍可hash；没有宽泛except。generation/carrier匹配失败、真实Tensor/NPU失败仍向上传播。observer OFF在触碰carrier/输出前返回。
4. 修正replay submission docstring：这是Host记录，不是device event。

关键逻辑（完整diff随包）：

```python
if value is None:
    return None, "OUTPUT_NOT_CAPTURED", "GRAPH_MANAGER_RETURNS_NONE"
if not nonempty_tensor_tree(value):
    return None, "OUTPUT_NOT_CAPTURED", "EMPTY_OR_UNSUPPORTED_OUTPUT"
return _hash_tensor_tree(value), "HASHED", None
```

没有为消灭null读取可能被复用的draft_tokens，没有在replay→UPDATE之间插入D2H，没有修改lease完成条件。输出hash不构成generation有效性或completion证明。

## 4. RED/GREEN与证据级别

旧代码直接测试None/空tuple/空list/空字符串/空tensor得到**5 failed**：None/字符串TypeError，其余错误地产生hash。日志`logs/red-output.log`保留完整异常。该反例针对production recorder，不依赖设备。

真实框架返回、多代retirement、独立checker、fixture、Target checkpoint和交付工具的准确命令/结果在文末自动汇总，原始日志全部随包；失败与未运行项不会被总计隐藏。受控native替代的Host测试只证明Python数据/控制合同，不证明捕获设备地址或stream行为。

## 5. IMPLEMENTATION_GAP_MATRIX

|项|源码事实/Host证据|Repair3设备证据|本轮动作/验收限制|
|---|---|---|---|
|公共/实验入口|public graph仍拒绝，实验flag独立于observer|A1负例、O0/O1成功|不改变任何产品Gate|
|persistent backing|P6按capture identity持有稳定表/长度|capture Python边界地址|继续地址/代际/别名Host回归；task内部地址OPEN|
|capture/update绑定|Ascend helper→backend FIA；UPDATE验证真实backend|15capture+5update仅gen0|完整层/bucket/multi-generation checker|
|read/write分离|private read oracle与canonical identity分离|前次alias点通过|继续real-owner、非法private alias反例|
|slot/positions/query/Target|canonical Full引用不clone|OFF记录充足，ON有限|新增严格对齐工具；自然序号不作为状态等价|
|generation/epoch|P3 identity与P6 runtime identity|仅generation0|多代框架测试；device generation结果需C2|
|padding/bucket|descriptor实际计数不同于请求数|capture3个/runtime1个|B0要求实际3桶replay、每层update、正常输出|
|生命周期/reuse|UPDATE状态是Host attribution，不是completion|无真实完成|不擅改重用协议；私有fixture诊断独立完成机制|
|abort|proposal异常走abort，正常才retire|B0异常路径|回归与受控abort入口，设备部分NOT_RUN|
|observer OFF|禁用取证副作用，实验Graph仍可走|O0/O1完成|保持独立开关，无event.query回归|
|数值输出|manager None不是tokens|B0确定缺陷|修missing合同；checker保持numeric OPEN|
|FULL_TARGET/KV|旧probe只有compute_logits HEAD_ONLY|47 OFF仅head|新增显式checkpoint/比较入口；状态是否可配对由实际完整输入/KV决定|
|physical/task事实|普通CSV不含关键字段|T0采集是真的，但字段不足|trace字段审计，不能复跑同命令期望魔法出现字段|

## 6. 原GAP与本轮处理

|GAP|分类|本地处理|服务器剩余|
|---|---|---|---|
|001 observer错误|PROVEN_CODE_DEFECT|Repair2结构/Repair3事件修复保留；本轮None合同修复|新SHA B0|
|002固定inventory多桶|DRIVER_GAP/DEVICE_NOT_RUN|冻结requests、真实bucket checker、1/2/4/1框架测试|真实replay覆盖，3请求→4padding|
|003G1 operand|OBSERVABILITY_GAP|保留实际FIA边界关联|task内部地址仍工具未知|
|004G2 ABA|DRIVER_GAP|受控私有fixture/独立oracle|与production完整MRV2集成范围分开|
|005G3 physical|TOOL_CAPABILITY_UNVERIFIED|CPU oracle、数值扰动、字段审计|physical read必须独立证据，不降级|
|006G4写侧|DRIVER_GAP|OFF/ON probe+严格FULL_TARGET工具|完整输入/KV配对，不以相同seed代替|
|007G5时序|DEVICE_NOT_RUN|源码时序审计，私有fixture completion/abort|实际effective generation和多stream覆盖|
|008trace能力|TOOL_CAPABILITY_UNVERIFIED|版本/API/schema/CSV字段probe|没有字段时ACCEPTANCE_DECISION_REQUIRED|
|009observer OFF|已实现局部，DEVICE_NOT_RUN新SHA|开关独立、无副作用回归|新SHA同fixture OFF/ON|
|010checker|DRIVER_GAP|非空、identity/关联、numeric缺失、层级判定反例|接收端复核，不能以完整性PASS替代功能|

## 7. G5源码及版本边界

Ascend `dflash/aclgraph.py`保持：update_stream.wait_stream(current)→replay提交→Host CONSUMER→`update_full_graph_params`。`attention_v1.full_graph_fia`捕获ExternalEvent.wait/reset+task group；`update_graph_params`在update_stream做begin→FIA.out→end→ExternalEvent.record。不查询ExternalEvent。

P6 `validate_backend_update`在实际backend调用前标记UPDATED。这是Host授权/归因状态，不证明device完成。P3成功retire也不是device完成。保留`update_effective_generation=None`及NEEDS_NPU_TIMELINE，不推断N或N+1。

服务器版本CANN9.1.0/torch_npu2.10.0.post4，Mac没有对应NPU运行时。公开接口说明只能支持调用职责，不能单凭Python位置证明该版本task更新代际。受控fixture需收集安装源码/扩展hash/API schema，并用区分度充足的A/B/A′实际结果判别，不能把分支源码当post4精确native版本。

诊断case中的普通device Event必须位于相关consumer之后，分别覆盖replay stream与update stream。任何诊断同步都标记NOT_PERFORMANCE_REPRESENTATIVE；它不证明无同步production无race。in-flight失败不能假装完成或复用。

## 8. Trace裁决与待验收决定

本轮真实T0字段有时间、Stream/Task标识、算子/FIA类型和shape等；缺少实际block-table元素/设备operand地址、P3 generation/mapping关联和可靠completion-owner。包内独立字段清单可重算。

服务器只做有界新能力probe：记录工具版本/`--help`→确认选项→执行采集→导出字段清单→对Gate逐字段映射。安装成功、选项存在、命令exit0都不等于证据充分。不承诺Memory/MemoryAccess提供physical block read-set。若无新字段，不重复相同T0命令并声称证据升级。

`ACCEPTANCE_DECISION_REQUIRED`：若task内部operand/physical memory transaction无法通过当前版本受支持工具获得，owner需决定是否接受严格限定的替代证据组合。数值扰动只能说明结果不依赖某些数据，不能说明硬件未读取它。本轮不替owner降级验收。

## 9. 发布前后与执行依赖

当前本地代码/工具就绪状态和服务器可获取状态分离：`publication_status=NOT_PUBLISHED`；输入包`PRE_PUBLICATION`。用户复核后另行授权发布及GitHub独立clone验收；完成前不得启动正式campaign。禁止服务器应用包中未提交补丁替代exact checkout。

固定Base：DSpark K=query7、sample_from_anchor=true、W1024、block128、capacity1151、max_model_len4096、max_num_batched_tokens4096、maxseq4、seed0、max_tokens16；FULL_DECODE_ONLY实际FULL；capture[7,14,28]；single STANDARD dense FIA；TP/DP/PP/PCP/DCP1；async/prefix/SP/DSACP/FlashComm关闭。capacity不是max_model_len。

顺序：P0 exact source/import/模型hash/运行环境→A0→A1→B0完整结束→B1/B2/G4-ON/T1；O0/O1/G4-OFF可在设备健康且独立时运行。C2私有fixture不需要真实请求allocator，但也不能替代MRV2集成。G4F实际输入/KV不匹配则OPEN；不能按第N条强配。G5/ABORT独立诊断与正常运行分账。最后R0完整打包接收端校验。

单case1800s，独立fixture有单独timeout，输出量8GiB打包硬限制，设备被其他进程占用/不可恢复native错误立即STOP。保存stderr、partial、launcher rc/signal、first divergence和实际命令。依赖阻断不会自动阻断健康设备上的独立安全fixture。新SHA未运行项都NOT_RUN。

## 10. 保持的边界

无upstream改动；无public Gate解冻；无Batch A；不修改Target/canonical owner；无slots/positions/query clone；无全局synchronize进入production；无UPDATE前移、allocator/scheduler重写、推测性双缓冲；无push/PR。本轮非性能优化。旧SHA设备成功不能继承给新SHA。

## 11. 最终实现范围与真实就绪程度

- `tools/p7x_graph_repair4_fixture.py`：独立child/private FullSource/P3/P6 +真实 `full_graph_fia`/`update_full_graph_params`；Q7/W1024/block128/cap1151；固定A/B/A′+短/非对齐/窗口外扰动，独立枚举oracle。使用FP16、q/k=0可区分KV均值；普通completion events在最后consumer/update后。Host实际构造P3/P6并走binding；NPU缺失明确NOT_RUN，不CPU fallback。它不执行完整模型capture helper、真实请求allocator或KV写，故不能代替B0/G4。
- `tools/p7x_graph_repair4_target.py` + Repair2 opt-in flag：真正包裹本instance Target `prepare_inputs` / `ModelAclGraphManager.run_fullgraph`，不是仅compute_logits。完整保存声明读写block集合的K/V（含版本态内容）、输入/metadata/输出/写槽，并检查未写槽不变；使用捕获FIA参数确认层KV集合。预/后诊断同步不放在replay→UPDATE中间。真正NPU错误传播。
- **G4F仍PARTIAL**：这是真实forward观察/比较器，不是保证OFF/ON同态的控制器；没有安全公开API可原子重建整个runner/KV/调度/采样状态，本轮没有直接篡改active allocator。自然流量不保证完整pre-KV相同；目前只接受相同physical block ID映射，不含跨allocator逻辑重映射。max records/bytes导致遗漏则OPEN；不能写FULL_TARGET_READY。
- `tools/p7x_graph_repair4_acceptance.py`：真实B0要求3桶runtime、每层UPDATE、多代retire和正常输出；null hash不影响合法None接口但numeric保持OPEN；旧历史B0重验得到 integrity/host PASS、B0 FAIL、numeric OPEN。另有供证JSON checker与trace实际字段检查，均不把人工JSON当设备producer。
- `tools/p7x_graph_repair4_campaign.py`：exact/import/tool preflight、冻结请求扩展argv、bounded launcher调用说明、ZIP pack/verify。全部参数经过真实argparse测试；不自动执行计划、不自动发布。

### 实际多代验证

真实upstream `CudaGraphManager.run_fullgraph`、Ascend metadata builder/capture adapter、P3 materialize/P6 binding、manager UPDATE入口与production proposal scope cleanup均实际执行。Native Graph replay、NPU stream/forward context以及backend原生UPDATE边界在Host替代。序列：1→2→4→1→3active/4padded，对应token7/14/28；5个generation各自record/retire、padding清零、同bucket地址稳定、Target不变、retired inputs不能再validate。不是native NPU行为证明。完整multi-layer共享/幂等/冲突/回滚与real-owner alias沿用并重跑Repair2/3测试。

### 准确测试命令与结果

环境：Mac本地repo `.venv`，Python3.12，VLLM_VERSION0.29.0，PYTHONPATH指向只读pin。NPU没有运行。主要命令：
```bash
VLLM_VERSION=0.29.0 PYTHONPATH=../vllm .venv/bin/pytest -q tests/ut/spec_decode/test_graph_repair4*.py tests/ut/spec_decode/test_graph_repair2_campaign.py tests/ut/spec_decode/test_draft_window_graph*.py tests/ut/spec_decode/test_draft_window_capture_observer.py tests/ut/spec_decode/test_draft_window.py tests/ut/spec_decode/test_draft_window_runtime.py tests/ut/spec_decode/test_draft_window_eager.py tests/ut/spec_decode/test_draft_window_eagle3.py tests/ut/spec_decode/test_dspark_speculator.py tests/ut/spec_decode/test_dspark_graph_contract.py tests/ut/worker/test_attn_utils_v2.py tests/ut/attention/test_attention_v1.py tests/ut/worker/v2/test_v2_block_table.py
```
结果 **798 passed, 1 warning, 2 subtests passed / exit0**。Warning为缺少upstream生成的`vllm._version`，不是跳过失败。没有新增skip。`python -O`下Repair2+Repair4 checker161 passed（pytest自身提示优化模式，production检查使用显式raise）。7源文件定向mypy、13文件Ruff/format、compileall、git diff --check通过。

完整pre-commit **ENVIRONMENT_BLOCKED/exit3**：下载ruff hook时DNS不能解析github.com；独立gitleaks **ENVIRONMENT_BLOCKED/exit127**：本机binary/wget不存在。没有把这两项计为PASS。没有为了凑数跑无关整个仓库，也没有把旧环境失败自动认定为本轮baseline失败。

RED: `pytest ...test_draft_window_graph_characterization.py -k optional_output`旧代码5fail。真实框架RED用`reproduction/run_red_integration.py`加载`git show 10cbf4c`的observer字节，在隔离subprocess执行同一新test；旧源文件未覆盖共享repo。关键输出为 `_hash_tensor_tree(None)` → TypeError。GREEN为production None status/null，全部集成13tests通过。早期构建测试中的seq_lens `is`断言失败后按源码slice合同改为storage ptr+value校验，不是更改production读取语义；历史探索日志保留。

## 12. 逐文件修改/审查索引

```
.../test_draft_window_graph_characterization.py    |   32 +
 .../spec_decode/test_graph_repair4_acceptance.py   |  566 +++++++++
 .../ut/spec_decode/test_graph_repair4_campaign.py  |   86 ++
 tests/ut/spec_decode/test_graph_repair4_fixture.py |  463 ++++++++
 .../spec_decode/test_graph_repair4_integration.py  |  336 ++++++
 tests/ut/spec_decode/test_graph_repair4_target.py  |  553 +++++++++
 tools/p7x_graph_repair2.py                         |   49 +-
 tools/p7x_graph_repair4_acceptance.py              |  685 +++++++++++
 tools/p7x_graph_repair4_campaign.py                |  306 +++++
 tools/p7x_graph_repair4_fixture.py                 | 1233 ++++++++++++++++++++
 tools/p7x_graph_repair4_target.py                  |  739 ++++++++++++
 .../worker/v2/spec_decode/dflash/aclgraph.py       |    4 +-
 .../draft_window_graph_characterization.py         |   46 +-
 13 files changed, 5088 insertions(+), 10 deletions(-)
```

核心运行路径变化只有合法返回注解与可选observer合同；新增大部分行是默认不进入生产的实验工具/独立检查器/测试。没有复制upstream manager，也未变更生产allocator/scheduler/Graph顺序。关键完整diff在`Full_Diff.patch`。新增工具不是public Graph开关。

## 13. 最终Git身份与交付

- branch `fix/p7x-graph-base-a3-repair4`
- commit `aaa4632612503adb34d90b55c36eedcaf0848979`
- tree `d39adc3de6b98523680b918997469914ca3992e4`
- parent `10cbf4c014fc6cc48a6fea611bb605cecdd54cfd`
- Signed-off-by: Lucian；未amend/rebase/squash；未push/PR。
- Ascend工作区clean；upstream HEAD `84030bbe3d74d99bad477a3d2e37a973ccd8865c` / tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`，clean/zero diff。

服务器命令全文、case matrix、schema与验收问题随两个ZIP。原始输入hash/复核结果随local包；不重复打包47个大型OFF tensor。`Server_Input_Pack`没有未提交source/patch/bundle，执行代码必须取最终Git。REPAIR4_PACKAGE_INDEX、ARTIFACT_INDEX、SHA256SUMS及顶层Download Manifest建立可校验字节链，不含自我循环hash。

## 14. 最终裁决

```text
REPAIR4_LOCAL_IMPLEMENTATION: PARTIAL (return fix + integration + scoped tools implemented)
REAL_GRAPH_RETURN_CONTRACT: HOST_VERIFIED
MULTI_GENERATION_INTEGRATION: HOST_VERIFIED
CONTROLLED_ABA_ENTRY: IMPLEMENTED / NPU_NOT_RUN / PRIVATE_SCOPE
CONTROLLED_FULL_TARGET_ENTRY: PARTIAL / ALIGNMENT_REQUIRED
G5_TIMELINE_AND_ABORT_ENTRY: IMPLEMENTED_DIAGNOSTIC_ONLY / NPU_NOT_RUN
TRACE_CAPABILITY: PARTIAL / TASK_AND_PHYSICAL_OPEN
HOST_VALIDATION: PASS (798 tests; full hooks environment blocked)
PUBLICATION: NOT_PUBLISHED
NEW_SHA_DEVICE_VERIFICATION: NOT_RUN
READY_FOR_PUBLICATION_REVIEW: YES
READY_FOR_A3_AFTER_PUBLICATION: YES_SCOPED (not all-Gates readiness)
READY_FOR_ALL_G1_G5_CLOSURE: NO
PUBLIC_GRAPH_GATE: STILL_FROZEN
```

下一步只允许用户review后另行发布；独立GitHub拉取验收成功后按矩阵集中A3。Base核心错误停止依赖case；独立私有fixture仅在设备健康条件下继续。G4F同态控制、task内部operand/physical read、无同步完整MRV2生命周期仍有明确缺口，须设备/能力/owner判定，不得借本轮Host成功解冻Graph。

## 附录：服务器可执行说明

# Repair4 server commands — PRE_PUBLICATION

Exact commit `aaa4632612503adb34d90b55c36eedcaf0848979` / tree `d39adc3de6b98523680b918997469914ca3992e4`. These instructions do NOT authorize execution before publication and independent network clone verification. No local patch/source copy may replace Git. All inference code comes from this commit.

## Environment and P0

Use the exact existing A3 runtime/native environment validated by Repair3 (CANN9.1.0, torch_npu2.10.0.post4). Install the new Git Python source normally or reconstruct the audited native-donor overlay with the NEW identity. Never execute the old hard-coded Repair3 overlay script unchanged. P0 compares imported Python bytes against Git even when an overlay is used. Keep old native provenance and new source provenance separate. MRV2 V2 runner/process settings are set by the frozen driver.

Set these task-specific absolute paths from the verified checkout/unpacked input package; do not copy example placeholders as real paths:
`REPAIR4_REPO`, `REPAIR4_VLLM`, `REPAIR4_INPUTS`, `REPAIR4_RESULTS`, `REPAIR4_RUN_ID`.
Choose the same already-verified A3 device after checking contention/memory. Do not guess a new model or capture size.

```bash
cd "$REPAIR4_REPO"
python tools/p7x_graph_repair4_campaign.py preflight \
 --handoff "$REPAIR4_INPUTS/P7X_Graph_Base_A3_Repair4_Server_Handoff.json" \
 --vllm-repo "$REPAIR4_VLLM" --require-npu --output "$REPAIR4_RESULTS/P0.json"
python tools/p7x_graph_repair4_campaign.py plan \
 --handoff "$REPAIR4_INPUTS/P7X_Graph_Base_A3_Repair4_Server_Handoff.json" --inputs "$REPAIR4_INPUTS" \
 --output-dir "$REPAIR4_RESULTS/cases" --vllm-repo "$REPAIR4_VLLM" \
 --run-id "$REPAIR4_RUN_ID" --output "$REPAIR4_RESULTS/plan.json"
```

The planner retains PRE_PUBLICATION, execution_authorized=false: a new external publication proof must be attached; never edit source/handoff to fake that proof. Validate fixture weights via the driver before model loading. Keep all expanded argv arrays.

## Execute one reviewed plan case

After publication proof and case dependencies have been checked, execute each existing `launcher_argv` exactly. This example executes A0, not all cases:

```bash
python -c 'import json,subprocess,sys; p=json.load(open(sys.argv[1])); raise SystemExit(subprocess.run(p["cases"][sys.argv[2]]["launcher_argv"]).returncode)' "$REPAIR4_RESULTS/plan.json" A0
```

Then A1(expected GRAPH_FROZEN), B0, B1, B2. Never reduce [7,14,28]. Original request files are exact copies. Actual replay buckets, not number of submitted requests, determine coverage. A3 device/native failure stops dependent runs; independent private fixture only with healthy device.

```bash
python tools/p7x_graph_repair4_acceptance.py check "$REPAIR4_RESULTS/cases/B0/campaign.json" \
 --run-id "$REPAIR4_RUN_ID" --case-id B0 --attempt-id 1 --output "$REPAIR4_RESULTS/B0-check.json"
python tools/p7x_graph_repair2.py analyze "$REPAIR4_RESULTS/cases/B1/campaign.json" --output "$REPAIR4_RESULTS/B1-analysis.json"
```

`check` is deliberately B0-specific. Its exit0 proves only the stated B0 functional requirements; numeric/physical/completion can still be OPEN. `analyze` is data discovery, not final Gate closure. B1 must show canonical S>0 and independent values; B2 real padding/length variation. Missing evidence stays OPEN.

## C2 / G5 / ABORT

```bash
python tools/p7x_graph_repair4_fixture.py run --dry-run
python tools/p7x_graph_repair4_fixture.py run --run-id "$REPAIR4_RUN_ID" --attempt C2 --output "$REPAIR4_RESULTS/C2" --timeout 180
python tools/p7x_graph_repair4_fixture.py check "$REPAIR4_RESULTS/C2/result.json" --manifest "$REPAIR4_RESULTS/C2/manifest.json"
```

Fresh disposable child and fixture-owned canonical/KV buffers; actual P3/P6/FIA/update path but not full model capture/allocator/write. Q7/W1024/B128/cap1151. FP16 numerical atol0.008/rtol0 fixed before run; zero query/key yields independently enumerable uniform attention. A/B/Aprime differ then restore logical contents at new generation. Short/nonaligned controls included. Ordinary events after last consumer/update explicitly diagnostic. No ExternalEvent.query.

Run the same command into NEW directories with `--abort-at before_replay`, `after_replay`, `after_update`, `after_completion`. Abort commands intentionally return non-PASS; assess recorded lifecycle/unsafe reuse, not exit0. Never treat child process death as completion. No sleep oracle. Keep partial/result/manifest/stdout/stderr/API hashes/launcher exit.

## G4 / G4F

Plan has G4-OFF/ON-short,long1,long2,mixed and G4F-OFF/ON variants. G4 is HEAD_ONLY plus write/metadata; G4F uses actual target manager forward and full mapped read/write KV blocks. Both arms use THIS SHA.
G4F is **PARTIAL**: bounded observations, not a deterministic OFF/ON state-construction fixture. It must reject unaligned inputs/pre-KV, omitted samples, changed selected read/write sets, and mismatched physical block mappings. No logical remap implemented. Cannot claim FULL_TARGET_READY solely from entry existence.

```bash
python tools/p7x_graph_repair4_target.py \
 "$REPAIR4_RESULTS/cases/G4F-OFF-short/target-full-forward.pt" \
 "$REPAIR4_RESULTS/cases/G4F-ON-short/target-full-forward.pt" \
 --atol 0 --rtol 0 --tolerance-reason 'initial exact deterministic diagnostic; relax only by predeclared dtype study' \
 --output "$REPAIR4_RESULTS/G4F-short-comparison.json"
```

Full forward is genuinely invoked; Graph replay may not execute Python model.forward. The probe wraps target run_fullgraph AFTER capture, waits its returned UPDATE submission, and snapshots complete selected KV. Its extra synchronization makes it NOT PERFORMANCE REPRESENTATIVE and cannot prove unsynchronized safety. Selected-block read coverage is computed from full Target lengths/table + physical write slots, not a few sampled entries. Unselected allocations remain unobserved. No output equivalence claim for Draft OFF vs ON.

## Trace T0/T1

Use plan T0/T1 driver argv as the profiler application. First `python tools/p7x_graph_repair2.py trace-probe --output ...` records available tools/options. Confirm installed help/version; do not invent command options. Preserve Repair3 successful profiler command in historical ledger but do not assume repeating it reveals missing fields. Inspect each actual export separately:

```bash
python tools/p7x_graph_repair4_acceptance.py trace-fields "$REPAIR4_RESULTS/traces/T0" --run-id "$REPAIR4_RUN_ID" --case-id T0 --attempt-id 1 --output "$REPAIR4_RESULTS/T0-fields.json"
python tools/p7x_graph_repair4_acceptance.py trace-fields "$REPAIR4_RESULTS/traces/T1" --run-id "$REPAIR4_RUN_ID" --case-id T1 --attempt-id 1 --output "$REPAIR4_RESULTS/T1-fields.json"
```

New capability probe is version/API source/native hash/FIA schema in C2 plus actual header/row analysis. No confirmed new tool providing task operand/physical read has been found. If absent, submit ACCEPTANCE_DECISION_REQUIRED, not a fabricated trace. Clocks from different domains require explicit correlation; sorting timestamps is not happens-before.

## R0

```bash
python tools/p7x_graph_repair4_campaign.py pack --root "$REPAIR4_RESULTS" --output "$REPAIR4_RESULTS.zip"
python tools/p7x_graph_repair4_campaign.py verify "$REPAIR4_RESULTS.zip"
```

pack rejects symlinks, existing output, output inside input, empty input and >8GiB total. Keep raw stderr/partial/exit/signal/commands and every failed case. Receiver repeats verify. This is evidence integrity only, not device correctness. Device model files/secrets must not be placed in artifacts.

