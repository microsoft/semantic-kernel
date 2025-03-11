# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.memory.pinecone import PineconeStore


async def test_create_store(pinecone_unit_test_env):
    """Test the creation of a Pinecone store."""

    # Create a Pinecone store
    store = PineconeStore()
    assert store is not None
    assert store.client is not None


def test_create_store_grpc(pinecone_unit_test_env):
    """Test the creation of a Pinecone store."""

    # Create a Pinecone store
    store = PineconeStore(use_grpc=True)
    assert store is not None
    assert store.client is not None


async def test_create_collection(pinecone_unit_test_env, data_model_definition):
    """Test the creation of a Pinecone collection."""

    # Create a Pinecone store
    store = PineconeStore()
    assert store is not None

    # Create a collection
    collection = store.get_collection("test_collection", dict, data_model_definition)
    assert collection is not None
    assert collection.collection_name == "test_collection"
