# Repair4 Review Fix and GitHub Publication

最终执行版本：`08c94a99032c47e2608b976c25065adbbc8dea09` / tree `7d58b3414a9911662604634198c32e98094b15cf`，branch `fix/p7x-graph-base-a3-repair4`。
review baseline 为 `aaa4632612503adb34d90b55c36eedcaf0848979`，父级 Repair3 为 `10cbf4c014fc6cc48a6fea611bb605cecdd54cfd`。
PUBLICATION=VERIFIED；CLEAN_ROOM=VERIFIED；NEW_SHA_DEVICE_VERIFICATION=NOT_RUN；
PUBLIC_GRAPH_GATE=STILL_FROZEN。没有执行服务器实验、PR、merge、tag 或 force push。

## 1. 结论与版本规则

四项审查均由真实源码/反例复核，全部 ACCEPTED。此次只改8个 tools/tests 文件，
没有改 vllm_ascend 生产模块、FIA、Graph调用顺序、Window数学、allocator、scheduler或completion。
原实现报告只描述 aaa46326，且有两处范围/容差错误，本报告明确覆盖其当前结论。
历史输入包/报告/handoff/download manifest原字节归档：
`/Users/wenqingzhang/Desktop/Note/MRV2/Repair4_PRE_PUBLICATION_aaa463261`。旧文件hash只代表历史文件，不能代表新服务器输入包。

## 2. Resolution Table

|ID|裁决|独立复现/源码事实|修复与验证|
|---|---|---|---|
|R4-R01|ACCEPTED|attention_v1.full_graph_fia构造17基础+4量化占位+layer，共22项；旧probe硬要求23|消费真实生产构造；校验K/V view、block_size、head/scale、length/sparse类型、quant与layer；未知schema拒绝；7种篡改负例|
|R4-R02|ACCEPTED|旧汇总顺序INVALID→OPEN→FAIL，掩盖已对齐失败|FAIL优先且单列confirmed_failure_count/evidence_complete/evidence_issues；PASS+OPEN、FAIL+OPEN、FAIL+INVALID均实测|
|R4-R03|ACCEPTED|源码0.016而COMMANDS写0.008；controls只有A/B/A_prime/short/nonaligned|保留预先设定0.016并加入manifest scope/digest；Host量化误差核对；outside-only明确NOT_IMPLEMENTED，不当作设备证据|
|R4-R04|ACCEPTED|旧B0接受每请求2tokens且不接收launcher|新增check-joint关联plan/request raw hash/campaign/launcher；要求每请求16、正常退出、PID和同run/case/attempt/source；A1与abort分别验收|

## 3. R01真实契约及 RED

`vllm_ascend/attention/attention_v1.py::full_graph_fia`原源码未修改。
tuple布局：

```text
0 query; 1 key; 2 value; 3 block_table; 4 mask; 5 block_size
6 actual_seq_lengths_kv; 7 actual_seq_lengths_q
8 kv_heads; 9 heads; 10 scale; 11 output; 12 softmax_lse
13 sparse_mode; 14 pre_tokens; 15 next_tokens; 16 sliding_window
17..20 quant operands/placeholders; 21 layer_name
```

Host测试不再人工制作23项tuple。实际调用production `_get_fia_params`与`full_graph_fia`，
真实生成22项，再交给`LiveTargetAdapter._boundary`。只替换native Graph/Event/FIA.out、
weak_ref native辅助及forward context；K/V库存、元数据和tuple构造没有mock成预期答案。
live runner设备准入/stream sync在Host替代，因此不等于真实NPU执行。

RED命令（old module字节来自git show aaa46326，不改工作区旧源码）：

```bash
VLLM_VERSION=0.29.0 PYTHONPATH=../vllm .venv/bin/python red_baseline.py
```

保留`logs/red-baseline-exact.log`，4 failed：

```text
test_production_fia_tuple_is_consumed_by_target_probe:
  assert len(p) == 22
  old LiveTargetAdapter._boundary(...)
  EvidenceError: unknown captured FIA parameter schema
FAIL+OPEN -> old overall OPEN
FAIL+INVALID_EVIDENCE -> old overall INVALID_EVIDENCE
```

