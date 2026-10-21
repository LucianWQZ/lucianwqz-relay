# P3 Lease / Workspace + Typed Transport + DraftMetadataStore Implementation Notes

## 1. 文档状态

| 项目 | 值 |
|---|---|
| 权威设计 | `MRV2_Speculative_Draft_Sliding_Window_Final_Design.md` |
| 实施计划 | `MRV2_Draft_Window_Implementation_Plan.md` |
| vLLM baseline | `84030bbe3d74d99bad477a3d2e37a973ccd8865c` |
| vLLM-Ascend P2 Final / P3 parent | `fac84121ddf84fe5a76cd739432cea3b61365a9b` |
| P3 / C3 | `feab28f573b973a6b970cef56d1baa35191ab319` |
| C3 title | `feat(spec-decode): add MRV2 draft-window runtime ownership` |
| C3 time | 2026-10-10 11:19:13 +0800 |
| P3 状态 | **FINAL: PASS**（Independent Review 已完成事实裁决） |
| review-fix commit | `16727882744c935d9e899f7775353b57738852bc` |
| review-fix title | `fix(spec-decode): address P3 draft-window review findings` |
| 最终裁决时间 | 2026-10-10 12:14:32 +0800 |
| upstream vLLM 修改 | 无 |
| Attention Window consumer | 无；Attention 仍读取 baseline full context |

本文所有路径和行号均以 review-fix commit 为准。`P3 FINAL: PASS` 只表示 P3
ownership/lifetime/transport/store contract 通过，不是 Feature 完成点，不能宣称 MRV2
`draft_window_size` 已生效。

## 2. P3 解决的问题

P2 能回答“完整 source 在哪里、一个 Window 应读哪些列、这些列是否真实存在”，但 P2
只有 frozen descriptor 和 borrowed FullSource。descriptor 本身没有 tensor backing，也不
证明 backing 在 reader 完成前不会被下一批请求覆盖。

P3 增加五个概念：

1. **generation identity**：把 caller-owned `mapping_epoch`、稳定 request IDs、
   descriptor/valid-count fingerprint、source/provider、phase/step/lane 绑定为一个不可变值。
2. **workspace**：speculator 拥有的固定容量 tensor backing；每代原地重写，不替换 storage。
3. **lease**：声明哪一代独占 workspace，以及最后一个 reader 完成前能否复用。
4. **typed transport**：把同一代的 table、valid counts、device/CPU exact、CPU upper 显式
   聚合；不通过全局变量、ContextVar 或 owner 临时交换传递。
5. **DraftMetadataStore**：独立于 Target store 的 Draft-only entry，并对 generation 与
   nested mutable alias 做验证。

pointer identity 只说明“还是这一块 allocation”。`idx_mapping.copy_(...)` 不改变
`data_ptr()`，所以 pointer、Python `id()`、row number、request count 和 block count 都不能
单独证明 freshness。`mapping_epoch` 是 caller 对 mapping 内容代际的显式承诺；runtime
另外使用内部单调 `generation_id` 防 ABA handle 重用。

## 3. P3 不解决的问题

- 没有修改 upstream `_build_draft_attn_metadata()`；
- 没有把 `DraftMetadataInputs` 交给任何 Attention builder/backend；
- 没有修改 slot mapping、positions、query layout 或 Target metadata；
- 没有 NPU operator correctness 证据；
- 没有 Graph capture/replay binding；
- fake completion token 不证明真实 NPU Async safety；
- 没有 MLA、DSA、SFA、native/recycling、multi-group 或 DFlash2 runtime；
- 没有 TP/DP/PP/PCP/DCP/SP/FlashComm 支持；
- 没有 prefix-cache/function-prefill Window ON 结论；
- 没有进入 P4。

## 4. 修改文件总览

| File | Class / Function | Before | After | Why |
|---|---|---|---|---|
| `vllm_ascend/worker/v2/spec_decode/draft_window.py` | `DraftWindowGenerationIdentity`（1193 起） | P2 只有 pointer-based `DraftWindowSourceIdentity` | immutable epoch/request/descriptor/provider/source/phase identity | 防 reorder、row reuse、in-place mapping rewrite 和 ABA |
| 同上 | `DraftWindowWorkspace`（1269 起） | 无 Window backing | 固定 shape table/count/device exact/CPU exact/upper | 建立 stable-address mutable owner |
| 同上 | `DraftWindowLease`、`_DraftWindowLeasePool`（1494、1529 起） | 无 reader lifetime | 单 lane acquire/pending/retire/reclaim | 防 active backing 覆盖 |
| 同上 | `DraftMetadataInputs`（1613 起） | 无 typed transport | frozen typed workspace views + lease validation | 显式携带 Draft read plane |
| 同上 | `DraftMetadataStore`（1708 起） | 只有 Target store | Draft-only generation entry + mandatory Target alias check | Target/Draft owner 隔离 |
| 同上 | `DraftWindowRuntimeState`、`build_draft_window_runtime_state()`（1751、1922 起） | 无统一 P3 owner | 一个 speculator-owned lifecycle/retirement owner | 原子组合 workspace、pool、store |
| `autoregressive/speculator.py` | `_initialize_draft_window_source_capability()`（91 起） | eligible 时只创建 P2 capability | 先在 local 变量创建 P2 + P3，再原子挂 owner | init 失败不留半初始化状态 |
| `dflash/speculator.py` | 同名 helper（40 起） | 同上 | 同上 | 三类 owner 保持一致 |
| `dspark/speculator.py` | 同名 helper（58 起） | 同上 | 同上 | 三类 owner 保持一致 |
| `tests/ut/spec_decode/test_draft_window_runtime.py` | 23 个 test function / 29 cases | 不存在 | P3 CPU state-machine、freshness、alias、cleanup tests | 独立保护 P3 contract |
| `tests/ut/spec_decode/test_draft_window.py` | owner/policy regressions | 只检查 P2 | 增 P3 allocation spy、atomic init、DFlash2 zero allocation | 保证 P1/P2 Gate 未退化 |

