# P7-X Graph Base A3 Repair2 — Implementation and Readiness Report

Date: 2026-10-19 (Asia/Shanghai)  
Scope: DSpark TP1 Base capture observer repair, faithful Host regression, bounded next-campaign collection.  
Author: Codex; independent review and new-SHA NPU execution remain outstanding.

## 中文审查摘要

本轮已实际完成代码修复、真实结构回归、采集工具/检查器补强和独立签署提交，**没有 push，也没有启动服务器实验**。

**根因已复现，但服务器报告的过度归因已撤销。** 真实 `build_attn_metadata` 在一个 attention group 内只构造一个 metadata，再把它放到每个 layer key 下。因此第一次 attach 遍历第二个 layer 时就会看到已有属性并抛错。旧 UT 用单层/新对象的简化结构掩盖了这个问题。不需要假设“第二个 descriptor 复用第一个 metadata”，现有 A3 证据也不足以证明那件事。

**修复不是吞异常或覆盖旧 context。** 同一次调用按对象去重；先完整验证 provider、CaptureIdentity、Target 归属和已有 context，再原子挂载。同 owner/同 identity 重复操作保留原 context；其他 owner/identity 冲突拒绝；中途赋值失败回滚新增状态；metadata context 随 forward closure 生存，不在准备 scope 结束时提前清除。真实每层 FIA callback 仍逐次记录，所以去重挂载不等于丢失 layer 事件。

还修复了有源码和 RED 测试依据的相邻观测问题：capture callback 内不再写文件/查询完成事件；REPLAY 到 UPDATE 提交之间不再为 source spy 做 D2H；输出 hash 的 D2H 移到 UPDATE 提交之后。**功能调用顺序仍然是 REPLAY → CONSUMER → UPDATE**，没有前移 UPDATE，没有新增全局 synchronize，也没有冒认设备生效代际。

本地结果：定向 **171 passed**；完整相关回归 **808 passed / 13 skipped / 7 failed / 25 subtests passed**。7 个失败在未修改的 `13373fff` 基线上同环境重现，均为 VWN Host backend 选择失败，不能把整套写为 PASS。Ruff、format、targeted Mypy、compileall、diff-check 和本机可执行 hooks 通过；完整 pre-commit 因 GitHub DNS 失败记为 `ENVIRONMENT_BLOCKED`。

本轮交付的服务器入口为 `tools/p7x_graph_repair2.py`，提供固定 A0/A1/B、observer-off、真实 inventory、逐层 operand、canonical-input 独立 oracle、Target-head/写侧快照、trace 能力探测和严格检查器。六段 JSON 已逐对象恢复并核对原始 bytes/SHA256；两个 command ledger 分片顺序合并后完整覆盖 CMD-0001～CMD-0030。历史 checker 的 26 PASS 只是失败归档完整性，不是 Graph PASS。

**必须保留的限制：**

- `READY_FOR_A3_RERUN=YES` 仅表示可以执行固定 smoke 和有界采集；不是保证下一轮一次关闭所有 Gate。
- L3 task 内部地址、L5 physical read-set、L6 update/completion 时序仍需设备 trace；工具能力未经验证，不承诺 msprof 一定能提供。
- Target probe 已能采集真实 `compute_logits` 输入/输出，但全 Target 数值比较还缺受控 tokens/history/KV/positions 对齐；不能用同 prompt/seed 或 head-only 相等代替。
- 自然 A/B/A′ 不保证物理 block ID 恰好恢复；严格设备 A/B/A′ 与 in-flight abort 仍开放，未通过改活跃 canonical table 或 sleep 造证据。
- 旧 alias 修复的 Host 回归仍通过，但 repair1 A3 未到达 bind；新 SHA 必须重新在 A3 到达该点。
- public Graph Gate 仍冻结；TP16/Prefix/Eagle3/DSA/MLA/Async/混合/multi-group 等 Batch A 均未扩展。

后文提供足够独立审查的源代码关系、关键 diff、RED/GREEN 输出、GAP-001～010 处置、固定模型 hash、可执行命令、必需回传件和停止条件。不会要求审查者仅凭本机日志链接相信结论。

## 1. Executive result and limits

```text
LOCAL_REPAIR_HOST_VERIFIED: YES
READY_FOR_A3_RERUN: YES — fixed-contract smoke and bounded evidence collection
ALL_G1_G5_CLOSURE_AUTOMATED: NO
NEW_SHA_DEVICE_EXECUTION: NOT_RUN
PUBLIC_GRAPH_GATE: STILL FROZEN
BATCH_A: NOT_IMPLEMENTED / BLOCKED UNTIL BASE G1–G5 PASS
PUSH: NOT_PERFORMED
```

The confirmed defect is **iteration over layer keys rather than unique metadata objects**. The real Ascend builder produces one metadata object per attention group, then places that same object under every layer name in that group. On the old code, the second layer of the **first attachment call** can raise `capture operand observer is already attached`. A second descriptor is not required to reproduce the failure.

This repair makes attachment atomic and same-owner/same-capture-identity idempotent, without overwriting another provider/descriptor's context. It leaves immutable context with its metadata/forward closure until that object is released. Deduplication applies only to attachment; actual per-layer FIA calls still each record an operator event.

Additional concrete observation defects were addressed: capture callbacks no longer serialize/query events/write files; source-stage observation no longer performs D2H between replay and the backend UPDATE; evidence output hashing runs only after UPDATE submission. The functional `REPLAY → CONSUMER → UPDATE` ordering is unchanged. These are observation safety repairs, **not proof of the device's effective update generation**.

The repository now contains a reusable driver and a stricter checker. They verify exact source, the original fixture hashes, actual capture/replay buckets, nonempty per-layer operand evidence, raw-canonical-input math, and record provenance. Observer-off is independent of the experimental candidate flag. Target-head output and full-write snapshots can be collected without changing return values.

Remaining limitations are deliberate and material:

- No NPU executed locally; no captured task-internal operand address, physical memory read-set, effective UPDATE generation or device reuse proof is claimed.
- Tools exporting the required L3/L5/L6 fields are `CAPABILITY_UNVERIFIED`. `msprof --help` or an option named MemoryAccess cannot close these gates.
- The driver collects real Target logits-head inputs/outputs, but does **not** manufacture a controlled full-Target/KV alignment fixture. G4 full numerical equivalence remains OPEN until those inputs/history/KV/positions are aligned.
- The natural A/B/A′ request attempt does not guarantee the allocator returns identical physical block IDs. Strict device A/B/A′ remains OPEN if that condition is not realized. No active canonical table is edited.
- Mid-flight device abort/completion cannot be established by the synchronous driver or Host fake events. This is explicitly separated from the fixed smoke.
- Full local regression retains seven reproduced baseline Host failures; the network-dependent pre-commit runner is environment-blocked. Neither is reported as PASS.

Therefore `READY_FOR_A3_RERUN=YES` means the next engineer can run the exact smoke and obtain non-vacuous evidence/failures using committed entry points. It does **not** mean every G1–G5 acceptance question has already been solved, or that the next device run is guaranteed to pass.

## 2. Exact source identity and safety

| Item | Value |
|---|---|
| Ascend repo | `/Users/wenqingzhang/Desktop/vllm/vllm-ascend` |
| Base branch | `fix/p7x-graph-base-a3-g1g5` |
| Base SHA | `13373fff637e819f3db125e05064f94cba3475a3` |
| Base tree | `739cde3de61e65be7cdbd187baebb6d17da04aee` |
| Base parent | `8cb4bed670f395c257c1233db944395159916009` |
| Final branch | `fix/p7x-graph-base-a3-repair2` |
| Final SHA | `1870e0ba8a00eeeae16c27f877e81eb65b711080` |
| Final tree | `a913b534d4a731cdcbca8256f42f0c1a3a6dc0a6` |
| Final parent | `13373fff637e819f3db125e05064f94cba3475a3` |
| Commit subject | `fix(spec-decode): repair shared capture observers and A3 evidence collection` |
| Sign-off | `Lucian <2207456347@qq.com>`; existing repository identity |
| vLLM repo | `/Users/wenqingzhang/Desktop/vllm/vllm` |
| vLLM SHA | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| vLLM tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |
| Initial/final source worktrees | clean; vLLM zero diff throughout |

