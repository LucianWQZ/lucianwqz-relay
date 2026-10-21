# Repair3 Evidence Adjudication

## 2. 原始证据与完整性

只读输入目录：
`/Users/wenqingzhang/Desktop/中转/private-file-relay/transfers/2026-10-20/MRV2_P7X_A3_Repair2/20261019T065743Z_8198ab7a/return`

| 包 | bytes | SHA256 | 校验 |
|---|---:|---|---|
| review.zip | 577782 | 726bbf44393da3dd316c9252728e7a59c13e7e1c29b8d21a9b0d3d4d9649d959 | CRC通过，163 entries；161项包内 hash通过 |
| raw.zip（part001+part002按顺序恢复） | 179215014 | ffe1b1581707509c13aaa100d1b0157aad96ece5423ae7f893025100be995f08 | CRC通过，207 entries；205项 hash通过 |

原 ZIP/part/manifest 均未修改。安全检查拒绝路径越界和 symlink。临时解析位置：`/private/tmp/p7x-repair3.BV5NUG/review`、`raw`；交付辅助目录 `evidence_verification.json` 保留原路径、哈希、排除项，可用附带 verify_evidence.py 重建，不把重新序列化的 JSON hash 当原始 hash。

ARTIFACT_INDEX 声明 file_count=205，实际 files 数组207项：额外两项是明确 self_excluded 的 ARTIFACT_INDEX/SHA256SUMS，没有循环 hash。review 缺42个 .pt与2个大型head比较JSON，恰是声明的raw-only文件；不是损坏。review 51份JSON、raw 53份JSON全部可解析。205个indexed有效文件bytes/hash匹配。38条ledger CMD-0001–0038完整。

9个 import_provenance Python module hash 对应 exact git blob 均匹配；native .so donor仅有记录，不宣称本机执行或重新校验服务器未交付本体。evidence refs 两个是源码符号引用（`draft_window_graph_characterization.py:664/678`、`tools/p7x_graph_repair2.py audit_campaign`），其余实际文件可解析。旧 runtime env/sitecustomize/overlay 构建配方没有随包完整交付；下一轮要求作为文本单独打包。

读取并重新解析：两份 partial、A0/A1/B-observer-off/B-boundaries/G4-A0/G4-B campaign，两个target-boundary，Gate Decisions/Next Local Input/中文报告/Gap报告，source/import manifest、campaign_plan、ledger、trace_probe、B0/B_crashpin stderr、query_trace，以及旧 compare_g4.py/run_official_g4_compare.py/g4_comparison/g3_oracle_partial。没有执行从服务器报告复制的脚本。

## 3. Finding Resolution

| ID | Server claim / 原始实证 | Source fact / 裁决 | Action / Test | Remaining |
|---|---|---|---|---|
| R3-01 | 两次observer-on native SIGSEGV；query_trace call3进入UPDATE query无EXIT；NPUEvent::query / rtEventQueryStatus | ACCEPTED：直接触发调用已定位；不能推断所有ExternalEvent/版本不支持query | 删除observer query helper；记录类型/Host identity，completion=null；禁止调用fake-event红绿测试 | A3同配置重跑确认不再在该点崩溃；native底层根因未证明 |
| R3-02 | record一次query，snapshot/write_artifact再次query | ACCEPTED：导出隐式设备访问是代码缺陷 | snapshot纯Host序列化，采样时间不变；重复导出全等；无事件强引用、weakref可回收 | 设备trace/completion仍OPEN |
| R3-03 | 15/15 capture layer_name=null | ACCEPTED：普通forward不填layer-aware缓存且未把layer传到FIA；原测试预填答案 | 实际forward在已挂载capture context时绑定instance execution layer name；与KV owner分离；真实forward链及5层三descriptor测试 | 新SHA每bucket真实层集合需A3核验 |
| R3-04 | 报告摘要有“update operator not reached” | PARTIALLY_ACCEPTED：持久化update=0属实；未到达UPDATE的归因不成立 | 修正文档，按source/内存/持久化/device四层分类；无功能时序改动 | 不据Python返回推断设备完成 |
| R3-05 | observer-off三bucket功能完成、G4 head-only一致 | PARTIALLY_ACCEPTED：完成输出/inventory属实；不能证明每bucket replay/task；G4仅短smoke | 全集严格比较，raw 21对独立复算通过；max position/exact=27；FULL_TARGET保持OPEN | 长上下文S>0、真实replay与KV对齐另测 |

旧两份 partial 都是10 events /15 operand /1 G4 /1 lifecycle；全部capture operand层名为null，不补填。历史Gate不被新checker或本机green改成PASS。

## 4. 根因、真实调用链和测试漏洞

### 4.1 原生事件

```text
DFlashAclGraphManager.run_fullgraph
  → update_full_graph_params
  → AscendAttentionBackendImpl.update_graph_params
  → graph_task_update_begin / FIA.out / graph_task_update_end / event.record
  → record_parallel_graph_update_operator_operand
  → record_update_operand: _append_operand(...)  [仅内存]
  → record_lifecycle: _query_event_without_sync(event)
  → NPUEvent::query → rtEventQueryStatus → SIGSEGV
```

query_trace: call1 replay event=False，call2导出重查同event=False，call3 UPDATE event无返回。Python except RuntimeError无法捕获native SIGSEGV。

| 层 | 本次旧证据能证明什么 |
|---|---|
| SOURCE_DERIVED_CALL_REACHABILITY | 到达observer之前backend update调用顺序已经执行到event.record返回 |
| IN_MEMORY_RECORD_REACHABILITY | 按exact source，在query调用前已执行_append_operand；无独立内存dump，不冒充durable证据 |
| DURABLE_ARTIFACT | 上次已刷盘的partial仍只有15 capture，0 update；finally在SIGSEGV下未执行 |
| DEVICE_COMPLETION | 未证明；record/return/id(handle)/Host timestamp都不是设备完成 |

### 4.2 逐层身份

真实builder对一个group构建一个metadata对象，再把同对象分配给多个layer key。Repair2按对象去重挂载是正确的，保留预验证、幂等、冲突/Target拒绝、setattr失败回滚和closure固定CaptureIdentity。

普通链是 `Attention layer → impl.forward(layer,...) → forward_impl → forward_fused_infer_attention → full_graph_fia(layer=None) → observer`。构造时 `_layer_name=None`，只有 `_use_layer_aware_fia_graph_replay=True` 才赋值。普通Base为False。原测试用 `impl._layer_name=layer_name` 再直接调full_graph_fia，因此掩盖了真实数据缺口。KV sharing时 `_graph_metadata_layer_name` 表达metadata owner，不等于executing layer。

本次最小绑定：backend实例新增独立 `_capture_observer_layer_name`，仅实际forward遇到已挂capture context的metadata时，从真实 `layer.layer_name` 设置；FIA observer优先使用显式layer参数，否则读取该instance执行身份。没有从共享metadata反推唯一layer、没有按dict轮询名称、没有修改layer-aware策略或KV-sharing replay key。普通无observer路径不设置观测身份；None metadata原行为继续通过。

这不是新增Graph支持范围。backend实例归属于Attention layer；capture closure再次执行真实forward时重新携带实际layer，metadata context仍携带对应descriptor/provider/backing。Host测试替代NPU primitive，但不替代builder/forward/FIA/observer链。


这是历史证据派生裁决；旧SHA Gate不升级。详细原始相对路径和包hash见主报告。
