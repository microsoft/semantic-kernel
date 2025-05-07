# Copyright (c) Microsoft. All rights reserved.


from pydantic import ValidationError
from pytest import fixture, raises

from semantic_kernel.data.vector_search import SearchType, VectorStoreTextSearch


@fixture
def vector_collection(DictVectorStoreRecordCollection, data_model_definition):
    return DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    )


def test_validation_no_collections():
    with raises(ValidationError):
        VectorStoreTextSearch()


def test_text_search(vector_collection):
    # Create a VectorStoreTextSearch instance with the collection
    vector_search = VectorStoreTextSearch(
        vector_search=vector_collection,
    )

    # Check that the instance is created correctly
    assert vector_search.vector_search == vector_collection
    assert vector_search.search_type == SearchType.VECTOR
