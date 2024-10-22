# Copyright (c) Microsoft. All rights reserved.


from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pytest import raises

from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions.memory_connector_exceptions import VectorStoreModelException


def test_vanilla():
    @vectorstoremodel
    class DataModelClass:
        def __init__(
            self,
            content: Annotated[str, VectorStoreRecordDataField()],
            content2: Annotated[str, VectorStoreRecordDataField],
            vector: Annotated[list[float], VectorStoreRecordVectorField()],
            id: Annotated[str, VectorStoreRecordKeyField()],
            non_vector_store_content: str | None = None,
            optional_content: Annotated[str | None, VectorStoreRecordDataField()] = None,
            annotated_content: Annotated[str | None, "description"] = None,
        ):
            self.content = content
            self.content2 = content2
            self.vector = vector
            self.id = id
            self.optional_content = optional_content
            self.non_vector_store_content = non_vector_store_content
            self.annotated_content = annotated_content

    assert hasattr(DataModelClass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClass, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClass.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 5
    assert data_model_definition.fields["content"].name == "content"
    assert data_model_definition.fields["content"].property_type == "str"
    assert data_model_definition.fields["content2"].name == "content2"
    assert data_model_definition.fields["content2"].property_type == "str"
    assert data_model_definition.fields["vector"].name == "vector"
    assert data_model_definition.fields["id"].name == "id"
    assert data_model_definition.fields["optional_content"].name == "optional_content"
    assert data_model_definition.fields["optional_content"].property_type == "str"
    assert data_model_definition.key_field_name == "id"
    assert data_model_definition.container_mode is False
    assert data_model_definition.vector_field_names == ["vector"]


def test_vanilla_2():
    @vectorstoremodel()
    class DataModelClass:
        def __init__(
            self,
            content: Annotated[str, VectorStoreRecordDataField()],
            id: Annotated[str, VectorStoreRecordKeyField()],
        ):
            self.content = content
            self.id = id

    assert hasattr(DataModelClass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClass, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClass.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 2


def test_dataclass():
    @vectorstoremodel
    @dataclass
    class DataModelClass:
        content: Annotated[str, VectorStoreRecordDataField()]
        content2: Annotated[str, VectorStoreRecordDataField]
        vector: Annotated[list[float], VectorStoreRecordVectorField()]
        id: Annotated[str, VectorStoreRecordKeyField()]
        non_vector_store_content: str | None = None
        optional_content: Annotated[str | None, VectorStoreRecordDataField()] = None
        annotated_content: Annotated[str | None, "description"] = None

    assert hasattr(DataModelClass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClass, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClass.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 5
    assert data_model_definition.fields["content"].name == "content"
    assert data_model_definition.fields["content"].property_type == "str"
    assert data_model_definition.fields["content2"].name == "content2"
    assert data_model_definition.fields["content2"].property_type == "str"
    assert data_model_definition.fields["vector"].name == "vector"
    assert data_model_definition.fields["id"].name == "id"
    assert data_model_definition.fields["optional_content"].name == "optional_content"
    assert data_model_definition.fields["optional_content"].property_type == "str"
    assert data_model_definition.key_field_name == "id"
    assert data_model_definition.container_mode is False
    assert data_model_definition.vector_field_names == ["vector"]


def test_dataclass_inverse_fail():
    with raises(VectorStoreModelException):

        @dataclass
        @vectorstoremodel
        class DataModelClass:
            id: Annotated[str, VectorStoreRecordKeyField()]
            content: Annotated[str, VectorStoreRecordDataField()]


def test_pydantic_base_model():
    @vectorstoremodel
    class DataModelClass(BaseModel):
        content: Annotated[str, VectorStoreRecordDataField()]
        content2: Annotated[str, VectorStoreRecordDataField]
        vector: Annotated[list[float], VectorStoreRecordVectorField()]
        id: Annotated[str, VectorStoreRecordKeyField()]
        non_vector_store_content: str | None = None
        optional_content: Annotated[str | None, VectorStoreRecordDataField()] = None
        annotated_content: Annotated[str | None, "description"] = None

    assert hasattr(DataModelClass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClass, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClass.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 5
    assert data_model_definition.fields["content"].name == "content"
    assert data_model_definition.fields["content"].property_type == "str"
    assert data_model_definition.fields["content2"].name == "content2"
    assert data_model_definition.fields["content2"].property_type == "str"
    assert data_model_definition.fields["vector"].name == "vector"
    assert data_model_definition.fields["id"].name == "id"
    assert data_model_definition.fields["optional_content"].name == "optional_content"
    assert data_model_definition.fields["optional_content"].property_type == "str"
    assert data_model_definition.key_field_name == "id"
    assert data_model_definition.container_mode is False
    assert data_model_definition.vector_field_names == ["vector"]


def test_pydantic_dataclass():
    @vectorstoremodel
    @pydantic_dataclass
    class DataModelClass:
        content: Annotated[str, VectorStoreRecordDataField()]
        content2: Annotated[str, VectorStoreRecordDataField]
        vector: Annotated[list[float], VectorStoreRecordVectorField()]
        id: Annotated[str, VectorStoreRecordKeyField()]
        non_vector_store_content: str | None = None
        optional_content: Annotated[str | None, VectorStoreRecordDataField()] = None
        annotated_content: Annotated[str | None, "description"] = None

    assert hasattr(DataModelClass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClass, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClass.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 5
    assert data_model_definition.fields["content"].name == "content"
    assert data_model_definition.fields["content"].property_type == "str"
    assert data_model_definition.fields["content2"].name == "content2"
    assert data_model_definition.fields["content2"].property_type == "str"
    assert data_model_definition.fields["vector"].name == "vector"
    assert data_model_definition.fields["id"].name == "id"
    assert data_model_definition.fields["optional_content"].name == "optional_content"
    assert data_model_definition.fields["optional_content"].property_type == "str"
    assert data_model_definition.key_field_name == "id"
    assert data_model_definition.container_mode is False
    assert data_model_definition.vector_field_names == ["vector"]


def test_empty_model():
    with raises(VectorStoreModelException):

        @vectorstoremodel
        class DataModelClass:
            def __init__(self):
                pass


def test_non_annotated_no_default():
    with raises(VectorStoreModelException):

        @vectorstoremodel
        class DataModelClass:
            def __init__(self, non_vector_store_content: str):
                self.non_vector_store_content = non_vector_store_content


def test_annotated_no_vsr_field_no_default():
    with raises(VectorStoreModelException):

        @vectorstoremodel
        class DataModelClass:
            def __init__(
                self,
                annotated_content: Annotated[str, "description"],
            ):
                self.annotated_content = annotated_content


def test_non_vector_list_and_dict():
    @vectorstoremodel
    @dataclass
    class DataModelClass:
        key: Annotated[str, VectorStoreRecordKeyField()]
        list1: Annotated[list[int], VectorStoreRecordDataField()]
        list2: Annotated[list[str], VectorStoreRecordDataField]
        dict1: Annotated[dict[str, int], VectorStoreRecordDataField()]
        dict2: Annotated[dict[str, str], VectorStoreRecordDataField]

    assert hasattr(DataModelClass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClass, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClass.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 5
    assert data_model_definition.fields["list1"].name == "list1"
    assert data_model_definition.fields["list1"].property_type == "list[int]"
    assert data_model_definition.fields["list2"].name == "list2"
    assert data_model_definition.fields["list2"].property_type == "list[str]"
    assert data_model_definition.fields["dict1"].name == "dict1"
    assert data_model_definition.fields["dict1"].property_type == "dict"
    assert data_model_definition.fields["dict2"].name == "dict2"
    assert data_model_definition.fields["dict2"].property_type == "dict"
    assert data_model_definition.container_mode is False
