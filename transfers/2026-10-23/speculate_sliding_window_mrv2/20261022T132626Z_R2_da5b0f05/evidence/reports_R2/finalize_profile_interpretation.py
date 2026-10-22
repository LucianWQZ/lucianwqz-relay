"""Assemble reviewed flow semantics after the source-specific analysis scripts."""
from pathlib import Path
import json
O=Path(__file__).resolve().parent;p=O/'MRV2_Profiling_Summary.json';d=json.loads(p.read_text());c=json.loads((O/'C17_direct_flow_实际目的地分类.json').read_text());d['diagnostic_comparison_C17']['direct_flow_destination_classification']=c;d['diagnostic_comparison_C17']['flow_caveat']='raw direct_matched21 means any flow in Host range; all63 event/queue destinations, MODEL_EXECUTE direct0'
for row in list(d['cases'].values())+list(d['diagnostic_comparison_C17']['cases'].values()):
 n=row['observed_draft_graph_replays'];row['whole_request_elapsed_per_observed_draft_replay_ms']=row['active_group_elapsed_ms']/n if n else 'NOT_AVAILABLE';row['normalized_elapsed_scope']='all external request work incl Target/prefill, not Draft kernel latency'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');p=O/'MRV2_Profiling分析.md';marker='### LIFE中“direct flow”必须按实际目的地细分';s=p.read_text().split(marker)[0];p.write_text(s.rstrip()+'\n\n'+(O/'profiling_C17/flow_interpretation.md').read_text().rstrip()+'\n')
