#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRV2 完整中文迁移包 —— 下载、校验、安全解压。

固定来源（不使用 latest Release）：
  repo: LucianWQZ/private-file-relay
  tag : 见 RELAY_TRANSFER_MANIFEST.json -> release.tag

流程：
  1. 读取清单，确认分片顺序、字节数与整包 SHA256
  2. 预检：gh 可用、已登录、目标目录、磁盘余量、现存文件
  3. 逐片下载（已存在且 SHA256 相符的分片直接复用）
  4. 逐片校验 SHA256；再按清单顺序流式串联校验整包 SHA256
  5. 空间复核（分片 + 解压后大小）
  6. 安全解压（拒绝绝对路径、越界路径、符号链接、设备文件）
  7. 校验 SHA256SUMS、必要索引与 JSON
  8. 输出 RECEIVE_RECEIPT.json

退出码：0 成功；2 预检失败；3 下载失败；4 校验失败；5 解压失败；6 后校验失败
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath

CHUNK = 8 * 1024 * 1024
REQUIRED_TOP = [
    "00_先读这里.md",
    "01_当前进展与下一步.md",
    "02_任务时间线.md",
    "03_完整文档目录.md",
    "04_迁移范围与完整性报告.md",
    "05_服务器接管说明.md",
    "TASK_INDEX.json",
    "PATH_MAP.json",
    "DOCUMENT_CATALOG.jsonl",
    "TRANSFER_MANIFEST.json",
    "SHA256SUMS",
    "VERIFY_TRANSFER.py",
]


def log(msg, fp=None):
    line = time.strftime("[%H:%M:%S] ") + str(msg)
    print(line, flush=True)
    if fp:
        fp.write(line + "\n")
        fp.flush()


def die(code, msg):
    print("ERROR: " + msg, file=sys.stderr, flush=True)
    sys.exit(code)


def human(n):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024.0:
            return "%.2f %s" % (n, unit)
        n /= 1024.0
    return "%.2f PiB" % n


def sha256_file(path, fp=None):
    h = hashlib.sha256()
    done = 0
    total = os.path.getsize(path)
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
            done += len(b)
            if fp and total and done % (256 * CHUNK) == 0:
                fp.write("    hash %s: %.1f%%\r" % (os.path.basename(path), 100.0 * done / total))
                fp.flush()
    return h.hexdigest()


class ConcatReader:
    """把按序分片伪装成一个可 seek 的只读文件，供 zipfile 使用（不产生第二份 30GB 副本）。"""

    def __init__(self, paths):
        self.paths = paths
        self.sizes = [os.path.getsize(p) for p in paths]
        self.offsets = []
        acc = 0
        for s in self.sizes:
            self.offsets.append(acc)
            acc += s
        self.total = acc
        self.pos = 0
        self._fh = None
        self._idx = -1

    def _open(self, idx):
        if self._fh:
            self._fh.close()
        self._fh = open(self.paths[idx], "rb")
        self._idx = idx

    def seek(self, off, whence=0):
        if whence == 0:
            self.pos = off
        elif whence == 1:
            self.pos += off
        elif whence == 2:
            self.pos = self.total + off
        return self.pos

    def tell(self):
        return self.pos

    def seekable(self):
        return True

    def readable(self):
        return True

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.total - self.pos
        out = bytearray()
        while n > 0 and self.pos < self.total:
            idx = 0
            for i, off in enumerate(self.offsets):
                if self.pos >= off:
                    idx = i
                else:
                    break
            if idx != self._idx:
                self._open(idx)
            local = self.pos - self.offsets[idx]
            remain = self.sizes[idx] - local
            take = min(n, remain)
            self._fh.seek(local)
            b = self._fh.read(take)
            if not b:
                break
            out += b
            self.pos += len(b)
            n -= len(b)
        return bytes(out)

    def close(self):
        if self._fh:
            self._fh.close()
            self._fh = None


def gh(cmd, capture=True):
    r = subprocess.run(cmd, capture_output=capture, text=True)
    return r


def check_gh(manifest, fp):
    if not shutil.which("gh"):
        die(2, "未找到 gh CLI；服务器需先安装并 gh auth login")
    r = gh(["gh", "auth", "status"])
    if r.returncode != 0:
        die(2, "gh 未登录或无授权：\n" + (r.stdout or "") + (r.stderr or ""))
    log("gh 已登录", fp)
    r = gh(["gh", "repo", "view", manifest["release"]["repo"], "--json", "nameWithOwner,visibility"])
    if r.returncode != 0:
        die(2, "无法读取仓库（私仓需 gh 授权）：" + (r.stderr or ""))
    log("仓库: " + r.stdout.strip(), fp)


def load_manifest(path):
    with open(path, "r", encoding="utf-8") as f:
        m = json.load(f)
    for k in ("task_id", "archive", "parts", "release"):
        if k not in m:
            die(2, "清单缺少字段: " + k)
    idx = [p["index"] for p in m["parts"]]
    if idx != list(range(len(m["parts"]))):
        die(2, "清单分片序号不连续：%r" % idx[:5])
    tot = sum(p["bytes"] for p in m["parts"])
    if tot != m["archive"]["bytes"]:
        die(2, "分片字节合计 %d != 整包 %d" % (tot, m["archive"]["bytes"]))
    return m


