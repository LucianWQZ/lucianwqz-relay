# 服务器 PR 资料接收结果

- 接收编号：`PR_RECV_20261023_0114_c0d3_r3`
- 执行机器：node-39-101（容器，root，openEuler 24.03 LTS-SP4 / aarch64）
- 执行时间：2026-10-23 01:02 – 01:20（Asia/Shanghai）
- 执行站点：**SERVER**（真实服务器接收，非本地演练）

```
SERVER_PREFLIGHT: PASS
RELAY_TAG_COMMIT_TREE: VERIFIED
RELEASE_METADATA: VERIFIED
REMOTE_ASSET_BYTES: PASS
SERVER_RECEIVE: RECEIVED_AND_VERIFIED
EXECUTION_SITE: SERVER
FULL_PAYLOAD_IDENTITY: PASS
SYMLINK_RESTORE: PASS
INDEPENDENT_VERIFY: PASS
KNOWN_MANIFEST_BRANCH_DRIFT: RECORDED_R2_FIELD_WITH_VERIFIED_R3_TAG
PUBLICATION_BINDING_SIDECAR: COMPLETE
EXTERNAL_MRV2_REFERENCE: NOT_VERIFIED
ARCHIVED_CANDIDATE_ARCHITECTURE: BLOCKED_A01_EXACT_LENGTH_ASYNC_CONTRACT
PRODUCTION_CHANGED_BY_THIS_TASK: NO
DEV_WORKSPACE_CHANGED_BY_THIS_TASK: NO
NPU_EXPERIMENTS_BY_THIS_TASK: NOT_RUN
GITHUB_WRITES_BY_THIS_TASK: NOT_ATTEMPTED
RETURN_PACKAGE: VERIFIED
NEXT_ACTION: USER_RETURNS_SERVER_RECEIVE_PACKAGE_FOR_REVIEW
```

## 1. 实际恢复位置

```
/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/
├── PR_服务器开发交接_20261022_170641_0800_c0d3/          # 原始冻结 payload（只读）
├── 发布附件缓存/PR_服务器开发交接_20261022_170641_0800_c0d3/   # 四附件
├── 发布补充/PR_服务器开发交接_20261022_170641_0800_c0d3/       # 补充包 14 文件
├── 接收回执/PR_服务器开发交接_20261022_170641_0800_c0d3/       # RECEIVE_RECEIPT / VALIDATION / STATE
└── 接收工作/pr-r3-V7KpdLW9/                              # 本轮证据与回传件
```

`reference/pr` 是 NFS 持久挂载（`172.27.1.1:/Share`）上的真实路径，不是容器本地目录。
**`dev/pr` 在本轮之前已存在且为空目录，本轮未向其写入任何内容、未恢复代码**；
未安装任何 vLLM/CANN/torch/npu 环境；未启动 NPU。

## 2. 使用的固定身份

| 项目 | 值 |
|---|---|
| repository | `LucianWQZ/lucianwqz-relay` |
| branch（实际 r3） | `transfer/pr-handoff-20261022-c0d3-r3` |
| tag | `pr-transfer-20261022-170641-c0d3-r3` |
| annotated tag object | `76cebd36bd96cdd5cf18e2eab29868541c3f2af5` |
| peeled commit | `7c6d3630413ccd8421544bb11d5d5515a046cfbf` |
| tree | `2768457f15bb18db0483aa2ce8a21e7831a2b952` |
| Release ID / URL | `420878240` / `.../releases/tag/pr-transfer-20261022-170641-c0d3-r3` |
| 任务 ID | `PR_服务器开发交接_20261022_170641_0800_c0d3` |

四项断言全部实测相等，工作树 `git status --porcelain` 为空。
远端 `ls-remote` 显示 `main = 5a3c705e…`，与本次资料仓 commit **不同**；本轮全程只用 tag 及其 peeled commit，未取 main、未用 latest、未用自动生成的 Source code 包。

## 3. 实际执行步骤

1. 前置检查：hostname、用户、时间/时区、Python 3.11.10、Git 2.54.0、`gh` **不存在**；确认 `/mnt/share` 为 NFS4 持久挂载；目标父目录可写；可用空间 3.85 TB、inode 充足。
2. 在 `reference/pr/接收工作/` 下建本轮唯一工作目录 `pr-r3-V7KpdLW9`（mktemp -d）。
3. `git clone --depth 1 --branch <r3 tag>` 到工作目录的 `relay/`；首次因代理瞬断失败，加 `http.version=HTTP/1.1` 重试一次成功（详见第 7 节）。
4. 逐项断言 HEAD / tree / tag object / peeled commit / clean。
5. 读取 `README_接收工具.md`、`SERVER_IMPORT_中文.md`、`RELAY_TRANSFER_MANIFEST.json`、`PUBLICATION_ADDENDUM.md`、`REPOSITORY_RENAME_ADDENDUM.md`、两个接收脚本与 `pr_receiver_common.py`，并核对哈希（全部匹配）。
6. 查询 Release API：id `420878240`、tag r3、`draft=false`、四附件 name/size/digest 与任务指定值一致（`target_commitish` 显示 `main`，仅展示值）。
7. 因无 `gh`，按允许的公共附件回退，用 `curl -fSL` 从固定 tag 的 Release 下载四附件到 `asset-source/`，先写 `.partial`，校验 bytes+SHA256 后原子改名。
8. `--dry-run`（SERVER）→ `DRY_RUN_PASS`，布局与空间满足。
9. 正式接收：`下载并恢复PR资料.py --execution-site SERVER --asset-dir <asset-source>`，退出码 0，耗时 83 秒。
10. 独立验证：`验证PR接收资料.py`，退出码 0，`status=PASS`。
11. 额外显式核对 `execution_site=SERVER`（verifier 只展示不强制）。

