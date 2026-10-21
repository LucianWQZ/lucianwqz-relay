# P7-X Graph Base A3 Repair6 Review-Fix — 本地实现与就绪报告

## 结论与范围

F1–F6均 **ACCEPTED**，有实际baseline RED，不是因为review来自其他Agent自动接受。另修复真实capture入口诊断sink丢失。完成独立本地commit；未push、未PR、未服务器实验，public Gate STILL_FROZEN。可进入发布审查；设备case仅在review+发布+独立网络恢复+各分支资源成立后运行。**不具备全部G1–G5 closure**。

branch `fix/p7x-graph-base-a3-repair6`
commit `fd0716c59562f64262672de12e4ae26259908d0b`
tree `125b29bcb8fe501d69b53e185f9ec89075528310`
parent `febc43be3309f6d2cd87f9332cb7e031ebaad001`
review baseline `febc43be3309f6d2cd87f9332cb7e031ebaad001` / tree `f68e57e4501dacb67cdf4c81831b8f713e4ddc18`。
vLLM `84030bbe3d74d99bad477a3d2e37a973ccd8865c` / `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` clean，未修改。Signed-off-by存在；密码学签名 `N`（N=未签名），不混同。

## 输入和历史证据

本轮完整核对旧实现报告、handoff、Download Manifest/Package Verification；两个ZIP列成员并重校CRC/index/hash/JSON。旧六份交付已保留archive_pre_review，Archive_Manifest绑定原bytes/hash，更新没有抹掉历史。
Repair5大raw不重复展开，复用已核验原包与逐样本结果，Input_Integrity_Reuse和Historical_Evidence_Index记录范围。历史事实仍是四臂7个CAPTURED_COMPLETE、第8mixed预算失败；两profile各7对完整Target前缀数值相等；整组FAILED/缺失样本不改成PASS。旧SHA d0a3fc的tokenABA/trace只能作历史证据，不是本轮新SHA NPU验证。

## 逐项裁决、RED/GREEN与旧测试盲点

|ID|裁决|baseline反例/旧测试为何漏检|实际修复与GREEN|
|---|---|---|---|
|F1|ACCEPTED|5 invalid CPU-tensor collections received PASS on febc43; repair6_red_initial.log；numeric joint trusted shape/status and eager all-row loading, did not validate canonical or execution consistency|continuous-v2 actual/reference operands, complete identity/KV/layer contract, independent W1024/B128 recompute, sequential join；review::test_f1_*; numeric_pipeline::full_geometry, artifact_mutations, CLI under python -O|
|F2|ACCEPTED|real pinned forward graph/reference differ yet producer did not raise; repair6_red_submission.log；record status not propagated to control flow|flush failed tensors, NumericMismatch, branch latch; driver exit3; checker/runner fail preserved；contracts numeric fault; numeric_pipeline::test_real_numeric_mismatch_stops_next_generation_and_runner|
|F3|ACCEPTED|native reference mutated cache to999, old finally restored1; driver ignored normal/numeric poison；unconditional restore/finalizer and only LIFE quarantine|instance SubmissionState, restore only completed reference, 74/no teardown on uncertain work; bounded owned-descendant watchdog；contracts native fault; driver_quarantine actual run_case/finally; nested setsid timeout test|
|F4|ACCEPTED|natural actual CLI wrote NUMERIC_MISMATCH but exit0；main discarded compare status|0 scoped accepted /2 OPEN/3 numeric/4 invalid/5 resource/124 timeout; runner read-only status and dependency contract；review actual natural subprocess; failure_execution exit matrix; python -O numeric runner|
|F5|ACCEPTED|real Target producer complete prefix+PREPARING tail became INVALID_EVIDENCE；reader tried loading path=None|recognize only final uncommitted tail; corrupt completion remains INVALID; earlier FAIL wins and corruption remains separate；review prefix; failure_execution four combinations complete/mismatch x preparing/corrupt|
|F6|ACCEPTED|sample_limit1 still budgeted11; repair6_red_initial.log；global/full collection budget used for prefix|one-arm runtime geometry/prefix, numeric own geometry, per-chunk disk checks, branch launch reserves, pack no-compression bound; no global82GB gate；prefix real runtime budget; real tensor mid-write lowdisk; independent branch and pack preflight|
|R6-RF-07|ACCEPTED|actual DSpark.capture failed freeze with empty sink; repair6_red_capture_contract.log；pinned warmup/capture callback passes NONE, old sink retained FULL only|instance collecting scope, latest real callback output, successful capture freeze; failure clears collecting；capture_chain real DSpark/Ascend/pinned manager/builder; default OFF; 12-generation pipeline|

