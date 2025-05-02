# Copyright (c) Microsoft. All rights reserved.


from pytest import fixture, raises

from semantic_kernel.data.vector_search import VectorStoreTextSearch
from semantic_kernel.exceptions import VectorStoreInitializationException


@fixture
def vector_collection(DictVectorStoreRecordCollection, data_model_definition):
    return DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    )


def test_validation_no_collections():
    with raises(VectorStoreInitializationException):
        VectorStoreTextSearch()
