# Copyright (c) Microsoft. All rights reserved.


import ast
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated, Any

from pandas import DataFrame
from pydantic import BaseModel, Field
from pytest import fixture

from semantic_kernel.data import (
    KernelSearchResults,
    VectorSearch,
    VectorSearchResult,
    VectorStoreRecordCollection,
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)
from semantic_kernel.kernel_types import OptionalOneOrMany


@fixture
def DictVectorStoreRecordCollection() -> type[VectorSearch]:
    class DictVectorStoreRecordCollection(
        VectorStoreRecordCollection[str, Any],
        VectorSearch[str, Any],
    ):
        inner_storage: dict[str, Any] = Field(default_factory=dict)

        async def _inner_delete(self, keys: Sequence[str], **kwargs: Any) -> None:
            for key in keys:
                self.inner_storage.pop(key, None)

        async def _inner_get(self, keys: Sequence[str], **kwargs: Any) -> Any | Sequence[Any] | None:
            return [self.inner_storage[key] for key in keys if key in self.inner_storage]

        async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[str]:
            updated_keys = []
            for record in records:
                key = (
                    record[self._key_field_name]
                    if isinstance(record, Mapping)
                    else getattr(record, self._key_field_name)
                )
                self.inner_storage[key] = record
                updated_keys.append(key)
            return updated_keys

        def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
            return records

        def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
            return records

        async def create_collection(self, **kwargs: Any) -> None:
            pass

        async def delete_collection(self, **kwargs: Any) -> None:
            self.inner_storage = {}

        async def does_collection_exist(self, **kwargs: Any) -> bool:
            return True

        async def _inner_search(
            self,
            options: Any = None,
            keywords: OptionalOneOrMany[str] = None,
            search_text: str | None = None,
            vectorizable_text: str | None = None,
            vector: list[float | int] | None = None,
            **kwargs: Any,
        ) -> Any:
            return KernelSearchResults(
                results=self.generator(),
                total_count=len(self.inner_storage) if options.include_total_count else None,
            )

        def _get_record_from_result(self, result: Any) -> Any:
            return result

        def _get_score_from_result(self, result: Any) -> float | None:
            return None

        async def generator(self):
            if self.inner_storage:
                for record in self.inner_storage.values():
                    yield VectorSearchResult(record=record)

        def _lambda_parser(self, node: ast.AST) -> str:
            return ""

    return DictVectorStoreRecordCollection


@fixture
def data_model_definition() -> object:
    return VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
            VectorStoreRecordVectorField(dimensions=5, name="vector"),
        ]
    )


@fixture
def data_model_serialize_definition() -> object:
    def serialize(record, **kwargs):
        return record

    def deserialize(records, **kwargs):
        return records

    return VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
            VectorStoreRecordVectorField(dimensions=5, name="vector"),
        ],
        serialize=serialize,
        deserialize=deserialize,
    )


@fixture
def data_model_to_from_dict_definition() -> object:
    def to_dict(record, **kwargs):
        return record

    def from_dict(records, **kwargs):
        return records

    return VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
            VectorStoreRecordVectorField(dimensions=5, name="vector"),
        ],
        to_dict=to_dict,
        from_dict=from_dict,
    )


@fixture
def data_model_container_definition() -> object:
    def to_dict(record: dict[str, dict[str, Any]], **kwargs) -> list[dict[str, Any]]:
        return [{"id": key} | value for key, value in record.items()]

    def from_dict(records: list[dict[str, Any]], **kwargs) -> dict[str, dict[str, Any]]:
        ret = {}
        for record in records:
            id = record.pop("id")
            ret[id] = record
        return ret

    return VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
            VectorStoreRecordVectorField(dimensions=5, name="vector"),
        ],
        container_mode=True,
        to_dict=to_dict,
        from_dict=from_dict,
    )


@fixture
def data_model_container_serialize_definition() -> object:
    def serialize(record: dict[str, dict[str, Any]], **kwargs) -> list[dict[str, Any]]:
        return [{"id": key} | value for key, value in record.items()]

    def deserialize(records: list[dict[str, Any]], **kwargs) -> dict[str, dict[str, Any]]:
        ret = {}
        for record in records:
            id = record.pop("id")
            ret[id] = record
        return ret

    return VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
            VectorStoreRecordVectorField(dimensions=5, name="vector"),
        ],
        container_mode=True,
        serialize=serialize,
        deserialize=deserialize,
    )


@fixture
def data_model_pandas_definition() -> object:
    from pandas import DataFrame

    return VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordVectorField(
                name="vector",
                index_kind="hnsw",
                dimensions=5,
                distance_function="cosine_similarity",
                property_type="float",
            ),
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(
                name="content",
                property_type="str",
            ),
        ],
        container_mode=True,
        to_dict=lambda x: x.to_dict(orient="records"),
        from_dict=lambda x, **_: DataFrame(x),
    )


@fixture
def data_model_type_vanilla():
    @vectorstoremodel
    class DataModelClass:
        def __init__(
            self,
            content: Annotated[str, VectorStoreRecordDataField()],
            id: Annotated[str, VectorStoreRecordKeyField()],
            vector: Annotated[list[float] | str | None, VectorStoreRecordVectorField(dimensions=5)] = None,
        ):
            self.content = content
            self.vector = vector
            self.id = id

        def __eq__(self, other) -> bool:
            return self.content == other.content and self.id == other.id and self.vector == other.vector

    return DataModelClass


