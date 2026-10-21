# Repair5 Review-Fix、集中验收补强与 GitHub 发布报告

本报告描述最终执行版本，不取代或篡改 `3bdc413a` 实现报告、Repair4 原始设备报告。新 SHA 的设备实验未运行。public Graph Gate 保持冻结。

## 1. 结论与身份

```text
repo   = https://github.com/LucianWQZ/vllm-ascend.git
branch = fix/p7x-graph-base-a3-repair5
commit = d0a3fc3d42d7d97e5e7da3890d2710263a097e63
tree   = 2f6b93415ced94fe3f4ba22c518699a023b97511
parent = 3bdc413aa9826e4c199f5d96125e71db2c343420
publication = VERIFIED
clean_room  = VERIFIED
```
Lineage: `08c94a990 → a8210d4f7 → 3bdc413aa → d0a3fc3d4`。
最终两仓 working tree clean。vLLM SHA/tree 与冻结 pin 精确一致。

- F1–F4 全部 **ACCEPTED**。依据是独立源码追踪、旧版本反例以及 producer/consumer 回归，不是直接采信评审结论。
- 本轮仅修改实验工具和 tests，共 12 文件；`vllm_ascend/` production runtime 无 diff，pinned vLLM 无修改。
- 可执行 scoped A3 campaign：正常锚点、严格联合 LIFE/ABORT、Base 与独立 Target4、受控 Target/已有 token ABA、正常路径 profiling/control 和独立 LIFE profiling。
- 不具备一次关闭所有 G1–G5 的保证：真实 MRV2 连续数值 Window reference 尚未实现；task 内部 operand、physical-read、正常无额外同步的 completion/reuse 仍有能力/证据缺口。
- 独立 Target4 是新的实验 profile，**不是**悄悄改变原 Base，也不是 public Graph 支持。
- 真实设备未执行；profiling 原生 API 是否可运行、是否产生有用关联字段仍需 A3 预检与实际采集。

## 2. 输入和证据边界

读取原 Repair5 实现报告、handoff、local_review ZIP、server input ZIP、download manifest；实际检查顶层大小/SHA256 和 ZIP CRC。原交付含 review 124 个、server 19 个 ZIP member（包括索引）。复用已校验 Repair4 接收结果与离线重判，不重复解包 362 MB raw；原始中转文件未修改。

Repair4 设备 SHA=`08c94a99032c47e2608b976c25065adbbc8dea09`，run=`20261020T035634Z_08c94a99`。旧 B0 的 21 代、15 capture/105 update、None 输出等事实只属于旧 SHA。旧离线 checker 修正不自动成为新设备证据。

原 fixture manifest SHA256 固定为：
`1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4`。
Target `/mnt/share/wql/Qwen3-8B`，Draft `/mnt/share/dspark_qwen3_8b_block7`；不重新寻找/替换模型。原模型 hashes 保留在包内原始 manifest，服务器必须逐项核对。

本轮证据分类：

| 类别 | 本轮取得什么 | 不能证明什么 |
|---|---|---|
| 旧版 RED | 不完整 LIFE/epoch 回退被旧 checker 接受；Target/Draft padding 不一致；ABORT 路径错误 | 新 SHA NPU 行为 |
| Host GREEN | 真实候选构建/dispatch、metadata/manager/recorder、真实 None 返回、联合校验与反例 | native replay/task completion |
| 源码审计 | greedy 输出生命周期、原始 capture sizes 推导、分离 observer/profiler | actual captured address/physical read |
| GitHub 网络恢复 | exact SHA/tree/parent/tool bytes | 模型运行、性能 |

## 3. Finding 裁决和修复