def ensure_space(need_bytes, where, fp, what):
    free = shutil.disk_usage(where).free
    log("%s 需要 %s，%s 可用 %s" % (what, human(need_bytes), where, human(free)), fp)
    if free < need_bytes:
        die(2, "磁盘空间不足：%s 需要 %s，仅剩 %s" % (what, human(need_bytes), human(free)))
    return free


def download_parts(m, work, fp):
    repo = m["release"]["repo"]
    tag = m["release"]["tag"]
    os.makedirs(work, exist_ok=True)
    paths = []
    for p in m["parts"]:
        dst = os.path.join(work, p["name"])
        paths.append(dst)
        ok = os.path.isfile(dst) and os.path.getsize(dst) == p["bytes"]
        if ok:
            log("复用已存在分片 %s (%s)" % (p["name"], human(p["bytes"])), fp)
            continue
        if os.path.isfile(dst) and os.path.getsize(dst) != p["bytes"]:
            log("大小不符，重下 %s" % p["name"], fp)
            os.remove(dst)
        log("下载 %s (%s)" % (p["name"], human(p["bytes"])), fp)
        r = gh(["gh", "release", "download", tag,
                "--repo", repo,
                "--pattern", p["name"],
                "--dir", work,
                "--clobber"])
        if r.returncode != 0:
            die(3, "下载失败 %s：%s" % (p["name"], r.stderr.strip()))
        if not os.path.isfile(dst) or os.path.getsize(dst) != p["bytes"]:
            die(3, "下载后大小不符 %s" % p["name"])
    return paths


def verify_parts(m, paths, fp):
    whole = hashlib.sha256()
    for p, path in zip(m["parts"], paths):
        h = sha256_file(path, fp)
        if h != p["sha256"]:
            die(4, "分片校验失败 %s\n  expect %s\n  actual %s" % (p["name"], p["sha256"], h))
        with open(path, "rb") as f:
            while True:
                b = f.read(CHUNK)
                if not b:
                    break
                whole.update(b)
        log("分片 OK %s %s" % (p["name"], h[:16] + "..."), fp)
    got = whole.hexdigest()
    if got != m["archive"]["sha256"]:
        die(4, "整包串联校验失败\n  expect %s\n  actual %s" % (m["archive"]["sha256"], got))
    log("整包串联 SHA256 OK: " + got, fp)
    return got


