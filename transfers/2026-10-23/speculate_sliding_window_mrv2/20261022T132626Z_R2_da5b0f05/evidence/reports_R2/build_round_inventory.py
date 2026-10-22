"""Index this round's immutable admissions; retain producer/checker scope."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt')
SID = '20261022T132626Z_R2'
RAW = ROOT / 'runs' / SID / 'raw'
OUT = ROOT / 'reports' / SID


def load(path):
    return json.loads(path.read_text())


def main():
    rows = []
    counts = dict(model_starts=0, expected_graph_frozen=0, model_producer_exit0=0,
                  expected_abort_exits=0, python_unwind_exits=0, other_model_failures=0,
                  private_fixtures=0, probes=0, profiler_collections=0, offline_reanalyses=0,
                  model_runner_accepted=0, model_acceptance_failed=0)
    for path in sorted(RAW.glob('admission*/*/attempt*/execution.json')):
        document = load(path)
        if 'runner' not in document:
            continue
        runner = document['runner']
        plan = load(path.with_name('admitted-plan.json'))
        case = document['case']
        expected = plan['cases'][case]
        result_path = Path(document['runner_result'])
        result = load(result_path)
        assert result['source_identity'] == [plan['run_id'], plan['commit'], plan['tree']]
        assert result['case_id'] == case
        artifact_root = Path(expected.get('outputs', path.parent))
        if case == 'C2':
            artifact_root = Path(expected['argv'][expected['argv'].index('--output') + 1])
        campaign_path = artifact_root / 'campaign.json'
        campaign = load(campaign_path) if campaign_path.exists() else {}
        fixture_path = artifact_root / 'result.json'
        launcher_path = Path(plan['output']) / 'launchers' / case / 'launcher.json' if 'output' in plan else artifact_root.parent / 'launchers' / case / 'launcher.json'
        launcher = load(launcher_path) if launcher_path.exists() else {}
        model = bool(launcher and any(Path(a).name == 'p7x_graph_repair2.py' for a in expected['argv']) and 'run' in expected['argv'])
        kind = 'MODEL' if model else 'PRIVATE_FIXTURE' if case == 'C2' else 'FRAMEWORK_CONFIG_NO_MODEL' if case == 'CONFIG' else 'CAPABILITY_NO_MODEL'
        if model:
            counts['model_starts'] += 1
            counts['model_runner_accepted' if result.get('dependency_satisfied') else 'model_acceptance_failed'] += 1
            rc = launcher['returncode']
            if case == 'A1' and campaign.get('exception_type') == 'NotImplementedError' and 'GRAPH_FROZEN' in campaign.get('exception_message', ''):
                counts['expected_graph_frozen'] += 1
            elif case.startswith('ABORT_') and rc == 73:
                counts['expected_abort_exits'] += 1
            elif case.startswith('UNWIND_') and rc == 74:
                counts['python_unwind_exits'] += 1
            elif rc == 0 and campaign.get('status') == 'OK':
                counts['model_producer_exit0'] += 1
            else:
                counts['other_model_failures'] += 1
            profile = artifact_root / 'profile.json'
            if profile.exists() and load(profile).get('profiler_enabled'):
                counts['profiler_collections'] += 1
        elif case == 'C2' and fixture_path.exists() and load(fixture_path).get('process_id'):
            counts['private_fixtures'] += 1
        commands = result.get('records', [])
        artifact_detail = {}
        diagnostic_first_failure = None
        for filename in ('numeric-reference.json', 'controlled-target.json', 'mrv2-lifecycle.json', 'task-dump-index.json', 'profile.json'):
            artifact_path = artifact_root / filename
            if not artifact_path.exists():
                continue
            doc = load(artifact_path)
            item = dict(path=str(artifact_path), status=doc.get('status', doc.get('execution', 'NOT_SPECIFIED')),
                        schema=doc.get('schema', 'NOT_SPECIFIED'), bytes=artifact_path.stat().st_size)
            if isinstance(doc.get('samples'), list):
                item['registered_samples'] = len(doc['samples'])
            if isinstance(doc.get('records'), list):
                item['records'] = len(doc['records'])
            if filename == 'task-dump-index.json' and doc.get('status') == 'EXPORT_FAILED':
                errors = [row['error'] for row in doc['records'] if row.get('error')]
                diagnostic_first_failure = dict(category='TOOL_DIAGNOSTIC_EXPORT', evidence=str(artifact_path), errors=errors,
                                                downstream_runner_failure=result.get('primary_failure'))
            artifact_detail[filename] = item
        rows.append(dict(
            record_kind=kind, case_id=case, source_sha=plan['commit'], source_tree=plan['tree'],
            checker_sha=plan['commit'], profile=expected.get('capture_profile', 'BASE_OR_CASE_ARGV'),
            config_hash=campaign.get('config_sha256', 'NOT_AVAILABLE'),
            request_hash=expected.get('requests_sha256', 'NOT_APPLICABLE'),
            device_segment='node-39-101 / Phy0 / visible0 / logical npu:0 / TP1; actual observations in admission',
            run_id=plan['run_id'], evidence=str(path), runner_result=str(result_path),
            admission_attempt=str(path.parent), producer_attempt=expected.get('attempt_id', 'NOT_APPLICABLE'),
            runner_pid=runner['pid'], model_pid=launcher.get('pid', 'NOT_CREATED'),
            start_utc=datetime.fromtimestamp(runner['start_ns'] / 1e9, timezone.utc).isoformat(),
            elapsed_seconds=runner['elapsed_seconds'],
            orchestrator_rc=document.get('orchestrator_rc', 'NOT_RECORDED'), runner_rc=runner['returncode'],
            producer_rc=commands[0]['returncode'] if commands else 'NOT_STARTED',
            checker_rc=json.dumps([x['returncode'] for x in commands[1:]]),
            producer_status=result.get('producer_status'),
            artifact_status='EXPORT_FAILED' if diagnostic_first_failure else 'AVAILABLE_SCOPED_ARTIFACTS' if artifact_detail else 'SEE_RUNNER_FILES',
            artifact_detail=json.dumps(artifact_detail, ensure_ascii=False),
            runner_artifact_status=result.get('artifact_status'),
            checker_status=result.get('acceptance_status'), runner_status=result['status'],
            dependency_satisfied=result['dependency_satisfied'],
            earliest_exception_or_failure=campaign.get('exception_message') if campaign.get('status') == 'EXCEPTION' else json.dumps(diagnostic_first_failure or result.get('primary_failure')),
            result_scope='ACTUAL_SOURCE_DEVICE_OR_CONFIG_EXECUTION; NOT_PUBLIC_GATE',
        ))
    for path in RAW.glob('probe_phy*/probe_result.json'):
        if load(path).get('rc') == 0:
            counts['probes'] += 1
    for path in RAW.glob('reanalysis_C12_ABORT_by_C13_01/*-reanalysis.json'):
        d = load(path)
        counts['offline_reanalyses'] += 1
        row = dict.fromkeys(rows[0], 'NOT_APPLICABLE')
        row.update(record_kind='READ_ONLY_REANALYSIS', case_id=d['new_verdict']['case_id'],
                   source_sha=d['producer_commit'], checker_sha=d['checker_commit'],
                   runner_status=d['new_verdict']['status'], checker_rc=d['checker_rc'],
                   evidence=str(path), result_scope=d['result_scope'],
                   dependency_satisfied=d['new_verdict']['dependency_satisfied'])
        rows.append(row)
    # This pre-admission failure had no producer. A later retry legitimately
    # created the first producer result at the plan path; do not join it back.
    failed_admission = RAW / 'admission_C13_attempt01/UNWIND_after_completion/attempt01'
    if failed_admission.exists() and not (failed_admission / 'execution.json').exists():
        row = dict.fromkeys(rows[0], 'NOT_APPLICABLE')
        row.update(record_kind='PRE_ADMISSION_RESOURCE_BUSY', case_id='UNWIND_after_completion',
                   source_sha='1da6b63cc631e63e1673080278bd92b8746b582b',
                   evidence=str(failed_admission / 'npu-smi-info.txt'), admission_attempt=str(failed_admission),
                   orchestrator_rc=1, model_pid='NOT_CREATED', producer_status='NOT_STARTED',
                   checker_status='NOT_RUN', runner_status='NOT_STARTED_RESOURCE_BUSY',
                   dependency_satisfied=False,
                   result_scope='ORIGINAL_PREFLIGHT_FAILURE; LATER_RETRY_RESULT_NOT_ASSOCIATED')
        rows.append(row)
    failed_auth = RAW / 'admission_C15_attempt01/NUMERIC_SENTINEL/attempt01'
    if failed_auth.exists() and not (failed_auth / 'execution.json').exists():
        row = dict.fromkeys(rows[0], 'NOT_APPLICABLE')
        row.update(record_kind='PRE_ADMISSION_AUTH_RECORD_CHANGED', case_id='NUMERIC_SENTINEL',
                   source_sha='1e88c8208670518f63043552b530b1ed3e2f2677',
                   evidence=str(failed_auth / 'check.stderr.log'), admission_attempt=str(failed_auth),
                   orchestrator_rc=1, model_pid='NOT_CREATED', producer_status='NOT_STARTED',
                   checker_status='NOT_RUN', runner_status='NOT_STARTED_AUTH_RECORD_HASH_MISMATCH',
                   earliest_exception_or_failure='changed user authorization record; exact original bytes restored, extra resource statement saved separately',
                   dependency_satisfied=False,
                   result_scope='ORIGINAL_ADMISSION_FAILURE; FOLLOWUP02_RESULT_NOT_ASSOCIATED')
        rows.append(row)
    # Explicit read-only results never count as new producer/device executions.
    native_path = OUT / 'C15_native长度值_C16只读复核.json'
    if native_path.exists():
        d = load(native_path)
        row = dict.fromkeys(rows[0], 'NOT_APPLICABLE')
        row.update(record_kind='READ_ONLY_NATIVE_REANALYSIS', case_id='LIFE_TASK_DUMP',
                   source_sha=d['producer_commit'], checker_sha=d['checker_commit'],
                   evidence=str(native_path), runner_status=d['status'],
                   result_scope=d['result_scope'], dependency_satisfied='NOT_DEVICE_ACCEPTANCE')
        rows.append(row)
        counts['offline_reanalyses'] += 1
    for join_path in sorted(RAW.glob('target_join_*/target-join.json')):
        d = load(join_path)
        row = dict.fromkeys(rows[0], 'NOT_APPLICABLE')
        row.update(record_kind='READ_ONLY_EXPLICIT_TARGET_JOIN', case_id='TARGET4_JOIN',
                   source_sha=d['source_sha'], checker_sha=d['source_sha'],
                   evidence=str(join_path), runner_status=d['status'],
                   result_scope='numeric/execution joint only; admission separately in original per-arm inspect/check/bind/runner; no new NPU',
                   dependency_satisfied='NOT_DEVICE_AUTHORIZATION_VERDICT')
        rows.append(row)
        counts['offline_reanalyses'] += 1
    for case in ('P0', 'CONFIG'):
        failed = RAW / 'admission_C16_attempt01' / case / 'attempt01'
        if (failed / 'inspect.stderr.log').exists() and not (failed / 'execution.json').exists():
            row = dict.fromkeys(rows[0], 'NOT_APPLICABLE')
            row.update(record_kind='PRE_ADMISSION_WRAPPER_PATH_ERROR', case_id=case,
                       source_sha='154f33d99d6b3c6bf373fcfb1af347ae49b915d5',
                       evidence=str(failed / 'inspect.stderr.log'), admission_attempt=str(failed),
                       orchestrator_rc=1, model_pid='NOT_CREATED', producer_status='NOT_STARTED',
                       checker_status='NOT_RUN', runner_status='NOT_STARTED_SOURCE_PATH_TYPO',
                       earliest_exception_or_failure='wrapper used C16_native instead of existing C16_native_bind; preserved original',
                       dependency_satisfied=False, result_scope='orchestration pre-admission error, no device model experiment')
            rows.append(row)
    target = OUT / 'MRV2_实验矩阵与结论.csv'
    with target.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / 'ROUND_COUNTS.json').write_text(json.dumps(dict(
        observed_at=datetime.now(timezone.utc).isoformat(), counts=counts,
        count_scope='round2 completed admission records only; starts are actual launcher children, not startup success; active case counted live in current_status until its execution record closes',
        elapsed_clock='runner wall UTC start + recorded monotonic elapsed; launcher Host ns are separate monotonic domain',
        rows=len(rows)), indent=2) + '\n')
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
