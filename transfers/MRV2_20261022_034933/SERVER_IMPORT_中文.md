# 服务器恢复步骤（MRV2 完整中文迁移包）

目标机器：Ascend 服务器，通过你自己的 `gh` 认证从私仓下载。
本文所有命令均在本机实测过（含 `--help` 输出与合成小样端到端跑通）。

## 0. 前置条件

| 项目 | 要求 |
|---|---|
| Python | ≥ 3.8（脚本只用标准库） |
| gh CLI | 已安装，且 `gh auth status` 显示已登录、对 `LucianWQZ/private-file-relay` 有读权限 |
| 磁盘 | ≥ **56 GiB** 可用（分片 27.78 GiB + 解压 27.79 GiB + 余量） |
| 网络 | 能访问 `github.com` 与 `objects.githubusercontent.com` |

先验证：

```bash
python3 -V
gh auth status
df -h /mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/adaption
```

## 1. 取脚本（不要整仓 clone 大文件）

```bash
mkdir -p ~/mrv2_transfer && cd ~/mrv2_transfer
git clone --depth 1 --branch transfer/mrv2-adaption-20261022 \
  https://github.com/LucianWQZ/private-file-relay.git relay
cd relay/transfers/MRV2_20261022_034933
```

（该分支只有文档与脚本，约 45 MiB，不含分片。）

## 2. 预检（不下载）

```bash
python3 下载并恢复资料.py --dry-run
```

期望输出包含：
- `仓库: {"nameWithOwner":"LucianWQZ/private-file-relay", ...}`
- `分片下载 需要 27.78 GiB，<root> 可用 ...`
- `dry-run：预检通过，未下载。`

## 3. 正式恢复

默认根目录已写在脚本里：

```bash
python3 下载并恢复资料.py --yes
```

等价于显式指定：

```bash
python3 下载并恢复资料.py --yes \
  --root /mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/adaption
```

恢复结果：

```
/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/adaption/
├── .mrv2_transfer_work/MRV2_完整中文迁移_20261022_034933_0800/   ← 56 个分片（保留）
└── MRV2_完整中文迁移_20261022_034933_0800/                       ← 解压结果
    ├── 00_先读这里.md … 05_服务器接管说明.md
    ├── 任务归档/（35 个任务）
    ├── TASK_INDEX.json / PATH_MAP.json / DOCUMENT_CATALOG.jsonl
    ├── SHA256SUMS / TRANSFER_MANIFEST.json / VERIFY_TRANSFER.py
    └── RECEIVE_RECEIPT.json
```

脚本会自动完成：
1. 逐片下载（已存在且 SHA256 相符的分片直接复用，支持断点重试）；
2. 逐片 SHA256 校验；
3. 按 `index 0..55` 顺序流式串联校验整包 SHA256（必须等于 `cdea5059…f267f45`）；
4. 解压前再查一次空间（按 ZIP 中央目录统计真实解压体积）；
5. 安全解压：拒绝绝对路径、`..` 越界、符号链接、设备文件；
6. 解压后校验 `SHA256SUMS`（7,480 条）、`TASK_INDEX.json`（35 个任务）与必要顶层文件。

## 4. 独立复核

```bash
python3 验证接收资料.py --dir \
  /mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/adaption/MRV2_完整中文迁移_20261022_034933_0800
```

期望 `"status": "PASS"`。结构抽查可加 `--skip-sha`（不建议用于交付）。

## 5. 空间计算（为什么要 56 GiB）

| 阶段 | 占用 |
|---|---|
| 分片（56 个，保留） | 27.78 GiB |
| 解压结果 | 27.79 GiB |
| 峰值 | ≈ 55.6 GiB |
| 脚本预留余量 | +64 MiB |

脚本**不会**生成第二份 30 GiB 的完整 ZIP：解压通过自定义只读流把 56 个分片当作一个可 seek 文件交给 `zipfile`。

## 6. 参数（实测 `--help`）

```
--root ROOT          恢复根目录（包解压到 <root>/<task_id>）
--manifest MANIFEST  传输清单（默认脚本同目录 RELAY_TRANSFER_MANIFEST.json）
--work-dir DIR       分片目录（默认 <root>/.mrv2_transfer_work/<task_id>）
--keep-parts         保留分片（默认即保留）
--clean-parts        成功后删除分片（默认不删；确认无需复核再用）
--skip-full-sha      跳过 SHA256SUMS 全量复核（不建议）
--dry-run            只预检与算空间
--yes                跳过交互确认
```

`验证接收资料.py` 参数：

```
--dir DIR            待校验目录
--manifest PATH      用于核对文件总数
--skip-sha           只做结构校验
--json-out PATH      结果另存 JSON
```

## 7. 常见失败

| 现象 | 原因 | 处理 |
|---|---|---|
| `gh 未登录或无授权` | 服务器未 `gh auth login` | 登录后重跑；私仓必须有 read 权限 |
| `磁盘空间不足` | 余量 < 27.78 GiB（下载）或 < 27.79 GiB（解压） | 清理或换 `--root` |
| `目标目录已存在` | 上次已解压 / 手工建过目录 | 确认后用新 `--root`，或人工移走旧目录 |
| `分片校验失败` | 下载中断或对象损坏 | 删掉该分片重跑，脚本会重新下载 |
| `整包串联校验失败` | 分片顺序错 / 混入其他版本 | 不要手工拼装，按脚本清单顺序 |
| `gh release download` 超时 | 网络抖动 | 直接重跑同一命令，已下载分片会自动复用 |

## 8. 边界

- 恢复成功只代表**资料已到服务器**，不代表 NPU 已验收。
- 不要修改解压后的任何原始文件；二次校验用 `验证接收资料.py`，不要重新打包。
- 不要删除 `.mrv2_transfer_work/` 里的分片，除非已经产出 receipt 且确认无需复核。
