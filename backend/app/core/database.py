import asyncio
import logging
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger("fixit.database")

class MockAsyncCursor:
    def __init__(self, sync_cursor):
        self.sync_cursor = sync_cursor

    def sort(self, *args, **kwargs):
        self.sync_cursor = self.sync_cursor.sort(*args, **kwargs)
        return self

    def skip(self, count: int):
        self.sync_cursor = self.sync_cursor.skip(count)
        return self

    def limit(self, count: int):
        self.sync_cursor = self.sync_cursor.limit(count)
        return self

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        docs = list(self.sync_cursor)
        if length is not None:
            return docs[:length]
        return docs

    def __aiter__(self):
        self._iter = iter(list(self.sync_cursor))
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration

class MockAsyncCollection:
    def __init__(self, sync_col):
        self.sync_col = sync_col

    async def find_one(self, filter: Optional[Dict[str, Any]] = None, *args, **kwargs) -> Optional[Dict[str, Any]]:
        return self.sync_col.find_one(filter, *args, **kwargs)

    def find(self, filter: Optional[Dict[str, Any]] = None, *args, **kwargs) -> MockAsyncCursor:
        cursor = self.sync_col.find(filter, *args, **kwargs)
        return MockAsyncCursor(cursor)

    def aggregate(self, pipeline: List[Dict[str, Any]], *args, **kwargs) -> MockAsyncCursor:
        return MockAsyncCursor(self.sync_col.aggregate(pipeline, *args, **kwargs))

    async def insert_one(self, document: Dict[str, Any], *args, **kwargs):
        return self.sync_col.insert_one(document, *args, **kwargs)

    async def insert_many(self, documents: List[Dict[str, Any]], *args, **kwargs):
        return self.sync_col.insert_many(documents, *args, **kwargs)

    async def update_one(self, filter: Dict[str, Any], update: Dict[str, Any], *args, **kwargs):
        return self.sync_col.update_one(filter, update, *args, **kwargs)

    async def update_many(self, filter: Dict[str, Any], update: Dict[str, Any], *args, **kwargs):
        return self.sync_col.update_many(filter, update, *args, **kwargs)

    async def delete_one(self, filter: Dict[str, Any], *args, **kwargs):
        return self.sync_col.delete_one(filter, *args, **kwargs)

    async def delete_many(self, filter: Dict[str, Any], *args, **kwargs):
        return self.sync_col.delete_many(filter, *args, **kwargs)

    async def count_documents(self, filter: Dict[str, Any], *args, **kwargs) -> int:
        return self.sync_col.count_documents(filter, *args, **kwargs)

    async def find_one_and_update(self, filter: Dict[str, Any], update: Dict[str, Any], *args, **kwargs):
        return self.sync_col.find_one_and_update(filter, update, *args, **kwargs)

    async def create_index(self, keys, **kwargs):
        return self.sync_col.create_index(keys, **kwargs)

    async def drop(self):
        return self.sync_col.drop()

class MockAsyncDatabase:
    def __init__(self, sync_db):
        self.sync_db = sync_db

    def __getitem__(self, name: str) -> MockAsyncCollection:
        return MockAsyncCollection(self.sync_db[name])

    def __getattr__(self, name: str) -> MockAsyncCollection:
        return self[name]

    async def command(self, *args, **kwargs):
        return {"ok": 1.0}

class DatabaseManager:
    client = None
    db = None
    is_mock = False

db_manager = DatabaseManager()

async def connect_to_mongo():
    if db_manager.is_mock and db_manager.db is not None:
        # Test harnesses may inject the mock database before application startup.
        # Indexes must still be initialized or uniqueness guarantees silently disappear.
        await init_indexes(db_manager.db)
        return

    try:
        # First attempt connecting to real MongoDB
        client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
        # Verify connection by pinging
        await client.admin.command('ping')
        db_manager.client = client
        db_manager.db = client[settings.DATABASE_NAME]
        db_manager.is_mock = False
        logger.info("Connected successfully to the configured MongoDB database.")
    except Exception as exc:
        # Never log the MongoDB URI or raw driver exception: both may contain credentials.
        if not settings.FALLBACK_TO_MOCK_DB or settings.is_production:
            logger.error("MongoDB connection failed (%s); refusing to start without the persistent database.", type(exc).__name__)
            raise RuntimeError("MongoDB connection failed; verify the database service and credentials.") from None
        logger.warning("MongoDB unavailable (%s); using the explicitly enabled development-only in-memory database.", type(exc).__name__)
        try:
            import mongomock
        except ImportError:
            logger.error("Development mock fallback requested, but mongomock is not installed.")
            raise RuntimeError("Install backend/requirements-dev.txt to use the development mock database.") from None
        mock_client = mongomock.MongoClient()
        mock_db = mock_client[settings.DATABASE_NAME]
        db_manager.client = mock_client
        db_manager.db = MockAsyncDatabase(mock_db)
        db_manager.is_mock = True

    # Index failures are startup failures: silently skipping them can break uniqueness/security assumptions.
    await init_indexes(db_manager.db)

async def close_mongo_connection():
    if db_manager.client:
        if not db_manager.is_mock:
            db_manager.client.close()
        logger.info("MongoDB connection closed.")

async def init_indexes(db):
    try:
        # Core collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("role")

        await db.tickets.create_index("ticket_id", unique=True)
        await db.tickets.create_index("status")
        await db.tickets.create_index("priority")
        await db.tickets.create_index("category")
        await db.tickets.create_index("created_by")
        await db.tickets.create_index("assigned_to")
        await db.tickets.create_index("created_at")
        await db.tickets.create_index("building")
        await db.tickets.create_index("floor")
        await db.tickets.create_index("room")

        await db.comments.create_index("ticket_id")
        await db.comments.create_index("is_internal")

        await db.notifications.create_index([("user_id", 1), ("is_read", 1)])
        await db.audit_logs.create_index("timestamp")

        # Campus hierarchy indexes
        await db.campuses.create_index("code", unique=True)
        await db.buildings.create_index([("campus_id", 1), ("name", 1)], unique=True)
        await db.buildings.create_index([("campus_id", 1), ("code", 1)], unique=True)
        await db.floors.create_index([("building_id", 1), ("floor_name", 1)], unique=True)
        await db.rooms.create_index([("floor_id", 1), ("room_number", 1)], unique=True)

        # Supporting entity indexes
        await db.departments.create_index("code", unique=True)
        await db.categories.create_index("name", unique=True)
        await db.sla_policies.create_index("priority", unique=True)
        await db.feedback.create_index("ticket_id", unique=True)
        await db.knowledge_base.create_index("category")
        await db.knowledge_base_votes.create_index([("article_id", 1), ("user_id", 1)], unique=True)
        await db.incidents.create_index("status")
        await db.feature_requests.create_index([("created_by.id", 1), ("created_at", -1)])
        await db.counters.create_index("name", unique=True)

        await db.refresh_tokens.create_index("token_hash", unique=True)
        await db.refresh_tokens.create_index("user_id")
        await db.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)
        await db.login_rate_limits.create_index("window_expires_at", expireAfterSeconds=0)
        logger.info("Database indexes verified for all collections.")
    except Exception:
        logger.exception("Database index initialization failed.")
        raise

def get_database():
    if db_manager.db is None:
        raise RuntimeError("Database is not initialized. Application startup has not completed.")
    return db_manager.db
