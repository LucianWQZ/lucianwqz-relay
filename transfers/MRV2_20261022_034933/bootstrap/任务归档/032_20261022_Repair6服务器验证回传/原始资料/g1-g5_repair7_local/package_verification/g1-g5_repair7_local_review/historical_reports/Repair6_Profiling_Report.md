# Repair6 Profiling Report

## 1. 状态

`BLOCKED_DEVICE_MAPPING`

本轮原计划包含 8 个正常/control profiling、PROFILE_ON_long_detailed 和 PROFILE_LIFE。设备资源纠正后：

- 当前容器可见 logical device 0 实际落在 host NPU4/Chip0/Phy-ID8；
- 用户允许的 host Phy-ID 0–7 在当前容器内不可选；
- 所有新的 NPU 模型启动已停止；
- 因此 Repair6 **没有**新的 profiling trace、四个 Host 子 range 或 device 关联数据。

不得用 Repair5 旧 trace 冒充 Repair6 当前 SHA/当前允许设备的 profiling 结果。Repair5 trace 只能作为历史分析参考。

## 2. 旧设备段已完成的非 profiling 证据

旧设备段保留：

- B0：21 generations，132 events、120 operand_events、21 G4、147 lifecycle，Draft `(1,7)/(2,14)/(4,28)` 各 7 次。
- B1：完整 11 组 16-token 输出，joint PASS。
- NORMAL_ORDER：`OBSERVED_NORMAL_ORDER_NOT_REUSE_PROOF`，normal reuse/effective generation 仍 UNPROVEN。
- TARGET4_OFF/ON：12/12 captured complete；TARGET4_COMPARE 12/12 PASS，hidden/logits max_abs=0。
- G4F_OFF/ON：10/10 captured complete；第 11 个 `(4,32)` blocked；G4F_COMPARE 10/10 PASS。

这些不是 profiling。

## 3. 旧 Repair5 Profiling 参考（不得当作 Repair6 结果）

Repair5 已采集的实际 trace 仍保留在：

- `/mnt/wenqing/mrv2_graph_repair5_verify/20261020T144145Z_d0a3fc3d/artifacts/reports/Repair5_Profiling_Summary.json`
- `/mnt/wenqing/mrv2_graph_repair5_verify/20261020T144145Z_d0a3fc3d/artifacts/reports/Repair5_Profiling_Report.md`

历史事实包括：short 21 次 Draft replay、long 47 次；ON long 有 14 个 active `source_start_column>0` descriptor；旧 trace 有 host/native flow 字段，但 target/draft generation 关联、physical read-set、completion 仍不完整。

Repair6 的新增四 Host 子 range（materialize/metadata/UPDATE_CALL/retire_host）没有在新 SHA 上执行，不能声称 installed/count/coverage PASS。

## 4. 必须回答问题的当前答案

| 问题 | 当前答案 |
|---|---|
| A. 实际 replay inventory | 本轮未采；仅旧设备 B0 有 replay 证据 |
| B. 四个新 Host 子 range | 未安装/未采；不得用旧 trace 代替 |
| C. materialize/metadata/UPDATE/retire 成本 | 未采 |
| D. Host API/range 到 device task 的唯一关联 | 未采 |
| E. Target/Draft/FIA 区分 | 未采 |
| F. memcpy/wait/sync | 未采 |
| G. current/update stream 等待/重叠 | 未采 |
| H. 设备空档/下发间隙/重复准备 | 未采 |
| I. OFF/ON 可比差异 | 未采；禁止跨设备配时 |
| J. 仍不能证明的字段 | task operand、physical read-set、UPDATE effective generation、completion owner 仍 OPEN |

## 5. 设备纠正后的执行条件

在容器重新映射 host Phy-ID 0–7 后，按原 profile 计划执行：

- 同一允许设备上成组完成 OFF/ON × short/long × control/normal；
- 每个 normal 先确认 active replay 数量和 descriptor；
- 保存 4 个 Host 子 range 的 installed/method/expected/actual/missing generation；
- detailed 只在 shapes/stack 有明确剩余问题时单独运行；
- PROFILE_LIFE 只在正常 LIFE 后做短诊断；
- 不把不同设备的耗时配对，不用有限 trace 做 release 性能结论。

## 6. 交付限制

- 没有新 trace 可交付；raw 中只有旧设备非 profiling 证据。
- 旧 Repair5 trace 的绝对路径保留在历史参考中，不能改名成 Repair6 结果。
- public Graph Gate 保持 `STILL_FROZEN`。
