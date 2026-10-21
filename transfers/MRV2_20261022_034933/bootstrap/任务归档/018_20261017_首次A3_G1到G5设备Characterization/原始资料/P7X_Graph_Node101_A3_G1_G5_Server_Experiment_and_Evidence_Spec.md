# P7-X MRV2 Draft Sliding Window — Node101 A3 G1–G5 服务器实验与证据交付规范

## 0. 文档用途

本文件用于让线上 GPT 生成交给公司服务器 Claude（可调用 DeepSeek API）的正式执行 Prompt。

服务器任务不是继续写 Graph Feature，也不是在服务器上修 production。服务器只需要使用已经发布的 exact candidate，完成第二轮真实 Ascend A3 Base Graph characterization，并交付足以回答下列问题的原始证据：

1. startup capture 是否真正绑定 P6/P7-X persistent Window backing；
2. runtime 每个 generation 是否在同一地址上刷新正确的 table/length；
3. FIA 实际接收并消费的 read carrier 是否符合独立 Window oracle；
4. slot、positions、query layout、Target metadata 和 KV write 是否完全保持 full/baseline；
5. `REPLAY → CONSUMER → UPDATE` 的真实设备代际和 completion/lifetime 语义是什么；
6. 当前 Base Graph architecture 是否足以作为后续 TP16、Prefix、Eagle3、DSA 等 Graph adapters 的公共底座；
7. 若不能通过，后续本地开发究竟应修改 capture、runtime carrier、metadata、update timeline、lease/lifetime，还是观测能力。

本次实验结束后，服务器必须给出“证据 + 事实裁决”，而不是只给日志摘要或主观结论。

---

# 1. 当前冻结事实

## 1.1 已发布代码

### vLLM-Ascend

```text
repo   = https://github.com/LucianWQZ/vllm-ascend.git
branch = fix/p7x-graph-base-a3-g1g5
SHA    = 13373fff637e819f3db125e05064f94cba3475a3
tree   = 739cde3de61e65be7cdbd187baebb6d17da04aee
parent = 8cb4bed670f395c257c1233db944395159916009
```

### pinned vLLM

```text
repo = 用户已验证的 LucianWQZ/vllm 或公司等价只读镜像
SHA  = 84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree = f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
```

两仓都必须 clean。服务器不得修改 vLLM，不得在 vLLM-Ascend checkout 中生成 commit，不得通过 site-packages 热补丁伪装 exact source。

## 1.2 当前 Gate

```text
PUBLIC GRAPH SUPPORT: STILL FROZEN
PUBLIC GRAPH USER GATE: FAIL-CLOSED
EXPERIMENTAL CHARACTERIZATION: DEFAULT OFF
NPU G1–G5: OPEN
```

实验变量 `VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1` 只是内部 characterization 开关，不是产品配置，不得据此宣称 Graph 已支持。

## 1.3 第一次 A3 实验结论

第一次真实 A3 campaign 已证明：

- MRV2 runner/speculator 身份正确；
- A0 Window OFF Graph baseline 正常；
- A1 public Graph Window 配置按预期 `GRAPH_FROZEN`；
- startup capture 成功；
- 第一次 runtime bind 因 validator 把合法 canonical Full write/query sharing 误判成 Target 污染而失败；
- G2–G5 因 G1 前置失败未执行。

错误：

```text
ValueError: Draft metadata mutable storage aliases Target metadata
```

commit `13373fff...` 已将两个不同 invariant 分离：

- Draft-private read state 必须与 Target-private mutable storage 隔离；
- `slot_mapping`、`positions`、`query_start_loc` 等必须保持 canonical Full identity，可以与 Target 引用同一个 canonical owner。

本轮首要任务是用真实 A3 证明这个修复进入了正确运行路径，并继续完成 G1–G5。

---

# 2. 严格范围

## 2.1 本轮只允许测试的正向 route

复用第一次 campaign 已接受的 fixture，不重新寻找模型：

| 字段 | 固定值 |
|---|---|
| target | `/mnt/share/wql/Qwen3-8B` |
| draft | `/mnt/share/dspark_qwen3_8b_block7` |
| model runner | `vllm_ascend.worker.v2.model_runner.NPUModelRunner` |
| speculator | `vllm_ascend.worker.v2.spec_decode.dspark.speculator.AscendDSparkSpeculator` |
| method | eligible `dspark` |
| K | `7` |
| actual query width | `7` (`sample_from_anchor=True`) |
| backend | `AscendAttentionBackendImpl` |
| layout | STANDARD dense GQA/FIA direct-prefix |
| groups | one executable gid |
| Graph | `FULL_DECODE_ONLY`；实际 decode descriptor 为 FULL |
| W | `1024` |
| block span | `128` tokens |
| capacity | `1151` tokens |
| topology | TP1 DP1 PP1 PCP1 DCP1 |
| disabled | async、prefix、SP、DSA-CP、FlashComm |
| capture sizes | `[7, 14, 28]` |
| capture buckets | `(1,7)`、`(2,14)`、`(4,28)` |

如服务器上的模型路径变化，只允许通过受控软链接或明确 path mapping 指向哈希相同的文件；不能换模型后沿用结论。

