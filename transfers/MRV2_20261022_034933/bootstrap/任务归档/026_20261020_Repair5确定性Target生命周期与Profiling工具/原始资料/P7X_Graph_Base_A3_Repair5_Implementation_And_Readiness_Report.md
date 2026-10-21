# Repair5：独立证据复核、工具契约修复与集中设备验证交付

本报告描述 **Repair5 本地提交**，不是 Repair4 设备运行报告，也不是新 SHA 的设备验收。

| 项目 | 结论 |
|---|---|
| 本地实现 | 工具契约已修复；受控完整 Target、私有 FIA A/B/A′、真实 MRV2 诊断生命周期及隔离 abort producer 已实现并做 Host 契约验证 |
| 发布 | NOT_PUBLISHED；未 push、PR、merge、tag |
| 新 SHA NPU | NOT_RUN |
| 发布后集中实验 | YES，限本文已实现的 scoped cases；需先独立网络恢复验收 |
| 全部 G1–G5 关闭 | NO |
| Public Graph | STILL_FROZEN；本轮未改 `vllm_ascend/` production 文件 |
| 主要缺口 | Target 四请求 bucket 缺失；真实 MRV2 token A/B 判别可能不足；task 内部 operand、physical read、UPDATE 生效代际、正常无额外同步的复用安全未证明 |

## 1. Git 与输入身份

```json
{
  "baseline": {
    "sha": "08c94a99032c47e2608b976c25065adbbc8dea09",
    "tree": "7d58b3414a9911662604634198c32e98094b15cf"
  },
  "final": {
    "branch": "fix/p7x-graph-base-a3-repair5",
    "sha": "3bdc413aa9826e4c199f5d96125e71db2c343420",
    "tree": "e72a3ef82fbd1cfd70ea20010c2eeb0b08c50a62",
    "parent": "a8210d4f725cdce7cf7ee9840a71d8feca3ce48d",
    "status": ""
  },
  "vllm": {
    "sha": "84030bbe3d74d99bad477a3d2e37a973ccd8865c",
    "tree": "f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee",
    "status": ""
  },
  "changed_file_sha256": {
    "tests/ut/spec_decode/test_graph_repair4_fixture.py": "7580f60d939125215cb89da12a6df3058fcd9f77e2ebc82f3daa68fed2971fc8",
    "tests/ut/spec_decode/test_graph_repair4_target.py": "140f5d7f34ea26496b2df683e979940379b513445bc8484e65266f370cb55c0f",
    "tests/ut/spec_decode/test_graph_repair5_cli.py": "74c126b278df44126105fbc1c866d68983590dbccd5b18c3d46c9160ad027b65",
    "tests/ut/spec_decode/test_graph_repair5_contracts.py": "1920d7a33553d7f479804c3bf1150c86ee3f6ef868d5bea38ae4659774fa61f7",
    "tests/ut/spec_decode/test_graph_repair5_producers.py": "e5c9fc83292552f44313c9f4cc3817c85f0ae005a3104de1b63e6698c2babfd9",
    "tools/p7x_graph_repair2.py": "ab6954c766d16c836cfea45a6ca8fe82e703194b63f0eb6bdfe6aa51273ed5eb",
    "tools/p7x_graph_repair4_acceptance.py": "6386ce1c2a21b249a0dd62e088a1c5a11e25c734500d03363d83db65bd5e8ead",
    "tools/p7x_graph_repair4_fixture.py": "4033947f76f36b6f224a4fc048a4d7aaff8e8ff0ac036c2d48bce3cd86a7baf6",
    "tools/p7x_graph_repair4_target.py": "0390337e1c33976835596ee910e9a1847d3615ef4870ec2195947712d266dc7f",
    "tools/p7x_graph_repair5.py": "e1675bd5646684dfa77327cc0eeac4c46baad432176ba6af1a5dadf49dab68c4",
    "tools/p7x_graph_repair5_campaign.py": "57a8627a3150b4f995eaa08dbee64eafee0df0e07e4fbb14362dd8ea1864228f",
    "tools/p7x_graph_repair5_lifecycle.py": "f5904377a3ac2191401560159c882fb373452a77fc9d26e888aa11a13f57368f",
    "tools/p7x_graph_repair5_target.py": "02c7714ca52edbd0ad398bbe25d72dc2224267013ebf0bd6b6f3a9520b109149"
  },
  "tool_sha256": {
    "tools/p7x_graph_g1_g5.py": "8c29e83d396bb06eb718e67c65aeb2085a18efd182cbd311f2b7da9defb2f64c",
    "tools/p7x_graph_repair2.py": "ab6954c766d16c836cfea45a6ca8fe82e703194b63f0eb6bdfe6aa51273ed5eb",
    "tools/p7x_graph_repair4_acceptance.py": "6386ce1c2a21b249a0dd62e088a1c5a11e25c734500d03363d83db65bd5e8ead",
    "tools/p7x_graph_repair4_campaign.py": "7889b2f6eccbd9490770789d47575db19c4734598386c897e8f79c9fb491a3e6",
    "tools/p7x_graph_repair4_fixture.py": "4033947f76f36b6f224a4fc048a4d7aaff8e8ff0ac036c2d48bce3cd86a7baf6",
    "tools/p7x_graph_repair4_target.py": "0390337e1c33976835596ee910e9a1847d3615ef4870ec2195947712d266dc7f",
    "tools/p7x_graph_repair5.py": "e1675bd5646684dfa77327cc0eeac4c46baad432176ba6af1a5dadf49dab68c4",
    "tools/p7x_graph_repair5_campaign.py": "57a8627a3150b4f995eaa08dbee64eafee0df0e07e4fbb14362dd8ea1864228f",
    "tools/p7x_graph_repair5_lifecycle.py": "f5904377a3ac2191401560159c882fb373452a77fc9d26e888aa11a13f57368f",
    "tools/p7x_graph_repair5_target.py": "02c7714ca52edbd0ad398bbe25d72dc2224267013ebf0bd6b6f3a9520b109149"
  },
  "signoff": "fix(tools): align graph microfixture with DSpark anchor K\n\nSigned-off-by: Lucian <2207456347@qq.com>",
  "cryptographic_signature": "N",
  "commits": [
    "a8210d4f725cdce7cf7ee9840a71d8feca3ce48d 08c94a99032c47e2608b976c25065adbbc8dea09 fix(spec-decode): prepare repair5 deterministic graph validation",
    "3bdc413aa9826e4c199f5d96125e71db2c343420 a8210d4f725cdce7cf7ee9840a71d8feca3ce48d fix(tools): align graph microfixture with DSpark anchor K"
  ],
  "publication": "NOT_PUBLISHED",
  "pr_created": false
}
```

