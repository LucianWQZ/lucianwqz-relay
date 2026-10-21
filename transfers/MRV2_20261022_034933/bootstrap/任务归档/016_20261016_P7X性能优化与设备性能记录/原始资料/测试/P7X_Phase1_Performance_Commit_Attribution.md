**# P7-X Phase 1 — Performance Commit Attribution**


> ****报告风格沿用团队 `sw-dspark-perf-matrix` Skill 的「性能汇总」组织方式****

> （源码树含 SHA → MRV2 证据 → 部署 → 测试口径 → 矩阵表 → 关键结论 → 数据来源）。

> 本报告由 ****REPORT-ONLY RECONSTRUCTION**** 生成：不跑 NPU、不起服务、不跑 aisbench，

> 全部数字来自已落盘的 Phase 1 原始 artifacts。


****性质****：`ATTRIBUTION`，不是 PERFORMANCE PASS，不是 RELEASE PASS。

****日期****：2026-10-16 · ****机器****：`node-39-101` · ****Campaign root****：`/mnt/wenqing/mrv2_p7x_full_nongraph_validation/`

****Phase 状态****：Phase 1 `COMPLETE`（24 formal runs；1 excluded warmup + 3 formal repeats per cell）

****服务状态****：已停止，HBM 已释放（SAFE_PAUSE）


**---**


**## 1. Exact Source**


| item | value |

|---|---|

| perf candidate (vllm-ascend) | `1b7215c37d1e3c9d1edac1fc20bcad26917ca251` |

| perf tree | `9a6c38c0e92853b462cd1f05aa5f70244f82a72f` |

| perf branch | `perf/p7x-draft-window-hotpath` |

| parent baseline (vllm-ascend) | `c1c2129aa49ee1de381130729de73124a6ec893a` |

| parent tree | `384af8a0466f6aea2e73d6217f9802415b5ccd40` |

| pinned vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |

| pinned vLLM tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |

| parent runtime overlay | `/home/wenqing/mrv2_p7x_final/runtime/p7x_overlay` |

| perf runtime overlay | `/home/wenqing/mrv2_p7x_perf_final/runtime/p7x_perf_overlay` |

| formal measurement tool | `aisbench_auto_tools_prefix-master` → `ais_bench` |

| acceptance parser | `sw-dspark-perf-matrix/bin/log_process_new.py` |


****可比性硬证据****（`manifests/parent_perf_runtime_comparability.json` → `SAME_DONOR_BYTE_IDENTICAL`）：


| check | value |

|---|---|

| same donor root | `true`（`/home/wenqing/vllm-ascend-main/vllm_ascend`） |

| native `.so` 逐字节一致（parent vs perf） | `true`（`vllm_ascend_C…so` sha `e2e8b132…7114`；`libvllm_ascend_kernels.so` sha `4052173e…6580`） |

| `cann_ops_custom` 聚合 sha | 两侧同为 `c7848294…9a7c`（1221 files） |

| python 文件差异 | ****仅**** perf commit 的 3 个生产文件（`python_files_differ_only_in_perf_commit: true`） |


> 即：两棵树的****二进制与算子完全一致****，Python 侧只差 perf commit 本身。这是 A/B 归因成立的前提。


**---**


**## 2. MRV2 16/16 worker proof**


四个 block ****各自独立取证****，未继承。worker 内观测探针取自

`raw/startup/\<instance>/identity.json`（每 rank 明细 `.rankN.json`）。


| block | verdict | ranks | model_runner_class | speculator_class |

|---|---|---|---|---|

| A1_parent | `MRV2_VERIFIED` | 16/16 | `vllm_ascend.worker.v2.model_runner.NPUModelRunner` | `vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator` |

| B1_perf | `MRV2_VERIFIED` | 16/16 | 同上 | 同上 |

| A2_parent | `MRV2_VERIFIED` | 16/16 | 同上 | 同上 |

| B2_perf | `MRV2_VERIFIED` | 16/16 | 同上 | 同上 |


```

MRV2: VERIFIED (4/4 blocks, 16/16 ranks each)

```


**---**


**## 3. Model / topology**


| 项 | 值 |

|---|---|

| Target model | `/mnt/share/weights/GLM-5.2-w4a8`（95 shards） |

| Draft model | `/mnt/share/l00887471/graph_vllm/dspark_test/sw-aspark/GLM5.2_dspark` |

| Draft identity | 与师傅历史 `…/GLM-5.2-speculator.dspark.0815/GLM5.2_dspark` ****逐字节一致****（5 文件 sha 全同，`model.safetensors` = 9,627,409,394 B） → `VERIFIED_SAME` |

| Served model name | `glm-52`，port `8078` |