Initial audit found the expected base, no later local commit on the working branch, and no user changes. A new branch was created without reset/rebase/amend. `AGENTS.md` was read; environment configuration is centralized in `envs.py`; the commit is signed off. A detached base worktree was used only for baseline failure comparison. No server login, GitHub push, PR, tag, upstream edit or Batch A implementation was performed.

Lineage:

```text
1b7215c37d1e3c9d1edac1fc20bcad26917ca251
  → c43989aabd9b40a561987d39f4ba4516934f2f5b
  → 8cb4bed670f395c257c1233db944395159916009
  → 13373fff637e819f3db125e05064f94cba3475a3
  → 1870e0ba8a00eeeae16c27f877e81eb65b711080
```

## 3. Inputs, strict recovery and immutable raw evidence

Original input directory, kept read-only:
`/Users/wenqingzhang/Desktop/Note/MRV2/g1-g5_repair1/`.

Actual files inspected:

- `P7X_A3_00_Return_Index.md`
- `P7X_A3_01_Report_CN.md`
- `P7X_A3_02_Execution_Record.md`
- `P7X_A3_03_Device_Facts.json`
- `P7X_A3_04_A0_A1_B_Record.md`
- `P7X_A3_05_G1_G5_Decisions.md`
- `P7X_A3_06_Evidence.json`
- `P7X_A3_06_Evidence.part001.json` — actually six comma-delimited JSON objects
- `P7X_A3_07_Raw_Text_Evidence.md`
- `P7X_A3_07_Raw_Text_Evidence.part001-006.md` — one combined Markdown file, not six separately present files
- `P7X_A3_08_Failures_And_Limits.md`
- `RETURN_TO_LOCAL_Graph_Mandatory_Gap_Report.md`
- `gate_status.json`, `independent_checker.log`, `independent_checker_final.log`, `independent_checker_result.json`, `result.txt`.

Related Notes used as design/history sources, not replacements for production source:

- `MRV2_Speculative_Draft_Sliding_Window_Final_Design.md`
- `MRV2_Draft_Window_Implementation_Plan.md`
- `P7X_Graph_Base_A3_Failure_Root_Cause.md`
- `P7X_Graph_Base_A3_Fix_Design.md`
- `P7X_Graph_Base_A3_Fix_Implementation_Report.md`
- `P7X_Graph_Base_Fix_Test_Report.md`
- `P7X_Graph_Base_A3_Fix_GitHub_Publication_Audit.md`
- `P7X_Graph_G1_G5_Observability_Audit.md`
- `P7X_Graph_G1_G5_Rerun_Handoff.md`
- `P7X_Graph_Node101_A3_G1_G5_Server_Experiment_and_Evidence_Spec.md`.

No historical document or Frozen Design was rewritten. This report supersedes the old campaign's unsupported root-cause inference and insufficient checker success interpretation, not its raw evidence.

### 3.1 Recovery algorithm

`recover_evidence.py` uses `JSONDecoder.raw_decode` repeatedly. It verifies whitespace/comma separators, rejects unexpected trailing content/trailing comma, requires six objects, `part_index=1..6`, `part_count=6`, and `run_id=20261019_055109_13373fff`. Record counts must be exactly `[5,4,5,1,1,3]`.

For each object it preserves the **original substring**, adds the original final newline, and hashes those UTF-8 bytes. It does not hash `json.dumps` output as if it were original evidence. All six recovered byte counts and SHA256 values matched the return index:

| Part | Records | Bytes after restoring final LF | SHA256 |
|---|---:|---:|---|
| 001 | 5 | 21553 | `2a918472ec80053690c23c40641d28fe2e7b665415327e78bce18e90b0204b62` |
| 002 | 4 | 19225 | `5b61c39aeef6610fb0f5e567170e578ed22ab0e15b9dc135f4aa913a3a271deb` |
| 003 | 5 | 26991 | `706c7de729f20ea7fd40252c2e939efcd20fc26b4f23ac8f4e7d3818f762f839` |
| 004 | 1 | 31257 | `621ea4e579c43642fbe1ea92dfe76e90ebbe8db30061041ac9d921b14946fc9f` |
| 005 | 1 | 42867 | `9f08e3e2f4020ee9e2cb0fb4f81b2577b162e6b6e0d1c5f2b0153c41dffe1125` |
| 006 | 3 | 25538 | `35364e2256403887f5dfd46a2a0671287f83ed8d5c426db38536faeb956f1adf` |

`EVID-COMMAND-LEDGER` is a list in each of parts 004/005. The two lists were concatenated in that order, not merged by dictionary key. The resulting 30 entries were checked against `CMD-0001` through `CMD-0030`, with no omission or overwrite.

Recovered originals are in `g1-g5_repair2_local/evidence/P7X_A3_06_Evidence.part00N.json`. Individual `EVID-*.partN.json` and `command_ledger_merged.json` are explicitly **derived/reformatted** files; their hashes are not the original server hashes. Rich-text Markdown snippets were never executed. Production facts came from Git source.

### 3.2 Checker versions

The embedded earlier checker snapshot is 25 PASS / 1 OPEN. The final independent file is 26 PASS. CHK-025 checks delivery-file completeness. It changed, not the failing B capture or Graph functionality. The final 26 PASS means the **historical failure archive was internally checked**, not that G1–G5 passed.

## 4. Re-adjudication of server observations

| Claim | Classification | Decision |
|---|---|---|
| A0 outputs normally on repair1 | Original fact | Accept for `13373fff` and that exact environment; rerun new SHA |
| A1 rejects with GRAPH_FROZEN | Original fact | Accept; public gate stays unchanged |
| B fails during startup observer attachment | Original fact | Accept exact stack/message below |
| Partial artifact has events=1, operands=0, G4=0, lifecycle=0 | Original fact | Before runtime bind/publish/replay; no empty-set functional PASS |
| Second descriptor reused first metadata | Report inference | Not proven by metadata identity chain; not used as root cause |
| First attach can encounter the same group object twice | Source + faithful RED proof | Confirmed defect; sufficient to explain observed exception without cross-descriptor reuse |
| Repair1 alias defect is gone on device | Not yet proved | Its old failure point was not reached in repair1 B |
| Single-size diagnostics emitted text, therefore Graph works | Unsupported inference | Reject promotion; inspect actual manager inventory and replay path |
| Helper capture record proves FIA operand/task binding | Unsupported inference | Helper is not actual operator or task-internal evidence |
| L3/L5/L6 established | Not proved | OPEN: no qualifying device trace |

Key raw traceback from `EVID-B-RESULT`, with long common path prefix omitted:

```text
vllm/v1/worker/gpu/model_runner.py:999 → self.speculator.capture()
vllm/v1/worker/gpu/spec_decode/dflash/speculator.py:150
vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py:96 → super().capture(...)
vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:121
vllm/v1/worker/gpu/cudagraph_utils.py:382
    forward_fn = create_forward_fn(desc, warmup=True)
vllm/v1/worker/gpu/spec_decode/dflash/cudagraph.py:99
    attn_state = _prepare_dflash_inputs_to_capture(...)
vllm_ascend/worker/v2/spec_decode/dflash/capture.py:376
    attach_parallel_graph_capture_operand_observer(...)
draft_window_graph_characterization.py:1006
    raise RuntimeError("capture operand observer is already attached")
RuntimeError: capture operand observer is already attached
```

The evidence is a warmup factory exception, not a replay exception. The device artifact lacks the complete chain of object IDs needed to assign it to a second descriptor.

