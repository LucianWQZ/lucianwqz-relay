# MRV2 正常路径 Profiling 分析

源码：C6 `1c920c3669b76f301ff9472650ceb0e842ccf03c`，TP1，node-39-101 / Phy0 / logical npu:0。C7–C10仅改检查器与测试，以下仍是C6采集，不能合并成新SHA的设备PASS。

原始根：`/mnt/wenqing/mrv2_graph_server_dev/20261022T0640Z_C2_recovery`。以下 `C6_prepare_04b/...` 均相对此根；报告脚本和联合检查路径可据此复查。

## 采集和有效工作量

已完成 OFF/ON × short/long 四个正常采集和四个无profiler控制。全部初始化/capture与warmup在采集前；采集覆盖有界请求阶段。使用当前torch_npu.profiler，不叠加msprof、不改业务is_profile；record_shapes/stack/memory关闭。重型observer、完整Target dump、连续数值reference、逐代LIFE同步关闭。每组仅一次campaign，不能作统计显著性或加速承诺。

| case | requests / generated tokens | Draft / Target Graph calls | request groups elapsed ms | runtime最大S列 |
|---|---:|---:|---:|---:|
| PROFILE_OFF_long_control | 15 / 240 | 47 / 30 | 5152.612 | NOT_AVAILABLE |
| PROFILE_OFF_long_normal | 15 / 240 | 47 / 30 | 1712.817 | NOT_AVAILABLE |
| PROFILE_OFF_short_control | 7 / 112 | 21 / 12 | 592.406 | NOT_AVAILABLE |
| PROFILE_OFF_short_normal | 7 / 112 | 21 / 12 | 684.611 | NOT_AVAILABLE |
| PROFILE_ON_long_control | 15 / 240 | 47 / 30 | 1743.273 | 8 |
| PROFILE_ON_long_normal | 15 / 240 | 47 / 30 | 1906.630 | 8 |
| PROFILE_ON_short_control | 7 / 112 | 21 / 12 | 652.946 | 0 |
| PROFILE_ON_short_normal | 7 / 112 | 21 / 12 | 789.341 | 0 |

证据：每个case的 `campaign.json:outputs/initialization_seconds/warmup` 与 `profile.json:groups/calls/profiler_enabled/profile_configuration`；汇总对应 `MRV2_Profiling_Summary.json:cases`。elapsed为各独立请求组Host区间之和，不含初始化；kernel duration另算，不混为端到端。short有3个active请求组，long另含边界长度请求；详细prompt token长度、group label和时间均在汇总，不凭文本字符数估算context。

ON-long `profile.json:calls[].window_descriptors[].source_start_column` 最大8，对应S=1024 token，直接确认发生真实Window裁剪；short最大0。descriptor是已有不可变Host状态，无额外D2H或设备query。OFF没有Window descriptor，标NOT_AVAILABLE/不适用。Target verification总数和acceptance未导出，均为NOT_AVAILABLE，不能拿Target Graph calls替代所有验证。

## A–C：Graph、FIA 与 Host/task/stream 关联

正常Graph replay有实际 `Draft_REPLAY_SUBMIT`/`Target_REPLAY_SUBMIT` Host范围及native MODEL_EXECUTE导出。short各21次Draft/12次Target，long各47/30。Host Target/Draft范围可区分，FIA名称只识别算子族，不能凭同名、shape或数量关联真实层/代际。

完整flow解析使用固定C6 `python -m tools.p7x_graph_repair6_trace`，避免直接脚本触发stdlib bisect影子模块问题。实际命令/退出码见 `profiling_C6_short/<case>/parser_execution.json`，典型片段见同目录 `typical_replay_fragment.json`。完整flow表留服务器，不进小包。

