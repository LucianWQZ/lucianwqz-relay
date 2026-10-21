# P7-X Node101 NPU Revalidation Matrix

All cases require exact vLLM `84030bbe3d74d99bad477a3d2e37a973ccd8865c`
and the post-review P7-X final SHA. Replace model placeholders only with
owner-signed realpaths/revisions/hashes; do not invent a checkpoint.

## Mandatory MRV2 preflight for every case

```bash
export VLLM_USE_V2_MODEL_RUNNER=1
```

The artifact must record exact commit/tree plus an in-worker fully-qualified
`model_runner_class` containing `worker.v2` and `speculator_class` containing
`worker.v2.spec_decode`. A missing/mismatched probe is
`INVALID_RUN_WRONG_MODEL_RUNNER`; no semantic or performance result from that
run is admissible.

| Case | Required route/config | Primary oracle | Status before run |
|---|---|---|---|
| GLM-TP16-OFF | GLM5.2 W4A8, eligible DSpark, K=8, TP16, eager, W=OFF | exact baseline output/slot/Target and profiler | model identity required |
| GLM-TP16-W1024 | same, W=1024 | per-rank S/E/V, table, physical reads, full slot/Target, output | Report1 backend inventory required |
| QW-E3-K3 | owner-selected Qwen Eagle3 static-K, TP1, eager | first pass + each AR step, frozen S, future block, rejection | model pair required |
| QW-DF-KP1 | owner-selected Qwen DFlash | K+1 query width and Draft read-set | model pair required |
| QW-DS-K | eligible Qwen DSpark | `sample_from_anchor=true` K path | resolved HF config required |
| QW-DS-KP1 | eligible Qwen DSpark | immutable HF config `sample_from_anchor=false`, K+1 | checkpoint/config required |
| DSACP-00 | actual required DSA-CP route, Window OFF, Graph NONE, effective DSA-CP ON | actual builder/shared kwargs; baseline output; full slot/write/Target; zero Window state | mandatory shared-path regression |
| DSACP-01 | actual required uncompressed DSA-CP route | common Window -> local lengths/indices -> operator; comm and slots | Report1 topology required |
| PFX-MISS | positive route, prefix enabled, miss | ordinary Window/read/write oracle | ready after model selection |
| PFX-SHARE | two requests share prefix, different tails | valid counts, table identity/content, isolation | ready after model selection |
| PFX-EVICT | eviction and physical block reuse | stale generation rejection; no evicted read | test harness required |
| CHUNK-LONG | long multi-chunk prompt | continuing baseline, terminal Window, next decode | ready after model selection |
| MIX-02 | continuing prefill row + decode row | row-wise full/window table and exact; no EngineCore abort | batch fixture required |
| MR-REORDER | A/B then B/A | mapping epoch/request identity, no cross-row contamination | batch fixture required |
| MR-FINISH-ADD | A finishes, C takes row | old metadata rejected; full slot/write | batch fixture required |
| MR-PREEMPT | preempt/resume | new generation and current FullSource | scheduler fixture required |
| ASYNC-1 | one DFlash/eligible DSpark proposal in flight | event/stream/lane address/generation/retirement; full slot/Target | async runtime required |
| ASYNC-2 | two proposals in flight | distinct lane addresses, event/stream, independent generations and retirement | async runtime required |
| ASYNC-PRESSURE | exceed configured/safe lane capacity | oldest-lane event wait, no overwrite, metadata retained, bounded pressure latency | async runtime required |
| ASYNC-REVERSE | two proposals complete newest first | nonblocking reclaim of completed lane; no wait/reuse of pending oldest | async runtime required |
| ASYNC-ABORT | abort after submit | abort flag, event/stream completion, metadata retained until retirement, safe reuse | async runtime required |
| ASYNC-TP | ordinary TP>1 + async | per-rank event/stream/lane/generation/retirement and any comm-stream coverage | `R1-TP-ASYNC-01` open |
| ASYNC-PREFIX | shared prefix + async | block lifetime, valid extent, lane address, eviction/reuse after event | `R1-PFX-ASYNC-01` open |
| NEG-MTP | configured W with MTP | warning once, zero Window state, baseline | mandatory negative |
| NEG-V4-DS | V4 co-trained DSpark | forced OFF before numeric/inventory | mandatory negative |
| NEG-CMP-DSA | compressed DSA/QLI | reject before FullSource | mandatory negative |
| NEG-GRAPH | FULL/FULL_DECODE_ONLY/PIECEWISE | existing Graph failure, no provider install | mandatory negative |

For GLM performance lengths 16K/32K/64K/128K use output 2000,
`data_num=4`, concurrency 1 and request rate 0. Compare OFF/W1024 with warmup,
repeated A/B/A runs and raw profiler artifacts. A semantic PASS requires actual
physical-read, full-slot/write and Target oracles; output equality alone is not
sufficient.

For every TP/DSA case collect per rank: `S`, `E`, `V`, table, exact, upper,
actual operator operand, slot mapping/write, Target metadata/output, stream,
event, lane address, generation and retirement. Report1's P8 observations may
select fixtures but may not close a P7-X row.
