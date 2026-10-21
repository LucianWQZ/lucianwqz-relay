# Repair7 实现与集中验收准备

时间：2026-10-22T01:11:38.528677+08:00。候选：`fix/p7x-graph-base-a3-repair7` / `7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14` / tree `6dd40a67a500480556068be8b6ebcd977e3cc3e8` / parent `fd0716c59562f64262672de12e4ae26259908d0b`。
PUBLICATION=NOT_PUBLISHED；NEW_SHA_DEVICE_VERIFICATION=NOT_RUN；PUBLIC_GRAPH_GATE=STILL_FROZEN。

## 结论与范围

完成真实Ascend配置缺陷、false字符串、同CLI配置预检、三代数值前哨、Target最终执行聚合、管理员辅助设备准入、首因保留和比较依赖。不是Graph Base设备PASS。可提交独立审查；发布前、完整EngineArgs预检前和授权设备映射前不能启动campaign。
没有改Window数学、Full/absolute写侧、canonical Target隔离、Graph manager None返回、replay→UPDATE顺序、allocator、scheduler；没有ExternalEvent.query回归或全局同步。两个production文件变更均为显式诊断配置入口。

## 输入完整性与旧证据独立复算

# Repair6证据纠偏（只读复算）

review735828bytes/hash3df148…，raw167619564bytes/hash0d1c0e…；本地校验3499 raw成员（3497被索引，另两个索引文件）、260review成员。原始输入未修改。Receiver_Verification.json为本地执行，不引用服务器自检替代。
Base 10完整pair逐tensor通过；第11个(4,32)缺失，不删除该记录；Target4 12完整pair全部通过，hidden/logits max_abs=max_rel=0、finite，KV前/后态与完整声明写集合检查无错误。容差未放宽。
真实registry41 = Target模型36 + Draft5，不称41Target层。
两臂source/plan/run/attempt/argv/PID/launcher/产物hash重新关联，旧paired的REQUIRES_EXTERNAL_EXECUTION_JOIN由新独立聚合结果补足；原文件不改写。
这些结论均绑定fd0716c59562f64262672de12e4ae26259908d0b、old_die8/Phy8，不能转成授权host0–7或Repair7设备验收。
NUMERIC_TARGET4首因严格配置拒绝，尚未加载模型/取得连续样本；下游缺文件INVALID另列。B2是资源纠正中断(rc143)，不是数值失败。Repair6没有新native trace；42项ledger包含未运行/环境阻塞/只读比较，见Repair6_Ledger_Reanalysis.json，绝非42Gate全PASS。
设备报告的“只能重建容器”不由当前证据充分推出；本轮交付owner辅助PID/节点准入，不自动改容器。

本地实际读取raw分块tensor，按pair逐块/mmap对比，不依赖最终PASS字符串。完整逐样本结果随review包附Repair6_Per_Sample_Reanalysis.json、Raw_Sample_Index.json、两份Offline_Join，包含不完整Base记录与输入哈希；大raw留原始/派生目录不重复打包。
必要执行身份、原始错误与42case账本同时随包；原始官方FAIL/INVALID均保留。本轮不是重跑设备。

## Finding裁决

|ID|裁决|实际状态|
|---|---|---|
|R7-01|ACCEPTED|FIXED_HOST_VERIFIED|
|R7-02|ACCEPTED|SCHEMA_HOST_VERIFIED_FRAMEWORK_NOT_RUN|
|R7-03|PARTIALLY_ACCEPTED|SERIAL_DIAGNOSTIC_CHAIN_HOST_VERIFIED_DEVICE_NOT_RUN|
|R7-04|ACCEPTED|OLD_RAW_JOIN_RECOMPUTED|
|R7-05|PARTIALLY_ACCEPTED|OWNER_ASSISTED_ADMISSION_HOST_VERIFIED|
|R7-06|ACCEPTED|FIRST_CAUSE_AND_SCOPED_SELECTION_HOST_VERIFIED|
|R7-07|PARTIALLY_ACCEPTED|SOURCE_AUDITED_PLATFORM_SEMANTICS_OPEN|
|R7-08|ACCEPTED|ENTRY_REUSED_AND_CONFIG_VALIDATED_DEVICE_NOT_RUN|