## 2.2 本轮禁止扩展

不要实现或验证为 PASS：

- TP16 Graph；
- Prefix Graph；
- Eagle3 Graph；
- DSA / DSA-CP / SFA / MLA Graph；
- Async Graph；
- mixed/chunked Graph；
- multi-group Graph；
- DFlash2 Graph；
- public Graph user Gate；
- 性能结论。

上述全部属于 Base G1–G5 通过后的后续 Batch A。若本次看到相关错误，只记录为 out-of-scope，不在服务器修改生产代码。

## 2.3 服务器修改规则

服务器可以：

- 创建 campaign 目录、外部 driver、解析脚本和报告；
- 使用仓库自带 `tools/p7x_graph_g1_g5.py`；
- 启用 CANN/msprof/msprobe 等只读观测；
- 为 profiler flush 使用 characterization-only 同步，但必须标注 `NOT PERFORMANCE REPRESENTATIVE`。

服务器不可以：

- 修改或 commit 两个仓库；
- 临时放开 public Gate；
- 改 capture/update 顺序；
- 添加 global/ContextVar/owner swap；
- 用 `torch.npu.synchronize()` 作为 feature completion 设计；
- 遇到观测缺口后直接写 production workaround；
- push、PR、tag。

如果现有代码不能提供某项证据，正确结果是 `OPEN` 加精确 missing seam，而不是现场修代码。

---

# 3. 证据等级

所有报告必须明确区分：

| Level | 含义 | 本次代码可直接提供 |
|---|---|---|
| L1 Source/Host identity | Python object/storage、generation、descriptor、route | 是 |
| L2 Operator-call boundary | 传入 Ascend FIA capture/task-update 调用的真实 table/length operand | 是，标记 `HOST_OPERATOR_BOUNDARY_FACT` |
| L3 ACL task internal binding | ACL task/runtime 内部保留的 operand/descriptor 地址 | 需要设备工具；不能由 L2 冒充 |
| L4 Device task/read boundary | profiler/task trace 能关联到 FIA task 和 carrier | 需要 CANN/msprof/msprobe |
| L5 Physical memory transaction/read set | NPU 实际读取了哪些物理 KV block | Python pointer 不足；工具不可见时保持 `UNPROVEN` |
| L6 Completion/effective generation | UPDATE 对哪次 replay 生效、何时可安全复用 backing | 需要真实 task/stream/event timeline |

禁止把：

- `build_attn_metadata` 输入地址写成 captured ACL task 地址；
- `full_graph_fia()` 的 Python 参数写成 physical memory transaction；
- Python function return 写成 device completion；
- `PROPOSAL_RETIRED` 写成 NPU reader complete；
- host A/B/A' 写成 NPU A/B/A'。

---

# 4. Campaign 目录和不可变记录

建议新建：

```text
/mnt/wenqing/mrv2_graph_g1g5_rerun_13373fff_<timestamp>/
```

目录必须至少包含：

```text
00_preflight/
01_source_and_import/
02_fixture/
03_host_tests/
A0_off_baseline/
A1_public_gate/
B_internal_candidate/
G1_operand_binding/
G2_refresh_aba/
G3_read_oracle/
G4_write_target/
G5_timeline_lifetime/
negative/
commands/
manifests/
raw_profiler/
reports/
summary/
SHA256SUMS
```

每条命令都保存：

- 原始 shell command；
- 完整展开后的 argv；
- 生效环境变量；
- stdout；
- stderr；
- exit code；
- 开始/结束时间；
- 使用的 device logical id；
- 输出文件列表和 SHA256。

不得只保存终端截图。

---

# 5. Preflight：任何 NPU run 之前必须完成

## 5.1 GitHub clean fetch

从 GitHub 获取目标分支，不允许从第一次 campaign checkout 手工覆盖文件：

```bash
git clone --branch fix/p7x-graph-base-a3-g1g5 --single-branch \
  https://github.com/LucianWQZ/vllm-ascend.git <NEW_ASCEND_CHECKOUT>
```

验证并保存：

```bash
git rev-parse HEAD
git rev-parse HEAD^{tree}
git rev-parse HEAD^
git status --porcelain --untracked-files=all
git log --graph --decorate --oneline -8
```

要求：

```text
HEAD   = 13373fff637e819f3db125e05064f94cba3475a3
tree   = 739cde3de61e65be7cdbd187baebb6d17da04aee
parent = 8cb4bed670f395c257c1233db944395159916009
status = clean
```

pinned vLLM 要求：

```text
HEAD   = 84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree   = f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
status = clean
```

任一不一致立即 STOP。

## 5.2 Import provenance

必须在实际 worker 进程内记录：

- `vllm.__file__`；
- `vllm_ascend.__file__`；
- `NPUModelRunner` class path；
- `AscendDSparkSpeculator` class path；
- `AscendAttentionBackendImpl` class path；
- `draft_window_graph_characterization` module path；
- `draft_window_graph_oracle` module path；
- `sys.path`；
- tracked Python 文件 SHA256；
- native extension/so 的来源和版本。

如果环境必须继续使用 native donor + Python overlay，必须复用第一次 campaign 已归档的 overlay recipe，并保存：

