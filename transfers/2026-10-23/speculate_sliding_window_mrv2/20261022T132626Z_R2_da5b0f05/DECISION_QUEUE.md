# 待决事项（2026-10-22T16:54:01.368486+00:00）

公开Graph Gate冻结；本文件是供审查的队列，未向他人发消息。常规工具/代码bug由本执行者直接修复，不退给用户。

## 1. CANN/torch_npu维护者：接受或补足正常多代依赖合同

具体问题：匹配9.1源码的endGraphNotify、MRV2 Stars路径、update_stream.wait_stream(current)及ExternalEvent多代复用，是否完整保证UPDATE(N)被本代放行的FIA消费，并使下一代current写在最后消费者之后？

已有证据：官方9.1任务更新说明；精确torch_npu/op-plugin；Runtime同版tag、CHIP_910_B_93 isStars=true/v100注册；实际worker加载v100；ExecuteAsync拒绝AICPU executor；FIA Host长度vector被复制。详见平台问题单.md和正常UPDATE与backing顺序核验.md。不能继续笼统写“没有API证据”。

建议：审查这些明确边，确认安装版补丁/适用合同及内部最后consumer覆盖。若不成立，给出具体缺失依赖后设计所有权/完成lease修复并测量代价；不先把LIFE同步塞进production。

不决定：NORMAL_UPDATE_GENERATION/NORMAL_BACKING_REUSE的完整正式裁决继续受阻。可继续：数值/Target、串行LIFE、异常隔离、有限profiling与代码审查。

## 2. 平台维护者 + 验收owner：native参数快照到执行实例/physical read的边界

已有证据：C15三图15FIA参数块来自Runtime同步D2H，不是仅Host镜像；严格ABI解析的KV长度区别初始capture并匹配最后Host值。原生ts/dur已证实为合成布局。C19已真实通过capture handle/event及K/V地址逐层关联15个FIA参数块，修复C17单Tensor容器误判；这是post-drain新NPU证据，仍无执行occurrence/physical-read。

待决定：post-drain device参数块能满足既定task operand合同的哪一部分；还需哪种可靠的replay occurrence/generation和KV physical-read证据。请提供可用平台能力或由owner明确验收方案，不能无限重复没有新字段的dump。

不决定：TASK_INTERNAL_OPERAND完整执行绑定、PHYSICAL_READ及production正式支持结论未关闭。可继续：C19native诊断和正常业务范围验证；可提交有明确边界的候选材料。

## 3. 平台维护者：原生部分提交失败的原子性与允许清理

Context::StreamEndTaskUpdate所查路径可报告部分成功/失败并重置任务组，没有展示整体rollback。C15四个os._exit和四个真实Python展开已分别完成，实际C1 quarantine/Host guard覆盖，不模拟破坏性native故障。

建议：逐点说明begin/FIA/end/event-record失败的提交保证；当前保持Host导出与进程隔离，不恢复设备/KV/backing。该决定仅阻塞native未知状态后的安全恢复；不阻塞保守隔离和独立正常分支。

## 4. 资料owner：历史relay公开问题

接收报告称LucianWQZ/private-file-relay实际public。owner决定既有资料处置和以后传输位置；本轮未上传新增日志/模型/raw，也未改仓库可见性。服务器本地开发不受阻。

## 已关闭、不再索取同样人工操作

- 自动审批预约时间冲突：用户明确确认预约有效至北京2026-10-23 10:00；单独保存原话，正式审批已接受。任务仍原2026-10-22 23:26:26 UTC截止，未重置窗口。
- Agent设备可见性与映射：真实Phy0 probe已4次；前三次与C19 probe04原件分别保留，probe不当成模型。
- C12 fixture真实capture/UPDATE/数值链已通过；C13/C15/C17实测继承，C19按实际结果更新。
- C1真实Python展开：C13/C15四点已实测，未知分支无新sync/D2H/query；原ABORT与Python展开单独裁决。
- C12 ABORT runner错误命令：C13修复，旧4次失败和只读复核保留；新C13/C15设备runner接受。
- C18准入Host证据分类bug已修、10项定向检查及真实计划派生反例证明旧接受/新拒绝。C17当前使用的原计划有全部必需证据，未依赖该缺陷。
- C19 native producer容器bug已修并commit，45项Host通过；真实设备重验已通过15个native FIA逐层绑定；完整12数值/ABA亦通过，Target4 OFF与剩余生命周期按当次joint更新。