R7-03部分接受的含义：旧配置阻塞已修；串行连续链生产者/consumer已有并通过Host真实结构，不能升级设备或正常重叠闭环。R7-05不伪造自动映射，实际需要管理员分配记录；R7-07不因缺观测猜测生产race或重构。

## 配置根因与真实调用链

CLI `repair6-numeric-reference`→build_llm_kwargs.additional_config→LLM/EngineArgs.create_engine_config→VllmConfig平台→init_ascend_config→AscendConfig(extra=forbid)→DSpark.capture输出sink。
旧schema不声明该键，工厂原样传入因此模型加载前失败；旧capture测试SimpleNamespace避开schema。现在字段bool=False，工厂仅允许DSpark/W1024显式诊断；consumer用同一TypeAdapter规则，False/"false"不启用；其他未知键仍拒绝。没有安装vllm_omni或改extra策略。
build_llm_kwargs与configure_run_environment从实际run中提取并共享给预检；未另造示例。39模型CLI配置、5种kwargs hash通过真实schema。完整EngineArgs/platform硬件派生在Mac缺_build_info/Ascend环境，ENVIRONMENT_NOT_RUN；服务器CONFIG不是argparse假通过。

## RED / GREEN 与真实边界

修改前真实schema+factory红测5failed/1passed，命令`VLLM_VERSION=0.29.0 PYTHONPATH=../vllm .venv/bin/python -m pytest -q tests/ut/spec_decode/test_graph_repair7.py`（当时仅初始6项）。
```text
FFFFF.                                                                   [100%]
=================================== FAILURES ===================================
_________________ test_numeric_configuration_schema[True-True] _________________

raw = True, expected = True

    @pytest.mark.parametrize("raw, expected", [(True, True), (False, False), ("false", False), ("true", True)])
    def test_numeric_configuration_schema(raw, expected):
>       config = AscendConfig(sparse_kv_offload_config=None, draft_window_graph_numeric_diagnostic=raw)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AscendConfig
E       draft_window_graph_numeric_diagnostic
E         Unexpected keyword argument [type=unexpected_keyword_argument, input_value=True, input_type=bool]
E           For further information visit https://errors.pydantic.dev/2.14/v/unexpected_keyword_argument

tests/ut/spec_decode/test_graph_repair7.py:13: ValidationError
----------------------------- Captured stdout call -----------------------------
INFO 10-22 00:50:37 [ascend_config.py:231] Dynamic EPLB is False
INFO 10-22 00:50:37 [ascend_config.py:232] The number of redundant experts is 0
------------------------------ Captured log call -------------------------------
INFO     vllm.logger:ascend_config.py:231 Dynamic EPLB is False
INFO     vllm.logger:ascend_config.py:232 The number of redundant experts is 0
________________ test_numeric_configuration_schema[False-False] ________________

raw = False, expected = False

    @pytest.mark.parametrize("raw, expected", [(True, True), (False, False
```
首因红测真实子进程配置异常+checker缺文件，旧汇总覆盖为INVALID：
```text
F                                                                        [100%]
=================================== FAILURES ===================================
__________ test_producer_first_failure_not_hidden_by_missing_artifact __________

tmp_path = PosixPath('/private/var/folders/jg/1291_6m930x__sj1qzy3kdsh0000gn/T/pytest-of-wenqingzhang/pytest-65/test_producer_first_failure_no0')

    def test_producer_first_failure_not_hidden_by_missing_artifact(tmp_path):
        import sys
        from tools.p7x_graph_repair6_runner import run_case
    
        plan = dict(publication_status="VERIFIED", cases={"NUMERIC": dict(
            argv=[sys.executable, "-c", "raise ValueError('configuration failure')"],
            timeout_seconds=5, validation_commands=[dict(
                argv=[sys.executable, "-c", "raise SystemExit(4)"], timeout=5, kind="read_only_acceptance")])})
        result = run_case(plan, "NUMERIC", tmp_path)
>       assert result["status"] == "EXECUTION_FAILED"
E       AssertionError: assert 'INVALID_EVIDENCE' == 'EXECUTION_FAILED'
E         
E         - EXECUTION_FAILED
E         + INVALID_EVIDENCE

tests/ut/spec_decode/test_graph_repair7.py:45: AssertionError
=============================== warnings summary ===============================
../vllm/vllm/__init__.py:7
  /Users/wenqingzhang/Desktop/vllm/vllm/vllm/__init__.py:7: RuntimeWarning: Failed to read commit hash:
  No module named 'vllm._version'
    from .version import __version__, __version_tuple__  # isort:skip

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/ut/spec_decode/test_graph_repair7.py::test_producer_first_failure_not_hidden_by_missing_artifact
1 failed, 7 deselected, 1 warning in 0.12s

```
GREEN：最终相关回归`735 passed, 1 warning in 50.19s`；优化模式51passed（pytest有优化模式警告，生产require非assert保留）；新Repair7 28项包含真实schema/工厂、完整计划、producer→store→joint、真实小tensor两臂与损坏反例。不是51/735台设备实验。
Host替代：conftest的native/build-info；工厂硬件派生/FinegrainedTP等替换但schema/factory不替换；capture集成保留真实DSpark/manager/builder/P3/P6，Graph replay/FIA/stream/event与模型计算替换为明确CPU surrogate。普通字符串false默认路径没有sink。多bucket、跨代、alias隔离和public gate由相关既有回归覆盖。
初次宽回归3项测试mock遗漏真实execute.status导致失败，已补该返回字段并保留原日志；未删除断言。另有早期plan数量预期40/实际39和tools路径shadow bisect问题，日志保留并修正。未为凑数重跑全spec_decode/VWN，历史7项VWN失败不记本轮PASS。

