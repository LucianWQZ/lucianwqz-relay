#!/usr/bin/env python3
"""Bounded structural inventory of ZIPs nested in the public transfer ZIP."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import time
import unicodedata
import zipfile


SOURCE = Path(
    "/Users/wenqingzhang/Desktop/中转/move/"
    "PR_服务器开发交接_20261022_170641_0800_c0d3/package/PR_FULL_TRANSFER.zip"
)
OUT = Path("/private/tmp/pr_publish_content_scan/nested_archive_inventory.json")
MAX_DEPTH = 3
MAX_ARCHIVE_BYTES = 128 << 20
MAX_MEMBER_BYTES = 256 << 20
MAX_TOTAL_EXPANDED_BYTES = 4 << 30
MAX_ENTRIES = 100_000
MAX_SECONDS = 300
SUSPICIOUS = re.compile(
    r"(^|/)(id_(rsa|dsa|ecdsa|ed25519)(\.|$)|\.netrc$|credentials?(\.|$)|"
    r"secrets?(\.|$)|.*\.(pem|p12|pfx|key|jks|keystore)$)",
    re.IGNORECASE,
)


def unsafe(name: str) -> bool:
    p = PurePosixPath(name)
    return p.is_absolute() or ".." in p.parts or "\\" in name or "\x00" in name


start = time.monotonic()
rows = []
seen_archives: dict[str, str] = {}
totals = {"entries": 0, "declared_uncompressed_bytes": 0, "archive_bytes_read": 0}
limits = []
suspicious_names = []


def inspect_zip(data: bytes | Path, label: str, depth: int) -> None:
    if time.monotonic() - start > MAX_SECONDS:
        limits.append({"scope": label, "reason": "time_budget_exceeded"})
        return
    raw_size = data.stat().st_size if isinstance(data, Path) else len(data)
    if depth and raw_size > MAX_ARCHIVE_BYTES:
        limits.append({"scope": label, "reason": "nested_archive_size_limit", "bytes": raw_size})
        return
    digest = None
    if isinstance(data, Path):
        h = hashlib.sha256()
        with data.open("rb") as f:
            for chunk in iter(lambda: f.read(4 << 20), b""):
                h.update(chunk)
        digest = h.hexdigest()
    else:
        digest = hashlib.sha256(data).hexdigest()
    if digest in seen_archives:
        rows.append(
            {
                "path": label,
                "depth": depth,
                "bytes": raw_size,
                "sha256": digest,
                "duplicate_of": seen_archives[digest],
            }
        )
        return
    seen_archives[digest] = label
    source = data if isinstance(data, Path) else io.BytesIO(data)
    try:
        with zipfile.ZipFile(source) as zf:
            infos = zf.infolist()
            names = [i.filename for i in infos]
            lower_norm = [unicodedata.normalize("NFC", n).casefold() for n in names]
            row = {
                "path": label,
                "depth": depth,
                "bytes": raw_size,
                "sha256": digest,
                "members": len(infos),
                "declared_uncompressed_bytes": sum(i.file_size for i in infos),
                "encrypted_members": sum(bool(i.flag_bits & 1) for i in infos),
                "unsafe_member_names": sum(unsafe(i.filename) for i in infos),
                "duplicate_member_names": len(names) - len(set(names)),
                "normalized_case_collisions": len(lower_norm) - len(set(lower_norm)),
                "oversized_members": sum(i.file_size > MAX_MEMBER_BYTES for i in infos),
                "status": "STRUCTURE_READ",
            }
            rows.append(row)
            totals["entries"] += len(infos)
            totals["declared_uncompressed_bytes"] += row["declared_uncompressed_bytes"]
            if totals["entries"] > MAX_ENTRIES:
                limits.append({"scope": label, "reason": "entry_budget_exceeded"})
                return
            if totals["declared_uncompressed_bytes"] > MAX_TOTAL_EXPANDED_BYTES:
                limits.append({"scope": label, "reason": "expanded_byte_budget_exceeded"})
                return
            for info in infos:
                if SUSPICIOUS.search(info.filename):
                    suspicious_names.append({"archive": label, "member": info.filename})
                if depth >= MAX_DEPTH or info.is_dir() or info.file_size > MAX_MEMBER_BYTES:
                    continue
                if not info.filename.lower().endswith(".zip"):
                    continue
                child = zf.read(info)
                totals["archive_bytes_read"] += len(child)
                inspect_zip(child, f"{label}!{info.filename}", depth + 1)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        rows.append(
            {
                "path": label,
                "depth": depth,
                "bytes": raw_size,
                "sha256": digest,
                "status": "UNREADABLE",
                "reason": type(exc).__name__,
            }
        )


inspect_zip(SOURCE, SOURCE.name, 0)
result = {
    "schema_version": 1,
    "status": "PASS" if not limits and all(r.get("status") != "UNREADABLE" for r in rows) else "PARTIAL",
    "source": str(SOURCE),
    "budgets": {
        "max_depth": MAX_DEPTH,
        "max_nested_archive_bytes": MAX_ARCHIVE_BYTES,
        "max_member_bytes": MAX_MEMBER_BYTES,
        "max_total_declared_expanded_bytes": MAX_TOTAL_EXPANDED_BYTES,
        "max_entries": MAX_ENTRIES,
        "max_seconds": MAX_SECONDS,
    },
    "totals": totals,
    "unique_archive_count": len(seen_archives),
    "archive_occurrence_count": len(rows),
    "limits_hit": limits,
    "suspicious_filenames": suspicious_names,
    "rows": rows,
    "elapsed_seconds": round(time.monotonic() - start, 3),
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False, indent=2))