| ID | 裁决 | 独立复现 | 实际修复 | 验证 |
|---|---|---|---|---|
| F1 | ACCEPTED | 旧 `check_lifecycle` 仅有非空 backing、Host 时间和自报 completion 即 PASS；第二代 epoch 99→0 也 PASS | 低层只返回 `STRUCTURE_VALID_NOT_EXECUTION_ACCEPTED`；最终 CLI 强制 plan/launcher/campaign/artifact 与 recorder 一一关联；检查完整 backing tensor identity、generation/epoch、active/token shape、事件来源、descriptor、每层 update/retire、覆盖 | 真实 P3/P6/manager/recorder 的 5 代测试与 PID/layer/address/epoch/duplicate/missing 负例 |
| F2 | ACCEPTED | Target active=1/padded=2，但 pinned Draft dispatch(1,7) 得到(1,7)；旧 checker 按 Target padding 生成长度 | producer 分别保存 Target 和实际执行的 Draft geometry；Draft 检查使用绑定 descriptor、query、source lineage；检查 active canonical 行和 Window padding 零值 | 真实框架 candidate/dispatch + 实际 metadata 构建/绑定；另有 producer schema ABA 反例，不把后者称 native |
| F3 | ACCEPTED | 旧四个 ABORT 的 argv 各自输出目录正确，`outputs` 却为 LIFE | 修复生成器 outputs，最终 child/launch/checker/打包路径同源；不修改原记录 | 所有 case argv 与输出路径合同测试 |
| F4 | ACCEPTED | 原受控 Target/ABA/LIFE 的结构/数值判断缺外部运行归属；没有新联合入口 | `check-diagnostic` 显式要求 input/campaign/launcher/plan/case-id；G4F 不套16-token joint；LIFE/normal profiling 仍检查16-token；ABORT 独立73退出与partial recorder；文件 bytes/hash、PID/source/mode/argv、退出状态必须一致 | 正常执行关联及 wrong PID/source/argv/hash/timeout/signal/returncode 负例，ABORT真实scope各故障点 |

### 3.1 F1 的最终验收不是非空断言集合

数据链为：

`冻结 plan → 外部 launcher child argv/PID/returncode → campaign identity/request SHA → diagnostic 文件 bytes/SHA → producer identity → recorder bound/replay/update/retirement`

每条 lifecycle 必须对应一个 bound；相同 recorder/process/provider scope；同代 epoch、descriptor、backing address；每个实际 Draft layer 恰好一个 update；replay/update/retire 序号正确。声明的三桶每桶至少两代。结构允许诊断完成，但最终联合结果只能是 `PASS_DIAGNOSTIC_SERIALIZED`，不能关闭 normal-overlap。

普通 Event/stream 字段来源固定为 instance-owned `MRV2LifecycleProbe` 在 replay 与 UPDATE 之后记录的普通 Event。`id(event)` 只作 Host provenance。事件 `synchronize/query` 的设备语义、覆盖最后 consumer 的关系仍须真实设备证明；不能把字符串或 Host 时钟当独立物理证明。

ABORT 采用 stage-specific partial，after_replay 可能尚未回到 manager 的 replay observer，不能强求尚未产生的最终记录；after_update/after_completion 要求完整同代逐层 update。实际退出73且无signal/timeout、正确故障点、snapshot绑定一致才能成为 `EXPECTED_QUARANTINE_OBSERVED`。这不是设备安全回收 PASS。

### 3.2 F2 不是只改一个长度

`target_geometry` 保存 Target descriptor/active/padded/query；`draft_geometry` 从已执行 recorder binding 读取 Draft descriptor/gen/epoch/source_identity，并取实际 speculator query layout。canonical source 对 active 行校验，Window padded 行和 exact/upper 尾部必须零；不得拿 Target padded 替 Draft padded。

`test_real_mrv2_aba_checker_schema_and_corruptions` 使用 actual candidate dispatch，但其中 Draft artifact 是 schema 构造，明确不声称跑了 Triton。另一个 integration test 将真实 metadata builder、proposal scope、manager、recorder 连起来，替换的是 Host 无法执行的 native replay/update 原语。

### 3.3 状态语义

