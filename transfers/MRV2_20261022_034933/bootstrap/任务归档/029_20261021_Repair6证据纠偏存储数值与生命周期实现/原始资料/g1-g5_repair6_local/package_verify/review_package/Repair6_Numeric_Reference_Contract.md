# 真实MRV2连续数值参考合同

DSpark.capture → 默认关闭instance-owned DraftGraphOutputReferences → pinned DFlash._run_model真实模型tensor → 每个实际FULL token bucket保留引用 → freeze真实inventory。
必须在LLM初始化/capture前安装；启动后纯工具无法取回已经离开作用域的hidden。manager返回None，greedy也不能假设draft_logits已写，因此最小production seam必要。默认关闭不分配sink/clone/event、不改变返回或Gate。开启保留引用可能影响allocator lifetime，明确为诊断capture。

ContinuousReference只允许独立empty-scheduler fixture：
1. query前、context KV已产生，保存全部canonical read/write Draft blocks、input_ids/positions；诊断同步在replay前。
2. 真实manager→pinned replay(None)→consumer→UPDATE；live generation仍存在。
3. 完成边界后读取本代sink hidden，保存Graph post-KV；检查同代submittedcarrier，不能再次consume_metadata。
4. 独立canonical Full/exact/valid计算 S=floor(max(E-1024,0)/128)*128、V=E-S和列，Draft padding不借Target padded；验证production Window。
5. 仅在独立诊断恢复全部相关Draft query pre-KV，用相同模型/输入/位置/query/slot与独立Window metadata调用真实_run_model(mode=NONE)，不切采样路线；finally恢复Graph post-KV。Target不swap、不restore。
6. 保存完整active hidden及padding范围、pre/postKV、canonical lineage、generation/epoch/descriptor，durable后下一代才能覆盖。

新增hidden合同预声明atol=rtol=0、FP16/BF16严格一致；非零差异NUMERIC_MISMATCH，不按设备结果放宽。原私有FIA0.016不变。
Target4冻结plan驱动A/B/A_prime、短/长、非对齐、mixed、1/2/4、3active4padded、切桶回旧桶。
Host实际pinned Python forward调用与CPU模型、真实builder/P3/P6 metadata/retire已贯通；native Graph replay/FIA/stream由明确替身，NPU NOT_RUN。
工具比较actual与本代/前代独立reference及可区分性，但范围是DIAGNOSTIC_SERIALIZED_BACKBONE_REFERENCE，不是采样算法完整新oracle，不是normal-overlap时序证明；不要求Window ON等于full-context OFF。

尚未实现：正常无逐代同步、完整受控连续hidden A/B/A_prime eager-reference producer。当前每桶输出可在下代覆写，要无扰动保存完整前/后KV并对照需新的隔离/多代输出合同及task语义。NormalOrderProbe只增加有界token device copy与末尾drain，不能伪称上述producer。此缺口阻塞全部G5 closure，不阻塞已实现串行数值实验。
