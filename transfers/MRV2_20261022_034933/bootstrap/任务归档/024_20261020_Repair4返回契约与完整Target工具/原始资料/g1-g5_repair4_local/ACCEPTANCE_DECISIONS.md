# Outstanding decisions — no standard lowered
1. Physical-read/task-internal operands remain OPEN. Existing ordinary msprof exports cannot establish them. Need version-supported capability or explicit owner acceptance decision.
2. FULL_TARGET deterministic two-arm generation is not implemented. Actual forward/checkpoint/strict pair comparison are implemented, but natural traffic need not align. Safely checkpointing/restoring all engine/model/scheduler/sampler state is not a proven API; no speculative mutation of active allocator is introduced.
3. Private synchronized FIA fixture G5 cannot close unsynchronized full MRV2 lifecycle, abort/reuse or stream race claims. Actual serving task-generation/completion trace remains required.
4. No batch A/public enablement until required Base gates are independently adjudicated; no local PASS propagation to device.
