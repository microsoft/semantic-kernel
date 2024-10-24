# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from pydantic import BaseModel

from semantic_kernel import Kernel
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.search_base import SearchBase
from semantic_kernel.data.search_options import SearchOptions
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.exceptions.search_exceptions import SearchResultEmptyError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def test_vanilla_search_base():
    search_base_class = SearchBase()
    assert search_base_class is not None
    assert search_base_class._search_function_map == {}
    assert search_base_class._get_options_class == SearchOptions


class TestSearchOptions(SearchOptions):
    """Test search options."""

    test_field: str = "test"


class TestSearchBase(SearchBase):
    async def search_function_test(self, **kwargs) -> KernelSearchResults[Any]:
        """Test search function."""

        async def generator() -> str:
            yield "test"

        return KernelSearchResults(results=generator(), metadata=kwargs)

    async def search_function_empty_test(self, **kwargs) -> KernelSearchResults[Any]:
        """Test search function."""
        raise SearchResultEmptyError("No results found.")

    @property
    def _search_function_map(self) -> dict[str, Callable[..., Awaitable[KernelSearchResults[Any]]]]:
        """Get the search function map."""
        return {
            "search_function_test": self.search_function_test,
            "search_function_empty_test": self.search_function_empty_test,
        }

    @property
    def _get_options_class(self):
        return TestSearchOptions


def test_create_kernel_function():
    search_base_class = TestSearchBase()

    search_function = "search_function_test"
    options = None
    parameters = None
    return_parameter = None
    function_name = "search"
    description = "description"
    map_function = None
    update_options_function = None
    kernel_function = search_base_class.create_kernel_function(
        search_function,
        options,
        parameters,
        return_parameter,
        function_name,
        description,
        map_function,
        update_options_function,
    )
    assert kernel_function is not None
    assert kernel_function.name == function_name
    assert kernel_function.description == description
    assert kernel_function.parameters == []
    assert kernel_function.return_parameter == KernelParameterMetadata(
        name="results",
        description="The search results.",
        type="list[str]",
        type_object=list,
        is_required=True,
    )


def test_create_kernel_function_fail():
    search_base_class = TestSearchBase()
    with pytest.raises(ValueError):
        search_base_class.create_kernel_function(
            search_function="unknown_test",
            options=None,
            parameters=None,
            return_parameter=None,
            function_name="search",
            description="description",
            map_function=None,
            update_options_function=None,
        )


@pytest.mark.asyncio
async def test_create_kernel_function_inner(kernel: Kernel):
    search_base_class = TestSearchBase()

    kernel_function = search_base_class.create_kernel_function(
        search_function="search_function_test",
        options=None,
        parameters=None,
        return_parameter=None,
        function_name="search",
        description="description",
        map_function=None,
        update_options_function=None,
    )
    results = await kernel_function.invoke(kernel, None)
    assert results is not None
    assert results.value == ["test"]


@pytest.mark.asyncio
async def test_create_kernel_function_inner_with_options(kernel: Kernel):
    search_base_class = TestSearchBase()

    kernel_function = search_base_class.create_kernel_function(
        search_function="search_function_test",
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
        map_function=None,
        update_options_function=None,
    )
    results = await kernel_function.invoke(kernel, KernelArguments(city="city"))
    assert results is not None
    assert results.value == ["test"]


@pytest.mark.asyncio
async def test_create_kernel_function_inner_with_other_options_type(kernel: Kernel):
    search_base_class = TestSearchBase()

    kernel_function = search_base_class.create_kernel_function(
        search_function="search_function_test",
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
        map_function=None,
        update_options_function=None,
    )
    results = await kernel_function.invoke(kernel, KernelArguments(test_field="city"))
    assert results is not None
    assert results.value == ["test"]


@pytest.mark.asyncio
async def test_create_kernel_function_inner_no_results(kernel: Kernel):
    search_base_class = TestSearchBase()

    kernel_function = search_base_class.create_kernel_function(
        search_function="search_function_empty_test",
        options=None,
        parameters=None,
        return_parameter=None,
        function_name="search",
        description="description",
        map_function=None,
        update_options_function=None,
    )
    results = await kernel_function.invoke(kernel, None)
    assert results is not None
    assert results.value == ["No results found for this query"]


@pytest.mark.asyncio
async def test_create_kernel_function_inner_update_options(kernel: Kernel):
    search_base_class = TestSearchBase()

    def update_options(search_text, query, vector, options: SearchOptions, kwargs):
        options.filter.equal_to("address/city", kwargs.get("city"))
        return search_text, query, vector, options

    kernel_function = search_base_class.create_kernel_function(
        search_function="search_function_test",
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
        map_function=None,
        update_options_function=update_options,
    )
    results = await kernel_function.invoke(kernel, KernelArguments(city="city"))
    assert results is not None
    assert results.value == ["test"]


def test_default_map_to_string():
    search_base_class = TestSearchBase()
    assert search_base_class._default_map_to_string("test") == "test"

    class TestClass(BaseModel):
        test: str

    assert search_base_class._default_map_to_string(TestClass(test="test")) == '{"test":"test"}'