- donor path/version；
- overlay source commit；
- copied/symlinked file list；
- 每个 overlay 文件 SHA256；
- import 实际命中的路径。

不允许在未证明 import provenance 时开始 G1。

## 5.3 Hardware/software manifest

记录：

- hostname；
- A3 具体产品名、PCI id、logical die 映射；
- `npu-smi info` before/after；
- driver、firmware、CANN、torch、torch-npu、Python；
- HBM 可用量；
- 其他租户/进程；
- device visibility 环境；
- msprof/msprobe/CANN trace 工具版本；
- 系统时钟和时区。

第一次 campaign 使用过 `node-39-101`、CANN 9.1.0、driver 26.0.rc1。若本次主机或软件不同，报告必须把结论 scope 到新环境，不得写成对旧环境的直接复现。

## 5.4 Fixture integrity

必须核对：

| 文件 | SHA256 |
|---|---|
| target `config.json` | `f7c4eadfbbf522470667b797a3c89be2524832d2d599797248dc304fff447c30` |
| target `model.safetensors.index.json` | `f9fdbcb91c23971c13ec5d5f2573d2349e8f61f2f049371ec699281748fdb1bc` |
| target `tokenizer.json` | `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4` |
| draft `config.json` | `e470e70a553616f0dce8f783f42cfd25b7bd7dfdcd57ead680a0623040725611` |
| draft `model.safetensors` | `5c922d1f96c8d18dbdf005c40ea99878d9133d70eaa3be4bd1077ee5f2afc1e5` |

target shard 全量哈希、原 prompt、prompt hash、seed、max tokens、scheduler limits 必须从第一次 campaign 的：

```text
/mnt/wenqing/mrv2_graph_g1g5_campaign/manifests/fixture_hashes.txt
/mnt/wenqing/mrv2_graph_g1g5_campaign/requests/prompt.txt
/mnt/wenqing/mrv2_graph_g1g5_campaign/requests/prompt.sha256
/mnt/wenqing/mrv2_graph_g1g5_campaign/commands/argv_*.txt
```

复用。缺失时 STOP，不自行换 prompt 后声称复现。

## 5.5 Resource isolation

- 使用经确认空闲的 logical die；
- 记录 card label 与 logical die 对应关系；
- launch 前后记录 HBM；
- failed run 后等待 HBM 释放；
- 不 kill 非本 campaign 进程；
- 每次 run 记录进程树和 PID；
- campaign 结束证明无残留进程。

---

# 6. Host/UT sanity

在服务器 source 环境中运行并保存完整输出：

```bash
pytest -q tests/ut/spec_decode/test_draft_window_graph_characterization.py
pytest -q tests/ut/spec_decode/test_draft_window_graph_carrier.py
pytest -q tests/ut/spec_decode/test_draft_window_graph_binding.py
pytest -q tests/ut/spec_decode/test_draft_window_graph_oracle.py
python tools/p7x_graph_g1_g5.py --help
```

如测试因 host/backend 环境失败：

- 保存 stack；
- 说明是否进入目标模块；
- 标记 `ENVIRONMENT_BLOCKED`，不能写 PASS；
- 不为绿测修改 production assertion。

重点确认两条 regression：

```text
test_real_target_metadata_sharing_is_allowed_for_full_write_carriers
test_draft_private_fields_still_reject_target_storage_alias
```

前者证明合法 canonical sharing；后者证明 Draft-private isolation 没被放松。

---

# 7. 运行环境

公共环境：

```bash
export VLLM_USE_V2_MODEL_RUNNER=1
export VLLM_ENABLE_V1_MULTIPROCESSING=0
export ASCEND_RT_VISIBLE_DEVICES=<verified free logical die>
```

`VLLM_ENABLE_V1_MULTIPROCESSING=0` 仅用于同进程 recorder access，不是产品能力条件。

A0/A1：

```bash
unset VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH
unset VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT
```

B/G1–G5：

```bash
export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1
export VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH_ARTIFACT=<campaign>/B_internal_candidate/G1_G5_characterization_v2.json
```

必须复用第一次 campaign 已归档的 driver 和完整 argv。不要重新写一套不同的模型加载流程：

```bash
python scripts/driver_case.py \
  --case <A0|A1|B> \
  --window <off|1024> \
  --flag <0|1> \
  <exact archived expanded arguments>
```

最终报告不得保留 `<...>` 占位符；必须写实际命令。

---

# 8. 强制执行顺序

```text
Preflight
→ Host UT
→ A0
→ A1
→ B minimal startup/bind/replay
→ G1
→ G2
→ G3
→ G4
→ G5
→ final cross-artifact audit
```

任何前置 STOP condition 触发后，不得跳到后续 Gate 拼凑 PASS。

---

# 9. A0 / A1 / B 控制组

## 9.1 A0 — Window OFF Graph baseline

```text
draft_window_size = off
experimental flag = unset/0
```

必须证明：

- engine 启动；
- 使用 MRV2 `NPUModelRunner` + `AscendDSparkSpeculator`；
- Graph baseline 正常；
- deterministic output 与第一次 A0 合同一致；
- zero characterization session/provider/carrier；
- 不产生 v2 artifact；
- Target/slot/write baseline 可保存为 G4 OFF oracle。

