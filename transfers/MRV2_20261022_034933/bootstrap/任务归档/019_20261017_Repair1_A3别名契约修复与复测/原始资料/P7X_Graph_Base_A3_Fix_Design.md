# P7-X Graph Base A3 Fix Design

Date: 2026-10-17  
Decision: `SEPARATE_PRIVATE_ISOLATION_AND_CANONICAL_WRITE_IDENTITY`  
Implementation commit: `13373fff637e819f3db125e05064f94cba3475a3`

## 1. Design objective

Repair the first A3 runtime-bind failure without changing Graph execution
semantics or weakening the Frozen read/write boundary.

The repair must make these two independent propositions true:

```text
Draft-private mutable read state does not alias Target-private storage.

Draft full write/query fields use the exact canonical full owners.
```

## 2. Chosen structure

### 2.1 Typed metadata build result

`DraftWindowGraphMetadataBuild` carries:

- `metadata`: the final Graph Draft metadata;
- `private_isolation_view`: the pre-restore Draft-private view.

Both mappings must be non-empty, distinct, and have the same ordered layer
keys. This prevents callers from silently validating one layer set and
publishing another.

### 2.2 Build sequence

`_build_private_graph_metadata()` performs:

```text
Ascend metadata builder
  -> deep Draft/Target isolation
  -> freeze private_isolation_view
  -> shallow-copy each Draft layer object
  -> restore canonical slot/positions/query and full query semantics
  -> return DraftWindowGraphMetadataBuild
```

Shallow-copying the layer object is intentional. Draft read tensors remain the
same persistent carrier tensors, while replacing full write/query attributes on
the final layer cannot mutate the private validation view.

### 2.3 Bind sequence

`DraftWindowGraphBindingProvider.bind_read_carrier()` performs:

```text
validate private view against Target recursively
validate private view uses Window table/length carrier
validate final metadata uses Window table/length carrier
validate final metadata uses canonical full write/query identity
validate canonical owners were not mutated
publish final metadata with private isolation_view
```

### 2.4 Store sequence

`DraftMetadataStore.publish(..., isolation_view=...)` retains its original eager
behavior when no view is supplied. Only the experimental Graph build supplies a
pre-restore view. The store validates that view and stores the final metadata.

This is a scoped extension to the P3 lifecycle, not a relaxation of eager
isolation.

## 3. Explicit validator responsibilities

| Validator | Input | Proves | Must not prove |
|---|---|---|---|
| `validate_draft_metadata_isolation` | pre-restore private view | no mutable Draft-private alias into Target | canonical full write identity |
| `_validate_metadata_uses_read_carrier` | private and final views | Window table and exact lengths use the registered backing | slot/positions/query ownership |
| `_validate_metadata_uses_carrier` | final view + write snapshot | read carrier plus exact canonical full write/query identity | recursive private isolation after canonical restore |
| `_validate_write_side_unchanged` | canonical reference/snapshot | content and identity remained stable | backend device execution |

## 4. Rejected alternatives

### Clone full carriers

Rejected because it changes ownership and may decouple the physical KV write
mapping from the canonical full table.

### Broad field-name exemption whitelist

Rejected as the primary design because a recursive validator with exclusions
would be fragile under metadata evolution and could accidentally exempt nested
Draft-private state.

### Disable Target isolation for Graph

Rejected because it would allow a real Window table/length alias to pass.

### Mutate Target metadata temporarily

Rejected by the repository and Frozen Design constraints.

## 5. Resulting ownership model

```text
Canonical FullSource ------------------------------+
                                                    |
BlockTables.slot_mappings -> canonical slot --------+--> final Draft metadata
input_buffers.positions -> canonical positions -----+
input_buffers.query_start_loc -> canonical query ----+

P3 workspace Window table ------------------------------> final Draft metadata
P3 workspace device exact ------------------------------> final Draft metadata
P3 workspace CPU exact/upper ----------------------------> final Draft metadata

Target metadata ---------------- no alias ----------------> private_isolation_view
```

The final Draft metadata can share only the canonical write/query owners that
are independently checked against the source snapshot.

## 6. Observability design included in the same repair

The next A3 campaign must not confuse host metadata with actual operator
binding. The repair therefore introduces typed, default-off evidence records:

- capture operator boundary;
- task-update operator boundary;
- G4 canonical/write/Target oracle record;
- replay submission event;
- existing backend update event;
- proposal retirement record;
- machine-readable artifact schema v2.

Each operand record is labelled `HOST_OPERATOR_BOUNDARY_FACT`. It is not called
a physical memory transaction. CANN/msprof/msprobe remains mandatory for G3.

## 7. No Graph semantic change

- public Graph user Gate remains frozen;
- characterization remains behind
  `VLLM_ASCEND_EXPERIMENTAL_DRAFT_WINDOW_GRAPH=1`;
- artifact output is optional and default-off;
- replay/consumer/update ordering is not moved;
- no global synchronization is inserted;
- no vLLM code changes;
- no Batch A feature is enabled.

## 8. Acceptance conditions

The design is locally accepted only if:

- the real-owner regression is green;
- private read alias remains red/fail-closed;
- canonical full table is unchanged;
- slot/positions/query are same object/storage and same values;
- Window read table/length use the private persistent backing;
- host A/B/A rejects stale identity;
- operator-boundary records do not claim physical reads;
- G5 records events without redefining completion.

All conditions are covered by the tests recorded in
`P7X_Graph_Base_Fix_Test_Report.md`.
