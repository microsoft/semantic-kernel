# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from httpx import HTTPStatusError, RequestError, Response

from semantic_kernel.connectors.google_search import (
    GoogleSearch,
    GoogleSearchInformation,
    GoogleSearchResponse,
    GoogleSearchResult,
)
from semantic_kernel.data.text_search import TextSearchResult
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
    with pytest.raises(ServiceInvalidRequestError) as exc:
        await google_search.search(query="test query", top=11)
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
        result = await google_search.search("test", output_type=TextSearchResult)
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
        result = await google_search.search("test", output_type="Any")
        items = [item async for item in result.results]
        assert len(items) == 2
        assert items[0].title == "Title1"
        assert items[1].link == "Link2"


async def test_google_search_includes_total_count(google_search) -> None:
    """Test that total_count is included if include_total_count is True."""
    search_info = GoogleSearchInformation(
        searchTime=0.23, totalResults="42", formattedSearchTime="0.23s", formattedTotalResults="42"
    )
    mock_response = GoogleSearchResponse(search_information=search_info, items=None)

    with patch.object(google_search, "_inner_search", new=AsyncMock(return_value=mock_response)):
        result = await google_search.search(query="test query", include_total_count=True)
        assert result.total_count == 42
        # if we set it to false, total_count should be None
        result_no_count = await google_search.search(query="test query", include_total_count=False)
        assert result_no_count.total_count is None


@pytest.mark.parametrize(
    "filter_lambda,expected",
    [
        ("lambda x: x.cr == 'US'", [{"cr": "US"}]),
        ("lambda x: x.dateRestrict == 'd7'", [{"dateRestrict": "d7"}]),
        ("lambda x: x.fileType == 'pdf'", [{"fileType": "pdf"}]),
        ("lambda x: x.lr == 'lang_en'", [{"lr": "lang_en"}]),
        ("lambda x: x.orTerms == 'foo bar'", [{"orTerms": "foo+bar"}]),
        ("lambda x: x.siteSearch == 'example.com'", [{"siteSearch": "example.com"}]),
        ("lambda x: x.siteSearchFilter == 'e'", [{"siteSearchFilter": "e"}]),
        ("lambda x: x.rights == 'cc_publicdomain'", [{"rights": "cc_publicdomain"}]),
        ("lambda y: y.rights == 'cc_publicdomain'", [{"rights": "cc_publicdomain"}]),
        ("lambda x: x.hl == 'en'", [{"hl": "en"}]),
        ("lambda x: x.filter == '1'", [{"filter": "1"}]),
        ("lambda x: x.cr == 'US' and x.lr == 'lang_en'", [{"cr": "US"}, {"lr": "lang_en"}]),
        (lambda x: x.cr == "US" and x.lr == "lang_en", [{"cr": "US"}, {"lr": "lang_en"}]),
        ("x.cr == 'US'", [{"cr": "US"}]),
    ],
)
def test_parse_filter_lambda_valid(google_search, filter_lambda, expected):
    assert google_search._parse_filter_lambda(filter_lambda) == expected


@pytest.mark.parametrize(
    "filter_lambda,exception_type",
    [
        ("lambda x: x.cr != 'US'", NotImplementedError),
        ("lambda x: x.cr == y", NotImplementedError),
        ("lambda x: x.cr == None", NotImplementedError),
        ("lambda x: x.cr > 'US'", NotImplementedError),
        ("lambda x: x.unknown == 'foo'", ValueError),
        ("lambda x: x.cr == 'US' or x.lr == 'lang_en'", NotImplementedError),
    ],
)
def test_parse_filter_lambda_invalid(google_search, filter_lambda, exception_type):
    with pytest.raises(exception_type):
        google_search._parse_filter_lambda(filter_lambda)
