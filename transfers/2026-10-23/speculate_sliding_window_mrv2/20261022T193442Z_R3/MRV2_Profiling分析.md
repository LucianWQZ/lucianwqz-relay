# MRV2 R3 Profiling分析

更新时间 2026-10-23T00:33:18.201785+00:00。本轮实际新采集4份（2份正常、2份实验长度来源），未采设备profiler控制12次。全部固定C28 c877639472386aedeb7df11f15b6bf75c078261c；TP1，Phy0/PCI0000:9D:00.0。旧C6/C15/C17 trace分别为历史，不冒充新采集。

## 1. 结果与有限重复

|比较臂|三次未采集控制 ms|中位 ms|
|---|---|---:|
|WINDOW_OFF|1093.05655, 1121.69816, 1127.67033|1121.69816|
|WINDOW_ON|1169.67386, 1164.88487, 1193.23759|1169.67386|
|COUNTER_LEGACY_ON|1282.90082, 1260.00113, 1276.91361|1276.91361|
|COUNTER_REUSE_ON|1271.97134, 1257.74442, 1269.36676|1269.36676|

Base OFF/ON均9请求、144输出tokens，实际最长3072，ON中位高4.277%；该工作负载未显示Window加速。OFF Host Draft/Target replay提交31/20，ON30/19，不能把工作量差异当作每kernel性能。六次输出序列hash一致只作请求核对，不代替连续数值。

Target4 LEGACY/REUSE均12请求192输出，ON独立profile [7,14,28,32]。三次中位REUSE变化-0.591%，差值小于各组三次极差；样本小，未建立稳定端到端收益。保存全部重复，不按最快值挑选。默认production长度路径保留，CPU counter仅默认关闭的工具原型。

精确请求/config hash、每组耗时、实际prompt长度、初始化/capture耗时、全部warmup组、输出hash、Host replay描述符及S>0计划证据，见MRV2_Profiling_Summary.json/cases和R3_实际执行与性能归约.json。Base请求SHA c61948898fa304a418eb600921eea02a1604fe4867f278a7649cd02a092f66d9；Target4 counter请求SHA 8209a74fd590609263535bc641b213577f9792b013241b1bfbafe616a2357dd3。二者及旧2K工作负载独立，不计算新旧总耗时加速率。

## 2. snapshot是什么、等待在哪里

draft_window_eager.py::_snapshot_prepared_draft_seq_lens实际对本代input_buffers.seq_lens[:padded]执行to(cpu,int32,copy=True)，不是日志字符串转换。冻结桶payload最多16bytes。安装匹配torch_npu CopyKernel两条所查阻塞路径先同步当前流前缀再memcpy；因此13ms不可全部称为复制带宽。当前前缀可能含Target与Draft context-KV等已下发工作；没有明确任务flow时不把等待全归某一个kernel。源文件/commit/hash见Summary/historical_R2/exact_copy_source、copy_dispatch_sources。

OFF也在Draft_build_attn_metadata范围出现长aten::copy_：新OFF trace同线程完整包含合计418.995ms；正常ON snapshot包含copy_400.040ms。它们是各自范围的导出记录，不能将嵌套sum重复相加或跨时钟相减。证据raw/profile_analysis_C28_01/summary.json的host_scoped_records及原始事件索引片段。

## 3. 精确CPU复用原型：值正确，等待部分转移

verify保留原D2H，37条真实proposal逐项等价，epoch0–36、ticket1–37，active/padded1/1、2/2、3/4、4/4及三桶。reuse先重算同SHA/config/request外部certificate，等待现有普通counter-copy event，读取当前CPU staging；不拿upper、旧代缓存或同一个输出改名当oracle。该等价验收不是模型输出numeric，也不是normal backing完成。证据C28_CPU精确长度等价_设备摘要.json及raw/C28_prepare_01/COUNTER_LENGTH_VERIFY/counter-joint.json。

|Host范围均值 ms|LEGACY profile|REUSE profile|
|---|---:|---:|
|Draft_materialize_exact_length_snapshot|13.94313|12.75753|
|Draft_materialize_workspace|0.46145|0.79095|
|Draft_materialize_runtime|0.69104|1.02157|
|Draft_materialize|15.25005|14.36586|
|Draft_metadata_bind|0.08408|0.08473|
|Draft_UPDATE_CALL|1.00347|1.00060|
|Draft_retire_host|0.08927|0.09234|

每臂37个active样本；p50/p95及逐call保留原profile.json，不用均值隐藏长尾。REUSE snapshot普通Event::synchronize的同线程导出累计466.501ms，workspace copy_合计由6.785ms增至18.092ms。Source在table D2D前先做valid_num_blocks H2D，后有window length H2D，默认blocking；已有等待不能直接删除。重叠Host准备可能带来小差异，但本组控制仅约0.59%，不足支撑新的production Host缓冲所有权/异步拷贝设计。

