# 性能与接受率（R5）

## 同SHA C59最终16K控制

16385输入、512输出，TP1，三臂各预声明3次，平衡交错顺序，所有组预热；Target策略均Graph，E_ON仅Draft eager。全部原始cell及失败保留。

|arm|有效重复|elapsed中位ms|范围ms|
|---|---:|---:|---|
|G_OFF|3|4125.66190|4103.996–4141.586|
|G_ON|3|3903.79164|3890.653–3904.585|
|E_ON|3|4293.73922|4266.539–4299.292|

Window_ON_vs_OFF：elapsed变化-5.3778%；完整3重复=True。

Graph_vs_Draft_eager_same_Window：elapsed变化-9.0818%；完整3重复=True。

接受率定义来自pinned scheduler/stats原文：proposed为实际调度proposal，不含padding；accepted不含bonus。平均接受长度含bonus=1+accepted/verification_request_steps。调度统计发生在最终stop/max_tokens截断之前，所以不能要求accepted+steps等于最终输出token数。

逐cell实际proposed、accepted、verification、Draft/Target replay、裁剪状态见Summary和CSV；分位置计数在完整JSON acceptance_per_request内。TTFT/TPOT/ITL均NOT_AVAILABLE；未用总elapsed倒算。原框架CPU统计未新增D2H/sync采样。CPU/RAM逐cell峰值NOT_AVAILABLE，准入与外部SMI背景保留。

## C52同轮历史控制与优化定位

C52原生16K：G_OFF/G_ON/E_ON中位4147.1237/3894.07557/4294.29099ms；ON比OFF elapsed低6.10177%，同Window Graph比Draft eager低9.31971%。OFF accepted/proposed=414/721(57.42025%)、验证103；ON与E_ON=426/595(71.59664%)、验证85。输出512token IDs相同；Window收益包含验证轮数减少，不能全归FIA kernel加速。

single-metadata默认关闭原型：3重复，8K elapsed约−1.8334%、short1−2.1825%、short3−3.4127%。省去未用metadata构建，exact snapshot仍约8ms等待；未获得全矩阵资格，保持默认关闭。

R4短/8K ON回退16.19%/11.85%/5.58%保留，不与140 R5新文本/长度混作同负载代码收益。不同SHA分表，不合并中位数。

## 解释与边界

有限重复、同机非独占背景；本任务控制期间无自身并行重负载，不能保证其他用户完全无干扰。长16K是真实中文技术文本，模型配置maxpos40960、runtime max_model_len24576，未擅改RoPE；不外推32K/128K或其他模型/拓扑。性能阈值未正式批准，测量完成不等于业务达标。完整数值/生命周期结论与性能分开。

## 最终输出复核

C59九个实际输入token IDs和512输出token IDs全部一致，复核原件为C59_performance_output_identity.json；这不是中间连续数值或Target KV检查的替代。
