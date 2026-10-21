# 连续数值合同

真实配置入口→DSpark.capture→真实builder→NONE capture closure输出引用→P3/P6 bind→Graph replay(None)→consumer→UPDATE→诊断完成→本代hidden与同Window eager reference→分块writer→联合checker→retire→下一代。
Host集成保留这些Python组件及状态转换；Graph/FIA/event/stream、模型算术使用显式CPU native替身。未执行A3。

独立性：checker从canonical Full/exact/valid重算S/E/V与列范围，reference重新构建Window读取；不直接采被测Window当答案。双方共享模型权重、模型forward实现、canonical输入及部分backend实现，因此共同模型/backend错误不由相等证明排除。现有负例覆盖start/length、generation、backing内容、缺层/NaN/缺chunk/前态损坏，不能用schema镜像代替NPU。
Target active/padded 与Draft dispatch分开；Target1-active/2-padded仍可Draft(1,7)。只比较有效hidden，padding检查finite/shape/read0/slot-1。
预声明容差：连续hidden及受控Target atol=rtol=0；私有FIA0.016另列不变。B不可区分则OPEN，不能改容差或只用argmax。

NUMERIC_SENTINEL=前三个A/B/A_prime，生产者sample_limit与plan.numeric_samples=3、argv、summary同时核对；状态PASS_NUMERIC_SENTINEL_ONLY不是12场景PASS。
NUMERIC_TARGET4=完整12场景，只有前哨通过才允许；Base仍无Target(4,32)。诊断数值FAIL落盘后停止后代；native提交不确定74只Host错误导出、隔离退出，不继续恢复设备/复用；不消费已SUBMITTED carrier。
默认关闭无sink/输出保留/事件查询/D2H；不将合法None制造为hash。
