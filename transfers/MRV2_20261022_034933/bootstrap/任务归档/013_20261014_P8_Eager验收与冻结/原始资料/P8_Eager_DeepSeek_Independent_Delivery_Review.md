# MRV2 Draft Sliding Window — P8-E Eager Delivery Independent Review

- Reviewer: DeepSeek（最终本地 Independent Reviewer；未修改任何 production 代码）
- Date: 2026-10-14
- 事实源：真实 checkout 的 source/diff/tree/artifacts + 我自行执行的测试、探针与 freeze 复现。Codex 的总结、Support Matrix、Owner Matrix、NPU Plan、测试数字、Freeze 声明均**仅作为被审计对象**。
- 审计对象：代码冻结于 P7-E Final `4753742ab181920292c504a79eedecf9b428ae1b`（**无 P8 production commit**），交付包 `Note/MRV2/P8_eager_freeze/`。

## 0. 结论摘要

| 必须回答项 | 结论 |
|---|---|
| `TRACK SEPARATION` | **PASS** |
| `EAGER SUPPORT MATRIX` | **FACTUAL** |
| `READY_FOR_NPU ROWS` | **VALID** |
| `OFF/FORCED-OFF` | **PASS** |
| `ASYNC EVIDENCE BOUNDARY` | **PASS** |
| `G-MIXED` | **OWNER_BLOCKED**（非 INCORRECTLY REPORTED） |
| `RUNTIME EVIDENCE LEDGER` | **FACTUAL** |
| `NPU CAMPAIGN PLAN` | **EXECUTABLE** |
| `PERFORMANCE PLAN` | **EXECUTABLE** |
| `FREEZE` | **REPRODUCIBLE** |

```
P8-E REVIEW: APPROVE FOR EAGER NPU CAMPAIGN
READY FOR COMPREHENSIVE EAGER NPU: YES（在 P7-final SHA 上；模型/W/K 由 owner 提供）
EAGER RELEASE: HOLD
GRAPH TRACK: CORRECTLY FROZEN
FULL FEATURE RELEASE: MUST REMAIN HOLD
EAGER NPU VERIFIED: NO — 本次未运行任何服务器 NPU，故不可能为 YES
```

Findings：**0 Critical / 0 Major / 6 Minor / 3 Question**（全部为文档级；**无需修改 production 代码**）。

---

## 1. Git / Baseline Audit（VERIFIED）

| 项 | 要求 | 实测 |
|---|---|---|
| vLLM HEAD / tree | `84030bbe...` / `f3e320f8...` | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` / `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`，`git status --porcelain --untracked-files=all` 空 |
| P7-E Final（= P8 parent） | `4753742ab181920292c504a79eedecf9b428ae1b` | 一致；tree `b7e525c3c9d45617ad1023ad45c6948c466a3631` |
| P8 commit | 允许“明确的小型 delivery-fix” | **不存在**：`git log --all --grep=P8` 无命中，无 P8 分支，工作区 clean → 交付以 P7-E Final 冻结体交付 |
| Debug branch commit | 不得进入 lineage | `2a485613`（证据账本所引 debug SHA）在本仓库 `cat-file` 不存在，`merge-base --is-ancestor` 非祖先 ✓ |
| 上游 hook 原型 | 不得进入 lineage | `04034692` 在本仓库不存在、非祖先 ✓ |
| 隐藏 dirty 文件 | 无 | `git status --porcelain -uall` 空；`git stash list` 0 条 ✓ |
| Graph capture 新实现 | 无 | P7-E Final 仅改 3 个 `draft_window*.py` + 3 个测试；P8 无 commit ✓ |

**完整 lineage（独立重建，`git log --reverse 841dc6cc..4753742`，16 条线性提交）**：

```
841dc6cc base
 → b12399a P1 policy/math → c58daea P1 fix
 → 8357967 P2 inventory/FullSource → fac8412 P2 fix
 → feab28f P3 runtime ownership → 1672788 P3 fix
 → 0dd83e9 P4a eager → 4c1f691 P4a fix
 → d0c8883 P4b Eagle3 static-K → 1011e2c P4b fix
 → 266eec5 P5 graph binding → 0702c89 P5 fix
 → 20673a1 P6 read carrier → 7599497 P6 fix
 → 7feb6de P7 capability → 4753742 P7 fix / Final
