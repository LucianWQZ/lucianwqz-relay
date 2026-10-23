# MRV2 Graph R3持续开发阶段总结

## 起点和结论

从已核验C19接续，新任务开始2026-10-22T19:34:42+00:00，原十小时截止2026-10-23T05:34:42+00:00，没有重置。设备工作于2026-10-23T01:06:49.327017+00:00安全收尾；本报告生成2026-10-23T01:16:11.042141+00:00，截至报告已用约5.69小时；交付完成时间见下载清单。明确PR避让2小时30分钟，期间有重叠Host工作；未为占满十小时重复采集。

最终候选C28：`c877639472386aedeb7df11f15b6bf75c078261c`，tree `729a2d3bc76ac814d1555cb4a457b513bb0b413f`。开发源码/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/work/vllm-ascend；固定运行源码/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/C28_graph_failure/vllm-ascend。vLLM pin84030bbe3d74d99bad477a3d2e37a973ccd8865c/tree f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee不变。R3新增9个本地DCO提交，无push/merge/远端发布；public Graph Gate冻结。

## 做了什么、为什么

1. 匹配版本源码完成A/B合同推导：capture附加流尾notify合流、RI endGraphNotify/current FIFO、单update流/ExternalEvent协议与FIA长度vector拥有拷贝。状态SOURCE_SUPPORTED_CONTRACT，维护者审查安装适用前提；不笼统称没有平台API证据，也不声称真实operand/read-set已取得。
2. 发现实际production早期异常缺口：typed inputs形成前materialize失败旧方法两次清零且未阻止下一scope；metadata发布内部abort也提前清理。C25让Graph失败保留贯穿lease，并保护外层早期scope；eager默认与正常成功copy/stream/replay/UPDATE顺序不改。C28继承。旧反例保留，162项受影响Host检查通过，11项flow/warmup检查有重叠不相加；Ruff0.14对17个改动Python文件通过，非全仓CI。原C19 pinned AST守卫失败、C27 lint错误说明均保留并精确修正。
3. 用真实模型验证新早期table-copy展开：quarantine/lease保留、下次Host guard拒绝、故障后无clear/replay、受控74退出；再重验4个原Python展开。metadata发布异常有Host反例，未单独新设NPU故障点。未知native部分提交没有安全模拟，不清零/恢复/再用可疑backing。
4. 预热所有请求组，独立2049/3072请求，有限交错控制；normal 2份和实验counter 2份profile。CPU counter原型37代精确等价通过，但三次控制中位仅约0.59%差异，未建立稳定收益；生产默认长度路径保留。snapshot等待包含前序工作，OFF metadata亦承受类似等待，不能都叫拷贝成本。

## 实际设备与数值结果

本轮只用node-39-101 Phy0（PCI9D:00.0，进程逻辑npu:0，TP1）。正式模型进程启动30：24正常完成、1预期GRAPH_FROZEN拒绝、5受控Python隔离；非预期模型失败0。另私有C2 fixture1、probe2、profile4（profile已包含在模型计数，不能再加）。33个runner case全部按各自专用checker限定接受。

C28同SHA：P0/真实CONFIG/A0/A1/B0、private C2、3样本前哨、完整12连续数值/ABA、Target4双臂12对、LIFE21代、早期materialize及原4个Python异常展开。input_ids=int32、positions=int64、DSpark noncausal、active3/padded4 offsets/FIA query合同原样保留，容差不放宽。Target比较范围CONTROLLED_DECODE_SYNTHETIC_PRE_KV，ON臂带串行连续参考；不升级为所有自然请求全面支持。

C19原15个post-drain原生参数绑定和4个ABORT保留旧SHA范围，按未改变路径引用，未冒充C28新NPU。Base缺Target(4,32)仍是已知范围，拟送审Target4独立profile[7,14,28,32]。不扩大到Eagle3/DFlash/TP16/Prefix/Async。

## 性能与边界

Base新固定工作负载OFF/ON三次控制中位1121.70/1169.67ms，ON约高4.28%，未显示加速。两臂9请求144输出，内部Host replay工作量不同；旧约2K数据不混算。Target4 counter LEGACY/REUSE中位1276.91/1269.37ms，小差异小于重复极差。profile里snapshot均值13.943→12.758ms，workspace0.461→0.791ms，materialize15.250→14.366ms；部分等待转移，不能凭子范围缩短宣称端到端收益。

四新trace未给generation-bound execution flow。FIA算子族、Host Target/Draft、事件/任务/流分层呈现；native参数末值的合成ts/dur不作真实时间线。正常UPDATE/backing是有版本依据的工程合同，仍需平台适用性审阅；physical-read/task execution operand的既定验收门槛由owner裁决，不能以numeric/exit0/profile成功替代。

## 当前可交付范围和下一步

代码、限定证据、失败反例与恢复材料已可提交正式审查；公开发布仍受平台适用性、原物理证据/验收范围及产品配置入口约束，Gate不解冻。下一步无需重复本套campaign：平台维护者审A/B具体前提；验收owner选择既定read-set路线/提供能力；产品owner审Target4范围与Base拒绝策略。若与非Graph PR集成，先冻结其接口/pin后建独立候选，按diff做最小重验，不直接cherry-pick变化中的PR。

当前NPU实验已结束，所有本任务进程和租约已审计释放。原始根/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261022T193442Z_R3/raw；大tensor/trace保留服务器。review含约400KiB真实数值片段，可用标准库独立复算输出/小输入；它不是完整KV/joint。Git bundle100834bytes从只含Repair7的新仓真实恢复到C28 SHA/tree。服务器自检不等于用户接收端已校验。
