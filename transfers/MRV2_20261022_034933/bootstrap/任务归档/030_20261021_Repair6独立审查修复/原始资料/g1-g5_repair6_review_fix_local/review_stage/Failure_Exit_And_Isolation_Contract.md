# 失败、退出与隔离合同

原始异常在 campaign.exception_type/message/traceback；导出与 cleanup 错误另列，不能覆盖原始异常。
SubmissionState 为每个诊断实例所有，不是 module-global，也不是生产 completion 协议。

|阶段|允许清理|退出/结果|
|---|---|---|
|尚未提交/已完成纯Host合同错误|恢复Python方法；已确认完成时可普通teardown|2或合同INVALID；不是设备PASS|
|replay/UPDATE pending、reference pending、observation pending|只保存已有Host字段，禁止再restore/query/sync或正常engine teardown|74，进程不可复用|
|已完成且durable NUMERIC_MISMATCH|失败样本保持，禁止下一代；可安全普通teardown|3|
|资源不足|保留PREPARING/partial，使用新attempt重试|5|
|有意ABORT|仅73+专用abort checker，其他非零不豁免|独立实验|
|外部超时|watchdog记录PID树，仅终止自身后代（含新session），先TERM再KILL|124/COMPARISON_TIMEOUT|

未知提交不能依赖 Python return 或 Host retirement 判定完成；numeric/normal/LIFE 任一 poisoned 都进入 driver finally 的74隔离。若OS禁止ps，至少终止已知进程组并抛出隔离能力错误，不能宣称所有后代清理成功。本机受限沙箱首次ps被拒，提升权限后真实子进程测试通过。没有终止其他任务/服务。
自然比较工具生成失败报告不再exit0。runner可在producer失败后执行独立只读比较以保留有效前缀；仅依赖失败case的分支阻断。Base不支持Target(4,32)仍OPEN，Target4独立profile不继承该OPEN。
