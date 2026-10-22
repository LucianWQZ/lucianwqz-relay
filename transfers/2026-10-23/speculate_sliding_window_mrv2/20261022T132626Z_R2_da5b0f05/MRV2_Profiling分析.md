# MRV2 第二轮 Profiling 分析

更新时间：2026-10-22T15:21:08.046199+00:00。源码 C15 `1e88c8208670518f63043552b530b1ed3e2f2677`，tree `8a233dc2fd99abdafcb793e484f1317c1af7ddc2`。node-39-101 / Phy0 / visible0 / logical npu:0 / TP1。

原始根：`runs/20261022T132626Z_R2/raw`（相对工作根）。本报告的 `C15_prepare_01/<case>` 均相对此原始根；完整flow表在`profile_analysis_C15/<case>`，本报告目录`profiling_C15/<case>`保留命令和小型片段。

## 采集范围与有效工作量

C6四采集四控制保留为历史，未冒充本轮新采集。本轮预声明三次OFF-long、三次ON-long无profiler控制，再各一次OFF-long/ON-long正常采集及ON-long materialize细分。正常采集无其他本任务模型并发，不启完整Target dump、连续reference、LIFE逐代同步或重型observer。旧OFF的observer_enabled只是driver推导标志；新campaign同时记录provider/recorder实际安装与recorder是否enabled。

所有long请求最大2049tokens，是W1024边界诊断，不是16K/128K矩阵。初始化/capture排除，first smoke请求组预热一次，之后采请求阶段。短长/shape未全预热，缓存沿用，先后顺序和全部重复保留。

|case|requests / output tokens|Draft / Target replay|请求组elapsed ms|初始化 s|最大S列|
|---|---:|---:|---:|---:|---:|
|PERF_OFF_long_01|15 / 240|47 / 30|1613.452|28.49|NOT_AVAILABLE|
|PERF_OFF_long_02|15 / 240|47 / 30|1648.560|28.59|NOT_AVAILABLE|
|PERF_OFF_long_03|15 / 240|47 / 30|1648.347|28.42|NOT_AVAILABLE|
|PERF_ON_long_01|15 / 240|47 / 30|1735.166|28.70|8|
|PERF_ON_long_02|15 / 240|47 / 30|1770.531|28.41|8|
|PERF_ON_long_03|15 / 240|47 / 30|1767.755|28.37|8|
|PROFILE_OFF_long_normal|15 / 240|47 / 30|1757.605|34.07|NOT_AVAILABLE|
|PROFILE_ON_long_materialize|15 / 240|47 / 30|1910.792|28.11|8|
|PROFILE_ON_long_normal|15 / 240|47 / 30|1875.770|28.04|8|

依据：各case `campaign.json:outputs/initialization_seconds/warmup/observer_installation` 与 `profile.json:groups/calls/scope/profile_configuration`；汇总`MRV2_Profiling_Summary.json:cases`，逐组`C15_profile逐请求.csv`。elapsed为非重叠请求组Host区间之和，不含启动/capture，不是kernel duration之和。ON-long运行时descriptor的source_start_column最大8，S=1024tokens，确认实际裁剪；OFF为不适用。Target verification总数与acceptance没有无侵入导出，NOT_AVAILABLE；不能用Graph calls替代它们。active/padded保留Draft descriptor计数，逐步真实active在正常产物中不能完整取得的部分为NOT_AVAILABLE，不由shape猜测。

## 有限重复与旧OFF异常

- OFF: 三次请求组elapsed=[1613.45239, 1648.56041, 1648.34687] ms；median=1648.347 ms，min/max=1613.452/1648.560 ms，样本标准差=20.208 ms。
- ON: 三次请求组elapsed=[1735.16642, 1770.53128, 1767.75462] ms；median=1767.755 ms，min/max=1735.166/1770.531 ms，样本标准差=19.665 ms。

三对请求数、tokens、prompt lengths、Draft/Target replay计数均相同（`paired_descriptive_work[].same_counted_work`）；只有3个进程重复，无法估计分布尾部或隔离缓存/外部负载因果。不挑最快、不报告Window加速率。OFF三次均未复现旧5152.6ms；旧逐组数据在`C6_long逐请求历史统计.csv`：首次32和1024token组约1847/1880ms，末尾32token约80ms；相应旧profile组107/123/87ms。冷shape/缓存/运行顺序是假设，旧控制缺原始Host/kernel trace，不能追认具体编译或算子原因。

