# Repair5 原始证据纠偏（历史官方FAIL不覆盖）

Device SHA d0a3fc3d42d7d97e5e7da3890d2710263a097e63；RUN_ID 20261020T144145Z_d0a3fc3d。本轮是离线重判，不是新设备执行。

## 接收核验

review 2,619,378 bytes / 52b3bf122c0c63ca35d63eecc32e56503d2ea133a60443b6d3cf6b567794b1dc。
raw 545,358,867 bytes / 6b58da786bfe8ef095f20d771891086c85e79cf678087c42756864f876d5aea1。
六片顺序/每片hash、整包、CRC、路径、成员bytes/hash、JSON实际本地核验；review434成员=432索引数据+2索引，raw1001=999+2。不是引用服务器receiver自检。
原始return只读。辅助目录input单次抽取供CPU mmap；没有重复复制四份5GB tensor集合。

## 四臂完整前缀

|序号|场景|G4F OFF/ON|TARGET4 OFF/ON|本地裁决|
|---|---|---|---|---|
|1|A|CAPTURED_COMPLETE|CAPTURED_COMPLETE|完整Target对齐数值相等|
|2|B|同上|同上|同上|
|3|A_prime|同上|同上|同上|
|4|short|同上|同上|同上|
|5|long|同上|同上|同上|
|6|boundary|同上|同上|同上|
|7|nonaligned|同上|同上|同上|
|8|mixed|BLOCKED|BLOCKED|budget cannot hold post-forward KV and output|

每个.pt有8条，而非0。前7 checkpoint.status=CAPTURED。两profile各7对，全量复核hidden/logits、声明逻辑KV前/后态、slot/write合法性、outside digest、Draft后Target快照，atol=rtol=0相等。逐样本/逐逻辑block的dtype/shape/finite/max_abs/max_rel完整保留。整体PARTIAL_PREFIX_VALID/INCOMPLETE_COVERAGE，原child EXCEPTION不能改成PASS。

两组ON各7代、7bound、35update_operator、7proposal_retired；DIAGNOSTIC_COMPLETE，retired=true。
tokens A=[17,23,21,15,4,315,220]；
B=[23,21,16,15,4,315,458]；A_prime=A。
同一实验backing相同，generation/epoch递增；full_exact有1159/1287/1159/39/1159/1031/1160。
A/A_prime完整Target逻辑KV前态、位置、hidden相等。
Repair5没有单独dump完整Draft pre-KV；deterministic _stage是源码证据，不能冒充全部Draft前态raw证明。因此恢复的是“真实MRV2串行诊断token ABA有效前缀”，不是正常reuse、完整G2/G5。

## 其他纠正

- B1真实11组，O0/O1 provider存在且observer关闭，不是关闭Graph实验路径。
- control无native trace；实际4份normal、1份LIFE。不是8份native trace。
- long Target replay (1,8)=24、(2,16)=6；short各6。Draft short21、long47。
- registry41=真实Target模型36+Draft5，不是41 Target执行层。
- 约5.31GB是整个collection，不是单样本预算。
- 自然short21/21、long1 12/12是已取hidden相同的HEAD数值结论；long2 14/14中4对相同输入PASS、10对不满足前提；mixed18/14中2对相同、12对不满足、4未配对。
  旧记录缺业务identity，新严格关联保持OPEN。HEAD不能代替完整Target/KV前态。
- flow存在但未唯一归属，与平台没有字段不是一回事。
