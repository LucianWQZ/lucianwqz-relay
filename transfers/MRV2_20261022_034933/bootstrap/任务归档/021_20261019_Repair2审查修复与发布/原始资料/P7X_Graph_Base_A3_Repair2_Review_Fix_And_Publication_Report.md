# P7-X Graph Base Repair2 — Review Findings Fix 与 Exact Publication

## 1. 本轮裁决及边界

本轮只修复证据检查工具与 Host 测试。四项 Finding 全部独立复现，均 ACCEPTED。没有修改 `vllm_ascend/` production 核心目录，没有改 capture observer、Graph carrier、REPLAY→CONSUMER→UPDATE 顺序、completion 协议或公开 Graph Gate。

本轮结果不能用于宣称 `GRAPH_BASE_DEVICE_PASS`、`G1_G5_VERIFIED` 或 `PUBLIC_GRAPH_SUPPORTED`。没有登录服务器、运行模型、执行 NPU campaign 或性能实验。

**当前终局（2026-10-19T06:20:16Z 复核）：本地修复通过；普通 push 已完成；GitHub 官方 API 与 Git remote 核验通过；使用 GitHub CLI 在全新独立目录执行 clone，SHA/tree/parent、ancestry、driver hash 与 clean 状态全部通过。`PUBLICATION=VERIFIED`，`READY_FOR_A3_SMOKE=YES`。此前网络失败保留于 §10.4–10.5；本次成功复验见 §10.6。没有再次 push、制造提交或启动服务器实验。**

| 项目 | 本轮事实 |
|---|---|
| Review findings | F1/F2/F3/F4 全部 ACCEPTED，已修复 |
| 原 Repair2 observer 修复 | 保留；实际 metadata 共享/幂等/冲突/回滚/closure 测试继续通过 |
| 新 SHA 设备验证 | NOT_RUN |
| 公开 Graph Gate | STILL_FROZEN |
| Ready for all G1–G5 closure | NO；设备/task/physical read/completion 与部分实验 fixture 仍有未闭环项 |
| 本轮改动 | `tools/p7x_graph_repair2.py` 与 `tests/ut/spec_decode/test_graph_repair2_campaign.py` 两个文件 |

发布身份与 clean-room 实证见本文最后的“最终身份与发布核验”节；与同名 Server Handoff JSON 配套使用。

## 2. 输入及精确基线

完整读取本轮授权附件：

`/Users/wenqingzhang/.codex/attachments/47357cb6-38d7-4b8a-b844-f2e9c00d424b/已粘贴的文本.txt`

读取上轮报告：

`/Users/wenqingzhang/Desktop/Note/MRV2/P7X_Graph_Base_A3_Repair2_Implementation_And_Readiness_Report.md`

辅助证据目录保持只读：

`/Users/wenqingzhang/Desktop/Note/MRV2/g1-g5_repair2_local/`

固定 fixture manifest：

`/Users/wenqingzhang/Desktop/Note/MRV2/g1-g5_repair2_local/fixture_manifest.json`

实际 SHA256：`1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4`。未改写 fixture、模型身份或历史证据。

