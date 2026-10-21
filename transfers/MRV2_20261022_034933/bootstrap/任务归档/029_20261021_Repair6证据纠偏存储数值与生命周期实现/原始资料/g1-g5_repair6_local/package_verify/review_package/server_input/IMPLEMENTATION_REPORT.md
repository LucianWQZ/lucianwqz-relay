# P7-X MRV2 Graph Base A3 Repair6 实现与就绪报告

时间：2026-10-21T11:02:47.019945+08:00。最终commit febc43be3309f6d2cd87f9332cb7e031ebaad001，tree f68e57e4501dacb67cdf4c81831b8f713e4ddc18。本轮只有本地开发、旧raw离线复算和Host验证。
PUBLICATION=NOT_PUBLISHED；NEW_SHA_DEVICE_VERIFICATION=NOT_RUN；PUBLIC_GRAPH_GATE=STILL_FROZEN。

## 执行摘要

实际完成：独立恢复Repair5完整raw并纠偏；四臂各7有效完整Target前缀复算；有界版本化chunk存储/legacy只读比较；partial与外部执行分账；真实MRV2同Window连续backbone参考；正常顺序多代观察；完整trace显式flow关联；新Host细范围及集中可分支计划。
不是只增加max_bytes或修一处API异常。

未完成：正常无附加同步的受控连续hidden UPDATE代际闭环、task内部operand、physical read-set、最后consumer与无扰动reuse证明。明确NOT_IMPLEMENTED/UNPROVEN/CAPABILITY_GAP，不能用Host测试掩盖。
LOCAL_REPAIR_HOST_VERIFIED；READY_FOR_PUBLICATION_REVIEW=YES_WITH_LIMITS；READY_FOR_A3_SCOPED=AFTER_PUBLICATION；READY_FOR_ALL_G1_G5_CLOSURE=NO。

## 原始证据与逐项裁决

# Repair5 原始证据纠偏（历史官方FAIL不覆盖）

Device SHA d0a3fc3d42d7d97e5e7da3890d2710263a097e63；RUN_ID 20261020T144145Z_d0a3fc3d。本轮是离线重判，不是新设备执行。

## 接收核验

review 2,619,378 bytes / 52b3bf122c0c63ca35d63eecc32e56503d2ea133a60443b6d3cf6b567794b1dc。
raw 545,358,867 bytes / 6b58da786bfe8ef095f20d771891086c85e79cf678087c42756864f876d5aea1。
六片顺序/每片hash、整包、CRC、路径、成员bytes/hash、JSON实际本地核验；review434成员=432索引数据+2索引，raw1001=999+2。不是引用服务器receiver自检。
原始return只读。辅助目录input单次抽取供CPU mmap；没有重复复制四份5GB tensor集合。

## 四臂完整前缀

|序号|场景|G4F OFF/ON|TARGET4 OFF/ON|本地裁决|
|---|---|---|---|---|
|1|A|CAPTURED_COMPLETE|CAPTURED_COMPLETE|完整Target对齐数值相等|
|2|B|同上|同上|同上|
|3|A_prime|同上|同上|同上|
|4|short|同上|同上|同上|
|5|long|同上|同上|同上|
|6|boundary|同上|同上|同上|
|7|nonaligned|同上|同上|同上|
|8|mixed|BLOCKED|BLOCKED|budget cannot hold post-forward KV and output|

每个.pt有8条，而非0。前7 checkpoint.status=CAPTURED。两profile各7对，全量复核hidden/logits、声明逻辑KV前/后态、slot/write合法性、outside digest、Draft后Target快照，atol=rtol=0相等。逐样本/逐逻辑block的dtype/shape/finite/max_abs/max_rel完整保留。整体PARTIAL_PREFIX_VALID/INCOMPLETE_COVERAGE，原child EXCEPTION不能改成PASS。

