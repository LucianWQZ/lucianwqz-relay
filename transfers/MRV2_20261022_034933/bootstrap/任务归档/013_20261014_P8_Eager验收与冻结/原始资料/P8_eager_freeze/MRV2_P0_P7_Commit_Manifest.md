# MRV2 Draft Sliding Window — P0–P7 Final Commit Manifest

> **EAGER TRACK: ACTIVE DELIVERY CANDIDATE**  
> **GRAPH TRACK: FROZEN AT P6/P6A**  
> **GRAPH REQUIREMENT: PRESERVED**  
> **GRAPH USER GATE: STILL FAIL-CLOSED**

## Repository identities

```text
vLLM required SHA       84030bbe3d74d99bad477a3d2e37a973ccd8865c
vLLM required tree      f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee
vLLM-Ascend base        841dc6ccdb134eab7ad09008859834d0572ee83f
vLLM-Ascend final       4753742ab181920292c504a79eedecf9b428ae1b
vLLM-Ascend final tree  b7e525c3c9d45617ad1023ad45c6948c466a3631
final branch            feature/p7-eager-completion
delivery commits        16, linear
```

## Exact commit graph

```text
841dc6cc  base
└─ b12399ad  P1 policy/math/types
   └─ c58daea0  P1 review fix
      └─ 83579675  P2 inventory/FullSource/provider
         └─ fac84121  P2 review fix
            └─ feab28f5  P3 runtime ownership
               └─ 16727882  P3 review fix
                  └─ 0dd83e9f  P4a Ascend-only eager
                     └─ 4c1f6914  P4a review fix
                        └─ d0c88838  P4b Eagle3 static-K
                           └─ 1011e2c2  P4b review fix
                              └─ 266eec5d  P5 Graph binding foundation
                                 └─ 0702c89d  P5 review fix
                                    └─ 20673a1c  P6 graph read carrier
                                       └─ 7599497a  P6 review fix / Graph partial freeze
                                          └─ 7feb6def  P7 Eager capability contracts
                                             └─ 4753742a  P7 review fix / Final
```

## Per-commit change map

All commits have one parent. Ten commits contain a `Signed-off-by` trailer; six
historical P3/P4 commits (`feab28f5`, `16727882`, `0dd83e9f`, `4c1f6914`,
`d0c88838`, `1011e2c2`) do not. This freeze records that immutable history and does
not rewrite it. “Apply” means the commit is independently reviewable but must be
applied after all earlier rows because the types and tests build phase by phase.

| # | SHA / subject | Parent | Stat | Main production files | Tests | Phase / dependency |
|---:|---|---|---|---|---|---|
| 1 | `b12399ad` `feat(spec-decode): add MRV2 draft-window policy and math` | `841dc6cc` | 8 files, +1107/-1 | `spec_decode/__init__.py`, AR/DFlash/DSpark speculators, new `draft_window.py` | new policy/math suite; DFlash2/factory updates | P1; apply first |
| 2 | `c58daea0` `fix(spec-decode): address P1 draft-window review findings` | `b12399ad` | 4, +213/-16 | factory + `draft_window.py` | P1 regressions | P1 review fix; requires #1 |
| 3 | `83579675` `feat(spec-decode): add MRV2 draft-window source inventory` | `c58daea0` | 6, +1880/-8 | inventory/source/provider in `draft_window.py`; method owners | P2 inventory/provider tests | P2; requires P1 |
| 4 | `fac84121` `fix(spec-decode): address P2 draft-window review findings` | `83579675` | 2, +223/-39 | `draft_window.py` | P2 regressions | P2 review fix |
| 5 | `feab28f5` `feat(spec-decode): add MRV2 draft-window runtime ownership` | `fac84121` | 6, +1501/-18 | generation/workspace/lease/store; speculator owners | new runtime suite | P3; requires P2 |
| 6 | `16727882` `fix(spec-decode): address P3 draft-window review findings` | `feab28f5` | 2, +138/-14 | runtime ownership | Target/alias/error regressions | P3 review fix |
| 7 | `0dd83e9f` `feat(spec-decode): integrate MRV2 draft windows in Ascend eager path` | `16727882` | 12, +2160/-50 | `draft_window_eager.py`, DFlash/DSpark, attn builder/operator seams | P4a, attention, runtime | P4a; requires P3 |
| 8 | `4c1f6914` `fix(spec-decode): address P4a Ascend-only review findings` | `0dd83e9f` | 5, +323/-23 | P4a source/runtime | profile/Target/OFF/drift regressions | P4a review fix |
| 9 | `d0c88838` `feat(spec-decode): integrate MRV2 draft windows for Eagle3 eager` | `4c1f6914` | 5, +2250/-5 | `draft_window_eagle3.py`, AR speculator, P3 step extension | new Eagle3 suite | P4b; requires P4a |
| 10 | `1011e2c2` `fix(spec-decode): address P4b Eagle3 window review findings` | `d0c88838` | 5, +119/-44 | shared prefill classifier + Eagle3 exact carrier | kernel drift/parity/prefill regressions | P4b final |
| 11 | `266eec5d` `feat(spec-decode): add Ascend-only draft-window graph binding foundation` | `1011e2c2` | 7, +1333 | new `draft_window_graph.py`, Ascend graph manager observation seams | new graph-binding suite | P5 static foundation; user Gate remains closed |
| 12 | `0702c89d` `fix(spec-decode): address P5 graph binding review findings` | `266eec5d` | 2, +49/-6 | graph foundation | P5 regressions | P5 final |
| 13 | `20673a1c` `feat(spec-decode): add per-consumer draft-window graph read carriers` | `0702c89d` | 10, +2168/-71 | graph carrier, managers, compilation/update seams | new carrier suite + graph binding | P6 static replay/update contract |
| 14 | `7599497a` `fix(spec-decode): address P6 graph carrier review findings` | `20673a1c` | 3, +460/-106 | carrier/attribution/fail-closed | P6 regressions | P6 partial freeze; capture remains blocked |
| 15 | `7feb6def` `feat(spec-decode): add eager draft-window capability contracts` | `7599497a` | 6, +1690/-17 | new eager capability + async host modules; P3 topology propagation | new capability/async suites | P7 Eager inventory/host lifecycle |
| 16 | `4753742a` `fix(spec-decode): address P7 eager capability review findings` | `7feb6def` | 6, +204/-5 | hardware-family Gate, alias and topology enforcement | 310P/alias/topology regressions | P7 final |

