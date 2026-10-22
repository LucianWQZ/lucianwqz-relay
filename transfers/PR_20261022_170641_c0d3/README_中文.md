# MRV2 非 Graph PR 资料发布入口

本目录是 PR_服务器开发交接_20261022_170641_0800_c0d3 的 GitHub 资料入口。它只保存导航、清单、接收工具和有限证据；约 696 MB 的完整迁移包及审阅小包通过固定 Release 附件发布，不作为 Git blob 提交。

## 固定源码与状态

- Ascend：2604675e520c23740c5225b6af8857eed8bd9391，tree afbf69a93f1c7e761769baa9044577d8b83b7a35。
- 配套 vLLM：a98247ab4db686ee03c66d5feb3c761e52a2f8ab，tree 7f2a24a827bbbb2f211e02031f9d4d0d556d536c。
- 代码起点裁决：CONTINUE_WITH_TARGETED_REWORK。
- 架构状态：BLOCKED_A01_EXACT_LENGTH_ASYNC_CONTRACT。
- 当前候选 A3：NOT_RUN；性能：NOT_RUN；完整非 Graph：未验收。

资料发布成功只证明固定字节可以从 GitHub 取得并按清单验证，不改变上述功能状态，也不表示官方架构认可。

## 两个原包

| 文件 | 用途 | 字节数 | SHA256 |
|---|---|---:|---|
| PR_FULL_TRANSFER.zip | PR 历史、导航、双仓恢复材料和校验证据的完整迁移包 | 696228223 | 675237faf78efcd4f95642494437af2b09c29680f21eb8e9e460cad7ab6a953e |
| PR_REVIEW_RETURN.zip | 供外部审阅者快速阅读的小包 | 1771620 | 71df7981a67a6643cf476e56d2d1e1a2795e431cb1ac271fed24a8e51391b470 |

原外置清单 HANDOFF_MANIFEST.json 保持逐字节不变。发布补充包只补充发布、接收和纠错说明，不嵌入上述两个 ZIP，也不改写原归档成员。

## 推荐阅读顺序

1. 本文件和 PUBLICATION_ADDENDUM.md。
2. SERVER_IMPORT_中文.md。
3. RELAY_TRANSFER_MANIFEST.json。
4. bootstrap/00_先读这里.md、bootstrap/06_回传ChatGPT摘要.md。
5. 需要进入开发时，再读 bootstrap/NEXT_SESSION_HANDOFF.json、bootstrap/CODE_STATE.json、bootstrap/04_架构兼容与待解决问题.md。

## 仓库改名说明

本资料原计划发布到 `LucianWQZ/private-file-relay`，该仓库已改名为 `LucianWQZ/lucianwqz-relay`（public，默认分支 main）。因此本轮发布使用 -r2 后缀的新分支与新 tag；bootstrap/ 内仍保留旧名称的文件是冻结历史快照，不作改写。

## GitHub 对象

建议身份如下，发布主流程必须先做冲突检查，再以实际结果为准：

- branch：transfer/pr-handoff-20261022-c0d3-r3
- tag：pr-transfer-20261022-170641-c0d3-r3
- Git 目录：transfers/PR_20261022_170641_c0d3

本文件不记录其所在 Git 提交的最终 SHA，以避免自引用。实际 relay commit/tree、tag object、peeled commit、Release URL 和资产 ID 应写入发布完成后生成的外置 GITHUB_PUBLICATION_RESULT.json 与 SERVER_RECEIVER_HANDOFF.json。

## 外部依赖

- 已有 MRV2 中文档案未重复上传；其服务器接收状态仍以用户转述记录，后续须读取真实回执。
- catlass 固定提交 41bf90da655bba3c66d0acd7e00abe33960ecfd6、CANN/torch_npu/native runtime、模型、团队工具和设备资源不在资料包内。
- 资料仓不是生产代码仓。后续通过完整包中的 bundle 恢复双仓，或按固定代码 ref 获取；不得把 GitHub 自动生成的 Source code.zip 当作完整迁移包。
