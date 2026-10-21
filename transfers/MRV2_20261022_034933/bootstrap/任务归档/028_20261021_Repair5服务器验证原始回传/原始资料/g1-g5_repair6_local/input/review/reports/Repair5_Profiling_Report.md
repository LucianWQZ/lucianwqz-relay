# Repair5 正常 Graph Profiling 报告

- RUN_ID：`20261020T144145Z_d0a3fc3d`
- source：`d0a3fc3d42d7d97e5e7da3890d2710263a097e63` / tree `2f6b93415ced94fe3f4ba22c518699a023b97511`
- device：`npu:0`（logical die 8）
- profiler：`torch_npu.profiler.profile` 2.10.0.post4；未使用 msprof wrapper，未叠加第二套 profiler
- 结论：`PASS_SCOPED_PROFILING`（正常调度/拷贝/等待字段与 host 统计可用）；`physical_read=OPEN`、`task_internal=OPEN`、`completion=UNPROVEN`

机器摘要：`artifacts/reports/Repair5_Profiling_Summary.json`

## 1. 执行矩阵

8 个正常对照 + 1 个诊断：

| case | profiler | status | active groups | Draft REPLAY | Target REPLAY |
|---|---:|---|---:|---:|---:|
| PROFILE_OFF_short_control | off | GRAPH_REPLAY_OBSERVED | 3 | 21 | 12 |
| PROFILE_OFF_short_normal | on | GRAPH_REPLAY_OBSERVED | 3 | 21 | 12 |
| PROFILE_OFF_long_control | off | GRAPH_REPLAY_OBSERVED | 11 | 47 | 30 |
| PROFILE_OFF_long_normal | on | GRAPH_REPLAY_OBSERVED | 11 | 47 | 30 |
| PROFILE_ON_short_control | off | GRAPH_REPLAY_OBSERVED | 3 | 21 | 12 |
| PROFILE_ON_short_normal | on | GRAPH_REPLAY_OBSERVED | 3 | 21 | 12 |
| PROFILE_ON_long_control | off | GRAPH_REPLAY_OBSERVED | 11 | 47 | 30 |
| PROFILE_ON_long_normal | on | GRAPH_REPLAY_OBSERVED | 11 | 47 | 30 |
| PROFILE_LIFE | on | GRAPH_REPLAY_OBSERVED / DIAGNOSTIC_SERIALIZED | 3 | 21 | 12 |

所有 normal/control 均：
- 完成初始化/capture；
- 第一组 `smoke-1` 预热一次，active 从 `smoke-1` 重新开始；
- 冻结请求全部完成，每个请求 16 tokens；
- 以完全相同 workload 的 control 先于 normal 执行；
- 官方 profile-joint 为 `PASS_SCOPED_PROFILING`。

`PROFILE_LIFE` 明确是 `DIAGNOSTIC_SERIALIZED`，不进入正常性能比较。

## 2. active 阶段是否真的发生 Graph replay

是。`profile.json` 的 `calls` 中 active 项统计如下：

- short：Draft `REPLAY_SUBMIT` 21 次，Draft `REPLAY_PLUS_UPDATE` 21 次，Target `REPLAY_SUBMIT` 12 次；
- long：Draft `REPLAY_SUBMIT` 47 次，Draft `REPLAY_PLUS_UPDATE` 47 次，Target `REPLAY_SUBMIT` 30 次；
- descriptor 分布：
  - short：`(1,7)=7`、`(2,14)=7`、`(4,28)=7`；
  - long：`(1,7)=33`、`(2,14)=7`、`(4,28)=7`；
  - Base Target：`(1,8)=6`、`(2,16)=6`，没有 `(4,32)`。

active 阶段不是“只采到初始化/capture”：每个 normal case 都有非零 active Draft replay 和完整选择请求组。`control` 没有 native profiler，但有同样的轻量 Host range 和 replay 计数。

