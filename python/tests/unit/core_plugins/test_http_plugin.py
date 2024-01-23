# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins import HttpPlugin
from semantic_kernel.orchestration.context_variables import ContextVariables


@pytest.mark.asyncio
async def test_it_can_be_instantiated():
    plugin = HttpPlugin()
    assert plugin is not None


@pytest.mark.asyncio
async def test_it_can_be_imported():
    kernel = Kernel()
    plugin = HttpPlugin()
    assert kernel.import_plugin(plugin, "http")
    assert kernel.plugins.has_native_function("http", "getAsync")
    assert kernel.plugins.has_native_function("http", "postAsync")


@patch("aiohttp.ClientSession.get")
@pytest.mark.asyncio
async def test_get(mock_get):
    mock_get.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_get.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    response = await plugin.get_async("https://example.org/get")
    assert response == "Hello"


@pytest.mark.asyncio
async def test_get_none_url():
    plugin = HttpPlugin()
    with pytest.raises(ValueError):
        await plugin.get_async(None)


@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_post(mock_post, context_factory):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    context_variables = ContextVariables()
    context_variables.set("body", "{message: 'Hello, world!'}")
    context = context_factory(context_variables)
    response = await plugin.post_async("https://example.org/post", context)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_post_nobody(mock_post, context_factory):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    context_variables = ContextVariables()
    context = context_factory(context_variables)
    response = await plugin.post_async("https://example.org/post", context)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
@pytest.mark.asyncio
async def test_put(mock_put, context_factory):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    context_variables = ContextVariables()
    context_variables.set("body", "{message: 'Hello, world!'}")
    context = context_factory(context_variables)
    response = await plugin.put_async("https://example.org/put", context)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
@pytest.mark.asyncio
async def test_put_nobody(mock_put, context_factory):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    context_variables = ContextVariables()
    context = context_factory(context_variables)
    response = await plugin.put_async("https://example.org/put", context)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.delete")
@pytest.mark.asyncio
async def test_delete(mock_delete):
    mock_delete.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_delete.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    response = await plugin.delete_async("https://example.org/delete")
    assert response == "Hello World !"