```

与 `MRV2_P0_P7_Commit_Manifest.md` 的链式图**逐条一致** ✓（含 `P6A` 无 production commit：lineage 中 7599497 → 7feb6de 直接相邻 ✓）。

---

## 2. Track Separation Audit

**结论：GRAPH TRACK = FROZEN（PASS）。**

- 交付包中对 `SUPPORTED` 的全部出现都是**否定式**：`P8_Eager_Final_Support_Matrix.md:18`（"No P7-final route is `SUPPORTED`"）、`:12`（"Graph is tracked separately as `GRAPH_FROZEN`"）、计划 `:207`、快照 `MRV2_P0_P7_Implementation_Snapshot.md:102`。全包未发现 "Graph READY" / "FULL supported" / "PIECEWISE supported" / "P6 carrier = Graph support" 任何等价表述。
- 源码侧独立复核：Graph 模式判定 `draft_window_eager_capability.py:250-255` → `FAIL_CLOSED`，且 `require_live_materialization()`（`:116-125`）在任何 P2/P3 分配前 raise；P6 provider `install_draft_window_graph_binding_provider` 在 production 中仍**无调用者**（`draft_window_graph.py:1443` 仅定义）。
- P8 包装内容（`notes/`、`evidence/`）也把 Graph 与 Eager 分开陈述，无状态混用。

---

## 3. Support Matrix 反向验证

我按“**method eligible / STANDARD family / dense GQA-FIA / one gid / graph NONE / async false / topology 全 1 / flags off / prefix off / policy 正确 / live P4 consumer 存在**”逐条回到 production 反查 `READY_FOR_NPU`：

| 必要条件 | 源码证据 |
|---|---|
| method eligible | `draft_window.py:610-672`（eagle3/dflash/dspark → `ELIGIBLE_ON`） |
| STANDARD hardware family | `draft_window.py:1309`（`get_current_hardware_profile().attention_backend_family`）+ `draft_window_eager_capability.py:243-249`；A2/A3/A5=`STANDARD`，`_310P`=`COMPATIBILITY`（`device/hardware_profile.py:168/180/197/220`） |
| dense GQA/FIA | `draft_window.py:849-877` 分类 + `:983-996` group failure（非 `AscendAttentionBackend`/非 `AscendAttentionMetadataBuilder` 一律拒绝） |
| one gid | `:150-179` + `draft_window_eager_capability.py:269-281, 330-335` |
| graph NONE | `:250-255` |
| async false | `:343-348`（async → `STATIC_READY`） |
| topology 全 1 + flags off | `:298-319` |
| prefix off | `:256-261` |
| live P4 consumer 存在 | `autoregressive/speculator.py:79`（`Eagle3DraftWindowMixin`）、`dflash/speculator.py:38`、`dspark/speculator.py:54`（`DraftWindowEagerMixin`） |

**继承泄漏专项（§6 “backend subclass accidentally classified dense”）**：我枚举了 `vllm_ascend/attention/` 全部 backend 类：

| 类 | 判定 | 结果 |
|---|---|---|
| `AscendDSABackend` + `C4/C128/SWA/C4State/C128State`（`dsa_v1.py:214/276/288/300/310/320`） | DSA | FAIL_CLOSED ✓ |
| `AscendMLABackend`（`mla_v1.py:82`） | MLA | FAIL_CLOSED ✓ |
| `AscendSFABackend`（`sfa_v1.py:267`）、`AscendSFAIndexerBackend`（`indexer.py:92`） | SFA | FAIL_CLOSED ✓ |
| `AscendFABackend`（`fa3_v1.py:11`）、`AscendIndexerKPoolBackend`/`TailBackend`（`indexer_kpool.py:210/300`） | 非 `AscendAttentionBackend` 子类 | group failure → FAIL_CLOSED ✓（recycling/kpool 未落入 dense） |
| `AscendAttentionBackend310`（`_310p/attention/attention_v1.py:48`） | 设备族 = COMPATIBILITY | **family gate 拦截** → FAIL_CLOSED ✓ |
| `AscendDFlash2Speculator`（`dflash2/speculator.py:107`） | route 仍为 `"dflash2"` | FAIL_CLOSED ✓（我**执行**验证：`_speculator_name='DFlash2'` → route `dflash2`；MRO 未回退到 `DFlash`） |

未发现任何“意外 dense”路径。**EAGER SUPPORT MATRIX: FACTUAL / READY_FOR_NPU ROWS: VALID。**

---

## 4. Platform Gate（P7 Review F-01 修复）独立验证

**结论：F-01 已被真实修复，且 class inheritance 无法绕过。**

1. **family 参与 decision**：`draft_window_eager_capability.py:243-249` 在 dynamic-K / route / graph / prefix / layout / parallel 全部判定**之前**检查 `runtime_context.attention_backend_family is not AttentionBackendFamily.STANDARD` → `FAIL_CLOSED`；family 同时进入 `P7EagerTopologyFingerprint`（`:42`，`__post_init__` `:67-68` 强制类型）与 `_build_topology_fingerprint`（`:161`）。
2. **COMPATIBILITY 不可进入 FullSource**：我**执行**了独立探针（自建，非复制其测试）：把 `draft_window.get_current_hardware_profile` 换成 COMPATIBILITY、并把 `build_full_draft_kv_source` 换成必抛断言，随后走 production 入口 `build_draft_window_source_capability(...)` → 抛 `NotImplementedError(... COMPATIBILITY ...)`，全程未创建 FullSource ✓。
3. **310P regression 存在**：`test_draft_window.py::test_compatibility_hardware_family_stops_before_full_source_allocation`、`test_draft_window_eager_capability.py::test_compatibility_attention_backend_family_fails_closed`（后者专门用 `AscendAttentionBackend`/`AscendAttentionMetadataBuilder` 的**子类**证明无法凭继承洗白）✓ 我本地运行通过。
4. **继承不可绕过**：判定来源是**设备 profile 常量**（`hardware_profile.py:168-220`），不是 backend 类关系；且未注册设备类型直接 `RuntimeError`（`hardware_profile.py:264-270`，我执行验证 `"NOT_A_DEVICE"` → raise，**无 STANDARD 兜底**）✓。
5. 我另行执行验证 `_310P → COMPATIBILITY`、`A2/A3/A5 → STANDARD` ✓。

**310P 不可能 READY_FOR_NPU** ✓（§4 的 Major/Critical 条件不成立）。

---

## 5. OFF / Forced-OFF（追 production 调用顺序，非只看 spy）

```
init_speculator (spec_decode/__init__.py:39)
  → resolve_draft_window_policy            # :44-51  最先
      ├ CONFIG_OFF  → _init_speculator_baseline 并 return   # :54-55
      ├ FORCED_OFF  → baseline + warning 并 return          # :57-63
      └ ELIGIBLE_ON → resolve_static_future_offset + validate_eligible_window_numbers  # :65-73
  → _configure_eligible_draft_window(_configure_draft_window)  # 仅 eligible
