# Next Action — P7-X Graph Base G1–G5

```text
NEXT_ACTION = RETURN_TO_LOCAL_CODEX
```

## One-line finding

The characterization candidate installs and captures correctly on A3/MRV2, but
its first real draft replay fails deterministically because Draft metadata must
simultaneously use the canonical full write carriers and share no mutable
storage with Target metadata. On the real vLLM path those canonical carriers
are the Target metadata objects.

## Exact failure

```text
ValueError: Draft metadata mutable storage aliases Target metadata

vllm_ascend/worker/v2/spec_decode/draft_window_graph_characterization.py:529
  prepare_parallel_draft_window_graph_characterization -> provider.bind_read_carrier

vllm_ascend/worker/v2/spec_decode/draft_window_graph.py:818
  bind_read_carrier -> validate_draft_metadata_isolation

vllm_ascend/worker/v2/spec_decode/draft_window.py:2585
  validate_draft_metadata_isolation -> raise ValueError
```

Reproduction: `negative/B/result.json` and `negative/B/driver.log`.

## Required local fix

Do not patch the device. Choose one consistent contract locally:

### Option A (preferred): separate the two invariants

1. Validate Draft-private isolation **before** restoring the canonical
   write-side references.
2. Keep `_validate_metadata_uses_carrier` as the sole assertion that the full
   write/query carriers are the exact canonical objects.
3. Do not feed the canonical write-side references into the isolation oracle.

### Option B: explicit exemption set

Exempt only the known immutable full write carriers
(`slot_mapping`, `positions`, `query_start_loc`, `actual_seq_lengths_q`,
`attn_state`, `num_actual_tokens`, `causal`) from
`validate_draft_metadata_isolation`, while continuing to reject every other
shared mutable object/storage.

Either option must preserve the design invariant:

- slot_mapping is never windowed;
- Draft KV writes go through the full block table;
- only FIA Draft reads are windowed.

Do **not** change the public Graph Window capability gate.

## Required test addition

Add a CPU/UT case where `target_metadata` is built the way the real engine builds
it:

- target `slot_mapping` is the same tensor object/storage as
  `block_tables.slot_mappings[...]`;
- target `positions` is `input_buffers.positions`;
- target `query_start_loc` is `input_buffers.query_start_loc`.

The existing synthetic `_target_metadata()` uses independent tensors and cannot
catch this class of defect.

Suggested test names:

- `test_real_target_metadata_sharing_is_allowed_for_full_write_carriers`
- `test_draft_private_fields_still_reject_target_storage_alias`

## Device re-run acceptance

After the local fix, re-run in this order on node-39-101:

1. UT sanity (three files).
2. A0 / A1 controls (must be unchanged).
3. B capture + bind (must emit BOUND, REPLAY, CONSUMER, UPDATE).
4. G1 exact operand-address evidence.
5. G2 A/B/A'.
6. G3 read-set oracle.
7. G4 OFF/ON write-side comparison.
8. G5 NPU timeline.

Only all-PASS may yield:

```text
BASE_GRAPH_DEVICE_ARCHITECTURE = PASS
```

## Environment notes for the re-run

- Use a verified free logical die. On this host logical dies 0–7 were occupied
  by another tenant for part of the campaign; logical dies 8–15 were free.
  `npu-smi` card labels are **not** logical die indices.
- Wait for HBM release before restarting after a failed run.
- Keep `VLLM_ENABLE_V1_MULTIPROCESSING=0` only if in-worker evidence is needed.
- Keep `VLLM_USE_V2_MODEL_RUNNER=1` and verify the live class, not just the env.
