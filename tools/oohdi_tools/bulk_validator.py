import argparse
import json
from pathlib import Path
from typing import List

from .schema_validator import validate_oohdi_record


def iter_json_files(path: str) -> List[Path]:
    target = Path(path)
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(target.rglob("*.json"))
    return []


def validate_path(path: str) -> List[str]:
    issues: List[str] = []
    files = iter_json_files(path)
    if not files:
        return [f"No JSON files found at: {path}"]

    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"{file_path}: invalid JSON ({exc})")
            continue

        errors = validate_oohdi_record(payload)
        if errors:
            issues.append(f"{file_path}:")
            for error in errors:
                issues.append(f"  - {error}")

    return issues


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one file or a directory of OOHDI JSON records.")
    parser.add_argument("path", help="A JSON file or a folder containing .json records")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    issues = validate_path(args.path)

    if issues:
        print("FAIL")
        for issue in issues:
            print(issue)
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
