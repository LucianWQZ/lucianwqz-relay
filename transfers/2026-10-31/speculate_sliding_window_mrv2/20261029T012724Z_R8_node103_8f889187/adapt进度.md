# Graph任务进度

<!-- NODE101_CURRENT_BEGIN -->
更新时间：2026-10-30T20:42:27.864127+00:00（UTC）  
主机：**node-25-140**  
当前状态：**设备窗口已结束；C302限定检查通过，C304代码及交接包已校验保存；无活动实验。**  
当前动作：CPU联合已于20:40:21 UTC退出0，用时2184.841360秒；16rank×3对全部通过。没有模型、worker、checker或后续派发器运行；本次代码/证据收尾已完成，等待后续指令。  
设备：**本任务NPU进程及租约已释放；本窗口不再派发**。CPU wrapper2112418/checker2112420亦已退出；完整清理审查见 `C304_final_release_audit02.json`。不宣称整机没有其他任务。  
候选：开发/纯生产 **C304 f25dce7e7f4f31ec2d0057257fca5d805e2ad70c**，tree **38e19e4be80b11c232bd52e3fbc7f381ec566025**；实际producer/checker **C302 1fd6da87ae146cd87cff35bee9c9f0011372da04**，生产仍C301 b10f59bc。C304仅新增Eagle普通入口未验拒绝，不改DSpark/DFlash/DFlash2；原结果不重标SHA。底座 **017cfca1 / vLLM544f182d**。  
截止：T0 **2026-10-30 00:39:27 UTC**；派发收尾 **19:54:27 UTC**；硬截止 **20:39:27 UTC / 10月31日04:39:27 +08:00**，均已到期，不重新计时。CPU联合按明确授权在设备截止后完成。

**整体管理进度95%，可信度中等；统一017/544候选仍 NOT_READY。** 这是原权重累计证据覆盖，不是544验收通过率；本次复验不重复加分。

当前主要缺口：①新544的GLM DFlash正常Graph/零提议及受影响eager资格未测；②新组合真实服务/正常reader适用性仍需受影响路径定向核验；③新544性能未测，完整旧C273四档12格仍仅属534/a982。Full8/Eagle新544普通入口及精确SWA checkpoint Graph关闭，原失败保留。

