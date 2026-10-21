**# P7-X Graph Base G1–G5 — Ascend A3 设备级架构裁决（中文总报告）**


日期：2026-10-17

机器：`node-39-101`（Ascend A3）

候选：`LucianWQZ/vllm-ascend` @ `8cb4bed670f395c257c1233db944395159916009`

性质：****DEVICE-LEVEL ARCHITECTURE ADJUDICATION****，不是产品启用、不是性能验收、不是发布验收。


**---**


**# 1. 一页结论**


**## 1.1 本轮做了什么**


本轮把 Mac 本地完成的 Graph Base Characterization Candidate

（`8cb4bed6`）完整同步到 node-39-101，在真实 Ascend A3 + MRV2 上：


1. 建立独立源码树（vllm-ascend `8cb4bed6` / vLLM `84030bbe`）。

2. 审计源码差异：`1b7215c3..8cb4bed6` 只有 13 个 Python 文件，****无 C++ / CANN op / native .so / ABI / build 变化****。

3. 复用 Node101 本机 A3 native donor，建立全新的 `graph_char_overlay`。

4. 证明 Python 实际 import 的是本 campaign 的 overlay，不是旧共享树。

5. 跑通 3 个必跑 UT：19 + 37 + 46 全部 PASS。

6. 找到并验证合法 TP1 fixture：****Qwen3-8B + DSpark `dspark_qwen3_8b_block7`****。

7. 在 worker 内取证 MRV2：真实 runner 是

   `vllm_ascend.worker.v2.model_runner.NPUModelRunner`，真实 speculator 是

   `AscendDSparkSpeculator`。

8. 跑 A0 / A1 / B 三个对照：

   - A0 关窗基线正常；

   - A1 公共 Graph Window 门按预期冻结；

   - B 内部 characterization 路径成功 capture，但在第一次真正 replay 的 bind 阶段稳定失败。


**## 1.2 为什么必须 A3**


Graph Base 的全部争议点是“设备侧真实 operand / physical read / write-side invariant /

timeline lifetime”。CPU UT 只能证明 Python builder 看到了 Window table，不能证明

ACL Graph task / NPU attention 真正读取了它。A3 是目标架构（PCI `19e5:d803`），

CANN 9.1.0 / driver 26.0.rc1 与目标栈一致。


**## 1.3 为什么必须 MRV2**


本 feature 的源码路径只在 MRV2：

`vllm_ascend/worker/v2/spec_decode/`。Ascend 上 MRV2 是 opt-in，

`VLLM_USE_V2_MODEL_RUNNER` 不设时会静默回退 MRV1，导致整轮实验无效。

本轮不仅设置了 env，还在 worker 内读取了真实类对象，满足 hard gate。


**## 1.4 是否找到合法 TP1 fixture**


****是。****


```

Qwen3-8B (bf16, /mnt/share/wql/Qwen3-8B)

\+ DSpark (dspark_qwen3_8b_block7)

TP1 / DP1 / PP1 / PCP1 / DCP1

K=7, query width=7

W=1024, block=128

FULL_DECODE_ONLY

```


DFlash 备选 `z-lab/Qwen3-8B-DFlash-b16` 只有 config/code，没有权重，不能构成

runtime fixture。Qwen3.5-9B DFlash 目标模型是 hybrid linear attention，不满足

dense GQA direct-prefix，已拒绝。


**## 1.5 实际使用 DFlash 还是 DSpark**


****DSpark。****


**## 1.6 G1–G5 结果**


| Gate | 结果 |

|---|---|

| G1 Capture Operand Address | ****FAIL**** |

| G2 Persistent Refresh | ****OPEN**** |

| G3 Physical Read | ****OPEN**** |

| G4 Full Write / Target Isolation | ****OPEN**** |

| G5 Replay / Update / Completion Lifetime | ****OPEN**** |


**## 1.7 最终裁决**


```

BASE_GRAPH_DEVICE_ARCHITECTURE = FAIL

PUBLIC GRAPH SUPPORT           = STILL FROZEN

NEXT_ACTION                    = RETURN_TO_LOCAL_CODEX

```


**## 1.8 是否可以进入正式 Graph Feature implementation**


****不可以。****


不是“fixture 不可用”，也不是“设备环境不支持”，而是候选代码在真实设备路径上

稳定触发一个集成缺陷：


