# 有限诊断开销对照（执行前声明）

问题：LIFE中的observer、普通event/synchronize与D2H诊断共同增加多少请求阶段开销？现有C15 normal-long与PROFILE_LIFE short工作量不同，不直接相除。

在当前完整numeric/Target与C15 LIFE/异常链结束后，若依赖、资源和deadline仍满足，仅追加三个已committed case：PROFILE_ON_short_control → PROFILE_ON_short_normal → PROFILE_LIFE。均同C15、Base、Phy0 TP1、相同smoke请求、16输出tokens；先验证实际请求/tokens/replay/active-padded范围一致，再给描述性对照。无其他本任务模型并行。历史同类启动约80–120s，硬timeout按计划每case1800s；不把timeout当ETA。

这是一次normal短工作负载与LIFE诊断总成本的有限比较，不拆分各同步单项因果，也不将LIFE变成正常复用证明。每种仅一个新进程，波动和profiler自身开销单列；不选最快、不扩展TP16或全部八组重跑。原C6四采集四控制仍仅历史证据。
