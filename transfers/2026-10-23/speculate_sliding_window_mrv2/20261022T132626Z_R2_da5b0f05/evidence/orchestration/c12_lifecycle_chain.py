import subprocess,json,time
from common import *
sequence=['CONFIG','A0','A1','B0','LIFE','ABORT_before_replay','ABORT_after_replay','ABORT_after_update','ABORT_after_completion'];plan=json.loads(PLAN.read_text());entries=[]
for case in sequence:
 if time.time()>json.loads(AUTH.read_text())['deadline_epoch_seconds']-600:break
 missing=[dep for dep in plan['cases'][case]['dependencies'] if not (RUN/'C12_campaign_01'/dep/'runner-result.json').exists() or not json.loads((RUN/'C12_campaign_01'/dep/'runner-result.json').read_text()).get('dependency_satisfied')]
 if missing:
  entries.append(dict(case=case,status='NOT_RUN_DEPENDENCY',missing=missing));continue
 a=[PYTHON,str(R/'runs'/SID/'orchestration/admit_case_c12.py'),'--case',case];start=time.time_ns();p=subprocess.run(a)
 result=json.loads((RUN/'C12_campaign_01'/case/'runner-result.json').read_text())
 entries.append(dict(case=case,orchestrator_rc=p.returncode,runner_status=result['status'],dependency_satisfied=result.get('dependency_satisfied'),start_ns=start,end_ns=time.time_ns()))
 (R/'state/R2_C12_LIFECYCLE_CHAIN.json').write_text(json.dumps(entries,indent=2)+'\n')
