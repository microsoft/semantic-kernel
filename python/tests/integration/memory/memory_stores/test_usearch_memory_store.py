# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime

import numpy as np
import pytest

from semantic_kernel.connectors.memory.usearch import USearchMemoryStore
from semantic_kernel.exceptions import ServiceResourceNotFoundError
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import pyarrow  # noqa: F401

    pyarrow_installed = True
except ImportError:
    pyarrow_installed = False

try:
    import usearch  # noqa: F401

    usearch_installed = True
except ImportError:
    usearch_installed = False


pytestmark = [
    pytest.mark.skipif(not usearch_installed, reason="`USearch` is not installed"),
    pytest.mark.skipif(
        not pyarrow_installed,
        reason="`USearch` dependency `pyarrow` is not installed",
    ),
]


@pytest.fixture
def memory_record1():
    return MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=np.array([0.5, 0.5], dtype=np.float32),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


@pytest.fixture
def memory_record1_with_collision():
    return MemoryRecord(
        id="test_id1",
        text="sample text2",
        is_reference=False,
        embedding=np.array([1, 0.6], dtype=np.float32),
        description="description_2",
        additional_metadata="additional metadata_2",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


@pytest.fixture
def memory_record2():
    return MemoryRecord(
        id="test_id2",
        text="sample text2",
        is_reference=False,
        embedding=np.array([0.25, 0.75], dtype=np.float32),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


@pytest.fixture
def memory_record3():
    return MemoryRecord(
        id="test_id3",
        text="sample text3",
        is_reference=False,
        embedding=np.array([0.25, 0.80], dtype=np.float32),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )


def gen_memory_records(count: int, ndim: int, start_index: int = 0) -> list[MemoryRecord]:
    return [
        MemoryRecord(
            is_reference=False,
            text="random text",
            additional_metadata="additional",
            external_source_name="external_name",
            description="something descriptive",
            timestamp=datetime.datetime.now(),
            id=f":{start_index + index}",
            embedding=np.random.uniform(0, 0.3, (ndim)).astype(np.float32),
        )
        for index in range(count)
    ]


def compare_memory_records(record1: MemoryRecord, record2: MemoryRecord, with_embedding: bool):
    """Compare two MemoryRecord instances and assert they are the same."""
    assert record1._key == record2._key, f"_key mismatch: {record1._key} != {record2._key}"
    assert (
        record1._timestamp == record2._timestamp
    ), f"_timestamp mismatch: {record1._timestamp} != {record2._timestamp}"
    assert (
        record1._is_reference == record2._is_reference
    ), f"_is_reference mismatch: {record1._is_reference} != {record2._is_reference}"
    assert (
        record1._external_source_name == record2._external_source_name
    ), f"_external_source_name mismatch: {record1._external_source_name} != {record2._external_source_name}"
    assert record1._id == record2._id, f"_id mismatch: {record1._id} != {record2._id}"
    assert (
        record1._description == record2._description
    ), f"_description mismatch: {record1._description} != {record2._description}"
    assert record1._text == record2._text, f"_text mismatch: {record1._text} != {record2._text}"
    assert (
        record1._additional_metadata == record2._additional_metadata
    ), f"_additional_metadata mismatch: {record1._additional_metadata} != {record2._additional_metadata}"
    if with_embedding is True:
        assert record1._embedding == pytest.approx(record2._embedding, abs=1e-2), "_embedding arrays are not equal"


@pytest.mark.asyncio
async def test_create_and_get_collection():
    memory = USearchMemoryStore()

    await memory.create_collection("test_collection1")
    await memory.create_collection("test_collection2")
    await memory.create_collection("test_collection3")
    result = await memory.get_collections()

    assert len(result) == 3
    assert result == ["test_collection1", "test_collection2", "test_collection3"]


@pytest.mark.asyncio
async def test_delete_collection():
    memory = USearchMemoryStore()

    await memory.create_collection("test_collection")
    await memory.delete_collection("test_collection")
    result = await memory.get_collections()
    assert len(result) == 0

    await memory.create_collection("test_collection")
    await memory.delete_collection("TEST_COLLECTION")
    result = await memory.get_collections()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_does_collection_exist():
    memory = USearchMemoryStore()
    await memory.create_collection("test_collection")
    result = await memory.does_collection_exist("test_collection")
    assert result is True

    result = await memory.does_collection_exist("TEST_COLLECTION")
    assert result is True


@pytest.mark.asyncio
async def test_upsert_and_get_with_no_embedding(memory_record1: MemoryRecord):
    memory = USearchMemoryStore()
    await memory.create_collection("test_collection", ndim=2)
    await memory.upsert("test_collection", memory_record1)

    result = await memory.get("test_collection", "test_id1", False)
    compare_memory_records(result, memory_record1, False)


@pytest.mark.asyncio
async def test_upsert_and_get_with_embedding(memory_record1: MemoryRecord):
    memory = USearchMemoryStore()
    await memory.create_collection("test_collection", ndim=2)
    await memory.upsert("test_collection", memory_record1)

    result = await memory.get("test_collection", "test_id1", True)
    compare_memory_records(result, memory_record1, True)


@pytest.mark.asyncio
async def test_upsert_and_get_batch(memory_record1: MemoryRecord, memory_record2: MemoryRecord):
    memory = USearchMemoryStore()
    await memory.create_collection("test_collection", ndim=memory_record1.embedding.shape[0])

    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])

    result = await memory.get_batch("test_collection", ["test_id1", "test_id2"], True)
    assert len(result) == 2

    compare_memory_records(result[0], memory_record1, True)
    compare_memory_records(result[1], memory_record2, True)