刻意没有修改 `worker/v2/attn_utils.py`。P3 没有 production Attention caller；现在加入
`seq_lens_cpu` seam 会制造无人消费的半接线。P4 应在 upstream live typed hook 确认后，
一次性把 CPU exact 传到 `attn_utils.py:223` 的 shared funnel，并保持默认 `None` baseline。

## 5. P2 结束时的数据流

```text
P1 WindowPlan
    ↓
P2 FullSource (borrowed, read-only)
    ↓
P2 ReadDescriptor (no backing, no lifetime)
    ↓
STOP
```

descriptor 能证明 source coverage，但 reader 若晚于下一批 materialize，它自己无法阻止
storage 被覆盖。

## 6. P3 结束后的数据流

```text
FullSource
    ↓
ReadDescriptor + valid-count fingerprint
    ↓
GenerationIdentity / mapping_epoch
    ↓
DraftWindowLease (lane 0)
    ↓
DraftWindowWorkspace
    ↓
DraftMetadataInputs
    ↓
DraftMetadataStore
    ↓
STOP
```

`STOP` 是真实 phase boundary：**Attention 仍然没有消费这些数据。**

## 7. mapping_epoch 完整例子

```text
same Tensor object
same Tensor pointer

Generation A:
mapping_epoch = 10
mapping       = [17, 93]

idx_mapping.copy_([4, 17])

Generation B:
mapping_epoch = 11
mapping       = [4, 17]
```

`copy_()` 只改 storage 内容，不改 Tensor object，也不改 `data_ptr()`。因此：

- `FullDraftKVSource.bind_batch()` 记录 pointer 只用于 owner/source diagnostics；
- caller 必须为每个 materialized generation 提供严格递增 `mapping_epoch`；
- `DraftWindowGenerationIdentity` 携带 epoch；
- lease、workspace bound identity、`DraftMetadataInputs` 和 store entry 都携带同一 identity；
- `validate_for()`、store `read()`、retire/abort 都比较完整 identity；
- A retire 后，即使 workspace 地址被 B 复用，A lease 已是 `RETIRED`，A typed inputs
  不能再次通过验证；
- 传入 epoch 11 的 expected identity 读取 A entry 会立即报 generation mismatch，不会
  自动更新 A，也不会 silent rebind。

对应回归是
`test_same_mapping_tensor_rewrite_cannot_reuse_generation_state()`。

## 8. Generation Identity

| Field | Meaning | Creator | Consumer | Lifetime | Why needed |
|---|---|---|---|---|---|
| `generation_id` | runtime 内部不复用序号 | `DraftWindowRuntimeState` | lease/inputs/store | runtime lifetime 内单调 | 防 ABA stale handle |
| `mapping_epoch` | caller-owned mapping 内容代际 | future P4 caller | 全链路 validator | 一个 materialized generation | pointer 不足以证明 freshness |
| `ordered_request_fingerprint` | ordered stable request IDs | future P4 从 `InputBatch.req_ids` 取 | inputs/store/read | generation | 检测 reorder/finish/add/row replacement |
| `actual_request_count` | active rows | runtime | workspace/typed inputs | generation | 区分 active 与 padding |
| `padded_request_count` | transport/capture padded rows | caller | workspace/typed inputs | generation | deterministic inert tail |
| `normalized_method` | P1 normalized route | P2 inventory | diagnostics/future P4 | owner lifetime | 防 route 串用 |
| `global_group_id` | executable Draft gid | P2 provider | source/workspace | owner lifetime | 不把 local index 当 global gid |
| `read_descriptor_fingerprint` | 每 row 的 gid/start/offset/required/safe/valid/width tuple | caller 从 P2 descriptor 传入 | workspace/identity validation | generation | 绑定 table slice 与 valid-count snapshot |
| `provider_id` | 当前 provider instance identity | runtime | identity comparison | owner lifetime | 防另一个 provider 的 descriptor 串用；不是 epoch 替代 |
| `provider_version` | provider contract version，当前为 1 | runtime | identity comparison | code-version contract | 为以后 layout ABI 演进留显式 Gate |
| `source_identity` | canonical owner + table/count/mapping pointers | bound FullSource | workspace/identity | generation | 检测 owner replacement并提供诊断；pointer不是 freshness |
| `execution_lane` | workspace lane，P3 只允许 0 | caller | lease pool | generation | 明确 serialized，不冒充 Async |
| `phase` | `PROPOSAL` / `STEP` | caller | future binding | generation | 防不同 metadata phase 串用 |
| `step` | proposal step identity | caller | future binding | generation | 防 Eagle3 step state串用 |

