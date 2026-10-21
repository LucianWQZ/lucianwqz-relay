# 准入证据与责任边界（标准未降低）

|项目|当前证据|关闭条件/责任|
|---|---|---|
|checker/producer状态合同|本轮真实Host反例与全链修复|本地已处理；新SHA设备仍须跑|
|完整Target/Window数值|旧SHA各7对前缀；新有界存储与连续reference已实现|A3执行完整Base/Target4矩阵，零容差不变|
|normal UPDATE代际|Host顺序/old串行tokenABA|本代/前代可区分结果+当前版本task-update语义；平台维护者|
|last consumer/reuse|普通流FIFO候选链；Target copy不覆盖Draft；Host retire非完成|平台提供跨流task/ExternalEvent语义，设备验证每次rewrite/最后consumer；不能只看末尾drain|
|task内部operand|Python边界table/length指针可记录|平台提供task handle→真实operand descriptor接口；当前CAPABILITY_GAP|
|physical read-set|数值窗口语义/窗外扰动不等于memory transaction|设备接口或验收负责人明确替代证据决策；ACCEPTANCE_DECISION_REQUIRED|
|Profiling|旧完整trace有flow，manager可关联但replay尚非唯一|新增4个真实Host子range+安装/计数/代际覆盖，正常OFF/ON短长；detailed独立、不重采同字段期待物理地址|

Production收尾仍需实验provider到正式配置/路由、正常跨流生命周期、异常隔离、capture inventory/fallback、用户文档及A3验证。Public Gate保持冻结，Batch A不做。任何owner未批准的证据替代不能自动豁免Frozen要求。
