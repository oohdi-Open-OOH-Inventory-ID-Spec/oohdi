import argparse
import re
import shutil
import subprocess
from typing import Dict, List, Optional


TXT_PATTERN = re.compile(r"v\s*=\s*([A-Za-z0-9]+)\s*;\s*r\s*=\s*([^;\s]+)\s*;?", re.IGNORECASE)


def _run_dns_query(domain: str) -> List[str]:
    target = f"_oohdi.{domain.strip()}"
    commands = [
        ["dig", "+short", "TXT", target],
        ["drill", "-t", "TXT", target],
        ["nslookup", "-type=TXT", target],
    ]

    for command in commands:
        if shutil.which(command[0]) is None:
            continue
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            output = result.stdout.strip()
            if output:
                return [line.strip() for line in output.splitlines() if line.strip()]
        except OSError:
            continue

    return []


def discover_authoritative_registry(domain: str) -> Dict[str, object]:
    record = {
        "domain": domain.strip(),
        "target": f"_oohdi.{domain.strip()}",
        "found": False,
        "records": [],
        "version": None,
        "registry": None,
    }

    raw_records = _run_dns_query(domain)
    record["records"] = raw_records
    for item in raw_records:
        match = TXT_PATTERN.search(item)
        if match:
            record["found"] = True
            record["version"] = match.group(1)
            record["registry"] = match.group(2)
            break

    if not raw_records:
        record["message"] = "No _oohdi TXT record found or no compatible DNS client is installed."
    else:
        record["message"] = "TXT record discovered." if record["found"] else "TXT record found but did not match OOHDI format."

    return record


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find the authoritative OOHDI registry for a domain via DNS TXT discovery.")
    parser.add_argument("domain", help="Domain to inspect, e.g. foobaroutdoor.com")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = discover_authoritative_registry(args.domain)
    print(f"Domain: {result['domain']}")
    print(f"TXT target: {result['target']}")
    print(f"Found: {result['found']}")
    if result.get("version"):
        print(f"Version: {result['version']}")
    if result.get("registry"):
        print(f"Authoritative registry: {result['registry']}")
    if result.get("records"):
        print("Records:")
        for rec in result["records"]:
            print(f"  - {rec}")
    else:
        print(result.get("message", "No records returned."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
