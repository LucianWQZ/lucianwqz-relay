"""Summarize actual profile exports without adjacency or shape attribution."""
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt')
RAW = ROOT/'runs/20261022T132626Z_R2/raw'
ANALYSIS_ROOT=ROOT/'reports/20261022T132626Z_R2' 


def load(path):
    return json.loads(path.read_text())


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 << 20), b''):
            h.update(block)
    return h.hexdigest()


def starts(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'source_start_column' and type(child) is int:
                yield child
            yield from starts(child)
    elif isinstance(value, list):
        for child in value:
            yield from starts(child)


def union_duration(intervals):
    total = Decimal(0)
    end = None
    for start, stop in sorted(intervals):
        if end is None or start > end:
            total += stop - start
            end = stop
        elif stop > end:
            total += stop - end
            end = stop
    return float(total)


def trace_stats(case_dir):
    traces = list((case_dir / 'trace').rglob('trace_view.json'))
    if len(traces) != 1:
        return dict(status='NOT_AVAILABLE', trace_count=len(traces))
    path = traces[0]
    document = load(path)
    events = document['traceEvents'] if isinstance(document, dict) else document
    selected = defaultdict(list)
    labels = {'acl_memcpy_host_to_device', 'acl_memcpy_device_to_host', 'acl_memcpy_device_to_device',
              'Event::synchronize', 'Event::wait', 'MODEL_EXECUTE', 'EVENT_WAIT', 'NOTIFY_WAIT',
              'MEM_WAIT_VALUE', 'MEMCPY_ASYNC'}
    for event in events:
        if event.get('ph') == 'X' and event.get('name') in labels:
            selected[event['name']].append(float(event['dur']))
    stats = {name:dict(count=len(values), summed_duration_us=sum(values),
                       median_duration_us=statistics.median(values)) for name,values in selected.items()}
    nested = {}
    for label in ('Draft_materialize', 'Draft_metadata_bind', 'Draft_UPDATE_CALL', 'Draft_retire_host'):
        parents = [e for e in events if e.get('ph') == 'X' and e.get('name') == 'repair5/' + label]
        child_stats = defaultdict(list)
        for parent in parents:
            low = Decimal(str(parent['ts']))
            high = low + Decimal(str(parent['dur']))
            for child in events:
                if child.get('ph') != 'X' or child.get('name') not in labels:
                    continue
                if (child.get('pid'), child.get('tid')) != (parent.get('pid'), parent.get('tid')):
                    continue
                start = Decimal(str(child['ts']))
                if low <= start and start + Decimal(str(child['dur'])) <= high:
                    child_stats[child['name']].append(float(child['dur']))
        nested[label] = dict(parent_count=len(parents), children={
            name:dict(count=len(values), summed_duration_us=sum(values)) for name,values in child_stats.items()})
    if 'acl_memcpy_device_to_device' not in stats:
        stats['acl_memcpy_device_to_device'] = 'NOT_AVAILABLE: no explicit direction label in this export'
    task_path = next((case_dir / 'trace').rglob('task_time.csv'), None)
    task_data = {}
    if task_path:
        tasks = list(csv.DictReader(task_path.open()))
        keys = Counter((r['Device_id'], r['stream_id'], r['task_id']) for r in tasks)
        kernels = [r for r in tasks if r['kernel_name'] != 'N/A']
        intervals = [(Decimal(r['task_start(us)'].strip()), Decimal(r['task_stop(us)'].strip())) for r in kernels]
        task_data = dict(path=str(task_path), rows=len(tasks),
                         duplicate_device_stream_task_keys=sum(n-1 for n in keys.values() if n>1),
                         streams=dict(Counter(r['stream_id'] for r in tasks)),
                         named_kernel_count=len(kernels),
                         fia_named_kernel_count=sum('FusedInferAttentionScore' in r['kernel_name'] for r in kernels),
                         summed_named_kernel_duration_us=sum(float(r['task_time(us)']) for r in kernels),
                         named_kernel_interval_union_us=union_duration(intervals),
                         named_kernel_span_us=float(max(e for _,e in intervals)-min(s for s,_ in intervals)) if intervals else None,
                         task_internal_operand='NOT_AVAILABLE', physical_read_set='NOT_AVAILABLE',
                         attribution='Kernel name identifies FIA family only; no Target/Draft/layer/generation inference')
    flow_path = RAW / ('profile_analysis_' + case_dir.parent.name.split('_')[0]) / case_dir.name / 'flow-analysis-module.json'
    flow = load(flow_path) if flow_path.exists() else None
    return dict(status='ANALYZED', source_trace=str(path), trace_bytes=path.stat().st_size,
                trace_sha256=digest(path), event_count=len(events), selected_event_statistics=stats,
                nested_same_thread_copy_sync=nested,
                task_table=task_data,
                flow_analysis=dict(path=str(flow_path), counts=flow['flow_counts'], coverage=flow['coverage'],
                                   manager_flow_counts=[len(r['replay_plus_update_flow_indices']) for r in flow['replays']],
                                   split='UNRESOLVED: replay and UPDATE device tasks cannot be split from these flows') if flow else 'NOT_AVAILABLE',
                clock_contract='Trace exported timestamps only; never subtract Host monotonic_ns from trace timestamps',
                device_idle='NOT_AVAILABLE: gaps between named kernels are not whole-device idle')


def analyze_case(path):
    campaign = load(path / 'campaign.json')
    profile = load(path / 'profile.json')
    groups = [g for g in profile['groups'] if g['active']]
    calls = [c for c in profile['calls'] if c['active']]
    outputs = campaign.get('outputs', [])
    token_count = sum(len(ids) for batch in outputs for ids in batch.get('token_ids', []))
    request_count = sum(len(batch.get('token_ids', [])) for batch in outputs)
    elapsed_ms = sum(g['end_ns']-g['start_ns'] for g in groups)/1e6
    offsets = list(starts(profile.get('calls', [])))
    window_descriptors = [d for c in calls for d in c.get('window_descriptors', [])]
    return dict(case_id=path.name, evidence_relative_path=str(path.relative_to(RAW)),
                source=campaign['identity'], config_sha256=campaign['config_sha256'],
                request_sha256=campaign['request_manifest']['sha256'], capture_profile=campaign['capture_profile'],
                profiler_enabled=profile['profiler_enabled'], profiler_scope=profile['scope'], configuration=profile['profile_configuration'],
                observer_enabled=campaign.get('observer_enabled'),
                diagnostic_artifacts=campaign.get('diagnostic_artifacts'),
                initialization_seconds=campaign['initialization_seconds'],
                active_groups=len(groups), completed_requests=request_count, generated_tokens=token_count,
                prompt_token_lengths=[len(ids) for batch in outputs for ids in batch.get('prompt_token_ids', [])],
                active_group_elapsed_ms=elapsed_ms,
                per_generated_token_ms=elapsed_ms/token_count if token_count else 'NOT_AVAILABLE',
                group_times=[dict(label=g['label'],elapsed_ms=(g['end_ns']-g['start_ns'])/1e6) for g in groups],
                observed_draft_graph_replays=sum(c['label']=='Draft_REPLAY_SUBMIT' for c in calls),
                observed_target_graph_replays=sum(c['label']=='Target_REPLAY_SUBMIT' for c in calls),
                target_verifications_total='NOT_AVAILABLE: Target Graph calls do not cover all eager/prefill verification work',
                acceptance='NOT_AVAILABLE: no acceptance telemetry in frozen profile artifact',
                descriptors=dict(Counter(json.dumps(c.get('descriptor'),sort_keys=True) for c in calls if c['label']=='Draft_REPLAY_SUBMIT')),
                runtime_window_descriptors=window_descriptors,
                actual_window_crop=dict(observed=any(x>0 for x in offsets),max_source_start_column=max(offsets) if offsets else 'NOT_AVAILABLE',
                                        scope='runtime descriptor evidence, not prompt length'),
                host_statistics=profile['host_statistics'], host_subrange_coverage=profile['host_subrange_coverage'],
                joint=load(path/'profile-joint.json') if (path/'profile-joint.json').exists() else 'NOT_AVAILABLE',
                trace=trace_stats(path) if profile['profiler_enabled'] else dict(status='CONTROL_NO_PROFILER'))

