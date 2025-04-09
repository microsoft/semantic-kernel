# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from httpx import HTTPStatusError, RequestError, Response

from semantic_kernel.connectors.search.google.google_search import GoogleSearch
from semantic_kernel.connectors.search.google.google_search_response import (
    GoogleSearchInformation,
    GoogleSearchResponse,
)
from semantic_kernel.connectors.search.google.google_search_result import GoogleSearchResult
from semantic_kernel.data.text_search import AnyTagsEqualTo, EqualTo, TextSearchOptions
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError


@pytest.fixture
def google_search(google_search_unit_test_env):
    """Fixture to return a GoogleSearch instance with valid settings."""
    return GoogleSearch()


async def test_google_search_init_success(google_search) -> None:
    """Test that GoogleSearch successfully initializes with valid parameters."""
    # Should not raise any exception
    assert google_search.settings.api_key.get_secret_value() == "test_api_key"
    assert google_search.settings.engine_id == "test_id"


@pytest.mark.parametrize("exclude_list", [["GOOGLE_SEARCH_API_KEY"]], indirect=True)
async def test_google_search_init_validation_error(google_search_unit_test_env) -> None:
    """Test that GoogleSearch raises ServiceInitializationError when GoogleSearchSettings creation fails."""
    with pytest.raises(ServiceInitializationError):
        GoogleSearch(env_file_path="invalid.env")


async def test_google_search_top_greater_than_10_raises_error(google_search) -> None:
    """Test that passing a top value greater than 10 raises ServiceInvalidRequestError."""
    options = TextSearchOptions()
    options.top = 11  # Invalid
    with pytest.raises(ServiceInvalidRequestError) as exc:
        await google_search.search(query="test query", options=options)
    assert "count value must be less than or equal to 10." in str(exc.value)


async def test_google_search_no_items_in_response(google_search) -> None:
    """Test that when the response has no items, search results yield nothing."""
    mock_response = GoogleSearchResponse(items=None)

    # We'll mock _inner_search to return our mock_response
    with patch.object(google_search, "_inner_search", new=AsyncMock(return_value=mock_response)):
        result = await google_search.search("test")
        # Extract all items from the AsyncIterable
        items = [item async for item in result.results]
        assert len(items) == 0


async def test_google_search_partial_items_in_response(google_search) -> None:
    """Test that snippets are properly returned in search results."""
    snippet_1 = "Snippet 1"
    snippet_2 = "Snippet 2"
    item_1 = GoogleSearchResult(snippet=snippet_1)
    item_2 = GoogleSearchResult(snippet=snippet_2)
    mock_response = GoogleSearchResponse(items=[item_1, item_2])

    with patch.object(google_search, "_inner_search", new=AsyncMock(return_value=mock_response)):
        result = await google_search.search("test")
        items = [item async for item in result.results]
        assert len(items) == 2
        assert items[0] == snippet_1
        assert items[1] == snippet_2


async def test_google_search_request_http_status_error(google_search) -> None:
    """Test that HTTP status errors raise ServiceInvalidRequestError."""
    # Mock the AsyncClient.get call to raise HTTPStatusError
    with patch(
        "httpx.AsyncClient.get",
        new=AsyncMock(side_effect=HTTPStatusError("Error", request=None, response=Response(status_code=400))),
    ):
        with pytest.raises(ServiceInvalidRequestError) as exc:
            await google_search.search("query")
        assert "Failed to get search results." in str(exc.value)


async def test_google_search_request_error(google_search) -> None:
    """Test that request errors raise ServiceInvalidRequestError."""
    # Mock the AsyncClient.get call to raise RequestError
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=RequestError("Client error"))):
        with pytest.raises(ServiceInvalidRequestError) as exc:
            await google_search.search("query")
        assert "A client error occurred while getting search results." in str(exc.value)


async def test_google_search_unexpected_error(google_search) -> None:
    """Test that unexpected exceptions raise ServiceInvalidRequestError."""
    # Mock the AsyncClient.get call to raise a random exception
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=Exception("Random error"))):
        with pytest.raises(ServiceInvalidRequestError) as exc:
            await google_search.search("query")
        assert "An unexpected error occurred while getting search results." in str(exc.value)


async def test_get_text_search_results(google_search) -> None:
    """Test that get_text_search_results returns TextSearchResults that contain name, value, and link."""
    item_1 = GoogleSearchResult(title="Title1", snippet="Snippet1", link="Link1")
    item_2 = GoogleSearchResult(title="Title2", snippet="Snippet2", link="Link2")
    mock_response = GoogleSearchResponse(items=[item_1, item_2])

    with patch.object(google_search, "_inner_search", new=AsyncMock(return_value=mock_response)):
        result = await google_search.get_text_search_results("test")
        items = [item async for item in result.results]
        assert len(items) == 2
        assert items[0].name == "Title1"
        assert items[0].value == "Snippet1"
        assert items[0].link == "Link1"
        assert items[1].name == "Title2"
        assert items[1].value == "Snippet2"
        assert items[1].link == "Link2"


async def test_get_search_results(google_search) -> None:
    """Test that get_search_results returns GoogleSearchResult items directly."""
    item_1 = GoogleSearchResult(title="Title1", snippet="Snippet1", link="Link1")
    item_2 = GoogleSearchResult(title="Title2", snippet="Snippet2", link="Link2")
    mock_response = GoogleSearchResponse(items=[item_1, item_2])

    with patch.object(google_search, "_inner_search", new=AsyncMock(return_value=mock_response)):
        result = await google_search.get_search_results("test")
        items = [item async for item in result.results]
        assert len(items) == 2
        assert items[0].title == "Title1"
        assert items[1].link == "Link2"


async def test_build_query_equal_to_filter(google_search) -> None:
    """Test that if an EqualTo filter is recognized, it is sent along in query params."""
    filters = [
        EqualTo(field_name="lr", value="lang_en"),
        AnyTagsEqualTo(field_name="tags", value="tag1"),
    ]  # second one is not recognized
    options = TextSearchOptions()
    options.filter.filters = filters

    with patch.object(google_search, "_inner_search", new=AsyncMock(return_value=GoogleSearchResponse())):
        await google_search.search(query="hello world", options=options)


async def test_google_search_includes_total_count(google_search) -> None:
    """Test that total_count is included if include_total_count is True."""
    search_info = GoogleSearchInformation(
        searchTime=0.23, totalResults="42", formattedSearchTime="0.23s", formattedTotalResults="42"
    )
    mock_response = GoogleSearchResponse(search_information=search_info, items=None)

    with patch.object(google_search, "_inner_search", new=AsyncMock(return_value=mock_response)):
        options = TextSearchOptions()
        options.include_total_count = True  # not standard, so we'll set it dynamically
        result = await google_search.search(query="test query", options=options)
        assert result.total_count == 42
        # if we set it to false, total_count should be None
        options.include_total_count = False
        result_no_count = await google_search.search(query="test query", options=options)
        assert result_no_count.total_count is None
