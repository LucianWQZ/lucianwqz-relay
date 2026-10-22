# MRV2持续开发阶段总结

更新时间：2026-10-22T18:03:56.191386+00:00。会话20261022T132626Z_R2，原起点2026-10-22 13:26:26 UTC（北京21:26:26），任务截止23:26:26 UTC（北京次日07:26:26），没有重置。全部本任务设备链在17:58:28 UTC结束；后续整理与交付时间仍计入本轮，最终封装时间见DOWNLOAD_MANIFEST。

## 最重要的进展

**最终固定候选C19 `da5b0f054c4b94362ff3539de911b26b4074052a`，tree `af4519a635d6ccd70646f77195fde18368bdf22b`。** 本轮七个本地提交，无push/merge/远端发布。node-39-101，主线仅宿主Phy0、visible0→logical npu:0、TP1；pinned vLLM84030bbe3d74d99bad477a3d2e37a973ccd8865c、torch_npu2.10.0.post4、CANN9.1.0不变。

C19同一SHA真实完成P0/私有fixture/CONFIG/A0/A1/B0、三代数值前哨、完整12连续数值/ABA、受控Target4双臂12对、21代LIFE、15个FIA原生参数块逐层绑定、四ABORT、四真实Python异常展开。每项有独立plan/launcher/准入/producer/storage/joint/runner记录；不是仅exit0或相同greedy token。

Graph正式支持尚未建立。**public Graph Gate保持冻结**。本阶段已形成限定范围代码和证据材料；正常多代合同与task/physical-read验收仍需平台维护者和验收owner决定，整体状态BLOCKED_PLATFORM_DECISION。没有降低标准。

## 从C12起点做了什么

- C12固定源码原先没有runtime/设备计划。本轮从成功C8 donor恢复必要运行产物，1223项、69262708 bytes，核验hash，未覆盖tracked业务Python。生成_build_info.py作为构建元数据单独披露。C12于13:31 UTC准备，随后真实fixture capture/UPDATE/数值退出通过。原准备manifest中的pending是当时状态，最终结论由实际case结果补足，不篡改原manifest。证据state/R2_C12_RUNTIME_OVERLAY.json、raw/C12_prepare_01/C2及C12_fixture结果.json。
- C13修复ABORT runner误用旧checker命令；保留C12四次原失败和C13四次只读复核。新增默认关闭的真实Python异常展开，实际进入C1 quarantine、保留backing并由Host guard拒绝后续使用；与os._exit故障点分开。
- C14/C15增加默认关闭Host细分、有限重复方案与成功LIFE后有界原生JSON导出。C15取得完整12数值/ABA、Target4十二对、LIFE/四ABORT/四Python展开和正常profiling，均保留C15身份。
- C16严格解析本版本FIA参数布局，增加capture handle/event与K/V指针关联；Host88通过、probe03通过，但无模型。外部wrapper路径错误及自动审批拒绝分别留证。用户明确确认预约有效到北京10月23日10:00后，经正式审批恢复；任务截止仍不延长。
- C17披露SDK verbose内含同步参数块D2H、ts/dur为合成布局；真实LIFE通过，但新增导出误要求K/V为list。首因是实际full_graph_fia与pinned weak_ref_tensors保留单Tensor；原EXPORT_FAILED和INVALID_EVIDENCE均保留。
- C18修准入必需分类的集合漏检，10项定向Host及真实计划派生损坏反例证明旧接受/新拒绝。C19只归一化Host元数据的单Tensor/list容器，保持生产入参、strict native ABI和数值容差；45项Host后在新固定候选取得15task真实绑定。

整个vllm_ascend production Git子树C12→C19完全相同。未发现足以据此改动正常所有权/同步的明确生产反例，未将LIFE同步、upper_bound替代或新的D2H插入正常路径。历史非Graph/其他方法的状态未推断为全矩阵通过。

## 最终候选的正确性与生命周期

连续数值12样本均PASS、finite=true、max_abs=0，原atol/rtol仍0；current_match及必要KV一致。涵盖A/B/A′、短/长/边界/非对齐/mixed/padding/回短/active3-padded4/active4。input_ids实际int32，positions仍int64；DSpark noncausal及padding输入offset[0,7,14,21,21]、FIA query[7,14,21,28]合同保留。逐样本CSV及原producer/storage/joint关联可复查；CPU小包仅重算保留输出和ABA，完整KV/调用独立性仍需服务器原件。

受控Target4 ON复用NUMERIC_TARGET4的真实12样本（含串行连续参考），OFF独立12样本，显式--on-case联合比较12/12对完整。控制阶段为CONTROLLED_DECODE_SYNTHETIC_PRE_KV，实际运行真实Target FULL图；输入、metadata、完整层集合、KV前后态和写集合按原合同检查，hidden/logits零差。target-join自身authorized_device_acceptance=false保留；设备授权由两臂实际inspect/check/bind/runner单独验证。comparison.completion/physical_read未改成PASS。

Base[7,14,28]与Target4[7,14,28,32]分开。本轮实际Base Target库存只有(1,8)/(2,16)，缺(4,32)；Target4有该桶。B0的Draft锚点不构成Base完整Target验收；未新增eager回退或伪造bucket。

