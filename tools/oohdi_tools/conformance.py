import argparse
import json
import sys
from typing import Any, Dict, List, Tuple

from .schema_validator import validate_oohdi_record


def _status_code_ok(status_code: int) -> bool:
    return status_code in {200, 301, 304, 404, 410, 421}


def run_registry_conformance_checks(sample_record: Dict[str, Any], response_status: int, response_body: Any) -> List[str]:
    errors: List[str] = []

    if not _status_code_ok(response_status):
        errors.append(f"Unexpected HTTP status: {response_status}")

    if response_status == 421:
        error_code = response_body.get("error_code") if isinstance(response_body, dict) else None
        if error_code != "not_authoritative":
            errors.append("421 responses must set error_code='not_authoritative'.")

    if response_status in {200, 301, 304}:
        if isinstance(response_body, dict):
            schema_errors = validate_oohdi_record(response_body)
            if schema_errors:
                errors.extend([f"Schema: {e}" for e in schema_errors])
        else:
            errors.append("200/301/304 responses must contain a JSON object body.")

    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OOHDI registry conformance checks against a sample response.")
    parser.add_argument("--status", type=int, required=True, help="HTTP status code for the response being checked")
    parser.add_argument("--body", help="JSON body to validate as a string")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.body is None:
        print("A JSON body is required for conformance checks.")
        return 2

    try:
        payload = json.loads(args.body)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON body: {exc}")
        return 2

    errors = run_registry_conformance_checks({"dummy": True}, args.status, payload)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
