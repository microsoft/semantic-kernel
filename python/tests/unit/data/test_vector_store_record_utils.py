# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

from pytest import mark, raises

from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_store_record_utils import VectorStoreRecordUtils
from semantic_kernel.exceptions.memory_connector_exceptions import VectorStoreModelException
from semantic_kernel.kernel import Kernel


@mark.asyncio
async def test_add_vector_to_records(data_model_definition):
    kernel = MagicMock(spec=Kernel)
    kernel.add_embedding_to_object = AsyncMock()
    utils = VectorStoreRecordUtils(kernel)
    assert utils is not None
    record = {"id": "test_id", "content": "content"}
    await utils.add_vector_to_records(record, None, data_model_definition)
    kernel.add_embedding_to_object.assert_called_once()


@mark.asyncio
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
