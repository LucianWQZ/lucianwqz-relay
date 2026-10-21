# P7-X Non-Graph Required Delivery Manifest

## Status

```text
Phase: independent review adjudicated; local freeze verified
Branch: feature/p7x-nongraph-completion
Parent: 4753742ab181920292c504a79eedecf9b428ae1b
Implementation: 7e88db6ed31e7965f526ea6f49cc17101f4a65b4
Review-fix: c1c2129aa49ee1de381130729de73124a6ec893a
Final tree: 384af8a0466f6aea2e73d6217f9802415b5ccd40
vLLM: 84030bbe3d74d99bad477a3d2e37a973ccd8865c, unchanged
Graph: frozen at P6/P6A
NPU: not verified
```

## Delivery scope

P7-X expands only the non-Graph eager data plane. It preserves P1 policy/math,
P2 canonical FullSource, P3 generation/lease/workspace/store, and P4 method
consumers. It adds typed contracts for ordinary replicated TP, phase-aware
chunked/mixed batches, prefix residency, uncompressed DSA/DSA-CP, and bounded
eager async execution.

| Required item | Local result | Exact boundary |
|---|---|---|
| TP16 | `LOCAL_STATIC_READY` | replicated Draft read visibility per TP rank; A3 TP16 NPU proof outstanding |
| DSA-CP | `LOCAL_STATIC_READY` | one uncompressed DSA group and actual DSA-CP builder; NPU local metadata/comm proof outstanding |
| Async | `LOCAL_STATIC_READY` for DFlash/eligible DSpark | pool defaults/minimum to host concurrency and pressure waits the oldest real event; NPU ordering open; Eagle3 and DSA async remain runtime-dependent |
| Prefix cache | `LOCAL_STATIC_READY` | canonical table plus generation-scoped valid block counts; NPU eviction/reuse proof outstanding |
| Chunked prefill | `LOCAL_STATIC_READY` | all-continuing batches use baseline full read; terminal/decode transitions are Window-aware |
| Mixed prefill/decode | `LOCAL_STATIC_READY` | row-wise full/window descriptors in one stable carrier |
| Multi-request | `LOCAL_STATIC_READY` | ordered request, mapping epoch, row-phase, lane and topology identities enforced |
| Backend generalization | `PARTIAL` | dense FIA and uncompressed DSA/DSA-CP source-safe; other derived backends gated |
| Homogeneous multi-group | `REPORT1_RUNTIME_DEPENDENT` | canonical-anchor contract exists; live P3/P4 bundled carrier does not |
| Heterogeneous multi-group | `REPORT1_RUNTIME_DEPENDENT` | actual required consumer identity and per-layout provider unresolved |
| GLM required route | `REPORT1_RUNTIME_DEPENDENT` | architecture can carry dense or uncompressed DSA/DSA-CP; actual Node101 composition unknown |
| Qwen required routes | `LOCAL_ARCHITECTURE_READY` | exact model/method/backend rows still require signed runtime inventory |

## Unchanged contracts

- MTP and DeepSeek-V4 co-trained DSpark are forced OFF before numeric validation.
- Draft Window changes only Draft read table/length.
- Target metadata/read lengths, positions, query layout, canonical full tables,
  slot mapping and physical KV writes remain baseline/full.
- Graph FULL, FULL_DECODE_ONLY and PIECEWISE remain fail-closed.
- No module global, ContextVar, shared-owner swap, vLLM patch, or MRV1 change exists.

## Shared MRV2 DSA-CP metadata fix

The `attn_utils.py` DSA-CP builder correction is shared by Window OFF and ON;
it is not Window-only behavior. Parent-red/P7-X-green proved the real builder
requires the common DSA request metadata. CONFIG_OFF is covered by an explicit
unit regression and mandatory Node101 case `DSACP-00`.

## Deployment identity and async policy

- Every campaign exports `VLLM_USE_V2_MODEL_RUNNER=1` and proves in-worker
  model-runner and speculator classes. Wrong-runner output is invalid evidence.
- `draft_window_async_lanes` is an optional positive integer. Default and
  minimum are `vllm_config.max_concurrent_batches`; smaller values reject at
  initialization. Exhaustion waits only the oldest submitted lane's event and
  never overwrites active backing.

## Review handoff

The independent review is resolved in `P7X_Review_Resolution.md`. Publication
and Node101 revalidation must use the final review-fix SHA, updated NPU matrix,
and runtime-identity requirement. No local statement or P8 Report1 observation
may be promoted to P7-X NPU support.