新分支是 `fix/p7x-graph-base-a3-repair5`。独立 commit 有 Signed-off-by；密码学签名状态为 `N`（未签名），两者不混淆。没有改写 Repair4 history。两仓最终工作区 clean，pinned vLLM 零 diff。

输入根目录：
`/Users/wenqingzhang/Desktop/中转/private-file-relay/transfers/2026-10-20/MRV2_P7X_A3_Repair4/20261020T035634Z_08c94a99/return`

读取并保留原始 Server Final Report、NEXT_LOCAL_CODEX_INPUT、DOWNLOAD_MANIFEST、RECEIVER_VERIFY、SHARDING/receiver 日志、review/raw 包和 raw reports/cases/progress/traces/inputs。另核对本地 Repair4 implementation/publication/handoff 及 G5 源码说明。服务器原始输入只读，恢复/重判写到独立临时目录，最终可审计内容在本交付 ZIP 中。

## 2. 本地接收端独立验证

先读 receiver 脚本，再用本地独立恢复程序依 manifest 顺序重组（不是引用服务器自检结果）。

| 包 | bytes | SHA256 | 成员文件 |
|---|---:|---|---:|
| review | 1460310 | `f87648717e4f6c7ca5a9c81fe14d091f2d21f7d81f5067ff854cf9610be89172` | 461 |
| raw | 362048588 | `03d875bc0fcb3ab461976b146a029a263111e1786d6041f6959919a9dd7802c5` | 816 |

4 分片按 manifest order 0–3 校验，前三片各 94371840 bytes，末片 78933068 bytes；逐片 hash、整包 hash、ZIP CRC、成员 bytes/hash、JSON、路径安全全部通过。335/382 是更早 Repair3 的数字，不套用到本轮。原始 fixture manifest bytes/hash 未改：
`1c485bc43a6e8f6d0d83c1dc6ebfd0fb9bb1f31a8ad9e498ef1d3e9d562e7cd4`。

`Receiver_Verification.json`、接收程序及原始成员索引纳入紧凑包。raw 原包不重复放入紧凑包。所有旧设备复算均标明 `device_execution_sha=08c94a99…`，并保存修复后 checker 文件 hash；不覆盖原 FAIL 文件。

## 3. Repair4 原始事实重判