这里没有用“一个巨大 runtime context”打包所有未来 backend 状态。只记录当前 single-group
dense candidate 证明 freshness 所必需的字段。

## 9. Request Fingerprint

假设 persistent request slots：

```text
row 17 = A
row 93 = B
row  4 = C

batch1 request IDs = [B, A]
batch1 idx_mapping = [93, 17]

batch2 request IDs = [C, A]
batch2 idx_mapping = [4, 17]
```

即使两个 batch 的 request count、table pointer 或 block count 相同，ordered stable IDs 与
epoch 都不同，batch1 identity 不能读取 batch2 backing。

再考虑 A finished，D 复用 persistent row 17：

```text
row 17 before = A
row 17 after  = D
```

row number 没变，但 request identity 从 A 变成 D。只保存 row 17 会发生 ABA；保存
`InputBatch.req_ids` 中的 stable request ID 能检测 replacement。P3 API 不自行发明第二套
request ID；P4 必须从当前 upstream `input_batch.py:45` 的 `req_ids` 传入。

## 10. Workspace 详解

P3 不支持 resize。初始化时使用 P2 candidate 的 canonical table request capacity 与 provider
column capacity 一次分配；任何超限都 deterministic error。没有 active reader 时也不替换
storage。这是最小且最容易审计的地址契约；未来若 Graph 需要 descriptor-specific backing，
必须单独设计，不能偷偷 resize 此 lane。

| Buffer | Device / dtype | Shape / capacity | Owner | Allocated when | Written by | Read by now | Reset | Future P4 consumer |
|---|---|---|---|---|---|---|---|---|
| `window_block_table` | canonical table device / int32 | `[max_num_reqs, provider_capacity_columns]` | workspace | eligible P2 capability 完成后 | `Workspace.materialize()` copy full-source slices | typed inputs tests only | failed materialize or retired completion | Draft Attention read table |
| `valid_num_blocks` | canonical count device / int32 | `[max_num_reqs]` | workspace | 同上 | P2 gather with same bound mapping | typed inputs/descriptor validation | 同上 | source coverage snapshot/diagnostic |
| `device_window_exact` | table device / int32 | `[max_num_reqs]` | workspace | 同上 | active rows `copy_()` | typed inputs tests only | 同上 | Draft Attention device lengths |
| `cpu_window_exact` | CPU / int32 | `[max_num_reqs]` | workspace | 同上 | active rows `copy_()` | typed inputs tests only | 同上 | Ascend exact CPU seam in P4 |
| `cpu_window_upper` | CPU / int32 | `[max_num_reqs]` | workspace | 同上 | active rows `copy_()` | typed inputs tests only | 同上 | metadata planning upper in P4 |
| descriptor fingerprint | Python immutable tuple | one descriptor per active row | generation identity | materialize call | caller/P2 provider | workspace validator | object retirement | P4 binding identity |

没有额外 scratch buffer：当前 CPU/PyTorch direct-prefix materializer 可以直接从 canonical row
copy 到固定 backing。没有为 DSA/SFA/MLA 等未来 backend 预分配未经验证的 derived buffer。

每次 materialize 先验证 capacity、shape、dtype、device、exact/upper 和 alias，再清零全部
workspace；只写 active rows，所有 padded rows、row tail 与旧 batch tail 保持 0。输入 length
不得 alias workspace，避免 `_zero_all()` 破坏输入。

## 11. Lease 状态机

```text
FREE / workspace unbound
        |
        | acquire(identity, lane=0)
        v
    ACQUIRED
      |   \
      |    \ retire(no reader)
      |     ----------------------> RETIRED handle + FREE lane
      |
      | mark_reader_pending(token)
      v
 READER_PENDING
      |
      | retire(token incomplete)
      v
 RETIRED_PENDING  -- token complete, observed at acquire --> RETIRED + FREE
      |
      +-- acquire while incomplete --> deterministic error, no overwrite
```

- `DraftWindowRuntimeState` 是唯一 retirement owner；`lease.retire()` 也回调该 owner，确保
  store、active inputs 和 pool 一起退休。