失败：STOP 全 campaign。

## 9.2 A1 — Public Gate control

```text
draft_window_size = 1024
experimental flag = unset/0
```

预期唯一正确结果：在任何 Window FullSource/workspace/provider/capture carrier 前 `GRAPH_FROZEN`。

若 public route 实际执行或分配 Window Graph state：安全缺陷，STOP。

## 9.3 B — Internal characterization candidate

```text
draft_window_size = 1024
experimental flag = 1
artifact path = explicit writable path
```

B minimal run 必须至少出现：

```text
capture
capture_operator
materialized
bound
live
replay
replay_submitted
consumer
update
update_operator
update_event_recorded
proposal_retired
G4 record
```

第一次 campaign 的 alias exception 必须消失。若仍出现同一错误，优先判断 import/overlay 是否仍指向 `8cb4bed...`，不要立即认定 fix 无效。

出现以下任一项立即 STOP：

- alias/isolation exception；
- Target metadata 为 None/空/owner 不符；
- carrier/descriptor/backend mismatch；
- generation/mapping epoch mismatch；
- missing source stage；
- Target/write mutation；
- stale generation；
- runtime crash。

---

# 10. G1 — Capture / update operand binding

## 10.1 要回答的问题

1. CaptureIdentity 所有的 stable backing 地址是什么？
2. `AscendAttentionBackendImpl.full_graph_fia()` 实际传给 capture operator 的 block table/length 地址是什么？
3. ACL task 内部真正保留的是哪个 operand？
4. runtime `update_graph_params()` 传入 task update 的 table/length 地址是什么？
5. capture/update 是否对应同一 descriptor、backend、layer、consumer 和 persistent owner？

## 10.2 必须保存的字段

对每个 capture descriptor 与活跃 runtime descriptor保存：

- route；
- graph mode；
- capture descriptor/bucket；
- query width/static K/W/block geometry；
- expected persistent table pointer；
- capture operator table pointer；
- update captured table pointer；
- update actual table pointer；
- length kind/address/values；
- backend impl；
- builder impl；
- layer name；
- consumer；
- task handle identity；
- ExternalEvent identity；
- stream identity；
- runtime generation_id/mapping_epoch；
- canonical Full/Target table pointers作为负对照。

## 10.3 工具调查与 trace

服务器必须记录实际可用工具及版本，并尝试获得：

- FIA operator/task id；
- task handle 与 profiler event 的关联；
- operator input descriptor；
- graph task capture/update记录；
- 若工具支持，operand device address。

优先调查：

- CANN profiler / msprof；
- msprobe；
- torch_npu graph/task diagnostics；
- ACL Graph task dump/trace；
- operator input descriptor dump。

若 API 只返回 shape/dtype 而不返回地址，原样记录限制。

## 10.4 PASS 分层

```text
G1_HOST_OPERATOR_BOUNDARY = PASS
```

要求：

```text
expected backing ptr == capture operator table ptr
expected backing ptr == update actual table ptr
descriptor/backend/consumer/layer一致
Window pointer != canonical Full/Target pointer
```

```text
G1_ACTUAL_ACL_TASK_INTERNAL = PASS
```

只有设备 trace 明确证明 task 内部绑定同一 persistent backing 才允许。

如果只能证明 L2：

```text
G1_HOST_OPERATOR_BOUNDARY = PASS
G1_ACTUAL_ACL_TASK_INTERNAL = OPEN
```

不能把总 G1 写成无条件 PASS。

---

# 11. G2 — Persistent backing A/B/A'

## 11.1 必须在同一 engine/session 中执行

不能重启 engine 后比较地址。A、B、A' 必须使用：

- 同一个 captured descriptor/bucket；
- 同一个 provider；
- 同一个 persistent backing；
- 三个不同 generation；
- 三个严格递增 mapping_epoch。

目标：

```text
A  : generation g,   epoch e,   content A
B  : generation g+1, epoch e+1, content B, B != A
A' : generation g+2, epoch e+2, semantic content A,
     but runtime identity != A
```

若 allocator 导致 A' 无法自然复用相同 block-id 内容，必须：

- 保留实际结果；
- 说明 fixture construction 为什么无法满足；
- 不伪造 table；
- 将 `G2_NPU_A_B_A = OPEN`；
- 给出后续需要的 test-only allocator/request fixture seam。

## 11.2 必须验证

- A/B/A' table address 完全相同；
- A 与 A' table/length semantic相同；
- B 内容不同；
- generation/epoch/request fingerprint 不同；
- A stale handle 不能 authorize A'；
- 每个 stage 的 table generation 与 length generation一致；
- previous Window 从未成为下一代 source；
- 下一代 rewrite 前，前一代 consumer 已完成，或者 runtime 明确拒绝/等待；
- Target/write state不随A/B/A'污染。

执行仓库自带 audit：

```bash
python tools/p7x_graph_g1_g5.py audit \
  <campaign>/B_internal_candidate/G1_G5_characterization_v2.json \
  --output <campaign>/G2_refresh_aba/G1_G5_audit.json
```