本轮Host外部负载采样见`runs/20261022T132626Z_R2/environment/profile_host_load.jsonl`和`profile_host_monitor.json`，从第二个ON控制开始覆盖到所有三组profiling，前三个控制无该项新观测。/proc/loadavg为整机历史负载，ps %CPU为进程平均，不是瞬时kernel忙碌；不能据其单独给旧异常定因。NPU占用由逐case admission和心跳记录。

## materialize细分：主要时间在哪里

|范围|样本|mean ms|p50 ms|p95 ms|
|---|---:|---:|---:|---:|
|outer_ms|47|11.517467|9.220620|37.099460|
|direct_children_union_ms|47|11.189044|8.907320|36.768150|
|unmarked_host_residual_ms|47|0.328423|0.314740|0.429840|
|Draft_materialize_epoch_validate_ms|47|0.341857|0.297850|0.350390|
|Draft_materialize_exact_length_snapshot_ms|47|10.186497|7.940710|35.693000|
|Draft_materialize_runtime_ms|47|0.660690|0.634570|0.853780|

依据：`C15_materialize逐次细分.csv`的call_id/parent_call_id、generation/epoch/request_group；`MRV2_Profiling_Summary.json:materialize_decomposition`。直接子区间取并集；runtime内含workspace/build_inputs，不能把嵌套sum再次加到外层。两次epoch validate在每个outer内合计，样本表47行对应94个实际validate调用。

精确长度快照均值10.1865ms，约占outer均值88.4%；runtime约0.6607ms（其中workspace约0.4392ms、build_inputs约0.1310ms）；未细分Host残余约0.3284ms，包含剩余规划/检查及标记开销，不能全部归到table构造。完整精确长度与原有校验保留，没有用upper_bound替代。

最长Host outer85.9938ms，其中snapshot84.6960ms、runtime0.6668ms，位于Host记录generation47、prompt-length-2049-attempt-9。`C15_snapshot_trace分析.json`同线程包含分析另见47次aten::to/_to_copy/copy_范围；最长copy_约84.589ms，trace内请求组关联由`C15_snapshot_request_group_join.json`独立确认。没有跨Host monotonic与trace时间域相减，也没有靠相邻行赋予代际。

snapshot没有可靠直接flow归属到设备拷贝/等待任务（matched_flow_count=0）。因此它表示阻塞CPU快照调用总时间，可能包含已有设备排队/等待和拷贝，不能全当D2H传输；对之前Target/prefill工作的等待是待证假设。没有据此删除精确快照或加同步。正常路径outer时间也不能直接作为Window净增耗时，因为等待可能在OFF其他位置承担。

## Graph、Host/task/stream/flow关联与四个子范围

|case|materialize p50/p95 ms|metadata p50/p95|UPDATE p50/p95|retire p50/p95|
|---|---:|---:|---:|---:|
|PROFILE_OFF_long_normal|NOT_APPLICABLE|0.4330/0.4624|0.7971/0.8993|NOT_APPLICABLE|
|PROFILE_ON_long_materialize|9.2206/37.0995|0.0835/0.1000|1.0322/1.1832|0.0942/0.1098|
|PROFILE_ON_long_normal|9.1703/37.3133|0.0833/0.0994|1.0030/1.1272|0.0907/0.0986|

依据各profile.json的host_statistics/host_subrange_coverage；ON四范围47次，OFF materialize/retire不适用，不把缺失写成0。Draft/Target有各自Host replay submit及native MODEL_EXECUTE；FIA名称仅区分算子族，不能由同名/shape或数量硬配Target/Draft/真实层。

