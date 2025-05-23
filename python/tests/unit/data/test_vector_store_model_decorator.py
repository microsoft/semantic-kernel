# Copyright (c) Microsoft. All rights reserved.


from dataclasses import dataclass
from typing import Annotated

from numpy import ndarray
from pydantic import BaseModel, ConfigDict
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pytest import raises

from semantic_kernel.data import VectorStoreCollectionDefinition, VectorStoreField
from semantic_kernel.data.definitions import vectorstoremodel
from semantic_kernel.exceptions import VectorStoreModelException


def get_field(defn, name):
    return next(f for f in defn.fields if f.name == name)


def test_vanilla():
    @vectorstoremodel
    class DataModelClassVanilla:
        def __init__(
            self,
            content: Annotated[str, VectorStoreField("data")],
            content2: Annotated[str, VectorStoreField("data")],
            vector: Annotated[list[float], VectorStoreField("vector", dimensions=5)],
            id: Annotated[str, VectorStoreField("key")],
            non_vector_store_content: str | None = None,
            optional_content: Annotated[str | None, VectorStoreField("data")] = None,
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
    definition: VectorStoreCollectionDefinition = DataModelClassVanilla.__kernel_vectorstoremodel_definition__
    assert len(definition.fields) == 5
    assert get_field(definition, "content").name == "content"
    assert get_field(definition, "content").type_ == "str"
    assert get_field(definition, "content2").name == "content2"
    assert get_field(definition, "content2").type_ == "str"
    assert get_field(definition, "vector").name == "vector"
    assert get_field(definition, "id").name == "id"
    assert get_field(definition, "optional_content").name == "optional_content"
    assert get_field(definition, "optional_content").type_ == "str"
    assert definition.key_name == "id"
    assert definition.container_mode is False
    assert definition.vector_field_names == ["vector"]


def test_vanilla_2():
    @vectorstoremodel()
    class DataModelClassVanilla2:
        def __init__(
            self,
            content: Annotated[str, VectorStoreField("data")],
            id: Annotated[str, VectorStoreField("key")],
        ):
            self.content = content
            self.id = id

    assert hasattr(DataModelClassVanilla2, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassVanilla2, "__kernel_vectorstoremodel_definition__")
    definition: VectorStoreCollectionDefinition = DataModelClassVanilla2.__kernel_vectorstoremodel_definition__
    assert len(definition.fields) == 2


def test_dataclass():
    @vectorstoremodel
    @dataclass
    class DataModelClassDataclass:
        content: Annotated[str, VectorStoreField("data")]
        content2: Annotated[str, VectorStoreField("data")]
        vector: Annotated[list[float], VectorStoreField("vector", dimensions=5)]
        id: Annotated[str, VectorStoreField("key")]
        non_vector_store_content: str | None = None
        optional_content: Annotated[str | None, VectorStoreField("data")] = None
        annotated_content: Annotated[str | None, "description"] = None

    assert hasattr(DataModelClassDataclass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassDataclass, "__kernel_vectorstoremodel_definition__")
    definition: VectorStoreCollectionDefinition = DataModelClassDataclass.__kernel_vectorstoremodel_definition__
    assert len(definition.fields) == 5
    assert get_field(definition, "content").name == "content"
    assert get_field(definition, "content").type_ == "str"
    assert get_field(definition, "content2").name == "content2"
    assert get_field(definition, "content2").type_ == "str"
    assert get_field(definition, "vector").name == "vector"
    assert get_field(definition, "id").name == "id"
    assert get_field(definition, "optional_content").name == "optional_content"
    assert get_field(definition, "optional_content").type_ == "str"
    assert definition.key_name == "id"
    assert definition.container_mode is False
    assert definition.vector_field_names == ["vector"]


def test_dataclass_inverse_fail():
    with raises(VectorStoreModelException):

        @dataclass
        @vectorstoremodel
        class DataModelClass:
            id: Annotated[str, VectorStoreField("key")]
            content: Annotated[str, VectorStoreField("data")]


def test_pydantic_base_model():
    @vectorstoremodel
    class DataModelClassPydantic(BaseModel):
        content: Annotated[str, VectorStoreField("data")]
        content2: Annotated[str, VectorStoreField("data")]
        vector: Annotated[list[float], VectorStoreField("vector", dimensions=5)]
        id: Annotated[str, VectorStoreField("key")]
        non_vector_store_content: str | None = None
        optional_content: Annotated[str | None, VectorStoreField("data")] = None
        annotated_content: Annotated[str | None, "description"] = None

    assert hasattr(DataModelClassPydantic, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassPydantic, "__kernel_vectorstoremodel_definition__")
    definition: VectorStoreCollectionDefinition = DataModelClassPydantic.__kernel_vectorstoremodel_definition__
    assert len(definition.fields) == 5
    assert get_field(definition, "content").name == "content"
    assert get_field(definition, "content").type_ == "str"
    assert get_field(definition, "content2").name == "content2"
    assert get_field(definition, "content2").type_ == "str"
    assert get_field(definition, "vector").name == "vector"
    assert get_field(definition, "id").name == "id"
    assert get_field(definition, "optional_content").name == "optional_content"
    assert get_field(definition, "optional_content").type_ == "str"
    assert definition.key_name == "id"
    assert definition.container_mode is False
    assert definition.vector_field_names == ["vector"]


def test_pydantic_dataclass():
    @vectorstoremodel
    @pydantic_dataclass
    class DataModelClassPydanticDataclass:
        content: Annotated[str, VectorStoreField("data")]
        content2: Annotated[str, VectorStoreField("data")]
        vector: Annotated[list[float], VectorStoreField("vector", dimensions=5)]
        id: Annotated[str, VectorStoreField("key")]
        non_vector_store_content: str | None = None
        optional_content: Annotated[str | None, VectorStoreField("data")] = None
        annotated_content: Annotated[str | None, "description"] = None

    assert hasattr(DataModelClassPydanticDataclass, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassPydanticDataclass, "__kernel_vectorstoremodel_definition__")
    definition: VectorStoreCollectionDefinition = DataModelClassPydanticDataclass.__kernel_vectorstoremodel_definition__
    assert len(definition.fields) == 5
    assert get_field(definition, "content").name == "content"
    assert get_field(definition, "content").type_ == "str"
    assert get_field(definition, "content2").name == "content2"
    assert get_field(definition, "content2").type_ == "str"
    assert get_field(definition, "vector").name == "vector"
    assert get_field(definition, "id").name == "id"
    assert get_field(definition, "optional_content").name == "optional_content"
    assert get_field(definition, "optional_content").type_ == "str"
    assert definition.key_name == "id"
    assert definition.container_mode is False
    assert definition.vector_field_names == ["vector"]


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
        key: Annotated[str, VectorStoreField("key")]
        list1: Annotated[list[int], VectorStoreField("data")]
        list2: Annotated[list[str], VectorStoreField("data")]
        list3: Annotated[list[str] | None, VectorStoreField("data")]
        dict1: Annotated[dict[str, int], VectorStoreField("data")]
        dict2: Annotated[dict[str, str], VectorStoreField("data")]
        dict3: Annotated[dict[str, str] | None, VectorStoreField("data")]

    assert hasattr(DataModelClassListDict, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassListDict, "__kernel_vectorstoremodel_definition__")
    definition: VectorStoreCollectionDefinition = DataModelClassListDict.__kernel_vectorstoremodel_definition__
    assert len(definition.fields) == 7
    assert get_field(definition, "list1").name == "list1"
    assert get_field(definition, "list1").type_ == "list[int]"
    assert get_field(definition, "list2").name == "list2"
    assert get_field(definition, "list2").type_ == "list[str]"
    assert get_field(definition, "list3").name == "list3"
    assert get_field(definition, "list3").type_ == "list[str]"
    assert get_field(definition, "dict1").name == "dict1"
    assert get_field(definition, "dict1").type_ == "dict[str, int]"
    assert get_field(definition, "dict2").name == "dict2"
    assert get_field(definition, "dict2").type_ == "dict[str, str]"
    assert get_field(definition, "dict3").name == "dict3"
    assert get_field(definition, "dict3").type_ == "dict[str, str]"
    assert definition.container_mode is False


def test_vector_fields_checks():
    @vectorstoremodel
    class DataModelClassVectorFields(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        id: Annotated[str, VectorStoreField("key")]
        vector_str: Annotated[str, VectorStoreField("vector", dimensions=5)]
        vector_list: Annotated[list[float], VectorStoreField("vector", dimensions=5)]
        vector_array: Annotated[
            ndarray,
            VectorStoreField("vector", dimensions=5),
        ]

    assert hasattr(DataModelClassVectorFields, "__kernel_vectorstoremodel__")
    assert hasattr(DataModelClassVectorFields, "__kernel_vectorstoremodel_definition__")
    definition: VectorStoreCollectionDefinition = DataModelClassVectorFields.__kernel_vectorstoremodel_definition__
    assert len(definition.fields) == 4
    assert get_field(definition, "id").name == "id"
    assert get_field(definition, "vector_str").type_ == "str"
    assert get_field(definition, "vector_list").type_ == "float"
    assert get_field(definition, "vector_array").type_ == "ndarray"
