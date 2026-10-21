**# SW-DSpark 性能汇总 — P7-X Phase 2 全长度矩阵**

**### （GLM-5.2 + DSpark · K=8 · TP16/DP1 · MRV2 · Async ON · conc=1 · 非图模式）**


> 组织方式沿用团队 `sw-dspark-perf-matrix` Skill 的「性能汇总」模板：

> 头部元信息 → 平均接收长度矩阵 → Output 吞吐矩阵 → TPOT 矩阵 → 关键结论 → 数据来源。

> 本报告为 ****REPORT-ONLY RECONSTRUCTION****：不跑 NPU、不起服务、不跑 aisbench，

> 全部数字重新取自 `02_length_curve/{off,w1024}/metrics.json` 原始 artifacts。


****日期****：2026-10-16 · ****机器****：`node-39-101` · ****Campaign root****：`/mnt/wenqing/mrv2_p7x_full_nongraph_validation/`

****源码树****：perf candidate `1b7215c37d1e3c9d1edac1fc20bcad26917ca251`（branch `perf/p7x-draft-window-hotpath`，tree `9a6c38c0e92853b462cd1f05aa5f70244f82a72f`），parent `c1c2129a…`，pinned vLLM `84030bbe…`

****测试命令****：`aisbench_auto_tools_prefix-master` → `ais_bench`，`--output_len 2000 --data_num 4 --concurrency 1 --request_rate 0`（`dataset_type=normal`，`temperature 0`，`ignore_eos`）

****矩阵规模****：窗长 `{off, 1024}` × 输入 `{16K, 32K, 64K, 128K}` = ****8 cell****，全部完成 ✅ 失败请求 0

****每 cell****：1 excluded warmup + ****3 formal repeats****（balanced order），共 24 formal runs


**---**


**## 0. 部署配置（Configuration）**


| 项 | 值 |

|---|---|

| 模型 | GLM-5.2-W4A8 + DSpark 草稿（`GLM5.2_dspark`，与历史 0815 逐字节一致） |

| 投机方法 / K | `dspark` / ****8**** |

| TP / DP / EP | ****16 / 1 / ON**** |

| `max_num_seqs` | ****16**** |

| `max_model_len` | ****132096**** |

| Model runner | ****MRV2****（`VLLM_USE_V2_MODEL_RUNNER=1`） |

| Async scheduling | ****ON**** |

| Cudagraph | `FULL_DECODE_ONLY`，capture sizes `[9, 18, 27, 36]` |

| 图模式 | ****非图模式（non-graph）轨迹**** |

| 并发 / 数据量 | `conc=1` / `data_num=4` |


> ⚠️ ****口径提示****：本轮 `conc=1`、每 cell 仅 4 请求；团队原矩阵是 `conc=16`、`data_num=64`。

> 两个口径****不可直接互换比较****，跨轮对比时以「同口径同轮」为准（见 §7 历史对比）。


**---**


**## 1. MRV2 16/16 worker proof**


两个服务实例****各自独立取证****，未继承。


| service instance | window | verdict | ranks |

|---|---|---|---|

| `curve_off` | OFF | `MRV2_VERIFIED` | 16/16 |

| `curve_w1024` | W1024 | `MRV2_VERIFIED` | 16/16 |


证据：`02_length_curve/{off,w1024}/worker_identity.json`（`ranks_verified_ok: 16`，

`expected_model_runner_class = vllm_ascend.worker.v2.model_runner.NPUModelRunner`，

`expected_speculator_class = …v2.spec_decode.dspark.speculator.AscendDSparkSpeculator`）。


**---**


**## 2. 平均接收长度矩阵（Mean acceptance length，主指标）**


| 窗长\输入 | 16K | 32K | 64K | 128K |

|---|---|---|---|---|

| ****OFF**** | ****6.3528**** | 5.6247 | 3.4699 | 1.7762 |

| ****W1024**** | 6.0529 | ****6.4062**** | ****6.3555**** | ****6.3831**** |

| ****gain**** | −4.72% | +13.89% | +83.16% | ****+259.37%**** |


**### 2.1 Per-position acceptance rate（3 repeats 均值）**


| 配置 · 输入 | Mean acc len | pos1 | pos2 | pos3 | pos4 | pos5 | pos6 | pos7 | pos8 |

|---|---|---|---|---|---|---|---|---|---|

