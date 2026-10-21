# Repair6 下一轮执行（PRE_PUBLICATION）

源码 febc43be3309f6d2cd87f9332cb7e031ebaad001 / tree f68e57e4501dacb67cdf4c81831b8f713e4ddc18 / parent d41bb588a7e62b67a3ee1ce4bf652bf2701662da。本轮未push。发布会话必须普通push、独立网络clone验收，再更新handoff publication_status=VERIFIED并重新打包。当前PREPARE/runner会拒绝执行，禁止手动绕过。
建议部署路径（尚未创建）：/mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend，配套/mnt/wenqing/mrv2_graph_repair6_verify/source/vllm，输入/mnt/wenqing/mrv2_graph_repair6_verify/server_input。实际Python/runtime/import由现场核对，不能复制Mac环境路径。模型路径、全部参数、请求来自原fixture与已提交driver。

## 发布后准备

~~~bash
python3 /mnt/wenqing/mrv2_graph_repair6_verify/server_input/PREPARE.py --repo /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend --vllm /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm --output /mnt/wenqing/mrv2_graph_repair6_verify/RUN_REPAIR6_febc43be --run-id RUN_REPAIR6_febc43be
~~~

PREPARE验证已发布handoff、两仓exact clean/import、toolhash、fixture每文件hash及全campaign预算；不加载模型。源码/模型/资源失败先停，不靠减少bucket/换模型/eager fallback。
其后用已提交runner单case执行：

~~~bash
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair6_runner.py --plan /mnt/wenqing/mrv2_graph_repair6_verify/RUN_REPAIR6_febc43be/case-plan.json --case-id P0 --output /mnt/wenqing/mrv2_graph_repair6_verify/RUN_REPAIR6_febc43be/runner
~~~

case_id替换为表中项。完整argv/dependencies/checkers在case-plan.preview.json，最终部署plan由PREPARE按实际目录生成；不将预览路径当既有机器路径。

|分支|case顺序|验收/产物|失败处理|
|---|---|---|---|
|源码/API|PREPARE→P0|exact/import/fixture；版本/API/FIA schema；资源|阻断设备，但允许独立离线分析|
|新SHA锚点|A0→A1→B0|A0请求；A1 GRAPH_FROZEN负例；B0真实3桶replay、多代每层update/retire、输出16token/外部launcher联合|核心错误停依赖分支|
|资源最小例|PREFIX_OFF/PREFIX_ON|首A完整Target+chunkwriter/reader/joint|该臂失败停全量，保留prefix|
|完整Target|G4F_OFF/ON→G4F_COMPARE；TARGET4_OFF/ON→TARGET4_COMPARE|原11/12场景；Base4row expectedOPEN；Target4实际4rowcapture/replay和双臂全比较|失败仍可显式只读COMPARE，不将prefix写整组PASS|
|真实连续数值|NUMERIC_TARGET4|同Window、真实MRV2 graphhidden/eagerreference、全部active/padding/源KV、A/B/A_prime/切桶|source/oracle/数值错停止，不调容差|
|正常顺序|NORMAL_ORDER|O1combined、observerOFF，三桶每桶>=2代、source/launcher/16tokens、末尾copydrain|只能normal-order观察，不作为reuse闭环|
|自然观察|G4_OFF/ON_long2、mixed（需要新identity才跑）|唯一业务配对，全部歧义/未配对|不强求自然轨迹等长|
|开销|PROFILE_OFF/ON_short/long_control/normal|capture后warmup/active，实际Graph，16token；新增Host子range|只一种nativeprofiler；control不计native|
|详细诊断|PROFILE_ON_long_detailed|签名支持shapes/stack、有明确新增字段目标|不支持则CAPABILITY_UNVERIFIED，不重复同trace找物理read|
|按需历史|C2/LIFE/ABORT_*|本轮未改其核心，异常风险或diff影响才重跑|abort73必须专用checker，74/timeout拒绝|

producer默认1800/3600s，read-only比较3300s，外层margin120s，精确值见plan。保存exit/signal/timeout/stderr/partial/laststage/progress与全部命令；runner max_rss_children为平台单位（Linux KiB），不是HBM。
producer完成、sample完整、数值、覆盖分别报告。NUMERIC_MISMATCH不能被OPEN覆盖；COMPARISON_TIMEOUT不是数值FAIL；SAMPLE_COMPLETE仍需要外部执行联合。
Base缺4row不会自动扩配置；Target4独立profile。各比较分支只依赖P0，须在两臂尝试后显式调用，容许失败前缀恢复，未成双臂不盲目加载大集合。

## 离线与回传

~~~bash
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair6.py compare-target --off OFF/controlled-target.json --on ON/controlled-target.json --timeout 3300 --output comparison.json
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair6_natural.py --off G4_OFF_long2 --on G4_ON_long2 --output natural.json
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair6_trace.py --trace trace_view.json --output full-flow.json
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair5_pack.py pack /mnt/wenqing/mrv2_graph_repair6_verify/RUN_REPAIR6_febc43be --output /mnt/wenqing/mrv2_graph_repair6_verify/Repair6_raw.zip
python3 /mnt/wenqing/mrv2_graph_repair6_verify/source/vllm-ascend/tools/p7x_graph_repair5_pack.py verify /mnt/wenqing/mrv2_graph_repair6_verify/Repair6_raw.zip
~~~

流式4MiB/ZIP64打包，保留失败，接收端重新verify。原模型manifest SHA 1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4。
旧Repair5已回答的前7Target、tokenABA前缀、B1计数和flow存在无需无理由重跑旧35项；旧SHA只是历史，不自动继承新SHA。没有新字段机制时，不重跑相同profiler期待physical read。