- `INVALID_EVIDENCE`：身份、关联、缺记录、损坏、未知结构。
- `FAIL`：已关联执行失败，或已对齐数值失败；不被 OPEN 覆盖。
- `OPEN/BLOCKED`：缺对应覆盖、bucket、数值判别力或能力。
- `SINGLE_ARM_STRUCTURE_VALID`：完整单臂结构和执行关联；不是 OFF/ON 数值等价。
- `compare-target` 是 `NUMERIC_COMPARISON_ONLY`，两臂各自先通过 `check-diagnostic` 才能组合验收。
- 低层 `check-lifecycle/check-mrv2-aba/check-abort` 保留调试用途，但 CLI exit=2，并明确不能作最终联合验收。

## 4. 独立 Target4 扩展

真实 pinned `CudaGraphManager._init_candidates()` 和 `dispatch()` 被 Host 调用（不是手填 graphs）。

| profile | capture sizes | Target candidates | Draft candidates |
|---|---|---|---|
| 原 Base | `[7,14,28]` | (1,8)、(2,16) | (1,7)、(2,14)、(4,28) |
| Target4 独立实验 | `[7,14,28,32]` | (1,8)、(2,16)、(4,32) | 原三桶不变 |

源码对 query width 向上对齐且受 max capture size 限制：原 Target 28→32 被上限28排除；扩展允许32。Draft 的32→35超过上限32，不添加第四桶。这里只证明 candidate/dispatch；启动后 driver 仍核验实际 captured inventory。

扩展使用 `--repair5-capture-profile target4`，独立 case/config SHA。包含 3 active/4 padded 以及4 active。Base11样本、扩展12样本，不修改原 Base。扩展依赖正常锚点而非 Base 缺桶引发的 expected OPEN；真实 native/binding 失败仍停止相关分支。

## 5. 数值参考与生命周期边界

已有 private FIA 的 A/B/A′、窗内/仅窗外扰动 oracle 保留。其 atol=0.016，rtol=0；受控 Target 的 deterministic OFF/ON 合同仍 atol=rtol=0，没有按结果放宽。

真实 MRV2 greedy `draft_logits` 不具有可读取的完整持久输出合同：pinned speculator 仅 probabilistic 模式分配该 buffer；greedy sampling 的 logits 为函数内临时值。Graph manager 正常返回 None。不能读未写入或旧代 buffer、不能用 None/hash占位，也不能为了取证改变 capture 输出或生产 lease。

因此 **真实 MRV2 连续 hidden/logit Window reference：NOT_IMPLEMENTED**。已实现的真实 MRV2 token ABA 继续要求 A/B 可区分；若 greedy A=B，结果保持 OPEN_NONDISCRIMINATING。用户允许的 scoped publication 不把这个缺口藏进总括 READY。

LIFE 的同步诊断、真实 MRV2调用链与私有FIA microfixture 分账；既有 UPDATE 相对顺序不变。normal overlap、UPDATE effective generation、最后 consumer completion 不由本轮 Host 测试关闭。

## 6. 采集成本与有界处理

- outside digest：每次最多约8MiB contiguous D2H，按原顺序逐块更新 hash；全覆盖未选中块，不删样本，不变更 v1 hash 定义。Host测试逐字节对照旧逐块算法。
- Target fixture：保留512MiB单checkpoint；总输出16GiB、执行3300秒，边界检查和有界 writer 在写入中生效；失败 `.partial` 不当完整产物。
- 分别记录初始化、stage、带checkpoint/sync的forward、三处outside hash、dump耗时。forward项包含诊断同步与snapshot，不冒充kernel时间。
- 新 `p7x_graph_repair5_pack.py` 采用4MiB流式压缩/哈希/验收；路径检查、重复/软链接拒绝、CRC、成员bytes/SHA和checksum index检查；JSON index上限16MiB。未一次 read_bytes 大ZIP/tensor。
- 打包依赖真实最终Git源码，不含未提交production overlay。

## 7. Profiling：正常路径与诊断路径分开

### P-A 正常路径

8个独立case：OFF/ON × short/long × control/normal。ON使用实验provider，但重型observer关闭；不安装Target probe、controlled KV dump或LIFE。control拥有相同warmup、冻结请求和轻量Host range，但不开native profiler。

