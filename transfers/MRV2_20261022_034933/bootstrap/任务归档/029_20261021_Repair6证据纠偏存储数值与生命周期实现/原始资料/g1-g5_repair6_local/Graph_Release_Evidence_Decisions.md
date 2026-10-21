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