| 仓库 | 初始 HEAD | 初始 tree | 状态 |
|---|---|---|---|
| vllm-ascend | `1870e0ba8a00eeeae16c27f877e81eb65b711080` | `a913b534d4a731cdcbca8256f42f0c1a3a6dc0a6` | clean，分支 `fix/p7x-graph-base-a3-repair2` |
| vLLM | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` | `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` | clean，零 diff，全程只读 |

Ascend 基线 parent 为 `13373fff637e819f3db125e05064f94cba3475a3`。没有用户未提交改动或待合并后续提交；未 reset、rebase、amend 或覆盖已有历史。适用 AGENTS.md 已读取。

## 3. Resolution Table

| ID | Finding | Reproduction | Resolution | Code action | 覆盖边界 |
|---|---|---|---|---|---|
| F1 | operand actual/expected 相等不等于属于对应 backing | 同时改两地址为 999，保留 backing=200；capture/update 两反例旧版均 PASS | ACCEPTED | capture operator 关联同 descriptor 的前序 capture helper；update 关联 capture、BOUND、同代 G4；三个 operand 地址均核验；同 provider 的同 descriptor backing/route 不得漂移 | HOST_OPERATOR_BOUNDARY_FACT，不是 ACL task 内部地址认证 |
| F2 | BOUND 内容未与 G4/独立 oracle 关联 | 只改 BOUND table 首元素为999，G4与 canonical 不变；旧版 PASS | ACCEPTED | BOUND/G4 两份 active rows 各自与独立 canonical oracle 比较；required columns、active tail、padded rows/lengths 分开验证；缓存事件必须引用准确 BOUND sequence | 允许不同合法零 padding/capacity；不伪造新的 device sample |
| F3 | 总数量相等掩盖重复/缺失代际 | 三代 BOUND，三条不同 sequence 的 G4 却都属于首代；旧版 PASS | ACCEPTED | 先按 key 分组，再强制唯一，重复不进入唯一索引；逐代检查 missing/orphan；A/B/A 同样拒绝重复 G4 | key 为 generation/epoch/descriptor，外层 recorder/process/provider scope 必须一致 |
| F4 | epoch 仅互异，未严格递增 | generation10/11/12，epoch30/20/10，内容A/B/A；旧版 PASS | ACCEPTED | 按 recorder sequence 排序，generation 与 mapping_epoch 均严格递增；允许正向间隔；同 scope/descriptor/backing，内容恢复不等于身份回退 | 当前 parallel Base proposal 协议；不能泛化到未支持的 Eagle3 Graph per-step 共 epoch 协议 |

没有将静态逻辑缺陷 defer 给 NPU。四项闭合只表示这些漏检已被覆盖，不表示 JSON 不可能被整体伪造；checker 不是签名/设备可信执行证明。

## 4. RED 实证与可重现方式

在修改工具前先加五个失败测试（F1 capture/update 两例，F2/F3/F4 各一例）：

```bash
cd /Users/wenqingzhang/Desktop/vllm/vllm-ascend
VLLM_VERSION=0.29.0 PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
  .venv/bin/pytest -q tests/ut/spec_decode/test_graph_repair2_campaign.py -k review_f
```

实际结果：exit 1，`5 failed, 28 deselected`。五例都是预期 INVALID_EVIDENCE/FAIL，却得到旧检查器 PASS，不是环境导入失败。

关键输出：

```text
F1 capture: assert 'PASS' == 'INVALID_EVIDENCE'  -> FAIL
F1 update:  assert 'PASS' == 'INVALID_EVIDENCE'  -> FAIL
F2 BOUND:   assert 'PASS' == 'INVALID_EVIDENCE'  -> FAIL
F3 G4:      assert 'PASS' == 'INVALID_EVIDENCE'  -> FAIL
F4 ABA:     assert 'PASS' == 'FAIL'             -> FAIL
```

另保存 `test_review_red.py`：通过 `git show 1870e0ba:...` 读取不可变的旧 checker 和旧 fixture，在内存执行相同反例，不 checkout、不修改源码；实际再次得到 `5 failed`、exit 1。这样后续即使测试 fixture 已更新，仍可重现旧版漏洞。

RED 辅助脚本与原始输出随本轮辅助证据保存，不提交 GitHub。

## 5. 修改设计及关键 diff

### 5.1 地址不是单条记录自洽即可

旧版主要条件：

```python
actual_table_address == expected_table_address
```

新版关联链：

```text
snapshot recorder/process/provider scope
  ├─ capture helper(descriptor, sequence, backing)
  │    └─ capture operator(expected/actual/captured address)
  └─ BOUND(generation, epoch, descriptor, backing)
       ├─ matching unique G4(window_table_address)
       └─ update operator(expected/actual/captured address)
```

同一 descriptor 的 warmup/capture helper 可以多次出现。使用当前事件之前最近的 helper，不按 descriptor 构造一个会覆盖历史的简单字典；重复 helper 的 length 可以变化，但同一 provider scope 中 persistent backing/route 不得改变。

关键代码：

```python
matching = [e for e in captures
            if e.get("capture_descriptor") == record.get("capture_descriptor")
            and e["sequence"] < record["sequence"]]
capture = max(matching, key=lambda e: e["sequence"]) if matching else None
for field in ("expected_table_address", "actual_table_address", "captured_table_address"):
    same_backing(capture, event.get(field), ...)
    # update 时再与对应 BOUND 关联
