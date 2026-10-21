# P7-X Mixed and Multi-request Specification

## Identity

One proposal generation carries:

- monotonic caller-owned `mapping_epoch`;
- ordered stable request IDs;
- `idx_mapping` contents;
- per-row phase fingerprint;
- actual and padded row counts;
- method/gid/source/provider/topology/lane/phase/step identity.

Pointer identity, persistent row number and request count are never freshness
proofs.

## Mixed batch semantics

For one batch containing continuing prefill, terminal prefill and decode rows:

```text
continuing row -> resident full prefix
terminal row   -> Window descriptor
decode row     -> Window descriptor
```

All rows are materialized into one stable full-width workspace. Active columns
are tracked per row; all tails and padded rows are reset. The metadata builder
receives one coherent table/exact/upper generation. There is no service-wide
`NotImplementedError` and no silent full-Draft fallback for decode rows.

## Lifecycle scenarios

| Scenario | Required behavior |
|---|---|
| reorder `[A,B] -> [B,A]` | new epoch/fingerprint; stale metadata rejected |
| A finishes and C is added | new ordered identity; old A row cannot be reused |
| same persistent row becomes D | request fingerprint mismatch rejects old state |
| preempt/resume | resumed work starts a new proposal identity and rebinds FullSource |
| shrink/grow | actual/padded counts and tails revalidated/reset |
| prefix eviction/reuse | current valid counts and source identity govern reads |
| async overlap | each generation owns a different lane until completion |

## Frozen invariants

Rows may differ only in Draft read visibility. Target metadata, positions,
query layout, canonical tables, slot mapping and physical writes remain full.
NPU batch>1/reorder/finish-add/preemption/true row-reuse remains mandatory
runtime evidence.