…
set_attn → _initialize_draft_window_source_capability
  → policy 缺失即 return（零状态）   # dflash:47-51 / dspark:47-51 / AR:105-106
```

- **CONFIG_OFF**：`resolve_draft_window_policy:625-632`（`requested_window_size is None`）→ 不调用 `_configure_draft_window` → `_initialize_...` 立即 return → 无 inventory、FullSource、workspace、P7 拓扑状态、async pool、Graph provider ✓（“zero Window allocation/state”成立）。
- **MTP**：`:633-641` 在**任何数值校验之前**返回 `FORCED_OFF`（docstring 明确此顺序属于契约）→ `validate_eligible_window_numbers` 根本不会执行 ✓。
- **DeepSeek-V4 共训 DSpark**：`:643-651`（`_is_deepseek_v4_target` 在 `:605-608`）→ 同样早于数值校验与 inventory ✓。
- 关键点：`build_draft_window_source_capability` **只可能**由 eligible 分支触发（`_configure_draft_window` 仅 `__init__.py:104` 调用）✓；即使被误调，P7 也会在 FullSource 前 raise ✓。

**OFF/FORCED-OFF: PASS。**

---

## 6. Complex Backend Gates（逐项）

DSA / SFA（main+indexer）/ MLA / native-recycling / V4 组合 的拒绝均在 **FullSource 之前**（`draft_window_eager_capability.py:283-296, 336-342`，滞后于 `require_live_materialization` 的 raise）。分类器与 backend 清单见 §3 表（全部落在 DSA/SFA/MLA/NATIVE_OR_RECYCLING 或非 AscendAttentionBackend → FAIL_CLOSED）。

- **V4/V4.1**：仓库**不存在** `dsa_v41.py`（`ls vllm_ascend/attention/` 无匹配）；分类器 import 的是当前 owner（`draft_window.py:35-38`：`dsa_v1`/`sfa_v1`/`indexer`/`mla_v1`）✓ “不使用旧 dsa_v41 路径、按实际 consumer 分类”成立。
- 未找到 backend 子类被误判为 dense 的情形（§3 表）。

---

## 7. Parallel Gates

`draft_window_eager_capability.py:299-313` 对 TP/DP/PP/PCP/DCP ≠1 与 SP / DSA-CP / FlashComm=true 一律 `FAIL_CLOSED`（在 live source 之前）。

- 矩阵 `MATH_READY ≠ LIVE_SUPPORT` 的表述与实际一致：`project_dcp_window_interval` 在 production 中**无调用者**（仅 `draft_window_eager_capability.py` 定义 + 测试）。
- DCP helper 未被误用为 live support ✓；其正确性已在上阶段由我与 vLLM `_dcp_local_seq_lens_kernel` 穷举比对（0 mismatch）确认，此处无改动。

---

## 8. Async Evidence Boundary

| 检查项 | 结果 | 证据 |
|---|---|---|
| host pool 存在 | ✓ | `draft_window_async.py:63-330`（capacity/lane/epoch/fingerprint/abort/poll/release/guard） |
| live production installation 缺失 | ✓ | 全仓 grep：`draft_window_async` 仅被测试 import；无 speculator 引用 |
| 无真实 NPU completion event | ✓ | `DraftWindowCompletionToken` 仅是 `is_complete()` Protocol（`draft_window.py:1427-1430`） |
| async decision 仍 STATIC_READY | ✓ | `draft_window_eager_capability.py:343-348` |
| `require_live_materialization` 拒绝它 | ✓ | `:116-125`；`test_draft_window.py::test_async_source_capability_stops_before_full_source_allocation`（monkeypatch 断言 FullSource 未被创建）我复现通过 |
| derived buffer alias 保护存在 | ✓ | 修复后 `draft_window_async.py:204-226` 三重校验；我**执行**验证：window backing 与 canonical FullSource 两种 alias 均被拒（`ValueError ... must not alias ...`），且失败后 handle → `RETIRED`（fail-closed） |
| topology enforcement 存在 | ✓ | `draft_window.py:2322-2336` `_validate_topology_fingerprint`，在 `refresh:2103` / `_materialize_identity:2175` / `_require_active_inputs:2325` 三处；我**执行**验证：把 lane runtime 的 fingerprint 篡改（含置 `None`）后 `publish_metadata` 抛 `RuntimeError: generation topology fingerprint does not match ...` |

P8 **未**把 Async 标为 `READY_FOR_NPU`（矩阵为 `STATIC_READY`，并写明 "live fail closed"）→ §8 的 Major 条件不成立。

---

## 9. G-MIXED（独立检查当前 production）

```text
mixed still raises?                        YES
   证据: draft_window_eager.py:557-580，raise 在 :579；调用点 draft_window_eagle3.py:153 早于
        epoch_source.begin :164 → 不分配任何 window 状态
       （该文件未被 P7-E Final 修改：git diff --name-only 7feb6de 4753742 无 draft_window_eager.py）