| OFF · 16K | 6.3528 | 0.9028 | 0.8274 | 0.7619 | 0.6997 | 0.6476 | 0.5832 | 0.5040 | 0.4259 |

| W1024 · 16K | 6.0529 | 0.8972 | 0.7989 | 0.7111 | 0.6366 | 0.5846 | 0.5318 | 0.4764 | 0.4163 |

| OFF · 32K | 5.6247 | 0.8834 | 0.7782 | 0.6915 | 0.6131 | 0.5398 | 0.4672 | 0.3830 | 0.2680 |

| W1024 · 32K | 6.4062 | 0.9230 | 0.8412 | 0.7632 | 0.6942 | 0.6378 | 0.5665 | 0.5159 | 0.4640 |

| OFF · 64K | 3.4699 | 0.8159 | 0.5799 | 0.4172 | 0.2863 | 0.1967 | 0.0999 | 0.0544 | 0.0202 |

| W1024 · 64K | 6.3555 | 0.9042 | 0.8182 | 0.7406 | 0.6779 | 0.6230 | 0.5802 | 0.5325 | 0.4780 |

| OFF · 128K | 1.7762 | 0.4607 | 0.1891 | 0.0795 | 0.0323 | 0.0087 | 0.0030 | 0.0020 | 0.0006 |

| W1024 · 128K | 6.3831 | 0.9273 | 0.8505 | 0.7607 | 0.6965 | 0.6317 | 0.5663 | 0.5107 | 0.4397 |


> ****坍塌机制一目了然****：OFF 在 64K/128K 下 ****pos1 就已经掉到 0.82 / 0.46****，后续位置迅速归零

> （128K 的 pos5–pos8 ≈ 0.009/0.003/0.002/0.0006）→ 平均接收长度塌到 1.78。

> W1024 在每个长度上都维持 ****pos1 ≈ 0.90–0.93、pos8 ≈ 0.42–0.48**** 的平坦形状。


**---**


**## 3. Output 吞吐矩阵（tok/s）**


| 窗长\输入 | 16K | 32K | 64K | 128K |

|---|---|---|---|---|

| ****OFF**** | ****87.120**** | 75.132 | 37.150 | 15.386 |

| ****W1024**** | 81.060 | ****84.865**** | ****56.716**** | ****26.800**** |

| ****gain**** | ****−6.96%**** | ****+12.96%**** | ****+52.67%**** | ****+74.18%**** |

| OFF CV | 0.0560 | 0.1209 | 0.0193 | 0.0314 |

| W1024 CV | 0.0352 | 0.1246 | 0.0273 | 0.0075 |


**---**


**## 4. TPOT 矩阵（ms，avg）**


| 窗长\输入 | 16K | 32K | 64K | 128K |

|---|---|---|---|---|

| ****OFF**** | 11.03 | 12.93 | 20.60 | 39.53 |

| ****W1024**** | 11.87 | 11.47 | 11.23 | 11.77 |

| ****变化**** | +7.6%（略差） | −11.3%（更好） | −45.5%（更好） | ****−70.2%（大幅更好）**** |


> ⚠️ ****口径提醒****：TPOT 依赖 acceptance length（每步吐的 token 越少，TPOT 越差）。

> 因此本表的 TPOT 变化****不是****独立的 kernel 性能指标，本质是 acceptance 坍塌的镜像。


**---**


**## 5. TTFT / E2E / Prefill 吞吐**


**### 5.1 TTFT average（ms）**


| 窗长\输入 | 16K | 32K | 64K | 128K |

|---|---|---|---|---|

| ****OFF**** | 1001.1 | 1083.2 | 12626.1 | 51024.2 |

| ****W1024**** | 1018.9 | 1080.1 | 12847.3 | 51144.9 |

| ****变化**** | +1.8% | −0.3% | +1.8% | +0.2% |


> TTFT 是****纯 prefill**** 指标，与滑窗无关 → 两列基本重合（±2%），符合预期。


**### 5.2 E2E average（ms）**


| 窗长\输入 | 16K | 32K | 64K | 128K |

|---|---|---|---|---|

| ****OFF**** | 23027.4 | 26998.7 | 53855.7 | 130112.9 |

| ****W1024**** | 24702.5 | 23974.2 | 35290.0 | 74630.6 |