两组ON各7代、7bound、35update_operator、7proposal_retired；DIAGNOSTIC_COMPLETE，retired=true。
tokens A=[17,23,21,15,4,315,220]；
B=[23,21,16,15,4,315,458]；A_prime=A。
同一实验backing相同，generation/epoch递增；full_exact有1159/1287/1159/39/1159/1031/1160。
A/A_prime完整Target逻辑KV前态、位置、hidden相等。
Repair5没有单独dump完整Draft pre-KV；deterministic _stage是源码证据，不能冒充全部Draft前态raw证明。因此恢复的是“真实MRV2串行诊断token ABA有效前缀”，不是正常reuse、完整G2/G5。

## 其他纠正

- B1真实11组，O0/O1 provider存在且observer关闭，不是关闭Graph实验路径。
- control无native trace；实际4份normal、1份LIFE。不是8份native trace。
- long Target replay (1,8)=24、(2,16)=6；short各6。Draft short21、long47。
- registry41=真实Target模型36+Draft5，不是41 Target执行层。
- 约5.31GB是整个collection，不是单样本预算。
- 自然short21/21、long1 12/12是已取hidden相同的HEAD数值结论；long2 14/14中4对相同输入PASS、10对不满足前提；mixed18/14中2对相同、12对不满足、4未配对。
  旧记录缺业务identity，新严格关联保持OPEN。HEAD不能代替完整Target/KV前态。
- flow存在但未唯一归属，与平台没有字段不是一回事。


|ID|裁决|事实/处置|
|---|---|---|
|R6-01|REJECTED|四臂各8记录，前7 CAPTURED_COMPLETE；ON 7代A!=B且A=A_prime，第8mixed预算失败；mmap全样本复算；历史FAIL保留|
|R6-02|ACCEPTED|36层共享2048²boolmask重复计数，mixed预算可预估不足；storage-view去重；chunk存储；几何预算|
|R6-03|ACCEPTED|旧大集合无法有界快速重判；repo runner、3300秒比较、独立partial状态|
|R6-04|PARTIALLY_ACCEPTED|long2仅4对输入相同；mixed18vs14不能zip当对齐；唯一业务identity关联；HEAD_ONLY与FULL_TARGET分开|
|R6-05|ACCEPTED|manager合法None；greedy不能假设draft_logits有效；默认关闭DSpark输出引用sink+独立Window真实backbone参考|
|R6-06|PARTIALLY_ACCEPTED|Host retire非device completion；ExternalEvent C++语义未闭环；normal有界copy+末尾drain；串行连续代际判别；正常代际OPEN|
|R6-07|REJECTED|完整trace有s/f/id2及queue关联，sample500X丢上下文；全trace显式flow解析，不升级为taskoperand|
|R6-08|ACCEPTED|11组；4normal+1LIFE native；long24+6，short6+6；报告纠偏，保留原hash|
|R6-09|ACCEPTED|真实P6类型抛DraftWindowGraphRoute序列化错误；复用已有_json_safe并全链回归|
|R6-10|ACCEPTED|原launcher原样返回73；仅73+专用check-abort通过；74/timeout仍拒绝|

原始return：/Users/wenqingzhang/Desktop/中转/private-file-relay/transfers/2026-10-21/MRV2_P7X_A3_Repair5/20261020T144145Z_d0a3fc3d/return。
只读原件；Receiver_Verification含分片与顶层hash。逐样本与逐block报告保留所有失败/未配对，不只挑PASS。Raw_Reference_Index记录全部member身份，紧凑包不重复大raw。

## 实现、资源和合同

# Target 有界存储与预算

## 实测几何

Target36层，Draft5层；KV heads8、head_dim128、block128、BF16(2byte)；hidden4096、vocab151936。
A的72份K/V各9blocks [9,128,8,128]，单份完整KV集合169,869,312 bytes。
旧inputs151,006,448 bytes：共享2048²boolmask按36layer重复copy；before/after各169,869,312；output393,216。unique storage逐样本见Prefix_Reanalysis。不能把5.31GB当单checkpoint预算，不能盲增2/4GiB。

