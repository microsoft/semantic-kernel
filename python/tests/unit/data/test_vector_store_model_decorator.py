# Copyright (c) Microsoft. All rights reserved.


from dataclasses import dataclass
from typing import Annotated

from numpy import ndarray
from pydantic import BaseModel, ConfigDict
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pytest import raises

from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.record_definition import vectorstoremodel
from semantic_kernel.exceptions import VectorStoreModelException


def get_field(defn, name):
    return next(f for f in defn.fields if f.name == name)


def test_vanilla():
    @vectorstoremodel
    class DataModelClassVanilla:
        def __init__(
            self,
            content: Annotated[str, VectorStoreRecordDataField()],
            content2: Annotated[str, VectorStoreRecordDataField],
            vector: Annotated[list[float], VectorStoreRecordVectorField(dimensions=5)],
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

    assert hasattr(DataModelClassVanilla, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassVanilla, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClassVanilla.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 5
    assert get_field(data_model_definition, "content").name == "content"
    assert get_field(data_model_definition, "content").property_type == "str"
    assert get_field(data_model_definition, "content2").name == "content2"
    assert get_field(data_model_definition, "content2").property_type == "str"
    assert get_field(data_model_definition, "vector").name == "vector"
    assert get_field(data_model_definition, "id").name == "id"
    assert get_field(data_model_definition, "optional_content").name == "optional_content"
    assert get_field(data_model_definition, "optional_content").property_type == "str"
    assert data_model_definition.key_field_name == "id"
    assert data_model_definition.container_mode is False
    assert data_model_definition.vector_field_names == ["vector"]


def test_vanilla_2():
    @vectorstoremodel()
    class DataModelClassVanilla2:
        def __init__(
            self,
            content: Annotated[str, VectorStoreRecordDataField()],
            id: Annotated[str, VectorStoreRecordKeyField()],
        ):
            self.content = content
            self.id = id

    assert hasattr(DataModelClassVanilla2, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassVanilla2, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClassVanilla2.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 2


def test_dataclass():
    @vectorstoremodel
    @dataclass
    class DataModelClassDataclass:
        content: Annotated[str, VectorStoreRecordDataField()]
        content2: Annotated[str, VectorStoreRecordDataField]
        vector: Annotated[list[float], VectorStoreRecordVectorField(dimensions=5)]
        id: Annotated[str, VectorStoreRecordKeyField()]
        non_vector_store_content: str | None = None
        optional_content: Annotated[str | None, VectorStoreRecordDataField()] = None
        annotated_content: Annotated[str | None, "description"] = None

    assert hasattr(DataModelClassDataclass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassDataclass, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClassDataclass.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 5
    assert get_field(data_model_definition, "content").name == "content"
    assert get_field(data_model_definition, "content").property_type == "str"
    assert get_field(data_model_definition, "content2").name == "content2"
    assert get_field(data_model_definition, "content2").property_type == "str"
    assert get_field(data_model_definition, "vector").name == "vector"
    assert get_field(data_model_definition, "id").name == "id"
    assert get_field(data_model_definition, "optional_content").name == "optional_content"
    assert get_field(data_model_definition, "optional_content").property_type == "str"
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
    class DataModelClassPydantic(BaseModel):
        content: Annotated[str, VectorStoreRecordDataField()]
        content2: Annotated[str, VectorStoreRecordDataField]
        vector: Annotated[list[float], VectorStoreRecordVectorField(dimensions=5)]
        id: Annotated[str, VectorStoreRecordKeyField()]
        non_vector_store_content: str | None = None
        optional_content: Annotated[str | None, VectorStoreRecordDataField()] = None
        annotated_content: Annotated[str | None, "description"] = None

    assert hasattr(DataModelClassPydantic, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassPydantic, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClassPydantic.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 5
    assert get_field(data_model_definition, "content").name == "content"
    assert get_field(data_model_definition, "content").property_type == "str"
    assert get_field(data_model_definition, "content2").name == "content2"
    assert get_field(data_model_definition, "content2").property_type == "str"
    assert get_field(data_model_definition, "vector").name == "vector"
    assert get_field(data_model_definition, "id").name == "id"
    assert get_field(data_model_definition, "optional_content").name == "optional_content"
    assert get_field(data_model_definition, "optional_content").property_type == "str"
    assert data_model_definition.key_field_name == "id"
    assert data_model_definition.container_mode is False
    assert data_model_definition.vector_field_names == ["vector"]


def test_pydantic_dataclass():
    @vectorstoremodel
    @pydantic_dataclass
    class DataModelClassPydanticDataclass:
        content: Annotated[str, VectorStoreRecordDataField()]
        content2: Annotated[str, VectorStoreRecordDataField]
        vector: Annotated[list[float], VectorStoreRecordVectorField(dimensions=5)]
        id: Annotated[str, VectorStoreRecordKeyField()]
        non_vector_store_content: str | None = None
        optional_content: Annotated[str | None, VectorStoreRecordDataField()] = None
        annotated_content: Annotated[str | None, "description"] = None

    assert hasattr(DataModelClassPydanticDataclass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassPydanticDataclass, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = (
        DataModelClassPydanticDataclass.__kernel_vectorstoremodel_definition__
    )
    assert len(data_model_definition.fields) == 5
    assert get_field(data_model_definition, "content").name == "content"
    assert get_field(data_model_definition, "content").property_type == "str"
    assert get_field(data_model_definition, "content2").name == "content2"
    assert get_field(data_model_definition, "content2").property_type == "str"
    assert get_field(data_model_definition, "vector").name == "vector"
    assert get_field(data_model_definition, "id").name == "id"
    assert get_field(data_model_definition, "optional_content").name == "optional_content"
    assert get_field(data_model_definition, "optional_content").property_type == "str"
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
    class DataModelClassListDict:
        key: Annotated[str, VectorStoreRecordKeyField()]
        list1: Annotated[list[int], VectorStoreRecordDataField()]
        list2: Annotated[list[str], VectorStoreRecordDataField]
        list3: Annotated[list[str] | None, VectorStoreRecordDataField]
        dict1: Annotated[dict[str, int], VectorStoreRecordDataField()]
        dict2: Annotated[dict[str, str], VectorStoreRecordDataField]
        dict3: Annotated[dict[str, str] | None, VectorStoreRecordDataField]

    assert hasattr(DataModelClassListDict, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassListDict, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = DataModelClassListDict.__kernel_vectorstoremodel_definition__
    assert len(data_model_definition.fields) == 7
    assert get_field(data_model_definition, "list1").name == "list1"
    assert get_field(data_model_definition, "list1").property_type == "list[int]"
    assert get_field(data_model_definition, "list2").name == "list2"
    assert get_field(data_model_definition, "list2").property_type == "list[str]"
    assert get_field(data_model_definition, "list3").name == "list3"
    assert get_field(data_model_definition, "list3").property_type == "list[str]"
    assert get_field(data_model_definition, "dict1").name == "dict1"
    assert get_field(data_model_definition, "dict1").property_type == "dict[str, int]"
    assert get_field(data_model_definition, "dict2").name == "dict2"
    assert get_field(data_model_definition, "dict2").property_type == "dict[str, str]"
    assert get_field(data_model_definition, "dict3").name == "dict3"
    assert get_field(data_model_definition, "dict3").property_type == "dict[str, str]"
    assert data_model_definition.container_mode is False


def test_vector_fields_checks():
    @vectorstoremodel
    class DataModelClassVectorFields(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        id: Annotated[str, VectorStoreRecordKeyField()]
        vector_str: Annotated[str, VectorStoreRecordVectorField(dimensions=5)]
        vector_list: Annotated[list[float], VectorStoreRecordVectorField(dimensions=5)]
        vector_array: Annotated[
            ndarray,
            VectorStoreRecordVectorField(dimensions=5),
        ]

    assert hasattr(DataModelClassVectorFields, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassVectorFields, "__kernel_vectorstoremodel_definition__")
    data_model_definition: VectorStoreRecordDefinition = (
        DataModelClassVectorFields.__kernel_vectorstoremodel_definition__
    )
    assert len(data_model_definition.fields) == 4
    assert get_field(data_model_definition, "id").name == "id"
    assert get_field(data_model_definition, "vector_str").property_type == "str"
    assert get_field(data_model_definition, "vector_list").property_type == "float"
    assert get_field(data_model_definition, "vector_array").property_type == "ndarray"
