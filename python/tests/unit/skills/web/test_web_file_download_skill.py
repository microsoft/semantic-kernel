# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest
import tempfile
import aiofiles
import os

from semantic_kernel import Kernel
from semantic_kernel.skills.web import WebFileDownloadSkill
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext


@pytest.mark.asyncio
async def test_it_can_be_instantiated():
    skill = WebFileDownloadSkill()
    assert skill is not None


@pytest.mark.asyncio
async def test_it_can_be_imported():
    kernel = Kernel()
    skill = WebFileDownloadSkill()
    assert kernel.import_skill(skill, "web")
    assert kernel.skills.has_native_function(
        "web", "downloadToFile")


@patch("aiohttp.ClientSession.get")
@pytest.mark.asyncio
async def test_download_to_file(mock_get):
    mock_get.return_value.__aenter__.return_value.read.return_value = b"Hello"
    mock_get.return_value.__aenter__.return_value.status = 200
    fp = None
    try:
        with tempfile.NamedTemporaryFile("rb", delete=False) as fp:
            skill = WebFileDownloadSkill()
            context_variables = ContextVariables()
            context_variables.set("filePath", fp.name)
            context = SKContext(context_variables, None, None, None) # type: ignore

            await skill.download_to_file("https://example.org/post", context)

            assert fp.read() == b"Hello"
    finally:
        if fp is not None:
            os.remove(fp.name)


@patch("aiohttp.ClientSession.get")
@pytest.mark.asyncio
async def test_invalid_path(mock_get):
    mock_get.return_value.__aenter__.return_value.read.return_value = b"Hello"
    mock_get.return_value.__aenter__.return_value.status = 200

    skill = WebFileDownloadSkill()
    context_variables = ContextVariables()
    context_variables.set("filePath", "")
    context = SKContext(context_variables, None, None, None) # type: ignore

    with pytest.raises(ValueError):
        await skill.download_to_file("https://example.org/post", context)