- `PROFILE_OFF_long_normal`：flow {'MATCHED': 41365, 'UNMATCHED': 1, 'AMBIGUOUS': 2}；{'total_replays': 47, 'direct_matched': 0}；task rows=46584，FIA命名kernel=1927。证据 `C6_prepare_04b/PROFILE_OFF_long_normal/trace/.../task_time.csv`、上述完整flow表。
- `PROFILE_OFF_short_normal`：flow {'MATCHED': 19685, 'UNMATCHED': 1}；{'total_replays': 21, 'direct_matched': 0}；task rows=20052，FIA命名kernel=861。证据 `C6_prepare_04b/PROFILE_OFF_short_normal/trace/.../task_time.csv`、上述完整flow表。
- `PROFILE_ON_long_normal`：flow {'MATCHED': 42718, 'UNMATCHED': 1, 'AMBIGUOUS': 2}；{'total_replays': 47, 'direct_matched': 0}；task rows=47035，FIA命名kernel=1927。证据 `C6_prepare_04b/PROFILE_ON_long_normal/trace/.../task_time.csv`、上述完整flow表。
- `PROFILE_ON_short_normal`：flow {'MATCHED': 20336, 'UNMATCHED': 1}；{'total_replays': 21, 'direct_matched': 0}；task rows=20269，FIA命名kernel=861。证据 `C6_prepare_04b/PROFILE_ON_short_normal/trace/.../task_time.csv`、上述完整flow表。

直接replay flow关联数为0；父 replay+UPDATE 范围有关联，但无法将二者device task拆开，因此UPDATE生效代际、最后consumer仍UNRESOLVED。关联依据flow ID及其方向、pid/tid、范围包含关系；不以相邻行为证据。task表的(Device_id,stream_id,task_id)有重复，必须带时间与模型上下文，不能单独当全局唯一键。Host monotonic_ns与trace导出时间域不直接相减。

## D：四个Host子范围

| case | materialize p50/p95 ms | metadata p50/p95 | UPDATE p50/p95 | retire p50/p95 |
|---|---:|---:|---:|---:|
| PROFILE_OFF_long_normal | NOT_APPLICABLE | 0.4210/0.5042 | 0.7446/0.8813 | NOT_APPLICABLE |
| PROFILE_OFF_short_normal | NOT_APPLICABLE | 0.4273/0.4816 | 0.7905/0.9305 | NOT_APPLICABLE |
| PROFILE_ON_long_normal | 9.3332/39.3739 | 0.0829/0.0959 | 0.9906/1.1439 | 0.0848/0.0929 |
| PROFILE_ON_short_normal | 7.6231/9.5274 | 0.0807/0.0942 | 1.0634/1.2259 | 0.0908/0.1172 |

证据：`profile.json:host_statistics/host_subrange_coverage`。ON四范围short各21、long各47，OFF materialize/retire不适用。范围嵌套，不把各sum相加当elapsed。ON-long materialize均值约11.90ms、p50约9.33ms，是明确的Host时间候选；源码 `_snapshot_prepared_draft_seq_lens` 含既有CPU拷贝，但trace同线程包含法未归入该range的copy/sync，当前不能将全部开销归因D2H。保留精确长度校验，不能用upper_bound替代来追求性能。

## E–F：拷贝、等待、设备空档与重叠

### PROFILE_OFF_long_normal

- `acl_memcpy_host_to_device`：count=1221，duration sum=4930.850us，中位数=3.530us。
- `Event::synchronize`：count=94，duration sum=3886.180us，中位数=41.160us。
- `Event::wait`：count=171，duration sum=4518.900us，中位数=26.130us。
- `acl_memcpy_device_to_host`：count=141，duration sum=477.360us，中位数=3.230us。
- `EVENT_WAIT`：count=171，duration sum=1152004.760us，中位数=0.020us。
- `MODEL_EXECUTE`：count=77，duration sum=778.580us，中位数=3.060us。
- `NOTIFY_WAIT`：count=77，duration sum=606414.800us，中位数=3807.200us。
- `MEM_WAIT_VALUE`：count=3945，duration sum=2197.640us，中位数=0.140us。
- `MEMCPY_ASYNC`：count=3771，duration sum=8457.040us，中位数=2.820us。
- `acl_memcpy_device_to_device`：NOT_AVAILABLE: no explicit direction label in this export。

命名kernel sum=1329582.160us；这些kernel区间union=1329582.160us；首尾span=1719237.740us。以上是所选kernel集合的统计，不代表所有设备活动。

### PROFILE_ON_long_normal