## 5. Real object structure and lifecycle

Paths in this section are relative to the exact final Ascend repo unless prefixed `vllm/`.

```text
DFlashAclGraphManager.capture (dflash/aclgraph.py)
  → draft_window_dflash_capture_scope(owner, private Draft InputBuffers, descriptors)
  → pinned DFlashCudaGraphManager.capture
      → create_forward_fn(desc, warmup=True)
          → ascend_prepare_dflash_inputs_to_capture (dflash/capture.py:294)
              → worker/v2/attn_utils.py:226 build_attn_metadata
                  → AscendAttentionMetadataBuilder.build_for_cudagraph_capture
                  → AscendAttentionMetadataBuilder.build
              → record_capture helper (not operator)
              → attach observer to Draft metadata
          → closure retains AttentionState.attn_metadata
      → warmup forward(s)
      → create_forward_fn(desc, warmup=False), new metadata build
      → graph capture forward
          → AscendAttentionBackendImpl.full_graph_fia
          → npu_fused_infer_attention_score.out
          → graph_task_group_end
          → per-layer capture operand callback
  → scope finally: remove InputBuffers preparation context; flush evidence
     (do not detach the metadata retained by closures)
```

Real builder logic (`attn_utils.py`, end of group loop):

```python
metadata = builder.build_for_cudagraph_capture(common_attn_metadata)
for layer_name in attn_group.layer_names:
    attn_metadata[layer_name] = metadata
```

The metadata builder creates a new `self.metadata_cls(...)` on each build for the selected dense FIA route. Its inherited `build_for_cudagraph_capture` delegates to `build`. No metadata-object cache was found on this path. Within one group build, however, **all layer entries deliberately alias the same object**. That is normal architecture, not stale storage.

| Question | Proven answer and boundary |
|---|---|
| Same mapping repeats same object? | Yes, one object per group under multiple layer keys |
| Different groups use same object? | Real test with separate builder calls gets distinct metadata; no broad cross-group support claim |
| Warmup and capture same object? | Selected builder called twice → fresh objects; tested through actual upstream closure factory |
| Different descriptors same object? | Selected path builds fresh; six objects for 3 descriptors × warmup/capture in faithful Host test. Device identity chain remains to be recorded |
| Builder cached object? | Not on selected route; masks/resources can be reused, but not the metadata root tested here |
| What does closure retain? | AttentionState with metadata mapping from that factory invocation |
| Old attach leaves partial state? | Yes: old loop sets first object then raises on duplicate/conflict; new atomic logic fixes this |
| May old context still be consumed? | Yes if a closure still references metadata. Therefore no overwrite/detach on later descriptor |
| Target object gets attached? | New preflight rejects any metadata root found in the actual Target mapping; tests assert no Target context |

The new faithful tests use real Ascend group assembly and real `AscendAttentionMetadataBuilder.build_for_cudagraph_capture/build`. Only hardware services (`pin_memory`, graph scope/NPU primitives) and necessary configuration scaffolding are substituted. They do not replace the critical builder with “return a fresh SimpleNamespace per layer.”

## 6. RED evidence before production repair

Environment: Mac Host, Python 3.12.14, PyTorch 2.14.1, pytest 9.1.1, no NPU. Tests use the repository's normal Host shims. `VLLM_VERSION=0.29.0`, `PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm`.

Initial test-first command on base `13373fff` (the test file then contained the first three cases):

```bash
VLLM_VERSION=0.29.0 \
PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
.venv/bin/pytest -q tests/ut/spec_decode/test_draft_window_capture_observer.py
```

Saved `red.log`, exit 1:

```text
FAILED test_real_group_builder_shared_metadata_reaches_every_layer[False]
FAILED test_real_group_builder_shared_metadata_reaches_every_layer[True]
FAILED test_attach_conflict_is_atomic_and_retryable
3 failed
...
if hasattr(layer_metadata, _CAPTURE_OPERAND_CONTEXT_ATTRIBUTE):
    raise RuntimeError("capture operand observer is already attached")
RuntimeError: capture operand observer is already attached
```

`[False]` is the real shared-group structure and fails on its first build. `[True]` uses distinct group objects and reaches the deliberately repeated same-identity attach, which also incorrectly failed on old code. The third test exposes prevalidation/partial-attachment semantics.

A separate RED check of the existing submitted-source observer on base, saved as `red-pre-update-sync.log`, installs a real bound/submitted provider and fails any call to `_tensor_rows/_tensor_values` before UPDATE:

```text
test_no_blocking_observation_between_replay_and_update
Failed: blocking D2H before UPDATE
1 failed (exit 1)
```

This proves the old observer attempted blocking snapshots in that interval. It does not claim the repair1 device run deadlocked there; repair1 never reached replay.

Checker tests were also written first. `red-tools.log` records 15 failures before the new tool existed. Later `red-record-scope.log` records three failing cross-recorder/process/provider splice cases before per-record provenance was enforced. These are test-first tool-contract checks, not device failures.

## 7. Repair design and ownership semantics

### 7.1 Attachment state rules

| Input/state | Behavior |
|---|---|
| No observer/provider observation disabled | Exact no-op attachment |
| Repeated layer entries pointing to same object | Deduplicate in a call-local strong-reference collection |
| Same recorder/provider and equal registered CaptureIdentity already attached | Idempotent; retain the exact previous immutable context, no rewrite |
| Different recorder/provider, descriptor, bucket/backing identity, malformed context | Hard fail before any new attachment |
| Metadata root is Target root/value | Hard fail; never install on Target |
| Assignment fails partway | Roll back only new contexts installed by this transaction; preserve prior valid contexts; propagate failure |
| Preparation scope ends | Delete only private InputBuffers preparation attribute; metadata context stays with consumer closure |
| A later descriptor attempts to use an earlier object's still-live context | Reject conflict, do not relabel the old closure |

There is no module-global metadata-ID registry. The temporary `unique` dictionary is local and holds strong object references, avoiding `id()` reuse during the transaction. Persistent identity lives in the existing typed `DraftWindowGraphCaptureOperandContext` on that metadata object. No fake request/generation/epoch is introduced for capture.

Key diff (condensed, exact decision logic):

```diff
- for layer_metadata in metadata.values():
-     if hasattr(layer_metadata, ATTRIBUTE):
-         raise RuntimeError("capture operand observer is already attached")
-     setattr(layer_metadata, ATTRIBUTE, context)
+ provider.startup_capture_read_inputs(identity)  # identity/backing validation
+ unique = {id(m): m for m in metadata.values() if m is not None}
+ # Preflight every unique object; reject Target and conflicting contexts.
+ if previous.recorder is recorder and previous.identity == identity:
+     continue  # retain previous immutable context
+ # Only after preflight: install all pending objects transactionally.
+ try:
+     for m in pending:
+         attempted.append(m)
+         setattr(m, ATTRIBUTE, context)
+ except BaseException:
+     for m in reversed(attempted):
+         if getattr(m, ATTRIBUTE, None) is context:
+             delattr(m, ATTRIBUTE)
+     raise
```

The real callback remains at each `full_graph_fia` invocation. Shared metadata therefore does not collapse layer observations. A Host test executes the real FIA method for both layer objects with only NPU primitives mocked and obtains both layer event names, descriptor, provider and exact backing identity.

### 7.2 Observation safety near capture and UPDATE

Source facts (`attention_v1.py:1081` and `:948`): capture creates `ExternalEvent`, inserts `wait/reset(stream)` and records a task handle; UPDATE invokes the FIA update, `graph_task_update_end`, then `event.record(update_stream)`. These exact facts motivate avoiding a blocking D2H before UPDATE submission. They do not decide whether UPDATE(N) affects replay N/N+1 internally.

Changes:

```diff
 ret = super().run_fullgraph(desc)
 record_parallel_graph_replay_submission(owner)
-record_parallel_graph_output(owner, ret)  # D2H/hash could wait before UPDATE
 observe(...CONSUMER...)
 observe(...UPDATE...)
 update_full_graph_params(...)
+record_parallel_graph_output(owner, ret)  # evidence-only, after submission
```

`recorder.record(REPLAY/CONSUMER/UPDATE)` now refers to the unique BOUND snapshot, annotating `values_sampled_at_sequence`. Those values are explicitly **cached Host observations**, not freshly sampled device values. Operator callbacks retain identity/pointer/shape/CPU length recording, but perform no table D2H and no artifact serialization or event query. Capture scope's `finally` flushes outside capture. Actual Tensor length pointer, when used, must match the persistent exact backing; host-sequence lengths must equal typed exact lengths.

Artifact writes use an atomic temp/replace. I/O/serialization errors are retained in bounded `artifact_errors` and cause checker `INVALID_EVIDENCE`; they do not replace an original model exception in a `finally`. Recorder count is bounded at 16384 events, Target probe at 256 records; exhaustion is an explicit failure, never silent truncation.

### 7.3 Evidence identity and observer-off

The snapshot carries a UUID recorder ID, process ID, provider identity, schema/revision, Host monotonic clock domain and error list. Every serialized event has the same `record_scope`, which the checker validates. The driver envelope adds run/case/attempt, source SHA/tree, pinned vLLM SHA, engine ID, imports and config. These protect accidental archive mixing; they are not cryptographic attestation of device truth.

New centralized non-sensitive strict 0/1 variable:
`VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_OBSERVE`, default 1 **inside the already opt-in experimental candidate**. Setting it to 0 removes recorder callbacks, evidence D2H/hash and completion-observation events, while keeping the experimental Graph carrier and all contract checks. Setting the experimental feature flag itself to 0 remains A1/public `GRAPH_FROZEN`, not an observer-off test.

## 8. Changed files and regression risk boundary

Eight files, **+1733 / −51**:

| File | Change | Why / invariant |
|---|---|---|
| `vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py` | Atomic unique-object attach; Target guard; immutable-context validation; bounded/scoped evidence, raw oracle inputs, no pre-update D2H; observer-off | Fix capture metadata structure and evidence honesty without owner swap |
| `vllm_ascend/worker/v2/spec_decode/dflash/capture.py` | Carry actual Target mapping into attach validation; record layer→object IDs; flush after capture scope | Protect Target; prove sharing; no premature detach |
| `vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py` | Move evidence output hashing after update submission | No functional replay/update reorder |
| `vllm_ascend/envs.py` | Strict internal observer switch | Experimental route remains gated; no public Graph enable |
| `tests/ut/spec_decode/test_draft_window_capture_observer.py` | 393 lines of faithful builder/factory/operator/lifetime tests | Addresses original mock-structure blind spot |
| `tests/ut/spec_decode/test_draft_window_graph_characterization.py` | Strict call-order assertion changed to update-before-output-hash | Locks the observation fix, not a weakened assertion |
| `tests/ut/spec_decode/test_graph_repair2_campaign.py` | 312 lines of checker/oracle/probe negative tests | No empty/foreign/stale/numerically-missing evidence PASS |
| `tools/p7x_graph_repair2.py` | Committed bounded A0/A1/B/observer-off driver and schema checker, compare/probe/fixture entry points | Eliminate ad hoc server driver guessing; no model artifacts in Git |

No changes to `attention_v1.py`, `compilation/acl_graph.py`, upstream vLLM, planner, scheduler, allocator, public gate, non-Graph speculator path, or Batch A capability. Existing backend callback seams are reused, not replaced with a different graph manager.

### 8.1 Repair1 read/private vs full/write remains intact

The following existing logic is unchanged:

```python
private_isolation_view = _isolate_draft_metadata_from_target(metadata, target_metadata)
# Validate the private view separately from final canonical references.
final_layer_metadata = copy.copy(layer_metadata)
final_layer_metadata.slot_mapping = write_side.slot_mapping
final_layer_metadata.positions = write_side.positions
final_layer_metadata.query_start_loc = write_side.query_start_loc
# provider._validate_metadata_uses_carrier checks Window READ identity
# and the canonical full write/query contract independently.
```

Window table/device exact/CPU exact-upper/backend private state must not alias Target-private storage. Canonical slot/positions/query references are intentionally shared with the same full owner; they are not cloned to satisfy isolation. Target root/content, canonical tables and physical write semantics stay unchanged. The previous Window is never used as FullSource. This repair does not weaken the private-view validator or add broad field exemptions.

Relevant preserved regression names include:

- `test_real_target_metadata_sharing_is_allowed_for_full_write_carriers`
- `test_draft_private_fields_still_reject_target_storage_alias`
- `test_carrier_rejects_nested_target_aliases`
- `test_carrier_rejects_noncanonical_write_side_slot_owner`
- `test_runtime_candidate_rejects_early_overwrite_and_cleans_bound_state`
- `test_retired_or_stale_generation_cannot_be_observed`.

## 9. Final validation (not device certification)

### 9.1 Directly affected suite

```bash
VLLM_VERSION=0.29.0 PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
.venv/bin/pytest -q \
  tests/ut/spec_decode/test_draft_window_capture_observer.py \
  tests/ut/spec_decode/test_graph_repair2_campaign.py \
  tests/ut/spec_decode/test_draft_window_graph_characterization.py \
  tests/ut/spec_decode/test_draft_window_graph_carrier.py \
  tests/ut/spec_decode/test_draft_window_graph_binding.py \
  tests/ut/spec_decode/test_draft_window_graph_oracle.py \
  tests/ut/spec_decode/test_dspark_graph_contract.py
```

Final code result: **171 passed**, 1 version warning, exit 0 (`final-targeted.log`). No final-code skips/failures in this set.

Coverage mapping:

| Risk | Actual regression |
|---|---|
| Two layer keys same object; distinct objects | Real builder parametrized shared/separate group tests |
| Legitimate repeat | Retains original context object; records every layer |
| Warmup/capture; fixed descriptors | Actual pinned upstream closure factory; descriptors 4/28,2/14,1/7; warmup True/False; six fresh roots/twelve layer callbacks |
| Cross-owner/provider/descriptor | Reject preflight; old context/closure unaffected |
| Failure midway/retry | Injected setattr failure rollback; later valid retry; preexisting context preserved |
| Still-live old closure | Call retained first closure after later descriptors; same original bucket events |
| Actual operator path | Real `full_graph_fia` function, substituted NPU primitives only, two actual layer invocations |
| Observer absent/off | No attribute/no observation work, but experimental provider/carrier still binds when observe=0 |
| Target sharing and private aliases | Existing real-owner positive and nested Tensor/ndarray negatives retained |
| Pre-update sync | Fail-on-D2H probes in submitted-source observer and strict manager call order |
| Capture callback safety | Reject D2H/file writes in callback; wrong length Tensor pointer fails |
| Evidence integrity | Empty, missing identity, duplicate sequence, process/provider/recorder mix, I/O error, one-step lag, missing layer/bucket, wrong table/length/source |
| Numeric comparisons | Missing values/alignment → OPEN, differing controlled values → FAIL; no crossprocess pointer equality |
| Probe lifecycle | Instance methods restored even after business exception; original exception preserved |

### 9.2 Full requested relevant regression

```bash
VLLM_VERSION=0.29.0 PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
.venv/bin/pytest -q tests/ut/spec_decode \
  tests/ut/worker/test_attn_utils_v2.py \
  tests/ut/attention/test_attention_v1.py \
  tests/ut/worker/test_block_table.py \
  tests/ut/worker/v2/test_v2_block_table.py
```

Result: **808 passed, 13 skipped, 7 failed, 25 subtests passed**, one version warning, exit 1 (`final-regression.log`). This includes P1–P7X, DFlash/DSpark, Graph carrier/binding/characterization, eager Window and Target isolation tests. It is **not a suite PASS**.