### 3.1 source、fixture、运行范围

实际 import 路径含服务器 runtime overlay，不直接据路径判定“修改过源码”。逐字节比较 vLLM init、MRV2 runner、DSpark speculator、DFlash manager、characterization 5 个实际导入文件与精确 git blob，hash 全相符。该检查只覆盖列出的文件，不扩张到全部 site-packages。

原 fixture 保持 Qwen3-8B + dspark_qwen3_8b_block7，DSpark、K/query=7、sample_from_anchor=true、W=1024、block span=128、capacity=1151。capacity 不是 max_model_len。TP/DP/PP/PCP/DCP=1，single STANDARD dense FIA，FULL_DECODE_ONLY 的实际 FULL，Draft capture sizes=[7,14,28]。其余引擎参数仍由既有 `repair2.run_case` 构造及原始 manifest/requests 校验，不换近似模型或减 bucket。

### 3.2 B0/B1/B2 与 observer-off

- B0：真实 replay 三 bucket `(1,7)/(2,14)/(4,28)`，21 generations、15 capture operators、105 update operators、21 retirement、21 `OUTPUT_NOT_CAPTURED`。合法 None 没有再变成 hash 异常。
- 这些是旧 SHA 实际覆盖，仍不等于完成 device update 或证明 backing 可复用。
- B1：**11 组**输出，请求数 `[1,2,4,1,1,1,1,1,1,1,1]`，不能写成仅三组；75 个 active-row 观测，实际 E=12…2075，14 个 S>0。
- B2：4 组 `[2,3,4,1]`，32 个 active-row 观测，E=39…2075，10 个 S>0。
- 所有 S/V 从 runtime canonical exact 重新算 `S=floor(max(E-W,0)/B)*B, V=E-S`，未以 prompt 长度代替 E。逐 generation/epoch/request/padded descriptor 的数值在 JSON 中完整保留。
- O0 是 provider **存在**、observer **关闭**，不是 CONFIG_OFF；O1 同样如此。不能将实验 flag=0 的 public rejection 当 observer-off Graph。

修复后官方 joint 对 20 份旧 campaign 重判：冻结 plan 内 **19 PASS**；额外 `O1-mixed` 请求关联可通过，但原 plan 无此 case，保持 `OPEN_NO_FROZEN_CASE_PLAN`。original verdict、campaign/request SHA、plan 来源、checker hash 均保留。这里只解决旧设备产物的文本/token-ID 工具合同，不是新代码 NPU PASS。

### 3.3 G4：全部 raw tensor，而非挑选相等样本

本地用 `torch.load(weights_only=True,map_location="cpu")` 读取 **128 个 .pt**：126 个 HEAD_ONLY tensor 文件和 2 个 G4F blocked 容器。逐样本表保留所有 65 个历史 ordinal 行、未配对项及全部 tensor SHA/index。

| 场景 | OFF/ON 样本数 | hidden 输入相等的历史 ordinal 对 | 对这些输入相等样本的 logits | 保留项 |
|---|---|---:|---|---|
| short | 21/21 | 21 | exact equal | 全部 |
| long1 | 12/12 | 12 | exact equal | 全部 |
| long2 | 14/14 | 4 | exact equal | 其余10对输入未对齐 |
| mixed | 18/14 | 2 | exact equal | 其余12对未对齐及4个无配对 |

原服务器 FAIL 不删除。以上 ordinal 对照仅用于复算历史 HEAD_ONLY 声明；原产物没有足够业务身份和 KV 前态，**hidden hash 相等不等于 FULL_TARGET 输入对齐**。不对齐输出差异不是已证实 production 数值缺陷。每行保存 raw path/SHA、dtype/shape、atol/rtol=0、max_abs/relative error、finite、原始裁决和本地裁决；KV pre/post 标 NOT_CAPTURED。紧凑包附最小原始 tensor 切片及来源 hash，不伪称完整 raw。

### 3.4 G4F/C2/trace

- 两个 G4F 容器各 8 条 BLOCKED：`EvidenceError: target layer inventory incomplete`；各另 skipped=4。请求 joint PASS 不证明 FULL_TARGET producer 成功。
- C2 在有效 device fixture 记录前因为 `torch_npu.npu.get_cann_version` 不存在而失败；属于已确认工具 API 缺陷，不是 NPU 算法 PASS，也不以“环境问题”逃避修复。
- 8 个 trace CSV、36 个 SQLite DB 实际检查列名、行数及非空计数。T0/T1 的 op_summary 各13676行，task_time 各23215行，TaskID/StreamID/shape/format/timing 有值。`COMPUTE_TASK_INFO.attrInfo=9` 经 STRING_IDS 解析是空字符串，不是 operand 明细。没有 canonical block ID、物理 read-set、Window generation 关联。
- 不安排同样的 profiler 命令盲目重跑。task operand/physical read 需要额外厂商能力或明确验收决策，保持 OPEN。

