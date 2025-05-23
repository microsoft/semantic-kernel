# Copyright (c) Microsoft. All rights reserved.

from pytest import raises

from semantic_kernel.data import VectorStoreCollectionDefinition, VectorStoreField
from semantic_kernel.exceptions import VectorStoreModelException


def test_vector_store_record_definition():
    id_field = VectorStoreField("key", name="id")
    vsrd = VectorStoreCollectionDefinition(fields=[id_field])
    assert vsrd.fields == [VectorStoreField("key", name="id")]
    assert vsrd.key_name == "id"
    assert vsrd.key_field == id_field
    assert vsrd.names == ["id"]
    assert vsrd.vector_field_names == []
    assert vsrd.container_mode is False
    assert vsrd.to_dict is None
    assert vsrd.from_dict is None
    assert vsrd.serialize is None
    assert vsrd.deserialize is None


def test_no_fields_fail():
    with raises(VectorStoreModelException):
        VectorStoreCollectionDefinition(fields=[])


def test_no_name_fields_fail():
    with raises(VectorStoreModelException):
        VectorStoreCollectionDefinition(fields=[VectorStoreField("key", name=None)])
    with raises(VectorStoreModelException):
        VectorStoreCollectionDefinition(fields=[VectorStoreField("key", name="")])


def test_no_key_field_fail():
    with raises(VectorStoreModelException):
        VectorStoreCollectionDefinition(fields=[VectorStoreField("data", name="content")])


def test_multiple_key_field_fail():
    with raises(VectorStoreModelException):
        VectorStoreCollectionDefinition(
            fields=[VectorStoreField("key", name="key1"), VectorStoreField("key", name="key2")]
        )


def test_vector_and_non_vector_field_names():
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id"),
            VectorStoreField("data", name="content"),
            VectorStoreField("vector", name="vector", dimensions=5),
        ]
    )
    assert definition.vector_field_names == ["vector"]
    assert definition.data_field_names == ["content"]


def test_try_get_vector_field():
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id"),
            VectorStoreField("data", name="content"),
            VectorStoreField("vector", name="vector", dimensions=5),
        ]
    )
    assert definition.try_get_vector_field() == definition.fields[2]
    assert definition.try_get_vector_field("vector") == definition.fields[2]


def test_try_get_vector_field_none():
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id"),
            VectorStoreField("data", name="content"),
        ]
    )
    assert definition.try_get_vector_field() is None
    with raises(VectorStoreModelException, match="Field vector not found."):
        definition.try_get_vector_field("vector")


def test_try_get_vector_field_wrong_name_fail():
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id"),
            VectorStoreField("data", name="content"),
        ]
    )
    with raises(VectorStoreModelException, match="Field content is not a vector field."):
        definition.try_get_vector_field("content")


def test_get_field_names():
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id"),
            VectorStoreField("data", name="content"),
            VectorStoreField("vector", name="vector", dimensions=5),
        ]
    )
    assert definition.get_names() == ["id", "content", "vector"]
    assert definition.get_names(include_vector_fields=False) == ["id", "content"]
    assert definition.get_names(include_key_field=False) == ["content", "vector"]
    assert definition.get_names(include_vector_fields=False, include_key_field=False) == ["content"]
