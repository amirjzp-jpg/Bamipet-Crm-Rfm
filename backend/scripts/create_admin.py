"""Bootstrap the first admin account (build plan Part 8) — idempotent.

    BOOTSTRAP_ADMIN_USERNAME=... BOOTSTRAP_ADMIN_PASSWORD=... \
        python -m scripts.create_admin

Never hardcodes a password; refuses to run without both env vars. If the
user already exists, resets its password and ensures the admin role (so a
forgotten admin password is recoverable from the server, by design).
"""
from __future__ import annotations

import sys

from sqlalchemy import select

from app.auth import hash_password
from app.config import get_settings
from app.database import SessionLocal
from app.models import User


def main() -> int:
    settings = get_settings()
    username = settings.BOOTSTRAP_ADMIN_USERNAME
    password = settings.BOOTSTRAP_ADMIN_PASSWORD
    if not username or not password:
        print("Set BOOTSTRAP_ADMIN_USERNAME and BOOTSTRAP_ADMIN_PASSWORD (env or .env).", file=sys.stderr)
        return 1
    if len(password) < 8:
        print("Admin password must be at least 8 characters.", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            db.add(User(username=username, password_hash=hash_password(password), role="admin"))
            print(f"Created admin user '{username}'.")
        else:
            user.password_hash = hash_password(password)
            user.role = "admin"
            print(f"Reset password for existing user '{username}' and ensured admin role.")
        db.commit()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