All seven failures are in `test_speculators_vwn_eagle3.py`:

```text
TestVwnLlamaDecoderLayer::test_forward_layer0[4-1.5]
TestVwnLlamaDecoderLayer::test_forward_layer0[4-1.0]
TestVwnLlamaDecoderLayer::test_qkv_proj_input_size_layer0
TestVwnLlamaModel::test_forward[1-False]
TestVwnLlamaModel::test_forward[1-True]
TestEagle3VwnLlamaForCausalLM::test_init_and_forward
TestEagle3VwnLlamaForCausalLM::test_embed_input_ids
... vllm/v1/attention/selector.py:208
ValueError: Invalid attention backend for None
```

The same file was run with the same interpreter/env in an unmodified detached `13373fff` worktree: **7 failed, 2 passed**, exit 1 (`baseline-vwn.log`). No new skip/assertion removal/fixture substitution was used to hide them. Existing 13 skips are reported, not counted as pass. Version warning is missing local upstream `_version`, not a hidden patched vLLM.

### 9.3 Static and repository checks

| Command/scope | Result |
|---|---|
| Ruff 0.16.10 check, all eight changed files | exit 0 |
| Ruff format --check, same eight files | 8 already formatted, exit 0 |
| Mypy 1.11.1 `--follow-imports=skip --ignore-missing-imports`, tool + characterization + capture + aclgraph | Success, 4 source files, exit 0; targeted, not whole-repo typing proof |
| compileall, tool/spec_decode/tests | exit 0 |
| `git diff HEAD^ HEAD --check` | exit 0 |
| Tool `--help` | exit 0; subcommands present |
| Local hooks: python-init, forbidden imports, boolean context manager, long-functions, logger, symbolic-meta | exit 0 |
| `bash format.sh ci` via fresh PRE_COMMIT_HOME | **ENVIRONMENT_BLOCKED**, exit 3: GitHub DNS failure while fetching ruff-pre-commit |
| Complete pre-commit remote toolchain / configured Ruff v0.14.0 / gitleaks download | Not certified; local Ruff version above is not misreported as that remote hook |
| NPU / ACL capture / task trace | NOT_RUN, no NPU here |

The actual pre-commit failure was `Could not resolve host: github.com`; no hook was disabled to fabricate PASS. No NPU/performance result is inferred from these local checks.

## 10. GAP-001 through GAP-010 disposition

| GAP | Classification | Local action / evidence | Remaining closure |
|---|---|---|---|
| 001 | PROVEN_CODE_DEFECT | Same-call group alias RED → atomic idempotent unique-object attach GREEN; do not accept “second descriptor” as established cause | New-SHA A3 startup capture |
| 002 | DRIVER_GAP + DEVICE_NOT_RUN | Committed fixed `[7,14,28]` driver; checks actual Target/Draft inventories and actual BOUND/replay buckets, not request counts | All three actual replay buckets and no fallback on A3 |
| 003 | OBSERVABILITY_GAP + TOOL_CAPABILITY_UNVERIFIED | Per-layer actual operator-call ptr/shape/type + provider/descriptor/task-handle wrapper IDs; explicit task-internal address null | Qualifying ACL/task export, with ID/address correlation |
| 004 | TOOL_CAPABILITY_UNVERIFIED + ACCEPTANCE_CONTRACT_QUESTION | Raw-canonical independent oracle; boundary sweep and submitted operand comparison ready | Physical block/token read trace; MemoryAccess name alone insufficient; owner/tool team decision if impossible |
| 005 | DEVICE_NOT_RUN + OBSERVABILITY_GAP | Submission sequence, event/query source/clock, update task wrapper IDs, retire observed; pre-update blocking observation removed | Device happens-before and effective-generation trace, no early overwrite/reuse proof |
| 006 | DRIVER_GAP + ACCEPTANCE_CONTRACT_QUESTION | Optional real Target compute_logits input/output tensors + full/write snapshots; strict numerical comparator requires explicit aligned full-state ID/tolerance | Controlled full-Target tokens/history/KV/position alignment not implemented; head-only equality cannot close whole-Target Gate |
| 007 | DRIVER_GAP + DEVICE_NOT_RUN | Same-engine request sweep, record source lineage/generation/epoch/backing; Host A/B/A + stale/pressure tests; strict checker | Natural physical A′ may not match; no deterministic allocator fixture added. If not realized, return OPEN/fixture requirement, never edit active table |
| 008 | DEVICE_NOT_RUN + DRIVER_GAP | Host abort/exception/early-overwrite regressions preserved; original exceptions/partial outputs captured | `LLMEngine.abort_request` exists, but synchronous generate lacks safe known in-flight task-boundary injection. Controlled device abort remains NOT_RUN; no sleep/race hack |
| 009 | TOOL_CAPABILITY_UNVERIFIED | Bounded trace capability-discovery entry point and required field schema | Actual installed-tool command run + export + sufficiency audit on server |
| 010 | DEVICE_NOT_RUN | Repair1 real-owner/private-alias regressions still green; BOUND path requires both validators | A3 reaches old bind/alias point, publishes and truly replays |

Only 001 and the independently reproduced adjacent observation D2H defect are fixed production logic. Missing device traces are not relabelled production defects. The new code does not claim to close all remaining driver/fixture/tool questions.

## 11. Collection interfaces and evidence levels

| Data | Real entry point | Output/fields | Level / impact |
|---|---|---|---|
| Source/model/config identity | `tools/p7x_graph_repair2.py run` | campaign envelope SHA/tree/imports, fixture manifest, exact kwargs, argv, pid/engine/run/case/attempt | Host provenance; model file hash I/O before load |
| Actual capture inventory | `_manager_inventory(runner.cudagraph_manager)` and Draft query manager | descriptors + actual `graphs` keys; required 1/7,2/14,4/28 | Real Python manager inventory, not replay itself |
| Shared metadata | `record_capture(...metadata=...)` | `layer_metadata_ids` | Helper-level object structure; not FIA operand |
| Capture FIA operands | backend `full_graph_fia` callback | actual/expected table ptr, length kind/ptr or values, shape/dtype/device, layer/gid/backend/descriptor, provider, task/event/stream Python identities | `HOST_OPERATOR_BOUNDARY_FACT`; no callback D2H |
| UPDATE FIA operands | backend `update_graph_params` callback | above + runtime generation/epoch, captured-vs-update ptr, CPU exact/upper | Submitted operator-call operands; not task-internal binding |
| Raw independent math | recorder `record_g4` → `_runtime_oracle_inputs` | canonical rows, full E, full CPU upper, valid counts, mapping/request IDs, source identity, B/W/query | Opt-in D2H outside capture; NOT PERFORMANCE REPRESENTATIVE |
| Full write/query + Target | G4 record; optional `--target-probe` | canonical table, slot/positions/query ptr+values, Target root/layers/lengths | Same-process identity; crossprocess semantic alignment required |
| Target numeric | `TargetBoundaryProbe` on actual model instance `compute_logits` | `.pt` hidden/logits, dtype/shape/input hash; `full_target_kv_alignment=null` | Actual head input/output only; D2H, not performance |
| Lifecycle | replay event, backend ExternalEvent record, retire observer | sequence, generation/epoch, stream/event identities, query result/time/source | Host observation + API event status; not automatic device timeline |
| Trace discovery | `trace-probe` | installed/help exit/options/raw output, required-export list, unverified sufficiency | No device capture executed by this command |
| Checks | `check`, `compare-write`, `compare-target` | split status namespaces; explicit OPEN/NOT_RUN/INVALID_EVIDENCE | Evidence audit, not support certification |

Missing actual task address/physical read-set remains `null`. Object IDs are not promoted to ACL internal IDs. Capture has no request generation: `generation_id/mapping_epoch=null`, not fake zero. Runtime table/exact/upper are bound to the same identity; source-stage cached values carry their sample sequence. Raw device table content at the operator instruction itself is not copied during capture.

