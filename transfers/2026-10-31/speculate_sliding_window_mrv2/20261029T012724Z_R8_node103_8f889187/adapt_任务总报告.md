<!-- NODE101_CURRENT_BEGIN -->
更新时间：2026-10-30T20:42:27.864127+00:00（UTC）  
主机：**node-25-140**  
当前状态：**设备窗口已结束；C302新017/544限定数值/Full写/ABA及完整Target48联合通过，交接已保存，设备任务停止。**  
当前动作：CPU联合已于20:40:21 UTC退出0，用时2184.841360秒；16rank×3对全部通过。没有模型、worker、checker或后续派发器运行；本次代码/证据收尾已完成，等待后续指令。  
设备：**本任务NPU进程及租约已释放；本窗口不再派发**。CPU wrapper2112418/checker2112420亦已退出；完整清理审查见 `C304_final_release_audit02.json`。不宣称整机没有其他任务。  
候选：开发/纯生产 **C304 f25dce7e7f4f31ec2d0057257fca5d805e2ad70c**，tree **38e19e4be80b11c232bd52e3fbc7f381ec566025**；实际producer/checker **C302 1fd6da87ae146cd87cff35bee9c9f0011372da04**，生产仍C301 b10f59bc。C304仅新增Eagle普通入口未验拒绝，不改DSpark/DFlash/DFlash2；原结果不重标SHA。底座 **017cfca1 / vLLM544f182d**。  
截止：T0 **2026-10-30 00:39:27 UTC**；派发收尾 **19:54:27 UTC**；硬截止 **20:39:27 UTC / 10月31日04:39:27 +08:00**，均已到期，不重新计时。CPU联合按明确授权在设备截止后完成。

**整体管理进度95%，可信度中等；统一017/544候选仍 NOT_READY。** 这是原权重累计证据覆盖，不是544验收通过率；本次复验不重复加分。

当前主要缺口：①新544的GLM DFlash正常Graph/零提议及受影响eager资格未测；②新组合真实服务/正常reader适用性仍需受影响路径定向核验；③新544性能未测，完整旧C273四档12格仍仅属534/a982。Full8/Eagle新544普通入口及精确SWA checkpoint Graph关闭，原失败保留。

下一项可验收结果：新的有效设备授权后，先执行已准备且禁用派发的C303 GLM DFlash G_ON正常功能/零提议资格（TP16，约35–45分钟/臂）；随后受影响eager与必要匹配性能。当前不启动它。完整Target48：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C302_CP_Target48_readonly_01/C302_OFF_ON_Target48.json`，SHA256 **fe89893165f255f1ffcaaa9e2a7568063fdb653f00206cccfcb63f8ce623189e**。
<!-- NODE101_CURRENT_END -->

<!-- C302_FINAL_SCOPED_RESULT_BEGIN -->
## 新017/544实际组合结论（2026-10-30T20:42:27.864127+00:00）

- C296原首样本失败是本次接线缺陷：typed ON UPDATE没有当前vLLM config，16rank均在backend选择处断言并保守exit74；C301在真实manager config上下文中执行UPDATE，未改OFF调用和所有权保护。新C302模型复验两臂均完成；原FAIL和未知提交隔离原件保留。
- ON：16rank×原0/10/2三场景，active/padded为1/2→3/4→1/2，Draft有效输出[8,6144]→[24,6144]→[8,6144]，原atol=rtol=0，48份输出与5层10个K/V组件的Full后态/ABA通过。独立544 canonical padded参考，不复制Graph可疑carrier。OFF只提供匹配Target/执行底座，不能写成OFF也有48份独立Draft数值参考。
- **完整OFF/ON Target48联合PASS**：16rank×3配对，原identity/有效行/positions/query布局/前态合同均接受，CPU rc0/2184.841360秒；完整JSON252163 bytes，SHA256 `fe89893165f255f1ffcaaa9e2a7568063fdb653f00206cccfcb63f8ce623189e`。这是原0/10/2子集，不是完整14矩阵、自然业务质量或正常Async重叠证明。
- 实际C304独立Source/vLLM544/自有CP312 native导入rc0/27.824秒，37个真实保护helper控制通过、PTA未初始化；只证明导入/保护。运行manifest SHA3044b01d5a14fb4d972b7caccc72725313785cef1a102780233642a7c2f40d6b；实际证明位于 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/PR017_544_runtime_prepared/C304_actual_Graph_import_Full8_guard01.json`。
- 新544 GLM DFlash正常0提议、受改eager、新组合服务和性能尚未完成；有限Eagle实际first/AR也未取得新544设备资格。Full8/SWA/Eagle普通入口按已批准保护保持关闭，没有静默fallback。
- 旧C273的16/32/64/128K三臂12格完整有效，但底座是534/a982；**新017/544四档为NOT_RUN**。不能跨底座拼接正式配对。代表性新资格约35–45分钟/臂；完整新12格按旧实测约160分钟（3次加载与测量），还需单独设备授权和实际影响裁定，不自动翻倍重跑。
- GitHub只读head仍017，#20288 draft/open、mergeable=false；E2E41007944791的precommit/ci-gate失败、CPU/NPU跳过，Docs通过。保存原KVPoolWorker基线复现，不声称CI通过。Graph未push，未更新交付分支/PR或开放Gate。
- Source/API+实际绑定/owner+独立多代数值/Full/Target的限定工程证据方式沿用已确认决定；逐次execution operand和硬件physical read-set仍UNPROVEN/NOT_OBSERVED，不宣称硬件只读取窗内地址。

完整Target原件：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C302_CP_Target48_readonly_01/C302_OFF_ON_Target48.json`；准确恢复入口：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/return/20261029T012724Z_R8_node103_8f889187/NEXT_SESSION_HANDOFF.json`；生产分支 `dev/mrv2-graph-pr017-vllm544-20261030`，工作树 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/work/node140/integration_PR017_GraphC294/vllm-ascend`。
<!-- C302_FINAL_SCOPED_RESULT_END -->

<!-- FINAL_SOURCE_DELIVERY_BEGIN -->
## PR017/544当前交付代码（C304源码独立恢复通过，设备资格分别裁决）

- 固定底座：Ascend `017cfca1c74c2e0b9984876bd4250593ed681908` / tree `45e4b805ff5df370d4a89e4285d2754d0281fe50`；vLLM `544f182d9f0c9bfe8bd7645525951d5e3692a542`。PR工作树/交付分支只读，未修改PR的Source、状态或入口。
- 最新生产 **C304 `f25dce7e7f4f31ec2d0057257fca5d805e2ad70c`** / tree `38e19e4be80b11c232bd52e3fbc7f381ec566025` / production `6c82f991116dbb36df8b195cd725dc7253cb2020`。固定producer/checker C302 `1fd6da87ae146cd87cff35bee9c9f0011372da04`、C303工具 `8b5d3fa058e74d59a499cde993fa2696e5364838` 的实际生产仍C301 `b10f59bc6700c995e6531c09cd5a13f92a8ef908`；原Source身份不重标。
- C304相对C301仅 `draft_graph_review_limits.py` 和对应窄UT：新017/544 Eagle普通有限入口尚未取得实际资格，按既有“未验不开放”决定显式拒绝；私有numeric、typed eager、原0/K3及形状保护保留。14项guard和16项Eagle Host定向检查通过。DSpark/DFlash/DFlash2 speculator三个blob逐字节未变，不能把代码适用性写成新候选NPU PASS。
- 保留017原DFlash2 resident-KV/typed eager、policy/cache builder和TargetDependentAR链；必要Graph接线含新版req_states工厂、独立context-KV-only完成owner、Graph/eager互斥、544 aux组合/metadata布局，以及C301实际manager配置的typed ON UPDATE。OFF原两参调用、backend/operand/owner检查保留。
- 自有CP312扩展SHA `ef173159087e6af357f5559ffceb8decf9dd5757e5f7f44fcb35a265ff426f3d`，csrc `19b96b8af59b825cf74b9ad7010be76dc30a3a5b` 与017相同；未复制PR native或升级底层栈。C302模型actual source/native固定，C303实际Tool81/Graph/native被动导入rc0/27.966秒且PTA未初始化；这不代替真实normal零提议资格。
- 相对017共**8个线性DCO提交**：7c5e5131集成、112e826a换行、3a7aeef8 Full8保护、8cddd977 import、def8f362格式、38df2431兼容诊断字符串、1dbcec3e typed ON UPDATE配置、f25dce7e Eagle普通入口未验拒绝。生产增量不含私有Tools、权重、日志、环境和native二进制。
- **C304实际独立恢复通过**：[restore receipt](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/production-restore-validation01/PR017_544_final_revision03/C304-Eagle-pending-incremental01/restore-receipt.json)，SHA256 `3796a16288ac78dea4c48d618f4d664dfb9e7a23adebc9eda01e102199756ab0`。在独立PR017对象基线上依次验证原C300/C301/C304增量bundle，另一个baseline-only仓独立git-am八提交；完整tree/production/native一致、无alternates/replace/grafts、严格fsck通过。原C300六提交与C301七提交receipt和失败尝试保持原件；不是把旧恢复PASS改标新Source。
- C302 ON原0/10/2已producer0/1238.42秒，16rank×3原件已保存且自身PID[]/租约RELEASED；独立只读数值/Full/Target/复用checker尚无最终裁决，不把producer0当PASS。C296原current-config断言及各rank主动exit74隔离保留，不认定外部kill。
- Ruff/format/diff及具名Host控制分别按真实边界保存；完整format CI仍保留固定actionlint Go下载RemoteDisconnected/rc3，源码hooks未全部执行，远端原KVPool mypy失败/后续跳过未豁免。旧a982四档12格性能、Eagle/Full8局部证据保留原身份；新544性能NOT_RUN。当前95%/NOT_READY，未推送交付远端或#20288、未合并、未批准发布，public Gate不开放。


## 历史534/a982可交接生产代码与独立恢复（017/544已接管，不作为最终组合）

生产分支 **deliver/mrv2-draft-window-graph-pr534-production-20261030**，工作树 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/work/node140/integration_PR534_GraphC254/production_delivery/vllm-ascend`；当前HEAD **89b32d671827d076d3d8e4c6e5f18af8deab9606**，tree **d07a4ff712b8b6ca343e667c04edf12fd89da81b**，生产subtree **53e10c6b14b2efc6be230a8d33b1ad1f7dc531b4**。固定基线 **PR534b5e236be0e8a0684b5f31fcee03f573a60b1a / vLLM a98247ab4db686ee03c66d5feb3c761e52a2f8ab**；不是用户之后提供的最终PR版本。生产差异39文件＝34生产文件＋5相关UT，不含tools/raw/环境/权重/native二进制。

|必要提交（按顺序）|作用|
|---|---|
|a2b56b5ae803c06166a736867b46bc11e9fdcabc|将独立Graph增量接到PR534/a982的dp_sync、context/capture、typed Graph和持久owner接口|
|549d89a350b4e1c31f72b81369df75a7ccf749ee|仅capture阶段保留私有数值诊断输出，普通路径不承担该留存|
|917168096b66bfd361abc40b421426e36d9b83de|精确checkpoint支持保护；指定SWA Graph拒绝，Full8按实际行保护|
|9aafb13f6004866541a9d84d4666dc3cf9a21608|私有Full metadata绑定持久Graph exact地址，保留本代精确信息|
|5756faab28099fe2b013edebf52821f27e0688f1|相同Graph group只绑定一次共享metadata，保留owner和完成依赖|
|f6aa18862666eaf8748e5b75b5329b05b3bfa5d2|补齐必要Target DSA-CP Graph metadata持久backing，保留a982布局|
|ada878e9b66c2fe8b1f8802c51ef601a1368fb5e|默认关闭、有限Eagle真实服务入口及请求生命周期保护|
|16e23dc34b8cd269729c2dc3f88be8deba417aa9|对齐实际Target EP/SP配置，Draft捕获资格不扩大|
|05ee05c0709f3cf65b69206e9ed1189e2c9193f7|覆盖Ascend配置派生前后合法backend/SP组合|
|3b4932bc1825dbc047f294242ff54fc017c3fdc5|仅隔离UT fixture对齐真实bool验证函数，不改生产|
|df0effada40097562a7d19ae4a915523333fa2f0|已知Full8多有效请求反例的执行保护：当前actual perDP active≥2拒绝，无静默fallback|

|0bfde3bb6e3bd437d7ce673f4c37efd89acdcdf4|限定Full8单请求配置/容量及actual1/padded1；拒绝提前到proposal状态更换前，正常scope进入顺序不变|
|89b32d671827d076d3d8e4c6e5f18af8deab9606|将既有W32768配置入口接到精确checkpoint和单请求保护，原DP2/私有numeric不变|

以上13条均有DCO。私有数值/服务/checker工具保留在DELIVERY树，不能把其原始证据SHA改标为PURE或新候选设备PASS。

**真实独立恢复已通过到PURE12**：2026-10-30T17:34:36.526Z—17:34:52.816Z，rc0/16.291秒；新独立PR534基线只有原5085对象、无alternates，bundle恢复0bfde3bb…、无3way git-am恢复e8fc309f…，完整tree7c203…/生产6b379…/csrc718ac…相同、严格fsck通过。随后实际CLI预检发现旧配置入口只准W32768/DP2或私有numeric，必要补充13号接线89b32d…后尚待真实服务和最终独立恢复；不能把12号恢复凭据改标13号。第一轮C290导出原件也保留。

- [上一版PURE12生产Git bundle](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/production-restore-validation01/padding-qualified-revision02/final-export/graph-production.bundle)：192500B，SHA256 `0cc0cc666ef8c7d2061e417214e986320125c3b8b078f6038980c750a261cca7`。
- [上一版PURE12生产补丁系列](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/production-restore-validation01/padding-qualified-revision02/final-export/graph-production-series.mbox)：810804B，SHA256 `a214cd9f8588b7d4037e98dc31e8c7a93ebcb6f38c710fa4df9a94a18aba8197`。
- [独立恢复凭据](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/production-restore-validation01/padding-qualified-revision02/final-export/restore-receipt.json)：7556B，SHA256 `146e46ac2e2b416fc812cd5bc0fca8fc7740b4d0c7f5d6dfdff9b9daa42e1b25`；记录完整Source/patch/artifact清单。

恢复前置为固定PR534，bundle仅含Graph增量；不包含PR完整历史、Python安装或模型。当前运行使用本任务隔离CP312与每候选overlay，不能复制旧CP311扩展，不能把PR editable或native引入Graph。csrc **718ac034b50849a0bcf13c781884337e4701f115** 与PR534一致；既有本任务CP312扩展和vendor可按实际加载manifest合法复用。PURE源码目录与运行快照分离，切换运行Source时必须重新绑定own overlay并核对实际worker import，不能直接沿用指向旧候选的pth。

历史534/a982时期曾计划等待最终PR。该等待已由用户提供017/544及集成授权结束：当前已完成固定新pair、必要接口/owner适配和C302 ON限定复验，OFF进行中，以顶部当前状态为准。旧producer身份保留，不跨版本拼正式性能；PR工作树只读，Gate未开放。
<!-- FINAL_SOURCE_DELIVERY_END -->

<!-- C277_C281_EAGLE_SINGLE_CURRENT_BEGIN -->
## 历史534/a982 Eagle有限单请求资格（数值、HTTP及reader已完成；不含017/544资格）

数值producer C277 `d7ab6427ef2af6b7b4a478309944cfe6eb6931db` / production4cd05 / vLLM a982，TP4DP1/Phy12–15；257/2051单请求各firstQ4＋AR1/AR2 Q1，4rank×6consumer。模型556.252845s/rc0；原checker内层schema遗漏INVALID保留。C281 Tool15只读重算23.758s/rc0，严格数值/Full写通过；每rank2 proposal×80 Target组件同proposal未污染。[联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C277_Eagle_single_readonly_C281_01/joint.json)，SHA256 `0c35c0c55892adac5535e3a4bb51b87a379a4b5d19b29503bb42b7fc4defb291`。不是独立Target forward/logits、业务质量或性能结论。

普通服务producer/checker C286 `e695578075da3a190f39e2a14d433a3d270d2e6c` / productiona44e9 / a982，两个真实HTTP请求[100]×257/[100]×2051，各out32，TP4DP1EP/K3/W1024；非Async、prefix/legacyCP/FlashComm关闭，FDO，未验配置明确拒绝。producer0/566.420s，checker0/4.044s，outer0/587.214s，API正常退出/4rank归属通过；17:00:01 UTC仅本任务PID[]/租约释放。[终态](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C286_R8_Qwen36_Eagle_TP4_single257_2051_out32_HTTP_G_ON_01_node140/result.json)，SHA256 `d03f7e706e81de69f2566312fd6b38051b839f844161830c93e506b30492b59a`。

每rank两请求合计34 proposal/102 consumer绑定＝100个Graph stage＋2个初始eager-first（FDO prefill），不能把所有first都写成Graph。单owner stream、三个稳定bank和first/AR独立ordinal核对；正常reader的8项Source/API与实际owner/绑定前提已限定关闭，未发现具体缺失完成边。C277/C281 strict数值/Full/Target与C286五核心文件/八核心方法相同，当前native/vendor1324项连续。具体见 [现有导出范围凭据](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/production-delivery-export-scope01.json) 的 eagle_finite_normal_reader。逐次operand与physical read-set仍UNPROVEN，不用HTTP/Host返回/进程退出代替最后reader证明。

C286修复仅使有限入口接受实际Ascend Target派生前后合法backend/SP成对状态；Draft capture SP仍False，不新增Draft SP支持。C290仅收紧Full8执行保护，Eagle此限定计算路径未变。四请求有效输出FAIL、准确API归属及更广长度/形状仍保留，不受本有限通过豁免。
<!-- C277_C281_EAGLE_SINGLE_CURRENT_END -->

<!-- C273_INITIAL12_PERFORMANCE_BEGIN -->
## 已完成的534/a982固定组合四档三臂性能（初始12单元，非544数据）

Producer/checker **C273 cefbbd6e**；vLLM **a98247ab**；140/Phy0–15、TP16/DP1/EP、DSpark K8/Q8（Target验证Q9）、W1024；n4/c1、每请求out2000。每臂1服务实例，每长度1计时单元；4档各2×128预热全部排除。prefix引擎开启但正式请求要求cached_tokens=0，组前native idle reset＋固定唯一salt。G_OFF03/G_ON01/E_ON01三臂均四档整臂checker通过（12/12）；退出审计各ownPID[]、租约RELEASED。此处是限定性能原件验收，不是数值/质量/发布批准。

|实际输入token数|模式|Output tok/s（组）|TTFT均值 s|TPOT均值 ms|E2E均值/组 s|MAL含bonus|accepted/drafted（接受率）|验证轮数|状态|
|---:|---|---:|---:|---:|---|---:|---|---:|---|
|16000|G_OFF|40.076|2.6302|23.6472|49.9023 / 199.6206|3.69405|5838/17336（33.676%）|2167|整臂checker通过|
|16000|G_ON|48.888|2.6530|19.1372|40.9088 / 163.6396|5.24754|6486/12216（53.094%）|1527|整臂checker通过|
|16000|E_ON|47.092|2.6558|19.9160|42.4686 / 169.8787|5.25787|6489/12192（53.223%）|1524|整臂checker通过|
|32000|G_OFF|16.947|5.4792|56.2923|118.0093 / 472.0511|1.55071|2840/41256（6.884%）|5157|整臂checker通过|
|32000|G_ON|38.940|5.4026|22.9893|51.3592 / 205.4427|4.36205|6166/14672（42.026%）|1834|整臂checker通过|
|32000|E_ON|37.575|5.3759|23.9366|53.2257 / 212.9080|4.36681|6168/14656（42.085%）|1832|整臂checker通过|
|64000|G_OFF|10.914|11.0142|86.1609|183.2526 / 733.0370|1.02290|179/62536（0.286%）|7817|整臂checker通过|
|64000|G_ON|25.396|10.9820|33.9004|78.7499 / 315.0076|2.96810|5306/21568（24.601%）|2696|整臂checker通过|
|64000|E_ON|24.449|10.9894|35.4235|81.8021 / 327.2164|2.96480|5303/21592（24.559%）|2699|整臂checker通过|
|128000|G_OFF|9.936|22.5898|89.3854|201.2749 / 805.1245|1.00113|9/63896（0.014%）|7987|整臂checker通过|
|128000|G_ON|18.294|22.3061|43.5303|109.3240 / 437.3102|2.31415|4543/27656（16.427%）|3457|整臂checker通过|
|128000|E_ON|17.684|22.2844|45.4278|113.0959 / 452.3975|2.31281|4541/27672（16.410%）|3459|整臂checker通过|

更新：2026-10-30T12:35:02.719665+00:00；**12/12**计时单元及三臂整臂checker已完成。G_OFF=Draft Graph/Window OFF；G_ON=Draft Graph/Window ON；E_ON=同Window Draft eager，Target Graph及其余要求配置一致。四档三臂已配齐且通过各自原件检查；以下仍仅单次观测。16000的G_OFF→G_ON单次观察为组耗时−18.02%、吞吐+21.99%、接受率+19.42个百分点、验证步数2167→1527；G_ON现已整臂checker通过，但每档仍仅1个计时单元，不宣称统计显著。

吞吐=实际输出token总数/组单调时钟耗时；E2E两栏分别是4请求算术均值和整组跨度。TTFT/TPOT来自客户端真实SSE，TPOT是首/末非空交付之间/(输出数−1)，不是设备纯decode或完整逐token ITL。accepted/drafted排除bonus/padding，MAL=1+accepted/验证步数；原生接受计数在输出stop/maxlen裁剪前，不能将其与可见输出数强行等同。每请求逐步/直方图/terminal计数独立对账，未重复累计TP ranks。

计数补充：a982首次普通Target输出token不进入投机计数；16K/32K四请求的 `1+accepted+steps−output` 分别为[1,2,4,2]/[0,0,1,0]，与最后SSE输出块裁剪一致。组级净差+5/−3不能直接称为截断数。当前客户端是实际Tool71 HTTP/SSE通路，未调用AISBench CLI；保留真实客户端原件，不伪称AISBench结果。

输入是已冻结的双语技术段落重复/截断及4个移位版本，并非独立业务语料；1计时单元不支持显著性结论。当前NPU管理采样只见本任务worker，不构成整机CPU/I/O独占证明。原初始化失败与早期外来context在原attempt保留，不改标通过。

原件：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C273_R8_GLM_DSpark_TP16_initial12_G_OFF_03_node140/model/requests.json`；固定IDs：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/inputs/20261029T012724Z_R8_node103_8f889187/DSpark_matched16to128k_n4c1_v1/requests.json`。历史84030性能保留原版本，不填入本表。
<!-- C273_WINDOW_OBSERVATIONS_BEGIN -->
### 同Graph模式，额外Window OFF→ON的单次观测

|实际输入tokens|组耗时节省|Output tok/s变化|验证步数OFF→ON|接受率变化|同Window Graph/eager|
|---:|---:|---:|---|---:|---|
|16000|+18.02%|+21.99%|2167→1527|+19.42个百分点|耗时−3.67% / TPS+3.81%，整臂已通过|
|32000|+56.48%|+129.77%|5157→1834|+35.14个百分点|耗时节省+3.51% / TPS+3.63%，整臂已通过|
|64000|+57.03%|+132.70%|7817→2696|+24.32个百分点|耗时节省3.73% / TPS+3.88%，整臂已通过|
|128000|+45.68%|+84.11%|7987→3457|+16.41个百分点|耗时节省3.34% / TPS+3.45%，整臂已通过|