@fixture
def data_model_type_vector_array():
    @vectorstoremodel
    class DataModelClass:
        def __init__(
            self,
            id: Annotated[str, VectorStoreRecordKeyField()],
            content: Annotated[str, VectorStoreRecordDataField()],
            vector: Annotated[
                list[float] | str | None,
                VectorStoreRecordVectorField(
                    dimensions=5,
                ),
            ] = None,
        ):
            self.content = content
            self.vector = vector
            self.id = id

        def __eq__(self, other) -> bool:
            return self.content == other.content and self.id == other.id and self.vector == other.vector

    return DataModelClass


@fixture
def data_model_type_vanilla_serialize():
    @vectorstoremodel
    class DataModelClass:
        def __init__(
            self,
            id: Annotated[str, VectorStoreRecordKeyField()],
            content: Annotated[str, VectorStoreRecordDataField()],
            vector: Annotated[list[float] | str | None, VectorStoreRecordVectorField(dimensions=5)] = None,
        ):
            self.content = content
            self.vector = vector
            self.id = id

        def serialize(self, **kwargs: Any) -> Any:
            """Serialize the object to the format required by the data store."""
            return {"id": self.id, "content": self.content, "vector": self.vector}

        @classmethod
        def deserialize(cls, obj: Any, **kwargs: Any):
            """Deserialize the output of the data store to an object."""
            return cls(**obj)

        def __eq__(self, other) -> bool:
            return self.content == other.content and self.id == other.id and self.vector == other.vector

    return DataModelClass


@fixture
def data_model_type_vanilla_to_from_dict():
    @vectorstoremodel
    class DataModelClass:
        def __init__(
            self,
            id: Annotated[str, VectorStoreRecordKeyField()],
            content: Annotated[str, VectorStoreRecordDataField()],
            vector: Annotated[str | list[float] | None, VectorStoreRecordVectorField(dimensions=5)] = None,
        ):
            self.content = content
            self.vector = vector
            self.id = id

        def to_dict(self, **kwargs: Any) -> Any:
            """Serialize the object to the format required by the data store."""
            return {"id": self.id, "content": self.content, "vector": self.vector}

        @classmethod
        def from_dict(cls, *args: Any, **kwargs: Any):
            """Deserialize the output of the data store to an object."""
            return cls(**args[0])

        def __eq__(self, other) -> bool:
            return self.content == other.content and self.id == other.id and self.vector == other.vector

    return DataModelClass


@fixture
def data_model_type_pydantic():
    @vectorstoremodel
    class DataModelClass(BaseModel):
        content: Annotated[str, VectorStoreRecordDataField()]
        id: Annotated[str, VectorStoreRecordKeyField()]
        vector: Annotated[str | list[float] | None, VectorStoreRecordVectorField(dimensions=5)] = None

    return DataModelClass


@fixture
def data_model_type_dataclass():
    @vectorstoremodel
    @dataclass
    class DataModelClass:
        content: Annotated[str, VectorStoreRecordDataField()]
        id: Annotated[str, VectorStoreRecordKeyField()]
        vector: Annotated[list[float] | str | None, VectorStoreRecordVectorField(dimensions=5)] = None

    return DataModelClass


@fixture(scope="function")
def vector_store_record_collection(
    DictVectorStoreRecordCollection,
    data_model_definition,
    data_model_serialize_definition,
    data_model_to_from_dict_definition,
    data_model_container_definition,
    data_model_container_serialize_definition,
    data_model_pandas_definition,
    data_model_type_vanilla,
    data_model_type_vanilla_serialize,
    data_model_type_vanilla_to_from_dict,
    data_model_type_pydantic,
    data_model_type_dataclass,
    data_model_type_vector_array,
    request,
) -> VectorSearch:
    item = request.param if request and hasattr(request, "param") else "definition_basic"
    defs = {
        "definition_basic": data_model_definition,
        "definition_with_serialize": data_model_serialize_definition,
        "definition_with_to_from": data_model_to_from_dict_definition,
        "definition_container": data_model_container_definition,
        "definition_container_serialize": data_model_container_serialize_definition,
        "definition_pandas": data_model_pandas_definition,
        "type_vanilla": data_model_type_vanilla,
        "type_vanilla_with_serialize": data_model_type_vanilla_serialize,
        "type_vanilla_with_to_from_dict": data_model_type_vanilla_to_from_dict,
        "type_pydantic": data_model_type_pydantic,
        "type_dataclass": data_model_type_dataclass,
        "type_vector_array": data_model_type_vector_array,
    }
    if item.endswith("pandas"):
        return DictVectorStoreRecordCollection(
            collection_name="test",
            data_model_type=DataFrame,
            data_model_definition=defs[item],
        )
    if item.startswith("definition_"):
        return DictVectorStoreRecordCollection(
            collection_name="test",
            data_model_type=dict,
            data_model_definition=defs[item],
        )
    return DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=defs[item],
    )
