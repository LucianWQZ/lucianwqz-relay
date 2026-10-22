import json,subprocess,time
from common_c13 import *
from tools.p7x_graph_repair6_runner import adjudicate_records
root=RUN/'reanalysis_C12_ABORT_by_C13_01';root.mkdir(exist_ok=False);plan=json.loads((RUN/'C12_prepare_01/case-plan.json').read_text());summary=[]
for point in ['before_replay','after_replay','after_update','after_completion']:
 name='ABORT_'+point;oldpath=RUN/'C12_campaign_01'/name/'runner-result.json';old=json.loads(oldpath.read_text());command=old['records'][1]['argv'][:];command[1]=str(SOURCE/'tools/p7x_graph_repair5.py');command[command.index('--output')+1]=str(root/(name+'-joint.json'));start=time.time_ns()
 with (root/(name+'.stdout')).open('w') as f:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=environment(),timeout=120)
 new=adjudicate_records(plan,name,old['records']);row=dict(producer_commit=plan['commit'],checker_commit='1da6b63cc631e63e1673080278bd92b8746b582b',source_run=str(RUN/'C12_prepare_01'),result_scope='旧C12设备产物的新C13 checker只读复核，非C13新NPU执行',old_result_path=str(oldpath),old_result_sha256=digest(oldpath),old_runner_status=old['status'],checker_argv=command,checker_rc=p.returncode,start_ns=start,end_ns=time.time_ns(),new_verdict=new)
 (root/(name+'-reanalysis.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');summary.append(dict(case=name,old=old['status'],new=new['status'],checker_rc=p.returncode));assert p.returncode==0 and new['dependency_satisfied']
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary,flush=True)