精确d0基线RED：同一16×16boolmask两layer，实际唯一256bytes，旧_snapshot报needs512、remaining256。新_snapshot按storage/view和选择块去重，两个字段和alias描述均保留，不clone canonical写侧隐藏alias。

## 格式与资源边界

repair6-tensor-store-v1：collection先IN_PROGRESS；sample先PREPARING，完成后原子payload+hash；tensor独立content-addressed bin，<=8MiB chunk，各段offset/bytes/hash、全hash、shape/dtype/逻辑归属。相同数据只存一份bin，原owner/alias描述不丢。
selected KV按稳定block/element顺序流式D2H，mmap读取。logical KV从完整checkpoint与block_owners重建，避免重复序列化。完成record不再整集合torch.save。
完整读写块、未授权写区域outside digest继续覆盖，不能以去重改为抽样。不同generation数据durable后不受后续buffer覆盖。
比较按pair/layer/block处理。legacy.pt weights_only+CPU mmap只读兼容，版本未知拒绝。异常partial保留，重试新attempt；不覆盖原FAIL。
8MiB只约束拷贝临时块，不是进程RSS承诺；OS mmap/模型Host内存仍需监测。连续reference额外Draft pre/post device snapshots上限1GiB，store4GiB，单独记账。

|Profile|单臂bytes|双臂+raw/atomic bytes|
|---|---:|---:|
|base|7102103552|28416802816|
|target4|9244631040|36986912768|

两profile合计65,403,715,584 bytes；准备阶段另要求16GiB reserve（prefix、numeric、日志/trace及临时产物），旧证据占用从实际free扣除。内容去重率不作为必然节省。模型自身Host/HBM峰值由设备记录，未伪造本地实测。

|场景|blocks|单KV集合|checkpoint预算|sample总量上界|
|---|---:|---:|---:|---:|
|A|9|169869312|355276800|699209728|
|B|10|188743680|393025536|774707200|
|A_prime|9|169869312|355276800|699209728|
|short|1|18874368|53286912|95229952|
|long|9|169869312|355276800|699209728|
|boundary|8|150994944|317528064|623712256|
|nonaligned|10|188743680|393025536|774707200|
|mixed|11|207618048|433729536|853159936|
|padding|2|37748736|93990912|173682688|
|return-short|1|18874368|53286912|95229952|
|three-active-four-padded|21|396361728|817127424|1614045184|
|four-active|28|528482304|1081368576|2142527488|


# 真实MRV2连续数值参考合同

DSpark.capture → 默认关闭instance-owned DraftGraphOutputReferences → pinned DFlash._run_model真实模型tensor → 每个实际FULL token bucket保留引用 → freeze真实inventory。
必须在LLM初始化/capture前安装；启动后纯工具无法取回已经离开作用域的hidden。manager返回None，greedy也不能假设draft_logits已写，因此最小production seam必要。默认关闭不分配sink/clone/event、不改变返回或Gate。开启保留引用可能影响allocator lifetime，明确为诊断capture。

ContinuousReference只允许独立empty-scheduler fixture：
1. query前、context KV已产生，保存全部canonical read/write Draft blocks、input_ids/positions；诊断同步在replay前。
2. 真实manager→pinned replay(None)→consumer→UPDATE；live generation仍存在。
3. 完成边界后读取本代sink hidden，保存Graph post-KV；检查同代submittedcarrier，不能再次consume_metadata。
4. 独立canonical Full/exact/valid计算 S=floor(max(E-1024,0)/128)*128、V=E-S和列，Draft padding不借Target padded；验证production Window。
5. 仅在独立诊断恢复全部相关Draft query pre-KV，用相同模型/输入/位置/query/slot与独立Window metadata调用真实_run_model(mode=NONE)，不切采样路线；finally恢复Graph post-KV。Target不swap、不restore。
6. 保存完整active hidden及padding范围、pre/postKV、canonical lineage、generation/epoch/descriptor，durable后下一代才能覆盖。

