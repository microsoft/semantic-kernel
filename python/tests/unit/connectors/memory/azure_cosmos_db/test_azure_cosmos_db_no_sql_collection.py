# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError

from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_collection import (
    AzureCosmosDBNoSQLCollection,
)
from semantic_kernel.connectors.memory.azure_cosmos_db.const import COSMOS_ITEM_ID_PROPERTY_NAME
from semantic_kernel.connectors.memory.azure_cosmos_db.utils import (
    CosmosClientWrapper,
    create_default_indexing_policy,
    create_default_vector_embedding_policy,
)
from semantic_kernel.exceptions import (
    VectorStoreInitializationException,
)
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreModelException, VectorStoreOperationException


def test_azure_cosmos_db_no_sql_collection_init(
    clear_azure_cosmos_db_no_sql_env,
    data_model_type,
    database_name: str,
    collection_name: str,
    url: str,
    key: str,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLCollection object."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
        database_name=database_name,
        url=url,
        key=key,
    )

    assert vector_collection is not None
    assert vector_collection.database_name == database_name
    assert vector_collection.collection_name == collection_name
    assert vector_collection.cosmos_client is not None
    assert vector_collection.partition_key.path == f"/{vector_collection.data_model_definition.key_field_name}"
    assert vector_collection.create_database is False