## 4. Finding 裁决与 RED/GREEN

| ID | 裁决 | 本地依据 | 动作 / 边界 |
|---|---|---|---|
| R5-01 | ACCEPTED | 旧代码两处引用 npu.get_cann_version；真实 API 位于 utils | 两处一起改；统一无模型 capability preflight，原生接口不可 introspect 单列 PROVENANCE_LIMITED |
| R5-02 | ACCEPTED | registry/config 同时含 Target 与 Draft；集合全等错误 | 根据 runner.model.modules() 对象归属恢复 Target；与真实捕获 K/V/task/metadata 完整映射 |
| R5-03 | ACCEPTED | token-ID 是 pinned 合法输入；旧 joint 只接受文本 | 严格解析并核实际使用 token；不放宽 source/PID/argv/rawbytes/16token 合同 |
| R5-04 | ACCEPTED | 自然 speculative 轨迹序号不构成业务身份 | 新 producer 预先声明逻辑身份；原历史 ordinal 保留为弱证据而非悄悄重配 |
| R5-05 | PARTIALLY_ACCEPTED | 需要真实 Target forward，非 LM head；当前 Target capture 无四请求 bucket | 受控完整 producer+checker 实现；10个可用状态及1个显式 BLOCKED，不改 capture 配置 |
| R5-06 | PARTIALLY_ACCEPTED | 私有 FIA 不等于真实 MRV2 | 两条 producer 分开；私有8控制含仅窗外扰动；真实 propose 采集token ABA，但无可判别结果保持OPEN |
| R5-07 | PARTIALLY_ACCEPTED | 缺设备完成事实不等于已证实调度缺陷 | 真实MRV2实例诊断普通Event/abort入口；不改production顺序；正常无同步路径仍UNPROVEN |
| “未对齐 logits 差异证明 Window 破坏 Target” | REJECTED | long2/mixed 全样本输入未对齐，KV前态也缺失 | 不据此修改production；原FAIL照存，新解释独立输出 |

精确 baseline blob RED 命令：

```text
VLLM_VERSION=0.29.0 PYTHONPATH=../vllm .venv/bin/python red_exact.py
3 failed, 5 deselected
test_post4_version_api_has_no_npu_get_cann_version
test_shared_registry_inventory_uses_actual_model_objects
test_official_joint_accepts_exact_token_id_inputs
```

脚本从 `git show 08c94a99:tools/...` 载入旧工具而保留新反例，未把错误 API 补到 mock 上。旧实现分别触发 AttributeError、Target inventory incomplete、合法 token-ID 输入 INVALID_EVIDENCE。完整栈在 red-exact-final.log。当前代码对应 focused 40 passed；最终 CLI 又执行10 passed。初期测试调试错误/失败路径名日志也保留，不拿它们算预期 RED。

最后一次交叉审计另发现旧私有 FIA fingerprint 使用 `static_k=QUERY_WIDTH-1=6`，不符合本 Base 的 DSpark anchor K=7。真实 ProductionBinding 构造加断言先得到 `AssertionError: 6 == 7`（red-private-k.log），再改为 static_k=QUERY_WIDTH=7，并把 sample_from_anchor=true 写入 fixture manifest。此为独立第二个本地提交，不 amend 第一个。私有 fixture 仍没有真实模型采样；修正身份不能抹去 scope 限制。

## 5. 真实调用链、关键设计与逐文件变更

