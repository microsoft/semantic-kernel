# Copyright (c) Microsoft. All rights reserved.


import platform
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

import numpy as np
import pytest
from pytest import fixture, mark, param

from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_store import AzureAISearchStore
from semantic_kernel.connectors.memory.qdrant.qdrant_store import QdrantStore
from semantic_kernel.connectors.memory.redis.const import RedisCollectionTypes
from semantic_kernel.connectors.memory.redis.redis_store import RedisStore
from semantic_kernel.connectors.memory.weaviate.weaviate_store import WeaviateStore
from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)

raw_record = {
    "id": "e6103c03-487f-4d7d-9c23-4723651c17f4",
    "content": "test content",
    "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
}


def record():
    return deepcopy(raw_record)


def DataModelArray(record) -> param:
    @vectorstoremodel
    @dataclass
    class MyDataModelArray:
        vector: Annotated[
            np.ndarray | None,
            VectorStoreRecordVectorField(
                index_kind="hnsw",
                dimensions=5,
                distance_function="cosine",
                property_type="float",
                serialize_function=np.ndarray.tolist,
                deserialize_function=np.array,
            ),
        ] = None
        other: str | None = None
        id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        content: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
        ] = "content1"

    record["vector"] = np.array(record["vector"])

    return "array", MyDataModelArray, None, MyDataModelArray(**record)


def DataModelList(record) -> tuple:
    @vectorstoremodel
    @dataclass
    class MyDataModelList:
        vector: Annotated[
            list[float] | None,
            VectorStoreRecordVectorField(
                index_kind="hnsw",
                dimensions=5,
                distance_function="cosine",
                property_type="float",
            ),
        ] = None
        other: str | None = None
        id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        content: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
        ] = "content1"

    return "list", MyDataModelList, None, MyDataModelList(**record)


def DataModelPandas(record) -> tuple:
    import pandas as pd

    definition = VectorStoreRecordDefinition(
        fields={
            "vector": VectorStoreRecordVectorField(
                name="vector",
                index_kind="hnsw",
                dimensions=5,
                distance_function="cosine",
                property_type="float",
            ),
            "id": VectorStoreRecordKeyField(name="id"),
            "content": VectorStoreRecordDataField(
                name="content", has_embedding=True, embedding_property_name="vector", property_type="str"
            ),
        },
        container_mode=True,
        to_dict=lambda x: x.to_dict(orient="records"),
        from_dict=lambda x, **_: pd.DataFrame(x),
    )
    df = pd.DataFrame([record])
    return "pandas", pd.DataFrame, definition, df


@fixture
def collection_details(request):
    match request.param:
        case "array":
            yield DataModelArray(record())
        case "list":
            yield DataModelList(record())
        case "pandas":
            yield DataModelPandas(record())


@fixture
def store(request):
    match request.param:
        case "redis_json":
            yield RedisStore(), {"collection_type": RedisCollectionTypes.JSON}
        case "redis_hashset":
            yield RedisStore(), {"collection_type": RedisCollectionTypes.HASHSET}
        case "azure_ai_search":
            yield AzureAISearchStore(), {}
        case "qdrant":
            yield QdrantStore(), {}
        case "qdrant_in_memory":
            yield QdrantStore(location=":memory:"), {}
        case "qdrant_grpc":
            yield QdrantStore(), {"prefer_grpc": True}
        case "weaviate_local":
            yield WeaviateStore(local_host="localhost"), {}
        case "weaviate_embedded":
            yield WeaviateStore(use_embed=True), {}


@fixture
@mark.asyncio
async def collection_and_data(store, collection_details):
    vector_store, collection_options = store
    collection_name, data_model_type, data_model_definition, data_record = collection_details
    collection = vector_store.get_collection(
        collection_name, data_model_type, data_model_definition, **collection_options
    )
    try:
        await collection.create_collection_if_not_exists()
    except Exception as exc:
        pytest.fail(f"Failed to create collection: {exc}")
    yield collection, data_record
    try:
        await collection.delete_collection()
    except Exception as exc:
        pytest.fail(f"Failed to delete collection: {exc}")


@mark.asyncio
@mark.parametrize("collection_details", ["array", "list", "pandas"], indirect=True)
@mark.parametrize(
    "store",
    [
        "redis_json",
        "redis_hashset",
        "azure_ai_search",
        "qdrant",
        "qdrant_in_memory",
        "qdrant_grpc",
        "weaviate_local",
        pytest.param(
            "weaviate_embedded",
            marks=[
                pytest.mark.skipif(
                    platform.system() == "Windows",
                    reason="Weaviate embedded is not supported on Windows: https://github.com/weaviate/weaviate/issues/3315",
                ),
                pytest.mark.xfail(reason="Weaviate embedded is an experimental feature and it's unstable"),
            ],
        ),
    ],
    indirect=True,
)
async def test_collections(collection_and_data):
    compare_record = record()
    async for collection, data_record in collection_and_data:
        print("upserting record")
        await collection.upsert(data_record)
        print("getting record")
        result = await collection.get(compare_record["id"])
        assert result is not None
        print("deleting record")
        await collection.delete(compare_record["id"])
        print("getting record again, expect None")
        result = await collection.get(compare_record["id"])
        assert result is None
