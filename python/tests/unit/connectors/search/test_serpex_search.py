# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import SecretStr

from semantic_kernel.connectors.serpex import (
    SerpexMetadata,
    SerpexResponse,
    SerpexResult,
    SerpexSearch,
    SerpexSettings,
)
from semantic_kernel.data.text_search import KernelSearchResults, TextSearchResult
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError


@pytest.fixture
def serpex_unit_test_env(monkeypatch):
    """Set up environment variables for Serpex tests."""
    monkeypatch.setenv("SERPEX_API_KEY", "test_api_key")
    monkeypatch.setenv("SERPEX_ENGINE", "auto")
    monkeypatch.setenv("SERPEX_CATEGORY", "web")


@pytest.fixture
def serpex_search(serpex_unit_test_env):
    """Set up the fixture to configure the Serpex Search for these tests."""
    return SerpexSearch()


@pytest.fixture
def async_client_mock():
    """Set up the fixture to mock AsyncClient."""
    async_client_mock = AsyncMock()
    with patch("semantic_kernel.connectors.serpex.AsyncClient", return_value=async_client_mock):
        yield async_client_mock


@pytest.fixture
def mock_serpex_response():
    """Set up the fixture to mock SerpexResponse."""
    mock_result = SerpexResult(
        position=1,
        title="Test Title",
        url="https://example.com",
        snippet="Test snippet content",
    )
    mock_metadata = SerpexMetadata(
        number_of_results=10,
        request_time=0.5,
        engine="google",
    )
    return SerpexResponse(
        metadata=mock_metadata,
        results=[mock_result],
        answers=[],
        infoboxes=[],
        suggestions=[],
        corrections=[],
    )


def test_serpex_search_init_success(serpex_unit_test_env):
    """Test that SerpexSearch initializes successfully with valid env."""
    search = SerpexSearch()
    assert search.api_key.get_secret_value() == "test_api_key"
    assert search.engine == "auto"
    assert search.category == "web"


def test_serpex_search_init_with_params():
    """Test that SerpexSearch initializes with provided parameters."""
    search = SerpexSearch(
        api_key=SecretStr("custom_key"),
        engine="google",
        category="web",
        time_range="day",
    )
    assert search.api_key.get_secret_value() == "custom_key"
    assert search.engine == "google"
    assert search.time_range == "day"


def test_serpex_search_init_invalid_engine():
    """Test that SerpexSearch raises error for invalid engine."""
    with pytest.raises(ServiceInitializationError) as exc_info:
        SerpexSearch(api_key=SecretStr("test_key"), engine="invalid_engine")
    assert "Invalid engine" in str(exc_info.value)


