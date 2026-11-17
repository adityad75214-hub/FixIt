"""Bootstrap the first FixIt platform administrator.

Run from backend after configuring the environment:
    python scripts/create_platform_admin.py
The password is prompted securely and is never stored in this script.
"""
import asyncio
import getpass
import sys
from datetime import datetime, timezone
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import settings
from app.core.security import get_password_hash


async def main() -> None:
    email = input("Platform administrator email: ").strip().lower()
    name = input("Full name: ").strip()
    password = getpass.getpass("Password (minimum 12 characters): ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    if "@" not in email or not name:
        raise SystemExit("Enter a valid email and name.")

    client = AsyncIOMotorClient(settings.MONGODB_URI)
    try:
        await client.admin.command("ping")
        db = client[settings.DATABASE_NAME]
        existing = await db.users.find_one({"email": email})
        if existing:
            raise SystemExit("An account with that email already exists; no changes were made.")
        user_id = "USR-PLATFORM-" + __import__("uuid").uuid4().hex[:10].upper()
        await db.users.insert_one({
            "_id": user_id,
            "email": email,
            "password_hash": get_password_hash(password),
            "name": name,
            "role": "platform_admin",
            "institution_id": "INST-PLATFORM",
            "department": "FixIt Platform Operations",
            "specialization": [],
            "is_active": True,
            "token_version": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        print("Platform administrator created. Sign in through the FixIt login endpoint.")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