新增hidden合同预声明atol=rtol=0、FP16/BF16严格一致；非零差异NUMERIC_MISMATCH，不按设备结果放宽。原私有FIA0.016不变。
Target4冻结plan驱动A/B/A_prime、短/长、非对齐、mixed、1/2/4、3active4padded、切桶回旧桶。
Host实际pinned Python forward调用与CPU模型、真实builder/P3/P6 metadata/retire已贯通；native Graph replay/FIA/stream由明确替身，NPU NOT_RUN。
工具比较actual与本代/前代独立reference及可区分性，但范围是DIAGNOSTIC_SERIALIZED_BACKBONE_REFERENCE，不是采样算法完整新oracle，不是normal-overlap时序证明；不要求Window ON等于full-context OFF。

尚未实现：正常无逐代同步、完整受控连续hidden A/B/A_prime eager-reference producer。当前每桶输出可在下代覆写，要无扰动保存完整前/后KV并对照需新的隔离/多代输出合同及task语义。NormalOrderProbe只增加有界token device copy与末尾drain，不能伪称上述producer。此缺口阻塞全部G5 closure，不阻塞已实现串行数值实验。


# 生命周期与UPDATE生效代际

|操作/真实入口|owner/stream|源码/Host事实|未证明|
|---|---|---|---|
|EagerMixin materialize/P3workspace|spec/canonical FullSource/current|epoch/table/length同代，Full write保持|copy最后consumer|
|DFlashAclGraphManager prepare/bind|provider persistent/current|同代carrier、公开Gate不变|task内部operand|
|update_stream.wait_stream(current)后super.run_fullgraph|wait在replay之前|pinned replay返回None|wait不等于覆盖随后replay|
|captured FIA ExternalEvent.wait/reset|Graph task|源码有依赖点|C++版本语义及generation关联|
|update_graph_params task_update_begin/end/event.record|UPDATE stream|同代carrier参数，未前移UPDATE|UPDATE(N)影响N或N+1|
|proposal_scope finally retire|Hostlease/state|清空live inputs|不是devicecompletion|
|下代materialize同backing|persistent provider|Host ownership/stale检测|最后consumer前是否可复用|

Repair5 capability含实际torch_npu/CANN版本和PythonEvent源码；包装器不能独立说明C++task_update生效代际。ExternalEvent.query不恢复。

NormalOrderProbe observerOFF、provider仍装：真实manager返回后device clone draft_tokens，无每代D2H/query/sync，最多128代；保存stream、provider、全部backing、immutableWindow描述/runtimebinding、retire。整个campaign结束普通Event分别record current/update并drain后D2H。
OBSERVED_NORMAL_ORDER_WITH_DEVICE_COPIES只证明观测copy最终完成；不证明每次reuse前全部consumer完成。额外copy可能扰动竞态；event对象ID不是硬件时间戳。异常QUARANTINED，不强行等待不确定部分提交Graph。
LIFE仍DIAGNOSTIC_SERIALIZED。新增连续reference给本代/前代可区分数值判别也只属串行诊断。无正常overlapUPDATE闭环，未凭猜测重排/双缓冲/allocator重构。
ABORT外部watchdog独立进程，before_replay/after_replay/after_update/after_completion明确故障点；73+专用checker才接受，74/nativeerror/timeout拒绝；不sleep代替completion，不全局忽略非零。


## Profiling已有证据与下一次新增机制

# Repair5完整Profiling独立分析

读取完整trace_view.json、SQLite，不用前500X sample推断。raw路径/hash、事件index、字段/args、表/列/行数在同名JSON。
trace时间Decimal微秒，Host monotonic_ns独立；flow按cat/name/id或id2/localPID/scope关联，仅唯一s/f接受，一对多/重用/缺失保留。

|Case|events|matched|unmatched|ambiguous|Draft replay|直接flow|manager有flow|
|---|---:|---:|---:|---:|---:|---:|---:|
|PROFILE_LIFE|167462|20504|1|0|21|21|21|
|PROFILE_OFF_long_normal|332917|41365|1|2|47|0|47|
|PROFILE_OFF_short_normal|155659|19685|1|0|21|0|21|
|PROFILE_ON_long_normal|345872|42722|1|0|47|0|47|
|PROFILE_ON_short_normal|162036|20336|1|0|21|0|21|

