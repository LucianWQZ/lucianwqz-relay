# MRV2 Draft Sliding Window — P6 Replay / Consumer / Update Timeline

Review-final code: original P6 `20673a1ced10160d8f8d1aaa79230e6ce0409d3c`,
review-fix `7599497ab2694c4cf343f61f82f449980d8bad93`.

## Source-verified order

The exact P5 Final/P6 checkout has the same method-level ordering for Eagle3 and the shared
DFlash/DSpark manager:

```text
build_draft_attn_metadatas()
  -> explicit carrier consume (P6 when provider exists)
  -> pre-replay metadata identity/bucket/mode validation
  -> current stream / update stream ordering
  -> super().run_fullgraph()                 # REPLAY
  -> Python-side return observation          # CONSUMER source point
  -> build DraftWindowGraphUpdateBinding
  -> update_full_graph_params()
  -> resolve backend impl + builder
  -> validate/attribute exact carrier        # UPDATE source point
  -> impl_cls.update_graph_params(...)
```

This differs from the historical design assumption that an update necessarily precedes and feeds
the same replay. P6 does not rewrite the existing Graph manager schedule.

## Typed timeline

`DraftWindowGraphReplayUpdateTimeline` contains:

| Field | P6 value | Meaning |
|---|---|---|
| `materialized_generation_ids` | known | Generations copied from validated P3 state into persistent carrier buffers |
| `submitted_replay_generation_ids` | known | Carrier metadata object set selected before replay |
| `consumer_generation_ids` | `None` | Python cannot attest which generation the captured NPU consumer read |
| `update_source_generation_ids` | known at UPDATE | Generations supplied to backend update entry |
| `update_effective_generation_ids` | `None` | Source order does not reveal the effective launch |
| `status` | `NEEDS_NPU_TIMELINE` | Required evidence is explicitly open |

`assert_update_effective_for()` always hard fails in P6. This prevents a static test from declaring
same-replay or next-replay semantics.

## Why Python source is insufficient

`AscendAttentionBackendImpl.update_graph_params()` updates graph task parameters inside task-update
boundaries, but the host call position alone does not prove:

- whether replay N had already consumed old operands;
- whether the update applies to replay N+1;
- whether task launch/update is deferred by the NPU runtime;
- whether table and length operands become effective atomically;
- which stream event protects carrier rewrite/reuse.

## One-step-lag policy

P6 tests lock the host ordering and reject all of these unsupported claims:

```text
update_source_generation == consumer_generation
update_effective_generation == submitted_generation
update always affects next replay
```

The carrier metadata object and exact generation are checked before replay and again at UPDATE, so
Python-side accidental one-step substitution is detected. Device-effective one-step lag remains an
NPU question.

Independent Review Q-02 was adjudicated `DEFERRED_TO_NPU`: manager-level tests prove that the typed
binding reaches the real manager call point, and a separate test invokes the real
`update_full_graph_params` backend-resolution entrance. Neither test can populate
`consumer_generation_ids` or `update_effective_generation_ids`; both remain `None`. The review-fix
does not rename events or infer that UPDATE(N) affects replay N or N+1.

## Minimum NPU timeline experiment

For one exact single-card dense-GQA route:

1. capture with instrumented table/length operand addresses;
2. run A, B, A' with distinct table/length fingerprints and monotonically increasing epochs;
3. trace replay submission, task update begin/end, attention launch, and completion events;
4. record the operand address/content observed by each attention launch;
5. prove table and exact length correspond to the same generation;
6. prove update effective generation (same, next, or recapture semantics);
7. prove happens-before before reusing carrier/workspace backing;
8. compare physical read-set and Target/write invariants.

Until that experiment passes:

```text
P6 HOST A/B/A: PASS
P6 NPU A/B/A: NOT VERIFIED
P6 UPDATE EFFECTIVE GENERATION: NEEDS_NPU_TIMELINE
GRAPH WINDOW USER GATE: STILL FAIL-CLOSED
```
