# Copyright (c) Microsoft. All rights reserved.

import json

import aiohttp

from semantic_kernel.connectors.memory_stores.astradb.utils import AsyncSession
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import APP_INFO

ASTRA_CALLER_IDENTITY: str
SEMANTIC_KERNEL_VERSION = APP_INFO.get("Semantic-Kernel-Version")
ASTRA_CALLER_IDENTITY = f"semantic-kernel/{SEMANTIC_KERNEL_VERSION}" if SEMANTIC_KERNEL_VERSION else "semantic-kernel"


@experimental
class AstraClient:
    """AstraClient."""

    def __init__(
        self,
        astra_id: str,
        astra_region: str,
        astra_application_token: str,
        keyspace_name: str,
        embedding_dim: int,
        similarity_function: str,
        session: aiohttp.ClientSession | None = None,
    ):
        """Initializes a new instance of the AstraClient class."""
        self.astra_id = astra_id
        self.astra_application_token = astra_application_token
        self.astra_region = astra_region
        self.keyspace_name = keyspace_name
        self.embedding_dim = embedding_dim
        self.similarity_function = similarity_function

        self.request_base_url = (
            f"https://{self.astra_id}-{self.astra_region}.apps.astra.datastax.com/api/json/v1/{self.keyspace_name}"
        )
        self.request_header = {
            "x-cassandra-token": self.astra_application_token,
            "Content-Type": "application/json",
            "User-Agent": ASTRA_CALLER_IDENTITY,
        }
        self._session = session

    async def _run_query(self, request_url: str, query: dict):
        async with (
            AsyncSession(self._session) as session,
            session.post(request_url, data=json.dumps(query), headers=self.request_header) as response,
        ):
            if response.status == 200:
                response_dict = await response.json()
                if "errors" in response_dict:
                    raise ServiceResponseException(f"Astra DB request error - {response_dict['errors']}")
                return response_dict
            raise ServiceResponseException(f"Astra DB not available. Status : {response}")

    async def find_collections(self, include_detail: bool = True):
        """Finds all collections in the keyspace."""
        query = {"findCollections": {"options": {"explain": include_detail}}}
        result = await self._run_query(self.request_base_url, query)
        return result["status"]["collections"]

    async def find_collection(self, collection_name: str):
        """Finds a collection in the keyspace."""
        collections = await self.find_collections(False)
        found = False
        for collection in collections:
            if collection == collection_name:
                found = True
                break
        return found

    async def create_collection(
        self,
        collection_name: str,
        embedding_dim: int | None = None,
        similarity_function: str | None = None,
    ):
        """Creates a new collection in the keyspace."""
        query = {
            "createCollection": {
                "name": collection_name,
                "options": {
                    "vector": {
                        "dimension": embedding_dim if embedding_dim is not None else self.embedding_dim,
                        "metric": similarity_function if similarity_function is not None else self.similarity_function,
                    }
                },
            }
        }
        result = await self._run_query(self.request_base_url, query)
        return result["status"]["ok"] == 1

    async def delete_collection(self, collection_name: str):
        """Deletes a collection from the keyspace."""
        query = {"deleteCollection": {"name": collection_name}}
        result = await self._run_query(self.request_base_url, query)
        return result["status"]["ok"] == 1

    def _build_request_collection_url(self, collection_name: str):
        return f"{self.request_base_url}/{collection_name}"

    async def find_documents(
        self,
        collection_name: str,
        filter: dict | None = None,
        vector: list[float] | None = None,
        limit: int | None = None,
        include_vector: bool | None = None,
        include_similarity: bool | None = None,
    ) -> list[dict]:
        """Finds all documents in the collection."""
        find_query = {}

        if filter is not None:
            find_query["filter"] = filter

        if vector is not None:
            find_query["sort"] = {"$vector": vector}

        if include_vector is not None and include_vector is False:
            find_query["projection"] = {"$vector": 0}
        else:
            find_query["projection"] = {"*": 1}

        if limit is not None:
            find_query["options"] = {"limit": limit}

        if include_similarity is not None:
            if "options" in find_query:
                find_query["options"]["includeSimilarity"] = int(include_similarity)
            else:
                find_query["options"] = {"includeSimilarity": int(include_similarity)}

        query = {"find": find_query}
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["data"]["documents"]

    async def insert_document(self, collection_name: str, document: dict) -> str:
        """Inserts a document into the collection."""
        query = {"insertOne": {"document": document}}
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]["insertedIds"][0]

    async def insert_documents(self, collection_name: str, documents: list[dict]) -> list[str]:
        """Inserts multiple documents into the collection."""
        query = {"insertMany": {"documents": documents}}
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]["insertedIds"]

    async def update_document(self, collection_name: str, filter: dict, update: dict, upsert: bool = True) -> dict:
        """Updates a document in the collection."""
        query = {
            "findOneAndUpdate": {
                "filter": filter,
                "update": update,
                "options": {"returnDocument": "after", "upsert": upsert},
            }
        }
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]

    async def update_documents(self, collection_name: str, filter: dict, update: dict):
        """Updates multiple documents in the collection."""
        query = {
            "updateMany": {
                "filter": filter,
                "update": update,
            }
        }
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]

    async def delete_documents(self, collection_name: str, filter: dict) -> int:
        """Deletes documents from the collection."""
        query = {"deleteMany": {"filter": filter}}
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]["deletedCount"]