```

ValueError: Draft metadata mutable storage aliases Target metadata

```


必须先回本地修正该缺陷，再重新做 G1–G5。


**---**


**# 2. 任务边界**


本轮****没有****做：


- Graph product enablement；

- 公共 support matrix 修改；

- Feature Batch A 实现；

- 性能验收（吞吐 / TTFT / TPOT / E2E 不作为 PASS 依据）；

- 服务器源码热修；

- Gate 删除或绕过；

- Graph replay/update 协议修改。


**---**


**# 3. Exact Source / Runtime**


**## 3.1 vllm-ascend**


| 项目 | 值 |

|---|---|

| 仓库 | `https\://github.com/LucianWQZ/vllm-ascend.git` |

| 要求 branch | `spike/p7x-draft-window-graph-patch` |

| SHA | `8cb4bed670f395c257c1233db944395159916009` |

| Tree | `899899c23fdc87acaed49c889eecd1f7889ad9c4` |

| Commit subject | `spike(spec-decode): prepare graph window characterization` |

| Working tree | clean（`git status --porcelain` 为空） |


**## 3.2 vLLM**


| 项目 | 值 |

|---|---|

| 仓库 | `https\://github.com/LucianWQZ/vllm.git` |

| SHA | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |

| Tree | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` |

| Working tree | clean |


**## 3.3 源码差异（1b7215c3 → 8cb4bed6）**


13 个文件，2378 insertions / 50 deletions：


- `envs.py`

- `patch/__init__.py`

- `patch/worker/patch_v2/patch_dflash_speculator.py`

- `dflash/aclgraph.py`

- `dflash/capture.py`（新增）

- `dflash/speculator.py`

- `dspark/speculator.py`

- `draft_window.py`

- `draft_window_eager.py`

- `draft_window_graph.py`

- `draft_window_graph_characterization.py`（新增）

- 两个 UT 文件


****Native / C++ / CANN custom op / .so / ABI / build system 变化：无。****

因此复用 Node101 本机 A3 native donor 是合法的。


**## 3.4 Runtime overlay**


```

/home/wenqing/mrv2_graph_g1g5/runtime/graph_char_overlay

```


构建规则：


```

vllm_ascend = {8cb4bed6 源码 *.py} ∪ {A3 donor 非 *.py}

vllm        = symlink -> /home/wenqing/mrv2_graph_g1g5/src/vllm

```


- Python 文件：617

- 非 Python 文件：1269

- native donor：`/home/wenqing/vllm-ascend-main/vllm_ascend`

- 未修改旧 overlay `/home/wenqing/mrv2_p7x_perf_final/runtime/p7x_perf_overlay`


关键模块 SHA256：


| 模块 | SHA256 |

|---|---|

| `draft_window_graph_characterization.py` | `2ece48cf77179db14d4d4fee31fb255984579f9d13749b002002e7fe68e15843` |

| `dflash/capture.py` | `f26d579a2d7c3d44d63122bc82f5def0fc761a6002d58017780d51062d883ccb` |

| `draft_window_graph.py` | `d53e3c78a4c25ecba072fc1ab40337afa88d2945f40ddcd1cc4433dbbc8284c6` |

| `draft_window.py` | `dd8ebbfc65c1009a2bfe8ff1b2e2435b0d1333ffc1fa930be47b1c896fb8b5b2` |


**## 3.5 Import provenance**


实际 import 结果：


```

vllm_file         = .../graph_char_overlay/vllm/__init__.py

vllm_version      = 0.28.1rc1.dev676+g84030bbe3

vllm_ascend_file  = .../graph_char_overlay/vllm_ascend/__init__.py