```

缺 capture backing 不能获得完整 Host/smoke PASS。即使同时伪改 expected/actual/captured 三个地址为相同错误值，也会被跨记录检查拒绝。

### 5.2 BOUND/G4 内容与合法 padding

actual count 来自真实 raw full_exact 的长度，并检查 full_upper/valid_counts/mapping/request_ids 同行数。对每个 active row，从原始 canonical Full table 和 H=E 的 parallel Base 合同，调用独立整数 oracle；不调用 production Window planner。

```python
tables = (bound["table_values"], g4["window_table_values"])
for row in active_rows:
    expected = independent_oracle(canonical_row, full_exact, full_upper, W, B, ...)
    for table in tables:
        require(table[row][:required_columns] == expected_block_ids)
        require(all(v == 0 for v in table[row][required_columns:]))
require(all_zero_padded_rows)
require(all_zero_padded_exact_and_upper)
```

没有要求两份 snapshot 的整个 shape 相同。不同额外零列/零行仍可合法；active required columns 必须相同且都等于 oracle。非零 tail、非零 padded row、缺 active row、非零 padded length 都失败。

### 5.3 唯一关联先于索引

```python
grouped.setdefault(generation_key, []).append(record)
if len(matches) != 1:
    errors.append("duplicate G4 generation ...")
else:
    unique[key] = matches[0]
