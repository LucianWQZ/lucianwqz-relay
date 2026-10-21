# Repair6 Review-Fix服务器入口：PRE_PUBLICATION

当前commit fd0716c59562f64262672de12e4ae26259908d0b / tree 125b29bcb8fe501d69b53e185f9ec89075528310 尚未发布。不能编辑JSON绕过发布门；先独立review、普通push及GitHub网络恢复核验，由发布任务重新签发VERIFIED handoff。
代码以Git提交为准；包内无生产覆盖补丁。fixture manifest原字节hash不变。

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
