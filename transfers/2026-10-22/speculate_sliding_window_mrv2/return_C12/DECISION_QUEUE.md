# 待决事项

## 平台维护者：UPDATE 与 backing 的 native 合同

问题：`aclmdlRICaptureTaskUpdateBegin/End` 在 replay 已提交后如何选择生效代际；更新 API 对 table/seq_len 设备地址的最后读取何时发生；ExternalEvent.record 之后是否保证相关参数读取结束；异常是否可能部分提交。

已有证据：`正常生命周期源码审计.md`；已安装 CANN 9.1.0 头文件与 torch_npu 2.10.0.post4 实现；本轮正常 trace 的完整 flow 关联表。缺少的是规范保证或能绑定 task-group handle/ModelID/StreamID/generation 与实际 operand 的 native 记录。

建议：维护者提供版本适用的书面 API 合同，或审定最小 native hook；若需要新增完成依赖，应绑定最后实际设备 consumer 并测量正常性能。当前不能仅把诊断 synchronize 移入正常路径后称原异步路线通过。

阻塞：NORMAL_UPDATE_GENERATION、NORMAL_BACKING_REUSE 的正式裁决。可继续：连续数值、Target/Full 不变式、独立隔离与正常 profiling。

## 验收 owner：task 内部绑定与 physical read-set

问题：当前 profiler 导出存在 stream/task/flow，但不暴露实际 operand 地址或物理读集合。直接 replay flow 未关联，父 replay+UPDATE 关联不能拆分。

建议：明确正式支持审查需要哪条 native/硬件证据；可选维护者 hook 或限定支持范围，必须单独裁决，不由执行 Agent 降低标准。阻塞 TASK_INTERNAL_OPERAND / PHYSICAL_READ；不阻塞继续现有软件与设备正确性验证。

## 资料 owner：private-file-relay 实际 public

接收记录称 LucianWQZ/private-file-relay 为 public。请资料 owner 决定既有公开资料处置和后续安全传输位置。本轮不上传新增日志、模型、内部清单或原实验包，不修改仓库可见性；服务器已有资料可继续本地开发。

### 可选择方案及影响（供维护者/验收 owner）

- 提供CANN9.1.0、torch_npu2.10.0.post4的UPDATE版本选择、参数地址最后读取、ExternalEvent与部分提交规范；若合同覆盖现有顺序，保留现有性能路线，补具名最小native验证。这是优先建议。
- 审定能导出task-group handle/ModelID/stream/task与generation、实际operand的最小native hook；增加构建和平台维护成本，但能区分当前trace无法区分的假设。重复现有profiler无此字段，无信息增量。
- 若合同要求新增所有权依赖，先明确最后consumer，再设计普通completion lease或明确串行支持路线；需单独测性能并审查冻结架构。不能直接把LIFE的同步搬入正常路径后称原异步路线成立。

C1目前对带characterization且live generation异常采取保守隔离，包含可能已确认未提交的异常；这是安全范围偏保守，不是确认部分提交。正常成功路径未新增该quarantine；多代请求可以运行，但这不证明native backing最后读取已完成。四个osexit故障点验证的是独立进程隔离合同，不能冒充C1异常栈展开函数的真实设备覆盖。
