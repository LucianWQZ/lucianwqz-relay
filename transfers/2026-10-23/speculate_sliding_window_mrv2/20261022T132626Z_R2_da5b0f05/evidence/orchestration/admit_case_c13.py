#!/usr/bin/env python3
"""Run one fixed round2 C12 case with separate authorization and machine evidence."""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path("/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt")
RUN = Path("/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt/runs/20261022T132626Z_R2/raw")
SOURCE = ROOT / "candidates/C13_unwind/vllm-ascend"
VLLM = ROOT / "candidates/C2_303ef7fe/vllm"
PLAN = RUN / "C13_prepare_01/case-plan.json"
PYTHON = "/usr/local/python3.11.10/bin/python"
DEVICE = SOURCE / "tools/p7x_graph_repair7_device.py"
BIND = SOURCE / "tools/p7x_graph_local_candidate.py"
RUNNER = SOURCE / "tools/p7x_graph_repair6_runner.py"
AUTH = ROOT / "state/ROUND2_USER_AUTHORIZATION_RECORD.json"
PROBE = RUN / "probe_phy0_01/probe_result.json"
PROBE_SMI = RUN / "probe_phy0_01/probe_observed_npu_smi.txt"
STATUS = ROOT / "journal/current_status.json"
PROGRESS = ROOT / "journal/progress.log"


def timestamp():
    utc = datetime.now(timezone.utc)
    return utc.isoformat(), utc.astimezone(timezone(timedelta(hours=8))).isoformat()