- PROFILE_OFF_long_normal: flow {'MATCHED': 41365, 'UNMATCHED': 1, 'AMBIGUOUS': 2}；direct replay {'total_replays': 47, 'direct_matched': 0}。
- PROFILE_ON_long_materialize: flow {'MATCHED': 42720, 'UNMATCHED': 1, 'AMBIGUOUS': 1}；direct replay {'total_replays': 47, 'direct_matched': 0}。
- PROFILE_ON_long_normal: flow {'MATCHED': 42722, 'UNMATCHED': 1}；direct replay {'total_replays': 47, 'direct_matched': 0}。

全部三组direct replay flow均0；父REPLAY_PLUS_UPDATE有flow，但不能把UPDATE与replay的设备任务拆分。关联用实际flow key、方向、pid/tid、范围包含及上下文；(device,stream,task)在导出有重复，不能当全局唯一键。完整flow表与小型片段保留，不凭相邻task配代际。

## 拷贝、wait/sync与设备区间

### PROFILE_OFF_long_normal

- acl_memcpy_host_to_device: count=1221, duration sum=5608.860us, median=4.060us。
- Event::synchronize: count=94, duration sum=4100.590us, median=43.165us。
- Event::wait: count=171, duration sum=5655.260us, median=28.200us。
- acl_memcpy_device_to_host: count=141, duration sum=547.880us, median=3.780us。
- EVENT_WAIT: count=171, duration sum=1101269.640us, median=0.020us。
- MODEL_EXECUTE: count=77, duration sum=742.040us, median=3.060us。
- NOTIFY_WAIT: count=77, duration sum=605059.360us, median=3808.780us。
- MEM_WAIT_VALUE: count=3945, duration sum=2190.260us, median=0.140us。
- MEMCPY_ASYNC: count=3771, duration sum=8451.480us, median=2.820us。
- acl_memcpy_device_to_device: NOT_AVAILABLE: no explicit direction label in this export。

命名kernel count=24640，FIA族=1927；duration sum=1325601.020us，区间union=1325601.020us，首尾span=1808073.240us。这是所选kernel集合，非全设备elapsed或空闲率。

### PROFILE_ON_long_materialize

- acl_memcpy_host_to_device: count=1221, duration sum=5616.920us, median=3.910us。
- Event::synchronize: count=94, duration sum=4015.790us, median=41.995us。
- Event::wait: count=171, duration sum=4824.330us, median=27.690us。
- acl_memcpy_device_to_host: count=141, duration sum=541.300us, median=3.650us。
- EVENT_WAIT: count=171, duration sum=1082944.020us, median=0.020us。
- MODEL_EXECUTE: count=77, duration sum=816.960us, median=3.060us。
- NOTIFY_WAIT: count=77, duration sum=616846.800us, median=4083.360us。
- MEM_WAIT_VALUE: count=3945, duration sum=2185.040us, median=0.140us。
- MEMCPY_ASYNC: count=4081, duration sum=8637.260us, median=2.800us。
- acl_memcpy_device_to_device: NOT_AVAILABLE: no explicit direction label in this export。

命名kernel count=24781，FIA族=1927；duration sum=1324126.340us，区间union=1324126.340us，首尾span=1949404.720us。这是所选kernel集合，非全设备elapsed或空闲率。

### PROFILE_ON_long_normal

- acl_memcpy_host_to_device: count=1221, duration sum=5638.420us, median=4.040us。
- Event::synchronize: count=94, duration sum=4068.140us, median=42.645us。
- Event::wait: count=171, duration sum=4845.260us, median=27.960us。
- acl_memcpy_device_to_host: count=141, duration sum=562.500us, median=3.830us。
- EVENT_WAIT: count=171, duration sum=1107044.880us, median=0.020us。
- MODEL_EXECUTE: count=77, duration sum=839.180us, median=3.080us。
- NOTIFY_WAIT: count=77, duration sum=616776.120us, median=4044.960us。
- MEM_WAIT_VALUE: count=3945, duration sum=2191.660us, median=0.140us。
- MEMCPY_ASYNC: count=4081, duration sum=8699.460us, median=2.820us。
- acl_memcpy_device_to_device: NOT_AVAILABLE: no explicit direction label in this export。

命名kernel count=24781，FIA族=1927；duration sum=1326899.320us，区间union=1326899.320us，首尾span=1909654.920us。这是所选kernel集合，非全设备elapsed或空闲率。

