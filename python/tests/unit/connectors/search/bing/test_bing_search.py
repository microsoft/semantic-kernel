# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.search.bing.bing_search import BingSearch
from semantic_kernel.connectors.search.bing.bing_search_response import BingSearchResponse, BingWebPages
from semantic_kernel.connectors.search.bing.bing_search_settings import BingSettings
from semantic_kernel.connectors.search.bing.bing_web_page import BingWebPage
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.text_search.text_search_filter import TextSearchFilter
from semantic_kernel.data.text_search.text_search_options import TextSearchOptions
from semantic_kernel.data.text_search.text_search_result import TextSearchResult
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError


async def test_bing_search_init_success():
    """Test that BingSearch initializes successfully with valid parameters."""
    # Arrange/Act
    with patch.object(BingSettings, "create", return_value=MagicMock(spec=BingSettings)) as mock_settings_create:
        search_instance = BingSearch(api_key="fake_api_key", custom_config="fake_config")

    # Assert
    mock_settings_create.assert_called_once()
    assert search_instance is not None


async def test_bing_search_init_validation_error():
    """Test that BingSearch raises ServiceInitializationError if BingSettings creation fails."""
    # Arrange
    with patch.object(BingSettings, "create", side_effect=ValidationError("error", [])):
        # Act / Assert
        with pytest.raises(ServiceInitializationError) as exc_info:
            _ = BingSearch(api_key="invalid_api_key")
        assert "Failed to create Bing settings." in str(exc_info.value)


async def test_search_success():
    """Test that search method returns KernelSearchResults successfully on valid response."""
    # Arrange
    mock_web_pages = BingWebPage(snippet="Test snippet")
    mock_response = BingSearchResponse(
        webPages=MagicMock(spec=BingWebPages, value=[mock_web_pages], total_estimated_matches=10),
        query_context={"alteredQuery": "altered something"},
    )

    async_client_mock = AsyncMock()
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
        patch("semantic_kernel.connectors.search.bing.bing_search.AsyncClient", return_value=async_client_mock),
        patch.object(BingSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        search_instance = BingSearch(api_key="fake_api_key")
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


async def test_search_http_status_error():
    """Test that search method raises ServiceInvalidRequestError on HTTPStatusError."""
    # Arrange
    async_client_mock = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )
    async_client_mock.get.return_value = mock_response

    # Act
    with patch(
        "semantic_kernel.connectors.search.bing.bing_search.AsyncClient.__aenter__", return_value=async_client_mock
    ):
        search_instance = BingSearch(api_key="fake_api_key")
        # Assert
        with pytest.raises(ServiceInvalidRequestError) as exc_info:
            await search_instance.search("Test query")
        assert "Failed to get search results." in str(exc_info.value)


async def test_search_request_error():
    """Test that search method raises ServiceInvalidRequestError on RequestError."""
    # Arrange
    async_client_mock = AsyncMock()
    async_client_mock.get.side_effect = httpx.RequestError("Client error")

    # Act
    with patch(
        "semantic_kernel.connectors.search.bing.bing_search.AsyncClient.__aenter__", return_value=async_client_mock
    ):
        search_instance = BingSearch(api_key="fake_api_key")
        # Assert
        with pytest.raises(ServiceInvalidRequestError) as exc_info:
            await search_instance.search("Test query")
        assert "A client error occurred while getting search results." in str(exc_info.value)


async def test_search_generic_exception():
    """Test that search method raises ServiceInvalidRequestError on unexpected exception."""
    # Arrange
    async_client_mock = AsyncMock()
    async_client_mock.get.side_effect = Exception("Something unexpected")

    # Act
    with patch(
        "semantic_kernel.connectors.search.bing.bing_search.AsyncClient.__aenter__", return_value=async_client_mock
    ):
        search_instance = BingSearch(api_key="fake_api_key")
        # Assert
        with pytest.raises(ServiceInvalidRequestError) as exc_info:
            await search_instance.search("Test query")
        assert "An unexpected error occurred while getting search results." in str(exc_info.value)


