# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from semantic_kernel.connectors.search.brave import BraveSearch, BraveSearchResponse, BraveWebPage, BraveWebPages
from semantic_kernel.data.text_search import KernelSearchResults, SearchFilter, TextSearchOptions, TextSearchResult
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError


@pytest.fixture
def brave_search(brave_unit_test_env):
    """Set up the fixture to configure the brave Search for these tests."""
    return BraveSearch()


@pytest.fixture
def async_client_mock():
    """Set up the fixture to mock AsyncClient."""
    async_client_mock = AsyncMock()
    with patch("semantic_kernel.connectors.search.brave.AsyncClient.__aenter__", return_value=async_client_mock):
        yield async_client_mock


@pytest.fixture
def mock_brave_search_response():
    """Set up the fixture to mock braveSearchResponse."""
    mock_web_page = BraveWebPage(name="Page Name", snippet="Page Snippet", url="test")
    mock_response = BraveSearchResponse(
        query_context={},
        webPages=MagicMock(spec=BraveWebPages, value=[mock_web_page], total_estimated_matches=3),
    )

    with (
        patch.object(BraveSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        yield mock_response


async def test_brave_search_init_success(brave_search):
    """Test that braveSearch initializes successfully with valid env."""
    # Should not raise any exception
    assert brave_search.settings.api_key.get_secret_value() == "test_api_key"


@pytest.mark.parametrize("exclude_list", [["BRAVE_API_KEY"]], indirect=True)
async def test_brave_search_init_validation_error(brave_unit_test_env):
    """Test that braveSearch raises ServiceInitializationError if BraveSettings creation fails."""
    with pytest.raises(ServiceInitializationError):
        BraveSearch(env_file_path="invalid.env")


async def test_search_success(brave_unit_test_env, async_client_mock):
    """Test that search method returns KernelSearchResults successfully on valid response."""
    # Arrange
    mock_web_pages = BraveWebPage(description="Test snippet")
    mock_response = BraveSearchResponse(
        web_pages=MagicMock(spec=BraveWebPages, results=[mock_web_pages]),
        query_context={
            "original": "original",
            "altered": "altered something",
            "show_strict_warning": False,
            "spellcheck_off": False,
            "country": "us",
        },
    )

    mock_result = MagicMock()
    mock_result.text = """
    {"query": {'original':'original',"altered": 
        "altered something","show_strict_warning":False,"spellcheck_off":False,'country':"us"},
    "results": [{"description": "Test snippet"}]}
    }"""
    async_client_mock.get.return_value = mock_result

    # Act
    with (
        patch.object(BraveSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        search_instance = BraveSearch()
        options = TextSearchOptions(include_total_count=True)
        kernel_results: KernelSearchResults[str] = await search_instance.search("Test query", options)

    # Assert
    results_list = []
    async for res in kernel_results.results:
        results_list.append(res)

    assert len(results_list) == 1
    assert results_list[0] == "Test snippet"
    assert kernel_results.total_count == 1
    assert kernel_results.metadata == {
        "original": "original",
        "altered": "altered something",
        "show_strict_warning": False,
        "spellcheck_off": False,
        "country": "us",
    }


async def test_search_http_status_error(brave_unit_test_env, async_client_mock):
    """Test that search method raises ServiceInvalidRequestError on HTTPStatusError."""
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )
    async_client_mock.get.return_value = mock_response

    # Act
    search_instance = BraveSearch()

    # Assert
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await search_instance.search("Test query")
    assert "Failed to get search results." in str(exc_info.value)


async def test_search_request_error(brave_unit_test_env, async_client_mock):
    """Test that search method raises ServiceInvalidRequestError on RequestError."""
    # Arrange
    async_client_mock.get.side_effect = httpx.RequestError("Client error")

    # Act
    search_instance = BraveSearch()

    # Assert
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await search_instance.search("Test query")
    assert "A client error occurred while getting search results." in str(exc_info.value)


async def test_search_generic_exception(brave_unit_test_env, async_client_mock):
    """Test that search method raises ServiceInvalidRequestError on unexpected exception."""
    # Arrange
    async_client_mock.get.side_effect = Exception("Something unexpected")

    search_instance = BraveSearch()
    # Assert
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await search_instance.search("Test query")
    assert "An unexpected error occurred while getting search results." in str(exc_info.value)


async def test_validate_options_raises_error_for_large_top(brave_search):
    """Test that _validate_options raises ServiceInvalidRequestError when top >= 21."""
    # Arrange
    options = TextSearchOptions(top=21)

    # Act / Assert
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await brave_search.search("test", options)
    assert "count value must be less than 21." in str(exc_info.value)


async def test_get_text_search_results_success(brave_unit_test_env, async_client_mock):
    """Test that get_text_search_results returns KernelSearchResults[TextSearchResult]."""

    # Arrange
    mock_web_pages = BraveWebPage(title="Result Name", description="Test snippet", url="test")
    mock_response = BraveSearchResponse(
        web_pages=MagicMock(spec=BraveWebPages, results=[mock_web_pages]),
        query_context={},
    )

    mock_result = MagicMock()
    mock_result.text = """
    { "results": [{"description": "Test snippet","title":"Result Name","url":"test"}] ,
    "query": {}
    }
    """
    async_client_mock.get.return_value = mock_result

    # Act
    with (
        patch.object(BraveSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        search_instance = BraveSearch()
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
    assert results_list[0].value == "Test snippet"
    assert results_list[0].link == "test"
    assert kernel_results.total_count == 1


async def test_get_search_results_success(brave_unit_test_env, async_client_mock, mock_brave_search_response):
    """Test that get_search_results returns KernelSearchResults[braveWebPage]."""
    # Arrange
    mock_web_pages = BraveWebPage(title="Result Name", description="Page snippet", url="test")
    mock_response = BraveSearchResponse(
        web_pages=MagicMock(spec=BraveWebPages, results=[mock_web_pages]),
        query_context={},
    )
    mock_result = MagicMock()
    mock_result.text = """
 { "results": [{"description": "Page snippet","title":"Result Name","url":"test"}] ,
                    
}"""

    async_client_mock.get.return_value = mock_result

    # Act
    with (
        patch.object(BraveSearchResponse, "model_validate_json", return_value=mock_response),
    ):
        # Act
        search_instance = BraveSearch()
        options = TextSearchOptions(include_total_count=True)
        kernel_results = await search_instance.get_search_results("Another query", options)

    # Assert
    results_list = []
    async for res in kernel_results.results:
        results_list.append(res)

    assert len(results_list) == 1
    assert isinstance(results_list[0], BraveWebPage)
    assert results_list[0].title == "Result Name"
    assert results_list[0].description == "Page snippet"
    assert results_list[0].url == "test"
    assert kernel_results.total_count == 1


async def test_search_no_filter(brave_search, async_client_mock, mock_brave_search_response):
    """Test that search properly sets params when no filter is provided."""
    # Arrange
    options = TextSearchOptions()

    # Act
    await brave_search.search("test query", options)

    # Assert
    params = async_client_mock.get.call_args.kwargs["params"]

    assert params["count"] == options.top
    assert params["offset"] == options.skip

    # TODO check: shouldn't this output be "test query" instead of "test query+"?
    assert params["q"] == "test query"


async def test_search_equal_to_filter(brave_search, async_client_mock, mock_brave_search_response):
    """Test that search properly sets params with an EqualTo filter."""

    # Arrange
    my_filter = SearchFilter.equal_to(field_name="spellcheck", value=True)
    options = TextSearchOptions(filter=my_filter)

    # Act
    await brave_search.search("test query", options)

    # Assert
    params = async_client_mock.get.call_args.kwargs["params"]

    assert params["count"] == options.top
    assert params["offset"] == options.skip
    # 'spellcheck' is recognized in QUERY_PARAMETERS, so 'spellcheck' should be set
    assert "spellcheck" in params
    assert params["spellcheck"]

    assert params["q"] == "test query"


async def test_search_not_recognized_filter(brave_search, async_client_mock, mock_brave_search_response):
    """Test that search properly appends non-recognized filters to the q parameter."""

    # Arrange
    # 'customProperty' is presumably not in QUERY_PARAMETERS
    my_filter = SearchFilter.equal_to(field_name="customProperty", value="customValue")
    options = TextSearchOptions(filter=my_filter)

    # Act
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await brave_search.search("test query", options)

    # Assert
    assert "Observed an unwanted parameter named customProperty with value customValue ." in str(exc_info.value)