| File | Change |
|---|---|
| `tests/ut/spec_decode/test_graph_repair4_fixture.py` | 真实结构/producer→artifact→checker/negative regression |
| `tests/ut/spec_decode/test_graph_repair4_target.py` | 真实结构/producer→artifact→checker/negative regression |
| `tests/ut/spec_decode/test_graph_repair5_cli.py` | 真实结构/producer→artifact→checker/negative regression |
| `tests/ut/spec_decode/test_graph_repair5_contracts.py` | 真实结构/producer→artifact→checker/negative regression |
| `tests/ut/spec_decode/test_graph_repair5_producers.py` | 真实结构/producer→artifact→checker/negative regression |
| `tools/p7x_graph_repair2.py` | explicit diagnostic flags; pre-model capability; disposable Target/MRV2/LIFE entry; error quarantine |
| `tools/p7x_graph_repair4_acceptance.py` | strict text/token-ID official joint |
| `tools/p7x_graph_repair4_fixture.py` | CANN API + provenance + eight controlled private-FIA cases, window perturbation |
| `tools/p7x_graph_repair4_target.py` | actual model object inventory and existing full 22-field chain |
| `tools/p7x_graph_repair5.py` | actual no-model preflight/plan/comparison/lifecycle/ABA/abort CLI |
| `tools/p7x_graph_repair5_campaign.py` | bounded source-hashed request plan, official check/joint and dependencies |
| `tools/p7x_graph_repair5_lifecycle.py` | instance-owned diagnostic events/real scope retirement/child quarantine |
| `tools/p7x_graph_repair5_target.py` | deterministic full Target and MRV2 controlled producer, semantic pairing, logical KV checking |


### 5.1 inventory / FIA / capability

`target_inventory(runner)` 从 `runner.model.modules()` 对象身份与 static_forward_context 交集得到实际 Target 层，再核其在 kv_cache_config、attn_groups、draft 层集合中的归属。41/5/36 只用于本 fixture 解释，不是实现常量。KV sharing/重复 K/V owner 仍拒绝。捕获 tuple 的 22 项 schema、K/V 位置、handle/event 数量、每一 Target task 的对应关系继续检查，不依赖按名字排序。

概念 diff：

```python
# before: names = all registry layers; require set(names)==set(configured)
# after:
model_objects = {id(module) for module in runner.model.modules()}
# Target = registered attention objects belonging to the actual Target model.
# Require config/group coverage, no Draft intersection, and one-to-one captured KV/task ownership.
get_cann_version = torch_npu.utils.get_cann_version
```

真实生产 `AscendAttentionBackendImpl.full_graph_fia` 产生 tuple → LiveTargetAdapter._boundary 消费的测试保留，不手工拼一个自证23项 tuple。

### 5.2 FULL_TARGET：独占诊断 engine，不恢复半个活跃请求

入口 `repair2 run --repair5-controlled-target --repair5-controlled-mrv2`。
`ControlledTarget` 只接受 scheduler requests/running/waiting 为空；在初始化 capture 完成后、任何自然请求入队前执行，结束后该子进程退出，诊断内容不得流入正常请求。

- 从现有 Target FULL graph descriptor 选择，不造 bucket，不改 Graph manager，不换 graph-bound 地址。
- 真正调用 `ModelAclGraphManager.run_fullgraph`，记录其完整 forward hidden，并计算 logits；不是用 head 重算冒充完整前向。
- 输入 batch/ModelState/metadata builder 使用真实 Ascend 实现；token、position、query、padding、seq、table、slot 全声明。
- Target query width=K+1=8，Draft query width=7，严格分开。
- 所有相关 Target/Draft KV 在空 engine 中原位初始化为确定的 synthetic logical pre-KV。不是声称经过自然 prefill 的 KV，也不在活跃 allocator 上修改表。
- OFF/ON 使用不同 physical block placement，完整 `physical -> (logical_request,column)` 映射保留；拒绝重复 writer/错 request/不完整集合。
- 保存全部 declared read/write blocks（含 overhang、padding），每层每 K/V；其余全部块流式 digest 前后比较，不只采几个相等点。
- 各 checkpoint 上限512MiB，11个预声明状态全部记账。无法采集就是 BLOCKED/FAIL，不能用 skipped 充 PASS。
- OFF/ON 同一新SHA、同fixture、同逻辑前态比较。atol=rtol=0 沿用冻结 Target 合同，不事后放宽。

实际已有 Target inventory 为 `(1,8),(2,16)`，Draft 为 `(1,7),(2,14),(4,28)`。在保持 capture=[7,14,28] 时，Target `(4,32)` 不存在。因此 `three-active-four-padded` **CAPTURE_BUCKET_ABSENT**，不会 eager fallback。该项需要 owner 决定是否授权额外 Target capture bucket；本轮不改。

### 5.3 phase-aware write 合同

新审计发现，pinned DFlash prepare_inputs 本来就会在 Target forward **之后**重写共用 `BlockTables.slot_mappings` 为 Draft absolute query slots，Window OFF 也一样。因此跨整个 propose 强制 slot values 永远不变是错误 oracle。

本轮分开验证：