## 12. Frozen fixture/config for the next A3 run

```text
Target: /mnt/share/wql/Qwen3-8B
Draft:  /mnt/share/dspark_qwen3_8b_block7
MRV2 runner: vllm_ascend.worker.v2.model_runner.NPUModelRunner
Speculator: vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator
DSpark K=7, query width=7, sample_from_anchor=true
single executable group, STANDARD dense GQA/FIA direct-prefix
TP=DP=PP=PCP=DCP=1
async/prefix/SP/DSA-CP/FlashComm OFF
W=1024; block span=128; Window capacity=1151
Graph FULL_DECODE_ONLY; actual decode descriptor FULL
capture sizes=[7,14,28]; actual buckets=(1,7),(2,14),(4,28)
max_model_len=4096  # NOT 1151
max_num_seqs=4; max_num_batched_tokens=4096; GPU memory utilization=.80
seed=0; temperature=0; ignore_eos=true; max_tokens=16
enable_adaptive_verification=false
VLLM_USE_V2_MODEL_RUNNER=1; VLLM_ENABLE_V1_MULTIPROCESSING=0
```

These values are recovered from the original manifest/ledger. Do not search for a new fixture, reduce capture sizes, silently use eager, or replace MRV2. Verify current A3 runtime versions against the prior record (torch 2.10.0+cpu / torch_npu 2.10.0.post4 / CANN 9.1.0 / driver 26.0.rc1). Any difference must be recorded, not hidden. The prior visible die was 5; reselect only an authorized idle A3 die and record it, rather than assuming 5 is still free.

The auxiliary `fixture_manifest.json` contains these ten original SHA256 values:

| File (relative to Target/Draft root) | SHA256 |
|---|---|
| Target config.json | `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30` |
| Target model.safetensors.index.json | `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc` |
| Target tokenizer.json | `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4` |
| Target model-00001-of-00005.safetensors | `31d6a825ae35f11fb85b195b4c42c146c051e446433125a215336abdf95cbf5f` |
| Target model-00002-of-00005.safetensors | `5991236cea6fe21f3d43cab0f0e84448734fbbe0789816202989f2ddc9d18282` |
| Target model-00003-of-00005.safetensors | `c5185c4794be2d8a9784d5753c9922db38df478ce11f9ed0b415b7304d896836` |
| Target model-00004-of-00005.safetensors | `b5ee7de71fbf17db3d5704e0c8f2bc7d005ca9e1d7ca2aeb19827b0cfcaa917a` |
| Target model-00005-of-00005.safetensors | `20c2d6366ab85c90786ccdd829cd2b9e7d30ef3b2ebbb998280e7e4014b542ff` |
| Draft config.json | `e470e70a553616f0dce8f783f42cfd25b7bd7dfdcd57ead680a0623040725611` |
| Draft model.safetensors | `5c922d1f96c8d18dbdf005c40ea99878d9133d70eaa3be4bd1077ee5f2afc1e5` |

## 13. Executable server handoff (after review and separately authorized publication)

This commit has **not** been pushed. Do not ask Node101 to fetch a nonexistent remote branch now. First complete independent review and the separately authorized publication workflow. Then clean-fetch the exact SHA/tree above. Do not manually paste a fix into server production or execute rich-text code from historical evidence.

### 13.1 Preflight and fixed smoke

Use the trusted existing server environment with matching runtime libraries. Set `ASCEND_REPO`, `VLLM_REPO`, `RUN_ROOT`, `FIXTURE_MANIFEST` to the actual deployment paths; these are path placeholders, not guessed server source directories. Output must be outside both Git trees. Copy the supplied fixture manifest from the Notes auxiliary bundle.

```bash
export ASCEND_REPO=<clean-new-Ascend-checkout>
export VLLM_REPO=<clean-pinned-vLLM-checkout>
export RUN_ROOT=<new-empty-campaign-directory>
export FIXTURE_MANIFEST=<copied-fixture_manifest.json>
export ASCEND_RT_VISIBLE_DEVICES=<authorized-idle-A3-die>
export PYTHONPATH="$ASCEND_REPO:$VLLM_REPO"
export VLLM_USE_V2_MODEL_RUNNER=1
export VLLM_ENABLE_V1_MULTIPROCESSING=0
cd "$ASCEND_REPO"
git rev-parse HEAD 'HEAD^{tree}'
git status --porcelain --untracked-files=all
git -C "$VLLM_REPO" rev-parse HEAD 'HEAD^{tree}'
git -C "$VLLM_REPO" status --porcelain --untracked-files=all
python tools/p7x_graph_repair2.py --help
```

Both repos must be exact/clean. Independently verify `vllm.__file__`, `vllm_ascend.__file__` point at these checkouts, not an older overlay/site-packages. Preserve expanded environment (redact secrets), version/package manifest, device inventory, full commands, exit codes, stdout and stderr. Do not set Mac-only `VLLM_VERSION` to disguise a server package mismatch.

Run A0, then A1, then B **sequentially**; stop on any unexpected control failure. Example for each `CASE` (`A0`, then `A1`, then `B`), with unique run ID and output directory:

```bash
python tools/p7x_graph_repair2.py run \
  --case "$CASE" --run-id <repair2-run-id> --attempt 01 \
  --expected-sha 1870e0ba8a00eeeae16c27f877e81eb65b711080 \
  --vllm-repo "$VLLM_REPO" \
  --target-model /mnt/share/wql/Qwen3-8B \
  --draft-model /mnt/share/dspark_qwen3_8b_block7 \
  --fixture-manifest "$FIXTURE_MANIFEST" \
  --output "$RUN_ROOT/$CASE"
```

The driver sets A0=no Window/experimental flag0; A1=W1024/flag0; B=W1024/flag1. It retains the entire `[7,14,28]` configuration in each case. A1 exit0 means the **expected exact GRAPH_FROZEN rejection**, not inference success. B checks runner/speculator class, actual capture graph keys and K/query/W/span. Default requests attempt 1/2/4 prompt batches in the same engine. Runtime descriptors—not those request counts—decide coverage.

After B:

```bash
python tools/p7x_graph_repair2.py check "$RUN_ROOT/B/campaign.json" \
  --output "$RUN_ROOT/B/checker.json"
```

`check` exit0 only means the declared fixed-inventory/replay evidence satisfied this checker. Read all four namespaces; it cannot close task/physical/completion gates. Exit2 means OPEN/NOT_RUN/INVALID evidence or missing coverage; retain it. Do not change capture sizes or classifier rules to obtain exit0.

If startup fails, `campaign.json` retains exception type/message/traceback and, when present, the atomic `partial.json`. A preflight model/source failure occurs before the model try/finally and must also be retained from the process stderr/exit code. No-record partial evidence is a diagnostic, not a pass.

### 13.2 Boundary requests / same-engine A/B/A′ attempts

```bash
python tools/p7x_graph_repair2.py make-requests \
  --target-model /mnt/share/wql/Qwen3-8B \
  --output "$RUN_ROOT/boundary_requests.json"
```

Then repeat the B run command with a fresh `--output "$RUN_ROOT/B-boundaries"` and `--requests "$RUN_ROOT/boundary_requests.json"`. It generates exact token-input lengths 32,1024,1025,1151,1152,1153,2049,32 using the verified local tokenizer, same engine, max_tokens16. These are stimuli, not assertions that runtime E/H equals prompt length. Preserve each real row's E/upper/generation/mapping/source and identify the actual boundary crossing.

The repeated short request is a bounded **A′ attempt**, not forced physical A′. `HOST_A_B_A_CONTENT` checks the last three bound generations only, and cannot automatically locate every useful triple in a long run. Preserve the full sequence and explicitly select a triple with same descriptor/provider/backing; record its sequence IDs. If no qualifying triple exists, report OPEN. A test-only deterministic allocator fixture would require separately reviewed safe allocation-stage control; it was not added here. Never overwrite active FullSource or use a previous Window as source.