async def test_validate_options_raises_error_for_large_top():
    """Test that _validate_options raises ServiceInvalidRequestError when top >= 50."""
    # Arrange
    search_instance = BingSearch(api_key="fake_api_key")
    options = TextSearchOptions(top=50)

    # Act / Assert
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await search_instance._inner_search("test", options)
    assert "count value must be less than 50." in str(exc_info.value)


async def test_get_text_search_results_success():
    """Test that get_text_search_results returns KernelSearchResults[TextSearchResult]."""
    # Arrange
    mock_web_pages = BingWebPage(name="Result Name", snippet="Snippet", url="test")
    mock_response = BingSearchResponse(
        query_context={},
        webPages=MagicMock(spec=BingWebPages, value=[mock_web_pages], total_estimated_matches=5),
    )

    async_client_mock = AsyncMock()
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
        patch(
            "semantic_kernel.connectors.search.bing.bing_search.AsyncClient.__aenter__", return_value=async_client_mock
        ),
        patch.object(BingSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        search_instance = BingSearch(api_key="fake_api_key")
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


async def test_get_search_results_success():
    """Test that get_search_results returns KernelSearchResults[BingWebPage]."""
    # Arrange
    mock_web_page = BingWebPage(name="Page Name", snippet="Page Snippet", url="test")
    mock_response = BingSearchResponse(
        query_context={},
        webPages=MagicMock(spec=BingWebPages, value=[mock_web_page], total_estimated_matches=3),
    )

    async_client_mock = AsyncMock()
    mock_result = MagicMock()
    mock_result.text = """
{"webPages": {
    "value": [{"name": "Page Name", "snippet": "Page Snippet", "url": "test"}],
    "totalEstimatedMatches": 3},
    "queryContext": {}
}"""
    async_client_mock.get.return_value = mock_result

    # Act
    with (
        patch(
            "semantic_kernel.connectors.search.bing.bing_search.AsyncClient.__aenter__", return_value=async_client_mock
        ),
        patch.object(BingSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        search_instance = BingSearch(api_key="fake_api_key")
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


async def test_build_request_parameters_no_filter():
    """Test that _build_request_parameters properly sets params when no filter is provided."""
    # Arrange
    search_instance = BingSearch(api_key="fake_api_key")
    options = TextSearchOptions()

    # Act
    params = search_instance._build_request_parameters("test query", options)

    # Assert
    assert params["count"] == options.top
    assert params["offset"] == options.skip
    # TODO: shouldn't this output be "test query" instead of "test query+"?
    assert params["q"] == "test query+"


async def test_build_request_parameters_equal_to_filter():
    """Test that _build_request_parameters properly sets params with an EqualTo filter."""

    # Arrange
    search_instance = BingSearch(api_key="fake_api_key")

    my_filter = TextSearchFilter.equal_to(field_name="freshness", value="Day")
    options = TextSearchOptions(filter=my_filter)

    # Act
    params = search_instance._build_request_parameters("test query", options)

    # Assert
    assert params["count"] == options.top
    assert params["offset"] == options.skip
    # 'freshness' is recognized in QUERY_PARAMETERS, so 'freshness' should be set
    assert "freshness" in params
    assert params["freshness"] == "Day"
    # 'q' should be a combination of the original query plus a plus sign
    assert params["q"] == "test query+".strip()


async def test_build_request_parameters_not_recognized_filter():
    """Test that _build_request_parameters properly appends non-recognized filters to the q parameter."""

    # Arrange
    search_instance = BingSearch(api_key="fake_api_key")

    # 'customProperty' is presumably not in QUERY_PARAMETERS
    my_filter = TextSearchFilter.equal_to(field_name="customProperty", value="customValue")
    options = TextSearchOptions(filter=my_filter)

    # Act
    params = search_instance._build_request_parameters("test query", options)

    # Assert
    assert params["count"] == options.top
    assert params["offset"] == options.skip
    assert "customProperty" not in params
    # We expect 'q' to contain the extra query param in a plus-joined format
    assert isinstance(params["q"], str)
    assert "customProperty:customValue" in params["q"]
