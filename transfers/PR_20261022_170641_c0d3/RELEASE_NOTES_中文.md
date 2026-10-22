# MRV2 非 Graph PR 服务器开发交接资料

本 Release 固定发布 PR_服务器开发交接_20261022_170641_0800_c0d3 的本地冻结资料，供后续服务器接收。它不是 vLLM-Ascend 产品 Release，不包含新生产提交，不代表 A3、性能或完整非 Graph 验收通过。

## 固定源码

- Ascend：2604675e520c23740c5225b6af8857eed8bd9391，tree afbf69a93f1c7e761769baa9044577d8b83b7a35
- vLLM：a98247ab4db686ee03c66d5feb3c761e52a2f8ab，tree 7f2a24a827bbbb2f211e02031f9d4d0d556d536c
- 架构：BLOCKED_A01_EXACT_LENGTH_ASYNC_CONTRACT
- A3/性能：本候选 NOT_RUN
- 完整非 Graph：未验收

## Release 附件白名单

1. PR_FULL_TRANSFER.zip — 完整 PR 迁移资料和代码恢复材料
2. PR_REVIEW_RETURN.zip — 外部审阅小包
3. HANDOFF_MANIFEST.json — 原冻结外置清单
4. PR_TRANSFER_SUPPLEMENT.zip — 发布补充、接收工具和本轮有限证据

请按本 Release 的固定 tag 获取附件。不要使用 latest，也不要把 GitHub 自动生成的 Source code.zip 当作 PR_FULL_TRANSFER.zip。

完整包的本地最终验证绑定 SHA256 675237faf78efcd4f95642494437af2b09c29680f21eb8e9e460cad7ab6a953e，并已从其实际 ZIP 成员恢复固定双仓。发布完成后还应以远端重新下载的字节执行本地接收演练；这仍不等于服务器已经接收。

详细边界、纠错映射和接收步骤见 Git 目录中的 PUBLICATION_ADDENDUM.md 与 SERVER_IMPORT_中文.md。

本 Release 应保持非 latest；不得修改已有 MRV2 transfer、旧 tag/Release 或仓库可见性。
