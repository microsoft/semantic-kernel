# Copyright (c) Microsoft. All rights reserved.


from dataclasses import field
from typing import Annotated, Any
from uuid import uuid4

from pydantic import BaseModel
from pytest import fixture

from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)


@fixture
def data_record() -> dict[str, Any]:
    return {
        "id": "e6103c03-487f-4d7d-9c23-4723651c17f4",
        "description": "This is a test record",
        "product_type": "test",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    }


@fixture
def data_model_type() -> type:
    @vectorstoremodel
    class TestDataModelType(BaseModel):
        vector: Annotated[
            list[float] | None,
            VectorStoreRecordVectorField(
                index_kind="flat",
                dimensions=5,
                distance_function="cosine_similarity",
                property_type="float",
            ),
        ] = None
        id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        product_type: Annotated[str, VectorStoreRecordDataField()] = "N/A"
        description: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
        ] = "N/A"

    return TestDataModelType


@fixture
def data_record_with_key_as_key_field() -> dict[str, Any]:
    return {
        "key": "e6103c03-487f-4d7d-9c23-4723651c17f4",
        "description": "This is a test record",
        "product_type": "test",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    }


@fixture
def data_model_type_with_key_as_key_field() -> type:
    @vectorstoremodel
    class TestDataModelType(BaseModel):
        vector: Annotated[
            list[float] | None,
            VectorStoreRecordVectorField(
                index_kind="flat",
                dimensions=5,
                distance_function="cosine_similarity",
                property_type="float",
            ),
        ] = None
        key: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        product_type: Annotated[str, VectorStoreRecordDataField()] = "N/A"
        description: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
        ] = "N/A"

    return TestDataModelType
