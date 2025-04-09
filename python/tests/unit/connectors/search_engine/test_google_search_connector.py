# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from httpx import HTTPStatusError, Request, RequestError, Response

from semantic_kernel.connectors.search_engine.google_connector import GoogleConnector
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError


@pytest.fixture
def google_connector(google_search_unit_test_env):
    return GoogleConnector()


@pytest.mark.parametrize(
    "status_code, response_data, expected_result",
    [
        (200, {"items": [{"snippet": "test snippet"}]}, ["test snippet"]),
        (201, {"items": [{"snippet": "test snippet"}]}, ["test snippet"]),
        (202, {"items": [{"snippet": "test snippet"}]}, ["test snippet"]),
        (204, {}, []),
        (200, {}, []),
    ],
)
@patch("httpx.AsyncClient.get")
async def test_search_success(mock_get, google_connector, status_code, response_data, expected_result):
    query = "test query"
    num_results = 1
    offset = 0

    mock_request = Request(method="GET", url="https://www.googleapis.com/customsearch/v1")

    mock_response = Response(
        status_code=status_code,
        json=response_data,
        request=mock_request,
    )

    mock_get.return_value = mock_response

    results = await google_connector.search(query, num_results, offset)
    assert results == expected_result
    mock_get.assert_awaited_once()


@pytest.mark.parametrize("exclude_list", [["GOOGLE_SEARCH_API_KEY"]], indirect=True)
def test_google_search_connector_init_with_empty_api_key(google_search_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        GoogleConnector(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["GOOGLE_SEARCH_ENGINE_ID"]], indirect=True)
def test_google_search_connector_init_with_empty_search_id(google_search_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        GoogleConnector(
            env_file_path="test.env",
        )


@patch("httpx.AsyncClient.get")
async def test_search_http_status_error(mock_get, google_connector):
    query = "test query"
    num_results = 1
    offset = 0

    mock_get.side_effect = HTTPStatusError("error", request=AsyncMock(), response=AsyncMock(status_code=500))

    with pytest.raises(ServiceInvalidRequestError, match="Failed to get search results."):
        await google_connector.search(query, num_results, offset)
    mock_get.assert_awaited_once()


@patch("httpx.AsyncClient.get")
async def test_search_request_error(mock_get, google_connector):
    query = "test query"
    num_results = 1
    offset = 0

    mock_get.side_effect = RequestError("error", request=AsyncMock())

    with pytest.raises(ServiceInvalidRequestError, match="A client error occurred while getting search results."):
        await google_connector.search(query, num_results, offset)
    mock_get.assert_awaited_once()


@patch("httpx.AsyncClient.get")
async def test_search_general_exception(mock_get, google_connector):
    query = "test query"
    num_results = 1
    offset = 0

    mock_get.side_effect = Exception("Unexpected error")

    with pytest.raises(ServiceInvalidRequestError, match="An unexpected error occurred while getting search results."):
        await google_connector.search(query, num_results, offset)
    mock_get.assert_awaited_once()


async def test_search_invalid_query(google_connector):
    with pytest.raises(ServiceInvalidRequestError, match="query cannot be 'None' or empty."):
        await google_connector.search(query="")


async def test_search_num_results_less_than_or_equal_to_zero(google_connector):
    with pytest.raises(ServiceInvalidRequestError, match="num_results value must be greater than 0."):
        await google_connector.search(query="test query", num_results=0)

    with pytest.raises(ServiceInvalidRequestError, match="num_results value must be greater than 0."):
        await google_connector.search(query="test query", num_results=-1)


async def test_search_num_results_greater_than_ten(google_connector):
    with pytest.raises(ServiceInvalidRequestError, match="num_results value must be less than or equal to 10."):
        await google_connector.search(query="test query", num_results=11)


async def test_search_offset_less_than_zero(google_connector):
    with pytest.raises(ServiceInvalidRequestError, match="offset must be greater than 0."):
        await google_connector.search(query="test query", offset=-1)