+normal每个REPLAY_PLUS_UPDATE都有显式flow源关联，ONlong每次32条；单REPLAY_SUBMIT直接0，不能将manager全部kernel归给replay。LIFE直接21/21但额外串行化。summary逐次保留关联；最小fragment覆盖完整manager范围+显式flow目的地，original_event_index可回原trace。
存在async_npu/torch_to_npu、async_task_queue/enqueue_to_dequeue、HostToDevice与Dequeue@acl_memcpy_host_to_device等。task/context/stream可复用，未建立generation唯一关联仍UNRESOLVED_ASSOCIATION，不因缺generation停止所有分析。
long Target(1,8)24/(2,16)6，short6/6。ONlong14条source_start_column>0为Host descriptor事实，不是物理read。control无native。
原control REPLAY_PLUS_UPDATE均值short1.337→2.578ms、long1.228→2.662ms保留。范围含materialize、metadata/bind、wait_stream Hostcall、replay提交、consumer/UPDATE及Host记录，不等于kernel duration，不能把差额归给FIA或UPDATE。
Repair6包真实方法增加materialize/metadata_bind/UPDATE_CALL/retire_host子range，不复制调用、不加D2H/sync/I/O；开销profile与额外shapes/stack详细profile分开，installed signature不支持则CAPABILITY_UNVERIFIED。旧record_shapes=False/with_stack=False不是平台能力缺失。
kernel duration sum与E2E分别报告，跨stream不相加当walltime；kernel未覆盖区间不是全设备idle。无法唯一细分prefill/decode、Target/Draft kernel的部分UNRESOLVED。P-A开销分析有效，不能升级成physical block read或task operand。


## 文件范围、production影响及为什么需要

~~~text
.../test_draft_window_graph_diagnostics.py         |  66 ++++
 .../ut/spec_decode/test_graph_repair6_contracts.py | 236 ++++++++++++++
 .../ut/spec_decode/test_graph_repair6_delivery.py  | 225 +++++++++++++
 tests/ut/spec_decode/test_graph_repair6_storage.py | 108 +++++++
 tools/p7x_graph_repair2.py                         | 131 +++++++-
 tools/p7x_graph_repair4_target.py                  |  47 ++-
 tools/p7x_graph_repair5_evidence.py                |   2 +
 tools/p7x_graph_repair5_profile.py                 |  28 +-
 tools/p7x_graph_repair5_target.py                  |  87 ++++-
 tools/p7x_graph_repair6.py                         | 358 +++++++++++++++++++++
 tools/p7x_graph_repair6_campaign.py                | 183 +++++++++++
 tools/p7x_graph_repair6_lifecycle.py               | 121 +++++++
 tools/p7x_graph_repair6_natural.py                 | 127 ++++++++
 tools/p7x_graph_repair6_numeric.py                 | 215 +++++++++++++
 tools/p7x_graph_repair6_runner.py                  | 101 ++++++
 tools/p7x_graph_repair6_storage.py                 | 278 ++++++++++++++++
 tools/p7x_graph_repair6_trace.py                   | 168 ++++++++++
 .../worker/v2/spec_decode/dflash/aclgraph.py       |   6 +-
 .../spec_decode/draft_window_graph_diagnostics.py  |  37 +++
 .../worker/v2/spec_decode/dspark/speculator.py     |  25 ++
 20 files changed, 2517 insertions(+), 32 deletions(-)
~~~

