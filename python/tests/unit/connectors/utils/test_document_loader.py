# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, HTTPStatusError, RequestError

from semantic_kernel.connectors.utils.document_loader import DocumentLoader
from semantic_kernel.exceptions import ServiceInvalidRequestError
from semantic_kernel.utils.telemetry.user_agent import HTTP_USER_AGENT


@pytest.fixture
def http_client():
    return AsyncClient()


@pytest.mark.parametrize(
    ("user_agent", "expected_user_agent"),
    [(None, HTTP_USER_AGENT), (HTTP_USER_AGENT, HTTP_USER_AGENT), ("Custom-Agent", "Custom-Agent")],
)
async def test_from_uri_success(http_client, user_agent, expected_user_agent):
    url = "https://example.com/document"
    response_text = "Document content"

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = response_text
    mock_response.raise_for_status = AsyncMock()

    http_client.get = AsyncMock(return_value=mock_response)

    result = await DocumentLoader.from_uri(url, http_client, None, user_agent)
    assert result == response_text
    http_client.get.assert_awaited_once_with(url, headers={"User-Agent": expected_user_agent})


async def test_from_uri_default_user_agent(http_client):
    url = "https://example.com/document"
    response_text = "Document content"

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = response_text
    mock_response.raise_for_status = AsyncMock()

    http_client.get = AsyncMock(return_value=mock_response)

    result = await DocumentLoader.from_uri(url, http_client, None)
    assert result == response_text
    http_client.get.assert_awaited_once_with(url, headers={"User-Agent": HTTP_USER_AGENT})


async def test_from_uri_with_auth_callback(http_client):
    url = "https://example.com/document"
    response_text = "Document content"

    async def auth_callback(client, url):
        return {"Authorization": "Bearer token"}

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = response_text
    mock_response.raise_for_status = AsyncMock()

    http_client.get = AsyncMock(return_value=mock_response)

    result = await DocumentLoader.from_uri(url, http_client, auth_callback)
    assert result == response_text
    http_client.get.assert_awaited_once_with(url, headers={"User-Agent": HTTP_USER_AGENT})


async def test_from_uri_request_error(http_client):
    url = "https://example.com/document"

    http_client.get = AsyncMock(side_effect=RequestError("error", request=None))

    with pytest.raises(ServiceInvalidRequestError):
        await DocumentLoader.from_uri(url, http_client, None)
    http_client.get.assert_awaited_once_with(url, headers={"User-Agent": HTTP_USER_AGENT})


@patch("httpx.AsyncClient.get")
async def test_from_uri_http_status_error(mock_get, http_client):
    url = "https://example.com/document"

    mock_get.side_effect = HTTPStatusError("error", request=AsyncMock(), response=AsyncMock(status_code=500))

    with pytest.raises(ServiceInvalidRequestError, match="Failed to get document."):
        await DocumentLoader.from_uri(url, http_client, None)
    mock_get.assert_awaited_once_with(url, headers={"User-Agent": HTTP_USER_AGENT})


@patch("httpx.AsyncClient.get")
async def test_from_uri_general_exception(mock_get, http_client):
    url = "https://example.com/document"

    mock_get.side_effect = Exception("Unexpected error")

    with pytest.raises(ServiceInvalidRequestError, match="An unexpected error occurred while getting the document."):
        await DocumentLoader.from_uri(url, http_client, None)
    mock_get.assert_awaited_once_with(url, headers={"User-Agent": HTTP_USER_AGENT})
