# MRV2 Draft Sliding Window P0–P4 Runtime Support Matrix

> Production：vLLM `84030bbe3d74d99bad477a3d2e37a973ccd8865c` +
> vLLM-Ascend `1011e2c2fa99729a46efde5b5bbaf6daed975a2c`。  
> 证据日期：2026-10-13。  
> Release：**HOLD**。

## 1. 状态词定义

- **STATIC_VERIFIED**：代码、CPU/state-machine、source/drift/invariant tests通过；不等于NPU支持。
- **NPU_VERIFIED_SCOPED**：只对表中写明的设备、method、拓扑、mode和batch scope成立。
- **OPEN**：代码可能存在，但验收证据未闭合。
- **BLOCKED / UNSUPPORTED**：Window ON必须fail closed；不能静默关闭其它feature继续运行。
- **BASELINE_BYPASS**：该phase走完整full baseline，不属于Window ON支持。
- **FORCED_OFF**：warning + baseline，且零P2/P3/P4 Window state。

## 2. Method / Backend / Mode 支持矩阵

| Method | Model / backend | Device evidence | Topology | Eager Window | Graph | Async | Prefix | Prefill | Multi-request | NPU evidence | Final status | Required next step |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DFlash | dense GQA / Ascend attention v1 | none for Window ON | candidate仅TP1；DP/PP/PCP/DCP/SP=1；no DSA-CP/FlashComm | implemented + STATIC_VERIFIED；query width K+1 | BLOCKED | BLOCKED | BLOCKED | pure scheduler-prefill BASELINE_BYPASS；mixed拒绝 | not verified | 无 | **OPEN / static candidate** | Node133/A2或目标正式设备做physical read、Target/write、lifecycle、profiler全套 |
| eligible DSpark | non-DeepSeek-V4 co-trained DSpark；dense GQA | none for Window ON | 同DFlash | implemented + STATIC_VERIFIED；default anchor K，explicit false K+1 | BLOCKED | BLOCKED | BLOCKED | pure scheduler-prefill BASELINE_BYPASS；mixed拒绝 | not verified | 无 | **OPEN / static candidate** | 与DFlash相同，并分别覆盖K与K+1 |
| Eagle3 static K | Eagle3 / single dense-GQA group | Node133 / Ascend 910B2（A2） | TP1、serialized eager；其它parallel关闭 | implemented + STATIC_VERIFIED | BLOCKED | BLOCKED | BLOCKED | pure scheduler-prefill BASELINE_BYPASS；Window从pure decode proposal开始；mixed拒绝 | 单请求通过；batch>1未形成 | L3+L4；K=3、W=64；0 oracle divergence；284/284 proposal；852/852 source row | **NPU_VERIFIED_SCOPED / general G-AR-STEP OPEN** | owner决定general multi-request或single-active产品范围；补L5、lifetime、slot oracle、性能 |
| plain Eagle | Eagle | none | n/a | FORCED_OFF / unsupported | n/a | n/a | n/a | n/a | n/a | 无 | **FORCED_OFF** | 如未来支持需独立policy/source/timing设计，不能继承Eagle3结论 |
| MTP | any | none | n/a | FORCED_OFF | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | n/a | n/a | 无 | **FORCED_OFF** | 无；当前Frozen明确不支持 |
| DeepSeek-V4 co-trained DSpark | DSpark | none | n/a | FORCED_OFF，warning + baseline | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | n/a | n/a | 无 | **FORCED_OFF** | 需要owner新设计才可改变 |
| DFlash2 | DFlash2 | none | n/a | P1/P2资格/contract可存在，但P4 runtime UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | n/a | n/a | 无 | **UNSUPPORTED** | 单独关闭G-DFLASH2并建立真实consumer证据 |
| dynamic-K Eagle3 | Eagle3 | negative runtime未在服务器执行 | any | fail closed before proposal Window state | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | n/a | n/a | NOT_RUN | **UNSUPPORTED / negative evidence incomplete** | 提供可配置入口并执行negative Gate；若支持需重做proposal horizon contract |
| multi-group | heterogeneous/multiple executable groups | none | any | capability Gate拒绝 | BLOCKED | BLOCKED | BLOCKED | n/a | n/a | 无 | **UNSUPPORTED** | 每group source/provider/consumer与组合lifecycle验证 |
| MLA | MLA | none | any | capability Gate拒绝 | BLOCKED | BLOCKED | BLOCKED | n/a | n/a | 无 | **UNSUPPORTED** | 新provider和backend oracle |
| DSA / V4.1 | DSA | none | any | capability Gate拒绝 | BLOCKED | BLOCKED | BLOCKED | n/a | n/a | 无 | **UNSUPPORTED** | 独立inventory、projection、operator oracle |
| SFA | SFA | none | any | capability Gate拒绝 | BLOCKED | BLOCKED | BLOCKED | n/a | n/a | 无 | **UNSUPPORTED** | 独立provider/consumer验证 |
| native / recycling | method-specific | none | any | capability Gate拒绝 | BLOCKED | BLOCKED | BLOCKED | n/a | n/a | 无 | **UNSUPPORTED** | ownership和address-stability重设计 |

