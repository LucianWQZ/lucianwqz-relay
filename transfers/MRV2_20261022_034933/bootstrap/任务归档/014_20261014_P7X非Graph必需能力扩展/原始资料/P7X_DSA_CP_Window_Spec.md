# P7-X DSA-CP Window Specification

## Source facts

The live route is identified by the actual attention group and metadata-builder
instance, never by model name. A candidate requires:

- layout inventory classified as DSA;
- builder class `AscendDSACPMetadataBuilder` when DSA-CP is enabled;
- one executable gid;
- valid logical/kernel geometry;
- actual `compressor_ratio` present and <= 1;
- Graph mode NONE and STANDARD hardware family.

Compressed ratio >1 is `SOURCE_BLOCKED`; missing ratio is
`REPORT1_RUNTIME_DEPENDENT`.

## Read path

```text
canonical FullSource kernel-block table
  -> absolute Window descriptor [S,E)
  -> stable common Window table + exact/upper
  -> build_attn_metadata shared DSA request metadata
  -> AscendDSACPMetadataBuilder
  -> local query/seq/index/SAS state
  -> DSA-CP operator
```

The P7-X change to `attn_utils.py` treats DSA-CP as a DSA consumer of
`common_ratio_to_sas_metadata` and `num_actual_reqs`. This is required by the
real builder contract and is a shared MRV2 metadata fix: it also executes when
Window is OFF. CONFIG_OFF DSA-CP is therefore a mandatory regression and NPU
case (`DSACP-00`). Positions, query layout, slot mapping and canonical
tables still come from the baseline owners.

The additional-config bit is the request, not final authority. Window topology
claims DSA-CP only when the request is true and the validated
`vllm_ascend.utils.enable_dsa_cp()` authority used by backend selection is also
true. A raw true/effective false route remains ordinary replicated semantics.

## Visibility semantics

```text
V_final = V_draft ∩ V_native_DSA_SWA ∩ V_resident
```

P7-X narrows the common table/length. Native DSA/SWA logic remains backend-owned
and performs the second intersection. Prefix valid counts provide residency.
No `min(W, native_window)` shortcut is used.

## Lifetime

Serialized eager uses the existing P3 generation/lease/store. Async DSA-CP is
not admitted because SAS/local/index buffers are builder-owned shared state and
have not yet been made lane-owned. That combination is
`REPORT1_RUNTIME_DEPENDENT`, not silently serialized.

## Static evidence and NPU gaps

Tests prove actual builder classification, shared kwargs, uncompressed source
construction, compressed pre-allocation rejection, topology identity and full
write state. Node101 must still prove local metadata values, communication,
physical reads, Target/slot equality and lifetime. GLM5.2's actual backend,
ratio, gid count and DSA-CP topology are Report1 inputs.
