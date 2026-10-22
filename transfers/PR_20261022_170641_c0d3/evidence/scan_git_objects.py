#!/usr/bin/env python3
"""Inspect Git objects actually stored in the PR handoff payload.

This utility never contacts a remote.  It restores the three distinct bundles
with their recorded shallow boundaries, enumerates locally present Git blobs,
and writes content-deduplicated text blobs for a secret scanner.  It also
enumerates the two archived audit repositories; missing promisor objects are
reported and are outside the published bytes.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(
    "/Users/wenqingzhang/Desktop/中转/move/"
    "PR_服务器开发交接_20261022_170641_0800_c0d3"
)
OUT = Path("/private/tmp/pr_publish_content_scan")
RESTORES = OUT / "git_object_repos"
STAGE = OUT / "git_blob_texts"


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_text(data: bytes) -> bool:
    if not data:
        return True
    head = data[:8192]
    if b"\x00" in head:
        return False
    try:
        data[: min(len(data), 1 << 20)].decode("utf-8")
        return True
    except UnicodeDecodeError:
        printable = sum(byte in b"\t\n\r" or 32 <= byte < 127 for byte in head)
        return printable / len(head) >= 0.90


def restore_bundle(label: str, bundle: Path, shallow: Path | None) -> Path:
    target = RESTORES / label
    run(["git", "init", "--quiet", str(target)])
    if shallow:
        (target / ".git" / "shallow").write_bytes(shallow.read_bytes())
    verified = run(["git", "bundle", "verify", str(bundle)], cwd=target, check=False)
    if verified.returncode != 0:
        raise RuntimeError(f"bundle verify failed for {label}: {verified.stderr}")
    heads = run(["git", "bundle", "list-heads", str(bundle)]).stdout.splitlines()
    if not heads:
        raise RuntimeError(f"bundle has no heads: {label}")
    ref = heads[0].split(maxsplit=1)[1]
    run(["git", "fetch", str(bundle), ref], cwd=target)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=target)
    fsck = run(["git", "fsck", "--full"], cwd=target, check=False)
    if fsck.returncode != 0:
        raise RuntimeError(f"fsck failed for {label}: {fsck.stderr}")
    return target


def list_local_objects(repo: Path) -> tuple[list[tuple[str, int]], str]:
    proc = run(
        [
            "git",
            "cat-file",
            "--batch-all-objects",
            "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        ],
        cwd=repo,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    blobs = []
    for line in proc.stdout.splitlines():
        oid, typ, size = line.split()
        if typ == "blob":
            blobs.append((oid, int(size)))
    return blobs, proc.stderr


def stage_blobs(repo: Path, label: str, seen: dict[str, dict], limit: int = 32 << 20) -> dict:
    blobs, stderr = list_local_objects(repo)
    stats = {
        "label": label,
        "repository": str(repo),
        "local_blob_objects": len(blobs),
        "blob_bytes_declared": sum(size for _, size in blobs),
        "max_blob_bytes": limit,
        "oversized_blob_count": 0,
        "binary_blob_count": 0,
        "text_blob_occurrences": 0,
        "unique_text_blob_additions": 0,
        "enumeration_stderr": stderr,
    }
    for oid, size in blobs:
        if size > limit:
            stats["oversized_blob_count"] += 1
            continue
        got = subprocess.run(
            ["git", "cat-file", "blob", oid], cwd=repo, check=True, capture_output=True
        ).stdout
        if len(got) != size:
            raise RuntimeError(f"blob size mismatch {label} {oid}")
        if not is_text(got):
            stats["binary_blob_count"] += 1
            continue
        stats["text_blob_occurrences"] += 1
        digest = hashlib.sha256(got).hexdigest()
        entry = seen.setdefault(digest, {"bytes": len(got), "occurrences": []})
        entry["occurrences"].append({"repo": label, "oid": oid})
        target = STAGE / f"{digest}.txt"
        if not target.exists():
            target.write_bytes(got)
            stats["unique_text_blob_additions"] += 1
    return stats


def main() -> None:
    shutil.rmtree(RESTORES, ignore_errors=True)
    shutil.rmtree(STAGE, ignore_errors=True)
    RESTORES.mkdir(parents=True)
    STAGE.mkdir(parents=True)

    bundles = list(ROOT.rglob("*.bundle"))
    by_hash: dict[str, list[Path]] = {}
    for path in bundles:
        by_hash.setdefault(sha256(path), []).append(path)

    expected = {
        "6a183cb3ebc435df49390cfe90ed8ad54be8dae15d7dd8f4c2de03b896f497bb": "vllm",
        "347fe1225cebf32dedbc3b9e54fbf8efe68e6435e0181122e1865fa1059e6469": "ascend_b013719",
        "920dbdd071e0ca5355608de156804dcc28fb1d74723a2cc8959d5fd9915c9e83": "ascend_2604675",
    }
    if set(by_hash) != set(expected):
        raise RuntimeError(f"unexpected bundle hashes: {sorted(by_hash)}")

    restored: list[tuple[str, Path]] = []
    bundle_rows = []
    for digest, label in expected.items():
        path = by_hash[digest][0]
        shallow_candidates = list(path.parent.glob("*.shallow"))
        shallow = None
        if label == "vllm":
            shallow = next((p for p in shallow_candidates if p.name == "vllm.shallow"), None)
        else:
            shallow = next((p for p in shallow_candidates if p.name == "vllm-ascend.shallow"), None)
        if shallow is None:
            # Historical bundle directories may omit boundaries; use the matching
            # boundary from the same candidate's package tree when present.
            name = "vllm.shallow" if label == "vllm" else "vllm-ascend.shallow"
            candidates = list(ROOT.rglob(name))
            # Bundle verification determines whether a candidate boundary fits.
            for candidate in candidates:
                try:
                    repo = restore_bundle(label, path, candidate)
                    shallow = candidate
                    break
                except Exception:
                    shutil.rmtree(RESTORES / label, ignore_errors=True)
            else:
                raise RuntimeError(f"no usable shallow boundary for {label}")
        else:
            repo = restore_bundle(label, path, shallow)
        restored.append((f"bundle:{label}", repo))
        bundle_rows.append(
            {
                "label": label,
                "sha256": digest,
                "bytes": path.stat().st_size,
                "occurrences": [str(p.relative_to(ROOT)) for p in by_hash[digest]],
                "shallow_path": str(shallow.relative_to(ROOT)) if shallow else None,
                "restored_head": run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip(),
                "restored_tree": run(["git", "rev-parse", "HEAD^{tree}"], cwd=repo).stdout.strip(),
            }
        )

    audit_root = (
        ROOT
        / "任务归档/001_20261020_非Graph历史审计与需求证据/原始资料/"
        "MRV2_NonGraph_Audit_20261020_2W0Wi3rU/audit_clones"
    )
    restored.extend(
        [
            ("embedded:vllm-ascend", audit_root / "vllm-ascend"),
            ("embedded:vllm", audit_root / "vllm"),
        ]
    )

    seen: dict[str, dict] = {}
    stats = [stage_blobs(repo, label, seen) for label, repo in restored]
    mapping = {
        digest: {
            "bytes": entry["bytes"],
            "occurrence_count": len(entry["occurrences"]),
            "sample_occurrences": entry["occurrences"][:8],
        }
        for digest, entry in seen.items()
    }
    (OUT / "git_blob_mapping.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n"
    )
    result = {
        "status": "PASS",
        "scope": "all locally stored blob objects in 3 unique bundles and 2 embedded Git object stores",
        "bundle_rows": bundle_rows,
        "repositories": stats,
        "unique_text_blobs": len(seen),
        "unique_text_bytes": sum(entry["bytes"] for entry in seen.values()),
        "limitations": [
            "Promisor objects absent from the payload are not scanned and are not published bytes.",
            "Blobs larger than 32 MiB and binary blobs are inventory-counted, not treated as text-secret scan inputs.",
        ],
    }
    (OUT / "git_object_inventory.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
