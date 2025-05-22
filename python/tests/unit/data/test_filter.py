# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.data.vectors import VectorSearchOptions


def test_lambda_filter():
    options = VectorSearchOptions(filter=lambda x: x.tag == "value")
    assert options.filter is not None


def test_lambda_filter_str():
    options = VectorSearchOptions(filter='lambda x: x.tag == "value"')
    assert options.filter is not None
