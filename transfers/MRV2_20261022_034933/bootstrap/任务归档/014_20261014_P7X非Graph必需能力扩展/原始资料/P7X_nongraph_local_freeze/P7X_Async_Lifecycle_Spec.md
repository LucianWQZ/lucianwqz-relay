# P7-X Eager Async Lifecycle Specification

## Scope

The production binding is enabled only for eligible non-Graph DFlash and
DSpark routes that pass the P7-X capability decision. Eagle3 multi-step async
and DSA/DSA-CP async remain `REPORT1_RUNTIME_DEPENDENT`.

## State machine

```text
FREE
  -> ACQUIRED
  -> MATERIALIZED
  -> BOUND
  -> SUBMITTED
  -> CONSUMER_COMPLETE
  -> RETIRED
  -> FREE
```

Each lane owns an independent P3 runtime, stable workspace and Draft store.
Each handle binds operation ID, mapping epoch, ordered request fingerprint,
phase, step, lane and full topology fingerprint.

## Submission and completion

The proposal scope reclaims completed lanes without blocking, acquires a free
lane, materializes, builds/publishes Draft-private metadata, forwards, records
a `torch.npu.Event` on the current stream, marks the reader pending, and retires
only after `event.query()` proves completion. The handle retains the metadata
object and backend-derived tensors after the P3 store is discarded for pending
retirement.

`additional_config.draft_window_async_lanes` is an optional positive integer.
Its default is `vllm_config.max_concurrent_batches`; configured capacity must be
at least that host-overlap depth or initialization fails. Host batch depth is a
lower-bound/configuration source, not a claim that it equals physical device
lane count.

## Abort semantics

- before materialization: retire/release immediately;
- after materialization/bind but before submit: abort P3 generation, clear
  metadata/buffers, release lane;
- after submit: set abort requested but retain lane/backing until completion;
- completion-query failure: retain ownership and retry; never infer completion;
- pool pressure: first nonblocking-reclaim completed lanes; if all lanes remain
  submitted, wait only for the oldest lane's real completion event, retire it,
  then reuse its stable backing. No polling spin, sleep, global stream sync, or
  overwrite is allowed. A query/wait error retains lane and metadata ownership.

Same mapping epoch is allowed only for an explicit same-request, next-step
continuation. This is currently a **HOST CONTRACT ONLY** and has no production
caller. ABA handles, stale topology, duplicate request IDs, reordered same-epoch
input and wrong lanes fail.

## Evidence boundary

Fake events prove state transitions, default/minimum capacity, two inflight
generations, delayed/reverse completion, pressure-only wait, abort-after-submit,
query/wait failures, metadata retention, prefix/TP identity and address reuse
without sleeps. They do not prove
real NPU stream ordering, event visibility, backend late readers or throughput.
Those remain Node101 requirements.
