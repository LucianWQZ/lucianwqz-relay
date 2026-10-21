# Repair7 GitHub Publication and Server Readiness

Generated: `2026-10-22T03:31:22.831134+08:00`

## Verdict

```text
FINAL_BRANCH=fix/p7x-graph-base-a3-repair7
FINAL_SHA=7a9f4aae1ebe5c5f3d4876ec9b49926949dfae14
FINAL_TREE=6dd40a67a500480556068be8b6ebcd977e3cc3e8
FINAL_PARENT=fd0716c59562f64262672de12e4ae26259908d0b
PUSH=PASS
REMOTE_IDENTITY=VERIFIED
CLEAN_ROOM=VERIFIED
PUBLICATION=VERIFIED
NEW_SHA_DEVICE_VERIFICATION=NOT_RUN
READY_FOR_A3_SCOPED=YES_AFTER_EXACT_PREFLIGHT_AND_DEVICE_ADMISSION
READY_FOR_ALL_G1_G5_CLOSURE=NO
PUBLIC_GRAPH_GATE=STILL_FROZEN
```

No PR, merge, tag, force push, server experiment, or public Graph enablement occurred.

## Candidate and package review

The local branch, HEAD, tree, and parent matched the frozen Repair7 identity and the worktree was clean. Pinned vLLM matched `84030bbe3d74d99bad477a3d2e37a973ccd8865c` / tree `f3e320f8ae2e9a30e57a3c8dccfac94fcae93bee` and was clean. The pre-publication handoff declared 27 tool hashes, 2 production hashes, and 14 changed-file hashes; all 43 file checks matched both the source checkout and the independent GitHub clone. Both original ZIPs passed CRC and unsafe-path checks.

Existing final-source test evidence was reused: 735 related Host tests and 51 optimized-mode checks passed; Ruff, format, targeted Mypy, compileall, diff-check, and locally executable hooks passed. The full manual pre-commit runner remains `ENVIRONMENT_BLOCKED` by npm `EALLOWGIT`; it is not reported as PASS. Repair7 remains Host-only and full EngineArgs/A3 execution is not locally claimed.

## Authentication and transport diagnosis

GitHub CLI reused the existing `LucianWQZ` keyring login; API permission for `LucianWQZ/vllm-ascend` was `push=true/admin=true`. No token value was requested, saved, or included in evidence.

The initial Git HTTPS failure was a transport issue, not authentication: macOS system proxy and proxy environment variables were empty while Veee listened on `127.0.0.1:15235` and `127.0.0.1:15236`. Bounded probes established `15235` as SOCKS5h and `15236` as HTTP CONNECT. Direct `github.com:443` timed out, while command-level `http.proxy=http://127.0.0.1:15236` succeeded. No global Git/system proxy, TLS verification, DNS, hosts file, or VPN setting was changed.

## Push and independent recovery

The remote branch did not exist. One ordinary non-force push created only `refs/heads/fix/p7x-graph-base-a3-repair7`. GitHub API then returned the exact SHA/tree/parent above. A fresh `gh repo clone` over the command-scoped Veee proxy recovered the branch into a new `/private/tmp` directory. The clone had no object alternates, was clean, and matched all 43 declared source hashes. The clone was not made with `--shared`, a local bundle, patch, or worktree.

## Server admission boundary

The POST_PUBLICATION pack may be used only after:

1. a fresh GitHub clone/fetch restores this exact clean SHA/tree;
2. pinned vLLM is restored exactly;
3. the original fixture manifest bytes/hash are verified;
4. the server owner proves the selected TP1 chip belongs to authorized host Phy-ID 0–7 and issues a fresh case receipt;
5. `CONFIG` validates the real EngineArgs/platform factory before model load;
6. A0/A1/B0 anchors run on the authorized device;
7. the three-sample continuous-numeric sentinel passes before the 12-sample matrix.

Forty-four planned cases and 140 parsed CLI invocations are local contract evidence, not device completion. Base missing Target `(4,32)` must not block independent Target4. Full Target resource shortage must not block unrelated light/profiling branches. Repair6 old Phy-ID8 results stay historical. Normal UPDATE generation, last-consumer completion/reuse, task-internal operand, and physical read remain OPEN.