RED原始日志：logs/repair6_red_initial.log（F1五例、F4实际CLI、F5尾部、F6prefix共8失败）；logs/repair6_red_submission.log（F2不抛错、F3旧finally错误恢复）；logs/repair6_red_capture_contract.log（真实capture sink inventory失败）。首次capture harness缺_draft_topk的日志单独保留，不把它当production根因。
补充GREEN包含实际driver.finally→74/no shutdown、真实OS setsid后代watchdog、python -O下producer→store→CLI→runner。没有只单测setattr/JSON字典。

## 新增capture根因及关键diff

pinned CudaGraphManager.capture两个create_forward_fn都传CUDAGraphMode.NONE。旧UT手动FULL；实际DSpark.capture虽然分配sink，但输出未retain，freeze inventory为空。

```diff
- super().capture()
+ sink.collecting = True  # 仅显式诊断开启时
+ try: super().capture()
+ finally: sink.collecting = False
  sink.freeze(actual_captured_graph_token_inventory)  # 仅成功后
- if sink is not None and mode == FULL:
+ if sink is not None and (sink.collecting or mode == FULL):
      sink.retain(owner, num_tokens, output)
```

真实capture warmup→capture按同bucket更新引用，最后实际capture输出保留；没有从manager的合法None制造tensor。默认关闭不创建sink、不保留额外输出、不加clone/event/sync，不改变greedy/返回合同。仅两个production文件变动：draft_window_graph_diagnostics.py和dspark/speculator.py，其他是工具/测试。

## 核心数值和异常修复

numeric v2保存真实actual/reference metadata、canonical table/exact/valid、输入/位置/slot/query、真实各层K/V inventory及Graph/reference前后态、隐藏维度、generation/epoch/backing。checker独立重算W1024/B128，不信producer oracle/status；顺序mmap验证，不整集合加载。summary/manifest/payload/campaign/launcher/冻结plan不一致不能PASS。既有NUMERIC_MISMATCH不得被后续OPEN/INVALID吞掉，证据错误另列。
pre/post restore只在已完成诊断路径允许；reference中途native失败后不再恢复/同步/普通teardown。SubmissionState与branch失败latch实例持有，未知提交74隔离，数值完成失败3。writer durable失败样本后立刻停止下一代。外部timeout只收尾自己创建的后代进程，完整性错误不假装device问题。
padding数值范围明确：active hidden全量零容差；padded hidden仅shape/dtype/finite，写侧slot=-1/readlength0。没有把padded数值相等算已验证。完整12-case Target4包含Target1active/2padded但Draft(1,7)、3active/4padded、切桶/返回旧桶。

## 资源和partial

prefix sample_limit=1只算1样本；完整Base11/Target4十二样本不缩短。每臂采集按实时free，numeric独立geometry，chunk前空间检查，打包不假定高压缩；不再82GB全局阻断P0/轻量/profiling。首次预算不足/中途首chunk后不足都留下可审计partial，不删原证据。PREPARING尾部=不完整，不是伪造损坏；声称complete却坏hash/缺文件=INVALID；前缀confirmed FAIL优先保留。

## Host验证与边界

