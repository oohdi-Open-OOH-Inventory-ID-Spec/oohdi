import argparse
import re
from typing import List

VALID_ID_PATTERN = re.compile(r"^[a-z0-9._~-]+/oohdi/[a-z0-9._~-]+$")
REVERSE_DNS_PATTERN = re.compile(r"^[a-z0-9._~-]+$")


def canonicalize_identifier(identifier: str) -> str:
    if identifier is None:
        raise ValueError("Identifier is required.")

    value = str(identifier).strip()
    if not value:
        raise ValueError("Identifier cannot be empty.")

    if value.endswith("/"):
        value = value.rstrip("/")

    normalized = value.lower()

    if len(normalized) > 255:
        raise ValueError("Identifier exceeds the 255-character maximum.")

    if normalized.startswith("/") or normalized.endswith("/"):
        raise ValueError("Identifier must not start or end with a slash.")

    if normalized.count("/oohdi/") != 1:
        raise ValueError("Identifier must contain exactly one /oohdi/ namespace segment.")

    if not VALID_ID_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Identifier contains invalid characters. Allowed: A-Z, a-z, 0-9, -, ., _, ~"
        )

    return normalized


def validate_identifier(identifier: str) -> List[str]:
    errors: List[str] = []

    try:
        canonicalize_identifier(identifier)
    except ValueError as exc:
        errors.append(str(exc))

    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and canonicalize an OOHDI identifier.")
    parser.add_argument("identifier", help="OOHDI identifier to validate, e.g. com.foobaroutdoor/oohdi/ABC-1234")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    errors = validate_identifier(args.identifier)

    if errors:
        print(f"INVALID: {args.identifier}")
        for error in errors:
            print(f"- {error}")
        return 1

    canonical = canonicalize_identifier(args.identifier)
    print(f"VALID: {canonical}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