| TP / DP | ****16 / 1**** |

| Expert parallel | ON |

| K (`num_speculative_tokens`) | ****8**** |

| `max_num_seqs` | ****16**** |

| `max_model_len` | ****132096**** |

| gpu-memory-utilization | 0.92 |

| cudagraph | `FULL_DECODE_ONLY`, capture sizes `[9, 18, 27, 36]` |

| async scheduling | ****ON**** |

| `VLLM_USE_V2_MODEL_RUNNER` | `1`（MRV2 硬门槛） |

| CANN / NIC / IP | 9.1.0 · `enp48s3u1u1` · `80.5.17.101` |

| ****双边窗长**** | ****W1024（A/B 两臂均开窗，见 §4）**** |


**---**


**## 4. Test methodology**


****问题****：perf commit `1b7215c3` 相对 parent `c1c2129a` 是否有可测的 E2E 收益/退化？


| 项 | 值 |

|---|---|

| 设计 | ****A/B/A/B****（parent → perf → parent → perf），每臂一次独立起服 + 独立 MRV2 取证 |

| 输入长度 | 16K (`16000`) 与 128K (`128000`) |

| 窗口 | ****W1024（两臂都开窗）**** —— 隔离的是 **commit**，不是 **feature** |

| 每 cell 运行数 | 1 excluded warmup + ****3 formal repeats**** |

| aisbench 口径 | `--output_len 2000 --data_num 4 --concurrency 1 --request_rate 0`，`dataset_type=normal`，`temperature 0`，`ignore_eos` |

| 顺序控制 | balanced order（避免单调漂移） |

| 统计口径 | pooled mean / median / std / CV + observed range overlap（****非**** formal significance test，见 §9） |

| formal runs | 24 |


> ⚠️ ****口径提示****：Phase 1 每 cell 只有 ****4 个请求、并发 1****。样本量很小，

> run-to-run 噪声是主导项。这不是团队原矩阵的 `conc=16 / data_num=64` 口径，读数时需注意。


**---**


**## 5. A1 / B1 / A2 / B2 全指标表**


**### 16K · W1024**


| metric | A1 parent | B1 perf | A2 parent | B2 perf |

|---|---|---|---|---|

| output throughput (tok/s) | 81.400 | 87.843 | 77.848 | 79.365 |

| TPOT avg (ms) | 12.07 | 11.20 | 12.60 | 12.37 |

| TTFT avg (ms) | 462.8 | 469.8 | 467.5 | 485.8 |

| E2E avg (ms) | 24585.1 | 22856.2 | 25709.2 | 25205.6 |

| mean acceptance length | 5.8927 | 6.3796 | 5.8809 | 5.9108 |

| prefill token throughput (tok/s) | 34612.4 | 34117.7 | 34282.0 | 33004.5 |

| failed requests | 0 | 0 | 0 | 0 |


**### 128K · W1024**


| metric | A1 parent | B1 perf | A2 parent | B2 perf |

|---|---|---|---|---|

| output throughput (tok/s) | 26.652 | 25.345 | 26.681 | 26.117 |

| TPOT avg (ms) | 11.70 | 13.70 | 11.70 | 12.43 |

| TTFT avg (ms) | 51658.7 | 51662.7 | 51592.3 | 51793.5 |

| E2E avg (ms) | 75062.2 | 79040.4 | 74971.0 | 76642.3 |

| mean acceptance length | 6.0444 | 5.6864 | 6.0635 | 6.0749 |

| prefill token throughput (tok/s) | 2478.0 | 2477.9 | 2481.2 | 2471.6 |

| failed requests | 0 | 0 | 0 | 0 |


**### Per-position acceptance（各 block 均值，W1024）**


| block · input | Mean acc len | pos1 | pos2 | pos3 | pos4 | pos5 | pos6 | pos7 | pos8 |

|---|---|---|---|---|---|---|---|---|---|

| A1 · 16K | 5.8710 | 0.8894 | 0.7928 | 0.7032 | 0.6262 | 0.5569 | 0.4932 | 0.4371 | 0.3722 |

| B1 · 16K | 6.3657 | 0.9122 | 0.8313 | 0.7479 | 0.6814 | 0.6265 | 0.5678 | 0.5232 | 0.4761 |

| A2 · 16K | 5.8795 | 0.8860 | 0.7890 | 0.6918 | 0.6151 | 0.5621 | 0.4991 | 0.4476 | 0.3889 |

| B2 · 16K | 5.9108 | 0.8780 | 0.7833 | 0.6953 | 0.6228 | 0.5612 | 0.5085 | 0.4604 | 0.4013 |

