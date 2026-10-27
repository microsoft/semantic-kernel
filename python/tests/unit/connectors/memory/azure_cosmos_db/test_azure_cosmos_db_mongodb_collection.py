# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo import AsyncMongoClient

from semantic_kernel.connectors.azure_cosmos_db import CosmosMongoCollection
from semantic_kernel.data.vector import VectorStoreCollectionDefinition, VectorStoreField
from semantic_kernel.exceptions import VectorStoreInitializationException


@pytest.fixture
def mock_model() -> VectorStoreCollectionDefinition:
    return VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id"),
            VectorStoreField("data", name="content"),
            VectorStoreField("vector", name="vector", dimensions=5),
        ]
    )


async def test_constructor_with_mongo_client_provided(mock_model) -> None:
    """
    Test the constructor of AzureCosmosDBforMongoDBCollection when a mongo_client
    is directly provided. Expect that the class is successfully initialized
    and doesn't attempt to manage the client.
    """
    mock_client = AsyncMock(spec=AsyncMongoClient)
    collection_name = "test_collection"

    collection = CosmosMongoCollection(
        collection_name=collection_name,
        record_type=dict,
        mongo_client=mock_client,
        definition=mock_model,
    )

    assert collection.mongo_client == mock_client
    assert collection.collection_name == collection_name
    assert not collection.managed_client, "Should not be managing client when provided"


@pytest.mark.parametrize("exclude_list", [["AZURE_COSMOS_DB_MONGODB_CONNECTION_STRING"]], indirect=True)
async def test_constructor_raises_exception_on_validation_error(
    azure_cosmos_db_mongo_db_unit_test_env, definition
) -> None:
    """
    Test that the constructor raises VectorStoreInitializationException when
    AzureCosmosDBforMongoDBSettings fails with ValidationError.
    """
    with pytest.raises(VectorStoreInitializationException) as exc_info:
        CosmosMongoCollection(
            collection_name="test_collection",
            record_type=dict,
            definition=definition,
            database_name="",
            env_file_path=".no.env",
        )
        assert "The Azure CosmosDB for MongoDB connection string is required." in str(exc_info.value)


async def test_ensure_collection_exists_calls_database_methods(definition) -> None:
    """
    Test ensure_collection_exists to verify that it first creates a collection, then
    calls the appropriate command to create a vector index.
    """
    # Setup
    mock_database = AsyncMock()
    mock_database.create_collection = AsyncMock()
    mock_database.command = AsyncMock()

    mock_client = AsyncMock(spec=AsyncMongoClient)
    mock_client.get_database = MagicMock(return_value=mock_database)

    # Instantiate
    collection = CosmosMongoCollection(
        collection_name="test_collection",
        record_type=dict,
        definition=definition,
        mongo_client=mock_client,
        database_name="test_db",
    )

    # Act
    await collection.ensure_collection_exists(customArg="customValue")

    # Assert
    mock_database.create_collection.assert_awaited_once_with("test_collection", customArg="customValue")
    mock_database.command.assert_awaited()
    command_args = mock_database.command.call_args.kwargs["command"]

    assert command_args["createIndexes"] == "test_collection"
    assert len(command_args["indexes"]) == 2, "One for the data field, one for the vector field"
    # Check the data field index
    assert command_args["indexes"][0]["name"] == "content_"
    # Check the vector field index creation
    assert command_args["indexes"][1]["name"] == "vector_"
    assert command_args["indexes"][1]["key"] == {"vector": "cosmosSearch"}
    # "kind" must be the index kind ("vector-hnsw" for index_kind="hnsw"),
    # not the distance-function similarity code ("COS").
    # See https://github.com/microsoft/semantic-kernel/issues/14104
    assert command_args["indexes"][1]["cosmosSearchOptions"]["kind"] == "vector-hnsw"
    assert command_args["indexes"][1]["cosmosSearchOptions"]["similarity"] == "COS"
    assert command_args["indexes"][1]["cosmosSearchOptions"]["dimensions"] == 5


async def test_context_manager_calls_aconnect_and_close_when_managed(mock_model) -> None:
    """
    Test that the context manager in AzureCosmosDBforMongoDBCollection calls 'aconnect' and
    'close' when the client is managed (i.e., created internally).
    """
    mock_client = AsyncMock(spec=AsyncMongoClient)

    with patch(
        "semantic_kernel.connectors.azure_cosmos_db.AsyncMongoClient",
        return_value=mock_client,
    ):
        collection = CosmosMongoCollection(
            collection_name="test_collection",
            record_type=dict,
            connection_string="mongodb://fake",
            definition=mock_model,
        )

    # "__aenter__" should call 'aconnect'
    async with collection as c:
        mock_client.aconnect.assert_awaited_once()
        assert c is collection

    # "__aexit__" should call 'close' if managed
    mock_client.close.assert_awaited_once()


async def test_context_manager_does_not_close_when_not_managed(mock_model) -> None:
    """
    Test that the context manager in AzureCosmosDBforMongoDBCollection does not call 'close'
    when the client is not managed (i.e., provided externally).
    """

    external_client = AsyncMock(spec=AsyncMongoClient, name="external_client", value=None)
    external_client.aconnect = AsyncMock(name="aconnect")
    external_client.close = AsyncMock(name="close")

    collection = CosmosMongoCollection(
        collection_name="test_collection",
        record_type=dict,
        mongo_client=external_client,
        definition=mock_model,
    )

    # "__aenter__" scenario
    async with collection as c:
        external_client.aconnect.assert_awaited()
        assert c is collection

    # "__aexit__" should NOT call "close" when not managed
    external_client.close.assert_not_awaited()


def test_get_index_definitions_uses_index_kind_for_kind() -> None:
    """Regression test for https://github.com/microsoft/semantic-kernel/issues/14104.

    The "kind" of a Cosmos DB for MongoDB vector index must come from
    INDEX_KIND_MAP_MONGODB (e.g. "vector-hnsw"), not from the distance
    function map ("COS"/"IP"/"L2"). Using the similarity code as "kind"
    sends an invalid createIndexes command and also prevents the
    HNSW/IVF/DiskANN tuning options from being attached (the `match`
    block could never hit a "vector-*" case).
    """
    from semantic_kernel.data.vector import DistanceFunction, IndexKind

    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id"),
            VectorStoreField("data", name="content"),
            VectorStoreField(
                "vector",
                name="vector",
                dimensions=4,
                index_kind=IndexKind.HNSW,
                distance_function=DistanceFunction.COSINE_SIMILARITY,
            ),
        ]
    )
    collection = CosmosMongoCollection(
        collection_name="test_collection",
        record_type=dict,
        mongo_client=AsyncMock(spec=AsyncMongoClient),
        definition=definition,
    )

    result = collection._get_index_definitions(m=16, efConstruction=64)
    vector_index = next(i for i in result["indexes"] if "cosmosSearchOptions" in i)
    options = vector_index["cosmosSearchOptions"]

    assert options["kind"] == "vector-hnsw"
    assert options["similarity"] == "COS"
    assert options["dimensions"] == 4
    assert options["m"] == 16
    assert options["efConstruction"] == 64