## 静态与环境限制

Ruff、format、targeted Mypy(7工具文件)、compileall、diff-check、5个可独立本地hook均通过。完整manual pre-commit退出3，npm EALLOWGIT依赖策略阻塞，ENVIRONMENT_BLOCKED，不关闭hook。仓库没有安装git pre-commit hook，独立signed-off commit不是绕过已有hook。
每项完整argv/exit/log以及最终逐文件SHA在tests-results/static-results中；最终提交文件哈希逐一核对。测试对应最终源码，不伪装NPU或完整EngineArgs已跑。

## 逐文件变化

|文件|性质|
|---|---|
|`tests/ut/spec_decode/test_graph_repair6_capture_chain.py`|回归测试|
|`tests/ut/spec_decode/test_graph_repair6_delivery.py`|回归测试|
|`tests/ut/spec_decode/test_graph_repair6_numeric_pipeline.py`|回归测试|
|`tests/ut/spec_decode/test_graph_repair7.py`|回归测试|
|`tools/p7x_graph_repair2.py`|实验工具/验收编排|
|`tools/p7x_graph_repair6.py`|实验工具/验收编排|
|`tools/p7x_graph_repair6_numeric.py`|实验工具/验收编排|
|`tools/p7x_graph_repair6_numeric_check.py`|实验工具/验收编排|
|`tools/p7x_graph_repair6_runner.py`|实验工具/验收编排|
|`tools/p7x_graph_repair7.py`|实验工具/验收编排|
|`tools/p7x_graph_repair7_campaign.py`|实验工具/验收编排|
|`tools/p7x_graph_repair7_device.py`|实验工具/验收编排|
|`vllm_ascend/ascend_config.py`|production入口合同|
|`vllm_ascend/worker/v2/spec_decode/dspark/speculator.py`|production入口合同|

完整diff随包；关键生产diff：新增默认false字段；工厂显式DSpark/W1024约束；capture使用validate_additional_config_bool。无其他production变更。

## 数值、Target与编排

# 连续数值合同