```


`sys.path` 首位是 overlay；旧树

`/home/wenqing/vllm-main`、`/home/wenqing/vllm-ascend-main`、

`/home/wenqing/mrv2_p8_final`、`/home/wenqing/mrv2_p7x_final`、

`/home/wenqing/mrv2_p7x_perf_final` 被 sitecustomize 阻断。


**## 3.6 软硬件**


| 项目 | 值 |

|---|---|

| NPU | Ascend910 A3，16 logical dies |

| PCI | `19e5:d803`（A3） |

| CANN | 9.1.0 |

| Driver | 26.0.rc1 |

| Python | 3.11.10 |

| torch | 2.10.0+cpu |

| torch_npu | 2.10.0.post4 |


**## 3.7 模型 / Draft / 运行参数**


| 项目 | 值 |

|---|---|

| 主模型 | `/mnt/share/wql/Qwen3-8B`（bf16，5 shards，16 GiB） |

| Draft | `/mnt/share/dspark_qwen3_8b_block7` |

| method | `dspark` |

| K | 7 |

| query width | 7 |

| 主模型结构 | 36 layers，hidden 4096，32 Q heads / 8 KV heads，head_dim 128 |

| Draft 结构 | 5 layers，hidden 4096，32/8 heads，target layers `[1,9,17,25,33]` |

| Graph mode | `FULL_DECODE_ONLY` |

| W | 1024 |

| block size | 128 |

| capacity | 1151 tokens |

| capture sizes | `[7,14,28]` → `(1,7)`, `(2,14)`, `(4,28)` |

| topology | TP1 / DP1 / PP1 / PCP1 / DCP1 |

| async / prefix / SP / DSA-CP / FlashComm | 全部 OFF |


**---**


**# 4. 工具审计与使用**


**## 4.1 团队工具完整性**


- 原始工具 A：`/home/wenqing/tools/sw-dspark-perf-matrix`

- 原始工具 B：`/home/wenqing/tools/aisbench_auto_tools_prefix-master`

- 两个都不是 git repo。

- 实验前后各 2296 个文件，SHA256 完全一致。


```

ORIGINAL_TEAM_TOOLS_UNCHANGED