## Changed-file inventory

The complete base-to-final range changes 28 Python files: 16 production files and 12 test
files. The binary-safe full diff in this package is authoritative. Key production
owners are:

- `draft_window.py`: P1 policy/math, P2 source/provider, P3 ownership and P7 topology;
- `draft_window_eager.py`: P4a live read path and isolation;
- `draft_window_eagle3.py`: P4b proposal/step path;
- `draft_window_graph.py`: P5/P6 host-static Graph contracts, still runtime-inert;
- `draft_window_eager_capability.py`: P7 matrix and topology fingerprint;
- `draft_window_async.py`: P7 host-only bounded lifecycle;
- DFlash/DSpark/AR speculators and Ascend metadata/operator adapters.

## Recovery dependencies

- Preferred offline path: begin with a repository containing exact base
  `841dc6cc...`, fetch the incremental bundle's
  `feature/p7-eager-completion` ref into a local branch, then checkout that branch.
  The bundle declares the base as a prerequisite because this source checkout is
  shallow; it is not a standalone-clone bundle.
- Review-preserving: checkout base `841dc6cc...`, then `git am` all 16 patches in
  lexical order.
- Emergency tree-only: checkout the clean base and apply the full diff. This loses
  commit authorship/messages and is not the preferred migration path.

## Explicitly excluded history

- vLLM prototype `0403469280c3d0f19c55cd1768e7e9d9e566a719` is a technical
  experiment and must never be delivered or required.
- Upstream-dependent Ascend prototype `e0dd8e8d14a287e4d5a69c54d7a617a6ae160529`
  is superseded and is not in this lineage.
- Server debug commits, including the terminal evidence SHA `2a485613...`, are not
  production ancestors and are not bundled as delivery history. That SHA is absent
  from the local object database and bundle, so its instrumentation diff is not
  independently source-auditable from this package; only the scoped archived server
  evidence may be cited.
- P6A produced no commit; it froze Graph through documentation and owner direction.

## Lineage assertion

`git rev-list --reverse --parents` proves each row's parent is the immediately
preceding row. No squash, rebase, debug merge, upstream patch, or P8 production
commit is present.

## P8 independent-review finalization

DeepSeek delivery review and Codex fact adjudication required documentation/evidence
corrections only. No production file, commit, parent, SHA or tree changed. The final
delivery remains the 16-commit lineage above at `4753742...` / tree `b7e525c3...`.
The regenerated freeze artifacts and clean-room report are indexed by the final
`SHA256SUMS`.
