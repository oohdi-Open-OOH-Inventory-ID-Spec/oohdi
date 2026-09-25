import argparse
import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List


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


def build_registry_url(registry_host: str, identifier: str) -> str:
    host = registry_host.strip().rstrip("/")
    if host.startswith("http://") or host.startswith("https://"):
        base = host
    else:
        if ":" in host and not host.startswith("["):
            base = f"http://{host}"
        else:
            base = f"https://{host}"

    canonical = canonicalize_identifier(identifier)
    namespace, media_owner_id = canonical.rsplit("/oohdi/", 1)
    return f"{base}/oohdi/{namespace}/{media_owner_id}"


def fetch_registry_record(registry_host: str, identifier: str) -> Dict[str, Any]:
    canonical = canonicalize_identifier(identifier)
    url = build_registry_url(registry_host, canonical)
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body) if body else {}
            return {
                "ok": True,
                "status": response.status,
                "url": url,
                "canonical": canonical,
                "payload": payload,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {"raw": body}
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "canonical": canonical,
            "payload": payload,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "url": url,
            "canonical": canonical,
            "payload": {},
            "error": str(exc),
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch an OOHDI record from a registry host and show the response.")
    parser.add_argument("registry_host", help="Registry hostname, e.g. example-registry.oohdi.org")
    parser.add_argument("identifier", help="OOHDI identifier, e.g. org.oohdi.example-media-owner/oohdi/emp-001")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = fetch_registry_record(args.registry_host, args.identifier)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
