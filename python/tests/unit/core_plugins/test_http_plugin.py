# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.http_plugin import HttpPlugin
from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_arguments import KernelArguments


async def test_it_can_be_instantiated():
    plugin = HttpPlugin(allow_all_domains=True)
    assert plugin is not None


async def test_it_can_be_instantiated_with_allowed_domains():
    plugin = HttpPlugin(allowed_domains={"example.com", "api.example.com"})
    assert plugin is not None
    assert plugin.allowed_domains == {"example.com", "api.example.com"}


async def test_it_can_be_imported():
    kernel = Kernel()
    plugin = HttpPlugin(allow_all_domains=True)
    kernel.add_plugin(plugin, "http")
    assert kernel.get_plugin(plugin_name="http") is not None
    assert kernel.get_plugin(plugin_name="http").name == "http"
    assert kernel.get_function(plugin_name="http", function_name="getAsync") is not None
    assert kernel.get_function(plugin_name="http", function_name="postAsync") is not None


@patch("aiohttp.ClientSession.get")
async def test_get(mock_get):
    mock_get.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_get.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    response = await plugin.get("https://example.org/get")
    assert response == "Hello"


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
async def test_fail_no_url(method):
    plugin = HttpPlugin(allow_all_domains=True)
    with pytest.raises(FunctionExecutionException):
        await getattr(plugin, method)(url="")


async def test_get_none_url():
    plugin = HttpPlugin(allow_all_domains=True)
    with pytest.raises(FunctionExecutionException):
        await plugin.get(None)


@patch("aiohttp.ClientSession.post")
async def test_post(mock_post):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    arguments = KernelArguments(url="https://example.org/post", body="{message: 'Hello, world!'}")
    response = await plugin.post(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.post")
async def test_post_nobody(mock_post):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    arguments = KernelArguments(url="https://example.org/post")
    response = await plugin.post(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
async def test_put(mock_put):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    arguments = KernelArguments(url="https://example.org/put", body="{message: 'Hello, world!'}")
    response = await plugin.put(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
async def test_put_nobody(mock_put):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    arguments = KernelArguments(url="https://example.org/put")
    response = await plugin.put(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.delete")
async def test_delete(mock_delete):
    mock_delete.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_delete.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    arguments = KernelArguments(url="https://example.org/delete")
    response = await plugin.delete(**arguments)
    assert response == "Hello World !"


# Tests for allowed_domains functionality


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
async def test_throws_for_disallowed_domain(method):
    """Test that all HTTP methods throw an exception when the domain is not in the allowed list."""
    plugin = HttpPlugin(allowed_domains={"example.com"})
    disallowed_url = "https://notexample.com/path"

    with pytest.raises(FunctionExecutionException, match="Sending requests to the provided location is not allowed"):
        if method in ["post", "put"]:
            await getattr(plugin, method)(url=disallowed_url, body={"key": "value"})
        else:
            await getattr(plugin, method)(url=disallowed_url)


@patch("aiohttp.ClientSession.get")
async def test_get_allowed_domain(mock_get):
    """Test that GET request succeeds when the domain is in the allowed list."""
    mock_get.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_get.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allowed_domains={"example.org"})
    response = await plugin.get("https://example.org/get")
    assert response == "Hello"


@patch("aiohttp.ClientSession.post")
async def test_post_allowed_domain(mock_post):
    """Test that POST request succeeds when the domain is in the allowed list."""
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allowed_domains={"example.org"})
    response = await plugin.post("https://example.org/post", body={"key": "value"})
    assert response == "Hello"


@patch("aiohttp.ClientSession.put")
async def test_put_allowed_domain(mock_put):
    """Test that PUT request succeeds when the domain is in the allowed list."""
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allowed_domains={"example.org"})
    response = await plugin.put("https://example.org/put", body={"key": "value"})
    assert response == "Hello"


@patch("aiohttp.ClientSession.delete")
async def test_delete_allowed_domain(mock_delete):
    """Test that DELETE request succeeds when the domain is in the allowed list."""
    mock_delete.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_delete.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allowed_domains={"example.org"})
    response = await plugin.delete("https://example.org/delete")
    assert response == "Hello"


