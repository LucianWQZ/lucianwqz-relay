# Repair6 Platform Semantics And Release Gaps

- source: `fd0716c59562f64262672de12e4ae26259908d0b` / tree `125b29bcb8fe501d69b53e185f9ec89075528310`
- pinned vLLM: `84030bbe3d74d99bad477a3d2e37a973ccd8865c`
- node: `node-39-101`; CANN 9.1.0; torch_npu 2.10.0.post4
- public Graph gate: `STILL_FROZEN`

本文件把需要平台/验收 owner 回答的问题与本地可修问题分开。没有把源码阅读、名称相似或末尾 drain 当成设备合同。

## 1. UPDATE(N) 的生效对象与代际语义

**当前证据**：`Normal_Lifecycle_Source_Audit.md` 与 `attention_v1.py` 显示 `update_stream` 上的 UPDATE begin/FIA.out/end/event.record 使用本代 metadata；`dflash/aclgraph.py` 在 replay 前 record `update_stream.wait_stream(current)`。

**未证明**：UPDATE(N) 是对正在提交/等待的 replay N 生效，还是只对后续 replay N+1 生效；没有 CANN/torch_npu 版本对应的 task-update 语义文档或设备 trace 能唯一证明。

**结论**：`NORMAL_UPDATE_GENERATION = UNPROVEN`。需要平台维护者给出该版本 `graph_task_update_begin/end` 的生效代际定义；本轮 NUMERIC_TARGET4 又因配置校验未执行，不能提供 current/previous reference 区分。

## 2. captured ExternalEvent 的 wait/reset/record 与重用 epoch

**当前证据**：`attention_v1.py::full_graph_fia` 有 capture stream 的 ExternalEvent wait/reset 路径；LIFE/ABORT 源码检查未发现 `ExternalEvent.query()` 被恢复到 production 热路径。

**未证明**：多次 replay 时 ExternalEvent 的 record/reset 与 mapping epoch 的复用合同；进程退出/普通 event 记录不是 device completion。

**结论**：`NORMAL_PATH_REUSE = UNPROVEN`。需要平台确认 event 的 epoch/重用语义，不能通过 Host 记录或末尾 synchronize 推导每次 overwrite 安全。

## 3. Window backing 最后读取者与下代 copy_ 的 happens-before

**当前证据**：源码审计认为最后 Window 读取者是 Draft attention 任务，位于 current stream；下代 `bind_read_carrier` copy_ 仍在 current stream。Target AsyncOutput copy_event 在 Draft propose 前创建/record，只覆盖 Target 采样输出，不能直接覆盖 Draft 完成。

**未证明**：跨 update stream 的 UPDATE 与本代 backing 消费之间的 HB；CANN `graph replay` task 所属 stream 的实际映射；普通非 structured-output 路径没有 Draft D2H fence 时的设备完成。

**结论**：只能保留“普通流 FIFO 候选链”，不能升级成设备级 reuse proof。需要平台提供 task/stream/flow 证据或明确合同。

## 4. UPDATE 是否继续访问 backing，何时消费结束

**当前证据**：UPDATE 使用 `update_full_graph_params` 更新 FIA 参数；有 update event 记录。

**未证明**：UPDATE 是否会在 GPU/NPU 上继续读取/写入本代 backing，以及哪个事件/合同证明其消费结束。Host event.record 不是完成证明。

**结论**：`UPDATE effective generation = UNPROVEN`；不能用末尾 drain 反推每代 overwrite 安全。

## 5. task handle 到 operand descriptor 的接口

**当前状态**：`CAPABILITY_GAP`。现有 Python 边界可记录 table/length 指针，但没有 task handle → 实际 operand descriptor 的可用接口。

**影响**：G1 task-internal 不能从现有 trace 关闭；不能把 Python 指针当 task binding。

**建议**：由平台维护者提供实际 task/operand 查询接口；否则验收 owner 必须明确接受较低证据层级。

## 6. physical read-set 接口

**当前状态**：`CAPABILITY_GAP / ACCEPTANCE_DECISION_REQUIRED`。没有 memory-transaction 或 read-set 字段；数值窗外扰动不证明 physical read。

**影响**：G3 physical read 不能关闭；不能用 shape/name/相邻时间硬连。

## 7. 本轮新增的配置契约问题

`NUMERIC_TARGET4` 在模型加载前失败：

```text
pydantic ValidationError: VllmConfig
draft_window_graph_numeric_diagnostic
Unexpected keyword argument
```

- 失败在 `LLM(**config)` 的 `create_engine_config`；
- 没有创建 device engine、没有 sample/chunk、没有数值证据；
- checker 的 `INVALID_EVIDENCE` 是缺失产物的下游结果，不是数值不一致；
- 这是提交配置与 pinned vLLM VllmConfig 的契约问题，换卡不能修复；
- 需要在本地定位 `additional_config` 的传递/解析路径并修复后重新发布；不得在服务器打补丁。

## 8. 设备映射问题

当前容器 visible logical 0 → host NPU4/Chip0/Phy-ID8；用户合法范围 host Phy-ID0–7 不可选。详见 `Device_Reassignment_Report.md`。这阻断：B2/O0/O1/C2/LIFE/ABORT/自然 G4/全部 profiling。

## 9. 平台/验收请求清单

### 需要 CANN/torch_npu 维护者

1. `graph_task_update_begin/end` 在当前 CANN 9.1 + torch_npu post4 的生效代际定义。
2. captured ExternalEvent wait/reset/record 的多 replay epoch/重用合同。
3. graph replay task 的 stream 归属，及跨 update stream 的 happens-before。
4. UPDATE 是否继续访问 backing、消费结束的可观测事件。
5. task handle → operand descriptor 接口。
6. physical read-set / memory transaction 接口或官方替代证据。

### 需要验收 owner

1. G4 是否必须 FULL_TARGET，还是接受 HEAD_ONLY + canonical write。
2. task-internal/physical-read 无法直接观测时，是否接受较低证据层级；若接受，必须写明替代证据。
3. Base `(4,32)` expected OPEN 与 Target4 诊断扩展的产品边界。
4. NUMERIC_TARGET4 配置契约修复后的最小重测矩阵。

## 10. 可以本地修复的部分

1. `additional_config.draft_window_graph_numeric_diagnostic` 到 `VllmConfig` 的配置传递/字段契约。
2. 诊断入口在配置错误时应保留明确的 `CONFIG_INVALID`，不要只在 checker 显示缺失产物。
3. 容器设备映射修正属于平台/容器 owner，不是本地代码。

## 11. 结论

- 本轮不能进入 production Graph 收尾。
- 旧设备段的 TARGET4 12/12 零容差比较是强证据，但它是旧设备、诊断受控、非正常 reuse 证明。
- 设备重映射和 NUMERIC_TARGET4 配置修复完成前，LIFE/ABORT/profiling/自然 G4/ B2 均不能补跑。
- Public Graph Gate 保持冻结；没有降低任何验收标准。
