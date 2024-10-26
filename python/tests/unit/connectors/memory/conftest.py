# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

from pydantic import BaseModel
from pytest import fixture

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)


@fixture
def index_kind(request) -> str:
    if hasattr(request, "param"):
        return request.param
    return "hnsw"


@fixture
def distance_function(request) -> str:
    if hasattr(request, "param"):
        return request.param
    return "cosine"


@fixture
def dataclass_vector_data_model(index_kind: str, distance_function: str) -> object:
    @vectorstoremodel
    @dataclass
    class MyDataModel:
        vector: Annotated[
            list[float] | None,
            VectorStoreRecordVectorField(
                embedding_settings={"default": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
                index_kind=index_kind,
                dimensions=1536,
                distance_function=distance_function,
                property_type="float",
            ),
        ] = None
        other: str | None = None
        id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        content: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
        ] = "content1"

    return MyDataModel


@fixture
def data_model_definition(index_kind: str, distance_function: str) -> object:
    return VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(
                has_embedding=True,
                embedding_property_name="vector",
            ),
            "vector": VectorStoreRecordVectorField(
                dimensions=3,
                index_kind=index_kind,
                distance_function=distance_function,
            ),
        }
    )


@fixture
def data_model_type(index_kind: str, distance_function: str) -> object:
    @vectorstoremodel
    class DataModelClass(BaseModel):
        content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")]
        vector: Annotated[
            list[float],
            VectorStoreRecordVectorField(
                index_kind=index_kind,
                distance_function=distance_function,
            ),
        ]
        id: Annotated[str, VectorStoreRecordKeyField()]

    return DataModelClass


@fixture
def data_model_type_with_key_as_key_field(index_kind: str, distance_function: str) -> object:
    """Data model type with key as key field."""

    @vectorstoremodel
    class DataModelClass(BaseModel):
        content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")]
        vector: Annotated[
            list[float],
            VectorStoreRecordVectorField(
                index_kind=index_kind,
                distance_function=distance_function,
            ),
        ]
        key: Annotated[str, VectorStoreRecordKeyField()]

    return DataModelClass
