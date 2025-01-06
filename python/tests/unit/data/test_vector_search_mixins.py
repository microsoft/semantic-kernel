# Copyright (c) Microsoft. All rights reserved.

from pytest import raises

from semantic_kernel.data import VectorizableTextSearchMixin, VectorizedSearchMixin, VectorTextSearchMixin
from semantic_kernel.exceptions import VectorStoreMixinException


class VectorTextSearchMixinTest(VectorTextSearchMixin):
    """The mixin for text search, to be used in combination with VectorSearchBase."""

    pass


class VectorizableTextSearchMixinTest(VectorizableTextSearchMixin):
    """The mixin for text search, to be used in combination with VectorSearchBase."""

    pass


class VectorizedSearchMixinTest(VectorizedSearchMixin):
    """The mixin for text search, to be used in combination with VectorSearchBase."""

    pass


async def test_text_search():
    test_instance = VectorTextSearchMixinTest()
    assert test_instance is not None
    with raises(VectorStoreMixinException):
        await test_instance.text_search("test")


async def test_vectorizable_text_search():
    test_instance = VectorizableTextSearchMixinTest()
    assert test_instance is not None
    with raises(VectorStoreMixinException):
        await test_instance.vectorizable_text_search("test")


async def test_vectorized_text_search():
    test_instance = VectorizedSearchMixinTest()
    assert test_instance is not None
    with raises(VectorStoreMixinException):
        await test_instance.vectorized_search([1, 2, 3])