def test_azure_cosmos_db_no_sql_collection_init_env(
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLCollection object with environment variables."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    assert vector_collection is not None
    assert (
        vector_collection.database_name == azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME"]
    )
    assert vector_collection.collection_name == collection_name
    assert vector_collection.partition_key.path == f"/{vector_collection.data_model_definition.key_field_name}"
    assert vector_collection.create_database is False


@pytest.mark.parametrize("exclude_list", [["AZURE_COSMOS_DB_NO_SQL_URL"]], indirect=True)
def test_azure_cosmos_db_no_sql_collection_init_no_url(
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLCollection object with missing URL."""
    with pytest.raises(VectorStoreInitializationException):
        AzureCosmosDBNoSQLCollection(
            data_model_type=data_model_type,
            collection_name=collection_name,
            env_file_path="fake_path",
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME"]], indirect=True)
def test_azure_cosmos_db_no_sql_collection_init_no_database_name(
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLCollection object with missing database name."""
    with pytest.raises(
        VectorStoreInitializationException, match="The name of the Azure Cosmos DB NoSQL database is missing."
    ):
        AzureCosmosDBNoSQLCollection(
            data_model_type=data_model_type,
            collection_name=collection_name,
            env_file_path="fake_path",
        )


def test_azure_cosmos_db_no_sql_collection_invalid_settings(
    clear_azure_cosmos_db_no_sql_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLCollection object with invalid settings."""
    with pytest.raises(VectorStoreInitializationException):
        AzureCosmosDBNoSQLCollection(
            data_model_type=data_model_type,
            collection_name=collection_name,
            url="invalid_url",
        )


@patch.object(CosmosClientWrapper, "__init__", return_value=None)
def test_azure_cosmos_db_no_sql_get_cosmos_client(
    mock_cosmos_client_init,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the creation of a cosmos client."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    assert vector_collection.cosmos_client is not None
    mock_cosmos_client_init.assert_called_once_with(
        str(azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_URL"]),
        credential=azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_KEY"],
    )


@patch.object(CosmosClientWrapper, "__init__", return_value=None)
def test_azure_cosmos_db_no_sql_get_cosmos_client_without_key(
    mock_cosmos_client_init,
    clear_azure_cosmos_db_no_sql_env,
    data_model_type,
    collection_name: str,
    database_name: str,
    url: str,
) -> None:
    """Test the creation of a cosmos client."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
        database_name=database_name,
        url=url,
    )

    assert vector_collection.cosmos_client is not None
    mock_cosmos_client_init.assert_called_once_with(url, credential=ANY)


@patch("azure.cosmos.aio.CosmosClient", spec=True)
async def test_azure_cosmos_db_no_sql_collection_create_database_if_not_exists(
    mock_cosmos_client,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the creation of a cosmos DB NoSQL database if it does not exist when create_database=True."""
    mock_cosmos_client.get_database_client.side_effect = CosmosResourceNotFoundError
    mock_cosmos_client.create_database = AsyncMock()

    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
        cosmos_client=mock_cosmos_client,
        create_database=True,
    )

    assert vector_collection.create_database is True

    await vector_collection._get_database_proxy()

    mock_cosmos_client.get_database_client.assert_called_once_with(
        azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME"]
    )
    mock_cosmos_client.create_database.assert_called_once_with(
        azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME"]
    )


@patch("azure.cosmos.aio.CosmosClient", spec=True)
async def test_azure_cosmos_db_no_sql_collection_create_database_raise_if_database_not_exists(
    mock_cosmos_client,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test _get_database_proxy raises an error if the database does not exist when create_database=False."""
    mock_cosmos_client.get_database_client.side_effect = CosmosResourceNotFoundError
    mock_cosmos_client.create_database = AsyncMock()

    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
        cosmos_client=mock_cosmos_client,
        create_database=False,
    )

    assert vector_collection.create_database is False

    with pytest.raises(VectorStoreOperationException):
        await vector_collection._get_database_proxy()


@patch("azure.cosmos.aio.CosmosClient")
@patch("azure.cosmos.aio.DatabaseProxy")
@pytest.mark.parametrize("index_kind, distance_function", [("flat", "cosine_similarity")])
async def test_azure_cosmos_db_no_sql_collection_create_collection(
    mock_database_proxy,
    mock_cosmos_client,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
):
    """Test the creation of a cosmos DB NoSQL collection."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    vector_collection._get_database_proxy = AsyncMock(return_value=mock_database_proxy)

    mock_database_proxy.create_container_if_not_exists = AsyncMock(return_value=None)

    await vector_collection.create_collection()

    mock_database_proxy.create_container_if_not_exists.assert_called_once_with(
        id=collection_name,
        partition_key=vector_collection.partition_key,
        indexing_policy=create_default_indexing_policy(vector_collection.data_model_definition),
        vector_embedding_policy=create_default_vector_embedding_policy(vector_collection.data_model_definition),
    )


@patch("azure.cosmos.aio.CosmosClient")
@patch("azure.cosmos.aio.DatabaseProxy")
@pytest.mark.parametrize("index_kind, distance_function", [("flat", "cosine_similarity")])
async def test_azure_cosmos_db_no_sql_collection_create_collection_allow_custom_indexing_policy(
    mock_database_proxy,
    mock_cosmos_client,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
):
    """Test the creation of a cosmos DB NoSQL collection with a custom indexing policy."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    vector_collection._get_database_proxy = AsyncMock(return_value=mock_database_proxy)

    mock_database_proxy.create_container_if_not_exists = AsyncMock(return_value=None)

    await vector_collection.create_collection(indexing_policy={"automatic": False})

    mock_database_proxy.create_container_if_not_exists.assert_called_once_with(
        id=collection_name,
        partition_key=vector_collection.partition_key,
        indexing_policy={"automatic": False},
        vector_embedding_policy=create_default_vector_embedding_policy(vector_collection.data_model_definition),
    )


@patch("azure.cosmos.aio.CosmosClient")
@patch("azure.cosmos.aio.DatabaseProxy")
@pytest.mark.parametrize("index_kind, distance_function", [("flat", "cosine_similarity")])
async def test_azure_cosmos_db_no_sql_collection_create_collection_allow_custom_vector_embedding_policy(
    mock_database_proxy,
    mock_cosmos_client,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
):
    """Test the creation of a cosmos DB NoSQL collection with a custom vector embedding policy."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    vector_collection._get_database_proxy = AsyncMock(return_value=mock_database_proxy)

    mock_database_proxy.create_container_if_not_exists = AsyncMock(return_value=None)

    await vector_collection.create_collection(vector_embedding_policy={"vectorEmbeddings": []})

    mock_database_proxy.create_container_if_not_exists.assert_called_once_with(
        id=collection_name,
        partition_key=vector_collection.partition_key,
        indexing_policy=create_default_indexing_policy(vector_collection.data_model_definition),
        vector_embedding_policy={"vectorEmbeddings": []},
    )


@patch("azure.cosmos.aio.CosmosClient")
@patch("azure.cosmos.aio.DatabaseProxy")
@pytest.mark.parametrize(
    "index_kind, distance_function, vector_property_type",
    [
        ("hnsw", "cosine_similarity", "float"),  # unsupported index kind
        ("flat", "hamming", "float"),  # unsupported distance function
        ("flat", "cosine_similarity", "double"),  # unsupported property type
    ],
)
async def test_azure_cosmos_db_no_sql_collection_create_collection_unsupported_vector_field_property(
    mock_database_proxy,
    mock_cosmos_client,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
):
    """Test the creation of a cosmos DB NoSQL collection with an unsupported index kind."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    vector_collection._get_database_proxy = AsyncMock(return_value=mock_database_proxy)

    mock_database_proxy.create_container_if_not_exists = AsyncMock(return_value=None)

    with pytest.raises(VectorStoreModelException):
        await vector_collection.create_collection()


@patch("azure.cosmos.aio.DatabaseProxy")
async def test_azure_cosmos_db_no_sql_collection_delete_collection(
    mock_database_proxy,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the deletion of a cosmos DB NoSQL collection."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    vector_collection._get_database_proxy = AsyncMock(return_value=mock_database_proxy)

    mock_database_proxy.delete_container = AsyncMock()

    await vector_collection.delete_collection()

    mock_database_proxy.delete_container.assert_called_once_with(collection_name)


@patch("azure.cosmos.aio.DatabaseProxy")
async def test_azure_cosmos_db_no_sql_collection_delete_collection_fail(
    mock_database_proxy,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the deletion of a cosmos DB NoSQL collection that does not exist."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    vector_collection._get_database_proxy = AsyncMock(return_value=mock_database_proxy)
    mock_database_proxy.delete_container = AsyncMock(side_effect=CosmosHttpResponseError)

    with pytest.raises(VectorStoreOperationException, match="Container could not be deleted."):
        await vector_collection.delete_collection()


@patch("azure.cosmos.aio.ContainerProxy")
async def test_azure_cosmos_db_no_sql_upsert(
    mock_container_proxy,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the upsert of a document in a cosmos DB NoSQL collection."""
    item = {"content": "test_content", "vector": [1.0, 2.0, 3.0], "id": "test_id"}

    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    vector_collection._get_container_proxy = AsyncMock(return_value=mock_container_proxy)

    mock_container_proxy.upsert_item = AsyncMock(return_value={COSMOS_ITEM_ID_PROPERTY_NAME: item["id"]})

    result = await vector_collection.upsert(item)

    mock_container_proxy.upsert_item.assert_called_once_with(item)
    assert result == item["id"]


@patch("azure.cosmos.aio.ContainerProxy")
async def test_azure_cosmos_db_no_sql_upsert_without_id(
    mock_container_proxy,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type_with_key_as_key_field,
    collection_name: str,
) -> None:
    """Test the upsert of a document in a cosmos DB NoSQL collection where the name of the key field is 'key'."""
    item = {"content": "test_content", "vector": [1.0, 2.0, 3.0], "key": "test_key"}
    item_with_id = {"content": "test_content", "vector": [1.0, 2.0, 3.0], COSMOS_ITEM_ID_PROPERTY_NAME: "test_key"}

    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type_with_key_as_key_field,
        collection_name=collection_name,
    )

    vector_collection._get_container_proxy = AsyncMock(return_value=mock_container_proxy)

    mock_container_proxy.upsert_item = AsyncMock(return_value={COSMOS_ITEM_ID_PROPERTY_NAME: item["key"]})

    result = await vector_collection.upsert(item)

    mock_container_proxy.upsert_item.assert_called_once_with(item_with_id)
    assert result == item["key"]


@patch("azure.cosmos.aio.ContainerProxy")
async def test_azure_cosmos_db_no_sql_get(
    mock_container_proxy,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the retrieval of a document from a cosmos DB NoSQL collection."""
    vector_collection: AzureCosmosDBNoSQLCollection[str, data_model_type] = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    )

    vector_collection._get_container_proxy = AsyncMock(return_value=mock_container_proxy)

    get_results = MagicMock(spec=AsyncGenerator)
    get_results.__aiter__.return_value = [{"content": "test_content", "vector": [1.0, 2.0, 3.0], "id": "test_id"}]
    mock_container_proxy.query_items.return_value = get_results

    record = await vector_collection.get("test_id")
    assert isinstance(record, data_model_type)
    assert record.content == "test_content"
    assert record.vector == [1.0, 2.0, 3.0]
    assert record.id == "test_id"


@patch("azure.cosmos.aio.ContainerProxy")
async def test_azure_cosmos_db_no_sql_get_without_id(
    mock_container_proxy,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type_with_key_as_key_field,
    collection_name: str,
) -> None:
    """Test the retrieval of a document from a cosmos DB NoSQL collection where the name of the key field is 'key'."""
    vector_collection = AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type_with_key_as_key_field,
        collection_name=collection_name,
    )

    vector_collection._get_container_proxy = AsyncMock(return_value=mock_container_proxy)

    get_results = MagicMock(spec=AsyncGenerator)
    get_results.__aiter__.return_value = [
        {"content": "test_content", "vector": [1.0, 2.0, 3.0], COSMOS_ITEM_ID_PROPERTY_NAME: "test_key"}
    ]
    mock_container_proxy.query_items.return_value = get_results

    record = await vector_collection.get("test_key")
    assert isinstance(record, data_model_type_with_key_as_key_field)
    assert record.content == "test_content"
    assert record.vector == [1.0, 2.0, 3.0]
    assert record.key == "test_key"


@patch.object(CosmosClientWrapper, "close", return_value=None)
async def test_client_is_closed(
    mock_cosmos_client_close,
    azure_cosmos_db_no_sql_unit_test_env,
    data_model_type,
    collection_name: str,
) -> None:
    """Test the close method of an AzureCosmosDBNoSQLCollection object."""
    async with AzureCosmosDBNoSQLCollection(
        data_model_type=data_model_type,
        collection_name=collection_name,
    ) as collection:
        assert collection.cosmos_client is not None

    mock_cosmos_client_close.assert_called()
