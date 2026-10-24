# MRV2 持续开发阶段总结

本轮R4：20261023T121157Z_R4_node140_c8776394；node-25-140。起点2026-10-23T12:11:57.418651+00:00，原deadline22:11:57.418651+00:00（北京时间10月24日06:11:57）；更新2026-10-23T21:42:39.890362+00:00，恢复/中断未重置。完整产品适配目标尚未完成，public Graph Gate保持冻结。

## 实际完成了什么

1. 从101 C28接管到140，核验本机SQLite、独立worktree/native来源、设备映射；C29只修后8授权合同，真实配置/模型/B0/前哨在140通过。没有覆盖101或PR工作树。
2. 8K真实请求发现两个环境临时目录错误和一个production continuing-prefill错误；环境绑定到本任务本机TMPDIR/TRITON_CACHE_DIR，C32修正phase dispatch，保留Window数学、Target/Full绝对写、decode Graph与UPDATE顺序。无新增逐代同步。
3. C33重新取得完整12场景连续数值/ABA（全元素误差0）、Target4 ON/OFF完整12对（输入/metadata/KV前态、输出/KV后态和写集合）、LIFE21代串行诊断。均保留源SHA，串行参考/同步不升级正常重叠安全。
4. C34安全Python故障实际贯通Runtime.publish_metadata内部store失败→failure handler→外层C1 quarantine→Host下一scope拒绝；前置边界点也单独运行。专用checker结合退出码74、PID、generation/backing、lease/guard和产物hash，未用退出码单独通过。未知native部分提交未模拟或恢复。
5. 正常三臂短/8K各三次未采控制、三臂真实文本和三份long正常profiling，可靠采集接受率；Window ON存在实测回退，Graph相同Window有有限收益。没有宣布性能达标。
6. C35本地新增独立DFlash K15/Q16 fixture/真实CONFIG与具名方法锚点，以及6轮18组30请求的异构/替换稳定性工作量。具体最新状态见实验表，不把锚点当完整方法验收。117项定向CPU检查通过，保留新launcher路径冲突红反例。

## 候选与来源

开发/fixed最终候选C35 f00e423936c23b0710fc2b5cd367d34ec7736d26，tree 5383f503852c3e520bd10442ed7562e1df5a9a04。生产子树C32至C35完全相同。vLLM仍84030bbe3d74d99bad477a3d2e37a973ccd8865c/tree f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee，Python3.11.10、torch2.10.0、torch_npu2.10.0.post4、CANN9.1。模型和native逐文件manifest/worker实际来源索引独立保存。源码bundle在全新bare仓仅C28前置上已实际verify/fetch恢复，未push/merge或伪称发布VERIFIED。

## 执行计数（以最终更新的机器表为准）

当前已记录正式模型producer启动61次，含预期Graph Gate拒绝、profiler和失败；probe完成7次，fixture 4次，框架CONFIG 7次，正常profiler 3次。各层producer/artifact/checker/runner/supervisor分开记录。三次原始C30失败没有删除。统计不把Host UT当NPU，不把schema、probe或exit0当模型/Graph全面通过。

## 性能与接受率结论

|组|N/臂|G_OFF秒|G_ON秒|E_ON秒|ON相对OFF|Graph相对eager|
|---|---|---|---|---|---|---|
|short-1-257|3|0.697976|0.810960|0.972752|+16.19%|-16.63%|
|short-3-257|3|0.812098|0.908368|1.064195|+11.85%|-14.64%|
|long-1-8193|3|1.528133|1.613384|1.788194|+5.58%|-9.78%|

8K合成组接受率OFF84.94%、ON/eager86.90%；真实文本逐组差异明显，不能用99.55%重复token接受率当业务质量。TTFT/TPOT/ITL未导出则NOT_AVAILABLE。非独占整机，未跨机算代码收益。snapshot均值约7.365ms含等待，不能等同传输带宽；OFF也在metadata承担等待。细节、每次样本/工作量和真实trace依据见性能与profiling报告。

## 尚未关闭的具体问题

- 正常UPDATE/最后consumer/backing复用：已有具版本来源的五步源码合同，140真载runtime v100且哈希匹配；仍需平台/验收对安装分支与适用前提审查。不是笼统“没有平台API证据”，也不是直接执行证明。
- task execution occurrence/operand、physical read-set：当前导出不提供必要绑定，post-drain native参数与event flow不能替代。网页GPT独立技术评审包V2已提供；意见尚非正式批准，原要求没有豁免。负责人未明确处写待确认。
- DFlash完整数值/Target/生命周期、Eagle3 AR Graph、必需拓扑及具体特性组合、真实公开产品接入与最终非Graph PR固定组合仍有实现/验证缺口。没有把未实现改unsupported，也没有把原MRV1不支持的组合扩成任意笛卡尔积。
- 性能回退和质量/接受率产品阈值待定；当前只提出建议供确认，不能自行判达标。
- 当前引擎实际FULL_DECODE_ONLY；FULL/PIECEWISE等模式没有因decode descriptor叫FULL就获得本轮覆盖。

## 资源与恢复

本轮只领取Phy8 TP1，后续整个空闲16单元使用授权未被用来预占设备。每段fresh probe/check/bind/原子租约；前八他人任务不处理。最终进程/租约释放以NEXT_SESSION_HANDOFF和最终实时清理证据为准，当前仍在跑则不能写已释放。起点至第一probe约6小时的准备/CLI/中断均计入本窗口，日志缺口不能伪造为精确的单项等待统计；本机没有占用PR TP16窗口。

下一会话先读取本目录RESUME/NEXT_SESSION_HANDOFF与state/R4_SESSION_STATE，检查实际进程、来源和期限；过期授权不能自动续用。最小后续工作按DFlash真实锚点结果补同Window连续数值与Target方法合同，推进Eagle3/拓扑范围；平台/最终PR基线问题继续具名处理，不能重复原C19或本轮整套campaign凑数量。


## 收尾补充

C35三臂DFlash锚点全部接受，Graph OFF/Draft ON的实际replay为98/90，eager为0，Target replay94/87/87；独立配置[16,32,64]，不归到DSpark Target4。全部三组输出在G_ON/G_OFF、G_ON/E_ON之间相等，仅支持该端到端greedy覆盖。完整方法数值/Target/LIFE仍缺。

C35稳定性18组/30个唯一请求ID、7680实际输出tokens，1974次活跃Draft replay，实际[1,7]/[2,14]/[4,28]切换；6轮相同组输出和接受率序列均一致，实际S>0与超W全读行几何被记录。逐行scheduler phase枚举未导出，不从输入长度替代全部mixed证明。资源曲线为全case粗采样，含初始化/预热，Host RAM逐请求趋势NOT_AVAILABLE，不能据此证明无界复用安全。

正式模型启动61次：成功服务50、预期GRAPH_FROZEN拒绝6、预期Python隔离异常2、原C30异常失败3（环境2/production1，已修复）；正常profiler3属于成功服务的子集，不重复相加。另probe7、私有fixture4、framework CONFIG7、只读P0六次。离线新增12对Target联合比较、三份trace解析和一组3份输出小样本重算，均不算新NPU模型。
