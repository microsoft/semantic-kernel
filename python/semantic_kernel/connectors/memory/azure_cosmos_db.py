# Copyright (c) Microsoft. All rights reserved.

# The name of the property that will be used as the item id in Azure Cosmos DB NoSQL
import asyncio
import sys
from collections.abc import AsyncIterable, Callable, Sequence
from importlib import metadata
from typing import Any, ClassVar, Final, Generic

from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError
from azure.cosmos.partition_key import PartitionKey
from pydantic import HttpUrl, SecretStr, ValidationError
from pymongo import AsyncMongoClient
from pymongo.driver_info import DriverInfo
from typing_extensions import override

from semantic_kernel.connectors.memory.mongodb import (
    DEFAULT_DB_NAME,
    MONGODB_SCORE_FIELD,
    MongoDBAtlasCollection,
    MongoDBAtlasStore,
)
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import VectorSearch, VectorSearchOptions, VectorSearchResult
from semantic_kernel.data.vector_storage import (
    GetFilteredRecordOptions,
    TKey,
    TModel,
    VectorStore,
    VectorStoreRecordCollection,
)
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreModelDeserializationException,
    VectorStoreModelException,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel, KernelBaseSettings
from semantic_kernel.utils.authentication.async_default_azure_credential_wrapper import (
    AsyncDefaultAzureCredentialWrapper,
)
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

# region: Constants

COSMOS_ITEM_ID_PROPERTY_NAME: Final[str] = "id"
INDEX_KIND_MAPPING: Final[dict[IndexKind, str]] = {
    IndexKind.FLAT: "flat",
    IndexKind.QUANTIZED_FLAT: "quantizedFlat",
    IndexKind.DISK_ANN: "diskANN",
    IndexKind.DEFAULT: "flat",
}
INDEX_KIND_MAPPING_MONGODB: Final[dict[IndexKind, str]] = {
    IndexKind.IVF_FLAT: "vector-ivf",
    IndexKind.HNSW: "vector-hnsw",
    IndexKind.DISK_ANN: "vector-diskann",
    IndexKind.DEFAULT: "vector-ivf",
}
DISTANCE_FUNCTION_MAPPING: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.COSINE_SIMILARITY: "cosine",
    DistanceFunction.DOT_PROD: "dotproduct",
    DistanceFunction.EUCLIDEAN_DISTANCE: "euclidean",
    DistanceFunction.DEFAULT: "cosine",
}
DISTANCE_FUNCTION_MAPPING_MONGODB: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.COSINE_SIMILARITY: "COS",
    DistanceFunction.DOT_PROD: "IP",
    DistanceFunction.EUCLIDEAN_DISTANCE: "L2",
    DistanceFunction.DEFAULT: "COS",
}
DATATYPES_MAPPING: Final[dict[str, str]] = {
    "default": "float32",
    "float": "float32",
    "list[float]": "float32",
    "int": "int32",
    "list[int]": "int32",
}

# region: Helpers


def _to_datatype(property_type: str | None) -> str:
    """Converts the property type to the data type for Azure Cosmos DB NoSQL container.

    Args:
        property_type: The property type.

    Returns:
        str: The data type as defined by Azure Cosmos DB NoSQL container.

    Raises:
        VectorStoreModelException: If the property type is not supported by Azure Cosmos DB NoSQL container

    """
    if property_type is None:
        # Use the default data type.
        return DATATYPES_MAPPING["default"]

    if property_type in DATATYPES_MAPPING:
        return DATATYPES_MAPPING[property_type]

    raise VectorStoreModelException(
        f"Property type '{property_type}' is not supported by Azure Cosmos DB NoSQL container."
    )