```

这不是先覆盖、事后比较总条数。缺少某代唯一 G4、孤立 G4、重复 BOUND 均被显式报告。Scope 在关联之前检查，跨 run/engine/provider 的 record_scope 混用不会靠相同数字地址获准。

### 5.4 时间顺序与缓存语义

`sequence` 是同一个 recorder 的 Host 顺序，不是设备时钟。BOUND 按 sequence 排序；generation 和 epoch 均须严格递增，不能只检查集合大小=3。JSON 数组重排不改变时间解释；允许递增但不连续的合法值。

真实 recorder 的 LIVE/REPLAY/CONSUMER/UPDATE 通过 `replace(bound, values_sampled_at_sequence=bound.sequence)` 引用缓存值，避免在待 UPDATE 的 replay 前新增 D2H。检查器要求该引用及 route/backing/table/exact/upper 与指定 BOUND 相同。**这些事件并不是再次读取设备内容，也不能证明设备已消费或完成。**

A/B/A′ 同时需要同 recorder/process/provider、descriptor、backing、A与A′的语义内容和 source lineage 对应；A′拥有新的 generation/epoch。无法自然重现相同物理内容仍然 OPEN，不由 checker 改写数据。

### 5.5 `python -O` 与损坏输入

所有新增及原 oracle 必要校验使用显式 `_require`，不依赖可被优化去掉的 assert。旧版 `-O` 直接抛 RuntimeError，可能没有报告；新版正常/优化模式对合法与损坏证据给出一致结果。

无效 root、结构、坏 sequence、截断 JSON、读文件失败会产生 INVALID_EVIDENCE 报告和非零退出。不能以无事件/无异常判功能 PASS。报告输出目的地自身不可写仍是基础 I/O 失败，不能承诺任意坏磁盘状态都能生成报告。

## 6. GREEN 与真实 recorder 测试

环境：Mac Host，无 NPU；Python 3.12.14 / Torch 2.14.1 / pytest 9.1.1。`VLLM_VERSION=0.29.0`，`PYTHONPATH` 指向精确 pinned vLLM。唯一 warning 是 upstream 缺本地 `_version`，未据此伪造或修改 upstream。

最终命令：

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

最终结果：**211 passed, 1 warning，exit 0；无失败、无跳过。** 其中 campaign checker 文件从28增加至68项，其余直接相关143项保留。没有为凑数重跑无关 full suite，也未将上轮808/13/7数字复用为本轮结果。

真实 recorder 集成保留：

```text
真实 P3 runtime/source/workspace
→ 注册真实 capture identity/persistent backing
→ recorder.record_capture / record_capture_operand
→ P3 materialize(2 active + 2 padded)
→ eager generation publish
→ prepare_parallel_draft_window_graph_characterization
→ 实际 carrier bind + G4 raw-input snapshot
→ consume + REPLAY/CONSUMER observer
→ actual backend-update validation + update operand recorder
→ recorder.snapshot()
→ audit_campaign()
```

替代范围：CPU Tensor、已有 Host metadata builder harness、无 NPU算子执行；不是理想化 JSON 全量代替 recorder。该测试通过真实字段结构、raw full producers、实际 padded rows 和缓存 sampling 引用。其 descriptor 为 Host fixture `(4,8)`，因此 Host contract PASS，但固定服务器 smoke OPEN；task、physical-read、completion 仍 OPEN。篡改这一真实 snapshot 的 operator 地址后即 INVALID_EVIDENCE。

| 测试族 | 证明内容 |
|---|---|
| F1 capture/update，两地址/三地址共同伪改 | 不再依赖单事件内自洽 |
| F2 原始反例及所有 cached event 同步伪改 | 独立 oracle 检查 BOUND，而不是仅靠缓存比较偶然失败 |
| zero padding 合法 shape 差异 | 不错误要求全矩阵 shape 相等 |
| F3 duplicate/missing/orphan/duplicate BOUND | 不用总数或字典覆盖冒充一一对应 |
| F4 decreasing/repeated/forward-gap epochs | 按真实 owner 顺序检查；不要求连续整数 |
| A/B/A scope/descriptor/backing splice | 内容相同不能授权另一 owner |
| repeated capture helper | 使用前序 helper；重复合法、backing漂移非法 |
| 12个正常/`-O` CLI场景 | 正向、错地址、错table、截断JSON、坏shape、null root均有明确结果 |
| 原有错误scope/layer/bucket/lag/empty | 保留，不降低原断言 |
| 原 real-owner/canonical alias及 observer 生命周期 | 原 production 合同回归继续通过 |

## 7. Checker exit code 与实验解释

`check` 默认仍要求实际 inventory 和 replay 三个 bucket：`(1,7)`、`(2,14)`、`(4,28)`。它不把请求数当 descriptor 覆盖。新增输出 required/missing replay buckets、missing inventory buckets。

单独边界 case 仅覆盖 `(1,7)`：可得 `HOST_CONTRACTS=PASS`，但 `fixed_inventory_replay=OPEN`、exit 2。应解释为完整 smoke 覆盖不足，不应自动归因 production defect。

完整三 bucket 正向样本：exit 0 只表示记录层面的 fixed-inventory smoke 满足当前检查。以下仍独立 OPEN：

- `DEVICE_FUNCTIONAL_GATES.G2_A_B_A`：Host 内容检查不是设备时序/读集证明。
- `DEVICE_FUNCTIONAL_GATES.G4_controlled_target_numeric`：必须另做受控输入/KV对齐的数值比较。
- task internal / physical_read / completion_and_effective_generation：缺设备证据不得由 Python record 推导。

## 8. 下一轮设备任务与剩余缺口

继续沿用已确认 DSpark fixture；不要重新找模型：Qwen3-8B + dspark_qwen3_8b_block7，K=7/query=7、W=1024、block span=128、capacity=1151（不是 max_model_len）、single STANDARD dense FIA、TP1，FULL_DECODE_ONLY 实际 FULL，capture sizes `[7,14,28]`。

其余模型/调度/环境/长度参数仍以原 manifest/command ledger 为准。manifest 不进入公开 GitHub，须单独传到服务器并先校验上述 hash。

执行顺序：精确拉取新 SHA/tree → pinned vLLM SHA/tree → driver/fixture hash → A0 → A1 → B固定inventory smoke → 核对capture/bind/replay实际记录 → 再按原计划G1–G5。失败保留原异常、partial artifact、first divergence；不能减少 capture sizes 或 fallback eager 来换 PASS。

本轮仍未解决/未执行的部分：

| 项目 | 状态/处理 |
|---|---|
| 新 SHA 的 startup capture、旧 alias 点、真实 bind/replay | DEVICE_NOT_RUN，先做 smoke |
| G1 task 内部 operand地址（L3） | 工具字段与真实导出能力待核；Python调用边界不可替代 |
| G3 physical memory read-set（L5） | TOOL_CAPABILITY_UNVERIFIED；msprof可运行不代表含物理block读集 |
| G5 update effective generation / completion（L6） | DEVICE_NOT_RUN；不得用 Python return/UPDATE return/Host假event替代 |
| 自然 A/B/A′ 物理内容重现 | fixture依赖未消除；不得改活跃 canonical table伪造 |
| G4 controlled Target numeric | 需要真实输入/位置/历史KV对齐与预先确定容差；null/hash缺失不是相等 |
| 设备 abort/exception 与 stream lifecycle | 仍需有界设备实验，未添加双缓冲或新completion架构 |
| observer-off Graph | 实验路径与observer开关已在基线拆分；本轮无设备验证 |
| Graph Batch A | TP16/Prefix/Eagle3/DSA/MLA/Async等不在本轮范围 |

能够开始 A3 smoke 与能够关闭全部 G1–G5 是两件事。前者在实际发布和 clean fetch 完成后可为 YES；后者当前必须 NO。

## 9. 静态/安全/发布核验

最终实际检查、提交身份与远端核验记录追加如下。

| 检查 | 实际结果 |
|---|---|
| Local Ruff 0.16.10 check / format --check | PASS，2文件 |
| 仓库配置 Ruff v0.14.0 pre-commit check / format | PASS，授权下载官方hook环境后重跑 |
| codespell / typos configured hooks | PASS |
| targeted Mypy 1.11.1 `--follow-imports=skip --ignore-missing-imports tools/p7x_graph_repair2.py` | PASS，1 source file；不是全仓类型证明 |
| compileall（两修改文件） | PASS |
| staged diff-check / 最终 commit diff-check | PASS |
| python-init、forbidden-imports、boolean-context-manager、long-functions、symbolic-meta、logger | 本机直接运行 PASS |
| 完整 pre-commit runner，第一次 | ENVIRONMENT_BLOCKED，GitHub DNS，exit3；原日志保留 |
| 完整 pre-commit runner，授权网络后重试 | ENVIRONMENT_BLOCKED，actionlint 的 `go install ./...` 下载 `proxy.golang.org` 依赖 i/o timeout，exit3；未伪报完整hooks PASS |
| Gitleaks8.30.1 staged scan | PASS，no leaks；独立运行，不依赖上面失败的通用runner |
| Gitleaks `13373fff..最终HEAD` | PASS，2 commits / 106229 bytes scanned / no leaks |
| 新 SHA NPU | NOT_RUN |

安全工具仅安装在临时目录。使用 Gitleaks 官方 GitHub v8.30.1 的 Darwin ARM64 发布包与官方 checksums，下载完成后验证 OK 才执行。下载过程中曾过早尝试一次 checksum，因文件尚未完成失败，未执行该 partial 包；完成后重新校验。没有执行仓库脚本中 `--no-check-certificate` 的二进制下载路径，也没有为使完整 runner 变绿禁用其失败项。

发布前人工范围检查与 secret scan 只覆盖 source/tests commit lineage。Notes、manifest、服务器 raw evidence、模型/tensor/profiler文件、临时扫描工具均不在Git提交中。没有 credentials/token、本机绝对路径或公司运行数据新增到本次代码diff。

## 10. 最终身份与发布核验

### 10.1 独立 review-fix commit

```text
branch: fix/p7x-graph-base-a3-repair2
commit: 8198ab7a6df6a163316f5d4ed2126242bbeb4aa8
tree:   27eee84d06ec60461be7471d7c2ff941ad6d27ea
parent: 1870e0ba8a00eeeae16c27f877e81eb65b711080
subject: fix(spec-decode): strengthen graph campaign evidence associations
Signed-off-by: Lucian <2207456347@qq.com>
```

本次 commit：2文件，`+541/-37`。工具 `+189/-25`；测试 `+352/-12`。旧 fixture 补上真实 schema 已有的 capture helper、captured pointer、route、window pointer、cached sample reference，未删除原负向测试。

```text
13373fff637e819f3db125e05064f94cba3475a3
  → 1870e0ba8a00eeeae16c27f877e81eb65b711080  (Repair2 原提交)
  → 8198ab7a6df6a163316f5d4ed2126242bbeb4aa8  (本轮 review-fix)