最终受影响集合 **1007 passed，1 warning**；包含37个明确测试文件，完整argv/环境/exit/文件hash在Validation.json和logs/regression.log。Ruff、format、定向Mypy、compile、diff及6个可独立执行仓库检查通过。完整manual pre-commit因npm `EALLOWGIT`安装markdownlint失败，**ENVIRONMENT_BLOCKED，不是PASS**；没有禁用hook或TLS，没有安装/改写底层栈。本机未安装git hooks，正常git commit -s，未用--no-verify。历史7个VWN Host backend失败不在本轮受影响集合，不重新宣称PASS。
真实Python链：DSpark capture→Ascend/pinned managers→真实builder→真实P3/P6 bind/consume/retire、多代reference→分块文件→独立checker→外部身份join→实际CLI(-O)→runner。仅native Graph/FIA/event/stream与模型算子由CPU surrogate代替，所有NPU行为NOT_RUN。默认OFF、上一轮canonical共享/private alias、公有Gate回归保留。

## 生命周期与Profiling的进一步结论

Target AsyncOutput copy_event在Draft propose前记录；普通非structured DraftTokensHandler不执行Draft D2H，get返回placeholder。不能用上述CPU返回作为Draft backing完成证明。current-stream FIFO是候选HB，但跨UPDATE stream、ExternalEvent/reset/task-update何时生效仍需版本语义。完整操作表在Normal_Lifecycle_Source_Audit.md；NormalOrder末尾drain不证明每次reuse。
四Host子range现在有installed/actual/expected/missing generation，不能hasattr跳过仍PASS；保存requestgroup/descriptor和可用epoch。嵌套时间不相加为E2E，初始化capture单列，prefill/decode/kernel无法唯一归因标UNRESOLVED。旧完整trace有flow但normal replay未唯一关联；不重复同字段期待物理地址。

## 下一轮及仍未完成

必跑P0/A0/A1/B0新SHA锚点；PREFIX双臂→完整Base/Target4双臂与逐样本COMPARE；NUMERIC_TARGET4完整连续参考；NORMAL_ORDER有界多代；新四range的8个OFF/ON短长control/normal。LIFE/ABORT只对本轮隔离变动做定点复测；detailed仅需新增字段时跑；旧C2/旧完整trace作为历史不机械重跑42项。
有实施代码和CLI，但设备NOT_RUN：完整Target store、串行连续reference、normal观测、故障隔离、profile。**NOT_IMPLEMENTED：无逐代同步的完整连续reference**。**CAPABILITY_GAP：task内部operand/physical read；UNPROVEN：正常UPDATE代际/每次backing reuse**。需要平台明确版本语义或验收owner决定证据替代，标准未自行下降，完整Target未降为HEAD_ONLY。
服务器资源不足只阻断该分支；实际NPU错误停止依赖分支、保留原stderr/partial/launcher；独立安全分支继续。发布前PREPARE硬拒绝正式campaign。详细命令/依赖在Server Input Pack与Repair6_Review_Server_Commands.md。

## 文件与审查

完整diff和28文件最终源码随review ZIP；Finding_Disposition、Validation、逐样本Host摘要、Failure/Exit、Continuous、StageResource、NormalLifecycle、Profiling合同、旧证据索引均随包。最终handoff明确NOT_PUBLISHED/NOT_RUN/STILL_FROZEN；package verification只证明交付一致性，不证明G1–G5。

## 可独立复核的具体记录

隔离git-archive重演：baseline F1/F4/F5/F6=8 failed；F2/F3=2 failed/1 passed；capture=1 failed/1 passed。相同最终测试覆盖最终源码后为8+3+2=13 passed。不是修改原checkout重现，production未overlay。原先红测和本次重演各自保留，不覆盖历史。

以下是真实Host producer→存储→checker→CLI(-O)→runner的12样本摘要；native/model为CPU surrogate（hidden宽度2），不是A3结果：