def safe_members(zf):
    out = []
    for i in zf.infolist():
        name = i.filename
        p = PurePosixPath(name)
        if name.startswith("/") or p.is_absolute() or ".." in p.parts:
            die(5, "危险成员路径：%r" % name)
        if "\\" in name:
            die(5, "含反斜杠路径（Windows 绝对路径风险）：%r" % name)
        mode = (i.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            die(5, "拒绝符号链接成员：%r" % name)
        if mode not in (0, 0o040000, 0o100000):
            die(5, "拒绝特殊文件成员：%r mode=%o" % (name, mode))
        out.append(i)
    return out


def extract(reader, target, fp):
    os.makedirs(target, exist_ok=True)
    with zipfile.ZipFile(reader) as zf:
        bad = zf.testzip()
        if bad:
            die(5, "CRC 校验失败：" + bad)
        members = safe_members(zf)
        n = 0
        for i in members:
            if i.is_dir():
                os.makedirs(os.path.join(target, i.filename), exist_ok=True)
                continue
            dst = os.path.join(target, i.filename)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with zf.open(i) as src, open(dst, "wb") as out:
                shutil.copyfileobj(src, out, CHUNK)
            try:
                os.chmod(dst, (i.external_attr >> 16) & 0o777 or 0o644)
            except OSError:
                pass
            n += 1
            if n % 500 == 0:
                log("解压 %d/%d" % (n, len(members)), fp)
    log("解压完成，文件 %d 个 -> %s" % (n, target), fp)
    return n


def post_verify(target, m, fp, full_sha=True):
    problems = []
    for name in REQUIRED_TOP:
        if not os.path.isfile(os.path.join(target, name)):
            problems.append("缺少 " + name)
    for name in ("TASK_INDEX.json", "TRANSFER_MANIFEST.json"):
        p = os.path.join(target, name)
        if os.path.isfile(p):
            try:
                json.load(open(p, encoding="utf-8"))
            except Exception as e:
                problems.append("%s 解析失败: %s" % (name, e))
    ti = os.path.join(target, "TASK_INDEX.json")
    tasks = 0
    if os.path.isfile(ti):
        tasks = len(json.load(open(ti, encoding="utf-8")).get("tasks", []))
        if tasks != 35:
            problems.append("TASK_INDEX 任务数 %d != 35" % tasks)
    n_files = sum(len(fs) for _, _, fs in os.walk(target))
    log("解压后文件数：%d；任务数：%d" % (n_files, tasks), fp)
    if full_sha:
        sums = os.path.join(target, "SHA256SUMS")
        bad = 0
        total = 0
        with open(sums, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                digest, rel = line.split("  ", 1)
                p = os.path.join(target, rel)
                total += 1
                if not os.path.isfile(p) or sha256_file(p) != digest:
                    bad += 1
                    if bad <= 5:
                        problems.append("SHA256SUMS 不符: " + rel)
        log("SHA256SUMS 校验：%d 条，失败 %d" % (total, bad), fp)
    return problems, n_files, tasks


def main():
    ap = argparse.ArgumentParser(
        description="MRV2 完整中文迁移包：下载 → 校验 → 安全解压 → 后校验",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例：
  python3 下载并恢复资料.py --dry-run
  python3 下载并恢复资料.py
  python3 下载并恢复资料.py --root /data/adaption --keep-parts
""")
    ap.add_argument("--root", default="/mnt/share/z00937950/project/speculate_sliding_window_mrv2/reference/adaption",
                    help="恢复根目录（包会解压到 <root>/<task_dir>）")
    ap.add_argument("--manifest", default=str(Path(__file__).with_name("RELAY_TRANSFER_MANIFEST.json")),
                    help="传输清单路径")
    ap.add_argument("--work-dir", default=None,
                    help="分片存放目录（默认 <root>/.mrv2_transfer_work/<task_id>）")
    ap.add_argument("--keep-parts", action="store_true", help="保留分片（默认保留，显式删除用 --clean-parts）")
    ap.add_argument("--clean-parts", action="store_true", help="成功后删除分片（默认不删）")
    ap.add_argument("--skip-full-sha", action="store_true", help="跳过 SHA256SUMS 全量复核（不建议）")
    ap.add_argument("--dry-run", action="store_true", help="只做预检与空间计算，不下载")
    ap.add_argument("--yes", action="store_true", help="跳过交互确认")
    a = ap.parse_args()

    m = load_manifest(a.manifest)
    task_dir = m["task_id"]
    target = os.path.join(a.root, task_dir)
    work = a.work_dir or os.path.join(a.root, ".mrv2_transfer_work", task_dir)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    logf = open(os.path.join(os.path.dirname(os.path.abspath(a.manifest)),
                             "RECEIVE_RUN.log"), "a", encoding="utf-8")
    fp = logf

    log("== MRV2 恢复开始 ==", fp)
    log("task=%s tag=%s repo=%s" % (task_dir, m["release"]["tag"], m["release"]["repo"]), fp)
    log("整包 %s bytes=%d" % (m["archive"]["filename"], m["archive"]["bytes"]), fp)
    check_gh(m, fp)

    if os.path.exists(target):
        if os.path.isfile(os.path.join(target, "SHA256SUMS")):
            die(2, "目标目录已存在且看起来已完成：%s（拒绝覆盖，请人工确认）" % target)
        die(2, "目标目录已存在：%s（拒绝覆盖既有目录）" % target)

    need = sum(p["bytes"] for p in m["parts"])
    ensure_space(need, a.root, fp, "分片下载")
    if a.dry_run:
        log("dry-run：预检通过，未下载。所需分片空间 %s" % human(need), fp)
        return 0

    if not a.yes:
        print("即将下载 %s 到 %s，解压到 %s" % (human(need), work, target))
        if input("继续？[y/N] ").strip().lower() not in ("y", "yes"):
            die(2, "用户取消")

    paths = download_parts(m, work, fp)
    whole = verify_parts(m, paths, fp)

    reader = ConcatReader(paths)
    try:
        zf0 = zipfile.ZipFile(reader)
    except zipfile.BadZipFile as e:
        die(5, "分片串联后不是有效 ZIP（停止，保留分片）：%s" % e)
    with zf0 as zf:
        extracted = sum(i.file_size for i in zf.infolist())
    log("解压后预计 %s" % human(extracted), fp)
    ensure_space(extracted + 64 * 1024 * 1024, a.root, fp, "解压")

    n_dir = extract(reader, target, fp)
    problems, n_files, tasks = post_verify(target, m, fp, full_sha=not a.skip_full_sha)
    if problems:
        for p in problems:
            log("后校验问题: " + p, fp)
        die(6, "后校验失败 %d 项" % len(problems))

    receipt = {
        "schema_version": 1,
        "status": "RECEIVED_AND_VERIFIED",
        "task_id": task_dir,
        "repo": m["release"]["repo"],
        "tag": m["release"]["tag"],
        "release_url": m["release"]["url"],
        "archive_sha256": whole,
        "archive_bytes": m["archive"]["bytes"],
        "parts_verified": len(paths),
        "extracted_dir": target,
        "extracted_files": n_files,
        "task_index_tasks": tasks,
        "sha256sums_checked": not a.skip_full_sha,
        "log": str(os.path.abspath(logf.name)),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "notes_zh": "本 receipt 只证明本机下载与解压校验通过，不代表 NPU 验收。",
    }
    out = os.path.join(target, "RECEIVE_RECEIPT.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
    log("receipt: " + out, fp)

    if a.clean_parts:
        log("按 --clean-parts 删除分片目录：%s" % work, fp)
        shutil.rmtree(work, ignore_errors=True)
    log("== 完成 ==", fp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
