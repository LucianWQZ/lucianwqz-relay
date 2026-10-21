# MRV2 完整中文迁移 —— 私仓传输目录（20261022_034933）

本目录是 MRV2 Draft Sliding Window 项目**完整中文迁移资料**的 GitHub 中转发布点。
它本身**不是**完整迁移；完整集合 = 本目录的清单 + Release 中的 56 个分片。

## 1. 三个部分，别混用

| 部分 | 位置 | 内容 | 是否完整 |
|---|---|---|---|
| Git 文档 | 本目录（分支 + tag） | 中文导航、35 个任务说明、原始 Markdown、关键交接 JSON、恢复脚本 | ❌ 只是索引与摘要 |
| Release 分片 | 同一 tag 的 Release | `MRV2_full_archive.zip.part-000 … part-055` | ✅ 完整包本体（29.84 GB） |
| 恢复脚本 | 本目录 | `下载并恢复资料.py`、`验证接收资料.py` | — |

**完整集合判定规则**：`RELAY_TRANSFER_MANIFEST.json` 中登记的全部 56 个分片按序拼接后，
SHA256 必须等于 `cdea50597f7f7dc898fae79935d8fecfac5cba73b59aa23a15f867125f267f45`，
字节数必须等于 `29,839,300,507`。任一不符即视为不完整。

**bootstrap 不等价于完整迁移**。`bootstrap/` 只覆盖中文导航、488 份原始 Markdown、
关键手交 JSON 与校验材料；`任务归档` 下的 `.pt`、`.bin`、trace JSON、原始 ZIP、
二进制证据等**必须**从完整包取得。

## 2. 目录结构

```
transfers/MRV2_20261022_034933/
├── README_中文.md                     ← 本文件
├── SERVER_IMPORT_中文.md              ← 服务器恢复步骤（含实测参数）
├── RELAY_HANDOFF.json                 ← 代码/中转/服务器身份与指针
├── RELAY_TRANSFER_MANIFEST.json       ← 分片清单（名称、字节、SHA256）
├── 原始_TRANSFER_MANIFEST.json        ← 迁移生成时的原始清单（未改写）
├── 下载并恢复资料.py                  ← 下载 + 校验 + 安全解压
├── 验证接收资料.py                    ← 已恢复目录的独立复核
└── bootstrap/
    ├── 00_先读这里.md … 05_服务器接管说明.md
    ├── TASK_INDEX.json / PATH_MAP.json / DOCUMENT_CATALOG.jsonl
    ├── SHA256SUMS / TRANSFER_MANIFEST.json / PACKAGE_VERIFICATION.json
    ├── BOOTSTRAP_INDEX.json           ← bootstrap 自身清单（682 个文件）
    └── 任务归档/<35 个任务>/…        ← 保持原始相对路径
```

## 3. 怎么用

- **只看文档**：直接读 `bootstrap/00_先读这里.md` → `01` → `02` → `05`，再进任务目录。
- **要在服务器恢复全量**：按 `SERVER_IMPORT_中文.md` 执行，脚本会自动下载、校验、安全解压。
- **只要某一组原始文件**：先在 `bootstrap/BOOTSTRAP_INDEX.json` 或 `DOCUMENT_CATALOG.jsonl` 里查到路径，
  bootstrap 里有就直接取，没有就从完整包解压后取。

## 4. 状态口径（不要越界引用）

- Repair7 代码：`vllm-ascend` / `fix/p7x-graph-base-a3-repair7` / `7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14`，
  该分支的 GitHub publication 状态为 `VERIFIED`。
- 新 SHA 的 NPU 设备验证：`NOT_RUN`。旧 Repair6 证据不能继承为 Repair7 验收。
- `PUBLIC_GRAPH_GATE=STILL_FROZEN`。
- **本目录的存在不代表资料已到达服务器，也不代表 NPU 已验收。**
  只有服务器侧执行恢复脚本并产出 `RECEIVE_RECEIPT.json`，才说明“资料已到服务器”。

## 5. 版本与发布

- 分支：`transfer/mrv2-adaption-20261022`
- 目录：`transfers/MRV2_20261022_034933/`
- tag / Release：见 `RELAY_TRANSFER_MANIFEST.json → release`
- 不覆盖其他任务、不改写原始 ZIP、不重新发布 Repair7。