1. Target forward 的 canonical slots / mapped KV writes；
2. Draft 阶段的 canonical full query slots、absolute positions、query layout；
3. Draft 不替换 Target metadata root、不改变 Target input ids/positions/query；
4. Draft 后 Target 各层 KV 与 Target post-state 一致，未授权写集合不变。

不 clone canonical write、不同步替换 Target owner，不修改 Window read/write 数学。工具将基线 phase 转换和 Window 污染分开记账。

### 5.4 A/B/A′ 两条路径

私有 FIA fixture 使用真实 P3/P6 carrier/helper 与 backend capture/update，但不是 MRV2 model runner。八个控制：
`A, B, A_prime, short, nonaligned, outside_only, inside_only, A_restore`。
A/B 有独立可区分期望；A′恢复输入；窗外-only 页与窗内-only 页分开扰动。oracle 从 canonical 数据计算，不读被测 S/V 答案。FP16 rounded V 和独立 oracle 保持，冻结 atol=0.016，不改成0.008。Host量化预算不是实际FIA误差证明。

真实 MRV2 producer 在受控 Target 之后调用原 `spec.propose`，走真实 eager context prepare→P3/P6 bind→Graph→UPDATE→retire，保存全部 generation、epoch、backing、canonical lineage 和实际 draft token。
checker 验 S/E/V、table/length、bucket、A′输入和同backing、多代单调性。若 A/B greedy token 不可区分，返回 `OPEN_NONDISCRIMINATING_DRAFT_TOKENS`；本轮**未实现真实 MRV2 Draft hidden-state 的 Window 参考数值 oracle**，不能把私有FIA数值实验升级为它。

### 5.5 真实 MRV2 lifecycle / abort

默认不开。`--repair5-lifecycle` 仅作用于该 speculator/manager/graph 实例，预检查后安装，失败 rollback，结束 restore；不是 upstream/module-global monkeypatch。

真实顺序保持：

```text
scope acquire / stage / bind
→ original graph.replay
→ ordinary consumer event record
→ original CONSUMER + backend UPDATE submission
→ ordinary update event record
→ diagnostic wait both ordinary events
→ snapshot persistent draft_tokens
→ original proposal scope retirement
→ next proposal
```

同步发生在必要 UPDATE 提交之后，capture callback 无 I/O/query；没有恢复 ExternalEvent.query。普通Event是真实设备入口，但本地测试替代了native事件，尚不是设备completion证明。该诊断有额外同步，只能得到 `PASS_DIAGNOSTIC_SERIALIZED`，不能证明生产无额外同步重叠路径。

abort 四点：before_replay / after_replay / after_update / after_completion。独立child写partial后exit73，外部launcher核signal/timeout/source/PID/argv；不确定提交则整进程 quarantine，禁止下一proposal reuse。意外native异常exit74，不冒充预期abort。没有随机kill、sleep证明race，也没有引入生产全局同步/双缓冲。

## 6. G5 源码与证据边界

精确源码：DFlash manager `run_fullgraph` 先 `super().run_fullgraph(desc)`，随后 `update_full_graph_params`；backend `full_graph_fia` 捕获 ExternalEvent.wait/reset、task/FIA；`update_graph_params` 在 update_stream task_update_begin/FIA/task_update_end 后 `event.record(update_stream)`。

这能说明 Host 提交关系，不能仅按源码行号证明 UPDATE(N) 生效于 N 或 N+1。服务器 C2 在 API 查询失败，旧 T0/T1 没有 generation→task→completion 关联。故：

| 声明 | 本轮结论 | 下一步 |
|---|---|---|
| Python/operator operands | 旧SHA有记录，新SHA入口保留 | B0/B1/C2新SHA重跑 |
| task内部operand | OPEN / CAPABILITY_GAP | 厂商提供版本匹配task参数读取/trace能力 |
| 数值读取语义 | 私有oracle与真实producer本地已实现 | 设备C2及受控MRV2；区分scope |
| physical memory read-set | OPEN / ACCEPTANCE_DECISION_REQUIRED | 不能以窗外非干扰或msprof TaskID替代 |
| UPDATE有效代际 | UNPROVEN | 有判别力的A/B/A′设备结果+有效任务关联 |
| last consumer completion | 诊断普通Event入口已实现，设备未执行 | 验证事件确实覆盖所需stream/task |
| normal backing reuse | UNPROVEN | 不能拿诊断串行化PASS覆盖正常重叠 |

没有找到可诚实宣称适用于当前工具链的新 physical-read export。capability preflight 采当前安装API源码/签名，若原生不可introspect则null+原因；不伪造官方文档语义。后续需 CANN/torch_npu 团队给出可用task/operand关联机制，或owner明确改变验收标准；本轮不降级标准。

