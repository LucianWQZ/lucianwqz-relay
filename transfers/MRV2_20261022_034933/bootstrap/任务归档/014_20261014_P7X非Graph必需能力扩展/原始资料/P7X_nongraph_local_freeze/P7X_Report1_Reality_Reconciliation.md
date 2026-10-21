# P7-X Report1 Reality Reconciliation

## Evidence identity

- Reconciliation date: 2026-10-15 (Asia/Shanghai)
- P7-X source under adjudication: `7e88db6ed31e7965f526ea6f49cc17101f4a65b4`
- P7-X source tree: `71800e2e250f0b4dc51aede643eebff55e39b404`
- Report1 actual path: `/Users/wenqingzhang/Desktop/Node101_MRV2_P8_Current_Final_Campaign_Combined_Report.md`
- Report1 SHA256: `cfd15811303b30d0786cf4541b2190ac7a66e349ba55e160b6f4dff065408bbf`
- Report1 mtime: `2026-10-15 09:16:18 CST`
- Report1 title: `Node101 — MRV2 Draft Sliding Window P8 Current-Final Campaign (Combined Report)`
- Report1 campaign host: `node-39-101`
- Report1 source SHA/tree: `4753742ab181920292c504a79eedecf9b428ae1b` / `b7e525c3c9d45617ad1023ad45c6948c466a3631`

Report1 predates P7-X. It may establish runtime topology, defaults, model identity,
fixtures, and P8 behavior. It does **not** directly validate or invalidate P7-X
production behavior at `7e88db6...`.

## Reality reconciliation table

