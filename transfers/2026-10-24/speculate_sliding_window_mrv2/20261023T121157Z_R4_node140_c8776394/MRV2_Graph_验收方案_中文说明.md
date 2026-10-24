# MRV2 Graph 验收方案：中文说明

生成于 2026-10-23T18:59:55.479402+00:00，同一 R4（node-25-140），截止仍为 2026-10-23 22:11:57 UTC。
**这是供网页 GPT 独立技术评审的方案，不是已获批准的替代验收；没有补齐的直接设备证据仍未补齐，public Graph Gate 仍冻结。**

## 先说当前事实

当前源码 C32：`45cd0e0296cd0ff64f30cc75d3e8a37805b8a71c`，tree `fc4d682b4aad954c9aee7b2d0755636801537ec6`。Python3.11.10、torch2.10.0、torch_npu2.10.0.post4、CANN9.1；vLLM pin `84030bbe3d74d99bad477a3d2e37a973ccd8865c`。拟先闭环的阶段是 Qwen3-8B + dspark_qwen3_8b_block7、K7、sample_from_anchor=true、W1024、block128、TP1、Target4 [7,14,28,32]。它不代表整体 MRV2 Graph 范围完成。

140 上 C29 已通过真实CONFIG、A0、预期GRAPH_FROZEN的A1、C2、B0、三代数值前哨。C30 的8K长请求首次暴露两个真实问题：NFS编译临时目录失败；continuing-prefill不创建Window generation，却仍被分派到Window Graph。C32已修后者，使用本机临时目录重验中。本包准确快照见 `acceptance_review/evidence/SNAPSHOT_IDENTITY.json`，不把运行中或旧候选结果写成C32通过。

## 1. 还担心什么，用户会看到什么

|具体错误|用户可能看到的后果|已有证据|仍没有排除的部分|
|---|---|---|---|
|本次replay拿到上一次或下一次UPDATE参数|输出错误、接受率异常、不同请求之间偶发串用|现有单update流/ExternalEvent顺序；真实三代A/B/A′连续输出可区分|每次设备实际执行的参数版本缺直接occurrence关联；源码与安装分支适用性需核实|
|下一代覆盖仍被上一代设备读取的backing|偶发数值不一致、请求失败，可能只在重叠/长请求出现|capture附加流合流、RI完成边与current FIFO的源码推导；生命周期/quarantine测试|正常路径不是逐代drain证明；需要确认真实安装分支覆盖最后相关consumer|
|最终导出的参数看似正确，但某次执行用了其他地址/旧长度|末值dump与greedy输出可能都“正常”，实际某代仍错|C19历史15个native参数块的逐层绑定；C29实际operator-boundary/数值证据|native dump是post-drain末值，不能一一配给真实执行实例；合成ts/dur不是时间线|
|窗口数学、当前精确长度、Target或Full写语义被污染|长上下文质量下降、Target验证错误、请求替换后错误|独立Window数学、完整层/输入/KV前态检查、Graph/eager独立调用、Target双臂历史数据|本包小样本不能重执行完整模型；C32 phase变更要用其自己的新设备证据覆盖|
|设备读了窗口外KV，但数学/输出没有变化|可能主要表现为内存带宽或性能不符合预期；是否违反产品语义取决于实际约定|有效长度/原生绑定、输出与ABA、性能各有独立证据|这些都不能直接证明硬件实际地址read-set；也不能把“读了但未使用”与语义错误混为一谈|

## 2. 必须保证的正确性，与证明方式

必须保证：Window只改Draft读视图；Target、绝对positions、Full table和slot_mapping不变；精确长度属于本代；不覆盖在读backing；异常提交不安全恢复。这些来自当前用户明确要求及原始设计不变式。

“实际地址read-set oracle”“逐次执行operand绑定”“LIFE逐代同步”等是设计/诊断材料中提出的取证或验收路径。原件确实要求这些证据，但本轮**未找到具名维护者签字或团队制度文件，不能把历史Agent编写的方案伪称不可修改的团队政策**。也不能据此由执行Agent自行删掉它们。来源分类与原文见证据表和 `REQUIREMENT_EXCERPTS.json`。当前用户明确没有豁免这些要求。

## 3. 建议提交评审的方案（尚未批准）

1. 正常UPDATE/backing：审查真实生产顺序与匹配版本的Runtime/torch_npu/op-plugin源码。只有安装适用前提成立时，接受有边界的工程合同推导。没有找到反例时，不无休止重复相同末值dump。
2. 数值/Target/异常：保留独立计算调用、同Window与相同KV前态、ABA区分、完整层、原始张量/外部执行关联。新production变更重验相关路径；诊断串行证据单独标注。
3. 执行operand：请平台维护者说明是否有可安全关联真实launch occurrence/参数版本的接口。没有该能力时，报告仍OPEN；可供评审的替代是源码合同+原生绑定+可区分多代输出，**不改名为直接实测**。
4. physical read-set：首先确认产品真正要求的是数学可见集、原生有效参数，还是硬件确切读取地址集合。如果要求最后一项，现有工具证据不足，需要平台能力或明确修改验收方式的决定。窗口外反事实不影响输出只能支持语义非干扰，不能证明没有读取。
5. 性能与接受率另行判断，不能拿来替代正确性。3臂同机、同Target策略、明确工作量/预热，保存全部有限重复；没有既定阈值时提出建议，不自行宣布达标。

## 4. 若评审赞成，仍能/不能承诺什么

可提出的有限承诺：在明确源码、配置、硬件/安装前提内，代码依赖链有依据，已覆盖设备数值、请求和异常场景成立。不能承诺所有方法/拓扑已适配，不能宣称每次operand或physical read-set已直接观察，也不能从LIFE同步通过推导正常无额外同步安全。

平台维护者（具体负责人待确认）应确认安装分支与API保证，或提供更直接的执行证据能力。项目验收/产品负责人（具体负责人待确认，用户可协助指定）应确认最终范围、性能阈值及证明方式是否充分。网页GPT仅提供独立技术意见，不能代替这些决定。

## 5. 包里怎样复查

- `source_C32/`：实际源码与专用checker；`reports/C32_changes.diff`和失败/成功Host日志。
- `raw_records/`：C29实际worker加载库、B0 joint，C30真实8K失败与launcher。
- `C29_sentinel/`：完整小型样本JSON、六份原始BF16输出、精确转成FP32的阅读副本、manifest/launcher/joint。运行 `recompute_outputs.py` 可复算有限值、Graph/reference相等与ABA；**不能离线重建完整KV和模型计算**。
- `platform_sources/`：相关Runtime9.1、torch_npu、op-plugin原件与出处/commit/hash。140实际worker映射证据与安装身份另列；同版本不等于二进制所有分支已证明。
- `requirement_sources/`：原始Frozen Design和Graph分析原件，供核查是正确性不变式、API条件还是历史诊断方法。

研发仍继续，本包完成不代表Graph适配完成或发布条件已满足。