def status_event(event, case, **fields):
    utc, local = timestamp()
    old = json.loads(STATUS.read_text())
    candidate_sha = fields.pop("candidate_sha", None)
    candidate_tree = fields.pop("candidate_tree", None)
    fields.pop("development_uncommitted_changes", None)
    if event == "CASE_PLANNED":
        old["running_candidate"] = dict(sha=candidate_sha, tree=candidate_tree, case=case)
        old["current_action"] = "固定C13独立case " + case
        old["current_case"] = case
        old["worker_pids"] = []
        old.update(model_worker_pids=[], model_worker_profiler_active=False, npu_observed_at=None, actual_host_phy_id=None, last_model_progress=None, runner_status=None, primary_failure=None, npu_after_exit=None, producer_status=None, checker_status=None)
    old.update(fields)
    old.update(event=event, last_monitor_check=utc, monitor_pid=os.getpid(), run_root=str(RUN))
    if event in ("CASE_PLANNED", "CASE_END"):
        old["last_agent_update"] = utc
    if event == "MODEL_PROCESS_CREATED":
        old["round_counts"]["formal_model_starts"] = fields["formal_model_experiments_started"]
    if event == "CASE_END":
        old.update(current_case=None, last_completed_case="C13/" + case, running_candidate=None, monitor_pid=None, model_worker_pids=[], model_worker_profiler_active=False)
        old["last_device_candidate"] = dict(sha=json.loads(PLAN.read_text())["commit"], case=case, runner_status=fields.get("runner_status"))
        result_path = RUN / "C13_prepare_01" / case / "result.json"
        if case == "C2" and result_path.exists():
            result = json.loads(result_path.read_text())
            if result.get("process_id"):
                old["round_counts"]["private_fixture_attempts"] += 1
                old["last_device_candidate"] = dict(sha=json.loads(PLAN.read_text())["commit"], case=case, result=result.get("status"))
    temporary = STATUS.with_suffix(".json.partial")
    temporary.write_text(json.dumps(old, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(STATUS)
    with PROGRESS.open("a") as stream:
        stream.write(f"{utc}（北京 {local}）：{event} {case}；" + "; ".join(f"{key}={value}" for key,value in fields.items() if key in ("status","runner_pid","model_worker_pids","npu_observation","runner_status","primary_failure","elapsed_seconds","durable_samples")) + "\n")


def monitored_runner(argv, env, out, timeout, case, plan, campaign):
    stdout = out.with_suffix(".stdout.log")
    stderr = out.with_suffix(".stderr.log")
    start = time.time_ns()
    deadline_epoch = json.loads(AUTH.read_text())["deadline_epoch_seconds"]
    progress_path = Path(plan["cases"][case].get("outputs", "")) / "progress.json"
    last_progress_mtime = None
    last_durable_samples = None
    npu_seen = False
    last_phase = "MODEL_STARTING" if case not in ("P0", "CONFIG") else "CHECKING"
    last_phase_source = "worker/process observation only"
    with stdout.open("wb") as output, stderr.open("wb") as errors:
        process = subprocess.Popen(argv, env=env, stdout=output, stderr=errors, start_new_session=True)
        status_event("PROCESS_STARTED", case, status="MODEL_STARTING" if case not in ("P0", "CONFIG") else "CHECKING",
                     runner_pid=process.pid, model_worker_pids=[], npu_observation="NOT_OBSERVED_YET")
        while process.poll() is None:
            try:
                process.wait(timeout=min(10 if case == "C2" else 30, max(0.1, deadline_epoch - time.time())))
                break
            except subprocess.TimeoutExpired:
                pass
            elapsed = (time.time_ns() - start) / 1e9
            if time.time() >= deadline_epoch:
                # Only this supervisor's runner and verified descendant tree.
                snapshot = subprocess.run(["ps", "-eo", "pid,ppid,args"], capture_output=True, text=True, timeout=10).stdout
                descendants = {process.pid}
                entries = [line.split(None, 2) for line in snapshot.splitlines()[1:]]
                changed = True
                while changed:
                    changed = False
                    for item in entries:
                        if len(item) == 3 and int(item[1]) in descendants and int(item[0]) not in descendants:
                            descendants.add(int(item[0])); changed = True
                identities = {}
                for pid in descendants:
                    try:
                        identities[pid] = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
                    except OSError:
                        pass
                out.with_name("deadline-process-evidence.json").write_text(json.dumps(dict(deadline_epoch=deadline_epoch, observed_at=timestamp()[0], runner_pid=process.pid, owned_pid_start_ticks=identities, process_snapshot=snapshot), indent=2) + "\n")
                status_event("DEADLINE_REACHED", case, status="BLOCKED", primary_failure="Original device authorization expired; terminate only verified owned process tree")
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    for pid, ticks in identities.items():
                        try:
                            if Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19] == ticks:
                                os.kill(pid, sig)
                        except (OSError, ProcessLookupError):
                            pass
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        pass
                process.wait(timeout=10)
                break
            try:
                smi = subprocess.run(["npu-smi", "info"], capture_output=True, text=True, timeout=10)
                smi_path = out.with_name(f"npu-smi-heartbeat-{int(elapsed):05}.txt")
                smi_path.write_text(smi.stdout + "\nSTDERR\n" + smi.stderr)
                npu_observation = str(smi_path) if smi.returncode == 0 else f"QUERY_RC_{smi.returncode}"
            except Exception as error:
                npu_observation = f"QUERY_FAILED_{type(error).__name__}"
            ps = subprocess.run(["ps", "-eo", "pid,ppid,lstart,stat,args"], capture_output=True, text=True, timeout=10)
            workers = [line for line in ps.stdout.splitlines()
                       if "p7x_graph_repair2.py" in line and plan["run_id"] in line and case in line
                       and "ps -eo" not in line]
            model_workers = [line for line in workers if "p7x_graph_repair2.py run" in line and "p7x_graph_repair2.py launch" not in line]
            model_pids = [int(line.split()[0]) for line in model_workers]
            experiment_key = f"{plan['run_id']}:{case}"
            current = json.loads(STATUS.read_text())
            if model_pids and experiment_key not in current.get("model_experiment_keys", []):
                keys = current.get("model_experiment_keys", []) + [experiment_key]
                status_event("MODEL_PROCESS_CREATED", case, model_worker_pids=model_pids, model_worker_profiler_active=True,
                             model_experiment_keys=keys,
                             formal_model_experiments_started=current.get("formal_model_experiments_started", 0) + 1)
            fixture_workers = [line for line in ps.stdout.splitlines() if "p7x_graph_repair4_fixture.py device-worker" in line and str(progress_path.parent) in line and "/bin/bash -c" not in line]
            device_pids = model_pids + [int(line.split()[0]) for line in fixture_workers]
            observed_rows = []
            if "smi" in locals() and smi.returncode == 0:
                for line in smi.stdout.splitlines():
                    fields = [field.strip() for field in line.strip().strip("|").split("|")]
                    if len(fields) >= 5 and fields[0].split() == ["0", "0"] and fields[4].isdigit() and int(fields[4]) in device_pids:
                        observed_rows.append(line)
            if observed_rows:
                npu_observation = f"OBSERVED_PHY0; evidence={smi_path}; rows={observed_rows}"
                if not npu_seen:
                    status_event("NPU_OBSERVED", case, actual_host_phy_id=0,
                                 npu_observed_at=timestamp()[0], npu_observation=npu_observation)
                    npu_seen = True
            elif "smi_path" in locals():
                npu_observation = f"NO_OWN_PROCESS_OBSERVED; evidence={smi_path}"
            phase = last_phase
            phase_source = last_phase_source
            if progress_path.is_file():
                mtime = progress_path.stat().st_mtime_ns
                if mtime != last_progress_mtime:
                    last_progress_mtime = mtime
                    data = json.loads(progress_path.read_text())
                    raw_phase = str(data.get("phase", ""))
                    phase_source = f"{progress_path}:phase={raw_phase}"
                    if "CAPTURE" in raw_phase:
                        phase = "GRAPH_CAPTURE"
                    elif "REQUEST" in raw_phase or "GENERAT" in raw_phase:
                        phase = "REQUEST_RUNNING"
                    elif "LOAD" in raw_phase:
                        phase = "MODEL_LOADING"
                    if raw_phase not in ("", "BEFORE_STARTUP"):
                        status_event("MODEL_PROGRESS", case, last_model_progress=timestamp()[0],
                                     model_phase_source=phase_source)
            durable = {}
            for manifest_name in ("numeric-reference.json", "controlled-target.json"):
                manifest_path = progress_path.parent / manifest_name
                if manifest_path.is_file():
                    try:
                        manifest = json.loads(manifest_path.read_text())
                        samples = manifest.get("samples", [])
                        durable[manifest_name] = dict(registered_samples=len(samples), finished_samples=sum(x.get("path") is not None and x.get("status") != "PREPARING" for x in samples), status_counts={state:sum(x.get("status") == state for x in samples) for state in {x.get("status") for x in samples}}, execution=manifest.get("execution"))
                    except (OSError, ValueError):
                        pass
            if durable and durable != last_durable_samples:
                last_durable_samples = durable
                phase = "REQUEST_RUNNING"
                phase_source = "durable producer manifests: " + json.dumps(durable)
                status_event("MODEL_PROGRESS", case, last_model_progress=timestamp()[0], durable_samples=durable, model_phase_source=phase_source)
            last_phase, last_phase_source = phase, phase_source
            status_event("HEARTBEAT", case, status=phase, runner_pid=process.pid,
                         model_worker_pids=model_pids, worker_process_details=workers,
                         npu_observation=npu_observation,
                         elapsed_seconds=round(elapsed, 1), model_phase_source=phase_source,
                         latest_runner_stdout_size=stdout.stat().st_size,
                         latest_runner_stderr_size=stderr.stat().st_size,
                         eta_remaining="UNKNOWN")
            if elapsed > timeout:
                status_event("STATUS_STALE", case, status="MODEL_STARTING",
                             primary_failure="outer supervision time exceeded; inspect owned runner tree")
        rc = process.returncode
    result_path = campaign / case / "runner-result.json"
    result = json.loads(result_path.read_text()) if result_path.is_file() else {}
    elapsed = (time.time_ns() - start) / 1e9
    try:
        final_smi = subprocess.run(["npu-smi", "info"], capture_output=True, text=True, timeout=10)
        final_path = out.with_name("npu-smi-after-exit.txt")
        final_path.write_text(final_smi.stdout + "\nSTDERR\n" + final_smi.stderr)
        final_occupancy = "NO_RUNNING_PROCESS_NPU0" if "No running processes found in NPU 0" in final_smi.stdout else "REVIEW_NPU0_PROCESS_TABLE"
    except Exception as error:
        final_occupancy = f"QUERY_FAILED_{type(error).__name__}"
        final_path = None
    status_event("CASE_END", case, status="FINISHED" if rc == 0 and result.get("dependency_satisfied") else "FAILED",
                 runner_pid=process.pid, runner_status=result.get("status", "MISSING_RESULT"),
                 primary_failure=result.get("primary_failure"), elapsed_seconds=round(elapsed, 1),
                 producer_status=result.get("producer_status"), artifact_status=result.get("artifact_status"),
                 checker_status=result.get("acceptance_status"), runner_returncode=rc,
                 npu_after_exit=final_occupancy, npu_after_exit_evidence=str(final_path),
                 model_worker_profiler_active=False if final_occupancy == "NO_RUNNING_PROCESS_NPU0" else "UNKNOWN")
    return {"argv": argv, "pid": process.pid, "start_ns": start, "end_ns": time.time_ns(),
            "returncode": rc, "stdout": str(stdout), "stderr": str(stderr),
            "timeout_seconds": timeout, "elapsed_seconds": elapsed,
            "runner_result": str(result_path)}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def evidence(path):
    return {"path": str(path), "sha256": digest(path)}


def environment():
    from common_c13 import environment as build_environment
    return build_environment()


def command(argv, env, out, timeout):
    start = time.time_ns()
    result = subprocess.run(argv, env=env, text=True, capture_output=True, timeout=timeout)
    out.with_suffix(".stdout.log").write_text(result.stdout)
    out.with_suffix(".stderr.log").write_text(result.stderr)
    return {"argv": argv, "pid_parent": os.getpid(), "start_ns": start,
            "end_ns": time.time_ns(), "returncode": result.returncode,
            "stdout": str(out.with_suffix(".stdout.log")), "stderr": str(out.with_suffix(".stderr.log"))}


def host_pid_from_probe():
    probe = json.loads(PROBE.read_text())
    for line in PROBE_SMI.read_text().splitlines():
        fields = [field.strip() for field in line.strip().strip("|").split("|")]
        if len(fields) >= 5 and fields[0].split() == ["0", "0"] and fields[4] == str(probe["pid"]):
            return int(fields[1]), probe
    raise ValueError("probe PID was not observed on Phy-ID0")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case")
    p.add_argument("--preprobe", action="store_true")
    args = p.parse_args()
    if args.preprobe == bool(args.case):
        p.error("select exactly one case or --preprobe")
    plan = json.loads(PLAN.read_text())
    case = args.case or "PREPROBE"
    if args.case and args.case not in plan["cases"]:
        p.error("unknown case")
    admission = RUN / "admission_C13_attempt01" / case / "attempt01"
    admission.mkdir(parents=True, exist_ok=False)
    env = environment()
    inventory_path = admission / "inspect.json"
    inspect_record = command([PYTHON, str(DEVICE), "inspect", "--output", str(inventory_path)], env,
                             admission / "inspect", 45)
    if inspect_record["returncode"]:
        raise RuntimeError(f"inspect failed: {inspect_record}")
    inventory = json.loads(inventory_path.read_text())
    resources = subprocess.run(["npu-smi", "info"], capture_output=True, text=True, timeout=20)
    resource_path = admission / "npu-smi-info.txt"
    resource_path.write_text(resources.stdout + "\nSTDERR\n" + resources.stderr)
    observed = time.time()
    if resources.returncode or "No running processes found in NPU 0" not in resources.stdout:
        raise RuntimeError("Phy-ID0 is occupied or npu-smi failed")
    host_pid, probe = host_pid_from_probe()
    now = time.time()
    deadline = json.loads(AUTH.read_text())["deadline_epoch_seconds"]
    receipt = dict(
        schema="repair7-user-authorized-device-v1",
        run_id=plan["run_id"], source_sha=plan["commit"], source_tree=plan["tree"],
        case_id=case, user_authorization=evidence(AUTH), issued_at=now,
        expires_at=min(now + 1800, deadline), host_phy_id=0, tp=1,
        allocated_nodes={"/dev/davinci0": inventory["nodes"]["/dev/davinci0"]},
        namespace=inventory["namespace"], boot_id=inventory["boot_id"],
        visibility=inventory["visibility"], mapping_evidence=[evidence(inventory_path)],
        resource_evidence=[evidence(resource_path)], resource_observed_at=observed,
        probe=dict(host_pid=host_pid, container_pid=probe["pid"], command=probe["argv"],
                   start_ns=probe["start_ns"], end_ns=probe["end_ns"], host_phy_id=0,
                   status="EXITED", returncode=probe["rc"],
                   host_process_evidence=evidence(PROBE_SMI), pid_namespace_evidence=evidence(PROBE)),
    )
    receipt_path = admission / "user-machine-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    records = {"case": case, "source_sha": plan["commit"], "source_tree": plan["tree"],
               "receipt": evidence(receipt_path), "environment": {key: env.get(key) for key in
               ("ASCEND_RT_VISIBLE_DEVICES", "PYTHONPATH", "VLLM_USE_V2_MODEL_RUNNER",
                "VLLM_VERSION", "VLLM_ENABLE_V1_MULTIPROCESSING", "VLLM_CACHE_ROOT", "TORCH_NPU_CACHE_DIR",
                "ASCEND_CACHE_PATH", "HF_HOME", "TMPDIR")}, "inspect": inspect_record}
    if args.preprobe:
        probe_output = admission / "committed-probe.json"
        records["committed_probe"] = command(
            [PYTHON, str(DEVICE), "probe", "--run-id", plan["run_id"], "--receipt",
             str(receipt_path), "--output", str(probe_output)], env, admission / "committed-probe", 90)
        if records["committed_probe"]["returncode"]:
            raise RuntimeError("committed probe failed")
        records["probe_value"] = json.loads(probe_output.read_text())["value"]
    else:
        records["check"] = command(
            [PYTHON, str(DEVICE), "check", "--run-id", plan["run_id"], "--receipt",
             str(receipt_path), "--output", str(admission / "check.json")], env,
            admission / "check", 60)
        if records["check"]["returncode"]:
            raise RuntimeError("device check failed")
        bound = admission / "admitted-plan.json"
        records["bind"] = command(
            [PYTHON, str(BIND), "bind", "--plan", str(PLAN), "--receipt", str(receipt_path),
             "--output", str(bound), "--case-id", case], env, admission / "bind", 180)
        if records["bind"]["returncode"]:
            raise RuntimeError("local candidate bind failed")
        campaign = RUN / "C13_campaign_01"
        timeout = plan["cases"][case]["timeout_seconds"] + 300
        argv = [PYTHON, str(RUNNER), "--plan", str(bound), "--case-id", case,
                "--output", str(campaign)]
        case_plan = plan["cases"][case]
        status_event("CASE_PLANNED", case, status="MODEL_STARTING" if case not in ("P0", "CONFIG") else "CHECKING",
                     run_id=plan["run_id"], attempt="01", candidate_sha=plan["commit"],
                     task=f"执行固定 C13 case {case}；以实际日志/进程/设备证据判定", current_blocker=None,
                     development_uncommitted_changes=False,
                     candidate_tree=plan["tree"], fixture_sha256=case_plan.get("fixture_sha256"),
                     request_sha256=case_plan.get("requests_sha256"),
                     config_identity=plan.get("local_candidate_manifest_sha256"),
                     profile_identity=case_plan.get("capture_profile", "BASE_OR_CASE_ARGV"),
                     hostname=Path("/etc/hostname").read_text().strip(),
                     host_phy_id_planned=0, logical_device_planned=0,
                     mapping_evidence=str(inventory_path), tp=1, argv=argv,
                     stdout=str(admission / "runner.stdout.log"),
                     stderr=str(admission / "runner.stderr.log"),
                     output=str(campaign / case),
                     estimated_duration="10–40s from C6 P0" if case == "P0" else
                     "25–80s based on completed C6 CONFIG attempts" if case == "CONFIG" else "ETA_UNKNOWN: candidate-specific run; C6 anchors 85–232s, numeric sentinel 350s for reference",
                     runner_child_hard_timeout_seconds=case_plan["timeout_seconds"] + 120,
                     outer_supervision_timeout_seconds=timeout)
        records["runner"] = monitored_runner(argv, env, admission / "runner", timeout,
                                              case, plan, campaign)
        records["runner_result"] = str(campaign / case / "runner-result.json")
    underlying = records.get("runner", records.get("committed_probe"))
    records["recording_rc"] = 0
    records["runner_process_rc"] = underlying["returncode"]
    result = json.loads(Path(records["runner_result"]).read_text()) if "runner_result" in records and Path(records["runner_result"]).exists() else {}
    records["runner_status"] = result.get("status")
    records["dependency_satisfied"] = result.get("dependency_satisfied", False)
    records["orchestrator_rc"] = underlying["returncode"] if underlying["returncode"] else 0 if args.preprobe or result.get("dependency_satisfied") else 2
    records["supervisor_sha256"] = digest(Path(__file__))
    (admission / "execution.json").write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps({"case": case, "record": str(admission / "execution.json"),
                      "runner_rc": records["runner_process_rc"], "orchestrator_rc": records["orchestrator_rc"], "dependency_satisfied": records["dependency_satisfied"]}))
    return records["orchestrator_rc"]


if __name__ == "__main__":
    raise SystemExit(main())
