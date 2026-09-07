# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from semantic_kernel.connectors.keenable import (
    APP_TITLE,
    DEFAULT_PUBLIC_URL,
    DEFAULT_URL,
    KeenableSearch,
    KeenableWebPage,
)
from semantic_kernel.data.text_search import KernelSearchResults, TextSearchResult
from semantic_kernel.exceptions import ServiceInvalidRequestError

RESPONSE_JSON = json.dumps({
    "query": "Test query",
    "results": [
        {
            "title": "First",
            "url": "https://example.com/first",
            "snippet": "First snippet",
            "description": "First description",
        },
        {
            "title": "Second",
            "url": "https://example.com/second",
            "snippet": "",
            "description": "Second description",
        },
        {
            "title": "Third",
            "url": "https://example.com/third",
            "snippet": "Third snippet",
            "description": "",
            "acquired_at": "2025-01-01T00:00:00Z",
        },
    ],
})


@pytest.fixture
def keenable_search(keenable_unit_test_env):
    """Set up the fixture to configure the Keenable Search for these tests."""
    return KeenableSearch()


@pytest.fixture
def keenable_search_keyless(monkeypatch):
    """A Keenable Search with no API key anywhere."""
    monkeypatch.delenv("KEENABLE_API_KEY", raising=False)
    return KeenableSearch(env_file_path="nonexistent.env")


@pytest.fixture
def async_client_mock():
    """Set up the fixture to mock AsyncClient."""
    async_client_mock = AsyncMock()
    with patch("semantic_kernel.connectors.keenable.AsyncClient.__aenter__", return_value=async_client_mock):
        yield async_client_mock


@pytest.fixture
def mock_response(async_client_mock):
    """Make the mocked client return a canned three-result response."""
    mock_result = MagicMock()
    mock_result.text = RESPONSE_JSON
    async_client_mock.post.return_value = mock_result
    return mock_result


async def test_keenable_search_init_with_key(keenable_search):
    """Test that KeenableSearch picks up the key from the env."""
    assert keenable_search.settings.api_key.get_secret_value() == "test_api_key"


@pytest.mark.parametrize("exclude_list", [["KEENABLE_API_KEY"]], indirect=True)
async def test_keenable_search_init_without_key(keenable_unit_test_env):
    """Test that KeenableSearch initializes without a key; the key is optional."""
    search_instance = KeenableSearch(env_file_path="nonexistent.env")
    assert search_instance.settings.api_key is None


async def test_keyless_request_uses_public_endpoint(keenable_search_keyless, async_client_mock, mock_response):
    """Without a key: public endpoint, title header, no key header."""
    await keenable_search_keyless.search("Test query")

    call = async_client_mock.post.call_args
    assert call.args[0] == DEFAULT_PUBLIC_URL
    headers = call.kwargs["headers"]
    assert headers["X-Keenable-Title"] == APP_TITLE
    assert "X-API-Key" not in headers
    assert call.kwargs["json"] == {"query": "Test query", "max_results": 5}


async def test_empty_key_is_keyless(monkeypatch, async_client_mock, mock_response):
    """An empty KEENABLE_API_KEY behaves like no key."""
    monkeypatch.setenv("KEENABLE_API_KEY", "")
    await KeenableSearch().search("Test query")

    call = async_client_mock.post.call_args
    assert call.args[0] == DEFAULT_PUBLIC_URL
    assert "X-API-Key" not in call.kwargs["headers"]


async def test_keyed_request_uses_authenticated_endpoint(keenable_search, async_client_mock, mock_response):
    """With a key: authenticated endpoint, key header, title header still sent."""
    await keenable_search.search("Test query", top=3)

    call = async_client_mock.post.call_args
    assert call.args[0] == DEFAULT_URL
    headers = call.kwargs["headers"]
    assert headers["X-API-Key"] == "test_api_key"
    assert headers["X-Keenable-Title"] == APP_TITLE
    assert call.kwargs["json"] == {"query": "Test query", "max_results": 3}


async def test_search_success(keenable_search, mock_response):
    """Test that search returns strings, using the description when the snippet is empty."""
    kernel_results: KernelSearchResults[str] = await keenable_search.search("Test query", include_total_count=True)

    results_list = [res async for res in kernel_results.results]

    assert results_list == ["First snippet", "Second description", "Third snippet"]
    assert kernel_results.total_count == 3
    assert kernel_results.metadata == {"query": "Test query"}


async def test_get_text_search_results_success(keenable_search, mock_response):
    """Test that search returns KernelSearchResults[TextSearchResult] with the right mapping."""
    kernel_results: KernelSearchResults[TextSearchResult] = await keenable_search.search(
        "Test query", include_total_count=True, output_type=TextSearchResult
    )

    results_list = [res async for res in kernel_results.results]

    assert len(results_list) == 3
    assert all(isinstance(res, TextSearchResult) for res in results_list)
    assert results_list[0].name == "First"
    assert results_list[0].value == "First snippet"
    assert results_list[0].link == "https://example.com/first"
    assert results_list[1].value == "Second description"
    assert kernel_results.total_count == 3


async def test_get_search_results_success(keenable_search, mock_response):
    """Test that search with output_type="Any" returns KernelSearchResults[KeenableWebPage]."""
    kernel_results = await keenable_search.search("Test query", include_total_count=True, output_type="Any")

    results_list = [res async for res in kernel_results.results]

    assert len(results_list) == 3
    assert all(isinstance(res, KeenableWebPage) for res in results_list)
    assert results_list[2].title == "Third"
    assert results_list[2].acquired_at == "2025-01-01T00:00:00Z"
    assert kernel_results.total_count == 3


