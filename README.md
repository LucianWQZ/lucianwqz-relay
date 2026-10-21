# private-file-relay

私有资料中转仓库（GitHub Release 承载大文件，Git 只放文档与脚本）。

## 当前内容

| 目录 | 说明 |
|---|---|
| [`transfers/MRV2_20261022_034933/`](transfers/MRV2_20261022_034933/README_中文.md) | MRV2 完整中文迁移：中文导航、35 个任务说明、恢复脚本（Git），完整包 56 个分片（Release） |

## 使用方式

- 只想读文档：进 `transfers/MRV2_20261022_034933/bootstrap/`，从 `00_先读这里.md` 开始。
- 要在服务器恢复全量 29.84 GB：按 `transfers/MRV2_20261022_034933/SERVER_IMPORT_中文.md` 执行。

## 仓库说明

- 本仓库仅用于资料传递，**不是**任何生产代码仓库；生产代码在 `LucianWQZ/vllm-ascend`。
- 2026-10-22 曾按要求清空过一次历史（旧提交不可达，GitHub 侧对象会延迟回收）。
- 大文件一律走 Release，不进入 Git 历史；单个 Git blob 控制在 50 MiB 以下。
- 仓库当前为 public，但只放可公开传递的迁移文档；如后续含敏感材料，请改为 private 再上传。

## 迁移集合的完整性

完整集合 = `RELAY_TRANSFER_MANIFEST.json` 登记的 56 个分片按序拼接，
SHA256 必须为 `cdea50597f7f7dc898fae79935d8fecfac5cba73b59aa23a15f867125f267f45`，
字节数必须为 `29,839,300,507`。文档目录（bootstrap）只是索引与摘要，不能替代完整包。