| ****变化**** | +7.3%（略差） | −11.2% | −34.5% | ****−42.6%**** |


**### 5.3 Prefill token throughput（tok/s）**


| 窗长\输入 | 16K | 32K | 64K | 128K |

|---|---|---|---|---|

| ****OFF**** | 25445.1 | 47350.8 | 5186.5 | 2508.9 |

| ****W1024**** | 24918.1 | 46361.2 | 5096.3 | 2503.0 |


> Prefill 吞吐两列基本重合；16K/32K 的 CV 极高（OFF 16K CV=0.49、32K CV=0.50），

> 因该指标受****首个请求冷启动****支配，单 cell 只有 4 请求 → 不是稳定指标，****仅作参考****。


**---**


**## 6. Failed requests**


| 窗长\输入 | 16K | 32K | 64K | 128K |

|---|---|---|---|---|

| ****OFF**** | 0 | 0 | 0 | 0 |

| ****W1024**** | 0 | 0 | 0 | 0 |


8/8 cell 全部 `aisbench_rc = 0`，****零失败请求****。


**---**


**## 7. 增益汇总与历史对比**


**### 7.1 本轮增益表**


| input_len | 指标 | OFF | W1024 | 变化 |

|---|---|---|---|---|

| 16K | Mean accept len | 6.3528 | 6.0529 | −4.72% |

| 16K | Output tok/s | 87.120 | 81.060 | ****−6.96%**** |

| 16K | TPOT | 11.03 ms | 11.87 ms | +7.6% |

| 32K | Mean accept len | 5.6247 | 6.4062 | +13.89% |

| 32K | Output tok/s | 75.132 | 84.865 | ****+12.96%**** |

| 32K | TPOT | 12.93 ms | 11.47 ms | −11.3% |

| 64K | Mean accept len | 3.4699 | 6.3555 | +83.16% |

| 64K | Output tok/s | 37.150 | 56.716 | ****+52.67%**** |

| 64K | TPOT | 20.60 ms | 11.23 ms | −45.5% |

| 128K | Mean accept len | 1.7762 | 6.3831 | +259.37% |

| 128K | Output tok/s | 15.386 | 26.800 | ****+74.18%**** |

| 128K | TPOT | 39.53 ms | 11.77 ms | −70.2% |


**### 7.2 历史 reference（**仅供方向对照**）**


| 指标 | 历史 MRV1 reference | 首轮 P7-X smoke | 本轮 full Phase 2 | 方向 |

|---|---|---|---|---|

| 16K throughput gain | ****+10.2%**** | ****−0.83%**** | ****−6.96%**** | ⚠️ 三轮都不一致 |

| 128K throughput gain | ****+75.8%**** | ****+64.6%**** | ****+74.18%**** | ✅ 同向同量级 |

| 16K acceptance | 5.64 → 6.27 | 6.1657 → 6.34 | 6.3528 → 6.0529 | ⚠️ 本轮反向 |

| 128K acceptance | 1.84 → 6.27 | 1.9227 → 6.0519 | 1.7762 → 6.3831 | ✅ 同向同量级 |

| 128K 坍塌（OFF） | 1.84 | 1.9227 | 1.7762 | ✅ 复现 |


> **### ⚠️ **HISTORICAL REFERENCE ≠ PASS THRESHOLD****

> 上表的历史数字是****跨轮、跨口径****（MRV1 vs MRV2；conc16 vs conc1）的参考锚点，

> ****不是****本轮验收标准，****不得****用来判定本轮 PASS/FAIL。


**---**


**## 8. Break-even 分析**


| input | W1024 vs OFF 吞吐 | zone |

|---|---|---|

| 16K | ****−6.96%**** | `BELOW_BREAK_EVEN`（低于盈亏平衡） |

| 32K | ****+12.96%**** | `ABOVE_BREAK_EVEN` |

| 64K | ****+52.67%**** | `STRONG_GAIN` |

| 128K | ****+74.18%**** | `STRONG_GAIN` |


****结论****：


* ****break-even 落在 16K 与 32K 之间****（本轮未落在采样点上，只能夹逼）。

* 16K 是****唯一负收益点****（−6.96%），机制见 §2.1：16K 下 OFF 的 acceptance（6.3528）

  已经很高，滑窗没有「救」的空间，却要付裁剪/投影的固定开销 → 净负。

