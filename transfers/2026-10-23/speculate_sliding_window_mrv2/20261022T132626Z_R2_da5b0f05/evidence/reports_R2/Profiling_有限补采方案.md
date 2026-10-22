# 有限补采方案（执行前声明）

候选C15（1e88c8208670518f63043552b530b1ed3e2f2677），TP1 Phy0。C14未执行设备；增加LIFE原生task导出默认关闭能力后沿用同一有限方案。先依赖通过，再按顺序 OFF-long01 / ON-long01 / OFF-long02 / ON-long02 / OFF-long03 / ON-long03，六个新进程、不采集 profiler 的控制；随后 OFF-long normal、ON-long normal、ON-long materialize 三个独立有界采集。所有重复保留，不选最快、不删除慢样本。正常采集不与本任务其他模型并发。

固定combined请求字节、16输出tokens；报告逐组prompt/output tokens和replay。long最大prompt2049，是W1024边界诊断，不称16K/128K吞吐矩阵。只预热first smoke请求一轮，保持旧协议；记录先后和共享缓存状态，不能把首轮冷缓存与后续热缓存差当Window加速。若变化仍大，给出样本数限制，不无限重复。

旧OFF-long控制5152.6ms的主要异常位于首次32token（1847.2ms）及首次1024token（1879.6ms）；同轮末尾32token79.8ms。旧profile对应107.4/122.7/86.8ms。依据是C6 profile.json groups与campaign.json outputs逐字段重算，统计见C6_long逐请求历史统计.csv。可能与shape预热/缓存或外部负载有关，尚未确定具体算子原因。OFF旧observer_enabled=true仅由driver mode推导，实际provider=false且无snapshot；不能单凭该标志否定对照。

materialize补采仅新增Host实例范围与call_id/parent_call_id、proposal context/epoch。精确长度快照保留原CPU copy/可能wait；epoch校验、runtime、workspace、build_inputs单列。外层减直接子区间的并集为未细分Host规划和开销，不能重复相加嵌套耗时或全部归因D2H。无新增同步、D2H、设备query或dispatch改变；instrumentation自身开销单列，仍非task operand/physical read证明。

采集关闭重型observer、完整Target dump、连续reference和LIFE逐代同步。保留原trace/CSV/DB、解析脚本、关联表及缺失指标；N/A不能填0。