def _create_default_indexing_policy(data_model_definition: VectorStoreRecordDefinition) -> dict[str, Any]:
    """Creates a default indexing policy for the Azure Cosmos DB NoSQL container.

    A default indexing policy is created based on the data model definition and has an automatic indexing policy.

    Args:
        data_model_definition (VectorStoreRecordDefinition): The definition of the data model.

    Returns:
        dict[str, Any]: The indexing policy.

    Raises:
        VectorStoreModelException: If the field is not full text searchable and not filterable.
    """
    indexing_policy: dict[str, Any] = {
        "automatic": True,
        "includedPaths": [
            {
                "path": "/*",
            }
        ],
        "excludedPaths": [
            {
                "path": '/"_etag"/?',
            }
        ],
        "vectorIndexes": [],
    }

    for field in data_model_definition.fields:
        if isinstance(field, VectorStoreRecordDataField) and (not field.is_full_text_indexed and not field.is_indexed):
            indexing_policy["excludedPaths"].append({"path": f'/"{field.storage_property_name or field.name}"/*'})

        if isinstance(field, VectorStoreRecordVectorField):
            if field.index_kind not in INDEX_KIND_MAPPING:
                raise VectorStoreModelException(
                    f"Index kind '{field.index_kind}' is not supported by Azure Cosmos DB NoSQL container."
                )
            indexing_policy["vectorIndexes"].append({
                "path": f'/"{field.storage_property_name or field.name}"',
                "type": INDEX_KIND_MAPPING[field.index_kind],
            })
            # Exclude the vector field from the index for performance optimization.
            indexing_policy["excludedPaths"].append({"path": f'/"{field.storage_property_name or field.name}"/*'})

    return indexing_policy


def _create_default_vector_embedding_policy(data_model_definition: VectorStoreRecordDefinition) -> dict[str, Any]:
    """Creates a default vector embedding policy for the Azure Cosmos DB NoSQL container.

    A default vector embedding policy is created based on the data model definition.

    Args:
        data_model_definition (VectorStoreRecordDefinition): The definition of the data model.

    Returns:
        dict[str, Any]: The vector embedding policy.

    Raises:
        VectorStoreModelException: If the datatype or distance function is not supported by Azure Cosmos DB NoSQL.

    """
    vector_embedding_policy: dict[str, Any] = {"vectorEmbeddings": []}

    for field in data_model_definition.fields:
        if isinstance(field, VectorStoreRecordVectorField):
            if field.distance_function not in DISTANCE_FUNCTION_MAPPING:
                raise VectorStoreModelException(
                    f"Distance function '{field.distance_function}' is not supported by Azure Cosmos DB NoSQL."
                )
            vector_embedding_policy["vectorEmbeddings"].append({
                "path": f'/"{field.storage_property_name or field.name}"',
                "dataType": _to_datatype(field.property_type),
                "distanceFunction": DISTANCE_FUNCTION_MAPPING[field.distance_function],
                "dimensions": field.dimensions,
            })

    return vector_embedding_policy


@experimental
class AzureCosmosDBNoSQLCompositeKey(KernelBaseModel):
    """Azure CosmosDB NoSQL composite key."""

    partition_key: str
    key: str


def _get_key(key: str | AzureCosmosDBNoSQLCompositeKey) -> str:
    """Gets the key value from the key.

    Args:
        key (str | AzureCosmosDBNoSQLCompositeKey): The key.

    Returns:
        str: The key.
    """
    if isinstance(key, AzureCosmosDBNoSQLCompositeKey):
        return key.key

    return key


def _get_partition_key(key: str | AzureCosmosDBNoSQLCompositeKey) -> str:
    """Gets the partition key value from the key.

    Args:
        key (str | AzureCosmosDBNoSQLCompositeKey): The key.

    Returns:
        str: The partition key.
    """
    if isinstance(key, AzureCosmosDBNoSQLCompositeKey):
        return key.partition_key

    return key


# region: Settings


@experimental
class AzureCosmosDBforMongoDBSettings(KernelBaseSettings):
    """Azure CosmosDB for MongoDB settings.

    The settings are first loaded from environment variables with
    the prefix 'AZURE_COSMOS_DB_MONGODB_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'AZURE_COSMOS_DB_MONGODB_':
    - connection_string:  The connection string of the Azure CosmosDB for MongoDB account.
       This value can be found in the Keys & Endpoint section when examining
       your resource from the Azure portal.
       (Env var name: AZURE_COSMOS_DB_MONGODB_CONNECTION_STRING)
    - database_name: str - The name of the database. Please refer to this documentation
       on Azure CosmosDB NoSQL resource model:
       https://learn.microsoft.com/en-us/azure/cosmos-db/resource-model
       (Env var name: AZURE_COSMOS_DB_MONGODB_DATABASE_NAME)
    """

    env_prefix: ClassVar[str] = "AZURE_COSMOS_DB_MONGODB_"

    connection_string: SecretStr | None = None
    database_name: str = DEFAULT_DB_NAME


