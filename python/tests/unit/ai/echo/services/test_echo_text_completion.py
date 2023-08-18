# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

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
