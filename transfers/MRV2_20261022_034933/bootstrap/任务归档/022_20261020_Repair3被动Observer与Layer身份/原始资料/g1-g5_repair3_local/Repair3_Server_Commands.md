# Repair3 A3 rerun — exact commands and stop rules

本文件是计划，不是设备执行结果。候选未发布。先 independent review，再由 owner 授权普通发布；服务器 clean fetch 后才运行。禁止本地包替代 GitHub source 身份，禁止偷偷改 capture sizes。所有命令在 bash 中执行，每项退出码独立保留。

## P0 — 必填路径与 exact source

以下四个路径由服务器 Agent 从实际部署/旧 command ledger 解析，不猜 Python/native 环境；必须指向新 clean checkout 和现有已审核 fixture manifest。不要创建假的模型路径。

```bash
export REPAIR3_REPO=/absolute/path/to/new-clean-vllm-ascend
export REPAIR3_VLLM=/absolute/path/to/pinned-clean-vllm
export REPAIR3_PYTHON=/absolute/path/to/approved/python
export REPAIR3_FIXTURE=/absolute/path/to/original/inputs/fixture_manifest.json
export REPAIR3_OUT=/absolute/path/to/new-empty-artifact-directory
export REPAIR3_RUN_ID=2026xxxxTxxxxxxZ_10cbf4c0
export REPAIR3_ATTEMPT=01
export REPAIR3_SHA=10cbf4c014fc6cc48a6fea611bb605cecdd54cfd
```

`REPAIR3_OUT`须不存在；`mkdir`失败就停止，不能覆盖旧证据。

```bash
set -euo pipefail
cd "$REPAIR3_REPO"
test "$(git rev-parse HEAD)" = "$REPAIR3_SHA"
test "$(git rev-parse HEAD^{tree})" = 28dddd6d1fc19e67270ee71b7b9e7fcd410ab3c9
test -z "$(git status --porcelain --untracked-files=all)"
test "$(git -C "$REPAIR3_VLLM" rev-parse HEAD)" = 84030bbe3d74d99bad477a3d2e37a973ccd8865c
test "$(git -C "$REPAIR3_VLLM" rev-parse HEAD^{tree})" = f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
test -z "$(git -C "$REPAIR3_VLLM" status --porcelain --untracked-files=all)"
test "$(sha256sum "$REPAIR3_FIXTURE" | cut -d ' ' -f1)" = 1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4
test "$(sha256sum tools/p7x_graph_repair2.py | cut -d ' ' -f1)" = 7e6f2e5984430bc5231511960da2fdc9b073ddc58cfed8bfaed796498b70660d
mkdir "$REPAIR3_OUT"
mkdir "$REPAIR3_OUT/inputs" "$REPAIR3_OUT/runtime-recipes" "$REPAIR3_OUT/analysis" "$REPAIR3_OUT/traces"
cp "$REPAIR3_FIXTURE" "$REPAIR3_OUT/inputs/fixture_manifest.json"
```

保存实际执行的 runtime env脚本、sitecustomize、overlay构建脚本、diagnostic wrapper 到 runtime-recipes/（仅文本，勿带token/native环境）。沿用 repair2 已审核 MRV2 overlay 的构建规则，但重新以新SHA生成；不能复用旧Python .py缓存。记录Python/CANN/torch/torch_npu/vLLM版本、每个import `__file__`和sha256、native donor版本、device UUID/rank和空闲资源。`PYTHONPATH`必须由该已审核环境配方给出，不能在这里猜一个不含native环境的路径。driver会再校验fixture各文件实际hash。

检查实际 runner=NPUModelRunner、speculator=AscendDSparkSpeculator、method=dspark、K/query=7、sample_from_anchor=true、single STANDARD dense FIA；A3 TP/DP/PP/PCP/DCP=1，其余async/prefix/SP/DSA-CP/FlashComm关闭。资源不足记RESOURCE_BLOCKED，不记expected Gate。

## 请求准备与统一 launcher

```bash
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py make-requests --target-model /mnt/share/wql/Qwen3-8B --profile smoke --output "$REPAIR3_OUT/inputs/smoke.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py make-requests --target-model /mnt/share/wql/Qwen3-8B --profile combined --output "$REPAIR3_OUT/inputs/combined.json"
```

combined在一个engine里先1/2/4 smoke，再32、1024、1025、1151、1152、1153、2049、32 token刺激。必须按actual H/E/S/V判覆盖，不根据prompt长度补造exact。

