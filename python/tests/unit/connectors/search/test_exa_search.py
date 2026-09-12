# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from semantic_kernel.connectors.exa import ExaSearch, ExaSearchResponse, ExaSearchResult
from semantic_kernel.data.text_search import KernelSearchResults, TextSearchResult
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError


@pytest.fixture
def exa_search(exa_unit_test_env):
    """Set up the fixture to configure the Exa Search for these tests."""
    return ExaSearch()


@pytest.fixture
def async_client_mock():
    """Set up the fixture to mock AsyncClient."""
    async_client_mock = AsyncMock()
    with patch("semantic_kernel.connectors.exa.AsyncClient.__aenter__", return_value=async_client_mock):
        yield async_client_mock


async def test_exa_search_init_success(exa_search):
    """Test that ExaSearch initializes successfully with valid env."""
    assert exa_search.settings.api_key.get_secret_value() == "test_api_key"


@pytest.mark.parametrize("exclude_list", [["EXA_API_KEY"]], indirect=True)
async def test_exa_search_init_validation_error(exa_unit_test_env):
    """Test that ExaSearch raises ServiceInitializationError if ExaSettings creation fails."""
    with pytest.raises(ServiceInitializationError):
        ExaSearch(env_file_path="invalid.env")


async def test_search_success(exa_unit_test_env, async_client_mock):
    """Test that search returns KernelSearchResults with the highlights joined."""
    mock_response = ExaSearchResponse(
        requestId="req-1",
        results=[
            ExaSearchResult(
                title="Result Name",
                url="https://example.com",
                highlights=["First highlight", "second highlight"],
            )
        ],
        searchTime=12.5,
    )
    async_client_mock.post.return_value = MagicMock()

    with patch.object(ExaSearchResponse, "model_validate_json", return_value=mock_response):
        search_instance = ExaSearch()
        kernel_results: KernelSearchResults[str] = await search_instance.search("Test query", include_total_count=True)

    results_list = [res async for res in kernel_results.results]

    assert results_list == ["First highlight second highlight"]
    assert kernel_results.total_count == 1
    assert kernel_results.metadata == {"request_id": "req-1", "search_time": 12.5, "cost_dollars": None}


async def test_search_falls_back_to_text(exa_unit_test_env, async_client_mock):
    """Test that results without highlights fall back to the summary or full text."""
    mock_response = ExaSearchResponse(
        results=[
            ExaSearchResult(title="Summarized", url="https://example.com/1", summary="A summary"),
            ExaSearchResult(title="Full text", url="https://example.com/2", text="Page text"),
            ExaSearchResult(title="Empty", url="https://example.com/3"),
        ]
    )
    async_client_mock.post.return_value = MagicMock()

    with patch.object(ExaSearchResponse, "model_validate_json", return_value=mock_response):
        kernel_results: KernelSearchResults[str] = await ExaSearch().search("Test query")

    assert [res async for res in kernel_results.results] == ["A summary", "Page text", ""]


async def test_get_text_search_results_success(exa_unit_test_env, async_client_mock):
    """Test that search with output_type=TextSearchResult returns TextSearchResults."""
    mock_response = ExaSearchResponse(
        results=[
            ExaSearchResult(title="Result Name", url="https://example.com", highlights=["Test snippet"]),
        ]
    )
    async_client_mock.post.return_value = MagicMock()

    with patch.object(ExaSearchResponse, "model_validate_json", return_value=mock_response):
        kernel_results: KernelSearchResults[TextSearchResult] = await ExaSearch().search(
            "Test query", include_total_count=True, output_type=TextSearchResult
        )

    results_list = [res async for res in kernel_results.results]

    assert len(results_list) == 1
    assert isinstance(results_list[0], TextSearchResult)
    assert results_list[0].name == "Result Name"
    assert results_list[0].value == "Test snippet"
    assert results_list[0].link == "https://example.com"
    assert kernel_results.total_count == 1


async def test_get_search_results_success(exa_unit_test_env, async_client_mock):
    """Test that search with output_type="Any" returns the raw ExaSearchResults."""
    mock_response = ExaSearchResponse(
        results=[ExaSearchResult(title="Result Name", url="https://example.com", publishedDate="2026-01-01")]
    )
    async_client_mock.post.return_value = MagicMock()

    with patch.object(ExaSearchResponse, "model_validate_json", return_value=mock_response):
        kernel_results: KernelSearchResults[ExaSearchResult] = await ExaSearch().search("Test query", output_type="Any")

    results_list = [res async for res in kernel_results.results]

    assert len(results_list) == 1
    assert isinstance(results_list[0], ExaSearchResult)
    assert results_list[0].published_date == "2026-01-01"


async def test_search_http_status_error(exa_unit_test_env, async_client_mock):
    """Test that search raises ServiceInvalidRequestError on HTTPStatusError."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )
    async_client_mock.post.return_value = mock_response

    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await ExaSearch().search("Test query")
    assert "Failed to get search results." in str(exc_info.value)


async def test_search_request_error(exa_unit_test_env, async_client_mock):
    """Test that search raises ServiceInvalidRequestError on RequestError."""
    async_client_mock.post.side_effect = httpx.RequestError("Client error")

    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await ExaSearch().search("Test query")
    assert "A client error occurred while getting search results." in str(exc_info.value)


async def test_search_generic_exception(exa_unit_test_env, async_client_mock):
    """Test that search raises ServiceInvalidRequestError on unexpected exception."""
    async_client_mock.post.side_effect = Exception("Something unexpected")

    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await ExaSearch().search("Test query")
    assert "An unexpected error occurred while getting search results." in str(exc_info.value)


async def test_validate_options_raises_error_for_large_top(exa_search):
    """Test that _validate_options raises when top exceeds the API maximum."""
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await exa_search.search("test", top=101)
    assert "numResults value must be less than or equal to 100." in str(exc_info.value)


async def test_validate_options_raises_error_for_nonzero_skip(exa_search):
    """Test that nonzero skip is rejected because Exa has no offset pagination."""
    with pytest.raises(ServiceInvalidRequestError) as exc_info:
        await exa_search.search("test", skip=10)
    assert "does not support skip/offset pagination" in str(exc_info.value)


def test_build_request_payload_nests_contents(exa_search):
    """Test that content extraction options are nested under `contents`."""
    payload = exa_search._build_request_payload("query", exa_search._get_options(top=3))

    assert payload == {
        "query": "query",
        "type": "auto",
        "numResults": 3,
        "contents": {"highlights": True},
    }


def test_build_request_payload_with_filters(exa_search):
    """Test that filter lambdas map onto Exa query parameters, collecting list-valued ones."""
    payload = exa_search._build_request_payload(
        "query",
        exa_search._get_options(
            top=5,
            filter=[
                'lambda x: x.category == "news"',
                'lambda x: x.includeDomains == "arxiv.org"',
                'lambda x: x.includeDomains == "nature.com"',
                'lambda x: x.includeText == "new york"',
            ],
        ),
    )

    assert payload["category"] == "news"
    assert payload["includeDomains"] == ["arxiv.org", "nature.com"]
    # SearchLambdaVisitor quote_plus-encodes; JSON body should get decoded values.
    assert payload["includeText"] == ["new york"]


def test_build_request_payload_ignores_invalid_filter(exa_search):
    """Test that an unparsable filter is ignored instead of failing the request."""
    payload = exa_search._build_request_payload(
        "query", exa_search._get_options(top=5, filter="lambda x: x.not_a_parameter == 'value'")
    )

    assert "not_a_parameter" not in payload
