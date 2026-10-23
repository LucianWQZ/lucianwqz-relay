# 正常 Graph 的 UPDATE 与 backing 合同审查（R3）

适用：DSpark TP1、Qwen3-8B + dspark_qwen3_8b_block7、K7/W1024/block128，async/prefix及其他并行关闭。C19至C24的production子树相同。C25及最终C28修正早期异常保留策略，正常成功路径的copy、stream、replay/UPDATE及数学未变；本表A/B推导不以Host异常修复代替设备完成证据。public Graph Gate冻结。

## 判定口径

本轮将“源码支持的工程合同”与“安装分支适用性”“执行可观测性”“验收决定”分别裁决。正常成功流依赖尚未发现确凿实现缺陷，因此没有加入同步、双缓冲或改动流顺序。另有已证实的早期materialize/metadata发布异常清理缺陷，以C25修正并由C28继承，C28已取得真实早期异常隔离、B0/C2/LIFE21代与完整12数值/ABA设备证据，正常A/B工程合同仍独立裁决。源码支持不冒充原生执行occurrence实测。

|问题|明确要求|已有依据|缺失条件/可区分动作|分类与责任方|停止重复条件|
|---|---|---|---|---|---|
|A 最后消费者→下一次写|旧Graph所有相关设备读取完成，才允许current流下一代覆盖|RI Stars endGraphNotify wait；本轮再查明capture结束时附加流尾notify汇入原流|维护者确认当前安装补丁与该capture分支相容；如指出绕开合流的具体consumer，再设计反例|SOURCE_SUPPORTED_CONTRACT；安装适用性由CANN维护者复核|没有新平台字段或具名反例，不重复LIFE/native dump|
|B UPDATE代际|N的wait放行时使用N参数，未来update不能越过上一代完成|官方9.1外部事件任务更新协议、单update流、各代wait-current前缀、长度vector拥有拷贝|维护者对task-group临界资源/事件复用合同的适用性确认；不要求压力无错代证|SOURCE_SUPPORTED_CONTRACT；平台适用性审查|只在有可区分版本观测API或合同反例时采集|
|执行参数occurrence|真实执行版本与replay/generation一一关联|C19 15个设备参数块逐层绑定，但为post-drain末值|需正式launch occurrence/参数版本能力；现有合成ts/dur无效|OBSERVABILITY_LIMIT；平台+验收owner|同样末值dump不能回答此问题，停止重复|
|physical read-set|区分有效长度/数学语义与实际KV地址访问|G3原有源码明确要求device-level read-set；当前只有参数绑定/数值/trace|owner明确既定门槛的可实施方案；平台提供安全地址访问证据|ACCEPTANCE_SCOPE_DECISION + OBSERVABILITY_LIMIT|没有新能力时不以重复dump填补|
|性能snapshot|解释10ms等待对象及OFF对应成本|本代prepared seq_lens的阻塞to(cpu)，OFF并行draft走device.tolist|全组预热、共同metadata范围、交错重复与少量3072请求|可独立设备分析；Graph执行者|有限3次重复+各1次profile，仍不稳定则报告限制|
|Base缺桶|不将Target4结果归给Base|Base仅(1,8)/(2,16)，Target4另有(4,32)|拟支持Target4；Base4请求正式范围/明确拒绝由owner决定|ACCEPTANCE_SCOPE_DECISION|不重复已知缺桶case|

## A：本轮新增的具体源码链

复用R2精确版本原件：`../20261022T132626Z_R2/platform_sources/`。官方Runtime9.1.0 commit 0b4af8a31c75a1f1f43638a8f75b9e3c6182e031；不是泛引同名API。

1. `runtime910__src__runtime__feature__aclgraph__context_aclgraph.cc:398` 的 `AddNotifyToAddedCaptureStream` 遍历 `GetAddStreamMap()`，在每组 `second.back()` 尾流record notify，在原流wait。成功结束capture之前已合流。
2. 同文件 `StreamEndCapture:514–559` 先检查子capture结束与有效性，调用上述合流，再设置执行notify、ResetCaptureEvents；非SoftwareSQ分支随后ModelEndGraph并LoadComplete。任一失败会返回，不作为可运行完整Graph。
3. `runtime910__src__runtime__feature__model__model.cc:1184–1233`，SubmitExecuteTask后，Stars非AICPU路径向RI执行流提交endGraphNotify的NtyWait；SoftwareSQ与非SoftwareSQ分别调用对应wait形式。
4. `capture_model.cc:268–310` 的ExecuteCommon在Model::ExecuteAsync前后设置notify。`model.cc:1366`明确拒绝AICPU executor。`config/910_B_93/dev_info_reg.cc`注册isStars=true、平台库v100；C19真实worker加载libruntime_v100.so（R2 environment/C19_actual_worker_provenance_complete.json）。