@experimental
class AzureCosmosDBNoSQLSettings(KernelBaseSettings):
    """Azure CosmosDB NoSQL settings.

    The settings are first loaded from environment variables with
    the prefix 'AZURE_COSMOS_DB_NO_SQL_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'AZURE_COSMOS_DB_NO_SQL_':
    - url: HttpsUrl - The uri of the Azure CosmosDB NoSQL account.
       This value can be found in the Keys & Endpoint section when examining
       your resource from the Azure portal.
       (Env var name: AZURE_COSMOS_DB_NO_SQL_URL)

    Optional settings for prefix 'AZURE_COSMOS_DB_NO_SQL_':
    - key: SecretStr - The primary key of the Azure CosmosDB NoSQL account.
       This value can be found in the Keys & Endpoint section when examining
       your resource from the Azure portal.
       (Env var name: AZURE_COSMOS_DB_NO_SQL_KEY)
    - database_name: str - The name of the database. Please refer to this documentation
       on Azure CosmosDB NoSQL resource model:
       https://learn.microsoft.com/en-us/azure/cosmos-db/resource-model
       (Env var name: AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME)
    """

    env_prefix: ClassVar[str] = "AZURE_COSMOS_DB_NO_SQL_"

    url: HttpUrl
    key: SecretStr | None = None
    database_name: str | None = None


# region: Mongo Collection


