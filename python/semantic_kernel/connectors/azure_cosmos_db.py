# Copyright (c) Microsoft. All rights reserved.

import ast
import asyncio
import json
import sys
from collections.abc import Sequence
from importlib import metadata
from typing import Any, ClassVar, Final, Generic, TypeVar

from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError
from azure.cosmos.partition_key import PartitionKey
from pydantic import HttpUrl, SecretStr, ValidationError
from pymongo import AsyncMongoClient
from pymongo.driver_info import DriverInfo
from typing_extensions import override

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.mongodb import (
    DEFAULT_DB_NAME,
    MONGODB_SCORE_FIELD,
    MongoDBAtlasCollection,
    MongoDBAtlasStore,
)
from semantic_kernel.data.vector import (
    DistanceFunction,
    FieldTypes,
    GetFilteredRecordOptions,
    IndexKind,
    KernelSearchResults,
    SearchType,
    TModel,
    VectorSearch,
    VectorSearchOptions,
    VectorSearchResult,
    VectorStore,
    VectorStoreCollection,
    VectorStoreCollectionDefinition,
    _get_collection_name_from_model,
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
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


@release_candidate
class CosmosNoSqlCompositeKey(KernelBaseModel):
    """CosmosDB NoSQL composite key."""

    partition_key: str
    key: str


TKey = TypeVar("TKey", bound=str)
TNoSQLKey = TypeVar("TNoSQLKey", str, CosmosNoSqlCompositeKey)

# region: Constants

COSMOS_ITEM_ID_PROPERTY_NAME: Final[str] = "id"
NOSQL_SCORE_PROPERTY_NAME: Final[str] = "distance"
INDEX_KIND_MAP_NOSQL: Final[dict[IndexKind, str]] = {
    IndexKind.FLAT: "flat",
    IndexKind.QUANTIZED_FLAT: "quantizedFlat",
    IndexKind.DISK_ANN: "diskANN",
    IndexKind.DEFAULT: "flat",
}
INDEX_KIND_MAP_MONGODB: Final[dict[IndexKind, str]] = {
    IndexKind.IVF_FLAT: "vector-ivf",
    IndexKind.HNSW: "vector-hnsw",
    IndexKind.DISK_ANN: "vector-diskann",
    IndexKind.DEFAULT: "vector-ivf",
}
DISTANCE_FUNCTION_MAP_NOSQL: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.COSINE_SIMILARITY: "cosine",
    DistanceFunction.DOT_PROD: "dotproduct",
    DistanceFunction.EUCLIDEAN_DISTANCE: "euclidean",
    DistanceFunction.DEFAULT: "cosine",
}
DISTANCE_FUNCTION_MAP_MONGODB: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.COSINE_SIMILARITY: "COS",
    DistanceFunction.DOT_PROD: "IP",
    DistanceFunction.EUCLIDEAN_DISTANCE: "L2",
    DistanceFunction.DEFAULT: "COS",
}
VECTOR_DATATYPES_MAP: Final[dict[str, str]] = {
    "default": "float32",
    "float": "float32",
    "list[float]": "float32",
    "int": "int32",
    "list[int]": "int32",
}

# region: Helpers


