# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.http_plugin import HttpPlugin
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from semantic_kernel.exceptions import FunctionExecutionException
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
from semantic_kernel.exceptions import FunctionExecutionException
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
from semantic_kernel.exceptions import FunctionExecutionException
=======
>>>>>>> Stashed changes
<<<<<<< main
from semantic_kernel.exceptions import FunctionExecutionException
=======
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
from semantic_kernel.functions.kernel_arguments import KernelArguments


@pytest.mark.asyncio
async def test_it_can_be_instantiated():
    plugin = HttpPlugin()
    assert plugin is not None


@pytest.mark.asyncio
async def test_it_can_be_imported():
    kernel = Kernel()
    plugin = HttpPlugin()
    kernel.add_plugin(plugin, "http")
    assert kernel.get_plugin(plugin_name="http") is not None
    assert kernel.get_plugin(plugin_name="http").name == "http"
    assert kernel.get_function(plugin_name="http", function_name="getAsync") is not None
    assert (
        kernel.get_function(plugin_name="http", function_name="postAsync") is not None
    )


@patch("aiohttp.ClientSession.get")
@pytest.mark.asyncio
async def test_get(mock_get):
    mock_get.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_get.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
    response = await plugin.get("https://example.org/get")
    assert response == "Hello"


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["get", "post", "put", "delete"])
async def test_fail_no_url(method):
    plugin = HttpPlugin()
    with pytest.raises(FunctionExecutionException):
        await getattr(plugin, method)(url="")


@pytest.mark.asyncio
async def test_get_none_url():
    plugin = HttpPlugin()
    with pytest.raises(FunctionExecutionException):
        await plugin.get(None)


@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_post(mock_post):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    plugin = HttpPlugin()
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    arguments = KernelArguments(
        url="https://example.org/post", body="{message: 'Hello, world!'}"
    )
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    arguments = KernelArguments(
        url="https://example.org/post", body="{message: 'Hello, world!'}"
    )
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< main
    arguments = KernelArguments(
        url="https://example.org/post", body="{message: 'Hello, world!'}"
    )
=======
    arguments = KernelArguments(url="https://example.org/post", body="{message: 'Hello, world!'}")
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
    arguments = KernelArguments(
        url="https://example.org/put", body="{message: 'Hello, world!'}"
    )
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    arguments = KernelArguments(
        url="https://example.org/put", body="{message: 'Hello, world!'}"
    )
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
<<<<<<< main
    arguments = KernelArguments(
        url="https://example.org/put", body="{message: 'Hello, world!'}"
    )
=======
    arguments = KernelArguments(url="https://example.org/put", body="{message: 'Hello, world!'}")
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