### 13.3 G4 aligned control collection

Run fresh A0 and B with `--target-probe` and identical declared fixtures. This emits `target-boundary.json` and real `target-logits-*.pt` files after startup. It wraps only these engine instances and restores methods even on exceptions. Do not enable it in timing experiments.

Within a process, use G4 records for canonical table/slot/positions/query identity and Target unchanged at the proper construction boundary. The optional probe's before/after proposal snapshots straddle **different full-prepare phases**; they are not expected to be bitwise equal across all fields. Compare corresponding phases between aligned controlled runs, not arbitrary pre/post entries.

Before numerical comparison choose one explicit scope:

1. **Logits-head only:** byte-identical hidden-state input, same weights/dtype/positions selection; compare actual stored head outputs. This cannot prove Target attention/KV equality.
2. **Whole Target:** require exact Target token IDs, absolute positions, request/query layout and equivalent KV history/state at the comparison point. Same prompt/seed alone is insufficient after speculative proposals diverge. This controlled alignment fixture is still required; do not fabricate its hash from the prompt.

Freeze dtype, atol/rtol and reason **before** reading comparison results. For byte-identical deterministic head-only replay, start from exact equality if that is the declared operator contract; if the deployed dtype/operator requires nonzero tolerance, owner/runtime team must justify a priori. No universal BF16 tolerance is invented locally.

Comparator inputs are explicit JSON:

```json
{
  "aligned_input_state_sha256": "<hash of the genuinely controlled comparison state>",
  "dtype": "<observed dtype>",
  "values": [1.0, 2.0],
  "atol": 0.0,
  "rtol": 0.0,
  "tolerance_reason": "<predeclared scope and justification>"
}
```

The example values are a schema illustration, **not device results**. Run `compare-target left.json right.json --output result.json`. Missing/null inputs yield OPEN. Full-write comparison uses `compare-write` with `alignment_sha256`, canonical table/slot/positions/query/Target-length values. If allocators assign different physical IDs across processes, first retain and prove a logical→physical translation and compare normalized logical semantics; do not assert numeric pointer equality or silently equate differing IDs. Current comparator expects already aligned values and does not invent that translation. Draft OFF/ON outputs are allowed to differ.

### 13.4 Observer-off (not public flag OFF)

Repeat the run command with `--case B-observer-off`, fresh output, no `--target-probe`. Experimental flag remains 1; the new observer switch is 0. Candidate provider/carrier/metadata validators remain installed, but recorder events/copies/output hashes are disabled. Startup inventory and outputs remain available.

The evidence checker deliberately cannot promote this empty-observer artifact to G1–G5 PASS. Proving actual observer-off replay and completion requires an external trace or independently reviewed nonintrusive runtime facility. Comparison with observer-on should separate functional contracts from timing perturbation. Do not use `experimental=0` (A1) as the observer-off Graph test.

## 14. G1–G5 case matrix and STOP criteria

| Case | Required evidence | PASS scope / STOP |
|---|---|---|
| C0 A0 | Exact source/model, MRV2 class, ordinary output, no Window provider/session | Baseline only; startup/output regression stops B |
| C1 A1 | Exact `NotImplementedError` with GRAPH_FROZEN before Window allocation | Negative gate only; resource/load error is not expected gate |
| C2 B fixed smoke | All actual capture graphs 1/7,2/14,4/28; nonempty bind→replay→consumer→update per generation; every actual Draft layer capture/update operand | Fixed smoke only; missing bucket→OPEN, exception→FAIL/first divergence; no fallback |
| G1 | CaptureIdentity vs actual FIA-call ptr/length; descriptor/layer/gid/backend/provider; task export mapping if available | Operator-boundary subgate can pass; full G1 requiring L3 stays OPEN without actual task binding |
| G2 | Same engine/descriptor/provider/backing A/B/A′; A≠B, A′ contents=A; unique generation/epoch; source lineage; device use/reuse trace | Host content separately labelled; device Gate OPEN without actual sequence/completion |
| G3-short | Runtime H≤W, canonical raw rows/counts, independent S/E/V/columns/IDs, actual operator and trace | No window movement required for this subcase; not representative long-case proof |
| G3-move | H>W and S>0, before/after aligned column switch; nonboundary rows; exact vs upper differences | Wrong table/length/source→STOP; helper-only data is insufficient |
| G3-negative | Independent oracle source shortage and unsupported offset tests | Host fail-closed only; don't corrupt live allocator to force device shortage |
| G4 | Same-process canonical identity + Target isolation; aligned A0/B write values; controlled Target numeric fixture | Missing alignment/logits→OPEN, never null equality; no Draft-output equality requirement |
| G5 | materialize/bind, replay submission, consumer, update/task/event relation, completion, rewrite/retire, exception path | Device causality required; Python return/retire/event-object ID is not completion |
| C3 observer-off | Same candidate/inventory, recorder disabled, external replay/trace evidence | No internal event artifact expected; cannot recycle observer-on device proof |

G3 independent integer examples, actual frozen B/span128/W1024/query7:

| H | E | Full upper | S | V=E−S | Window upper | Required columns |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 32 | 39 | 0 | 32 | 39 | 1 |
| 1024 | 1024 | 1031 | 0 | 1024 | 1024 | 8 |
| 1025 | 1025 | 1032 | 0 | 1025 | 1032 | 9 |
| 1151 | 1151 | 1158 | 0 | 1151 | 1152 | 9 |
| 1152 | 1152 | 1159 | 128 | 1024 | 1024 | 8 |
| 1153 | 1153 | 1160 | 128 | 1025 | 1032 | 9 |
| 2049 | 2049 | 2056 | 1024 | 1025 | 1032 | 9 |
| 1152 | 1149 | 1155 | 128 | 1021 | 1024 | 8 |

The last row is the independent oracle's legal distinct H/E/upper contract, **not an assertion that Base DSpark uses a future offset**. Base runtime uses H=E and future_offset=0. S is aligned down; V may exceed W up to W+B−1. Upper is clipped to materialized column extent and can be 1152 while exact capacity is 1151. Do not replace this with `min(V,W)` or set max_model_len to capacity.

The oracle module has no production planner import. Runtime raw inputs are collected from canonical owners: full device seq_lens, input-batch CPU upper plus actual query width capped at model limit, valid block counts indexed by gid/persistent row, canonical full table. The checker recomputes S/columns/IDs independently. It does not reconstruct E from production V+S.

## 15. Trace capability probe and G5 timing discipline

Run once before trace work:

```bash
python tools/p7x_graph_repair2.py trace-probe \
  --output "$RUN_ROOT/trace_capability_discovery.json"
```

Each installed tool's help call is bounded to 20 seconds. This command **does not launch profiling**. On A3, the agent must separately record these five steps:

1. Installed version/path and runtime compatibility.
2. Actual documented option support from that installed version.
3. One bounded capture command around the fixed B smoke can execute and exit/export successfully.
4. Export contains the required columns (operator/task/stream ID, operand address/descriptor, launch/update relation, event completion; physical blocks/tokens only if genuinely provided).
5. A source-to-export correlation sample proves those fields mean what the claimed Gate requires.

The exact profiling argv must be derived from installed tool help and recorded expanded, not copied from an assumed version here. Run at most one bounded minimum trace probe per candidate tool, with a stated wall-time/output cap; if unavailable/inadequate, retain help/error/export schema and mark `CAPABILITY_UNVERIFIED` or `INSUFFICIENT_TOOL_EVIDENCE`. Do not repeatedly run the full model while guessing unsupported flags. Any privileged tracing/install requirement needs server owner authorization.