首次测试编写中缺forward context的失败也保留，但不作为R01有效RED；
修正native context替身后，上述exact baseline重现才是有效证据。
GREEN包含真实tuple消费及长度/KV交换/block/head/quant/layer/qlen漂移拒绝。
不修改FIA来迎合probe。

## 4. R02：失败与证据完整性独立

逐pair先验证输入/完整pre-KV对齐；不对齐仍OPEN，不是数值错误。
已对齐output或post-KV差异才FAIL。集合聚合优先FAIL，但同时明确记录其他pair的
INVALID/OPEN/缺失和collection omissions。即使有采集上限遗漏，已存在的对齐FAIL不被吞掉。
数值失败与不完整可同时成立。非空hash也不使FULL_TARGET变READY。

## 5. R03：预先冻结容差与范围

仅C2 private FP16 uniform fixture使用atol=0.016/rtol=0。
正常值<32，每次输入/输出half-ULP≤1/128，保守和≤0.015625；
nonaligned仅一个高sentinel，输入量化误差按1/1025稀释。
测试逐control/channel用实际FP16输入量化、float64均值和FP16输出舍入
与独立未量化oracle比较，均小于0.016。这个Host量化核对不是native FIA误差上界证明。
native还须在同一预设阈值下通过，不能按未来设备结果调大。
容差写入scope.numerical_acceptance并受manifest digest/source校验。
G4F使用自己的预声明容差，不能自动继承0.016。

“仅改窗口外KV”的设备control **NOT_IMPLEMENTED**。
原报告“窗口外扰动”过度声明撤销；人工checker负例不算device control；
A/B改变可见表/长度，nonaligned改变可见tail，不可冒充隔离外部扰动。
即便以后实现，该对照也不能证明硬件physical non-read。

## 6. R04联合验收

旧反例：完整synthetic B0内部graph记录、每请求仅2tokens、无外部launcher，
旧checker B0=PASS。见`logs/r04-baseline-counterexample.json`，这是Host反例，不是设备证据。

新生产诊断driver在加载模型前只读一次请求文件，保存raw SHA256和parsed entries，
随后执行该list；launcher在起子进程前独立hash同一文件；output记录实际提交prompts。
plan保存expanded argv及run/case/attempt/mode/source/hash。
`check-joint`同时核对这些值、PID、Host时间区间、每个group和每个请求16tokens、
status/startup、无遗漏/重复/乱序、exit0/signal=null/timeout=false及cleanup错误。
不同身份INVALID_EVIDENCE；身份对齐但执行失败FAIL。B0嵌套保留原checker结果。
其他case的joint PASS只证明外部执行/请求完成，不自动关闭S>0/数值/physical Gate。

A1要求NotImplementedError含GRAPH_FROZEN、无正常outputs及driver映射后的exit0。
OOM/资源错误/timeout不是预期拒绝。ABORT使用独立`check-abort`：
exact injected error + manifest digest/identity + child exit2/no timeout + unsafe reuse rejected；
只可得到EXPECTED_ABORT_OBSERVED，不证明completion或正常功能PASS。
原始campaign/launcher/checker不会被重写。

## 7. 验证

环境：Mac、repo .venv Python3.12、VLLM_VERSION=0.29.0、PYTHONPATH=../vllm。
NPU未运行。测试类型：真实Python生产参数构造/元数据合同，native边界Host替身；
checker合成证据明确只作负向验证；launcher测试实际启动无NPU的Host子进程。