async def test_allowed_domains_case_insensitive():
    """Test that domain matching is case-insensitive."""
    plugin = HttpPlugin(allowed_domains={"EXAMPLE.COM"})
    # Should not raise - case insensitive
    assert plugin._is_uri_allowed("https://example.com/path") is True
    assert plugin._is_uri_allowed("https://EXAMPLE.COM/path") is True
    assert plugin._is_uri_allowed("https://Example.Com/path") is True


async def test_allow_all_domains_allows_all():
    """Test that when allow_all_domains is True, all domains are allowed."""
    plugin = HttpPlugin(allow_all_domains=True)
    assert plugin._is_uri_allowed("https://any-domain.com/path") is True
    assert plugin._is_uri_allowed("https://another-domain.org/path") is True


async def test_allowed_domains_multiple_domains():
    """Test that multiple allowed domains work correctly."""
    plugin = HttpPlugin(allowed_domains={"example.com", "api.example.com", "test.org"})
    assert plugin._is_uri_allowed("https://example.com/path") is True
    assert plugin._is_uri_allowed("https://api.example.com/path") is True
    assert plugin._is_uri_allowed("https://test.org/path") is True
    assert plugin._is_uri_allowed("https://notallowed.com/path") is False


async def test_allowed_domains_with_port():
    """Test that domain matching works with URLs containing ports."""
    plugin = HttpPlugin(allowed_domains={"example.com"})
    # Port is not part of the host/hostname in urlparse
    assert plugin._is_uri_allowed("https://example.com:8080/path") is True


async def test_allowed_domains_subdomain_not_matched():
    """Test that subdomains are not automatically matched."""
    plugin = HttpPlugin(allowed_domains={"example.com"})
    # subdomain should not match unless explicitly allowed
    assert plugin._is_uri_allowed("https://sub.example.com/path") is False


async def test_allowed_domains_exact_subdomain_match():
    """Test that exact subdomain matching works."""
    plugin = HttpPlugin(allowed_domains={"sub.example.com"})
    assert plugin._is_uri_allowed("https://sub.example.com/path") is True
    assert plugin._is_uri_allowed("https://example.com/path") is False
    assert plugin._is_uri_allowed("https://other.example.com/path") is False


# Security regression tests


async def test_default_constructor_denies_all():
    """Test that default HttpPlugin() denies all requests (issue 115285)."""
    plugin = HttpPlugin()
    assert plugin._is_uri_allowed("https://example.com/path") is False
    assert plugin._is_uri_allowed("https://any-domain.com/path") is False


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
async def test_default_constructor_blocks_requests(method):
    """Test that default HttpPlugin() blocks all HTTP methods (issue 115285)."""
    plugin = HttpPlugin()
    with pytest.raises(FunctionExecutionException, match="Sending requests to the provided location is not allowed"):
        if method in ["post", "put"]:
            await getattr(plugin, method)(url="https://example.com/path", body={"key": "value"})
        else:
            await getattr(plugin, method)(url="https://example.com/path")


@patch("aiohttp.ClientSession.get")
async def test_allow_all_domains_flag(mock_get):
    """Test that allow_all_domains=True permits requests to any domain."""
    mock_get.return_value.__aenter__.return_value.text.return_value = "OK"
    mock_get.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    response = await plugin.get("https://any-domain.com/path")
    assert response == "OK"


@patch("aiohttp.ClientSession.get")
async def test_redirects_disabled_with_allowed_domains(mock_get):
    """Test that redirects are disabled when allowed_domains is set (issue 115048)."""
    mock_get.return_value.__aenter__.return_value.text.return_value = "OK"
    mock_get.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allowed_domains={"example.com"})
    await plugin.get("https://example.com/path")

    _, kwargs = mock_get.call_args
    assert kwargs["allow_redirects"] is False


@patch("aiohttp.ClientSession.post")
async def test_redirects_disabled_for_post_with_allowed_domains(mock_post):
    """Test that redirects are disabled for POST when allowed_domains is set."""
    mock_post.return_value.__aenter__.return_value.text.return_value = "OK"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allowed_domains={"example.com"})
    await plugin.post("https://example.com/path", body={"key": "value"})

    _, kwargs = mock_post.call_args
    assert kwargs["allow_redirects"] is False


