# 生命周期与 production 收尾（Repair7）

未改功能顺序，以下以本次最终源码与 pinned vLLM 为准。

|阶段|owner / stream / 证据|仍缺事实|
|---|---|---|
|物化与 backing copy|P3/P6 provider 持有 persistent table/length；current stream；draft_window_graph.bind_read_carrier|不是完成事件|
|metadata bind|canonical Full write/query 与 Window read 分开；typed carrier 同代|设备真实 task operand 仍未暴露|
|replay|dflash/aclgraph.run_fullgraph：update_stream.wait_stream(current) 在 replay 之前；super 返回 None|wait覆盖此前copy，不等于覆盖随后replay|
|UPDATE|attention_v1.update_graph_params：update_begin→FIA.out→update_end→ExternalEvent.record，update stream|当前CANN/torch_npu对N/N+1生效语义须维护者确认|
|consumer|captured Draft attention 等待/重置 ExternalEvent；sampling消费其输出|最后读者/异步task归属不能仅凭Host回调认定|
|retire|proposal_scope finally / P3 Host lease；不是设备 fence|Target输出copy event在Draft之前，不能充当Draft完成|
|next copy/reuse|同current stream FIFO是候选依赖，需证明外部task/UPDATE语义闭环|正常重叠复用UNPROVEN|

NUMERIC为每样本诊断drain；NORMAL_ORDER保留顺序，有额外有界token copy及末尾drain；LIFE每代串行。三者不能互相替代。
本轮没有证据证明必须前移UPDATE/双缓冲/全局同步，也没有宣称现状无race。

## 生产收尾映射

- 已有：private read backing、严格canonical write identity、实验provider、capture/update绑定、同代Host状态、public fail-closed。
- 本轮修复：严格Ascend配置合法诊断键和false解析；没有新增正常路径device操作。
- 仍需：当前版本task update生效代际、最后consumer覆盖、异常部分提交后正式quarantine/reuse语义；目前仅诊断子进程退出。
- 正式provider安装、公开配置路线承诺、fallback禁用/异常隔离、正常生命周期证明和A3回归仍未完成；不能将实验路径升级生产支持。
- TP16/Prefix/Eagle3/DSA/Async等Batch A仍排除。

## 平台与验收owner问题

固定服务器栈报告 CANN9.1 / torch_npu2.10.0.post4（下轮重新读取实际版本）。请维护者给出graph_task_update_begin/end、ExternalEvent wait/reset/record跨replay的版本契约，确认UPDATE(N)作用的任务及完成边界、update stream是否最后读backing。需要API源码/版本说明或可区分设备实验，不接受Python return代替。
physical read/task内部地址现接口不足：CAPABILITY_GAP / ACCEPTANCE_DECISION_REQUIRED。可提出连续数值+窗外非干扰+版本契约作为替代证据供owner决策，但本轮不降低Frozen标准、不解冻Gate。
