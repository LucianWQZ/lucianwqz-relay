# 仓库改名与 r2 发布身份

## 改名事实

- 原名：LucianWQZ/private-file-relay
- 现名：LucianWQZ/lucianwqz-relay
- 可见性：public（未变更；本任务不执行任何可见性修改）
- 默认分支：main（改名后 main 已前进到 5a3c705e2642e9b7f57bec95db797415dbfa18ae）

GitHub 对旧地址返回 301，因此旧链接仍可解析，但本任务的全部清单、命令和接收工具只使用新名称。

## 为什么需要 r2

attempt1 计划建立在改名前的仓库身份和旧 main 基线上，且其 Git smart-HTTP push 未能在远端形成任何 ref。改名后：

1. 远端 main 已前进一提交，旧本地基线不再等于远端 main；
2. 传输清单需要绑定新仓库名、新 tag 与新补充包 hash；
3. 接收工具的命令行示例必须与新仓库一致。

因此使用 `-r2` 后缀的新分支与新 tag，从远端 main 新建，不改动任何旧对象。

## 不变的东西

- 三个冻结附件（完整包、审阅包、原外置清单）字节不变；
- 源码绑定（Ascend/vLLM SHA 与 tree）不变；
- 架构与验收状态不变：BLOCKED_A01_EXACT_LENGTH_ASYNC_CONTRACT、A3/性能 NOT_RUN、完整非 Graph 未验收；
- 旧 MRV2 transfer 目录、旧分支、旧 tag、旧 Release 均不修改。

## attempt1 存档

- branch：transfer/pr-handoff-20261022-c0d3
- commit：9eb5618d1ec6d2e86eeb0ab314296eece3b302c0
- tree：2bda34c60a337f461627bf9c7d0ad14323b10766
- tag：pr-transfer-20261022-170641-c0d3
- tag object：91f53eb98fc00f4fabdd5bca2593a8468f783519
- 远端发布：否（只读核对确认 refs 不存在）

## r2 -> r3

r2 的首次发布尝试已在远端建立 branch/tag，但其补充包内部 FILES_MANIFEST.json 使用了错误的字段名（bytes 而非 receiver 合约要求的 size），导致接收工具在补充包校验阶段失败。为遵守“不 force push、不移动已有 tag”的约束，r2 保留为历史对象，最终身份改用 r3：内容与 r2 相同，仅修正补充包内部清单 schema 与随之更新的 hash 绑定。