def _create_default_indexing_policy_nosql(definition: VectorStoreCollectionDefinition) -> dict[str, Any]:
    """Creates a default indexing policy for the Azure Cosmos DB NoSQL container.

    A default indexing policy is created based on the data model definition and has an automatic indexing policy.

    Args:
        definition (VectorStoreRecordDefinition): The definition of the data model.

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

    for field in definition.fields:
        if field.field_type == FieldTypes.DATA and (not field.is_full_text_indexed and not field.is_indexed):
            indexing_policy["excludedPaths"].append({"path": f'/"{field.storage_name or field.name}"/*'})

        if field.field_type == FieldTypes.VECTOR:
            if field.index_kind not in INDEX_KIND_MAP_NOSQL:
                raise VectorStoreModelException(
                    f"Index kind '{field.index_kind}' is not supported by Azure Cosmos DB NoSQL container."
                )
            indexing_policy["vectorIndexes"].append({
                "path": f'/"{field.storage_name or field.name}"',
                "type": INDEX_KIND_MAP_NOSQL[field.index_kind],
            })
            # Exclude the vector field from the index for performance optimization.
            indexing_policy["excludedPaths"].append({"path": f'/"{field.storage_name or field.name}"/*'})

    return indexing_policy


def _create_default_vector_embedding_policy(definition: VectorStoreCollectionDefinition) -> dict[str, Any]:
    """Creates a default vector embedding policy for the Azure Cosmos DB NoSQL container.

    A default vector embedding policy is created based on the data model definition.

    Args:
        definition (VectorStoreRecordDefinition): The definition of the data model.

    Returns:
        dict[str, Any]: The vector embedding policy.

    Raises:
        VectorStoreModelException: If the datatype or distance function is not supported by Azure Cosmos DB NoSQL.

    """
    vector_embedding_policy: dict[str, Any] = {"vectorEmbeddings": []}

    for field in definition.fields:
        if field.field_type == FieldTypes.VECTOR:
            if field.distance_function not in DISTANCE_FUNCTION_MAP_NOSQL:
                raise VectorStoreModelException(
                    f"Distance function '{field.distance_function}' is not supported by Azure Cosmos DB NoSQL."
                )
            if field.type_ and field.type_ not in VECTOR_DATATYPES_MAP:
                raise VectorStoreModelException(
                    f"Vector property type '{field.type_}' is not supported by Azure Cosmos DB NoSQL."
                )

            vector_embedding_policy["vectorEmbeddings"].append({
                "path": f'/"{field.storage_name or field.name}"',
                "dataType": VECTOR_DATATYPES_MAP[field.type_ or "default"],
                "distanceFunction": DISTANCE_FUNCTION_MAP_NOSQL[field.distance_function],
                "dimensions": field.dimensions,
            })

    return vector_embedding_policy


def _get_key(key: str | CosmosNoSqlCompositeKey) -> str:
    """Gets the key value from the key."""
    if isinstance(key, CosmosNoSqlCompositeKey):
        return key.key
    return key


def _get_partition_key(key: str | CosmosNoSqlCompositeKey) -> str:
    """Gets the partition key value from the key."""
    if isinstance(key, CosmosNoSqlCompositeKey):
        return key.partition_key
    return key


# region: Settings


@release_candidate
class CosmosMongoSettings(KernelBaseSettings):
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

    connection_string: SecretStr
    database_name: str = DEFAULT_DB_NAME


@release_candidate
class CosmosNoSqlSettings(KernelBaseSettings):
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


@release_candidate
class CosmosMongoCollection(MongoDBAtlasCollection[TKey, TModel], Generic[TKey, TModel]):
    """Azure Cosmos DB for MongoDB collection."""

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        mongo_client: AsyncMongoClient | None = None,
        connection_string: str | None = None,
        database_name: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the CosmosMongoCollection class.

        Args:
            record_type: The type of the data model.
            definition: The model definition, optional.
            collection_name: The name of the collection, optional.
            embedding_generator: The embedding generator to use for generating embeddings.
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
        if not collection_name:
            collection_name = _get_collection_name_from_model(record_type, definition)
        if not collection_name:
            raise VectorStoreInitializationException(
                "The collection name is required, can be passed directly or through the data model."
            )
        managed_client = not mongo_client
        if mongo_client:
            super().__init__(
                record_type=record_type,
                definition=definition,
                mongo_client=mongo_client,
                collection_name=collection_name,
                database_name=database_name or DEFAULT_DB_NAME,
                managed_client=managed_client,
                embedding_generator=embedding_generator,
            )
            return

        try:
            settings = CosmosMongoSettings(
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                connection_string=connection_string,
                database_name=database_name,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create Azure CosmosDB for MongoDB settings.") from exc

        mongo_client = AsyncMongoClient(
            settings.connection_string.get_secret_value(),
            driver=DriverInfo(SEMANTIC_KERNEL_USER_AGENT, metadata.version("semantic-kernel")),
        )

        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=settings.database_name,
            embedding_generator=embedding_generator,
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
        await self._get_database().command(command=self._get_index_definitions(**kwargs))

    def _get_index_definitions(self, **kwargs: Any) -> dict[str, Any]:
        """Creates index definitions for the collection."""
        indexes = [
            {
                "name": f"{field.storage_name or field.name}_",
                FieldTypes.KEY: {field.storage_name or field.name: 1},
            }
            for field in self.definition.data_fields
            if field.is_indexed or field.is_full_text_indexed
        ]
        for field in self.definition.vector_fields:
            if field.index_kind not in INDEX_KIND_MAP_MONGODB:
                raise VectorStoreModelException(
                    f"Index kind '{field.index_kind}' is not supported by Azure Cosmos DB for MongoDB."
                )
            if field.distance_function not in DISTANCE_FUNCTION_MAP_MONGODB:
                raise VectorStoreModelException(
                    f"Distance function '{field.distance_function}' is not supported by Azure Cosmos DB for MongoDB."
                )
            index_name = f"{field.storage_name or field.name}_"
            index_kind = DISTANCE_FUNCTION_MAP_MONGODB[field.distance_function]
            index: dict[str, Any] = {
                "name": index_name,
                FieldTypes.KEY: {field.storage_name or field.name: "cosmosSearch"},
                "cosmosSearchOptions": {
                    "kind": index_kind,
                    "similarity": DISTANCE_FUNCTION_MAP_MONGODB[field.distance_function],
                    "dimensions": field.dimensions,
                },
            }
            match index_kind:
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
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        collection = self._get_collection()
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorStoreModelException(
                f"Vector field '{options.vector_property_name}' not found in the data model definition."
            )
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        vector_search_query: dict[str, Any] = {
            "k": options.top + options.skip,
            "index": f"{vector_field.storage_name or vector_field.name}_",
            "vector": vector,
            "path": vector_field.storage_name or vector_field.name,
        }
        if filter := self._build_filter(options.filter):  # type: ignore
            vector_search_query["filter"] = filter if isinstance(filter, dict) else {"$and": filter}

        projection_query: dict[str, int | dict] = {
            field: 1
            for field in self.definition.get_names(
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


# region: Mongo Store


@release_candidate
class CosmosMongoStore(MongoDBAtlasStore):
    """Azure Cosmos DB for MongoDB store."""

    def __init__(
        self,
        connection_string: str | None = None,
        database_name: str | None = None,
        mongo_client: AsyncMongoClient | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the CosmosMongoStore class."""
        managed_client: bool = not mongo_client
        if mongo_client:
            super().__init__(
                mongo_client=mongo_client,
                managed_client=managed_client,
                database_name=database_name,
                embedding_generator=embedding_generator,
            )
            return
        try:
            settings = CosmosMongoSettings(
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                connection_string=connection_string,
                database_name=database_name,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create Azure CosmosDB for MongoDB settings.") from exc

        mongo_client = AsyncMongoClient(
            settings.connection_string.get_secret_value(),
            driver=DriverInfo(SEMANTIC_KERNEL_USER_AGENT, metadata.version("semantic-kernel")),
        )

        super().__init__(
            mongo_client=mongo_client,
            managed_client=managed_client,
            database_name=settings.database_name,
            embedding_generator=embedding_generator,
        )

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> CosmosMongoCollection:
        return CosmosMongoCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            mongo_client=self.mongo_client,
            managed_client=False,
            database_name=self.database_name,
            embedding_generator=embedding_generator or self.embedding_generator,
            **kwargs,
        )


