import requests
import json
from typing import Any, Dict, List, Optional, Union

import aiohttp
import asyncio
import nest_asyncio
nest_asyncio.apply()

class AstraClient:
    def __init__(
        self,
        astra_id: str,
        astra_region: str,
        astra_application_token: str,
        keyspace_name: str,
        embedding_dim: int,
        similarity_function: str,
    ):
        self.astra_id = astra_id
        self.astra_application_token = astra_application_token
        self.astra_region = astra_region
        self.keyspace_name = keyspace_name
        self.embedding_dim = embedding_dim
        self.similarity_function = similarity_function

        self.request_base_url = f"https://{self.astra_id}-{self.astra_region}.apps.astra.datastax.com/api/json/v1/{self.keyspace_name}"
        self.request_header = {
            "x-cassandra-token": self.astra_application_token,
            "Content-Type": "application/json",
        }

    async def _run_query(self, request_url: str, query: Dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(request_url, data=json.dumps(query), headers = self.request_header ) as response:
                if response.status == 200:
                    response_dict = await response.json()
                    if "errors" in response_dict:
                        raise Exception(f"Astra DB request error - {response_dict['errors']}")
                    else:
                        return response_dict
                else:
                    raise Exception(f"Astra DB not available. Status : {response}")

    def find_collections(self, include_detail: bool = True):
        query = {"findCollections": {"options": {"explain": include_detail}}}
        result = asyncio.run(self._run_query(self.request_base_url, query))
        return result["status"]["collections"]

    def find_collection(self, collection_name: str):
        collections = self.find_collections(False)
        found = False
        for collection in collections:
            if collection == collection_name:
                found = True
                break
        return found

    def create_collection(self, collection_name: str, embedding_dim: Optional[int] = None, similarity_function: Optional[str] = None):
        query = {"createCollection": {
            "name": collection_name,
            "options": {
                "vector": {
                    "dimension": embedding_dim if embedding_dim is not None else self.embedding_dim,
                    "metric": similarity_function if similarity_function is not None else self.similarity_function,
                }
            }
        }}
        result = asyncio.run(self._run_query(self.request_base_url, query))
        return True if result["status"]["ok"] == 1 else False

    def delete_collection(self, collection_name: str):
        query = {"deleteCollection": {"name": collection_name}}
        result = asyncio.run(self._run_query(self.request_base_url, query))
        return True if result["status"]["ok"] == 1 else False

    def _build_collection_query(self, collection_name: str):
        return f"{self.request_base_url}/{collection_name}"

    def find_documents(self,
                       collection_name: str,
                       filter: Optional[Dict] = None,
                       vector: Optional[List[float]] = None,
                       limit: Optional[int] = None,
                       include_vector: Optional[bool] = None,
                       include_similarity: Optional[bool] = None) -> List[Dict]:
        find_query = {}

        if filter is not None:
            find_query["filter"] = filter

        if vector is not None:
            find_query["sort"] = {
                "$vector": vector
            }

        if include_vector is not None and include_vector == False:
            find_query["projection"] = {
                "$vector": 0
            }

        if limit is not None:
            find_query["options"] = {
                "limit": limit
            }

        if include_similarity is not None:
            if "options" in find_query:
                find_query["options"]["includeSimilarity"] = int(
                    include_similarity)
            else:
                find_query["options"] = {
                    "includeSimilarity": int(include_similarity)
                }

        query = {"find": find_query}
        result = asyncio.run(self._run_query(
            self._build_collection_query(collection_name), query))
        return result["data"]["documents"]

    def insert_document(self, collection_name: str, document: Dict) -> str:
        query = {"insertOne": {"document": document}}
        result = asyncio.run(self._run_query(
            self._build_collection_query(collection_name), query))
        return result["status"]["insertedIds"][0]

    def insert_documents(self, collection_name: str, documents: List[Dict]) -> List[str]:
        query = {"insertMany": {"documents": documents}}
        result = asyncio.run(self._run_query(
            self._build_collection_query(collection_name), query))
        return result["status"]["insertedIds"]

    def update_document(self, collection_name: str, filter: Dict, update: Dict, upsert: bool = True) -> Dict:
        query = {"findOneAndUpdate": {
            "filter": filter,
            "update": update,
            "options": {
                "returnDocument": "after",
                "upsert": upsert
            }
        }}
        result = asyncio.run(self._run_query(
            self._build_collection_query(collection_name), query))
        return result["status"]

    def update_documents(self, collection_name: str, filter: Dict, update: Dict):
        query = {"updateMany": {
            "filter": filter,
            "update": update,
        }}
        result = asyncio.run(self._run_query(
            self._build_collection_query(collection_name), query))
        return result["status"]

    def delete_documents(self, collection_name: str, filter: Dict) -> int:
        query = {"deleteMany": {"filter": filter}}
        result = asyncio.run(self._run_query(
            self._build_collection_query(collection_name), query))
        return result["status"]["deletedCount"]