- production三文件：dspark/speculator默认关闭capture输出引用；draft_window_graph_diagnostics instance所有权/shape/inventory；dflash/aclgraph将原UPDATE转交instance方法用于真实Hostrange。不改相对顺序、None return、算法、公开gate。
- repair4_target：sharedview去重及tensor_sink。repair5_target：per-sample durable、实际几何budget、prefix预检/numeric关联/异常保留；仍真实Target forward，非HEAD_ONLY替代。
- repair6_storage/repair6：新格式、legacy只读、全计划覆盖、partial/数值/执行joint分层；confirmedFAIL优先。
- repair6_numeric/lifecycle：串行连续参考与正常顺序观察分账；同代submittedcarrier而非第二次consume_metadata。
- repair2：默认关闭CLI、Target sample业务identity、预检、诊断artifact、清理错误单列，不吞核心异常。
- profile/trace/natural：真实调用range、完整显式flow、唯一业务配对；不按时间邻近猜kernel，不按列表zip自然样本。
- campaign/runner：维护于Git源内、per-commandtimeout、冻结依赖、abort专用非零语义。无包内production覆盖补丁。
- 新测试4文件：真实pinned Python forward/capture、builder、P3/P6 bind/retire、实际CPU tensor→writer/reader/checker、CLI及外部身份负例。native replay/FIA/stream/Event均明确Host替身。

## RED/GREEN与测试范围

基线RED通过git show d0a3fc3d42d7d97e5e7da3890d2710263a097e63:tools/p7x_graph_repair4_target.py加载，未切checkout：
VLLM_VERSION=0.29.0 PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm .venv/bin/python g1-g5_repair6_local/red_baseline.py
（实际脚本位于Notes辅助目录，完整argv在日志）。
exit1原栈：EvidenceError: complete checkpoint needs 512 bytes; remaining budget 256。
旧UT小独立字段未覆盖真实sharedmask与36层预算/集合放大。GREEN保留所有字段、alias与写侧，唯一view不重复copy。
本轮真实runtime identity新记录又抓到TypeError: Object of type DraftWindowGraphRoute is not JSON serializable，复用已有_json_safe后全链GREEN。原失败logs_pre_serialization_fix保留。真实P3/P6集成还防止重复消费metadata：reference必须查看已经SUBMITTED的同代carrier。

最终20个受影响测试文件（Repair2/4/5/6，P6 binding/carrier、observer、oracle）：554 passed,1warning,42.26s。
没有宣称全spec_decode或NPU suite。env VLLM_VERSION=0.29.0、pinned vLLM PYTHONPATH，完整argv/exit/文件hash在Validation.json。
Ruff/format、14文件targeted Mypy(follow-imports=skip)、compileall、diff-check全部exit0。
8项独立仓库检查packageinit/logger/import/boolean/longfunction/symbolic/codespell/typos通过。
完整pre-commit/manual exit3：actionlint下载压缩包EOF截断，ENVIRONMENT_BLOCKED，未关规则。gitleaks本地未找到，仓库fallback带--no-check-certificate未执行，ENVIRONMENT_BLOCKED；有限新文件凭据pattern扫描无命中，不冒充gitleaks。仓库hooks未安装，正常commit -s，未使用--no-verify。
历史7项VWN失败仅引用Repair5报告精确3bdc同环境对照，不计PASS、不重跑无关suite。所有NPU native NOT_RUN。
Validation before/after的20文件hash与最终提交逐一相等；Final_Git_Identity保存绑定。首轮/中间失败日志保留，最终logs独立。

## 证据门与production收尾

# Graph准入证据/平台决策与production收尾

|要求|已有证据|缺口/具体问题|本地措施/关闭条件|责任范围|
|---|---|---|---|---|
|Python FIA operand|旧SHA真实层/table/length|Task最终operand不是Python地址|保留operator级，需task handle→输入descriptor地址接口|平台维护者/验收owner|
|task binding|task_update调用|当前版本update生效和ExternalEvent re-record语义？|可复核正式语义或真实task/generation trace|CANN/torch_npu维护者|
|数值窗口语义|旧Target7对、真实tokenABA|新连续reference及完整mixed/padded|NUMERIC_TARGET4+完整Target；失败不放宽容差|执行者/reviewer|
|physical read-set|边界operand+数值不干扰|现有导出无block事务|CAPABILITY_GAP/ACCEPTANCE_DECISION_REQUIRED|验收owner/平台|
|UPDATE代际|Host顺序/串行ABA|正常N/N+1|串行连续current/previous可补信息；正常受控未实现|平台/开发|
|最后consumer/reuse|LIFE event、normal末尾drain|每次rewrite前完整happens-before|normal观察不关门；需task/event语义|平台|
|完整Target|前7对完整raw相等|mixed/3active4padded/4active全计划|有界store后全量重跑，不能降HEAD_ONLY|A3执行者|