- double acquire 在 lane 占用时失败。
- wrong-generation retire 在任何清理前失败，active entry 保留。
- double retire / stale handle 失败，不是 silent idempotent。
- P3 只有 lane 0；lane 非 0 为 `NotImplementedError`。
- 固定一条 lane 只证明 serialized lifecycle，不代表 Async supported。
- pressure 策略是不等待、不扩容、确定报错；绝不 blind round-robin。

## 12. Fake Event vs NPU Event

| CPU fake completion test 证明 | 仍不能证明 |
|---|---|
| incomplete token 阻止 lane reuse | NPU event 是否记录在正确 stream |
| delayed token 完成后可安全 reclaim | device kernel 是否真的完成全部 table/length reads |
| pending 时 workspace 内容不被覆盖 | ACL Graph captured operand 是否指向该 backing |
| retire/ABA/wrong generation 状态机正确 | 多 stream、Async scheduler、PP overlap correctness |
| exception guard 仍尊重 pending token | event query 的 NPU error/teardown behavior |

所以文档只称“CPU lease state machine 已验证”，不称“async-safe”。Async Gate 仍 BLOCKED。

## 13. Typed DraftMetadataInputs

| Field | Producer | Meaning | Exact / upper / capacity | Device |
|---|---|---|---|---|
| `identity` | runtime | 完整 generation freshness | identity | host object |
| `window_block_table` | workspace view | padded rows的 narrow read table | fixed column capacity | source device |
| `valid_num_blocks` | workspace gather | 同 mapping generation 的 valid snapshot | exact source count | source device |
| `device_window_exact` | workspace copy | active Window exact lengths | exact | source device |
| `cpu_window_exact` | workspace copy | host exact lengths | exact | CPU |
| `cpu_window_upper` | workspace copy | planning/apply upper | upper，逐 row `>= exact` | CPU |
| `active_table_columns` | materializer | 每 active row 实际写入 columns | active extent | host tuple |
| `actual_request_count` | identity | active rows | exact count | host int |
| `padded_request_count` | identity | transport rows | padded count | host int |
| `table_capacity_columns` | provider/workspace | 固定 backing width | capacity | host int |
| `_lease` | runtime | 验证 backing 尚属于该代 | lifetime | host object |

dataclass 是 frozen；tensor 本身不是语言级 immutable，所以任何 consumer 读取前必须调用
`validate_for(expected_identity)`，并由 lease 阻止 workspace reuse。

**绝对不在 typed inputs 里的字段：**

- `positions`；
- `query_start_loc` 或 query layout；
- `slot_mapping`；
- Target metadata / Target store；
- canonical full block-table owner；
- module-global/context-local transport。

## 14. DraftMetadataStore vs Target Store

```text
Target ModelState
    ↓
model_state.attn_metadata       (P3 never writes or owns this)

Speculator
    ↓
_draft_window_runtime_state
    ↓
DraftMetadataStore             (one generation-scoped Draft entry)
```

`publish_metadata(..., target_metadata=...)` 的 Target 参数现在是 mandatory keyword，显式
`None` 也会报错并清理 generation；不能通过省略参数关闭隔离检查。检查器遍历
dict/list/set/dataclass、普通 `__dict__` object、非 dataclass `__slots__` holder 和 Tensor
storage。Draft 与 Target 任一受支持的 nested mutable object/storage 相交就报错并清理
Draft generation。store 不保存 Target reference。测试不仅检查 `draft is not target`，还
覆盖 slotted holder、修改 Draft nested tensor，并验证 Target root identity、nested list
identity、tensor identity和内容全部不变。P4 必须传真实
`model_state.attn_metadata`，不能用空占位对象冒充 Target owner。

store 规则：

- 一个 active entry，不允许 overwrite/repeated publish；第二次 publish 失败并 abort 该代；
- read 必须传完整 expected identity；
- stale epoch/request/descriptor/source identity 全部失败；
- retire/reset 后 entry 清除，旧 entry 不可读；
- store 不注册 Graph、不使用 module global；
- P3 只存测试 payload，未构造真实 Attention metadata。

## 15. Exception / Cleanup

| Failure | Cleanup owner | Behavior |
|---|---|---|
| materialize validation/copy 异常 | `DraftWindowRuntimeState.materialize()` | 自动 retire acquired lease、清零 workspace；epoch 已消费，下一代必须更大 |
| store publish / alias / overwrite 异常 | `publish_metadata()` | 自动 discard entry、retire/pend lease |
| caller/reader body 异常 | `generation_guard()` | 自动 abort；若已有 incomplete reader token，lane 保持 pending，不提前复用 |
| normal reader 完成 | caller future P4 + runtime | 先 bind completion token，再 `retire_generation()`；完成前不复用 |
| retire token query 异常 | lease pool | store 已 discard；lease 保持 `READER_PENDING`、lane/active inputs仍归原 generation，不覆盖 backing；token恢复后可重试 retire |
| stale generation / wrong retire | validator | 在修改 store/workspace 前失败；stale caller无 cleanup ownership |
| owner init allocation异常 | 三个 speculator helper | P2 capability/P3 state 都先保存在 locals；不挂半初始化 attribute |