safe admission exists?                     NO
   证据: production 中 grep "admission|single_active|max_num_seqs == 1" 无命中

owner decision exists?                     NO
   证据: P8_Eager_Owner_Mandatory_Matrix.md OM-20 = OWNER_DECISION_REQUIRED；文件尾
        "OWNER MANDATORY MATRIX: PARTIAL"；Release Risk Register R-01/R-08 = RELEASE_BLOCKER

service-wide abort evidence still applicable?  YES
   证据: 抛出点未变（同一 raise），P4 期 node133 观测的 EngineCore 级 abort 机制仍成立；
        ledger 将其 scope 限定为旧 SHA/A2/Eagle3 ✓
```

交付包将该状态如实标为 `OWNER_BLOCKED` + `RELEASE_BLOCKER` + `FEATURE RELEASE: HOLD`，**未**标 Eager release-ready → §9 的 Critical 条件不成立。**G-MIXED: OWNER_BLOCKED。**

---

## 10. Runtime Evidence Ledger 反向审查

| 非法继承 | 账本是否显式禁止 | 我的复核 |
|---|---|---|
| P4b → P4a | ✓ "P4b evidence does not prove P4a DFlash or DSpark" | ✓ |
| A2 → A3/A5 | ✓ "Node133 A2 does not prove Node101 A3 or A5"；Node101 行 = `missing` | ✓ 无 A3/A5 artifact |
| single → multi | ✓ "Single request does not prove batch>1, reorder, row reuse, or general serving"；并记录 4 次构造 batch>1 失败 | ✓ |
| L4 → L5 | ✓ "L4 operator arguments do not prove L5 kernel physical reads" | ✓（P4b 行只标 L3+L4） |
| old SHA → P7 SHA | ✓ "P4 evidence does not transfer to P7 final SHA without rerun" | ✓ 支持矩阵 Eagle3 行同口径 |
| host async → NPU async | ✓ "Host fake completion does not prove NPU completion or stream ordering" | ✓ |

**数值可核对**：账本引用 P4b 的 `284/284 proposals、852/852 active rows、33/33 Draft FIA exact lengths`，我在其底层证据 `evidence/Server_Final_Evidence/MRV2_Draft_Window_P0_P4_Server_Final_Evidence_Report_CN.md:419-423,551,715,719` 中逐项对上 ✓；“负向 gate 5/6”亦与底层 `:603,723` 及 closeout 报告（`dynamic_K NOT_RUN`）一致 ✓ → 账本未放大或丢 scope。

**唯一缺口 → Q-01**：账本引用的 debug SHA `2a485613` 在本仓库不存在（无法逐行复核）；其“非生产祖先”声明成立但只能由“不存在”推出。

**RUNTIME EVIDENCE LEDGER: FACTUAL。**

---

## 11. NPU Test Plan Quality（可执行性判断）

判定标准：一台不了解开发史的服务器 Claude 能否直接执行。抽样结论：

| 抽样项 | exact config | model | command | oracle | pass condition | artifact | failure 分类 |
|---|---|---|---|---|---|---|---|
| DFlash（DFA-01..08） | ✓ 方法/K/W 位（`METHOD=dflash`、query width K+1） | △ “owner-approved DFlash pair”（无具体身份）→ **m-06** | ✓ §2 模板 | ✓ §4 八条 universal | ✓ 每案 | ✓ §3 schema + 目录名 | ✓ §9 |
| DSpark K（DSP-01） | ✓ `sample_from_anchor` 默认 true | △ 同上 | ✓ | ✓ | ✓ | ✓ | ✓ |
| DSpark K+1（DSP-02） | △ 只说 “Explicit `sample_from_anchor=false`”，**未给机制**（该键来自 **draft 模型 hf_config**，非 CLI 开关：`vllm/v1/worker/gpu/spec_decode/dspark/speculator.py:49-50`、`vllm_ascend/spec_decode/dspark_proposer.py:39`）→ **m-03** | △ | △ | ✓ | ✓ | ✓ | ✓ |
| Eagle3 K=3（E3-01..13） | ✓ W=64/K=3/具体 fixture | ✓ 参考路径 `/mnt/share/z00841464/model_weights/Qwen3-4B`（draft 需现场解析） | ✓ | ✓ | ✓ | ✓ | ✓ |
| multi-request（E3-10/E3-09） | ✓ 但注明“若可构造”并给 `INSUFFICIENT_EVIDENCE` 出口 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| negative Gate（NEG-01..19） | ✓ 期望状态逐条 | n/a | △ 负例的 flag 未逐条写成命令行（TP2/DP2/PP2/PCP2/DCP2、SP、DSA-CP、FlashComm、async、prefix）→ **m-05** | ✓ | ✓（§9：只有命中**指定** Gate 才算 PASS） | ✓ | ✓ |
| 310P negative（NEG-18） | ✓ 但写作 “existing MTP-only startup rejection **and/or** P7 family rejection” | n/a | ✓ | ✓ | ✓ | ✓ | ✓ → 见 **m-01** |

另外：§1 前置清单（hostname/device/firmware/CANN/容器 digest/双仓 SHA+tree/argv/env/展开配置/拓扑指纹/请求 fixture）、§10 停止条件、§9 结果分类（`ENVIRONMENT_OR_FIXTURE_ERROR` 明确不得计 PASS）齐备 ✓。`--additional-config '{"draft_window_size":W}'` 是真实可用键（`ascend_config.py:333,468`）✓。

**NPU CAMPAIGN PLAN: EXECUTABLE**（缺口均为参数化/机制说明级，见 Minor）。

---

## 12. Performance Plan

- A/B/A' 定义 + 只允许 `draft_window_size` 不同 + 不一致即拒绝（§1）✓
- warmup（≥10 未计量 + 最后 5 个样本稳定性）、repetitions（短 50 / 长 30 + bootstrap CI）、跨≥3 次独立启动随机化顺序（§4）✓
- 噪声/竞争拒绝（§4.5 + §2 前后记录其它设备进程；并发仅在 G-MIXED 关闭后）✓
- D2H/H2D（§7：逐笔记录 source/dest/caller/是否阻塞/为何不可复用）、sync（§5+§7）、HBM（§8 分五类，含“OFF/forced-OFF 不得分配 Window 状态”）✓
- TTFT/TPOT/延迟/acceptance/吞吐 + 全分位 + 配对差值（§6）✓
- **不拿 correctness run 冒充 performance**：§3 “Correctness campaign must pass before its performance sample is admissible”；§9 完成但无条件数据只记 `MEASURED`；文档头 “No performance result is generated locally” + `EAGER PERFORMANCE VERIFIED: NO` ✓
- 阈值由 owner 提供前不得给 release 判定 ✓

**PERFORMANCE PLAN: EXECUTABLE。**

---

## 13. Debug Playbook（症状抽样）

Playbook 为 13 层固定顺序，每层均有 `Source / Expect / Inspect / First divergence / Likely bugs / Forbidden workaround / Cleanup`，末附 first-divergence 报告模板与 Frozen Graph 附录。

| 抽样症状 | 是否给出 first divergence → 精确 source/function → 证据 → 安全插桩 |
|---|---|
| policy failure | ✓ §1（`init_speculator` / `resolve_draft_window_policy`；first divergence = 归一化/工厂 parity；禁止“静默 OFF”） |
| source shortage | ✓ §5（canonical FullSource；禁“从零值推断 valid count”）+ §6（禁“静默 clamp / 二次对齐 / window-of-window”） |
| wrong table | ✓ §11（builder kwargs/alias parity）+ §12（metadata 对但 actual operand 错；比较完整 table pointer/content，禁止仅凭 Python 对象相等推断物理读） |
| slot pollution | **△** 无独立条目；最近的是 §11（full slot mapping 合法性）与 §12（full physical slots 保持 baseline）→ **m-04** |
| stale generation | ✓ §7（stale/ABA identity、active backing 被覆盖）+ §9（stale read 失败） |
| async pending reader | ✓ §7 Cleanup（“preserve pending reader ownership”）+ §13（retire/reuse 顺序；禁止用全局 synchronize 冒充证明） |

**结论**：不是原则性空文；除 slot-pollution 缺独立条目（Minor）外，均满足“可定位到精确 source 与证据层级”的要求。

---

## 14. Freeze Audit（我独立复现四项声明）

| 声明 | 我的复现 | 结果 |
|---|---|---|
| `SHA256SUMS` 完整 | `shasum -a 256 -c SHA256SUMS`（107 条） | **0 FAILED** ✓ |
| Full diff → 精确 final tree | 以 `git archive 841dc6cc` 建干净基线 → `git apply --check` PASS → `git apply` → `git add -A` → `git write-tree` | `b7e525c3c9d45617ad1023ad45c6948c466a3631` ✓ **等于 final tree** |
| format patches → 精确 final tree | 基线 + `git am format-patches/*.patch`（16 条，lexical 顺序）→ 17 commits | tree 同上 ✓（**commit SHA 不同**，因为 `git am` 重签 committer 信息——文档已如实声明“tree identity 保留、commit id 可能不同”✓） |
| bundle → 精确 final SHA/tree | 先满足 prerequisite（`update-ref refs/heads/base 841dc6cc`）再 `git fetch MRV2_P0_P7.bundle 'refs/heads/feature/p7-eager-completion:refs/heads/restored'` | `restored` = `4753742ab181920292c504a79eedecf9b428ae1b`，tree = `b7e525c3...` ✓，`841dc6cc..restored` = **16 commits** ✓ |
| `git bundle verify` | 在源仓库执行 | `is okay`；记录 `requires 841dc6cc...`、ref → `4753742...` ✓ |

补充（对**恢复流程**有用的运维事实，非缺陷）：我第一次用 `git archive | tar` + `git add -A` 重建基线时 tree 少 4 个条目——3 个是被 `.gitignore:229/232` 忽略（`.claude/README.md`、`.gemini/*`）的**已跟踪**文件，1 个是 gitlink（`csrc/third_party/catlass`，`git archive` 无法落地）。改用 `git add -A -f` + `update-index --cacheinfo 160000,...` 后 tree 精确相等。**任何从零重建 index 的恢复脚本**都必须处理这两类条目；文档给出的 git-native 恢复路径（checkout → fetch bundle）不受影响。

**FREEZE: REPRODUCIBLE**（`P8_Freeze_Reproducibility_Report.md` 的四项声明与我的复现**逐项一致**，含“增量 bundle 需 exact base、非 standalone”的限制说明）。

---

## 15. Independent Tests（全部为我本地重跑）

| 范围 | 我的结果 | 与交付文档一致性 |
|---|---|---|
| P1–P7 targeted（9 文件：draft_window / async / capability / graph_binding / graph_carrier / eagle3 / eager / dspark_graph_contract / eagle_aclgraph_source） | **340 passed** | 文档写 `360 passed`（“P1–P7 targeted…DFlash2”，未列文件清单）→ **m-02** |
| 更宽 13 文件含 dflash2/dspark_speculator/runtime | **405 passed** | 同上 |
| `tests/ut/spec_decode/` 全量 | **588 passed, 13 skipped, 7 failed** | **与文档完全一致** ✓ |
| `tests/ut/attention/` | **472 passed, 3 skipped** | 一致 ✓ |
| `tests/ut/distributed/` | **572 passed**（284 subtests） | 一致 ✓（文档记录的沙箱内 571+1 error 亦为 socket 限制） |
| `tests/ut/worker/v2/` + `worker/test_block_table.py` | **37 passed** | 文档拆为 31 + 14（同源）✓ |
| `tests/ut/_310p/`（我跑整目录） | **155 passed, 2 skipped** | 文档只跑 310P model_runner（41 passed）→ 我覆盖更宽 ✓ |
| `tests/ut/test_ascend_config.py` | **71 failed / 51 passed** | 文档 83/71 → **Q-02**（失败数一致 71；分类同为 NOT PASS / environment-blocked ✓） |
| 静态检查（我自跑） | `ruff check` PASS；`ruff format --check`（3 文件）PASS；`git diff --check 841dc6cc 4753742` clean；`compileall` OK | 一致 ✓ |

环境问题分类（按 §15 记 NOT RUN / ENVIRONMENT BLOCKED）：
1. `test_speculators_vwn_eagle3.py` 7 项：`ValueError: Invalid attention backend for None`（`vllm/v1/attention/selector.py:208`），宿主机无 NPU；该文件对 draft_window 零引用；与 P6/P7 基线同数同因 ✓。
2. `test_ascend_config.py`：70 项 `RuntimeError: Failed to infer device type`（`vllm/config/device.py:56`）+ 1 项 `_build_info` ImportError → 环境阻塞，非 P7/P8 回归（P7 未改这些文件）✓。
3. `test_vllm_version_is`：与本环境必需的 `VLLM_VERSION=0.29.0` 互斥 → NOT RUN（环境冲突）✓。

---

## 16. Findings

### Critical — 无
（Graph READY / FULL-PIECEWISE supported / P6 carrier 冒充 Graph support / 310P READY / Async READY / G-MIXED 标 release-ready：**均不存在**。）

### Major — 无

### Minor

**m-01 — “310P startup admits only MTP” 在 4 份交付物中不成立（文档事实性）**
- Claim（`P8_Eager_Final_Support_Matrix.md` 310P 行、`P8_Eager_Owner_Mandatory_Matrix.md` OM-21、`P8_Eager_Release_Risk_Register.md` R-10、`P8_Eager_Comprehensive_NPU_Test_Plan.md` NEG-18 的 “MTP-only startup rejection and/or …”）：310P 启动只接受 MTP。
- Observed：`patch/worker/patch_v2/patch_spec_decode_310.py:39-52` 对**非 MTP** 方法直接委派 `_orig_init_speculator`；`spec_decode/__init__.py:107-165` 的 `_init_speculator_baseline` **没有任何 310P 门**（按 method 分派 dspark/dflash/mtp/eagle3）；`_310p/worker/v2/model_runner.py:727-736` 只按工厂结果接线。
- Expected：310P 上非 MTP 方法会正常构造 speculator，只有 **Window** 被 P7 family gate 拒绝。
- Reproduction：`grep -n "310\|is_310p" vllm_ascend/worker/v2/spec_decode/__init__.py` → 空；读上述三处。
- Correction：把该短语改为“窗口被 P7 `AttentionBackendFamily.COMPATIBILITY` 门在 FullSource 前拒绝；310P 非 MTP spec-decode 的启动路由不受本特性约束”。
- Release impact：无（状态列 `FAIL_CLOSED` 正确，且 family gate 已独立验证）；但会误导服务器操作者对 310P 行为的判断。

**m-02 — “360 passed” 未给文件清单，无法精确复现**
- Observed：文档 `P8_Local_Test_Results.md` §2 首行 `360 passed`，scope 描述为“P1–P7 targeted…DFlash2”。
- 我实测：9 文件 = 340；13 文件（含 dflash2/dspark/runtime）= 405；全量 spec_decode = 588（与文档一致）。
- Correction：在该行附确切文件清单（或直接以 `tests/ut/spec_decode/` 全量 + 排除文件的方式表述）。
- Release impact：无（所有 scope 均全绿；仅审计可复现性）。

**m-03 — DSP-02 未给 `sample_from_anchor=false` 的设置机制**
- Observed：`P8_Eager_Comprehensive_NPU_Test_Plan.md` DSP-02 只写 “Explicit `sample_from_anchor=false`”。
- 该键来源：draft 模型的 **hf_config**（`vllm/v1/worker/gpu/spec_decode/dspark/speculator.py:49-50`；Ascend 端 `vllm_ascend/spec_decode/dspark_proposer.py:39`），**不是** vLLM CLI 开关。
- Correction：在案例中写明具体机制（改 draft model `config.json`，或等价的 hf override 方式），否则服务器 Claude 无法构造 K+1 query width，且会误判为 oracle 失败。
- Release impact：影响 OM-03 若被 owner 列为 mandatory 时的可执行性。

**m-04 — Debug Playbook 缺 “slot pollution / 写侧” 独立条目**
- Observed：§5/§11/§12 覆盖了 slot 的**合法性/parity**，但没有一节以 “写侧 slot 污染” 为入口，也未给出写路径 owner（`_get_fia_params` 写侧 / KV 写入算子）作为 first-divergence 定位点。
- Correction：新增一节（Source = 写侧 slot 计算与 KV 写入；Inspect = 独立重算物理 slot（NPU plan §4.5 已定义该 oracle）；First divergence = Draft 写入落在 Target 行或 slot 被截断）。
- Release impact：无（该症状的检测 oracle 已存在于 NPU plan）。

**m-05 — 负例清单未逐条给出命令行 flag**
- Observed：NEG-13/14/15/16 只给维度名（TP2、DP2、PP2、PCP2、DCP2、SP、DSA-CP、FlashComm、async、prefix），§2 模板只演示正例。
- Correction：为每个负例补一行可直接复制的启动参数（标准 vLLM flag）或在 §2 给参数对照表。
- Release impact：无（可推导，但增加服务器侧猜测空间）。

**m-06 — DFlash/DSpark 正例无具体模型身份**
- Observed：DFA/DSP 案例要求 “owner-approved DFlash/DSpark pair”，无具体路径/仓库；Eagle3 反而给了 `/mnt/share/z00841464/model_weights/Qwen3-4B` 参考。
- Correction：若 campaign 需在 owner 下发前先跑通，请补一对参考模型（或在 §1 明确“模型身份由 owner 下发，附件另行提供”）。
- Release impact：影响 DFA/DSP 的即期可执行性（OM-02/OM-03 亦为 OWNER_DECISION_REQUIRED）。

### Question

**Q-01 — 证据账本引用的 debug SHA 无法复核**
`2a485613` 在本仓库不存在（`cat-file` 失败）。账本已声明“debug commits are observation tools only and are not production ancestors”，该声明成立（由不存在推出），但外部审计者无法检视其内容。建议在交付包中附 debug diff（或注明该 SHA 仅存在于服务器侧、不可打包），以保持账本可审计性。

**Q-02 — `test_ascend_config.py` 通过数不一致**
文档 `83 passed / 71 failed`，我实测 `51 passed / 71 failed`（失败数与失败原因完全同类：70× 设备类型推断失败 + 1× `_build_info`）。两方结论都是 **NOT PASS / environment-blocked** ✓。请确认其运行是否额外设置了 device-type 环境变量，以便该行可复现。

**Q-03 — Owner 决策项仍全部 OPEN（发布门，而非缺陷）**
`P8_Eager_Owner_Mandatory_Matrix.md` 的 21 行中，除 OM-04/05/21 为 mandatory negative 外，全部 `OWNER_DECISION_REQUIRED`；文件尾自评 `PARTIAL`。需要 owner 签署：正例方法/模型对/设备/W/K、general serving vs 单活跃准入、A3/A5 是否 mandatory、L5 读集与设备 happens-before 是否作为发布证据。P8 未替 owner 决定 ✓。

---

## 17. 最终裁定

```
TRACK SEPARATION:              PASS
    （P8 全包对 SUPPORTED/Graph 的表述均为否定式；无 Graph READY / FULL-PIECEWISE supported /
      P6-carrier-as-Graph-support；源码侧 graph 模式仍双层 fail-closed，provider 仍无安装点。）

EAGER SUPPORT MATRIX:          FACTUAL
    （每行状态与 production 一致；310P 行的状态列正确，仅解释性短语需修正 → m-01。）

READY_FOR_NPU ROWS:            VALID
    （11 项必要条件逐条回查源码；三条正例均有 live P4 consumer；无意外 dense 分类；
      P7 F-01/F-02/F-03 修复经我独立执行验证。）

OFF/FORCED-OFF:                PASS
    （按 production 调用顺序验证：policy 最先、forced-OFF 早于数值校验/inventory、
      capability 不构建、`_initialize_...` 立即 return → 零状态。）

ASYNC EVIDENCE BOUNDARY:       PASS
    （host pool 有界且无 production 安装点；无真实 NPU event；decision=STATIC_READY；
      require_live_materialization 拒绝；derived-buffer alias 与 topology drift 均被拒——已执行验证。）

G-MIXED:                       OWNER_BLOCKED
    （mixed 仍 raise（:579，且在 epoch 创建前）；无 admission；无 owner 决策；
      旧 P4 的 service-wide abort 证据仍适用。交付包如实标为 RELEASE_BLOCKER，未标 release-ready。）

RUNTIME EVIDENCE LEDGER:       FACTUAL
    （六类非法继承全部显式禁止；数值与底层服务器证据逐项对上；scope 精确到 SHA/机器/设备/方法/级别。
      唯一缺口：debug SHA 在本仓库不可检视 → Q-01。）

NPU CAMPAIGN PLAN:             EXECUTABLE
    （19 个负例 + 27 个正例案例，含 config 模板、oracle、pass 条件、artifact schema、失败分类与停止条件；
      缺口为参数化与机制说明级 → m-03/m-05/m-06。）

PERFORMANCE PLAN:              EXECUTABLE
    （A/B/A'、warmup/重复/随机化、竞争与噪声拒绝、D2H/H2D/sync/HBM 归因、TTFT/TPOT/吞吐与分位、
      correctness 未过不得计入、阈值为 owner 门。）

FREEZE:                        REPRODUCIBLE
    （SHA256SUMS 107/107 OK；full diff → 精确 final tree；16-patch git am → 精确 final tree；
      bundle → 精确 final SHA+tree（需 exact base 841dc6cc，文档已声明）；commit lineage 16 条线性重建成功。）
```

```text
P8-E REVIEW: APPROVE FOR EAGER NPU CAMPAIGN

READY FOR COMPREHENSIVE EAGER NPU:  YES
    （在 vLLM 84030bbe / vLLM-Ascend 4753742 上；模型路径与 W/K 由 owner 下发；
      m-01..m-06 为文档修正项，不阻塞 campaign 启动，但应在交付给服务器前修订。）

EAGER RELEASE:                      HOLD
    （G-MIXED OWNER_BLOCKED + R-01/R-02/R-03/R-08/R-17 + owner matrix PARTIAL。）

GRAPH TRACK:                        CORRECTLY FROZEN
FULL FEATURE RELEASE:               MUST REMAIN HOLD

EAGER NPU VERIFIED:                 NO   ← 本次评审未在服务器 NPU 上运行任何实验
EAGER PERFORMANCE VERIFIED:         NO
```

---

## 附录 A — 我的复现命令

```bash
# baseline
cd /Users/wenqingzhang/Desktop/vllm/vllm && git rev-parse HEAD HEAD^{tree} && git status --porcelain -uall
cd /Users/wenqingzhang/Desktop/vllm/vllm-ascend && git rev-parse HEAD HEAD^{tree} && git status --porcelain -uall
git log --oneline --reverse 841dc6cc..4753742          # 16 条线性
git cat-file -t 2a485613 2>&1                          # 不存在（debug SHA）
git cat-file -t 04034692 2>&1                          # 不存在（上游原型）

# tests（我的数字）
run() { env VLLM_VERSION=0.29.0 \
  PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm:/Users/wenqingzhang/Desktop/vllm/vllm-ascend \
  .venv/bin/python -m pytest -q "$@"; }
run tests/ut/spec_decode/            # 588 passed, 13 skipped, 7 failed(env)
run tests/ut/attention/              # 472 passed
run tests/ut/distributed/            # 572 passed
run tests/ut/_310p/                  # 155 passed
run tests/ut/worker/v2/ tests/ut/worker/test_block_table.py   # 37 passed

# static
.venv/bin/python -m ruff check  vllm_ascend/worker/v2/spec_decode/draft_window*.py
.venv/bin/python -m ruff format --check vllm_ascend/worker/v2/spec_decode/draft_window*.py
git diff --check 841dc6cc 4753742

# freeze（在 /tmp 复现，源仓库仅读操作）
cd /Users/wenqingzhang/Desktop/Note/MRV2/P8_eager_freeze && shasum -a 256 -c SHA256SUMS
git -C /Users/wenqingzhang/Desktop/vllm/vllm-ascend archive 841dc6cc | tar -x -C /tmp/p8freeze/base
cd /tmp/p8freeze/base && git init -q . && git add -A && git commit -qm base
git apply /…/MRV2_P0_P7_Full_Diff.patch && git add -A -f >/dev/null && \
  git update-index --add --cacheinfo 160000,41bf90da655bba3c66d0acd7e00abe33960ecfd6,csrc/third_party/catlass && \
  git write-tree                       # == b7e525c3…（final tree）
git bundle verify /…/MRV2_P0_P7.bundle
# bundle 恢复：先 update-ref 满足 prerequisite 841dc6cc，再 fetch → 4753742 / b7e525c3
```

独立探针（自建，未写入仓库）：
- `/tmp/p7probe/p8_probe.py`（310P→COMPATIBILITY 常量映射、未注册设备类型 raise、COMPATIBILITY 在 FullSource 前拒绝）
- `/tmp/p7probe/p8_probe2.py`（topology drift 拒绝 ×2、`backend_derived_buffers` 对 workspace 与 canonical FullSource 的 alias 拒绝）
- `/tmp/p7probe/route_probe.py`（DFlash2 route 保持 `dflash2`，继承未回退）