替代证据建议只供owner决策：operator+数值不干扰+正式stream语义可能证明算法正确，但不证明物理事务。本轮未降低Frozen标准。
正式收尾仍需：实验provider→正式配置/路由、正常生命周期、异常隔离、capture fallback、文档/回归/性能/合入审查。Base只限DSparkTP1 STANDARD dense single gid、query7/window1024/block128、同步无prefix；Target4独立实验不扩大产品支持。Batch A未做。
Window只改Draft read；Full write/query引用不变；None return不变；无ExternalEvent.query/global synchronize热路径/ContextVar/Target owner swap/上游修改。public Gate STILL_FROZEN。


## 服务器顺序、依赖与停止

# Repair6 下一轮执行（PRE_PUBLICATION）

源码 febc43be3309f6d2cd87f9332cb7e031ebaad001 / tree f68e57e4501dacb67cdf4c81831b8f713e4ddc18 / parent d41bb588a7e62b67a3ee1ce4bf652bf2701662da。本轮未push。发布会话必须普通push、独立网络clone验收，再更新handoff publication_status=VERIFIED并重新打包。当前PREPARE/runner会拒绝执行，禁止手动绕过。
建议部署路径（尚未创建）：/mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend，配套/mnt/wenqing/mrv2_graph_repair6_verify/source/vllm，输入/mnt/wenqing/mrv2_graph_repair6_verify/server_input。实际Python/runtime/import由现场核对，不能复制Mac环境路径。模型路径、全部参数、请求来自原fixture与已提交driver。

## 发布后准备

~~~bash
python3 /mnt/wenqing/mrv2_graph_repair6_verify/server_input/PREPARE.py --repo /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend --vllm /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm --output /mnt/wenqing/mrv2_graph_repair6_verify/RUN_REPAIR6_febc43be --run-id RUN_REPAIR6_febc43be
~~~

PREPARE验证已发布handoff、两仓exact clean/import、toolhash、fixture每文件hash及全campaign预算；不加载模型。源码/模型/资源失败先停，不靠减少bucket/换模型/eager fallback。
其后用已提交runner单case执行：

~~~bash
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair6_runner.py --plan /mnt/wenqing/mrv2_graph_repair6_verify/RUN_REPAIR6_febc43be/case-plan.json --case-id P0 --output /mnt/wenqing/mrv2_graph_repair6_verify/RUN_REPAIR6_febc43be/runner
~~~

case_id替换为表中项。完整argv/dependencies/checkers在case-plan.preview.json，最终部署plan由PREPARE按实际目录生成；不将预览路径当既有机器路径。

