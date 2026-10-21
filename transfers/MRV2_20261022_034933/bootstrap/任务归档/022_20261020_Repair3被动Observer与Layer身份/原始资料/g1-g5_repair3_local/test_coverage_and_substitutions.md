# Host coverage and substitutions

Final command/exit/log: check_results.json (targeted.log copied under green/).
270 unique tests, 2 extra subtests; do not add repeated runs. 1 vLLM._version warning. No NPU.

- Real builder sharing multiple layer keys -> actual forward -> FIA function -> capture observer -> snapshot/checker runs in CPU harness.
- Hardware graph/task/event/FIA kernel/timer is stubbed; no device stream completion or task binding proof.
- _use_layer_aware_fia_graph_replay=False and _layer_name=None initially. KV metadata owner can differ from execution layer; no prefilled answer.
- Three descriptors [7,14,28], warmup/capture and old closure, five actual layer instances; all names originate actual forward layer argument.
- Forbidden event query/sync/wait count zero; pure repeated export, no timestamp refresh, weakref event freed.
- F1-F4/wrong source/owner/generation/backing, alias/isolation and public Gate remain strict.
- Actual recorder-to-checker fixture's single Host bucket stays OPEN for full three-bucket smoke.
- Raw head 21 pairs recomputed separately: not counted as NPU or production tests; all hashes unique and numeric exact, FULL_TARGET OPEN.
- Driver launch tested real child exit3 and mocked child -11 (no native crash induced).
- Packager synthetic smoke is separately logged, not added to production test count.
- Full precommit environment blocked by actionlint downloads; individual installed hooks pass, no false full PASS.
