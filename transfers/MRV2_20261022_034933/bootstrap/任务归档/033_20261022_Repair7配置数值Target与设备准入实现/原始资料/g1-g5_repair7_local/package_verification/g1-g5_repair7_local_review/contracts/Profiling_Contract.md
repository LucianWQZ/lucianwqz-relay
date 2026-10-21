# Profiling合同（没有Repair6/7新trace）

本轮复用已提交torch_npu profiler入口，不运行任何采集。OFF/ON × short/long × control/normal；一个ON long detailed；LIFE成功后PROFILE_LIFE。完整配置来自同一build_llm_kwargs，normal observer-off且不装controlled Target/numeric/LIFE同步。禁止业务is_profile=True来开启profiler。
模型初始化/capture后warmup，16-token冻结请求组重复、有限active阶段；控制组不装native profiler。长窗以runtime source_start_column>0/实际S>0验收，不以prompt字符数推断。
tools/p7x_graph_repair5_profile.py::ProfileSession.install的实例wrapper包住真实_materialize_draft_window_read_inputs、build_draft_attn_metadatas、_update_full_graph_params、retire_generation；标签Draft_materialize/Draft_metadata_bind/Draft_UPDATE_CALL/Draft_retire_host。不是只包日志，不代表device completed；不在replay→UPDATE间新增D2H/同步/I/O。
真实plan中的--help/argv已解析；服务器capability preflight需确认实际profiler API。详细shapes/stack另profile，不与normal成本混算，不升级底层栈。
保存原trace、API版本/config、PID/stream/task/flow、解析日志与片段。tools/p7x_graph_repair6_trace.py为完整flow分析；工具可得字段/成功关联/歧义/无法关联分别统计。禁止按邻行/shape强连generation，禁止Host monotonic和设备时间直接相减。
Repair5旧trace可参考但不能标新SHA；Repair6无新trace，无本轮性能数字。正常开销诊断不等于正式性能收益，也不关闭physical-read证据。