- `acl_memcpy_host_to_device`：count=1221，duration sum=5017.380us，中位数=3.500us。
- `Event::synchronize`：count=94，duration sum=3939.470us，中位数=41.635us。
- `Event::wait`：count=171，duration sum=4536.310us，中位数=26.430us。
- `acl_memcpy_device_to_host`：count=141，duration sum=493.840us，中位数=3.430us。
- `EVENT_WAIT`：count=171，duration sum=1130590.560us，中位数=0.020us。
- `MODEL_EXECUTE`：count=77，duration sum=771.820us，中位数=3.060us。
- `NOTIFY_WAIT`：count=77，duration sum=641494.820us，中位数=4069.680us。
- `MEM_WAIT_VALUE`：count=3945，duration sum=2191.460us，中位数=0.140us。
- `MEMCPY_ASYNC`：count=4081，duration sum=8628.160us，中位数=2.800us。
- `acl_memcpy_device_to_device`：NOT_AVAILABLE: no explicit direction label in this export。

命名kernel sum=1325240.400us；这些kernel区间union=1325240.400us；首尾span=1912765.840us。以上是所选kernel集合的统计，不代表所有设备活动。

证据：`trace_view.json`中显式方向label与`task_time.csv`实际start/stop/stream；解析脚本`analyze_profile_campaign.py`。H2D/D2H统计为导出API范围，MEMCPY_ASYNC并非全都能确定方向。显式D2D方向未导出，填NOT_AVAILABLE。wait/sync包含Host与设备不同类别，sum会重叠，不能直接相加成停顿。命名kernel间空隙不等于全设备idle；跨stream数据缺少完备任务语义，设备全空档及重叠效益为NOT_AVAILABLE。

## G–H：可比单位工作与采集影响

- {'window': 'OFF', 'length': 'short', 'status': 'DESCRIPTIVE_SINGLE_CAMPAIGN', 'same_counted_work': True, 'profile_to_control_elapsed_ratio': 1.1556452752052544, 'interpretation': 'Profiler plus run-to-run variability; not an isolated causal estimate'}
- {'window': 'OFF', 'length': 'long', 'status': 'DESCRIPTIVE_SINGLE_CAMPAIGN', 'same_counted_work': True, 'profile_to_control_elapsed_ratio': 0.33241732605554863, 'interpretation': 'Profiler plus run-to-run variability; not an isolated causal estimate'}
- {'window': 'ON', 'length': 'short', 'status': 'DESCRIPTIVE_SINGLE_CAMPAIGN', 'same_counted_work': True, 'profile_to_control_elapsed_ratio': 1.2088904611807834, 'interpretation': 'Profiler plus run-to-run variability; not an isolated causal estimate'}
- {'window': 'ON', 'length': 'long', 'status': 'DESCRIPTIVE_SINGLE_CAMPAIGN', 'same_counted_work': True, 'profile_to_control_elapsed_ratio': 1.0937070432728437, 'interpretation': 'Profiler plus run-to-run variability; not an isolated causal estimate'}

每组requests/tokens/Graph calls计数相同，可展示每generated token的描述性耗时（汇总`per_generated_token_ms`）。但没有acceptance和全部Target verification，不宣称完全相同有效工作。OFF-long控制5152.6ms而采集1712.8ms，明显存在单次运行波动；不能由此称profiler加速，也不能直接作Window加速率。ON-long控制1743.3ms、采集1906.6ms，同样只描述此两次运行。未采用诊断同步trace估计正常性能。初始化/capture、prefill和decode的精确device时间拆分仍NOT_AVAILABLE：目前请求组包含prefill+decode，Host Graph范围主要覆盖decode，缺完整逐阶段device归属。

## I：仍不能证明的事项

1. UPDATE(N)究竟影响哪次replay；父范围flow不能拆分参数更新与执行。
2. backing最后真实device consumer完成、下一代同址覆盖的安全时点。
3. task内部operand地址、KV实际物理read-set；profiler不暴露这些字段。
4. 不同clock domain的精确跨域时差与完整设备idle。

这些缺口已写入DECISION_QUEUE.md，需平台维护者合同或审定native证据方案。本次真实正常采集与分析完成，不代表production Graph正式支持；public Graph Gate保持冻结。
