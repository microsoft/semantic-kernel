# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from semantic_kernel.connectors.search.bing.bing_search import BingSearch
from semantic_kernel.connectors.search.bing.bing_search_response import BingSearchResponse, BingWebPages
from semantic_kernel.connectors.search.bing.bing_web_page import BingWebPage
from semantic_kernel.data.text_search import KernelSearchResults, SearchFilter, TextSearchOptions, TextSearchResult
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError


@pytest.fixture
def bing_search(bing_unit_test_env):
    """Set up the fixture to configure the Bing Search for these tests."""
    return BingSearch()


@pytest.fixture
def async_client_mock():
    """Set up the fixture to mock AsyncClient."""
    async_client_mock = AsyncMock()
    with patch(
        "semantic_kernel.connectors.search.bing.bing_search.AsyncClient.__aenter__", return_value=async_client_mock
    ):
        yield async_client_mock


@pytest.fixture
def mock_bing_search_response():
    """Set up the fixture to mock BingSearchResponse."""
    mock_web_page = BingWebPage(name="Page Name", snippet="Page Snippet", url="test")
    mock_response = BingSearchResponse(
        query_context={},
        webPages=MagicMock(spec=BingWebPages, value=[mock_web_page], total_estimated_matches=3),
    )

    with (
        patch.object(BingSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        yield mock_response


async def test_bing_search_init_success(bing_search):
    """Test that BingSearch initializes successfully with valid env."""
    # Should not raise any exception
    assert bing_search.settings.api_key.get_secret_value() == "test_api_key"
    assert bing_search.settings.custom_config == "test_org_id"


@pytest.mark.parametrize("exclude_list", [["BING_API_KEY"]], indirect=True)
async def test_bing_search_init_validation_error(bing_unit_test_env, exclude_list):
    """Test that BingSearch raises ServiceInitializationError if BingSettings creation fails."""
    with pytest.raises(ServiceInitializationError):
        BingSearch(env_file_path="invalid.env")


async def test_search_success(bing_unit_test_env, async_client_mock):
    """Test that search method returns KernelSearchResults successfully on valid response."""
    # Arrange
    mock_web_pages = BingWebPage(snippet="Test snippet")
    mock_response = BingSearchResponse(
        webPages=MagicMock(spec=BingWebPages, value=[mock_web_pages], total_estimated_matches=10),
        query_context={"alteredQuery": "altered something"},
    )

    mock_result = MagicMock()
    mock_result.text = """
{"webPages": {
    "value": [{"snippet": "Test snippet"}],
    "totalEstimatedMatches": 10},
    "queryContext": {"alteredQuery": "altered something"}
}"""
    async_client_mock.get.return_value = mock_result

    # Act
    with (
        patch.object(BingSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        search_instance = BingSearch()
        options = TextSearchOptions(include_total_count=True)
        kernel_results: KernelSearchResults[str] = await search_instance.search("Test query", options)

    # Assert
    results_list = []
    async for res in kernel_results.results:
        results_list.append(res)

    assert len(results_list) == 1
    assert results_list[0] == "Test snippet"
    assert kernel_results.total_count == 10
    assert kernel_results.metadata == {"altered_query": "altered something"}


async def test_search_http_status_error(bing_unit_test_env, async_client_mock):
    """Test that search method raises ServiceInvalidRequestError on HTTPStatusError."""
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )
    async_client_mock.get.return_value = mock_response

    # Act
    search_instance = BingSearch()

    # Assert
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await search_instance.search("Test query")
    assert "Failed to get search results." in str(exc_info.value)


async def test_search_request_error(bing_unit_test_env, async_client_mock):
    """Test that search method raises ServiceInvalidRequestError on RequestError."""
    # Arrange
    async_client_mock.get.side_effect = httpx.RequestError("Client error")

    # Act
    search_instance = BingSearch()

    # Assert
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await search_instance.search("Test query")
    assert "A client error occurred while getting search results." in str(exc_info.value)


async def test_search_generic_exception(bing_unit_test_env, async_client_mock):
    """Test that search method raises ServiceInvalidRequestError on unexpected exception."""
    # Arrange
    async_client_mock.get.side_effect = Exception("Something unexpected")

    search_instance = BingSearch()
    # Assert
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await search_instance.search("Test query")
    assert "An unexpected error occurred while getting search results." in str(exc_info.value)


async def test_validate_options_raises_error_for_large_top(bing_search):
    """Test that _validate_options raises ServiceInvalidRequestError when top >= 50."""
    # Arrange
    options = TextSearchOptions(top=50)

    # Act / Assert
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await bing_search.search("test", options)
    assert "count value must be less than 50." in str(exc_info.value)


async def test_get_text_search_results_success(bing_unit_test_env, async_client_mock):
    """Test that get_text_search_results returns KernelSearchResults[TextSearchResult]."""
    # Arrange
    mock_web_pages = BingWebPage(name="Result Name", snippet="Snippet", url="test")
    mock_response = BingSearchResponse(
        query_context={},
        webPages=MagicMock(spec=BingWebPages, value=[mock_web_pages], total_estimated_matches=5),
    )

    mock_result = MagicMock()
    mock_result.text = """"
{"webPages": {
    "value": [{"snippet": "Snippet", "name":"Result Name", "url":"test"}],
    "totalEstimatedMatches": 5},
    "queryContext": {}
}'
"""
    async_client_mock.get.return_value = mock_result

    # Act
    with (
        patch.object(BingSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        search_instance = BingSearch()
        options = TextSearchOptions(include_total_count=True)
        kernel_results: KernelSearchResults[TextSearchResult] = await search_instance.get_text_search_results(
            "Test query", options
        )

    # Assert
    results_list = []
    async for res in kernel_results.results:
        results_list.append(res)

    assert len(results_list) == 1
    assert isinstance(results_list[0], TextSearchResult)
    assert results_list[0].name == "Result Name"
    assert results_list[0].value == "Snippet"
    assert results_list[0].link == "test"
    assert kernel_results.total_count == 5


async def test_get_search_results_success(bing_unit_test_env, async_client_mock, mock_bing_search_response):
    """Test that get_search_results returns KernelSearchResults[BingWebPage]."""
    # Arrange
    mock_result = MagicMock()
    mock_result.text = """
{"webPages": {
    "value": [{"name": "Page Name", "snippet": "Page Snippet", "url": "test"}],
    "totalEstimatedMatches": 3},
    "queryContext": {}
}"""
    async_client_mock.get.return_value = mock_result

    # Act
    search_instance = BingSearch()
    options = TextSearchOptions(include_total_count=True)
    kernel_results = await search_instance.get_search_results("Another query", options)

    # Assert
    results_list = []
    async for res in kernel_results.results:
        results_list.append(res)

    assert len(results_list) == 1
    assert isinstance(results_list[0], BingWebPage)
    assert results_list[0].name == "Page Name"
    assert results_list[0].snippet == "Page Snippet"
    assert results_list[0].url == "test"
    assert kernel_results.total_count == 3


async def test_search_no_filter(bing_search, async_client_mock, mock_bing_search_response):
    """Test that search properly sets params when no filter is provided."""
    # Arrange
    options = TextSearchOptions()

    # Act
    await bing_search.search("test query", options)

    # Assert
    params = async_client_mock.get.call_args.kwargs["params"]

    assert params["count"] == options.top
    assert params["offset"] == options.skip

    # TODO check: shouldn't this output be "test query" instead of "test query+"?
    assert params["q"] == "test query+"


async def test_search_equal_to_filter(bing_search, async_client_mock, mock_bing_search_response):
    """Test that search properly sets params with an EqualTo filter."""

    # Arrange
    my_filter = SearchFilter.equal_to(field_name="freshness", value="Day")
    options = TextSearchOptions(filter=my_filter)

    # Act
    await bing_search.search("test query", options)

    # Assert
    params = async_client_mock.get.call_args.kwargs["params"]

    assert params["count"] == options.top
    assert params["offset"] == options.skip
    # 'freshness' is recognized in QUERY_PARAMETERS, so 'freshness' should be set
    assert "freshness" in params
    assert params["freshness"] == "Day"
    # 'q' should be a combination of the original query plus a plus sign
    assert params["q"] == "test query+".strip()


async def test_search_not_recognized_filter(bing_search, async_client_mock, mock_bing_search_response):
    """Test that search properly appends non-recognized filters to the q parameter."""

    # Arrange
    # 'customProperty' is presumably not in QUERY_PARAMETERS
    my_filter = SearchFilter.equal_to(field_name="customProperty", value="customValue")
    options = TextSearchOptions(filter=my_filter)

    # Act
    await bing_search.search("test query", options)

    # Assert
    params = async_client_mock.get.call_args.kwargs["params"]
    assert params["count"] == options.top
    assert params["offset"] == options.skip
    assert "customProperty" not in params
    # We expect 'q' to contain the extra query param in a plus-joined format
    assert isinstance(params["q"], str)
    assert "customProperty:customValue" in params["q"]
