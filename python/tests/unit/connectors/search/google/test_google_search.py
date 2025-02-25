# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import HTTPStatusError, RequestError
from pydantic import ValidationError

from semantic_kernel.connectors.search.google.google_search import GoogleSearch
from semantic_kernel.connectors.search.google.google_search_response import (
    GoogleSearchInformation,
    GoogleSearchResponse,
)
from semantic_kernel.connectors.search.google.google_search_result import GoogleSearchResult
from semantic_kernel.connectors.search.google.google_search_settings import GoogleSearchSettings
from semantic_kernel.data.text_search.text_search_filter import TextSearchFilter
from semantic_kernel.data.text_search.text_search_options import TextSearchOptions
from semantic_kernel.data.text_search.text_search_result import TextSearchResult
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError


async def test_google_search_init_success() -> None:
    """Test that GoogleSearch is initialized successfully when settings are valid."""
    with patch.object(
        GoogleSearchSettings, "create", return_value=MagicMock(spec=GoogleSearchSettings)
    ) as mock_settings_create:
        # Arrange
        api_key = "fake_api_key"
        search_engine_id = "fake_engine_id"

        # Act
        google_search = GoogleSearch(api_key=api_key, search_engine_id=search_engine_id)

        # Assert
        mock_settings_create.assert_called_once_with(
            api_key=api_key,
            engine_id=search_engine_id,
            env_file_path=None,
            env_file_encoding=None,
        )
        assert google_search.settings is not None


async def test_google_search_init_validation_error() -> None:
    """Test that ServiceInitializationError is raised if settings creation fails validation."""
    with patch.object(GoogleSearchSettings, "create", side_effect=ValidationError("error", [])):
        # Arrange & Act & Assert
        with pytest.raises(ServiceInitializationError) as exc:
            GoogleSearch(api_key="invalid", search_engine_id="invalid")
        assert "Failed to create Google settings." in str(exc.value)


async def test_google_search_search_calls_inner_search() -> None:
    """Test the search method calls _inner_search with the correct arguments."""
    # Arrange
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    mock_response = MagicMock()
    with patch.object(google_search, "_inner_search", return_value=mock_response) as mock_inner:
        # Act
        await google_search.search(query="test query", options=None)

        # Assert
        mock_inner.assert_called_once()


async def test_google_search_get_text_search_results_calls_inner_search() -> None:
    """Test the get_text_search_results method calls _inner_search with the correct arguments."""
    # Arrange
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    mock_response = MagicMock()
    with patch.object(google_search, "_inner_search", return_value=mock_response) as mock_inner:
        # Act
        await google_search.get_text_search_results(query="test query", options=None)

        # Assert
        mock_inner.assert_called_once()


async def test_google_search_get_search_results_calls_inner_search() -> None:
    """Test the get_search_results method calls _inner_search with the correct arguments."""
    # Arrange
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    mock_response = MagicMock()
    with patch.object(google_search, "_inner_search", return_value=mock_response) as mock_inner:
        # Act
        await google_search.get_search_results(query="test query", options=None)

        # Assert
        mock_inner.assert_called_once()


async def test__validate_options_raises_error_if_top_too_high() -> None:
    """Test that _validate_options raises ServiceInvalidRequestError if top results > 10."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    options = TextSearchOptions(top=11, skip=0)
    with pytest.raises(ServiceInvalidRequestError) as exc:
        google_search._validate_options(options)
    assert "count value must be less than or equal to 10." in str(exc.value)


async def test__validate_options_does_not_raise_if_top_ok() -> None:
    """Test that _validate_options does not raise if top <= 10."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    options = TextSearchOptions(top=10, skip=0)
    # Should not raise
    google_search._validate_options(options)


async def test__get_options_returns_existing_text_search_options() -> None:
    """Test _get_options returns the provided TextSearchOptions if already of correct type."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    original_options = TextSearchOptions(top=5, skip=2)
    returned_options = google_search._get_options(original_options)
    assert returned_options == original_options


async def test__get_options_creates_new_text_search_options_if_none() -> None:
    """Test _get_options creates new TextSearchOptions if none is provided."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    returned_options = google_search._get_options(None)
    assert isinstance(returned_options, TextSearchOptions)


