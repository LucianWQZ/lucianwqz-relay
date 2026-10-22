#!/usr/bin/env python3
"""Redacted custom pattern scan over actual outer and nested ZIP members."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
import time
import urllib.parse
import zipfile


SOURCE = Path(
    "/Users/wenqingzhang/Desktop/中转/move/"
    "PR_服务器开发交接_20261022_170641_0800_c0d3/package/PR_FULL_TRANSFER.zip"
)
OUT = Path("/private/tmp/pr_publish_content_scan/container_pattern_scan_redacted.json")
MAX_DEPTH = 3
MAX_MEMBER = 64 << 20
MAX_TEXT_BYTES = 2 << 30
MAX_SECONDS = 300

PATTERNS = {
    "private_key_pem": re.compile(rb"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    "authorization_header": re.compile(
        rb"authorization\s*:\s*(?:bearer|basic)\s+[A-Za-z0-9+/_.=\-]{8,}", re.I
    ),
    "credential_url": re.compile(
        rb"(?:https?|ssh)://[^\s/@:]+:[^\s/@]+@[^\s/]+", re.I
    ),
    "aws_access_key_shape": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github_token_shape": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
}


def textlike(data: bytes) -> bool:
    head = data[:8192]
    return b"\x00" not in head and (
        not head
        or sum(byte in b"\t\n\r" or 32 <= byte < 127 or byte >= 128 for byte in head)
        / len(head)
        >= 0.90
    )


start = time.monotonic()
seen_text: dict[str, str] = {}
seen_archives: set[str] = set()
findings = []
binary_findings = []
stats = {
    "archive_occurrences": 0,
    "unique_archives": 0,
    "member_occurrences": 0,
    "text_occurrences": 0,
    "unique_text_members": 0,
    "unique_text_bytes_scanned": 0,
    "binary_or_nontext_occurrences": 0,
    "oversized_occurrences": 0,
}
limits = []
git_configs = []


def scan_text(data: bytes, path: str) -> None:
    digest = hashlib.sha256(data).hexdigest()
    if digest in seen_text:
        return
    if stats["unique_text_bytes_scanned"] + len(data) > MAX_TEXT_BYTES:
        limits.append({"scope": path, "reason": "text_byte_budget"})
        return
    seen_text[digest] = path
    stats["unique_text_members"] += 1
    stats["unique_text_bytes_scanned"] += len(data)
    for rule, pattern in PATTERNS.items():
        count = len(pattern.findall(data))
        if count:
            findings.append(
                {
                    "rule": rule,
                    "path": path,
                    "content_sha256": digest,
                    "count": count,
                    "matched_value_included": False,
                }
            )
    if path.lower().endswith("/.git/config") or path.lower().endswith("!.git/config"):
        text = data.decode("utf-8", "replace")
        url_rows = []
        for raw in re.findall(r"(?im)^\s*url\s*=\s*(.+?)\s*$", text):
            value = raw.strip()
            split = urllib.parse.urlsplit(value)
            url_rows.append(
                {
                    "scheme": split.scheme or "path-or-scp",
                    "host": split.hostname,
                    "userinfo_present": bool(split.username or split.password),
                    "password_component_present": split.password is not None,
                }
            )
        sensitive_keys = len(
            re.findall(
                r"(?im)^\s*(?:extraheader|helper|username)\s*=\s*\S+", text
            )
        )
        git_configs.append(
            {
                "path": path,
                "sha256": digest,
                "urls": url_rows,
                "sensitive_config_key_count": sensitive_keys,
            }
        )


def walk_zip(source: Path | bytes, label: str, depth: int) -> None:
    if time.monotonic() - start > MAX_SECONDS:
        limits.append({"scope": label, "reason": "time_budget"})
        return
    raw = source.read_bytes() if isinstance(source, Path) and depth else source
    if isinstance(raw, Path):
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        opened = raw
    else:
        digest = hashlib.sha256(raw).hexdigest()
        opened = io.BytesIO(raw)
    stats["archive_occurrences"] += 1
    if digest in seen_archives:
        return
    seen_archives.add(digest)
    stats["unique_archives"] += 1
    with zipfile.ZipFile(opened) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            stats["member_occurrences"] += 1
            path = f"{label}!{info.filename}" if depth else info.filename
            if info.file_size > MAX_MEMBER:
                stats["oversized_occurrences"] += 1
                continue
            data = zf.read(info)
            if depth < MAX_DEPTH and info.filename.lower().endswith(".zip"):
                walk_zip(data, path, depth + 1)
                continue
            if textlike(data):
                stats["text_occurrences"] += 1
                scan_text(data, path)
            else:
                stats["binary_or_nontext_occurrences"] += 1
                digest = hashlib.sha256(data).hexdigest()
                for rule, pattern in PATTERNS.items():
                    count = len(pattern.findall(data))
                    if count:
                        binary_findings.append(
                            {
                                "rule": rule,
                                "path": path,
                                "content_sha256": digest,
                                "count": count,
                                "matched_value_included": False,
                            }
                        )


walk_zip(SOURCE, SOURCE.name, 0)
result = {
    "schema_version": 1,
    "status": "PASS" if not limits else "PARTIAL",
    "source": str(SOURCE),
    "budgets": {
        "max_depth": MAX_DEPTH,
        "max_member_bytes": MAX_MEMBER,
        "max_unique_text_bytes": MAX_TEXT_BYTES,
        "max_seconds": MAX_SECONDS,
    },
    "stats": stats,
    "limits_hit": limits,
    "pattern_findings": findings,
    "binary_pattern_findings": binary_findings,
    "git_configs": git_configs,
    "matched_values_included": False,
    "elapsed_seconds": round(time.monotonic() - start, 3),
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(
    json.dumps(
        {
            "status": result["status"],
            "stats": stats,
            "limits_hit": limits,
            "pattern_finding_count": len(findings),
            "binary_pattern_finding_count": len(binary_findings),
            "pattern_rule_counts": {
                rule: sum(r["count"] for r in findings if r["rule"] == rule)
                for rule in PATTERNS
            },
            "git_config_count": len(git_configs),
            "elapsed_seconds": result["elapsed_seconds"],
        },
        ensure_ascii=False,
        indent=2,
    )
)
