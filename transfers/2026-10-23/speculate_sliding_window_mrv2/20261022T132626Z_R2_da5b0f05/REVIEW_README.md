# 审查包阅读入口

先读阶段总结、候选与证据对应表、Profiling分析。20项分开裁决见ACCEPTANCE_VERDICTS.json；public Graph Gate冻结，正常多代/physical-read待owner。

根目录为本轮自包含交付；evidence保存原件副本及路径映射。证据中的绝对路径/相对raw路径指向服务器原件，COPY_INDEX.json逐文件给出服务器路径、bytes/hash；RAW_ARTIFACT_INDEX索引大型tensor/trace。未复制模型、整个历史归档或凭据。

CPU小样本在evidence/compact_numeric_C19，普通python3 recompute.py可独立复算，不用-O、无需torch/NPU/pickle。它仅覆盖保留输入/输出和ABA，完整KV/metadata/执行关联用服务器原件。

历史/编排命令供审计，不自动执行。恢复从RESUME核对当前进程/原deadline，再核对固定candidate、pin和runtime；bundle前置精确Repair7且已实际恢复验证。Source代码在Git bundle和patch，必要Host拒绝反例和旧失败保留。

服务器CRC/严格JSON/文件引用与hash自检不代表用户接收验证。用户下载后应核对外部DOWNLOAD_MANIFEST及本ZIP SHA，再运行CPU复算。
