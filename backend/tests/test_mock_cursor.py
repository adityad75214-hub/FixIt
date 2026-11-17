import asyncio

import mongomock

from app.core.database import MockAsyncCursor


def test_mock_cursor_async_iteration_ends_normally():
    collection = mongomock.MongoClient().db.items
    collection.insert_many([{"value": 1}, {"value": 2}])
    cursor = MockAsyncCursor(collection.find({}))

    async def collect():
        return [item async for item in cursor]

    assert [item["value"] for item in asyncio.run(collect())] == [1, 2]


def test_empty_mock_cursor_async_iteration_returns_empty_list():
    collection = mongomock.MongoClient().db.items
    cursor = MockAsyncCursor(collection.find({}))

    async def collect():
        return [item async for item in cursor]

    assert asyncio.run(collect()) == []
