# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.http_plugin import HttpPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments


@pytest.mark.asyncio
async def test_it_can_be_instantiated():
    plugin = HttpPlugin()
    assert plugin is not None


@pytest.mark.asyncio
async def test_it_can_be_imported():
    kernel = Kernel()
    plugin = HttpPlugin()
    assert kernel.import_plugin(plugin, "http")
    assert kernel.plugins["http"] is not None
    assert kernel.plugins["http"].name == "http"
    assert kernel.plugins["http"]["getAsync"] is not None
    assert kernel.plugins["http"]["postAsync"] is not None


@patch("aiohttp.ClientSession.get")
@pytest.mark.asyncio
async def test_get(mock_get):
    mock_get.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_get.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    response = await plugin.get("https://example.org/get")
    assert response == "Hello"


@pytest.mark.asyncio
async def test_get_none_url():
    plugin = HttpPlugin()
    with pytest.raises(ValueError):
        await plugin.get(None)


@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_post(mock_post):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/post", body="{message: 'Hello, world!'}")
    response = await plugin.post(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_post_nobody(mock_post):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/post")
    response = await plugin.post(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
@pytest.mark.asyncio
async def test_put(mock_put):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/put", body="{message: 'Hello, world!'}")
    response = await plugin.put(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
@pytest.mark.asyncio
async def test_put_nobody(mock_put):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/put")
    response = await plugin.put(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.delete")
@pytest.mark.asyncio
async def test_delete(mock_delete):
    mock_delete.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_delete.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/delete")
    response = await plugin.delete(**arguments)
    assert response == "Hello World !"