```bash
run_repair3_case() {
  local case_id="$1" driver_mode="$2" profile="$3"
  shift 3
  "$REPAIR3_PYTHON" tools/p7x_graph_repair2.py launch \
    --run-id "$REPAIR3_RUN_ID" --case-id "$case_id" --mode "$driver_mode" \
    --attempt "$REPAIR3_ATTEMPT" --timeout 1800 \
    --output "$REPAIR3_OUT/${case_id}-launcher" -- \
    "$REPAIR3_PYTHON" tools/p7x_graph_repair2.py run \
    --case "$driver_mode" --case-id "$case_id" --run-id "$REPAIR3_RUN_ID" \
    --attempt "$REPAIR3_ATTEMPT" --expected-sha "$REPAIR3_SHA" \
    --vllm-repo "$REPAIR3_VLLM" --fixture-manifest "$REPAIR3_FIXTURE" \
    --target-model /mnt/share/wql/Qwen3-8B --draft-model /mnt/share/dspark_qwen3_8b_block7 \
    --requests "$REPAIR3_OUT/inputs/${profile}.json" --output "$REPAIR3_OUT/$case_id" "$@"
}
```

launcher身份在模型启动前落盘；SIGSEGV child returncode=-11/signal=11，shell139，不伪造campaign。Host monotonic仅进程内时钟。独立工具输出和真实子进程exit不得被echo/tee覆盖。每个case执行后先审核结果再继续：

```bash
run_repair3_case A0 A0 smoke
run_repair3_case A1 A1 smoke
run_repair3_case B0 B smoke
run_repair3_case B1 B combined
run_repair3_case O0 B-observer-off smoke
```

A1 driver只有捕获到预期GRAPH_FROZEN才expected；检查campaign exception/callsite，不将任意启动错误算成功。A0无provider/session。B0/B1 provider存在且bound/publish真实到达，observer-on；O0保留experimental1但observe0，不能experimental0。固定图配置`FULL_DECODE_ONLY`/actualFULL/capture[7,14,28]不变；max_model_len4096、capacity1151是两个不同概念。

## B0/B1严格判定

```bash
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py check "$REPAIR3_OUT/B0/campaign.json" --output "$REPAIR3_OUT/analysis/B0-check.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py analyze "$REPAIR3_OUT/B0/campaign.json" --output "$REPAIR3_OUT/analysis/B0-analysis.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py check "$REPAIR3_OUT/B1/campaign.json" --output "$REPAIR3_OUT/analysis/B1-check.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py analyze "$REPAIR3_OUT/B1/campaign.json" --output "$REPAIR3_OUT/analysis/B1-analysis.json"
```

check exit2可以是OPEN或INVALID，必须读取四namespace；不能把它改成shell PASS。无campaign时不要用empty JSON顶替，保留partial/progress/launcher。B0要求实际capture/bound/replay/update的(1,7)/(2,14)/(4,28)，预期层集来自spec.draft_attn_layer_names、非null、无缺层错层重复task/layer、同generation/source/backing。不能硬编码5次UPDATE总量。nativequery零是新source合同，A3不崩是待检验结果。TASK_BINDING/PHYSICAL_READ/COMPLETION不因Host check PASS升级。

B1要求runtime oracle至少S=0和S>0、非block-end、变化active/padded rows、多generation。未精确触达E=1024等时标NOT_REACHED；允许据真实观察设计下一轮fixture，但不能把期待值改成观察值。出现source shortage、identity mismatch、alias、Gate错误，停止依赖该路径的后续case并保留first divergence。

## G4短/长分列

```bash
run_repair3_case G4-A0-short A0 smoke --target-probe
run_repair3_case G4-B-short B smoke --target-probe
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py compare-probes "$REPAIR3_OUT/G4-A0-short/target-boundary.json" "$REPAIR3_OUT/G4-B-short/target-boundary.json" --output "$REPAIR3_OUT/analysis/G4-short.json"
run_repair3_case G4-A0-long A0 combined --target-probe
run_repair3_case G4-B-long B combined --target-probe
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py compare-probes "$REPAIR3_OUT/G4-A0-long/target-boundary.json" "$REPAIR3_OUT/G4-B-long/target-boundary.json" --output "$REPAIR3_OUT/analysis/G4-long.json"
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py analyze "$REPAIR3_OUT/G4-B-long/campaign.json" --output "$REPAIR3_OUT/analysis/G4-long-boundaries.json"
```