保存 exit code。`ready_for_device_campaign=true` 只表示 artifact sections 齐全，不等于设备 G1–G5 PASS。

---

# 12. G3 — Independent oracle 与真实 read carrier

## 12.1 Case matrix

至少覆盖：

| Case | 目的 |
|---|---|
| G3-SHORT | `H <= W`，S=0 |
| G3-BOUNDARY | Window start/required columns落在精确block边界 |
| G3-NONBOUNDARY | 非边界 exact/upper |
| G3-LONG | 长上下文，明确丢弃旧历史 |
| G3-SOURCE-SHORTAGE | source不足必须在operator submission前fail closed |

若 source-shortage 只能由 host/CPU fixture 构造，应标记 host negative，不伪称 NPU positive case。

## 12.2 独立 oracle

每个 positive case从 runtime raw record提取：

- canonical full table row；
- H；
- E；
- full upper；
- W；
- legacy alignment B；
- block span；
- query width；
- valid block count。

然后独立运行：

```bash
python tools/p7x_graph_g1_g5.py oracle \
  --full-table <actual comma-separated canonical row> \
  --horizon <actual H> \
  --exact <actual E> \
  --upper <actual upper> \
  --window 1024 \
  --legacy-block-size <actual B> \
  --block-span 128 \
  --query-width 7 \
  --valid-block-count <actual count> \
  --output <case>/independent_oracle.json
```

这个 oracle 不调用 production planner。必须比较：

- S；
- E；
- V；
- projected upper；
- source start column；
- required columns；
- expected column indices；
- expected block ids；
- operator-boundary table values；
- operator-boundary exact/upper values。

## 12.3 设备证据

必须尽最大可能关联：

```text
independent oracle
→ operator-boundary operand
→ ACL graph task/FIA operator
→ profiler/task trace
```

如果 profiler 不暴露物理 memory transaction，最终必须诚实写：

```text
G3_OPERATOR_BOUNDARY = PASS/FAIL
G3_TASK_CORRELATION = PASS/OPEN
G3_PHYSICAL_MEMORY_TRANSACTION = UNPROVEN
```

不要静默把 G3 标准降为 pointer equality。

## 12.4 建议额外输出

为每个 case生成 `oracle_vs_actual.json`：

```json
{
  "case_id": "G3-LONG",
  "generation_id": 0,
  "mapping_epoch": 0,
  "expected": {
    "S": 0,
    "E": 0,
    "V": 0,
    "columns": [],
    "block_ids": [],
    "exact": [],
    "upper": []
  },
  "operator_boundary_actual": {
    "table_address": 0,
    "table_values": [],
    "length_values": []
  },
  "device_trace": {
    "tool": "actual tool name",
    "task_id": "actual id",
    "operand_address_visible": false,
    "physical_read_visible": false
  },
  "verdict": "PASS|FAIL|OPEN"
}
```

示例中的零值只是 schema，占位值必须在最终 artifact 中替换为真实数据。

---

# 13. G4 — Full write / Target invariants

## 13.1 A0 与 B 必须同源比较

使用同一：

- model/draft；
- prompt/seed；
- scheduler limits；
- request shape；
- topology；
- capture bucket；
- device；
- software环境。

生成机器可读 `G4_off_vs_on.json`，至少包含：

| State | 必须比较 |
|---|---|
| canonical Full table | pointer、shape、dtype、values |
| Window table | pointer、values；必须private |
| slot_mapping | pointer、storage、values |
| positions | pointer、storage、values |
| query_start_loc | pointer、storage、values |
| actual_seq_lengths_q | values/semantics |
| Target metadata | root identity、每层identity、nested tensor/ndarray storage |
| Target read lengths | exact/upper/consumer fields |
| KV write | slot/address mapping，若工具可见 |
| Draft output | hash/tokens |
| Target output | logits/output hash，若driver真实提供 |

## 13.2 PASS 条件

- canonical Full table OFF == ON；
- slot pointer/storage/value OFF == ON；
- positions value/absolute semantics OFF == ON；
- query layout OFF == ON；
- Target metadata 未被 Draft build/bind/update 原地修改；
- Target lengths OFF == ON；
- physical KV write mapping OFF == ON；
- Window table不alias canonical Full或Target-private read state；
- 唯一允许变化是 Draft read table/length；
- controlled Target logits/output 在可观测时相等。

若 `target_output_hash` 未由外部 driver传入，不得把空值解释为相等；G4 Target-output 子项保持 OPEN，并说明需要哪个 driver seam。

---

# 14. G5 — Replay / Update / completion / lifetime

## 14.1 必须回答的核心问题

当前 source 顺序是：

```text
metadata/bind
→ REPLAY
→ CONSUMER observer
→ UPDATE
```

这不自动证明 UPDATE(N) 对 replay N 生效。服务器必须用设备 task/stream trace 和不同 generation 内容指纹回答：

```text
UPDATE(N) affects replay N?
UPDATE(N) affects replay N+1?
first replay uses capture dummy, previous generation, or current generation?
```

## 14.2 Timeline record

每个 generation 至少记录：