C19串行LIFE21代与原生绑定case各有独立过程，额外普通event/synchronize/D2H明确记录。15个FIA参数块以实际capture handle/event确定层，再按K/V pair匹配task，Q/table/output/shape/dtype交叉验证。原生KV末值28区别capture1151并唯一匹配Host末代6/13/20，结论限POST_DRAIN_EXPORTED_PARAMETERS_ONLY；不能填成native执行代际。

四ABORT专用checker/runner接受exit73；四Python展开接受exit74，真实quarantine调用一次、backing保留、下一scope.body_entered=false，未知分支故障后无新设备操作。before_replay仅本次replay未调用，materialize可能已有设备操作；after_replay/update完成未知；after_completion先有诊断drain。不能声称模拟了native部分提交或可恢复。

## Profiling与性能结论

C15六个long控制和三次正常采集、C17一个short控制与两次normal/LIFE采集全部留存。本轮共5次profiler采集，C6旧四采集四控制仅历史引用。

OFF-long三次1613.452/1648.560/1648.347ms，ON-long1735.166/1770.531/1767.755ms；各15请求240tokens、47 Draft/30 Target Host replay，旧5152.6ms OFF控制未复现。缓存/shape/顺序是旧异常的候选原因，缺旧控制trace不能定因。没有从不同工作量或3个样本宣布加速率。

ON-long实际S列8（1024tokens）裁剪。47个materialize外层mean11.517ms，精确snapshot mean10.186ms约占88.4%，p95约35.693ms；不能把CPU快照总阻塞全归D2H传输，未删除精确检查。嵌套runtime/workspace/build不重复相加。

C17 short同外部7请求112tokens、21Draft/12Target Host replay：控制669.664ms、正常profile763.094ms、LIFE29929.465ms。LIFE含observer、Host序列化/I/O和额外同步，不能当正常路径性能。原parser direct范围21条实际共63条event/queue流，目的地MODEL_EXECUTE直接边0；完整原结果和目的地分类均保留。缺acceptance/全部verification/每层device归属/physical read写NOT_AVAILABLE，未填0。

## 正常UPDATE/backing还缺什么

本轮已查明精确op-plugin复制Host长度vector、9.1 Runtime Stars/v100及endGraphNotify流内完成边，实际worker加载相应库；ExecuteAsync源码拒绝AICPU executor。正常顺序报告给出五步跨代依赖推导，问题收窄到完成/事件更新合同适用性。没有以Host return、retire、Target较早copy或进程退出替代设备完成。

native verbose确实从Device参数块同步D2H，但不是FIA实际KV read-set；ts/dur是合成布局。维护者/验收owner需决定源码合同与具体launch/task/physical-read证据如何满足既定门槛。平台问题单列出具体API、两种假设、已有证据、可行方案及影响；未向任何人自动发送。

## 执行统计与保留的失败

正式模型launcher启动72次：producer正常exit0 39，预期GRAPH_FROZEN拒绝5，os._exit注入16，Python展开注入12，其他模型启动/运行失败0。正常退出不等于验收PASS。

runner接受67次（包含预期拒绝/隔离），验收失败5次：C12旧ABORT runner4次与C17 native export1次均保留。另有4个准入前失败/错误，无模型：C13资源占用、C15授权文件hash变更、C16两个wrapper路径错误；审批拒绝未创建进程。

NPU短探针4、私有FIA fixture5、profiler5分别计数；只读联合/复核7次不是新NPU。两份小型CPU数值复算亦不是模型实验。矩阵保留orchestrator/runner/producer/artifact/checker各层。

外部监督脚本曾仅补offline计数，exit时文件hash不等于加载代码hash；已从早期B0 hash精确恢复前版本，证明只有status_event计数函数变化。原execution不改，两个脚本快照及哈希范围审计保留。固定candidate/committed runner/producer/checker和argv不变。

## 资源、交付和下一步

18:00:40 UTC只读核对164个本任务已知PID无残留，npu-smi成功且NPU0无运行进程；该观察不等于物理完成证明。未kill他人、reset设备或改变共享栈/权限。仅使用Phy0，未扩展TP16或其他特性。

raw：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261022T132626Z_R2/raw；/mnt/wenqing/mrv2_graph_server_dev/20261022T132626Z_R2仅缓存。挂载/可写/空间与未知quota在STORAGE_BINDING，逐case预算基于实测C15产物5.5GiB，不复用旧500GiB门槛。没有上传新数据到公开relay。

最终审查包位于唯一return/20261022T132626Z_R2_da5b0f05/，自检后更新LATEST.json。bundle前置精确Repair7，已真实恢复SHA/tree；无凭据/模型。review含必要反例、原生参数、准入、逐样本结论与小型CPU复算，完整tensor/trace留服务器。服务器自检与用户接收校验分开。

下一轮最小工作：维护者确认正常多代依赖/部分提交合同；验收owner裁决既定task operand/physical-read证据方案及Base/Target4支持范围。只在新假设或代码变化时补有判别力验证；恢复先核对进程/原deadline，不重新探索或重置预约。