## 7. 本地验证账本

| Verification | Result | Log |
|---|---|---|
| exact baseline RED | 3 failed / 5 deselected, exit1 expected | red-exact-final.log |
| Repair5 focused | 40 passed, exit0 | repair5-final-focused.log |
| final campaign CLI after dependency additions | 10 passed, exit0 | final-cli.log |
| DSpark fingerprint K红测 | 1 failed, `6 != 7` | red-private-k.log |
| 最终K修复后的private fixture +全部Repair5 +Repair4 integration | 115 passed, exit0 | final-after-k.log |
| full spec_decode + attn_utils + attention_v1 + two BlockTable suites | 1148 passed / 13 skipped / 7 failed / 25 subtests, exit1 | final-regression.log |
| baseline VWN same host, git archive08c94 | 7 failed / 2 passed; same upstream Invalid attention backend for None | baseline-vwn.log |
| Ruff/format/8-tool targetedMypy/compile/diff | PASS | *-final.log |
| independently executable repository hooks | 12 PASS | hook-*.log |
| full pre-commit setup | ENVIRONMENT_BLOCKED: Go proxy TCP timeout | precommit-full.log |
| no-model capability on Mac | CORE_CAPABILITY_MISSING, exit2; no CPU fallback | host-capability.json |
| NPU model/Graph/task/completion | NOT_RUN | no fabricated device log |

宽回归之后调整campaign生成（natural G4入口及依赖排序/类型注解），随后发现并修正私有fixture静态K=6→7，最终受影响115项重跑通过。宽回归不是事后伪称已在第二个commit重跑；生产runtime文件未变，最终文件SHA集合与static检查逐字节对齐。第一次宽回归命令误写不存在的test_block_tables.py，exit4/未运行，保留final-validation.log；随后用真实两个文件完成上述运行。没有把collection失败算PASS。


真实Python对象：AscendInputBuffers/InputBatch/ModelState、真实metadata builder、full_graph_fia参数组装、Target ModelAclGraphManager、真实Draft manager/upstream返回None、P3/P6 scope与retire。测试连接producer→`.pt`/JSON→checker。

被替换native：NPU replay/stream/event/FIA/Triton不可在Mac执行，用确定性CPU stand-in。Target Host replay不是Qwen。单独测试 Target→Draft phase 的完整propose被有限stub替换；另有真实proposal scope/manager/update/next-generation测试。真实device Qwen forward、采样和task更新均未执行，不把这些不同测试拼成“完整NPU通过”。

负例涵盖共享registry缺层/错绑draft/重复/未知tuple/遗漏task；文本与token-ID、bool/空/歧义；缺失/重复/extra/generation/NaN/slot/query/输出/KV；FAIL不被OPEN覆盖；abort非零signal/timeout/PID错；安装中途失败rollback；python -O关键验收。

full pre-commit曾在默认与允许联网环境尝试，Go依赖 `proxy.golang.org:443` 连接超时，记 **ENVIRONMENT_BLOCKED**。可独立执行的12项hook通过，不关闭检查、不改hook配置、不称完整pre-commit PASS。

## 8. 下一轮集中执行：实际 CLI，不是待写脚本

输入包含原始 fixture、5份原始request bytes、最终handoff、case plan/commands、package/receiver工具。代码必须从**发布后的最终Git提交**取得；输入包没有源代码覆盖补丁。

先发布审查→普通push→独立GitHub clean clone验证，再运行输入包 `VERIFY_SOURCES.py`；它核对两仓SHA/tree/clean、全部工具SHA和原fixturebytes。再生成路径准确的计划：

```bash
python tools/p7x_graph_repair5_campaign.py \
  --repo <actual-ascend-repo> --inputs <unpacked-inputs> \
  --output <new-artifacts-dir> --vllm <exact-vllm-repo> \
  --python <server-python> --sha 3bdc413aa9826e4c199f5d96125e71db2c343420 --tree e72a3ef82fbd1cfd70ea20010c2eeb0b08c50a62 \
  --run-id <new-unique-run-id>
```

所有subcommand均实际--help测试。生成器只生成命令，不启动设备。commands按依赖顺序，不能忽略失败整文件盲跑。

补充本地入口验证：用最终 handoff SHA/tree 实际调用计划生成 CLI，生成24个case；用两仓真实clean checkout执行 VERIFY_SOURCES；对返回打包器实际pack→extract→verify，并注入错误hash确认拒绝。结果为 `Auxiliary_Validation.json`，只说明Host工具可执行，不说明服务器路径存在或设备已运行。

