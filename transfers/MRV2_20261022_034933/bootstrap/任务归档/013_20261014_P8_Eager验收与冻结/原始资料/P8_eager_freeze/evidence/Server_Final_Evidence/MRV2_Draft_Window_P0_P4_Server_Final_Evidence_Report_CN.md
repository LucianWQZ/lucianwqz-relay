**# MRV2 Draft Sliding Window — P0–P4 服务器证据终局合并报告**



**\*\*角色\*\***：Evidence Consolidator / Release Auditor（非开发者）

**\*\*机器\*\***：\`80.48.37.146\` / \`node133\`，容器 \`vllm-wenqing-dev\`

**\*\*日期\*\***：2026-10-13

**\*\*范围\*\***：只做证据裁决与合并。未修改 production 代码，未运行模型，未进入 P5，未跑 R4 性能。



**---**



**## 1. 执行摘要**



本报告合并 node133 上全部 P0–P4 证据，按证据优先级裁决冲突，并对齐冻结文档的 Gate 定义。



**\*\*一句话结论\*\***：P0–P4 &#x7684;**\*\*静态实现交付完成\*\***（production 基线干净、lineage 正确、Debug 与 production 严格隔离）；**\*\*P4b 单请求 NPU 语义已通过\*\***（含 Level 4 算子参数证据）；但 **\*\*P4a 的 NPU Window ON 从未在本机运行\*\***，**\*\*P4b 的受控多请求无法构造\*\***，**\*\*设备生命周期与 Level 5 kernel 读数未观测\*\***。因此 **\*\*\`G-GQA-EAGER\` 与 \`G-AR-STEP\` 均保持 OPEN\*\***，**\*\*Feature release 保持 HOLD\*\***。



**\*\*本轮最重要的三条事实\*\***：



1\. **\*\*Debug 与 production 完全隔离\*\***：6 个 debug commit &#x4E2D;**\*\*没有任何一个是\*\*** \`1011e2c2\` 的祖先（\`git merge-base --is-ancestor\` 逐一验证）；production diff &#x4E2D;**\*\*不含任何 trace/debug 文件\*\***。

2\. **\*\*受控多请求无法构造，且失败模式是服务级崩溃\*\***：四种构造（并发 HTTP、barrier 同步、\`n=2\`、离线 \`LLM.enqueue\`）全部失败。调度器 dump 显&#x793A;**\*\*每步只准入一个新请求\*\***，于是第二个请求的 prefill 必然与第一个的 decode 重叠 → mixed → \`NotImplementedError\` → **\*\*整个 EngineCore 中止，两个请求同时失败\*\***。

3\. **\*\*Node101 证据完全缺失\*\***：任务列出的三份 Node101 报告在本机不存在。迁移包已生成，&#x4F46;**\*\*无任何证据表明它已在 Node101 执行\*\***。故 **\*\*Node101 (A3) 状态为 UNKNOWN，本报告不予继承\*\***。



**\*\*严禁的六类过度表述\*\***，本报告逐一避免（见 §4 与 §12）：400 条 FIA 记录不等于 Draft 全覆盖；顺序请求隔离不等于 persistent row reuse；NO_SYNC 输出一致不等于 stream happens-before；长 prompt 跨历史 block 不等于 future-column 通过；OFF 无 trace 不等于 ON prefill bypass 的直接证据；Node133 A2 结果不可继承为 Node101 A3 PASS。



**---**



**## 2. 权威版本与仓库边界**



从 Git 实读（非引用）：



\| 仓库 | HEAD | tree | 状态 |

\|---|---|---|---|

\| vLLM production | \`84030bbe3d74d99bad477a3d2e37a973ccd8865c\` | \`f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee\` | clean (0) |

\| vLLM-Ascend production | \`1011e2c2fa99729a46efde5b5bbaf6daed975a2c\` | \`7d165d585755766e7493e02f0281598e4aca3602\` | clean (0) |

\| Debug worktree | \`2a4856134648c068cab044ddfb11eb0e0d907453\` | — | clean (0) |



两组 SHA/tree 与冻结文档一致，工作树干净，**\*\*diff against baseline 为空\*\***。



**### 2.1 production lineage（实读，逐 commit 与冻结文档一致）**



\`\`\`text

841dc6cc  upstream base

 → b12399ad  P1  feat: draft-window policy and math

 → c58daea0  P1  fix: P1 review findings

 → 83579675  P2  feat: source inventory

 → fac84121  P2  fix: P2 review findings

 → feab28f5  P3  feat: runtime ownership

 → 16727882  P3  fix: P3 review findings

 → 0dd83e9f  P4a feat: integrate in Ascend eager path

 → 4c1f6914  P4a fix: P4a Ascend-only review findings

 → d0c88838  P4b feat: integrate for Eagle3 eager

 → 1011e2c2  P4b fix: P4b Eagle3 window review findings

\`\`\`



\`841dc6cc\` 是 \`1011e2c2\` 的祖先：**\*\*YES\*\***（已验证）。



**### 2.2 Debug 隔离裁决**



6 个 debug commit：\`4c79efaa7 → 11e6369e3 → 30c87a598 → 6e06c5486 → 24758c5f5 → 2a4856134\`。



\| 裁决项 | 结果 |

\|---|---|

\| 任一 debug commit 是 production 祖先？ | **\*\*否\*\***（6/6 逐一验证） |

\| production diff 含 trace/debug 文件？ | **\*\*否\*\***（\`grep -iE 'trace\\|debug\\|\_test'\` 无命中，仅测试目录有 \`test\_\*\`） |

\| Debug 是否可算作 production 交付？ | **\*\*不可\*\***。仅作观测工具证据 |



**---**



**## 3. 证据来源与优先级**



发生冲突时的裁决优先级（本报告严格执行）：



1\. 当前 Git SHA / tree / 真实 source；

2\. 原始 NPU trace、service log、cmdline、run manifest；

3\. 机器生成的 JSON/CSV；

4\. 后续 Closeout 报告；

5\. 早期报告摘要；

6\. 推断。



同一报告"开头历史状态"与"后续追加章节"冲突时：**\*\*以后续真实执行结果为准\*\***，历史保留不删。

本轮实证：\`P4b_R3_Final_Correctness_Report.md\` 开头写 \`ENVIRONMENT_BLOCKED\`，§25/§26 追加了真实执行结果。按优先级 4 > 5，**\*\*采用 §25/§26\*\***，开头历史作为过程记录保留。



**### 3.1 证据分级（本报告全程区分，绝不混用）**



\| 级别 | 含义 | 本轮是否有 |

\|---|---|---|

\| static / CPU | 纯 CPU 单测与静态检查 | 有 |

\| NPU live L3 | Python metadata 边界（consumer boundary） | 有 |

\| **\*\*NPU live L4\*\*** | 算子调用参数（task-bound operand） | **\*\*有\*\*** |

\| NPU live L5 | kernel/profiler 实际读取集 | **\*\*无\*\*** |

\| 单请求 | 单 request | 有 |

\| 受控多请求 | batch>1 纯 decode | **\*\*无（无法构造）\*\*** |

\| 一般在线 mixed arrival | 任意到达顺序的并发 | **\*\*不支持，服务级崩溃\*\*** |



机器维度：**\*\*Node133 = A2 (910B2)\*\***；**\*\*Node101 = A3，本机无证据\*\***。



**---**



**## 4. 时间线**



\| 时间（Asia/Shanghai） | 事件 |

\|---|---|

\| 2026-10-10 | P1–P4b 静态冻结；Plan header 记录 \`G-GQA-EAGER\` OPEN、\`G-AR-STEP\` STATIC CONTRACT PASS / NPU RUNTIME OPEN、release HOLD |

\| 2026-10-12 09:57 | Mac Final 导出为 \`P4_freeze/\`（bundle + 10 format-patches + notes） |

\| 2026-10-12 15:3x | 服务器下载并解压 freeze |

\| 2026-10-12 16:27 | **\*\*R0\*\*** Server Restore → PASS |

\| 2026-10-12 17:06 | **\*\*R0\*\*** Runtime Binary Binding → PASS |

\| 2026-10-12 17:52 | **\*\*R1\*\*** Service & Candidate Preflight → OFF startup PASS |

\| 2026-10-12 18:59 | **\*\*R2\*\*** Route Establishment → READY（OFF/ON/OFF smoke） |

\| 2026-10-12 19:35 | **\*\*R3a\*\*** Observability → READY |

\| 2026-10-12 20:13 | **\*\*R3a+\*\*** Trace Semantics → READY |

\| 2026-10-12 20:43 | **\*\*R3\*\*** Final Correctness 首版 → ENVIRONMENT_BLOCKED（NPU 被其他租户占满） |

\| 2026-10-12 21:37–22:10 | 容量恢复；执行 A1/B/A2/B2/B3/A3 campaigns |

\| 2026-10-12 22:39 | R3 报告 §25 Resume Run 追加 |

\| 2026-10-13 11:37 | R3 报告 §26 追加（E10/E11/E12） |

\| 2026-10-13 12:33 | **\*\*R3 Closeout\*\*** → 受控批处理、写侧隔离、顺序复用 |

\| 2026-10-13 | 本合并报告 |

\| **\*\*Node101\*\*** | **\*\*无任何本机证据\*\*** |



**---**



**## 5. P0–P4 阶段总结**



\| Phase | 生产 Deliverable | 生产 Commit | Static/CPU | NPU | Open Gate | Verdict |

\|---|---|---|---|---|---|---|

\| P0 | owner acceptance manifest；repository boundary | （doc） | 冻结文档 | — | 无新增 | **\*\*PARTIAL\*\***（仅文档，本轮未重新推导） |

\| P1 | policy / CONFIG_OFF / FORCED_OFF / math / types | \`b12399ad\`,\`c58daea0\` | PASS | — | — | **\*\*PASS (static)\*\*** |

\| P2 | inventory / FullSource / provider / unsupported gate | \`83579675\`,\`fac84121\` | PASS | — | — | **\*\*PASS (static)\*\*** |

\| P3 | mapping_epoch / workspace / lease / transport / store | \`feab28f5\`,\`16727882\` | PASS | 真实 NPU lifecycle 未测 | — | **\*\*PASS (static)\*\*** |

\| P4a | DFlash / eligible DSpark dense eager Window ON | \`0dd83e9f\`,\`4c1f6914\` | STATIC FINAL PASS | **\*\*本机无 Window ON 运行\*\*** | **\*\*\`G-GQA-EAGER\` OPEN\*\*** | **\*\*STATIC_VERIFIED / NPU OPEN\*\*** |

\| P4b | Eagle3 static-K eager Window ON | \`d0c88838\`,\`1011e2c2\` | STATIC FINAL PASS | 单请求 PASS（L4） | **\*\*\`G-AR-STEP\` OPEN\*\*** | **\*\*NPU_VERIFIED (single-request) / multi-request INCOMPLETE\*\*** |



**### 5.1 P0 细项**

\- owner acceptance manifest：冻结文档存在，**\*\*本轮未重新推导\*\***（PARTIAL）。

\- source drift：production tree 与冻结一致（\`7d165d58…\`）。

\- repository boundary：Debug worktree 独立，**\*\*无 commit 泄漏进 production\*\***。

\- **\*\*owner 未决项\*\***：\`G-GQA-EAGER\`、\`G-AR-STEP\` 仍 OPEN；feature release HOLD。



**### 5.2 P1 细项（static PASS）**

policy / CONFIG_OFF / FORCED_OFF / normalized method & model / pure math / types / warnings / validation —— 均由 production 单测覆盖（\`test_draft_window\.py\` 135 项等）。



**### 5.3 P2 细项（static PASS）**

inventory / FullSource / valid counts / provider / unsupported gate / **\*\*no Window mutation of canonical table\*\***（由本轮 W01 在 NPU 实测进一步确认：canonical FullSource 在 BEFORE/AFTER 之间 84/84 不变）。



**### 5.4 P3 细项（static PASS / NPU lifecycle 缺口）**

mapping_epoch / workspace / lease / typed transport / DraftMetadataStore / Target isolation / CPU lifecycle 测试 —— static PASS。

**\*\*真实 NPU lifecycle 仍缺口\*\***：lease acquire→retire→reuse 的设备时序未在 NPU 上被事件级证明（见 §13 L01）。



**### 5.5 P4a 细项**

\- DFlash：**\*\*ELIGIBLE_ON 静态验证，本机无 NPU Window ON 运行\*\***。

\- eligible DSpark：同上。

\- pure-prefill bypass：**\*\*已实现\*\***（\`\_requires_prefill_baseline_bypass\`），但本机 P4a 未在 NPU 上验证其 ON 路径。

\- mixed fail-closed：**\*\*已实现且在 NPU 上实测触发\*\***（见 §8），失败模式为服务级中止。

\- **\*\*\`G-GQA-EAGER\`：OPEN\*\*** —— 冻结定义要求 "FIA actual read set、padding、CPU upper 语义" 的 **\*\*physical-slot oracle\*\***，本&#x8F6E;**\*\*未完成\*\***（见 §13 W02）。

\- **\*\*本机无 Qwen3-8B + DFlash 的 NPU 结果\*\***。

\- **\*\*GLM-5.2 + DSpark TP=8 的 Window OFF smoke 不能替代 P4a Window ON correctness\*\***（TP=8 本身即被 P2 gate 拒绝）。



**### 5.6 P4b 细项**

见 §8。



**---**



**## 6. 生产代码改动**



\`\`\`bash

git diff --stat 841dc6ccdb134eab7ad09008859834d0572ee83f \\

                   1011e2c2fa99729a46efde5b5bbaf6daed975a2c

\# 18 files changed, 9706 insertions(+), 10 deletions(-)

\`\`\`



\| File | Phase | Class/Function | Before | After | Why | Runtime effect |

\|---|---|---|---|---|---|---|

\| \`worker/v2/spec_decode/draft_window\.py\` | P1–P3 | 新增（2362 行）\`compute_legacy_anchor\`/\`compute_draft_window_scalar_plan\`/\`SingleGroupDirectPrefixProvider\`/\`DraftWindowRuntimeState\`/\`DraftMetadataInputs\`/\`DraftWindowGenerationIdentity\` | 无 | 新增 | P1 policy+math、P2 inventory/FullSource、P3 workspace/lease/store | Window OFF 时完全不加载 |

\| \`worker/v2/spec_decode/draft_window_eager.py\` | P4a | 新增（760 行）\`AscendDraftAttentionReadInputs\`、\`\_requires_prefill_baseline_bypass\`、\`\_isolate_draft_metadata_from_target\` | 无 | 新增 | P4a eager 读输入与 mixed fail-closed | 仅在 ELIGIBLE_ON 路径 |

\| \`worker/v2/spec_decode/draft_window_eagle3.py\` | P4b | 新增（617 行）\`Eagle3DraftWindowMixin\`、\`build_eagle3_frozen_proposal_plan\`、\`build_eagle3_step_materialization_plan\` | 无 | 新增 | P4b static-K frozen anchor + per-step E_s | 仅 Eagle3 + static K |

\| \`worker/v2/spec_decode/autoregressive/speculator.py\` | P4a/P4b | \`\_configure_draft_window\`、\`\_initialize_draft_window_source_capability\`、\`\_build_eagle3_private_attn_metadata\` | 无 window 分支 | +264 行 | 接入 capability/read-input/metadata | window OFF 走原路径 |

\| \`worker/v2/spec_decode/dflash/speculator.py\` | P4a | DFlash speculator | — | +53/-? | P4a DFlash 接入 | — |

\| \`worker/v2/spec_decode/dspark/speculator.py\` | P4a | DSpark speculator | — | +48/-? | P4a eligible DSpark 接入 | — |

\| \`worker/v2/spec_decode/\_\_init\_\_.py\` | P4a/P4b | \`use_dflash()\`/\`use_dspark()\` 分派 | — | +80 | 路由分派 | — |

\| \`worker/v2/attn_utils.py\` | P4a/P4b | \`build_attn_metadata_wrapper\`、\`build_draft_attn_metadata_factory\` | — | +28/-? | Draft metadata 装配 seam | — |

\| \`attention/attention_v1.py\` | P4a | Ascend attention | — | +15/-? | 读输入/slot 一致性 | — |

\| \`attention/utils.py\` | P4a | Ascend attention utils | — | +5 | 辅助 | — |

\| \`tests/ut/\*\*\`（7 文件） | P1–P4b | — | — | +5378 | 静态验收 | 不进入 runtime |



**\*\*未包含\*\***：\`draft_window_trace.py\`（Debug-only，**\*\*不在 production\*\***）。这一点已用 \`git diff --name-only\` 过滤验证。



**---**



**## 7. P4a 运行结论**



\| 项 | 结论 | 证据 |

\|---|---|---|

\| DFlash 路由存在 | 是（static） | production diff \`dflash/speculator.py\` |

\| eligible DSpark 路由存在 | 是（static） | production diff \`dspark/speculator.py\` |

\| pure-prefill bypass 实现 | 是 | \`\_requires_prefill_baseline_bypass\` |

\| mixed fail-closed 实现 | 是 | 同上，抛 \`NotImplementedError\` |

\| **\*\*mixed 在 NPU 上实测触发\*\*** | **\*\*是\*\*** | E10/E11 logs |

\| **\*\*P4a Window ON correctness（NPU）\*\*** | **\*\*无证据\*\*** | 本机未运行 |

\| \`G-GQA-EAGER\` | **\*\*OPEN\*\*** | 缺 physical-slot oracle |

\| Qwen3-8B + DFlash NPU 结果 | **\*\*无\*\*** | — |



**\*\*明确禁止的替代\*\***：GLM-5.2 + DSpark 的 TP=8 Window OFF smoke **\*\*不能\*\***&#x4F5C;为 P4a Window ON correctness 证据——TP=8 本身就被 P2 gate 拒绝（\`reason=TP=2 is not verified in P2\` 同类）。



**---**



**## 8. P4b 运行结论**



**### 8.1 单请求（PASS，NPU live）**



\`\`\`

oracle divergences          : 0     （28/28 proposal rows, 852/852 step rows）

proposal_complete           : 284/284 ；trace_truncated=False ；exp==obs==3

active_row_equality         : 852/852 equal（与 canonical FullSource slice 逐值相同）

trace_error / abort         : 0 / 0

E04 精确边界                 : L0=189 H=192 H−W=128 start=128

E05 非边界                   : start=0 (H−W=104) ；start=128 (H−W=143) ；start=512 (H−W=543)

OFF==ON 输出                 : 9 次 fixture-run 逐字节相同

\`\`\`



**### 8.2 受控多请求（INCOMPLETE）**



四种构造，全部无法形成 \`num_reqs=2 且全列 decode\` 的目标状态：



\| 构造 | 结果 |

\|---|---|

\| 并发 HTTP（短+长） | EngineCore abort (mixed) |

\| 并发 HTTP + barrier 同步 + 等长 | EngineCore abort (mixed) |

\| \`n=2\` | HTTP 400 \`"n must be 1 when using greedy sampling"\`（**\*\*API 约束，非 Window gate\*\***） |

\| 离线 \`LLM.enqueue([A,B])\` + \`wait_for_completion()\` | EngineCore abort (mixed) |

\| 离线 + \`max_num_batched_tokens=40960\`（授权的唯一修正） | **\*\*完全相同\*\*** |



调度器 dump（两次离线运行一致）：



\`\`\`

scheduled_new_reqs=[NewRequestData(req_id=1-b573de99, prompt_token_ids_len=5, …)]

num_scheduled_tokens={'1-b573de99': 5, '0-a124c49f': 4}   # B 在 prefill，A 在 decode

\`\`\`



**\*\*只有第二个请求是本步新增\*\***。\`draft_slots\` 不是限制（非并行 EAGLE3 的 \`max_num_new_slots_for_drafting = 0\`）。



**\*\*范围声明\*\***：这证明的&#x662F;**\*\*本 build 上所有可用接口都无法达到 batch>1\*\***，**\*\*不证明\*\***&#x7EAF; decode 多请求在任何情况下都不可能。未修改调度器。



**### 8.3 顺序同 Engine 隔离（PASS）**



单 Engine，三次批 \`A → C → A\`：



\`\`\`

0-b4c69d84  15/15 完整   epochs 0..14

1-949ac6a6  16/16 完整   epochs 15..30

2-8ce8559c  15/15 完整   epochs 31..45

oracle divergences 0 ；active-row equality 138/138 ；trace_error 0 ；aborts 0

A_first == A_repeat 逐字节相同

\`\`\`



epoch 区&#x95F4;**\*\*逐请求严格不相交\*\***。



**### 8.4 其余 P4b 项**



\| 项 | 结论 |

\|---|---|

\| actual row reuse | **\*\*NOT_OBSERVED\*\***（\`idx_mapping\` 未插桩；复用是从隔离正确&#x6027;**\*\*推断\*\***，非观测） |

\| write/Target 隔离 | **\*\*PASS\*\***（84/84 pairs，positions/slot_mapping/qsl/canonical FullSource/target owner+layers 全部 BEFORE==AFTER） |

\| slot oracle | **\*\*INCOMPLETE\*\***（未独立重算；trace 中 FullSource 值截断至 32，不足以做行级 oracle） |

\| operator inputs | **\*\*PASS（Level 4）\*\***；Level 5 **\*\*NOT_OBSERVED\*\*** |

\| device lifetime | **\*\*OPEN\*\*** |

\| general online mixed arrival | **\*\*UNSUPPORTED_WITH_ENGINE_ABORT\*\*** |



**### 8.5 算子参数证据的正确读法**



\| run | draft \`[1,2]\` | draft 匹配 consumer | target | target 匹配 |

\|---|---|---|---|---|

\| B_on | 33 | 33 | 367 | 0 |

\| CL_SEQ_on | 18 | 18 | 182 | 0 |

\| CL_WRITE_ISO | 18 | 18 | 182 | 0 |



\- Draft/Target 归&#x5C5E;**\*\*按 block table 形状判定\*\***，**\*\*与 oracle 是否匹配无关\*\***；**\*\*不匹配与未归属调用全部计数保留，不筛除\*\***。

\- \`actual_seq_lengths_kv == window_visible_exact\` 在 **\*\*33/33\*\*** draft 记录上成立。

\- **\*\*这是算子调用参数证据\*\***，**\*\*不是\*\***&#x8BBE;备执行证据，**\*\*不是\*\*** kernel 读行为证据。\`LEVEL_4\` 标&#x7B7E;**\*\*不\*\***&#x65AD;言已观测全部物理读取。



**---**



**## 9. 方法 / Backend / 拓扑支持矩阵**



完整机器可读版本：\`reports/P0_P4_Server_Support_Matrix.json\`（14 项）。



\| Method | Model/backend | Window OFF | Window ON eager | Graph | Async | Prefix | Parallel | NPU evidence | Verdict |

\|---|---|---|---|---|---|---|---|---|---|

\| MTP | any | FORCED_OFF | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | none | **\*\*FORCED_OFF\*\*** |

\| DeepSeek-V4 co-trained DSpark | dspark | CONFIG_OFF | CONFIG_OFF | — | — | — | — | none | **\*\*EXPECTED_GATE\*\*** |

\| DFlash | dflash | CONFIG_OFF | ELIGIBLE_ON | EXPECTED_GATE | EXPECTED_GATE | EXPECTED_GATE | EXPECTED_GATE | static only | **\*\*STATIC_VERIFIED\*\*** |

\| eligible DSpark | dspark | CONFIG_OFF | ELIGIBLE_ON | EXPECTED_GATE | EXPECTED_GATE | EXPECTED_GATE | EXPECTED_GATE | static only | **\*\*STATIC_VERIFIED\*\*** |

\| **\*\*Eagle3 static K\*\*** | eagle3 / dense GQA | ELIGIBLE_ON | **\*\*ELIGIBLE_ON（单请求已 NPU 验证）\*\*** | EXPECTED_GATE | EXPECTED_GATE | EXPECTED_GATE | EXPECTED_GATE | **\*\*NPU L3+L4\*\*** | **\*\*NPU_VERIFIED（单请求）\*\*** |

\| plain Eagle | eagle | FORCED_OFF | FORCED_OFF | — | — | — | — | none | **\*\*FORCED_OFF\*\*** |

\| DFlash2 | dflash2 | UNSUPPORTED | UNSUPPORTED | — | — | — | — | none | **\*\*UNSUPPORTED\*\*** |

\| dense GQA | ascend attn v1 | n/a | 必需 | EXPECTED_GATE | EXPECTED_GATE | EXPECTED_GATE | ELIGIBLE_ON (TP1) | NPU live | **\*\*STATIC_VERIFIED\*\*** |

\| DSA | dsa | n/a | UNSUPPORTED | — | — | — | — | none | **\*\*UNSUPPORTED\*\*** |

\| SFA | sfa | n/a | UNSUPPORTED | — | — | — | — | none | **\*\*UNSUPPORTED\*\*** |

\| MLA | mla | n/a | UNSUPPORTED | — | — | — | — | none | **\*\*UNSUPPORTED\*\*** |

\| recycling | — | n/a | UNSUPPORTED | — | — | — | — | none | **\*\*UNSUPPORTED\*\*** |

\| multi-group | — | n/a | UNSUPPORTED | — | — | — | — | none | **\*\*UNSUPPORTED\*\*** |

\| TP/CP/SP/FlashComm | 并行 | ELIGIBLE_ON | EXPECTED_GATE | — | — | — | UNSUPPORTED | none | **\*\*EXPECTED_GATE\*\*** |



E12 负向 gate 实测（5/6，均为显式 \`reason=\` P2 拒绝）：



\`\`\`

graph  : reason=Graph mode FULL_AND_PIECEWISE is not verified in P2

async  : reason=Async scheduling is not verified in P2

prefix : reason=prefix cache is not verified for Window ON

TP=2   : reason=TP=2 is not verified in P2

mixed  : NotImplementedError: MRV2 draft-window P4a does not support mixed prefill/decode proposals

dynamic-K : NOT_RUN（本 build 无 CLI 入口）

\`\`\`



**---**



**## 10. Debug 观测工具说明**



Debug 分支 \`debug/p4b-r3-observability\`，6 个 commit，**\*\*全部为观测/测试工具\*\***：



\| commit | 内容 |

\|---|---|

\| \`4c79efaa7\` | R3a 运行时 trace（policy / proposal / step / read_inputs / consumer_boundary / lifecycle） |

\| \`11e6369e3\` | R3a+ 语义加固（字段改名、independent oracle、active-row equality、completeness、multi-request 控制、sync 分级） |

\| \`30c87a598\` | **\*\*Level 4\*\***：\`device_op.py:110\` 算子叶子前的 task-bound operand 捕获 |

\| \`6e06c5486\` | 非 tensor operand（list）支持 + \`NO_SYNC\` 模式 |

\| \`24758c5f5\` | active-slice carrier + \`admit_step\` 缺陷修复 |

\| \`2a4856134\` | 同步内 BEFORE_WINDOW / AFTER_WINDOW 写侧/Target 快照 |



**\*\*开关纪律\*\***：全部由 \`VLLM_ASCEND_DRAFT_WINDOW_DEBUG=1\` 控制；关闭&#x65F6;**\*\*不产生输出、不建 tensor、不做 D2H、不改控制流\*\***（由 \`Tensor.cpu\` 调用计数=0 的单测证明）。测试 **\*\*44/44 通过\*\***。



**\*\*Debug 不得算作 production 交付\*\***——已由 §2.2 验证。



**---**



**## 11. Node133 与 Node101 差异**



\| | Node133 | Node101 |

\|---|---|---|

\| 设备族 | **\*\*A2 (910B2)\*\*** | A3（声称） |

\| 证据 | **\*\*完整\*\***（8 份报告 + 17 run 目录 + traces） | **\*\*完全缺失\*\*** |

\| 报告 | 全部存在 | \`P4b_R3_Node101_Restore_Report.md\` 等三&#x4EFD;**\*\*不存在\*\*** |

\| 迁移包 | 已生成（\`migration/\`，tar+bundle+SHA256SUMS） | **\*\*无执行证据\*\*** |

\| 结论可继承性 | — | **\*\*不可继承\*\*** |



**\*\*裁决\*\***：**\*\*Node101 状态 = UNKNOWN\*\***。Node133 的 A2 结&#x8BBA;**\*\*不得\*\***&#x88AB;表述为 Node101 的 A3 PASS。任务描述的 \`reports/source_node133/\`、\`reports/external_node101/\`、\`commands/\` 目&#x5F55;**\*\*不存在\*\***；实际布局为 \`reports/\`、\`results/\`、\`debug/\`、\`logs/\`、\`migration/\`。



**---**



**## 12. 已验证内容**



\| 项 | 级别 | 证据 |

\|---|---|---|

\| production SHA/tree 一致、clean | Git | §2 |

\| 10 个 production commit lineage 正确 | Git | §2.1 |

\| Debug 与 production 隔离 | Git | §2.2 |

\| P1/P2/P3 静态实现 | static | production 单测 |

\| P4a/P4b 静态契约 | static | 冻结文档 + 单测 |

\| P4b 单请求 oracle / completeness / anchor / per-step E_s | **\*\*NPU L3\*\*** | B_on 等 trace |

\| P4b FullSource 投影（active row == canonical slice） | **\*\*NPU L3\*\*** | 852/852 |

\| P4b 写侧 / Target 隔离 | **\*\*NPU L3\*\*** | CL_WRITE_ISO 84/84 |

\| P4b 算子参数（draft vs target 分离） | **\*\*NPU L4\*\*** | 33/33 匹配 consumer 与 oracle |

\| P4b 顺序同 Engine 隔离 | **\*\*NPU L3\*\*** | CL_SEQ_on |

\| 负向 gate（5/6） | **\*\*NPU live\*\*** | E12 显式 reason |

\| mixed fail-closed 在 NPU 触发 | **\*\*NPU live\*\*** | E10/E11 |

\| Final 非 Debug overlay 可用 | **\*\*NPU live\*\*** | CL_FINAL_NODEBUG |



**---**



**## 13. 未验证内容**



\| 项 | 状态 | 原因 |

\|---|---|---|

\| **\*\*P4a NPU Window ON\*\*** | **\*\*无证据\*\*** | 本机未运行；GLM TP8 OFF smoke 不可替代 |

\| **\*\*受控多请求纯 decode\*\*** | **\*\*INCOMPLETE\*\*** | 四种构造均无法形成 batch>1 |

\| persistent row index reuse | **\*\*NOT_OBSERVED\*\*** | \`idx_mapping\` 未插桩 |

\| strict \`[A,B]→[B,A]\` swap | **\*\*NOT_OBSERVED\*\*** | 依赖 batch>1 |

\| **\*\*slot oracle（independent）\*\*** | **\*\*INCOMPLETE\*\*** | 未独立重算 \`expected_slot\` |

\| **\*\*future-column 真实逐步列需求\*\*** | **\*\*PARTIAL\*\*** | F07 跨 4 block 且行匹配，&#x4F46;**\*\*未隔离出 step 间新增列需求事件\*\*** |

\| **\*\*E09 cross-boundary rejection\*\*** | **\*\*INSUFFICIENT_EVIDENCE\*\*** | 固定 fixture/seed 下不可稳定复现 |

\| **\*\*Level 5 kernel 读取\*\*** | **\*\*NOT_OBSERVED\*\*** | 无 profiler/kernel trace |

\| **\*\*device lifetime happens-before\*\*** | **\*\*OPEN\*\*** | NO_SYNC 一致性≠reader/overwrite 顺序 |

\| dynamic-K 负向测试 | **\*\*NOT_RUN\*\*** | 无 CLI 入口 |

\| R4 性能 | **\*\*NOT_RUN\*\*** | 超范围 |

\| Node101 (A3) 全部 | **\*\*UNKNOWN\*\*** | 证据缺失 |



**\*\*特别声明\*\***（对应 §1 的六条禁令）：

\- OFF 期间 0 条 trace **\*\*不是\*\*** ON prefill bypass 的直接证据；bypass 证据来自 ON 侧 \`window_initialized\` 在 profile 之后才触发 + prefill 走 baseline 的 ON 侧观测。

\- 长 prompt 跨多个历史 block **\*\*不等于\*\*** future-column 通过（当前为 PARTIAL）。



**---**



**## 14. 风险登记**



\| Risk | Evidence | Impact | Current mitigation | Required next action | Gate |

\|---|---|---|---|---|---|

\| **\*\*mixed arrival 导致服务级 EngineCore 退出\*\*** | \`results/E10_E11_multireq\` | **\*\*两个请求全失败 + 服务停止服务\*\***；若目标是通用在线并发，这&#x662F;**\*\*发布阻塞\*\*** | 无（fail-closed 是设计契约，但爆炸半径未缓解） | 决策：per-request 优雅拒绝 vs 维持中止；或限制为 batch=1 | **\*\*release HOLD\*\*** |

\| multi-request baseline 未建立 | §8.2 | 无法验证 batch>1 语义 | 无 | 需调度层支持或改变到达模型 | \`G-AR-STEP\` |

\| stream / lifecycle 未证明 | §13 | reader/overwrite 顺序无保证 | NO_SYNC 表明结果不依赖观测 | 事件/stream 级插桩 | L01 |

\| slot oracle 缺口 | §13 W02 | 物理写位置未独立校验 | 输出一致间接约束 | 独立重算 \`expected_slot\` | \`G-GQA-EAGER\` |

\| Level 5 未观察 | §13 | 证据上限 L4 | 明确标注 | profiler/kernel trace | \`G-GQA-EAGER\` |

\| **\*\*P4a NPU Gate 仍 OPEN\*\*** | §7 | P4a correctness 未在 NPU 验证 | static 已 PASS | NPU Window ON 运行 | \`G-GQA-EAGER\` |

\| Graph one-step lag | 设计文档 | graph 模式语义差一步 | graph 被 gate 拒绝 | P6 | graph gate |

\| capture 绑定错误 storage | 设计文档 | 潜在错误绑定 | 未测 | P6 spike | — |

\| stale pointer | 设计文档 | 复用陈旧指针 | 未测 | P6 | — |

\| Target alias | §12 W01 已测（84/84 隔离） | — | **\*\*已验证隔离\*\*** | 保持回归 | 已缓解 |

\| parallel / async lane reuse | 设计文档 | lane 复用污染 | gate 拒绝 | P7 独立 Gate | P7 |

\| **\*\*Debug provenance 与 production 混淆\*\*** | §2.2 已验证隔离 | 曾为风险 | \`git merge-base\` 逐 commit 验证 | 每次交付前重跑该检查 | 已缓解 |

\| **\*\*Node133 A2 与 Node101 A3 不可直接继承\*\*** | §11 | 错误结论传播 | 本报告显式标注 UNKNOWN | Node101 独立运行 | Node101 |

\| release HOLD | 冻结文档 + 本轮 | 未发布 | 保持 | 见 §13 | **\*\*HOLD\*\*** |



**---**



**## 15. P5–P8 readiness**



\| Phase | 目标 | 结论 |

\|---|---|---|

\| **\*\*P5\*\*** | live/capture/replay source spy；Ascend-only seam；OFF 无变化 | **\*\*DESIGN READY：是\*\***（Final Design 已定义）\<br>**\*\*TEST-ONLY SPIKE READY：部分\*\***（单请求 eager 基线已有，受控多请求无基线）\<br>**\*\*PRODUCTION GRAPH BINDING READY：否\*\***\<br>**\*\*GRAPH ON READY：否\*\***（\`reason=Graph mode FULL_AND_PIECEWISE is not verified in P2\`） |

\| **\*\*P6\*\*** | PIECEWISE/FULL per consumer；route fingerprint；A/B/A；timeline；AR per-step | **\*\*前置未满足\*\***：Level 5 未观察、graph gate 未开、graph one-step lag 未处理。**\*\*BLOCKED\*\*** |

\| **\*\*P7\*\*** | DSA/SFA/V4.1/recycling；CP/SP/FlashComm；async；parallel | **\*\*BLOCKED\*\***。**\*\*明确不得\*\***&#x56E0; P4b 单请求通过而默认开放这些 route——每条 route 需独立 Gate。 |

\| **\*\*P8\*\*** | owner mandatory 矩阵；OFF 回归；性能报告；交付包；release 结论 | **\*\*HOLD\*\***：multi-request INCOMPLETE、P4a NPU OPEN、R4 未跑 |



**---**



**## 16. 后续测试建议**



1\. **\*\*P4a NPU Window ON\*\***（最高优先）：用 DFlash 或 eligible DSpark + 单请求，在 A2 上取得 NPU 证据，并完成 **\*\*physical-slot oracle\*\*** 以关闭 \`G-GQA-EAGER\`。

2\. **\*\*slot oracle\*\***：独立重算 \`expected_slot = physical_block\*B + offset\`（需 trace 记&#x5F55;**\*\*完整\*\*** active row 的 physical block id，而非截断 32 值）。

3\. **\*\*device lifetime\*\***：以事件/stream 插桩证明 \`previous reader complete → retire → rewrite permitted\`；不得用 NO_SYNC 一致性替代。

4\. **\*\*多请求\*\***：先裁决 mixed &#x7684;**\*\*语义\*\***（优雅拒绝 vs 中止），再考虑是否值得为 batch>1 改到达模型；**\*\*不要\*\***&#x7EE7;续用并发 HTTP 撞 gate。

5\. **\*\*future-column\*\***：构&#x9020;**\*\*逐步新增列需求\*\***&#x7684; case，而非依赖长 prompt。

6\. **\*\*E09\*\***：有界搜索 fixture/seed；若无则永久记 \`INSUFFICIENT_EVIDENCE\`。

7\. **\*\*Level 5\*\***：如 \`G-GQA-EAGER\` 要求 profiler oracle，需小规模 kernel/profiler 诊断。

8\. **\*\*Node101\*\***：先确认迁移包是否落地并执行；**\*\*不要\*\***&#x628A; Node133 结论直接写成 Node101 PASS。



**---**



**## 17. Artifact 索引**



完整清单见 \`reports/P0_P4_Server_Evidence_Index.md\`（39 项已发现 / 3 项缺失）。



关键产物：



\`\`\`

reports/MRV2_Draft_Window_P0_P4_Server_Final_Evidence_Report_CN.md   本报告

reports/P0_P4_Server_Gate_Status.csv                                  23 行

reports/P0_P4_Server_Support_Matrix.json                              14 methods

reports/P0_P4_Server_Conflict_Resolution.csv                          25 行

reports/P0_P4_Server_Evidence_Index.md                                发现/缺失清单

reports/P4_Server_Restore_Report.md / P4_Runtime_Binary_Binding_Report.md

reports/P4_R1_Service_And_Candidate_Preflight_Report.md

reports/P4b_R2_Route_Establishment_Report.md

reports/P4b_R3a_Observability_Report.md / P4b_R3a_Plus_Trace_Semantics_Report.md

reports/P4b_R3_Final_Correctness_Report.md（§25/§26 为当前状态）

reports/P4b_R3_Closeout_Report_node133.md

results/run_manifest.json（17 runs）/ case_results.json（28 cases）

results/{B_on,B2_boundary,B3_nosync,B4_active_slice,CL_SEQ_on,CL_WRITE_ISO,

         CL_FINAL_NODEBUG,CL_AB_on,CL_AB_mbt,E10_probe,E10_n2,E10_E11_multireq,

         E12_negative,E12_graph,A1_off,A2_off,A3_off_F08}/

debug/（6 个 patch、trace schema、44 个测试、offline_batch_driver.py 等）

/home/wenqing/reference/P4_freeze/（设计文档 + notes + 10 format-patches + bundle）

migration/（Node101 迁移包：tar + bundle + SHA256SUMS）

\`\`\`



**---**



**## 18. 最终 Verdict**



\`\`\`text

P0–P3 PRODUCTION IMPLEMENTATION : PARTIAL   （static PASS；P0 manifest 本轮未重推导）

P4a STATIC                      : PASS

P4a NPU                         : OPEN      （本机无 Window ON 运行）

P4b STATIC                      : PASS

P4b SINGLE-REQUEST NPU          : PASS

P4b MULTI-REQUEST NPU           : OPEN      （受控构造无法形成 batch>1）

G-GQA-EAGER                     : OPEN

G-AR-STEP                       : OPEN

P0–P4 REQUIRED DELIVERY         : PARTIAL

P5 DESIGN PREFLIGHT             : READY

P5 GRAPH ON                     : BLOCKED

FEATURE RELEASE                 : HOLD

\`\`\`



**\*\*P4b 精确结论（对应 §8）\*\***：



\`\`\`text

SINGLE-REQUEST WINDOW              : PASS

CONTROLLED MULTI-REQUEST PURE-DECODE : INCOMPLETE

SEQUENTIAL SAME-ENGINE ISOLATION   : PASS

PERSISTENT ROW REUSE               : NOT_OBSERVED

WRITE/TARGET ISOLATION             : PASS

SLOT ORACLE                        : INCOMPLETE

OPERATOR INPUTS                    : PASS (Level 4)

KERNEL READ BEHAVIOUR              : NOT_OBSERVED

DEVICE LIFETIME                    : OPEN

GENERAL ONLINE MIXED ARRIVALS      : UNSUPPORTED_WITH_ENGINE_ABORT

G-AR-STEP                          : OPEN

\`\`\`



**\*\*本报告的审计立场\*\***：以上每一项均按证据优先级裁决，**\*\*未把 OPEN 写成 PASS\*\***。\`G-GQA-EAGER\` 与 \`G-AR-STEP\` 的 OPEN 状态与冻结文档（2026-10-10）一致，本&#x8F6E;**\*\*没有\*\***&#x4EFB;何证据支持关闭它们。Feature release 保持 **\*\*HOLD\*\***。



**---**



*\*本报告为证据裁决文档，非开发交付。未修改 production，未运行模型，未进入 P5，未跑 R4。\**