两Graph臂各自整臂检查通过，每长度仍只有1个计时单元。上述是包含提议/接受及验证轮数变化的服务整体效果，不是等工作量纯kernel加速；不代表统计显著、业务质量或发布批准。
<!-- C273_WINDOW_OBSERVATIONS_END -->

最终只读复算：[C273_final12_http_rollup.json](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C273_final12_http_rollup.json)，SHA256 `b8429589d20624d2de7312adddc049db6380a774102061fab4a63fb92ade2313`。包含12单元、8比较、逐请求accepted/drafted/steps及原失败attempt索引。四档同Window Graph的组耗时节省依次3.6727%/3.5064%/3.7311%/3.3350%，吞吐提高3.8127%/3.6338%/3.8757%/3.4500%；不把二者混用。三臂Target Graph及适用特性匹配，接受计数略有自然变化，不能称严格等工作量kernel对比。

12单元可直接分析的完整精度表：[C273_final12_metrics.csv](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C273_final12_metrics.csv)；保留实际Source C273/production4cd05/a982和原rollup hash，逐请求原始计数仍在JSON。CSV的验证轮数与drafted token数分别列出，不混用Host调用数。

正常Source完成合同引用已有具名证据；本组API清理三臂均为 **FORCED_NOT_GRACEFUL**（超时后仅精确自身API PID/start被收尾，worker独立退出及租约释放），这不是正常reader或设备完成证明。当前private Tool71 HTTP/SSE是真实测量入口，未冒称AISBench。大group-boundaries已在非正式计时阶段一次性只读解析，全部12单元16rank统计一致：实际CPU proposal均active1（由请求行记录核实）；G_ON runtime active/padded=1/2、E_ON=1/1。两Graph臂真实Host提交Draft descriptor均2行/16 query tokens，Target为2行/18 tokens；这不是设备operand观测。ON/E_ON实测有效exact读长1024–1151，四档window_start分别14976–16896、30976–32896、62976–64896、126976–128896。所有已记录materialization均裁窗，continuing-prefill中未materialize部分不外推；G_OFF没有window materialization，不补造其runtime exact。详见 [工作量原件摘要](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C273_final12_workload_metadata_summary.json)（60832B，SHA256 9247d8ddc16d351999fed112678c6777b81cab0ec89a4b52f3937993c213cc65）。Host返回次数不冒充设备task数量或完成依据。
<!-- C273_INITIAL12_PERFORMANCE_END -->
<!-- C273_DFLASH_FUNCTIONAL_TIMINGS_BEGIN -->
## GLM DFlash现有服务代表指标（功能样本，不是正式三臂性能）

实际C273/534/a982、140 TP16DP1EP、K15/Q16/W1024；两臂各6预热与6功能请求，以下仅功能请求，各out256。两臂同组并发2/1/3，5/6真实prefix命中；Target Graph保持，G_ON Draft Graph、E_ON Draft eager。客户端TTFT为POST前至首非空chunk，TPOT为首至末非空chunk/(256−1)，E2E至完整SSE/DONE；不包含模型初始化，不冒充设备纯decode或逐token ITL。表格每格为G_ON / E_ON。

|输入token数|组/并发|cached tokens|TTFT ms|TPOT ms|请求E2E s|MAL含bonus|
|---:|---|---:|---|---|---|---|
|257|1/2|128|577.900 / 619.461|19.212 / 20.481|5.477 / 5.843|4.526 / 4.691|
|8193|1/2|8064|1125.443 / 1181.664|9.033 / 9.722|3.429 / 3.661|9.429 / 9.778|
|16385|2/1|16256|568.559 / 609.695|6.062 / 6.681|2.115 / 2.314|12.750 / 12.750|
|8193|3/3|8064|638.110 / 568.222|11.685 / 13.671|3.618 / 4.055|9.429 / 9.808|
|129|3/3|0|1229.435 / 1105.781|37.323 / 38.589|10.747 / 10.946|2.048 / 2.327|
|2049|3/3|1920|1229.334 / 1750.340|11.918 / 13.294|4.269 / 5.141|7.371 / 7.111|

真实完整组elapsed G_ON=[5.477585,2.115112,10.748511]s、E_ON=[5.842856,2.313983,10.947979]s；各组输出512/256/768，直接按组wall派生吞吐分别G_ON=[93.472,121.034,71.452]、E_ON=[87.628,110.632,70.150] tok/s。不是AISBench生成字段或正式达标结论。该组混合调度/真实缓存命中及轻量审计，与DSpark四档冷缓存口径不同，不能互为基线。部分TTFT慢、部分接受工作量变化均保留，不将全部差异归Graph执行。

接受原始计数G_ON accepted1262/drafted4395/steps293，接受比例28.7144%、MAL=1+1262/293=5.30717；E_ON1270/4110/274，30.9002%、5.63504。每请求Target计数只取一份，不累加TP ranks。完整逐请求计数、原始SSE/client时间边界在现有 `production-delivery-export-scope01.json → glm_dflash_functional_acceptance.service_timings`；来源为两臂 `raw/C273_R8_GLM_DFlash_TP16_required_features_{G_ON,E_ON}_01_node140/model/requests.json` 及 `http-artifact-joint.json`。本次仅离线提取，不启动新模型或把功能数据改为正式性能。
<!-- C273_DFLASH_FUNCTIONAL_TIMINGS_END -->


<!-- C271_NECESSARY_FIX_REVIEW_BEGIN -->
### 当前固定组合的具名必要修复迁移核对

|来源|C271对应实现|结论与受影响验证|
|---|---|---|
|C138 / 94e61a2c Target CP Graph metadata持久地址|C271 d5e33ee75；纯生产f6aa18862，`attention/context_parallel/sfa_cp.py`|发现原提取漏项并最小恢复，保留a982 NoPE和query布局。真实CPU旧6反例失败/修后9通过；C272三样本两臂数值/Full/ABA及Target48已限定通过；C271正常12请求完成、原清理2另保留。不是全部长度或性能通过。|
|PR185e→0be Q023加载对齐，固定底座PR534包含|`models/qwen3_dflash.py`与PR534一致，load_draft_model保留一次加载处理|已等价保留，不重复移植/旋转；当前C273/C278 GLM DFlash关键数值/Full写/Target48及正常G_ON/E_ON已取得自身限定证据，PR PASS仍不继承。|
|C157前序正常回收、C248退休异常保护|`draft_window_async.py`与C157字节一致；proposal_scope/discard关键函数与C248 AST一致|没有发现本次漏项；新调用上下文以设备正常服务核对。C144/C247/C249本身工具提交不冒称Source修复。|
|C233/235/236具名Eagle桥|geometry helper保留，TP4 K3 causal eager资格gate/source保留；C236为Tool46|现有桥保留；C277/C281新组合6consumer数值/Full/Target、C286有限普通HTTP与正常reader已完成；旧四请求有效FAIL仍拒绝。|

限定证据：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/C271_known_required_fix_migration_review01.json`（SHA256 3615422b8ad0da595c565514a1b19e08a0d449fc3538a1cff0a3d19c4377bca4）。仅核已明确修复，不是新全仓审计；源码迁移正确不等于设备PASS。
<!-- C271_NECESSARY_FIX_REVIEW_END -->
<!-- C273_CP312_NORMAL_API_BEGIN -->
CP312具名正常Graph API适用性已核对：同2.10.0.post4/git的streams.py、graphs.py、NPUGraph.h、NPUEvent.h与原安装逐字节一致，当前/旧worker的CANN核心库hash一致；CP312 libtorch_npu.so不同hash单列保留。wait-current、ExternalEvent/typed UPDATE及持久owner未发现本次迁移新增的具体缺失边，尾notify/FIFO仍依用户已接受的限定Source/API前提，不冒充直接设备完成或hardware read-set。仅DSpark已登记consumer范围适用，不能自动替代Eagle AR或DP2正常资格。详见 [CP312_normal_graph_api_applicability_review01.json](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/CP312_normal_graph_api_applicability_review01.json)（SHA256 d627d86c2c79ae68ca59a6cb0fe56d9d31af06770d8c6f1e03e3d64b03dbaea1）。没有新人工决定待办，不增加管理分数。
<!-- C273_CP312_NORMAL_API_END -->

<!-- C273_GLM_DFLASH_CURRENT_QUALIFICATION_BEGIN -->
## 当前GLM DFlash新组合：关键数值、正常Graph与eager功能已限定完成

固定producer **C273 `cefbbd6ebc103be7cb51f84463f509abb78203e8`**、只读数值/Target checker **C278 `e2c12e83531326868a16d01398168c3179ccde48`**，PR534/a982、production4cd05、自有CP312/native。GLM5.2＋指定DFlash、TP16/DP1/EP、K15/Q16/W1024；正常服务共同启用约定Async/prefix/chunked/SP/legacyDSA-CP/FlashComm与Target Graph。各证据分别裁决，不合并成全部模型/性能/发布通过。

|已完成项|实际结果与边界|原件|
|---|---|---|
|CP三场景数值/Full写|OFF01与ON03原场景7/10/11、16rank×3；ON独立canonical可比前态Graph/eager有效BF16输出及5层Full写严格零差。旧dtype INVALID保留，C278只修checker|[ON03完整联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C273_DFlash_ON03_readonly_C278_01/ON03-joint.json)|
|完整Target48|OFF01-ON03，16rank×3共48对，原判据全部PASS。CPU02 rc0、无timeout、1620.543329秒；CPU01在1200秒超时，原30对局部通过不改成完整PASS或生产FAIL；无模型重载|[完整联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C273_DFlash_Target48_readonly_C278_02/OFF01-ON03-Target48-joint.json) · [真实终态](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C273_DFlash_Target48_readonly_C278_02/target48-checker-execution.json)|
|正常G_ON服务|producer/checker均0、2005.071278秒；6预热＋6功能，实际prefix命中、多阶段、16rank、每rank3稳定banks/430代绑定通过。498 Host proposals不当设备执行次数|[G_ON联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C273_R8_GLM_DFlash_TP16_required_features_G_ON_01_node140/http-artifact-joint.json)|
|正常Graph reader八前提|Q16单parallel ordinal0/5层注册consumer、wait-current、typed UPDATE/ExternalEvent、图尾notify/FIFO、持久bank、异常quarantine、当前CP312身份及独立数值/Full/Target前提已在已接受Source/API方法下限定关闭，未发现具名缺边|[八前提限定收口](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/C273_GLM_DFlash_normal_reader_applicability01.json)|
|同配置E_ON功能|producer/checker/outer均0、1979.633469秒，14:48 UTC完整终态；16rank、6预热＋6功能，真实Draft eager/Target Graph、每rank2个稳定lane/413代通过；ownPID[]/RELEASED|[E_ON联合](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C273_R8_GLM_DFlash_TP16_required_features_E_ON_01_node140/http-artifact-joint.json) · [真实退出](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C273_R8_GLM_DFlash_TP16_required_features_E_ON_01_node140/result.json)|

直接逐次operand与physical read-set仍 **UNPROVEN/NOT_OBSERVED**。CP312 PTA native与旧CP311不同hash继续保留；API清理 **FORCED_NOT_GRACEFUL** 与独立worker正常退出/租约释放分别记录，不以HTTP/退出证明最后reader完成。上述正常G_ON工程证据不借eager完成事件作证明；E_ON功能不是正式匹配性能或业务质量批准。

**当前剩余**：GLM上述项不再待派发。Full8 C285前两个active1严格数值/Full写/Target640通过，但第三active3有效输出和KV后态仍FAIL；C290实际拒active≥2，正在准备单请求普通资格，临时产品范围待用户选择。Eagle C286有限普通HTTP与reader已完成，四请求仍拒绝；指定SWA精确checkpoint Graph仍阻塞。管理估计93%，新增仅计实际Eagle验收项关闭；无新同输入原生probe。
### 已对齐加载底座的功能接受表现（非正式性能）

复算现有两臂各6个功能请求（另6预热不混计），实际输出各1536；G_ON drafted/accepted/验证步数=4395/1262/293，接受率28.7144%，含bonus平均接受长度=1+1262/293=5.30717；E_ON=4110/1270/274，接受率30.9002%，含bonus平均接受长度5.63504。每臂5/6功能请求真实prefix hit、cached tokens合计34432；逐请求终态SSE与per-step/直方图对账，不重复累计TP ranks。两臂加载前后32份rank header核对一致，QuaRot处理、FC[6144,30720]/BF16及owned embedding/head底座一致。这里只描述功能接受表现，不将两臂差异归因加载修复、滑窗或Graph收益，不代表业务质量。

详细原件/计数边界：`integration-actual-check01/production-delivery-export-scope01.json → glm_dflash_functional_acceptance`（位于本轮PREP目录；同时含actual CLI及Source-only入口静态适用性说明，去worker-extension设备验证仍NOT_RUN）。

<!-- C273_GLM_DFLASH_CURRENT_QUALIFICATION_END -->




<!-- R8_PR534_INTEGRATION_BEGIN -->
本轮四档实际输入token IDs长度已只读核对：**16000 / 32000 / 64000 / 128000**，各4请求、out2000；最大总长度130000<132096。16K等仅档位标签，后续表使用实际长度，不采用旧摘要中的二进制换算。

**前序记录（2026-10-30，C260阶段）**：C260固定cdd470c5/tree8b91a192/production4557c917，交付工作分支deliver/mrv2-graph-pr534-20261030。C259只纳入C256已核三文件桥；C260仅私有性能工具改为新12单元方案。自有CP312扩展构建/独立ABI及实际EngineCore/NPUModelRunner导入、bare child来源核对通过；原311 SyntaxError作为历史保留且不修改上游。当前首个新pair DSpark TP16 ON模型段正在执行准入/加载，尚无数值PASS。资格原件：PREP/cp312_execution_20h_20261030T003927Z；实际Source/native环境：runtime/node140/C260_PR534_Graph_delivery/runtime_manifest.json。以下C255/C258内容为实现来源及前序记录，旧等待不再控制本轮。

## 历史实现来源：C260 / PR534+a982，后续当前状态以顶部为准

**最新固定Source**：C258 `5f3809faf6230c715dbae1150ceef77eeba47806` /tree`cf52d929d210e7b0e360ff6c7dd3183a4ab65f13`，`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/node140/C258_PR534_Graph_validation/vllm-ascend`，production仍C255的943daa123b0c88eecbd1f509fd4b9c53ccd3bcad；C256 Eagle桥独立保留。仅统一现有NUM canonical/Full/context与PERF请求/计时工具，11项同名差异逐项选择、单一tools包；实际Git/blob/SHA256＋CLI/外部runtime admission核对，不沿用旧311 binding。5项窄Host及提交后实际tool proof通过，固定Source无native。未新312/ABI/模型/数值/性能；不是C258设备PASS。Source绑定state/R8_C258_NODE140_SOURCE_BINDING.json；原件PREP/root-C258-fixed-source-proof01.json。


用户已授权自主选择已采用固定交付与最小Ascend适配。只读PR会话01a164e7-cbc0-7e62-8c14-ac9c4d1e539b最近有效记录及共享交接/Git后，选Ascend **534b5e236be0e8a0684b5f31fcee03f573a60b1a**（tree2410cc66025c67aa2b5e6b37ccfab4fd82266f39），配套 **a98247ab4db686ee03c66d5feb3c761e52a2f8ab**。它是已纳入DFlash2 eager的明确交付快照，成熟度PARTIAL/PR_READY=NO；不跟随Q030隔离参考7e/296或未采用fadd。PR0be保留历史，但不再作为“等批准才可选底座”的当前阻塞。PR代码/状态/观察入口均未写。

隔离分支 dev/mrv2-graph-r8-integrate-pr534-c254 已提交 **C255 60cd795851e34e5c19d43b45b4b9f23f385c13ab**，tree416e058c84647f79f0927a0802f9a9b7e99d15c7。11个共享文件按函数接线，移入16个Graph专属模块（含dflash capture），保留PR typed eager/DFlash2、Q023既有等价加载。新DPsync_state、uniform/context-KV capture、当前exact证书和typed UpdatableGraph桥；无双owner、无底层升级/PR native复制。52项实际函数AST/CPU协议控制通过，原attempt01测试误导入系统框架导致收集失败保留。没有C255新模型/数值/性能PASS。

|路线/问题|现在可以做什么|不能继承的结论|
|---|---|---|
|GLM DSpark|旧C147严格数值/Full写/Target、C151全特性服务等具备选择代表性新pair验证的基础；先核新uniform/context与实际调用|旧84030不是a982新pair设备通过；Draft K8/Q8（sample_from_anchor=true），Target验证宽度另计，需worker实际确认|
|GLM DFlash|C244/C246/C248旧required Graph/eager、数值/Full写/Target/正常reader及C249隔离可按未变属性引用；C253本组六实例已完成|C253测的是独立84030，不是C255；新context/capture/owner接口仍需定向验证|
|Qwen Full8|旧局部可比前态/Target/DP2正常reader成果保留，C254全特性两臂服务限定通过|active8有效数值FAIL仍在；DP2共同特性功能已有结果；内部数值、active8原FAIL、最后reader适用性与性能仍分别审查|
|Eagle/SWA|保留C245/C250有效输出/调用层异常与API适用性待确认，原实现不删除|不能以集成抹去FAIL；新pair未接方法明确拒绝，不fallback冒充Graph支持|

C253/C254的production子树相同7f406fad20b437d84304c48523b2e5307cb8aace，但两者工具不同，当前组六实例全部固定C253 producer/checker；C254不是这组新producer。C255 production943daa123b0c88eecbd1f509fd4b9c53ccd3bcad包含新底座/调用上下文，必须独立验证。原数据/源SHA分别保留。

依据：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/PR_latest_frozen_base_selection01.json；同目录PR_session_tail_decisions01.json、PR534b_GraphC254_code_impact_map01.json（追加typed完成边窄审；未发现新具名缺边，实际新pair前提仍待验）；C255_initial_integration_commit01.json、integration-actual-check01/host-interface-tests-attempt03.json、DSpark_new_pair_matched_perf_minimum01.json。绑定state/R8_C255_NODE140_BINDING.json。public Gate冻结，直接operand/physical-read仍NOT_OBSERVED。

**运行前置实际结果（2026-10-29T17:39:03.161674+00:00）**：C255固定a982在Python3.11真实导入于sharded_state_loader.py:214语法失败，尚未加载模型；已核现有PR Python3.12.15可解析，但Triton/Transformers依赖不同，R8-C255-RUNTIME-01已async提问，仅新pair运行等待。原C253测量现已全部结束。 导入guard01被设备清单查询保护拦截，guard02允许只读真实数量16，但无初始化/stream调用；真实vLLM/Ascend origin均指C255/a982，随后上游PEP701语法退出。不是模型数值或Graph kernel失败。原件 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/fixed_pair_import_attempt02.json`；历史等待；2026-10-30用户新20小时指令已明确批准匹配依赖，当前正在实施。

本轮native依赖已实际准备：C255 QLI metadata绑定需要新`aclnnVllmAscendQuantLightningIndexerV2Metadata`，旧C253 donor缺失。自己的C255/A3/CANN9.1 vendor包已用原3.11、4jobs、独立缓存构建成功（1754.212秒），15,923,063B/SHA494578ced793ebf597ba4395bc5de6c752d55fc504ac3cfde90b4e20f7ba9b40。readelf核新Metadata/WorkspaceSize符号，包内与生成库SHA93b500a9ec299cd69bad79a7c858122de37b07fd95342ec90e7327ec6ef13c24相同。未运行installer/最终加载/CP312扩展；不是ABI或设备通过。仅private build recipe将prepare.sh并行限制4，原固定源码不变，无下载/共享配置修改。详见PREP/vendor-only/vendor_build_review01.json与build receipt。

16K/32K/64K/128K固定输入已建立于 `dev/adapt/inputs/20261029T012724Z_R8_node103_8f889187/DSpark_matched16to128k_n4c1_v1/requests.json`，SHA256 `63db6759bea0b8042b8562c5edbc3bd41c28ffaf1c9d2809c63448f0d83776ed`。32K与C201逐字段/IDs相同，其他长度沿同canonical流与四移位构造。来源是一个重复双语技术段落的合成长上下文诊断，四请求不是独立业务语料，也不是师傅历史随机数据；仅固定测量负载，不关闭质量/代表性要求。MANIFEST记录tokenizer/current重建及cold/no-hit规则，未启动新队列。

新pair数值工具的a982 context前缀修正已完成准备：Graph前快照Target features/positions，从原case及canonical Full table独立重建Full context slots，KV恢复后调用固定上游真实context helper再跑eager query；严格输出/全部选中K/V后态/原Full写/Target/ABA保留。actual_cpu_context_result_attempt01.json记录原Python3.11/Torch CPU 1.72秒、4正例及5损坏拒绝，无PTA/vLLM/NPU。仅证明工具tensor兼容，不是C255模型PASS；prepared manifest仍disabled。依据同PREP/C255_prepared_tools_root_review01.json及C255_numeric_tools_prepared/context-prefix-v3/review.json。实际新runtime/native/模型资格仍待R8-C255-RUNTIME-01。

**Eagle局部接口进展（2026-10-29T20:36:41.271153+00:00）**：独立分支dev/mrv2-graph-r8-pr534-eagle-bridge已保存C256 `9415c47762cffc53644f619ed7969335a9ccec96` /treeaee4d8c98597f1a99a35b42d2cf138bf198f4215，固定 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/node140/C256_PR534_Eagle_bridge/vllm-ascend`。在C255基础上只接Eagle mixin、AR manager的session分支；保持first Q4和AR1/AR2各Q1独立bank、eager first退休/adopt后仍merged AR Graph、dummy/continuing基线、当前exact与Full写。21项控制绑定实际已应用Source/hash通过，独立审查无新具名问题；通用typed UPDATE、共享AR speculator、upstream及PR未修改。原Eagle有效输出FAIL/API未知仍在；默认关闭attention discriminator尚未适配typed capture，开启明确拒绝；普通numeric标志False不受该诊断guard影响。此为必要接口实现，未进行新runtime真实模块/模型/数值测试，不宣称原失败已修。主线DSpark新pair生产基础仍C255，工具候选现为C258，不将其尚未产生的PASS转给C256。原件 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C244_glm_dflash_required_OFF_baseline01/required-eager-prepared/integration-actual-check01/eagle-new-pair-prepared/root-C256-commit01.json`。