@experimental
class AzureCosmosDBforMongoDBCollection(MongoDBAtlasCollection[TKey, TModel], Generic[TKey, TModel]):
    """Azure Cosmos DB for MongoDB collection."""

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        mongo_client: AsyncMongoClient | None = None,
        connection_string: str | None = None,
        database_name: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the AzureCosmosDBforMongoDBCollection class.

        Args:
            data_model_type: The type of the data model.
            data_model_definition: The model definition, optional.
            collection_name: The name of the collection, optional.
            mongo_client: The MongoDB client for interacting with Azure CosmosDB for MongoDB,
                used for creating and deleting collections.
            connection_string: The connection string for MongoDB Atlas, optional.
            Can be read from environment variables.
            database_name: The name of the database, will be filled from the env when this is not set.
            connection_string: str | None = None,
            env_file_path: str | None = None,
            env_file_encoding: str | None = None
            **kwargs: Additional keyword arguments

        """
        managed_client = not mongo_client
        if mongo_client:
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                mongo_client=mongo_client,
                collection_name=collection_name,
                database_name=database_name or DEFAULT_DB_NAME,
                managed_client=managed_client,
            )
            return

        try:
            settings = AzureCosmosDBforMongoDBSettings(
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                connection_string=connection_string,
                database_name=database_name,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create Azure CosmosDB for MongoDB settings.") from exc
        if not settings.connection_string:
            raise VectorStoreInitializationException("The Azure CosmosDB for MongoDB connection string is required.")

        mongo_client = AsyncMongoClient(
            settings.connection_string.get_secret_value(),
            driver=DriverInfo(SEMANTIC_KERNEL_USER_AGENT, metadata.version("semantic-kernel")),
        )

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=settings.database_name,
        )

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new collection in Azure CosmosDB for MongoDB.

        This first creates a collection, with the kwargs.
        Then creates a search index based on the data model definition.

        By the naming convection of MongoDB indexes are created by using the field name
        with a underscore.

        Args:
            **kwargs: Additional keyword arguments.
                These are the additional keyword arguments for creating
                vector indexes in Azure Cosmos DB for MongoDB.
                And they depend on the kind of index you are creating.
                See https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search
                for more information.
                Other kwargs are passed to the create_collection method.
        """
        await self._get_database().create_collection(self.collection_name, **kwargs)
        await self._get_database().command(command=self._get_vector_index(**kwargs))

    def _get_vector_index(self, **kwargs: Any) -> dict[str, Any]:
        indexes = [
            {"name": f"{field.name}_", "key": {field.name: 1}}
            for field in self.data_model_definition.fields
            if isinstance(field, VectorStoreRecordDataField) and (field.is_indexed or field.is_full_text_indexed)
        ]
        for vector_field in self.data_model_definition.vector_fields:
            index_name = f"{vector_field.name}_"

            similarity = (
                DISTANCE_FUNCTION_MAPPING_MONGODB.get(vector_field.distance_function)
                if vector_field.distance_function
                else "COS"
            )
            kind = INDEX_KIND_MAPPING_MONGODB.get(vector_field.index_kind) if vector_field.index_kind else "vector-ivf"
            if similarity is None:
                raise VectorStoreInitializationException(f"Invalid distance function: {vector_field.distance_function}")
            if kind is None:
                raise VectorStoreInitializationException(f"Invalid index kind: {vector_field.index_kind}")
            index: dict[str, Any] = {
                "name": index_name,
                "key": {vector_field.name: "cosmosSearch"},
                "cosmosSearchOptions": {
                    "kind": kind,
                    "similarity": similarity,
                    "dimensions": vector_field.dimensions,
                },
            }
            match kind:
                case "vector-diskann":
                    if "maxDegree" in kwargs:
                        index["cosmosSearchOptions"]["maxDegree"] = kwargs["maxDegree"]
                    if "lBuild" in kwargs:
                        index["cosmosSearchOptions"]["lBuild"] = kwargs["lBuild"]
                case "vector-hnsw":
                    if "m" in kwargs:
                        index["cosmosSearchOptions"]["m"] = kwargs["m"]
                    if "efConstruction" in kwargs:
                        index["cosmosSearchOptions"]["efConstruction"] = kwargs["efConstruction"]
                case "vector-ivf":
                    if "numList" in kwargs:
                        index["cosmosSearchOptions"]["numList"] = kwargs["numList"]
            indexes.append(index)

        return {"createIndexes": self.collection_name, "indexes": indexes}

    @override
    async def _inner_vector_search(
        self,
        options: VectorSearchOptions,
        vector: list[float | int],
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        collection = self._get_collection()
        vector_search_query: dict[str, Any] = {
            "k": options.top + options.skip,
            "index": f"{options.vector_field_name}_",
            "vector": vector,
            "path": options.vector_field_name,
        }
        if options.filter and (filter := self._build_filter_dict(options.filter)):
            vector_search_query["filter"] = filter
        projection_query: dict[str, int | dict] = {
            field: 1
            for field in self.data_model_definition.get_field_names(
                include_vector_fields=options.include_vectors,
                include_key_field=False,  # _id is always included
            )
        }
        projection_query[MONGODB_SCORE_FIELD] = {"$meta": "searchScore"}
        try:
            raw_results = await collection.aggregate([
                {"$search": {"cosmosSearch": vector_search_query}},
                {"$project": projection_query},
            ])
        except Exception as exc:
            raise VectorSearchExecutionException("Failed to search the collection.") from exc
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(raw_results, options),
            total_count=None,  # no way to get a count before looping through the result cursor
        )

    async def _get_vector_search_results_from_cursor(
        self,
        filter: dict[str, Any],
        projection: dict[str, int | dict],
        options: VectorSearchOptions | None = None,
    ) -> AsyncIterable[VectorSearchResult[TModel]]:
        collection = self._get_collection()
        async for result in collection.find(
            filter=filter,
            projection=projection,
            skip=options.skip if options else 0,
            limit=options.top if options else 0,
        ):
            try:
                record = self.deserialize(
                    self._get_record_from_result(result), include_vectors=options.include_vectors if options else True
                )
            except VectorStoreModelDeserializationException:
                raise
            except Exception as exc:
                raise VectorStoreModelDeserializationException(
                    f"An error occurred while deserializing the record: {exc}"
                ) from exc
            score = self._get_score_from_result(result)
            if record:
                # single records are always returned as single records by the deserializer
                yield VectorSearchResult(record=record, score=score)  # type: ignore


# region: Mongo Store