P4 必须将真实 forward/dispatch 包在同等 `try/finally` 或 `generation_guard()` 边界内。

## 16. 修改前后执行流程

### Before P3

```text
set_attn
  -> P2 capability (inventory + borrowed FullSource + provider)
  -> normal baseline propose/build/forward
```

### After P3

```text
set_attn
  -> build P2 capability locally
  -> allocate P3 runtime/workspace/store locally
  -> atomically attach both to eligible speculator
  -> normal baseline propose/build/forward (unchanged)

P3 test-only/manual future call:
  runtime.materialize(epoch, req_ids, mapping, descriptors, lengths)
  -> acquire lease
  -> bind FullSource to mapping
  -> rewrite fixed workspace
  -> return typed inputs
  -> optional Draft-only store
  -> completion + retire
```

没有 production propose/build method 调用 `runtime.materialize()`；这是刻意的 P3 stop。

## 17. Runtime Effect

```text
P3 before:
Attention reads full.

P3 after:
Attention still reads full.
```

P3 新增的是 backing、ownership、freshness、lifetime、typed transport 和 Draft-only store。
它没有新增实际 Window Attention read。C1～C3 仍只能作为 held feature branch infrastructure；
P4 Gate 关闭前不能单独发布为“功能已生效”。

## 18. Tests

P3 新文件最终有 23 个 test function、29 个 collected case；与 P1/P2/DFlash2 targeted
合计 `166 passed`。

| Test / family | What it proves | Why it matters | Failure meaning |
|---|---|---|---|
| workspace materialize / reuse | fixed allocation、stable pointer、active copy、tail/padding clear | 防 stale rows 和 hidden reallocation | backing ownership错误 |
| capacity failures | request/column pressure deterministic error且下一 epoch可恢复 | 不覆盖 active lane | resize/pressure contract破坏 |
| same-pointer rewrite | epoch 10 `[17,93]` 到 epoch 11 `[4,17]` 使 A lease/inputs/store stale | mandatory P3 exit | pointer被误当freshness |
| reorder/finish/add/replacement | ordered stable IDs进入 identity | row index不等于request | 串请求/ABA风险 |
| descriptor/valid snapshot | descriptor tuple和current gather都参与验证 | table slice必须与count同代 | stale source coverage进入consumer |
| monotonic epoch/ABA | 重复 epoch拒绝、internal generation不复用 | caller contract可审计 | silent rebind |
| delayed fake event | incomplete reader阻止复用且内容不变 | lifetime correctness | in-flight overwrite |
| completion query exception | query异常后lane保持归原代，恢复后可重试retire | fail-closed不能变成leak或early reuse | backing提前覆盖或永久不可恢复 |
| wrong/double retire | stale owner不能清 active generation | unique retirement owner | entry被错误清理 |
| exception cleanup | materialize/store/reader异常释放或安全pending | error path不能泄漏/覆盖 | lane死锁或early reuse |
| typed validation | frozen、shape/dtype/device/exact/upper/padding/alias | typed contract不是裸dict | P4输入可混代 |
| Target isolation | root/nested/tensor storage不alias且Target内容不变 | Final I01 | Draft操作污染Target |
| mandatory Target input / slotted alias | 省略/None被拒，slot-only可达Tensor仍被发现 | 隔离检查不能由caller无意关闭 | P4过滤Target对象后可静默污染 |
| empty batch | 0 active/0 padded生成空views并正常retire | 明确边界状态且无stale残留 | 空批生命周期未定义 |
| owner allocation spies | OFF/forced/DFlash2不分配，eligible原子挂P3 | policy boundary | unsupported route创建P3 state |

Test-first 记录：首次运行新 test 文件在 collection 阶段因 P3 symbols 尚不存在而失败；首版
实现后有 6 个 regression 暴露“pre-bind materialize failure 的 cleanup 错误要求 workspace
已绑定”。修正为 lease 已证明 lane ownership时允许清理 unbound workspace；其他已绑定
identity仍硬拒绝。Independent Review 后先加入 F-01/F-06 regression：原 C3 聚焦运行结果
为 `2 failed, 2 passed`，失败项正是“省略 Target 参数未拒绝”和“slotted holder alias未发现”；
修复后四项均通过。随后所有 P3 tests 通过。

### 最终命令结果

