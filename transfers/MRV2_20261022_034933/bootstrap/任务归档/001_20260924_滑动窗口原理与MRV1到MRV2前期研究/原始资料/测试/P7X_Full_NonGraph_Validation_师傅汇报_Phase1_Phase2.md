# P7-X Full Non-Graph Validation — 师傅汇报（Phase 1 + Phase 2）

**机器** `node-39-101` · **Campaign** `/mnt/wenqing/mrv2_p7x_full_nongraph_validation/`  
**日期** 2026-10-16 · **Phase 1 COMPLETE / Phase 2 COMPLETE / Phase 3 PAUSED（服务已停，HBM 已释放）**  
**报告性质**：REPORT-ONLY RECONSTRUCTION（未跑 NPU、未起服务、未跑 aisbench）

---

## 一、Version（源码树）

| item | value |
|---|---|
| perf candidate (vllm-ascend) | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` |
| perf tree / branch | `9a6c38c0e92853b462cd1f05aa5f70244f82a72f` / `perf/p7x-draft-window-hotpath` |
| parent baseline | `c1c2129aa49ee1de381130729de73124a6ec893a`（tree `384af8a0…`） |
| pinned vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| 可比性 | `SAME_DONOR_BYTE_IDENTICAL` —— 两树 native `.so` 与 `cann_ops_custom` 逐字节一致，Python 差异**仅** perf commit 的 3 个生产文件 |

**部署**：GLM-5.2-W4A8 + DSpark（K=8）· TP16/DP1/EP · `max_num_seqs=16` · `max_model_len=132096` · **MRV2** · Async ON · 非图模式 · `conc=1 / data_num=4`

## 二、MRV2 proof（16/16 硬门槛）

| instance | window | verdict | ranks |
|---|---|---|---|
| `A1_parent` / `B1_perf` / `A2_parent` / `B2_perf` | W1024 | `MRV2_VERIFIED` | **16/16** ×4 |
| `curve_off` | OFF | `MRV2_VERIFIED` | **16/16** |
| `curve_w1024` | W1024 | `MRV2_VERIFIED` | **16/16** |

✅ 6 个服务实例各自独立取证（worker 内观测探针 `identity.json`），未继承。

---

## 三、Phase 2 长度矩阵（**主表**）

配置：GLM5.2 + DSpark · K8 · TP16 · DP1 · max_num_seqs 16 · max_model_len 132096 · MRV2 · Async ON

| input | OFF 吞吐 (tok/s) | W1024 吞吐 | **gain** | OFF acc | W1024 acc | OFF TPOT | W1024 TPOT |
|---|---|---|---|---|---|---|---|
| **16K** | 87.120 | 81.060 | **−6.96%** | 6.3528 | 6.0529 | 11.03 ms | 11.87 ms |
| **32K** | 75.132 | 84.865 | **+12.96%** | 5.6247 | 6.4062 | 12.93 ms | 11.47 ms |
| **64K** | 37.150 | 56.716 | **+52.67%** | 3.4699 | 6.3555 | 20.60 ms | 11.23 ms |
| **128K** | 15.386 | 26.800 | **+74.18%** | 1.7762 | 6.3831 | 39.53 ms | 11.77 ms |

失败请求：**8/8 cell 全 0**。  
TTFT / prefill 两列基本重合（±2%）→ 收益**全部**来自 decode 阶段的 acceptance 恢复。

**Break-even：落在 16K 与 32K 之间。** 16K 是唯一负收益点；32K 起转正且快速放大。  
**128K regression guard（不差于 −5%）：PASS。**

### 坍塌机制（per-position）

| input | OFF pos1 | OFF pos8 | OFF acc |
|---|---|---|---|
| 16K | 0.9028 | 0.4259 | 6.3528 |
| 64K | 0.8159 | 0.0202 | 3.4699 |
| 128K | **0.4607** | **0.0006** | **1.7762** |

W1024 在所有长度上 pos1 稳在 0.90–0.93、pos8 稳在 0.42–0.48。  
⇒ **收益 = OFF 的坍塌深度**；128K 不是「优化得好」，而是**修好了一条本来要失效的路径**。

---

## 四、Phase 1 归因（**另一件事，别混**）

设计：**A/B/A/B**，两臂**都开 W1024**，唯一变量是 **commit**；16K + 128K，各 1 warmup + **3 formal repeats**。

| input | parent 池化 | perf 池化 | delta | ranges | classification |
|---|---|---|---|---|---|
| 16K | 79.624 | 83.604 | **+5.00%** | overlapping | `NO_MEASURABLE_DIFFERENCE` |
| 128K | 26.667 | 25.731 | **−3.51%** | overlapping | `NO_MEASURABLE_DIFFERENCE` |

```text
PERFORMANCE COMMIT ATTRIBUTION: NO_MEASURABLE_DIFFERENCE
```

- 两个方向的均值差都**小于**本机 run-to-run spread（perf 池化 CV 16K 0.069 / 128K 0.038）；
- **既不能**判定为 improvement，**也不能**判定为 regression；
- 24 formal runs 全部 `rc=0`，failed 全 0。
- 判据是 **observed range overlap + 2% 阈值**（**保守的工程判据，不是 formal significance test**）。

### 两者为什么不能混

| | Phase 1 | Phase 2 |
|---|---|---|
| 自变量 | **commit**（parent vs perf） | **window**（OFF vs W1024） |
| 期望效应量 | 个位数 % | 数十 ~ 数百 % |
| 结论 | `NO_MEASURABLE_DIFFERENCE` | `FEATURE_EFFECTIVE_AT_LONG_CONTEXT` |

⚠️ 不许把 Phase 2 的 +74.18% 记到 perf commit 头上；也不许把 Phase 1 的 −3.51% 说成「开窗有害」。

---

## 五、与历史 reference 的方向对比

| 指标 | 历史 MRV1 | 首轮 P7-X smoke | **本轮 full Phase 2** | 方向 |
|---|---|---|---|---|
| 16K throughput gain | +10.2% | −0.83% | **−6.96%** | ⚠️ 三轮不一致 |
| 128K throughput gain | +75.8% | +64.6% | **+74.18%** | ✅ 同向同量级 |
| 128K acceptance | 1.84 → 6.27 | 1.9227 → 6.0519 | 1.7762 → 6.3831 | ✅ 同向同量级 |

> ### **HISTORICAL REFERENCE ≠ PASS THRESHOLD**
> 上表是**跨轮、跨口径**（MRV1 vs MRV2；conc16 vs conc1）的方向锚点，**不是**本轮验收标准。

---

## 六、W1024 数据可得性（必须先说清）

上一版 **Interim 报告里 W1024 全部标为缺失值（`N/A`）** —— 那是**报告生成 bug**：  
lookup 用了目录名 `curve_1024`，而实际实例目录是 **`curve_w1024` / `w1024`**  
（`meta.json.stack == "curve_1024"` 与 block 目录名不一致）。

**这是报告 bug，不是测试没跑。** 本轮已从  
`02_length_curve/{off,w1024}/metrics.json` 原始 artifacts **重新 reconcile**，  
8/8 cell 全部有数，**未继承任何 stale 缺失值**。

---

## 七、结论

| 问题 | 答案 |
|---|---|
| **Performance commit** | `NO_MEASURABLE_DIFFERENCE`（16K +5.00% / 128K −3.51%，均落在噪声内） |
| **Sliding Window 特征** | **长上下文收益明确**：32K +12.96% / 64K +52.67% / 128K +74.18% |
| **16K** | 唯一负收益点（−6.96%），与噪声同量级，读作「无收益 / 略负」 |
| **Break-even** | 落在 **16K–32K 之间**（未精确定位，建议补测 24K） |
| **commit 是否保留** | **证据不足以判定** —— 既未证明有收益，也未证明有害；建议**暂留 + 补测**（repeats 3 → 6–8） |

```text
FEATURE CONCLUSION: STRONG LONG-CONTEXT BENEFIT
COMMIT ATTRIBUTION:  NO_MEASURABLE_DIFFERENCE
```

### 明确不写的

- ❌ **不是 PERFORMANCE PASS**
- ❌ **不是 RELEASE PASS**
- ❌ 16K 的 −6.96% **不得**写成 REGRESSION
- ❌ 128K 的 +74.18% **不得**写成 perf commit 的收益

---

## 附：报告索引

| 报告 | 路径 |
|---|---|
| Phase 1 Skill-style | `reports/skill_style/P7X_Phase1_Performance_Commit_Attribution_SkillStyle.md` |
| Phase 2 Skill-style | `reports/skill_style/P7X_Phase2_SW_DSpark_Length_Matrix_SkillStyle.md` |
| 工程复盘（开发者向） | `reports/skill_style/P7X_Phase1_Phase2_Engineering_Review_CN.md` |
| 本汇报 | `reports/skill_style/P7X_Phase1_Phase2_Teacher_Summary_CN.md` |
| 图表 | `reports/skill_style/plots/` |
| reconciled 数据 | `reports/skill_style/work/phase2_reconciled.json` · `phase2_skill_style_table.csv` |