@experimental
class AzureCosmosDBforMongoDBStore(MongoDBAtlasStore):
    """Azure Cosmos DB for MongoDB store implementation."""

    def __init__(
        self,
        connection_string: str | None = None,
        database_name: str | None = None,
        mongo_client: AsyncMongoClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the AzureCosmosDBforMongoDBStore client.

        Args:
        connection_string (str): The connection string for Azure CosmosDB for MongoDB, optional.
            Can be read from environment variables.
        database_name (str): The name of the database, optional. Can be read from environment variables.
        mongo_client (MongoClient): The MongoDB client, optional.
        env_file_path (str): Use the environment settings file as a fallback
            to environment variables.
        env_file_encoding (str): The encoding of the environment settings file.

        """
        managed_client: bool = not mongo_client
        if mongo_client:
            super().__init__(
                mongo_client=mongo_client,
                managed_client=managed_client,
                database_name=database_name or DEFAULT_DB_NAME,
            )
            return
        from semantic_kernel.connectors.memory.azure_cosmos_db import AzureCosmosDBforMongoDBSettings

        try:
            settings = AzureCosmosDBforMongoDBSettings(
                env_file_path=env_file_path,
                connection_string=connection_string,
                database_name=database_name,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create MongoDB Atlas settings.") from exc
        if not settings.connection_string:
            raise VectorStoreInitializationException("The connection string is missing.")

        mongo_client = AsyncMongoClient(
            settings.connection_string.get_secret_value(),
            driver=DriverInfo(SEMANTIC_KERNEL_USER_AGENT, metadata.version("semantic-kernel")),
        )

        super().__init__(
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=settings.database_name,
        )

    @override
    def get_collection(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        return AzureCosmosDBforMongoDBCollection(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            mongo_client=self.mongo_client,
            collection_name=collection_name,
            database_name=self.database_name,
            **kwargs,
        )


# region: NoSQL Base


@experimental
class AzureCosmosDBNoSQLBase(KernelBaseModel):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    cosmos_client: CosmosClient
    database_name: str
    cosmos_db_nosql_settings: AzureCosmosDBNoSQLSettings
    # If create_database is True, the database will be created
    # if it does not exist when an operation requires a database.
    create_database: bool

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
        database_name: str | None = None,
        cosmos_client: CosmosClient | None = None,
        create_database: bool = False,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs,
    ):
        """Initialize the AzureCosmosDBNoSQLBase.

        Args:
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            database_name (str): The name of the database. The database may not exist yet. If it does not exist,
                                 it will be created when the first collection is created. Defaults to None.
            cosmos_client (CosmosClient): The custom Azure Cosmos DB NoSQL client whose lifetime is managed by the user.
                                          Defaults to None.
            create_database (bool): If True, the database will be created if it does not exist.
                                    Defaults to False.
            env_file_path (str): The path to the .env file. Defaults to None.
            env_file_encoding (str): The encoding of the .env file. Defaults to None.
            kwargs: Additional keyword arguments.
        """
        try:
            cosmos_db_nosql_settings = AzureCosmosDBNoSQLSettings(
                url=url,
                key=key,
                database_name=database_name,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise VectorStoreInitializationException("Failed to validate Azure Cosmos DB NoSQL settings.") from e

        if cosmos_db_nosql_settings.database_name is None:
            raise VectorStoreInitializationException("The name of the Azure Cosmos DB NoSQL database is missing.")

        if cosmos_client is None:
            if cosmos_db_nosql_settings.key is not None:
                cosmos_client = CosmosClient(
                    str(cosmos_db_nosql_settings.url), credential=cosmos_db_nosql_settings.key.get_secret_value()
                )
            else:
                cosmos_client = CosmosClient(
                    str(cosmos_db_nosql_settings.url), credential=AsyncDefaultAzureCredentialWrapper()
                )

        super().__init__(
            cosmos_client=cosmos_client,
            database_name=cosmos_db_nosql_settings.database_name,
            cosmos_db_nosql_settings=cosmos_db_nosql_settings,
            create_database=create_database,
            **kwargs,
        )

    async def _does_database_exist(self) -> bool:
        """Checks if the database exists."""
        try:
            await self.cosmos_client.get_database_client(self.database_name).read()
            return True
        except CosmosResourceNotFoundError:
            return False
        except Exception as e:
            raise VectorStoreOperationException(
                f"Failed to check if database '{self.database_name}' exists, with message {e}"
            ) from e

    async def _get_database_proxy(self, **kwargs) -> DatabaseProxy:
        """Gets the database proxy."""
        try:
            if await self._does_database_exist():
                return self.cosmos_client.get_database_client(self.database_name)

            if self.create_database:
                return await self.cosmos_client.create_database(self.database_name, **kwargs)
            raise VectorStoreOperationException(f"Database '{self.database_name}' does not exist.")
        except Exception as e:
            raise VectorStoreOperationException(f"Failed to get database proxy for '{id}'.") from e

    async def _get_container_proxy(self, container_name: str, **kwargs) -> ContainerProxy:
        """Gets the container proxy."""
        try:
            database_proxy = await self._get_database_proxy(**kwargs)
            return database_proxy.get_container_client(container_name)
        except Exception as e:
            raise VectorStoreOperationException(f"Failed to get container proxy for '{container_name}'.") from e


# region: NoSQL Collection


@experimental
class AzureCosmosDBNoSQLCollection(
    AzureCosmosDBNoSQLBase,
    VectorStoreRecordCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    partition_key: PartitionKey

    def __init__(
        self,
        data_model_type: type[TModel],
        collection_name: str,
        database_name: str | None = None,
        data_model_definition: VectorStoreRecordDefinition | None = None,
        url: str | None = None,
        key: str | None = None,
        cosmos_client: CosmosClient | None = None,
        partition_key: PartitionKey | str | None = None,
        create_database: bool = False,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initializes a new instance of the AzureCosmosDBNoSQLCollection class.

        Args:
            data_model_type (type[TModel]): The type of the data model.
            collection_name (str): The name of the collection.
            database_name (str): The name of the database. Used to create a database proxy if not provided.
                                 Defaults to None.
            data_model_definition (VectorStoreRecordDefinition): The definition of the data model. Defaults to None.
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            cosmos_client (CosmosClient): The custom Azure Cosmos DB NoSQL client whose lifetime is managed by the user.
            partition_key (PartitionKey | str): The partition key. Defaults to None. If not provided, the partition
                                                key will be based on the key field of the data model definition.
                                                https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview
            create_database (bool): Indicates whether to create the database if it does not exist.
                                    Defaults to False.
            env_file_path (str): The path to the .env file. Defaults to None.
            env_file_encoding (str): The encoding of the .env file. Defaults to None.
        """
        if not partition_key:
            partition_key = PartitionKey(path=f"/{COSMOS_ITEM_ID_PROPERTY_NAME}")
        else:
            if isinstance(partition_key, str):
                partition_key = PartitionKey(path=f"/{partition_key.strip('/')}")

        super().__init__(
            partition_key=partition_key,
            url=url,
            key=key,
            database_name=database_name,
            cosmos_client=cosmos_client,
            create_database=create_database,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            managed_client=cosmos_client is None,
        )

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        results = await asyncio.gather(*(container_proxy.upsert_item(record) for record in records))
        return [result[COSMOS_ITEM_ID_PROPERTY_NAME] for result in results]

    @override
    async def _inner_get(  # type: ignore
        self,
        keys: Sequence[TGetKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs: Any,
    ) -> Sequence[Any] | None:
        if not keys:
            if options is not None:
                raise NotImplementedError("Get without keys is not yet implemented.")
            return None
        include_vectors = kwargs.pop("include_vectors", False)
        query = (
            f"SELECT {self._build_select_clause(include_vectors)} FROM c WHERE "  # nosec: B608
            f"c.id IN ({', '.join([f'@id{i}' for i in range(len(keys))])})"  # nosec: B608
        )  # nosec: B608
        parameters: list[dict[str, Any]] = [{"name": f"@id{i}", "value": _get_key(key)} for i, key in enumerate(keys)]

        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        return [item async for item in container_proxy.query_items(query=query, parameters=parameters)]

    @override
    async def _inner_delete(self, keys: Sequence[TGetKey], **kwargs: Any) -> None:  # type: ignore
        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        results = await asyncio.gather(
            *[container_proxy.delete_item(item=_get_key(key), partition_key=_get_partition_key(key)) for key in keys],
            return_exceptions=True,
        )
        exceptions = [result for result in results if isinstance(result, Exception)]
        if exceptions:
            raise VectorStoreOperationException("Failed to delete item(s).", exceptions)

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        keywords: OptionalOneOrMany[str] = None,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        params = [{"name": "@top", "value": options.top}]
        if search_text is not None:
            query = self._build_search_text_query(options)
            params.append({"name": "@search_text", "value": search_text})
        elif vector is not None:
            query = self._build_vector_query(options)
            params.append({"name": "@vector", "value": vector})
        else:
            raise VectorSearchExecutionException("Either search_text or vector must be provided.")
        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        try:
            results = container_proxy.query_items(query, parameters=params)
        except Exception as exc:
            raise VectorSearchExecutionException("Failed to search items.") from exc
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(results, options),
            total_count=None,
        )

    def _build_search_text_query(self, options: VectorSearchOptions) -> str:
        where_clauses = self._build_where_clauses_from_filter(options.filter)
        contains_clauses = " OR ".join(
            f"CONTAINS(c.{field}, @search_text)"
            for field, field_def in self.data_model_definition.fields.items()
            if isinstance(field_def, VectorStoreRecordDataField) and field_def.is_full_text_indexed
        )
        if where_clauses:
            where_clauses = f" {where_clauses} AND"
        return (
            f"SELECT TOP @top {self._build_select_clause(options.include_vectors)} "  # nosec: B608
            f"FROM c WHERE{where_clauses} ({contains_clauses})"  # nosec: B608
        )

    def _build_vector_query(self, options: VectorSearchOptions) -> str:
        where_clauses = self._build_where_clauses_from_filter(options.filter)
        if where_clauses:
            where_clauses = f"WHERE {where_clauses} "
        vector_field_name: str = self.data_model_definition.try_get_vector_field(options.vector_field_name).name  # type: ignore
        return (
            f"SELECT TOP @top {self._build_select_clause(options.include_vectors)}, "  # nosec: B608
            f"VectorDistance(c.{vector_field_name}, @vector) AS distance FROM c "  # nosec: B608
            f"{where_clauses}ORDER BY VectorDistance(c.{vector_field_name}, @vector)"  # nosec: B608
        )

    def _build_select_clause(self, include_vectors: bool) -> str:
        """Create the select clause for a CosmosDB query."""
        included_fields = [
            field
            for field in self.data_model_definition.field_names
            if include_vectors or field not in self.data_model_definition.vector_field_names
        ]
        if self.data_model_definition.key_field_name != COSMOS_ITEM_ID_PROPERTY_NAME:
            # Replace the key field name with the Cosmos item id property name
            included_fields = [
                field if field != self.data_model_definition.key_field_name else COSMOS_ITEM_ID_PROPERTY_NAME
                for field in included_fields
            ]

        return ", ".join(f"c.{field}" for field in included_fields)

    def _build_where_clauses_from_filter(self, filters: OneOrMany[Callable | str] | None) -> str:
        if filters is None:
            return ""
        # TODO (eavanvalkenburg): add parser
        clauses = []
        for filter in filters.filters:
            field_def = self.data_model_definition.fields[filter.field_name]
            match filter:
                case EqualTo():
                    clause = ""
                    if field_def.property_type in ["int", "float"]:
                        clause = f"c.{filter.field_name} = {filter.value}"
                    if field_def.property_type == "str":
                        clause = f"c.{filter.field_name} = '{filter.value}'"
                    if field_def.property_type == "list[str]":
                        filter_value = f"ARRAY_CONTAINS(c.{filter.field_name}, '{filter.value}')"
                    if field_def.property_type in ["list[int]", "list[float]"]:
                        filter_value = f"ARRAY_CONTAINS(c.{filter.field_name}, {filter.value})"
                    clauses.append(clause)
                case AnyTagsEqualTo():
                    filter_value = filter.value
                    if field_def.property_type == "list[str]":
                        filter_value = f"'{filter.value}'"
                    clauses.append(f"{filter_value} IN c.{filter.field_name}")
                case _:
                    raise ValueError(f"Unsupported filter: {filter}")
        return " AND ".join(clauses)

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: dict[str, Any]) -> float | None:
        return result.get("distance")

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        serialized_records = []

        key_field_name = self.data_model_definition.key_field_name
        for record in records:
            serialized_record = {**record, COSMOS_ITEM_ID_PROPERTY_NAME: record[key_field_name]}
            if key_field_name != COSMOS_ITEM_ID_PROPERTY_NAME:
                # Remove the key field from the serialized record
                serialized_record.pop(key_field_name, None)

            serialized_records.append(serialized_record)

        return serialized_records

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        deserialized_records = []

        key_field_name = self.data_model_definition.key_field_name
        for record in records:
            if COSMOS_ITEM_ID_PROPERTY_NAME not in record:
                raise VectorStoreModelDeserializationException(
                    f"The record does not have the {COSMOS_ITEM_ID_PROPERTY_NAME} property."
                )

            deserialized_record = {**record, key_field_name: record[COSMOS_ITEM_ID_PROPERTY_NAME]}
            if key_field_name != COSMOS_ITEM_ID_PROPERTY_NAME:
                # Remove the id property from the deserialized record
                deserialized_record.pop(COSMOS_ITEM_ID_PROPERTY_NAME, None)

            deserialized_records.append(deserialized_record)

        return deserialized_records

    @override
    async def create_collection(self, **kwargs) -> None:
        indexing_policy = kwargs.pop("indexing_policy", _create_default_indexing_policy(self.data_model_definition))
        vector_embedding_policy = kwargs.pop(
            "vector_embedding_policy", _create_default_vector_embedding_policy(self.data_model_definition)
        )
        database_proxy = await self._get_database_proxy(**kwargs)
        try:
            await database_proxy.create_container_if_not_exists(
                id=self.collection_name,
                partition_key=self.partition_key,
                indexing_policy=indexing_policy,
                vector_embedding_policy=vector_embedding_policy,
                **kwargs,
            )
        except CosmosHttpResponseError as e:
            raise VectorStoreOperationException("Failed to create container.") from e

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        try:
            await container_proxy.read(**kwargs)
            return True
        except CosmosHttpResponseError:
            return False

    @override
    async def delete_collection(self, **kwargs) -> None:
        database_proxy = await self._get_database_proxy(**kwargs)
        try:
            await database_proxy.delete_container(self.collection_name)
        except Exception as e:
            raise VectorStoreOperationException("Container could not be deleted.") from e

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.cosmos_client.close()


