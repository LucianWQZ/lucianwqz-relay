# 服务器 Codex CLI 启动提示词模板

你将接手 MRV2 Draft Sliding Window 的非 Graph 开发。先不要修改代码或使用 NPU。

1. 显式读取本任务目录中的 `00_先读这里.md`、`01_最终需求与验收范围.md`、`REQUIREMENT_MATRIX.csv`、`03_代码起点裁决.md`、`CODE_STATE.json`、`04_架构兼容与待解决问题.md`、`05_服务器接管说明.md`、`NEXT_SESSION_HANDOFF.json`、`服务器恢复入口模板/CURRENT_STATE.md`、`TASK_QUEUE.md`、`OPEN_QUESTIONS.md` 和 `DECISIONS.md`。
2. 按 `代码恢复材料/README_恢复代码.md` 在新的独立目录恢复双仓，核对完整 SHA/tree、clean、fsck、无 alternates；不要修改 `reference/` 原件。
3. 在两个恢复仓中读取实际适用的 `AGENTS.md`、固定版本 MRV2 design、Ascend patch/testing 与本特性设计文档。固定 paired vLLM，不追最新 main。
4. 把 `服务器恢复入口模板/` 复制到 `dev/pr/state/` 后再更新；填好源码、runtime/native、模型和资源合同。`authorized=false` 时不得启动设备实验。
5. 第一个有界问题是 `DW-A01`：先核实 fixed ABI、exact-length consumer 和同步频次，再决定最小局部实现。不要用 upper/旧 generation 代替 exact，不要把同步搬家或伪装为 non-blocking。
6. 保留最终范围：Eagle3、DFlash、eligible DSpark、forced-OFF、Async、FlashComm/SP、prefix/chunked/mixed、required backend/multi-gid、legacy DSA-CP 缺口、共享 MRV1/Target Graph 回归。PCP 不替代 legacy DSA-CP。
7. 每次生产修改形成新的有意义提交和 SHA/tree，列出失效的旧证据；设备运行固定源码/环境并按 run_id/attempt 保存。不得在冻结 checkout 热补丁后沿用旧候选身份。

先输出：恢复核验、当前事实、资源是否授权、DW-A01 源码/ABI 调查计划和唯一实际阻塞。不要把 Host PASS、远端 fetch 或历史报告写成当前 SHA 的 A3/性能 PASS。
