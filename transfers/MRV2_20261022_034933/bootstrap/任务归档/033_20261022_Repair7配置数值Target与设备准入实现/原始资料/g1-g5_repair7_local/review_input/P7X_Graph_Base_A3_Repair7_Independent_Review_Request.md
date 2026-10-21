# Repair7 Independent Review Request

请反驳候选，而不是同意报告。基线fd0716c59562f64262672de12e4ae26259908d0b；候选7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14；tree6dd40a67a500480556068be8b6ebcd977e3cc3e8；parentfd0716c59562f64262672de12e4ae26259908d0b；branchfix/p7x-graph-base-a3-repair7。pinned vLLM 84030bbe3d74d99bad477a3d2e37a973ccd8865c / f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee。未发布未设备运行，Gate冻结。

优先阅读handoff→完整diff→生产config/DSpark→tools repair7/config/campaign/device→runner/numericchecker→真实结构测试→raw重算两臂结果。ZIP不含6.7GB raw；Raw_Sample_Index和receiver hash说明外部证据边界。

重点攻击：
1. 严格Ascend schema/factory是否真修；false字符串、未知键、DSpark/W1024 scope、默认无设备操作；完整EngineArgs未执行是否诚实标记。
2. CONFIG逐组合是否使用真实driver kwargs；framework全局环境/缓存是否影响跨配置；实际模型是否安装全部numeric/lifecycle/Target4组合。
3. capture NONE引用、真实SUBMITTED生命周期、同代hidden、独立Window数学；共享backend错误可否两侧同时漏检；sentinel不得冒充12case。
4. 最终Target join run/attempt/profile/arm/fixture/source/launcher/artifact是否齐全；失败优先级；旧Phy8不能批准授权0–7。
5. owner辅助receipt是否足够防误用；原始映射语义/workerPID仍需人核对，不接受工具自报自动物理证明。
6. first cause、数值3、未知native74、timeout、用户中断、expectedabort、partial、两个attempt前禁止COMPARE、跨run依赖是否能绕过。
7. 不要把Host PASS、LIFE诊断drain、最后drain等同normal-overlap reuse；UPDATE N/N+1平台问题是否仍开放。
8. package PRE_PUBLICATION、原fixture、最终hash、所有实际CLI及独立profiling分支是否一致；小scoped campaign能否减少下轮入口阻断。

Finding格式：ID / Severity / Source file:function:line / Facts / Minimal reproduction（注明native替身）/ Impact / Proposed minimum fix / Required regression / Device-only uncertainty。
裁决建议区分CODE_DEFECT、TOOL_DEFECT、DEVICE_NOT_RUN、PLATFORM_SEMANTICS、OWNER_DECISION。发现可静态证明的bug不得推给NPU；缺设备事实也不得猜测重构。
