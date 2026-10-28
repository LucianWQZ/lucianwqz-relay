# MRV2 Draft Sliding Window Graph：R6续跑阶段交接

更新时间：2026-10-28T02:44:24.974155+08:00；实际机器node-25-140；实验SESSION `20261024T195020Z_R6_node140_3bf24139`。这不是Codex会话UUID。

## 一页结论

最终开发候选C204 `06fafe0da5f690bbd7accb21984063b53fb60031`，tree `95496f41d5d1ef0cdf297ce15b8c5217f3c9e98d`；production subtree `ab16df434d92217bd751651cfe55303aab097cdb`。配套vLLM `84030bbe3d74d99bad477a3d2e37a973ccd8865c`、tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`。开发树/固定候选保持干净；运行时native单列manifest。本窗口不push、merge或开放public Gate。

**工程整体未完成，NOT_READY；管理估算58/100，不是验收通过率。** DSpark主线不是只完成探针：已有真正GLM TP16官方CLI/HTTP、Draft capture/replay、CP数值/Full写/Target联合、真实调度和三臂性能。DFlash及Eagle也保留真实方法证据；不能将旧模型/旧producer全部改标最终候选PASS。

本轮新增或收敛：

- C147 GLM DSpark CP两臂全16rank×14样本及224对Target；C151三臂真实调度/服务，C157 eager双lane完成事件/回收及已有Python异常隔离，按原身份复用。
- C159/C164 GLM DFlash14场景与224对Target；Qwen3.6 Full8 TP4/DP2服务；C195真实Draft eager参考纠正后、C196只读checker重算接受4rank×3样本。原错误参考与INVALID保留，无重复加载补PASS。
- Eagle旧C59 K后态差异由C61外部持有post目的地修复，C91旧profile42consumer/ABA及Target14、C100 LIFE/异常证据有效。指定Qwen3.6 TP2另外完成C190两臂自然请求锚点。
- C199新V前态异常由C200外部持有prestate修复，同Graph旧池快照仍坏、owned参考通过前6consumer/rank。**C203仍失败**：第7四请求first，generation105/epoch35，两个输出各7296/32768有效BF16元素差、max0.3125（−15.0625/−15.375）；所有K/V前态恢复及后态精确。owned输出与同Graph旧引用相同，输出引用覆盖假设未成立。保留C200原7009/max0.5，不放宽、不归Q017。
- C185完整两启动块/臂×3同实例重复，72组108正式请求；C204新增32K/2000/c1 pilot：OFF自身40分钟timeout但有1完整正式组474.264秒；ON三组196.959/196.341/196.691秒并经外部checker/all16关联限定接受。E_ON本pilot因时间预算NOT_RUN。两组不混成正式平衡性能PASS。
- C184/C186/C188来源判别为D：原生调用层异常成立，但准确API合法性/完整官方模型可比路径未证，未认定平台缺陷；SWA正确性及正式性能继续阻塞，未继续无新假设探针或底层修复。

## 当前真正剩余

以下按缺口分组列出，执行优先级仍为DSpark→DFlash→Eagle3，不是把Eagle移到首位。DSpark先审已有具名合同/轨迹与32K匹配E_ON预算；确实依赖外部答案的分支才等待，独立后续准备继续。

1. Eagle四请求有效输出差异：先一次保存真实attention Q/输出和完整调用参数，区分attention前计算、实际绑定、eager参考上下文，再决定必要Ascend修复。不能先排除第二请求或接受小误差。
2. DSpark自然轨迹/跨padding验收合同、正常Graph reader/backing证据适用性仍待技术裁决；C158/C151原FAIL保留。C160首层Native复现不能解释全部后续差异。
3. Qwen Full8扩展数值/Target/正常reader；SWA API/归属；GLM DFlash加载质量Q023适用性/最终组合；指定Eagle Target/ABA/正常生命周期/性能尚缺。
4. 最终Graph/PR固定pair未批准；PR238c7589/pin a982与Graph84030bbe不同，0be加载修复仍独立。Graph独有缺口不阻塞先交Draft eager PR，共用加载问题只交接具体提交/风险。

## 时间与资源

原T0北京时间2026-10-26 15:21:18.369；硬截止2026-10-28 03:21:18.369，至少02:36:18.369收尾；迁移/等待计入，未延期。当前NPU、writer、dispatcher和lease核查见 `final_process_lease_audit.json`。停止新设备派发，未达标不自动续期。CPU/NPU/等待可能重叠，case elapsed包含加载，不据此推算人工工时或纯NPU时间。

## 如何审这份交付

先读本页、正常合同、性能报告和Eagle首因报告，再看完整Target join与原始小张量。`evidence/hidden_outputs_C195_C200`、`evidence/hidden_outputs_C203`可用标准库offline_recheck.py复算有效输出，**不是完整KV artifact**。原始tensor/trace留服务器并以索引追溯。bundle明确依赖官方Ascend基线52ce43b1，已实际恢复；包完整性/CPU复算/完整模型NPU验证三者分别声明。
