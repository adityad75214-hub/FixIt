import asyncio

from app.core.database import get_database
from app.seed import _insert_seed_if_missing


def test_seed_helper_never_overwrites_existing_user():
    async def scenario():
        collection = get_database().users
        original = {
            "_id": "USR-SEED-SAFETY-TEST",
            "email": "seed-safety-test@college.edu",
            "name": "Existing Account Name",
            "role": "student",
        }
        await collection.insert_one(original)
        try:
            inserted = await _insert_seed_if_missing(
                collection,
                {
                    "_id": original["_id"],
                    "email": original["email"],
                    "name": "Demo Seed Name",
                    "role": "admin",
                },
                ("_id", "email"),
            )
            stored = await collection.find_one({"_id": original["_id"]})
            return inserted, stored
        finally:
            await collection.delete_one({"_id": original["_id"]})

    inserted, stored = asyncio.run(scenario())
    assert inserted is False
    assert stored["name"] == "Existing Account Name"
    assert stored["role"] == "student"