@pytest.mark.asyncio
async def test_remove(memory_record1):
    memory = USearchMemoryStore()
    await memory.create_collection("test_collection", ndim=memory_record1.embedding.shape[0])

    await memory.upsert("test_collection", memory_record1)
    await memory.remove("test_collection", "test_id1")

    # memory.get should raise Exception if record is not found
    with pytest.raises(ServiceResourceNotFoundError):
        await memory.get("test_collection", "test_id1", True)


@pytest.mark.asyncio
async def test_remove_batch(memory_record1: MemoryRecord, memory_record2: MemoryRecord):
    memory = USearchMemoryStore()
    await memory.create_collection("test_collection", ndim=memory_record1.embedding.shape[0])

    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])
    await memory.remove_batch("test_collection", ["test_id1", "test_id2"])

    result = await memory.get_batch("test_collection", ["test_id1", "test_id2"], True)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_nearest_match(memory_record1: MemoryRecord, memory_record2: MemoryRecord):
    memory = USearchMemoryStore()

    collection_name = "test_collection"
    await memory.create_collection(collection_name, ndim=memory_record1.embedding.shape[0], metric="cos")

    await memory.upsert_batch(collection_name, [memory_record1, memory_record2])

    result = await memory.get_nearest_match(collection_name, np.array([0.5, 0.5]), exact=True)

    assert len(result) == 2
    assert isinstance(result[0], MemoryRecord)
    assert result[1] == pytest.approx(1, abs=1e-2)


@pytest.mark.asyncio
async def test_get_nearest_matches(memory_record1: MemoryRecord, memory_record2: MemoryRecord):
    memory = USearchMemoryStore()

    collection_name = "test_collection"
    await memory.create_collection(collection_name, ndim=memory_record1.embedding.shape[0], metric="cos")

    await memory.upsert_batch(collection_name, [memory_record1, memory_record2])

    results = await memory.get_nearest_matches(collection_name, np.array([0.5, 0.5]), limit=2, exact=True)

    assert len(results) == 2
    assert isinstance(results[0][0], MemoryRecord)
    assert results[0][1] == pytest.approx(1, abs=1e-2)
    assert results[1][1] == pytest.approx(0.90450, abs=1e-2)


@pytest.mark.asyncio
async def test_create_and_save_collection(tmpdir, memory_record1, memory_record2, memory_record3):
    memory = USearchMemoryStore(tmpdir)

    await memory.create_collection("test_collection1", ndim=2)
    await memory.create_collection("test_collection2", ndim=2)
    await memory.create_collection("test_collection3", ndim=2)
    await memory.upsert_batch("test_collection1", [memory_record1, memory_record2])
    await memory.upsert_batch("test_collection2", [memory_record2, memory_record3])
    await memory.upsert_batch("test_collection3", [memory_record1, memory_record3])
    await memory.close()

    assert (tmpdir / "test_collection1.parquet").exists()
    assert (tmpdir / "test_collection1.usearch").exists()
    assert (tmpdir / "test_collection2.parquet").exists()
    assert (tmpdir / "test_collection2.usearch").exists()
    assert (tmpdir / "test_collection3.parquet").exists()
    assert (tmpdir / "test_collection3.usearch").exists()

    memory = USearchMemoryStore(tmpdir)
    result = await memory.get_collections()
    assert len(result) == 3
    assert set(result) == {"test_collection1", "test_collection2", "test_collection3"}
    await memory.delete_collection("test_collection1")
    await memory.delete_collection("test_collection3")
    await memory.close()

    memory = USearchMemoryStore(tmpdir)
    result = await memory.get_collections()
    assert len(result) == 1
    assert set(result) == {"test_collection2"}
    await memory.delete_collection("test_collection2")
    await memory.close()

    memory = USearchMemoryStore(tmpdir)
    result = await memory.get_collections()
    assert len(result) == 0


@pytest.mark.asyncio
async def test_upsert_and_get_with_embedding_with_persist(
    tmpdir, memory_record1: MemoryRecord, memory_record1_with_collision: MemoryRecord
):
    memory = USearchMemoryStore(tmpdir)
    assert len(await memory.get_collections()) == 0
    await memory.create_collection("test_collection", ndim=2)
    await memory.upsert("test_collection", memory_record1)
    await memory.close()

    memory = USearchMemoryStore(tmpdir)
    assert len(await memory.get_collections()) == 1
    result = await memory.get("test_collection", "test_id1", True)
    compare_memory_records(result, memory_record1, True)

    await memory.upsert("test_collection", memory_record1_with_collision)
    result = await memory.get("test_collection", "test_id1", True)
    compare_memory_records(result, memory_record1_with_collision, True)
    await memory.close()

    memory = USearchMemoryStore(tmpdir)
    assert len(await memory.get_collections()) == 1
    result = await memory.get("test_collection", "test_id1", True)
    compare_memory_records(result, memory_record1_with_collision, True)


@pytest.mark.asyncio
async def test_remove_get(memory_record1: MemoryRecord, memory_record2: MemoryRecord):
    memory = USearchMemoryStore()
    await memory.create_collection("test_collection", ndim=memory_record1.embedding.shape[0])

    await memory.upsert_batch("test_collection", [memory_record1, memory_record2])
    await memory.remove("test_collection", "test_id1")

    result = await memory.get_batch("test_collection", ["test_id1", "test_id2"], True)
    assert len(result) == 1
    compare_memory_records(result[0], memory_record2, True)
