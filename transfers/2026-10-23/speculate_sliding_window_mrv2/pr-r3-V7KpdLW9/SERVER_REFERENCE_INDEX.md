# 服务器 PR 参考资料导航

- 生成时间：2026-10-23T01:20+08:00
- 生成机器：node-39-101（容器，root）
- 资料根：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr`
- 任务目录：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/PR_服务器开发交接_20261022_170641_0800_c0d3`

> `reference/pr` 只保存参考资料与原始证据。
> **`dev/pr` 在本轮之前已存在且为空目录，本轮未向其中写入任何内容、未恢复代码**；
> 代码恢复留待下一轮显式授权的开发接管任务。

## 1. 关键绝对路径

| 用途 | 绝对路径 |
|---|---|
| 原始冻结 payload | `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/PR_服务器开发交接_20261022_170641_0800_c0d3` |
| 四附件缓存 | `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/发布附件缓存/PR_服务器开发交接_20261022_170641_0800_c0d3` |
| 发布补充材料 | `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/发布补充/PR_服务器开发交接_20261022_170641_0800_c0d3` |
| 接收回执 | `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/接收回执/PR_服务器开发交接_20261022_170641_0800_c0d3` |
| 本轮接收证据 | `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/接收工作/pr-r3-V7KpdLW9` |

## 2. 推荐阅读顺序（与归档 00/05 一致）

1. `00_先读这里.md`
2. `01_最终需求与验收范围.md` + `REQUIREMENT_MATRIX.csv`
3. `02_PR任务时间线与当前有效链路.md`
4. `03_代码起点裁决.md` + `CODE_STATE.json`
5. `04_架构兼容与待解决问题.md`
6. `05_服务器接管说明.md` + `NEXT_SESSION_HANDOFF.json`
7. `服务器恢复入口模板/CURRENT_STATE.md`、`TASK_QUEUE.md`、`OPEN_QUESTIONS.md`、`DECISIONS.md`、`RESOURCE_CONTRACT.template.json`
8. `代码恢复材料/README_恢复代码.md`
9. 只在具体问题需要时按 `DOCUMENT_CATALOG.jsonl` 打开原始证据

## 3. 六阶段任务导航（`TASK_INDEX.json`，tasks=6）

| 阶段 | 标题 | 归档目录（相对任务根） |
|---|---|---|
| T01 | 非Graph历史审计与迁移输入 | `任务归档/001_20261020_非Graph历史审计与需求证据` |
| T02 | 非Graph迁移实现与首版服务器输入 | `任务归档/002_20261021_非Graph迁移实现与Host验证` |
| T03 | b013719候选冻结与本地收尾 | `任务归档/003_20261021_候选冻结与本地收尾` |
| T04 | b013719固定候选发布 | `任务归档/004_20261021_b013719诊断发布` |
| T05 | 2604675架构复核与定向修复 | `任务归档/005_20261021_架构审查与2604675候选` |
| T06 | 2604675诊断发布与服务器补充 | `任务归档/006_20261021_诊断发布与服务器补充` |

## 4. 代码恢复材料

目录：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/PR_服务器开发交接_20261022_170641_0800_c0d3/代码恢复材料`

| 文件 | 大小 |
|---|---|
| `README_恢复代码.md` | 3,519 |
| `SOURCE_BINDING.json` | 1,178 |
| `bundles/vllm-ascend.bundle` | 19,550,081 |
| `bundles/vllm-ascend.shallow` | 41 |
| `bundles/vllm.bundle` | 47,272,654 |
| `bundles/vllm.shallow` | 41 |
| `tools/restore_sources.py` | 3,259 |
| `tools/server_preflight.py` | 24,468 |
| `official_base_to_recommended.patch` | 341,261 |

恢复命令模板（**本轮未执行**，下一轮经授权再用）：

```bash
TASK_ROOT=/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/PR_服务器开发交接_20261022_170641_0800_c0d3
RESTORE_ROOT=/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/pr.restore-$(date +%Y%m%d-%H%M%S)
python3 "$TASK_ROOT/代码恢复材料/tools/restore_sources.py" \
  --input-root "$TASK_ROOT/代码恢复材料" \
  --owned-root "$RESTORE_ROOT" \
  --binding "$TASK_ROOT/代码恢复材料/SOURCE_BINDING.json"
```

## 5. 归档时点的代码与验收状态（只记录，未审计、未改动）

| 项 | 值 |
|---|---|
| CODE_START_DECISION | `CONTINUE_WITH_TARGETED_REWORK` |
| ARCHITECTURE_STATUS | `BLOCKED_A01_EXACT_LENGTH_ASYNC_CONTRACT` |
| Ascend SHA / tree | `2604675e520c23740c5225b6af8857eed8bd9391` / `afbf69a93f1c7e761769baa9044577d8b83b7a35` |
| vLLM SHA / tree | `a98247ab4db686ee03c66d5feb3c761e52a2f8ab` / `7f2a24a827bbbb2f211e02031f9d4d0d556d536c` |
| Ascend 固定 base | `128f35ed1461ecb34bc8b87583a67a66bc4bd1d6` |
| A3 / 性能 | 该候选 `NOT_RUN` |
| FULL_NONGRAPH_SCOPE_VALIDATED | `NO` |
| 首个有界开发问题 | `DW-A01`（exact-length consumer / D2H 契约） |

这些是**归档时点**的状态。本服务器若已有更晚的开发记录，本轮未审计、未回滚、未改写。

## 6. 包内容事实

- 完整 payload：13,836 项 = 13,828 普通文件 + 8 个内部相对符号链接，合计 873,310,016 bytes。
- 8 个符号链接全部位于 `任务归档/001_.../audit_clones/vllm/.claude/skills/` 下，目标为 `../../.agents/skills/<name>`，均解析在恢复根内且目标存在。
- 发布补充：14 个普通文件，79,134 bytes。
- 本归档不含约 30 GB MRV2 历史档案、模型、venv、NPU runtime。
