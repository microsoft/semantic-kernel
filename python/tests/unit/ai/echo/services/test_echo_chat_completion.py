# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

import pytest

from semantic_kernel.connectors.ai.echo.services.echo_chat_completion import (
    EchoChatCompletion,
)


def test_azure_chat_completion_init() -> None:
    logger = Logger("test_logger")

    echo_chat_completion = EchoChatCompletion(
        logger=logger,
    )

    assert isinstance(echo_chat_completion, EchoChatCompletion)


@pytest.mark.asyncio
async def test_complete_chat_async() -> None:
    echo = EchoChatCompletion()
    resp = await echo.complete_chat_async([("chat", "hello world")], None, None)
    assert resp == ["chat_hello world"]