依据：各trace_view.json的显式API标签与task_time.csv的stream/task/start/stop；字段索引和统计在Summary cases.trace。D2D没有显式方向标签时NOT_AVAILABLE，不能填0；不同类别等待/同步可能嵌套或跨流重叠，sum不等于总停顿。命名kernel之间的空隙不等于整设备idle。跨stream重叠收益和完整Host下发瓶颈的因果量化缺完备时钟/任务归属，NOT_AVAILABLE。

## 采集开销、诊断与验收边界

正常ON-long1875.770ms、materialize标记ON-long1910.792ms；仅各一次，差约35ms，包含run-to-run波动，不单独归因为标记成本。正常采集与六控制均不含串行数值reference/LIFE同步。配对short normal/control与PROFILE_LIFE诊断仅按预声明有限补充方案执行，若尚未产出则NOT_RUN；不能将不同long/short总耗时相除。

初始化/capture已排除；请求组含prefill+decode，完整device逐阶段拆分为NOT_AVAILABLE。Host的Graph范围主要覆盖decode，不能把其数量等同全部Target验证。无layer/task直接映射的每层指标为NOT_AVAILABLE。

正常UPDATE代际、最后consumer/backing复用、task内完整operand绑定、physical read均未因采集成功而通过。C15成功LIFE后另有15个native FIA task地址字与匹配安装kernel资料，见C15_native_FIA参数字分析.json及平台问题单.md；那是额外串行诊断产物，不是本正常trace的物理访问证明。public Graph Gate保持冻结。

## C17短请求正常/诊断对照（本轮新采集）

源码C17 `057b8e0300967e68e3f2a78c5910c8877521674e`，同一Phy0 TP1。逐次原件`C17_prepare_02/<case>`；两个profile的完整flow表`profile_analysis_C17/<case>/flow-analysis-module.json`，小型典型片段`profiling_C17/<case>`。C17 native参数导出失败不影响这些独立profile；本组三个case的runner/profile-joint均接受。

|case|scope|requests/tokens|Draft/Target replay|elapsed ms|初始化 s|
|---|---|---:|---:|---:|---:|
|PROFILE_ON_short_control|NORMAL_OBSERVER_OFF|7/112|21/12|669.664|31.980|
|PROFILE_ON_short_normal|NORMAL_OBSERVER_OFF|7/112|21/12|763.094|28.652|
|PROFILE_LIFE|DIAGNOSTIC_SERIALIZED|7/112|21/12|29929.465|27.762|

外部有效工作量逐项一致性：`{'completed_requests': True, 'generated_tokens': True, 'prompt_token_lengths': True, 'observed_draft_graph_replays': True, 'observed_target_graph_replays': True}`，字段来自campaign.outputs/profile.calls，非shape猜测。仅各一次短对照，没有足够样本作置信区间或加速率；不与long总时间相除。

### 显式拷贝/同步标签

|标签|normal count / summed us|LIFE count / summed us|
|---|---:|---:|
|EVENT_WAIT|75 / 212689.980|75 / 198136.120|
|Event::synchronize|42 / 1850.640|84 / 4021.570|
|Event::wait|75 / 2255.850|75 / 2258.540|
|MEMCPY_ASYNC|1859 / 3782.640|1859 / 3756.380|
|MEM_WAIT_VALUE|1611 / 904.540|1611 / 1250.040|
|MODEL_EXECUTE|33 / 664.160|33 / 763.840|
|NOTIFY_WAIT|33 / 255075.580|33 / 10663284.840|
|acl_memcpy_device_to_device|NOT_AVAILABLE|NOT_AVAILABLE|
|acl_memcpy_device_to_host|63 / 259.380|63 / 239.980|
|acl_memcpy_host_to_device|513 / 2780.150|513 / 2384.370|

类别sum可能包含嵌套等待/跨流重叠，不能加总为端到端停顿；缺显式方向字段为NOT_AVAILABLE，不填0。LIFE的event/sync/D2H与observer、额外诊断准备一起计入总开销，不能将elapsed差全归给某一种同步。

### Host范围与真实flow

