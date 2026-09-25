import argparse
import sys

from .bulk_validator import main as bulk_main
from .conformance import main as conformance_main
from .dns_checker import main as dns_main
from .fetch import main as fetch_main
from .resolve import main as resolve_main
from .schema_validator import main as schema_main
from .test_suite import main as test_main
from .validator import main as validate_main


COMMANDS = {
    "validate": validate_main,
    "dns": dns_main,
    "schema": schema_main,
    "conformance": conformance_main,
    "bulk": bulk_main,
    "resolve": resolve_main,
    "test": test_main,
    "fetch": fetch_main,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="OOHDI developer tools")
    parser.add_argument("command", choices=sorted(COMMANDS.keys()), help="Command to run")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments to pass to the selected command")
    args = parser.parse_args()

    command_main = COMMANDS[args.command]
    sys.argv = [f"oohdi {args.command}", *args.args]
    return command_main()


if __name__ == "__main__":
    raise SystemExit(main())
