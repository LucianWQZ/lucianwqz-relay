# MRV2 Draft Sliding Window — P6 Route Fingerprint Specification

Review-final code: original P6 `20673a1ced10160d8f8d1aaa79230e6ce0409d3c`,
review-fix `7599497ab2694c4cf343f61f82f449980d8bad93`.

## Purpose

`DraftWindowGraphRouteFingerprint` is an immutable compatibility key for a captured Graph consumer.
It is not a request freshness token and intentionally contains no request ID, generation ID, or
`mapping_epoch`.

## Fields

| Category | Fields | Why required |
|---|---|---|
| Method/route | normalized `method`, `route`, `graph_mode` | Separates Eagle3 first pass, Eagle3 AR, DFlash, and DSpark; prevents mode drift |
| Backend | `backend_impl`, `builder_impl`, `global_group_id`, `layout` | Prevents caller-declared consumer identity and wrong layer-group/backend reuse |
| Capture program | `capture_descriptor`, `capture_bucket` | Names the concrete capture shape/bucket |
| Query geometry | `query_width`, padded request/token count, `static_k` | Prevents K/query-width/token-bucket mismatch |
| Window geometry | `window_size`, logical/kernel block size, block span | Prevents backing interpretation drift |
| Parallel topology | TP, DP, PP, PCP, DCP, SP, DSA-CP, FlashComm | P6 only models the exact single-lane topology |
| Runtime feature switches | async, prefix cache | Prevents unsupported feature combinations from sharing a capture identity |

## Validation rules

1. Route must match normalized method.
2. Mode must be explicit: `FULL`, `FULL_DECODE_ONLY`, or `PIECEWISE`.
3. Descriptor must be non-empty and bucket must equal padded geometry.
4. First-pass/DFlash/DSpark token bucket equals padded requests × query width.
5. Eagle3 AR requires query width 1 and one token per padded request.
6. Static K, W, block geometry, and all counts must be positive integers; gid/lane/ordinal are
   non-negative integers and booleans cannot masquerade as integers.
7. P6 rejects TP/DP/PP/PCP/DCP > 1, SP, DSA-CP, FlashComm, async, and prefix caching.
8. Registration rechecks method, gid, layout, builder, W, and block geometry against P2 inventory.
9. At the real UPDATE entrance P6 re-derives exact backend impl and builder impl and compares them
   with every carrier fingerprint.
10. The shared DFlash/DSpark manager resolves method/route exclusively from the installed
    provider's P2 normalized `inventory.method`; `_speculator_name`, class names, and caller labels
    are not route authorities. Any non-`dflash`/`dspark` provider hard fails.

## Method routes

| Route | Method | Phase | Step rule | P6 runtime result |
|---|---|---|---|---|
| `EAGLE3_FIRST_PASS` | eagle3 | proposal | step = 0 | carrier/update foundation only; capture blocked |
| `EAGLE3_AR_STEP` | eagle3 | step | step > 0 | per-step carrier foundation only; capture blocked |
| `DFLASH` | dflash | proposal | step = 0 | carrier/update foundation only; capture blocked |
| `DSPARK` | dspark | proposal | step = 0 | inherited query-graph foundation only; capture blocked |

## Equality and mismatch policy

All fields participate in dataclass equality. A mismatch is never normalized, silently rebound, or
allowed to fall back to Target/full metadata. The provider either uses the exact explicit carrier or
hard fails before replay/forward.

The review-fix additionally binds a typed full write/query reference. It is not part of the capture
fingerprint because it is runtime content, but its canonical slot owner, query geometry, tensor
identity, and mutation version are validated under the compatible fingerprint before metadata can
be submitted.

## Graph modes are inventoried, not enabled

Accepting a mode string in the fingerprint only makes incompatibility explicit. It does not close
the user Gate. In P6:

- FULL remains rejected by the existing Window runtime gate;
- FULL_DECODE_ONLY remains rejected;
- PIECEWISE remains rejected;
- no mode has NPU capture/address/read-set evidence.

```text
P6 ROUTE FINGERPRINT: STATIC CONTRACT PASS
GRAPH WINDOW USER GATE: STILL FAIL-CLOSED
```
