# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from httpx import HTTPStatusError, Request, RequestError, Response

from semantic_kernel.connectors.search_engine.brave_connector import BraveConnector
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidRequestError


@pytest.fixture
def brave_connector(brave_unit_test_env):
    """Set up the fixture to configure the brave connector for these tests."""
    return BraveConnector()


@pytest.mark.parametrize(
    "status_code, response_data, expected_result",
    [
        (200, {"web": {"results": [{"description": "test snippet"}]}}, ["test snippet"]),
        (201, {"web": {"results": [{"description": "test snippet"}]}}, ["test snippet"]),
        (202, {"web": {"results": [{"description": "test snippet"}]}}, ["test snippet"]),
        (204, {}, []),
        (200, {}, []),
    ],
)
@patch("httpx.AsyncClient.get")
async def test_search_success(mock_get, brave_connector, status_code, response_data, expected_result):
    query = "test query"
    num_results = 1
    offset = 0

    mock_request = Request(method="GET", url="https://api.search.brave.com/res/v1/web/search")

    mock_response = Response(
        status_code=status_code,
        json=response_data,
        request=mock_request,
    )

    mock_get.return_value = mock_response

    results = await brave_connector.search(query, num_results, offset)
    assert results == expected_result
    mock_get.assert_awaited_once()


@pytest.mark.parametrize("exclude_list", [["BRAVE_API_KEY"]], indirect=True)
def test_brave_search_connector_init_with_empty_api_key(brave_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        BraveConnector(
            env_file_path="test.env",
        )


@patch("httpx.AsyncClient.get")
async def test_search_http_status_error(mock_get, brave_connector):
    query = "test query"
    num_results = 1
    offset = 0

    mock_get.side_effect = HTTPStatusError("error", request=AsyncMock(), response=AsyncMock(status_code=500))

    with pytest.raises(ServiceInvalidRequestError, match="Failed to get search results."):
        await brave_connector.search(query, num_results, offset)
    mock_get.assert_awaited_once()


@patch("httpx.AsyncClient.get")
async def test_search_request_error(mock_get, brave_connector):
    query = "test query"
    num_results = 1
    offset = 0

    mock_get.side_effect = RequestError("error", request=AsyncMock())

    with pytest.raises(ServiceInvalidRequestError, match="A client error occurred while getting search results."):
        await brave_connector.search(query, num_results, offset)
    mock_get.assert_awaited_once()


@patch("httpx.AsyncClient.get")
async def test_search_general_exception(mock_get, brave_connector):
    query = "test query"
    num_results = 1
    offset = 0

    mock_get.side_effect = Exception("Unexpected error")

    with pytest.raises(ServiceInvalidRequestError, match="An unexpected error occurred while getting search results."):
        await brave_connector.search(query, num_results, offset)
    mock_get.assert_awaited_once()


async def test_search_empty_query(brave_connector):
    with pytest.raises(ServiceInvalidRequestError) as excinfo:
        await brave_connector.search("", 1, 0)
    assert str(excinfo.value) == "query cannot be 'None' or empty."


async def test_search_invalid_num_results(brave_connector):
    with pytest.raises(ServiceInvalidRequestError) as excinfo:
        await brave_connector.search("test", 0, 0)
    assert str(excinfo.value) == "num_results value must be greater than 0."

    with pytest.raises(ServiceInvalidRequestError) as excinfo:
        await brave_connector.search("test", 21, 0)
    assert str(excinfo.value) == "num_results value must be less than or equal to 20."


async def test_search_invalid_offset(brave_connector):
    with pytest.raises(ServiceInvalidRequestError) as excinfo:
        await brave_connector.search("test", 1, -1)
    assert str(excinfo.value) == "offset must be greater than 0."

    with pytest.raises(ServiceInvalidRequestError) as excinfo:
        await brave_connector.search("test", 1, 10)
    assert str(excinfo.value) == "offset must be less than 10."


async def test_search_api_failure(brave_connector):
    query = "test query"
    num_results = 1
    offset = 0

    async def mock_get(*args, **kwargs):
        raise HTTPStatusError("error", request=AsyncMock(), response=AsyncMock(status_code=500))

    with (
        patch("httpx.AsyncClient.get", new=mock_get),
        pytest.raises(ServiceInvalidRequestError, match="Failed to get search results."),
    ):
        await brave_connector.search(query, num_results, offset)
