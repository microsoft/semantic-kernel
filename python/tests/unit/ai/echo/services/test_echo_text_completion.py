# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

import pytest

from semantic_kernel.connectors.ai.echo.services.echo_text_completion import (
    EchoTextCompletion,
)


def test_echo_text_completion_init() -> None:
    # Test successful initialization
    logger = Logger("test_logger")

    echo_text_completion = EchoTextCompletion(
        logger=logger,
    )

    assert isinstance(echo_text_completion, EchoTextCompletion)


@pytest.mark.asyncio
async def test_complete_async() -> None:
    echo = EchoTextCompletion()
    resp = await echo.complete_async("hello world", None)
    assert resp == "hello world"