```

重要区分：本次发布的新分支同时携带之前未发布的 Repair2 原提交及本次 review-fix；并不是宣称 `13373fff→最终HEAD` 只有两个文件。该整个增量为原 Repair2涉及的8文件；本轮相对1870只改工具与测试。

`vllm_ascend/` subtree 在1870及最终commit均为 `1b00fbb9339d1f133726aa9485ffae5dd83e000d`，提供 production核心逐位未改的Git证据。

最终driver SHA256：`b165211b833bc0f32afdd32b134475648a8b14fe3734bc76c3d6d7e1653cea68`。

### 10.2 发布命令

GitHub CLI已登录用户 `LucianWQZ`，API确认仓库 `LucianWQZ/vllm-ascend` 且push权限为true。未索取、输出或复制token。origin：`https://github.com/LucianWQZ/vllm-ascend.git`。

发布前目标远端分支不存在。执行：

```bash
git -c push.followTags=false push -u origin \
 refs/heads/fix/p7x-graph-base-a3-repair2:refs/heads/fix/p7x-graph-base-a3-repair2
```

实际输出：

```text
* [new branch] fix/p7x-graph-base-a3-repair2 -> fix/p7x-graph-base-a3-repair2
branch ... set up to track origin/fix/p7x-graph-base-a3-repair2
```