# region: NoSQL Base


@release_candidate
class CosmosNoSqlBase(KernelBaseModel):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    cosmos_client: CosmosClient
    database_name: str
    cosmos_db_nosql_settings: CosmosNoSqlSettings
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
        """Initialize the CosmosNoSqlBase.

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
            cosmos_db_nosql_settings = CosmosNoSqlSettings(
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


@release_candidate
class CosmosNoSqlCollection(
    CosmosNoSqlBase,
    VectorStoreCollection[TNoSQLKey, TModel],
    VectorSearch[TNoSQLKey, TModel],
    Generic[TNoSQLKey, TModel],
):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    partition_key: PartitionKey
    supported_key_types: ClassVar[set[str] | None] = {"str", "CosmosNoSqlCompositeKey"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR, SearchType.KEYWORD_HYBRID}

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        database_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        url: str | None = None,
        key: str | None = None,
        cosmos_client: CosmosClient | None = None,
        partition_key: PartitionKey | str | None = None,
        create_database: bool = False,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initializes a new instance of the CosmosNoSqlCollection class.

        Args:
            record_type: The type of the data model.
            collection_name: The name of the collection.
            database_name: The name of the database. Used to create a database proxy if not provided.
                                 Defaults to None.
            embedding_generator: The embedding generator to use for generating embeddings.
            definition: The definition of the data model. Defaults to None.
            url: The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key: The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            cosmos_client: The custom Azure Cosmos DB NoSQL client whose lifetime is managed by the user.
            partition_key: The partition key. Defaults to None. If not provided, the partition
                                                key will be based on the key field of the data model definition.
                                                https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview
            create_database: Indicates whether to create the database if it does not exist.
                                    Defaults to False.
            env_file_path: The path to the .env file. Defaults to None.
            env_file_encoding: The encoding of the .env file. Defaults to None.
        """
        if not collection_name:
            collection_name = _get_collection_name_from_model(record_type, definition)
        if not partition_key:
            partition_key = PartitionKey(path=f"/{COSMOS_ITEM_ID_PROPERTY_NAME}")
        elif isinstance(partition_key, str):
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
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            managed_client=cosmos_client is None,
            embedding_generator=embedding_generator,
        )

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TNoSQLKey]:
        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        results = await asyncio.gather(*(container_proxy.upsert_item(record) for record in records))
        return [result[COSMOS_ITEM_ID_PROPERTY_NAME] for result in results]

    @override
    async def _inner_get(  # type: ignore
        self,
        keys: Sequence[TNoSQLKey] | None = None,
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
    async def _inner_delete(self, keys: Sequence[TNoSQLKey], **kwargs: Any) -> None:  # type: ignore
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
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        params = [{"name": "@top", "value": options.top}]
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorStoreModelException(
                f"Vector field '{options.vector_property_name}' not found in the data model definition."
            )
        if not vector:
            vector = await self._generate_vector_from_values(values, options)

        if where_clauses := self._build_filter(options.filter):  # type: ignore
            where_clauses = (
                f"WHERE {where_clauses} "
                if isinstance(where_clauses, str)
                else f"WHERE ({' AND '.join(where_clauses)}) "
            )
        vector_field_name = vector_field.storage_name or vector_field.name
        select_clause = self._build_select_clause(options.include_vectors)
        params.append({"name": "@vector", "value": vector})
        if vector_field.distance_function not in DISTANCE_FUNCTION_MAP_NOSQL:
            raise VectorStoreModelException(
                f"Distance function '{vector_field.distance_function}' is not supported by Azure Cosmos DB NoSQL."
            )
        distance_obj = json.dumps({"distanceFunction": DISTANCE_FUNCTION_MAP_NOSQL[vector_field.distance_function]})
        if search_type == SearchType.VECTOR:
            distance_clause = f"VectorDistance(c.{vector_field_name}, @vector, false {distance_obj})"
        elif search_type == SearchType.KEYWORD_HYBRID:
            # Hybrid search: requires both a vector and keywords
            params.append({"name": "@keywords", "value": values})
            text_field = options.additional_property_name
            if not text_field:
                raise VectorStoreModelException("Hybrid search requires 'keyword_field_name' in options.")
            distance_clause = f"RRF(VectorDistance(c.{vector_field_name}, @vector, false, {distance_obj}), "
            f"FullTextScore(c.{text_field}, @keywords))"
        else:
            raise VectorStoreModelException(f"Search type '{search_type}' is not supported.")
        query = (
            f"SELECT TOP @top {select_clause}, "  # nosec: B608
            f"{distance_clause} as {NOSQL_SCORE_PROPERTY_NAME} "  # nosec: B608
            "FROM c "
            f"{where_clauses}"  # nosec: B608
            f"ORDER BY RANK {distance_clause}"  # nosec: B608
        )
        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        try:
            results = container_proxy.query_items(query, parameters=params)
        except Exception as exc:
            raise VectorSearchExecutionException("Failed to search items.") from exc
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(results, options),
            total_count=None,
        )

    def _build_select_clause(self, include_vectors: bool) -> str:
        """Create the select clause for a CosmosDB query."""
        included_fields = [field for field in self.definition.get_storage_names(include_vector_fields=include_vectors)]
        if self.definition.key_name != COSMOS_ITEM_ID_PROPERTY_NAME:
            # Replace the key field name with the Cosmos item id property name
            included_fields = [
                field if field != self.definition.key_name else COSMOS_ITEM_ID_PROPERTY_NAME
                for field in included_fields
            ]

        return ", ".join(f"c.{field}" for field in included_fields)

    @override
    def _lambda_parser(self, node: ast.AST) -> Any:
        match node:
            case ast.Compare():
                if len(node.ops) > 1:
                    # Chain comparisons (e.g., a < b < c) become AND-ed comparisons
                    values = []
                    for idx in range(len(node.ops)):
                        if idx == 0:
                            values.append(
                                ast.Compare(
                                    left=node.left,
                                    ops=[node.ops[idx]],
                                    comparators=[node.comparators[idx]],
                                )
                            )
                        else:
                            values.append(
                                ast.Compare(
                                    left=node.comparators[idx - 1],
                                    ops=[node.ops[idx]],
                                    comparators=[node.comparators[idx]],
                                )
                            )
                    return "(" + " AND ".join([self._lambda_parser(v) for v in values]) + ")"
                left = self._lambda_parser(node.left)
                right = self._lambda_parser(node.comparators[0])
                op = node.ops[0]
                match op:
                    case ast.In():
                        # Cosmos DB: ARRAY_CONTAINS(right, left)
                        return f"ARRAY_CONTAINS({right}, {left})"
                    case ast.NotIn():
                        return f"NOT ARRAY_CONTAINS({right}, {left})"
                    case ast.Eq():
                        return f"{left} = {right}"
                    case ast.NotEq():
                        return f"{left} != {right}"
                    case ast.Gt():
                        return f"{left} > {right}"
                    case ast.GtE():
                        return f"{left} >= {right}"
                    case ast.Lt():
                        return f"{left} < {right}"
                    case ast.LtE():
                        return f"{left} <= {right}"
                raise NotImplementedError(f"Unsupported operator: {type(op)}")
            case ast.BoolOp():
                op_str = "AND" if isinstance(node.op, ast.And) else "OR"
                return "(" + f" {op_str} ".join([self._lambda_parser(v) for v in node.values]) + ")"
            case ast.UnaryOp():
                match node.op:
                    case ast.Not():
                        return f"NOT ({self._lambda_parser(node.operand)})"
                    case ast.UAdd():
                        return f"+{self._lambda_parser(node.operand)}"
                    case ast.USub():
                        return f"-{self._lambda_parser(node.operand)}"
                    case ast.Invert():
                        raise NotImplementedError("Invert operation is not supported.")
                raise NotImplementedError(f"Unsupported unary operator: {type(node.op)}")
            case ast.Attribute():
                # Cosmos DB: c.field_name
                if node.attr not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.attr}' not in data model (storage property names are used)."
                    )
                return f"c.{node.attr}"
            case ast.Name():
                # Could be a variable or constant; not supported
                raise NotImplementedError("Constants or variables are not supported, use a value or attribute.")
            case ast.Constant():
                # Quote strings, leave numbers as is
                if isinstance(node.value, str):
                    return f"'{node.value}'"
                if isinstance(node.value, (float, int)):
                    return str(node.value)
                if node.value is None:
                    return "null"
                raise NotImplementedError(f"Unsupported constant type: {type(node.value)}")
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: dict[str, Any]) -> float | None:
        return result.get(NOSQL_SCORE_PROPERTY_NAME)

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        serialized_records = []

        key_field_name = self.definition.key_name
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

        key_field_name = self.definition.key_name
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
        indexing_policy = kwargs.pop("indexing_policy", _create_default_indexing_policy_nosql(self.definition))
        vector_embedding_policy = kwargs.pop(
            "vector_embedding_policy", _create_default_vector_embedding_policy(self.definition)
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
    async def ensure_collection_deleted(self, **kwargs) -> None:
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


@release_candidate
class CosmosNoSqlStore(CosmosNoSqlBase, VectorStore):
    """A VectorStore implementation that uses Azure CosmosDB NoSQL as the backend storage."""

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
        database_name: str | None = None,
        cosmos_client: CosmosClient | None = None,
        create_database: bool = False,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initialize the CosmosNoSqlStore.

        Args:
            url: The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key: The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            database_name: The name of the database. The database may not exist yet. If it does not exist,
                                 it will be created when the first collection is created. Defaults to None.
            cosmos_client: The custom Azure Cosmos DB NoSQL client whose lifetime is managed by the user.
                                          Defaults to None.
            create_database: If True, the database will be created if it does not exist.
                                    Defaults to False.
            embedding_generator: The embedding generator to use for generating embeddings.
            env_file_path: The path to the .env file. Defaults to None.
            env_file_encoding: The encoding of the .env file. Defaults to None.
        """
        super().__init__(
            url=url,
            key=key,
            database_name=database_name,
            cosmos_client=cosmos_client,
            create_database=create_database,
            embedding_generator=embedding_generator,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> CosmosNoSqlCollection:
        return CosmosNoSqlCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            database_name=self.database_name,
            embedding_generator=embedding_generator or self.embedding_generator,
            url=str(self.cosmos_db_nosql_settings.url),
            key=self.cosmos_db_nosql_settings.key.get_secret_value() if self.cosmos_db_nosql_settings.key else None,
            cosmos_client=self.cosmos_client,
            partition_key=None,
            create_database=self.create_database,
            env_file_path=None,
            env_file_encoding=None,
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

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.cosmos_client.close()