```text
host monotonic timestamp
device/profiler timestamp
generation_id
mapping_epoch
request fingerprint
capture descriptor
table pointer + content hash
length pointer/value hash
materialized
bound
metadata built
replay submitted
FIA task start/end
consumer observed
update begin/operator/end
update event recorded
update effective replay generation
replay completion event state
lease state
proposal retired
backing rewrite/reuse
```

## 14.3 Real completion evidence

当前代码已提供：

- replay 后在 current stream 上记录的 `torch.npu.Event`；
- backend task update 后的 `torch.npu.ExternalEvent`；
- task handle identity；
- stream identity；
- host retirement state。

服务器必须将它们与 profiler/task trace关联。以下都不是独立 completion proof：

- Python `run_fullgraph()` return；
- CONSUMER observer；
- UPDATE return；
- `PROPOSAL_RETIRED`；
- 为了收集 profiler 而执行的全局 synchronize。

## 14.4 PASS 条件

- 明确 current/next effective generation；
- replay消费的table/length属于同一个 expected generation；
- 不存在 table更新而length滞后一代，或反之；
- backing rewrite不早于真实device reader completion；
- A/B/A'无 stale/early overwrite；
- update stream/task/event 与正确 descriptor/layer 关联；
- 异常/abort 后 backing/lease不会被错误复用。

若事实证明 UPDATE(N) 只影响 replay(N+1)，而当前实现仍假设它影响 N，则 G5 必须 FAIL，并把后续修复指向 pre-replay update、双buffer/bank或timeline contract调整；不得只改 event 名称。

---

# 15. Negative 与 fail-closed 检查

在不消耗大量 NPU 时间的前提下，至少重验：

- CONFIG_OFF：zero candidate state；
- A1 public Graph Gate：仍 `GRAPH_FROZEN`；
- wrong descriptor/bucket；
- wrong backend；
- mapping_epoch mismatch；
- generation mismatch；
- stale carrier；
- source shortage；
- Target-private read alias；
- unsupported hardware family；
- prefix/async/TP>1 等 base route misuse 在 FullSource/workspace前拒绝。

资源、模型缺失、HBM不足、端口冲突或其他租户占卡都必须标记 `INFRA`，不能计作 expected Gate PASS。

---

# 16. 跨 artifact 自动一致性检查

服务器 Agent 应生成一个独立 parser/checker，至少验证：

1. artifact schema 为 `mrv2-draft-window-graph-characterization-v2`；
2. source stages齐全且sequence严格递增；
3. capture event generation/epoch为空；
4. runtime stages generation/epoch一致；
5. capture/update operand descriptor一致；
6. expected/capture/update table address关系；
7. table/length generation不分裂；
8. G4 record能唯一映射一个 generation；
9. lifecycle event能唯一映射一个 generation；
10. A/B/A'同址、内容关系和identity关系；
11. OFF/ON write/Target comparison无缺字段；
12. profiler task id能关联到对应 operator event；
13. 所有报告引用的文件存在且hash一致。

仓库自带 audit 的输出必须保留，但不可把它作为唯一裁决器，因为它不会关闭 L3/L5/L6 device facts。

---

# 17. 服务器必须生成的报告

建议统一放入 `reports/`：

## 17.1 总报告

### `P7X_Graph_G1_G5_A3_Rerun_Final_Report_CN.md`

必须包含：

- Executive verdict；
- source/import/fixture/device identity；
- A0/A1/B结果；
- G1–G5逐项事实；
- evidence level；
- raw artifact链接；
- first divergence；
- root cause classification；
- 是否允许进入后续 Graph Base productionization；
- 需要返回本地修改的 exact function/file；
- 不能证明的事实。

## 17.2 机器事实

### `P7X_Graph_G1_G5_A3_Rerun_Device_Facts.json`

至少包含：

```text
source
import_provenance
hardware
software
fixture
controls
g1
g2
g3
g4
g5
negative
cleanup
decision
```

## 17.3 Gate 状态

### `P7X_Graph_G1_G5_A3_Rerun_Gate_Status.csv`

列：

```text
gate,subgate,status,evidence_level,artifact,scope,first_divergence,next_action
```

status只能使用：

```text
PASS
FAIL
OPEN
INFRA
NOT_RUN
```

## 17.4 G1 报告

### `G1_Operand_Binding_Report.md`
### `G1_Operand_Binding.json`

逐 descriptor列 expected/capture/update/task pointer、length、backend、consumer、task/event/stream，并明确 L2 与 L3 的差别。

## 17.5 G2 报告

### `G2_A_B_A_Prime_Report.md`
### `G2_A_B_A_Prime.json`

包含三代完整 identity、content、pointer、event、completion、rewrite时机。

## 17.6 G3 报告

### `G3_Independent_Oracle_Report.md`
### `G3_Oracle_vs_Actual.csv`

逐case列S/E/V/upper/columns/block ids/operator values/task trace/physical read可见性。

## 17.7 G4 报告

### `G4_OFF_ON_Write_Target_Report.md`
### `G4_OFF_ON_Write_Target.json`

要求 machine-readable pointer、storage、values、hash差异。

## 17.8 G5 报告

