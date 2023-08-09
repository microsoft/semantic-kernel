# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_skills import HttpSkill
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext


@pytest.mark.asyncio
async def test_it_can_be_instantiated():
    skill = HttpSkill()
    assert skill is not None


@pytest.mark.asyncio
async def test_it_can_be_imported():
    kernel = Kernel()
    skill = HttpSkill()
    assert kernel.import_skill(skill, "http")
    assert kernel.skills.has_native_function("http", "getAsync")
    assert kernel.skills.has_native_function("http", "postAsync")


@patch("aiohttp.ClientSession.get")
@pytest.mark.asyncio
async def test_get(mock_get):
    mock_get.return_value.__aenter__.return_value.text.return_value = "Hello"
    mock_get.return_value.__aenter__.return_value.status = 200

    skill = HttpSkill()
    response = await skill.get_async("https://example.org/get")
    assert response == "Hello"


@pytest.mark.asyncio
async def test_get_none_url():
    skill = HttpSkill()
    with pytest.raises(ValueError):
        await skill.get_async(None)


@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_post(mock_post, context_factory):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    skill = HttpSkill()
    context_variables = ContextVariables()
    context_variables.set("body", "{message: 'Hello, world!'}")
    context = context_factory(context_variables)
    response = await skill.post_async("https://example.org/post", context)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_post_nobody(mock_post, context_factory):
    mock_post.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_post.return_value.__aenter__.return_value.status = 200

    skill = HttpSkill()
    context_variables = ContextVariables()
    context = context_factory(context_variables)
    response = await skill.post_async("https://example.org/post", context)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
@pytest.mark.asyncio
async def test_put(mock_put, context_factory):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    skill = HttpSkill()
    context_variables = ContextVariables()
    context_variables.set("body", "{message: 'Hello, world!'}")
    context = context_factory(context_variables)
    response = await skill.put_async("https://example.org/put", context)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.put")
@pytest.mark.asyncio
async def test_put_nobody(mock_put, context_factory):
    mock_put.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_put.return_value.__aenter__.return_value.status = 200

    skill = HttpSkill()
    context_variables = ContextVariables()
    context = context_factory(context_variables)
    response = await skill.put_async("https://example.org/put", context)
    assert response == "Hello World !"


@patch("aiohttp.ClientSession.delete")
@pytest.mark.asyncio
async def test_delete(mock_delete):
    mock_delete.return_value.__aenter__.return_value.text.return_value = "Hello World !"
    mock_delete.return_value.__aenter__.return_value.status = 200

    skill = HttpSkill()
    response = await skill.delete_async("https://example.org/delete")
    assert response == "Hello World !"