async def test__get_options_creates_new_options_if_wrong_type_in_kwargs() -> None:
    """Test _get_options handles invalid kwargs gracefully and returns a default TextSearchOptions."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    returned_options = google_search._get_options(None, top="invalid")
    # should still return a default object
    assert isinstance(returned_options, TextSearchOptions)


async def test__inner_search_success_returns_parsed_response() -> None:
    """Test _inner_search returns the parsed JSON response on success."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")

    mock_response = GoogleSearchResponse()

    # mock an OK response from the client
    mock_ok_response = MagicMock()
    mock_ok_response.raise_for_status = MagicMock()
    mock_ok_response.text = "fake_json_text"

    async_client_mock = AsyncMock()
    async_client_mock.get.return_value = mock_ok_response

    with (
        patch.object(google_search, "_validate_options") as mock_validate,
        patch(
            "semantic_kernel.connectors.search.google.google_search.AsyncClient.__aenter__",
            return_value=async_client_mock,
        ),
        patch(
            "semantic_kernel.connectors.search.google.google_search_response.GoogleSearchResponse.model_validate_json",
            return_value=mock_response,
        ) as mock_model_validate_json,
    ):
        result = await google_search._inner_search("test query", TextSearchOptions())

        mock_validate.assert_called_once()
        # ensure the mock_model_validate_json method was called
        mock_model_validate_json.assert_called_once_with("fake_json_text")
        assert result == mock_response


async def test__inner_search_http_status_error_raises_service_invalid_request_error() -> None:
    """Test _inner_search raises ServiceInvalidRequestError if an HTTPStatusError occurs."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")

    with patch.object(google_search, "_validate_options"), patch("httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        # Mock a failing get call that raises HTTPStatusError
        instance.get.side_effect = HTTPStatusError("Error", request=MagicMock(), response=MagicMock())

        with pytest.raises(ServiceInvalidRequestError) as exc:
            await google_search._inner_search("test query", TextSearchOptions())
        assert "Failed to get search results." in str(exc.value)


async def test__inner_search_request_error_raises_service_invalid_request_error() -> None:
    """Test _inner_search raises ServiceInvalidRequestError if a client-side RequestError occurs."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")

    async_client_mock = AsyncMock()
    # Mock a failing get call that raises RequestError
    async_client_mock.get.side_effect = RequestError("Client error")

    with (
        patch.object(google_search, "_validate_options"),
        patch(
            "semantic_kernel.connectors.search.google.google_search.AsyncClient.__aenter__",
            return_value=async_client_mock,
        ),
    ):
        with pytest.raises(ServiceInvalidRequestError) as exc:
            await google_search._inner_search("test query", TextSearchOptions())
        assert "A client error occurred while getting search results." in str(exc.value)


async def test__inner_search_unexpected_error_raises_service_invalid_request_error() -> None:
    """Test _inner_search raises ServiceInvalidRequestError if an unexpected error occurs."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")

    async_client_mock = AsyncMock()
    # Trigger a generic exception
    async_client_mock.get.side_effect = Exception("Unexpected error")

    with (
        patch.object(google_search, "_validate_options"),
        patch(
            "semantic_kernel.connectors.search.google.google_search.AsyncClient.__aenter__",
            return_value=async_client_mock,
        ),
    ):
        with pytest.raises(ServiceInvalidRequestError) as exc:
            await google_search._inner_search("test query", TextSearchOptions())
        assert "An unexpected error occurred while getting search results." in str(exc.value)


async def test__build_query_no_filter() -> None:
    """Test _build_query constructs the expected Google Search URL part with no filter clauses."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    options = TextSearchOptions(top=5, skip=2)
    query_str = google_search._build_query("hello world", options)
    # We expect it to produce something like ?q=hello+world&key=fake_api_key&cx=fake_engine_id&num=5&start=2
    assert "hello+world" in query_str
    assert "key=fake_api_key" in query_str
    assert "cx=fake_engine_id" in query_str
    assert "num=5" in query_str
    assert "start=2" in query_str