counter profile可按同一运行的mapping_epoch、请求group、当前post-Target计数与实际prompt长度做精确CPU状态分组：6条当前计数等于prompt、31条超过prompt。后者snapshot均值7.639ms、materialize9.089ms；前者snapshot均值39.202ms/中位0.202ms，两个长prompt拖高均值。证据C28_counter阶段CPU状态归因.json/rows、statistics。仅为该实验的Host状态分组，不把另一个Legacy实例同shape/epoch硬配，也不作native prefill/decode kernel归因。正常Legacy的native阶段细分仍NOT_AVAILABLE；初始化、全组warmup与活动请求时间分别保留。

## 4. replay、任务、流与拷贝的边界

Host Draft/Target分工由真实包装入口确认；设备FusedInferAttentionScore只能确认算子族，没有可靠flow时不能分配给某层/某代/Target或Draft。四份新trace的any flow、Host queue/event、device event和model execution context direct覆盖均为0；generation-bound execution=NOT_AVAILABLE。原C17 LIFE 21/21是event/queue关联，不能简称执行关联通过。

Counter LEGACY/REUSE导出各19411个KERNEL_*任务，kernel区间并集约1022.926/1023.698ms；不是GPU kernel获得加速。各流及PCIE_DMA_SQE/SDMA_SQE/event/notify记录见Summary/new_trace_analysis。并集正确合并并行区间，kernel duration之和不当作elapsed。可见kernel区间未显示重叠，控制/数据task存在多流；该有限导出不证明所有生产路径没有重叠。kernel-uncovered区间不叫整卡idle，也不能仅凭相邻时间认定Host瓶颈。

Host记录Event::synchronize由74增至111，符合实验每proposal新增普通counter event等待。两臂异步DMA task计数相同；导出未给每条方向，也未唯一暴露同步D2H，所以不能据此计算移除多少实际H2D/D2H/D2D传输。Host明确命名copy记录按名字分别统计，不将不同层记录相加当唯一传输数。缺失指标写NOT_AVAILABLE。

Source C28 p7x_graph_repair6_trace.py采用显式flow ID与同线程区间，原始task/stream/connection_id及典型片段留raw/profile_analysis_C28_01/*-scope-fragments.json；不跨Host monotonic_ns与设备时域相减。新native execution occurrence/operand/read-set没有暴露，不能用最终参数快照或合成ts/dur代替。

## 5. profiler、observer与资源干扰

未采集控制仍保留相同轻量Host wrappers/record_function；采集还开启materialize子范围和torch_npu profiler，额外开销不可等同纯生产基线。业务is_profile未启用，不改变Graph dispatch。counter reuse单独标EXPERIMENTAL_COUNTER_REUSE_NORMAL_DISPATCH_OBSERVER_OFF，原有普通event等待显式披露；正常Legacy关闭完整Target、连续numeric、LIFE逐代同步与native verbose。

OFF observer_enabled=true，但provider_installed=false、recorder_installed=false、recorder_enabled=false；ON provider/recorder已安装而recorder_enabled=false。绑定provider是Graph所需的metadata路径，不等于重型tensor observer执行。Source characterization.py:934传入observer=None，campaign diagnostic_artifacts仅profile，无tensor snapshot。证据各campaign/observer_installation与diagnostic_artifacts；不凭单一布尔宣布旧对照无效。

双方安静确认覆盖实际性能段；外部管理采样36份，仍未关联进程行0、原Host PID已关联但容器PID0的尾部记录1条（保留原行/此前映射，不视为活worker或设备完成）、无法识别查询0，PR声明活跃心跳2。全机粗采样78份、load1范围[19.21, 43.42]；只作干扰上下文，不能排除采样间隙或未记录Host噪声。第一段00:13:19释放，之后仅正确性，不把后段卡窗口当安静性能授权。

## 6. 结论与下一步

本轮关闭snapshot操作/等待位置不清与预热覆盖不明的问题，取得同代CPU精确长度复用的受限可行证据。没有稳定端到端性能收益结论；不新增同步、删除校验、使用upper或扩到16K/128K/TP16。后续若要进入production精确CPU共享，应先与非Graph PR的owned exact/read-view接口建立固定基线集成合同，再决定最小优化及数值/Target验证；不是直接使用其CPU缓存。正常UPDATE/backing工程合同另见MRV2_正常Graph合同审查.md，正式平台适用性与physical-read验收仍由对应owner决定。

服务器原始根：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261022T193442Z_R3/raw。每条结论的case/source/request/config、原trace和分析hash、统计字段见MRV2_Profiling_Summary.json；完整trace/CSV/DB不重复打包，review仅放索引和可复查片段。
