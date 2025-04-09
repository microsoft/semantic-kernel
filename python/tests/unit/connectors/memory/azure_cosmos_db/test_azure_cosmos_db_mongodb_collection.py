# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError
from pydantic.errors import ErrorWrapper
from pymongo import AsyncMongoClient

import semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_collection as cosmos_collection
import semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_settings as cosmos_settings
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import VectorStoreInitializationException


class FakeDataModel:
    """
    A fake data model class to satisfy the "type" requirement for data_model_type.
    """

    pass


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
        data_model_type=FakeDataModel,
        mongo_client=mock_client,
        data_model_definition=fake_definition,
    )

    assert collection.mongo_client == mock_client
    assert collection.collection_name == collection_name
    assert not collection.managed_client, "Should not be managing client when provided"


async def test_constructor_without_mongo_client_success() -> None:
    """
    Test the constructor of AzureCosmosDBforMongoDBCollection when a mongo_client
    is not provided. Expect it to create settings and initialize an AsyncMongoClient.
    """
    mock_data_model_definition = VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(),
            "vector": VectorStoreRecordVectorField(),
        }
    )

    fake_client = AsyncMock(name="fake_async_client", spec=AsyncMongoClient)

    with (
        patch.object(
            cosmos_settings.AzureCosmosDBforMongoDBSettings,
            "create",
            return_value=AsyncMock(
                connection_string=AsyncMock(get_secret_value=lambda: "mongodb://test"), database_name="test_db"
            ),
        ) as mock_settings_create,
        patch(
            "semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_collection.AsyncMongoClient",
            return_value=fake_client,
            spec=AsyncMongoClient,
        ) as mock_async_client,
    ):
        collection = cosmos_collection.AzureCosmosDBforMongoDBCollection(
            collection_name="test_collection",
            data_model_type=FakeDataModel,
            data_model_definition=mock_data_model_definition,
            connection_string="mongodb://test-env",
            database_name="",
        )

    mock_settings_create.assert_called_once()
    mock_async_client.assert_called_once()

    created_client = mock_async_client.return_value

    assert collection.mongo_client == created_client
    assert collection.managed_client, "Should manage client when none is provided"
    assert collection.database_name == "test_db"


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

    errors = [
        ErrorWrapper(
            exc=ValueError("field required"),
            loc=("connection_string",),
            msg="field required",
            type="missing",
        )
    ]

    validation_error = ValidationError(errors, DummyModel)

    with patch.object(
        cosmos_settings.AzureCosmosDBforMongoDBSettings,
        "create",
        side_effect=validation_error,
    ):
        with pytest.raises(VectorStoreInitializationException) as exc_info:
            cosmos_collection.AzureCosmosDBforMongoDBCollection(
                collection_name="test_collection",
                data_model_type=FakeDataModel,
                data_model_definition=mock_data_model_definition,
                connection_string="mongodb://test-env",
                database_name="",
            )
        assert "Failed to create Azure CosmosDB for MongoDB settings." in str(exc_info.value)


@pytest.mark.asyncio
async def test_constructor_raises_exception_if_no_connection_string() -> None:
    """
    Ensure that a VectorStoreInitializationException is raised if the
    AzureCosmosDBforMongoDBSettings.connection_string is None.
    """
    # Mock settings without a connection string
    mock_settings = MagicMock()
    type(mock_settings.connection_string).get_secret_value.return_value = None
    mock_settings.database_name = "some_database"

    with patch.object(cosmos_settings.AzureCosmosDBforMongoDBSettings, "create", return_value=mock_settings):
        with pytest.raises(VectorStoreInitializationException) as exc_info:
            cosmos_collection.AzureCosmosDBforMongoDBCollection(
                collection_name="test_collection", data_model_type=FakeDataModel
            )
        assert "The Azure CosmosDB for MongoDB connection string is required." in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_collection_calls_database_methods() -> None:
    """
    Test create_collection to verify that it first creates a collection, then
    calls the appropriate command to create a vector index.
    """
    # Setup
    mock_database = AsyncMock()
    mock_database.create_collection = AsyncMock()
    mock_database.command = AsyncMock()

    mock_client = MagicMock()
    mock_client.get_database = MagicMock(return_value=mock_database)

    mock_data_model_definition = MagicMock()
    # Simulate a data_model_definition with certain fields & vector_fields
    mock_field = MagicMock()
    type(mock_field).name = "test_field"
    type(mock_field).is_filterable = True
    type(mock_field).is_full_text_searchable = True

    mock_vector_field = MagicMock()
    type(mock_vector_field).dimensions = 128
    type(mock_vector_field).name = "embedding"
    type(mock_vector_field).distance_function = "Euclidean"
    type(mock_vector_field).index_kind = "IVF"

    mock_data_model_definition.fields = {"test_field": mock_field}
    mock_data_model_definition.vector_fields = [mock_vector_field]

    # Instantiate
    collection = cosmos_collection.AzureCosmosDBforMongoDBCollection(
        collection_name="test_collection",
        data_model_type=FakeDataModel,
        data_model_definition=mock_data_model_definition,
        mongo_client=mock_client,
        database_name="test_db",
    )

    # Act
    await collection.create_collection(customArg="customValue")

    # Assert
    mock_database.create_collection.assert_awaited_once_with("test_collection", customArg="customValue")
    mock_database.command.assert_awaited()
    command_args = mock_database.command.call_args[0][0]

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


@pytest.mark.asyncio
async def test_context_manager_calls_aconnect_and_close_when_managed() -> None:
    """
    Test that the context manager in AzureCosmosDBforMongoDBCollection calls 'aconnect' and
    'close' when the client is managed (i.e., created internally).
    """
    mock_client = AsyncMock()

    with patch("pymongo.AsyncMongoClient", return_value=mock_client):
        collection = cosmos_collection.AzureCosmosDBforMongoDBCollection(
            collection_name="test_collection",
            data_model_type=FakeDataModel,
            connection_string="mongodb://fake",
        )

    # "__aenter__" should call 'aconnect'
    async with collection as c:
        mock_client.aconnect.assert_awaited_once()
        assert c is collection

    # "__aexit__" should call 'close' if managed
    mock_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_context_manager_does_not_close_when_not_managed() -> None:
    """
    Test that the context manager in AzureCosmosDBforMongoDBCollection does not call 'close'
    when the client is not managed (i.e., provided externally).
    """
    external_client = AsyncMock()

    collection = cosmos_collection.AzureCosmosDBforMongoDBCollection(
        collection_name="test_collection",
        data_model_type=FakeDataModel,
        mongo_client=external_client,
    )

    # "__aenter__" scenario
    async with collection as c:
        # Should not call aconnect on external client by design.
        external_client.aconnect.assert_not_awaited()
        assert c is collection

    # "__aexit__" should NOT call "close" when not managed
    external_client.close.assert_not_awaited()