|检查|结果|
|---|---|
|R01/R02 exact baseline RED|4 failed（预期）|
|R03/R04扩展合同先测|16 failed（未实现manifest/API，预期）；旧B0短输出反例另独立复现|
|Repair4工具/Repair2 campaign中间GREEN|318 passed|
|最终受影响完整回归|834 passed，2 subtests passed，1 upstream _version warning，无skip|
|优化模式checker回归|184 passed，python -O下显式校验保留|
|Ruff/format|PASS|
|定向Mypy|5 source files PASS|
|compileall / git diff --check|PASS|
|适用12项staged hooks|PASS（ruff/check/format、codespell、typos、Gitleaks、filename、init、logger、import、boolean、long-function、symbolic）|
|完整format.sh ci|ENVIRONMENT_BLOCKED：npm11.9拒绝markdownlint git+file安装，非PASS|
|整套默认pre-commit初始化|ENVIRONMENT_BLOCKED：actionlint所需Go下载解压EOF；非PASS|
|安全扫描|官方checksum验证的Gitleaks8.30.1；staged及Repair3→final两commit扫描无leaks|

hooks还揭示原fixture `import re`违反仓库规则；改为`import regex as re`并复验，
没有关闭/跳过检查或使用--no-verify。未修改hook配置。完整环境初始化阻塞历史保留。
不涉及的Markdown/Go检查无法由本轮Python检查PASS代替。

最终回归命令：

```bash
VLLM_VERSION=0.29.0 PYTHONPATH=../vllm .venv/bin/pytest -q \
 tests/ut/spec_decode/test_graph_repair4*.py tests/ut/spec_decode/test_graph_repair2_campaign.py \
 tests/ut/spec_decode/test_draft_window_graph*.py tests/ut/spec_decode/test_draft_window_capture_observer.py \
 tests/ut/spec_decode/test_draft_window.py tests/ut/spec_decode/test_draft_window_runtime.py \
 tests/ut/spec_decode/test_draft_window_eager.py tests/ut/spec_decode/test_draft_window_eagle3.py \
 tests/ut/spec_decode/test_dspark_speculator.py tests/ut/spec_decode/test_dspark_graph_contract.py \
 tests/ut/worker/test_attn_utils_v2.py tests/ut/attention/test_attention_v1.py \
 tests/ut/worker/v2/test_v2_block_table.py
```

## 8. 最终文件范围

```text
.../spec_decode/test_graph_repair4_acceptance.py   | 166 ++++++++++++++++++
 tests/ut/spec_decode/test_graph_repair4_fixture.py |  21 +++
 tests/ut/spec_decode/test_graph_repair4_target.py  |  89 +++++++++-
 tools/p7x_graph_repair2.py                         |  20 ++-
 tools/p7x_graph_repair4_acceptance.py              | 193 ++++++++++++++++++++-
 tools/p7x_graph_repair4_campaign.py                |  30 ++++
 tools/p7x_graph_repair4_fixture.py                 |  13 +-
 tools/p7x_graph_repair4_target.py                  |  68 ++++++--
 8 files changed, 570 insertions(+), 30 deletions(-)
```

完整review diff和Repair3→final combined diff在review ZIP。
没有模型、运行日志或Notes进入Git；实验模型路径只存在原有driver合法参数。

## 9. 发布及独立恢复

- GitHub身份：LucianWQZ，API核实repo `LucianWQZ/vllm-ascend`，push=true。
- 沙箱内最初显示失效/无法连接；在正常授权环境外同一keyring有效，未重复登录。
- 实际采用现有系统HTTP代理127.0.0.1:15236；单命令配置，不修改全局proxy/TLS。
- 发布前远端Repair4分支不存在；只普通push指定ref，其他remote heads逐项相同。
- 时间：2026-10-20T03:40:34.639208+00:00 至 2026-10-20T03:41:02.859729+00:00。
- `gh repo clone LucianWQZ/vllm-ascend <fresh> -- --single-branch --branch fix/p7x-graph-base-a3-repair4`
- 独立目录：`/var/folders/jg/1291_6m930x__sj1qzy3kdsh0000gn/T/repair4-github-cleanroom-tiyjzlz3/vllm-ascend`，从GitHub网络clone，非本地objects/worktree/bundle。
- API branch/commit及独立clone：SHA `08c94a99032c47e2608b976c25065adbbc8dea09` / tree `7d58b3414a9911662604634198c32e98094b15cf` / parent `aaa4632612503adb34d90b55c36eedcaf0848979`。
- ancestor检查通过aaa46326、10cbf4c、8198ab7a、841dc6cc；5个工具SHA256与本地逐一相同。
- 原始fixture manifest SHA256仍为 `1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4`；
  它是私有输入包文件，刻意不在Git，未伪称从GitHub获取。