自有vendor被动树已安全暂存于 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/work/node140/native_C255_vendor311_build01/private-vendor-staging01`，1311 regular files/51,322,939B，仅自身已构建包的bytes；排除install/uninstall/upgrade脚本，内部软链接经范围核验，库hash与生成/包内一致。未运行installer、最终库加载或312依赖，无设备活动。它不是部署或ABI资格。

**新pair四长度性能真实缺项**：C255/a982尚无实测，不能用84030旧结果填表。固定输入为16000/32000/64000/128000，每长度4请求、输出2000/C1、K8/Q8/W1024，16rank。当前各长度的G_OFF/G_ON/E_ON Output tok/s、TPOT、E2E、平均接受长度均为 **NOT_RUN**；前置是runtime依赖选择、own CP312 native/导入、代表性数值/Full写/Target和受影响eager回归。旧84030启动约17–20分钟、32K单组OFF约474秒/ON196.7秒/E211.9秒，只能支持新组六实例约14–22设备小时的低置信预算；64K/128K尚未实测校准，不保证在此区间完成，不派发必然越过收尾的长实例。C253是DFlash且out256，不混作此DSpark性能。

**runtime启动的两个具体适配前提已静态明确**：①父进程-S不能覆盖Torch裸Python子进程；建议标准private零安装venv骨架＋自有纯路径.pth，选择独立固定Source（自有CP312 native在包根）、owna982及只读generic依赖，禁止执行PR editable finder。②own a982缺合法生成_version.py，可复用同a982干净checkout的561-byte SCM文件（SHA338188c2cc11ee8c419743e65ee780bf8a8d1f3f91ef2eb6cecbe3a949644064），模块实际0.1.dev1+ga98247ab4与dist metadata的.empty后缀分列，不能借旧VLLM_VERSION覆盖真实来源。所查NPU入口无必须复制PR upstream vLLM二进制的依据；own CP312 Ascend extension仍须构建。未创建新env/复制该版本leaf/启动312或加载新栈，原runtime问题等待用户答复。执行草案以PREP/private_cp312_bootstrap_plan.disabled.json（SHA6a52010d…）和extension_build_preparation.json（SHA81f32b77…）为准，默认禁用；原provenance revisions/hash保留。
<!-- R8_PR534_INTEGRATION_END -->

<!-- R8_C253_REQUIRED_COLD_BEGIN -->
## C253 GLM DFlash required/cold平衡测量：6/6实例完成

UTC2026-10-29 19:45:58最后wrapper真实退出0。六实例producer/checker/outer全部0、各16rank关联、worker和租约全部释放；无自动下一项/重试。每臂2独立实例×3正式重复，共36组/72正式请求；另24请求预热全部排除。未采样观察到外来设备context，不等于证明Host绝对独占。

固定C253 `54f8c6611cf3a422f84ce578e46887727c6827ea` / vLLM84030、TP16/DP1/EP16、DFlash K15/Q16/W1024，Target FDO，Draft按G_OFF/G_ON/E_ON。Async/prefix/chunk256/SP/legacyDSA-CP/FlashComm同底座；prefix引擎ON，正式单元重置缓存+salt并核实际cached0。每组2请求、串行C1、各输出256。顺序OFF/ON/E与E/ON/OFF；同实例重复不冒充6次独立启动。轻量Host审计开销仍包含，重型observer/数值/逐代LIFE同步/profiler关闭。

|实际输入tokens|臂|组E2E中位（范围）s|组Output tok/s中位|平均TPOT中位 ms|平均TTFT中位 s|平均接受长度含bonus|accepted/proposed|
|---|---|---:|---:|---:|---:|---:|---|
|短（76/70）|G_OFF|13.7608（13.3833–14.1983）|37.218|24.341|0.6487|3.4353|2182/13440（16.235%）|
|16K（16012/16006）|G_OFF|95.6172（93.1976–97.7368）|5.355|19.850|42.0590|4.0955|2334/11310（20.637%）|
|短（76/70）|G_ON|14.5111（14.3048–14.6377）|35.284|25.923|0.6395|3.4353|2182/13440（16.235%）|
|16K（16012/16006）|G_ON|95.0329（93.6034–96.7945）|5.388|20.824|41.6862|4.2283|2376/11040（21.522%）|
|短（76/70）|E_ON|14.7910（14.6301–14.9692）|34.616|26.414|0.6594|3.4353|2182/13440（16.235%）|
|16K（16012/16006）|E_ON|96.1813（93.7972–99.9872）|5.323|21.192|42.3260|4.2283|2376/11040（21.522%）|

Window ON相对Graph OFF：短组E2E**回退5.45%**、tok/s−5.20%；16K E2E节省**0.61%**、tok/s+0.61%。同Window Draft Graph相对Draft eager：短组E2E节省**1.89%**、tok/s+1.93%；16K节省**1.19%**、tok/s+1.21%。两类问题分别裁决，不将耗时节省直接当吞吐增幅。16K各臂E2E变异系数约1.2%–2.1%，不能把0.61%视为稳定产品收益。短组达到既定>5%定位触发线，不是自动否定整体功能；未批准正式性能门槛。

TTFT取客户端首个非空token交付；TPOT取首末交付span/(实际输出N−1)，不是E2E反推；SSE可按接受块交付，未取得可靠逐token ITL分布。每臂12请求sampler接受数只记一次，计数在stop trimming前、排除bonus/padding、不跨TP累加；含bonus平均接受长度=1+accepted/验证步数，不是准确率。16K TTFT约42秒/请求，E2E主要受prefill影响；不把整模型初始化/capture约35分钟计为推理耗时。

短组每repeat跨臂proposed/accepted/验证轮数完全一致，原b1/G_ON materialization短组window_start=0、CPU exact最大350<W1024，未实际裁窗；不能用接受率或裁远上下文解释其回退。长组原b1记录实际window_start14976–15232、有效读长1024–1151。已有四实例cost_review只给混合短/长rank0 Host manager并集，缺逐proposal归因，不能把4字节snapshot等同纯拷贝或删除必要等待。没有追加轮次追求正收益，原因仍需基于具体新线索定位。

原件：BASE/raw/C253_R8_GLM_DFlash_required_cold_b1_p1_G_OFF_01_node140 等六个精确run；完整机器读汇总 `reanalysis/C253_required_cold_balanced01/current_summary.json`、逐组原始计数 `formal_groups.csv`。初次CSV派生列名映射缺项在本地发现，原派生文件以attempt01保留，最终列名和36行完整性已核；producer/checker/数值结论未变。六实例自然轨迹已只读补齐：同Window G_ON/E_ON 24/24逐token相同，Graph OFF/ON 24/24相同，同臂跨实例对应repeat 36/36相同；实例内跨repeat共72对为24同/48不同，最早第9输出token（3491/3409）。实际输入IDs/temp0/seed0/cache salt/SSE与usage关联核对无异常；完整原KV/Target前态未保存，原因仍UNKNOWN，不视为准确率或质量结论。trajectory_review.json SHA256093a3e54c83f27b88cbef43ed4119c71662989caf96bd1a70c4bb970ddd80ae8；cost分析仍为原四实例范围，不扩大归因。旧C241普通配置、140/101不同机和C255新pair均不混表。计算正确性/正常完成合同/自然质量/性能与发布分别记录。
<!-- R8_C253_REQUIRED_COLD_END -->

<!-- R8_C254_FULL8_REQUIRED_BEGIN -->
## C257短G_ON Host成本诊断：已限定完成

C257 `c41b611c9a3a47c0f34bbe9a8735b08c8b8ee692`，production与C253相同，311/84030/native未变。只选原76/70-token两请求、各out256/C1，一次warm＋一次诊断；与C253完整warm短+长及6重复不拼性能组。UTC21:15:15启动/21:43:37退出，模型1659.716秒/outer1702.349秒，producer/checker/outer均0、16rank实际关联；无外来设备context观测，非整机排他证明；自有进程/租约全释放。

诊断组实际14.379849秒。16rank各单TID/2561条span，audit self壁钟31.466–33.915ms、threadCPU30.332–32.969ms；**不把16rank相加当elapsed**。rank0 phase-prefix约24.646ms；provider-bind151次壁钟299.646ms/CPU297.412ms。production按同TID区间并集，rank0约11659.341ms，不能把manager/update/bind嵌套相加。exact-snapshot151次壁钟10826.370ms、threadCPU392.874ms；其中承载前序工作等待，不能按4字节算带宽或删掉本代exact/完成边。各rank749条context UNKNOWN、1051条generation UNKNOWN保留，不用邻近时间补关联。

本次没有OFF控制，私有timer自身增加未校准开销，因此仅支持“审计自CPU在本次为几十毫秒量级、下一步有界核对实际绑定Host工作”，**没有定位C253全部回退根因，没有生产优化PASS**。未新增数值/Full/Target/LIFE/质量裁决，也未直接观测device operand/read-set。

原件：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C257_R8_GLM_DFlash_required_G_ON_short_audit_diagnostic_01_node140`；只读分析`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C253_required_cold_balanced01/C257_short_audit_analysis01.json`（SHA256 `7d613a7e1db5e3f22778a21bb79e8dd9acf9290f23f49a669adbb1e369ce1ba2`）。原私有工具身份错关联、旧错误接受反例和修复在`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C253_glm_required_cold_performance01/short-audit-diagnostic-prepared`，已在加载前关闭；修工具不算生产功能新增。C258工具接线已完成并固定；provider-bind窄审未找到不改合同且有收益依据的小改，不重启相同诊断。

## C254 Full8 DP2共同特性：OFF/ON两臂限定通过

固定C254/84030、Qwen3.6 Full8 DFlash K7/Q8/W32768，TP4/DP2/EP8、Phy8–15；Async/prefix/chunk256/SP-MoE/FlashComm共同开启，DSA-CP false。OFF模型676.462秒/总715.069秒，ON模型689.127秒/总728.073秒；两臂producer/checker/outer全部0、无signal或timeout，8rank/两DP实际请求/非dummy Host Graph dispatch、prefix命中和continuing/terminal/decode/mixed均核对通过。ON于UTC20:19:01.675995完整退出，租约20:18:45.578640释放，remaining_owned_pids为空，无自动下一项。每臂12预热＋12功能请求，一次功能集不是性能重复。

请求global4/2/6对应各DP local2/1/3、最大padded4，含33025越W输入与8193前缀复用。ON每DP实际window_clipped=true，所有worker source_prefix_identity=true，正式long请求各DP cached_tokens31744。两个DP proposal分别1105/952（含warm及调度，不作设备执行数）；8worker均具名关联，所有声明phase均出现。

这关闭当前共同特性服务缺口，不覆盖active8；C228有效数值FAIL及C232/C238调用层API待确认仍保留。功能checker原字段保留：内部numeric为NOT_ASSESSED、normal_completion为NOT_PROVEN。现已完成独立适用性审查 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/Full8_DP2_required_features_prepared/C254_required_normal_reader_scope01.json`：DP0每TP967代/967绑定、DP1每TP809代/809绑定，8rank前后provider/runtime/main/update/bank不变；同Source/API FIFO、ExternalEvent及Graph尾notify链覆盖实际Async/prefix/chunk/SP/FC上下文，未发现新具名缺边。成功退休scratch reset含原native zero写，并非纯Host，但与持久Graph bank分离、顺序和异常隔离不变。这支持用户已接受范围的正常reader工程审查，不是新device completion测量，也不把HTTP完成当最后reader证明。直接execution operand/physical read-set未观测，业务质量和正式性能未评。本次CPU vendor编译与功能服务并行，服务总耗时不能当干净性能结果。

原件：BASE/raw/C254_R8_Qwen36_Full8_TP4_DP2_required_G_OFF_01_node140 与 required_G_ON_01_node140 的result.json、joint.json、execution.json、own_cleanup_exit_audit.json、lease_release.json；outer exit在orchestration/Full8_DP2_required_features_prepared/C254_disabled_functional_plan01。原producer/checker均6b9c145b，不归为C255新pair设备通过。
<!-- R8_C254_FULL8_REQUIRED_END -->

<!-- R8_RETIREMENT_EXCEPTION_BEGIN -->
## 具名实现缺口：proposal成功后的回收异常已限定修复并验证（保留原反例）

2026-10-29T21:10:55.289227+08:00。C247/production7099的真实AscendDFlashSpeculator.propose→proposal_scope→retire_generation→lease_pool→workspace.reset/_zero_all，以首个zero_的明确CPU stand-in写后抛异常，实际最小反例FAIL。原件 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C239_glm_loaded_multirow_subset/required-feature-adaptation-prepared/retirement-exception-host01/actual_cpu_result_attempt1.json`；不是模型设备失败、不是基线精度/API问题，也不套Q017。NPU未初始化/无计算设备FD。已保留active runtime/lease，但uncertain=False、原native_full_snapshot清掉，下一scope body实际获准；仅依最终materialize拒绝不能排除其前段设备准备。

最小修复限定vLLM-Ascend成功retire/record异常：纯Host标记不确定、保留snapshot/owner、原异常重抛并在下一scope入口拒绝，不再reset/zero/query/sync。覆盖同一Graph及同步eager分支，正常Async lane分支保持；修复已提交并固定C248 `396a6000d10eb5cde846dc7033b88d76d5f239e0`/production b6f3341…：Graph/同步eager reset异常、退休后记录异常及相邻正常/Async共9个实际DEV定向CPU检查通过；原FAIL保留。正常Async pool分支不改，尚未设备复验。C246固定健康ON继续，已有正常数值/服务不被改成FAIL；但原生命周期10分中重开1点，管理84→83，NOT_READY。

PR冻结0be/tree e9af2ff3…已只读核对：无adapt Workspace.retire/reset/_zero_all链；其sync/Async eager共用OwnerPool.operation，record/query/wait/active-body错误均quarantine＋poison，_release仅清Host引用。固定源码4个CPU错误控制检查阻止下一acquire；本次具体缺陷不适用于其固定实现，不新增PR阻塞。来源required-eager-prepared/REVIEW.json的PR_impact_retirement_exception，最终整合仍需组合验证。直接operand/physicalread未观测的既有证据决定不豁免本次具体错误。

**2026-10-29T22:56:09.667555+08:00追加终态**：C249 entry02真实worker受控退休入口异常完成，next真实Source scope在body前拒绝，原异常保留、uncertain=True/active owner不变，无postfault设备操作；结合实际DEV9、原reset写后异常及记录异常反例，具名Source隔离漏洞限定关闭。不是原生部分提交故障或所有16rank新异常证明。`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C239_glm_loaded_multirow_subset/required-feature-adaptation-prepared/retirement-exception-host01/device-prepared/source-boundary.json`记录独立联合审查；恢复原暂扣生命周期1点。
<!-- R8_RETIREMENT_EXCEPTION_END -->

<!-- R8_C248_REQUIRED_EAGER_BEGIN -->
## C248全特性E_ON功能对照已实际通过

2026-10-29 13:59:30Z真实终态，固定C248 `396a6000d10eb5cde846dc7033b88d76d5f239e0`，GLM5.2+DFlash已QuaRot对齐底座、TP16/DP1/EP、K15/Q16/W1024、Target FULL_DECODE_ONLY/Draft eager。producer/checker/runner/outer均0，16rank设备关联、全部自有进程/租约释放；model1731.907秒、外层1778.902秒含初始化/预热/清理，不算推理性能。

6warm另计；6功能请求共35206输入/1536输出，prefix命中5/6，实际cached tokens为[128,8064,16256,8064,0,1920]。每rank2独立eager lane、371个Window代、444个proposal/eager forward Host返回、73个all-continuing full-read baseline、329次Target Host Graph调用；Draft Graph调用/库存/provider/bind为0。实际4类调度阶段及12条HTTP到内部request ID精确关联成立；Target78个CP层、每rank444个metadata/CP上下文。Async/prefix/chunk/SP资格及路径/legacyCP/FlashComm有效配置/EP按具名checker成立；FlashComm不另宣称独立kernel trace已证明。eager active/padded为1/1、2/2、3/3，不能与Graph原臂3/4强配自然数值。

只关闭同一required-feature底座的真实eager功能能力；不是5次匹配性能、独立内部数值、Graph最后reader或业务质量批准。C246独立数值与C244 Graph reader材料按各自身份引用；成功收尾异常由C248修复/C249单worker验证另行闭合。原件 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C248_R8_GLM_DFlash_TP16_required_features_E_ON_01_node140/result.json`，43662B，SHA256 `ca3f02f874302dc144f62113d6f1e507e15a329dda7cfe083fe3f3584f8959f9`。审查索引在C244 required-eager-prepared/REVIEW.json。停止后的EngineDeadError按已保存的自有shutdown时间线归类，不改成请求生产错误。
<!-- R8_C248_REQUIRED_EAGER_END -->

<!-- R8_C246_REQUIRED_NUMERIC_BEGIN -->
## C246新Q16 CP/SP上下文：三场景严格数值、Full写与Target48已完成

2026-10-29 13:57Z。producer/checker均固定C246 `b1b94bf93ae2609e5380214d70cb846c3940a353`；GLM5.2+DFlash、K15/Q16/W1024、TP16/DP1/EP，同已接线Async/prefix/chunked/SP/legacyDSA-CP/FlashComm配置。原场景7/10/11为mixed active2/padded2、active3/padded4、active4/padded4。实际ON全16rank×3有效BF16输出与canonical独立eager参考严格零差异（atol=rtol=0），5层KV/Full写精确；OFF为独立Target底座，两模型producer/checker/outer均0并清理。OFF首次纯launcher模块名错误保存，真正成功原件为attempt02，不改写第一次失败。

离线Target联合实际1689.772秒、rc0，16rank×3共48对全部PASS。原件 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C246_glm_required_cp_numeric01/joint.json`，321634B，SHA256 `97317e796634a3041202fcd942c9f956b9f30a4d60dc72ad500bf2098b226591`。独立CPU只读重算，不是第三次模型/NPU运行。此项只覆盖所选三场景完成后串行诊断，不重新标记完整14/ABA、正常Async overlap或直接operand/physical read；正常reader适用性另引C244 Source/API与实际绑定，退休异常另引C248/C249，不混为单份全面PASS。
<!-- R8_C246_REQUIRED_NUMERIC_END -->

<!-- R8_C244_NORMAL_READER_BEGIN -->
## C244全特性正常Graph reader：适用性已核对，CP独立数值另验

2026-10-29T20:34:09.269993+08:00。原件 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/GLM_DFlash_C244_required_context_reader_scope01.json`，45630B，SHA73b18bf18056ef2c37dd1aa4b7a838effccb056f04a1280af6cfdecfc0ea6bf8。固定Source六文件/native身份与既有Source/API合同一致；实际C244 ON全16rank各400generations/400 Host绑定、3bucket provider/runtime及table/CPU exact owner稳定，Async/prefix/chunk/SP/legacyCP实际进入，重型观察关闭。72个all-continuing baseline提案不消费Window Graph；自然有效行1/1、2/2、3/4，未自然覆盖active4。

未发现新的具名缺失完成边，支持用户已允许的Source/API＋实际绑定/所有权限定工程审查；HTTP完成、Host返回、Target copy或eager event均未被当作Graph最后reader完成。合法原件通过、7种具名损坏仍拒绝；直接operand/physical read-set为NOT_OBSERVED。新CP/SP独立数值/Full写/Target由C246三场景继续验证，现未把C239无CP数值或服务PASS扩大为此项通过。

**退休范围纠正（2026-10-29T13:55:53.803073+00:00）**：上述冻结reader原件保持hash不变。其中“successful retirement is logical only”不能概括整个scratch退休链：实际`retire_generation → pool.retire → Workspace.reset/_zero_all`会提交scratch清零。固定captured bank的持久所有权及FIFO/ExternalEvent/Graph尾notify证据仍按原范围有效；正常400代绑定不因此作废。新发现的成功收尾抛错隔离缝隙由C248异常guard及独立反例/待测单worker异常补证处理，旧normal-reader报告不覆盖该错误路径。
<!-- R8_C244_NORMAL_READER_END -->

<!-- R8_C241_OBSERVER_COST_BEGIN -->
### C241性能的轻量审计边界（Source有界核对）

C241是带既有轻量Host审计的正常三臂测量，不是observer全关的生产性能。实际MRO不经过RankNumericWorker/GLMServiceWorker，无串行参考/phase deepcopy/Target dump。ON/E_ON每代额外创建CPU字典/row列表并对已CPU-owned exact做tolist；仅G_ON还记录submitted_carriers身份，getter只是已存tuple。短正式段每rank ON/E_ON各615次materialization，三臂同9075proposed/1970accepted/605验证步。没有发现这些**审计**新增D2H/sync/event.query/整张量clone；这不否认生产Window本身已有exact snapshot与必要等待成本。

身份RPC在cohort前后，校验与HTTP组计时不重叠，组JSON写在group_end后；仍有上述ON/OFF不同的CPU审计成本，当前不能定量归因为7.14%短回退。保留原数据/负收益，未新加ablation或重复整个cohort。依据 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C231_balanced_summary01/C241_observer_cost_source_review01.json`，19007B，SHA256 `7a5c4ffb2fc84598d602b656a442cc0a474ce58c07f860ebe77d1ad79d2b2341`。只在出现可检验的新假设且预算合适时考虑移除测量工具的审计成本；不能把移除工具后的变化写成生产代码收益。
<!-- R8_C241_OBSERVER_COST_END -->

<!-- R8_C242_REQUIRED_FEATURE_STARTUP_BEGIN -->
## GLM DFlash：C242新全特性上下文启动失败（未进入功能/数值检查）

2026-10-29T19:09:11.601505+08:00。C242 `68c9c99ed3c1c0f343c0f216d71eb3b0ebb28062`、fixed84030、同Q023对齐GLM模型/K15/Q16/TP16；相对C241同步prefixOFF测量，本次开启Async、prefix、chunked、FlashComm/SP及legacy DSA-CP，batch256、capture[16,32,64]，预定C148真实12请求。但实际producer1/runner2、外层446.24秒退出，尚未HTTP ready、未运行请求，不能填全特性服务PASS。

明确Python报告在rank9/PID1598457的Target启动profile dummy SP通信；显示all_gather栈、PTA working-op HcclReduceScatter、原生AICPU allreduce和allocator stream错误。它们异步报告，不能强配为同一次算子；Python内嵌18:50:36也不等于已确认首发设备时刻。保存own PID原生plog、106行excerpt及有界Source核对：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C242_R8_GLM_DFlash_TP16_required_features_G_ON_01_node140/firstcause_review01/review.json`，12476B，SHA21933ac6adce29e1ba89db29dcbd46ae4dd3cb9458b7ecadd396eaf5a59165f8。相关runner/worker/Deepseek patch/parallel_state/utils与C151逐字节相同，但DFlash方法/aux/capture64不同，不能由DSpark历史PASS排除新上下文问题；尚无具体需修的本任务stream/参数错误，也未证明独立官方平台缺陷。

原运行Phy8有稀疏未关联context，既有原件不删；不据此认定因果或他人杀进程。随后用户确认16片可用，11:06:57UTCfresh只见本任务Eagle四片，资源等待解除。C242全部本任务worker/租约已释放；不因看到外来PID主动结束健康服务。

本轮对照已经推进：C244同模型/K15/Q16/TP16/capture/全特性，仅Window OFF，producer/checker0、外层1796.6962秒，6warm＋6functional成功，全16rank精确设备关联；actualprefix cached tokens包含8064/16256，mixed/continuing/terminal/decode均有CPU阶段原件。OFF每rank499次Host提案、385次Target调用不是设备执行次数；Window provider/runtime/绑定无工作。证据 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C244_R8_GLM_DFlash_TP16_required_features_G_OFF_01_node140/http-artifact-joint.json`。收尾后EngineDeadError位于显式shutdown触发及自身EngineCore终止之后，原日志保留，不误记请求运行失败。