## 3. Cross-cutting capability matrix

| Capability | Current production behavior | Static evidence | NPU evidence | Status | Required next step |
|---|---|---|---|---|---|
| CONFIG_OFF | exact baseline factory/consumer path | PASS | baseline行为非本featureNPU gate | PASS | 持续回归 |
| forced-OFF | warning + baseline；numeric/inventory/workspace前返回 | PASS | 未要求Window NPU | PASS | 持续回归 |
| canonical FullSource | borrowed full owner；只读；每step重新bind/materialize | PASS | Eagle3 852/852 active row canonical slice equality | scoped PASS | 补多请求/row reuse/future-column事件 |
| mapping_epoch | production proposal source；严格单调；identity/store/lease全链验证 | PASS | sequential A→C→A epochs disjoint | PARTIAL runtime | batch>1 in-place mapping/reorder证据 |
| workspace/lease | serialized fixed backing；reader pending防覆盖 | PASS CPU state machine | NO_SYNC equality不是happens-before | OPEN runtime | NPU event/timeline或profiler证明 |
| DraftMetadataStore | real nonempty Target参与alias audit；Draft owner独立 | PASS | write/Target 84/84 before==after | scoped PASS | 多请求owner replacement与row reuse |
| pure scheduler-prefill | continuing/terminal均full baseline bypass，零Window state | PASS | long prompt可进入后续decode；不等于Window prefill | BASELINE_BYPASS | 文档保持清楚；不能标Window prefill支持 |
| mixed prefill/decode | proposal时hard reject | PASS fail-closed | 已观察EngineCore abort和service停止 | **BLOCKED** | 实现支持或在admission阶段安全拒绝 |
| Graph FULL/FULL_DECODE_ONLY/PIECEWISE | P2/P4前fail closed | PASS negative | E12 graph reason已观察 | **BLOCKED** | P5 design/source preflight；不得开启production |
| Async scheduling | fail closed | PASS negative | reason已观察 | **BLOCKED** | 多lane/真实event所有权与并发测试 |
| Prefix cache | fail closed | PASS negative | reason已观察 | **BLOCKED** | source/version/eviction语义与NPU验证 |
| TP>1 / CP / PCP / DCP / SP | fail closed | PASS | TP2 reason已观察，其余无positive | **BLOCKED** | 每topology独立projection/slot/write invariant |
| DSA-CP / FlashComm | fail closed，包括env Gate | PASS | 无positive | **BLOCKED** | 独立route |
| controlled pure-decode batch>1 | source contract存在 | PASS static | 4种构造未形成batch>1；scheduler每step只admit 1 | **OPEN** | scheduler/admission test harness或正式产品scope选择 |
| strict reorder `[A,B]→[B,A]` | stale fingerprint应拒绝 | PASS static | NOT_OBSERVED | **OPEN** | batch>1 NPU trace |
| persistent row reuse | same-row new request fingerprint应拒绝 | PASS static | NOT_OBSERVED；idx_mapping未instrument | **OPEN** | NPU instrumentation + deterministic scenario |
| independent slot oracle | full slot carrier invariant | PASS static | INCOMPLETE；trace table值被截断 | **OPEN** | 保存完整table与独立CPU recomputation |
| FIA operator arguments | explicit exact carrier | PASS | 33/33 Draft records匹配visible exact | L4 scoped PASS | 保持Target call分离并补P4a |
| kernel physical read-set | 未直接观测 | n/a | Level 5 NOT_OBSERVED | **OPEN** | profiler/kernel trace |
| performance / D2H | 一proposal受控snapshot；无debug validator热路径 | PASS static/spy | R4 NOT_RUN | **OPEN** | NPU profiler、latency/throughput、D2H/H2D计数 |

## 4. 精确已验证 NPU 路由

当前唯一可写成NPU PASS的Window ON路由是：

```text
machine/device : node133 / ascend-910b2 (A2)
method         : Eagle3
K / W          : K=3 / W=64
backend        : single executable dense GQA / Ascend attention v1
mode           : serialized eager
topology       : TP1; no DP/PP/PCP/DCP/SP/DSA-CP/FlashComm
request scope  : single active request
evidence       : L3 state + L4 FIA operator arguments
production SHA : 1011e2c2fa99729a46efde5b5bbaf6daed975a2c
```

即使在这条路由上，也没有Level 5 kernel read、完整device happens-before或R4性能证据。
Node101/A3状态为UNKNOWN。

## 5. 产品范围分叉

- 若产品要求general serving：mixed batch、batch>1、row reuse、reorder、EngineCore blast radius必须先关闭。
- 若首版只允许single-active-request：必须由owner批准，并在admission/startup前显式限制；不能依赖运行期abort。

在决策前：`G-AR-STEP=OPEN`，`P0–P4 REQUIRED DELIVERY=PARTIAL`，`FEATURE RELEASE=HOLD`。
