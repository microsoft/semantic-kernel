# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

from semantic_kernel.connectors.ai.echo.services.echo_chat_completion import (
    EchoChatCompletion,
)


def test_azure_chat_completion_init() -> None:
    logger = Logger("test_logger")

    # Test successful initialization
    echo_chat_completion = EchoChatCompletion(
        logger=logger,
    )

    assert isinstance(echo_chat_completion, EchoChatCompletion)