| Scope | Result | Limitation |
|---|---|---|
| P3 runtime file | `29 passed, 1 warning` | CPU state machine；fake token不是NPU event |
| P1/P2/P3 targeted + DFlash2 | `166 passed, 1 warning` | CPU/static |
| `tests/ut/spec_decode` excluding VWN host-only failure file | `392 passed, 13 skipped, 2 subtests passed` | 无 NPU backend |
| relevant BlockTables / attn-utils / extract-hidden-state | `52 passed` | CPU/static |
| full `tests/ut/spec_decode` | `394 passed, 13 skipped, 7 failed, 2 subtests passed` | 7 个 VWN failures均为 `Invalid attention backend for None`；P2 Final、原C3与DeepSeek review均复现同类，stack不经过P3；不是PASS |
| Ruff check / format / compileall / diff-check | PASS | changed files |
| targeted Mypy P3 + DFlash/DSpark | PASS | `--follow-imports=skip` |
| AR owner Mypy | 4 个既有 `issubclass(type | None)` errors | 与 P2记录相同，P3行无新增 error |
| selected repository hooks | PASS | Ruff、format、codespell、typos、filename、package、logger、forbidden-import、boolean-context、long-function、symbolic-meta、suggestion |
| full pre-commit | 未完成 | actionlint Go dependencies从 `proxy.golang.org` 下载超时；gitleaks缺binary且本机无`wget`；不是PASS |
| NPU / Graph / Async E2E | 未运行 | 保持 Gate open/blocked |

唯一常规 warning 是 editable vLLM 缺 `_version`，与 C3 无关。

## 19. P3 Invariants

- [x] canonical `FullDraftKVSource` owner/tensor 不修改；只读 slice copy 到新 backing；
- [x] slot mapping 未修改，`compute_slot_mappings` 路径未接触；
- [x] positions/query layout 未修改；
- [x] Target store 未写；Target参数mandatory，nested mutable/Tensor/slotted-holder alias被拒绝；
- [x] 无 module global、ContextVar、process singleton transport；
- [x] `mapping_epoch` 是 mandatory caller input，严格单调；
- [x] pointer/Python object identity 不替代 epoch；
- [x] descriptor与 valid-count snapshot 进入 immutable identity；
- [x] stale generation、wrong generation、ABA handle 被拒绝；
- [x] active/incomplete reader backing 不覆盖；
- [x] active/tail/padding每代确定性清零；
- [x] CONFIG_OFF / FORCED_OFF 无 P3 state/allocation；
- [x] P2 unsupported capability/DFlash2 在 workspace builder前失败；
- [x] fixed capacity，无隐式 resize；
- [x] single lane明确不代表 Async；
- [x] P4 Attention binding未实现；
- [x] Graph、complex backend、parallel Gate未打开。

## 20. P1 / P2 / P3 / P4 关系

```text
P1 policy + scalar math
    ↓
谁允许、S/E/V/capacity 是什么
    ↓
P2 source + inventory + provider
    ↓
真实 Draft consumer是谁、full source在哪、读哪些列、source够不够
    ↓
P3 ownership + freshness + lifetime + transport
    ↓
这些列放在哪里、哪一代拥有、何时可复用、怎样显式传递
    ↓
P4 real Attention consumer
    ↓
typed read inputs进入live builder/backend（尚未实现）
```

P3 不更改 P1/P2 数学和 provider，不提前复制 P4 主流程。

## 21. 开发者阅读顺序

1. `draft_window.py:192-293`：P2 `SourceIdentity` / `FullDraftKVSource`，理解 pointer 限制；
2. `draft_window.py:295-475`：P2 descriptor/provider；
3. `draft_window.py:1193-1252`：phase 与完整 generation identity；
4. `draft_window.py:1269-1491`：workspace 分配、materialize、tail reset；
5. `draft_window.py:1494-1610`：lease 与 single-lane pool 状态机；
6. `draft_window.py:1613-1700`：typed inputs validation；
7. `draft_window.py:1708-1748`：DraftMetadataStore mandatory Target隔离；
8. `draft_window.py:1751-1919`：runtime orchestration、epoch contract、exception/retire；
9. 三个 speculator owner helper：原子挂载且无 Attention consumption；
10. `test_draft_window_runtime.py:161-664`：按 workspace→epoch→lease→store 顺序读 oracle。

## 22. P3 完成后的心智模型

1. FullSource 永远是 canonical full owner 的 borrowed read source。
2. descriptor 是不可变“读哪一段”，不是 backing。
3. mapping pointer 不新鲜；caller 必须提供新 epoch。
4. request fingerprint 使用稳定 request IDs，不使用 row 代替。
5. 一个 runtime 只有一条 serialized lane 和一个 workspace。
6. materialize 原地重写全部 active/tail/padding，不替换 storage。
7. typed inputs 只是受 lease 保护的 workspace views。
8. Draft store 与 Target store 是两棵 owner tree，nested storage也不能共享。
9. reader completion 前，retire只进入 pending，下一代不能覆盖。
10. 到 P3 为止，真实 Attention 仍 full；P4 才是首次 consumer 接线。

## 23. Open Gates