OFF实际成功不证明C242原ON错误的原因或整个底层无问题。随后同固定C244 G_ON/W1024于UTC11:48:17启动、12:17:32结束，producer/checker/runner/outer均0，16rank设备关联、6warm＋6functional及全部特性实际检查限定通过，model1715.5267s、outer1755.2618s；自身worker及租约均已释放。C242原失败保留，仅记新尝试未复现，不宣称已修复其根因，不混入正式性能。日志 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C244_R8_GLM_DFlash_TP16_required_features_G_ON_01_node140/model/server.stdout.log`。capture过程GLOBAL/72B H2D EE1016原件及Source有界判读保存原raw/capture_native_observation01，实际Target/Draft capture均完成并完成请求，但72B来源/具体fallback仍UNKNOWN，不认定平台缺陷。

新上下文数值仍缺：C239原7/10/11仅sync/no-prefix、无SP/legacyCP；C246私有工具已固定，仅补同原三场景Q16 CP/SP。137唯一CPU用例分三attempt通过，导入/解析首失败保留。没有新生产/native变化；C246已启动CP/SP数值OFF，尚无该次数值裁决；串行数值不代替正常Async/prefixhit完成链。
<!-- R8_C242_REQUIRED_FEATURE_STARTUP_END -->

<!-- R8_C239_MULTIROW_RESULT_BEGIN -->
## GLM DFlash：新加载多行两臂与Target48（已完成）

更新2026-10-29T18:27:23.926541+08:00。producer/checker固定C239 `595e0c65e5dfbe3e1bb7f36ed294f32a8f27c15f`，tree02368db...，production7099...，同Q023对齐GLM Target/Draft、TP16/DP1、K15/Q16、W1024。仅补原7/10/11：mixed2/padded2、active3/padded4、active4/padded4；16rank各3样本，全5层Dense Draft KV与177种Target组件。ON独立canonical eager同前态、有效输出分别32/48/64×6144，BF16、原atol=rtol=0，全部48样本finite/max_abs=max_rel=0、kv_equal=true。padding按backend合法写槽合同核查，不把未定义输出作为有效数值。

OFF model1011.77s/check164.36s；ON model955.92s/check166.33s，各模型/checker/监督器均0，独立nonce且完整16rank实际设备关联、own worker空/租约释放。单臂检查不等于Target联合，随后CPU独立重读完整产物并完成48对Target：checker0，1500.43s，结果 `PASS_SCOPED_GLM_DFLASH_TP16_TARGET_MULTIROW_7_10_11_48_PAIRS`。完整原件 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C239_glm_loaded_multirow_subset/joint.json`，321360B，SHA256 `e477d0a12ecdd9b484fc6b68b5f841ddc8fcdb725b3f9fe58b29737682f09b26`；两臂raw `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C239_R8_GLM_DFlash_loaded_multirow_{OFF,ON}_01_node140/`。

本次是串行诊断，不新增完整14/ABA、正常Async重叠或物理read-set结论。C208已成立prefix3/ABA和旧C159/C164完整14分别保留身份；当前新Async/prefix/chunked联合上下文另列必要验证，不由这里自动关闭。
<!-- R8_C239_MULTIROW_RESULT_END -->

<!-- R8_C241_MATCHED_RESULT_BEGIN -->
## GLM DFlash：C241同机三臂5次实例内测量（已完成）

更新2026-10-29T14:56:31.742764+08:00。producer/checker C241 `9fba44cc859b718d553a70d2f56142f214233f08`、vLLM `84030bbe...`、node-25-140；Target `/mnt/share/weights/GLM-5.2-w4a8`，Draft `/mnt/weight/GLM-5.2-FP8-DFlash`，同一Q023已对齐加载底座。TP16/DP1/EP、K15/Q16、W1024、max_model_len24576、输出每请求256、每组两请求顺序执行/c1；短输入76/70、长输入16012/16006。Async/prefix OFF，Target FULL_DECODE_ONLY保持；G_OFF/G_ON用Draft Graph，E_ON仅Draft eager。不是DSpark全特性性能。

三实例固定G_OFF→G_ON→E_ON，每臂先完整4请求预热，再20正式请求（短/长各5组），共60正式/12预热；每组512实际输出。三臂各producer/checker0、16rank实际Source/物理设备关联与清理通过；没有数值/LIFE同步/profiler。**1boot/臂、5次同实例重复，非5个独立boot或逆序双块；时间/次序相关性保留。** C231原六实例及干扰记录独立，不池化。

|负载|臂|正式组耗时中位[min,max]秒|输出tok/s中位|accepted/proposed（bonus/padding不计）|验证请求步|客户端TTFT中位秒|请求mean-TPOT中位秒|
|---|---|---|---:|---|---:|---:|---:|
|短|G_OFF|8.164828 [8.093208,8.235262]|62.7080|1970/9075=21.7080%|605|0.444760|0.014345|
|短|G_ON|8.748118 [8.648989,8.939238]|58.5269|1970/9075=21.7080%|605|0.468034|0.015395|
|短|E_ON|9.511428 [9.473389,9.552029]|53.8300|1970/9075=21.7080%|605|0.484259|0.016728|
|16K|G_OFF|21.548487 [21.490630,21.722899]|23.7604|1805/11250=16.0444%|750|5.814589|0.019460|
|16K|G_ON|21.917840 [21.894484,22.064558]|23.3600|1830/10875=16.8276%|725|5.859246|0.020036|
|16K|E_ON|22.863120 [22.769283,22.900591]|22.3941|1830/10875=16.8276%|725|5.874563|0.021744|

- Window ON相对OFF：短**耗时增加7.14%/吞吐降低6.67%**；16K**耗时增加1.71%/吞吐降低1.69%**。同Window Graph相对Draft eager：短**耗时节省8.03%/吞吐提高8.73%**，16K**耗时节省4.13%/吞吐提高4.31%**，不混用两个百分比定义。
- 短负载G_ON/E_ON实测S=0、exact86–349，未实际裁窗，CPU active/padded=1/1；三臂accepted1970/proposed9075、验证步605一致，G_OFF/G_ON Host Draft Graph615/Target605一致。回退触发既定>5%定位线，不能归为“裁远处上下文”或接受率变化。ON准备/绑定和CPU审计存在额外成本，但这组未单独把残差归因某kernel/带宽；不为消掉该数删除必要完成边。
- 16K G_ON/E_ON实测S14976–15232、exact1024–1151、active/padded1/1，确实裁窗。接受率16.0444%→16.8276%，验证步750→725；Host Draft Graph790→735、Target750→725。Draft Graph次数差还包含continuing-prefill走NONE/full-read的工作分类，不能当成少做55次总计算或设备执行次数。
- accepted/验证步是不含bonus的平均接受Draft长度：短各3.2562、长OFF2.4067/ON与E_ON2.5241；含bonus另加1。计数在stop裁剪前，不累加TP ranks，分位置原计数和全部逐请求SSE保留在机器可读结果。TTFT为客户端开始到首个非空SSE token；meanTPOT为首/末非空chunk间隔除输出token数−1，非设备纯decode；逐token ITL分位数**NOT_AVAILABLE**。

自然输出的两类配对共40对，40对相同；只表示原服务输出一致性，不是准确率/业务质量或同KV前态数值证明。数值/Full写/Target依C208及当前C239独立检查。三臂管理采样未观察外来device context，**不据此宣称Host排他或真实峰值**。CPU/RAM为40秒抽样（sumRSS重复共享页、VmHWM含PID历史），HBM只报整臂管理采样上下文，每负载峰值未可靠获取；资源解析已用真实已结束样本和对应损坏副本做12项CPU检查通过；三臂各4个正式整体采样点/3个完整CPU区间、逐组没有完整40秒CPU区间，27/28/29份管理采样均完整解析16Phy。没有发现工具bug，原summary/hash保持；不把这些解析检查计作设备PASS。

原件索引与逐样本、实际Source/native、计数/资源：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C231_balanced_summary01/C241_single_cohort_summary.json`，当前SHA256 `cdc0ce2a750d1db269bfc54115bc5d6c0c010aaeb3b68e8228328eae5aca8111`；原raw为`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C241_R8_GLM_DFlash_HTTP_five_repeat_global_b3_{G_OFF,G_ON,E_ON}_01_node140/`。

结论：**测量完成，未获正式性能/质量/发布批准。** 短无裁窗出现明确额外成本，16K接受工作量改善仍未取得Window净收益；同Window Draft Graph在本组快于eager。保留负向与全部慢样本，不增加第二替代cohort或扩大64K/128K扫描。
<!-- R8_C241_MATCHED_RESULT_END -->

<!-- R8_EAGLE_TARGET_CANARY_TOOL_BEGIN -->
## Eagle同一次数值诊断的Target非干扰工具：已固定、尚未设备执行

2026-10-29T13:01:25.702206+08:00，C240 `a94bca867288d0c8e0cea1fcd9e272132bb08394` / tree `5ed67471711990419e34bc035c3bafd536448961`，生产树仍`7099f9d5a98c47d9f92e6982b6758971fc6c4b53`。只改Tool77/78及一个小测试：复用固定Qwen Hybrid Target80组件，围绕原3请求组、每组first/AR1/AR2共9consumer，在同一TP4 ON模型采Target Full/GDN、输入及metadata前后状态。最后AR写槽由Target-before的query/rejected/绝对positions与原canonical表独立推导；common全capacity、每metadata/forward槽、有效前缀和全部-1尾部严格检查，不照抄Graph carrier作为期望。unknown提交后仅Host通知/隔离，无额外设备读取或下一proposal。

定向Host首轮209通过/19项因attention导入顺序失败；按真实入口先import ops后仅重跑19项通过，累计228项，NPU未初始化/阻止的设备操作0。原失败日志保留在`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/host/C240_eagle_target_canary01/`。这不是设备PASS、完整Target独立forward/logits、正常reader、硬件read-set或旧TP2失败豁免；默认producer/原数值与Full写容差不变。Source和1223 native/generated文件按C239同inode保留，runtime`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runtime/node140/C240_eagle_numeric_target_canaries/runtime_manifest.json`，SHA `ef5f5048d40727627906d42f0366182784aa83fc9d1fd7477fa01e0fa702ab5a`。

原C231六实例已结束并保留；当前C241独立5次cohort受测源码不改，后续GLM多行仍用已固定C239。Eagle旧C237禁用numeric计划不原样执行，已用新C240独立禁用绑定替代这一尚未执行项，减少额外模型重载。仅工具准备不增加进度。
<!-- R8_EAGLE_TARGET_CANARY_TOOL_END -->



<!-- R8_EAGLE_TP4_ACTUAL_BEGIN -->
## 本轮Eagle真实TP4进展及剩余边界

C237固定`8f889187b33b719290e40342ca020b46c61244bc`，Qwen3.6指定配对TP4/DP1/EP4、K3/W1024，Target FULL_DECODE_ONLY、Draft AutoRegressiveAclGraphManager；OFF与ON分别508.276/490.830秒，producer0/四rank外部联合checker PASS，5请求输入257/2051/771/387/259，各32输出，共3725输入/160输出；所有本任务worker与租约释放。上述elapsed含加载/编译/预热与请求，**不用于计算窗口或Graph性能收益**。不是PR W1035、完整数值、Target或质量PASS。OFF细节`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C237_Eagle_TP4_G_OFF_anchor_summary01.json`，两臂raw在`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C237_R8_Qwen36_Eagle_TP4_{G_OFF,G_ON}_anchor_01_node140/`。

当前ON每rank48个Host Graph epoch、144次bank绑定、9个稳定bank table地址；first独立Graph、AR1/AR2同merged Graph但各自独立bank/event，scratch退休只表示bank拷贝入队，bank复用依赖Graph tail合流/RI endGraphNotify与同current FIFO。actual runtime_v100/PTA/native已匹配固定API材料；未发现具名缺边。不拿Host finish、HTTP/进程退出或Target较早output-copy event当最后Draft reader完成。Source审查`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C237_Eagle_TP4_three_consumer_normal_reader_scope01.json`（f1a72c538c0661f5c10fcf752ad7cbaef0efda1b37c02246e6a6af87f2fb3ad6）。Eagle独立数值与Target仍缺，故不是完整生命周期/正确性闭合；旧TP2 C203/C213/C216反例与API合法性未知保留，逐次operand/physical-read NOT_OBSERVED。

具名TP4 Tool78九consumer＋Q/attention区分计划`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C237_eagle_tp4_numeric_prepared/plan.disabled.json`已非设备预检、保持禁用。仅原3请求组×first/AR1/AR2、原容差与Full写、真实canonical eager参考，不重采旧TP2。此处C237禁用numeric计划仅为历史、不再执行；当前实际数值/Target计划为`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C240_eagle_tp4_numeric_target01/plan.disabled.json`。此句为C237时期历史安排，C241/C239现均已完成；C240/C243失败原件保留。该C245待启动说明属于历史；它后来实际执行失败，当前状态以顶部及本节终态为准，不再恢复旧计划。

**2026-10-29T14:59:41.131336+00:00 C245实际终态追加（取代上述历史待启动步骤）**：producer74/outer2、512.559秒、无timeout，全部自有进程/租约释放。4rank×前6consumer独立canonical数值/Full写严格通过；sample006 boundary-four:first(generation105/epoch35、active/padded4/4、Q16)的第二请求5-b7c2900c有效query4–7 attention O不同，rank0/1/2/3 maxabs分别0.0234375/0.1484375/0.1318359375/0.3828125，超零容差732/894/247/3032元素，均finite。最终hidden7535/32768不同、max0.5（如−34与−33.5）；七输入/Q、KV前后/Full写、canonical到refpre及merged到真实缓存恢复精确。原数值合同atol=rtol=0不变。不是padding/自然轨迹豁免或已证明平台缺陷。

实际peer均在sample-done报告submission_pending=False；parent保守unknown_native_submission=True并隔离退出74、无posterror设备操作，两者原记录都保留，不将保守parent标记当作该peer仍在执行的证明。未完成后两AR及第三组Targetpost，不记完整9/Target通过。独立CPU原件`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/orchestration/C245_eagle_tp4_numeric_target01/offline-prepared/partial_numeric_review.json`，200959B/SHA099fd018d57e4ec6b64cb66e1e51f167f80982f9a781b794880d7b8924c5a113。

下一项C250仅Tool83显式TP4 Q[16,4,256]/GQA4:1profile；准备同原KV[18040,128,256]、offset12127498240/12718632960元素、owner26619535360B、mask/页表/长度/ND格式，四原生调用各3次。旧TP2/Full8/offset-control不变；18项实际DEV CPU检查通过。准确API和官方合法模型路径归属UNKNOWN。该唯一原生判别不加载模型、不重跑TP2/offset，不启动LIFE/HTTP/性能越过有效数值FAIL。

**C250原生判别已完成（UTC15:09:11Z）**：四路径各3次，native18.071558秒、outer24.563636秒，native/checker/outer0，无timeout，自有PID/Phy15租约全释放。各phase内相对首份的差异元素/最大值：defaults重复1为57/0.015625、重复2为1717/0.06640625；explicit重复1为562/0.03125、重复2为241/0.015625；out重复1为1086/0.02734375、重复2为2720/0.06640625；GraphUPDATE重复1/2均163/0.015625。全部仅第二请求有效query4–7、全12输出无NaN/Inf；最大例token7/head0/d4为−0.279296875与−0.345703125。输入前后逐bit及canonical页覆盖经独立NumPy复核，48项摘要与原件一致。部分native等保存eager，无一等保存Graph，不是正确性oracle或根因证明。实际设备执行短于40秒采样，管理进程关联列表为空；不写成未执行NPU，也不虚构在采样中见到PID。

原件`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C250_R8_Eagle_saved_TP4_GQA4_first_rank0_01_node140`；独立review86149B/SHA`aadf78b4fd6bd4eab78fa3da356ee25e94dfa983961a73f318183604d2cf17ce`，含原始schema、版本、完整run/check命令。准确API/storage-offset约束与官方合法模型路径归属仍UNKNOWN；CANN精确build未由该PID导出，引用既有固定环境记录并注明，不猜底层aclnn入口。沿用户既有选择2保留维护者待确认，不重复询问/同探针，不归入Q017。

**C251必要Source适配**：`dddab4dcecc9e43c413376fbbcb0a991563c1baa`，production`2c8744d34ed764b2c5b81acf6b5542f0e6dfdad8`；Eagle具名TP4 Source inventory允许已验证独立dense几何的Async/SP/FlashComm来源，返回实际拓扑并校验prefix canonical owner；matching E_ON同步。未改W1024/K3/Q、capture/update参数、现有bank/event；DSA-CP、错误rank/拓扑及默认Gate拒绝不放开。实际DEV15定向检查通过，非临时Source替代模块，NPU未初始化/FD不增；报告在required-features-prepared/actual-dev-check01，SHA27fee792a3fe6008dc50042f2421cc53697f8921b2f342c3d401ffa3e2ab352b。尚未新特性设备验证，不豁免C245。
<!-- R8_EAGLE_TP4_ACTUAL_END -->

<!-- R8_DFLASH_REQUIRED_CONTEXT_BEGIN -->
## GLM DFlash具名特性上下文：C244服务/C246数值/C248 eager功能已分别限定通过

2026-10-29核对现有最终矩阵items[7–9]：DFlash Async×Graph、prefix真实命中、chunked/mixed仍属既有适用项；C231/C241为Async/prefix OFF，不由DSpark结果横向关闭。固定84030的EagleModelTypes实际嵌入DFlash Literal，mp/V2支持Async；Ascend TP16/DP1 replicated Graph既有allow_required_service_features接线，source capability恢复真实Async/SP/CP/FlashComm身份，prefix有效驻留/phase-aware读取已有。尚未发现必须改生产或新增完成边的具体错误。

正在现有Tool81准备默认关闭的具名功能profile，复用Tool33并发client_groups、既有C148四phase/实际prefix-hit请求与CPU phase/feature collector；保留DFlash K15/Q16/capture16,32,64及独立原数值oracle，不套DSpark Q8/48桶。先被动合同/必要Host检查，再实际TP16服务；不自动重跑14数值或72性能、不扩大到每个DFlash模型全组合。新上下文正常reader须核对实际bank、epoch/request与Graph尾notify/current FIFO；Target较早AsyncOutput/copy_event仍不充当最后Draft reader。工具准备不计设备PASS。

<!-- R8_DFLASH_REQUIRED_CONTEXT_END -->

<!-- R8_GLM_METRICS_CONTEXT_BEGIN -->
## 本轮GLM匹配测量：计数与干扰边界

更新2026-10-29T11:44:22.922760+08:00。固定C231 + vLLM84030中，detailed只增加CPU直方图/逐step列表及终态响应序列化；调度原有sampled IDs/counts D2H及output event并非统计新增。三臂统一开启CPU逐请求接受统计与Host dispatch审计，保留CPU/IPC/SSE开销；没有none开销控制，不称零观测成本。proposed为有效已调度proposal数，accepted为每次验证返回数量减bonus、stop裁剪前统计；排除padding/bonus、不求和TP ranks；逐位置分母各自使用proposed_i。既有output copy event早于Draft proposal，不是最后reader完成依据。实际Source文件/hash/调用点见`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C231_request_metrics_source_scope01.json`。

b1 G_ON完成1097.959秒、16rank关联、producer/checker0，短/16K组中位8.70632509/22.05486675秒，接受1182/5445与1098/6525。Phy8外部context宿主1855536/容器1767798与正式03:36:22.707–03:37:56.007Z窗口重叠，本任务rank8为4037384/1110605，身份不同；确认context重叠，实际计算抢占及减速幅度未知。整实例保留CONTENDED，不能挑短组作为干净对照；完整预声明六实例已完成前5，当前第6 b2 G_OFF；其余未结束前不称正式平衡PASS。
<!-- R8_GLM_METRICS_CONTEXT_END -->

<!-- R8_PRODUCT_ENTRY_BEGIN -->
## 真实受控产品入口：已实现的职责与观测边界
C231/C238的NPUWorker→MRV2 factory→DSpark/DFlash `set_attn`→`init_cudagraph_manager`生产链自动安装Window provider。Tool81/59/46的已核对继承链没有构造、加载、编译或capture override，不是功能安装器；仅在现有方法上做Host观测、返回原值。observer关闭不会关闭provider或所有权保护。仍需默认关闭experimental/review准入，public Gate未开放；不将此状态记为入口“尚未实现”，也不再为证明同一已存在职责重启无扩展整模。
C151三臂各自HTTP服务真实限定PASS，正式各6请求/另6预热；每rank实际Host阶段记录OFF527/ON504/eager592次，包含mixed、continuing/terminal prefill、decode，不能当作设备执行次数。旧联合token差异FAIL另外保留，不用它作服务PASS链接。FlashComm有有效配置和Source适用/Graph身份，尚非独立kernel时间线裁决。观测有真实CPU成本，正常计时未混入重型数值/逐代同步，但不宣称零观测开销。
具名行号、13入口文件/配置差异、扩展完整MRO及真实三臂原件：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/product_entry_current_scope01.json`。本次确认既有服务贡献的来源和范围，不将剩余17分自动补满；最终组合、质量/性能标准和发布决定仍各自单列。
<!-- R8_PRODUCT_ENTRY_END -->

<!-- R8_GLM_NORMAL_READER_BEGIN -->
## 新加载GLM DFlash正常Graph的限定工程结论
C231实际TP16/DP1、sync/prefixOFF、active1/padded1、五Dense Draft层，单parallel query consumer/ordinal0、真实业务bucket[1,16]。C208→C231六份关键生产文件相同，七个实际加载native库hash一致；Source/API的主流等待、ExternalEvent更新、Graph尾notify合流/FIFO及持久bank所有权结合独立数值/Full写/Target和真实绑定，可按用户已接受的证据方式关闭此范围的正常reader适用性等待项，未发现具名缺边。每rank1080代绑定/Host Draft提交是Host记录，不当成逐次设备完成证明。
直接operand/physical-read仍未观测；不是Async/prefixON、多有效行或其它consumer总PASS。C159/C164是旧加载数值/Target；LIFE160/ABORT/UNWIND原件属于C45 Qwen TP1，不能记为本次GLM故障设备PASS。新加载多有效行只补原mixed(7)、active3/padded4(10)、active4(11)，保留原索引和独立canonical检查，其他未变几何按范围复用。
证据`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/GLM_DFlash_C231_normal_reader_scope01.json`。本次C231独立G_ON服务记录12正式/4预热、各rank1080次Host Draft/1064次Host Target调用（包含预热，不跨TP累计），短/16K组中位8.72270/21.93122秒；正式新平衡组另记，旧pilot不混入。
<!-- R8_GLM_NORMAL_READER_END -->

