# 连续数值证据 v2

真实DSpark.capture→Ascend DFlashAclGraphManager→pinned CudaGraphManager.capture→真实Ascend metadata builder→DSpark._generate_draft/_run_model。
pinned的warmup与实际capture都传NONE；实例collecting期间最后一次输出引用属于该bucket的capture，成功后freeze。旧UT直接传FULL掩盖此问题。默认关闭无sink、无新增clone/event/sync、None返回与replay→consumer→UPDATE→retire顺序不变。

ContinuousReference在独占空scheduler诊断里保存canonical Full/exact/valid、请求映射、输入/绝对position/full slot/query、实际与独立reference metadata、真实各Draft层K/V inventory、graph/reference前后KV、active+padded hidden及同代provider/backing。先验证提交并诊断drain，才读取本代捕获输出。reference只恢复fixture私有Draft完整相关read/write KV，不交换Target；native异常不再finally无条件恢复。

独立checker从canonical重算 S=floor(max(E-1024,0)/128)*128，E=Target ends+7，V=E-S，列[start/128,ceil(E/128))，valid/source bounds/padding/slot。Target padded与Draft dispatch分开（Target1-active/2-padded → Draft(1,7)）。检查声明层K/V的shape/dtype/finite/fullselected范围、reference完全相同前态、本代实际table/exact地址与persistent backing、source/runtime/epoch/plan/summary/launcher/recorder关联。

hidden/Target容差仍atol=rtol=0；私有FIA0.016未改。完整active hidden、K/V后态逐项重算；padding仅finite、shape、read-length0及slot-1约束，不声明padded hidden数值相等。窗口外physical memory事务不在此证据层。

逐样本mmap验证；只保留当前KV与A/前代必要输出/前态digest，finite按chunk处理。A/B判别、A′前态/输出恢复、本代/前代reference匹配独立输出。B无区分力保持OPEN，不升级G5。NUMERIC_MISMATCH被落盘后停止依赖分支，完整前缀仍可读。

Host集成使用W1024/B128/query7、真实P3/P6 BOUND→SUBMITTED→retire→下一代，Target4全部12case；真实Python调用链未整体mock。Native Graph/FIA/stream/event及模型计算使用明确CPU surrogate；不能称NPU数值验证。正常无逐代同步的完整连续reference仍NOT_IMPLEMENTED，当前为DIAGNOSTIC_SERIALIZED。
