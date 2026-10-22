### LIFE中“direct flow”必须按实际目的地细分

原committed解析器coverage.direct_matched只统计Host Draft_REPLAY_SUBMIT范围内任一显式flow。LIFE该原始指标21/21，而normal0/21；逐条复查63条目的地，42条是destroy/record event的Host队列，21条是设备EVENT_RECORD，**没有一条目的地MODEL_EXECUTE**。因此本轮没有获得21条replay→模型执行直接边。原解析结果不覆盖，新分类原件为`C17_direct_flow_实际目的地分类.json`（含原event indices、flow key、目的地真实名称/args）。不能将诊断事件误写为Graph执行绑定；正常源代际、task operand和physical read仍未因此关闭。

正常和LIFE中Event::synchronize显式调用分别42/84次；LIFE增加42次，与21代每代两个普通event drain一致。API自身sum约1.85/4.02ms，不能解释29.9s全部差异；device NOTIFY_WAIT的sum约255ms/10663ms，有跨流重叠且可能等待Host下发，不能加总为elapsed或将其当作单一根因。

LIFE启用了heavy recorder，而normal仅安装但recorder_enabled=false。源码还有`_append_lifecycle→write_artifact→snapshot/json.dumps/write_text`逐层Host工作和LIFE `_flush`，这些不在正常observer-off路径。本轮没有单独测量其CPU序列化/I/O时间，故只报告诊断总开销，不将差值全归给同步、D2H或某个算子。三个short样本仅各一次，不能估计尾分位数或稳定比率。

Summary补充whole_request_elapsed_per_observed_draft_replay_ms用于相同外部工作量的描述；它含Target/prefill等全部工作，不是Draft kernel延迟。每层device归属、全部verification和acceptance为NOT_AVAILABLE。

## 可导出的统计图

[有限重复与materialize逐次范围](Profiling_C15有限重复与materialize.svg)（另有PNG）：保留全部三次控制和47个Host样本，不将嵌套区间相加。

[正常与LIFE诊断短请求对照](Profiling_C17正常与LIFE诊断.svg)（另有PNG）：纵轴为对数、三模式各一次，仅描述同外部工作量下的总时序，不能归为同步单因或正常Window加速率。

生成脚本plot_profiling_summary.py只读本报告Summary和CSV、CPU绘图，不运行模型；图不是原始trace的替代。
