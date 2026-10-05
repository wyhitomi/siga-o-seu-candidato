"""Operator commands: `python -m app.cli <command>`."""

import argparse
import asyncio
import json
import sys
from pathlib import Path


def export_openapi(output: Path) -> None:
    from app.main import app

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n")
    print(f"OpenAPI written to {output}")


async def create_admin(email: str) -> None:
    from sqlalchemy import select

    from app.core.db import SessionLocal
    from app.modules.auth.models import AdminUser

    email = email.strip().lower()
    async with SessionLocal() as session:
        admin = await session.scalar(select(AdminUser).where(AdminUser.email == email))
        if admin is None:
            session.add(AdminUser(email=email))
            print(f"Admin {email} created")
        else:
            admin.is_active = True
            print(f"Admin {email} already exists; ensured it is active")
        await session.commit()


async def deactivate_admin(email: str) -> None:
    from sqlalchemy import update

    from app.core.db import SessionLocal
    from app.modules.auth.models import AdminUser

    async with SessionLocal() as session:
        result = await session.execute(
            update(AdminUser)
            .where(AdminUser.email == email.strip().lower())
            .values(is_active=False)
        )
        await session.commit()
    print(f"Admin {email} deactivated" if result.rowcount else f"Admin {email} not found")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    openapi = sub.add_parser("export-openapi", help="Write the OpenAPI document to a file")
    openapi.add_argument("--output", type=Path, default=Path("../openapi/openapi.json"))

    for name, help_text in [
        ("create-admin", "Create (or reactivate) an admin user"),
        ("deactivate-admin", "Deactivate an admin user"),
    ]:
        sub.add_parser(name, help=help_text).add_argument("email")

    args = parser.parse_args(argv)
    if args.command == "export-openapi":
        export_openapi(args.output)
    elif args.command == "create-admin":
        asyncio.run(create_admin(args.email))
    elif args.command == "deactivate-admin":
        asyncio.run(deactivate_admin(args.email))
    return 0


if __name__ == "__main__":
    sys.exit(main())
