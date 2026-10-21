# Repair6 服务器入口：POST_PUBLICATION

已通过普通 push 与独立 GitHub 网络 clone。执行版本 fd0716c59562f64262672de12e4ae26259908d0b / tree 125b29bcb8fe501d69b53e185f9ec89075528310 / parent febc43be3309f6d2cd87f9332cb7e031ebaad001。
包内 REVIEW_FIX_REPORT.md 是历史 PRE_PUBLICATION 审查记录；本次 PUBLICATION_REPORT.md 才是最终发布状态。历史记录中的未发布状态不得抹除，也不得误用为当前状态。
本包不是源代码覆盖补丁。必须从 GitHub 获取专用分支并核对 exact SHA/tree、pinned vLLM、实际 import/tool hashes；原 fixture manifest 字节保持不变。

发布后：使用已安装当前栈Python，不升级CANN/torch_npu，真实路径替换下面变量。PREPARE会核验源码/import/tool hashes/fixture/NPU，只生成plan不执行模型。没有全局82GB门槛。

```bash
python PREPARE.py --repo /actual/vllm-ascend --vllm /actual/vllm --output /actual/NEW_ATTEMPT --run-id NEW_RUN_ID
python /actual/vllm-ascend/tools/p7x_graph_repair6_runner.py --plan /actual/NEW_ATTEMPT/case-plan.json --case-id P0 --output /actual/NEW_ATTEMPT/runner
```

同一runner每次只运行明确case；case-plan包含真实argv、launcher、checker、3300秒比较上限、依赖、输出和资源策略。不能执行preview里的占位路径。

必跑：P0→A0/A1/B0新SHA锚点→PREFIX_OFF/ON→G4F_OFF/ON、TARGET4_OFF/ON；双臂尝试后各COMPARE可只读恢复partial。Base expected不支持Target(4,32)不阻断Target4。NUMERIC_TARGET4依赖PREFIX_ON，12个完整场景；NORMAL_ORDER依赖B0。
Profiling：OFF/ON×short/long×control/normal（8个case）重跑以取得新增四子range；详细PROFILE_ON_long_detailed仅在新字段确有用途时跑，保持独立诊断。
LIFE/ABORT：本轮异常隔离有变更，先LIFE正常，再按plan故障点独立子进程；73必须专用checker，74/signal/timeout不得当PASS。原C2数值、无改变的历史trace可参考，不冒充新SHA结果。
失败后只停依赖分支。绝不删case/减bucket/eagerfallback。numeric第一个确认失败会durable落盘并停止后续代；native不确定退出74，不在进程内恢复重试。新attempt用新输出目录。

资源：Target按实际单臂/单样本geometry；numeric另加Draft snapshots；profiling2GiB启动预留非最大trace保证；pack按实际未压缩bytes预检。每阶段保存实时磁盘/RSS/HBM；保留旧失败文件。预算不足仅该分支BLOCKED_RESOURCE。

回传与校验：
```bash
python /actual/vllm-ascend/tools/p7x_graph_repair5_pack.py pack /actual/NEW_ATTEMPT --output /separate/evidence.zip
python /actual/vllm-ascend/tools/p7x_graph_repair5_pack.py verify /separate/evidence.zip
```

0只表示所声明scope可接受；2=OPEN/不完整/执行失败，3=数值失败，4=无效证据，5=资源不足，124=超时。报告保留四层：执行身份/产物完整性/样本数值/整组覆盖，任何局部PASS不关闭全部G1–G5。

## 调度硬约束

不要按 JSON 对象顺序一键运行全部 case。G4F_COMPARE / TARGET4_COMPARE 即使在计划拓扑列表中靠前，也必须等待对应 OFF、ON 两臂都结束尝试后才运行；一臂失败保留原退出/partial，再做只读前缀比较，不能改写失败。
42 case / 136 argv 只完成 Host 参数解析，不是设备通过。Base 缺 Target(4,32) 的 expected OPEN 不传播到独立 Target4。完整 Target 资源不足不能阻断轻量分支或 profiling。
PREPARE.py 需要真实 NPU/source/import/模型文件核验，禁止用 Host stub 伪造。服务器模型路径和请求配置来自 inputs/，不要另找 fixture。
生产 Gate 仍冻结。连续数值参考为 DIAGNOSTIC_SERIALIZED；NORMAL_ORDER 观测与其不同，不能由串行 PASS 推导无同步 reuse 安全。
