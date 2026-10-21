# Repair4 server commands — PRE_PUBLICATION

Exact commit `aaa4632612503adb34d90b55c36eedcaf0848979` / tree `d39adc3de6b98523680b918997469914ca3992e4`. These instructions do NOT authorize execution before publication and independent network clone verification. No local patch/source copy may replace Git. All inference code comes from this commit.

## Environment and P0

Use the exact existing A3 runtime/native environment validated by Repair3 (CANN9.1.0, torch_npu2.10.0.post4). Install the new Git Python source normally or reconstruct the audited native-donor overlay with the NEW identity. Never execute the old hard-coded Repair3 overlay script unchanged. P0 compares imported Python bytes against Git even when an overlay is used. Keep old native provenance and new source provenance separate. MRV2 V2 runner/process settings are set by the frozen driver.

Set these task-specific absolute paths from the verified checkout/unpacked input package; do not copy example placeholders as real paths:
`REPAIR4_REPO`, `REPAIR4_VLLM`, `REPAIR4_INPUTS`, `REPAIR4_RESULTS`, `REPAIR4_RUN_ID`.
Choose the same already-verified A3 device after checking contention/memory. Do not guess a new model or capture size.

```bash
cd "$REPAIR4_REPO"
python tools/p7x_graph_repair4_campaign.py preflight \
 --handoff "$REPAIR4_INPUTS/P7X_Graph_Base_A3_Repair4_Server_Handoff.json" \
 --vllm-repo "$REPAIR4_VLLM" --require-npu --output "$REPAIR4_RESULTS/P0.json"
python tools/p7x_graph_repair4_campaign.py plan \
 --handoff "$REPAIR4_INPUTS/P7X_Graph_Base_A3_Repair4_Server_Handoff.json" --inputs "$REPAIR4_INPUTS" \
 --output-dir "$REPAIR4_RESULTS/cases" --vllm-repo "$REPAIR4_VLLM" \
 --run-id "$REPAIR4_RUN_ID" --output "$REPAIR4_RESULTS/plan.json"
```

The planner retains PRE_PUBLICATION, execution_authorized=false: a new external publication proof must be attached; never edit source/handoff to fake that proof. Validate fixture weights via the driver before model loading. Keep all expanded argv arrays.

## Execute one reviewed plan case

After publication proof and case dependencies have been checked, execute each existing `launcher_argv` exactly. This example executes A0, not all cases:

```bash
python -c 'import json,subprocess,sys; p=json.load(open(sys.argv[1])); raise SystemExit(subprocess.run(p["cases"][sys.argv[2]]["launcher_argv"]).returncode)' "$REPAIR4_RESULTS/plan.json" A0
```

Then A1(expected GRAPH_FROZEN), B0, B1, B2. Never reduce [7,14,28]. Original request files are exact copies. Actual replay buckets, not number of submitted requests, determine coverage. A3 device/native failure stops dependent runs; independent private fixture only with healthy device.

```bash
python tools/p7x_graph_repair4_acceptance.py check "$REPAIR4_RESULTS/cases/B0/campaign.json" \
 --run-id "$REPAIR4_RUN_ID" --case-id B0 --attempt-id 1 --output "$REPAIR4_RESULTS/B0-check.json"
python tools/p7x_graph_repair2.py analyze "$REPAIR4_RESULTS/cases/B1/campaign.json" --output "$REPAIR4_RESULTS/B1-analysis.json"
```

`check` is deliberately B0-specific. Its exit0 proves only the stated B0 functional requirements; numeric/physical/completion can still be OPEN. `analyze` is data discovery, not final Gate closure. B1 must show canonical S>0 and independent values; B2 real padding/length variation. Missing evidence stays OPEN.

## C2 / G5 / ABORT

```bash
python tools/p7x_graph_repair4_fixture.py run --dry-run
python tools/p7x_graph_repair4_fixture.py run --run-id "$REPAIR4_RUN_ID" --attempt C2 --output "$REPAIR4_RESULTS/C2" --timeout 180
python tools/p7x_graph_repair4_fixture.py check "$REPAIR4_RESULTS/C2/result.json" --manifest "$REPAIR4_RESULTS/C2/manifest.json"
```

