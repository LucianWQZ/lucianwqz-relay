# Repair6 Review Package

- source: `fd0716c59562f64262672de12e4ae26259908d0b` / tree `125b29bcb8fe501d69b53e185f9ec89075528310`
- run: `20261021T071630Z_fd0716c5`
- segment: **old Phy-ID8** (not authorized host Phy-ID0-7)
- device correction: `reports/Device_Reassignment_Report.md`

Includes reports, 42-case status, frozen plan, request/config metadata, launchers, campaign/checker/joint metadata, Target manifest/index and NUMERIC failure. Tensor chunks, complete sample JSON, full stdout/stderr and raw source remain in raw.

TARGET4 12/12 paired PASS and G4F 10/10 paired PASS are old-device diagnostic results, not new authorized-device or complete campaign PASS. NUMERIC_TARGET4 failed before model load at VllmConfig; checker INVALID_EVIDENCE is downstream. Public Graph gate remains frozen.
