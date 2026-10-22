# C7 dtype 修复与旧设备产物复核

producer_commit：`1c920c3669b76f301ff9472650ceb0e842ccf03c`（C6）。checker_commit：`810b85a5b1d494fe83a686951ef1b6ecc5288c6d`（C7）。result_scope：旧设备产物的新 checker 复核，C7 尚未运行 NPU。

原始实验：`/mnt/wenqing/mrv2_graph_server_dev/20261022T0640Z_C2_recovery/C6_prepare_04b/NUMERIC_SENTINEL/`，launcher 与 case-plan 仍为原件。旧 `numeric-joint.json` 的 `evidence_errors=[tensor dtype mismatch]` 保留。

固定 vLLM `vllm/v1/worker/gpu/input_batch.py:31` 明确创建 int32 input_ids、int64 positions。三份原始样本的 inputs/reference_inputs 均遵从该定义。C6 checker 的 `validate_sample` 对 input_ids 误要求 int64；Host capture fixture 也错误创建 int64，导致此前测试未捕获。

C7 只改 input_ids 的精确 dtype 判据，未 cast、未改生产输入、未改其他字段或数值容差。修正 Host fixture，新增两臂等值但同为错误 int64 的反例。`C7_dtype_host_tests.log`：31 passed。

完整联合复核产物：`reports/reanalysis_C7_dtype_01/numeric-joint.json`。新结果继续为 INVALID_EVIDENCE，原因已推进到 query/causal mismatch；数值验收未通过。原始三样本均存在，不能用 joint.samples=[] 否定原件存在。

后续发现：实际五层 causal=false；固定 Draft config 的五层均为 full_attention，固定 vLLM `_dflash_layer_causal` 对 full_attention 返回 false。下一轮仅在该冻结 DSpark 合同范围内核实并修正 checker；所有损坏证据拒绝条件继续保留。
