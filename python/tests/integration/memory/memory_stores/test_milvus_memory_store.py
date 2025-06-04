# Copyright (c) Microsoft. All rights reserved.


import numpy as np
import pytest

pytest.skip(
    (
        "Temporarily disabling this test module due to import error from milvus: "
        "AttributeError: module 'marshmallow' has no attribute '__version_info__'"
    ),
    allow_module_level=True,
)

from semantic_kernel.connectors.memory.milvus import MilvusMemoryStore  # noqa: E402
from semantic_kernel.memory.memory_record import MemoryRecord  # noqa: E402

try:
    from milvus import default_server

    milvus_installed = True
except ImportError:
    milvus_installed = False

# pytestmark = pytest.mark.skipif(not milvus_installed, reason="local milvus is not installed")

# pytestmark = pytest.mark.skipif(
#     platform.system() == "Windows",
#     reason="local milvus is not officially supported on Windows",
# )
pytestmark = pytest.mark.skip(
    reason="milvus SDK and local server seem to be out of step, will fix with new integration.",
)


@pytest.fixture(scope="module")
def setup_milvus():
    default_server.cleanup()
    default_server.start()
    host = "http://127.0.0.1:" + str(default_server.listen_port)
    token = None
    yield host, token
    default_server.stop()
    default_server.cleanup()


async def test_create_and_get_collection(setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection", 2)
    result = await memory.get_collections()
    assert result == ["test_collection"]


async def test_get_collections(setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection1", 2)
    await memory.create_collection("test_collection2", 2)
    await memory.create_collection("test_collection3", 2)
    result = await memory.get_collections()
    assert len(result) == 3


async def test_delete_collection(setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection", 2)
    await memory.delete_collection("test_collection", 2)
    result = await memory.get_collections()
    assert len(result) == 0

    await memory.create_collection("test_collection", 2)
    await memory.delete_collection("TEST_COLLECTION", 2)
    result = await memory.get_collections()
    assert len(result) == 0


async def test_does_collection_exist(setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection", 2)
    result = await memory.does_collection_exist("test_collection")
    assert result is True

    result = await memory.does_collection_exist("TEST_COLLECTION")
    assert result is False


async def test_upsert_and_get(memory_record1, setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)

    await memory.create_collection("test_collection", 2)
    await memory.upsert("test_collection", memory_record1)

    result = await memory.get("test_collection", "test_id1", True)
    assert result._id == "test_id1"
    assert result._text == "sample text1"
    assert result._is_reference is False
    assert np.array_equal(result.embedding, np.array([0.5, 0.5]))
    assert result._description == "description"
    assert result._external_source_name == "external source"
    assert result._additional_metadata == "additional metadata"


async def test_upsert_and_get_with_no_embedding(memory_record1, setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection", 2)

    await memory.upsert("test_collection", memory_record1)

    result = await memory.get("test_collection", "test_id1", False)
    assert result._id == "test_id1"
    assert result._text == "sample text1"
    assert result._is_reference is False
    assert result.embedding is None
    assert result._description == "description"
    assert result._external_source_name == "external source"
    assert result._additional_metadata == "additional metadata"


async def test_upsert_and_get_batch(memory_record1, memory_record2, setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection", 2)

    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])

    result = await memory.get_batch("test_collection", ["test_id1", "test_id2"], True)
    assert len(result) == 2
    assert result[0]._id == "test_id1"
    assert result[0]._text == "sample text1"
    assert result[0]._is_reference is False
    assert np.array_equal(result[0].embedding, np.array([0.5, 0.5]))
    assert result[0]._description == "description"
    assert result[0]._external_source_name == "external source"
    assert result[0]._additional_metadata == "additional metadata"


async def test_remove(memory_record1, setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection", 2)

    await memory.upsert("test_collection", memory_record1)
    await memory.remove("test_collection", "test_id1")

    # memory.get should raise Exception if record is not found
    with pytest.raises(Exception):
        await memory.get("test_collection", "test_id1", True)


async def test_remove_batch(memory_record1, memory_record2, setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection", 2)

    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])
    await memory.remove_batch("test_collection", ["test_id1", "test_id2"])

    result = await memory.get_batch("test_collection", ["test_id1", "test_id2"], True)
    assert result == []


async def test_get_nearest_matches(memory_record1, memory_record2, setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection", 2)
    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])
    results = await memory.get_nearest_matches("test_collection", np.array([0.5, 0.5]), limit=2)
    assert len(results) == 2
    assert isinstance(results[0][0], MemoryRecord)
    assert results[0][1] == pytest.approx(0.5, abs=1e-5)


async def test_get_nearest_match(memory_record1, memory_record2, setup_milvus):
    URI, TOKEN = setup_milvus
    memory = MilvusMemoryStore(uri=URI, token=TOKEN)
    await memory.delete_collection(all=True)
    await memory.create_collection("test_collection", 2)
    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])

    result = await memory.get_nearest_match("test_collection", np.array([0.5, 0.5]))
    assert len(result) == 2
    assert isinstance(result[0], MemoryRecord)
    assert result[1] == pytest.approx(0.5, abs=1e-5)
