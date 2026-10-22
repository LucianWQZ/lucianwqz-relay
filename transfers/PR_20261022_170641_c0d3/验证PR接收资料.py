#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立复核已接收的 PR 迁移资料、Release 资产与回执。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pr_receiver_common import (
    ReceiverError,
    asset_rows,
    atomic_json,
    inspect_payload_zip,
    json_read,
    now_local,
    relay_identity,
    row_for_role,
    target_layout,
    validate_original_handoff,
    verify_archive_payload_hashes,
    verify_directory,
    verify_outer_asset,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="验证固定 repo/tag 对应的 PR 接收结果。")
    result.add_argument("--root", required=True, type=Path, help="reference/pr 根")
    result.add_argument("--manifest", required=True, type=Path, help="RELAY_TRANSFER_MANIFEST.json")
    result.add_argument("--repo", required=True)
    result.add_argument("--tag", required=True)
    result.add_argument("--dry-run", action="store_true", help="只展示待验证路径；不创建或修改文件")
    return result


def expected_zip_fields(row: dict, original: dict | None = None) -> dict:
    return {
        "expected_internal_manifest_sha256": row.get("internal_manifest_sha256") or (original or {}).get("internal_manifest_sha256"),
        "expected_entries": row.get("payload_entries") if row.get("payload_entries") is not None else (original or {}).get("payload_entries"),
        "expected_payload_bytes": row.get("payload_bytes") if row.get("payload_bytes") is not None else (original or {}).get("payload_bytes"),
    }


def main() -> int:
    args = parser().parse_args()
    manifest_path = args.manifest.expanduser().resolve()
    root = args.root.expanduser().resolve(strict=False)
    manifest = json_read(manifest_path)
    fixed_repo, fixed_tag = relay_identity(manifest)
    if args.repo != fixed_repo or args.tag != fixed_tag or args.tag.casefold() == "latest":
        raise ReceiverError("repo/tag 必须与传输清单精确一致，且不得为 latest")
    rows = asset_rows(manifest)
    layout = target_layout(manifest, root)
    if args.dry_run:
        print(json.dumps({
            "status": "DRY_RUN_PASS",
            "dry_run": True,
            "no_files_created": True,
            "repository": fixed_repo,
            "tag": fixed_tag,
            "layout": {key: str(value) for key, value in layout.items()},
            "assets": [row["name"] for row in rows],
        }, ensure_ascii=False, indent=2))
        return 0

    verified_assets = [verify_outer_asset(layout["cache"] / row["name"], row) for row in rows]
    original = validate_original_handoff(layout["cache"], rows)
    full_row = row_for_role(rows, "full", "full_archive", "pr_full_transfer")
    full_archive = layout["cache"] / full_row["name"]
    full_plan = inspect_payload_zip(full_archive, **expected_zip_fields(full_row, original))
    full_archive_result = verify_archive_payload_hashes(full_archive, full_plan)
    full_directory_result = verify_directory(layout["archive"], full_plan["records"])

    supplement_row = row_for_role(rows, "supplement", "supplement_zip")
    supplement_archive = layout["cache"] / supplement_row["name"]
    supplement_plan = inspect_payload_zip(supplement_archive, **expected_zip_fields(supplement_row))
    supplement_archive_result = verify_archive_payload_hashes(supplement_archive, supplement_plan)
    supplement_directory_result = verify_directory(layout["supplement"], supplement_plan["records"])

    receipt_path = layout["receipt"] / "RECEIVE_RECEIPT.json"
    receipt = json_read(receipt_path)
    if receipt.get("status") != "RECEIVED_AND_VERIFIED":
        raise ReceiverError("RECEIVE_RECEIPT status 不是 RECEIVED_AND_VERIFIED")
    if receipt.get("source", {}).get("repository") != fixed_repo or receipt.get("source", {}).get("tag") != fixed_tag:
        raise ReceiverError("RECEIVE_RECEIPT repo/tag 与传输清单不符")
    result = {
        "schema_version": 1,
        "role": "receive-validation",
        "status": "PASS",
        "verified_at": now_local(),
        "repository": fixed_repo,
        "tag": fixed_tag,
        "root": str(root),
        "assets": verified_assets,
        "original_handoff_binding": original,
        "full_archive": full_archive_result,
        "full_directory": full_directory_result,
        "supplement_archive": supplement_archive_result,
        "supplement_directory": supplement_directory_result,
        "receipt": {
            "path": str(receipt_path),
            "status": receipt["status"],
            "execution_site": receipt.get("execution_site"),
        },
        "scope": "传输与内容完整性；不代表 A3、性能或完整非 Graph 验收。",
    }
    output = layout["receipt"] / "RECEIVE_VALIDATION.json"
    atomic_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReceiverError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