ON long 的 immutable Window descriptor：
- `PROFILE_ON_long_normal` 的 active `Draft_REPLAY_PLUS_UPDATE` descriptor 中，`source_start_column` 实际值有 `0`（61 个）、`1`（10 个）、`8`（4 个）；
- 共 14 个 active descriptor 满足 `source_start_column > 0`；
- 这不是从 prompt 长度推断，来自 `profile.json` 的 `window_descriptors`。
- 但没有 Window descriptor 与具体 Target task/flow 的直接 correlation ID；不能把该事实升级为完整 task/flow 证据。

## 3. Target/Draft/FIA 可区分性

- Host range 标签明确存在：`Draft_propose`、`Draft_REPLAY_SUBMIT`、`Draft_REPLAY_PLUS_UPDATE`、`Target_REPLAY_SUBMIT`、`Target_REPLAY_PLUS_UPDATE`。
- `operator_details.csv` 有 `Name`、`Input Shapes`、`Call Stack`、`Host/Device Self/Total Duration(us)` 字段；实际 `Input Shapes`、`Call Stack` 为空。
- `kernel_details.csv` 有 `Name`、`Type`、`Start Time(us)`、`Duration(us)`、`Wait Time(us)`、`Block Num`；实际 `Type` 全为 `N/A`。
- `task_time.csv` 有 `stream_id`、`task_id`、`kernel_name`、`task_start(us)`、`task_stop(us)`。
- 仅凭相邻行、相同 shape 或算子名不能把某 kernel 绑定到某 generation。当前没有可靠的 flow/correlation ID 把 Target/Draft kernel 绑定到具体 generation；`target_draft_kernel_attribution = UNRESOLVED_UNLESS_EXPLICIT_FLOW_ASSOCIATION`。

## 4. replay/UPDATE 关联粒度

`profile.json` 明确记录：

```text
update_host_range = UNRESOLVED_SEPARATE; manager range includes replay plus UPDATE
```

- 可报告 `Draft_REPLAY_PLUS_UPDATE` 的整体 Host 区间；
- 不能把该区间写成独立 UPDATE 耗时；
- `task_time.csv` 的 stream/task ID 可用于后续进一步关联，但当前没有校准的 Host/device 时钟或 generation flow；
- `Event::synchronize` 事件存在，但不能据此推断设备完成或 UPDATE effective generation。

## 5. stream / 等待 / 重叠

- `task_time.csv` 实际观察到多个 stream：short 约 9/10/11/12/13/42/43/45/47/48 等；long 同量级，任务行数更多。
- `trace_view.json` 有大量 `enqueue`/`dequeue`、`async_task_queue`、`async_npu` flow 事件。
- 这些字段证明并发队列/流存在，但没有校准的 cross-stream overlap 解析；不能把 duration 相加当 elapsed 或设备占用。
- 设备空档、Host 下发间隔、重复准备：`UNRESOLVED`，需要可校准的 host/device 时间基或明确 flow。

## 6. 拷贝统计

`trace_view.json` 实际事件名统计（ON long normal）：

- `acl_memcpy_host_to_device`：1221
- `acl_memcpy_device_to_host`：141
- `MEMCPY_ASYNC`：4081
- `aten::copy_`：4743
- `aten::_to_copy`：642
- `Event::synchronize` 名称事件：4175

OFF long normal：
- H2D `acl_memcpy_host_to_device`：1221
- D2H `acl_memcpy_device_to_host`：141
- `MEMCPY_ASYNC`：3771
- `Event::synchronize`：3865

short normal：
- OFF：H2D 513、D2H 63、`MEMCPY_ASYNC` 1705、sync 1747
- ON：H2D 513、D2H 63、`MEMCPY_ASYNC` 1859、sync 1901

限制：
- trace 事件没有 `bytes`/size 字段，**字节数 UNAVAILABLE**，不能填 0。
- D2D 没有独立的可证实字段；`MEMCPY_ASYNC` 不能自动等同于 D2D。
- 拷贝 duration 不能直接与 kernel duration 相加为 E2E。
- 这些是 profiler 观测，不是 physical read-set 证据。

## 7. 可比较的 Host 统计

