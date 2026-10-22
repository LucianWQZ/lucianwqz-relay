# PR 单文件 Release 接收工具

这组工具只负责固定 GitHub Release 的下载、解压与完整性验证。它不会执行归档内脚本，不会安装环境，不会创建 `dev/pr`，也不会启动 NPU 或 Codex 开发。

## 运行要求

- Python 3.9 或更高版本；仅使用 Python 标准库。本地已在 macOS 系统 Python 3.9.6 完成语法、离线接收和攻击样例测试。
- 从 GitHub 下载时需要可执行的 GitHub CLI `gh`，并且当前身份对指定仓库具有读权限。脚本使用 `gh release download <固定 tag> --repo <固定 repo> --pattern <精确附件名> --output <name>.partial`。本交接验证版本为 `gh 2.73.0`，因此把 2.73.0 作为保守的最低受支持版本；更旧版本即使可能具有这些参数，也属于未验证。
- 离线演练使用 `--asset-dir`，不需要 `gh`。
- 两个接收脚本本身不调用 Git。若从资料分支取得 bootstrap/manifest，Git 版本由发布入口另行记录；不能据此声称任意旧 Git 已验证。
- 恢复目标和 staging 必须位于 `--root` 所在文件系统，才能用目录 rename 完成原子落位。

## 清单契约

脚本读取发布仓 Git 中的 `RELAY_TRANSFER_MANIFEST.json`。必需字段如下：

```json
{
  "schema_version": 1,
  "task_id": "PR_服务器开发交接_20261022_170641_0800_c0d3",
  "relay": {
    "repository": "LucianWQZ/lucianwqz-relay",
    "tag": "固定 tag",
    "commit": "发布资料仓 commit；可以在提交后由外置 handoff 记录",
    "tree": "发布资料仓 tree；可以在提交后由外置 handoff 记录"
  },
  "release_assets": [
    {"role": "full", "name": "PR_FULL_TRANSFER.zip", "bytes": 0, "sha256": "...", "payload_entries": 0, "payload_bytes": 0, "internal_manifest_sha256": "..."},
    {"role": "review", "name": "PR_REVIEW_RETURN.zip", "bytes": 0, "sha256": "..."},
    {"role": "original_manifest", "name": "HANDOFF_MANIFEST.json", "bytes": 0, "sha256": "..."},
    {"role": "supplement", "name": "PR_TRANSFER_SUPPLEMENT.zip", "bytes": 0, "sha256": "...", "payload_entries": 0, "payload_bytes": 0, "internal_manifest_sha256": "..."}
  ],
  "target": {
    "task_directory_name": "PR_服务器开发交接_20261022_170641_0800_c0d3",
    "cache_relative": "发布附件缓存/PR_服务器开发交接_20261022_170641_0800_c0d3",
    "supplement_relative": "发布补充/PR_服务器开发交接_20261022_170641_0800_c0d3",
    "receipt_relative": "接收回执/PR_服务器开发交接_20261022_170641_0800_c0d3",
    "full_payload_bytes": 0,
    "space_margin_bytes": 536870912,
    "peak_disk_bytes": 0
  }
}
```

`peak_disk_bytes` 如存在，必须不小于工具按“全部下载附件 + 完整包展开 payload + 补充包展开 payload + margin”计算的值。发布者应把实际精确值写进清单。

## 命令

以下命令中的 repo 和 tag 必须与清单完全一致，不能使用 `latest`：

```bash
python3 下载并恢复PR资料.py \
  --root /mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr \
  --manifest RELAY_TRANSFER_MANIFEST.json \
  --repo LucianWQZ/lucianwqz-relay \
  --tag '<固定 tag>' \
  --execution-site SERVER \
  --dry-run

python3 下载并恢复PR资料.py \
  --root /mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr \
  --manifest RELAY_TRANSFER_MANIFEST.json \
  --repo LucianWQZ/lucianwqz-relay \
  --tag '<固定 tag>' \
  --execution-site SERVER

python3 验证PR接收资料.py \
  --root /mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr \
  --manifest RELAY_TRANSFER_MANIFEST.json \
  --repo LucianWQZ/lucianwqz-relay \
  --tag '<固定 tag>'
```

本地独立下载后的演练把四个附件放入一个目录，再加：

```bash
--asset-dir /path/to/downloaded-assets --execution-site LOCAL_SIMULATION
```

`--dry-run` 不创建 root、缓存、锁或回执，也不下载附件。正式执行使用 `.partial`，只有大小和 SHA256 都匹配才 rename 为可用缓存。目标已存在时仅在逐 payload 验证完全一致后复用；不一致立即停止，不合并覆盖。

## 安全边界

- 拒绝绝对路径、目录逃逸、反斜线、重复成员、文件/父目录冲突，以及 Unicode NFC/大小写折叠冲突。
- 从 ZIP 内部 `FILES_MANIFEST.json` 核对 type、size、SHA256、mode。普通文件 mode 会与 ZIP metadata 对照、恢复并在目标目录复核；symlink mode 不具备跨平台可恢复语义（原打包器也按 0777 写 ZIP metadata），因此只保留其声明值，实际契约是 type、target 文本和 target 最终仍在恢复根内。
- 先写并验证全部普通文件，最后恢复符号链接。链接 target 可含 `../`，但词法规范化后的目标必须仍位于本次恢复根内且实际存在。
- staging 失败时保留现场，工具不自动删除；已有正式目标身份不同则停止。
- `RECEIVE_RECEIPT.json` 与 `RECEIVE_VALIDATION.json` 位于独立回执目录，不混入冻结 payload。

接收 PASS 只表示资料传输和内容完整性。它不改变 `BLOCKED_A01_EXACT_LENGTH_ASYNC_CONTRACT`，也不代表 A3、性能或完整非 Graph 范围通过。
