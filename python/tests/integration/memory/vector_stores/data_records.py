# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

import numpy as np
import pandas as pd

from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)

RAW_RECORD_LIST = {
    "id": "e6103c03-487f-4d7d-9c23-4723651c17f4",
    "content": "test content",
    "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
}


RAW_RECORD_ARRAY = {
    "id": "e6103c03-487f-4d7d-9c23-4723651c17f4",
    "content": "test content",
    "vector": np.array([0.1, 0.2, 0.3, 0.4, 0.5]),
}


PANDAS_RECORD_DEFINITION = VectorStoreRecordDefinition(
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


@vectorstoremodel
@dataclass
class TestDataModelArray:
    """A data model where the vector is a numpy array."""

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


@vectorstoremodel
@dataclass
class TestDataModelList:
    """A data model where the vector is a list."""

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
