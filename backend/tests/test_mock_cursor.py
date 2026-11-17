import asyncio

import mongomock

from app.core.database import MockAsyncCursor


def test_mock_cursor_async_iteration_ends_normally():
    cursor = MockAsyncCursor(mongomock.MongoClient().db.items.find({}))
    cursor.sync_cursor.collection.insert_many([{"value": 1}, {"value": 2}])

    async def collect():
        return [item async for item in cursor]

    assert [item["value"] for item in asyncio.run(collect())] == [1, 2]


def test_empty_mock_cursor_async_iteration_returns_empty_list():
    cursor = MockAsyncCursor(mongomock.MongoClient().db.items.find({}))

    async def collect():
        return [item async for item in cursor]

    assert asyncio.run(collect()) == []
