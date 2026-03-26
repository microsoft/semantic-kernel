# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.web_scraper_plugin import WebScraperPlugin
from semantic_kernel.exceptions import FunctionExecutionException


async def test_it_can_be_instantiated():
    plugin = WebScraperPlugin()
    assert plugin is not None
    assert plugin.base_url == "http://localhost:3000"
    assert plugin.api_key is None
    assert plugin.max_markdown_preview == 500


async def test_it_can_be_instantiated_with_config():
    plugin = WebScraperPlugin(
        base_url="http://crw.example.com:4000",
        api_key="fc-test-key",
        max_markdown_preview=1000,
    )
    assert plugin.base_url == "http://crw.example.com:4000"
    assert plugin.api_key == "fc-test-key"
    assert plugin.max_markdown_preview == 1000


async def test_it_can_be_imported():
    kernel = Kernel()
    plugin = WebScraperPlugin()
    kernel.add_plugin(plugin, "WebScraper")
    assert kernel.get_plugin(plugin_name="WebScraper") is not None
    assert kernel.get_function(plugin_name="WebScraper", function_name="scrape_url") is not None
    assert kernel.get_function(plugin_name="WebScraper", function_name="crawl_website") is not None
    assert kernel.get_function(plugin_name="WebScraper", function_name="check_crawl_status") is not None
    assert kernel.get_function(plugin_name="WebScraper", function_name="map_site") is not None


async def test_headers_without_api_key():
    plugin = WebScraperPlugin()
    headers = plugin._headers()
    assert headers == {"Content-Type": "application/json"}
    assert "Authorization" not in headers


async def test_headers_with_api_key():
    plugin = WebScraperPlugin(api_key="fc-secret")
    headers = plugin._headers()
    assert headers["Authorization"] == "Bearer fc-secret"


def _mock_response(json_data, status=200):
    """Create a mock aiohttp response."""
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data)
    return mock_resp


def _mock_non_json_response(status=502, text="<html>Bad Gateway</html>"):
    """Create a mock aiohttp response that raises on .json()."""
    import aiohttp

    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(side_effect=aiohttp.ContentTypeError(
        MagicMock(), MagicMock(), message="Attempt to decode JSON with unexpected mimetype"
    ))
    mock_resp.text = AsyncMock(return_value=text)
    return mock_resp


def _setup_mock_session(mock_session_cls, mock_resp, method="post"):
    """Configure a mock ClientSession with the given response and HTTP method."""
    mock_session = MagicMock()
    mock_method = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_resp),
            __aexit__=AsyncMock(return_value=False),
        )
    )
    setattr(mock_session, method, mock_method)
    mock_session.close = AsyncMock()
    mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_session


@patch("aiohttp.ClientSession")
async def test_scrape_url(mock_session_cls):
    response_data = {
        "success": True,
        "data": {
            "markdown": "# Example\n\nHello world",
            "metadata": {"title": "Example", "sourceURL": "https://example.com"},
        },
    }
    mock_resp = _mock_response(response_data)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    result = await plugin.scrape_url("https://example.com")
    assert result == "# Example\n\nHello world"


@patch("aiohttp.ClientSession")
async def test_scrape_url_returns_html(mock_session_cls):
    response_data = {
        "success": True,
        "data": {"html": "<h1>Example</h1>"},
    }
    mock_resp = _mock_response(response_data)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    result = await plugin.scrape_url("https://example.com", formats="html")
    assert result == "<h1>Example</h1>"


@patch("aiohttp.ClientSession")
async def test_scrape_url_returns_plain_text(mock_session_cls):
    response_data = {
        "success": True,
        "data": {"plainText": "Hello world"},
    }
    mock_resp = _mock_response(response_data)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    result = await plugin.scrape_url("https://example.com", formats="plainText")
    assert result == "Hello world"


@patch("aiohttp.ClientSession")
async def test_scrape_url_returns_links(mock_session_cls):
    response_data = {
        "success": True,
        "data": {"links": ["https://example.com/a", "https://example.com/b"]},
    }
    mock_resp = _mock_response(response_data)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    result = await plugin.scrape_url("https://example.com", formats="links")
    assert json.loads(result) == ["https://example.com/a", "https://example.com/b"]


async def test_scrape_url_empty_url():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.scrape_url("")


async def test_scrape_url_invalid_scheme():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException, match="http or https scheme"):
        await plugin.scrape_url("ftp://example.com")


async def test_crawl_website_empty_url():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.crawl_website("")


async def test_check_crawl_status_empty_id():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.check_crawl_status("")


async def test_map_site_empty_url():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.map_site("")


@patch("aiohttp.ClientSession")
async def test_crawl_website(mock_session_cls):
    response_data = {"success": True, "id": "abc-123"}
    mock_resp = _mock_response(response_data)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    result = await plugin.crawl_website("https://example.com", max_depth=3, max_pages=5)
    assert result == "abc-123"


