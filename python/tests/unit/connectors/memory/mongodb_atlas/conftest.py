# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import patch

import pytest
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

BASE_PATH = "pymongo.asynchronous.mongo_client.AsyncMongoClient"
DATABASE_PATH = "pymongo.asynchronous.database.AsyncDatabase"
COLLECTION_PATH = "pymongo.asynchronous.collection.AsyncCollection"


@pytest.fixture(autouse=True)
def mock_mongo_client():
    with patch(BASE_PATH, spec=AsyncMongoClient) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_get_database(mock_mongo_client):
    with (
        patch(DATABASE_PATH, spec=AsyncDatabase) as mock_db,
        patch.object(mock_mongo_client, "get_database", new_callable=lambda: mock_db) as mock,
    ):
        yield mock


@pytest.fixture(autouse=True)
def mock_get_collection(mock_get_database):
    with (
        patch(COLLECTION_PATH, spec=AsyncCollection) as mock_collection,
        patch.object(mock_get_database, "get_collection", new_callable=lambda: mock_collection) as mock,
    ):
        yield mock