async def test__build_query_equal_to_filter() -> None:
    """Test _build_query includes EqualTo filter parameters if matching the known query parameters."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    options = TextSearchOptions(top=3, skip=0)
    options.filter = TextSearchFilter.equal_to(field_name="lr", value="lang_en")

    query_str = google_search._build_query("test", options)
    assert "lr=lang_en" in query_str


@pytest.mark.asyncio
async def test__build_query_any_tags_equal_to_unsupported_filter() -> None:
    """Test _build_query logs debug message when AnyTagsEqualTo filter is present but doesn't break query."""
    from semantic_kernel.data.filter_clauses.any_tags_equal_to_filter_clause import AnyTagsEqualTo

    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    options = TextSearchOptions(top=3, skip=0)
    options.filter.filters.append(AnyTagsEqualTo(field_name="tags", value="some_tag"))

    query_str = google_search._build_query("test", options)
    assert "q=test" in query_str
    assert "cx=fake_engine_id" in query_str


async def test__get_result_strings_no_items() -> None:
    """Test _get_result_strings yields nothing if response contains no items."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    response = GoogleSearchResponse(items=None)
    results = [r async for r in google_search._get_result_strings(response)]
    assert results == []


async def test__get_result_strings_with_items() -> None:
    """Test _get_result_strings yields the snippet of each item."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    item1 = GoogleSearchResult(snippet="snippet1")
    item2 = GoogleSearchResult(snippet="snippet2")
    response = GoogleSearchResponse(items=[item1, item2])

    results = [r async for r in google_search._get_result_strings(response)]
    assert results == ["snippet1", "snippet2"]


async def test__get_text_search_results_no_items() -> None:
    """Test _get_text_search_results yields nothing if response contains no items."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    response = GoogleSearchResponse(items=None)
    results = [r async for r in google_search._get_text_search_results(response)]
    assert results == []


async def test__get_text_search_results_with_items() -> None:
    """Test _get_text_search_results yields TextSearchResult objects for each item."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    item = GoogleSearchResult(title="test title", snippet="test snippet", link="test")
    response = GoogleSearchResponse(items=[item])

    results = [r async for r in google_search._get_text_search_results(response)]
    assert len(results) == 1
    assert isinstance(results[0], TextSearchResult)
    assert results[0].name == "test title"
    assert results[0].value == "test snippet"
    assert results[0].link == "test"


async def test__get_google_search_results_no_items() -> None:
    """Test _get_google_search_results yields nothing if response contains no items."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    response = GoogleSearchResponse(items=None)
    results = [r async for r in google_search._get_google_search_results(response)]
    assert results == []


async def test__get_google_search_results_with_items() -> None:
    """Test _get_google_search_results yields each GoogleSearchResult in the response items."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    item1 = GoogleSearchResult()
    item2 = GoogleSearchResult()
    response = GoogleSearchResponse(items=[item1, item2])

    results = [r async for r in google_search._get_google_search_results(response)]
    assert len(results) == 2
    assert results[0] is item1
    assert results[1] is item2


async def test__get_total_count_included() -> None:
    """Test _get_total_count returns total if include_total_count is True."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    response = GoogleSearchResponse()
    response.search_information = MagicMock(spec=GoogleSearchInformation)
    response.search_information.total_results = 42

    options = TextSearchOptions()
    options.include_total_count = True

    total = google_search._get_total_count(response, options)
    assert total == 42


async def test__get_total_count_excluded() -> None:
    """Test _get_total_count returns None if include_total_count is False."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    response = GoogleSearchResponse()
    response.search_information = MagicMock(spec=GoogleSearchInformation)
    response.search_information.total_results = 42

    options = TextSearchOptions()
    options.include_total_count = False

    total = google_search._get_total_count(response, options)
    assert total is None


async def test__get_metadata_includes_search_time() -> None:
    """Test _get_metadata includes search_time if present."""
    google_search = GoogleSearch(api_key="fake_api_key", search_engine_id="fake_engine_id")
    response = GoogleSearchResponse()
    response.search_information = MagicMock(spec=GoogleSearchInformation)
    response.search_information.search_time = 1.234

    metadata = google_search._get_metadata(response)
    assert metadata["search_time"] == 1.234
