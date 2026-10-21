# P7-E Eager Async Host State Machine

## Status

```text
HOST/STATIC OWNERSHIP MODEL: IMPLEMENTED
HOST/STATIC REVIEW CONTRACT: PASS
LIVE SPECULATOR BINDING: ABSENT
REAL NPU COMPLETION EVENT: ABSENT
ASYNC EAGER WINDOW: STATIC_READY / LIVE FAIL-CLOSED
```

This state machine is a bounded host proof built on P3 ownership. It is not installed
in a production DFlash, DSpark, or Eagle3 speculator and cannot be used to claim
NPU async support.

## Owners

| Object | Owner | Lifetime |
|---|---|---|
| `DraftWindowEagerAsyncPool` | future speculator/runtime owner | pool lifetime |
| lane `DraftWindowRuntimeState` | pool | stable for one lane; independent workspace/backing |
| `DraftWindowEagerAsyncHandle` | one operation/caller | acquire through release; never reused |
| P3 lease and metadata entry | lane runtime | materialize through completion/abort |
| completion token | submitted handle | retained until consumer complete/release |
| backend-derived buffers | submitted handle | retained until completion/release |

Backend-derived buffers must be independently owned tensors. At bind time their
storage is checked against every Window workspace tensor, canonical FullSource
table/count backing, and nested Target tensor/NumPy/mutable storage. Alias is a
hard failure that aborts the active P3 generation and retires the handle.

Pool capacity is fixed. It never blindly round-robins onto an occupied lane and does
not resize active backing.

## State transitions

```text
FREE
  └─ acquire(epoch, requests, phase, step)
       → ACQUIRED
          └─ materialize(canonical FullSource, descriptors, exact/upper)
               → MATERIALIZED
                  └─ bind(Draft-private metadata, real Target metadata, derived buffers)
                       → BOUND
                          └─ submit(explicit completion token)
                               → SUBMITTED
                                  └─ poll(token complete)
                                       → CONSUMER_COMPLETE
                                          └─ retire
                                               → RETIRED
                                                  └─ release
                                                       → FREE
```

Allowed abort paths:

- `ACQUIRED`, `MATERIALIZED`, or `BOUND` can abort immediately and retire owned P3 state;
- `SUBMITTED` records `abort_requested` but keeps all backing/buffers owned until the
  completion token proves consumer completion;
- `CONSUMER_COMPLETE` may transition to `RETIRED` on abort;
- `operation_guard()` releases an immediately retired operation after exceptions.

## Identity and freshness

Each handle binds:

- unique monotonically increasing operation id;
- caller-owned strictly increasing `mapping_epoch`;
- ordered stable request fingerprint;
- phase and step;
- lane;
- full `P7EagerTopologyFingerprint`;
- P3 generation identity after materialization.

The lane runtime revalidates the exact topology fingerprint before workspace
materialization/refresh and before any active typed input is consumed. It cannot
be silently changed after the handle/generation was created.

Same-row replacement/reorder therefore changes the request fingerprint and mapping
epoch; stale handles and ABA operation ids cannot access a currently active lane.

## Completion semantics

The host tests use explicit fake completion tokens implementing the P3 completion
interface. They do not sleep. Delayed and reverse completion prove that:

- a pending reader keeps its lane and backing;
- another free lane can make progress independently;
- pool pressure produces a deterministic error;
- retirement/reuse happens only after the specific token reports complete;
- a token-query exception does not imply completion and leaves the operation
  `SUBMITTED` so polling can safely retry;
- derived backend buffers remain strongly owned until release.

These facts do not prove NPU stream happens-before, event recording placement,
cross-stream visibility, or that the live attention consumer has stopped reading.

## Failure cleanup

| Failure point | Cleanup |
|---|---|
| acquire validation | no lane is assigned |
| materialization | P3 materialize retires/aborts its lease; handle becomes retired |
| invalid derived buffer | active P3 generation aborted; handle retired |
| derived buffer aliases Window/FullSource/Target | active P3 generation aborted; handle retired |
| metadata publish/isolation | P3 aborts; handle retired |
| submit setup | active generation aborted; derived buffers released |
| completion query | ownership retained; retry via `poll()` |
| user exception before submit | `operation_guard()` aborts and releases |
| abort after submit | wait for completion; never overwrite pending backing |

## Test matrix

The host suite covers:

- capacity 2 with two active generations;
- delayed completion and reverse completion;
- bounded pool pressure;
- mapping epoch monotonicity;
- reorder, finish/add, and same-row replacement fingerprints;
- stale handle and lane ownership;
- topology mismatch;
- abort before submit and after submit;
- exception cleanup;
- incomplete reader preventing reuse;
- backend-derived buffer ownership;
- completion-token query exception and retry;
- stable lane backing with changed contents across generations;
- canonical FullSource non-aliasing.
- Window/FullSource/Target storage isolation for backend-derived buffers.
- serialized topology drift rejected before workspace write.

## Production gate

`evaluate_draft_window_eager_capability()` classifies an otherwise eligible async
route as `STATIC_READY`. `require_live_materialization()` rejects that status before
FullSource/workspace creation. The pool has no production installation point.

Closing async later requires, at minimum:

1. a real Ascend/NPU completion event tied to the actual Draft attention consumer;
2. a live speculator binding for each method/step;
3. stream-order and no-early-overwrite NPU evidence;
4. abort/preemption integration with the real engine;
5. profiler evidence for event/synchronization cost;
6. independent review and owner release approval.

## Independent Review Resolution

| Finding | Resolution | Final contract |
|---|---|---|
| F-02 derived-buffer ownership | `PARTIALLY_ACCEPTED` | Missing host isolation was real and fixed; no live async consumer or demonstrated production contamination exists. |
| F-03 topology only recorded | `ACCEPTED` | Exact topology is enforced by the shared P3 runtime at write/refresh/consume boundaries. |

The red tests showed all three alias classes were previously accepted and a
same-source topology drift could continue. They now fail closed. This closes the
host/static contract only:

```text
ASYNC STATIC: PASS
ASYNC LIVE/NPU: NOT VERIFIED / FAIL-CLOSED
GRAPH TRACK: FROZEN
```

