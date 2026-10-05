"""Operator commands: `python -m app.cli <command>`."""

import argparse
import json
import sys
from pathlib import Path


def export_openapi(output: Path) -> None:
    from app.main import app

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n")
    print(f"OpenAPI written to {output}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    openapi = sub.add_parser("export-openapi", help="Write the OpenAPI document to a file")
    openapi.add_argument("--output", type=Path, default=Path("../openapi/openapi.json"))

    args = parser.parse_args(argv)
    if args.command == "export-openapi":
        export_openapi(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