* 从 32K 起收益转正并****快速放大****：32K +13% → 64K +53% → 128K +74%，

  与 OFF 的 acceptance 坍塌速度（6.35 → 5.62 → 3.47 → 1.78）****完全对应****。


**### 8.1 128K regression guard**


****`PASS`**** — 判据是「不差于 −5%」，W1024 在 128K 为 ****+74.18%****，远超阈值。


**---**


**## 9. 图表**


| 图 | 文件 |

|---|---|

| Output throughput vs input | `plots/throughput_vs_input.png` |

| Mean acceptance length vs input | `plots/acceptance_vs_input.png` |

| TPOT average vs input | `plots/tpot_vs_input.png` |

| Throughput gain vs OFF（break-even） | `plots/throughput_gain_vs_input.png` |


每张图的每个点都可追溯到 `02_length_curve/{off,w1024}/metrics.json`；

生成脚本 `reports/skill_style/work/make_plots.py`，输入 `reports/skill_style/work/phase2_skill_style_table.csv`。


**---**


**## 10. 数据来源**


| 类别 | 路径 |

|---|---|

| OFF 原始 cell | `02_length_curve/off/r{1,2,3}_{16000,32000,64000,128000}/`（含 `meta.json`、`outputs_default_run/performances/vllm-api-stream-chat/gsm8k.{json,csv}`、`aisbench.log`、`rendered_api_config.py`、`server_slice.log`、`npu_{before,during,after}.txt`） |

| W1024 原始 cell | `02_length_curve/w1024/r{1,2,3}_{16000,32000,64000,128000}/`（同上） |

| 接收长度统计 | `02_length_curve/\<block>/skill_matrix/_flat_all/_flat_all_日志统计汇总.md`（`sw-dspark-perf-matrix/bin/log_process_new.py`） |

| 每 block 指标聚合 | `02_length_curve/{off,w1024}/metrics.json` |

| acceptance parser 全量输出 | `acceptance/phase2_acceptance_parser.log` |

| 全局聚合 | `reports/results.json`、`reports/results.csv`、`reports/cells.csv`、`reports/run_manifest.jsonl` |

| ****本报告 recon 产物**** | `reports/skill_style/work/phase2_reconciled.json`、`reports/skill_style/work/phase2_skill_style_table.csv` |


> ****W1024 数据可得性说明（重要）****：上一版 Interim 报告里 W1024 全部标为缺失值（`N/A`），

> 原因是报告生成时的目录 lookup 用了 `curve_1024`，而实际实例目录名是 ****`curve_w1024` / `w1024`****

> （`meta.json.stack == "curve_1024"`，但 block 目录是 `w1024`）。

> ****这是报告生成 bug，不是测试没跑。**** 本轮已从原始 artifacts 重新 reconcile，

> 8/8 cell 全部有数，****不再继承 stale 缺失值****（详见 §11）。


**---**


**## 11. 关键结论**


1. ****滑窗特征在长上下文上的收益明确且连续****：32K/64K/128K = ****+12.96% / +52.67% / +74.18%****，

   acceptance 从坍塌（1.78 @128K）恢复到 \~6.38。

2. ****16K 是唯一负收益点（−6.96%）****：OFF 基线本就高、无收益空间，滑窗只剩固定开销。

   break-even 位于 16K–32K 之间。

3. ****TTFT/prefill 不受影响****（±2%），收益****全部****来自 decode 阶段的 acceptance 恢复。

4. ****本轮数字与历史 MRV1 / 首轮 smoke 在 128K 上同向同量级****；16K 三轮方向不一致

   （+10.2% / −0.83% / −6.96%），****不能****用历史数字当判据（§7.2）。

5. 8/8 cell 零失败请求；MRV2 两实例 16/16 独立取证。


```

PHASE2_VERDICT: WINDOW_FEATURE_EFFECTIVE_AT_LONG_CONTEXT

16K −6.96% (BELOW_BREAK_EVEN) · 32K +12.96% · 64K +52.67% · 128K +74.18%

BREAK-EVEN BETWEEN 16K AND 32K

128K REGRESSION GUARD: PASS

NOT A RELEASE PASS

```


> 本报告只陈述 ****Sliding Window 特征（OFF vs W1024）**** 的效应，

> ****不****构成对 perf commit 的归因 —— 那是 Phase 1 的职责（`NO_MEASURABLE_DIFFERENCE`）。