普通非force push。未创建PR、未打tag、未merge main/lucian-dev、未amend/rebase/squash。GitHub打印的“Create a pull request”提示仅是链接，未访问创建PR接口。

### 10.3 远端身份与引用核验

推送后 GitHub 官方 API 返回：

```json
{
  "ref": "refs/heads/fix/p7x-graph-base-a3-repair2",
  "sha": "8198ab7a6df6a163316f5d4ed2126242bbeb4aa8"
}
```

Git commit API 返回：

```json
{
  "parents": ["1870e0ba8a00eeeae16c27f877e81eb65b711080"],
  "sha": "8198ab7a6df6a163316f5d4ed2126242bbeb4aa8",
  "tree": "27eee84d06ec60461be7471d7c2ff941ad6d27ea"
}
```

发布前 `git ls-remote origin` 保存85行（含HEAD和peeled tag）。发布后使用可访问的官方 `git/refs` API 返回branch/tag对象，排除本次唯一新分支、HEAD与peeled tag展示行后排序diff，exit0。**其余所有branch/tag对象 SHA 未变**，包括 `main`、`lucian-dev`、旧冻结分支、`perf/p7x-draft-window-hotpath` 和 repair1分支。

GitHub真实分支：

https://github.com/LucianWQZ/vllm-ascend/tree/fix/p7x-graph-base-a3-repair2

### 10.4 历史记录：首次独立 clean-room 未完成

新建的独立目录：

`/private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend`

没有复用当前 `.git`、worktree、bundle或patch。执行：

```bash
git init /private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend
git -C /private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend remote add origin \
  https://github.com/LucianWQZ/vllm-ascend.git
git -C /private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend \
  fetch --depth=2 --no-tags origin refs/heads/fix/p7x-graph-base-a3-repair2
```

真实结果（exit128）：

```text
fatal: unable to access 'https://github.com/LucianWQZ/vllm-ascend.git/':
Failed to connect to github.com port 443 after 75003 ms:
Couldn't connect to server
```

在该失败快照中，`checkout FETCH_HEAD`、clean-room SHA/tree/parent、clean-room ancestry/status 尚未得到证明，当时 JSON 对应字段为 null。此历史状态由 §10.6 的成功独立恢复更新，不以本地已知值替代拉取证明。

后续只读排查：普通 ls-remote、HTTP/1.1 ls-remote再次超时；curl普通/IPv4 HTTPS均在10秒连接超时；官方SSH443可连接但 `Permission denied (publickey)`，没有新增key或改变主机信任。`api.github.com`始终可读，所以能够确认提交确实存在，但不能将API对象响应替代用户要求的独立Git恢复。

### 10.5 历史恢复计划（已由 §10.6 完成）

只重试 fetch/checkout/verify，不需再次push：

```bash
git -C /private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend \
  fetch --depth=2 --no-tags origin refs/heads/fix/p7x-graph-base-a3-repair2
git -C /private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend checkout --detach FETCH_HEAD
git -C /private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend rev-parse HEAD 'HEAD^{tree}' HEAD^
git -C /private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend \
  merge-base --is-ancestor 1870e0ba8a00eeeae16c27f877e81eb65b711080 HEAD
git -C /private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend status --porcelain --untracked-files=all
shasum -a 256 /private/tmp/p7x-repair2-cleanroom.U4q2zg/vllm-ascend/tools/p7x_graph_repair2.py
```

必须分别匹配本文最终 SHA/tree/parent/driver hash，ancestry exit0、status为空。只有这些成功且远端ref仍精确一致，才可将report/handoff改为 `publication_status=VERIFIED`、`ready_for_a3_smoke=true`。即使届时成功，`ready_for_all_g1_g5_closure=false` 和新SHA设备验证NOT_RUN仍不得改变。

### 10.6 GitHub CLI 独立恢复成功：2026-10-19

用户要求使用 GitHub CLI 后重新执行 `gh auth status`、`gh api user --jq .login`：现有 keyring 授权有效，登录用户精确为 `LucianWQZ`。未索取 token、未输出 token、未重复触发无必要登录；授权有效与前次 Git HTTPS 超时是不同事实。