`profile.json` 的 `host_statistics` 是 Host 提交区间，scope 明确为 `HOST_SUBMISSION_NOT_DEVICE_COMPLETION`。下表为 `Draft_REPLAY_PLUS_UPDATE` 每样本均值（ms）：

| workload | control | normal | diagnostic delta |
|---|---:|---:|---:|
| OFF short | 1.337 | 1.555 | +16.3% |
| OFF long | 1.228 | 1.649 | +34.3% |
| ON short | 2.578 | 2.942 | +14.1% |
| ON long | 2.662 | 2.885 | +8.4% |

这些差异是**诊断性对照**，包含 profiler/轻量 range 开销、进程/资源差异；不是 release 性能结论，也不是加速比。

`Draft_REPLAY_SUBMIT`、`Draft_propose`、`Target_REPLAY_PLUS_UPDATE` 的逐 case 样本数、mean/p50/p95/sum 见 `Repair5_Profiling_Summary.json`。

## 8. PROFILE_LIFE 串行化开销

`PROFILE_LIFE` 是 `DIAGNOSTIC_SERIALIZED`，独立于正常对照：

- `Draft_REPLAY_PLUS_UPDATE` mean 约 1062.5 ms，p50 1012.9 ms；
- 正常 ON long mean 约 2.66–2.89 ms；
- `Draft_propose` mean 约 1360.0 ms；
- 说明 LIFE 的 event/wait/D2H/落盘串行化有显著观测开销；
- 不参与正常路径性能比较，不写成 release 性能。

## 9. A–I 结论

| 问题 | 结论 |
|---|---|
| A. active 是否发生 Graph replay？ | 是；short 21、long 47 次 Draft replay，descriptor 分布已记录。 |
| B. Target/Draft/FIA 能否区分？ | Host range 可区分；native kernel/flow 到 generation 的绑定 UNRESOLVED。 |
| C. replay/UPDATE 关联粒度？ | manager range 含 replay+UPDATE；独立 UPDATE 子 range UNRESOLVED。 |
| D. 同/跨 stream 等待重叠？ | stream/task 字段存在；因果重叠未解析。 |
| E. H2D/D2H/D2D 次数/字节/时间？ | H2D/D2H 事件次数可数；字节字段 UNAVAILABLE；D2D 未证实。 |
| F. 设备空档/Host 间隔/重复准备/同步？ | 存在 sync/flow 事件，但空档与重复准备 UNRESOLVED。 |
| G. OFF/ON 差异？ | 只有同 workload diagnostic Host 区间差异；不声称 release 加速。 |
| H. profiling/LIFE 开销？ | LIFE 明确串行化，Draft 区间约 1.0–1.4 s，显著高于 normal。 |
| I. 哪些字段仍不足？ | task operand、physical read-set、UPDATE effective generation、completion owner 均不足；保持 OPEN。 |

## 10. 关键原始路径

- `artifacts/retry1/PROFILE_ON_long_normal/profile.json`
- `artifacts/retry1/PROFILE_ON_long_normal/trace-analysis.json`
- `artifacts/retry1/PROFILE_ON_long_normal/trace/node-39-101_609735_20261021005343964_ascend_pt/ASCEND_PROFILER_OUTPUT/trace_view.json`
- `artifacts/retry1/PROFILE_ON_long_normal/trace/.../ASCEND_PROFILER_OUTPUT/task_time.csv`
- `artifacts/retry1/PROFILE_LIFE/profile.json`
- `artifacts/retry1/PROFILE_LIFE/trace-analysis.json`

原始 PROF/ascend_pt 目录、DB/CSV、时间线 JSON 与解析日志均在 raw 包中。

## 11. 限制

- 原始日志中的服务器绝对路径保留；review/raw 包提供相对路径映射。
- Host monotonic_ns 不与 device timestamp 直接排序。
- Host range 结束不等于设备 task 完成。
- 并行 duration 总和不等于 elapsed 或设备利用率。
- 控制组仍有轻量 Host range 观测开销。
- 采样规模足够做诊断，但不足以声称 release 性能 PASS。
- 本轮没有、也不能从这些 trace 证明 physical read-set 或 task-internal operand。