|分支|case顺序|验收/产物|失败处理|
|---|---|---|---|
|源码/API|PREPARE→P0|exact/import/fixture；版本/API/FIA schema；资源|阻断设备，但允许独立离线分析|
|新SHA锚点|A0→A1→B0|A0请求；A1 GRAPH_FROZEN负例；B0真实3桶replay、多代每层update/retire、输出16token/外部launcher联合|核心错误停依赖分支|
|资源最小例|PREFIX_OFF/PREFIX_ON|首A完整Target+chunkwriter/reader/joint|该臂失败停全量，保留prefix|
|完整Target|G4F_OFF/ON→G4F_COMPARE；TARGET4_OFF/ON→TARGET4_COMPARE|原11/12场景；Base4row expectedOPEN；Target4实际4rowcapture/replay和双臂全比较|失败仍可显式只读COMPARE，不将prefix写整组PASS|
|真实连续数值|NUMERIC_TARGET4|同Window、真实MRV2 graphhidden/eagerreference、全部active/padding/源KV、A/B/A_prime/切桶|source/oracle/数值错停止，不调容差|
|正常顺序|NORMAL_ORDER|O1combined、observerOFF，三桶每桶>=2代、source/launcher/16tokens、末尾copydrain|只能normal-order观察，不作为reuse闭环|
|自然观察|G4_OFF/ON_long2、mixed（需要新identity才跑）|唯一业务配对，全部歧义/未配对|不强求自然轨迹等长|
|开销|PROFILE_OFF/ON_short/long_control/normal|capture后warmup/active，实际Graph，16token；新增Host子range|只一种nativeprofiler；control不计native|
|详细诊断|PROFILE_ON_long_detailed|签名支持shapes/stack、有明确新增字段目标|不支持则CAPABILITY_UNVERIFIED，不重复同trace找物理read|
|按需历史|C2/LIFE/ABORT_*|本轮未改其核心，异常风险或diff影响才重跑|abort73必须专用checker，74/timeout拒绝|

producer默认1800/3600s，read-only比较3300s，外层margin120s，精确值见plan。保存exit/signal/timeout/stderr/partial/laststage/progress与全部命令；runner max_rss_children为平台单位（Linux KiB），不是HBM。
producer完成、sample完整、数值、覆盖分别报告。NUMERIC_MISMATCH不能被OPEN覆盖；COMPARISON_TIMEOUT不是数值FAIL；SAMPLE_COMPLETE仍需要外部执行联合。
Base缺4row不会自动扩配置；Target4独立profile。各比较分支只依赖P0，须在两臂尝试后显式调用，容许失败前缀恢复，未成双臂不盲目加载大集合。

## 离线与回传

~~~bash
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair6.py compare-target --off OFF/controlled-target.json --on ON/controlled-target.json --timeout 3300 --output comparison.json
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair6_natural.py --off G4_OFF_long2 --on G4_ON_long2 --output natural.json
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair6_trace.py --trace trace_view.json --output full-flow.json
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair5_pack.py pack /mnt/wenqing/mrv2_graph_repair6_verify/RUN_REPAIR6_febc43be --output /mnt/wenqing/mrv2_graph_repair6_verify/Repair6_raw.zip
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair5_pack.py verify /mnt/wenqing/mrv2_graph_repair6_verify/Repair6_raw.zip
~~~

流式4MiB/ZIP64打包，保留失败，接收端重新verify。原模型manifest SHA 1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4。
旧Repair5已回答的前7Target、tokenABA前缀、B1计数和flow存在无需无理由重跑旧35项；旧SHA只是历史，不自动继承新SHA。没有新字段机制时，不重跑相同profiler期待physical read。


## 最终身份与交付

branch=fix/p7x-graph-base-a3-repair6
commit=febc43be3309f6d2cd87f9332cb7e031ebaad001
tree=f68e57e4501dacb67cdf4c81831b8f713e4ddc18
parent=d41bb588a7e62b67a3ee1ce4bf652bf2701662da

两个独立提交：d41bb588a7e62b67a3ee1ce4bf652bf2701662da（production默认关闭诊断seam）→febc43be3309f6d2cd87f9332cb7e031ebaad001（工具/测试），父基线d0a3fc3d42d7d97e5e7da3890d2710263a097e63未改写。
Signed-off-by Lucian存在；密码学签名N，分别记账。
vLLM 84030bbe3d74d99bad477a3d2e37a973ccd8865c / f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee clean/zero diff。本仓clean。未push、PR、merge、tag；未运行服务器；未改Frozen设计、旧报告或raw。
顶层本报告、handoff、review ZIP、Server Input Pack、Download Manifest、Package Verification在Notes/MRV2；aux含完整diff、逐样本/逐block复算、rawhash、flow片段、验证日志。
旧设备事实与新checker/final code分账。任何新G1–G5均未升级为设备PASS。