- 两仓clean；vLLM SHA `84030bbe3d74d99bad477a3d2e37a973ccd8865c` /
  tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` unchanged。
- 无amend/rebase/force/PR/tag/merge；无服务器实验。

实际push：

```bash
git -c http.proxy=http://127.0.0.1:15236 push -u origin refs/heads/fix/p7x-graph-base-a3-repair4:refs/heads/fix/p7x-graph-base-a3-repair4
```

## 10. 服务器下一步与未闭环

只在新SHA exact preflight后，按COMMANDS和plan依赖运行：
P0→A0→A1→B0（联合验收）→B1/B2；observer OFF对照；
C2 private、G4/G4F observation、T0/T1能力探测、G5/ABORT diagnostic、R0。
固定DSpark TP1、q=K7、W1024、B128、capacity1151、capture[7,14,28]不变。
不减少bucket，不eager fallback，不使用未提交补丁。

仍OPEN：task内部operand、physical read、unsynchronized设备timeline/reuse、
FULL_TARGET确定性对齐/跨allocator逻辑映射、新SHA所有NPU实测。
outside-only KV control未实现。所有G1–G5 closure就绪=NO。
真实数值失败、native错误停止依赖case；工具缺失/未运行项不得造PASS。
G4F因边界变化仍必须在设备重新证明，不从Host通过推断FIA correctness。

## 11. 交付索引与状态

当前有效：本报告、最新handoff、Server_Input_Pack、review_fix_publication ZIP、
Publication_Download_Manifest。历史Download_Manifest只对archive中的旧包有效。
每ZIP含ARTIFACT_INDEX、SHA256SUMS、REPAIR4_PACKAGE_INDEX，CRC/成员hash/JSON/引用已验证；
服务器包内handoff与外部字节相同。执行源码只取上述Git commit。

```text
PUBLICATION: VERIFIED
CLEAN_ROOM: VERIFIED
FINAL_SHA: 08c94a99032c47e2608b976c25065adbbc8dea09
FINAL_TREE: 7d58b3414a9911662604634198c32e98094b15cf
FINAL_PARENT: aaa4632612503adb34d90b55c36eedcaf0848979
R4_REVIEW_FINDINGS: 4 ACCEPTED / FIXED
READY_FOR_A3_SCOPED_CAMPAIGN: YES
READY_FOR_ALL_G1_G5_CLOSURE: NO
NEW_SHA_DEVICE_VERIFICATION: NOT_RUN
PUBLIC_GRAPH_GATE: STILL_FROZEN
```

## 12. 关键diff（供独立审阅）

```diff
diff --git a/tools/p7x_graph_repair4_target.py b/tools/p7x_graph_repair4_target.py
index be5d3ebba..13c0b4559 100644
--- a/tools/p7x_graph_repair4_target.py
+++ b/tools/p7x_graph_repair4_target.py
@@ -589,9 +589,36 @@ class LiveTargetAdapter(FullForwardCheckpointer):
             expected[signature] = name
         seen = set()
         for param in captured:
-            _require(isinstance(param, tuple) and len(param) == 23, "unknown captured FIA parameter schema")
+            # full_graph_fia: 17 base operands, four quantization slots, layer.
+            # full_graph_fia_v2/PA and future tuple revisions are not this schema.
+            _require(isinstance(param, tuple) and len(param) == 22, "unknown captured FIA parameter schema")
+            _require(
+                all(isinstance(param[i], torch.Tensor) for i in (0, 1, 2, 3, 11, 12))
+                and (param[4] is None or isinstance(param[4], torch.Tensor)),
+                "invalid captured FIA tensor fields",
+            )
             signature = (_view(param[1]), _view(param[2]))
             _require(signature in expected and signature not in seen, "captured KV read inventory mismatch")
