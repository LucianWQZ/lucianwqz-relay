# MRV2 Draft Sliding Window：P5–P8 Entry Baseline

> 本文是 P5–P8 的起点约束，不是 P5 implementation plan。  
> Production code 本轮未修改。  
> P5 design/preflight：**READY**。P5 production Graph enable：**BLOCKED**。

## 1. Immutable production baseline

```text
vLLM repo        /Users/wenqingzhang/Desktop/vllm/vllm
vLLM SHA         84030bbe3d74d99bad477a3d2e37a973ccd8865c
vLLM tree        f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee

vLLM-Ascend repo /Users/wenqingzhang/Desktop/vllm/vllm-ascend
branch           feature/p4b-eagle3-static-k
base             841dc6ccdb134eab7ad09008859834d0572ee83f
Final SHA        1011e2c2fa99729a46efde5b5bbaf6daed975a2c
Final tree       7d165d585755766e7493e02f0281598e4aca3602
```

`R-REPO-01`继续有效：production只允许修改vllm-ascend；不得重新引入upstream hook prototype、
私有vLLM API、site-packages patch或debug commits。

## 2. P1–P4 可复用资产

| Layer | Reusable production asset | Owner / lifetime | P5–P8 use |
|---|---|---|---|
| P1 | `DraftWindowPolicyDecision`, scalar plan, legacy anchor/capacity math | immutable per speculator/config | 所有新route先通过policy；不得绕过forced-OFF |
| P2 | runtime inventory、`FullDraftKVSource`、valid counts、`SingleGroupDirectPrefixProvider`、read descriptor | source借用canonical owner；batch bind | Graph/新backend只能新增经过验证的provider，不能改FullSource |
| P3 | `DraftWindowGenerationIdentity` + caller-owned `mapping_epoch` | proposal/step generation | capture/replay必须验证同一generation，不可用pointer freshness |
| P3 | fixed `DraftWindowWorkspace` | speculator/lane owned | Graph候选地址基础；resize/address变化必须显式Gate |
| P3 | lease/completion state machine | generation reader lifecycle | Graph/Async必须换成真实device completion证明，不可复用fake token结论 |
| P3 | immutable `DraftMetadataInputs` | lease scope | 唯一typed read transport；不得增加positions/slot/Target override |
| P3 | `DraftMetadataStore` | speculator-owned per active generation | Draft metadata与Target隔离；Graph registry不能替代它 |
| P4a | production epoch source、pure-prefill classifier、single validate boundary、Ascend read adapter | instance-scoped eager proposal | P5应复用contract，不应复制第二套隐式transport |
| P4a | explicit CPU exact seam + FIA carrier | metadata build/forward | Graph需证明capture/replay时exact/upper/table绑定，不得退回full mirror |
| P4b | proposal `L0/K/H/S` freeze和per-step `E_s/V_s` | one Eagle3 proposal | Graph multi-step要保持S冻结和每stepFullSource refresh |
| P4b | Eagle3 serialized step continuation | per-step retired generation | Graph/Async扩展前先证明地址与reader时序 |

## 3. P4 eager exact route

### P4a static candidates

- DFlash，single-group dense GQA，query width K+1；
- eligible non-DeepSeek-V4 DSpark，default K / explicit non-anchor K+1；
- serialized eager、graph NONE、async false、TP1、其它parallel off；
- prefix cache off、mixed prefill/decode off；pure scheduler-prefill baseline bypass。

它们仅是STATIC_VERIFIED；`G-GQA-EAGER`仍OPEN。

### P4b NPU-evidenced scoped candidate

```text
Node133 / ascend-910b2 (A2)
Eagle3 static K=3
W=64
single executable dense-GQA group
TP1 serialized eager
single active request
L3 state + L4 FIA operator-argument evidence
```

这不是general P4 support。batch>1、strict reorder、persistent row reuse、L5、device happens-before、
performance和Node101/A3均未关闭。

## 4. 为什么 Graph 必须继续 fail closed

1. P3 workspace address“尽量稳定”不是capture/replay binding证明。
2. mapping_epoch与request fingerprint在eager Python边界验证；Graph replay如何执行同等验证尚未设计。
3. captured metadata/table/length pointer是否对应当前generation尚未证明。
4. P4 vendor-local builder和FIA exact seam只在eager调用链验证。
5. Eagle3每step重写workspace；capture/replay与reader completion的happens-before缺失。
6. 没有Level 5 physical read-set，也没有真实NPU event/lifetime证据。
7. Server E12已确认Graph FULL_AND_PIECEWISE被当前Gate拒绝；这是正确行为。

因此P5开始时必须保持Graph Window ON fail closed。

## 5. P5 可以做什么

P5只允许在不启用production Graph的前提下：

