import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

from .validator import validate_identifier
from .schema_validator import validate_oohdi_record


def run_test_file(path: str) -> List[str]:
    file_path = Path(path)
    issues: List[str] = []

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: invalid JSON ({exc})"]

    id_value = payload.get("identity", {}).get("id") if isinstance(payload, dict) else None
    if isinstance(id_value, str):
        id_errors = validate_identifier(id_value)
        if id_errors:
            issues.append(f"{path}: identifier invalid: {id_errors}")

    if isinstance(payload, dict):
        schema_errors = validate_oohdi_record(payload)
        if schema_errors:
            for err in schema_errors:
                issues.append(f"{path}: {err}")

    return issues


def run_test_directory(path: str) -> List[str]:
    directory = Path(path)
    all_issues: List[str] = []
    for file_path in sorted(directory.rglob("*.json")):
        all_issues.extend(run_test_file(str(file_path)))
    return all_issues


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a lightweight OOHDI validation test suite over records or directories.")
    parser.add_argument("path", help="A JSON file or a folder containing OOHDI records")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    target = Path(args.path)
    if target.is_file():
        issues = run_test_file(str(target))
    elif target.is_dir():
        issues = run_test_directory(str(target))
    else:
        print(f"Path not found: {args.path}")
        return 2

    if issues:
        print("FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
