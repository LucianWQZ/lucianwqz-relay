# MRV2 Draft Sliding Window — P8-E Release Risk Register

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

| ID | Risk | Evidence / current control | Likelihood | Impact | Owner / required action | Release state |
|---|---|---|---|---|---|---|
| R-01 | Mixed prefill/decode can raise and terminate EngineCore | Source hard reject before epoch; node133 observed service-wide abort; no admission restriction | High under general serving | Critical | Product + scheduler owner chooses general support or safe early single-active scope; return to P7 if implementation needed | `RELEASE_BLOCKER` |
| R-02 | P7-final positive routes lack NPU rerun | P7 is static only; P4 Eagle3 evidence is old SHA | Certain evidence gap | High | Execute comprehensive campaign at `4753742...` | `RELEASE_BLOCKER` |
| R-03 | DFlash/DSpark Window ON have no NPU correctness evidence and no owner-signed model pair in this package | P4a and P7 static tests only; campaign model identities remain owner inputs | Certain evidence gap | High | Owner supplies immutable target/draft identities, then run both methods including DSpark K/K+1 | `RELEASE_BLOCKER` if owner marks mandatory |
| R-04 | Physical kernel read-set unproven | Existing Eagle3 evidence is L4 operator arguments, not L5 | Medium | High | Approved kernel/profiler oracle | OPEN |
| R-05 | Device lifetime/no-early-overwrite unproven | Host lease tests and NO_SYNC equality do not establish happens-before | Medium | High | Real event/stream timeline plus A/B/A pressure | OPEN |
| R-06 | Controlled multi-request, reorder and persistent row reuse unproven | Four old attempts became mixed; sequential A→C→A passed | High | High | Construct pure-decode batch and instrument idx_mapping/owner | `RELEASE_BLOCKER` for general serving |
| R-07 | Independent slot oracle incomplete | Static contract strong; old trace was truncated | Medium | High | Complete untruncated full-table/position slot recomputation | OPEN |
| R-08 | Owner mandatory scope unresolved | Matrix has no signed mandatory/optional selection | High | High | Owner signs methods/devices/topology/serving/evidence thresholds | `RELEASE_BLOCKER` |
| R-09 | STANDARD family could be overgeneralized across A2/A3/A5 | Typed family Gate exists; only old A2 evidence exists; A3 reports missing | Medium | High | Separate campaign per selected device | OPEN |
| R-10 | 310P class inheritance could leak a Window route after future drift | P7 typed COMPATIBILITY Gate rejects before FullSource; the 310P patch separately delegates non-MTP startup to the baseline factory | Low | High | Preserve P8 hardware-family regression in CI; do not rely on an incorrect MTP-only startup assumption | CONTROLLED |
| R-11 | Async host model mistaken for live support | Pool has no production installation and capability returns STATIC_READY | Medium communication risk | High | Keep live gate; return to P7 for real binding/event | CONTROLLED / unsupported |
| R-12 | DCP math mistaken for parallel support | Pure helper is correct; all DCP>1 routes fail closed | Medium communication risk | High | State `MATH_READY ≠ LIVE_SUPPORT` in matrix and docs | CONTROLLED / unsupported |
| R-13 | Complex backend approximation could violate native/resident visibility | DSA/SFA/MLA/native/recycling all fail before FullSource | Low in current code | Critical if Gate removed | Require typed intersection/provider before any enablement | CONTROLLED / unsupported |
| R-14 | Prefix cache or multi-group silently enabled by future refactor | Explicit P7 Gate and tests | Low | High | Keep preallocation negative tests | CONTROLLED |
| R-15 | Graph static carrier misreported as Graph support | P6A freeze, no provider installation, method/capability gates | Medium communication risk | Critical | Keep Graph documents and separate status vocabulary; owner-only resume | `FULL FEATURE BLOCKER` |
| R-16 | Vendor-local metadata assembly drifts from upstream | AST/signature drift guards and OFF differential tests | Medium over time | High | Fail CI on drift and re-review exact baseline | CONTROLLED at pinned baseline |
| R-17 | Performance regression from D2H/H2D/synchronization | No P7 profiler evidence | Unknown | High | Execute component and A/B/A performance plan | `RELEASE_BLOCKER` pending thresholds |
| R-18 | Freeze package cannot restore exact source | Addressed by diff check, format-patch git-am, incremental-bundle fetch from exact base, and tree equality | Low after verification | High | Preserve the bundle's `841dc6cc...` prerequisite; re-run verification after any artifact change; validate SHA256SUMS | Must PASS for local acceptance |
| R-19 | Debug code contaminates production or is over-relied upon without an auditable diff | Historical server debug SHAs are not production ancestors; debug SHA `2a485613...` is not present in the local production object database or bundle | Low | High | Preserve separate lineage; scope claims to archived server evidence and mark instrumentation source inspection unavailable | CONTROLLED with evidence limitation |
| R-20 | Host environment failures hide regressions | 7 VWN failures stop in upstream selector; full config suite lacks generated build info | Medium | Medium | Record as failure/block, compare untouched paths, rerun on configured CI/NPU host | OPEN environment limitation |

## Escalation thresholds

- `RETURN_TO_P7_OR_OWNER`: any fix requires scheduler redesign, mixed-serving
  implementation, complex backend/parallel data plane, live async binding, or Graph
  capture work.
- Stop NPU campaign immediately on Target/write mutation, silent fallback, stale
  generation, source alias, wrong operator operand, or early backing reuse.
- No release state can become READY while R-01 or R-08 is open.

```text
EAGER RELEASE: HOLD
FULL FEATURE RELEASE: HOLD
```
