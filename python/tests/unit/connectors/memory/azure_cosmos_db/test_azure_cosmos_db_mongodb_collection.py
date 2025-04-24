# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError
from pydantic_core import InitErrorDetails
from pymongo import AsyncMongoClient

import semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_collection as cosmos_collection
import semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_settings as cosmos_settings
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import VectorStoreInitializationException


async def test_constructor_with_mongo_client_provided() -> None:
    """
    Test the constructor of AzureCosmosDBforMongoDBCollection when a mongo_client
    is directly provided. Expect that the class is successfully initialized
    and doesn't attempt to manage the client.
    """
    mock_client = AsyncMock(spec=AsyncMongoClient)
    collection_name = "test_collection"
    fake_definition = VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(),
            "vector": VectorStoreRecordVectorField(),
        }
    )

    collection = cosmos_collection.AzureCosmosDBforMongoDBCollection(
        collection_name=collection_name,
        data_model_type=dict,
        mongo_client=mock_client,
        data_model_definition=fake_definition,
    )

    assert collection.mongo_client == mock_client
    assert collection.collection_name == collection_name
    assert not collection.managed_client, "Should not be managing client when provided"


async def test_constructor_raises_exception_on_validation_error() -> None:
    """
    Test that the constructor raises VectorStoreInitializationException when
    AzureCosmosDBforMongoDBSettings.create fails with ValidationError.
    """

    mock_data_model_definition = VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(),
            "vector": VectorStoreRecordVectorField(),
        }
    )

    class DummyModel(BaseModel):
        connection_string: str

    error = InitErrorDetails(
        type="missing",
        loc=("connection_string",),
        msg="Field required",
        input=None,
    )  # type: ignore

    validation_error = ValidationError.from_exception_data("DummyModel", [error])

    with patch.object(
        cosmos_settings.AzureCosmosDBforMongoDBSettings,
        "create",
        side_effect=validation_error,
    ):
        with pytest.raises(VectorStoreInitializationException) as exc_info:
            cosmos_collection.AzureCosmosDBforMongoDBCollection(
                collection_name="test_collection",
                data_model_type=dict,
                data_model_definition=mock_data_model_definition,
                database_name="",
            )
        assert "The Azure CosmosDB for MongoDB connection string is required." in str(exc_info.value)


async def test_constructor_raises_exception_if_no_connection_string() -> None:
    """
    Ensure that a VectorStoreInitializationException is raised if the
    AzureCosmosDBforMongoDBSettings.connection_string is None.
    """
    # Mock settings without a connection string
    mock_settings = AsyncMock(spec=cosmos_settings.AzureCosmosDBforMongoDBSettings)
    mock_settings.connection_string = None
    mock_settings.database_name = "some_database"

    with patch.object(cosmos_settings.AzureCosmosDBforMongoDBSettings, "create", return_value=mock_settings):
        with pytest.raises(VectorStoreInitializationException) as exc_info:
            cosmos_collection.AzureCosmosDBforMongoDBCollection(collection_name="test_collection", data_model_type=dict)
        assert "The Azure CosmosDB for MongoDB connection string is required." in str(exc_info.value)


async def test_create_collection_calls_database_methods() -> None:
    """
    Test create_collection to verify that it first creates a collection, then
    calls the appropriate command to create a vector index.
    """
    # Setup
    mock_database = AsyncMock()
    mock_database.create_collection = AsyncMock()
    mock_database.command = AsyncMock()

    mock_client = AsyncMock(spec=AsyncMongoClient)
    mock_client.get_database = MagicMock(return_value=mock_database)

    mock_data_model_definition = AsyncMock(spec=VectorStoreRecordDefinition)
    # Simulate a data_model_definition with certain fields & vector_fields
    mock_field = AsyncMock(spec=VectorStoreRecordDataField)
    type(mock_field).name = "test_field"
    type(mock_field).is_filterable = True
    type(mock_field).is_full_text_searchable = True

    type(mock_field).property_type = "str"

    mock_vector_field = AsyncMock()
    type(mock_vector_field).dimensions = 128
    type(mock_vector_field).name = "embedding"
    type(mock_vector_field).distance_function = DistanceFunction.COSINE_SIMILARITY
    type(mock_vector_field).index_kind = IndexKind.IVF_FLAT
    type(mock_vector_field).property_type = "float"

    mock_data_model_definition.fields = {"test_field": mock_field}
    mock_data_model_definition.vector_fields = [mock_vector_field]
    mock_data_model_definition.key_field = mock_field

    # Instantiate
    collection = cosmos_collection.AzureCosmosDBforMongoDBCollection(
        collection_name="test_collection",
        data_model_type=dict,
        data_model_definition=mock_data_model_definition,
        mongo_client=mock_client,
        database_name="test_db",
    )

    # Act
    await collection.create_collection(customArg="customValue")

    # Assert
    mock_database.create_collection.assert_awaited_once_with("test_collection", customArg="customValue")
    mock_database.command.assert_awaited()
    command_args = mock_database.command.call_args.kwargs["command"]

    assert command_args["createIndexes"] == "test_collection"
    assert len(command_args["indexes"]) == 2, "One for the data field, one for the vector field"
    # Check the data field index
    assert command_args["indexes"][0]["name"] == "test_field_"
    # Check the vector field index creation
    assert command_args["indexes"][1]["name"] == "embedding_"
    assert command_args["indexes"][1]["key"] == {"embedding": "cosmosSearch"}
    assert command_args["indexes"][1]["cosmosSearchOptions"]["kind"] == "vector-ivf"
    assert command_args["indexes"][1]["cosmosSearchOptions"]["similarity"] is not None
    assert command_args["indexes"][1]["cosmosSearchOptions"]["dimensions"] == 128


async def test_context_manager_calls_aconnect_and_close_when_managed() -> None:
    """
    Test that the context manager in AzureCosmosDBforMongoDBCollection calls 'aconnect' and
    'close' when the client is managed (i.e., created internally).
    """
    mock_client = AsyncMock(spec=AsyncMongoClient)

    mock_data_model_definition = VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(),
            "vector": VectorStoreRecordVectorField(),
        }
    )

    with patch(
        "semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_collection.AsyncMongoClient",
        return_value=mock_client,
    ):
        collection = cosmos_collection.AzureCosmosDBforMongoDBCollection(
            collection_name="test_collection",
            data_model_type=dict,
            connection_string="mongodb://fake",
            data_model_definition=mock_data_model_definition,
        )

    # "__aenter__" should call 'aconnect'
    async with collection as c:
        mock_client.aconnect.assert_awaited_once()
        assert c is collection

    # "__aexit__" should call 'close' if managed
    mock_client.close.assert_awaited_once()


async def test_context_manager_does_not_close_when_not_managed() -> None:
    """
    Test that the context manager in AzureCosmosDBforMongoDBCollection does not call 'close'
    when the client is not managed (i.e., provided externally).
    """
    mock_data_model_definition = VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(),
            "vector": VectorStoreRecordVectorField(),
        }
    )

    external_client = AsyncMock(spec=AsyncMongoClient, name="external_client", value=None)
    external_client.aconnect = AsyncMock(name="aconnect")
    external_client.close = AsyncMock(name="close")

    collection = cosmos_collection.AzureCosmosDBforMongoDBCollection(
        collection_name="test_collection",
        data_model_type=dict,
        mongo_client=external_client,
        data_model_definition=mock_data_model_definition,
    )

    # "__aenter__" scenario
    async with collection as c:
        external_client.aconnect.assert_awaited()
        assert c is collection

    # "__aexit__" should NOT call "close" when not managed
    external_client.close.assert_not_awaited()