### `G5_Replay_Update_Completion_Timeline.md`
### `G5_Replay_Update_Completion_Timeline.json`
### `G5_Timeline.csv`

要求 host/device时间轴、task/event/stream、effective generation和safe reuse裁决。

## 17.9 后续开发输入

### `RETURN_TO_LOCAL_Graph_Mandatory_Gap_Report.md`

即使全部 PASS 也要生成。格式：

| Gap ID | Gate | Observed fact | Expected | First divergent function | Required local change | Regression/NPU rerun | Scope |
|---|---|---|---|---|---|---|---|

不要直接在服务器修 gap。

## 17.10 Artifact index

### `ARTIFACT_INDEX.md`
### `SHA256SUMS`

索引每个原始/派生文件、生成命令、用途、证据等级和hash。

---

# 18. 如何判定“信息足够指导后续开发”

只有同时满足下面条件，服务器交付才算完整：

| 决策问题 | 最低充分证据 |
|---|---|
| alias fix是否进入真实路径 | B首次bind/replay成功 + real-owner pointer/storage record |
| capture绑定谁 | L2 exact operand + 尽可能L3 task correlation |
| runtime是否刷新当前代 | A/B/A' + per-stage generation/content fingerprints |
| Window数学/columns是否正确 | 独立oracle与actual operator operand逐case一致 |
| 是否真的physical read | device tool证据；不可见时明确UNPROVEN |
| write/Target是否不变 | A0/B machine comparison + storage/value/hash oracle |
| UPDATE作用哪代 | distinguishable generation content + task timeline |
| 何时能重写backing | real completion event/task end与rewrite时序 |
| 后续改哪里 | first-divergence定位到具体source function/contract |
| 能否进入Batch A | Base G1–G5全部裁决且无隐藏OPEN影响公共底座 |

如果缺少 task internal pointer 或 physical transaction，但所有 source/operator-boundary证据正确，报告仍然有价值；只是相关 Gate 保持 OPEN，后续 owner 决定是否增加新的本地 characterization seam或采用更强设备工具。

---

# 19. 结果到后续开发的映射

| 实验结果 | 后续本地开发方向 |
|---|---|
| B仍报合法sharing alias | import drift，或 private isolation view/restore boundary仍不完整 |
| capture pointer不是persistent backing | capture adapter/descriptor/provider registration错误 |
| update pointer不是current carrier | `update_full_graph_params`/backend binding wiring错误 |
| replay使用上一代内容 | timeline存在one-step lag；需pre-replay update或carrier bank redesign |
| table与length不同代 | typed carrier原子绑定不足；需generation-coupled update |
| A/B/A'地址变化 | backing owner/capacity/descriptor复用策略错误 |
| early overwrite | lease retirement和device completion未绑定；需真实completion token |
| oracle与operator table不符 | P1/P2 projection或Graph materialize/bind错误 |
| operator正确但task/read错误 | ACL task binding/update语义或backend consumer错误 |
| slot/positions/query变化 | read/write边界回归，必须阻断全部Graph工作 |
| Target metadata变化 | Draft-private build/isolation回归 |
| G1–G5全部PASS | 才可开始按独立分支实现TP16/Prefix/Eagle3/DSA等Batch A |

即使 G1–G5 全 PASS，也不能直接开放 public Gate。后续仍需要：

1. 把设备事实固化成 regression/integration tests；
2. 明确 production completion/lifetime contract；
3. 移除或关闭 characterization-only D2H/observer；
4. 单独做 observer-off correctness rerun；
5. 单独做性能 A/B/A；
6. 由 owner 决定 exact supported route 与 release Gate。

---

# 20. STOP 条件

出现以下任一项，停止正向 campaign并打包证据：

- source/tree/import/fixture drift；
- A0 baseline regression；
- A1不再fail closed；
- alias/private isolation错误；
- capture/update operand记录缺失；
- descriptor/backend/consumer mismatch；
- generation/epoch/request fingerprint mismatch；
- table/length代际分裂；
- canonical Full、slot、positions、query或Target被修改；
- stale A authorize A'；
- backing在reader pending时被覆盖；
- task timeline无法归因；
- 设备资源/工具异常导致结果不可解释。

STOP 后不得进入 TP16、Prefix、Eagle3 等 feature branch测试。

---

# 21. Final Verdict 模板

服务器总报告必须以此结尾：

