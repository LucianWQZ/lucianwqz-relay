# 授权设备准入：管理员辅助，不自动猜映射

授权host Phy-ID 0–7中分配给本任务的**一个**芯片；TP1。不等同容器0/runtime0/进程npu:0。
1. 在导入torch/NPU前由管理员设置本进程及后续子进程的实际可见性；执行committed device.py inspect（只读npu-smi -m、/dev节点major/minor、namespace、boot ID、环境/PID）。
2. owner根据宿主/容器实际映射与资源占用提供receipt。不能把其他用户Phy8 PID当自己的证据。未知则BLOCKED，不启动模型，不重建/提权容器。
3. receipt未有probe时只允许在映射已明确后运行device.py probe：1024元素，仅本PID；管理员关联其host/container PID、命令、开始/结束、节点与设备记录，填入原始证据path/hash。无映射证明禁止先probe。
4. check要求有效<=1小时、boot/namespace/visibility/节点相同、host0–7、probe0退出与自身PID证据。每个case启动前重新检查资源并签发绑定run/source/tree/case的receipt。
5. BIND_DEVICE.py保存新的admitted-plan，不改原计划参数；runner在任何child启动前核验receipt/hash。

receipt v1字段：schema=repair7-device-receipt-v1,run_id,source_sha,source_tree,case_id,allocation_owner,issued_at,expires_at,host_phy_id,tp=1,allocated_nodes{路径:{major,minor}},namespace,boot_id,visibility,mapping_evidence/resource_evidence[{path,sha256}],probe{host_pid,container_pid,command,start_ns,end_ns,host_phy_id,status=EXITED,returncode=0,host_process_evidence:{path,sha256},pid_namespace_evidence:{path,sha256}}。
这是owner签发内容的完整性/一致性校验，不是密码学签名，也不自动理解任意npu-smi文本。管理员仍须复核映射语义；实际worker PID/继承环境及设备归属需随campaign保存。没有实现自动宿主PID发现/worker物理证明；不宣称工具单独能证实分配。
禁止reset、kill无关任务、改变设备挂载/权限、自动回退Phy8。若管理员协助仍不能证明映射，保持BLOCKED_DEVICE_MAPPING。