由此，A所需的“捕获的附加流也应汇入完成边”已有可审查源码依据，不再只写一个孤立的NtyWait。该推导适用已注册/合法捕获的Graph消费者，不覆盖私自脱离capture的异步工作或未知安装补丁。安装头文件、库与平台注册证据支持适用性；不把同版号当作整个二进制全部分支的证明。需要维护者回答的是是否存在具体安装例外/额外消费者，不能笼统回到“没有API证据”。

## B：跨代版本推导

项目 `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py::run_fullgraph` 实际顺序保持：

materialize/bind N → update_stream.wait_stream(current) → replay N → UPDATE N → event.record N。

- current的前缀包含上一代RI完成边及本代Device写；wait_stream排在本代replay前，因此不等待本代被event阻塞的replay，避免人为移位构成循环。
- FIA捕获任务前有ExternalEvent wait/reset；本代UPDATE与record在同一update流FIFO。官方 `CANN91_TaskUpdate_en.txt` 明确这套协议用于让任务等待更新完成；task group是临界资源，不允许多线程/多流同时更新。
- 本项目更新只有一个流；UPDATE(N+1)前再次wait current，current前缀含RI(N)完成及N+1写。因此未来record/update不能跨过尚未完成的N；已捕获的reset也在该完成边内。
- op-plugin 8b9c8534fa41eff367a41c155843daa530ab3a08 的FIA更新专用宏复制Host长度vector，队列lambda拥有拷贝。不是CPU workspace裸指针一直被设备读取。
- 因此，A/B前提成立时，固定Device backing的写→读→再写可依靠既有设备边排序，不依靠Host retire/UPDATE return/Target早期D2H。

结论：正常多代依赖是 **SOURCE_SUPPORTED_CONTRACT**，具体安装适用性尚需 **PLATFORM_APPLICABILITY_PENDING** 审阅；设备执行occurrence/read-set仍无新实测。不是IMPLEMENTATION_DEFECT，也不由本Agent自签正式支持。

## 异常与范围

C19四ABORT与四真实Python展开保留原身份与边界。未知部分提交仅Host导出、quarantine、进程隔离；不设备恢复/清零/同步取证/再用可疑backing。Runtime StreamEndTaskUpdate有部分失败计数，没有整组rollback保证，故不缩小C1保护。正常成功路径不新增保留列表。

## 需要owner作出的有限决定

1. CANN/torch_npu维护者审阅A/B适用前提，明确有无实际补丁/消费者例外；若无例外，可认可源码工程合同，不必再索取相同dump。
2. 验收owner对原有G3 device-level read-set要求选择：提供可安全关联真实执行/地址范围的能力；或另行审查并修改正式验收合同；或继续冻结发布。本Agent不选择降低门槛。
3. 原生快照POST_DRAIN_EXPORTED_PARAMETERS_ONLY只覆盖绑定事实，不命名为执行代际。窗口数学、输出正确性、原生绑定、地址read-set、性能收益分别报告。

## 历史22:54准备检查点（已由后述真实设备证据更新）

原C24在typed inputs形成前首次合法拷贝后抛错，CPU真实方法反例观察到两次清零，外层C1未阻止早期重入；metadata发布也有内部abort提前清理。C25引入Graph失败保留贯穿lease，C28继承；正常成功顺序没有新增event/sync/D2H。162项受影响Host检查通过，设备验证尚未开始。此缺陷分类IMPLEMENTATION_DEFECT，修复状态HOST_VERIFIED_DEVICE_PENDING，不声称观察到真实设备读写损坏。原始FAIL和旧C19 AST guard失败均保留，见C25_源码影响与Host结论.json、已批准pin与既有AST守卫精确核对.json、C28_final_affected_host.log。

## 2026-10-23T00:42:37.898514+00:00 实际设备更新

C28真实早期materialize异常已由专用joint接受（lease保留、Host guard拒绝、无后续清零/replay、隔离74）；B0/C2/LIFE21代及完整12数值/ABA已接受。证据C28_早期materialize异常设备验证.md、各case runner/joint。C28实际worker十类关键库与C19哈希相同，csrc树26fe09e3161116a2998e02c6df4be546d965452e一致，见C28与C19实际worker二进制身份对照.json；支持版本连续性，不扩成整个二进制分支或真实operand/read-set证明。四个新正常/实验profile均无generation-bound execution flow，未重复同样native末值dump。Source-supported A/B合同及正式平台适用性/验收边界保持。