|代|场景|Target桶|Draft桶|canonical exact|独立S|active hidden max_abs|KV前/后逐块|
|---|---|---|---|---|---|---|---|
|0|A|[1, 8]|[1, 7]|[1159]|[128]|0.0|22块:相等|
|1|B|[1, 8]|[1, 7]|[1287]|[256]|0.0|24块:相等|
|2|A_prime|[1, 8]|[1, 7]|[1159]|[128]|0.0|22块:相等|
|3|short|[1, 8]|[1, 7]|[39]|[0]|0.0|4块:相等|
|4|long|[1, 8]|[1, 7]|[1159]|[128]|0.0|22块:相等|
|5|boundary|[1, 8]|[1, 7]|[1031]|[0]|0.0|20块:相等|
|6|nonaligned|[1, 8]|[1, 7]|[1160]|[128]|0.0|22块:相等|
|7|mixed|[2, 16]|[2, 14]|[39, 1160]|[0, 128]|0.0|24块:相等|
|8|padding|[2, 16]|[1, 7]|[39]|[0]|0.0|4块:相等|
|9|return-short|[1, 8]|[1, 7]|[39]|[0]|0.0|4块:相等|
|10|three-active-four-padded|[4, 32]|[4, 28]|[39, 1032, 1160]|[0, 0, 128]|0.0|42块:相等|
|11|four-active|[4, 32]|[4, 28]|[39, 1031, 1159, 1160]|[0, 0, 128, 128]|0.0|62块:相等|

故障注入B reference真实增加1：只保留A/B两个样本，未进入A′；失败output.json与runner结果随host_evidence/numeric_failure提供，不能通过输出报告成功来覆盖数值失败。

资源（bytes；实际模型加载/Host RSS/HBM另测，不把paged mmap误称硬RSS上限）：

|范围|单臂新增free|双臂保留|比较新增|两臂+raw峰值|
|---|---:|---:|---:|---:|
|base|7110492160|14212595712|8388608|28416802816|
|target4|9253019648|18497650688|8388608|36986912768|
|prefix1|707598336|1406808064|8388608|2805227520|

逐文件范围（完整diff随包）：

|路径|类别|
|---|---|
|`tests/ut/spec_decode/test_draft_window_graph_carrier.py`|Host真实合同/反例测试|
|`tests/ut/spec_decode/test_draft_window_graph_characterization.py`|Host真实合同/反例测试|
|`tests/ut/spec_decode/test_graph_repair4_integration.py`|Host真实合同/反例测试|
|`tests/ut/spec_decode/test_graph_repair6_capture_chain.py`|Host真实合同/反例测试|
|`tests/ut/spec_decode/test_graph_repair6_contracts.py`|Host真实合同/反例测试|
|`tests/ut/spec_decode/test_graph_repair6_delivery.py`|Host真实合同/反例测试|
|`tests/ut/spec_decode/test_graph_repair6_driver_quarantine.py`|Host真实合同/反例测试|
|`tests/ut/spec_decode/test_graph_repair6_failure_execution.py`|Host真实合同/反例测试|
|`tests/ut/spec_decode/test_graph_repair6_numeric_pipeline.py`|Host真实合同/反例测试|
|`tests/ut/spec_decode/test_graph_repair6_review.py`|Host真实合同/反例测试|
|`tools/p7x_graph_repair2.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair5.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair5_lifecycle.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair5_pack.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair5_profile.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair5_target.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6_campaign.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6_lifecycle.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6_natural.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6_numeric.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6_numeric_check.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6_runner.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6_storage.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6_submission.py`|受控工具/producer/checker/runner与有界交付|
|`tools/p7x_graph_repair6_watchdog.py`|受控工具/producer/checker/runner与有界交付|
|`vllm_ascend/worker/v2/spec_decode/draft_window_graph_diagnostics.py`|显式诊断production seam；默认OFF不改功能|
|`vllm_ascend/worker/v2/spec_decode/dspark/speculator.py`|显式诊断production seam；默认OFF不改功能|