- 重新trace Ascend graph capture/replay、ACL Graph和speculator method-specific调用链；
- 定义capture-time与replay-time generation/read-input绑定协议；
- 证明workspace地址、active rows、exact/upper/table和slot/write边界；
- 设计instance-scoped Graph registry或typed binding，但不得用module global/ContextVar；
- 建立Graph source-drift guards、CPU/static spy和NPU experiment plan；
- 对DFlash/DSpark与Eagle3分别列capture/replay时序；
- 明确Graph invalidation、request reorder、shape/capacity变化与fallback策略；
- 先产出P5 Implementation Review和Architecture Gate，不直接打开Window ON。

## 6. P5 不能做什么

- 不得修改vLLM或依赖私有upstream patch；
- 不得以P4 eager single-request证据宣称Graph正确；
- 不得打开FULL、FULL_DECODE_ONLY或PIECEWISE Window ON；
- 不得把slot mapping、positions、query layout或Target放进Draft read override；
- 不得在capture/replay间临时swap canonical owner；
- 不得用CPU fake event替代NPU completion；
- 不得顺便打开Async、prefix、parallel、DSA/SFA/MLA/recycling；
- 不得忽略general mixed arrival造成EngineCore abort的产品风险。

## 7. P5 Exit prerequisites

P5设计可进入；production实现/enable前至少需要：

1. 精确Graph mode与method route定义；
2. capture/replay read-input identity与mapping_epoch验证边界；
3. address stability或显式recapture/invalidation contract；
4. full slot/write/Target parity tests；
5. stale replay、row replacement、shape变化和exception cleanup tests；
6. NPU capture/replay operator参数与physical read计划；
7. owner确认P4产品范围（general multi-request或single-active）；
8. `G-GQA-EAGER`/`G-AR-STEP`未关闭部分不得被Graph结果掩盖。

## 8. P6 prerequisites

P6（按consumer/mode扩展PIECEWISE/FULL）前必须：

- P5选定的Graph seam完成独立review；
- 至少一个精确Graph route在NPU上证明capture和replay均使用正确generation；
- Level 5或等价physical read oracle；
- eager↔graph切换、recapture、shape变化和one-step-lag测试；
- Eagle3 per-step S/E/V与workspace rewrite真实时序；
- Target/write invariants与OFF parity；
- device lifetime happens-before闭合。

当前P6状态：**BLOCKED**。

## 9. P7 prerequisites

P7涉及parallel/Async/complex backend扩展。每条route必须独立完成：

- inventory和layout分类；
- canonical source与provider数学；
- topology-specific gid/local-index/valid counts；
- lane/lease/event/stream ownership；
- typed transport与真实consumer；
- slot/write/Target不变量；
- negative Gate和source-drift测试；
- NPU physical read、reorder/isolation和性能。

禁止从TP1 dense-GQA或single-request Eagle3外推到TP/CP/SP/FlashComm、DSA/SFA/MLA、recycling、
multi-group、Async或prefix cache。当前P7状态：**BLOCKED**。

## 10. P8 acceptance items

Release前必须有owner签署的mandatory matrix，至少包括：

1. exact supported method/model/backend/device/topology；
2. P4a DFlash与DSpark各自NPU Window ON；
3. P4b product scope决定及对应多请求或single-active admission证据；
4. mixed arrival不能再service-wide abort；
5. persistent row reuse、strict reorder、finish/add和same-row replacement；
6. independent slot oracle与Target/write/logit parity；
7. Level 5 physical read-set；
8. real device lifetime/stream ordering；
9. Graph/Async等声明范围的positive与negative tests；
10. R4性能：latency、throughput、memory、D2H/H2D、graph recapture成本；
11. OFF/MRV1/unrelated MRV2 features全量回归；
12. deployment、support matrix、known limitations、rollback和release notes。

当前P8/release状态：**HOLD**。

## 11. Product-scope decision required before broad P5/P6 claims

### Option A：general multi-request serving

必须实现mixed phase策略、修复EngineCore abort、构造batch>1 pure decode并完成request isolation/NPU矩阵。

### Option B：single-active-request first release

必须owner批准，并在admission/startup层提前限制；不能依赖proposal运行期异常。Gate和文档必须显式带上
device/method/K/W/topology/request scope，原general验收项只能defer，不能删除。

本文不替owner作决定。

## 12. P5 start checklist

- [ ] 两个repo仍是上述exact SHA且clean；
- [ ] 新branch从`1011e2c2...`建立；
- [ ] Frozen Design只读，Plan增量记录；
- [ ] 先做P5 source drift/preflight，不先写production；
- [ ] Graph Window ON继续fail closed；
- [ ] 不引入vLLM patch/global/ContextVar/shared-owner swap；
- [ ] 明确证据等级，不把L4写成L5；
- [ ] 保持P4a/P4b eager regression；
- [ ] 把Node101/A3视为UNKNOWN；
- [ ] Feature release继续HOLD。

## 13. Entry verdict

```text
P5 DESIGN ENTRY: READY
P5 PRODUCTION GRAPH ENABLE: BLOCKED
P6: BLOCKED
P7: BLOCKED
P8 / FEATURE RELEASE: HOLD
```
