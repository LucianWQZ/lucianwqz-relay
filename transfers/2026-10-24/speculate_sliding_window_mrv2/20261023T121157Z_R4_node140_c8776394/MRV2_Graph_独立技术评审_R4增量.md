# 网页GPT独立技术评审：R4增量

当前本地候选C35 f00e423936c23b0710fc2b5cd367d34ec7736d26/tree5383f503852c3e520bd10442ed7562e1df5a9a04，production tree7f8bd00506f1896233d9d3d1cddbc0c5b68ad1dd与C32/C33/C34完全相同。原V2是明确C32快照，保持原件；此主审查包附V2原内容、新C35代码/diff和新增实际证据，不将旧producer改SHA。

## 请独立核查

1. C32 continuing-prefill phase修复是否严格维持full-read baseline，未造成decode缺桶eager回退或Target/full positions/slot污染；源与红/绿反例齐备。
2. C33完整12数值/ABA与12对Target4，独立参考是否真正另行调用CUDAGraphMode.NONE、从canonical table独立算Window，并核对本代输入、必要KV前态/完整层。相同output blob是内容寻址去重，不能单凭hash判参考独立。共享模型权重/FIA底层仍可能共同失效，边界请指出。
3. C33 LIFE21有额外event、同步、D2H，仅串行诊断。新正常profiling无逐代LIFE同步，direct replay flow仍0，父UPDATE flow是queue/event。不能将它们升级正常执行operand证明。
4. C34两种metadata Python故障实际进入的分支不同：before点内部handler0，store点1；quarantine/lease与Host下一scope拒绝均有actual PID/74/plan/launcher/原件。未知native部分提交没有模拟或恢复。请核查异常后是否仍有设备操作或错误复用、成功路径是否泄漏。
5. C35 DFlash独立K15/Q16三臂锚点均接受；它没有完整方法数值/Target/LIFE，不能从相同greedy输出扩展支持。稳定性30请求/1974Draft replay有真实bucket/S>0与重复性，但不是普遍生命周期证明。
6. 正常A/B合同已有版本匹配的CANN/torch_npu/op-plugin源码推导、FIA vector拷贝、实际runtime_v100加载。140管理board是9382/V1/0xb1/firmware9.0.0.0.205，公开头文件/已保存源码未找到直接注册映射。请判断哪些前提已有足够工程依据，哪些确需平台维护者确认，避免逻辑跳跃与无限新增取证要求。
7. physical-read/task occurrence各要求的来源，区分用户明确保留的正确性与历史Agent提出的某一种证明方式。负责人未明确时写待确认。替代证据方案尚未批准，网页GPT意见也不是设备PASS或正式发布批准。
8. 性能短/8K Window ON回退，Graph相同Window有有限收益；接受率真实CPU计数，短/长合成与自然文本差异明显。请审查统计/工作量/观测开销、提出可执行优化与产品阈值建议，不将测过改成达标。

## 附件可复算性

C33_output_samples原BF16/input样本和标准库recompute脚本可离线运行；完整模型/KV前后态需服务器。execution为实际小原件/launcher/plan/joint，profiling_excerpt含真实ID/flow和Host区间。超过大小上限的稳定性profile提供明确excerpt及原件bytes/hash，不能将excerpt当完整artifact运行原checker。大raw路径索引是补充，关键代码、失败反例和原始小样本已附，非只给不可访问路径。

最终完整Graph产品范围仍未完成，public Gate FROZEN，不自动push/合并。请给独立技术意见、可反驳的问题清单和最小补证方法，不代替正式发布授权。
