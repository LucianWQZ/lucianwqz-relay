# 导师评审版：使用说明

本压缩包包含：

- `MRV2_Draft_Sliding_Window_导师评审与讲解版.md`：**主讲稿**，面向师傅/现场演示，按旧版对比→运行样例→架构→接入→风险→测试→编码风格组织；并附 12–15 分钟讲述顺序和问答。
- `img/`：6 张演示流程图，**SVG 为 Markdown 引用的矢量图**，PNG 为兼容性预览；两种格式由同一 SVG 转换，不需要联网。
- `reference/MRV2_Speculative_Draft_Sliding_Window_Final_Design.md`：**原始最终规范设计的逐字副本**（SHA-256：`34bac670d7651f468d75b55300d35df5ca5ab1ef9fd9ffcce53731effcfbcdba`），保留完整 28 章、32 项 Conflict Resolution、37 项 Decision Log、所有 Gate 与 Blocker。

## 使用方式

1. 解压，保持 `.md` 与 `img/` 位于同级。
2. 使用 VS Code 的 `Markdown: Open Preview`（Mac 可 `Cmd+Shift+V`），或 Typora / Obsidian 打开主讲稿。
3. 讲解参考主稿 §16 的时间安排，遇到状态争议跳转 `reference/` 同步对照源稿。
4. 源设计有 **CONDITIONAL** 和 **NOT YET ESTABLISHED**，本稿没有自行宣布 Graph/NPU 验证已通过。

## 同等性边界

这是对原最终架构的**讲解式改写**，不是原文全文原样重印；原始决策、门槛、兼容政策以 `reference/` 的规范性原文为准。主稿 §15 的代码风格注意事项是对设计不变量的工程落实建议，实际项目 lint/type/test 标准优先，不能当作新的 Frozen API 规范。
