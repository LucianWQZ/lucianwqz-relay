# 候选与证据对应表

所有后续候选为LOCAL_COMMITTED_CANDIDATE，REMOTE_PUBLICATION=NOT_PERFORMED。原Repair7发布事实不转移到本地提交。

|候选/完整SHA|定向Host检查|本轮正式模型启动|设备与复核范围|
|---|---:|---:|---|
|C12 `d15a510c2afba62b8a0e37aa574550852079fd13`|14历史定向|8|fixture8/CONFIG/A0/A1/B0/LIFE21；原ABORT runner4失败保留|
|C13 `1da6b63cc631e63e1673080278bd92b8746b582b`|69|12|新四ABORT/四实际C1展开接受；旧C12四只读复核另列|
|C14 `6e8b617b59d975c67467ab896f35821bd31290a7`|50|0|Host/prepare，未NPU|
|C15 `1e88c8208670518f63043552b530b1ed3e2f2677`|68|26|完整12数值/ABA、Target4十二对、LIFE/四ABORT/四展开，六控制三profile|
|C16 `154f33d99d6b3c6bf373fcfb1af347ae49b915d5`|88|0|probe03，未模型；路径错误/审批拒绝保留；C15旧raw解码不是C16设备|
|C17 `057b8e0300967e68e3f2a78c5910c8877521674e`|33+3锚点|9|真实锚点/前哨/LIFE及三short对照；native容器失败保留，无完整矩阵|
|C18 `52c3d487bb3c302d7170087aaaa79e34e3de7846`|10|0|仅Host准入修复，未NPU|
|C19 `da5b0f054c4b94362ff3539de911b26b4074052a`|45|17|同SHA20个计划case全部runner接受；17正式模型，fixture/probe另计；完整数值/Target/LIFE/故障/native参数|

C19 tree `af4519a635d6ccd70646f77195fde18368bdf22b`；Repair7 ancestry、vLLM pin与实际worker来源见源码身份当前核验.json。C12→C19整个production子树相同，诊断/工具变化按实际影响分别重验。

## 来源分层

- 本轮实测：上述各SHA对应原admission/launcher/campaign/joint；C19当前闭环见20项ACCEPTANCE_VERDICTS.json。
- 历史引用：C6四采集四控制、C8原12样本+C10只读复核、C8 NORMAL_ORDER47条（含设备拷贝与最终drain）；未改名C19 PASS。
- C15旧native由C16只读解码：producer/checker不同，原件保留；C19另外实际采集15task并绑定层，身份分开。
- 其他特性/拓扑未在本轮重审，不从“主要剩Graph”推断全部通过；Base与Target4配置不混用。
- 新C19正常性能不重复无影响的C15/C17采集：改变仅post-LIFE元数据容器和Host准入分类，正常producer/production字节无相关变化；性能数据仍标原SHA。
