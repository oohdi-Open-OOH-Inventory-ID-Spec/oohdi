import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def canonicalize_identifier(identifier: str) -> str:
    if identifier is None:
        raise ValueError("Identifier is required.")

    value = str(identifier).strip().lower().rstrip("/")
    if not value or value.startswith("/"):
        raise ValueError("Identifier is invalid.")

    if value.count("/oohdi/") != 1:
        raise ValueError("Identifier must contain exactly one /oohdi/ segment.")

    if len(value) > 255:
        raise ValueError("Identifier exceeds the 255-character limit.")

    if not re.fullmatch(r"[a-z0-9._~-]+/oohdi/[a-z0-9._~-]+", value):
        raise ValueError("Identifier contains invalid characters.")

    return value


def load_json_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object.")
    return payload


def resolve_identifier(identifier: str, records_dir: Optional[str] = None) -> Dict[str, Any]:
    canonical = canonicalize_identifier(identifier)
    result: Dict[str, Any] = {
        "input": identifier,
        "canonical": canonical,
        "resolved": False,
        "source": "none",
        "record": None,
    }

    if records_dir is None:
        return result

    candidates = [
        Path(records_dir) / "record.json",
        Path(records_dir) / f"{canonical.replace('/', '_')}.json",
        Path(records_dir) / f"{canonical.split('/')[-1]}.json",
    ]

    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            result["record"] = load_json_file(str(candidate))
            result["resolved"] = True
            result["source"] = str(candidate)
            break
        except ValueError:
            continue

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve a canonical OOHDI identifier against a local data directory.")
    parser.add_argument("identifier", help="OOHDI identifier to resolve")
    parser.add_argument("--records-dir", default=None, help="Optional directory containing local sample records")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = resolve_identifier(args.identifier, args.records_dir)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["resolved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
