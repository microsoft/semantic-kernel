# Copyright (c) Microsoft. All rights reserved.

import os
import time

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.memory.astradb import AstraDBMemoryStore
from semantic_kernel.connectors.memory.astradb.astradb_settings import AstraDBSettings
from tests.utils import retry

astradb_installed: bool
try:
    if os.environ["ASTRADB_INTEGRATION_TEST"]:
        astradb_installed = True
except KeyError:
    astradb_installed = False


pytestmark = pytest.mark.skipif(not astradb_installed, reason="astradb is not installed")


@pytest.fixture(autouse=True, scope="module")
def slow_down_tests():
    yield
    time.sleep(3)


@pytest.fixture(scope="session")
def get_astradb_config():
    try:
        astradb_settings = AstraDBSettings()
        app_token = astradb_settings.app_token.get_secret_value()
        db_id = astradb_settings.db_id
        region = astradb_settings.region
        keyspace = astradb_settings.keyspace
        return app_token, db_id, region, keyspace
    except ValidationError:
        pytest.skip("AsbtraDBSettings not found in env vars.")


async def test_constructor(get_astradb_config):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")
    result = await retry(lambda: memory.get_collections())

    assert result is not None


async def test_create_and_get_collection(get_astradb_config):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    result = await retry(lambda: memory.does_collection_exist("test_collection"))
    assert result is not None
    assert result is True


async def test_get_collections(get_astradb_config):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    result = await retry(lambda: memory.get_collections())
    assert "test_collection" in result


async def test_delete_collection(get_astradb_config):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    await retry(lambda: memory.delete_collection("test_collection"))
    result = await retry(lambda: memory.get_collections())
    assert "test_collection" not in result


async def test_does_collection_exist(get_astradb_config):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    result = await retry(lambda: memory.does_collection_exist("test_collection"))
    assert result is True


async def test_upsert_and_get(get_astradb_config, memory_record1):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    await retry(lambda: memory.upsert("test_collection", memory_record1))

    result = await retry(
        lambda: memory.get(
            "test_collection",
            memory_record1._id,
            with_embedding=True,
        )
    )

    assert result is not None
    assert result._id == memory_record1._id
    assert result._description == memory_record1._description
    assert result._text == memory_record1._text
    assert result.embedding is not None


async def test_upsert_batch_and_get_batch(get_astradb_config, memory_record1, memory_record2):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    await retry(lambda: memory.upsert_batch("test_collection", [memory_record1, memory_record2]))

    results = await retry(
        lambda: memory.get_batch(
            "test_collection",
            [memory_record1._id, memory_record2._id],
            with_embeddings=True,
        )
    )

    assert len(results) >= 2
    assert results[0]._id in [memory_record1._id, memory_record2._id]
    assert results[1]._id in [memory_record1._id, memory_record2._id]


async def test_remove(get_astradb_config, memory_record1):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    await retry(lambda: memory.upsert("test_collection", memory_record1))
    await retry(lambda: memory.remove("test_collection", memory_record1._id))

    with pytest.raises(KeyError):
        _ = await memory.get("test_collection", memory_record1._id, with_embedding=True)


async def test_remove_batch(get_astradb_config, memory_record1, memory_record2):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    await retry(lambda: memory.upsert_batch("test_collection", [memory_record1, memory_record2]))
    await retry(lambda: memory.remove_batch("test_collection", [memory_record1._id, memory_record2._id]))

    with pytest.raises(KeyError):
        _ = await memory.get("test_collection", memory_record1._id, with_embedding=True)

    with pytest.raises(KeyError):
        _ = await memory.get("test_collection", memory_record2._id, with_embedding=True)


async def test_get_nearest_match(get_astradb_config, memory_record1, memory_record2):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    await retry(lambda: memory.upsert_batch("test_collection", [memory_record1, memory_record2]))

    test_embedding = memory_record1.embedding
    test_embedding[0] = test_embedding[0] + 0.01

    result = await retry(
        lambda: memory.get_nearest_match(
            "test_collection",
            test_embedding,
            min_relevance_score=0.0,
            with_embedding=True,
        )
    )

    assert result is not None
    assert result[0]._id == memory_record1._id


async def test_get_nearest_matches(get_astradb_config, memory_record1, memory_record2, memory_record3):
    app_token, db_id, region, keyspace = get_astradb_config
    memory = AstraDBMemoryStore(app_token, db_id, region, keyspace, 2, "cosine_similarity")

    await retry(lambda: memory.create_collection("test_collection"))
    await retry(lambda: memory.upsert_batch("test_collection", [memory_record1, memory_record2, memory_record3]))

    test_embedding = memory_record2.embedding
    test_embedding[0] = test_embedding[0] + 0.025

    result = await retry(
        lambda: memory.get_nearest_matches(
            "test_collection",
            test_embedding,
            limit=2,
            min_relevance_score=0.0,
            with_embeddings=True,
        )
    )

    assert len(result) == 2
    assert result[0][0]._id in [memory_record3._id, memory_record2._id]
    assert result[1][0]._id in [memory_record3._id, memory_record2._id]
