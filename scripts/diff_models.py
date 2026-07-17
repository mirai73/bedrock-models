#!/usr/bin/env python3
"""
diff_models.py — Compare two versions of bedrock_models.json and report changes.

Usage:
    python scripts/diff_models.py <old_file> <new_file>

For each top-level model key that changed between the two files:
  - NEW      : key exists only in the new file
  - REMOVED  : key exists only in the old file
  - CHANGED  : key exists in both but the value differs (shows old vs new)
"""

import json
import sys
from pathlib import Path


def load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def format_value(value: dict) -> str:
    return json.dumps(value, indent=4, sort_keys=True)


def diff_models(old: dict, new: dict) -> None:
    old_keys = set(old.keys())
    new_keys = set(new.keys())

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    common = sorted(old_keys & new_keys)
    changed = [k for k in common if old[k] != new[k]]

    total = len(added) + len(removed) + len(changed)
    if total == 0:
        print("No differences found.")
        return

    print(f"Summary: {len(added)} added, {len(removed)} removed, {len(changed)} changed\n")
    print("=" * 72)

    for key in added:
        print(f"\n[NEW] {key}")
        print("-" * 72)
        print(format_value(new[key]))

    for key in removed:
        print(f"\n[REMOVED] {key}")
        print("-" * 72)
        print(format_value(old[key]))

    for key in changed:
        print(f"\n[CHANGED] {key}")
        print("-" * 72)
        print("  Previous:")
        for line in format_value(old[key]).splitlines():
            print(f"    {line}")
        print("  New:")
        for line in format_value(new[key]).splitlines():
            print(f"    {line}")


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <old_file> <new_file>", file=sys.stderr)
        sys.exit(1)

    old_path, new_path = sys.argv[1], sys.argv[2]
    old = load_json(old_path)
    new = load_json(new_path)

    print(f"Comparing:")
    print(f"  old: {old_path}  ({len(old)} models)")
    print(f"  new: {new_path}  ({len(new)} models)")
    print()

    diff_models(old, new)


if __name__ == "__main__":
    main()