所有.pt须留在对应target-boundary.json旁边。完整有序样本/层集合/shape/dtype/有限值/源hash/数值都检查，重复hash不覆盖。不对齐时FAIL_ALIGNMENT/OPEN，不说明Window数学一定错。atol=rtol=0仅identical hidden input的head诊断。cross-process不要求数字ptr相等；same-process canonical identity由live validator验证。长case未实际S>0不得宣称long G4。probe含D2H，NOT_PERFORMANCE_REPRESENTATIVE。

FULL_TARGET/KV fixture当前**未实现**。禁止将head-only PASS改为FULL_TARGET PASS；需要Target实际token/positions/query/request layout与KV内容/版本/phase同态，再固定dtype容差。本轮无安全控制seam就输出FIXTURE_REQUIRED，不修改scheduler/owner。

## T0独立能力探测与有界采集

T0 help发现不依赖B0成功。采集仅在P0/A0通过、设备和最小O0路径可用时运行；若B0失败仍可独立检查O0，不能拿它覆盖B0失败。

```bash
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py trace-probe --output "$REPAIR3_OUT/traces/trace_probe.json"
msprof --help
```

repair2真实帮助包含`--application/--output/--runtime-api/--task-time/--export/--summary-format/--type`。先核对本机help；不存在就CAPABILITY_UNVERIFIED，不替换为未经核对的选项。最小采集命令（路径不含空格；有空格须正确shell quoting）：

```bash
"$REPAIR3_PYTHON" tools/p7x_graph_repair2.py launch \
 --run-id "$REPAIR3_RUN_ID" --case-id T0 --mode B-observer-off --attempt "$REPAIR3_ATTEMPT" \
 --timeout 1800 --output "$REPAIR3_OUT/T0-launcher" -- \
 msprof --output="$REPAIR3_OUT/traces/msprof" --runtime-api=on --task-time=on --export=on --type=text --summary-format=csv \
 --application="$REPAIR3_PYTHON $REPAIR3_REPO/tools/p7x_graph_repair2.py run --case B-observer-off --case-id T0 --run-id $REPAIR3_RUN_ID --attempt $REPAIR3_ATTEMPT --expected-sha $REPAIR3_SHA --vllm-repo $REPAIR3_VLLM --fixture-manifest $REPAIR3_FIXTURE --target-model /mnt/share/wql/Qwen3-8B --draft-model /mnt/share/dspark_qwen3_8b_block7 --requests $REPAIR3_OUT/inputs/smoke.json --output $REPAIR3_OUT/T0"
```

区分profiler wrapper退出与被测进程真实status，解析其stderr和campaign；两者任一缺失就OPEN。若导出自动失败，保留采集目录与错误，按本机help可用的export模式单独执行/保存exit，不编造命令。

导出所需字段：device/process/task/stream/correlation IDs、task create/update/launch/completion、descriptor与真实operand地址/length关联。Host id(handle/event)非设备ID。`Memory/MemoryAccess`指标**不等于**physical block read-set。列installed/help/capture/export-fields/sufficient五阶段；每个缺口提交确切验收问题，不重引入unsafe event query。

## G2、Abort、R0

G2复用B1-analysis全序列候选。只有同run/engine/provider/descriptor/backing且generation/epoch递增，A与A′ table/exact/upper和source-lineage一致，B不同才HOST_CANDIDATE。没有候选或scan_complete=false就OPEN。即使Host候选通过，需task/stream trace关联replay/update/rewrite，才能设备裁决；不可重写活跃allocator伪造A′。

Abort无安全的in-flight注入/观测seam，当前NOT_RUN / FIXTURE_REQUIRED。不要用kill进程当无early-overwrite证明，或用Host假event当device completion。只在owner确认具体seam后新增case，本轮不自动执行。

R0保存：新source/import identity，device/topology，fixture hashes，完整command+exit ledger，各case launcher/progress/campaign/partial/原stderr，checker四namespace，原始trace，runtime文本配方，target-boundary与引用.pt。空数据不是功能PASS。使用交付的`package_repair3_return.py`生成review/raw两个包，raw数字结论明确RAW_REQUIRED；最终ZIP固定后在包外计算DOWNLOAD_MANIFEST。上传接收后再次核对bytes/hash/CRC/member-hash，才RECEIVED_VERIFIED。本机产物校验不等于用户已收到。

停止规则：不自动重试native crash；保存first divergence。P0 identity/fixture错误阻止所有模型测试；B0失败阻止B1/G4-B/G2，允许独立T0 help/O0资源许可诊断；T0失败不改功能路径；G4不对齐不能删样本凑PASS。全程无Batch A、性能测量或public Graph enable。
