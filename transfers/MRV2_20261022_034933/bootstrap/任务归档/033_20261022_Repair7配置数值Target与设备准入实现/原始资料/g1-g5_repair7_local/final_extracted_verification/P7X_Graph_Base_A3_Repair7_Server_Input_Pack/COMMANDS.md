# Repair7执行交接 — PRE_PUBLICATION

候选 7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14 / tree 6dd40a67a500480556068be8b6ebcd977e3cc3e8。当前禁止设备执行；先独立审查，再由另任务发布并网络恢复，重新签发VERIFIED handoff。本包不自行修改publication字段绕过。

## 发布后实际入口

先由服务器owner建立授权映射/环境，代码与输入包各自固定路径。以下变量必须替换为真实独立目录，不能使用本机preview路径：
```sh
REPO=/path/to/exact/vllm-ascend
VLLM_REPO=/path/to/pinned/vllm
PACK=/path/to/extracted/input-pack
RUN=/path/to/new/repair7-attempt
PY=/path/to/server/python
RUN_ID=unique-repair7-run
$PY "$REPO/tools/p7x_graph_repair7_device.py" inspect --output /path/to/inventory.json
# owner确认只读映射后，才允许probe；保存probe自身host/container PID证明
$PY "$REPO/tools/p7x_graph_repair7_device.py" probe --receipt /path/to/owner-mapping.json --run-id "$RUN_ID" --output /path/to/probe.json
$PY "$REPO/tools/p7x_graph_repair7_device.py" check --receipt /path/to/complete-receipt.json --run-id "$RUN_ID" --output /path/to/admission.json
$PY "$PACK/PREPARE.py" --repo "$REPO" --vllm "$VLLM_REPO" --output "$RUN" --run-id "$RUN_ID" --receipt /path/to/complete-receipt.json
# 每case新receipt，不能复用过期/其他case授权；以下以CONFIG为例
$PY "$PACK/BIND_DEVICE.py" --repo "$REPO" --plan "$RUN/case-plan.json" --case-id CONFIG --receipt /path/to/CONFIG-receipt.json --output "$RUN/admitted-CONFIG.json"
$PY "$REPO/tools/p7x_graph_repair6_runner.py" --plan "$RUN/admitted-CONFIG.json" --case-id CONFIG --output "$RUN/executions"
```
所有设备case同样先BIND；只读COMPARE不需device receipt，但需两个同run/source arm结束attempt。runner只执行指定case，不自动campaign。保留case-plan/各admitted-plan、receipt和全部原始命令。

## 顺序与依赖

P0 exact/import/fixture/capability（授权后）与CONFIG实际EngineArgs平台工厂预检均应先完成；A0/A1/B0锚点；NUMERIC_SENTINEL前三代；通过后NUMERIC_TARGET4全部12。Target分支PREFIX_OFF/ON资源存储前哨→G4F/TARGET4 OFF/ON→对应COMPARE→target-join最终外部裁决。Base缺Target(4,32)保留，不阻断Target4。
独立B2/O0/O1/C2和normal profiling按plan依赖，不受NUMERIC失败拖死。LIFE通过后ABORT/PROFILE_LIFE；NORMAL_ORDER独立保留正常顺序观测。
下一轮优先执行新配置/数值锚点和授权设备来源；旧Target12/12可离线引用，但新SHA和授权设备锚点仍需。无需重新尝试已知Base缺桶或重复无新增字段的physical-read trace。

## 实际最终聚合

```sh
$PY "$REPO/tools/p7x_graph_repair7.py" target-join --root "$RUN" --plan "$RUN/case-plan.json" --profile TARGET4 --device /path/to/device-segment.json --output "$RUN/target4-final-join.json"
$PY "$REPO/tools/p7x_graph_repair7.py" target-join --root "$RUN" --plan "$RUN/case-plan.json" --profile G4F --device /path/to/device-segment.json --output "$RUN/base-final-join.json"
```
原始launcher路径必须保留为RUN/launchers/CASE/launcher.json。比较重新读取chunk，不接受陈旧PASS；仍将authorized_device_acceptance=false，设备分配由单独准入/worker证据裁决，不自动盖章。
入口/参数/timeout/resource_policy以case-plan为准；44case与140CLI解析仅本地合同，不是设备完成数。

回传保存plan、receipts、launcher/campaign、target/numeric chunks、partial、原异常/exit/signal/timeout、joint、runner-result、native trace与解析。用最终Git中的tools/p7x_graph_repair5_pack.py pack/verify流式打包；大raw独立、review不含模型。禁止包内补丁覆盖checkout。
