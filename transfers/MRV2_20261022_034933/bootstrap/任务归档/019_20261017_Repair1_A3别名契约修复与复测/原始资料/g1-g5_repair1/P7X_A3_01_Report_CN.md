**# P7-X MRV2 Draft Sliding Window — Node101 Ascend A3 第二轮 G1–G5 终局报告**


RUN_ID：`20261019_055109_13373fff`

RUN_ROOT：`/mnt/wenqing/mrv2_graph_g1g5_rerun/20261019_055109_13373fff`

日期：2026-10-19

性质：设备级 Base 复验；不是性能验收，不是公共 Graph 启用。


**---**


**## 1. 结论**


```

EXPERIMENT_EXECUTION_COMPLETE = false (device positive path blocked)

TEXT_EVIDENCE_HANDOFF_COMPLETE = true

BASE_G1_G5_VERIFIED = false

READY_FOR_LOCAL_FOLLOWUP = true

OVERALL_VERDICT = RETURN_TO_LOCAL_FIX

SECONDARY_VERDICT = DEVICE_EVIDENCE_BLOCKED

PUBLIC GRAPH SUPPORT = STILL FROZEN

SERVER PRODUCTION MODIFICATIONS = NONE

```


本轮精确复验了 `13373fff`，并确认：


1. ****A0 基线正常****：MRV2 `NPUModelRunner` + `AscendDSparkSpeculator`，窗口关闭，输出 16 个 token 与旧合同逐 token 一致。

2. ****A1 公共门仍冻结****：窗口配置 + experimental flag OFF 时，在 `GRAPH_FROZEN` 处提前拒绝，未创建 FullSource/workspace/provider/capture carrier。

3. ****旧 alias 失败点未在设备上到达****：`13373fff` 的 fixed-contract B 在 startup capture 阶段就失败了，早于旧的 `bind_read_carrier` / `validate_draft_metadata_isolation`。

4. ****新的 production 缺陷****：

   `attach_parallel_graph_capture_operand_observer` 在多 descriptor capture 时重复向同一 layer metadata 对象 attach，第二次抛

   `RuntimeError: capture operand observer is already attached`。

   这是 characterization observer 的生命周期/idempotency 缺陷，不是旧 canonical-sharing 修复失败。

5. ****旧 alias 修复在 host 上已验证****：

   `test_real_target_metadata_sharing_is_allowed_for_full_write_carriers` 与

   `test_draft_private_fields_still_reject_target_storage_alias` 均 PASS。

   但设备上因 capture 先失败，`ALIAS_FIX_DEVICE = NOT_REACHED`。

6. ****G1–G5 设备正向证据未取得****：

   G1 host operator boundary OPEN；G1 ACL task internal OPEN；

   G2 host A/B/A′ PASS，NPU A/B/A′ NOT_RUN；

   G3 independent oracle PASS，operator/task/physical read OPEN；

   G4 host record PASS，device OFF/ON OPEN；

   G5 host event instrumentation PASS，first replay/update/completion OPEN。


因此本轮不能给出 `BASE_G1_G5_PASS`。必须回本地修复 capture observer 生命周期，再回 A3 重跑。


**---**


**## 2. 旧失败与本轮修复合同**


**### 2.1 旧失败（上一轮，8cb4bed6）**


上一轮在设备上完成了 capture，随后第一次 runtime bind 抛：


```

ValueError: Draft metadata mutable storage aliases Target metadata

  draft_window_graph_characterization.py:529 bind_read_carrier

  draft_window_graph.py:818 validate_draft_metadata_isolation

  draft_window.py:2585 raise

```


根因：Draft metadata 在恢复 canonical full write/query carrier 之后，又把同一批 canonical 对象交给 isolation oracle；真实 Target metadata 也引用这些对象，于是被误判为污染。


**### 2.2 本轮修复（13373fff）**


`13373fff` 引入：


- `DraftWindowGraphMetadataBuild`：同时携带 `metadata` 与 `private_isolation_view`。

- `_build_private_graph_metadata` 先对 Draft-private metadata 做 isolation，保留 `private_isolation_view`；final metadata 使用 layer shallow copy，再恢复 canonical write/query carrier。

- `bind_read_carrier` 对 `private_isolation_view` 做 Target isolation 校验，对 final metadata 做 read-carrier 与 write-carrier 校验，两者分离。