真实配置入口→DSpark.capture→真实builder→NONE capture closure输出引用→P3/P6 bind→Graph replay(None)→consumer→UPDATE→诊断完成→本代hidden与同Window eager reference→分块writer→联合checker→retire→下一代。
Host集成保留这些Python组件及状态转换；Graph/FIA/event/stream、模型算术使用显式CPU native替身。未执行A3。

独立性：checker从canonical Full/exact/valid重算S/E/V与列范围，reference重新构建Window读取；不直接采被测Window当答案。双方共享模型权重、模型forward实现、canonical输入及部分backend实现，因此共同模型/backend错误不由相等证明排除。现有负例覆盖start/length、generation、backing内容、缺层/NaN/缺chunk/前态损坏，不能用schema镜像代替NPU。
Target active/padded 与Draft dispatch分开；Target1-active/2-padded仍可Draft(1,7)。只比较有效hidden，padding检查finite/shape/read0/slot-1。
预声明容差：连续hidden及受控Target atol=rtol=0；私有FIA0.016另列不变。B不可区分则OPEN，不能改容差或只用argmax。

NUMERIC_SENTINEL=前三个A/B/A_prime，生产者sample_limit与plan.numeric_samples=3、argv、summary同时核对；状态PASS_NUMERIC_SENTINEL_ONLY不是12场景PASS。
NUMERIC_TARGET4=完整12场景，只有前哨通过才允许；Base仍无Target(4,32)。诊断数值FAIL落盘后停止后代；native提交不确定74只Host错误导出、隔离退出，不继续恢复设备/复用；不消费已SUBMITTED carrier。
默认关闭无sink/输出保留/事件查询/D2H；不将合法None制造为hash。

# 首因、依赖、资源与恢复

runner单case执行，所有旧attempt只读保留；同目录不可覆写。新run用新root重新PREPARE。当前已实现精确run/SHA/tree依赖、case选择与原始命令/退出码保留；未实现自动跨attempt继承成功。
配置/模型启动失败→EXECUTION_FAILED，checker缺文件→acceptance_status INVALID_EVIDENCE另列，primary_failure始终首个非预期失败。
数值3→NUMERIC_MISMATCH，未知native74→SUBMISSION_UNCERTAIN_QUARANTINED，预算5→BLOCKED_RESOURCE，producer超时→EXECUTION_TIMEOUT，比较超时→COMPARISON_TIMEOUT，用户中断→USER_INTERRUPTED。ABORT73必须联合专用checker成功，不能通用忽略非零。
合法complete prefix可由只读比较恢复；生产者非零仍保留。COMPARE必须等两臂attempt都结束，不要求两臂都PASS，且拒绝跨run/source旧runner-result。
不通过复制旧runner-result恢复：跨attempt复用需显式离线reanalysis记录，只参考旧结果；新SHA锚点重跑。
预算沿用Repair6各分支resource_policy/runtime几何预检；完整Target累计chunk/两臂/临时落盘与打包空间单独核算。无全局Target硬门；不足不缩矩阵、不删失败证据。profiling不依赖NUMERIC或完整Target。
当前RAM/HBM自动估计只到既有几何预检能力，不是实时服务器资源保证；owner资源receipt和每分支preload-resource-plan是必需证据。

Target join实际重新调用单臂audit_execution和两臂tensor compare，校验arm/profile/run/attempt/source；原始artifact修改后旧campaign hash失效，不能沿用。10pair与12pair仅受控Target，未证明Draft正常completion或physical read。

## 设备准入、剩余production工作

# 授权设备准入：管理员辅助，不自动猜映射

