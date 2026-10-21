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