- 新增 operator-boundary observer：

  - `record_parallel_graph_capture_operator_operand`

  - `record_parallel_graph_update_operator_operand`

- 新增 v2 artifact：

  `mrv2-draft-window-graph-characterization-v2`

- 新增 independent oracle 与 `tools/p7x_graph_g1_g5.py`。


**### 2.3 本轮实际结果**


修复合同本身在 host 上成立（见 §6）；但设备路径被新的 capture observer 生命周期缺陷阻断（见 §5）。


**---**


**## 3. Source / Runtime / Fixture**


**### 3.1 Source（exact）**


| 项目 | 值 |

|---|---|

| vllm-ascend repo | `https\://github.com/LucianWQZ/vllm-ascend.git` |

| branch | `fix/p7x-graph-base-a3-g1g5` |

| SHA | `13373fff637e819f3db125e05064f94cba3475a3` |

| tree | `739cde3de61e65be7cdbd187baebb6d17da04aee` |

| parent | `8cb4bed670f395c257c1233db944395159916009` |

| subject | `fix(spec-decode): repair graph window base device contract` |

| clean | yes（post-run `git status --porcelain --untracked-files=all` 为空） |

| vLLM SHA/tree | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` / `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |

| vLLM clean | yes |


远端 branch tip 在开始时精确等于 `13373fff`，没有测试最新 HEAD。


**### 3.2 Delta `8cb4bed6 → 13373fff`**


14 个文件，1737 insertions / 52 deletions：


```

tests/ut/.../test_draft_window_graph_carrier.py

tests/ut/.../test_draft_window_graph_characterization.py

tests/ut/.../test_draft_window_graph_oracle.py (new)

tools/p7x_graph_g1_g5.py (new)

vllm_ascend/attention/attention_v1.py

vllm_ascend/compilation/acl_graph.py

vllm_ascend/envs.py

vllm_ascend/worker/v2/spec_decode/dflash/aclgraph.py

vllm_ascend/worker/v2/spec_decode/dflash/capture.py

vllm_ascend/worker/v2/spec_decode/draft_window.py

vllm_ascend/worker/v2/spec_decode/draft_window_eager.py

vllm_ascend/worker/v2/spec_decode/draft_window_graph.py

vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py

vllm_ascend/worker/v2/spec_decode/draft_window_graph_oracle.py (new)

```


`native_or_build_changes = []`。因此复用 Node101 本机 A3 donor。


**### 3.3 Runtime**


- Overlay：`\<run_root>/runtime/graph_char_overlay`

- Python payload：exact `13373fff`，618 个 `.py`

- Non-Python payload：A3 donor，1269 个文件

- `vllm` 为 symlink → `\<run_root>/src/vllm`

- Import provenance：`provenance_ok = true`；12 个必需 module 全部解析到 overlay 或 pinned checkout

- 关键 module SHA256 见 `manifests/runtime_identity.json`


**### 3.4 软硬件**


| 项目 | 值 |

|---|---|

| Host | node-39-101 |

| NPU | Ascend910 A3，PCI `19e5:d803`，16 logical dies |

| CANN | 9.1.0 |

| Driver | 26.0.rc1 |

| Python | 3.11.10 |

| torch | 2.10.0+cpu |

| torch_npu | 2.10.0.post4 |


**### 3.5 Fixture**


```

Target: /mnt/share/wql/Qwen3-8B

Draft : /mnt/share/dspark_qwen3_8b_block7

method: dspark

K=7, query width=7, sample_from_anchor=True

backend: AscendAttentionBackendImpl / STANDARD dense GQA-FIA direct-prefix

W=1024, block span=128, capture capacity=1151

Graph: FULL_DECODE_ONLY，decode descriptor FULL

topology: TP1 DP1 PP1 PCP1 DCP1

capture sizes: [7,14,28] → buckets (1,7),(2,14),(4,28)

```


模型 hash 本轮重新计算，5 个 target shards、config/index/tokenizer、draft config/weights 全部与合同一致。


**---**


**## 4. 实际流程**


1. Preflight：16 个 logical die 初始空闲；无他人 vLLM 进程；`/mnt` 189G、`/home` 129G。

2. 恢复旧 campaign 输入：driver、request contract、prompt/hash、A0/A1/B 结果、首次完整 traceback、fixture manifest、overlay recipe、env/sitecustomize/import probe；全部存在且 hash 可核对。

3. 新建独立 checkout，验证 SHA/tree/parent/clean。