| Gate | P3 后状态 | 关闭条件 |
|---|---|---|
| G-LIVE-HOOK | OPEN / P4 blocker | upstream vendor-neutral read-input hook + Ascend exact CPU seam review |
| G-GQA-EAGER | OPEN / P4 blocker | real single-group dense NPU physical read-set oracle |
| G-AR-STEP | OPEN / Eagle3 blocker | first pass独立Draft metadata + 每step static-K identity/read correctness |
| Graph | BLOCKED / fail closed | capture/replay binding、actual operand trace、A/B/A NPU |
| NPU | OPEN | real kernel correctness、stream/event lifetime |
| Async | BLOCKED | real scheduler generations、multi-lane/event stress；CPU fake event不足 |
| Prefix cache / function prefill | OPEN | Window ON combination-specific E2E；OFF regression已保留 |
| Backend extensions | BLOCKED PER ROUTE | MLA/DSA/SFA/native/recycling各自 provider、derived-state lease、operator oracle |
| Parallel | BLOCKED | TP/DP/PP/PCP/DCP/SP/FlashComm逐项 proof |
| DFlash2 | BLOCKED | 独立 runtime/capture证据；P2/P3 allocation前 fail closed |
| Feature release | HOLD | 至少一个 P4 eligible Attention consumer真正接通并通过 Gate |
| P4 epoch provenance | OPEN / P4 blocker | production caller从同一batch generation产生epoch和ordered req IDs；mapping变化测试证明必增 |
| P4 validation boundary | OPEN / P4 blocker | 在唯一read-input adapter消费前调用`validate_for(expected_identity)`并有spy/regression |
| P4 host-sync policy | OPEN / P4 blocker | 删除/隔离每proposal D2H与device tail sync，或以NPU trace证明合约；Graph继续fail closed |

P3 没有 architecture escalation，也没有 phase boundary violation。Independent Review 与事实
裁决已完成；P4 仍需单独 Implementation Review，不能由本结论自动开始。

# P3 Review Resolution

## Review Metadata

| Item | Value |
|---|---|
| DeepSeek review | `Independent Source Review — MRV2 Draft Window P3`，针对 C3 `feab28f573b973a6b970cef56d1baa35191ab319` |
| P3原commit | `feab28f573b973a6b970cef56d1baa35191ab319` |
| review-fix commit | `16727882744c935d9e899f7775353b57738852bc` |
| 裁决时间 | 2026-10-10 12:14:32 +0800 |
| Architecture escalation | 无 |

## Finding Statistics

| Resolution | Count |
|---|---:|
| ACCEPTED | 1 |
| PARTIALLY_ACCEPTED | 3 |
| REJECTED | 0 |
| DEFERRED | 2 |
| OPTIONAL_STYLE_ONLY | 2 |
| ARCHITECTURE_ESCALATION | 0 |

## Resolution Table

| ID | Severity | Finding | Resolution | Evidence | Code/Test/Doc Change |
|---|---|---|---|---|---|
| F-01 | Major | Target alias guard可省略 | **ACCEPTED** | C3 `DraftMetadataStore.publish()`只在非None时检查；review-before regression确实未抛错 | `target_metadata`改mandatory且None拒绝；新增missing/None test；P4必须传真实Target store |
| F-02 | Minor | epoch语义仍由caller attested | **PARTIALLY_ACCEPTED** | runtime在`1792-1796`只可验证类型/严格单调，无法从pointer推导语义；这与Frozen caller-owned契约一致 | API doc明确epoch必须对应本次mapping；P4 production provenance与req-id change test列为blocker，不在P3改成runtime自造epoch |
| F-03 | Minor | validation含device-to-host/device sync | **DEFERRED_TO_P4** | `1369-1373`的`.cpu()`和`1689` device `count_nonzero()`静态成立；P3无production caller | 不在无consumer时猜测删除正确性检查；P4启动前决定无hot-D2H策略并以trace测试，Graph保持fail closed |
| F-04 | Minor | stale workspace view需consumer主动validate | **DEFERRED_TO_P4** | typed tensors是固定workspace views；`validate_for()`在`1696-1699`验证full identity/lease，但Python无法撤销已借出的Tensor引用 | P4只允许一个消费adapter，在构建Attention read inputs前validate并加spy；当前无consumer、无误enable |
| F-05 | Minor | runtime workspace/store属性公开 | **OPTIONAL_STYLE_ONLY** | 当前runtime为package-internal且production只有builder持有；改成下划线/property仍不能防Python调用者写Tensor | 不改代码；文档保持owner contract，P4不得直接写backing/store internals |
| F-06 | Minor | alias traversal漏非dataclass slots/buffer-like | **PARTIALLY_ACCEPTED** | 当前Ascend metadata是dataclass，但slot-only holder red test证明Tensor alias可漏；任意NumPy/buffer不是当前typed metadata contract | 增MRO `__slots__` traversal与regression；未知buffer-like backend进入extension gate，不无证据扩张generic storage协议 |
| F-07 | Minor | 部分测试为identity field isolation；缺empty/token-error | **PARTIALLY_ACCEPTED** | synthetic `replace()`确实不是scheduler场景，但用于隔离fingerprint字段；真实same-pointer/stale-handle场景已另测。empty/token-error原来未覆盖 | 保留field-level contract tests；新增empty batch与raising-token状态转换/retry tests；精确更新异常文档 |
| F-08 | Suggestion | retire path bare assert在`-O`消失 | **OPTIONAL_STYLE_ONLY** | `mark_reader_pending()`先写token再切state；只有该state才能到两处assert，当前API无token-None可达路径 | 无正确性改动；若未来状态可反序列化/外部恢复，再改显式corruption error |