@patch("aiohttp.ClientSession")
async def test_crawl_website_missing_id(mock_session_cls):
    response_data = {"success": True}
    mock_resp = _mock_response(response_data)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException, match="did not return a crawl job ID"):
        await plugin.crawl_website("https://example.com")


@patch("aiohttp.ClientSession")
async def test_check_crawl_status(mock_session_cls):
    response_data = {
        "status": "completed",
        "total": 1,
        "completed": 1,
        "data": [
            {
                "markdown": "# Example",
                "metadata": {"title": "Example", "sourceURL": "https://example.com"},
            }
        ],
    }
    mock_resp = _mock_response(response_data)
    _setup_mock_session(mock_session_cls, mock_resp, "get")

    plugin = WebScraperPlugin()
    result = await plugin.check_crawl_status("abc-123")
    parsed = json.loads(result)
    assert parsed["status"] == "completed"
    assert parsed["total"] == 1
    assert len(parsed["pages"]) == 1


@patch("aiohttp.ClientSession")
async def test_check_crawl_status_error_response(mock_session_cls):
    mock_resp = _mock_response({"error": "not_found"}, status=404)
    _setup_mock_session(mock_session_cls, mock_resp, "get")

    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException, match="CRW request failed"):
        await plugin.check_crawl_status("nonexistent-id")


@patch("aiohttp.ClientSession")
async def test_check_crawl_status_500_error(mock_session_cls):
    mock_resp = _mock_response({"error": "internal_error"}, status=500)
    _setup_mock_session(mock_session_cls, mock_resp, "get")

    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException, match="CRW request failed"):
        await plugin.check_crawl_status("some-id")


@patch("aiohttp.ClientSession")
async def test_get_non_json_error_response(mock_session_cls):
    mock_resp = _mock_non_json_response(status=502)
    _setup_mock_session(mock_session_cls, mock_resp, "get")

    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException, match="HTTP 502"):
        await plugin.check_crawl_status("some-id")


@patch("aiohttp.ClientSession")
async def test_post_non_json_error_response(mock_session_cls):
    mock_resp = _mock_non_json_response(status=502)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException, match="HTTP 502"):
        await plugin.scrape_url("https://example.com")


@patch("aiohttp.ClientSession")
async def test_map_site(mock_session_cls):
    response_data = {
        "success": True,
        "links": ["https://example.com", "https://example.com/about"],
    }
    mock_resp = _mock_response(response_data)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    result = await plugin.map_site("https://example.com")
    links = json.loads(result)
    assert len(links) == 2
    assert "https://example.com/about" in links


@patch("aiohttp.ClientSession")
async def test_scrape_url_error_response(mock_session_cls):
    response_data = {"success": False, "error": "invalid_url"}
    mock_resp = _mock_response(response_data, status=400)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException, match="CRW request failed"):
        await plugin.scrape_url("https://not-a-url.invalid")


@patch("aiohttp.ClientSession")
async def test_scrape_url_with_formats(mock_session_cls):
    response_data = {
        "success": True,
        "data": {
            "markdown": "# Example",
            "links": ["https://example.com/a"],
        },
    }
    mock_resp = _mock_response(response_data)
    _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    result = await plugin.scrape_url("https://example.com", formats="markdown, links")
    assert result == "# Example"


@patch("aiohttp.ClientSession")
async def test_scrape_url_with_css_selector(mock_session_cls):
    response_data = {
        "success": True,
        "data": {"markdown": "# Selected Content"},
    }
    mock_resp = _mock_response(response_data)
    mock_session = _setup_mock_session(mock_session_cls, mock_resp, "post")

    plugin = WebScraperPlugin()
    result = await plugin.scrape_url("https://example.com", css_selector="article.main")
    assert result == "# Selected Content"

    # Verify css_selector was included in the request body
    call_args = mock_session.post.call_args
    sent_body = json.loads(call_args[1]["data"] if "data" in call_args[1] else call_args.kwargs["data"])
    assert sent_body["cssSelector"] == "article.main"


async def test_scrape_url_unsupported_format():
    plugin = WebScraperPlugin()
    with pytest.raises(FunctionExecutionException, match="Unsupported format"):
        await plugin.scrape_url("https://example.com", formats="markdown, xml")


@patch("aiohttp.ClientSession")
async def test_crawl_id_sanitization(mock_session_cls):
    response_data = {
        "status": "completed",
        "total": 0,
        "completed": 0,
        "data": [],
    }
    mock_resp = _mock_response(response_data)
    mock_session = _setup_mock_session(mock_session_cls, mock_resp, "get")

    plugin = WebScraperPlugin()
    await plugin.check_crawl_status("abc/../etc/passwd")

    # Verify the crawl_id was URL-encoded in the request
    call_args = mock_session.get.call_args
    called_url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
    assert "abc/../etc/passwd" not in called_url
    assert "abc%2F..%2Fetc%2Fpasswd" in called_url