4. 构建 run-local overlay，验证 import provenance。

5. 运行 4 个 host UT 文件：25 + 47 + 37 + 7 = 116 PASS。

6. 显式运行两类 real-owner regression：2 PASS。

7. A0：window OFF、flag 0 → OK，16 tokens 与旧合同一致，zero characterization state。

8. A1：W1024、flag 0 → `GRAPH_FROZEN`（预期），发生在 FullSource/workspace/provider/capture carrier 之前。

9. B：W1024、flag 1、fixed `[7,14,28]` → startup capture 新缺陷，`capture operand observer is already attached`；partial artifact 1 个 capture 事件，0 operand / 0 G4 / 0 lifecycle。

10. 单/部分 capture inventory 诊断（明确非固定合同）：`[7]`、`[14]`、`[28]` 均未触发 Graph（target manager 无 capture descriptor）；`[24]` 在 characterization install 处报 draft capture descriptors 为空。这些只用于定位，不作为 Base 证据。

11. Host 生命周期测试：16 PASS（bind/publish、A/B/A′、operator boundary、G4/G5 recorder、recorder exception、auditor）。

12. Host oracle：SHORT/BOUNDARY/NONBOUNDARY/LONG 全部符合；SOURCE_SHORTAGE 与 NONZERO_OFFSET 按预期拒绝。

13. Negative matrix：31/31。

14. 独立 checker：最终 26/26 PASS（首个 run 为 25 PASS / 1 OPEN，OPEN 仅为“十类交付文件尚未全部生成”；补齐后复跑 26/26）。

15. 清理：无 campaign 进程；HBM 释放；两仓 clean；旧目录未写；团队工具 2296 文件 hash 不变。


**---**


**## 5. 首个分歧（First Divergence）**


**### 5.1 精确失败**


Fixed-contract B（CMD-0019）：


```

RuntimeError: capture operand observer is already attached


vllm_ascend/worker/v2/spec_decode/dflash/capture.py:376

  attach_parallel_graph_capture_operand_observer(...)


vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py:1006

  raise RuntimeError("capture operand observer is already attached")

```


调用栈：


```

DFlashAclGraphManager.capture

  -> DFlashCudaGraphManager.create_forward_fn(desc, warmup=True)

  -> ascend_prepare_dflash_inputs_to_capture

  -> record_parallel_graph_capture(...)       # 写入 1 个 capture 事件

  -> attach_parallel_graph_capture_operand_observer(...)

  -> raise

```


**### 5.2 机制**


`attach_parallel_graph_capture_operand_observer` 对 `metadata.values()` 中的每个 layer metadata 检查：


```python

if hasattr(layer_metadata, _CAPTURE_OPERAND_CONTEXT_ATTRIBUTE):

    raise RuntimeError("capture operand observer is already attached")

```


capture manager 对每个 descriptor 调用 `create_forward_fn(desc, warmup=True)` 和 `create_forward_fn(desc, warmup=False)`；在固定 `[7,14,28]` 下，第一个 descriptor `(4,28)` 先 attach；后续 descriptor 的 metadata 复用了同一 layer metadata 对象，属性仍在，于是第二次 attach 抛错。


**### 5.3 为什么不是旧 alias 修复失败**


旧失败在 `bind_read_carrier` 的 `validate_draft_metadata_isolation`；本轮失败发生在 capture helper 的 observer attach，时间更早。`bind_read_carrier` 从未执行，因此：


```

B_OLD_FIX_POINT = NOT_REACHED

B_BIND_PUBLISH  = NOT_RUN

B_REAL_REPLAY   = NOT_RUN

ALIAS_FIX_DEVICE = NOT_REACHED

```


Host 上旧 alias 修复已通过（见 §6），但不能替代设备证据。


**### 5.4 Partial artifact**


`B/artifact/B_artifact.json`：


- schema：`mrv2-draft-window-graph-characterization-v2`

- events：1

- operand_events：0

- g4_records：0

- lifecycle_events：0


唯一 capture 事件：


| 字段 | 值 |

|---|---|

| descriptor | `mode=FULL;reqs=4;tokens=28;uniform=7` |

| backing table address | 20623361164800 |

| exact/upper lengths | 1151 × 4 |

| slot mapping | -1 × 28 |

| positions | 0 × 28 |

| query layout | [0, 7, 14, 21, 28] |

| generation / epoch | null / null |


