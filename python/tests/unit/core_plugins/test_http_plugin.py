# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.http_plugin import HttpPlugin
from semantic_kernel.exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_arguments import KernelArguments


async def test_it_can_be_instantiated():
    plugin = HttpPlugin()
    assert plugin is not None


async def test_it_can_be_imported():
    kernel = Kernel()
    plugin = HttpPlugin()
    kernel.add_plugin(plugin, "http")
    assert kernel.get_plugin(plugin_name="http") is not None
    assert kernel.get_plugin(plugin_name="http").name == "http"
    assert kernel.get_function(plugin_name="http", function_name="getAsync") is not None
    assert kernel.get_function(plugin_name="http", function_name="postAsync") is not None


@patch("aiohttp.ClientSession.get")
async def test_get(mock_get):
    mock_get.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_get.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    response = await plugin.get("https://example.org/get")
    assert response == "Hello"


@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
async def test_fail_no_url(method):
    plugin = HttpPlugin()
    with pytest.raises(FunctionExecutionException):
        await getattr(plugin, method)(url="")


async def test_get_none_url():
    plugin = HttpPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.get(None)


@patch("aiohttp.ClientSession.post")
async def test_post(mock_post):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/post", body="{message: 'Hello, world!'}")
    response = await plugin.post(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.post")
async def test_post_nobody(mock_post):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/post")
    response = await plugin.post(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
async def test_put(mock_put):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/put", body="{message: 'Hello, world!'}")
    response = await plugin.put(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
async def test_put_nobody(mock_put):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/put")
    response = await plugin.put(**arguments)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.delete")
async def test_delete(mock_delete):
    mock_delete.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_delete.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    arguments = KernelArguments(url="https://example.org/delete")
    response = await plugin.delete(**arguments)
    assert response == "Hello World !"