授权host Phy-ID 0–7中分配给本任务的**一个**芯片；TP1。不等同容器0/runtime0/进程npu:0。
1. 在导入torch/NPU前由管理员设置本进程及后续子进程的实际可见性；执行committed device.py inspect（只读npu-smi -m、/dev节点major/minor、namespace、boot ID、环境/PID）。
2. owner根据宿主/容器实际映射与资源占用提供receipt。不能把其他用户Phy8 PID当自己的证据。未知则BLOCKED，不启动模型，不重建/提权容器。
3. receipt未有probe时只允许在映射已明确后运行device.py probe：1024元素，仅本PID；管理员关联其host/container PID、命令、开始/结束、节点与设备记录，填入原始证据path/hash。无映射证明禁止先probe。
4. check要求有效<=1小时、boot/namespace/visibility/节点相同、host0–7、probe0退出与自身PID证据。每个case启动前重新检查资源并签发绑定run/source/tree/case的receipt。
5. BIND_DEVICE.py保存新的admitted-plan，不改原计划参数；runner在任何child启动前核验receipt/hash。

receipt v1字段：schema=repair7-device-receipt-v1,run_id,source_sha,source_tree,case_id,allocation_owner,issued_at,expires_at,host_phy_id,tp=1,allocated_nodes{路径:{major,minor}},namespace,boot_id,visibility,mapping_evidence/resource_evidence[{path,sha256}],probe{host_pid,container_pid,command,start_ns,end_ns,host_phy_id,status=EXITED,returncode=0,host_process_evidence:{path,sha256},pid_namespace_evidence:{path,sha256}}。
这是owner签发内容的完整性/一致性校验，不是密码学签名，也不自动理解任意npu-smi文本。管理员仍须复核映射语义；实际worker PID/继承环境及设备归属需随campaign保存。没有实现自动宿主PID发现/worker物理证明；不宣称工具单独能证实分配。
禁止reset、kill无关任务、改变设备挂载/权限、自动回退Phy8。若管理员协助仍不能证明映射，保持BLOCKED_DEVICE_MAPPING。

# 生命周期与 production 收尾（Repair7）

未改功能顺序，以下以本次最终源码与 pinned vLLM 为准。

|阶段|owner / stream / 证据|仍缺事实|
|---|---|---|
|物化与 backing copy|P3/P6 provider 持有 persistent table/length；current stream；draft_window_graph.bind_read_carrier|不是完成事件|
|metadata bind|canonical Full write/query 与 Window read 分开；typed carrier 同代|设备真实 task operand 仍未暴露|
|replay|dflash/aclgraph.run_fullgraph：update_stream.wait_stream(current) 在 replay 之前；super 返回 None|wait覆盖此前copy，不等于覆盖随后replay|
|UPDATE|attention_v1.update_graph_params：update_begin→FIA.out→update_end→ExternalEvent.record，update stream|当前CANN/torch_npu对N/N+1生效语义须维护者确认|
|consumer|captured Draft attention 等待/重置 ExternalEvent；sampling消费其输出|最后读者/异步task归属不能仅凭Host回调认定|
|retire|proposal_scope finally / P3 Host lease；不是设备 fence|Target输出copy event在Draft之前，不能充当Draft完成|
|next copy/reuse|同current stream FIFO是候选依赖，需证明外部task/UPDATE语义闭环|正常重叠复用UNPROVEN|

NUMERIC为每样本诊断drain；NORMAL_ORDER保留顺序，有额外有界token copy及末尾drain；LIFE每代串行。三者不能互相替代。
本轮没有证据证明必须前移UPDATE/双缓冲/全局同步，也没有宣称现状无race。

## 生产收尾映射

- 已有：private read backing、严格canonical write identity、实验provider、capture/update绑定、同代Host状态、public fail-closed。
- 本轮修复：严格Ascend配置合法诊断键和false解析；没有新增正常路径device操作。
- 仍需：当前版本task update生效代际、最后consumer覆盖、异常部分提交后正式quarantine/reuse语义；目前仅诊断子进程退出。
- 正式provider安装、公开配置路线承诺、fallback禁用/异常隔离、正常生命周期证明和A3回归仍未完成；不能将实验路径升级生产支持。
- TP16/Prefix/Eagle3/DSA/Async等Batch A仍排除。

## 平台与验收owner问题