| A1 · 128K | 6.0035 | 0.9094 | 0.8142 | 0.7084 | 0.6251 | 0.5625 | 0.5058 | 0.4643 | 0.4135 |

| B1 · 128K | 5.6590 | 0.8889 | 0.7711 | 0.6696 | 0.5921 | 0.5197 | 0.4661 | 0.4158 | 0.3363 |

| A2 · 128K | 6.0370 | 0.9052 | 0.8137 | 0.7258 | 0.6322 | 0.5602 | 0.5064 | 0.4665 | 0.4271 |

| B2 · 128K | 6.0392 | 0.9068 | 0.8162 | 0.7317 | 0.6316 | 0.5674 | 0.5058 | 0.4600 | 0.4193 |


> 两臂的 acceptance 形状****同量级、无明显系统性差异****；128K 下 B1 的 5.659 是唯一明显偏低点，

> 正好对应 §9 里 perf 128K 均值被拖低的三个慢 repeat 之一。


**---**


**## 6. 16K — throughput / TPOT / TTFT / acceptance**


| 指标 | parent 均值 | perf 均值 | delta | 方向 |

|---|---|---|---|---|

| output throughput (tok/s) | ****79.6240**** | ****83.6041**** | ****+5.00%**** | perf 略高 |

| TPOT avg (ms) | 12.33 | 11.78 | −4.5% | perf 略好 |

| TTFT avg (ms) | 465.2 | 477.8 | +2.7% | 基本持平 |

| E2E avg (ms) | 25147.1 | 24030.9 | −4.4% | perf 略好 |

| mean acceptance length | 5.8868 | 6.1452 | +4.4% | perf 略高 |

| prefill token throughput (tok/s) | 34447.2 | 33561.1 | −2.6% | 基本持平 |


****分类：`NO_MEASURABLE_DIFFERENCE`****（见 §10）。


**---**


**## 7. 128K — throughput / TPOT / TTFT / acceptance**


| 指标 | parent 均值 | perf 均值 | delta | 方向 |

|---|---|---|---|---|

| output throughput (tok/s) | ****26.6666**** | ****25.7310**** | ****−3.51%**** | perf 略低 |

| TPOT avg (ms) | 11.70 | 13.07 | +11.7% | perf 略差 |

| TTFT avg (ms) | 51625.5 | 51728.1 | +0.2% | 持平 |

| E2E avg (ms) | 75016.6 | 77841.3 | +3.8% | perf 略差 |

| mean acceptance length | 6.0540 | 5.8807 | −2.9% | 基本持平 |

| prefill token throughput (tok/s) | 2479.6 | 2474.7 | −0.2% | 持平 |


****分类：`NO_MEASURABLE_DIFFERENCE`****（见 §10）。


**---**


**## 8. Parent pooled vs Perf pooled**


| input | series | N | mean | median | std | CV |

|---|---|---|---|---|---|---|

| 16K | parent (A1+A2) | 6 | 79.6240 | 79.3582 | 2.7172 | 0.03413 |

| 16K | perf (B1+B2) | 6 | 83.6041 | 80.7363 | 5.7670 | 0.06898 |

| 128K | parent (A1+A2) | 6 | 26.6666 | 26.5806 | 0.4067 | 0.01525 |

| 128K | perf (B1+B2) | 6 | 25.7310 | 25.9488 | 0.9800 | 0.03809 |


****Headline****


| input | parent mean | perf mean | delta | ranges | classification |

|---|---|---|---|---|---|

| 16K | 79.624 | 83.604 | ****+5.00%**** | overlapping | `NO_MEASURABLE_DIFFERENCE` |

| 128K | 26.667 | 25.731 | ****−3.51%**** | overlapping | `NO_MEASURABLE_DIFFERENCE` |


**---**


**## 9. CV / range / noise**


| input | series | observed range (6 repeats) | block-to-block spread | pooled CV |

|---|---|---|---|---|

| 16K | parent | [74.951, 84.095] | 12.20% | 0.03413 |

| 16K | perf | [77.955, 93.331] | 19.72% | 0.06898 |

| 128K | parent | [26.067, 27.191] | 4.31% | 0.01525 |

| 128K | perf | [24.055, 26.788] | 11.36% | 0.03809 |


****逐 repeat 明细（output throughput, tok/s）****


| block | 16K r1 / r2 / r3 | 128K r1 / r2 / r3 |

|---|---|---|

| A1 parent | 80.981 / 84.095 / 79.126 | 26.699 / 26.067 / 27.191 |

| B1 perf | 80.516 / 93.331 / 89.682 | 25.405 / 26.575 / 24.055 |

| A2 parent | 79.000 / 74.951 / 79.591 | 26.413 / 26.462 / 27.167 |

