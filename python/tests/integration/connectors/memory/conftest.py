# Copyright (c) Microsoft. All rights reserved.


from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any
from uuid import uuid4

import numpy as np
from pytest import fixture

from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_model_definition import (
    VectorStoreRecordDefinition,
)
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.memory.memory_record import MemoryRecord

raw_record = {
    "id": "testid",
    "content": "test content",
    "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
}


@fixture
def record():
    return deepcopy(raw_record)


def DataModelArray(
    record,
) -> tuple[type | None, VectorStoreRecordDefinition | None, Any]:
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
        id: Annotated[str, VectorStoreRecordKeyField()] = field(
            default_factory=lambda: str(uuid4())
        )
        content: Annotated[
            str,
            VectorStoreRecordDataField(
                has_embedding=True,
                embedding_property_name="vector",
                property_type="str",
            ),
        ] = "content1"

    record["vector"] = np.array(record["vector"])

    return MyDataModelArray, None, MyDataModelArray(**record)


def DataModelList(
    record,
) -> tuple[type | None, VectorStoreRecordDefinition | None, Any]:
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
        id: Annotated[str, VectorStoreRecordKeyField()] = field(
            default_factory=lambda: str(uuid4())
        )
        content: Annotated[
            str,
            VectorStoreRecordDataField(
                has_embedding=True,
                embedding_property_name="vector",
                property_type="str",
            ),
        ] = "content1"

    return MyDataModelList, None, MyDataModelList(**record)


def DataModelPandas(
    record,
) -> tuple[type | None, VectorStoreRecordDefinition | None, Any]:
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
                name="content",
                has_embedding=True,
                embedding_property_name="vector",
                property_type="str",
            ),
        },
        container_mode=True,
    )
    df = pd.DataFrame([record])
    return None, definition, df


@fixture(scope="module")
def models(record):
    return [DataModelArray(record), DataModelList(record), DataModelPandas(record)]


@fixture(scope="module")
def memory_record1():
    return MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=np.array([0.5, 0.5]),
        description="description",
        external_source_name="external source",
        additional_metadata="additional metadata",
        timestamp=datetime.now(),
    )


@fixture(scope="module")
def memory_record2():
    return MemoryRecord(
        id="test_id2",
        text="sample text2",
        is_reference=False,
        embedding=np.array([0.25, 0.75]),
        description="description",
        external_source_name="external source",
        additional_metadata="additional metadata",
        timestamp=datetime.now(),
    )


@fixture(scope="module")
def memory_record3():
    return MemoryRecord(
        id="test_id3",
        text="sample text3",
        is_reference=False,
        embedding=np.array([0.25, 0.80]),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp=datetime.now(),
    )
