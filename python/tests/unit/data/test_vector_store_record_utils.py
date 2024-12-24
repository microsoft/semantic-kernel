# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

from pytest import raises

from semantic_kernel import Kernel
from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordUtils,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import VectorStoreModelException


async def test_add_vector_to_records(data_model_definition):
    kernel = MagicMock(spec=Kernel)
    kernel.add_embedding_to_object = AsyncMock()
    utils = VectorStoreRecordUtils(kernel)
    assert utils is not None
    record = {"id": "test_id", "content": "content"}
    await utils.add_vector_to_records(record, None, data_model_definition)
    kernel.add_embedding_to_object.assert_called_once()


async def test_add_vector_wrong_fields():
    data_model = VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(has_embedding=True, embedding_property_name="id"),
            "vector": VectorStoreRecordVectorField(),
        }
    )
    kernel = MagicMock(spec=Kernel)
    kernel.add_embedding_to_object = AsyncMock()
    utils = VectorStoreRecordUtils(kernel)
    assert utils is not None
    record = {"id": "test_id", "content": "content"}
    with raises(VectorStoreModelException, match="Embedding field"):
        await utils.add_vector_to_records(record, None, data_model)


async def test_fail():
    kernel = MagicMock(spec=Kernel)
    kernel.add_embedding_to_object = AsyncMock()
    utils = VectorStoreRecordUtils(kernel)
    assert utils is not None
    record = {"id": "test_id", "content": "content"}
    with raises(VectorStoreModelException, match="Data model definition is required"):
        await utils.add_vector_to_records(record, dict, None)
    kernel.add_embedding_to_object.assert_not_called()
