#!/usr/bin/env python3
"""Produce a redacted, path-only summary of Git-object gitleaks findings."""

from __future__ import annotations

import collections
import json
from pathlib import Path
import subprocess


OUT = Path("/private/tmp/pr_publish_content_scan")


def object_paths(repo: Path) -> dict[str, list[str]]:
    proc = subprocess.run(
        ["git", "rev-list", "--objects", "--all", "--missing=allow-any"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    result: dict[str, list[str]] = collections.defaultdict(list)
    for line in proc.stdout.splitlines():
        oid, _, path = line.partition(" ")
        if path:
            result[oid].append(path)
    return result


def main() -> None:
    mappings = json.loads((OUT / "git_blob_mapping.json").read_text())
    findings = json.loads((OUT / "gitleaks_git_objects_redacted.json").read_text())
    repos = {
        p.name: p for p in (OUT / "git_object_repos").iterdir() if (p / ".git").is_dir()
    }
    path_maps = {f"bundle:{name}": object_paths(repo) for name, repo in repos.items()}
    rows = []
    for finding in findings:
        digest = Path(finding["File"]).stem
        entry = mappings[digest]
        paths = set()
        labels = set()
        for occurrence in entry["sample_occurrences"]:
            label = occurrence["repo"]
            labels.add(label)
            for path in path_maps.get(label, {}).get(occurrence["oid"], []):
                paths.add(path)
        rows.append(
            {
                "rule_id": finding["RuleID"],
                "content_sha256": digest,
                "bytes": entry["bytes"],
                "occurrence_count": entry["occurrence_count"],
                "repository_labels": sorted(labels),
                "candidate_paths": sorted(paths)[:30],
                "path_mapping_complete": bool(paths),
            }
        )
    summary = {
        "status": "REDACTED_FINDING_INDEX",
        "finding_count": len(rows),
        "rule_counts": dict(collections.Counter(r["rule_id"] for r in rows)),
        "mapped_path_count": sum(r["path_mapping_complete"] for r in rows),
        "rows": rows,
        "secret_values_included": False,
    }
    (OUT / "git_object_findings_redacted_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    counts = collections.Counter()
    for row in rows:
        if row["candidate_paths"]:
            for path in row["candidate_paths"]:
                counts[(row["rule_id"], path)] += 1
        else:
            counts[(row["rule_id"], "<unmapped-local-object>")] += 1
    print(json.dumps({"findings": len(rows), "mapped": summary["mapped_path_count"]}, indent=2))
    for (rule, path), count in counts.most_common():
        print(count, rule, path)


if __name__ == "__main__":
    main()
