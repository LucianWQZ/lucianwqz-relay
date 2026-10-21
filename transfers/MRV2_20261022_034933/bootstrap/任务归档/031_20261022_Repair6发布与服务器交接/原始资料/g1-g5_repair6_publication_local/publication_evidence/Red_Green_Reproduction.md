# 可重复 RED/GREEN（不切换原 checkout）

原始先红后绿记录见logs/repair6_red_*.log。额外用git archive隔离复核baseline：只覆盖新回归测试/helper，没有覆盖production或工具；完整命令/exit/测试文件hash见red_repro/Reproduction.json。

```bash
python red_repro/reproduce.py --repo /absolute/vllm-ascend --vllm /absolute/vllm --python /absolute/vllm-ascend/.venv/bin/python --revision febc43be3309f6d2cd87f9332cb7e031ebaad001 --output /new/isolated-red
python red_repro/reproduce.py --repo /absolute/vllm-ascend --vllm /absolute/vllm --python /absolute/vllm-ascend/.venv/bin/python --revision fd0716c59562f64262672de12e4ae26259908d0b --output /new/isolated-green
```

测试集：F1五个真实CPU tensor writer/reader+外部关联；F4真实CLI；F5真实Target producer前缀；F6实际prefix预算；F2/F3真实pinned forward故障；capture真实Python入口。Native NPU/模型计算为声明的CPU替身，非设备验证。
最终代码的完整GREEN与精确argv在logs/regression.log（1007 passed），测试文件hash在Validation.json。初始capture harness `_draft_topk`错误仅是测试准备错误，不能作为生产RED。