Fresh disposable child and fixture-owned canonical/KV buffers; actual P3/P6/FIA/update path but not full model capture/allocator/write. Q7/W1024/B128/cap1151. FP16 numerical atol0.008/rtol0 fixed before run; zero query/key yields independently enumerable uniform attention. A/B/Aprime differ then restore logical contents at new generation. Short/nonaligned controls included. Ordinary events after last consumer/update explicitly diagnostic. No ExternalEvent.query.

Run the same command into NEW directories with `--abort-at before_replay`, `after_replay`, `after_update`, `after_completion`. Abort commands intentionally return non-PASS; assess recorded lifecycle/unsafe reuse, not exit0. Never treat child process death as completion. No sleep oracle. Keep partial/result/manifest/stdout/stderr/API hashes/launcher exit.

## G4 / G4F

Plan has G4-OFF/ON-short,long1,long2,mixed and G4F-OFF/ON variants. G4 is HEAD_ONLY plus write/metadata; G4F uses actual target manager forward and full mapped read/write KV blocks. Both arms use THIS SHA.
G4F is **PARTIAL**: bounded observations, not a deterministic OFF/ON state-construction fixture. It must reject unaligned inputs/pre-KV, omitted samples, changed selected read/write sets, and mismatched physical block mappings. No logical remap implemented. Cannot claim FULL_TARGET_READY solely from entry existence.

```bash
python tools/p7x_graph_repair4_target.py \
 "$REPAIR4_RESULTS/cases/G4F-OFF-short/target-full-forward.pt" \
 "$REPAIR4_RESULTS/cases/G4F-ON-short/target-full-forward.pt" \
 --atol 0 --rtol 0 --tolerance-reason 'initial exact deterministic diagnostic; relax only by predeclared dtype study' \
 --output "$REPAIR4_RESULTS/G4F-short-comparison.json"
```

Full forward is genuinely invoked; Graph replay may not execute Python model.forward. The probe wraps target run_fullgraph AFTER capture, waits its returned UPDATE submission, and snapshots complete selected KV. Its extra synchronization makes it NOT PERFORMANCE REPRESENTATIVE and cannot prove unsynchronized safety. Selected-block read coverage is computed from full Target lengths/table + physical write slots, not a few sampled entries. Unselected allocations remain unobserved. No output equivalence claim for Draft OFF vs ON.

## Trace T0/T1

Use plan T0/T1 driver argv as the profiler application. First `python tools/p7x_graph_repair2.py trace-probe --output ...` records available tools/options. Confirm installed help/version; do not invent command options. Preserve Repair3 successful profiler command in historical ledger but do not assume repeating it reveals missing fields. Inspect each actual export separately:

```bash
python tools/p7x_graph_repair4_acceptance.py trace-fields "$REPAIR4_RESULTS/traces/T0" --run-id "$REPAIR4_RUN_ID" --case-id T0 --attempt-id 1 --output "$REPAIR4_RESULTS/T0-fields.json"
python tools/p7x_graph_repair4_acceptance.py trace-fields "$REPAIR4_RESULTS/traces/T1" --run-id "$REPAIR4_RUN_ID" --case-id T1 --attempt-id 1 --output "$REPAIR4_RESULTS/T1-fields.json"
```

New capability probe is version/API source/native hash/FIA schema in C2 plus actual header/row analysis. No confirmed new tool providing task operand/physical read has been found. If absent, submit ACCEPTANCE_DECISION_REQUIRED, not a fabricated trace. Clocks from different domains require explicit correlation; sorting timestamps is not happens-before.

## R0

```bash
python tools/p7x_graph_repair4_campaign.py pack --root "$REPAIR4_RESULTS" --output "$REPAIR4_RESULTS.zip"
python tools/p7x_graph_repair4_campaign.py verify "$REPAIR4_RESULTS.zip"
```

pack rejects symlinks, existing output, output inside input, empty input and >8GiB total. Keep raw stderr/partial/exit/signal/commands and every failed case. Receiver repeats verify. This is evidence integrity only, not device correctness. Device model files/secrets must not be placed in artifacts.
