# PR 迁移包发布补充与边界说明

本文件是冻结包 PR_FULL_TRANSFER.zip 和 PR_REVIEW_RETURN.zip 的发布 sidecar。它不修改原包，也不把发布后的事实倒写进冻结成员。

## 1. 冻结前表述纠正

06_回传ChatGPT摘要.md 第 8 节和 代码恢复材料/README_恢复代码.md 中“最终还会从完整 ZIP 实际成员恢复一次”的句子写于最终打包验证完成前。实际最终结果已经生成：

- 结果文件：校验结果/PACKAGE_VERIFICATION.json
- 验证时间：2026-10-22T17:24:01+08:00
- 完整 ZIP：696228223 bytes
- SHA256：675237faf78efcd4f95642494437af2b09c29680f21eb8e9e460cad7ab6a953e
- 完整 ZIP 内部 manifest SHA256：51bebc046c8bc56b0574fa740fbb780074dbcd5ab83ea04e0c01574a92014488
- code_restore_from_actual_full_zip.status：PASS

该验证从完整 ZIP 的实际成员提取恢复材料，得到精确双仓 SHA/tree、clean、fsck 通过和 no-alternates。它是源码可恢复证据，不是 A3、native ABI 或功能正确性证据。

外部 ChatGPT 已核验三份上传附件的大小/hash、审阅 ZIP CRC、150 个 payload 的大小/hash、内部 manifest，以及 40 个 JSON、2 个 JSONL、6 个 CSV 的可解析性。外部 ChatGPT 没有下载、解压或亲自恢复约 696 MB 的完整 ZIP；完整包结论仍依赖本地 PACKAGE_VERIFICATION.json 以及本轮远端下载后的接收演练。

## 2. 实际导航字段

旧时间线中出现的 inventory.jsonl、reading_coverage.json 等名称是早期建议，不是最终正式入口。实际导航如下：

| 目的 | 实际文件 | 实际字段 |
|---|---|---|
| 任务阶段与顺序 | TASK_INDEX.json | tasks[].task_id、source_top、archive_dir、source_relative_root、recommended_archive_directory、previous_task_id、next_task_id |
| 原路径/归档/服务器映射 | PATH_MAP.json | entries[].kind 及相应 original、archive、future_server；输出别名项使用 user_path、observed_alias、same_filesystem_object |
| 每个文件身份与阅读状态 | DOCUMENT_CATALOG.jsonl | source_relative_path、task_id、kind、copy_status、archive_destination、read_status、read_scope、sha256 |
| 阅读覆盖汇总 | 校验结果/READING_COVERAGE.json | regular_file_status_counts、critical_chain_complete、critical_full_files、partial_files、recorded_remainder |
| 源复制核对 | 校验结果/SOURCE_COPY_VERIFICATION.json | counts、regular_source_bytes_checked、errors |
| 符号链接 | 校验结果/SYMLINK_HANDLING.json | entries[].path、target、copied、reason |
| 包和实际 ZIP 恢复 | 校验结果/PACKAGE_VERIFICATION.json | packages.full 与 code_restore_from_actual_full_zip |

所有路径修正只存在于导航/sidecar；原始证据中的旧绝对路径保持原字节。

## 3. 实际复制结果

最终 SOURCE_COPY_VERIFICATION.json 的结果是：

- 13705 个普通文件 COPIED_HASH_VERIFIED；
- 2 个上游公开 workflow 模板副本 COPIED_REDACTED；
- 8 个内部相对符号链接 COPIED_SYMLINK_PRESERVED；
- 2236 个目录按清单重建；
- 根 .DS_Store 排除；
- 指向本机外部 runtime 的 node_modules 符号链接排除。

不能把时间线中的“建议排除”扩写成实际排除项。两个脱敏副本与源文件的不同 SHA 已记录在 校验结果/SENSITIVE_CONTENT_REVIEW.json；源原件未修改。

## 4. 规范和架构结论边界

仓内规范清单和固定版本设计文档证明了审查依据，不证明本候选的所有修改已经获得 vLLM/vLLM-Ascend 维护者认可。现有小包没有明确列出 2–3 个独立、已合入的同类特性 PR 作为风格对照；该工作保留为后续架构收敛和正式 PR 准备待办，本轮不扩展为代码重审。

当前结论保持：

- CODE_START_DECISION=CONTINUE_WITH_TARGETED_REWORK
- ARCHITECTURE_STATUS=BLOCKED_A01_EXACT_LENGTH_ASYNC_CONTRACT
- Ascend 2604675e520c23740c5225b6af8857eed8bd9391 的 A3 与性能均 NOT_RUN
- FULL_NONGRAPH_SCOPE_VALIDATED=NO

GitHub 资料发布、远端字节校验和本地接收演练均不能把这些状态改为通过。

## 5. 发布内容审查边界

冻结时的 SENSITIVE_CONTENT_REVIEW.json 只对复制后的任务档案做了顶层/普通文件扫描，并明确声明未递归证明嵌套历史容器无秘密。本轮公开发布必须对实际完整 ZIP、嵌套 ZIP/文本/脚本/config、Git bundle 对象及准备提交的新文件做有界复核，记录工具、深度/大小/时间上限、内容 hash 去重、命中裁决和未检查范围。

只有本轮 PUBLISH_CONTENT_REVIEW 通过后，才能上传四个白名单附件。若发现真实凭据、带真实认证信息的 URL、私钥或明确不可公开资料，应停止受影响发布；不得通过静默删文件、修改仓库可见性或重写 bundle 来制造通过。

## 6. 后续责任

服务器真实接收仍是下一轮任务。本轮只允许：

- 固定 branch/tag/Release 与四个附件；
- 从 GitHub 独立下载全部附件并验证字节；
- 在本地临时目录执行接收演练，回执标记 LOCAL_SIMULATION。

真实服务器接收必须另行生成回执；现有 MRV2 大档案的服务器状态仍为 USER_REPORTED，不能从其远端 ref 存在推导出服务器已核验。

## 7. 仓库改名与 -r2 重发布

原发布目标 `LucianWQZ/private-file-relay` 已由仓库所有者改名为 `LucianWQZ/lucianwqz-relay`。改名导致：旧地址 301 跳转到新地址；旧计划中的 branch/tag 不再适用；补充包与传输清单必须绑定新仓库身份。

因此本轮（r2）的实际身份为：

- repository：LucianWQZ/lucianwqz-relay（public，默认分支 main）
- branch：transfer/pr-handoff-20261022-c0d3-r3
- tag：pr-transfer-20261022-170641-c0d3-r3
- transfer directory：transfers/PR_20261022_170641_c0d3

冻结的 bootstrap/06_回传ChatGPT摘要.md、bootstrap/EXTERNAL_DEPENDENCIES.json 中出现的旧仓库名属于冻结历史，不为改名回写；改名事实只记录在本补充说明与新生成的 REPOSITORY_RENAME_ADDENDUM.md 中。

第一次发布尝试（attempt1）的本地 commit `9eb5618d1ec6d2e86eeb0ab314296eece3b302c0` 与新 tag `pr-transfer-20261022-170641-c0d3` 从未在远端形成 ref，其失败证据保存在外置发布目录的 evidence/attempt1_private_file_relay_blocked/，本轮不删除、不移动。
