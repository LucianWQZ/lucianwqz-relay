#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从固定 GitHub Release 或离线资产目录安全接收 PR 迁移资料。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from pr_receiver_common import (
    ReceiverError,
    asset_rows,
    atomic_json,
    build_receipt,
    disk_plan,
    download_assets,
    extract_atomically,
    inspect_payload_zip,
    json_read,
    now_local,
    relay_identity,
    row_for_role,
    target_layout,
    validate_original_handoff,
    verify_archive_payload_hashes,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="固定 repo/tag 的 PR 资料接收器；不会执行归档内代码或创建 dev/pr。"
    )
    result.add_argument("--root", required=True, type=Path, help="reference/pr 根；本地演练可指向临时目录")
    result.add_argument("--manifest", required=True, type=Path, help="RELAY_TRANSFER_MANIFEST.json")
    result.add_argument("--repo", required=True, help="必须与 manifest relay.repository 完全一致")
    result.add_argument("--tag", required=True, help="必须与 manifest relay.tag 完全一致；禁止 latest")
    result.add_argument(
        "--asset-dir", type=Path,
        help="离线/演练资产目录；省略时使用 gh release download 从固定 tag 下载",
    )
    result.add_argument(
        "--execution-site", choices=["LOCAL_SIMULATION", "SERVER"], default="SERVER",
        help="回执站点；本地演练必须显式使用 LOCAL_SIMULATION",
    )
    result.add_argument("--dry-run", action="store_true", help="只校验参数、空间方案与目标布局；不创建目录、不下载")
    return result


def expected_zip_fields(row: dict, original: dict | None = None) -> dict:
    result = {
        "expected_internal_manifest_sha256": row.get("internal_manifest_sha256"),
        "expected_entries": row.get("payload_entries"),
        "expected_payload_bytes": row.get("payload_bytes"),
    }
    if original:
        result["expected_internal_manifest_sha256"] = result["expected_internal_manifest_sha256"] or original.get("internal_manifest_sha256")
        result["expected_entries"] = result["expected_entries"] if result["expected_entries"] is not None else original.get("payload_entries")
        result["expected_payload_bytes"] = result["expected_payload_bytes"] if result["expected_payload_bytes"] is not None else original.get("payload_bytes")
    return result


def main() -> int:
    args = parser().parse_args()
    manifest_path = args.manifest.expanduser().resolve()
    root = args.root.expanduser().resolve(strict=False)
    manifest = json_read(manifest_path)
    fixed_repo, fixed_tag = relay_identity(manifest)
    if args.repo != fixed_repo or args.tag != fixed_tag:
        raise ReceiverError(
            f"repo/tag 与清单不一致：传入 {args.repo}@{args.tag}，清单 {fixed_repo}@{fixed_tag}"
        )
    if args.tag.casefold() == "latest":
        raise ReceiverError("拒绝 latest；必须使用固定 tag")
    rows = asset_rows(manifest)
    layout = target_layout(manifest, root)
    disk = disk_plan(manifest, rows, root)
    dry_result = {
        "status": "DRY_RUN_PASS" if disk["sufficient"] else "DRY_RUN_BLOCKED_SPACE",
        "dry_run": True,
        "no_files_created": True,
        "manifest": str(manifest_path),
        "repository": fixed_repo,
        "tag": fixed_tag,
        "execution_site": args.execution_site,
        "layout": {key: str(value) for key, value in layout.items()},
        "assets": [{key: row.get(key) for key in ("role", "name", "bytes", "sha256")} for row in rows],
        "disk_plan": disk,
        "asset_source": str(args.asset_dir.resolve()) if args.asset_dir else "GITHUB_RELEASE_VIA_GH",
    }
    if args.dry_run:
        print(json.dumps(dry_result, ensure_ascii=False, indent=2))
        return 0 if disk["sufficient"] else 2
    if not disk["sufficient"]:
        raise ReceiverError(
            f"空间不足：free={disk['observed_free_bytes']} required={disk['required_free_bytes']}"
        )
    if args.asset_dir is not None:
        source = args.asset_dir.expanduser().resolve()
        if not source.is_dir():
            raise ReceiverError(f"--asset-dir 不是目录：{source}")
    else:
        source = None
        if shutil.which("gh") is None:
            raise ReceiverError("未找到 gh；安装 GitHub CLI 或使用 --asset-dir")

    # All generated state stays outside the immutable restored payload.
    layout["receipt"].mkdir(parents=True, exist_ok=True)
    lock = layout["receipt"] / ".receive.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ReceiverError(f"已有接收锁，可能存在进行中或中断任务：{lock}") from exc
    os.write(descriptor, f"pid={os.getpid()} started={now_local()}\n".encode())
    os.close(descriptor)
    state_path = layout["receipt"] / "RECEIVE_STATE.json"
    try:
        atomic_json(state_path, {"phase": "STARTED", "updated_at": now_local()})
        assets = download_assets(
            rows,
            cache=layout["cache"],
            repo=fixed_repo,
            tag=fixed_tag,
            asset_source_dir=source,
            state_path=state_path,
        )
        original = validate_original_handoff(layout["cache"], rows)
        full_row = row_for_role(rows, "full", "full_archive", "pr_full_transfer")
        full_archive = layout["cache"] / full_row["name"]
        full_plan = inspect_payload_zip(full_archive, **expected_zip_fields(full_row, original))
        full_archive_check = verify_archive_payload_hashes(full_archive, full_plan)
        archive_result = extract_atomically(full_archive, layout["archive"], full_plan)
        archive_result["archive_validation"] = full_archive_check

        supplement_row = row_for_role(rows, "supplement", "supplement_zip")
        supplement_archive = layout["cache"] / supplement_row["name"]
        supplement_plan = inspect_payload_zip(supplement_archive, **expected_zip_fields(supplement_row))
        supplement_archive_check = verify_archive_payload_hashes(supplement_archive, supplement_plan)
        supplement_result = extract_atomically(supplement_archive, layout["supplement"], supplement_plan)
        supplement_result["archive_validation"] = supplement_archive_check

        receipt = build_receipt(
            execution_site=args.execution_site,
            manifest=manifest,
            repo=fixed_repo,
            tag=fixed_tag,
            layout=layout,
            assets=assets,
            archive_result=archive_result,
            supplement_result=supplement_result,
            disk=disk,
        )
        receipt["original_handoff_binding"] = original
        receipt_path = layout["receipt"] / "RECEIVE_RECEIPT.json"
        atomic_json(receipt_path, receipt)
        atomic_json(state_path, {"phase": "RECEIVED_AND_VERIFIED", "updated_at": now_local(), "receipt": str(receipt_path)})
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        atomic_json(
            state_path,
            {
                "phase": "FAILED",
                "updated_at": now_local(),
                "error_type": type(exc).__name__,
                "error": str(exc),
                "note": "partial/staging 保留供审阅；工具不会自动删除或合并。",
            },
        )
        raise
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReceiverError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
