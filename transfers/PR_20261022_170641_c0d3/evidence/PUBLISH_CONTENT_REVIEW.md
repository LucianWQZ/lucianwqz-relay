# 公开发布载荷有界内容检查

## 结论

**PUBLISH_CONTENT_REVIEW: PASS_WITH_DECLARED_SCOPE**

对冻结的 `PR_FULL_TRANSFER.zip`、`PR_REVIEW_RETURN.zip` 和原始
`HANDOFF_MANIFEST.json` 未发现用户凭据、私钥、认证文件或带凭据的 Git
remote。所有规则命中均被裁决为公开上游源码/测试/文档示例、候选与基线代码中的
标识符误报，或已脱敏的扫描报告本身。**BLOCKING secret: 0**。

此结论允许发布上述冻结附件。本轮新生成的 publication addendum、receiver
scripts、bootstrap、transfer manifest 和 supplement ZIP 必须在最终冻结后再执行一次
脱敏扫描；它们不属于本次已扫描的冻结输入。

## 固定载荷身份

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PR_FULL_TRANSFER.zip` | 696228223 | `675237faf78efcd4f95642494437af2b09c29680f21eb8e9e460cad7ab6a953e` |
| `PR_REVIEW_RETURN.zip` | 1771620 | `71df7981a67a6643cf476e56d2d1e1a2795e431cb1ac271fed24a8e51391b470` |
| `HANDOFF_MANIFEST.json` | 2680 | `4606f83f060e3162296fc3b8207439420034d096980de0a9f0e31e24897720bc` |

## 实际扫描范围

1. 使用 `gitleaks 8.30.1`（二进制 SHA256
   `ba52fb1bfabbcde42f032afad3d6e0b19dff8ed105229a16e7caa338bbc0e84f`）对完整 ZIP 直接执行
   archive-depth 3 的递归检查；工具报告扫描 835,014,594 bytes。报告使用
   100% secret redaction。
2. 独立解析外层及所有实际嵌套 ZIP：9 个唯一容器、14,863 个条目、
   1,165,419,461 字节声明展开量。深度/字节/时间上限均未命中；未发现加密条目、
   无法读取容器、不安全成员名或 Unicode/大小写冲突。
3. 按内容 hash 去重扫描 12,118 个唯一文本成员，共 211,643,113 bytes。自定义
   检查覆盖 PEM 私钥、Authorization header、带凭据 URL、AWS/GitHub token 形状；
   对非文本 bytes 也扫描这些明文签名。
4. 全部容器中共有 16 个 Git bundle 出现位置（外层 8、嵌套 ZIP 8），按 SHA256
   去重后仅有 3 个唯一 bundle。对这 3 个唯一 bundle 按记录的 shallow boundary 完成
   `bundle verify`/restore/`fsck`；另枚举 2 个内嵌 `.git` 对象库。对所有实际本地
   Git blob 枚举，获得 11,370 个去重文本 blob，共 152,323,494 bytes，并独立
   运行 gitleaks。
5. 两个实际 `.git/config` 均仅指向无 userinfo 的 `github.com` HTTPS remote；无
   credential helper/extraHeader/username 等敏感配置。

## 命中裁决（不包含匹配原文）

- 完整 ZIP：101 条（100 `generic-api-key`、1 `curl-auth-header`）。其中 91 条是旧的
  已人工复核集合，4 条是新生成的 candidate/base 源码快照重复，6 条是嵌套历史
  ZIP 重复。
- 审阅 ZIP：4 条 `generic-api-key`，均为 candidate/base speculator 源码标识符误报。
- Git 对象文本：77 条（76 `generic-api-key`、1 `curl-auth-header`），全部映射到已审
  公开上游 source/test/CI/docs 路径；未出现仅历史对象中存在的新类型敏感内容。
- 自定义文本签名命中 3 处：公开文档 Authorization 示例、已脱敏扫描报告中的
  Authorization 模式、使用保留域 `example.com` 的公开上游测试 URL。
- PEM 私钥、AWS access-key 形状、GitHub token 形状、非文本明文签名：均 0。
- 文件名审查唯一敏感样式为公开上游 Helm `secrets.yaml` 模板，不是认证文件。

## 边界

- 124 PNG、6 JPEG、2 MP4 和 1 ICO 未做语义/隐写分析；对其 bytes 的常见明文
  凭据签名扫描无命中。
- 10 个 PYC 和非文本/数值 Git blob 未反编译或语义解释；对常见明文凭据签名的
  byte 扫描无命中，可得的对应源文本已另行扫描。
- 内嵌 vLLM partial clone 声明的缺失 promisor objects 并不存在于公开包 bytes 中；
  包内自包含 bundle 的 7,233 个实际本地 blob 已枚举。
- 模式扫描不能证明任意未知编码中绝对没有秘密；本结论仅适用于上述实际范围。

## 发布代理最终动作

1. 对最终 Git transfer 白名单目录和 `PR_TRANSFER_SUPPLEMENT.zip` 使用同一 gitleaks 二进制、
   `--redact=100 --max-archive-depth 3`。
2. 只保留脱敏统计和路径；不将任何未脱敏 match/secret 字段放入 Git 或 Release。
3. 新扫描若出现无法裁决的凭据形状，阻止受影响附件的发布；不覆盖或改写原冻结包。