```


证据：`00_tools/team_tools_before.txt`、`00_tools/team_tools_after.txt`、

`00_tools/verdict.txt`。


**## 4.2 `/sw-dspark-perf-matrix` skill**


实际审计了 `SKILL.md`、`config/bench.env`、`bin/*`。


复用了通用部分：


- 空闲 NPU / 源码路径绑定自检思路；

- `wait_ready` 轮询；

- per-case log 目录；

- 进程安全经验（`setsid`，不要对 orchestrator 做进程组 kill）；

- 原始日志 + 机器可读汇总的结果收集纪律。


没有复用：


- `glm5_test.sh`：硬绑定 GLM-5.2 + DSpark TP16 / `--quantization ascend`，与 TP1 Qwen3-8B 不兼容；

- `run_matrix.sh`：性能矩阵编排，不是 G1–G5 characterization；

- `collect_results.sh` / `log_process_new.py`：接收长度/吞吐统计，不能作为 G1–G5 证据。


状态：


```

TEAM SKILL = PARTIAL

```


**## 4.3 aisbench**


实际审计了 `config.py`、`aisbench_test.py`、`process_dataset.py`、

`save_file.py`、`temp_api.py`。


它提供标准的固定输入/输出长度、data_num、concurrency、request_rate、

temperature、ignore_eos 请求契约。但：


- G1–G5 证据必须在 worker 内部读取 recorder/carrier/metadata/timeline；

- aisbench 是 HTTP-only，无法暴露这些对象；

- 即使跑出 throughput/TTFT/TPOT/E2E，也只能作为 diagnostic context，不能作为 PASS 依据。


因此：


```

AISBENCH = NOT_APPLICABLE (for G1-G5 evidence)

```


本轮 A0/A1/B 由 custom deterministic driver 驱动，明确标注：


```

CUSTOM_CORRECTNESS_DRIVER

NOT FORMAL PERFORMANCE

```


**## 4.4 Custom driver**


- `scripts/driver_case.py`：A0/A1/B，in-process engine（MP=0）；

- `scripts/smoke_identity.py`：首次 MRV2 identity smoke；

- `scripts/negative_matrix_cpu.py`：31 项 CPU policy/validation 检查；

- `scripts/probe_import_provenance.py`：import provenance；

- `scripts/assemble_evidence.py`：证据汇总。


完整源码、argv、seed、prompt、输出 token ids 都已保存。


**---**


**# 5. MRV2 Runtime Identity（单独章节）**


**## 5.1 结论**


```

MRV2 = VERIFIED

MRV1 = NOT PARTICIPATED

```


**## 5.2 实际类**


从 live in-process engine 对象图读取：


```

model_runner_class =

  vllm_ascend.worker.v2.model_runner.NPUModelRunner


speculator_class =

  vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator

```


**## 5.3 证据文件**


- `G0_mrv2_identity/identity.json`

- `negative/A0/result.json`（基线服务实例）

- `negative/B/result.json`（characterization 服务实例）

- `G0_mrv2_identity/smoke_identity.log`

- `00_preflight/import_provenance.txt`


**## 5.4 日志标志**


```

WARNING worker.py:497 npu model runner v2 is in developing

INFO speculator.py:144 Capturing model for DSpark speculator...

```


**## 5.5 服务实例与 Graph mode**


| 实例 | 用途 | Graph mode | 结果 |

|---|---|---|---|

| A0 | 关窗基线 | FULL_DECODE_ONLY | OK |

| A1 | 公共门对照 | FULL_DECODE_ONLY | GRAPH_FROZEN |

| B | 内部 characterization | FULL_DECODE_ONLY | bind 失败 |


**## 5.6 明确声明**


本轮没有任何 MRV1 代码路径参与。env 只是前置条件；真正的证据是

worker 内的 `NPUModelRunner` 类对象和 `AscendDSparkSpeculator` 类对象。


**---**


**# 6. Fixture 裁决**


**## 6.1 选中 fixture**


```

Qwen3-8B + dspark_qwen3_8b_block7

```


权重完整，可加载；policy 解析为 `ELIGIBLE_ON`；runtime 身份正确。


关键 hash：


| 文件 | SHA256 |

|---|---|

| main `config.json` | `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30` |

| main `model.safetensors.index.json` | `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc` |

| draft `config.json` | `e470e70a553616f0dce8f783f42cfd25b7bd7dfdcd57ead680a0623040725611` |

| draft `model.safetensors` | `5c922d1f96c8d18dbdf005c40ea99878d9133d70eaa3be4bd1077ee5f2afc1e5` |


**## 6.2 被拒候选**


| 候选 | 拒绝原因 |

|---|---|

| Qwen3-8B + `z-lab/Qwen3-8B-DFlash-b16` | draft 目录只有 config/code，无权重；runtime 报 `Cannot find any model weights` |

| Qwen3.5-9B + `Qwen3.5-9B-DFlash-full` | 目标为 hybrid linear/full attention，不是 dense GQA direct-prefix |

| Qwen3.8-27B + `Qwen3.8-27B-DFlash2` | `dflash2` 不在 base route 集合 `{dflash,dspark}` |

| GLM-5.2 TP16 + DSpark | TP16，不满足 TP1 |


**---**


**# 7. 启动契约与对照**


**## 7.1 公共启动契约**


```

VLLM_USE_V2_MODEL_RUNNER=1

VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1   (B only)

W=1024

Graph=FULL_DECODE_ONLY

Async=OFF

Prefix=OFF

TP=1 DP=1 PP=1 PCP=1 DCP=1

SP=OFF, DSA-CP=OFF, FlashComm=OFF

single dense FIA group

```


A0/A1 的 internal flag 分别为 0。


**## 7.2 对照结果**


| 对照 | Window | Internal flag | 结果 |

|---|---|---|---|

| A0 | OFF | 0 | OK：MRV2 graph 基线，输出 16 个确定性 token，无 characterization/provider 状态 |

| A1 | 1024 | 0 | EXPECTED_REJECT：`GRAPH_FROZEN`，公共 Graph Window 门仍关闭 |

| B | 1024 | 1 | CANDIDATE_RUNTIME_FAILURE：capture 成功，首次 bind 失败 |


A1 报错：


```

MRV2 Draft Window P7-X route rejected before materialization:

status=GRAPH_FROZEN; Graph mode FULL_DECODE_ONLY belongs to the frozen Graph Track

```


这证明公共 Graph Window 支持矩阵没有因为内部 flag 而被放开。


**---**


**# 8. G1 — Capture Operand Address**


**## 8.1 结论**


```

G1 = FAIL

```


**## 8.2 CaptureIdentity backing 地址**


B 运行启动时，characterization 为 3 个真实 capture bucket 注册了持久 backing：


| Bucket | persistent table address | length address | exact/upper |

|---|---:|---:|---:|

| (1,7) | 20623361168384 | 20623361169408 | 1151 |

| (2,14) | 20623361166848 | 20623361167872 | 1151 |

| (4,28) | 20623361164800 | 20623361166336 | 1151 |


6 个 CAPTURE 事件（每个 bucket warmup + capture）记录的 slot mapping 地址为

`20623361145856`，query layout 地址为 `20623359268352`。


1 个 MATERIALIZED 事件：


| 字段 | 值 |

|---|---|

| generation_id | 0 |

| mapping_epoch | 0 |

| runtime workspace table address | 20623361162752 |

| table row | `[1, 0, 0, ...]` |

| exact length | 12 |

| upper length | 12 |


**## 8.3 真实 ACL/NPU task operand 地址**


****没有取得。****


原因：第一次真正 replay 的 bind 在

`validate_draft_metadata_isolation` 处抛异常，没有 BOUND / REPLAY /

CONSUMER 事件，也就没有进入 ACL Graph task replay。


因此：


- Window table backing 地址：有（recorder 事实）；

- Window read length：有（recorder 事实，capture 时 1151，runtime materialize 时 12）；

- Full slot mapping / Target canonical 地址：capture 快照有，但未做 device 侧等值证明；

- 真实 NPU task operand 地址：****未观测****；

- exact address equality：****不成立****。


**## 8.4 为什么是 FAIL 而不是 OPEN**


这不是“观测手段不够导致的 OPEN”，而是候选代码在合法 fixture 上确定性地抛异常。

CAPTURE 阶段本身工作；失败发生在 runtime bind。按规则 22，G1 不 PASS，

不能继续 G2–G5。


**## 8.5 证据**


- `G1_capture/capture_events.json`

- `G1_capture/bind_failure.json`

- `negative/B/result.json`

- `negative/B/driver.log`


**---**


**# 9. G2 — Persistent Refresh**


```

G2 = OPEN (BLOCKED_BY_G1)

```


没有执行 A / B / A'。因此以下全部未知：


| 项目 | A | B | A' |

|---|---|---|---|

| generation | 未执行 | 未执行 | 未执行 |

| mapping_epoch | 未执行 | 未执行 | 未执行 |

| persistent address | 未验证 | 未验证 | 未验证 |

| content hash | 未验证 | 未验证 | 未验证 |

| read length | 未验证 | 未验证 | 未验证 |

| replay generation | 未观测 | 未观测 | 未观测 |

| completion | 未观测 | 未观测 | 未观测 |


不能声称：


- stable address；

- current content；

- no one-generation lag。


**---**


**# 10. G3 — Physical Read Oracle**


```

G3 = OPEN (NOT_RUN)

```


两个原因：


1. G1 未 PASS，规则 24 不允许继续。

2. 候选本身没有 device physical read-set observer。仓库搜索未发现

   `physical read` / `read-set` / `device read` / NPU trace 相关 instrumentation。

   现有 characterization 只有 CPU oracle（table values / lengths）。


代表 case（short / boundary / non-boundary / long）均未执行，因此没有：


- S / E / V；

- expected block ids vs materialized table vs actual operator read-set；

- source shortage negative。


即使输出正确，也不能据此声称 physical reads 正确。


**---**


**# 11. G4 — Full Write / Target Isolation**


```

G4 = OPEN (NOT_RUN)

```


OFF / ON 对照没有完成：


| 项目 | OFF (A0) | ON (B) | 结论 |

|---|---|---|---|

| Full table | 基线运行 | bind 失败 | 未比较 |

| slot mapping ptr + values | 未采集完整 | capture 快照 `-1` | 未比较 |

| positions | 未采集完整 | capture 快照 `0` | 未比较 |

| query layout | 未采集完整 | capture 快照 `[0,7,...]` | 未比较 |

| KV physical writes | 未观测 | 未观测 | 未比较 |

| Target metadata | 未比较 | 未比较 | 未比较 |

| Target lengths | 未比较 | 未比较 | 未比较 |

| Target logits/output | A0 有输出 | B 无输出 | 未比较 |


不能写 `UNCHANGED` 或 `DIFFERENT`。任何 write-side 结论都没有证据。


**---**


**# 12. G5 — Timeline / Lifetime**


```

G5 = OPEN (NOT_RUN)

```


实际 timeline 只到：


```

materialize N  ->  (bind 失败)

```


没有：


- bind N；

- metadata N（consumed）；

- replay submit N；

- consumer start/end N；

- update_full_graph_params N；

- backend task update；

- completion N；

- retire/reuse N。


源码本身已经明确：


```python

def assert_update_effective_for(self, generation_id: int) -> None:

    del generation_id

    raise RuntimeError("effective graph update generation requires NPU timeline evidence")

```


因此：


```

EFFECTIVE_GENERATION_MAPPING = UNKNOWN

DEVICE_COMPLETION_OWNER      = UNKNOWN

EARLIEST_SAFE_CARRIER_REUSE  = UNKNOWN

```


UPDATE(N) 影响谁、completion owner 是谁、最早何时可以复用 carrier，均无法回答。

本轮没有采集 `msprof` / NPU trace。


**---**


**# 13. Negative Matrix**


**## 13.1 设备对照**


| Case | 期望 | 实际 |

|---|---|---|

| A0 CONFIG_OFF | 零 characterization 状态、基线正常 | OK |

| A1 flag OFF | 公共 Graph 门关闭 | `GRAPH_FROZEN` |

| B flag ON | 内部路径可进入 | capture OK，bind FAIL |

| B_DFLASH | 备选 fixture 可用 | 权重缺失，不可用 |


**## 13.2 CPU matrix（31/31 MATCH）**


| Case | 结果 |

|---|---|

| flag unset / `1` | OK |

| flag `true` | `ValueError`（严格 0/1） |

| CONFIG_OFF | `CONFIG_OFF` |

| MTP | `FORCED_OFF` reason `mtp` |

| DeepSeek-V4 DSpark | `FORCED_OFF` reason `deepseek_v4_cotrained_dspark` |

| plain Eagle | `NotImplementedError` |

| unknown method | `NotImplementedError` |

| DSpark/Qwen3、DFlash/Qwen3 | `ELIGIBLE_ON` |

| graph NONE / PIECEWISE | reject |

| async ON | reject |

| TP/DP/PP/PCP/DCP > 1 | reject |

| SP / DSA-CP / FlashComm / prefix | reject |

| COMPATIBILITY backend | reject |

| W=0 / W < future offset | `ValueError` |

| W == future offset | OK |

| dynamic K | reject |


**## 13.3 UT / source 覆盖**


- Draft eager → no graph provider：UT PASS；

- flag OFF → no provider：UT PASS；

- policy OFF → zero state：UT PASS；

- stale mapping epoch：UT PASS（expected reject）；

- wrong capture bucket / descriptor：UT PASS（expected reject）；

- multi-group / non-direct-prefix：source `require_single_group_direct_prefix`，

  未单独设备执行；

- wrong MRV2 identity：driver hard gate → INVALID_RUN。


**---**


**# 14. 根因分析**


**## 14.1 精确失败点**


```

ValueError: Draft metadata mutable storage aliases Target metadata


draft_window_graph_characterization.py:529

  prepare_parallel_draft_window_graph_characterization

    -> session.provider.bind_read_carrier(...)


draft_window_graph.py:818

  bind_read_carrier

    -> validate_draft_metadata_isolation(metadata, target_metadata=target_metadata)


draft_window.py:2585

  validate_draft_metadata_isolation

    -> raise ValueError(f"{subject} mutable storage aliases Target metadata")

```


**## 14.2 候选内部的两个矛盾要求**


`_build_private_graph_metadata` 在 `_isolate_draft_metadata_from_target` 之后，

显式把 canonical full write/query carrier 恢复到 Draft metadata：


```python

layer_metadata.slot_mapping = write_side.slot_mapping

layer_metadata.positions = write_side.positions

layer_metadata.query_start_loc = write_side.query_start_loc

layer_metadata.actual_seq_lengths_q = list(write_side.actual_seq_lengths_q)

layer_metadata.attn_state = write_side.attn_state

layer_metadata.num_actual_tokens = write_side.num_actual_tokens

layer_metadata.causal = write_side.causal

```


其中：


```python

slot_mapping    = owner.block_tables.slot_mappings[gid, :token_count]

positions       = owner.input_buffers.positions[:token_count]

query_start_loc = owner.input_buffers.query_start_loc[:request_count + 1]

```


紧接着 `bind_read_carrier` 调用 `validate_draft_metadata_isolation`，要求

Draft metadata 不能与 Target metadata 共享任何可变对象/storage。


**## 14.3 真实路径为什么必然共享**


真实 vLLM V1 路径：


- `vllm/v1/worker/gpu/attn_utils.py:355 build_slot_mappings_by_layer`

  把同一个 `slot_mapping` tensor 对象直接放进每一层的 dict；

- Target `positions` / `query_start_loc` 来自同一个 `InputBuffers`；

- Draft 的 write-side reference 又刻意引用同一批 canonical 对象。


所以：


```

Target metadata 的 slot_mapping/positions/query_start_loc

\==

Draft write-side reference 的 slot_mapping/positions/query_start_loc

```


isolation oracle 必然命中，必然抛 `ValueError`。


**## 14.4 为什么 CPU UT 没抓到**


UT 的 `_target_metadata()` 使用独立创建的 tensor，不是真实 engine 的 canonical

对象。UT 还特意断言：


```python

assert graph_layer.slot_mapping.data_ptr() == owner.block_tables.slot_mappings[0, :8].data_ptr()

```


也就是说，UT 只验证了“Draft 使用 canonical slot mapping”，没有验证

“Target metadata 也使用同一 canonical slot mapping 时，isolation 仍应成立”。


**## 14.5 性质判定**


这是****候选代码的设备侧集成缺陷****，不是：


- fixture 问题；

- A3/CANN/driver 问题；

- 权重问题；

- MRV2 身份问题。


按规则 28，服务器上没有做任何热修。


**---**


**# 15. 证据分级**


| 结论 | 级别 |

|---|---|

| 源码 SHA/tree、13 文件差异、无 native 变化 | SOURCE FACT |

| import provenance、overlay 内容 | HOST / RECORDER FACT |

| MRV2 runner/speculator 类 | HOST / RECORDER FACT（live worker 对象） |

| capture backing 地址、长度、CAPTURE/MATERIALIZED 事件 | HOST / RECORDER FACT |

| bind 异常与 traceback | HOST / RECORDER FACT |

| 真实 NPU task operand 地址相等 | ****未观测**** |

| physical read set | ****未观测**** |

| effective update generation / completion owner | ****未观测**** |

| 根因机制（canonical 对象共享） | INFERENCE（source + 运行时对象） |


本报告没有用“输出正确”来声称“physical reads 正确”。


**---**


**# 16. 是否进入下一阶段**


最终只能三选一：


- A. `PROCEED_TO_LOCAL_FEATURE_IMPLEMENTATION`

- B. `RETURN_TO_LOCAL_CODEX`

- C. `NEED_DEVICE_OBSERVABILITY`


本轮选择：


```

B. RETURN_TO_LOCAL_CODEX

```


原因：


1. G1 FAIL，G2–G5 OPEN，不满足 A 的条件。

2. 失败不是“缺少观测手段”，而是候选代码在设备上确定性抛异常。

3. 需要先在本地修正 isolation / write-side 契约，再回设备重跑。


**---**


**# 17. 下一实施阶段**


**## 17.1 本轮不进入**


在 BASE PASS 之前，不进入：


- TP16；

- Prefix caching；

- Eagle3；

- DSA；

- MLA。


**## 17.2 BASE PASS 后的第一批建议**


如果修复后 BASE 全 PASS，下一批本地实现建议为：


1. TP16；

2. Prefix caching；

3. Eagle3；

4. DSA；

5. MLA。


**## 17.3 为什么暂不进入**


- Async：会改变 timeline 与 completion lifetime，必须等 G5 完成；

- DSA-CP：跨 rank/context 语义，超出 base single-die；

- Mixed / SFA：metadata 形态与 single dense FIA 不同；

- multi-group：当前 characterization 明确只接受

  `require_single_group_direct_prefix()`；

- DFlash2：不在 base route 集合 `{dflash,dspark}`，需要单独 policy/capability；

- DeepSeek-V4 co-trained DSpark：policy 明确 forced off。


**---**


**# 18. 清理、完整性与可复现性**


**## 18.1 清理**


- 本 campaign 的 vLLM / driver / benchmark 进程：****0 个残留****。

- HBM 已释放；`00_preflight/npu_after.txt` 已保存。

- 未杀任何未知进程。


**## 18.2 服务器源码**


```

SERVER SOURCE MODIFICATIONS = NONE

PUBLIC GRAPH SUPPORT        = STILL FROZEN

```


**## 18.3 团队工具**


```

ORIGINAL_TEAM_TOOLS_UNCHANGED

```


2296 个文件前后 SHA256 完全一致。


**## 18.4 透明说明**


为了取得 `8cb4bed6` 这个对象，本 campaign 曾在只读旧树

`/home/wenqing/mrv2_p7x_perf_final/src/vllm-ascend` 的 `.git` 对象库中执行过一次

object-only `git fetch`。没有 checkout、reset、delete、overwrite、ref 变更，

旧工作树 `git status --porcelain` 仍为空。所有 campaign 工作都在新的独立 clone：

`/home/wenqing/mrv2_graph_g1g5/src/`。


**## 18.5 环境注意**


- `npu-smi` 的 NPU/card 编号不是 logical die 编号；本轮曾出现 logical die 0–7

  被其他租户占用、8–15 空闲的情况。

- 失败重启前必须等 HBM 释放，否则会误报

  `Free memory ... less than desired GPU memory utilization`。

- MRV2 必须设置 `VLLM_USE_V2_MODEL_RUNNER=1`，但必须用 worker 内类对象取证。


**---**


**# 19. 最终终端裁决**


```

P7-X GRAPH BASE A3 CHARACTERIZATION

\===================================


HOST:

node-39-101


DEVICE:

Ascend910 A3 (PCI 19e5:d803), 16 logical dies


MRV2:

VERIFIED


MODEL RUNNER:

vllm_ascend.worker.v2.model_runner.NPUModelRunner


SPECULATOR:

vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator


VLLM-ASCEND:

8cb4bed670f395c257c1233db944395159916009


TREE:

899899c23fdc87acaed49c889eecd1f7889ad9c4


VLLM:

84030bbe3d74d99bad477a3d2e37a973ccd8865c


TREE:

f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee


FIXTURE:

Qwen3-8B + dspark_qwen3_8b_block7 (TP1, bf16 + DSpark)


METHOD:

DSpark


BACKEND:

AscendAttentionBackendImpl / STANDARD dense FIA single group


TOPOLOGY:

TP1


TEAM SKILL:

PARTIAL


AISBENCH:

NOT_APPLICABLE (G1-G5 evidence; custom correctness driver used)


G1 CAPTURE ADDRESS:

FAIL


G2 PERSISTENT REFRESH:

OPEN


G3 PHYSICAL READ:

OPEN


G4 FULL WRITE / TARGET:

OPEN


G5 TIMELINE / LIFETIME:

OPEN


BASE GRAPH DEVICE ARCHITECTURE:

FAIL


PUBLIC GRAPH SUPPORT:

STILL FROZEN


SERVER SOURCE MODIFICATIONS:

NONE


NEXT ACTION:

RETURN_TO_LOCAL_CODEX


MASTER CHINESE REPORT:

/home/wenqing/reference/

P7X_Graph_G1_G5_A3_Characterization_CN.md


CAMPAIGN REPORT:

/mnt/wenqing/mrv2_graph_g1g5_campaign/reports/

P7X_Graph_G1_G5_NPU_Characterization.md


ARTIFACT INDEX:

/mnt/wenqing/mrv2_graph_g1g5_campaign/reports/

ARTIFACT_INDEX.md

```


**---**


**# 20. 附录：证据路径**


**## 20.1 核心证据**


- `/mnt/wenqing/mrv2_graph_g1g5_campaign/G0_mrv2_identity/identity.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/G0_fixture/fixture_inventory.md`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/G1_capture/capture_events.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/G1_capture/bind_failure.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/negative/A0/result.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/negative/A1/result.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/negative/B/result.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/negative/negative_matrix_cpu.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/manifests/source_identity.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/manifests/runtime_identity.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/manifests/fixture.json`


**## 20.2 报告**


- `/mnt/wenqing/mrv2_graph_g1g5_campaign/reports/P7X_Graph_G1_G5_NPU_Characterization.md`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/reports/P7X_Graph_G1_G5_Teacher_Summary_CN.md`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/reports/P7X_Graph_G1_G5_Device_Facts.json`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/reports/P7X_Graph_G1_G5_Next_Action.md`

- `/mnt/wenqing/mrv2_graph_g1g5_campaign/reports/ARTIFACT_INDEX.md`


**## 20.3 源码与运行时**


- `/home/wenqing/mrv2_graph_g1g5/src/vllm-ascend`

- `/home/wenqing/mrv2_graph_g1g5/src/vllm`

- `/home/wenqing/mrv2_graph_g1g5/runtime/graph_char_overlay`

- `/home/wenqing/mrv2_graph_g1g5/runtime/env_graph_char.sh`

- `/home/wenqing/mrv2_graph_g1g5/runtime/site/sitecustomize.py`
