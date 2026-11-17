import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.core.security import get_password_hash


async def bootstrap_admin():
    """Create the first admin from backend/.env or the process environment.

    Existing accounts are never promoted, overwritten, or reset by this command.
    """
    env_file = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_file, override=False)

    admin_email = (os.getenv("FIRST_ADMIN_EMAIL") or "").strip().lower()
    admin_password = os.getenv("FIRST_ADMIN_PASSWORD") or ""
    admin_name = (os.getenv("FIRST_ADMIN_NAME") or "System Administrator").strip()

    if not admin_email or not admin_password:
        raise RuntimeError(
            f"FIRST_ADMIN_EMAIL and FIRST_ADMIN_PASSWORD must be set in {env_file} "
            "or in the process environment; no default admin credentials are permitted."
        )
    if len(admin_password) < 12:
        raise RuntimeError("FIRST_ADMIN_PASSWORD must contain at least 12 characters.")

    print(f"[*] Bootstrapping admin account for: {admin_email}")
    await connect_to_mongo()
    try:
        db = get_database()
        existing = await db.users.find_one({"email": admin_email})
        if existing:
            if existing.get("role") != "admin":
                raise RuntimeError(
                    "The configured bootstrap email already belongs to a non-admin account. "
                    "Choose a dedicated admin email; this script will not elevate an existing user."
                )
            print(f"[!] Admin account {admin_email} already exists; leaving its credentials and privileges unchanged.")
            return

        existing_admin = await db.users.find_one({"role": "admin"})
        if existing_admin:
            print("[!] An administrator already exists. Use the admin user-management screen to add another administrator.")
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        admin_doc = {
            "_id": f"USR-ADMIN-{uuid.uuid4().hex[:10].upper()}",
            "email": admin_email,
            "password_hash": get_password_hash(admin_password),
            "name": admin_name,
            "role": "admin",
            "department": "IT Operations",
            "phone": "",
            "identifier": "",
            "specialization": ["Administration", "Security"],
            "is_active": True,
            "token_version": 0,
            "created_at": now_iso,
        }
        await db.users.insert_one(admin_doc)
        print(f"[OK] Successfully bootstrapped new system admin: {admin_email}")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(bootstrap_admin())