下一项可验收结果：新的有效设备授权后，先执行已准备且禁用派发的C303 GLM DFlash G_ON正常功能/零提议资格（TP16，约35–45分钟/臂）；随后受影响eager与必要匹配性能。当前不启动它。完整Target48：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C302_CP_Target48_readonly_01/C302_OFF_ON_Target48.json`，SHA256 **fe89893165f255f1ffcaaa9e2a7568063fdb653f00206cccfcb63f8ce623189e**。
<!-- NODE101_CURRENT_END -->

## 阶段总览

“已计贡献/权重”统一为**总体百分点**，不是阶段内部百分比。各剩余项共享原目标余额，不重复计数。

|阶段|状态|已计贡献/权重|当前剩余重点|剩余时间估计|所需资源|
|---|---|---:|---|---|---|
|公共基础与policy|原具名公共验收项限定关闭|10/10|仅实际新增共享行为触发回归，不重复预扣最终集成|当前无独立设备待办|CPU；按实际diff|
|阶段一：GLM DSpark|旧534/a982具名项和四档三臂完成；新017/544定向资格进行中|65/65|实际缓存/接口/owner改变后的数值、Full、Target及复用；必要新组合性能对照|限定CP联合已完成；后续设备需新授权，按实测TP16约20–35分钟/最小资格|TP16；旧12格不重标新版本|
|阶段二：GLM/Qwen DFlash、约定SWA|旧GLM具名项已完成；新544调用待资格；Full8未开放|11/12|GLM受影响Graph调用；Full8普通单请求资格；指定SWA维持拒绝|当前设备收尾；GLM后续TP16约35–45分钟/臂，Full8未开放|TP16/TP4顺序执行|
|阶段三：Qwen3.6 Eagle3及policy|旧a982有限六consumer/普通HTTP已通过；新544 zero/AR接线待定向资格|6/8|新组合实际first/AR与临时形状保护；四请求仍拒绝|Host已完成；新设备窗口TP4约10–20分钟，普通服务另验|TP4；不做原生重复探针|
|最终交付：组合、集成、审阅|017/544生产C304固定，八DCO链独立恢复通过|3/5|C302限定联合已通过；实际normal零提议及必要共享eager回归仍待设备；支持边界/交接|CPU交接；后续设备需新授权|CPU＋必要TP16|
|**合计**||**95/100**|完整目标NOT_READY；受限基础版收尾中|||

## 公共基础与policy

### 已完成

已完成Window读取视图、canonical Full写入和既定方法policy的限定实现/验证，对总体已计 **10个百分点**。

|完成事项|适用候选与范围|证据入口|
|---|---|---|
|Window只改变Draft读视图；OFF/forced-OFF保留；完整positions/slot语义|各原producer与方法合同，未自动覆盖所有新组合|[总报告](adapt_任务总报告.md)、[冻结设计/来源核查](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/DSpark_requirement_and_evidence_reconciliation01.json)|
|持久输入所有权与已观察错误修复|C138 Target CP地址修复；原C136失败保留|[冻结交接](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/return/20261024T195020Z_R6_node140_3bf24139/transfer_101_to_140_20261026T140253Z/GRAPH_TRANSFER_101_TO_140.md)|
|原公共CP Full写缺口关闭|C147 TP16×14 Full写和Target224已成立，当前Source核心policy/math/Full-provider属性未变；不扩成方法原FAIL通过|[原余项来源](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/reports/20261024T195020Z_R6_node140_3bf24139/adapt进度_旧格式归档.md:21)、[人工映射](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/manual_review/adapt_人工后续核查.md)|

### 待完成

本目标原具名余项“新CP路径Full写尚未裁决”已由C147关闭，并核对当前未变公共属性；当前没有独立基础实现/设备待办。未来真实共享行为变化才补受影响回归，不为尚未形成的集成diff重复占用此目标额度。

|事项|状态/下一步|完成判据|资源|预计用时|可增加的总体百分点|
|---|---|---|---|---|---|
|新增共享行为的必要回归|按实际diff触发；当前无具名新增缺口|OFF/forced-OFF、Full写及拒绝/warning保持约定|按diff|不预设额外设备工时|0；已计满10|

## 阶段一：GLM DSpark完整Graph路线

### 已完成

已完成可比前态数值/Full写/ABA/Target、实际TP16全特性服务、正常reader限定工程合同、C248/C249退休异常保护及平衡测量，对总体已计 **65个百分点**（数值20＋服务25＋生命周期10＋测量10）；成功收尾异常经C248实际DEV与C249真实worker证据已限定关闭，恢复原暂扣1点，原反例和边界保留。

|完成事项|适用候选与范围|证据入口|
|---|---|---|
|新534/a982四档三臂测量与受改eager能力|C273同机TP16、实际16000/32000/64000/128000，12单元、三臂各16正式请求；全部整臂通过。每格一次无波动估计；初始失败/强制API清理原件保留|[12单元复算](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C273_final12_http_rollup.json)|
|新534/a982组合CP关键回归|C272 TP16两臂各0/10/2三样本，C274只读严格联合及Target48 PASS；sameproduction4cd05，不外推全14矩阵|[Target48](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C272_CP_subset_readonly_C274_01/C272_OFF_ON_target_join_newchecker.json)|
|CP数值、Full写、ABA与224对Target|C147 TP16×14；C158同M前哨；串行诊断，原容差不变|[C147完整联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C147_CP_Target_14_all_rank_join_01.json)|
|三臂真实服务/调度、prefix命中、chunking、legacy DSA-CP/Async/SP等|C138服务/C140配对、C151各16rank12请求（6正式＋6预热）及实际阶段。FlashComm有效配置/适用Source与独立kernel观测分开|[G_OFF服务PASS](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C151_glm_actual_phases_G_OFF_01_node140/http-artifact-joint.json)、[G_ON服务PASS](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C151_glm_actual_phases_G_ON_01_node140/http-artifact-joint.json)、[E_ON服务PASS](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C151_glm_actual_phases_E_ON_01_node140/http-artifact-joint.json)、[当前来源核查](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/DSpark_requirement_and_evidence_reconciliation01.json)|
|正常Graph最后reader/复用限定审查与已有异常隔离|Source/API、C151正常绑定、C147数值/Full写/Target和C148既有异常有效；新成功收尾reset抛错缝隙已由C248/C249实际反例/worker联合限定关闭，保留原失败。C157 eager完成不冒充Graph|[正常Graph收口](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/DSpark_normal_Graph_scoped_engineering_closure01.json)|
|平衡三臂正常测量与32K缺臂|C185每臂2实例×3重复、72组/108请求；C20432K E_ON补3组。不是发布性能PASS；32K仍不平衡pilot|[C185逐次原始表](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C185_matched_performance/summary.json)、[32K](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C204_32K_missing_E_ON_result01.json)|
|自然轨迹合同与有界原件审查|C151同Window5/12相同、7/12不同；257输入第38token首分歧，两臂active/padded=1/1与2/2是真实batch差异，均未裁窗。36 SSE的ID/采样/token/框架计数未见具名新错误；不证明全部差异原因或业务质量|[已采用原答](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C151_trajectory_acceptance_boundary_decision01.json)、[有界复核](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C151_bounded_request_and_verification_review01.json)|

### 待完成

旧534/a982 DSpark具名工程/测量项已在各自限定范围关闭，原贡献65点已计满。新017/544只重开实际缓存/接口/owner受影响的代表性数值、Full写、Target与复用；旧C147/C151/C185不重复。自然轨迹差异仍是独立质量限制，正式发布和最终PR组合另待用户审阅，不把它们改写为数值PASS。

|事项|状态/下一步|完成判据|资源|预计用时|可增加的总体百分点|
|---|---|---|---|---|---|
|新544正常服务与复用适用性|两臂模型/单臂检查及完整Target48联合PASS；正常服务/零提议适用性待后续定向核验，C296原断言/exit74保留|独立原数值、Full、Target和复用合同全部裁决|当前CPU已结束；新设备窗口TP16正常路径|联合已完成2184.84秒；正常路径约35–45分钟/臂|0；不重复计分|
|自然轨迹与质量限制说明|C151等原差异和已决定可比前态合同保留，不无界追查|报告明确未知原因、证据边界与业务质量未评估|CPU原件复用|随最终交接|0；不作自动质量通过|

逐次执行operand与硬件physical read-set仍 **UNPROVEN/NOT_OBSERVED**；用户已接受限定工程证据方式，不等待重复裁决、不重复采trace。新的数值、绑定或提前复用错误仍须处理。

## 阶段二：GLM/Qwen3.6 DFlash及约定SWA

### 已完成

已完成独立方法合同、旧完整GLM矩阵及新534/a982组合的CP数值/Full写/Target48、正常Graph reader与受改E_ON功能；Full8旧范围保留，对总体仍已计 **11个百分点**。

|完成事项|适用候选与范围|证据入口|
|---|---|---|
|新534/a982 GLM DFlash两臂CP数值/Full写与Target48|producer C273、checker C278；原场景7/10/11各16rank，ON严格零差/Full写通过，OFF01-ON03共48对Target原判据通过。旧dtype INVALID、CPU01超时保留；CPU02 rc0/1620.543秒，不是模型重跑|[ON完整联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C273_DFlash_ON03_readonly_C278_01/ON03-joint.json) · [Target48](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C273_DFlash_Target48_readonly_C278_02/OFF01-ON03-Target48-joint.json)|
|新534/a982 GLM DFlash正常Graph服务与reader限定收口|C273 TP16/K15Q16/W1024，6预热＋6功能；每rank3稳定Q16 banks/430代绑定、498 Host提案，prefix实际命中及全部具名阶段通过。当前8前提按已接受Source/API＋实际绑定＋独立数值/Full/Target限定关闭；直接operand/read-set未观测，API FORCED_NOT_GRACEFUL不当device完成|[服务原件](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C273_R8_GLM_DFlash_TP16_required_features_G_ON_01_node140/http-artifact-joint.json) · [reader八前提](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/C273_GLM_DFlash_normal_reader_applicability01.json)|
|新534/a982 GLM DFlash同配置E_ON功能|C273 producer/checker/outer均0、模型1979.633469秒、16rank关联；6预热＋6功能，实际Draft eager/Target Graph及每rank2条稳定eager lane/413代通过。自身PID[]/租约RELEASED；不是正式性能或Graph完成证明|[E_ON联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C273_R8_GLM_DFlash_TP16_required_features_E_ON_01_node140/http-artifact-joint.json) · [退出与资源](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C273_R8_GLM_DFlash_TP16_required_features_E_ON_01_node140/result.json)|
|GLM K15/Q16完整14数值/Full写/ABA与224对Target|C159 producer/C164 checker，原加载身份；几何/未变代码属性复用，不改名为C208全部新PASS|[旧完整联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C159_DFlash_Target_14_all_rank_join_C164_01/joint.json)|
|必要QuaRot加载适配与受影响数值|C205加载代码；C207 OFF全16rank标记/请求；C208新加载两臂各16×3严格数值/Full写/ABA，48对Target联合通过。合成短请求3.61%接受率不当业务质量|[C208新加载Target48](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C208_loaded_Target_prefix3_join01/joint.json)|
|新加载GLM G_ON正常请求及reader限定适用性|C231 TP16/DP1/sync/prefixOFF、active1/padded1、5层Dense；12正式/4预热及16rank设备关联。Source/API完成链与C208连续性核对、未发现具名缺边，不拿HTTP/Host次数当完成|[C231服务小表](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C231_GLM_G_ON_service_result01/summary.json)、[正常reader限定审查](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/GLM_DFlash_C231_normal_reader_scope01.json)|
|新加载GLM多有效行数值/Full写和Target48|C239 OFF/ON各16rank×3原场景7/10/11；ON有效输出BF16零差、全5层KV/Full写、48对Target严格联合通过；未新增14场景/ABA/正常重叠结论|[C239完整联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C239_glm_loaded_multirow_subset/joint.json)|
|C241同底座HTTP三臂测量|每臂20正式/4预热、5次同实例重复/负载、16rank及producer/checker0；短Window耗时+7.14%、16K+1.71%，同窗Graph耗时−8.03%/−4.13%。固定单块顺序，不算正式性能通过|[本轮测量结论](adapt_任务总报告.md#glm-dflashc241同机三臂5次实例内测量已完成)|
|C244全特性OFF/ON真实服务|同TP16/DP1、K15/Q16、Async/prefix/chunk/SP/legacyCP；每臂6预热＋6功能请求、全16rank精确关联，producer/checker0。OFF无Window工作；ON实际裁窗/绑定、prefix命中及四phase成立。内部数值/正式性能另裁决|[OFF原联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C244_R8_GLM_DFlash_TP16_required_features_G_OFF_01_node140/http-artifact-joint.json)|
|C246 required CP/SP数值/Full写/Target＋C248同配置E_ON功能|C246所选3场景16rank×3、Target48严格通过；C248实际16rank/6功能＋6warm通过。C249退休隔离具名Source缺陷已限定关闭；不同producer保留身份|[当前总报告](adapt_任务总报告.md)|
|C244正常Graph reader范围核对|实际ON全16rank各400代/400 Host绑定，3bucket owner稳定，含72个continuing baseline；自然active/padded1/1、2/2、3/4。未发现具名新完成缺边，Source/API与实际owner支持限定工程结论；直接operand/readset未观测|[实际范围审查](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/GLM_DFlash_C244_required_context_reader_scope01.json)|
|Full8实际eager参考纠正与三样本数值|C195/C196 TP4各3样本，8层KV与有效输出零差异；原C191错误参考FAIL保留，不放宽容差|[完整外部联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C195_Full8_numeric3_external_C196_01/joint.json)|
|Full8 TP4DP2正常服务与具名reader|C165/C167 OFF、C172 ON真实8worker/EP8、8请求×256；当前Source/native连续性核查。Host绑定/事件合同和独立数值分别支持，非直接device occurrence|[C172原件](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C172_qwen36_full8_DP2_ON_service_01_node140/joint.json)、[reader核查](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/DFlash_Full8_normal_reader_scope_review01.json)|
|Full8 Target Full/GDN隔离|C209两臂TP4各3提案，共24提案/1920组件；10Full层K/V与30GDN conv/SSM已分配页及有效输入非干扰通过。不是独立Target forward/logits恒等或正常时序证明|[C209完整联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C209_Full8_Target_OFF_ON_join01/joint.json)|
|Full8产品DP2/W32768真实三臂能力|C221 G_OFF、C222 G_ON/E_ON，真实8worker/TP4DP2EP8、257/33025输入、两DP路由及实际模式/裁窗；每臂仅有限请求，不是正式性能/内部数值通过|[C222 G_ON](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C222_R7_Full8_TP4_DP2_W32768_G_ON_01_node140/joint.json)、[E_ON](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C222_R7_Full8_TP4_DP2_W32768_E_ON_01_node140/joint.json)|
|Full8 W32768独立数值与Full写|C224 TP4/DP1串行，各rank1条33025输入，8层/16KV部分；无Target联合/ABA/DP2正常重叠结论|[C224联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C224_R7_Full8_W32768_long33025_numeric_ON_01_node140/joint.json)|
|Full8真实文本首三次consumer|C227 TP4/DP1，同C225首差33025-token输入，terminal-prefill＋2decode、每rank3样本；原严格数值/8层Full写通过。非原DP2 Target前态/自然根因|[C227联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C227_R7_Full8_C225_real_prompt_first3_numeric_ON_02_node140/joint.json)|
|Full8有限匹配三臂测量|C217同候选TP4/DP1 W1024、257/8193输入各6观测；实际Target Graph、Draft模式按臂。窗口负收益与同窗Graph收益分开，非DP2产品性能达标|[完整逐次汇总](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C217_Full8_matched_performance/summary.json)|
|Full8 8K匹配配置的必要数值|C218 TP4各1条8193输入、maxlen12288，独立actual eager/canonical输出与全部8层/16KV部分Full写通过；不增加Target/ABA/正常时序主张|[C218联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C218_R7_Qwen_Full8_long8193_numeric_ON_01_node140/joint.json)|
|Full8四有效请求边界|C215 TP4各1条active4/padded4、32有效query，8层/16KV部分、独立actual eager与Full写通过；串行诊断，不新增ABA/Target/正常时序主张|[C215完整联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C215_R7_Qwen_Full8_active4_boundary_ON_01_node140/joint.json)|
|Full8 DP2共同特性服务与正常reader适用性|C254/84030两臂all8/两DP、prefix真实命中、四phase/ON裁窗均限定通过；local最大3/padded4。实际Source/API完成链适用性未发现新具名缺边，不冒充直接device完成或active8数值通过|[当前两臂服务](adapt_任务总报告.md#c254-full8-dp2共同特性offon两臂限定通过)、[reader范围](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/Full8_DP2_required_features_prepared/C254_required_normal_reader_scope01.json)|
|SWA6实际Graph长短锚点及原FAIL保留|C174/C176 OFF、C177/C178 W32768 ON真实TP4长请求锚点；C184/C186/C188原生异常保持D类：准确API/官方合法模型归属证据不足|[现有总报告](adapt_任务总报告.md)、[人工台账](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/manual_review/adapt_人工后续核查.md)|

### 待完成

本轮只补Full8有限单请求普通资格及支持范围交接；原三请求/DP2有效反例和指定SWA问题保留后续，不原样重跑。CPU准备约20–30分钟，TP4约12–20分钟；范围决定已明确，不再等待答复。原目标全部关闭且其他项不变，总体可由 **95%推进至96%**，并非获得临时批准即可加分。

|事项|状态/下一步|完成判据|资源|预计用时|可增加的总体百分点|
|---|---|---|---|---|---|
|Full8普通单请求资格|准备中：保留33025输入/W32768/TP4，顺序两个有限请求；现有prefix数值/Full/Target复用|实际普通Graph replay、真实请求映射、正常reader适用前提和全部退出；仅声明实际长度/形状|CPU＋TP4 Phy12–15|CPU20–30分钟；设备12–20分钟，不干扰正式性能（已结束）|共享本阶段剩余1点，关闭后核算|
|Full8临时支持范围|已决定：普通资格通过才开放实际范围；若有效FAIL或保护不可靠，本checkpoint全拒已授权|Source config与actual/padding保护、真实资格和文档一致；不静默fallback|CPU＋必要TP4|随单请求资格结果，不再等待答复|不因范围选择加分|
|Full8原active3/DP2及更大有效行|已观察有效输出/KV后态FAIL；原C285保留；新guard实际隔离，不再重派旧mixed/DP2队列|后续有具体局部修复/可判别证据才重开，原容差不变|本轮不占卡|待具体原因后估算|同一剩余额度，不重复计分|
|指定SWA checkpoint Draft Graph|正确性及准确API归属仍阻塞，精确checkpoint拒绝；不是因性能负向禁用|保留原FAIL和可转交材料，获得准确合同或本功能具体修复后再开|外部接口；本轮不重复探针|未知|同一剩余额度|

## 阶段三：Qwen3.6 Eagle3及对应policy

### 已完成

已完成新组合限定单请求数值/Full/Target及普通HTTP、正常reader工程合同，对总体已计 **6个百分点**。不是任意长度或四请求Graph已通过。

|完成事项|适用候选与范围|证据入口|
|---|---|---|
|新组合数值、Full写和Target隔离|C277 producer/C281 checker，TP4DP1，257/2051各firstQ4＋AR1/AR2 Q1，4rank×6consumer严格通过；每rank2proposal×80 Target组件同proposal未污染|[联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C277_Eagle_single_readonly_C281_01/joint.json)|
|有限普通HTTP及实际Graph dispatch|C286，TP4DP1EP/K3/W1024，257/2051各out32，两HTTP通过；每rank100 Graph stage＋2个初始eager-first；API正常退出、全部本任务进程/租约已释放|[服务终态](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C286_R8_Qwen36_Eagle_TP4_single257_2051_out32_HTTP_G_ON_01_node140/result.json)|
|正常reader/缓冲区复用的限定工程合同|8具名前提已关闭；Source/API完成边、每rank102绑定/三稳定bank及独立数值/Full/Target。逐次operand/physical-read未直接观测，不把HTTP完成当设备完成|[reader与Source适用性](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/production-delivery-export-scope01.json)|
|实际入口和拒绝保护|C286修正TP4EP Target派生前后SP/backend成对条件；Draft捕获SP仍False，未验配置拒绝。C290仅收紧Full8 guard，Eagle计算/完成路径未变|[总报告](adapt_任务总报告.md)|

### 待完成

原范围仍有四请求有效输出FAIL与更广形状；本轮不重复原生探针，不等待底层最终归因。剩余2点属于后续完整范围，外部时间未知；全部关闭且其他项不变时总体由 **95%推进至97%**。

|事项|状态/下一步|完成判据|资源|预计用时|可增加的总体百分点|
|---|---|---|---|---|---|
|四请求有效输出与准确API归属|原FAIL保留，执行前明确拒绝；仅有新准确API或可判别线索再开|解决有效输出反例或用户/维护者明确相应后续处置；不静默fallback|当前不占卡|待准确约束/具体修复后估算|本阶段剩余2点，通过后核算|
|扩大单请求资格范围|当前只声明已验257/2051、out32和固定配置|新需求及具体资格；不由“单请求”推所有长度|不自动派发|形成具体需求后估算|同一剩余额度，不重复计分|

## 最终交付：组合、集成与审阅

### 已完成

已形成固定PR017/544＋Graph独立生产分支和源代码/证据绑定，C304八DCO链已独立bundle恢复与git-am复演通过；旧PURE12/534原件保留，对总体仍已计 **3个百分点**。

|完成事项|适用候选与范围|证据入口|
|---|---|---|
|固定集成生产分支与可追溯增量|C304 f25dce7e，PR017/544八DCO链；bundle与独立git-am核对tree/prod/native一致。C302/C303及旧PURE/工具身份分别保留|[恢复凭据](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/production-restore-validation01/PR017_544_final_revision03/C304-Eagle-pending-incremental01/restore-receipt.json)|
|验收来源及人工决定|可比前态合同、正常Graph限定工程证据方式已明确；直接观测缺项保留，public Gate冻结|[人工台账](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/manual_review/adapt_人工后续核查.md)|

### 待完成

代码/范围/结果交接已保存；还剩固定017/544组合的必要实际资格及审阅。C304八DCO链已独立恢复，旧534链保持历史身份；不再把已完成CPU收尾计为剩余工时。全部完成且其他项不变时总体由 **95%推进至97%**；不是正式发布批准。

|事项|状态/下一步|完成判据|资源|预计用时|可增加的总体百分点|
|---|---|---|---|---|---|
|受限支持边界与交接|新017/544 Full8及Eagle普通入口未验先拒绝；旧a982有限通过、原FAIL及SWA拒绝分别保留|代码、已验范围、限制、性能及剩余项一致；不把PENDING当批准|CPU；Full8必要TP4资格另列|当前交接已完成；外部审阅时间未知|同一余额|
|用户最终PR组合及正式审阅|已按用户固定017/544集成；C304代码恢复通过，必要设备资格和限制交接仍待结果|满足具名集成验证后再按既有授权审查个人fork候选；不等于发布/merge/Gate批准|CPU＋具名资格；外部最终接受|需新设备授权，随后按资格实际结果|同一余额，不能因批准回复自动加分|

## 最近3条重要变化

- 新017/544：C302原0/10/2×16严格数值、Full写、ABA及完整Target48联合限定通过，CPU已退出0。
- C301修复typed ON UPDATE实际config上下文；C304落实新组合Eagle普通入口未验拒绝，八DCO源码链独立恢复通过。
- 原20小时NPU窗口结束；模型/worker/CPU检查/租约释放，当前无活动实验或自动续跑。新544正常DFlash/eager和性能仍需设备。

## 固定入口

- [总体过程](adapt_progress.log) · [当前实时日志](adapt_live.log) · [活动JSON](adapt_日志入口.json) · [任务总报告](adapt_任务总报告.md)
- [恢复入口](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/reports/RESUME.md) · [人工台账](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/manual_review/adapt_人工后续核查.md)
- 历史细节保留于原journal/raw、冻结R6交付与总报告；当前页不保留旧节点/40%/迁移暂停快照。

- [本轮代码与证据交接包](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/return/20261029T012724Z_R8_node103_8f889187/MRV2_PR017_544_C304_scoped_review.zip) · [下载与校验manifest](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/return/20261029T012724Z_R8_node103_8f889187/DOWNLOAD_MANIFEST_PR017_544_C304.json)