async def test_skip_is_applied_client_side(keenable_search, async_client_mock, mock_response):
    """Test that skip asks for top + skip results and drops the first skip."""
    kernel_results = await keenable_search.search("Test query", top=2, skip=1, include_total_count=True)

    assert async_client_mock.post.call_args.kwargs["json"]["max_results"] == 3
    results_list = [res async for res in kernel_results.results]
    assert results_list == ["Second description", "Third snippet"]
    assert kernel_results.total_count == 2


async def test_search_http_status_error(keenable_search, async_client_mock):
    """Test that search raises ServiceInvalidRequestError on HTTPStatusError."""
    mock_result = MagicMock()
    mock_result.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock(status_code=500)
    )
    async_client_mock.post.return_value = mock_result

    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await keenable_search.search("Test query")
    assert "Failed to get search results." in str(exc_info.value)


async def test_search_rate_limited_keyless(keenable_search_keyless, async_client_mock):
    """Test that a 429 raises, with a hint to set the key when running keyless."""
    mock_result = MagicMock()
    mock_result.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    async_client_mock.post.return_value = mock_result

    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await keenable_search_keyless.search("Test query")
    assert "rate limit" in str(exc_info.value)
    assert "KEENABLE_API_KEY" in str(exc_info.value)


async def test_search_rate_limited_keyed(keenable_search, async_client_mock):
    """Test that a 429 with a key raises without the keyless hint."""
    mock_result = MagicMock()
    mock_result.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    async_client_mock.post.return_value = mock_result

    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await keenable_search.search("Test query")
    assert "rate limit" in str(exc_info.value)
    assert "KEENABLE_API_KEY" not in str(exc_info.value)


async def test_search_request_error(keenable_search, async_client_mock):
    """Test that search raises ServiceInvalidRequestError on RequestError."""
    async_client_mock.post.side_effect = httpx.RequestError("Client error")

    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await keenable_search.search("Test query")
    assert "A client error occurred while getting search results." in str(exc_info.value)


async def test_search_generic_exception(keenable_search, async_client_mock):
    """Test that search raises ServiceInvalidRequestError on an unexpected exception."""
    async_client_mock.post.side_effect = Exception("Something unexpected")

    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await keenable_search.search("Test query")
    assert "An unexpected error occurred while getting search results." in str(exc_info.value)


async def test_validate_options_raises_error_for_large_top(keenable_search):
    """Test that _validate_options raises when top + skip exceeds the API maximum."""
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await keenable_search.search("test", top=50, skip=1)
    assert "top plus skip must not exceed 50." in str(exc_info.value)


async def test_search_no_filter(keenable_search, async_client_mock, mock_response):
    """Test that search sends only query and max_results when no filter is provided."""
    await keenable_search.search("test query")

    assert async_client_mock.post.call_args.kwargs["json"] == {"query": "test query", "max_results": 5}


async def test_search_with_filters(keenable_search, async_client_mock, mock_response):
    """Test that site and date filters end up in the request body, decoded."""
    await keenable_search.search(
        "test query",
        filter="lambda x: x.site == 'learn.microsoft.com' and x.published_after == '2025-01-01'",
    )

    body = async_client_mock.post.call_args.kwargs["json"]
    assert body["site"] == "learn.microsoft.com"
    assert body["published_after"] == "2025-01-01"


async def test_search_ignores_invalid_filter(keenable_search, async_client_mock, mock_response):
    """Test that an unsupported filter is ignored rather than failing the search."""
    await keenable_search.search("test query", filter="lambda x: x.country == 'US'")

    body = async_client_mock.post.call_args.kwargs["json"]
    assert body == {"query": "test query", "max_results": 5}


@pytest.mark.parametrize(
    "filter_lambda,expected",
    [
        ("lambda x: x.site == 'example.com'", [{"site": "example.com"}]),
        ("lambda x: x.published_after == '2025-01-01'", [{"published_after": "2025-01-01"}]),
        ("lambda x: x.published_before == '2025-12-31'", [{"published_before": "2025-12-31"}]),
        (
            "lambda x: x.site == 'example.com' and x.published_after == '2025-01-01'",
            [{"site": "example.com"}, {"published_after": "2025-01-01"}],
        ),
        (
            lambda x: x.site == "example.com" and x.published_after == "2025-01-01",
            [{"site": "example.com"}, {"published_after": "2025-01-01"}],
        ),
    ],
)
def test_parse_filter_lambda_valid(keenable_search, filter_lambda, expected):
    assert keenable_search._parse_filter_lambda(filter_lambda) == expected


@pytest.mark.parametrize(
    "filter_lambda,exception_type",
    [
        ("lambda x: x.site != 'example.com'", NotImplementedError),
        ("lambda x: x.site == y", NotImplementedError),
        ("lambda x: x.site == None", NotImplementedError),
        ("lambda x: x.published_after > '2025-01-01'", NotImplementedError),
        ("lambda x: x.unknown == 'foo'", ValueError),
        ("lambda x: x.site == 'a.com' or x.site == 'b.com'", NotImplementedError),
        ("lambda x: x.country == 'US'", ValueError),  # not in Keenable QUERY_PARAMETERS
    ],
)
def test_parse_filter_lambda_invalid(keenable_search, filter_lambda, exception_type):
    with pytest.raises(exception_type):
        keenable_search._parse_filter_lambda(filter_lambda)