`--repair5-profile normal` 使用已安装 `torch_npu.profiler.profile`；执行前（不加载模型）采集实际版本/API/signature/source可得性，缺失即BLOCKED。不叠加msprof。先完成模型初始化/capture，再用第一请求组预热一次，再采完整冻结请求组，max_tokens仍16。

本轮没有把 `propose(is_profile=True)` 当profiler开关：该业务参数可改变dispatch；包装器原样转发参数。Host测试验证原调用参数不变、真实candidate dispatch保留、active期间确有replay调用。服务器最终仍须验证actual Graph。

轻量range：request/group、Target_REPLAY_PLUS_UPDATE、Draft_propose、Draft_REPLAY_SUBMIT、Draft_REPLAY_PLUS_UPDATE。**独立 UPDATE Host 子range 尚未提供**，用完整manager范围和native trace中可关联的API字段；不可声称其中每段已精确归因。没有在replay→UPDATE间加D2H/sync/I/O。

ON long要从实际immutable Window descriptor取得source_start_column>0，而不是只看prompt长度。任何设备/工具异常保留；缺实际replay或采样不足保持OPEN。请求阶段内部900秒预算，外部watchdog1800秒。

### P-B LIFE profiling

`PROFILE_LIFE` 使用 `--repair5-profile life --repair5-lifecycle`，明确 DIAGNOSTIC_SERIALIZED，单独记录 event/wait开销解释，不进入正常性能AB比较。

### 分析入口及不能宣称的内容

`p7x_graph_repair5_profile.py analyze --input TRACE_DIR --output trace-analysis.json`：
流式读实际CSV字段和值，按各文件分别汇总已标单位的duration与copy/wait/update/replay类别；单位不明的 `Duration` 只列字段、不冒充微秒。

Host提交统计给出样本数/mean/p50/p95/sum。duration相加不是E2E，也不是无重叠device occupancy。无可靠flow/task关联时Target/Draft kernel、设备空档、prefill/decode归因保持UNRESOLVED；Host monotonic_ns不与device timestamp直接比较。

raw trace、可用CSV/DB、配置与API provenance、worker PID/device、warmup/active组和source/tool hashes必须一起返回。本工具无msprof wrapper进程；launcher PID是实际Python child。若未来使用额外wrapper，应另记PID。