这只能作为 capture helper 的 L1/L2 部分记录，不能作为 G1 capture operand equality 或 replay 证据。


**---**


**## 6. Host 证据**


**### 6.1 UT 文件**


| 文件 | 结果 |

|---|---|

| `test_draft_window_graph_characterization.py` | 25 passed |

| `test_draft_window_graph_carrier.py` | 47 passed |

| `test_draft_window_graph_binding.py` | 37 passed |

| `test_draft_window_graph_oracle.py` | 7 passed |


**### 6.2 Real-owner regression**


```

test_real_target_metadata_sharing_is_allowed_for_full_write_carriers PASSED

test_draft_private_fields_still_reject_target_storage_alias PASSED

```


这证明修复代码在 host 上：

- 接受合法 canonical full write/query sharing；

- 仍然拒绝 Draft-private 字段与 Target storage alias。


**### 6.3 Host 生命周期**


16/16 PASS：


- bind/publish 使用真实 P3 generation；

- host A/B/A′ 在 stable address 上刷新内容；

- capture/update operator boundary recorder；

- replay submission 使用真实 `torch.npu.Event` 记录且不 host synchronize；

- G4 machine-readable record；

- recorder 异常时释放 bound carrier；

- campaign auditor 要求全部证据层并检测 host A/B/A；

- manager 在消费 graph metadata 前准备 candidate。


这些是 ****HOST**** 证据，不能替代设备 L2/L3/L5/L6。


**---**


**## 7. G1–G5 裁决**


| Gate | 状态 | 说明 |

|---|---|---|

| G1 host operator boundary | OPEN | 只有 1 个 capture 事件；无 update_operator；无 bound |

| G1 actual ACL task internal | OPEN | 需要 NPU task trace |

| G2 host A/B/A′ | PASS | host UT |

| G2 NPU A/B/A′ | NOT_RUN | capture 阻断 |

| G2 canonical source lineage | OPEN | 无设备 A/B/A′ |

| G3 independent oracle | PASS | host synthetic canonical inputs |

| G3 operator boundary | OPEN | 无设备 update operand |

| G3 task correlation | OPEN | 需要 device trace |

| G3 physical memory transaction | OPEN / UNPROVEN | 无物理 read-set |

| G4 host write/target record | PASS | host UT |

| G4 full write / Target (device) | OPEN | 无设备 G4 record |

| G4 device KV write | OPEN | 无物理写事务证据 |

| G4 Target numeric | NOT_RUN | capture 阻断 |

| G5 event instrumentation (host) | PASS | host UT |

| G5 first replay source | NOT_RUN | 无 replay |

| G5 update effective generation | OPEN | 需要 NPU timeline |

| G5 completion / reuse | OPEN | 无 device completion |

| G5 abort/exception | HOST_PASS_DEVICE_OPEN | host recorder exception test PASS；device abort 未跑 |


**---**


**## 8. Negative Matrix**


CPU 31/31 MATCH，覆盖：


- strict flag parsing；

- CONFIG_OFF；

- MTP forced off；

- DeepSeek-V4 DSpark forced off；

- plain Eagle / unknown method reject；

- DSpark/DFlash Qwen3 eligible；

- graph NONE/PIECEWISE reject；

- async/TP/DP/PP/PCP/DCP>1/SP/DSA-CP/FlashComm/prefix reject；

- COMPATIBILITY backend reject；

- W=0 / W\<future offset reject；

- dynamic K reject。


设备负例：


- A0 CONFIG_OFF：zero state，基线 OK；

- A1 flag OFF：`GRAPH_FROZEN`；

- B：新 capture 缺陷；

- 其余设备负例（wrong bucket/backend/epoch/stale carrier/source shortage）未执行，因为正向 capture 已失败。Host 覆盖的项在 05 文档中标注证据等级。


**---**


**## 9. 观测影响**


- Characterization 路径在 capture/update 之后做 host snapshot（`.cpu()` / `.tolist()`），会同步；B 本身已在 capture 失败，未进入 runtime，因此没有性能代表性。

- A0/A1 没有 enable characterization；A0 是正常 baseline，A1 在 init 早期失败。

- 本轮没有跑性能，不报告 throughput/TTFT/TPOT/E2E 结论。

- 所有 host 证据都标记为 `HOST`，没有写成 device L3/L5/L6。


**---**


**## 10. 覆盖与未覆盖**


**### 覆盖**


- Exact source/runtime/fixture 身份。