+            name = expected[signature]
+            impl = context[name].impl
+            _require(
+                param[5] == context[name].kv_cache[0].shape[1]
+                and param[8:11] == (impl.num_kv_heads, impl.num_heads, impl.scale)
+                and param[16] is None
+                and all(value is None for value in param[17:21])
+                and param[21] in (None, name),
+                "captured FIA geometry/quantization/layer schema mismatch",
+            )
+            _require(
+                all(
+                    isinstance(param[i], list) and param[i] and all(type(v) is int and v >= 0 for v in param[i])
+                    for i in (6, 7)
+                )
+                and len(param[6]) == len(param[7])
+                and param[7][-1] == n
+                and all(type(param[i]) is int for i in (13, 14, 15)),
+                "invalid captured FIA sequence/sparse fields",
+            )
             seen.add(signature)
         _require(seen == expected.keys(), "uncaptured target KV layer")
         inputs = {
@@ -700,29 +727,40 @@ def main() -> int:
         "update_effective_generation": "UNKNOWN",
         "block_mapping_comparison": "EXACT_PHYSICAL_IDS_NO_LOGICAL_REMAP",
         "pairs": [],
+        "confirmed_failure_count": 0,
+        "evidence_complete": False,
     }
     try:
         a, b = (torch.load(path, map_location="cpu", weights_only=True) for path in (args.left, args.right))
         _require(a.get("schema") == b.get("schema") == SCHEMA, "invalid collection schema")
-        if (
+        omissions = bool(
             a.get("skipped_for_limit")
             or b.get("skipped_for_limit")
             or not a.get("records")
             or len(a["records"]) != len(b.get("records", []))
-        ):
+        )
+        if omissions:
             report["reason"] = "missing/unpaired records or bounded collection omissions"
-        else:
-            results = [
-                compare_records(x, y, atol=args.atol, rtol=args.rtol, tolerance_reason=args.tolerance_reason)
-                for x, y in zip(a["records"], b["records"])
-            ]
-            statuses = {result["observed_forward_pair"] for result in results}
-            report["pairs"] = results
-            report["observed_forward_pair"] = next(
-                status for status in ("INVALID_EVIDENCE", "OPEN", "FAIL", "PASS") if status in statuses
-            )
-            if all(result["alignment"] == "MATCHED_COMPLETE_DECLARED_PRE_KV" for result in results):
-                report["alignment"] = "MATCHED_COMPLETE_DECLARED_PRE_KV"
+        results = [
+            compare_records(x, y, atol=args.atol, rtol=args.rtol, tolerance_reason=args.tolerance_reason)
+            for x, y in zip(a.get("records", []), b.get("records", []))
+        ]
+        statuses = [result["observed_forward_pair"] for result in results]
+        report["pairs"] = results
+        report["confirmed_failure_count"] = statuses.count("FAIL")
+        report["evidence_complete"] = bool(results) and not omissions and all(s in ("PASS", "FAIL") for s in statuses)
+        report["evidence_issues"] = {
+            "invalid_pairs": statuses.count("INVALID_EVIDENCE"),
+            "open_pairs": statuses.count("OPEN"),
+            "collection_omissions": omissions,
+        }
+        # A proven aligned difference survives unrelated missing/invalid evidence.
+        candidates = set(statuses) | ({"OPEN"} if omissions or not results else set())
+        report["observed_forward_pair"] = next(
+            status for status in ("FAIL", "INVALID_EVIDENCE", "OPEN", "PASS") if status in candidates
+        )
+        if report["evidence_complete"]:
+            report["alignment"] = "MATCHED_COMPLETE_DECLARED_PRE_KV"
     except Exception as error:
         report.update(observed_forward_pair="INVALID_EVIDENCE", reason=f"{type(error).__name__}: {error}")
     payload = json.dumps(report, indent=2) + "\n"
```