固定服务器栈报告 CANN9.1 / torch_npu2.10.0.post4（下轮重新读取实际版本）。请维护者给出graph_task_update_begin/end、ExternalEvent wait/reset/record跨replay的版本契约，确认UPDATE(N)作用的任务及完成边界、update stream是否最后读backing。需要API源码/版本说明或可区分设备实验，不接受Python return代替。
physical read/task内部地址现接口不足：CAPABILITY_GAP / ACCEPTANCE_DECISION_REQUIRED。可提出连续数值+窗外非干扰+版本契约作为替代证据供owner决策，但本轮不降低Frozen标准、不解冻Gate。


## Profiling与下一轮

# Profiling合同（没有Repair6/7新trace）

本轮复用已提交torch_npu profiler入口，不运行任何采集。OFF/ON × short/long × control/normal；一个ON long detailed；LIFE成功后PROFILE_LIFE。完整配置来自同一build_llm_kwargs，normal observer-off且不装controlled Target/numeric/LIFE同步。禁止业务is_profile=True来开启profiler。
模型初始化/capture后warmup，16-token冻结请求组重复、有限active阶段；控制组不装native profiler。长窗以runtime source_start_column>0/实际S>0验收，不以prompt字符数推断。
tools/p7x_graph_repair5_profile.py::RequestProfiler.__enter__的实例wrapper包住真实_materialize_draft_window_read_inputs、build_draft_attn_metadatas、_update_full_graph_params、retire_generation；标签Draft_materialize/Draft_metadata_bind/Draft_UPDATE_CALL/Draft_retire_host。不是只包日志，不代表device completed；不在replay→UPDATE间新增D2H/同步/I/O。
真实plan中的--help/argv已解析；服务器capability preflight需确认实际profiler API。详细shapes/stack另profile，不与normal成本混算，不升级底层栈。
保存原trace、API版本/config、PID/stream/task/flow、解析日志与片段。tools/p7x_graph_repair6_trace.py为完整flow分析；工具可得字段/成功关联/歧义/无法关联分别统计。禁止按邻行/shape强连generation，禁止Host monotonic和设备时间直接相减。
Repair5旧trace可参考但不能标新SHA；Repair6无新trace，无本轮性能数字。正常开销诊断不等于正式性能收益，也不关闭physical-read证据。

# Repair7执行交接 — PRE_PUBLICATION

候选 7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14 / tree 6dd40a67a500480556068be8b6ebcd977e3cc3e8。当前禁止设备执行；先独立审查，再由另任务发布并网络恢复，重新签发VERIFIED handoff。本包不自行修改publication字段绕过。

## 发布后实际入口

先由服务器owner建立授权映射/环境，代码与输入包各自固定路径。以下变量必须替换为真实独立目录，不能使用本机preview路径：
```sh
REPO=/path/to/exact/vllm-ascend
VLLM_REPO=/path/to/pinned/vllm
PACK=/path/to/extracted/input-pack
RUN=/path/to/new/repair7-attempt
PY=/path/to/server/python
RUN_ID=unique-repair7-run
$PY "$REPO/tools/p7x_graph_repair7_device.py" inspect --output /path/to/inventory.json
# owner确认只读映射后，才允许probe；保存probe自身host/container PID证明
$PY "$REPO/tools/p7x_graph_repair7_device.py" probe --receipt /path/to/owner-mapping.json --run-id "$RUN_ID" --output /path/to/probe.json
$PY "$REPO/tools/p7x_graph_repair7_device.py" check --receipt /path/to/complete-receipt.json --run-id "$RUN_ID" --output /path/to/admission.json
$PY "$PACK/PREPARE.py" --repo "$REPO" --vllm "$VLLM_REPO" --output "$RUN" --run-id "$RUN_ID" --receipt /path/to/complete-receipt.json
# 每case新receipt，不能复用过期/其他case授权；以下以CONFIG为例
$PY "$PACK/BIND_DEVICE.py" --repo "$REPO" --plan "$RUN/case-plan.json" --case-id CONFIG --receipt /path/to/CONFIG-receipt.json --output "$RUN/admitted-CONFIG.json"
$PY "$REPO/tools/p7x_graph_repair6_runner.py" --plan "$RUN/admitted-CONFIG.json" --case-id CONFIG --output "$RUN/executions"
```
所有设备case同样先BIND；只读COMPARE不需device receipt，但需两个同run/source arm结束attempt。runner只执行指定case，不自动campaign。保留case-plan/各admitted-plan、receipt和全部原始命令。

