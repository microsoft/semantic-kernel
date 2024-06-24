import json
from typing import Dict, List, Optional

import aiohttp

from semantic_kernel.connectors.memory.astradb.utils import AsyncSession
from semantic_kernel.exceptions import ServiceResponseException


class AstraClient:
    def __init__(
        self,
        astra_id: str,
        astra_region: str,
        astra_application_token: str,
        keyspace_name: str,
        embedding_dim: int,
        similarity_function: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
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
        }
        self._session = session

    async def _run_query(self, request_url: str, query: Dict):
        async with AsyncSession(self._session) as session:
            async with session.post(request_url, data=json.dumps(query), headers=self.request_header) as response:
                if response.status == 200:
                    response_dict = await response.json()
                    if "errors" in response_dict:
                        raise ServiceResponseException(f"Astra DB request error - {response_dict['errors']}")
                    else:
                        return response_dict
                else:
                    raise ServiceResponseException(f"Astra DB not available. Status : {response}")

    async def find_collections(self, include_detail: bool = True):
        query = {"findCollections": {"options": {"explain": include_detail}}}
        result = await self._run_query(self.request_base_url, query)
        return result["status"]["collections"]

    async def find_collection(self, collection_name: str):
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
        embedding_dim: Optional[int] = None,
        similarity_function: Optional[str] = None,
    ):
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
        return True if result["status"]["ok"] == 1 else False

    async def delete_collection(self, collection_name: str):
        query = {"deleteCollection": {"name": collection_name}}
        result = await self._run_query(self.request_base_url, query)
        return True if result["status"]["ok"] == 1 else False

    def _build_request_collection_url(self, collection_name: str):
        return f"{self.request_base_url}/{collection_name}"

    async def find_documents(
        self,
        collection_name: str,
        filter: Optional[Dict] = None,
        vector: Optional[List[float]] = None,
        limit: Optional[int] = None,
        include_vector: Optional[bool] = None,
        include_similarity: Optional[bool] = None,
    ) -> List[Dict]:
        find_query = {}

        if filter is not None:
            find_query["filter"] = filter

        if vector is not None:
            find_query["sort"] = {"$vector": vector}

        if include_vector is not None and include_vector is False:
            find_query["projection"] = {"$vector": 0}

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

    async def insert_document(self, collection_name: str, document: Dict) -> str:
        query = {"insertOne": {"document": document}}
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]["insertedIds"][0]

    async def insert_documents(self, collection_name: str, documents: List[Dict]) -> List[str]:
        query = {"insertMany": {"documents": documents}}
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]["insertedIds"]

    async def update_document(self, collection_name: str, filter: Dict, update: Dict, upsert: bool = True) -> Dict:
        query = {
            "findOneAndUpdate": {
                "filter": filter,
                "update": update,
                "options": {"returnDocument": "after", "upsert": upsert},
            }
        }
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]

    async def update_documents(self, collection_name: str, filter: Dict, update: Dict):
        query = {
            "updateMany": {
                "filter": filter,
                "update": update,
            }
        }
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]

    async def delete_documents(self, collection_name: str, filter: Dict) -> int:
        query = {"deleteMany": {"filter": filter}}
        result = await self._run_query(self._build_request_collection_url(collection_name), query)
        return result["status"]["deletedCount"]
