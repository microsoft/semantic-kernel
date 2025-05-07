# Copyright (c) Microsoft. All rights reserved.

from pydantic import ValidationError
from pytest import raises

from semantic_kernel.data import VectorStoreRecordDataField, VectorStoreRecordDefinition, VectorStoreRecordKeyField
from semantic_kernel.data.record_definition import VectorStoreRecordVectorField
from semantic_kernel.exceptions import VectorStoreModelException


def test_vector_store_record_definition():
    id_field = VectorStoreRecordKeyField(name="id")
    vsrd = VectorStoreRecordDefinition(fields=[id_field])
    assert vsrd.fields == [VectorStoreRecordKeyField(name="id")]
    assert vsrd.key_field_name == "id"
    assert vsrd.key_field == id_field
    assert vsrd.field_names == ["id"]
    assert vsrd.vector_field_names == []
    assert vsrd.container_mode is False
    assert vsrd.to_dict is None
    assert vsrd.from_dict is None
    assert vsrd.serialize is None
    assert vsrd.deserialize is None


def test_no_fields_fail():
    with raises(VectorStoreModelException):
        VectorStoreRecordDefinition(fields=[])


def test_no_name_fields_fail():
    with raises(ValidationError):
        VectorStoreRecordDefinition(fields=[VectorStoreRecordKeyField(name=None)])  # type: ignore
    with raises(VectorStoreModelException):
        VectorStoreRecordDefinition(fields=[VectorStoreRecordKeyField(name="")])


def test_no_key_field_fail():
    with raises(VectorStoreModelException):
        VectorStoreRecordDefinition(fields=[VectorStoreRecordDataField(name="content")])


def test_multiple_key_field_fail():
    with raises(VectorStoreModelException):
        VectorStoreRecordDefinition(
            fields=[VectorStoreRecordKeyField(name="key1"), VectorStoreRecordKeyField(name="key2")]
        )


def test_vector_and_non_vector_field_names():
    definition = VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
            VectorStoreRecordVectorField(name="vector", dimensions=5),
        ]
    )
    assert definition.vector_field_names == ["vector"]
    assert definition.data_field_names == ["content"]


def test_try_get_vector_field():
    definition = VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
            VectorStoreRecordVectorField(name="vector", dimensions=5),
        ]
    )
    assert definition.try_get_vector_field() == definition.fields[2]
    assert definition.try_get_vector_field("vector") == definition.fields[2]


def test_try_get_vector_field_none():
    definition = VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
        ]
    )
    assert definition.try_get_vector_field() is None
    with raises(VectorStoreModelException, match="Field vector not found."):
        definition.try_get_vector_field("vector")


def test_try_get_vector_field_wrong_name_fail():
    definition = VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
        ]
    )
    with raises(VectorStoreModelException, match="Field content is not a vector field."):
        definition.try_get_vector_field("content")


def test_get_field_names():
    definition = VectorStoreRecordDefinition(
        fields=[
            VectorStoreRecordKeyField(name="id"),
            VectorStoreRecordDataField(name="content"),
            VectorStoreRecordVectorField(name="vector", dimensions=5),
        ]
    )
    assert definition.get_field_names() == ["id", "content", "vector"]
    assert definition.get_field_names(include_vector_fields=False) == ["id", "content"]
    assert definition.get_field_names(include_key_field=False) == ["content", "vector"]
    assert definition.get_field_names(include_vector_fields=False, include_key_field=False) == ["content"]
