"""Build a bounded, immutable C19 review directory; update LATEST only after checks."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,zipfile,subprocess,re
R=Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');SID='20261022T132626Z_R2';SHA='da5b0f054c4b94362ff3539de911b26b4074052a';O=R/'reports'/SID;RAW=R/'runs'/SID/'raw';D=R/'return'/f'{SID}_{SHA[:8]}';D.mkdir(exist_ok=False);v=json.loads((O/'ACCEPTANCE_VERDICTS.json').read_text());assert v['stage']=='FINAL_CASE_RECORDS_COMPLETE';assert not json.loads((R/'runs'/SID/'environment/final_release_check/snapshot.json').read_text())['task_processes'];copied=[]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def copy(src,dst):
 assert src.is_file() and not src.is_symlink(),src
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);copied.append(dict(package_path=str(dst.relative_to(D)),source_path=str(src),bytes=dst.stat().st_size,sha256=sha(dst)))
rootfiles=['MRV2_持续开发阶段总结.md','MRV2_实验矩阵与结论.csv','MRV2_候选与证据对应表.md','MRV2_Profiling分析.md','MRV2_Profiling_Summary.json','MRV2_Graph剩余问题与验收边界.md','平台问题单.md','NEXT_SESSION_HANDOFF.json','RESUME.md','DECISION_QUEUE.md','ACCEPTANCE_VERDICTS.json','本轮commit清单.txt','完整恢复链_Repair7至C19_commits.txt','本轮关键diff_C12至C19.patch','源码差异_Repair7至da5b0f05.patch','MRV2_da5b0f05_from_Repair7.bundle','Git_bundle_恢复自检_da5b0f05.json']
for name in rootfiles:copy(O/name,D/name)
copy(R/'state/STORAGE_BINDING.json',D/'STORAGE_BINDING.json')
# New evidence only; no historical archive, model, credential or compiled runtime bundle.
for p in sorted(O.iterdir()):
 if p.is_file() and p.name not in rootfiles and p.suffix in ('.md','.json','.csv','.py','.log','.svg','.png','.txt') and p.stat().st_size<4<<20:copy(p,D/'evidence/reports_R2'/p.name)
for folder in ('compact_numeric_C19','profiling_C15','profiling_C17','orchestration_snapshots','admission_negative_01','platform_sources'):
 for p in sorted((O/folder).rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:copy(p,D/'evidence'/folder/p.relative_to(O/folder))
for name in ('C10_真实padding合同与复核.md',):
 p=R/'return'/name
 if p.exists():copy(p,D/'evidence/history'/name)
for name in ('ROUND2_SESSION.json','ROUND2_USER_AUTHORIZATION_RECORD.json','R2_USER_RESERVATION_CONFIRMATION_20261022T1626Z.json','R2_C12_RUNTIME_OVERLAY.json','R2_C19_RUNTIME_OVERLAY.json','R2_C19_HOST_EVIDENCE.json','R2_C19_CAMPAIGN.json','PATH_BINDING.json','SESSION_STATE.json','R2_TOOL_SESSIONS.json'):
 copy(R/'state'/name,D/'evidence/state'/name)
for name in ('progress.log','01_迭代时间线.md','00_当前进展.md','current_status.json'):
 copy(R/'journal'/name,D/'evidence/journal'/name)
ENV=R/'runs'/SID/'environment'
for name in ('C19_actual_worker_provenance_complete.json','C19_numeric_storage_environment.json','C17_actual_worker_provenance_complete.json','C15_actual_worker_provenance.json','profile_host_load.jsonl','profile_host_monitor.json','navigation_C19_monitor.json'):
 p=ENV/name
 if p.exists():copy(p,D/'evidence/environment'/name)
for p in (ENV/'final_release_check').iterdir():
 if p.is_file():copy(p,D/'evidence/environment/final_release_check'/p.name)
for p in sorted((R/'runs'/SID/'orchestration').glob('*.py')):
 if any(s in p.name for s in ('c12','c13','c15','c16','c17','c19')):copy(p,D/'evidence/orchestration'/p.name)
# Exact plan, joints, actual launch/admission and minimal original error artifacts.
for name in ('case-plan.json','local-candidate-manifest.json','config-schema.json'):copy(RAW/'C19_prepare_01'/name,D/'evidence/C19_plan'/name)
for entry in json.loads((R/'state/R2_C19_CAMPAIGN.json').read_text()):
 case=entry['case'];base=RAW/'C19_prepare_01'/case;result=RAW/'C19_campaign_01'/case/'runner-result.json';copy(result,D/'evidence/C19_cases'/case/'runner-result.json')
 for p in base.glob('*.json'):
  if p.name in ('campaign.json','joint.json','acceptance.json','numeric-joint.json','lifecycle-joint.json','task-dump-index.json','task-dump-joint.json','native-bindings-joint.json','python-unwind.json','unwind-joint.json','abort-check.json','abort-partial.json','result.json','profile-joint.json'):copy(p,D/'evidence/C19_cases'/case/p.name)
 launcher=RAW/'C19_prepare_01/launchers'/case
 if (launcher/'launcher.json').exists():copy(launcher/'launcher.json',D/'evidence/C19_cases'/case/'launcher.json')
 admission=RAW/'admission_C19_attempt01'/case/'attempt01'
 for name in ('execution.json','inspect.json','check.json','user-machine-receipt.json','storage-budget.json','npu-smi-info.txt','npu-smi-after-exit.txt'):
  p=admission/name
  if p.exists():copy(p,D/'evidence/C19_admission'/case/name)
for p in (RAW/'C19_prepare_01/LIFE_TASK_BIND/native-graph-json').glob('*.json'):copy(p,D/'evidence/C19_cases/LIFE_TASK_BIND/native-graph-json'/p.name)
for p in (RAW/'target_join_C19_01').iterdir():
 if p.is_file():copy(p,D/'evidence/target_join_C19_01'/p.name)
for root in (RAW/'probe_phy0_04',RAW/'C17_prepare_02/LIFE_TASK_BIND',RAW/'admission_C16_attempt01/P0/attempt01',RAW/'admission_C16_attempt01/CONFIG/attempt01'):
 for p in root.iterdir():
  if p.is_file() and p.stat().st_size<2<<20:copy(p,D/'evidence/preserved_originals'/root.relative_to(RAW)/p.name)
for p in (RAW/'reanalysis_C12_ABORT_by_C13_01').glob('*.json'):copy(p,D/'evidence/preserved_originals'/p.parent.name/p.name)
# Index large originals by existing content hashes; do not redundantly read all tensor payloads.
rawindex=[]
for path in sorted(RAW.iterdir()):
 if not path.is_dir():continue
 files=[p for p in path.rglob('*') if p.is_file()];rawindex.append(dict(path=str(path),files=len(files),logical_bytes=sum(p.stat().st_size for p in files),retention='SERVER_ONLY',hash_contract='producer sample/chunk manifests and joint validations; profile trace SHA in Profiling Summary; no redundant full rehash'))
(D/'RAW_ARTIFACT_INDEX.json').write_text(json.dumps(dict(raw_root=str(RAW),directories=rawindex,server_originals_not_copied=True,model_weights_not_included=True),ensure_ascii=False,indent=2)+'\n')
(D/'REVIEW_README.md').write_text('''# 审查包阅读入口

先读阶段总结、候选与证据对应表、Profiling分析。20项分开裁决见ACCEPTANCE_VERDICTS.json；public Graph Gate冻结，正常多代/physical-read待owner。

根目录为本轮自包含交付；evidence保存原件副本及路径映射。证据中的绝对路径/相对raw路径指向服务器原件，COPY_INDEX.json逐文件给出服务器路径、bytes/hash；RAW_ARTIFACT_INDEX索引大型tensor/trace。未复制模型、整个历史归档或凭据。

CPU小样本在evidence/compact_numeric_C19，普通python3 recompute.py可独立复算，不用-O、无需torch/NPU/pickle。它仅覆盖保留输入/输出和ABA，完整KV/metadata/执行关联用服务器原件。

历史/编排命令供审计，不自动执行。恢复从RESUME核对当前进程/原deadline，再核对固定candidate、pin和runtime；bundle前置精确Repair7且已实际恢复验证。Source代码在Git bundle和patch，必要Host拒绝反例和旧失败保留。

服务器CRC/严格JSON/文件引用与hash自检不代表用户接收验证。用户下载后应核对外部DOWNLOAD_MANIFEST及本ZIP SHA，再运行CPU复算。
''')
(D/'COPY_INDEX.json').write_text(json.dumps(dict(files=copied,scope='exact byte copies, source paths verified while assembling'),ensure_ascii=False,indent=2)+'\n')
# Verify all copied bytes and strict JSON, including SDK native originals.
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate key '+str(k))
  d[k]=v
 return d
def bad(s):raise ValueError('nonstandard JSON '+s)
files=sorted(p for p in D.rglob('*') if p.is_file());json_count=0
for p in files:
 if p.suffix=='.json':json.loads(p.read_bytes(),object_pairs_hook=unique,parse_constant=bad);json_count+=1
 if p.suffix=='.jsonl':
  for line in p.read_text().splitlines():
   if line.strip():json.loads(line,object_pairs_hook=unique,parse_constant=bad)
 if p.suffix in ('.md','.json','.jsonl','.py','.log','.txt','.patch'):
  text=p.read_text(errors='replace');assert not re.search(r'\bgh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|\bAKIA[A-Z0-9]{16}\b',text),'possible secret '+str(p)
for item in copied:assert Path(item['source_path']).is_file() and sha(D/item['package_path'])==item['sha256']
# Original gates' server paths remain resolvable; no missing references hidden by packet copying.
references=[]
for verdict in v['verdicts'].values():
 for ref in verdict['evidence']:
  p=R/ref;assert p.exists(),ref;references.append(dict(path=ref,exists=True))
cpu=subprocess.run(['/usr/local/python3.11.10/bin/python',str(D/'evidence/compact_numeric_C19/recompute.py')],capture_output=True,text=True,timeout=60);assert cpu.returncode==0,cpu.stderr;assert json.loads(cpu.stdout)['producer_commit']==SHA
(D/'SERVER_PREPACK_CHECK.json').write_text(json.dumps(dict(observed_utc=datetime.now(timezone.utc).isoformat(),strict_json_files=json_count,copy_hashes='PASS',references=references,compact_cpu_recompute=json.loads(cpu.stdout),bundle_restore_evidence='Git_bundle_恢复自检_da5b0f05.json',server_only_not_user_receipt=True),ensure_ascii=False,indent=2)+'\n')
# This index intentionally excludes itself and the ZIP/outer download manifest.
files=sorted(p for p in D.rglob('*') if p.is_file());index=[dict(path=str(p.relative_to(D)),bytes=p.stat().st_size,sha256=sha(p)) for p in files];(D/'PACKAGE_FILE_INDEX.json').write_text(json.dumps(dict(files=index,self_excluded=True,zip_and_outer_manifest_excluded=True),ensure_ascii=False,indent=2)+'\n')
z=D/f'MRV2_Server_Dev_review_{SID}_{SHA[:8]}.zip'
with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
 for p in sorted(D.rglob('*')):
  if p.is_file() and p!=z:archive.write(p,str(p.relative_to(D)))
assert z.stat().st_size<20<<20,z.stat().st_size
with zipfile.ZipFile(z) as archive:
 assert archive.testzip() is None;names=archive.namelist();assert len(names)==len(set(names));assert not any(n.startswith('/') or '..' in Path(n).parts for n in names)
 for name in rootfiles+['STORAGE_BINDING.json','PACKAGE_FILE_INDEX.json']:assert name in names,name
 for name in names:
  if name.endswith('.json'):json.loads(archive.read(name),object_pairs_hook=unique,parse_constant=bad)
(D/'ZIP_MEMBER_LIST.txt').write_text('\n'.join(names)+'\n');check=dict(observed_utc=datetime.now(timezone.utc).isoformat(),zip=str(z),bytes=z.stat().st_size,sha256=sha(z),crc='PASS',unique_members=len(names),strict_json='PASS',copy_hashes='PASS',references='PASS',bundle_restore='PASS_EXACT_SHA_TREE',compact_cpu_recompute='PASS_RETAINED_OUTPUT_NUMERIC_AND_ABA_ONLY',server_selfcheck=True,user_receipt_verified=False);(D/'SERVER_FINAL_SELF_CHECK.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
manifest=dict(schema='mrv2-download-manifest-v3',session_id=SID,source_sha=SHA,source_tree='af4519a635d6ccd70646f77195fde18368bdf22b',start_utc='2026-10-22T13:26:26+00:00',task_deadline_utc='2026-10-22T23:26:26+00:00',packaged_utc=datetime.now(timezone.utc).isoformat(),server_selfcheck=check,server_selfcheck_not_user_receipt=True,files=[dict(path=str(p),name=p.name,bytes=p.stat().st_size,sha256=sha(p),chat_upload_suitable=p.suffix in ('.zip','.bundle','.md','.json','.csv','.txt'),scope='review only, no model/credentials') for p in sorted(D.iterdir()) if p.is_file()],server_only_raw=str(RAW),large_raw_upload_to_chat=False,manifest_self_hash_reported_by='return/LATEST.json and final terminal output');m=D/'DOWNLOAD_MANIFEST.json';m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');json.loads(m.read_text(),object_pairs_hook=unique,parse_constant=bad)
latest=dict(schema='mrv2-latest-reviewed-delivery-v1',session_id=SID,source_sha=SHA,source_tree=manifest['source_tree'],directory=str(D),review_zip=dict(path=str(z),bytes=z.stat().st_size,sha256=sha(z)),download_manifest=dict(path=str(m),bytes=m.stat().st_size,sha256=sha(m)),server_selfcheck='PASS',user_receipt_verified=False,created_utc=manifest['packaged_utc']);temp=R/'return/LATEST.json.partial';temp.write_text(json.dumps(latest,ensure_ascii=False,indent=2)+'\n');temp.replace(R/'return/LATEST.json');print(json.dumps(latest,ensure_ascii=False))
