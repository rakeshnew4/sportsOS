"""One-time bootstrap for the first superadmin account.

There is no public signup for admin accounts by design — a superadmin creates
every other admin/venue-owner account through the /admin/accounts API (see the
superadmin screen in the web app). This script exists only to create that very
first superadmin, since nothing else can.

Run inside the backend container:

    docker compose exec backend python scripts/create_superadmin.py --email you@example.com --phone +911234567890

Prompts for a password interactively (not passed as an arg, so it doesn't end
up in shell history). If the email already exists, promotes that account to
superadmin instead of creating a new one.
"""

import argparse
import getpass

from app.core.database import SessionLocal
from app.core.passwords import hash_password
from app.db.orm import User


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--phone", required=True)
    parser.add_argument("--display-name", default="Superadmin")
    args = parser.parse_args()

    password = getpass.getpass("Password for superadmin: ")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords did not match")

    db = SessionLocal()
    try:
        import uuid

        user = db.query(User).filter(User.email == args.email.lower()).first()
        if user:
            user.password_hash = hash_password(password)
            user.is_superadmin = True
            db.commit()
            print(f"Promoted existing account {user.uid} ({user.email}) to superadmin.")
            return

        user = User(
            uid=uuid.uuid4().hex,
            display_name=args.display_name,
            phone=args.phone,
            is_player=False,
            email=args.email.lower(),
            password_hash=hash_password(password),
            is_superadmin=True,
        )
        db.add(user)
        db.commit()
        print(f"Created superadmin {user.uid} ({user.email}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
