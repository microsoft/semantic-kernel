# Copyright (c) Microsoft. All rights reserved.

from typing import Any
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from semantic_kernel import Kernel
from semantic_kernel.data.const import DEFAULT_DESCRIPTION, DEFAULT_FUNCTION_NAME
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.search_options import SearchOptions
from semantic_kernel.data.text_search.text_search import TextSearch
from semantic_kernel.data.text_search.text_search_options import TextSearchOptions
from semantic_kernel.data.text_search.text_search_result import TextSearchResult
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.exceptions.function_exceptions import TextSearchException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def test_text_search():
    search_base_class = TextSearch()
    assert search_base_class is not None
    assert search_base_class.options_class == TextSearchOptions


class TestSearch(TextSearch):
    async def search(self, **kwargs) -> KernelSearchResults[Any]:
        """Test search function."""

        async def generator() -> str:
            yield "test"

        return KernelSearchResults(results=generator(), metadata=kwargs)

    async def get_text_search_results(
        self, query: str, options: SearchOptions | None = None, **kwargs: Any
    ) -> KernelSearchResults[TextSearchResult]:
        """Test get text search result function."""

        async def generator() -> TextSearchResult:
            yield TextSearchResult(value="test")

        return KernelSearchResults(results=generator(), metadata=kwargs)

    async def get_search_results(
        self, query: str, options: SearchOptions | None = None, **kwargs: Any
    ) -> KernelSearchResults[Any]:
        """Test get search result function."""

        async def generator() -> str:
            yield "test"

        return KernelSearchResults(results=generator(), metadata=kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize("search_function", ["search", "get_text_search_result", "get_search_result"])
async def test_create_kernel_function(search_function: str, kernel: Kernel):
    test_search = TestSearch()
    kernel_function = test_search._create_kernel_function(
        search_function,
    )
    assert kernel_function is not None
    assert kernel_function.name == DEFAULT_FUNCTION_NAME
    assert kernel_function.description == DEFAULT_DESCRIPTION
    assert len(kernel_function.parameters) == 3
    assert kernel_function.return_parameter == KernelParameterMetadata(
        name="results",
        description="The search results.",
        type="list[str]",
        type_object=list,
        is_required=True,
    )
    results = await kernel_function.invoke(kernel, KernelArguments(query="query"))
    assert results is not None
    assert results.value == (
        ['{"name":null,"value":"test","link":null}'] if search_function == "get_text_search_result" else ["test"]
    )


def test_create_kernel_function_fail():
    test_search = TestSearch()
    with pytest.raises(ValueError):
        test_search._create_kernel_function(
            search_function="unknown_test",
            options=None,
            parameters=None,
            return_parameter=None,
            function_name="search",
            description="description",
            string_mapper=None,
        )


@pytest.mark.asyncio
async def test_create_kernel_function_inner(kernel: Kernel):
    test_search = TestSearch()

    kernel_function = test_search._create_kernel_function(
        search_function="search",
        options=None,
        parameters=[],
        return_parameter=None,
        function_name="search",
        description="description",
        string_mapper=None,
    )
    results = await kernel_function.invoke(kernel, None)
    assert results is not None
    assert results.value == ["test"]


@pytest.mark.asyncio
async def test_create_kernel_function_inner_with_options(kernel: Kernel):
    test_search = TestSearch()

    kernel_function = test_search._create_kernel_function(
        search_function="search",
        options=SearchOptions(),
        parameters=[
            KernelParameterMetadata(
                name="city",
                description="The city that you want to search for a hotel in.",
                type="str",
                is_required=False,
                type_object=str,
            )
        ],
        return_parameter=None,
        function_name="search",
        description="description",
        string_mapper=None,
    )
    results = await kernel_function.invoke(kernel, KernelArguments(city="city"))
    assert results is not None
    assert results.value == ["test"]


@pytest.mark.asyncio
async def test_create_kernel_function_inner_with_other_options_type(kernel: Kernel):
    test_search = TestSearch()

    kernel_function = test_search._create_kernel_function(
        search_function="search",
        options=VectorSearchOptions(),
        parameters=[
            KernelParameterMetadata(
                name="test_field",
                description="The test field.",
                type="str",
                is_required=False,
                type_object=str,
            )
        ],
        return_parameter=None,
        function_name="search",
        description="description",
        string_mapper=None,
    )
    results = await kernel_function.invoke(kernel, KernelArguments(test_field="city"))
    assert results is not None
    assert results.value == ["test"]


@pytest.mark.asyncio
async def test_create_kernel_function_inner_no_results(kernel: Kernel):
    test_search = TestSearch()

    kernel_function = test_search._create_kernel_function(
        search_function="search",
        options=None,
        parameters=[],
        return_parameter=None,
        function_name="search",
        description="description",
        string_mapper=None,
    )
    with (
        patch.object(test_search, "search") as mock_search,
        pytest.raises(TextSearchException),
    ):
        mock_search.side_effect = Exception("fail")
        await kernel_function.invoke(kernel, None)


@pytest.mark.asyncio
async def test_create_kernel_function_inner_update_options(kernel: Kernel):
    test_search = TestSearch()

    def update_options(search_text, query, vector, options: SearchOptions, kwargs):
        options.filter.equal_to("address/city", kwargs.get("city"))
        return search_text, query, vector, options

    kernel_function = test_search._create_kernel_function(
        search_function="search",
        options=None,
        parameters=[
            KernelParameterMetadata(
                name="city",
                description="The city that you want to search for a hotel in.",
                type="str",
                is_required=False,
                type_object=str,
            )
        ],
        return_parameter=None,
        function_name="search",
        description="description",
        string_mapper=None,
    )
    results = await kernel_function.invoke(kernel, KernelArguments(city="city"))
    assert results is not None
    assert results.value == ["test"]


def test_default_map_to_string():
    test_search = TestSearch()
    assert test_search._default_map_to_string("test") == "test"

    class TestClass(BaseModel):
        test: str

    assert test_search._default_map_to_string(TestClass(test="test")) == '{"test":"test"}'
