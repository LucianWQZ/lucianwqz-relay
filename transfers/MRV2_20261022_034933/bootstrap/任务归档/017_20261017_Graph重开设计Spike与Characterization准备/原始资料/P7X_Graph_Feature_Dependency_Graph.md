# P7-X Graph Feature Dependency Graph

## 1. Source-derived Dependency DAG

```text
P1–P3 policy/source/generation/workspace
                │
                ▼
P5/P6 provider + capture/runtime identity + read/write invariant
                │
                ▼
c439 Ascend-owned DFlash capture adapter
                │
                ▼
8cb4 base candidate + G1–G5 recorder
                │
                ├───────────────┬────────────────┬────────────────┬─────────────────┐
                ▼               ▼                ▼                ▼                 ▼
          TP/rank identity  Prefix resident  Eagle3 adapter   DSA adapter       MLA adapter
                │               │                │                │                 │
                │               ├──────┐         │                ├──────┐          │
                │               ▼      ▼         ▼                ▼      ▼          ▼
                │           Chunked  Mixed   Eagle3 AR       DSA Async DSA-CP   MLA multi-group
                │               │      │         │                       │
                ├───────────────┴──┬───┴─────────┴───────────────────────┤
                ▼                  ▼                                     ▼
          TP16 NPU oracle     Multi-request identity              CP/rank-local oracle
                │                  │                                     │
                └──────────────────┴──────────────┬──────────────────────┘
                                                  ▼
                                  Async Graph completion/lane bank
                                                  │
                                                  ▼
                                     multi-group/heterogeneous compose
```

SFA/indexer/QLI分支独立于MLA/FIA更新机制：

```text
base identity/provider core
    → SFA main persistent carrier
    → indexer/top-k/QLI persistent carrier
    → shared generation + completion
```

DFlash2不在该DAG内，因为当前method自身Graph prerequisite缺失；必须先有DFlash2 Graph支持，Window adapter才有入口。

## 2. Hard Dependencies

| Feature | Hard dependency | Why |
|---|---|---|
| 所有Graph feature | base G1–G5 | capture地址、物理读取、timeline未证前扩展会放大未知量 |
| TP16 | per-rank identity + base carrier | provider天然per-process，但fingerprint必须防rank错绑 |
| Async | sync carrier for same backend | completion token必须绑定真实Graph replay消费 |
| Prefix | resident snapshot + eviction hold | table content可能因residency改变，不能只看Window math |
| Chunked | phase plan + FULL_DECODE_ONLY participation | chunk本身可能eager，但会改变下一decode source/epoch |
| Mixed | chunked policy + capture bucket semantics | 同batch不同phase，uniform decode descriptor不足 |
| Multi-request | request fingerprint + mapping_epoch | storage固定但row语义可变 |
| DSA | DSA derived persistent backing | backend update是no-op，不能复用FIA task-rebind |
| DSA-CP | DSA + global→local CP projection | local seq/index/SAS依赖global logicalWindow |
| SFA/indexer | SFA-specific stable derived bank | main/indexer均可能是captured operand，update no-op |
| MLA | MLA schema adapter | update存在但carrier字段不同于FIA |
| Multi-group | every participating gid adapter | one generation must atomically bind N consumers |
| Eagle3 | AR capture adapter + per-step bank | 不经过DFlash helper且一个proposal有多个E_s |

## 3. Work That Can Proceed in Parallel after G1–G5

以下源码实现彼此没有hard dependency，可并行：

- TP/rank-aware fingerprint和per-rank provider tests；
- sync Prefix resident epoch/lifetime；
- Eagle3 capture adapter；
- DSA stable SAS/SWA carrier；
- MLA-specific task-rebind adapter；
- multi-group provider API的纯typed扩展（保持所有runtime gate关闭）。

以下不应提前并行：

- Async必须等待对应backend同步carrier成立；
- DSA-CP必须等待DSA carrier字段稳定；
- mixed Graph必须先有owner对fallback/支持范围的决策；
- heterogeneous multi-group必须等各backend adapter都能同generation提交；
- SFA indexer/QLI要先明确operator capture operand与completion owner。

## 4. Device Campaign Dependencies

```text
G1 capture address FAIL → stop all positive Graph cases
G1–G5 base PASS
    ├→ G6-TP independent
    ├→ G6-Prefix independent
    ├→ G6-Eagle3 independent after adapter
    ├→ G6-DSA independent after adapter
    └→ G6-MLA independent after adapter

One G6 branch FAIL
    → record branch failure
    → continue unrelated branches
```

Async、DSA-CP和multi-group是第二层组合campaign，不应与base G1–G5混在同一首次debug run里。

## 5. Critical Path

最短产品路径（single-card FIA DFlash/DSpark）：

```text
base G1–G5 NPU
→ local adjudication/fix if needed
→ clean NPU confirmation + profiler
→ owner review
```

TP16 mandatory路径：

```text
base G1–G5
→ rank-aware typed contract/code
→ per-rank G6-TP NPU
→ TP16 A/B/A + slot/write + performance
```

完整Graph Feature路径：

```text
base evidence
→ parallel adapters
→ batch G6 campaign
→ combination layer (Async/DSA-CP/multi-group/mixed)
→ final NPU/performance/release audit
```

## 6. Gates That Stay Closed

无论设计成熟度如何，当前公开Gate仍拒绝：FULL、FULL_DECODE_ONLY、PIECEWISE下的Window ON。`8cb4bed`只通过严格internal flag进入base characterization，不能作为支持矩阵中的SUPPORTED/NPU_VERIFIED。
