#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRV2 完整中文迁移包 —— 已恢复目录的独立校验。

用于：
  - 恢复完成后的复核；
  - 服务器迁移、拷贝、挂载之后的完整性抽查；
  - 交付前确认目录未被改动。

校验内容：
  1. 必要顶层文件齐全（00–05、索引、清单、SHA256SUMS）
  2. JSON/JSONL 可解析
  3. TASK_INDEX.json 任务数 = 35
  4. 文件总数与清单登记一致（若清单提供 members）
  5. SHA256SUMS 逐条复核（可 --skip-sha 跳过）
"""

import argparse
import hashlib
import json
import os
import sys
import time

CHUNK = 8 * 1024 * 1024
REQUIRED = [
    "00_先读这里.md", "01_当前进展与下一步.md", "02_任务时间线.md",
    "03_完整文档目录.md", "04_迁移范围与完整性报告.md", "05_服务器接管说明.md",
    "TASK_INDEX.json", "PATH_MAP.json", "DOCUMENT_CATALOG.jsonl",
    "TRANSFER_MANIFEST.json", "SHA256SUMS", "VERIFY_TRANSFER.py",
]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(
        description="校验已恢复的 MRV2 完整中文迁移目录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n  python3 验证接收资料.py --dir <解压目录>\n  python3 验证接收资料.py --dir <解压目录> --skip-sha\n")
    ap.add_argument("--dir", default="/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/adaption/MRV2_完整中文迁移_20261022_034933_0800",
                    help="待校验的解压目录")
    ap.add_argument("--manifest", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      "RELAY_TRANSFER_MANIFEST.json"),
                    help="传输清单（用于核对文件总数）")
    ap.add_argument("--skip-sha", action="store_true", help="跳过 SHA256SUMS 全量复核（只查结构）")
    ap.add_argument("--json-out", default=None, help="把结果另存为 JSON")
    a = ap.parse_args()

    problems = []
    info = {"dir": a.dir, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

    if not os.path.isdir(a.dir):
        print(json.dumps({"status": "FAIL", "errors": ["目录不存在: " + a.dir]}, ensure_ascii=False, indent=2))
        return 2

    for name in REQUIRED:
        if not os.path.isfile(os.path.join(a.dir, name)):
            problems.append("缺少 " + name)

    tasks = 0
    ti = os.path.join(a.dir, "TASK_INDEX.json")
    if os.path.isfile(ti):
        try:
            tasks = len(json.load(open(ti, encoding="utf-8")).get("tasks", []))
        except Exception as e:
            problems.append("TASK_INDEX.json 解析失败: %s" % e)
    if tasks != 35:
        problems.append("TASK_INDEX 任务数 %d != 35" % tasks)
    info["tasks"] = tasks

    for name in ("PATH_MAP.json", "TRANSFER_MANIFEST.json", "PACKAGE_VERIFICATION.json"):
        p = os.path.join(a.dir, name)
        if os.path.isfile(p):
            try:
                json.load(open(p, encoding="utf-8"))
            except Exception as e:
                problems.append("%s 解析失败: %s" % (name, e))

    n = sum(len(fs) for _, _, fs in os.walk(a.dir))
    info["files"] = n
    if os.path.isfile(a.manifest):
        try:
            m = json.load(open(a.manifest, encoding="utf-8"))
            exp = m.get("archive", {}).get("members")
            if exp and n != exp:
                problems.append("文件数 %d != 清单登记 %d" % (n, exp))
        except Exception as e:
            problems.append("清单解析失败: %s" % e)

    if not a.skip_sha:
        sums = os.path.join(a.dir, "SHA256SUMS")
        bad = []
        total = 0
        if os.path.isfile(sums):
            with open(sums, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if not line:
                        continue
                    digest, rel = line.split("  ", 1)
                    total += 1
                    p = os.path.join(a.dir, rel)
                    if not os.path.isfile(p) or sha256_file(p) != digest:
                        bad.append(rel)
        info["sha256sums_entries"] = total
        info["sha256sums_failed"] = len(bad)
        if bad:
            problems.append("SHA256SUMS 不符 %d 项，例如：%s" % (len(bad), bad[:3]))

    result = {"status": "PASS" if not problems else "FAIL", "errors": problems, **info}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
