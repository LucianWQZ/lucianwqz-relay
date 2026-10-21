# P7-X Prefix Cache and Prefill Specification

## Prefix residency contract

Prefix cache changes physical sharing/residency, not Window math. For each
generation P7-X snapshots:

```text
gid
ordered request IDs
idx_mapping contents
canonical FullSource identity
per-row valid block count
```

The per-row valid count is the allocated/current canonical extent for currently
admitted routes, not a universal physical-residency probe. Materialization
always copies from current canonical FullSource and validates that every
descriptor ends within the current valid count. Request reorder,
finish/add, row replacement, eviction/reuse or owner rebinding therefore makes
old metadata stale. Block ID zero remains a valid ID, never a sentinel.

Future SFA/offload/recycling/native-circular routes require a dedicated
resident-set provider; they may not inherit this current-extent contract.

## Prefill phase contract

Pinned `InputBatch` fields define row phase at proposal entry:

```text
computed >= prefill_len
  -> PURE_DECODE

computed < prefill_len and computed + scheduled < prefill_len
  -> PREFILL_CONTINUING

otherwise
  -> PREFILL_TERMINAL
```

`is_prefilling_np` and `has_prefill` must agree with those counters. The entire
phase plan is immutable within one mapping epoch.

## Read behavior

| Row phase | Draft read carrier |
|---|---|
| continuing prefill | current resident full prefix (`S=0`) |
| terminal prefill | normal method-specific Window |
| decode | normal Window |

An all-continuing batch uses the baseline path and allocates no Window state.
This is intentional because no speculative decode Window is consumed. A mixed
batch uses one full-width stable workspace with row-specific descriptors; it is
not a batch-wide fallback.

Eagle3 keeps proposal-frozen S for Window rows and refreshes every step from
FullSource. DFlash remains K+1. DSpark retains actual K or K+1 based on its
configured sampling anchor. Query/positions/bonus/slot semantics are unchanged.

## Required runtime campaign

Node101 must cover miss, hit, shared prefix with different tails, eviction,
stale/reused physical block, long multi-chunk prompt, terminal transition,
mixed batch, reorder and finish/add. Oracles include table/length, physical
read-set, full slot/write and Target equality.
