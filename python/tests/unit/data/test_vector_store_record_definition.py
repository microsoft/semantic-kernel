# Copyright (c) Microsoft. All rights reserved.

from pytest import raises

from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordDataField, VectorStoreRecordKeyField
from semantic_kernel.exceptions.memory_connector_exceptions import VectorStoreModelException


def test_vector_store_record_definition():
    id_field = VectorStoreRecordKeyField()
    vsrd = VectorStoreRecordDefinition(fields={"id": id_field})
    assert vsrd.fields == {"id": VectorStoreRecordKeyField(name="id")}
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
        VectorStoreRecordDefinition(fields={})


def test_no_name_fields_fail():
    with raises(VectorStoreModelException):
        VectorStoreRecordDefinition(fields={None: VectorStoreRecordKeyField()})  # type: ignore
    with raises(VectorStoreModelException):
        VectorStoreRecordDefinition(fields={"": VectorStoreRecordKeyField()})


def test_no_key_field_fail():
    with raises(VectorStoreModelException):
        VectorStoreRecordDefinition(fields={"content": VectorStoreRecordDataField()})


def test_multiple_key_field_fail():
    with raises(VectorStoreModelException):
        VectorStoreRecordDefinition(fields={"key1": VectorStoreRecordKeyField(), "key2": VectorStoreRecordKeyField()})


def test_no_matching_vector_field_fail():
    with raises(VectorStoreModelException):
        VectorStoreRecordDefinition(
            fields={
                "id": VectorStoreRecordKeyField(),
                "content": VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector"),
            }
        )
