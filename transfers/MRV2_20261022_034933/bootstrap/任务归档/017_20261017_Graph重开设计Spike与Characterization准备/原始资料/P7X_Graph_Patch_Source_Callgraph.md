# P7-X Graph Patch Source Callgraph

## Status and exact source

- Investigation branch: `spike/p7x-draft-window-graph-patch`
- vLLM-Ascend base: `1b7215c37d1e3c9d1edac1fc20bcad26917ca251`
- vLLM-Ascend base tree: `9a6c38c0e92853b462cd1f05aa5f70244f82a72f`
- pinned vLLM: `84030bbe3d74d99bad477a3d2e37a973ccd8865c`
- pinned vLLM tree: `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee`
- Scope: DFlash and eligible DSpark startup capture only. Eagle3, complex
  backends, parallel topologies, async, prefix, and product enablement are out
  of scope.

## Existing worker patch installation

```text
NPU worker initialization
  -> vllm_ascend.patch.worker.patch_v2.patch_dflash_speculator import
  -> upstream dflash.cudagraph.build_attn_metadata
       = vllm_ascend.worker.v2.attn_utils.build_attn_metadata
  -> upstream dflash.speculator.DFlashCudaGraphManager
       = vllm_ascend.worker.v2.spec_decode.dflash.aclgraph.DFlashAclGraphManager
  -> upstream dflash2 selector kernel
       = Ascend selector implementation
```

The patch is installed once during worker startup. It is not a per-capture
mutable function swap.

## DFlash / DSpark construction and ownership

```text
AscendDFlashSpeculator / AscendDSparkSpeculator
  -> upstream DFlashSpeculator / DSparkSpeculator
  -> DraftModelSpeculator.__init__
       creates self.input_buffers = InputBuffers(...)
  -> DraftModelSpeculator.set_attn
       stores self.target_input_buffers separately
  -> init_cudagraph_manager
       draft enforce_eager=True => Draft manager mode NONE
       otherwise upstream normalizes supported full mode to FULL_DECODE_ONLY
  -> patched DFlashAclGraphManager instance
```

The object passed to the DFlash capture manager is
`speculator.input_buffers`. It is not `speculator.target_input_buffers`.
`InputBuffers` has an ordinary instance `__dict__`, so an explicitly scoped,
typed context can be attached to the Draft-private object without a module
registry.

## Startup capture chain

```text
AscendDFlashSpeculator.capture
  / AscendDSparkSpeculator inherits the same parallel-draft capture route
  -> query_cudagraph_manager.capture(
       forward_fn=self._generate_draft,
       input_buffers=self.input_buffers,              # Draft-private
       block_tables=self.block_tables,                # canonical full owner
       attn_groups=self.attn_groups,
       kv_cache_config=self.kv_cache_config,
       max_model_len=self.max_model_len)
  -> DFlashAclGraphManager.capture
       -> communicator_switch
       -> model_capture_wrapper
       -> upstream DFlashCudaGraphManager.capture
          -> generic CudaGraphManager.capture
             -> each BatchExecutionDescriptor, warmup and capture passes
             -> create_forward_fn(desc, warmup)
                -> _prepare_dflash_inputs_to_capture(
                     num_reqs=desc.num_reqs,
                     num_tokens=desc.num_tokens,
                     input_buffers=Draft-private InputBuffers,
                     block_tables=canonical full BlockTables,
                     skip_attn=(desc.cg_mode == PIECEWISE))
                   -> InputBatch.make_dummy
                   -> BlockTables.get_dummy_block_tables       # full read baseline
                   -> BlockTables.get_dummy_slot_mappings      # full write slots
                   -> build_slot_mappings_by_layer             # full write carrier
                   -> build_attn_metadata
                      current worker patch resolves to Ascend builder
                   -> AttentionState(metadata, full layer slots)
                -> forward_fn(CUDAGraphMode.NONE/PIECEWISE)
                   -> Draft model operator capture
```

The helper's `block_tables` and `slot_mappings` arguments to
`build_attn_metadata` are already independent. A Window-aware helper can use
persistent Window table/length carriers while continuing to derive slot
mapping from canonical `BlockTables`.

## Descriptor semantics

For DFlash/DSpark, upstream `DFlashSpeculator.init_cudagraph_manager` converts
a supported requested full mode to `FULL_DECODE_ONLY`. Generic
`CudaGraphManager` then creates decode descriptors with `desc.cg_mode == FULL`.
PIECEWISE is explicitly unsupported by DFlash and is retained only as a
defensive helper contract.

The helper sees `(num_reqs, num_tokens, skip_attn)`. In the current P6
single-lane DFlash/DSpark scope this maps to fingerprint
`capture_bucket=(num_reqs, num_tokens)` and effective descriptor mode
`FULL` (`skip_attn=False`) or `PIECEWISE` (`skip_attn=True`). Duplicate
matches must hard fail; no first-match fallback is allowed.

## Runtime replay/update chain (frozen)

```text
propose
  -> prepare_dflash_inputs using canonical full table
       positions/query state: full absolute
       slot_mapping/KV write: canonical full
  -> build_draft_attn_metadatas
       P6 explicit Window metadata when a provider/carrier exists
       baseline metadata otherwise
  -> DFlashAclGraphManager.run_fullgraph
       -> validate submitted metadata and capture bucket
       -> REPLAY observation
       -> super().run_fullgraph(desc)                  # actual replay
       -> CONSUMER observation
       -> build_draft_window_graph_update_binding
       -> update_full_graph_params
       -> backend.update_graph_params                 # task rebinding
```

The order remains:

```text
metadata rebuild -> REPLAY -> CONSUMER -> UPDATE
```

This spike must not reorder it. Static source cannot prove whether UPDATE(N)
affects replay N or N+1; `NEEDS_NPU_TIMELINE` remains authoritative.

## Target Graph versus Draft Graph

The Ascend DFlash/DSpark `init_cudagraph_manager()` changes only the Draft
`query_cudagraph_manager` mode when `speculative_config.enforce_eager` is true.
It does not change the Target model runner graph mode. Existing Phase 1/2
evidence used Target `FULL_DECODE_ONLY` with Draft eager and Window ON.

- `CAN_TARGET_GRAPH_WITH_DRAFT_EAGER = YES`
- `DRAFT_WINDOW_GRAPH_REQUIRED_FOR_EAGER_FEATURE_DELIVERY = NO`

## Frozen boundaries

- Window changes Draft read table/length only.
- canonical full table, full slot mapping, absolute positions, query layout,
  physical KV write, and Target state stay unchanged.
- pinned vLLM is read-only.
- no module-global runtime state, ContextVar, Target-owner swap, canonical-owner
  mutation, or replay/update reordering.
- user-visible Graph Window gate remains fail closed.