参考接口资料（不是本机/A3版本证明）：[Ascend torch_npu profiler API](https://www.hiascend.com/doc_center/source/zh/CANNCommunityEdition/80RC1alpha003/apiref/fmkadptapi/ptaoplist_000263.html)、[MindStudio profiling](https://www.hiascend.com/document/detail/zh/mindstudio/70RC1/mscommandtoolug/mscommandug/atlasprofiling_16_0037.html)。以服务器实际 capability 输出为准。

“不重复同字段trace来冒充更强physical证据”仍成立；不等于禁止正常调度/拷贝/等待与开销profiling。本轮明确交付P-A/P-B。

## 8. RED/GREEN 与验证

环境：macOS Host；`.venv/bin/python`，`VLLM_VERSION=0.29.0`，
`PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm`。所有最终12文件SHA已与提交tree逐一核对。

| 验证 | 真实结果 |
|---|---|
| focused Repair4/5、Graph binding/carrier/characterization/oracle/capture observer | 434 passed |
| full tests/ut/spec_decode | 1070 passed / 13 skipped / 7 failed，exit1，非全绿 |
| exact 3bdc413a 同环境 VWN 对照 | 7 failed / 2 passed；同 upstream Invalid attention backend for None |
| Ruff check / format | PASS |
| targeted Mypy（8 tools，follow-imports=skip） | PASS；不是全仓类型证明 |
| compileall / diff-check | PASS |
| 12适用hooks（含gitleaks） | PASS |
| 完整 `bash format.sh ci` | ENVIRONMENT_BLOCKED：初次npm cache EPERM；临时可写cache/network后npm EALLOWGIT；非PASS |
| NPU/native profiler | NOT_RUN |

完整命令、原始输出与最终每文件hash在 `Validation.json`、`Hooks.json`、logs中；
`exact-baseline-vwn.log` 才是正确baseline对照。早期误以当前cwd运行的对照日志不作证据。
没有禁用hook或修改全局npm安全配置；完整check未绿是交付限制。

RED原始关键输出：

```text
F1: PASS_DIAGNOSTIC_SERIALIZED != INVALID_EVIDENCE
    不完整record、epoch99→0两个反例均失败
F4: 新外部关联模块不存在（原CLI没有最终joint）
F2: 真实Draft dispatch为1行，旧checker按Target2行：INVALID_EVIDENCE而非预期正确结构
F3: ABORT outputs 为 artifacts/LIFE，与真实child output不等
```

红测使用 `3bdc413a` 原函数；F2/F3利用 `git show` 加载原工具到测试内存，不重写工作树。绿色重点覆盖：
完整proposal→prepare/materialize/bind→真实upstream None返回→recorder UPDATE→retire→下一代；1/2/4/1/3active4pad；真实多layer共享metadata相关旧回归；结构/哈希/身份/退出关联反例；python -O；CLI帮助与生成器路径。

Native replay、NPU Event、部分FIA更新调用在Host替换。Target真实模型前向、真实native task、profilingdevice执行均未跑。测试日志不以“通过总数”替代证据等级。

## 9. 文件和边界审计

- `tests/ut/spec_decode/test_graph_repair5_cli.py`
- `tests/ut/spec_decode/test_graph_repair5_producers.py`
- `tests/ut/spec_decode/test_graph_repair5_profile.py`
- `tests/ut/spec_decode/test_graph_repair5_review.py`
- `tools/p7x_graph_repair2.py`
- `tools/p7x_graph_repair5.py`
- `tools/p7x_graph_repair5_campaign.py`
- `tools/p7x_graph_repair5_evidence.py`
- `tools/p7x_graph_repair5_lifecycle.py`
- `tools/p7x_graph_repair5_pack.py`
- `tools/p7x_graph_repair5_profile.py`
- `tools/p7x_graph_repair5_target.py`

F1/F4主要在 evidence/lifecycle/CLI；F2在target；F3/Target4在campaign/driver；profiling/pack为新工具；tests为同提交。公开Gate、allocator/scheduler、Window数学、UPDATE顺序、pinned vLLM、CANN/torch_npu安装包均未改。

发布前检查12文件tested hash==index==working tree，gitleaks staged scan通过；没有模型、token、密码、大raw/profiler产物加入Git。原模型绝对路径仅为用户指定实验fixture引用，不是模型文件。所有Notes/ZIP均留本机，未提交到公开repo。

## 10. 发布与独立恢复

GitHub身份 `LucianWQZ`，目标repo push=true。首次远端Repair5分支不存在。
复用keyring登录与既有gh credential helper；通过当前macOS实际HTTP代理
`127.0.0.1:15236` 命令级Git配置传输；不改全局proxy、不关闭TLS，不重复授权。

```sh
git push -u origin fix/p7x-graph-base-a3-repair5:fix/p7x-graph-base-a3-repair5
gh repo clone LucianWQZ/vllm-ascend <独立临时目录>/vllm-ascend -- --single-branch --branch fix/p7x-graph-base-a3-repair5
git checkout --detach d0a3fc3d42d7d97e5e7da3890d2710263a097e63
```

发布UTC：`2026-10-20T14:07:42.788263+00:00`。
独立网络clone：`/var/folders/jg/1291_6m930x__sj1qzy3kdsh0000gn/T/repair5-github-cleanroom-tdm4yq38/vllm-ascend`。
API commit/tree/parent与本地精确一致，clone clean、无objects alternates；
3bdc/a821/08c ancestry均通过，13个graph工具hash均相同。
所有其他远端heads前后快照一致。不存在本地bundle/patch替代networkclone。
Signed-off-by: Lucian；密码学签名：unsigned（GitHub verification=false），二者不混淆。

仅普通 push Repair5 分支。无force、PR、merge、tag、amend；原两次Repair5提交保留。Signed-off-by与密码学签名分开记录。

## 11. 服务器集中执行

server input内有最终handoff、原fixture/requests、实际生成的case-plan与commands、source verifier、profiling合同及回传说明。示例路径只用于评审；部署后必须用真实根目录重新生成plan，不能编辑argv后继续用旧plan验收。

本地对生成的120条 argv 调用对应真实CLI parser，全部参数解析成功（截断在任何模型/设备执行之前）。输入包 RUN_CASE 调度辅助脚本另以无设备 child/checker 实际执行验证；它只负责日志与有界子进程，不替代各Gate，也不自动替用户裁决依赖。clean-room源码还通过包内 source verifier 复核原fixture与工具hash。

1. exact GitHub fetch/checkout和两仓source/import/fixture核验；P0与profiler轻量preflight。
2. A0/A1、新SHA B0；真实三Draft replay bucket/逐层UPDATE/多代/16token/退出由相应checker验证。
3. 独立C2正常路径；B1/B2、O0/O1与自然G4按依赖进行。
4. Base G4F和独立Target4 OFF/ON；每臂先 `check-diagnostic --kind target`，再 `compare-target`，ON另ABA；Base缺4bucket不伪装PASS。
5. LIFE正常后才4种ABORT；LIFE最终联合要求三桶每桶≥2代。
6. P-A八case，P-B PROFILE_LIFE。每个child有外部watchdog、退出和请求验收；保存所有raw trace，不承诺physical证据。
7. 回传pack/verify、所有partial、launcher、schema/error、rawtrace。一个分支native/binding错误停止依赖分支，不能删桶/eager fallback；独立健康实验可继续。

### Remaining Gates

| 项目 | 当前 | 关闭条件 |
|---|---|---|
| 新SHA正常Graph及Target4 | DEVICE_NOT_RUN | 新源码锚点、真实inventory/replay及完整数值artifact |
| 真实MRV2连续Window reference | NOT_IMPLEMENTED | 经审查的同代连续输出及同Window语义参考seam |
| token A/B/A′ | scoped entry ready，可能OPEN | A/B可区分、A′恢复、同backing多代完整来源 |
| FULL_TARGET | producer/Host合同已实现 | 两臂联合执行通过，完整preKV/input对齐、outputs/KV比对 |
| 同步LIFE/ABORT | Host已验证，device未跑 | 普通event实际completion及stage证据；隔离进程quarantine |
| normal-overlap reuse | UNPROVEN | 无额外串行化路径的有效consumer依赖/时序证据 |
| task内部operand/physical-read | CAPABILITY_GAP | 新字段/外部支持或owner验收决策；本轮不降标准 |
| P-A/P-B | implemented, DEVICE_NOT_RUN | 实际profile API、raw导出、足够replay样本、诚实字段归因 |
| public Graph | STILL_FROZEN | 后续独立完整验收及明确owner授权 |

## 12. 交付与历史

所有最终交付位于 `/Users/wenqingzhang/Desktop/Note/MRV2`。旧 `3bdc413a` handoff/inputpack/download manifest 另行归档，原实现报告保留为review baseline。新发布报告是最终执行身份依据。

评审ZIP包含完整diff、关键源码/tests、RED/GREEN、最终验证文件hash、精确baseline失败对照、发布/网络clone证据和合同。server ZIP不携带覆盖源码patch；执行只使用已验证Git commit。

最终top-level download manifest不自引用；ZIP索引不包含自身hash，避免循环。实际解压后检查成员SHA/CRC/JSON、handoff内外一致、plan与argv输出路径及最终SHA/tree一致。

最终结论：**READY_FOR_A3_SCOPED=YES（依赖成功且使用最终已发布exact源码）；READY_FOR_ALL_G1_G5_CLOSURE=NO；NEW_SHA_DEVICE_VERIFICATION=NOT_RUN；PUBLIC_GRAPH_GATE=STILL_FROZEN。**
