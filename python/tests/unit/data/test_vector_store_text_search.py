# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

from pytest import fixture, mark, raises

from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding
from semantic_kernel.data import VectorStoreTextSearch
from semantic_kernel.exceptions import VectorStoreTextSearchValidationError


@fixture
def vector_collection(DictVectorStoreRecordCollection, data_model_definition):
    return DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    )


@mark.asyncio
async def test_from_vectorizable_text_search(vector_collection):
    vsts = VectorStoreTextSearch.from_vectorizable_text_search(vector_collection)
    assert vsts is not None
    assert vsts.vectorizable_text_search is not None
    search = await vsts.search("test")
    text_search_result = await vsts.get_text_search_results("test")
    search_result = await vsts.get_search_results("test")
    assert search is not None
    assert text_search_result is not None
    assert search_result is not None


@mark.asyncio
async def test_from_vector_text_search(vector_collection):
    vsts = VectorStoreTextSearch.from_vector_text_search(vector_collection)
    assert vsts is not None
    assert vsts.vector_text_search is not None
    search = await vsts.search("test")
    text_search_result = await vsts.get_text_search_results("test")
    search_result = await vsts.get_search_results("test")
    assert search is not None
    assert text_search_result is not None
    assert search_result is not None


@mark.asyncio
async def test_from_vectorized_search(vector_collection, azure_openai_unit_test_env):
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding_base.OpenAITextEmbeddingBase.generate_raw_embeddings",
        return_value=[1, 2, 3],
    ):
        vsts = VectorStoreTextSearch.from_vectorized_search(vector_collection, AzureTextEmbedding())
        assert vsts is not None
        assert vsts.vectorized_search is not None
        assert vsts.embedding_service is not None
        search = await vsts.search("test")
        text_search_result = await vsts.get_text_search_results("test")
        search_result = await vsts.get_search_results("test")
        assert search is not None
        assert text_search_result is not None
        assert search_result is not None


def test_validation_no_embedder_for_vectorized_search(vector_collection):
    with raises(VectorStoreTextSearchValidationError):
        VectorStoreTextSearch(vectorized_search=vector_collection)


def test_validation_no_collections():
    with raises(VectorStoreTextSearchValidationError):
        VectorStoreTextSearch()
