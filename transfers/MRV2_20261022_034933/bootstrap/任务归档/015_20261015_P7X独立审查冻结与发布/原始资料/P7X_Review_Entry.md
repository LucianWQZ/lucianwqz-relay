# P7-X Independent Review Entry

## Review target

```text
base: 4753742ab181920292c504a79eedecf9b428ae1b
implementation: 7e88db6ed31e7965f526ea6f49cc17101f4a65b4
tree: 71800e2e250f0b4dc51aede643eebff55e39b404
branch: feature/p7x-nongraph-completion
vLLM: 84030bbe3d74d99bad477a3d2e37a973ccd8865c, clean/unchanged
```

Read in this order:

1. `P7X_NonGraph_Required_Delivery_Manifest.md`
2. `P7X_NonGraph_Source_Preflight.md`
3. `P7X_NonGraph_Implementation_Notes.md`
4. `P7X_NonGraph_Capability_Matrix.md`
5. `P7X_Report1_Assumption_Register.md`
6. provider/parallel/prefix/async/mixed specs
7. `P7X_Original_Commit_Manifest.md`
8. `P7X_Full_Diff.patch`
9. `P7X_Test_Results.md`

## Production facts to reproduce

- CONFIG_OFF/FORCED_OFF return before P7-X allocation.
- Graph and COMPATIBILITY hardware reject before FullSource.
- ordinary TP is explicit replicated semantics with rank identity, never
  `V/world_size`.
- mixed rows share one generation but have immutable row-wise descriptors.
- prefix residency comes from current canonical source + valid counts.
- async lanes own independent P3 backing and retain metadata until completion.
- uncompressed DSA/DSA-CP uses actual builder/ratio facts; compressed DSA rejects.
- Target, positions, query layout, canonical table, slot and KV writes are unchanged.

## Source-derived contracts, not NPU facts

- TP logical read visibility is replicated per rank.
- DSA-CP derives local state from common metadata.
- event record/query ordering is correctly represented by the host state machine.
- mixed metadata can carry per-row full/window reads.

These require Node101 confirmation and are enumerated in the assumption register.

## Deliberately unresolved

- exact GLM5.2 and Qwen checkpoint/backend/group composition;
- physical NPU read-set, stream/event completion and performance;
- async Eagle3 and async DSA/DSA-CP;
- compressed DSA/QLI, SFA, MLA, native/recycling providers;
- live homogeneous/heterogeneous multi-group bundle;
- DP/PP/PCP/DCP/SP/FlashComm combinations outside source-proven DSA-CP.

## Review discipline

Do not downgrade a precise `REPORT1_RUNTIME_DEPENDENT` row merely because it is
not green, and do not accept a positive row without tracing the real consumer.
Any static bug must be fixed locally in a separate review-fix commit. Do not log
into Node101, read a nonexistent Report1, modify vLLM, or reopen Graph during
this review.