在新建的空临时目录中执行以下命令，exit0：

```bash
gh repo clone LucianWQZ/vllm-ascend \
 /private/tmp/p7x-repair2-gh-cleanroom.GqgSW9/vllm-ascend \
 -- --branch fix/p7x-graph-base-a3-repair2 --single-branch --depth=2 --no-tags
```

没有使用本地 `.git`、objects、worktree、bundle 或 patch；`.git/objects/info/alternates` 不存在。`gh repo clone` 对 fork 自动添加了只读 fetch 的 upstream，并拉取其 main/tags；这不是对 upstream 或 origin 的 push，也没有改变原工作仓库。最终 checkout 仍精确为用户 fork 的目标分支。

实际独立恢复结果：

```text
origin=https://github.com/LucianWQZ/vllm-ascend.git
branch=fix/p7x-graph-base-a3-repair2
HEAD=8198ab7a6df6a163316f5d4ed2126242bbeb4aa8
tree=27eee84d06ec60461be7471d7c2ff941ad6d27ea
parent=1870e0ba8a00eeeae16c27f877e81eb65b711080
git merge-base --is-ancestor 1870e0ba8a00eeeae16c27f877e81eb65b711080 HEAD: exit0
git status --porcelain --untracked-files=all: empty
git diff --exit-code HEAD: exit0
git fsck --connectivity-only: exit0
tools/p7x_graph_repair2.py SHA256:
b165211b833bc0f32afdd32b134475648a8b14fe3734bc76c3d6d7e1653cea68
```

SHA/tree/parent/ancestry/clean/no-alternates 以串联命令显式断言，整体 exit0；不是只看最后一条命令。GitHub CLI commit/ref API 与恢复后的 `git ls-remote --heads origin refs/heads/fix/p7x-graph-base-a3-repair2` 再次返回同一身份。复核时间：`2026-10-19T06:20:16Z`（北京时间14:20:16）。

在新 clone 中运行工具 `--help` 及 `compileall`，均成功；使用现有 Python 解释器，但执行的脚本文件来自新 clone，bytecode cache 写到 clone 外的临时目录。未运行 `run`、未加载模型或 NPU；这是独立源码恢复/CLI smoke，不是新设备验证或新完整UT运行。

原 Ascend 工作仓库仍 clean，HEAD/tree 没有变化；原 vLLM 仍 clean，固定 SHA/tree 未变。fixture manifest hash 再次核对一致。本次没有再次 push、PR、tag 或远端分支写入。

## 11. 交付文件与最终状态

- 主报告：`/Users/wenqingzhang/Desktop/Note/MRV2/P7X_Graph_Base_A3_Repair2_Review_Fix_And_Publication_Report.md`
- 机器handoff：`/Users/wenqingzhang/Desktop/Note/MRV2/P7X_Graph_Base_A3_Repair2_Server_Handoff.json`
- 本轮辅助审计：`/Users/wenqingzhang/Desktop/Note/MRV2/g1-g5_repair2_review_local/`（RED脚本/日志、GREEN日志、hooks失败日志、安全扫描日志、patch、远端refs/API记录）。不属于production提交。

最终两原始仓库均clean。Ascend HEAD为8198ab7a6；vLLM保持固定84030bbe及f3e320f8 tree。完整 pre-commit 的历史网络环境失败仍为 ENVIRONMENT_BLOCKED，未被本次 clone 成功覆盖；GitHub独立恢复已按 §10.6 实际完成。服务器可开始 A3 smoke，但不得将 smoke readiness 理解为 G1–G5 已闭合或公开 Graph 支持。

```text
LOCAL_REVIEW_FINDINGS: F1/F2/F3/F4 CLOSED
LOCAL_REPAIR_HOST_VERIFIED: YES
PUSH_PERFORMED: YES
REMOTE_API_IDENTITY: VERIFIED
OTHER_BRANCHES_AND_TAGS: UNCHANGED
CLEAN_ROOM_RECOVERY: VERIFIED
PUBLICATION: VERIFIED
READY_FOR_A3_SMOKE: YES
READY_FOR_ALL_G1_G5_CLOSURE: NO
NEW_SHA_DEVICE_VERIFICATION: NOT_RUN
PUBLIC_GRAPH_GATE: STILL_FROZEN
```