<!-- R8_FULL8_NATIVE_CURRENT_BEGIN -->
## R8 Full8新原生调用证据与边界
C232固定Source `82c0b1026b17c7d91eca582db70409a302df0718`，Phy14/PCI0000:81:00.0，native PID3682750/start_ticks82161190，2026-10-29T01:57:52Z启动；实际26.139秒/exit0，外部checker10.050秒/exit0，联合分类`FIXED_INPUT_REPEAT_DIVERGENCE`。该exit0表示采集/检查完整，不是数值PASS；无模型加载。输入Q[64,8,128]、KV[10824,128,128]BF16/ND、GQA8:1、block128、TND、sparse0/maskNone，Q累计长度8..64；KV长度[32785,2067,1553,265,521,779,1161,1033]，scale128**-0.5、pre/nextINTMAX。原K/V offsets7753101312/7930441728元素，owner16,215,564,288bytes。输入完成前后回读精确，全部输出finite；只第2/第7请求不同。
functional重复1/2对各自首次的bit不同数9276/7804，max5.85791015625，在query49/head7/dim19（第7请求）两次值−0.10791015625与5.75；out不同9088/10530，max5.586914/5.740234；UPDATE不同8911/11368，max5.8046875。原零容差仍保留。Source已保存每次执行完成后的独立CPU快照；未知提交未发生（pending=false），原模型C228/C231 FAIL不改。实际加载PTA2.10.0.post4、CANN9.1动态库路径/hash及PID映射已保存；短case未捕获管理器进程行，SMI逐次PID观察标NOT_CAPTURED，不因退出后无进程否定已保存NPU计算，也不补造管理关联。
原件`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/raw/C232_R8_Full8_active8_saved_first_FIA_native_01_node140`；关键数值与hash `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C232_Full8_saved_native01/summary.json`。结论只到“给定输入的原生调用重复差异”，不证明官方合法模型路径或平台归属，不与SWA/Eagle自动合并。
C238 `abd1e1b6ea30a9fdbb29c3cfb092c84eacccfaac` / tree`fd6eb22006e7450bd6be0a6a253ab72c0719beb9` 仅工具，生产tree仍7099f9d5…；为尚未测过的Full8 D128组合提供一次原offset/实测零offset交错functional对照，各3次，固定同逻辑KV/Q/table/长度/mask。独立schema/原输入hash，与旧Eagle D256 C226分开；35相关Host及原C232只读重算/4损坏拒绝通过，实际对照已完成：16.130秒/exit0、checker8.043秒/0；原布局repeat1/2不同8183/6259元素，零布局11714/6361，二者最大均5.85791015625（query49/head7/dim19，−0.10791015625与5.75），均finite且只第2/7请求。CPU直接解析BF16输出独立复算一致；实测零offset为0、独立KV owner各354680832bytes，逻辑内容前后精确。大offset不是该异常的必要条件，停止此方向加测，准确API/官方合法路径归属待确认，原模型FAIL未豁免。原件与小摘要见`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261029T012724Z_R8_node103_8f889187/node140_return_20261029T0150Z/reanalysis/C238_Full8_paired_storage01/summary.json`。计划`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/state/R8_C238_FULL8_OFFSETS_PLAN_01.json`已终态disabled且租约/进程退出；不把复制KV加入生产。GLM TP16匹配组当前优先。
<!-- R8_FULL8_NATIVE_CURRENT_END -->

<!-- R7_FULL8_PRODUCT_CURRENT_BEGIN -->
## Full8产品宽窗口当前证据（R7）

|结果|真实身份和范围|证据|
|---|---|---|
|TP4DP2EP8 OFF/ON/eager服务能力|C221 OFF；C222 ON/eager，各8真实worker，257/33025输入、每DP路由、Target Graph，ON真正裁窗；单臂有限正式请求，不是全部业务负载/内部数值|`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C222_R7_Full8_TP4_DP2_W32768_G_ON_01_node140/joint.json`、同目录E_ON对应case|
|精确请求联合/正常reader适用性|C222两臂8对token一致（4正式/4预热）；DP0每TP298代、DP1每TP226代，bucket持久地址与本代epoch关联、dummy隔离；三个完成边源码文件及7个native hash与既有审查相同，7类损坏原件拒绝。未发现具体缺失完成边，Source/API证据方式沿用已批准限定范围；直接operand/physical-read未观测|`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C222_wide_service_pair_reader01.json`，同名py可只读重算|
|W32768局部数值/Full写|C224四rank各1条33025输入，全部8层/16KV部分严格独立canonical实际eager/Graph；串行TP4DP1，不推断DP2正常时间、Target/ABA|`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C224_R7_Full8_W32768_long33025_numeric_ON_01_node140/joint.json`|
|当前有限匹配测量|C225只有工具变化，生产tree仍1e13f390…；W32768、TP4DP2EP8、257/33025固定输入各2请求/c2/out256，Target Graph，sync/prefixOFF。2实例块×3正式重复，初始化/预热单列；使用框架SSE/原始每请求sampler统计，不冒充AISBench或历史n64/c16/out1500主负载|`state/R7_C225_FULL8_PRODUCT_DP2_PLAN_01.json`和活动JSON；原始产物不覆盖C217|

C217 W1024/TP4DP1负收益继续原样保留；新Window/DP2负载不能与旧负载算优化幅度。这是当时仅用后8的历史资源条件；当前按用户后续答复，完整16实际释放后自动使用，否则继续合适后卡。GLM TP16不降TP替代。

**C225完整有限测量结果**：同候选C225、TP4DP2EP8/W32768，257/33025输入、c2、一请求/DP、out256；每臂2实例×3正式重复，72正式请求/24预热。G_OFF/G_ON/E_ON中位秒：短3.056434/3.796583/5.088248；长3.858053/4.534391/5.097344。Window ON耗时+24.22%/+17.53%，TPS−19.49%/−14.92%；同窗Graph耗时节省25.39%/11.04%，TPS+34.03%/+12.41%。长请求接受率OFF81.45%/ON84.85%/eager83.25%，仍不足抵消本负载窗口开销；不是业务质量判定。48自然对中40相同8不同（同Window20/24相同），差异保留；R7-FULL8-NATURAL-01已获用户明确采用可比前态合同，原DP2全局前态未知，不解释全部差异。所有采样未见后8无法关联context，但不称整机独占或排除采样间隙的干扰。使用框架SSE/每请求计数，非AISBench；不代替c16/out1500主负载和正式性能标准。逐次表、配置、资源快照和公式：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C225_Full8_wide_matched_performance/summary.json`、同目录samples.csv。

**Full8轨迹合同已明确（2026-10-28T22:46:26.726821+08:00）**：仅关闭C227 TP4/DP1四rank各3consumer、原严格容差的数值/Full写检查。C225原20/24同窗口输出一致、首差第3输出、局部active/padded1/1且原DP2完整KV/Target前态未保存继续保留，20/24不是准确率。固定输入token IDs、采样/seed已有证据一致；同实例变化发生在b1 E_ON长DP0、b2 E_ON长DP0、b2 G_ON短DP1和长DP0；有效首差及逐对计数经精确请求ID联合核验。其余未保存前态UNKNOWN。只读表见 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C225_Full8_wide_matched_performance/first_natural_difference.json`。不重跑三臂或C227，不批准质量/性能/发布。

**新的可比数值反例仍阻塞**：C228混合8有效请求、Q64，4rank隐藏32616元素不同、最大12.8125（6.5625对19.375），全部finite；仅第2/第7请求且这两行未裁窗，首层KV/全部前态恢复精确、后续KV差异限声明写slot。未保存首层Q/attention，不能定责。C230一次采证在请求前被旧profile断言拒绝，producer74/runner2、无数值样本；本任务全退出。正在修私有安装检查，不改生产算子/容差。

**C231首层区分性采证已完成**：producer505.35秒/74（真实数值FAIL），外部capture checker0，runner0只表示采证完整、`scoped_accepted=false`。TP4四rankQ[64,8,128]全部精确；首层attention不同元素5641/5684/5481/9679，均finite，差异仅实际行1/6（零起算，rank2仅行1）。rank0最大5.740234375，位置[50,3,19]，Graph5.5625对eager−0.177734375。所有rank隐藏结果传播差异，owned=legacy、首层K/V后态/16恢复精确、无声明slot外写。元数据独立canonical校验原样成立。采集头是capture时地址/形状，**不是执行时operand**；当前Host有效长度32785/2067/1553/265/521/779/1161/1033，非因果sparse0/maskNone/GQA8:1/D128。尚不能判平台或自然噪声。`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C231_active8_first_attention01/result.json`；完整样本及tensor在对应raw，CPU只读分析脚本同目录。
<!-- R7_FULL8_PRODUCT_CURRENT_END -->

<!-- R7_EAGLE_C216_MAINTAINER_BEGIN -->
## 可直接转交师傅／FIA／PTA维护者：Eagle C216原生调用异常

更新时间：2026-10-28T20:21:54.385905+08:00。用户已选择“暂时没有资料，保留待确认项”；**未获维护者确认、未向外发送、不定责、不套Q017，不豁免Eagle原FAIL**。

### 简短摘要

node-25-140/A3既有910_9382环境，CANN9.1.0（OPP build `20260730_231653901`）、driver26.0.rc1、Python3.11.10、torch2.10.0+cpu、PTA2.10.0.post4。固定且回读全部有效输入、不加载模型、不写KV，functional默认/显式、out、Graph UPDATE各自三次仍有有效第二请求的重复差异；最大0.3515625，在TND索引[4,4,45]为0.44921875对0.80078125，所有输出finite。这里只证明原生调用层可复现；准确API组合、storage offset约束、官方合法模型路径归属仍待确认，不能解释全部C203/C213失败。实际底层aclnn选择入口 **UNKNOWN**，Python/dispatcher名称和库hash不能替代该结论。

|调用路径|本路径重复与其repeat0比较：最大差／对应超原精确判据元素数|位置／实际值|不同路径与functional默认repeat0比较（取本路径repeat0）|
|---|---|---|---|
|functional默认|0.3515625／4298（repeat1）|[4,4,45]：0.44921875 vs0.80078125|自身基准|
|functional显式pre/next|0.3515625／2532（repeat1）|[4,4,45]：0.44921875 vs0.80078125|4384元素，max0.2763671875|
|out|0.2744140625／2204（repeat1）|[6,6,113]：−0.1689453125 vs−0.443359375|2525元素，max0.203125|
|Graph UPDATE|0.2666015625／3013（repeat1）|[6,6,113]：−0.443359375 vs−0.1767578125|4415元素，max0.2666015625|

全部重复差异限T=4..7（第二真实请求的4个query），具体head见原JSON；默认functional涉及head0..7。每个输出共32768 BF16有效元素，无padding输出纳入。原Eagle受控checker冻结atol=rtol=0（repair15 checker），上表超判据数亦为不相等元素数；这不是新增通用算子逐bit确定性要求。数值范围约[−3.828125,3.875]，NaN/Inf均0。不同路径共享底层与工具，不能算四份独立平台缺陷证明。C213参考来自canonical前态和真实eager backend，但仍共享FIA/PTA，非独立native算术oracle。

### 准确调用与存储描述

Python：`torch_npu.npu_fused_infer_attention_score`、其`.out`、`_npu_fused_infer_attention_score_get_max_workspace`；Graph使用`graph_task_group_begin/end`、`graph_task_update_begin/end`和ExternalEvent。Q=[16,8,256] BF16、stride[2048,256,1]；K/V各[11168,128,256] BF16、stride[32768,256,1]、ND format2，逻辑连续；table=[4,32] int32/stride[32,1]，mask=[2048,2048] int8/stride[2048,1]，mask为0/1上三角。TND cumulative query=[4,8,12,16]，每请求Q=4，KV=[1029,517,133,131]，GQA8:1，D256，B128，scale0.0625，sparse_mode3，pre_tokens=next_tokens=2147483647；softmax_lse_flag=False，其余可选量化/rope/padding参数未设置。capture初始KV长度[1151]*4、零capture table仅用于工作区/捕获；真实UPDATE和functional/out均传上述当前table与长度。

K offset=7507755008元素=15015510016字节；V offset=7873708032元素=15747416064字节。共同owner16479322112字节，每个逻辑KV张量731906048字节，范围不重叠。实际K/V data_ptr分别20637300981760/20638032887808；按记录地址计算均32/64/256/512/4096字节对齐，offset字节亦对齐；这只报告数值，不替平台确认要求。原大owner全部zero初始化，完整需读页已填充，页表各行有效页唯一且位于11168范围。

每次调用后显式诊断同步，再CPU独立clone；out/Graph历史结果不保留复用buffer引用。workspace先按capture参数求取、同步并保持owner，actual table/长度列表/mask/Event/Graph在所有重复中存活。同步与快照仅隔离诊断，不进入生产热路径。

实际进程加载库（路径、全hash见原worker-provenance）：
- `/usr/local/Ascend/cann-9.1.0/aarch64-linux/lib64/libacl_rt.so`：SHA256 `5a6518505ef66688f02b4bde97517ba217212f29304d59b3a6ef0db14ded6c83`。
- `/usr/local/Ascend/cann-9.1.0/aarch64-linux/lib64/libacl_rt_impl.so`：SHA256 `4595d4cf50f064cc9d6a97688eecf5e95ef92a4291911e26dd301091997c37ee`。
- `/usr/local/Ascend/cann-9.1.0/aarch64-linux/lib64/libascendcl.so`：SHA256 `123d67c313f743e5d6f2e856f40c24d5edac376975cf0a7a1019e079b4171480`。
- `/usr/local/python3.11.10/lib/python3.11/site-packages/torch_npu/lib/libtorch_npu.so`：SHA256 `3b43f9530ba124efd1f9cc8ea9f93088171d4493bfd8da9152b9ca547399a68a`。

### 复现入口与待回答问题

固定工具：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/node140/C216_saved_eagle_fia/vllm-ascend/tools/p7x_graph_repair83_saved_eagle_fia.py`，producer C216 `e0d17164efc32f3bc71cb74c53ea1615e88967ba`；Graph pin84030bbe，不是PR pin。

历史实际命令（旧admission已过120秒启动有效期、输出目录已存在，**不可原样覆盖重跑**）：

```bash
/usr/local/python3.11.10/bin/python /mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/node140/C216_saved_eagle_fia/vllm-ascend/tools/p7x_graph_repair83_saved_eagle_fia.py run --input /mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/inputs/C216_Eagle_saved_rank0_sample6 --admission /mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C216_R7_Eagle_saved_FIA_causal_first_rank0_01_node140/admission.json --expected-sha e0d17164efc32f3bc71cb74c53ea1615e88967ba --output /mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C216_R7_Eagle_saved_FIA_causal_first_rank0_01_node140/native
```

最小重放只需同工具`run --input /mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/inputs/C216_Eagle_saved_rank0_sample6 --admission <本任务新生成的单卡receipt> --expected-sha e0d17164efc32f3bc71cb74c53ea1615e88967ba --output <新attempt/native>`；沿用对应固定源码/pin/native环境与新原子租约，不重新加载完整模型。当前不执行同一探针。

输入：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/inputs/C216_Eagle_saved_rank0_sample6/input.json`、`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/inputs/C216_Eagle_saved_rank0_sample6/operands.safetensors`（12,912,240字节，SHA256 `fd48f22ab9bc50e7681f80305a373b384200ccd0d43b184871aa8d119cdd316b`）。原输出/独立输入回读/原checker/调用schema：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C216_R7_Eagle_saved_FIA_causal_first_rank0_01_node140/native/`和`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C216_R7_Eagle_saved_FIA_causal_first_rank0_01_node140/joint.json`；完整参数及新增逐路径数值、storage字节/对齐：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C216_R7_Eagle_saved_FIA_causal_first_rank0_01_node140/api_contract_review.json`。

请确认：①实际A3/CANN9.1入口是否支持上述整套TND/paged/GQA/D256/sparse3/mask参数；②当前非零大offset、完整owner、实际地址和连续性是否有额外对齐/范围/描述约束；③mask及TND长度分段是否符合此版本；④若合法，如何提交有效输出重复差异。其他版本资料仅线索，未证明9.1合法或非法。

**唯一新增布局对照已完成（C226）**：producer/checker `029cd53c89e66ca138c794e40365451c15f79c47`，Phy14，13:00:16–13:00:55 UTC，总39.27秒，原生producer17.54秒/0退出、checker0，未加载模型。相同逻辑内容/shape/dtype/stride/table/长度/mask，原大offset与实测offset=0交错各3次functional显式调用；全逻辑K/V前后比较均True，独立CPU输入回读精确。

原offset重复1 vs0：579元素不等/max0.3515625；重复2：5060/max0.2666015625。零offset重复1 vs0：3100/max0.408203125；重复2：1106/max0.0625，全部输出finite。零offset K/V实际shape均[11168,128,256]、ND2/stride[32768,256,1]，各独立storage731906048字节，offset元素/字节均0；实际base/data_ptr为20639465340928、20640539082752。原offset共享owner16479322112字节及原offset数值完整保留。

结论：**大非零offset不是复现差异的必要条件；停止该方向加测**。这不证明完整布局/API合法性，不定责平台，也不关闭Eagle原输出FAIL；不采用生产全KV复制方案。SWA C184组合分开。原件：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C226_R7_Eagle_original_vs_zero_offset_native_01_node140/native/result.json`、`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C226_R7_Eagle_original_vs_zero_offset_native_01_node140/native/outputs.safetensors`、`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C226_R7_Eagle_original_vs_zero_offset_native_01_node140/native/input_readback.safetensors`、`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C226_R7_Eagle_original_vs_zero_offset_native_01_node140/joint.json`。

**复现命令时效说明**：本节上方保留的是C216历史实际argv；其中admission已过时、output已有原件，不能原样重复执行或覆盖。维护者需绑定其本机有效准入及全新空输出目录；模型与旧原件无需重采/复制。等价入口为：

```bash
/usr/local/python3.11.10/bin/python /mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/node140/C216_saved_eagle_fia/vllm-ascend/tools/p7x_graph_repair83_saved_eagle_fia.py run --input /mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/inputs/C216_Eagle_saved_rank0_sample6 --admission "$FRESH_ADMISSION_JSON" --expected-sha e0d17164efc32f3bc71cb74c53ea1615e88967ba --output "$NEW_EMPTY_OUTPUT_DIR"
```

`FRESH_ADMISSION_JSON`必须是该固定工具现有验证器认可的实际本机准入，`NEW_EMPTY_OUTPUT_DIR`不得指向旧原件；沿用已记录Python/native环境。此处提供入口，不表示已向维护者发送，也不自动派发复跑。C226补充控制已完成且两布局仍异常，停止offset方向重复加测。运行stderr还出现32-padding allocator warning，原文在C226日志；尚不能关联根因，不据此改底层栈。


**后续指定TP4入口准备（2026-10-28T23:58:40.873844+08:00）**：C233 `e1407a8c9a694c29b926eabf04519a7245433d35` 仅在默认关闭受控Graph review下，为实际一层Dense Eagle K3/h2048/D256/global Q16/KV2增加TP4资格；Window仍1024、capture `[1,2,4,8,16]`、firstQ4/ARQ1不变。Tool46贯通4rank准入、真实模型kwargs、已加载QKV属性/源码hash与两KV头各两rank复制，检查全部peer的业务读视图；不把逻辑长度除以TP。135项定向Host通过，未设备运行；后续C234已贯通Tool78真实TP4四rank×9consumer数值producer/checker，115项受影响Host检查和真实C190旧原件复算通过；TP4实际设备数值、Target/reader及实际PR W1035配置尚需完成。C203/C213/C216/C226原FAIL与准确API归属不变，没有Gate/发布批准。固定源码 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/node140/C233_eagle_tp4_rank_entry/vllm-ascend`；binding `state/R7_C233_NODE140_BINDING.json`。此生产diff仅Eagle方法准入条件，当前GLM/Full8固定producer不受热改，其他方法原未变证据可按影响说明引用。
**C234数值程序准备（非设备验证）**：`9e90426405a0314fa40cfc67103186c451a4d5ba`，production tree与C233相同；4rank×9consumer的实际tp、RPC payload、checkpoint、独立存储checker及全peer故障传播已接通，canonical参考和原容差不变；真实C190 OFF02原件由C234只读checker复算通过，producer仍C190，不改写旧FAIL。固定 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/node140/C234_eagle_tp4_numeric_chain/vllm-ascend`，证据 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/host/C234_real_C190_anchor_recheck01/result.json`、`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/host/C234_eagle_tp4_numeric_contract01`。没有runtime或TP4模型结果，阶段顺序不变。

<!-- R7_EAGLE_C216_MAINTAINER_END -->



<!-- R7_DSPARK_RECONCILIATION_BEGIN -->
## R7 DSpark验收来源与已有证据收敛（2026-10-28T11:07:15.607233+08:00）

|问题|当前具名结论|下一步|
|---|---|---|
|同前态/同shape/同Window|C147完整CP、Full写、ABA/Target224及C158同M三样本原严格结果直接复用；本轮未改DSpark生产路径|不重跑14场景|
|不同M/padding|C158原FAIL保留：hiddenmax0.09375、首V1ULP；C160只复现首层组件。跨M逐位零差来自私有诊断，未找到团队明确硬门槛原文|分开记录，不修通用BF16、不强制生产padding，不宣布全部误差已解释|
|自然token|C151 E_ON/G_ON5/12相同、7/12不同，首个同Window差异是warmup257第38token；OFF/ON8/12相同、4/12不同；原版/旧OFF冷热亦有差异。输入/输出prefix相同不足以证明内部KV/shape/调度前态相同|原FAIL保留，已复核首consumer：G_ON active/padded2/2、E_ON1/1，两臂Window starts全0；内部前态未确立。用户已采用可比数值合同；36原SSE/唯一请求/有效ID/采样/框架验证记录有界复核通过，未见这些记录内具体新错误，原FAIL和未完全解释的质量限制保留，不重跑全服务dump|
|正常Graph reader/backing|**本项已限定收口**：用户接受既有证据方式；实际C151正常绑定、C147独立数值/Full写/Target及C148异常，连同C147/C158→C204源连续性已核对；本GLM DSpark TP16/DP1范围未发现具名缺失完成边|不再等待重复批准；逐次operand/physical-read仍UNPROVEN/NOT_OBSERVED，其他consumer不自动继承。[完整前提/hash](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/DSpark_normal_Graph_scoped_engineering_closure01.json)|

Frozen Design I16/I19是正确性要求；旧Master Analysis G1–G5是历史调查/取证方案，不能混成已获团队批准的唯一方法。未直接观察到内部细节也不自动判生产失败。精确来源/hash和剩余问题：[当前只读分析](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/DSpark_requirement_and_evidence_reconciliation01.json)。正常Graph证据方式已按原答采用；C151自然轨迹、Eagle与SWA失败不豁免。当前性能仍是诊断；public Gate冻结。

**自然轨迹合同已明确（2026-10-28T12:13:16.658276+08:00）**：本轮不将不同真实批次/调度的最终token恒等作为默认硬门槛；同模型/精度/输入/KV前态/Window及有效行、positions、形状可比条件下原数值判据不变。active=真实参与请求数，padded=执行槽数；1/1与2/2改变实际batch，不只是padding。C151短请求未裁窗，不能用远处上下文被裁解释；C160仅首层。对36条原SSE重新检查ID、采样、有效token/usage、per-step accepted/proposed/hist与公式均一致；该检查不替代逐步Target logits/语义业务质量评估。已有C147/C158可比数值及Full写/Target按范围复用，数值目标20点收口；旧FAIL不改写，Gate/发布/其他方法失败不豁免。依据：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C151_trajectory_acceptance_boundary_decision01.json，/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C151_bounded_request_and_verification_review01.json。


**DFlash Full8正常reader具名原件核对**：沿用用户接受的工程证据方式，C172原8worker实际TP4/DP2，DP0各406代、DP1各413代，dummy每rank25/18；generation/epoch/capture-bank地址及dummy不绑定live Window记录通过只读核查，4类对真实原件的损坏拒绝。manager/metadata/Event/FIA完成边文件至C206字节不变，实际7库hash匹配；Qwen量化optional为空，C205QuaRot路径早返，nativeSWA计划None。此处不称Host次数为设备执行数，不关闭Target hybrid Full/GDN隔离或SWA/新GLM加载数值，也未增加分数。原件：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/DFlash_Full8_normal_reader_scope_review01.json。

