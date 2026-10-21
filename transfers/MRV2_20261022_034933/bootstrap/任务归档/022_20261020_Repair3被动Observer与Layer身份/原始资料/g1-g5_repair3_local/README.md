# Repair3 local review package

Main report and handoff are included. No new server run; publication NOT_PUBLISHED.
Original verified server ZIPs are not duplicated. Historical small inputs are byte-for-byte copies under historical_inputs/.
Immutable input package hashes and extraction paths: evidence_verification.json/main report.
Final source diff: diff/repair3-full.patch; apply only to exact base 8198ab7a clean checkout.
All logs are original runs; green/targeted.log + check_results.json is final postcommit run.
run_checks.py uses exact base..HEAD (not empty worktree diff). Analysis scripts may reference original Mac input locations.
Server commands are a plan; no authority to auto-publish/server-run. Configure actual approved runtime recipe first.
sha256sum -c SHA256SUMS validates payload including ARTIFACT_INDEX; SHA256SUMS excludes itself.
ZIP final checksum and verification reside outside the ZIP to avoid cycles.
