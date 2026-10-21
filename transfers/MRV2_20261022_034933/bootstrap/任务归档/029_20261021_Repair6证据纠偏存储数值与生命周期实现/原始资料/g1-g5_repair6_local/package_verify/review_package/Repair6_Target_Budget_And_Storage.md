# Target 有界存储与预算

## 实测几何

Target36层，Draft5层；KV heads8、head_dim128、block128、BF16(2byte)；hidden4096、vocab151936。
A的72份K/V各9blocks [9,128,8,128]，单份完整KV集合169,869,312 bytes。
旧inputs151,006,448 bytes：共享2048²boolmask按36layer重复copy；before/after各169,869,312；output393,216。unique storage逐样本见Prefix_Reanalysis。不能把5.31GB当单checkpoint预算，不能盲增2/4GiB。

精确d0基线RED：同一16×16boolmask两layer，实际唯一256bytes，旧_snapshot报needs512、remaining256。新_snapshot按storage/view和选择块去重，两个字段和alias描述均保留，不clone canonical写侧隐藏alias。

## 格式与资源边界

repair6-tensor-store-v1：collection先IN_PROGRESS；sample先PREPARING，完成后原子payload+hash；tensor独立content-addressed bin，<=8MiB chunk，各段offset/bytes/hash、全hash、shape/dtype/逻辑归属。相同数据只存一份bin，原owner/alias描述不丢。
selected KV按稳定block/element顺序流式D2H，mmap读取。logical KV从完整checkpoint与block_owners重建，避免重复序列化。完成record不再整集合torch.save。
完整读写块、未授权写区域outside digest继续覆盖，不能以去重改为抽样。不同generation数据durable后不受后续buffer覆盖。
比较按pair/layer/block处理。legacy.pt weights_only+CPU mmap只读兼容，版本未知拒绝。异常partial保留，重试新attempt；不覆盖原FAIL。
8MiB只约束拷贝临时块，不是进程RSS承诺；OS mmap/模型Host内存仍需监测。连续reference额外Draft pre/post device snapshots上限1GiB，store4GiB，单独记账。

|Profile|单臂bytes|双臂+raw/atomic bytes|
|---|---:|---:|
|base|7102103552|28416802816|
|target4|9244631040|36986912768|

两profile合计65,403,715,584 bytes；准备阶段另要求16GiB reserve（prefix、numeric、日志/trace及临时产物），旧证据占用从实际free扣除。内容去重率不作为必然节省。模型自身Host/HBM峰值由设备记录，未伪造本地实测。

|场景|blocks|单KV集合|checkpoint预算|sample总量上界|
|---|---:|---:|---:|---:|
|A|9|169869312|355276800|699209728|
|B|10|188743680|393025536|774707200|
|A_prime|9|169869312|355276800|699209728|
|short|1|18874368|53286912|95229952|
|long|9|169869312|355276800|699209728|
|boundary|8|150994944|317528064|623712256|
|nonaligned|10|188743680|393025536|774707200|
|mixed|11|207618048|433729536|853159936|
|padding|2|37748736|93990912|173682688|
|return-short|1|18874368|53286912|95229952|
|three-active-four-padded|21|396361728|817127424|1614045184|
|four-active|28|528482304|1081368576|2142527488|