<!-- R7_DSPARK_RECONCILIATION_END -->

<!-- R7_DFLASH_LOADING_BEGIN -->
## R7 DFlash加载与受影响补证

必要生产适配C205 `062ccf3d8ff01c2fa477b8e729760bf68a3ed86d`复用PR已合入0be的QuaRot方向和辅助层合同，Graph固定vLLM pin不变。C207/C208/C209仅工具改变，生产子树均`7fd4156a7b6c05c8d52826efbed66b5e838ca6a5`。

- C206原FAIL：16rank初始化与capture完成后，诊断器错误要求旧`rot.safetensors`，实际固定量化配置为`optional/quarot.safetensors`。请求0、producer74原件保留，不判生产失败。C207工具局部修复。
- C207 OFF：全16rank真实加载/Graph请求锚点外部通过，模型917.193s、checker12.046s，4×32输出；accepted45/proposed1245（3.61%）、83验证请求步。合成重复token负载不能充当业务质量/加载性能改善证明。
- C208 ON：新加载底座16rank×3独立同前态eager/Graph、Full写、ABA外部PASS；模型1010.451s、CPUchecker134.240s。
- C208 OFF：同源16rank×3外部PASS；模型877.904s、CPUchecker138.247s、监督器实际退出0。新加载Target48已在CPU独立联合通过（1145.34秒，rc0）；旧完整14/Target224仍为C159/C164的原加载身份。
- C209 Full8：只补Target10Full层K/V、30GDN层conv/SSM及真实输入非干扰，实际TP4；不重新执行已通过的C195/C196 eager数值。3个提案/rank、分配页由canonical表/行映射/原CPU计数独立核对；Source官方已消费的共享slot scratch不作为Target KV oracle。显式诊断drain/Host就绪，因此不冒充正常时序或独立Target前向相等。正常Source/API与C172 TP4DP2原件按未改属性复用；SWA另保留阻塞。

原件：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C207_R7_GLM_DFlash_QuaRot_OFF_anchor_01_node140/result.json`、`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C208_R7_GLM_DFlash_loaded_prefix3_ON_01_node140/result.json`、`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/raw/C208_R7_GLM_DFlash_loaded_prefix3_OFF_01_node140/result.json`、`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C208_loaded_Target_prefix3_join01`。C209 OFF/ON联合已完成（39.628秒，rc0），结论为24次实际proposal/1920组件隔离；不证明Target独立前向相等。C209历史控制记录：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/state/R7_C209_FULL8_TARGET_ACTIVE_CONTROLLER.json`。模型/机器/启动重复均按原身份列，不跨机拼性能。

**2026-10-28T14:44:59.706713+08:00 当前执行增量**：C208 Target48已完成，C209双臂24proposal/1920 mapped Target组件联合已完成；相应Target/reader限定缺项从待办移走。当前C212 `105c52803b5db35196cfb18c992d7f9bc6c053d8` 是新加载GLM DFlash真实HTTP G_OFF首臂，K15/Q16、TP16、prefix关闭/同步、Target Graph不变；请求直接复用PR固定tokenIDs70/76/16006/16012，输出256是本组新预声明，不与PR64输出性能直接比。计划2平衡实例块×每实例3正式重复，不继承DSpark全特性或其他pin的PASS。原始请求/次序：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/state/R7_C212_DFLASH_HTTP_PLAN_01.json。

Eagle新增工具故障分别保留：C210配置登记前拒绝（无权重加载）；C211真实模型首样本后Host导出读不存在的dense max_seq_len字段，404.541s/rc74，尚无新数值裁决，按未知pending状态隔离，未故障后读设备或复用。C211已登记默认关闭键；C213 `d333817939a041c204d77e6bb21be4099219420c` 纯工具使用真实AscendMetadata.max_query_len及owned Host长度，实际dataclass回归通过。C203有效输出FAIL不被工具问题覆盖；修复后一次采证排在当前DFlash关键工作后。
<!-- R7_DFLASH_LOADING_END -->

**C235匹配eager入口准备（非设备通过）**：`cd72cac7c2e36e61cd2f8adfaaabe8a02e0be748`，tree`c0388fe22a9002ecf3d8b0a46d6dffce3e071423`。原Eagle TP4同窗eager在DSpark/DFlash专用review准入处被拒绝，四rank正例原4FAIL；最小扩展既有默认关闭review，只允许具名Dense TP4/K3/W1024、causal且无Async/prefix/SP/DSA-CP/FlashComm，保留实际rank/canonical Full owner和原eager流程，不改窗口/exact/capture/完成边。修复后69项相关Host通过；真实E_ON服务/数值/正常reader仍NOT_RUN，当前工具46的服务观察接线还需对应eager路径。证据 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/host/C235_eagle_eager_entry_before01`、`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/host/C235_eagle_eager_entry_after01`。生产仅Eagle eager review分支，当前固定C231/C232 DFlash实验不受影响；无额外进度或发布批准。

**C236三臂实际入口/绑定准备（非设备通过）**：`8a0f15d8e80211aad7719121dd9cea2c361ce28a` / tree`eccd1516bfa5e99c6b75a326eccec68d04ef9b78`，production tree`7099f9d5a98c47d9f92e6982b6758971fc6c4b53`与C235相同。Tool46为E_ON建立独立TP4/K3/W1024 profile；只将Draft设eager，Target保持Graph。沿真实`_run_model`记录已有CPU generation/epoch/step，不加同步/D2H/query；四rankchecker要求Draft Graph库存/绑定/重放为空，实际eager first与两AR分别对应真实Window generation，保留Target FULL调度及Source/native/物理进程联合。184相关Host、17定向typed检查通过；C190真实Graph原件只读通过，缺rank/改输入/换worker/producer自报PASS四损坏仍拒绝。冻结真实模型header/Source导入及运行绑定/临时缓存preflight通过。**尚无C236模型/NPU结果**，不证明Eagle原FAIL已修复、不支持W1035、不代替正常reader/Target/性能。证据 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/host/C236_eagle_eager_chain_after01`、`C236_real_C190_and_typed_identity01`、`C236_real_C190_damage01`、`C236_frozen_real_factory01`、`C236_orchestration_import01`。

历史C236准备计划（未运行，已由C237派生计划接续）`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/state/R7_C236_QWEN36_EAGLE_TP4_PLAN_01.json` disabled，先实际TP4 G_OFF官方Draft Graph底座，再具名G_ON，另设E_ON真实对照，不自动串发；每臂预计15–25分钟、硬2700秒。只有DFlash当前必要任务合理结束或明确等待外部条件时使用后卡；完整16可用优先GLM G_ON。沿C232已验证native lineage硬链1223文件/69,262,708bytes，全部hash核对；ABI/pin未变，无旧production Python混入，runtime manifest SHA`14872b183e46e15ba33c60be4d038f043b77907fd763189095c638964125cf67`。

**历史C237实际首轮query工具纠正（Host限定）**：`8f889187b33b719290e40342ca020b46c61244bc` / tree`96639a960d44aba1235c4df6b17b9fab8a5ea3a6`，生产仍C236。真实`autoregressive/speculator.py::_prefill`把当前`num_tokens`、`input_batch.query_start_loc_np`交给独立Draft metadata；terminal prefill并非固定Q4，实际短decode也可能不足4。旧私有Tool46误套固定首轮Q4，Host合法257/3-query反例先失败，现按已有Host `actual_seq_lengths_q`累计ends与首轮CPU输入核对；AR仍要求每有效请求Q1。无设备读取、同步或生产修改。132相关Host、真实C190旧Graph原件重算及4类损坏关联通过；只关闭工具假设错误，不解释C203/C213/C216。当前准备计划`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/state/R7_C237_QWEN36_EAGLE_TP4_PLAN_01.json`仍disabled，沿DFlash之后的TP4 OFF底座→ON/独立E_ON顺序；native1223文件/69,262,708bytes与C236不可变donor逐个同inode/bytes，manifest SHA`6f3b2eee2fadecce802b10275da51c9c0cc450e840d8b4a395959060aa02a775`。证据`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/host/C237_actual_query_layout_after01`、`C237_real_C190_recheck01`、`C237_real_C190_damage01`、`C237_orchestration_import01`，没有新TP4 NPU通过。

**C232未启动脚本的Host纠正**（2026-10-29T01:15:43.910672+08:00）：发现并修复attempt02入口写成不存在的`tools/p7x_graph_repair83_saved_full8_fia.py`，实际固定文件为`tools/p7x_graph_repair83_saved_eagle_fia.py`；保留`--full8-active8`限定，source/producer/checker均仍C232，input manifest不变。该问题尚未触发native或模型；原attempt01在更早设备准入处拒绝，不改旧记录。当前准备script SHA`8c319dbc926705f2db03a49c42526c0c0b9272809f3ce973a6bcd36d0e2f1dd2`；已将PCI日志标签绑定新鲜准入返回值，状态及启动身份以`state/R7_C232_SAVED_FULL8_PLAN_02.json`为准。已对C231/C232/C236实际工具文件、完整依赖hash及C232准备wrapper真实导入核对，无main/无GPU；原件 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/host/C232_attempt02_actual_tool_path_correction01`、`C232_attempt02_actual_wrapper_import01`。不是production修复或设备PASS。

**DSpark旧证据在C236的受影响范围核对**：只审C204之后6个生产差异文件，主要是必要DFlash加载、具名方法准入和私有诊断。9个DSpark核心attention/speculator/Graph carrier/metadata/生命周期文件逐字节一致；C151、C204与C236的全部1223 native/generated相对路径、bytes/hash完全相同，当前C236建overlay时已重核donor内容。共享eager准入对实际DSpark TP16/DP1/W1024走原等价分支；没有从这批delta发现需要重开C147/C151/C185矩阵的依据。完整diff/逐文件理由 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C204_to_C236_DS_existing_scope_impact.json`。这只确认复用适用性，不把旧数据改标C236设备/性能PASS；自然轨迹、业务质量、负收益及正式性能标准仍分别保留，不加进度。

<!-- R7_PR_SHARED_RECONCILIATION_BEGIN -->
## PR冻结共享修复核对（2026-10-28T16:10:32.181764+08:00）

稳定只读来源：PR Ascend **0be870af5e9e559b33c86e71e7c4bb8b485df87d** / tree `e9af2ff3dcde00d3fdc4f4ca076c276e45bc8fcf`，配套vLLM **a98247ab4db686ee03c66d5feb3c761e52a2f8ab**。实际读取固定Git对象，未跟随下午5小时探索；W16384无已验证生产收益，不采用。Graph保持vLLM **84030bbe3d74d99bad477a3d2e37a973ccd8865c**、本机Python/native和冻结public Gate；本段初次核对时开发为C215 `f3ae7334f14748eab964e180c572d73dd45dd02a`（历史时点），当前开发以顶部权威摘要为准；C205对齐函数及调用未变。

**Q023完整链已吸收，无本次新增生产移植**：确认PR前置 `238c7589b640408439204007d1b1c8103f934912` → `185e80c69088397cd3ead2ced45b6bc6a4871a28`（加载后对齐）→ `0be870af…`（non-aux早返保护），不是只取0be末尾6行。Graph C205 `062ccf3d8ff01c2fa477b8e729760bf68a3ed86d`已实现等价加载链：`AscendDFlashSpeculator.load_draft_model`在官方load返回后、capture/KV运行前调用`align_dflash_weights`；实际Target旋转路径为`GLM-5.2-w4a8/optional/quarot.safetensors`，五辅助层[1,20,38,56,75]、fc[6144,30720]。仅加载时fc每个输入块执行W@Q；缺失自有vocab时创建本rank私有Parallel层并按Target loader执行W@Q.T，不原地改共享Target。非QuaRot/non-aux早返；缺失/打包或非浮点fc拒绝；同绑定重复调用早返，换绑定拒绝；失败丢弃该Draft，不在同对象恢复。Graph显式CPU device context适配自己的旧pin helper默认分配规则，PR新helper显式device，与TP16当前布局语义对应；未移植其他PP/新pin接口，也未复制任何PR二进制或改原权重。

|PR固定来源|Graph对应实现|等价/差异|此次是否吸收|理由、验证和保留范围|
|---|---|---|---|---|
|185e→0be `models/qwen3_dflash.py`、DFlash加载后hook、DSpark对齐helper|C205 `models/qwen3_dflash.py::align_dflash_weights` + `dflash/speculator.py::load_draft_model`|当前GLM QuaRot aux/owned-vocab语义等价；旧pin显式CPU计算范围不同|**已包含；本次0项生产修改**|11项加载Host原证据，C207实际16rank加载/4×32锚点；C208新底座两臂前3样本数值/Full写/ABA+48对Target；不是把PR PASS继承|
|0be `draft_window_policy.py`|现有Graph policy/工厂准入与Frozen约定，C213具名影响审阅|OFF/forced-OFF、MTP/内置V4、支持方法和拒绝合同一致；版本接口不逐行等价|保留已验证Graph实现|Q015/Q017/Q005不重开；未改Source政策路径，`C213_bounded_new_production_policy_review01.json`和对应42项原结果复用|
|0be `draft_window_plan/read/runtime.py` + backend读视图|Graph `draft_window.py`、`draft_window_eager.py`及私有Graph metadata/provider|相同窗口/Full写约束；exact来源及Graph生命周期不同|不以PR eager覆盖|Graph本代device exact/CPU拥有拷贝及canonical full表，C147/C208/C195独立参考为依据；不换CPU upper，不把PR接口PASS当本pin证明|
|PR Full写/slot布局及新pin DCP准备接口|Graph原full table、positions、slot_mapping和现有SP/legacy DSA-CP接线|合同共用；a982与840的调用参数/粒度接口不同|没有具名缺口，不盲移新pin兼容|现有C147 CP全写/Target及C138服务修复保留；DFlash方法自己的结果分别归属，不据DSpark自动覆盖|
|PR eager reader事件/请求结束回收|Graph wait-current、ExternalEvent、尾notify合流/FIFO与持久bank所有权|**执行合同不同，不能直接等同**|保留Graph保护|用户已接受限定工程证据；正常Graph与eager、串行诊断各自独立；逐次operand/physical-read仍未直接观测|
|PR午休/下午W16384等配置探索|本轮Graph固定Window与请求配置|配置探索非共享生产修复|暂不采用|不跟随探索HEAD/窗长；最终整体集成pair仍需另行固定，不改PR或Graph pin|

本Graph真实接受表现：C207合成短锚点45/1245=3.61%仅fixture；C212同一新加载底座真实短文本G_OFF/E_ON均为每重复394/1815=21.71%，16K G_OFF361/2250=16.04%、E_ON366/2175=16.83%。计数排除bonus/padding、不跨TP求和；这不是加载前后质量/收益比较，也不是同Window Graph收益。C212 G_ON在启动期失败、没有正式请求；E_ON第三次16K期间有117MiB外来context，整臂保留CONTENDED_OR_UNKNOWN标记。旧C159/C164保留旧加载身份；未因本次同步重新跑模型或增加管理计分。

证据：`runs/20261028T023750Z_R7_node140_06fafe0d/raw/C207_R7_GLM_DFlash_QuaRot_OFF_anchor_01_node140`；`reanalysis/C208_loaded_Target_prefix3_join01/joint.json`；C212两臂`http-artifact-joint.json`及`reanalysis/C212_E_ON_competition_timing01.json`。PR完整说明来源为`dev/report/MRV2_Draft滑窗_PR完整说明与评审报告.md`；源码核对使用上述固定Git对象，不把报告摘要代替实际worker证据。

