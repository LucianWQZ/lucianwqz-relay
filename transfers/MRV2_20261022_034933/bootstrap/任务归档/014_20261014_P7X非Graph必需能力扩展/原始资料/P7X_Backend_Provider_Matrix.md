# P7-X Backend Provider Matrix

| Layout / consumer | Source table | Length carrier | Native visibility | Derived owner | Local state | Reason / next evidence |
|---|---|---|---|---|---|---|
| dense GQA/FIA | canonical kernel-block FullSource | Window exact + CPU exact/upper | full attention over supplied read view | existing Ascend builder | `LOCAL_STATIC_READY` | P4 carrier; NPU physical reads remain |
| DSA native/SWA ratio <=1 | canonical kernel-block FullSource plus current allocated valid extent | common Window exact/upper | backend SWA/SAS intersects common view | actual `AscendDSAMetadataBuilder` | `LOCAL_STATIC_READY` | NPU derived metadata/read-set required |
| DSA-CP ratio <=1 | same canonical source/current extent | common Window exact/upper then local derivation | DSA native + CP-local operator | actual `AscendDSACPMetadataBuilder` | `LOCAL_STATIC_READY` | NPU local ranges/comm required; Window-OFF shared builder regression mandatory |
| compressed DSA ratio >1 | compressed/indexed state not representable by direct-prefix source | unresolved | compressor/QLI | shared backend buffers | `SOURCE_BLOCKED` | dedicated provider/lane owner required |
| SFA main | unresolved per-token indexed source | per-token visible counts required | sparse top-k/index filtering | SFA builder/backend | `REPORT1_RUNTIME_DEPENDENT` | exact runtime consumer and persistent buffers |
| SFA indexer | index table/translation unresolved | indexer-specific | index translation | indexer owner | `REPORT1_RUNTIME_DEPENDENT` | operator-level contract |
| MLA | source/operand composition unresolved | exact/upper semantics differ from FIA | MLA backend | MLA builder | `REPORT1_RUNTIME_DEPENDENT` | actual Draft route and D2H/lifetime |
| native SWA/circular | physical resident set may be gapped | cannot be scalar-min | native mask/circular layout | backend | `REPORT1_RUNTIME_DEPENDENT` | resident-set provider |
| recycling/offload | canonical logical order plus dynamic residency | per-query intersection | eviction/in-flight state | recycling manager | `REPORT1_RUNTIME_DEPENDENT` | stable resident snapshot and completion owner |
| unknown/custom | none | none | none | none | `REPORT1_RUNTIME_DEPENDENT` | fail before FullSource; no dense fallback |

## Provider rules

1. Backend identity is taken from the actual attention group and builder.
2. Source geometry failures are separate from old conservative P2 capability
   failures; P7-X may close a conservative route Gate but never erase geometry.
3. A DSA provider requires an actual compression ratio. Ratio >1 is rejected.
4. Multi-group inventory may describe many groups, but the live P3/P4 source
   capability still requires one executable group. This prevents a fake
   multi-group PASS.
5. Final visibility is a set intersection, never scalar `min`.
6. Backend-derived buffers must not alias workspace, canonical FullSource or
   Target metadata and must live through the relevant completion.
7. Current valid block count is not a generic physical-residency oracle. Any
   offload/SFA/recycling route needs an explicit resident-set provider.
