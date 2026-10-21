# P7-X MRV2 Runtime Identity Requirement

## Status

This requirement is frozen for every P7-X Node101 campaign. It is a deployment
and evidence-validity requirement, not a request to change the Ascend global
default and not a production-code modification.

## Source and Report1 fact

On the pinned stack, an unset `VLLM_USE_V2_MODEL_RUNNER` selects MRV1 on
Ascend. Report1 confirmed that the historical GLM TP16 launcher entered
`model_runner_v1.py`. Therefore a process that merely imports P7-X code, or a
launcher that only claims MRV2 in its filename, is not valid evidence.

Every P7-X MRV2 run must set before process creation:

```bash
export VLLM_USE_V2_MODEL_RUNNER=1
```

Changing the global platform default from MRV1 to MRV2 is explicitly outside
this feature and is forbidden as a Sliding Window fix.

## Required two-layer proof

Before a semantic or performance result is accepted, the artifact must contain:

1. import/runtime environment proof showing the exact vLLM and vllm-ascend
   commits and the effective `VLLM_USE_V2_MODEL_RUNNER=1` value;
2. an in-worker probe after initialization showing:
   - model runner fully-qualified class/module contains `worker.v2`;
   - speculator fully-qualified class/module contains
     `worker.v2.spec_decode`;
   - normalized speculative method and concrete speculator class;
   - P7-X final SHA/tree.

If either proof is missing or names an MRV1 class, classify the run as:

```text
INVALID_RUN_WRONG_MODEL_RUNNER
```

Do not interpret its Window Gate, output, trace, profiler, or failure as P7-X
evidence.

## Scope

The rule applies to every positive and negative P7-X case, including Window
OFF, forced-OFF, TP16, DSA-CP, async, prefix, chunked, mixed, multi-request,
and backend-gate cases. Report1 observations at P8 SHA `4753742...` remain
historical fixtures and do not validate P7-X final.

