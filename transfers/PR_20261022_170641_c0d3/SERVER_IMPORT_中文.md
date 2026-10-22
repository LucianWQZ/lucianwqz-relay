# 服务器接收 PR 资料

本说明用于下一轮真实服务器接收。本轮发布任务只在本地独立目录演练，不连接服务器，不创建 dev/pr，不运行 NPU。

## 固定目标

- 接收根：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr
- 原完整归档落位：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/pr/PR_服务器开发交接_20261022_170641_0800_c0d3
- 下载缓存和发布补充材料必须放在 reference/pr 下独立子目录，不能混入原 payload。

后续开发目标 dev/pr/src/vllm-ascend 与 dev/pr/src/vllm 不由接收工具创建。接收成功后，下一轮另行按 代码恢复材料/README_恢复代码.md 恢复并开始开发。

## 仓库改名说明

资料仓已从 `LucianWQZ/private-file-relay` 改名为 `LucianWQZ/lucianwqz-relay`；旧地址仍 301 跳转，但本任务只认新名称。GitHub 自动生成的 Source code 归档仍不属于白名单。

## 必须固定的来源

接收工具必须显式指定资料仓与固定 tag，不得使用 latest：

- repository：LucianWQZ/lucianwqz-relay
- 推荐 tag：pr-transfer-20261022-170641-c0d3-r3（以最终 SERVER_RECEIVER_HANDOFF.json 为准）
- transfer directory：transfers/PR_20261022_170641_c0d3

Release 白名单只有：PR_FULL_TRANSFER.zip、PR_REVIEW_RETURN.zip、HANDOFF_MANIFEST.json、PR_TRANSFER_SUPPLEMENT.zip。GitHub 自动生成的 Source code.zip/Source code.tar.gz 不在白名单内。

## 接收顺序

1. 克隆或 fetch 固定 relay commit，并核对 tag 的 peeled commit；不能只跟踪可移动分支。
2. 在不创建接收目录、不下载大包的 --dry-run 中解析固定 tag、清单、目标 root 和空间预算。
3. 正式执行时，下载到任务专属临时缓存；流式写入 .partial，大小和 SHA256 匹配后再原子改名。
4. 解压前检查成员名、重复路径、Unicode/NFC 和大小写冲突、类型及声明大小。
5. 先安全落普通目录和文件，最后按 manifest 建立 8 个内部相对符号链接。链接中的 ../ 需规范化后确认最终目标仍位于本次恢复根；不得一概拒绝，也不得跟随链接写出目标根。
6. 验证完整包内部 FILES_MANIFEST.json 中的类型、大小、SHA256 和必要 mode，再在同一文件系统原子落位。
7. 正式目标已存在时，只允许身份一致后复用；身份不同立即停止，不合并覆盖。
8. 生成 RECEIVE_RECEIPT.json 和独立验证 JSON。真实服务器回执必须记录机器、时间、repo/tag/commit、附件 hash、目标目录、文件/链接统计、异常和外部依赖。

本地演练的回执必须是 execution_site=LOCAL_SIMULATION，不能作为服务器已经接收的证据。

## 原完整包的期望

- ZIP：696228223 bytes，SHA256 675237faf78efcd4f95642494437af2b09c29680f21eb8e9e460cad7ab6a953e。
- ZIP 成员：13837，其中 payload 13836；payload 未压缩总字节 873310016。
- 内部 manifest SHA256：51bebc046c8bc56b0574fa740fbb780074dbcd5ab83ea04e0c01574a92014488。
- 原复制结果：13705 个普通文件字节一致、2 个公开上游工作流模板副本脱敏、8 个内部相对符号链接保留；根 .DS_Store 和 1 个指向外部 runtime 的 node_modules 符号链接排除。

## 源码恢复边界

完整 ZIP 的最终验证已经从 ZIP 实际成员提取双仓 bundle 并恢复：

- Ascend SHA/tree：2604675e520c23740c5225b6af8857eed8bd9391 / afbf69a93f1c7e761769baa9044577d8b83b7a35
- vLLM SHA/tree：a98247ab4db686ee03c66d5feb3c761e52a2f8ab / 7f2a24a827bbbb2f211e02031f9d4d0d556d536c

验证结果只证明代码对象、tree、clean、fsck 和 no-alternates。native ABI、模型、A3、分布式行为和性能仍须在后续任务中验证。

## 禁止事项

- 不下载 latest，不根据仓库页面上的最新 Release 猜 tag。
- 不执行归档中的历史任务脚本、安装脚本或启动命令。
- 不因接收成功自动创建 dev/pr、编译 native、加载模型或占用设备。
- 不改写原档案中的旧绝对路径；使用 PATH_MAP.json 和本发布补充说明导航。