**固定pair的最小准备（C234，只读静态核对）**：Graph pin84030bbe是PR pin a982的祖先，二者之间1684个上游提交；这不是授权升级或要求整体合并。固定对象/相关函数签名逐项保存在 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/PR0be_GraphC234_minimum_interface_pair01.json`。已确认的具体组合风险：

|接口|Graph固定pin|PR稳定pin/实现|最小后续处理及必须重验|
|---|---|---|---|
|Speculator/DFlash `propose`|参数`dp_sync`，没有动态`num_speculative_tokens`末参数|`dp_sync_state`，新增可选`num_speculative_tokens`；PR Ascend含新旧接口兼容分支|不能直接覆盖Graph speculator或换上游pin；最终pair批准后只在隔离组合候选适配真实调用参数，重验dummy/DP及三种方法实际proposal|
|源read-view/metadata|Graph持久bank、generation、当前exact和真实capture/UPDATE binding|PR `DraftWindowRuntime`＋`DenseDraftRead/Batch`、`_draft_window_device_read`|以PR eager稳定入口与Graph专有carrier分别保留，明确单一owner/selector，先Host真实调用反例，再重验数值/Full写/Target；不把两套runtime并行注入同一metadata|
|GLM DFlash加载|C205辅助fc W@Q及私有vocab W@Q.T|185e→0be完整修复链|当前已等价吸收，无新生产移植；将来只确认单次加载及非aux保护，不重复变换，不复制PR二进制|
|reader完成|Graph ExternalEvent/尾notify/stream FIFO/持久bank；eager各自完成event|PR eager runtime及回收|未来组合不能用PR eager事件替换Graph最后reader边；生命周期或调用上下文变动时定向重验，不重跑未变整矩阵|

推荐执行顺序仍是独立Graph先关闭当前有效失败/缺臂，再提交明确Graph/PR/pin组合供确认；未批准整体集成，暂不修改任何上游/PR代码或生产底座。C234只有必要Eagle TP4准入及私有工具链变化，不影响当前固定C231 GLM或C232单卡对照。该准备不增加进度、不构成集成PASS。

<!-- R7_PR_SHARED_RECONCILIATION_END -->




<!-- FIA_ORIGIN_REVIEW_BEGIN -->
## C184来源判别：有界补证已结束，准确API归属待确认

**当前结论D（证据不足）**：已在原生调用层复现，尚未证明完整官方模型的合法路径也发生同一问题。未确认平台缺陷，未归入Q017；SWA数值/正式性能仍阻塞。本轮不继续底层修复或无新假设的重复探针。

|证据|实际内容与结果|边界|
|---|---|---|
|C184原件|functional/out/Graph各自5次重复不一致；有效query8–15/head4–7，out第0/1次[14,7,35]为−11.875/12.5，差24.375，该对1639元素不同；全部finite，原padding24–31未变|三条路径共享底层和部分工具，非三份独立归属证明；Full是SWA6末层noncausal Full层|
|C186回读/容量|实际Q/K/V/table前后精确一致；同view缩容量与紧凑ND仍复现|排除所测输入修改/单纯可见容量假设，未证明API合法|
|C188唯一补证|两个独立新进程、3正长度请求、各5次functional，Q[24,8,128]、KV[11688,128,256] ND；canonical OFF max22.5625（−10.0625/12.5，最多3951元素不同），current Window max14.0625（4.8125/−9.25）；输入回读一致、输出finite，21.904/22.781秒，producer/checker0及Phy15实际关联/释放|去掉手工out/LSE、零KV padding、旧Graph状态仍复现；只到调用层，不扩大为完整官方模型或所有SWA失败|

环境：A3/910_9382，torch2.10.0+cpu、PTA2.10.0.post4/git`5dd8ef3f9b375b5ae4a83538d5785754148c3302`，CANN9.1.0。固定op-plugin gitlink`8b9c8534fa41eff367a41c155843daa530ab3a08`源码推导该平台分支走V3，未捕获实际函数解析入口。实际两进程加载batch_invariant vendor `libcust_opapi.so`，SHA`ff82d965a8a08bfa2862567022a04a1fd04df56d142f4393f1fb527592111069`；这只证明加载，未证明FIA调用它。本轮未修改vendor、确定性或依赖栈。

来源核对：官方祖先`52ce43b15172fce79297ae4f20612fec3a476f3f`的noncausal调用、cached分支及KV view helper与当前对应AST相同；整文件已有项目hook，不能称整模型未改。此前临时用到的167278/Repair7为项目修订，纠正原件留在目录。保存的canonical Full table及所需页面提供可比原始输入，但准确API适用性仍缺。

**可直接转交维护者的问题**：上述A3/CANN9.1/PTA版本，BF16 TND、heads8:2/D128、page128、maskNone/sparse0、scale1/√128、pre/next2147483647，Q累计[8,16,24]、逐请求KV[36889,8201,395]的paged调用，长度表示与shape/stride组合具体需要什么约束、有效输出精度合同是什么？希望由CANN/PTA FIA维护者确认，负责人待明确。现有材料不能把明显异常简单称作非确定性。

[完整现有目录](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C184_saved_SWA_Full_FIA_native_probe_01_node140)含`valid_output_analysis.json`、`api_review.json`、`canonical_off_call_source_proof.json`、准确版本片段、`canonical_pair_results.json`、输入hash和库hash。唯一命令在该目录匹配环境/新授权设备运行（本轮已执行，不继续重跑）：

```bash
ASCEND_RT_VISIBLE_DEVICES=<分配物理单元> python reproduce_functional_only.py run --input canonical_pair_input.json --view canonical-off --output fresh_canonical_off
```

另一个新进程以`--view current-window`及新的输出目录运行；必要材料为脚本、JSON及49,619,440字节`operands.safetensors`，`reproduction_command.json`含版本/hash。完整原FAIL/容差保留。本任务范围内若未来发现具体工具/接入错误才局部修；独立基线/底层问题交接，不以此关闭受影响交付项。C195 Full8另一个合法配置的数值通过不豁免本例。

<!-- FIA_ORIGIN_REVIEW_END -->

<!-- C185_MATCHED_PERFORMANCE_BEGIN -->
## C185匹配性能：已完成的限定测量

同node140/C185、GLM5.2+DSpark K8/Q8、W1024、TP16/DP1/EP及要求特性；Target各臂Graph，E_ON仅Draft eager。每臂2个独立服务实例，各3次同实例重复，不是6次独立启动。四组固定请求，初始化/capture/预热/官方prefix reset/RPC排除；正式108请求、72测量组，cached_tokens全0，预热36不计。真实HTTP/SSE aiohttp客户端，不冒称AISBench。

|固定输入/输出/并发|G_OFF中位秒|G_ON中位秒|E_ON中位秒|Window耗时节省|同Window Graph耗时节省|
|---|---:|---:|---:|---:|---:|
|257/256/1|4.962736|4.938499|5.416848|+0.49%|+8.83%|
|8193/512/1|12.283477|14.935678|16.133031|-21.59%|+7.42%|
|真实文本16385/512/1|14.230234|11.643295|12.511821|+18.18%|+6.94%|
|[127,2049,8193]/各256/3|11.581193|12.966991|13.466588|-11.97%|+3.71%|

负号是回退，0.49%不宣称稳定收益。短G_OFF范围4.790–8.380秒；混合G_OFF 8.175–15.133秒，全部保留。8K接受率G_OFF39.12%→G_ON33.48%、验证请求步743→834；16K36.70%→55.11%、782→568；混合34.21%→25.73%、1241→1518。工作量变化能解释方向，但不能据此排除metadata/等待成本；混合请求并发未消除轨迹与调度波动。

接受=框架采样器在stop裁剪前接受的实际Draft token，proposed=实际调度提案，二者排除bonus/padding；平均接受长度包含bonus。不累计TP rank作为额外样本。TTFT与客户端平均TPOT来自真实SSE单调时钟（可多token一批）；逐token ITL缺失，不能由elapsed伪造。每次Host manager调用、窗口E/start/active/padded和精确请求ID关联已审计，Host次数不等于device occurrence。短请求实际start全0、E265–526，Graph padded2/eager padded1；未裁窗也有自然轨迹差异，仍由原R6-C151-TOKEN-01处理，不自行豁免。

未观察外来设备context不等于整机独占证明。真实CPU/RAM/HBM峰值未完整测得，HBM管理采样保留。历史采集时C151/C158及正常Graph证据方式未裁决；现已按本轮用户原答明确可比数值与限定Source/API工程合同，原测量/FAIL不改写。正式产品性能标准仍未批准；未覆盖师傅32–128K/2000输出完整历史主负载。未做生产优化来美化数字。

完整逐次计数/范围/逐位置/whole-response配对：[summary.json](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C185_matched_performance/summary.json)、[samples.csv](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C185_matched_performance/samples.csv)。六段all16实际join和退出/租约记录均在原case；C177/C182失败原件不覆盖。

<!-- C185_MATCHED_PERFORMANCE_END -->

<!-- C185_WORKLOAD_SPLIT_BEGIN -->
### C185工作量拆分（已有原件，无新增设备）

短G_OFF最慢8.37955秒对应97验证请求步，其他同臂样本中位55；不能删除为“噪声”。提案/接受/逐位置计数都相同的两个短请求，ON仍慢6.78%与5.17%，且实际window_start全0：整体0.49%的净差不代表准备开销消失。8K接受率下降、验证总步743→834，16K782→568；这些改变工作量，但尚不能把全部时间差归某kernel。混合3请求的pooled请求步不是串行engine轮数，不按它推kernel耗时；并发也未自动消除波动。

36对最终输出中，G_OFF/G_ON 21对相同，G_ON/E_ON 34对相同；只比较最终轨迹，不是配对中间前态或质量/正确性豁免。实际OFF每代U/E未保存，不能凭推测归Q015。当前未启用single-metadata实验开关，未删除exact等待或移植CPU镜像策略。[逐次对照与全部慢样本](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C185_matched_performance/workload_split.json)，同目录可复算脚本。没有新增性能PASS或生产优化收益声明。

<!-- C185_WORKLOAD_SPLIT_END -->

<!-- FULL8_FIRST_FAILURE_BEGIN -->
## Full8参考工具纠正：首样本与三样本复验均已完成

- C191旧原件保留：四rank首样本有效hidden最大31.75、16370/16384个BF16元素不同。C195同一前态实验精确重现这一差异；不是删除反例或放宽判据。
- 具体原因在工具参考上下文：Graph carrier继承Target的`PrefillNoCache`；直接copy给eager使真实backend走query-only K/V（长度8、无页表）。真实Draft eager builder给出的状态为`None`，读缓存/table/本代exact1033。Graph task UPDATE实际使用缓存参数；carrier枚举不能当eager参考合同。
- C195仅工具改动：从canonical独立计算table/exact，调用实际Draft eager metadata builder及query-padding updater；CPU upper仅作当前max bound。生产树与C194相同，53定向Host通过。
- **已核验设备/独立CPU结果**：first discriminator producer0、461.178秒；所有4rank Graph/正确eager hidden与全部16路KV均零差异，第二次独立正确eager仍相同；首层Query/FIA输出、functional两次均相同。旧参考同前态精确复现最大31.75（−36.5对−4.75）、16370元素不同。所有restore精确、输出finite。此结论只关闭首样本参考工具问题，不等于完整Full8/Target/正常生命周期通过。
- 完整逐rank原件与独立复算：[verdict.json](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C195_Full8_reference_origin_01/verdict.json)；首样本raw在同目录上级`raw/C195_qwen36_Full8_actual_eager_first_discriminator_01_node140`。C194 guard失败主sample仅PREPARING/path=null，原raw-ready判断已在其`raw_completion_correction.json`追加纠正。
- **已完成必要复验**：同C195不带`--owned-failure-probe`，关闭额外D2D owned采集，仅保留原连续数值诊断；TP4、Phy8–11，两active1＋一active3/padded4。plan`state/C195_NODE140_FULL8_NUMERIC3_PLAN_01.json`；raw`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C195_qwen36_Full8_actual_eager_numeric3_01_node140`。producer0/289.697秒；C196 checker离线全4rank×3通过，原checker误将Window exact1033与Full终点1545相比，C196从end减start512，保留全部绑定/数值/写集合检查。57 Host合法与损坏检查通过。原INVALID不覆盖；结论`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C195_Full8_numeric3_external_C196_01/joint.json`。不是性能、完整Target/ABA或正常无附加同步证明。
- SWA C180 state-only反事实原先仍失败；C184/C188另有正请求/GQA8:2的原生异常。不能将本次Full8/B1/GQA8:1工具归因移植为SWA豁免。C184归属D与API问题保留。

## 历史：PR只读接口与加载依赖（2026-10-27T23:36:14.043349+08:00，Q023已被上方R7核对替代）

- PR实际主线`238c7589b640408439204007d1b1c8103f934912`/tree`c6aca7e6287aac3f77c4a200343184fc497a233a`，pin`a98247ab4db686ee03c66d5feb3c761e52a2f8ab`；已只读git核对。旧CANDIDATE_TRACKING.json仍停C23，不作为当前事实。Graph固定pin仍84030bbe，未获最终集成pair批准，两个候选没有组合验证。
- PR报告新增Q023：GLM DFlash QuaRot辅助投影加载缺口。独立修复`0be870af5e9e559b33c86e71e7c4bb8b485df87d`未并入238；源码diff为新`models/qwen3_dflash.py`45行、加载后调用及现有对齐helper/测试。PR报告称OFF四case质量改善，Graph未独立复验这一结果。
- Graph当前DFlash沿固定上游loader，没有对应专用QuaRot对齐hook；本仓DSpark有`process_weight`和专用load_weights旋转。此为共享加载依赖线索，不能从Graph/eager彼此相同推导模型配对业务质量已正确。保留C159窗口数值/Target范围，其接受率/业务质量及最终交付仍需该加载问题的适用性处理。
- 按当前范围决定：**先交接独立基线问题，不自动移植、不改pin、不复制PR二进制、不修改PR工作树**。将来固定pair采用修复时需检查旧pin的DFlash辅助层/embedding/lm_head所有权接口，重新验证受影响方法数值/Target/接受率；Qwen非QuaRot模型和未涉及的DSpark证据不从零重做。
- 接口准备：PR `DraftReadView.exact_cpu_for`/owner pool/eager-completion，Graph `DraftWindowGenerationIdentity`/persistent carrier/ExternalEvent分别有同等职责，不能直接替换类名。固定pair确定后按配置→exact/read-view→metadata selector→generation/reader→异常的调用点适配，并补真正组合验证；当前先保留必要差异，不强并全分支。

## 历史交付计划与验收边界（2026-10-27T12:15:47+08:00；保留原判据与时点，不控制当前派发）

已关闭项按原producer/checker复用：C147全16rank×14 CP数值/Full写/ABA及224 Target联合；C151三臂实际prefill/mixed/decode与真实服务；C157 eager正常双lane event回收和既有异常；C159/C164 GLM DFlash完整数值及224 Target联合；C161指定Qwen Full8 TP4DP1 OFF/ON；C165/C167原版TP4DP2EP8八worker官方HTTP/设备关联。当前不再派发这些未变producer。C169配置失败与C170 carrier guard失败均保留，C172局部修复后同SHA producer/checker均0：8worker实际DP2/EP8、两组裁窗、172次dummy基线UPDATE；[完整joint](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C172_qwen36_full8_DP2_ON_service_01_node140/joint.json)。仅服务接线/当前代绑定，不是数值或最后reader完成。此句为C173历史执行点；当前以顶部固定计划为准，不派发旧队列。

SWA当前事实：C173 producer74退出发生于工具的两group假设，非数值比较；所有四rank原始post-capture头信息已保存，实际gid10–15逐层分区，前五causal/native4096、末层noncausal/Full。C174只改工具，66 Host通过；[真实四rank头＋三类损坏离线结果](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C173_post_capture_headers_C174_01.json)。原FAIL保持，原件没有请求结果，因此C174仅补此前缺失请求。C173/C174生产子树均`b2c6813f091d621c292746061f549c200e3080f4`，不重跑已通过GLM数值。

指定Qwen3.6 Eagle3静态准备：固定pin实际EngineArgs G_OFF/G_ON均构建成功，TP2/K3/aux(3,19,35)、KV2/head256，使用PR已有fc_norm派生权重；[CPU配置原件](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/host/C173_Qwen36_Eagle_actual_config_preflight02/result.json)。首个Host attempt导入路径错误保留，第二次纠正后通过；未加载模型或运行NPU，设备顺序仍在DFlash之后。

SWA原版底座新增：C174四rank短请求完整接受；C176 `15401f34312917ab7e112b3c083d60fb9bb96530` 原版OFF以max_model_len40960/chunk4096，固定输入36865以及36865/8193/387，各输出256，四rank完整capture/replay及设备关联联合通过。模型493.41秒；[完整原件](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C176_qwen36_SWA6_DFlash_long36865_OFF_anchor_01_node140/joint.json)。这不是额外Window、内部数值、DP2或正式性能通过，不按启动/检查数量加分。

### DSpark：三个不同的数值要求（沿用R6-C151-TOKEN-01，不追加通用BF16任务）

|比较对象|原要求/来源|现有实际结果|已解释与未排除|下一步/裁决|
|---|---|---|---|---|
|相同前态、shape、Window的Graph/eager|用户要求独立同Window参考、不得放宽checker；冻结设计§20的Target/Full写与§15 A/B/A合同。严格zero oracle见固定C158 `tools/p7x_graph_repair65_glm_eager_padding.py`调用CP checker|C147完整14及C158三样本各16rank原Q16 Graph/eager输出/KV严格通过；generation/ABA及Full slot各自有效|该路径未观察到待修数值错误；串行诊断不代替正常完成|不重复模型；最终生产diff若影响此路径再定向复验|
|相同有效前态、不同padding/M8/M16的原生计算|C158私有区分实验主动设置逐位判据，原FAIL保留；所查冻结设计§4.5/§20未明确要求所有跨M BF16算子逐位一致。未找到团队已确认的跨M阈值原文|C158 `FAIL_VALID_EVIDENCE_EAGER_PADDING_CONTRAST`；两shape各自ABA相同、差异位于合法Full写集合。C160六次原生数学复现首层V：−0.02490234375 vs −0.0247802734375|至少这一首层差异不需Window/Graph/KV即可产生；不能解释全部深层误差或自然token，也不证明平台违反精度合同|用户/师傅提供既定跨M精度要求或确认适用性；负责人待明确。无新具体Window错误时不改通用算子、不升级栈、不改变容差|
|自然调度下的完整token轨迹|C149 Tool60 whole-request identity＋tokens逐位join；这是本任务诊断门槛，未查到其等同于团队跨不同调度/Window轨迹发布标准的原文。用户已要求不同前态不得强配|C151各臂服务有效，跨臂严格token FAIL：OFF/ON4/12不同、E_ON/G_ON7/12不同；C155原版E_OFF/G_OFF12/12相同，但各自冷热仍2/6不同|已排除仅summary拼接，未排除自然上下文中的Window新错误；C160仅解释一个首层差异|保留FAIL与原SSE；请师傅明确自然请求的精度/质量合同。若要求固定形状布局，需先审方案与成本；不直接强迫padding来制造PASS|

关键原件：[C158完整joint](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C158_glm_cp_same_prestate_eager_Q8_Q16_prefix3_01_node140/joint.json)、[C160独立数学](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C160_dspark_first_projection_math_01_node140/math_joint.json)、[C151 token明细](/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C151_three_phase_token_mismatch_details_01.json)。冻结设计路径：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/adaption/MRV2_完整中文迁移_20261022_034933_0800/任务归档/002_20261008_多方设计评审与最终架构冻结/原始资料/MRV2_Speculative_Draft_Sliding_Window_Final_Design.md`，本次读取SHA256 `47a8e54d4f36f25ef6fe13a519d3f3c9361930de2afbe515e2c2d686f95bb006`。只核对相关条款，未重审历史全库。

### 正常Graph reader/backing：具名的剩余适用前提

|consumer/完成依赖|已有源码与行为依据|还缺什么、最小动作|
|---|---|---|
|DSpark K8 parallel query Graph内FIA读取持久Window table/exact，后继current写入|`dflash/aclgraph.py::run_fullgraph`：materialize/bind N→update_stream.wait_stream(current)→replay→同update流task-update/ExternalEvent.record。CANN9.1/runtime_v100/910_9382附加capture流尾notify合流、RI endGraphNotify/current FIFO；FIA Host长度vector有拥有副本。C151每rank438代/绑定，403次裁窗，bucket(2,16)/(4,32)地址稳定|未发现新的具体缺失边。平台维护者（负责人待确认）只需确认已引API覆盖本安装的注册consumer/附加流，或指出例外；若指出未登记reader再定向修复，不再重复同类trace|
|正常Async Target输出copy_event|已查`sample_tokens`先创建AsyncOutput，后执行Draft proposal，Target的较早copy_event不覆盖后继Draft|明确不用它冒充Draft最后reader完成；C157 eager双lane522操作/520完成释放按其scope保留，不改写为Graph证书|
|每次执行的operand/硬件physical-read|数值、参数绑定、源码排序分别已有证据；现trace不含所需逐次地址/读取字段|仍NOT_OBSERVED/NOT_AVAILABLE；本行原“证据方式待裁决”已由R7用户明确接受限定Source/API、绑定/所有权、独立多代数值/Full写/Target/异常材料而关闭。直接硬件读取缺项保留，不重复observer；有新具体缺边或团队直接观测硬条款时才具名提出|

### 匹配性能：重复与启动的区别

R6-04用户原文为“同机、同候选、固定请求与采样配置，至少做5次平衡重复”；所查答复没有要求每次独立启动。旧Tool56的18次服务启动、六排列属于原脚本执行安排，保留为历史，不自动派发旧队列。下一性能方案优先在少量独立实例内保留有限重复，明确报告实例数与同实例重复数、预热/缓存/次序，不能冒称六个独立启动。若改变已约定统计口径则先具体follow-up。本段形成时尚未派发新性能；C185现已完成6/6服务（本段原5/6为历史中间态），末臂G_OFF执行中的表述为历史中间态，C151/C158原FAIL及后续已明确的合同分别保留，新增结果最多是诊断；不得宣布正式达标。

约定主负载与prefix命中兼容分开：bench GLM DSpark历史是引擎prefix开启但无实际命中；C151真实命中/阶段证据已足够复用，不生成“命中/无命中×全部长度×三臂”。匹配G_OFF/G_ON/E_ON使用同机新固定候选，正式计时排除模型初始化、预热、数值诊断和profiler。Q015镜像性能取舍和Q017既定基线例外保持原范围。

<!-- CURRENT_DELIVERY_DETAIL_END -->


<details>
<summary>C138/C140旧计划，仅追溯、不可派发</summary>

## 历史校准明细（C138/C140时点；当前状态以上方及进度页为准）

|目标|原权重|原贡献→当前贡献|本次计分依据及剩余|
|---|---:|---:|---|
|基础Window数学、Full写入及policy|10|8→8|保留已有多方法证据；新CP路径Full写尚未裁决|
|GLM DSpark Draft Graph与数值/Target|20|15→15|C106全16rank限定诊断保留；新增CP数值/14场景未通过前不加分|
|GLM真实服务和必需特性共同开启|25|5→8|C138 OFF/ON服务、16rank、prefix/chunked与C140完整token配对关闭预声明服务子门槛；源码/最终候选及内部验证未闭|
|正常生命周期、异常与请求调度|10|5→5|C126历史故障链保留；联合Async reader完成/复用尚未验收|
|GLM匹配对照、服务性能与接受率|10|4→4|C110/C128保留原身份；本轮初始化耗时不算性能，尚无新匹配三臂性能|
|GLM/Qwen3.6 DFlash交付路线|12|1→1|仍为阶段二，旧Qwen3-8B成果部分复用，不取消|
|Qwen3.6 Eagle3及policy回归|8|1→1|仍为阶段三，已有修复保留，不取消|
|最终组合、PR集成与审查|5|1→1|无获批固定集成pair；两份独立PASS不合并为产品PASS|
|合计|100|40→43|管理估算，不是通过率或发布批准|

### DSpark阶段：已完成与仍待完成

已完成4个限定服务子门槛：①真实GLM/DSpark官方CLI+TP16身份及capture库存；②必需特性同开时G_OFF底座；③同开G_ON服务与实际窗口source/Host replay；④完整请求配对、真实prefix命中与分块阶段记录。上述不是“DSpark完成4/4”，内部数值、生命周期与匹配性能仍在下表，不与服务门槛混成完成率。

|剩余项/类别|已知事实及具体缺口|下一步/是否改生产代码|设备与时间估算|完成判据|
|---|---|---|---|---|
|1. CP数值、Full写与Target隔离：必需验证|C138修复了C136 Target Q9=36 native失败的输入buffer所有权；服务复现范围有效，但新CP内部数值未闭|SP输出bucket读取已在C144修复；C144又遇CP Full slot边界失败，先离线区分dtype/value/pad并形成反例；迁移暂停，后续独立候选通过三样本才做ON14+OFF14+完整Target join|TP16；工具修复/定向检查约20–45分钟；新固定候选前哨设备约20–35分钟+CPU复核；完整两臂约2–5小时，随前哨实测修正|每个rank连续数值/ABA、Full slots/positions及177类Target组件、完整14对执行关联独立通过；原失败不删|
|2. 正常Async reader/backing：必需验证+合同适用性|SOURCE_SUPPORTED合同已有；服务完成和串行数值不证明最后reader已完成。联合CP/Async consumer及异常仍需覆盖|核对C138真实consumer/current-stream尾notify/下一代写入，复用现有异常机制补有判别力的正常/失败回归；只有具体缺陷才改production|TP16；分析1–2小时，设备约1–3小时；不能拿逐代drain冒充正常时序|所有实际consumer的完成边与所有权可审查；未完成不得复用；故障进入隔离且下一scope拒绝，无无条件设备恢复|
|3. 全特性E_ON：实际准入缺口|C138 `build_draft_window_source_capability`→P2/P7-X会以SP/DSA-CP-without-DSA-provider拒绝dense Draft；Graph已有独立审核source入口|C142新增默认关闭`draft_window_parallel_eager_review`，真实factory→source→Async lane；Host通过，尚无设备。C143实际lane记录工具已完成Host检查，C144已固定但E_ON尚无设备。属于production修改，后续独立候选复验|TP16；余Host/固定候选约0.5–1小时；首臂设备约20–35分钟|Draft eager真执行、Target Graph保持、全部特性/source身份不丢、真实窗口裁剪、完整请求输出与正常隔离通过；不继承C138设备PASS|
|4. 匹配性能与接受率：必需测量|C110/C128及140数字均有原scope，不能跨机/跨候选拼本轮正式三臂；预热与初始化不计入性能|待数值与E_ON准入后，固定同候选/101/请求，按已声明6次平衡三臂运行；正式计时不混入数值/profiler。性能工具不改production|TP16无本任务其他重负载；约6–9小时，主要为18个服务初始化；若复用启动须另明平衡合同|保留每次原始SSE/服务指标与接受率；同Window Graph/eager和同Graph OFF/ON分开；≥5次中位及波动；受竞争样本单列，无已批准发布阈值|
|5. 真实请求与最终组合回归：必需验证|当前为固定token ID的官方服务诊断请求；mixed输入不自动证明实际mixed scheduler阶段。真实文本、请求替换/结束和最终源码回归仍缺|复用框架请求与轻量phase记录，固定真实文本，触发prefix hit/continuing/terminal/decode及实际mixed/替换；按生产diff选回归，不全排列|TP16；准备0.5–1.5小时，设备1–2小时；可与匹配性能共享合法请求但保持身份|具名业务输入、实际阶段/16rank/Graph dispatch与请求完成；同窗口正确参考；OFF/forced-OFF/原unsupported不回退|
|6. operand/physical read与最终集成：人工裁决/外部依赖|原验收技术包区分语义不变式和取证方式；当前trace无逐次执行operand/read-set字段，不是已观察到生产失败|复用已有API/源码、独立数值和异常材料；用户/维护者审查替代证据，负责人待确认；PR固定commit+pin批准后独立集成。暂不继续无界trace调查|本项技术审查不先占卡；集成确认后按diff估算|用户/明确维护者对具名验收要求作显式裁决；技术意见不自动变发布批准；集成候选有自身回归|

时间是依赖估算；Host与在跑设备可重叠，不机械相加，也不承诺本轮全部完成。C144前哨已失败并保留原件；本次迁移暂停，不继续实验。后续先区分首因，再按新证据修正估时。

### E_ON缺口的最小解释

Graph不是靠公共eager能力判定运行：它先核对实际review配置，再用受限的dense Draft source构建读视图，最后恢复真实SP/DSA-CP/FlashComm/Async身份。原eager入口直接把Target执行器的这些维度交给通用P2/P7-X判定，因此拒绝；这首先是当前baseline的入口/能力合同缺口，尚未证明eager kernel数值错误。

C142的最小修复为两个production文件（配置准入与source工厂），复用既有P3和Async独立完成lane；不删除原guard，不改Window数学、Full写/slots、Graph回放或C138受测源码。Host验证了真实配置工厂、默认拒绝、实际rank与canonical Full owner保留、独立Async lane及policy；它没有证明NPU数值、正常完成边或性能。C143只读采集工具已扩展到实际lane并通过Host反例，避免把未使用的初始runtime误当数据源；尚无新E_ON设备验收。C142及后续工具候选必须在同一固定producer上做匹配三臂与受影响验证，不能与C138直接拼正式性能。

验收未决依据：`reports/DECISION_QUEUE.md`及`dev/manual_review/adapt_人工后续核查.md`中的execution occurrence/physical-read原问题与用户“仅供独立技术评审、未豁免”答复；已有源码合同、安装库hash及独立技术包保留。具体裁决人尚未明确，记录“负责人待确认”，不虚构审批结论。



</details>

<details>
<summary>历史快照（node140 17:52等旧状态/旧待办，仅供追溯，已被上方当前计划替代）</summary>

---

---

---

## 历史增量（2026-10-26T17:52:31.984758+08:00，不控制当前派发）

更新时间：2026-10-26T17:52:31.984758+08:00；node-25-140；SESSION `20261024T195020Z_R6_node140_3bf24139`。

- 当前 `WAIT_RESOURCE / HOST_ANALYSIS`；16卡按用户要求让给同事，Graph无活动进程或租约，不会自动派发。
- 开发/只读checker为C134 `d3032810…`；设备producer仍为C133 `5ee6c354…`，二者不得混记。
- C133/C134启动与配对Host预检通过；Graph/PR共同DP1 SP谓词只读核对完成。两边pin不同、无批准集成pair，Gate仍冻结。
- 资源归还后执行C133 G_OFF→G_ON→C134离线联合checker；不重启C131中断attempt。
- 新截止：UTC `2026-10-27T19:21:18.369Z`，北京时间 `2026-10-28T03:21:18.369+08:00`。旧截止和旧候选段均为历史快照。
- 本次只完成Host/离线审计，不修改production，不增加设备PASS。