## Final Diff Summary

| File | Review前 | Review后 |
|---|---|---|
| `vllm_ascend/worker/v2/spec_decode/draft_window.py` | Target check optional；generic object只遍历`__dict__`；epoch API说明较短 | Target mandatory/None拒绝；遍历MRO slots；materialize doc写明epoch provenance contract |
| `tests/ut/spec_decode/test_draft_window_runtime.py` | 19 functions / 25 cases | 23 functions / 29 cases；增加mandatory Target、slotted alias、empty batch、completion-query exception/retry |
| 本说明文档 | C3 pre-review状态 | 同步final code、裁决、测试、P4 gates与review-fix SHA |
| Implementation Plan | P3等待review | P3 Final PASS；写入P4三项新prerequisite与remaining blockers |

## Final Tests

| Command / Scope | Result | Limitation |
|---|---|---|
| review-before 4-case regression | `2 failed, 2 passed` | 原C3红测；失败精确对应F-01和F-06 |
| same 4 cases after fix | `4 passed` | CPU/static |
| P3 runtime file | `29 passed` | fake completion token，不证明NPU event |
| P1/P2/P3 targeted + DFlash2 | `166 passed` | CPU/static |
| spec_decode excluding VWN | `392 passed, 13 skipped, 2 subtests passed` | 无NPU backend |
| relevant BlockTables/attn-utils/worker | `52 passed` | CPU/static |
| full spec_decode | `394 passed, 13 skipped, 7 failed, 2 subtests passed` | 7个既有VWN host failures；与P2/C3同类且stack不经过P3；不是PASS |
| Ruff check / format / compileall / diff-check | PASS | final changed files |
| Mypy changed files + DFlash/DSpark | PASS | `--follow-imports=skip --check-untyped-defs` |
| AR Mypy | 4 existing errors | `issubclass(type[Any] | None)`；P2/C3既有，review-fix未改AR |
| selected pre-commit hooks | PASS | 12项本机可执行hook |
| full pre-commit | NOT COMPLETED | actionlint Go proxy timeout；gitleaks缺binary/wget；不是PASS |

## Final P3 Invariant Audit

- [x] P1 policy与P2 FullSource/provider未修改；
- [x] CONFIG_OFF/FORCED_OFF/unsupported route零P3 state；
- [x] mapping_epoch mandatory、strictly monotonic并贯穿identity/lease/workspace/inputs/store；
- [x] same-pointer mapping rewrite、request reorder/replacement与ABA stale handle被拒；
- [x] workspace不alias canonical table/count，active/tail/padding确定性重写；
- [x] active/incomplete reader backing不覆盖，completion query异常也保留lane ownership；
- [x] stale lease/wrong retire在修改active state前拒绝；
- [x] Target参数不可省略，nested mutable/Tensor/slotted-holder alias拒绝；
- [x] 无module global、ContextVar或shared owner swap；
- [x] slot mapping、positions、query layout、Target store、canonical FullSource untouched；
- [x] 无P4 Attention binding、Graph hook或NPU correctness claim。

## Final Runtime Effect

```text
P3 Final:
Attention still reads baseline full context.
```

P3 Final只增加安全的Draft read-plane基础设施，不是用户可见Window ON。

## Remaining Gates

- `G-LIVE-HOOK`：OPEN / P4 blocker；
- `G-GQA-EAGER`：OPEN / P4 blocker；
- `G-AR-STEP`：OPEN / Eagle3 blocker；
- P4 epoch provenance：OPEN；
- P4 single validate-for consumption boundary：OPEN；
- P4 hot-D2H/device-sync policy：OPEN；
- Graph、Async、backend extensions、parallel：BLOCKED / fail closed；
- NPU correctness：未验证；
- Feature release：HOLD。

## Developer Mental Model

1. C3建立owner/lifetime；review-fix只封死可省略的Target隔离并补alias边界。
2. epoch是caller对同一batch mapping generation的承诺，不是pointer别名。
3. runtime只接受严格递增epoch；P4还必须证明production epoch来源正确。
4. workspace view只在lease有效期内可借用；retire后旧Tensor引用没有消费权。
5. P4必须在唯一adapter消费前调用`validate_for()`。
6. completion查询异常时不释放lane；恢复后由同一owner重试retire。
7. Draft publish必须同时看到真实Target metadata用于disjointness检查。
8. 当前`.cpu()`/device-tail validation没有live caller；P4不得直接带入热路径或Graph。
9. P3 CPU tests不证明NPU event、Async、Graph或物理read set。
10. Attention到P3 Final仍读取full context。