|case|materialize p50/p95 ms|metadata|UPDATE|retire|
|---|---:|---:|---:|---:|
|PROFILE_ON_short_normal|8.059050/9.508830|0.082330/0.091220|1.063050/1.364070|0.093120/0.105500|
|PROFILE_LIFE|3.832420/9.053010|92.926210/160.611470|483.216390/791.751990|0.126680/0.146830|

PROFILE_ON_short_normal flow：`{"path": "/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261022T132626Z_R2/raw/profile_analysis_C17/PROFILE_ON_short_normal/flow-analysis-module.json", "counts": {"MATCHED": 20334, "UNMATCHED": 1, "AMBIGUOUS": 1}, "coverage": {"total_replays": 21, "direct_matched": 0}, "manager_flow_counts": [32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32], "split": "UNRESOLVED: replay and UPDATE device tasks cannot be split from these flows"}`。


PROFILE_LIFE flow：`{"path": "/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261022T132626Z_R2/raw/profile_analysis_C17/PROFILE_LIFE/flow-analysis-module.json", "counts": {"MATCHED": 20504, "UNMATCHED": 1}, "coverage": {"total_replays": 21, "direct_matched": 21}, "manager_flow_counts": [38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38], "split": "UNRESOLVED: replay and UPDATE device tasks cannot be split from these flows"}`。


正常ON provider/recorder实际安装与enabled字段在Summary.diagnostic_comparison_C17.cases[].observer_installation；LIFE属于DIAGNOSTIC_SERIALIZED，不能作为正常无额外同步路径。二者初始化/capture与请求区间分别保存；设备prefill/decode的完整拆分、acceptance、全部Target verification数仍NOT_AVAILABLE。

该对照回答诊断观察的总时序影响，没有关闭正常UPDATE生效代际/backing最后consumer、task执行operand或KV physical-read。Native dump内部参数块D2H与本PROFILE_LIFE是不同开关，不能凭D2H标签把它们当作同一种证据。

### LIFE中“direct flow”必须按实际目的地细分

原committed解析器coverage.direct_matched只统计Host Draft_REPLAY_SUBMIT范围内任一显式flow。LIFE该原始指标21/21，而normal0/21；逐条复查63条目的地，42条是destroy/record event的Host队列，21条是设备EVENT_RECORD，**没有一条目的地MODEL_EXECUTE**。因此本轮没有获得21条replay→模型执行直接边。原解析结果不覆盖，新分类原件为`C17_direct_flow_实际目的地分类.json`（含原event indices、flow key、目的地真实名称/args）。不能将诊断事件误写为Graph执行绑定；正常源代际、task operand和physical read仍未因此关闭。

正常和LIFE中Event::synchronize显式调用分别42/84次；LIFE增加42次，与21代每代两个普通event drain一致。API自身sum约1.85/4.02ms，不能解释29.9s全部差异；device NOTIFY_WAIT的sum约255ms/10663ms，有跨流重叠且可能等待Host下发，不能加总为elapsed或将其当作单一根因。

LIFE启用了heavy recorder，而normal仅安装但recorder_enabled=false。源码还有`_append_lifecycle→write_artifact→snapshot/json.dumps/write_text`逐层Host工作和LIFE `_flush`，这些不在正常observer-off路径。本轮没有单独测量其CPU序列化/I/O时间，故只报告诊断总开销，不将差值全归给同步、D2H或某个算子。三个short样本仅各一次，不能估计尾分位数或稳定比率。

Summary补充whole_request_elapsed_per_observed_draft_replay_ms用于相同外部工作量的描述；它含Target/prefill等全部工作，不是Draft kernel延迟。每层device归属、全部verification和acceptance为NOT_AVAILABLE。

## 可导出的统计图

[有限重复与materialize逐次范围](Profiling_C15有限重复与materialize.svg)（另有PNG）：保留全部三次控制和47个Host样本，不将嵌套区间相加。

[正常与LIFE诊断短请求对照](Profiling_C17正常与LIFE诊断.svg)（另有PNG）：纵轴为对数、三模式各一次，仅描述同外部工作量下的总时序，不能归为同步单因或正常Window加速率。

生成脚本plot_profiling_summary.py只读本报告Summary和CSV、CPU绘图，不运行模型；图不是原始trace的替代。