---

<!-- C133_HOST_PROFILING_DELTA -->
## 2026-10-26 17:41:42 +08：C133 等待资源期间的 exact-length 归因

C133 `5ee6c3547a160ce944edcd2d5ffa0a4ace25f9d3` 已固定，NPU按用户要求让给同事。本次只读复用C110/C98产物：GLM TP16单请求每代snapshot只有1个int32，却平均阻塞55.380ms，说明范围主要承载前序设备等待；C98 Window OFF也在metadata内承载近似等待。未发现可在不破坏本代exact/epoch所有权下直接删除的冗余，因此没有production改动。完整数字、适用范围和后续最小实验见 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/reports/20261024T195020Z_R6_node140_3bf24139/R6_C133_C110_exact_length等待归因.md`。

# adapt MRV2 Draft Sliding Window Graph 总报告

更新时间2026-10-26T17:35:39.714680+08:00；node-25-140；SESSION 20261024T195020Z_R6_node140_3bf24139。当前WAIT_RESOURCE/HOST_FIX，NPU未使用，无本任务进程和租约。

## 历史：C133时点增量（当前以上方R8状态为准）

C133 `5ee6c3547a160ce944edcd2d5ffa0a4ace25f9d3` / tree `306071997c63c4bb63bf23f27772e0ecd82f06c1` 是最新开发与待设备验证候选。它补入Ascend TP/EP、DP1 sequence-parallel资格，修正请求但未生效的FlashComm身份，允许已审查GLM TP16 Graph路线保留Async/SP/DSA-CP/FlashComm身份，并避免Graph模式误建eager async pool。Host检查506+36项通过。固定源码 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/candidates/node140/C133_glm_joint_features/vllm-ascend`；计划 `/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/state/C133_DEVICE_PLAN_01.json`。

C131 prefix G_ON官方服务已限定通过。C131 required G_OFF在模型启动阶段观察到SP=false及DSA-CP/FlashComm被禁用，随后按用户要求让卡停止；不是PASS或生产失败裁决。资源恢复后先用C133区分平台补丁是否令G_OFF实际Target特性生效，再验证G_ON联合配置。旧C106数值、C110性能、C128三臂证据保持原producer身份。整体NOT_READY，Gate冻结。

---

## 以下为更新前历史快照，仅供追溯

## 本轮继续检查点 C131 / 2026-10-26

更新时间：2026-10-26T16:59:54.439626+08:00；node-25-140；SESSION 20261024T195020Z_R6_node140_3bf24139。

- 开发与固定候选C131：e8b4c010b4cdfb13f29bac36795eee2dc329a18c，tree 7fadc3e3ef7c276c6ca32f97352804d9504f9ecc，干净。C131只改工具；production继承C129 prefix接线。
- C128真实TP16三臂首周期全部联合接受：G_OFF 26.415682s、G_ON 18.564209s、E_ON 20.430217s；各512输出。首周期Window耗时下降29.72%、同Window Graph下降9.13%，不是>=5次完整性能判定。
- C127已取得GLM官方HTTP/SSE、真实Draft/Target capture/replay、16rank设备关联；这不是全特性或新数值证明。
- C126 before_replay/after_update两rank真实sample_tokens异常展开、quarantine和Host guard均联合接受；旧R41无导出失败保留。
- C130 prefix_01/02均在模型前因Host导入问题失败，未计模型启动；C131改为worker内延迟导入，62定向检查通过。历史C131服务当时进入有限队列，已由C138及后续真实服务取代；不恢复旧派发。
- 下一独立分支：Window OFF真实Async/prefix/FlashComm/SP/legacyDSA-CP/chunked底座；随后Window ON按实际缺口适配。不能把底座通过算Window ON全特性通过。
- GLM关键连续数值/Target仍为C106；>=5次OFF/ON完整性能为C110，保留来源SHA。C129 prefix分支尚无设备数值验收。
- 新授权T0=2026-10-26T07:21:18.369Z；硬截止2026-10-27T19:21:18.369Z（北京10月28日03:21:18.369），最后45分钟收尾，不重置。
- dev/all五入口已建立：adapt_progress.log、adapt_live.log、adapt进度.md、adapt_任务总报告.md、adapt_日志入口.json；原journal/progress.log只追加，inode未更换。
- 人工核查：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/manual_review/adapt_人工后续核查.md；PR工作树和pr_*入口只读。DSpark→DFlash→Eagle3，完整交付NOT_READY，public Gate冻结。

---

> 2026-10-26T08:19:04.506366+00:00 当前：开发C128，parallel-prefix改动未提交；固定C128 TP16首个16K三臂周期运行中。C127 GLM官方服务10HTTP/16rank联合通过（非全特性/数值）；C126两个TP2故障分支通过。旧C106/C110仍分别为关键数值/完整性能证据。

> 当前权威增量：C126已在Phy12/13启动TP2 before_replay异常复验；worker911149/911150，已由管理采样关联到实际物理卡。以下C125和历史范围保持原始身份，后续按真实结论更新。

# adapt MRV2 Draft Sliding Window Graph 总报告

更新时间2026-10-26T15:19:33.932909+08:00；node-25-140；SESSION 20261024T195020Z_R6_node140_3bf24139。HOST_EDIT；NPU当前未使用；无后台模型/worker/profiler/派发器及本任务设备租约。新授权T0=2026-10-26T07:21:18.369+00:00；新硬截止2026-10-27T19:21:18.369+00:00，北京10月28日03:21:18.369；最后45分钟收尾，旧合同保留。

## 目标、分工与候选

阶段一GLM5.2+DSpark，包括FlashComm、适用SP、legacy DSA-CP、Async、chunked prefill、真实prefix hit与Target/Draft Graph共同开启；阶段二GLM/Qwen3.6 DFlash及已约定结构化SWA；阶段三Qwen3.6 Eagle3最后，不取消。PR先交付Draft eager、Target可开图，adapt独有缺口不阻塞PR；发现共用问题以具体commit/证据交接，不直接修改PR工作树。

开发：C125 15d428d9f3d270e8b5adcae7930d51d42af76c4c，tree e83764853a5e2a6a834ece72abb320dd03aee9ab；/dev/adapt/work/node140/vllm-ascend（前缀为本项目根）。R41已独立提交C126 50c00977d6d1e8273280a6d482ce88a9c02f9fa3/tree dc40b672c01bc0e43f366249aa994881920f0617；67项定向Host通过，production与C125相同；真实TP2复验正在进行。固定旧源码 candidates/node140/C125_window_history/vllm-ascend，runtime/node140/C125_window_history/runtime_manifest.json。
配套vLLM 84030bbe3d74d99bad477a3d2e37a973ccd8865c / tree f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee；Python3.11.10/torch2.10.0/torch_npu2.10.0.post4/CANN9.1；不改共享安装。实际worker来源须每次启动核验，不以开发树存在冒充实际导入。

## 模型计划及身份

以下均为完整路径；realpath和配置身份本轮仍在增量核对，未核验的明确写待核对。PR统一搜索/下载/共享索引，adapt不下载、不修改原config、不加载staging。

|路线|Target|Draft|身份与配置|实际Graph证据|
|---|---|---|---|---|
|GLM DSpark主线|/mnt/share/weights/GLM-5.2-w4a8|/mnt/share/l00887471/graph_vllm/dspark_test/sw-aspark/GLM5.2_dspark|已运行固定GQA5层，K8/Q8、TargetQ9、W1024/block128、TP16/DP1/EP；Target SFA/indexer，Draft dense FIA|C106真实16rank离线数值/ABA/Target；C110正常性能，非HTTP全特性服务|
|GLM DSpark MLA|同上|/mnt/share/weights/GLM-5.2-DSpark-MLA-NPU|PR已有ordinary MLA+TargetCP，adapt当前pin/Graph适用性待核对|不将PR eager结果记为Graph通过|
|GLM DFlash|同上|/mnt/weight/GLM-5.2-FP8-DFlash|PR报告实际BF16非名称FP8，K15/Q16；adapt静态身份待核对|无本Graph候选GLM完整设备通过|
|Qwen3.6 DFlash/SWA|/mnt/share/weight/Qwen3.6-35B-A3B-w8a8/|PR已声明/mnt/weight/Qwen3.6-35B-A3B-DFlash；结构化SWA固定身份待共享索引|Target实际config Qwen3_5MoeForConditionalGeneration，不能仅按名称断定loader；block_size不自动等于K|历史bench不同拓扑/模型，只作参考|
|Qwen3.6 Eagle3|同上|待PR固定身份；不自行另选|隐藏维度/辅助层/词表/位置编码/固定loader待核对|最后阶段，不能删除|
|旧Qwen DSpark|/mnt/share/wql/Qwen3-8B|/mnt/share/dspark_qwen3_8b_block7|历史路径按manifest核对；K7/Q7 anchor或config-only Q8，W1024/TP1|数值/Target/LIFE/异常及HTTP服务已有原SHA证据，不替代GLM|
|旧Qwen DFlash/Eagle|历史Qwen3-8B Target，准确路径以原manifest为准|/mnt/weight/Qwen3-8B-DFlash-b16；/mnt/weight/Qwen3-8B-speculator-eagle3|DFlash K15/Q16；Eagle K3 firstQ4+AR Q1，方法合同独立|C45/C91/C100原始设备成果保留，不改标最终SHA|

## 各交付环节真实进展

|环节|当前事实|缺口|
|---|---|---|
|加载与Draft capture/replay|GLM TP16 C106/C110已真实完成，不只是探针；Qwen官方服务C114已完成|GLM HTTP服务及全部必需特性共同开启未完成|
|数值与Full/Target|C106 16rank各14样本+ABA，Target224对|新生产变化按差异决定重测，不自动归C125|
|metadata/operand|实际provider/carrier与generation关联有限定证据|执行实例operand直接观测仍UNPROVEN；不得用最终参数替代|
|正常reader/backing|已建立SOURCE_SUPPORTED_CONTRACT，capture尾notify/RI合流、FIFO、单update流和ExternalEvent次序、Host长度vector拥有拷贝|真实Async/多lane/全特性消费者适用性要单列；LIFE逐代drain不是正常重叠证明|
|故障隔离|多方法TP1有LIFE/ABORT/Python异常；TP2准备拒绝通过|最新TP2 before_replay两rank预期异常，但导出工具漏sample_tokens，INVALID_EVIDENCE，正修复|
|全特性|当前GLM已实际chunked配置开启，EP/Target SFA成立|Async/prefix/FlashComm/SP/DSA-CP仍有guard/接口缺口；参数存在不作通过|
|性能|C110每负载每臂6次G_OFF/G_ON；长16K获益、短输入回退|匹配TP16 E_ON、服务TTFT/TPOT/ITL及全特性主配置性能缺|
|产品入口|受控实验入口observer-off仍保留provider；Qwen官方HTTP服务通过|GLM主配置真实CLI→engine→worker→Draft Graph全链缺|
|发布|public Gate FROZEN；独立技术建议非正式批准|最终范围/集成与发布仍NOT_READY|

## 现有性能与分析对象

C110 GLM TP16 K8/W1024：short257/256out，OFF中位3745.605725ms、ON3978.46936ms（回退6.21698%）；long16385/512out，OFF26006.228015ms、ON18762.510775ms（耗时降低27.85378%）。长接受draft比例216/2360=9.15254%→345/1384=24.92775%，验证295→173轮；bonus/padding排除，不能重复累加TP ranks。只有离线generate elapsed，不冒充TTFT/TPOT。
匹配E_ON未有TP16结果。C112旧Qwen Q8三臂显示Window短/长回退14.00%/7.88%，同Window Graph较Draft eager快17.68%/13.19%，与GLM不同权重/拓扑不能直接相减。历史负收益保留。
现有GLM正常profile 16rank共约28.53GB，代表rank0两份派生trace各127394713字节，导出曾有界停止，内容尚待核验；优先读取派生trace，不运行会修改原件的官方analyse、不再次采大trace。原始路径：runs/20261024T195020Z_R6_node140_3bf24139/raw/C110_glm_real16k_G_ON_profile01/model/profiles。

## PR共享依赖及复用界限

当前PR报告dev/all/pr_任务总报告.md已出现，07:14UTC版本：node-25-139，开发d63a6e8409614fbd60b7f67c736e1d976c3478e7，vLLM a98247ab4db686ee03c66d5feb3c761e52a2f8ab，设备MLA声明范围d63，完整匹配性能fb86，仍NOT_READY。与Graphpin不同、nativeABI不同，不直接复制安装/全分支。PR共享修复5db/d63需要最小接口影响分析，不能把两个PASS拼整体集成。GLM模型尽量相同固定路径。
可直接引用：原候选已通过的数学/数值原始结果和既定policy；差异后复用：production未改路径；必须补测：consumer/长度/生命周期/服务入口变化；历史参考：不同模型、拓扑、机器和teacher性能。Graph未知直接physical-read不能自动阻塞PR eager，具体共用错误另通知。

## 下一步与风险

1. R41双入口Host异常导出，单次导出/原异常/无设备恢复反例→独立commit→2卡定向验证。Host10–30分钟，模型历史初始化约1–3分钟，硬超时20分钟，保留原收尾余量。
2. GLM真实服务/Async/prefix/FlashComm/SP/DSA-CP缺口表与当前PR接口对比，挑有明确合同的最小生产修改；不只删guard。先2–6小时分析再调整总估计。
3. 有界解析已有rank0 trace，核对snapshot等待、metadata次数/区间并集、replay/update分工；0.5–2小时CPU，无新NPU。
4. 具备真实主配置后TP16 eager/Graph与OFF/ON、实际prefixhit/chunking/调度、服务生命周期及必要性能。按每cell12–15分钟和已知全矩阵约1–2小时/臂估算，资源等待不计有效工作。
5. 阶段一后继续DFlash，再Eagle3；不下载重复权重，不重新跑全部历史扫描。

人工裁决原文：dev/manual_review/adapt_人工后续核查.md。MTP/DeepSeek-V4内置共训DSpark强制OFF，其余方法按既定支持/拒绝/warning，不因Graph fallback就声明支持。physical read-set未知不等于已观察生产失败；替代证据方案仅待独立技术评审，不自行豁免验收。


</details>

<!-- C200_EAGLE_PRESTATE_RESULT -->
## Eagle C199→C200：诊断前态所有权修复与独立剩余失败

C199在第5个long-three/AR1样本的reference V前态含NaN，Graph实际V有限，原FAIL保留。C200仅修改默认关闭数值诊断：在capture之外预分配owned pre-KV，以out形式快照；保留旧capture-pool结果作同Graph非oracle反事实。相同Graph内owned前态/独立eager得到完整short与long的6消费者/rank全通过；旧AR1 V仍差28751/28752元素并含NaN、旧AR2 V差17663。故这是具体的诊断buffer所有权缺陷，未修改native或正常路径时序。

第7样本boundary-four/first仍失败：all2 rank，generation105/epoch35，active4/padded4，descriptor[4,16]，L0/end[1029,517,133,131]、start全0；7009/32768有效hidden BF16元素不同，max0.5（−35.25/−34.75），全部finite；K/V前后态、reference及Full写零差。归属未确认，不套Q017，也不因输出相近而放宽。两个后续AR未执行参考裁决，整组不能PASS。下一最小区分动作可核对model输出是否同样依赖capture pool，保存owned与旧引用同Graph对照；尚未实施/未取得该结论。

证据：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C200_qwen36_Eagle3_TP2_owned_prestate_numeric_01_node140`；CPU复算`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/reanalysis/C200_Eagle_prestate_counterfactual_01/metrics.json`。production树c1c4f91d、56定向Host通过；C201普通GLM不启用该诊断。

<!-- C204_PRODUCT32K_PILOT_BEGIN -->
## 32K/2000输出顺序pilot：已终态，C204不完整组保留

- 固定GLM DSpark K8/Q8、TP16/DP1/EP、W1024三臂；四条固定token stream各32000输入/2000输出，c1逐请求；1完整预热＋3同实例重复，前向1服务/臂。与C185的2独立服务/臂×3重复不同，此pilot不冒充≥5平衡组或师傅GSM8K/128K主负载。
- C201在调用旧服务guard处12.06秒失败，无模型；C202工具guard修复50Host后实际16rank加载，但max-model-len49152需要5.06GiB KV、实际4.11GiB，未到HTTP ready或请求。root对已确认自身API server先SIGTERM、90秒后自身producer SIGTERM，触发现有监督器精确PID/ticks清理；不是外来终止或健康任务被让卡。原result的−15不替代首因。
- C204 `06fafe0da5f690bbd7accb21984063b53fb60031`仅将实验容量上限36864（固定请求总长34000，低于日志估计39808），利用率0.6、请求/K/W/采样/特性不变，50Host；生产GLM路径与C202等价。C203仅default-off Eagle诊断改动保留独立身份，不当作GLM新增语义。
- 原件：`/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261024T195020Z_R6_node140_3bf24139/node140_return_C144_20261026T1425Z/raw/C202_glm_product32k_b1_p1_G_OFF_01_node140/capacity_failure_analysis.json`。当前plan `state/C204_NODE140_MATCHED_PERFORMANCE_PLAN_01.json`；OFF已40min自身timeout，原producer−15/runner2，after16rank与1完整正式组通过只读核验：474.264秒/16.8682tok/s、accepted2835/proposed41304、5163验证请求步。未齐3重复、不是整臂PASS。G_ON已producer/checker0、全部16rank关联，3正式组196.958977/196.341399/196.691099秒，中位196.691099秒；每组accepted6131/proposed14992、1874验证请求步。ON中位相对单OFF描述性少58.53%，1对3且无逆序块，不称正式稳定收益。E_ON因收尾预算NOT_RUN；两臂均已退出并释放，plan不再派发。正式计时排除初始化、预热、reset和RPC，源数据/SSE/计数/所有慢样本保留。结果仍受C151/正常Graph合同限制，为诊断性能。

**R7补缺臂已完成（2026-10-28T11:36:59.463708+08:00）**：C204 E_ON同请求同node140，单实例3正式组211.901073/211.815928/211.995940秒，中位211.901073秒、37.7535输出tok/s；各组accepted6134/proposed14984=40.936999%，验证请求步1873，平均接受Draft长度3.274960（不含bonus）。12正式请求、预热另计；16rank与来源/特性/外部设备关联通过，producer/checker/runner0，整case2179.913秒，全部own进程与lease释放。未观察到foreign context不等于独占整机证明。旧ON中位196.691099秒相对本E_ON描述性节省7.1779%，但OFF1/ON3/EON3且跨新旧资源窗，不能拼正式平衡PASS。依据：/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261028T023750Z_R7_node140_06fafe0d/reanalysis/C204_32K_missing_E_ON_result01.json。上述“E_ON因收尾NOT_RUN”仅为R6旧时点记录，已由本R7缺臂结果补充，不再派发同一缺臂。

<!-- C204_PRODUCT32K_PILOT_END -->

### 2026-10-28T01:38:11.512058+08:00 PR只读时点更新（不影响Graph运行）

PR主线仍238c7589b640408439204007d1b1c8103f934912/tree c6aca7e6287aac3f77c4a200343184fc497a233a；最新报告为139→101迁移暂停，非本Graph控制状态。历史时点0be870af加载修复仍为独立未合主线候选；**此描述已过期：当前稳定0be已合入，Graph C205已完成等价加载适配，见R7表，不作为当前待办。**Graph GQA DSpark路径与PR报告相同，config SHA730803ab71b25b7ef38008024afef60fcfffeb6279db30732068eb668e218961；另一个MLA模型是不同路径/config70578186…，不能混同或据此另扩Graph矩阵。未改PR、未借其资源截止、未批准最终集成pair。

<!-- R8_FULL8_DP2_REQUIRED_CONTEXT_BEGIN -->
## 历史：Full8 DP2接入缺口（C254已取得限定功能结果）

原GLM C244/C246/C248只覆盖TP16DP1；Full8 C172/C222覆盖TP4DP2未组合底座。当前有两处明确限制：characterization的DP2组合guard、Graph fingerprint.parallel_dp对features=false的固定资格，不是Target/normalreader旧待办，也不只删一个guard。PR固定Full8产品配置的Async/prefix/chunk/SP/FlashComm为参考，不能复制其PASS；本Graph配套84030需实际适配/复验。

已核对C222八worker中两个DP engine/TP组的独立PID和本地canonical owner；跨进程相同数字地址不是共享owner证据。Graph使用持久bank/stream顺序/ExternalEvent/尾notify，始终lane0，不套eager双lane pool。原固定Source44项CPU底座/错误控制已过，尚非新组合通过。当前最小计划在既有C244 required-eager-prepared/REVIEW.json与dp2-feature-prepared，未改PR、共享权重或底层栈。Full8 active8原数值FAIL/SWA/API等待继续保留，不做正式性能。

**C252实现/Host已完成，设备待测**：SHA `7fc83ef426260cb21e8a04a5e746f51111051241`，production`7f406fad20b437d84304c48523b2e5307cb8aace`。Full8 TP4DP2/K7Q8/W32768具名Source及capture/runtime fingerprint保留真实Async/prefix/SP/FlashComm身份，DSA-CP/其他方法/W/K拒绝；每DP独立worker/provider/canonical owner，Graph lane0及持久bank不套eager池。Eagle TP4/K3/W1024 firstQ4/ARQ1另补prefix capture资格，不与DSA-CP混用。actual-dev-final-check01实际DEV91通过，无NPU初始化/FD新增；无新模型PASS。Root_communication_reader_review.json核对实际DFlash调用/输出通信参数，没有新具名private Window reader或缺边；完整新DP2服务仍需有效flags/rank/prefixhit/chunk/phase/dummy原件。

**C253限定性能工具**：SHA `54f8c6611cf3a422f84ce578e46887727c6827ea`，production与C252相同；Tool81显式冷缓存required-profile，2个相反平衡块、每实例3次重复，每臂6/2boots；固定C241短76/70、16K16012/16006、每请求输出256、并发1。prefix引擎ON而实际cachedtokens须0，功能prefixhit复用C244/C248。关闭functional重型dump，只保留轻量Host phase身份/计数；正式计时无数值/LIFE同步/profiler/CPU重负载。实际DEV50CPU＋23真实组件/损坏控制通过；尚未新性能producer原件。来源核查在required-cold-performance-prepared/Root_GLM_source_transition_review.json，GLM TP16DP1不进入C252新增Full8/Eagle分支。各旧结果不改标C253全部通过。

**C254仅功能工具已保存**：`6b9c145bf5b191cadc22c49e2ec48f38c43f60b7`，production仍C253相同。Tool33/69显式Full8 required-profile；8worker按DP独立请求/owner/phase/prefixhit，实际每DP最多3active/padded4，不覆盖active8原FAIL。原默认三臂argv及C225真实dispatch等价、请求ID/DP损坏拒绝、旧sync原件不能升格新profile，actual-dev-check01实际DEV21项通过，NPU未初始化/FD不变。新header只读CPU配置和缓存身份/地址，未增event.query/sync/D2H或吞proposal异常；完整新服务仍NOT_RUN。该检查已于UTC16:00:52退出，早于C253 UTC16:02:21启动，不污染新正式计时。
<!-- R8_FULL8_DP2_REQUIRED_CONTEXT_END -->