| 顺序 | case | 目的/产物 | 失败处理 |
|---|---|---|---|
| 1 | P0 | 无模型 API/CANN/FIA预检 + 外部 exact source/import/fixture | 核心能力缺失停止依赖；provenance受限单列 |
| 2 | A0/A1/B0 | OFF正常、public拒绝、三真实replaybucket/多代/16tokens/launcher joint | 原生binding失败停止所有依赖B0 |
| 3 | C2 | 独立privateFIA八控制，oracle/普通event/trace身份 | 与B0逻辑独立；设备健康时可独立执行 |
| 4 | G4F_OFF/ON | 空engine受控Target+MRV2；10有效状态+4row显式blocked | 不掩盖blocked；先短/已有bucket健康，再完整记录 |
| 5 | B1/B2 + natural G4 OFF/ON | 真S>0、非对齐、mixed/padding、自然观察HEAD_ONLY | 数值必须先验证输入身份，不能ordinal强配 |
| 6 | LIFE | 真实MRV2三bucket多代，诊断ordinarycompletion+retire | 缺事件/没有replay不能PASS |
| 7 | 4 ABORT | 正常LIFE成功后隔离故障点、quarantine | exit73按独立checker；timeout/signal不是PASS |
| 8 | O0/O1 | 实验Graph保留、observer关闭 | 不用关闭experimental flag替代 |
| 9 | trace | 当前不重复相同T0/T1 | 获得新增字段机制后再安排 |
| 10 | R0 | 全量产物打包、CRC/hash、接收端校验 | 不删除失败/partial/未配对数据 |

B0与自然case必须同时跑官方joint（request字节、identity、argv/PID、16tokens、returncode/signal/timeout）和对应Graph checker；joint不替代G1–G5。
默认自然case1800秒，受控Target3600秒，C2内部180秒；Target输出预算16GiB、每checkpoint512MiB。超预算直接停该分支并保留partial；不裁掉失败样本。旧Repair4 OFF不能替代新SHA OFF。

## 9. Readiness 与未完成项

| 能力 | 已实现/Host | 尚未完成 |
|---|---|---|
| API/schema/token joint | HOST_VERIFIED；旧device离线19PASS+1OPEN | 新SHA device重跑 |
| Target实际inventory | HOST_VERIFIED | 新模型实例36层完整capture/KV设备映射 |
| Controlled FULL_TARGET | IMPLEMENTED_SCOPED；真实框架producer链Host验证 | 四请求Targetbucket缺失；nativeforward未运行 |
| 私有FIA A/B/A′ | IMPLEMENTED；含仅窗外扰动 | NPU数值/代际 |
| 真实MRV2 A/B/A′ | IMPLEMENTED_SCOPED token oracle | greedy nondiscrimination可能OPEN；hidden Window oracle NOT_IMPLEMENTED |
| realMRV2 lifecycle | IMPLEMENTED_DIAGNOSTIC_SERIALIZED | normal-overlap reuse UNPROVEN |
| abort | IMPLEMENTED_CHILD_QUARANTINE | 真实inflight设备验证NOT_RUN |
| trace | 字段实际审计完成 | task/physical-read CAPABILITY_GAP |

总体是 **LOCAL_IMPLEMENTATION_PARTIAL / READY_FOR_PUBLICATION_REVIEW / READY_FOR_A3_SCOPED_AFTER_PUBLICATION**，不是全部要求已关闭。部分具体阻塞不妨碍其他独立验证，但不能被总括READY掩盖。

## 10. 交付内容与审阅方式

主报告自包含；紧凑ZIP另含 Receiver、离线逐样本数值/未配对表、128 tensor完整索引、trace字段、source audit、Finding/Inventory/Readiness contracts、红绿/检查日志、完整diff、13个修改文件、最小raw切片及来源映射、最终Git身份、SHA256SUMS。

服务器包只含handoff/计划/请求/原manifest/校验与打包辅助，不含未提交production覆盖。两个ZIP实际解压校验CRC、每成员hash、JSON、内部引用和handoff identity。Download Manifest不自引用，保留 publication=NOT_PUBLISHED / device=NOT_RUN。

下一步：独立Repair5 review → 本地事实裁决/必要修复 → 用户授权发布 → 独立网络恢复 → A3 scoped campaign。**不直接开始服务器实验，不解冻public Graph。**