@pytest.mark.parametrize("exclude_list", [["SERPEX_API_KEY"]], indirect=True)
def test_serpex_search_init_no_api_key(monkeypatch):
    """Test that SerpexSearch raises ServiceInitializationError without API key."""
    monkeypatch.delenv("SERPEX_API_KEY", raising=False)
    with pytest.raises(ServiceInitializationError) as exc_info:
        SerpexSearch()
    assert "API key is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_success(serpex_unit_test_env, mock_serpex_response):
    """Test that search method returns KernelSearchResults successfully."""
    # Arrange
    search = SerpexSearch()
    
    mock_http_response = MagicMock()
    mock_http_response.json.return_value = {
        "metadata": {"number_of_results": 10, "request_time": 0.5, "engine": "google"},
        "results": [
            {
                "position": 1,
                "title": "Test Title",
                "url": "https://example.com",
                "snippet": "Test snippet content",
            }
        ],
        "answers": [],
        "infoboxes": [],
        "suggestions": [],
        "corrections": [],
    }
    mock_http_response.raise_for_status = MagicMock()
    
    # Act
    with patch("semantic_kernel.connectors.serpex.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_http_response
        mock_client_class.return_value = mock_client
        
        results: KernelSearchResults[TextSearchResult] = await search.search("Python programming")
    
    # Assert
    assert len(results.results) == 1
    assert results.results[0].name == "Test Title"
    assert results.results[0].value == "Test snippet content"
    assert results.results[0].link == "https://example.com"
    assert results.total_count == 10


@pytest.mark.asyncio
async def test_search_http_status_error(serpex_unit_test_env):
    """Test that search raises ServiceInvalidRequestError on HTTP error."""
    # Arrange
    search = SerpexSearch()
    
    # Act & Assert
    with patch("semantic_kernel.connectors.serpex.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=MagicMock()
        )
        mock_client_class.return_value = mock_client
        
        with pytest.raises(ServiceInvalidRequestError) as exc_info:
            await search.search("Test query")
        assert "Serpex API request failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_request_error(serpex_unit_test_env):
    """Test that search raises ServiceInvalidRequestError on request error."""
    # Arrange
    search = SerpexSearch()
    
    # Act & Assert
    with patch("semantic_kernel.connectors.serpex.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client_class.return_value = mock_client
        
        with pytest.raises(ServiceInvalidRequestError) as exc_info:
            await search.search("Test query")
        assert "Failed to connect to Serpex API" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_with_custom_engine(serpex_unit_test_env):
    """Test search with custom engine parameter."""
    # Arrange
    search = SerpexSearch()
    
    mock_http_response = MagicMock()
    mock_http_response.json.return_value = {
        "metadata": {"number_of_results": 5, "request_time": 0.3, "engine": "bing"},
        "results": [],
        "answers": [],
        "infoboxes": [],
        "suggestions": [],
        "corrections": [],
    }
    mock_http_response.raise_for_status = MagicMock()
    
    # Act
    with patch("semantic_kernel.connectors.serpex.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_http_response
        mock_client_class.return_value = mock_client
        
        await search.search("Test query", engine="bing")
        
        # Verify the correct engine was passed
        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["engine"] == "bing"


@pytest.mark.asyncio
async def test_get_text_search_results(serpex_unit_test_env):
    """Test get_text_search_results method."""
    # Arrange
    search = SerpexSearch()
    
    mock_http_response = MagicMock()
    mock_http_response.json.return_value = {
        "metadata": {"number_of_results": 2, "request_time": 0.4, "engine": "google"},
        "results": [
            {"position": 1, "title": "Result 1", "url": "https://test1.com", "snippet": "Snippet 1"},
            {"position": 2, "title": "Result 2", "url": "https://test2.com", "snippet": "Snippet 2"},
        ],
        "answers": [],
        "infoboxes": [],
        "suggestions": [],
        "corrections": [],
    }
    mock_http_response.raise_for_status = MagicMock()
    
    # Act
    with patch("semantic_kernel.connectors.serpex.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_http_response
        mock_client_class.return_value = mock_client
        
        results = []
        async for result in search.get_text_search_results("Test query"):
            results.append(result)
    
    # Assert
    assert len(results) == 2
    assert results[0].name == "Result 1"
    assert results[1].name == "Result 2"


@pytest.mark.asyncio
async def test_get_search_results(serpex_unit_test_env):
    """Test get_search_results method returns SerpexResult objects."""
    # Arrange
    search = SerpexSearch()
    
    mock_http_response = MagicMock()
    mock_http_response.json.return_value = {
        "metadata": {"number_of_results": 1, "request_time": 0.2, "engine": "duckduckgo"},
        "results": [
            {
                "position": 1,
                "title": "DuckDuckGo Result",
                "url": "https://duck.com",
                "snippet": "Privacy search",
            },
        ],
        "answers": [],
        "infoboxes": [],
        "suggestions": [],
        "corrections": [],
    }
    mock_http_response.raise_for_status = MagicMock()
    
    # Act
    with patch("semantic_kernel.connectors.serpex.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_http_response
        mock_client_class.return_value = mock_client
        
        results = []
        async for result in search.get_search_results("Privacy test"):
            results.append(result)
    
    # Assert
    assert len(results) == 1
    assert isinstance(results[0], SerpexResult)
    assert results[0].title == "DuckDuckGo Result"
    assert results[0].url == "https://duck.com"
