# C10 真实 padding 合同与完整数值复核

本轮假设：完整矩阵第11样本的拒绝来自检查器混淆输入 query offset 与 FIA padded query 长度。

## 首因与修复

C8 `2c550f267484360802578f340429f95f95299e33` 真实 `NUMERIC_TARGET4` 已保存12样本。原 `numeric-joint.json` 在前10样本接受后报 `query layout mismatch`；原 runner 返回4，原文件不改。

`vllm_ascend/worker/v2/spec_decode/dflash/speculator.py` 的输入内核将 padding offset 填为 `num_reqs * num_query_per_req`；`_update_draft_attn_metadata` 则明确为 FIA TND 构建全部 padded 行 query 长度。真实样本10（active3/padded4）：输入为 `[0,7,14,21,21]`，5个Draft层的 FIA query 均为 `[7,14,21,28]`。旧 Host fake 将输入也写成单调递增到28，掩盖了错误。

C10 `c8f9a4bbddf33bc4cc02fdfe39f6aad75c6cad4a` 仅修输入 offset 精确合同，并修 Host fixture；FIA metadata、绝对 positions、Full canonical slot、KV前后态、层集合、数值容差均保留。没有修改生产输入、cast或全局替换。

## 验证与范围

- `C10_query_host_tests.log`：26项通过，包含双臂都写错误 padding offset 的拒绝反例。
- `reanalysis_C10_full_01/real_padding_regression.json`：真实C8样本旧checker拒绝、新checker接受；双臂错误input padding与双臂错误FIA padding分别被拒绝。
- `reanalysis_C10_full_01/numeric-joint.json`：`PASS_DIAGNOSTIC_CONTINUOUS_REFERENCE`，完整12样本，`aba=PASS_SCOPED`；BF16有效输出逐元素一致，max_abs/max_rel均0，KV前后对应检查通过。
- `reanalysis_C10_full_01/execution.json`：实际argv、producer/checker SHA、原joint哈希和只读复核范围；联合检查重新读取完整producer/artifact/launcher/plan。

以上是 C8 设备产物经 C10 检查器的独立复核，不是 C10 已执行新NPU。参考使用真实模型独立 eager backbone 调用，输入、独立Window table/length及KV前态受检；不是把同一输出改名。连续参考显式同步、保存并恢复KV，因此不证明正常异步 UPDATE 的生效代际或 backing 可复用完成。

原始证据根：`/mnt/wenqing/mrv2_graph_server_dev/20261022T0640Z_C2_recovery/C8_prepare_01/NUMERIC_TARGET4`。旧失败与所有 chunks 保留。