Python `id(handle/stream/event)` is an object identity, not automatically the device task ID. The required correlation artifact must map those through the real runtime handle/provider/task export or explicitly say mapping unavailable. `actual_task_table_address` and `actual_memory_read_set` remain null in our Host records. No msprof Memory/MemoryAccess feature is promised to yield per-block physical reads. If L5 cannot be observed, submit a precise acceptance question to owner/tool team; preserve the Gate, do not rename operator-boundary evidence L5.

G5 source sequence is still:

```text
materialize → bind/private validation/publish → REPLAY submission
  → stream event recorded (observation)
  → CONSUMER source point → UPDATE source point
  → backend task update → existing ExternalEvent.record(update_stream)
  → evidence-only output D2H/hash → proposal-owner retirement observation
```

Host sequence/time is `process_monotonic_ns`, not device time. Event `.query()` is a nonblocking observation at `query_host_monotonic_ns`, not the exact device completion timestamp. API source/class is recorded. To establish happens-before, correlate the actual stream/task/event dependency chain with generation/table/length, not timestamps from unrelated clocks. Determine experimentally whether UPDATE(N) affects replay N or N+1. A renamed event cannot settle that issue.

No UPDATE movement, global synchronize, double-buffer, new lease protocol, or device completion claim was introduced. Observer-on D2H can perturb or hide timing issues; observer-off plus qualifying external trace is required for the corresponding evidence. The current narrow diagnostic candidate is not a performance baseline.

Safe abort limitation: pinned vLLM exposes `LLMEngine.abort_request` (`vllm/v1/engine/llm_engine.py:217`) and core-client abort methods, but the current in-process synchronous `generate` does not expose an independently proven callback precisely while a graph task is pending. Do not call it from an arbitrary racing thread or use sleep. Preserve normal exceptions and early-owner cleanup now; in-flight device abort requires a separately established safe injection/completion boundary and remains NOT_RUN.

## 16. Checker responsibilities, schemas and negative rules

Historical `independent_checker_result.json` validates the **specific repair1 archive** (including that B failed with the known message and counts). Keep it immutable; do not reuse it as a success checker for new runs.

The committed repair2 checker separates:

| Namespace | Meaning |
|---|---|
| `EVIDENCE_INTEGRITY` | schema, run/case/attempt/source identity, process/provider/recorder scope, duplicate sequence, artifact errors, basic required operand geometry |
| `HOST_CONTRACTS` | nonempty bound/operator/raw-oracle data; same-generation exact/upper/table; canonical independent math; per-layer source association/order |
| `DEVICE_FUNCTIONAL_GATES` | fixed startup/actual graph keys/replay records; G2/G4 remain OPEN unless separately established |
| `DEVICE_EVIDENCE_LEVELS` | operator boundary may be populated; task-internal/physical/completion remain OPEN without independently qualified trace |

A synthetic Host test fixture may exercise a checker's PASS branch; it is labelled Host data and is not a device result. Run metadata and source provenance must be audited independently. This checker is a deterministic contract checker, not protection against deliberately forged evidence.

Negative rules now tested:

- empty artifact can have structurally valid integrity but Host OPEN / device NOT_RUN; it cannot functionally pass;
- missing run/source/engine identity, wrong pinned source or bad SHA format is invalid;
- process/provider/recorder scope mismatch, duplicate sequence, I/O/serialization error is invalid;
- orphan/lagging generation and wrong exact length cannot reach fixed-inventory PASS;
- actual missing layer or bucket is OPEN, not inferred from request count;
- canonical source pointer lineage, table contents and exact/upper mismatch fail the independent oracle;
- Target numeric/logit null or absent alignment is OPEN, not equal;
- different process numeric pointers do not invalidate otherwise aligned semantic write data;
- stale A epoch cannot authorize A′;
- task/internal read/completion fields are never synthesized from Host records.

Current limitations are explicit: checks do not authenticate device exports, do not derive controlled full-KV alignment, and only evaluate the last-three-bound Host A/B/A content candidate. Their statuses must be combined with the declared case matrix and independent trace reviewer, never collapsed into “all Graph tests PASS.”

## 17. Required next return package

Return under a new run directory, not over repair1:

```text
00_return_index.md                    # every raw file bytes/SHA256, source/run IDs
01_report_cn.md                       # observed facts / inference / unknown separated
02_execution_ledger.json              # every expanded argv/env(redacted)/exit/start/end
03_device_and_source_facts.json       # runner/speculator/import paths/config/models
A0/campaign.json + stdout/stderr
A1/campaign.json + stdout/stderr
B/campaign.json + partial.json + checker.json + stdout/stderr
B-boundaries/...
G4-A0/target-boundary.json + target-logits-*.pt
G4-B/target-boundary.json + target-logits-*.pt
G4_alignment_and_tolerance.json       # or explicit OPEN with missing fixture
B-observer-off/...
trace_capability_discovery.json
trace_command_and_export_schema.json
raw_traces/                          # if collected; never imaginary placeholders
G1_G5_gate_decisions.json             # evidence level and exact limits per Gate
first_divergence.md
RETURN_TO_LOCAL_Graph_Mandatory_Gap_Report.md
SHA256SUMS
```

If a command fails, preserve full original exception, partial record, first divergence and cleanup outcome. Do not run dependent cases against a known-corrupt engine. Do not claim smaller capture inventory or eager output is an alternative PASS. Store raw tensors/logs only in the internal evidence directory, not GitHub/source Git. If any evidence must be text-split for return, one strict JSON object per file is preferred; preserve original bytes/hash/index and part order.

## 18. Final audit, auxiliary files and next action

Final code is signed commit `1870e0ba8a00eeeae16c27f877e81eb65b711080`, tree `a913b534d4a731cdcbca8256f42f0c1a3a6dc0a6`, parent `13373fff637e819f3db125e05064f94cba3475a3`. Both source repositories are clean; vLLM remains exact pinned SHA/tree. No published history was amended and no push was performed.

Auxiliary delivery directory:
`/Users/wenqingzhang/Desktop/Note/MRV2/g1-g5_repair2_local/`.

It contains the strict recovery script/output/checks, complete merged command ledger, exact fixture manifest, RED/GREEN/baseline/environment-blocked logs, final source audit, full reviewable diff, and hashes. The main report embeds the root cause, key diff, commands, outcomes and all remaining limits so a reviewer does not need the repository to understand the decision.

Recommended sequence:

1. Independent local review of this repair, especially context lifetime and the new checker/driver limitations.
2. Separately authorize publication of the exact new SHA; clean-fetch and verify it on A3.
3. Execute source/fixture preflight → A0 → A1 → fixed B; stop at first real divergence.
4. Only after that smoke works, run independent boundary oracle, same-engine A/B/A′ attempt, aligned G4 collection and bounded trace capability probe.
5. Keep L3/L5/L6 and controlled full-Target/abort questions OPEN until actual evidence closes them. Return precise remaining gaps, not an unsupported aggregate PASS.
6. No TP16/Prefix/Eagle3/DSA/MLA/Async/DSA-CP/SFA/Mixed/multi-group/DFlash2 Graph work before Base G1–G5 acceptance.

```text
CORE_OBSERVER_REPAIR: LOCAL_REPAIR_HOST_VERIFIED
REAL_METADATA_STRUCTURE_REGRESSION: PASS
PRIVATE_READ_AND_CANONICAL_WRITE_CONTRACT: PRESERVED (HOST)
READY_FOR_A3_RERUN: YES (bounded smoke/collection, not full Gate closure)
G1_G5_NEW_SHA_DEVICE_VERIFICATION: NOT_RUN
FULL_TARGET_NUMERIC_ALIGNMENT_FIXTURE: OPEN
STRICT_DEVICE_A_B_A_AND_ABORT: OPEN
TASK_PHYSICAL_READ_COMPLETION_TOOL_CAPABILITY: UNVERIFIED
PUBLIC_GRAPH_SUPPORT: STILL FROZEN
PUSH: NO
```
