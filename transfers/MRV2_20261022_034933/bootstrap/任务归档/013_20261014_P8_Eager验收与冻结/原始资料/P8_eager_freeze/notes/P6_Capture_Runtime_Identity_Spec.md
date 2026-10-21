# MRV2 Draft Sliding Window — P6 Capture / Runtime Identity Specification

Review-final code: original P6 `20673a1ced10160d8f8d1aaa79230e6ce0409d3c`,
review-fix `7599497ab2694c4cf343f61f82f449980d8bad93`, final tree
`b4f7d12bd24b0a7632f9e606b29703a7c96278de`.

## 1. Why two namespaces are mandatory

Startup graph capture occurs without a live request, proposal, `idx_mapping`, or
`mapping_epoch`. P3/P5 `DraftWindowGenerationIdentity` is request-generation state and therefore
cannot represent capture. P6 explicitly separates:

```text
DraftWindowGraphCaptureIdentity       DraftWindowGenerationIdentity
--------------------------------      -----------------------------
startup graph program/bucket          live proposal/batch
no request IDs                        ordered request fingerprint
no mapping_epoch                      caller-owned mapping_epoch
stable carrier address                materialized P3 generation
capture consumer ordinal              proposal phase / AR step
```

The types are not interchangeable. Passing a runtime generation to capture is a hard failure;
P6 never invents `generation_id=0`, fake request IDs, or fake epochs.

## 2. Capture identity

`DraftWindowGraphCaptureIdentity` contains:

| Field | Meaning | Freshness role |
|---|---|---|
| `fingerprint` | Full route/program/topology compatibility key | Capture/runtime compatibility, not request freshness |
| `execution_lane` | Stable serialized execution lane | Rejects wrong-lane reuse |
| `consumer_ordinal` | Per-route metadata consumer index | Gives deterministic multi-consumer ordering |
| `provider_schema_version` | Carrier schema version (`2` in P6) | Rejects incompatible provider layouts |
| `backing_identity` | Owner plus table/length addresses and geometry | Detects address/shape/dtype/device drift |

Registration allocates provider-owned persistent buffers only after an explicit eligible provider
exists. CONFIG_OFF, FORCED_OFF, unsupported candidates, and normal fail-closed Graph execution do
not install the provider and allocate nothing.

## 3. Runtime generation identity

The runtime side remains P3-owned and carries:

- generation id;
- caller-owned monotonic `mapping_epoch`;
- ordered request fingerprint;
- actual/padded request count;
- normalized method and global gid;
- provider/source identities and versions;
- execution lane;
- proposal phase and step.

P6 projects these fields into `DraftWindowGraphBindingIdentity`, adding `proposal_id` and the exact
Graph route. This identity is attached only after P3 `DraftMetadataInputs.validate_for()` succeeds.

## 4. Compatibility relation

Capture and runtime identities are compatible only when all relevant facts agree:

1. method and method-specific route;
2. global gid;
3. padded request geometry;
4. lane;
5. route fingerprint, including graph mode, backend/builder, layout, bucket, query width, static K,
   W, block geometry, topology, async, and prefix-cache flags;
6. registered backing identity remains unchanged;
7. runtime P3 workspace and canonical FullSource ownership remain valid.

Compatibility does not merge the namespaces and does not prove startup capture used the backing.

## 5. State machine

```text
EMPTY (registered stable backing)
  -> BOUND (one validated runtime generation copied; full write/query reference bound;
            Draft-private metadata built)
  -> SUBMITTED (exact metadata object set selected for replay)
  -> UPDATED (actual standard FIA UPDATE entrance attributed)
  -> BOUND (later generation may reuse the same address after explicit rebinding)
```

An active `BOUND` or `SUBMITTED` carrier cannot be overwritten. Old generation handles fail after
rebinding, including A → B → A' ABA where A and A' have equal semantic contents but different
generation/epoch.

`DraftWindowGraphWriteSideReference` is not a third freshness namespace. It is an immutable typed
reference attached to the runtime binding and contains the canonical full slot-mapping view,
positions owner, query layout, attention state, actual token count, and causal contract. Its tensor
addresses/geometry and mutation versions are snapshotted at bind and revalidated after metadata
build and at UPDATE. Runtime freshness still comes only from P3 generation + mapping_epoch.

`UPDATED` means the update entrance was validated; it does **not** prove the task consumed the
update or establish its effective replay generation.

## 6. Hard-failure examples

- capture descriptor or bucket mismatch;
- backend/builder/gid/layout mismatch;
- phase/step/method mismatch;
- request fingerprint or `mapping_epoch` mismatch across consumers;
- stale generation lookup after A/B/A';
- carrier metadata replaced by Target-derived metadata;
- noncanonical or Window-derived slot mapping presented as full write state;
- full query/positions owner replacement or in-place mutation during metadata build;
- backing address/geometry mismatch;
- attempt to use runtime generation as startup capture identity;
- attempt to claim UPDATE effective generation without NPU timeline evidence.

## 7. Current limitation

The pinned vLLM capture builder owns dummy metadata internally. Ascend can define and validate the
capture identity, but cannot inject this backing without an upstream change, shared-state mutation,
or duplicated capture builder. All are forbidden by the current boundary. Therefore:

Installing the runtime provider before this seam is resolved intentionally makes startup capture
hard fail. This is an explicit safety contract, not an enablement route and not a fake capture
identity.

```text
P6 CAPTURE IDENTITY: PASS (host/static)
P6 CAPTURE PATH: BLOCKED
GRAPH WINDOW USER GATE: STILL FAIL-CLOSED
```