```text
P7-X GRAPH BASE A3 G1-G5 RERUN
================================

SOURCE IDENTITY: PASS / FAIL
IMPORT PROVENANCE: PASS / FAIL
FIXTURE IDENTITY: PASS / FAIL
A0 OFF BASELINE: PASS / FAIL / INFRA
A1 PUBLIC GATE: PASS / FAIL
B INTERNAL CANDIDATE: PASS / FAIL / INFRA

ALIAS FIX DEVICE REVALIDATION: PASS / FAIL

G1 HOST OPERATOR BOUNDARY: PASS / FAIL / OPEN
G1 ACL TASK INTERNAL BINDING: PASS / FAIL / OPEN

G2 HOST A/B/A': PASS / FAIL / OPEN
G2 NPU A/B/A': PASS / FAIL / OPEN

G3 INDEPENDENT ORACLE: PASS / FAIL / OPEN
G3 OPERATOR BOUNDARY: PASS / FAIL / OPEN
G3 DEVICE TASK CORRELATION: PASS / FAIL / OPEN
G3 PHYSICAL MEMORY TRANSACTION: PASS / FAIL / UNPROVEN

G4 FULL WRITE/TARGET: PASS / FAIL / OPEN

G5 UPDATE EFFECTIVE GENERATION: CURRENT / NEXT / UNRESOLVED
G5 DEVICE COMPLETION/LIFETIME: PASS / FAIL / OPEN

BASE GRAPH DEVICE ARCHITECTURE: PASS / PARTIAL / FAIL
READY FOR LOCAL GRAPH FOLLOW-UP DEVELOPMENT: YES / NO
READY FOR BATCH A: YES / NO

PUBLIC GRAPH SUPPORT: STILL FROZEN
SERVER PRODUCTION MODIFICATIONS: NONE
NEXT ACTION: RETURN_TO_LOCAL_CODEX / OWNER_DECISION / INFRA_RETRY
```

`PARTIAL` 必须列出每个 OPEN 对后续开发是否构成 blocker，不能只写“大部分通过”。

---

# 22. 交付回 Mac 的最小包

必须复制回 `/Users/wenqingzhang/Desktop/Note/MRV2/` 下的新目录，至少包含：

```text
P7X_Graph_G1_G5_A3_Rerun_Final_Report_CN.md
P7X_Graph_G1_G5_A3_Rerun_Device_Facts.json
P7X_Graph_G1_G5_A3_Rerun_Gate_Status.csv
G1_Operand_Binding_Report.md
G1_Operand_Binding.json
G2_A_B_A_Prime_Report.md
G2_A_B_A_Prime.json
G3_Independent_Oracle_Report.md
G3_Oracle_vs_Actual.csv
G4_OFF_ON_Write_Target_Report.md
G4_OFF_ON_Write_Target.json
G5_Replay_Update_Completion_Timeline.md
G5_Replay_Update_Completion_Timeline.json
G5_Timeline.csv
RETURN_TO_LOCAL_Graph_Mandatory_Gap_Report.md
ARTIFACT_INDEX.md
SHA256SUMS
```

以及所有引用的 raw：

- A0/A1/B logs/result JSON；
- `G1_G5_characterization_v2.json`；
- `G1_G5_audit.json`；
- 每个 independent oracle JSON；
- CANN/msprof/msprobe raw traces；
- exact commands/env/argv；
- source/import/fixture manifests；
- prompt和prompt hash；
- NPU before/after与cleanup证明。

不要只复制最终Markdown而丢掉raw trace。

---

# 23. 给线上 Prompt 生成器的简版任务摘要

可将以下摘要与本文件一起交给线上 GPT：

```text
请为公司A3服务器Claude生成一个严格执行Prompt。

代码必须从GitHub clean fetch：
LucianWQZ/vllm-ascend
branch fix/p7x-graph-base-a3-g1g5
SHA 13373fff637e819f3db125e05064f94cba3475a3
tree 739cde3de61e65be7cdbd187baebb6d17da04aee

pinned vLLM：
84030bbe3d74d99bad477a3d2e37a973ccd8865c
tree f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee

复用原Qwen3-8B + dspark_qwen3_8b_block7、DSpark K=7、W=1024、
FULL_DECODE_ONLY、dense FIA、single-group、TP1 fixture。

按Preflight→UT→A0→A1→B→G1→G2→G3→G4→G5执行。
不得修改production、不得开放Graph、不得扩到TP16/Prefix/Eagle3/DSA等。

重点证明：
1. alias fix在真实owner路径通过；
2. capture/update operand是否绑定persistent Window backing；
3. A/B/A' current-generation refresh与无early overwrite；
4. 独立oracle与operator/task/read evidence；
5. OFF/ON slot/write/Target不变；
6. UPDATE(N)实际影响N还是N+1，真实completion何时发生。

必须区分host identity、operator boundary、ACL task internal、physical read和completion。
不能把Python pointer/return当NPU physical/read/completion证明。

按本规范第17、21、22节生成全部报告和raw artifact，最后打包SHA256SUMS。
```

---

# 24. 本地后续使用方式

服务器结果返回后，本地 Codex/DeepSeek 应按以下顺序审查：

1. 校验 `SHA256SUMS` 和 artifact index；
2. 校验 source/import/fixture identity；
3. 复算独立 oracle；
4. 对齐 recorder sequence 与 profiler task timeline；
5. 逐项裁决 G1–G5；
6. 以 `RETURN_TO_LOCAL_Graph_Mandatory_Gap_Report.md` 为输入，只修被证据确认的 gap；
7. 新代码继续走 local implementation → independent review → adjudication → new GitHub branch → clean server rerun；
8. 旧 SHA 的 NPU 证据不得自动继承到新 SHA。

当前最终状态：

```text
SERVER CAMPAIGN SPEC: READY
EXACT CANDIDATE: PUBLISHED
NEXT: NODE101/ASCEND A3 G1–G5 REVALIDATION
PUBLIC GRAPH SUPPORT: STILL FROZEN
```