- A0/A1 控制。

- Fixed-contract B startup capture 到 first divergence。

- Host UT（116 + 2 + 16）。

- Host oracle 四类正例 + 两类负例。

- CPU negative matrix 31/31。

- Partial artifact schema/sequence/identity 检查。

- 独立 checker 26 项。

- 清理与完整性。


**### 未覆盖**


- Fixed `[7,14,28]` 下的 capture 完成、bind、publish、replay、update、consumer、completion。

- `(1,7)`、`(2,14)`、`(4,28)` 的完整 runtime coverage（固定 inventory 被 capture 缺陷阻断；部分 inventory 诊断不构成 Graph 证据）。

- G2 设备 A/B/A′。

- G3 operator/physical read。

- G4 设备 OFF/ON write/Target、Target logits/output。

- G5 设备 timeline、effective update generation、completion/reuse、abort。

- msprof/NPU trace 未采集（B 未进入 replay）。


**---**


**## 11. 本地后续方向**


第一优先级（阻塞 Base）：


1. 修复 `attach_parallel_graph_capture_operand_observer` 的跨 descriptor / 跨 warmup 生命周期：

   - 让 attach 对同一 metadata 对象幂等；或

   - 每个 capture descriptor 使用独立的 observer context；或

   - 在 descriptor 切换时显式清理旧 context。

2. 增加 red test：复用同一 layer metadata 对象的多 descriptor capture（固定 `[7,14,28]`），断言不重复 attach。

3. 回 A3 重跑 fixed `[7,14,28]`：A0/A1/B → G1 → G2 → G3 → G4 → G5。


第二优先级（证据接口，不一定需要 production 修改）：


4. G1 L3：使用 msprof task-level trace 关联 FIA task handle/stream/event 与 operand。

5. G3 L5：使用 msprof Memory/MemoryAccess metrics 或等价 device trace 证明 physical read set。

6. G5 L6：采集 replay/update/completion timeline，回答 UPDATE(N) effective generation 与 safe reuse。

7. G4 Target numeric：在 driver 中采集 Target logits/output，固定 token/position/mask/KV 条件后比较 OFF/ON。


**---**


**## 12. 最终裁决**


```

RUN_ID: 20261019_055109_13373fff

SOURCE: 13373fff637e819f3db125e05064f94cba3475a3

A0: PASS

A1 EARLY GRAPH_FROZEN: PASS

B OLD FIX POINT: NOT_REACHED

B BIND / PUBLISH / REAL REPLAY: NOT_RUN

ALIAS FIX VERDICT: HOST_PASS_DEVICE_NOT_REACHED


G1 HOST OPERATOR: OPEN

G1 ACL TASK INTERNAL: OPEN


G2 HOST ABA: PASS

G2 NPU ABA: NOT_RUN

G2 CANONICAL SOURCE LINEAGE: OPEN


G3 ORACLE: PASS

G3 OPERATOR: OPEN

G3 TASK: OPEN

G3 PHYSICAL READ: OPEN


G4 FULL WRITE / TARGET: OPEN

G4 DEVICE KV WRITE: OPEN

G4 TARGET NUMERIC: NOT_RUN


G5 FIRST REPLAY SOURCE: NOT_RUN

G5 UPDATE EFFECTIVE GENERATION: OPEN

G5 COMPLETION / REUSE: OPEN

G5 ABORT / EXCEPTION: HOST_PASS_DEVICE_OPEN


NEGATIVE MATRIX: PASS (host, 31/31)

CROSS-ARTIFACT AUDIT: PASS (26/26 final)

COVERED / UNCOVERED DESCRIPTORS: capture (4,28) partial; no runtime coverage

OBSERVATION EFFECTS: characterization sync not performance representative; no device runtime reached


OVERALL VERDICT: RETURN_TO_LOCAL_FIX

ALL BLOCKERS: capture operand observer re-attach (production defect)

READY FOR LOCAL FOLLOWUP: YES

EXACT NEXT LOCAL TASK: make capture observer attach idempotent across capture descriptors; add red test; rerun fixed [7,14,28]

READY FOR BATCH A: NO


PUBLIC GRAPH SUPPORT: STILL FROZEN

SERVER PRODUCTION MODIFICATIONS: NONE

TEXT EVIDENCE HANDOFF: COMPLETE

SOURCE UNCHANGED: YES

OWN PROCESSES CLEANED UP: YES

```
