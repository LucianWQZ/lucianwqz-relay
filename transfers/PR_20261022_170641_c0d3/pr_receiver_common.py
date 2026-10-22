#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared, standard-library-only helpers for the PR relay receiver.

The module treats archives as untrusted data.  It never imports or executes a
file from an archive and it creates symlinks only after every ordinary payload
file has been written and verified.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import stat
import subprocess
import tempfile
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


CHUNK = 4 * 1024 * 1024
MANIFEST_MEMBER = "FILES_MANIFEST.json"


class ReceiverError(RuntimeError):
    """A deterministic validation or receive error."""


def now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def json_read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exact parser message varies
        raise ReceiverError(f"无法解析 JSON：{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReceiverError(f"JSON 顶层必须是对象：{path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with tmp.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_stream(handle) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    for chunk in iter(lambda: handle.read(CHUNK), b""):
        size += len(chunk)
        digest.update(chunk)
    return size, digest.hexdigest()


def parse_mode(value: Any) -> int:
    if isinstance(value, int):
        mode = value
    elif isinstance(value, str):
        try:
            mode = int(value, 8)
        except ValueError as exc:
            raise ReceiverError(f"非法 mode：{value!r}") from exc
    else:
        raise ReceiverError(f"非法 mode 类型：{value!r}")
    mode = stat.S_IMODE(mode)
    if mode & 0o7000:
        raise ReceiverError(f"拒绝 setuid/setgid/sticky mode：{value!r}")
    return mode


def safe_relative(value: str, *, label: str) -> PurePosixPath:
    if not value or "\x00" in value or "\\" in value:
        raise ReceiverError(f"{label} 含空值、NUL 或反斜线：{value!r}")
    raw_parts = value.split("/")
    if any(part in ("", ".", "..") for part in raw_parts):
        raise ReceiverError(f"{label} 含空、点或上级路径段：{value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("/"):
        raise ReceiverError(f"{label} 是绝对路径：{value!r}")
    if any(part in ("", ".", "..") for part in path.parts):
        raise ReceiverError(f"{label} 含非规范路径段：{value!r}")
    return path


def normalized_collision_key(path: PurePosixPath) -> str:
    return "/".join(unicodedata.normalize("NFC", part).casefold() for part in path.parts)


def resolve_link_lexically(link_path: PurePosixPath, target: str) -> PurePosixPath:
    if not target or "\x00" in target or "\\" in target:
        raise ReceiverError(f"符号链接目标非法：{link_path} -> {target!r}")
    raw = PurePosixPath(target)
    if raw.is_absolute() or target.startswith("/"):
        raise ReceiverError(f"符号链接目标是绝对路径：{link_path} -> {target}")
    parts = list(link_path.parent.parts)
    for part in raw.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise ReceiverError(f"符号链接越出恢复根：{link_path} -> {target}")
            parts.pop()
        else:
            parts.append(part)
    if not parts:
        raise ReceiverError(f"符号链接目标解析为恢复根：{link_path} -> {target}")
    return PurePosixPath(*parts)


def _zip_type(info: zipfile.ZipInfo) -> str:
    mode = (info.external_attr >> 16) & 0xFFFF
    if info.is_dir():
        return "directory"
    if stat.S_ISLNK(mode):
        return "symlink"
    if mode and not stat.S_ISREG(mode):
        raise ReceiverError(f"ZIP 含特殊文件类型：{info.filename}")
    return "file"


def _validate_paths(paths: Iterable[PurePosixPath]) -> None:
    paths = list(paths)
    exact = set()
    folded: dict[str, str] = {}
    for path in paths:
        value = path.as_posix()
        if value in exact:
            raise ReceiverError(f"ZIP 重复路径：{value}")
        exact.add(value)
        key = normalized_collision_key(path)
        previous = folded.get(key)
        if previous is not None and previous != value:
            raise ReceiverError(f"ZIP 含大小写或 Unicode 归一化冲突：{previous!r} / {value!r}")
        folded[key] = value
    for value in exact:
        parts = PurePosixPath(value).parts
        for index in range(1, len(parts)):
            ancestor = PurePosixPath(*parts[:index]).as_posix()
            if ancestor in exact:
                raise ReceiverError(f"ZIP 文件路径同时是另一成员的父目录：{ancestor}")


def inspect_payload_zip(
    archive: Path,
    *,
    expected_internal_manifest_sha256: str | None = None,
    expected_entries: int | None = None,
    expected_payload_bytes: int | None = None,
) -> dict[str, Any]:
    """Validate structure and internal manifest without extracting."""
    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        names = [info.filename for info in infos]
        if MANIFEST_MEMBER not in names:
            raise ReceiverError(f"ZIP 缺少 {MANIFEST_MEMBER}：{archive}")
        paths = [safe_relative(name, label="ZIP member") for name in names]
        _validate_paths(paths)
        manifest_raw = zf.read(MANIFEST_MEMBER)
        internal_sha = hashlib.sha256(manifest_raw).hexdigest()
        if expected_internal_manifest_sha256 and internal_sha != expected_internal_manifest_sha256:
            raise ReceiverError("内部 FILES_MANIFEST.json SHA256 不匹配")
        try:
            manifest = json.loads(manifest_raw)
            rows = manifest["files"]
        except Exception as exc:
            raise ReceiverError(f"内部 manifest schema 非法：{exc}") from exc
        if not isinstance(rows, list):
            raise ReceiverError("内部 manifest files 必须是数组")
        records: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                raise ReceiverError("内部 manifest 文件记录非法")
            rel = safe_relative(row["path"], label="manifest path").as_posix()
            if rel == MANIFEST_MEMBER or rel in records:
                raise ReceiverError(f"内部 manifest 路径重复或自引用：{rel}")
            kind = row.get("type")
            if kind not in {"file", "symlink"}:
                raise ReceiverError(f"内部 manifest type 非法：{rel}: {kind!r}")
            if not isinstance(row.get("size"), int) or row["size"] < 0:
                raise ReceiverError(f"内部 manifest size 非法：{rel}")
            digest = row.get("sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                raise ReceiverError(f"内部 manifest SHA256 非法：{rel}")
            parse_mode(row.get("mode"))
            if kind == "symlink":
                target = row.get("target")
                if not isinstance(target, str):
                    raise ReceiverError(f"符号链接缺少 target：{rel}")
                resolve_link_lexically(PurePosixPath(rel), target)
            records[rel] = row

        payload_infos = {info.filename: info for info in infos if info.filename != MANIFEST_MEMBER}
        if set(payload_infos) != set(records):
            missing = sorted(set(records) - set(payload_infos))[:3]
            extra = sorted(set(payload_infos) - set(records))[:3]
            raise ReceiverError(f"ZIP 与内部 manifest 成员不一致；missing={missing}, extra={extra}")
        for rel, row in records.items():
            info = payload_infos[rel]
            actual_type = _zip_type(info)
            if actual_type != row["type"]:
                raise ReceiverError(f"ZIP 类型与 manifest 不符：{rel}")
            if info.file_size != row["size"]:
                raise ReceiverError(f"ZIP 声明大小与 manifest 不符：{rel}")
            zip_mode = stat.S_IMODE((info.external_attr >> 16) & 0xFFFF)
            if actual_type == "file" and zip_mode and zip_mode != parse_mode(row["mode"]):
                raise ReceiverError(f"ZIP mode 与 manifest 不符：{rel}")

        payload_bytes = sum(row["size"] for row in records.values())
        if expected_entries is not None and len(records) != expected_entries:
            raise ReceiverError(f"payload 数量不符：{len(records)} != {expected_entries}")
        if expected_payload_bytes is not None and payload_bytes != expected_payload_bytes:
            raise ReceiverError(f"payload 总字节不符：{payload_bytes} != {expected_payload_bytes}")
        summary = manifest.get("summary", {})
        if summary:
            if summary.get("payload_entries") != len(records) or summary.get("payload_bytes") != payload_bytes:
                raise ReceiverError("内部 manifest summary 与 files 不一致")
        return {
            "archive": str(archive),
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": sha256_file(archive),
            "internal_manifest_sha256": internal_sha,
            "payload_entries": len(records),
            "payload_bytes": payload_bytes,
            "regular_files": sum(row["type"] == "file" for row in records.values()),
            "symlinks": sum(row["type"] == "symlink" for row in records.values()),
            "records": records,
            "crc_checked": False,
            "payload_hashes_checked": False,
        }


def verify_archive_payload_hashes(archive: Path, plan: dict[str, Any]) -> dict[str, Any]:
    records = plan["records"]
    with zipfile.ZipFile(archive) as zf:
        bad = zf.testzip()
        if bad:
            raise ReceiverError(f"ZIP CRC 失败：{bad}")
        for rel, row in records.items():
            with zf.open(rel, "r") as handle:
                size, digest = sha256_stream(handle)
            if size != row["size"] or digest != row["sha256"]:
                raise ReceiverError(f"ZIP payload hash/size 不符：{rel}")
    plan = dict(plan)
    plan.pop("records", None)
    plan["crc_checked"] = True
    plan["payload_hashes_checked"] = True
    return plan


def _directory_entries(root: Path) -> dict[str, tuple[str, Path]]:
    found: dict[str, tuple[str, Path]] = {}

    def visit(base: Path, relative: PurePosixPath | None = None) -> None:
        for child in sorted(base.iterdir(), key=lambda item: item.name):
            rel = PurePosixPath(child.name) if relative is None else relative / child.name
            st = child.lstat()
            if stat.S_ISLNK(st.st_mode):
                found[rel.as_posix()] = ("symlink", child)
            elif stat.S_ISREG(st.st_mode):
                found[rel.as_posix()] = ("file", child)
            elif stat.S_ISDIR(st.st_mode):
                visit(child, rel)
            else:
                found[rel.as_posix()] = ("special", child)

    visit(root)
    return found


def verify_directory(root: Path, records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not root.is_dir() or root.is_symlink():
        raise ReceiverError(f"恢复目标不是普通目录：{root}")
    actual = _directory_entries(root)
    if set(actual) != set(records):
        missing = sorted(set(records) - set(actual))[:5]
        extra = sorted(set(actual) - set(records))[:5]
        raise ReceiverError(f"恢复目录成员不符；missing={missing}, extra={extra}")
    for rel, row in records.items():
        kind, path = actual[rel]
        if kind != row["type"]:
            raise ReceiverError(f"恢复类型不符：{rel}: {kind} != {row['type']}")
        st = path.lstat()
        # POSIX symlink permission bits are not portable and Linux creates
        # them as 0777 regardless of ZIP metadata.  Their declared mode is
        # checked against the ZIP entry above; regular-file modes are restored
        # and checked on disk.
        if kind == "file" and stat.S_IMODE(st.st_mode) != parse_mode(row["mode"]):
            raise ReceiverError(f"恢复 mode 不符：{rel}")
        if kind == "file":
            if st.st_size != row["size"] or sha256_file(path) != row["sha256"]:
                raise ReceiverError(f"恢复文件 hash/size 不符：{rel}")
        else:
            target = os.readlink(path)
            data = target.encode("utf-8")
            if target != row["target"] or len(data) != row["size"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ReceiverError(f"恢复符号链接目标不符：{rel}")
            resolved = resolve_link_lexically(PurePosixPath(rel), target)
            if not (root / resolved.as_posix()).exists():
                raise ReceiverError(f"恢复符号链接目标不存在：{rel} -> {target}")
    return {
        "status": "PASS",
        "root": str(root),
        "payload_entries": len(records),
        "regular_files": sum(row["type"] == "file" for row in records.values()),
        "symlinks": sum(row["type"] == "symlink" for row in records.values()),
        "payload_bytes": sum(row["size"] for row in records.values()),
    }


def extract_atomically(archive: Path, destination: Path, plan: dict[str, Any]) -> dict[str, Any]:
    records = plan["records"]
    if destination.exists() or destination.is_symlink():
        result = verify_directory(destination, records)
        result["action"] = "REUSED_EXISTING_VERIFIED_DESTINATION"
        return result
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = destination.parent / f".{destination.name}.receiving"
    if stage.exists() or stage.is_symlink():
        raise ReceiverError(f"发现未完成 staging；请先审阅，不自动删除：{stage}")
    stage.mkdir(mode=0o700)
    try:
        with zipfile.ZipFile(archive) as zf:
            # Ordinary files first.  No archive symlink exists yet, so parent
            # directory creation cannot follow one out of the staging root.
            for rel, row in records.items():
                if row["type"] != "file":
                    continue
                dest = stage.joinpath(*PurePosixPath(rel).parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                size = 0
                with zf.open(rel, "r") as source, dest.open("xb") as output:
                    for chunk in iter(lambda: source.read(CHUNK), b""):
                        output.write(chunk)
                        size += len(chunk)
                        digest.update(chunk)
                    output.flush()
                    os.fsync(output.fileno())
                if size != row["size"] or digest.hexdigest() != row["sha256"]:
                    raise ReceiverError(f"解压时 hash/size 不符：{rel}")
                os.chmod(dest, parse_mode(row["mode"]))
            for rel, row in records.items():
                if row["type"] != "symlink":
                    continue
                link_rel = PurePosixPath(rel)
                resolved = resolve_link_lexically(link_rel, row["target"])
                target_on_disk = stage.joinpath(*resolved.parts)
                if not target_on_disk.exists():
                    raise ReceiverError(f"符号链接目标在 payload 中不存在：{rel} -> {row['target']}")
                dest = stage.joinpath(*link_rel.parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(row["target"], dest)
        checked = verify_directory(stage, records)
        os.replace(stage, destination)
        checked["root"] = str(destination)
        checked["action"] = "EXTRACTED_AND_ATOMICALLY_PLACED"
        return checked
    except Exception:
        # Keep staging intact as failure evidence; never merge or delete it.
        raise


def relay_identity(manifest: dict[str, Any]) -> tuple[str, str]:
    relay = manifest.get("relay")
    if not isinstance(relay, dict):
        raise ReceiverError("传输清单缺少 relay")
    repo = relay.get("repository") or relay.get("repo")
    tag = relay.get("tag")
    if not isinstance(repo, str) or not repo or not isinstance(tag, str) or not tag:
        raise ReceiverError("传输清单 relay.repository/tag 非法")
    return repo, tag


def asset_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    value = manifest.get("release_assets", manifest.get("assets"))
    if isinstance(value, dict):
        rows = []
        for role, row in value.items():
            if not isinstance(row, dict):
                raise ReceiverError("assets 映射值必须是对象")
            rows.append({"role": role, **row})
    elif isinstance(value, list):
        rows = value
    else:
        raise ReceiverError("传输清单缺少 release_assets/assets")
    seen = set()
    checked = []
    for raw in rows:
        if not isinstance(raw, dict):
            raise ReceiverError("asset 记录必须是对象")
        row = dict(raw)
        name = row.get("name") or row.get("filename")
        if not isinstance(name, str) or Path(name).name != name or name in seen:
            raise ReceiverError(f"asset 名非法或重复：{name!r}")
        seen.add(name)
        row["name"] = name
        if not isinstance(row.get("bytes"), int) or row["bytes"] < 0:
            raise ReceiverError(f"asset bytes 非法：{name}")
        if not isinstance(row.get("sha256"), str) or len(row["sha256"]) != 64:
            raise ReceiverError(f"asset SHA256 非法：{name}")
        checked.append(row)
    return checked


def row_for_role(rows: list[dict[str, Any]], *roles: str) -> dict[str, Any]:
    wanted = {role.casefold() for role in roles}
    matched = [row for row in rows if str(row.get("role", "")).casefold() in wanted]
    if len(matched) != 1:
        raise ReceiverError(f"角色 {sorted(wanted)} 必须恰好匹配一个 asset，实际 {len(matched)}")
    return matched[0]


def target_layout(manifest: dict[str, Any], root: Path) -> dict[str, Path]:
    target = manifest.get("target")
    if not isinstance(target, dict):
        raise ReceiverError("传输清单缺少 target")
    task = target.get("task_directory_name") or target.get("archive_directory_name") or manifest.get("task_id")
    if not isinstance(task, str):
        raise ReceiverError("target 缺少 task_directory_name")
    task_rel = safe_relative(task, label="task directory")
    if len(task_rel.parts) != 1:
        raise ReceiverError("task_directory_name 必须是单层目录名")
    cache_rel = safe_relative(target.get("cache_relative", f"发布附件缓存/{task}"), label="cache_relative")
    supplement_rel = safe_relative(target.get("supplement_relative", f"发布补充/{task}"), label="supplement_relative")
    receipt_rel = safe_relative(target.get("receipt_relative", f"接收回执/{task}"), label="receipt_relative")
    return {
        "root": root,
        "archive": root.joinpath(*task_rel.parts),
        "cache": root.joinpath(*cache_rel.parts),
        "supplement": root.joinpath(*supplement_rel.parts),
        "receipt": root.joinpath(*receipt_rel.parts),
    }


def nearest_existing(path: Path) -> Path:
    candidate = path
    while not candidate.exists():
        if candidate.parent == candidate:
            raise ReceiverError(f"找不到可检查空间的父目录：{path}")
        candidate = candidate.parent
    return candidate


def disk_plan(manifest: dict[str, Any], rows: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    target = manifest.get("target", {})
    asset_bytes = sum(row["bytes"] for row in rows)
    full = row_for_role(rows, "full", "full_archive", "pr_full_transfer")
    unpacked = full.get("payload_bytes", target.get("full_payload_bytes"))
    if not isinstance(unpacked, int) or unpacked < 0:
        raise ReceiverError("传输清单必须提供完整包 payload_bytes 或 target.full_payload_bytes")
    supplement = next((row for row in rows if str(row.get("role", "")).casefold() in {"supplement", "supplement_zip"}), None)
    supplement_unpacked = 0 if supplement is None else int(supplement.get("payload_bytes", 0))
    base = asset_bytes + unpacked + supplement_unpacked
    margin = target.get("space_margin_bytes", max(512 * 1024 * 1024, base // 10))
    if not isinstance(margin, int) or margin < 0:
        raise ReceiverError("target.space_margin_bytes 非法")
    computed = base + margin
    declared = target.get("peak_disk_bytes")
    if declared is not None and (not isinstance(declared, int) or declared < computed):
        raise ReceiverError(f"target.peak_disk_bytes 小于安全计算值：{declared} < {computed}")
    required = declared if declared is not None else computed
    usage = shutil.disk_usage(nearest_existing(root))
    return {
        "asset_bytes": asset_bytes,
        "full_payload_bytes": unpacked,
        "supplement_payload_bytes": supplement_unpacked,
        "space_margin_bytes": margin,
        "computed_peak_disk_bytes": computed,
        "declared_peak_disk_bytes": declared,
        "required_free_bytes": required,
        "observed_free_bytes": usage.free,
        "sufficient": usage.free >= required,
    }


def verify_outer_asset(path: Path, row: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ReceiverError(f"asset 不存在或不是普通文件：{path}")
    size = path.stat().st_size
    digest = sha256_file(path)
    if size != row["bytes"] or digest != row["sha256"]:
        raise ReceiverError(f"asset identity 不符：{row['name']}")
    return {"name": row["name"], "bytes": size, "sha256": digest, "status": "PASS"}


def download_assets(
    rows: list[dict[str, Any]],
    *,
    cache: Path,
    repo: str,
    tag: str,
    asset_source_dir: Path | None,
    state_path: Path,
) -> list[dict[str, Any]]:
    cache.mkdir(parents=True, exist_ok=True)
    completed = []
    for row in rows:
        final = cache / row["name"]
        if final.exists() or final.is_symlink():
            result = verify_outer_asset(final, row)
            result["action"] = "REUSED_EXISTING_VERIFIED_ASSET"
            completed.append(result)
            continue
        partial = cache / (row["name"] + ".partial")
        if partial.exists() or partial.is_symlink():
            try:
                verify_outer_asset(partial, {**row, "name": partial.name})
            except ReceiverError as exc:
                raise ReceiverError(f"发现身份不符的 partial，保留供审阅：{partial}: {exc}") from exc
            os.replace(partial, final)
            result = verify_outer_asset(final, row)
            result["action"] = "PROMOTED_VERIFIED_PARTIAL"
            completed.append(result)
            continue
        if asset_source_dir is not None:
            source = asset_source_dir / row["name"]
            if not source.is_file() or source.is_symlink():
                raise ReceiverError(f"离线 asset-source-dir 缺少普通文件：{source}")
            with source.open("rb") as src, partial.open("xb") as dst:
                shutil.copyfileobj(src, dst, CHUNK)
                dst.flush()
                os.fsync(dst.fileno())
        else:
            cmd = [
                "gh", "release", "download", tag,
                "--repo", repo,
                "--pattern", row["name"],
                "--output", str(partial),
            ]
            proc = subprocess.run(cmd, text=True, capture_output=True)
            if proc.returncode:
                raise ReceiverError(
                    f"gh 下载失败（partial 若存在则保留）：{row['name']}；"
                    f"exit={proc.returncode}；stderr={proc.stderr[-2000:]}"
                )
        verify_outer_asset(partial, {**row, "name": partial.name})
        os.replace(partial, final)
        result = verify_outer_asset(final, row)
        result["action"] = "DOWNLOADED_AND_VERIFIED"
        completed.append(result)
        atomic_json(state_path, {"phase": "DOWNLOADING", "updated_at": now_local(), "assets": completed})
    return completed


def validate_original_handoff(cache: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_row = row_for_role(rows, "original_manifest", "handoff_manifest")
    full_row = row_for_role(rows, "full", "full_archive", "pr_full_transfer")
    original = json_read(cache / manifest_row["name"])
    packages = original.get("packages")
    if not isinstance(packages, dict) or not isinstance(packages.get("full"), dict):
        raise ReceiverError("原 HANDOFF_MANIFEST packages.full 缺失")
    bound = packages["full"]
    if bound.get("name") != full_row["name"] or bound.get("bytes") != full_row["bytes"] or bound.get("sha256") != full_row["sha256"]:
        raise ReceiverError("原 HANDOFF_MANIFEST 与 Release 完整包 identity 不一致")
    return {
        "status": "PASS",
        "manifest": manifest_row["name"],
        "full_asset": full_row["name"],
        "internal_manifest_sha256": bound.get("internal_manifest_sha256"),
        "payload_entries": bound.get("payload_entries"),
        "payload_bytes": bound.get("payload_bytes"),
    }


def build_receipt(
    *,
    execution_site: str,
    manifest: dict[str, Any],
    repo: str,
    tag: str,
    layout: dict[str, Path],
    assets: list[dict[str, Any]],
    archive_result: dict[str, Any],
    supplement_result: dict[str, Any],
    disk: dict[str, Any],
) -> dict[str, Any]:
    relay = manifest.get("relay", {})
    return {
        "schema_version": 1,
        "role": "receive-receipt",
        "status": "RECEIVED_AND_VERIFIED",
        "execution_site": execution_site,
        "received_at": now_local(),
        "machine": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "task_id": manifest.get("task_id"),
        "source": {
            "repository": repo,
            "tag": tag,
            "commit": relay.get("commit"),
            "tree": relay.get("tree"),
            "release_url": relay.get("release_url"),
        },
        "assets": assets,
        "target": {key: str(value) for key, value in layout.items()},
        "archive": archive_result,
        "supplement": supplement_result,
        "disk_plan": disk,
        "external_dependencies": manifest.get("external_dependencies", []),
        "source_binding": manifest.get("source_binding"),
        "generated_files_not_in_payload": ["RECEIVE_RECEIPT.json", "RECEIVE_VALIDATION.json"],
        "limitations": [
            "传输与完整性通过不代表 A3、性能或完整非 Graph 验收通过。",
            "接收器没有执行归档内脚本、安装依赖或创建 dev/pr。",
        ],
    }