| B2 perf | 79.184 / 77.955 / 80.957 | 26.788 / 25.069 / 26.492 |


****读法****


* ****16K****：perf 均值高 5.0%，但由两个快 repeat（89.7、93.3）拉动；其余落在 parent 同一带内。

  parent 最大值（84.1）仍高于 perf 最小值（78.0）→ ****两序列不可分离****。

* ****128K****：perf 均值低 3.5%，由三个慢 repeat（24.1、25.1、25.4）拖低，另三个（26.5、26.6、26.8）

  与 parent 最差值（26.1）持平或更好 → ****同样不可分离****。


**### 关于「统计措辞」的声明**


本报告使用 ****observed range overlap**** 作为****保守的工程判据****：


> 只有当两序列的 observed range ****完全不相交****且 delta 超过 ****2%**** 时，才称 improvement / regression。


****这不是 formal statistical significance test。****

`NO_MEASURABLE_DIFFERENCE` ****不等于****「两者完全相等」——它表示

「在本次采样规模下，效应量被 run-to-run 噪声淹没，无法把差异从噪声中分离出来」。


**---**


**## 10. Classification**


| input | delta | ranges | classification |

|---|---|---|---|

| 16K | +5.00% | overlapping | ****`NO_MEASURABLE_DIFFERENCE`**** |

| 128K | −3.51% | overlapping | ****`NO_MEASURABLE_DIFFERENCE`**** |


```

PHASE1 OVERALL: NO_MEASURABLE_DIFFERENCE

```


* ****不得****读作优化获胜（PERFORMANCE IMPROVEMENT PASS）；

* ****不得****读作退化（REGRESSION）。

* draft-window hot-path 改动在代码里是****真实存在****的（perf commit 3 个生产文件），

  但在 3 repeats/block 的采样下，其效应落在本机 run-to-run 噪声之内。

* 要得到确定性归因，需要****更多 repeats per cell****；这是 resumed campaign 的决策，不是这 24 次运行能推断的。


**---**


**## 11. Raw artifacts**


| 类别 | 路径 |

|---|---|

| A1 parent | `/mnt/wenqing/mrv2_p7x_full_nongraph_validation/01_attribution/A1_parent/` |

| B1 perf | `…/01_attribution/B1_perf/` |

| A2 parent | `…/01_attribution/A2_parent/` |

| B2 perf | `…/01_attribution/B2_perf/` |

| 每个 run 内含 | `meta.json`、`outputs_default_run/performances/\<abbr>/gsm8k.{json,csv}`、`aisbench.log`、`rendered_api_config.py`、`server_slice.log`、`npu_{before,during,after}.txt` |

| 每 block 指标聚合 | `…/\<block>/metrics.json` |

| MRV2 取证 | `raw/startup/{A1_parent,B1_perf,A2_parent,B2_perf}/identity.json` |

| acceptance parser 输出 | `acceptance/phase1_acceptance_parser.log` |

| 全局聚合 | `reports/results.json`、`reports/results.csv`、`reports/cells.csv`、`reports/run_manifest.jsonl` |

| 本报告 recon 产物 | `reports/skill_style/work/` |


**---**


**## 12. Conclusion**


****Phase 1 只回答一个问题****：perf commit `1b7215c3` 相对 parent `c1c2129a`，在 ****W1024**** 口径下，

有没有****稳定可测的 E2E 收益或退化****？


****回答：没有。****


| input | perf vs parent | classification |

|---|---|---|

| 16K | +5.00%（均值方向为正） | `NO_MEASURABLE_DIFFERENCE` |

| 128K | −3.51%（均值方向为负） | `NO_MEASURABLE_DIFFERENCE` |


* 16K：****+5% mean direction，但两序列 observed range 重叠 → NO_MEASURABLE_DIFFERENCE****；

* 128K：****−3.51% mean direction，但两序列 observed range 重叠 → NO_MEASURABLE_DIFFERENCE****；

* 24 formal runs 全部 `rc=0`，failed requests 全 0；MRV2 4/4 blocks 16/16；

* 两个方向的均值差都****小于****本机 run-to-run spread，****不能****升级为 PASS，****也不能****判定为 REGRESSION。


****保留决策****：本 phase 的证据****不足以****判定 perf commit 是否值得保留（既没证明有收益，也没证明有害）。

判定需要更多 repeats —— 留给 resumed campaign。


```

PHASE1_VERDICT: NO_MEASURABLE_DIFFERENCE (16K +5.00% / 128K −3.51%, both overlapping)

NOT A PERFORMANCE PASS · NOT A REGRESSION · NOT A RELEASE PASS

```
