import subprocess,json,time
from common_c15 import *
sequence=['NUMERIC_SENTINEL','PERF_OFF_long_01','PERF_ON_long_01','PERF_OFF_long_02','PERF_ON_long_02','PERF_OFF_long_03','PERF_ON_long_03','PROFILE_OFF_long_normal','PROFILE_ON_long_normal','PROFILE_ON_long_materialize','NUMERIC_TARGET4','PREFIX_OFF','TARGET4_OFF','LIFE','ABORT_before_replay','ABORT_after_replay','ABORT_after_update','ABORT_after_completion','UNWIND_before_replay','UNWIND_after_replay','UNWIND_after_update','UNWIND_after_completion']
plan=json.loads(PLAN.read_text());entries=[]
for case in sequence:
 remaining=json.loads(AUTH.read_text())['deadline_epoch_seconds']-time.time()
 if remaining<plan['cases'][case]['timeout_seconds']+1500:break
 missing=[dep for dep in plan['cases'][case]['dependencies'] if not (RUN/'C15_campaign_01'/dep/'runner-result.json').exists() or not json.loads((RUN/'C15_campaign_01'/dep/'runner-result.json').read_text()).get('dependency_satisfied')]
 if missing:
  entries.append(dict(case=case,status='NOT_RUN_DEPENDENCY',missing=missing))
 else:
  argv=[PYTHON,str(R/'runs'/SID/'orchestration/admit_case_c15_followup.py'),'--case',case];start=time.time_ns();p=subprocess.run(argv);path=RUN/'C15_campaign_01'/case/'runner-result.json';result=json.loads(path.read_text()) if path.exists() else dict(status='MISSING_RUNNER_RESULT',dependency_satisfied=False)
  row=dict(case=case,orchestrator_rc=p.returncode,runner_status=result['status'],dependency_satisfied=result.get('dependency_satisfied'),start_ns=start,end_ns=time.time_ns());entries.append(row);print(json.dumps(row),flush=True)
 (R/'state/R2_C15_FOLLOWUP.json').write_text(json.dumps(entries,indent=2)+'\n')
