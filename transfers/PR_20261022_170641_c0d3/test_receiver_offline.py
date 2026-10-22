#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from pr_receiver_common import ReceiverError, inspect_payload_zip


HERE = Path(__file__).resolve().parent
DOWNLOAD = HERE / "下载并恢复PR资料.py"
VERIFY = HERE / "验证PR接收资料.py"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


def make_payload_zip(path: Path, payload: dict[str, tuple[str, bytes, int, str | None]]) -> dict:
    rows = []
    with zipfile.ZipFile(path, "w") as zf:
        for rel, (kind, data, mode, target) in payload.items():
            info = zipfile.ZipInfo(rel)
            info.create_system = 3
            if kind == "symlink":
                info.external_attr = (stat.S_IFLNK | mode) << 16
            else:
                info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data)
            row = {
                "path": rel,
                "type": kind,
                "size": len(data),
                "sha256": digest(data),
                "mode": oct(mode),
            }
            if target is not None:
                row["target"] = target
            rows.append(row)
        manifest = {
            "schema_version": 1,
            "files": rows,
            "summary": {
                "payload_entries": len(rows),
                "payload_bytes": sum(row["size"] for row in rows),
                "regular_files": sum(row["type"] == "file" for row in rows),
                "symlinks": sum(row["type"] == "symlink" for row in rows),
            },
        }
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
        zf.writestr("FILES_MANIFEST.json", raw)
    return {
        "bytes": path.stat().st_size,
        "sha256": file_digest(path),
        "payload_entries": len(rows),
        "payload_bytes": sum(row["size"] for row in rows),
        "internal_manifest_sha256": digest(raw),
    }


class ReceiverOfflineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pr-receiver-test.")
        self.base = Path(self.temp.name)
        self.assets = self.base / "assets"
        self.assets.mkdir()
        self.full = self.assets / "PR_FULL_TRANSFER.zip"
        self.full_meta = make_payload_zip(
            self.full,
            {
                "a/target.txt": ("file", b"payload\n", 0o640, None),
                "a/sub/link": ("symlink", b"../target.txt", 0o777, "../target.txt"),
            },
        )
        self.supplement = self.assets / "PR_TRANSFER_SUPPLEMENT.zip"
        self.supplement_meta = make_payload_zip(
            self.supplement,
            {"PUBLICATION_ADDENDUM.md": ("file", b"supplement\n", 0o644, None)},
        )
        self.review = self.assets / "PR_REVIEW_RETURN.zip"
        self.review.write_bytes(b"review fixture")
        self.original = self.assets / "HANDOFF_MANIFEST.json"
        original_value = {
            "schema_version": 1,
            "packages": {"full": {"name": self.full.name, **self.full_meta}},
        }
        self.original.write_text(json.dumps(original_value), encoding="utf-8")
        self.manifest = self.base / "RELAY_TRANSFER_MANIFEST.json"
        rows = [
            {"role": "full", "name": self.full.name, **self.full_meta},
            {"role": "review", "name": self.review.name, "bytes": self.review.stat().st_size, "sha256": file_digest(self.review)},
            {"role": "original_manifest", "name": self.original.name, "bytes": self.original.stat().st_size, "sha256": file_digest(self.original)},
            {"role": "supplement", "name": self.supplement.name, **self.supplement_meta},
        ]
        value = {
            "schema_version": 1,
            "task_id": "fixture-task",
            "relay": {"repository": "owner/repo", "tag": "fixed-tag", "commit": "a" * 40, "tree": "b" * 40},
            "release_assets": rows,
            "target": {
                "task_directory_name": "fixture-task",
                "cache_relative": "cache/fixture-task",
                "supplement_relative": "supplement/fixture-task",
                "receipt_relative": "receipts/fixture-task",
                "full_payload_bytes": self.full_meta["payload_bytes"],
                "space_margin_bytes": 0,
            },
            "source_binding": {"ascend_sha": "c" * 40, "vllm_sha": "d" * 40},
        }
        self.manifest.write_text(json.dumps(value), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def command(self, script: Path, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable, str(script), "--root", str(root), "--manifest", str(self.manifest),
                "--repo", "owner/repo", "--tag", "fixed-tag", *extra,
            ],
            text=True,
            capture_output=True,
        )

    def test_dry_run_does_not_create_root(self):
        root = self.base / "dry-root"
        proc = self.command(DOWNLOAD, root, "--asset-dir", str(self.assets), "--execution-site", "LOCAL_SIMULATION", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(root.exists())
        self.assertEqual(json.loads(proc.stdout)["status"], "DRY_RUN_PASS")

    def test_offline_receive_and_independent_verify(self):
        root = self.base / "receive-root"
        proc = self.command(DOWNLOAD, root, "--asset-dir", str(self.assets), "--execution-site", "LOCAL_SIMULATION")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        receipt = json.loads(proc.stdout)
        self.assertEqual(receipt["execution_site"], "LOCAL_SIMULATION")
        target = root / "fixture-task"
        self.assertEqual((target / "a/target.txt").read_bytes(), b"payload\n")
        self.assertTrue((target / "a/sub/link").is_symlink())
        self.assertEqual(os.readlink(target / "a/sub/link"), "../target.txt")
        verify = self.command(VERIFY, root)
        self.assertEqual(verify.returncode, 0, verify.stderr)
        self.assertEqual(json.loads(verify.stdout)["status"], "PASS")

    def test_reject_symlink_escape(self):
        archive = self.base / "escape.zip"
        make_payload_zip(archive, {"x/link": ("symlink", b"../../outside", 0o777, "../../outside")})
        with self.assertRaises(ReceiverError):
            inspect_payload_zip(archive)

    def test_reject_casefold_collision(self):
        archive = self.base / "collision.zip"
        make_payload_zip(
            archive,
            {
                "A.txt": ("file", b"one", 0o644, None),
                "a.txt": ("file", b"two", 0o644, None),
            },
        )
        with self.assertRaises(ReceiverError):
            inspect_payload_zip(archive)

    def test_wrong_repo_is_rejected(self):
        root = self.base / "wrong-repo-root"
        proc = subprocess.run(
            [sys.executable, str(DOWNLOAD), "--root", str(root), "--manifest", str(self.manifest), "--repo", "other/repo", "--tag", "fixed-tag", "--dry-run"],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
