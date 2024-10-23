# Copyright (c) Microsoft. All rights reserved.

from typing import Any

import pandas as pd
import pytest

from semantic_kernel.connectors.memory.redis.const import RedisCollectionTypes
from semantic_kernel.data.vector_store import VectorStore
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from tests.integration.memory.vector_stores.data_records import (
    PANDAS_RECORD_DEFINITION,
    RAW_RECORD_ARRAY,
    RAW_RECORD_LIST,
    TestDataModelArray,
    TestDataModelList,
)
from tests.integration.memory.vector_stores.vector_store_test_base import VectorStoreTestBase


class TestVectorStore(VectorStoreTestBase):
    """Test vector store functionality.

    This only tests if the vector stores can upsert, get, and delete records.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "store_id, collection_name, collection_options, data_model_type, data_model_definition, record",
        [
            # region Redis
            pytest.param(
                "redis",
                "redis_json_array_data_model",
                {"collection_type": RedisCollectionTypes.JSON},
                TestDataModelArray,
                None,
                RAW_RECORD_ARRAY,
                id="redis_json_array_data_model",
            ),
            pytest.param(
                "redis",
                "redis_json_list_data_model",
                {"collection_type": RedisCollectionTypes.JSON},
                TestDataModelList,
                None,
                RAW_RECORD_LIST,
                id="redis_json_list_data_model",
            ),
            pytest.param(
                "redis",
                "redis_json_pandas_data_model",
                {"collection_type": RedisCollectionTypes.JSON},
                pd.DataFrame,
                PANDAS_RECORD_DEFINITION,
                RAW_RECORD_LIST,
                id="redis_json_pandas_data_model",
            ),
            pytest.param(
                "redis",
                "redis_hashset_array_data_model",
                {"collection_type": RedisCollectionTypes.HASHSET},
                TestDataModelArray,
                None,
                RAW_RECORD_ARRAY,
                id="redis_hashset_array_data_model",
            ),
            pytest.param(
                "redis",
                "redis_hashset_list_data_model",
                {"collection_type": RedisCollectionTypes.HASHSET},
                TestDataModelList,
                None,
                RAW_RECORD_LIST,
                id="redis_hashset_list_data_model",
            ),
            pytest.param(
                "redis",
                "redis_hashset_pandas_data_model",
                {"collection_type": RedisCollectionTypes.HASHSET},
                pd.DataFrame,
                PANDAS_RECORD_DEFINITION,
                RAW_RECORD_LIST,
                id="redis_hashset_pandas_data_model",
            ),
            # endregion
            # region Azure AI Search
            pytest.param(
                "azure_ai_search",
                "azure_ai_search_array_data_model",
                {},
                TestDataModelArray,
                None,
                RAW_RECORD_ARRAY,
                id="azure_ai_search_array_data_model",
            ),
            pytest.param(
                "azure_ai_search",
                "azure_ai_search_list_data_model",
                {},
                TestDataModelList,
                None,
                RAW_RECORD_LIST,
                id="azure_ai_search_list_data_model",
            ),
            pytest.param(
                "azure_ai_search",
                "azure_ai_search_pandas_data_model",
                {},
                pd.DataFrame,
                PANDAS_RECORD_DEFINITION,
                RAW_RECORD_LIST,
                id="azure_ai_search_pandas_data_model",
            ),
            # endregion
            # region Qdrant
            pytest.param(
                "qdrant",
                "qdrant_array_data_model",
                {},
                TestDataModelArray,
                None,
                RAW_RECORD_ARRAY,
                id="qdrant_array_data_model",
            ),
            pytest.param(
                "qdrant",
                "qdrant_list_data_model",
                {},
                TestDataModelList,
                None,
                RAW_RECORD_LIST,
                id="qdrant_list_data_model",
            ),
            pytest.param(
                "qdrant",
                "qdrant_pandas_data_model",
                {},
                pd.DataFrame,
                PANDAS_RECORD_DEFINITION,
                RAW_RECORD_LIST,
                id="qdrant_pandas_data_model",
            ),
            pytest.param(
                "qdrant_in_memory",
                "qdrant_in_memory_array_data_model",
                {},
                TestDataModelArray,
                None,
                RAW_RECORD_ARRAY,
                id="qdrant_in_memory_array_data_model",
            ),
            pytest.param(
                "qdrant_in_memory",
                "qdrant_in_memory_list_data_model",
                {},
                TestDataModelList,
                None,
                RAW_RECORD_LIST,
                id="qdrant_in_memory_list_data_model",
            ),
            pytest.param(
                "qdrant_in_memory",
                "qdrant_in_memory_pandas_data_model",
                {},
                pd.DataFrame,
                PANDAS_RECORD_DEFINITION,
                RAW_RECORD_LIST,
                id="qdrant_in_memory_pandas_data_model",
            ),
            pytest.param(
                "qdrant",
                "qdrant_grpc_array_data_model",
                {"prefer_grpc": True},
                TestDataModelArray,
                None,
                RAW_RECORD_ARRAY,
                id="qdrant_grpc_array_data_model",
            ),
            pytest.param(
                "qdrant",
                "qdrant_grpc_list_data_model",
                {"prefer_grpc": True},
                TestDataModelList,
                None,
                RAW_RECORD_LIST,
                id="qdrant_grpc_list_data_model",
            ),
            pytest.param(
                "qdrant",
                "qdrant_grpc_pandas_data_model",
                {"prefer_grpc": True},
                pd.DataFrame,
                PANDAS_RECORD_DEFINITION,
                RAW_RECORD_LIST,
                id="qdrant_grpc_pandas_data_model",
            ),
            # endregion
            # region Weaviate
            pytest.param(
                "weaviate_local",
                "weaviate_local_array_data_model",
                {},
                TestDataModelArray,
                None,
                RAW_RECORD_ARRAY,
                id="weaviate_local_array_data_model",
            ),
            pytest.param(
                "weaviate_local",
                "weaviate_local_list_data_model",
                {},
                TestDataModelList,
                None,
                RAW_RECORD_LIST,
                id="weaviate_local_list_data_model",
            ),
            pytest.param(
                "weaviate_local",
                "weaviate_local_pandas_data_model",
                {},
                pd.DataFrame,
                PANDAS_RECORD_DEFINITION,
                RAW_RECORD_LIST,
                id="weaviate_local_pandas_data_model",
            ),
            # endregion
        ],
    )
    async def test_vector_store(
        self,
        stores: dict[str, VectorStore],
        store_id: str,
        collection_name: str,
        collection_options: dict[str, Any],
        data_model_type: type,
        data_model_definition: VectorStoreRecordDefinition | None,
        record: dict[str, Any],
    ):
        vector_store = stores[store_id]
        collection = vector_store.get_collection(
            collection_name, data_model_type, data_model_definition, **collection_options
        )

        try:
            await collection.create_collection_if_not_exists()
        except Exception as exc:
            pytest.fail(f"Failed to create collection: {exc}")

        # Upsert record
        await collection.upsert(
            data_model_type([record]) if data_model_type == pd.DataFrame else data_model_type(**record)
        )
        # Get record
        result = await collection.get(record["id"])
        assert result is not None
        # Delete record
        await collection.delete(record["id"])
        # Get record again, expect None
        result = await collection.get(record["id"])
        assert result is None

        try:
            await collection.delete_collection()
        except Exception as exc:
            pytest.fail(f"Failed to delete collection: {exc}")
