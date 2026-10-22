import json,pathlib,os,hashlib,time
R=pathlib.Path('/mnt/share/z00937950/project/speculate_sliding_window_mrv2/dev/adapt');end=time.monotonic()+1200
keys=['PYTHONPATH','VLLM_VERSION','ASCEND_RT_VISIBLE_DEVICES','ASCEND_VISIBLE_DEVICES','LD_LIBRARY_PATH','VLLM_USE_V2_MODEL_RUNNER','VLLM_ENABLE_V1_MULTIPROCESSING','ASCEND_LAUNCH_BLOCKING','TASK_QUEUE_ENABLE','COMBINED_ENABLE','MULTI_STREAM_MEMORY_REUSE','TORCH_DEVICE_BACKEND_AUTOLOAD','PYTORCH_NPU_ALLOC_CONF','ASCEND_CUSTOM_OPP_PATH']
while time.monotonic()<end:
 s=json.loads((R/'journal/current_status.json').read_text())
 if s.get('current_case') in ['B0','LIFE_TASK_BIND','NUMERIC_SENTINEL']:
  for pid in s.get('model_worker_pids',[]):
   p=pathlib.Path('/proc')/str(pid)
   try:
    argv=(p/'cmdline').read_text().split('\0')
    if not any(x==str(R/'candidates/C17_native_disclosure/vllm-ascend/tools/p7x_graph_repair2.py') for x in argv):continue
    libs=sorted({x.split()[-1] for x in (p/'maps').read_text().splitlines() if any(y in x for y in ['libvllm','vllm_ascend_C','libcust_opapi','libascendcl','libtorch_npu','libruntime','libacl_rt']) and x.split()[-1].startswith('/')})
    if not all(any(token in path for path in libs) for token in ['libvllm_ascend_kernels','vllm_ascend_C','libcust_opapi','libtorch_npu','libacl_rt','libruntime']):continue
    env=dict(x.split('=',1) for x in (p/'environ').read_text().split('\0') if '=' in x)
    a=dict(pid=pid,case=s['current_case'],source_sha='057b8e0300967e68e3f2a78c5910c8877521674e',observed_ns=time.time_ns(),argv=argv,exe=os.readlink(p/'exe'),start_ticks=(p/'stat').read_text().split()[21],environment={k:env.get(k,'UNSET') for k in keys},loaded_libraries=[dict(path=x,sha256=hashlib.file_digest(open(x,'rb'),'sha256').hexdigest()) for x in libs],scope='actual same-process MRV2 worker; source class/import path separately in campaign; no device reads')
    q=R/'runs/20261022T132626Z_R2/environment/C17_actual_worker_provenance_complete.json';q.write_text(json.dumps(a,indent=2)+'\n');print('captured',pid,s['current_case'],len(libs),flush=True);raise SystemExit(0)
   except (FileNotFoundError,ProcessLookupError):pass
 time.sleep(5)
print('bounded provenance window expired without qualifying live worker',flush=True)
raise SystemExit(2)
