# P7-X Graph Base A3 Failure Root Cause

Date: 2026-10-17  
Status: repaired locally; device revalidation pending  
Branch: `fix/p7x-graph-base-a3-g1g5`  
Parent: `8cb4bed670f395c257c1233db944395159916009`  
Repair commit: `13373fff637e819f3db125e05064f94cba3475a3`  
Repair tree: `739cde3de61e65be7cdbd187baebb6d17da04aee`

## 1. Device failure being adjudicated

The first Ascend A3 campaign used the already accepted fixture:

- target: `/mnt/share/wql/Qwen3-8B`;
- draft: `/mnt/share/dspark_qwen3_8b_block7`;
- method: eligible DSpark;
- `K=7`, query width `7`;
- STANDARD dense FIA, one executable group;
- `FULL_DECODE_ONLY`, `W=1024`;
- TP1/DP1/PP1/PCP1/DCP1; async, prefix, SP, DSA-CP and FlashComm off.

The control runs were valid: A0 passed and A1 stopped at the public
`GRAPH_FROZEN` gate as expected. In internal case B, startup capture succeeded,
but the first runtime bind failed before replay:

```text
prepare_parallel_draft_window_graph_characterization
  -> DraftWindowGraphBindingProvider.bind_read_carrier
  -> validate_draft_metadata_isolation
  -> ValueError: Draft metadata mutable storage aliases Target metadata
```

Consequently G1 did not pass and G2-G5 were not run.

## 2. Locally reproduced RED

The new owner-faithful regression is:

```text
tests/ut/spec_decode/test_draft_window_graph_characterization.py
  test_real_target_metadata_sharing_is_allowed_for_full_write_carriers
```

It deliberately models the real engine ownership relationship:

```text
target.slot_mapping     -> block_tables.slot_mappings[gid, ...]
target.positions        -> input_buffers.positions[...]
target.query_start_loc  -> input_buffers.query_start_loc[...]
```

Before the production fix, this command failed with the same device exception:

```bash
VLLM_VERSION=0.29.0 \
PYTHONPATH=/Users/wenqingzhang/Desktop/vllm/vllm \
.venv/bin/pytest -q \
  tests/ut/spec_decode/test_draft_window_graph_characterization.py::test_real_target_metadata_sharing_is_allowed_for_full_write_carriers
```

Observed pre-fix result:

```text
FAILED
ValueError: Draft metadata mutable storage aliases Target metadata
```

This is a true red-to-green reproduction; it is not a synthetic exception-string
test.

## 3. Why the previous Mac tests passed

The earlier fixtures created Target metadata tensors independently from the
canonical `BlockTables` and `input_buffers` tensors. That arrangement proved
that Draft metadata did not alias an artificial Target object, but it did not
model the real engine's canonical ownership. The broad recursive isolation
validator therefore saw no sharing on Mac.

On the A3 engine, Target metadata legitimately points at canonical full
write/query buffers. The characterization builder restored those same canonical
references into Draft metadata, then a later broad validator interpreted that
intentional sharing as contamination. The difference was fixture ownership, not
device-specific tensor semantics.

## 4. The conflicting invariants

The old code attempted to enforce two different invariants with one broad
recursive alias check.

### Draft-private read invariant

These fields must not alias Target-private storage:

- Window block table;
- device exact Window lengths;
- CPU exact and upper Window lengths;
- backend-derived Draft read state;
- other mutable state that belongs only to the Draft read plane.

### Canonical full write/query invariant

These fields must retain exact canonical full ownership and may therefore be
the same object/storage that Target metadata references:

- `slot_mapping`;
- `positions`;
- `query_start_loc`;
- `actual_seq_lengths_q` semantics;
- `attn_state`;
- `num_actual_tokens`;
- `causal`.

The Frozen Design requires both statements at once:

```text
Draft READ visibility changes.
Full write/query and Target ownership do not change.
```

## 5. Root cause

`_build_private_graph_metadata()` first produced isolated Draft metadata and
then restored canonical full write/query references. The final object was passed
through `validate_draft_metadata_isolation()` in
`DraftWindowGraphBindingProvider.bind_read_carrier()`, and again when the P3
`DraftMetadataStore` published it. Since that validator traversed every mutable
field, it could not distinguish intentional canonical sharing from an illegal
Draft-read alias.

The failure was therefore a validator-contract defect:

```text
correct owner graph + over-broad post-restore isolation oracle -> false reject
```

It was not a reason to clone canonical full carriers and not evidence that the
A3 fixture was invalid.

## 6. Why cloning was rejected

Cloning `slot_mapping`, `positions`, or `query_start_loc` would silence the
alias error while violating the feature contract:

- slot mapping must still be derived from the canonical full table;
- positions remain absolute;
- query layout remains baseline;
- the physical KV write path must be identical with Window OFF and ON.

The repair therefore changes the validation boundary, not the owner.

## 7. Corrected contract

The builder now returns two distinct views:

1. `private_isolation_view`: immutable for validation purposes and captured
   before canonical full references are restored;
2. final metadata: shallow-copied layer objects carrying the same Draft-private
   read tensors plus exact canonical full write/query references.

The provider validates them independently:

```text
private_isolation_view
  -> recursive Target isolation
  -> exact Window read-carrier identity

final metadata
  -> exact Window read-carrier identity
  -> exact canonical write/query identity
  -> unchanged write-side snapshot
```

`DraftMetadataStore.publish()` receives the private validation view explicitly,
while storing the final metadata consumed by the Graph path.

## 8. Negative protection retained

`test_draft_private_fields_still_reject_target_storage_alias` supplies a
distinct mapping whose private layer/storage still aliases Target. It continues
to fail closed with:

```text
ValueError: Draft metadata mutable storage aliases Target metadata
```

Thus the fix does not whitelist all Target sharing. It recognizes only the
separate canonical full identity contract after private isolation has already
passed.

## 9. Final conclusion

```text
A3 FAILURE REPRODUCED LOCALLY: YES
ROOT CAUSE: one broad post-restore alias oracle conflated Draft-private reads
            with intentionally shared canonical full write/query owners
FIX: separate private isolation from canonical write identity
SLOT/POSITION/QUERY CLONING: REJECTED
DEVICE REVALIDATION: REQUIRED
```