@patch("aiohttp.ClientSession.put")
async def test_redirects_disabled_for_put_with_allowed_domains(mock_put):
    """Test that redirects are disabled for PUT when allowed_domains is set."""
    mock_put.return_value.__aenter__.return_value.text.return_value = "OK"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allowed_domains={"example.com"})
    await plugin.put("https://example.com/path", body={"key": "value"})

    _, kwargs = mock_put.call_args
    assert kwargs["allow_redirects"] is False


@patch("aiohttp.ClientSession.delete")
async def test_redirects_disabled_for_delete_with_allowed_domains(mock_delete):
    """Test that redirects are disabled for DELETE when allowed_domains is set."""
    mock_delete.return_value.__aenter__.return_value.text.return_value = "OK"
    mock_delete.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allowed_domains={"example.com"})
    await plugin.delete("https://example.com/path")

    _, kwargs = mock_delete.call_args
    assert kwargs["allow_redirects"] is False


@patch("aiohttp.ClientSession.get")
async def test_redirects_allowed_with_allow_all_domains(mock_get):
    """Test that redirects are still allowed when allow_all_domains is True."""
    mock_get.return_value.__aenter__.return_value.text.return_value = "OK"
    mock_get.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    await plugin.get("https://example.com/path")

    _, kwargs = mock_get.call_args
    assert kwargs["allow_redirects"] is True


@patch("aiohttp.ClientSession.post")
async def test_redirects_allowed_for_post_with_allow_all_domains(mock_post):
    """Test that redirects are allowed for POST when allow_all_domains is True."""
    mock_post.return_value.__aenter__.return_value.text.return_value = "OK"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    await plugin.post("https://example.com/path", body={"key": "value"})

    _, kwargs = mock_post.call_args
    assert kwargs["allow_redirects"] is True


@patch("aiohttp.ClientSession.put")
async def test_redirects_allowed_for_put_with_allow_all_domains(mock_put):
    """Test that redirects are allowed for PUT when allow_all_domains is True."""
    mock_put.return_value.__aenter__.return_value.text.return_value = "OK"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    await plugin.put("https://example.com/path", body={"key": "value"})

    _, kwargs = mock_put.call_args
    assert kwargs["allow_redirects"] is True


@patch("aiohttp.ClientSession.delete")
async def test_redirects_allowed_for_delete_with_allow_all_domains(mock_delete):
    """Test that redirects are allowed for DELETE when allow_all_domains is True."""
    mock_delete.return_value.__aenter__.return_value.text.return_value = "OK"
    mock_delete.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin(allow_all_domains=True)
    await plugin.delete("https://example.com/path")

    _, kwargs = mock_delete.call_args
    assert kwargs["allow_redirects"] is True


@pytest.mark.parametrize("scheme", ["file", "ftp", "gopher", "data"])
async def test_disallowed_schemes_blocked(scheme):
    """Test that non-HTTP schemes are blocked."""
    plugin = HttpPlugin(allow_all_domains=True)
    assert plugin._is_uri_allowed(f"{scheme}://example.com/path") is False


@pytest.mark.parametrize("scheme", ["file", "ftp", "gopher"])
@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
async def test_disallowed_schemes_blocked_all_methods(scheme, method):
    """Test that non-HTTP schemes are blocked for all HTTP methods."""
    plugin = HttpPlugin(allow_all_domains=True)
    with pytest.raises(FunctionExecutionException, match="Sending requests to the provided location is not allowed"):
        if method in ["post", "put"]:
            await getattr(plugin, method)(url=f"{scheme}://example.com/path", body={"key": "value"})
        else:
            await getattr(plugin, method)(url=f"{scheme}://example.com/path")


async def test_http_scheme_allowed():
    """Test that both http and https schemes are allowed."""
    plugin = HttpPlugin(allow_all_domains=True)
    assert plugin._is_uri_allowed("http://example.com/path") is True
    assert plugin._is_uri_allowed("https://example.com/path") is True


async def test_empty_hostname_rejected():
    """Test that URLs with empty hostnames are rejected."""
    plugin = HttpPlugin(allow_all_domains=True)
    assert plugin._is_uri_allowed("http://") is False
    assert plugin._is_uri_allowed("https://") is False


async def test_allow_all_domains_with_allowed_domains_allows_redirects():
    """Test that redirects are allowed when both allow_all_domains and allowed_domains are set."""
    plugin = HttpPlugin(allowed_domains={"example.com"}, allow_all_domains=True)
    assert plugin._is_uri_allowed("https://any-domain.com/path") is True