# region: NoSQL Store


@experimental
class AzureCosmosDBNoSQLStore(AzureCosmosDBNoSQLBase, VectorStore):
    """A VectorStore implementation that uses Azure CosmosDB NoSQL as the backend storage."""

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
        database_name: str | None = None,
        cosmos_client: CosmosClient | None = None,
        create_database: bool = False,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initialize the AzureCosmosDBNoSQLStore.

        Args:
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            database_name (str): The name of the database. The database may not exist yet. If it does not exist,
                                 it will be created when the first collection is created. Defaults to None.
            cosmos_client (CosmosClient): The custom Azure Cosmos DB NoSQL client whose lifetime is managed by the user.
                                          Defaults to None.
            create_database (bool): If True, the database will be created if it does not exist.
                                    Defaults to False.
            env_file_path (str): The path to the .env file. Defaults to None.
            env_file_encoding (str): The encoding of the .env file. Defaults to None.
        """
        super().__init__(
            url=url,
            key=key,
            database_name=database_name,
            cosmos_client=cosmos_client,
            create_database=create_database,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
            managed_client=cosmos_client is None,
        )

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[object],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> VectorStoreRecordCollection:
        return AzureCosmosDBNoSQLCollection(
            data_model_type,
            collection_name,
            database_name=self.database_name,
            data_model_definition=data_model_definition,
            cosmos_client=self.cosmos_client,
            create_database=self.create_database,
            env_file_path=self.cosmos_db_nosql_settings.env_file_path,
            env_file_encoding=self.cosmos_db_nosql_settings.env_file_encoding,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        try:
            database = await self._get_database_proxy()
            containers = database.list_containers()
            return [container["id"] async for container in containers]
        except Exception as e:
            raise VectorStoreOperationException("Failed to list collection names.") from e

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.cosmos_client.close()
