# C19实际数值样本的小型CPU复算

运行`python3 recompute.py`（普通Python，不用-O；无需torch、NPU或pickle）。此目录来自C19真实NUMERIC_SENTINEL三样本A/B/A′，不是构造的合成答案。INDEX记录producer完整SHA、原始sample manifest/hash及原joint哈希。

脚本检查raw/chunk哈希、dtype/字节数/shape、int32 input_ids与int64 positions、graph/reference输入一致、finite、原始零容差输出相等，以及A/B可区分、A′恢复。生成的recompute-result.json是服务器自检，用户接收后仍需自行运行；不标作用户已验证。

该小包有意省略完整KV前后态和全部metadata，不证明oracle调用独立性、完整12矩阵、Target、正常生命周期或physical read。完整判定需服务器原始producer/launcher/plan/storage/joint；这里不是用相同hash替代完整验收。