## 4. 字节核验

| 附件 | bytes | SHA256 | 结果 |
|---|---|---|---|
| `PR_FULL_TRANSFER.zip` | 696,228,223 | `675237fa…6a953e` | PASS |
| `PR_REVIEW_RETURN.zip` | 1,771,620 | `71df7981…91b470` | PASS |
| `HANDOFF_MANIFEST.json` | 2,680 | `4606f83f…7720bc` | PASS |
| `PR_TRANSFER_SUPPLEMENT.zip` | 35,484 | `4828ee66…c8819e` | PASS |

- 完整 ZIP 内部 `FILES_MANIFEST.json` SHA256 = `51bebc04…014488`，与预期一致。
- 补充 ZIP 内部 manifest SHA256 = `06f885d6…4624f4`，与预期一致。
- 原 `HANDOFF_MANIFEST.json` 与完整包 identity 绑定校验 PASS。
- ZIP CRC 全量通过；payload 每个文件 size/hash 逐一通过。

## 5. 文件 / 链接数量

| 口径 | 实测 | 预期 | 结果 |
|---|---|---|---|
| payload 条目 | 13,836 | 13,836 | PASS |
| 普通文件 | 13,828 | 13,828 | PASS |
| 符号链接 | 8 | 8 | PASS |
| payload 字节 | 873,310,016 | 873,310,016 | PASS |
| 补充包普通文件 | 14 | 14 | PASS |
| 补充包字节 | 79,134 | 79,134 | PASS |
| 恢复目录目录数 | 2,308 | — | 记录 |
| 普通文件 mode | 逐个对照 ZIP metadata 与内部清单 | — | PASS |

8 个符号链接全部位于
`任务归档/001_20261020_非Graph历史审计与需求证据/原始资料/MRV2_NonGraph_Audit_20261020_2W0Wi3rU/audit_clones/vllm/.claude/skills/`
下，目标均为 `../../.agents/skills/<name>`，规范化后仍在恢复根内且目标实际存在。

## 6. 回执

- `RECEIVE_RECEIPT.json`：`status=RECEIVED_AND_VERIFIED`、`execution_site=SERVER`、
  `machine.hostname=node-39-101`、`received_at=2026-10-23T01:15:36+08:00`、
  `target.root`/`archive` 均为真实持久路径。
- 该回执的 `source.commit` / `source.tree` / `source.release_url` 为 **null**：
  当前 manifest 用 `commit_binding`/`release_binding` 占位，未提供这三项，接收器照原样写入。
  **这不是脚本核验成功，也不代表身份未知**——实际身份由外置
  `SERVER_PUBLICATION_BINDING.json` 用 Git 与 Release 实测证据给出。原回执未做任何改写。

## 7. 已知 branch 遗留与失败/重试

**branch 遗留（已记录）**：`RELAY_TRANSFER_MANIFEST.json → relay.branch` 仍是
`transfer/pr-handoff-20261022-c0d3-r2`，而实际 r3 分支头为 `7c6d3630…`。
接收器只用 `repository`/`tag` 校验，不读 branch；本轮按 r3 tag 与其 peeled commit 取件，
未改写冻结 manifest。另 `PUBLICATION_ADDENDUM.md` 第 7 节仍以"本轮（r2）"叙述，同属遗留文字。

**失败与重试**：

| # | 阶段 | 现象 | 处理 | 结果 |
|---|---|---|---|---|
| 1 | git clone | `RPC failed; curl 56 OpenSSL SSL_read: SSL_ERROR_SYSCALL`（代理瞬断） | 加 `http.version=HTTP/1.1` 与 lowSpeed 参数重试一次 | 成功 |

除上述一次 clone 重试外，下载、接收、验证均一次通过；无 partial 残留、无 `.receive.lock`
残留、无 `.receiving` staging 残留。

## 8. 外部 MRV2 历史档案（只读核对）

- 路径：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/adaption/MRV2_完整中文迁移_20261022_034933_0800`
- 回执：`RECEIVE_RECEIPT.json`，1,714 B，sha256 `e03469f9…2081040`
- `task_id = MRV2_完整中文迁移_20261022_034933_0800`，`status = RECEIVED_AND_VERIFIED`
- `archive_sha256 = cdea5059…f267f45`（与应绑定值一致），`archive_bytes = 29,839,300,507`
- **`execution_site` 字段缺失**（也无 `machine` 字段）

按"字段不足即 NOT_VERIFIED"的规则，本轮标记 `EXTERNAL_MRV2_REFERENCE: NOT_VERIFIED`。
未重下 30 GB、未修改历史回执、未重扫该档案全部字节，也未影响本轮 PR 资料判定。

## 9. 停止点

接收与验证闭环已完成。本轮到此结束：未执行 `SERVER_START_PROMPT.md` ·
未开始 `DW-A01` · 未恢复 dev/pr 代码 · 未占用 NPU · 未向 GitHub 写入任何内容。
下一轮由用户回传并审阅本接收包后，另行安排服务器 Codex/Claude 的开发接管任务。

归档绑定的候选状态仍为：`CODE_START_DECISION=CONTINUE_WITH_TARGETED_REWORK`、
`ARCHITECTURE_STATUS=BLOCKED_A01_EXACT_LENGTH_ASYNC_CONTRACT`、A3/性能 `NOT_RUN`、
`FULL_NONGRAPH_SCOPE_VALIDATED=NO`。资料接收不改变这些结论。