| ID | Area | P7-X assumption/claim | DeepSeek verdict | Report1 observation | Contradiction? | Action |
|---|---|---|---|---|---|---|
| RR-01 | MRV2 runtime selection | P7-X docs assumed an MRV2 campaign would enter `worker.v2` but did not freeze the required environment knob | Review did not challenge production wiring | With `VLLM_USE_V2_MODEL_RUNNER` unset, Ascend selects MRV1; the old GLM TP16 launcher demonstrably ran `model_runner_v1.py` and MRV1 spec decode | **Yes, deployment-document gap; not a P7-X code-path bug** | Freeze `VLLM_USE_V2_MODEL_RUNNER=1` and require both model-runner and speculator module/class probes before accepting any campaign result |
| RR-02 | TP16 | Ordinary TP is replicated logical read visibility; TP2/4/16 are `LOCAL_STATIC_READY` | `APPROVE_STATIC`; no `V/world_size`, rank resolution and full slot/write path are source-proven | TP16 was `ENVIRONMENT_BLOCKED`; old P8 TP2 only proved the old gate rejected TP>1 | No direct contradiction; P7-X remains untested on NPU | Preserve P7-X TP production code and `LOCAL_STATIC_READY`; require per-rank S/E/V/table/exact/upper/operator/slot/write/Target evidence |
| RR-03 | TP rank | Live TP rank comes from initialized TP group; no rank-0 fallback | Source-proven | Report1 did not reach P7-X TP16 and collected no per-rank data | No | Retain source contract; add rank and per-rank artifacts to the second-round matrix |
| RR-04 | Slot/write | Window never changes full/absolute slot mapping or KV writes | Source-proven statically | P8 positive runs did not instrument write-side/slot oracle; TP2 old gate rejected before allocation | No; runtime evidence remains absent | Require per-rank and per-request slot/write oracle on P7-X final |
| RR-05 | GLM target/backend | Required GLM route might be dense FIA or uncompressed DSA/DSA-CP; exact runtime composition was unknown | Correctly kept `REPORT1_RUNTIME_DEPENDENT`; no inference from target backend allowed | Target is `GLM-5.2-W4A8`, architecture `GlmMoeDsaForCausalLM`, with MLA + DSA sparse index; actual MRV2 Draft backend/builder/gids/geometry were not observed | P7-X's broad candidate list is narrowed, but no contradiction to its fail-closed status | Record known target facts; continue to require actual Draft inventory from a P7-X MRV2 run |
| RR-06 | GLM Draft checkpoint | Exact checkpoint and DSpark K/config were unknown | Report1-dependent | Draft is `/mnt/share/l00887471/graph_vllm/dspark_test/sw-aspark/GLM5.2_dspark`; same as historical MRV1 draft; K=8; `sample_from_anchor=true` | Resolves asset identity only | Freeze fixture paths/identity in the assumption register and test matrix; do not infer backend from target |
| RR-07 | DSA-CP | Uncompressed, single-gid DSA-CP common-carrier contract is locally static-ready | `APPROVE_STATIC`; shared `attn_utils` change needs an independent Window-OFF regression and NPU case | DSA-CP actual runtime was not observed | No | Add `R1-DSACP-OFF-01`, Window-OFF regression UT, and `DSACP-00` NPU case |
| RR-08 | Async default | Async DFlash/eligible DSpark production binding is locally static-ready; NPU ordering remains open | Static wiring/lifetime accepted; pressure strategy is Major M-02 | P8 source auto-resolved DFlash/DSpark async to true; old P8 then rejected before live binding. No P7-X async run occurred | Confirms default reachability and raises pressure importance; does not test P7-X | Keep P7-X evidence local-only; fix pressure policy locally and add full async NPU sequence |
| RR-09 | Async streams/events | Event recorded on current NPU stream after Draft submission; late/backend/communication stream coverage remains open | SOURCE_PROVEN ordering in Python, NPU-required for real happens-before | Report1 collected no live async events, streams, reuse, or completion | No | Require event/stream/lane/generation/retirement evidence for one/two/pressure/reverse/abort/TP/prefix cases |
| RR-10 | Prefix | Canonical FullSource + persistent valid counts provide the local contract | `APPROVE_STATIC`, with terminology correction: allocated/current valid extent is not a universal physical-residency oracle | P8 measured the old prefix gate only; no prefix data plane was observed | No direct contradiction | Preserve local status, correct terminology, require hit/share/evict/reuse and lifetime evidence on P7-X final |
| RR-11 | Chunked prefill | Per-row pre-step counters classify continuing/terminal/decode correctly | `APPROVE_STATIC` | Chunked prefill was enabled and a 9015-token prompt spanned chunks, but no per-chunk transition data were captured; P8 only exercised decode output | No | Preserve local status; require counter/phase/table transition evidence on P7-X final |
| RR-12 | Mixed prefill/decode | One stable carrier can contain continuing full rows and terminal/decode Window rows | `APPROVE_STATIC`; batch-global backend behavior still runtime-dependent | P8 ran `max_num_seqs=1`; mixed was not observed | No | Preserve local status; require mixed operator-input and no-EngineCore-abort evidence |
| RR-13 | Multi-request | Request order, mapping epoch, row phase, topology and lane identity protect reorder/finish-add/row reuse | `APPROVE_STATIC` | Batch>1/reorder/finish-add/row reuse were not observed | No | Preserve local status and run dedicated second-round fixtures |
| RR-14 | Multi-group | Live P3/P4 carrier remains single-group; homogeneous and heterogeneous routes stay runtime-dependent | Review agreed there is no fake PASS | P8 observed one gid only; multi-group was static-only/not observed | No | Keep both multi-group rows `REPORT1_RUNTIME_DEPENDENT`; no local enablement |
| RR-15 | Other parallel modes | DP/PP/PCP/DCP/SP/FlashComm are not implicitly supported by ordinary TP | Review agreed they remain gated; DSA-CP is separately typed | Report1 did not observe these modes | No | Keep runtime-dependent/fail-closed status; do not inherit TP evidence |
| RR-16 | Qwen positive routes | Qwen method/provider architecture is locally ready, exact assets and current-SHA NPU evidence pending | Positive dense consumers and gates are factual | At P8 SHA, Qwen3-8B DFlash TP1 and Eagle3 TP1 ran under true MRV2 with async off; DSpark pair was missing | Resolves useful fixtures but not P7-X behavior | Reuse exact DFlash/Eagle3 assets as P7-X revalidation fixtures; classify DSpark input missing until owner provides a pair |

## Reconciliation decision

Report1 does not falsify the P7-X static TP, DSA-CP, prefix, chunked, mixed, or
multi-request contracts. It does establish two mandatory campaign facts:

1. MRV2 execution must be explicitly selected and proven from inside the worker.
2. DFlash/DSpark default to async scheduling, so async pressure and device
   completion are release-critical rather than optional edge cases.

All Report1 NPU observations remain scoped to P8 SHA `4753742...`; P7-X final
requires a fresh Node101 campaign and cannot inherit those results.