## 顺序与依赖

P0 exact/import/fixture/capability（授权后）与CONFIG实际EngineArgs平台工厂预检均应先完成；A0/A1/B0锚点；NUMERIC_SENTINEL前三代；通过后NUMERIC_TARGET4全部12。Target分支PREFIX_OFF/ON资源存储前哨→G4F/TARGET4 OFF/ON→对应COMPARE→target-join最终外部裁决。Base缺Target(4,32)保留，不阻断Target4。
独立B2/O0/O1/C2和normal profiling按plan依赖，不受NUMERIC失败拖死。LIFE通过后ABORT/PROFILE_LIFE；NORMAL_ORDER独立保留正常顺序观测。
下一轮优先执行新配置/数值锚点和授权设备来源；旧Target12/12可离线引用，但新SHA和授权设备锚点仍需。无需重新尝试已知Base缺桶或重复无新增字段的physical-read trace。

## 实际最终聚合

```sh
$PY "$REPO/tools/p7x_graph_repair7.py" target-join --root "$RUN" --plan "$RUN/case-plan.json" --profile TARGET4 --device /path/to/device-segment.json --output "$RUN/target4-final-join.json"
$PY "$REPO/tools/p7x_graph_repair7.py" target-join --root "$RUN" --plan "$RUN/case-plan.json" --profile G4F --device /path/to/device-segment.json --output "$RUN/base-final-join.json"
```
原始launcher路径必须保留为RUN/launchers/CASE/launcher.json。比较重新读取chunk，不接受陈旧PASS；仍将authorized_device_acceptance=false，设备分配由单独准入/worker证据裁决，不自动盖章。
入口/参数/timeout/resource_policy以case-plan为准；44case与140CLI解析仅本地合同，不是设备完成数。

回传保存plan、receipts、launcher/campaign、target/numeric chunks、partial、原异常/exit/signal/timeout、joint、runner-result、native trace与解析。用最终Git中的tools/p7x_graph_repair5_pack.py pack/verify流式打包；大raw独立、review不含模型。禁止包内补丁覆盖checkout。


## 明确未完成/不夸大的部分

1. 新SHA未在A3启动；真实EngineArgs/完整模型安装组合仍需服务器CONFIG和数值前哨验证。
2. 自动宿主/容器worker物理映射未实现；owner证明+工具完整性检查是明确边界，必须随包原始PID/node证据。不能空填receipt或自报编号。
3. 正常重叠连续reference、UPDATE生效代际、normal backing复用、task内部operand/physical read仍UNPROVEN/CAPABILITY_GAP；串行诊断不替代。
4. 跨attempt自动恢复未实现；当前只支持新目录、显式case、同run/source依赖和独立旧证据重分析。禁止复制runner-result假恢复。
5. 完整hooks环境阻塞；本地readonly配置schema已验，但完整框架配置ENVIRONMENT_NOT_RUN。
6. Target最终数值聚合不自动批准设备授权；old_die8保留技术事实，授权验收须新设备锚点。

## Git与交付

base `fd0716c59562f64262672de12e4ae26259908d0b` → final `7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14`，tree `6dd40a67a500480556068be8b6ebcd977e3cc3e8`，parent `fd0716c59562f64262672de12e4ae26259908d0b`。Signed-off-by Lucian；密码学签名ABSENT。两仓clean，vLLM exact `84030bbe3d74d99bad477a3d2e37a973ccd8865c` / `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`。未push、未PR、未tag、未设备实验。
本报告、handoff、review请求和两ZIP见Download Manifest；包校验文件记录CRC/成员hash/JSON/最终身份/fixture/CLI检查。哈希证明传输一致，不证明模型正确。
