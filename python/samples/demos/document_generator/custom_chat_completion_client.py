# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib

from azure.ai.inference.aio import ChatCompletionsClient


class CustomChatCompletionsClient(ChatCompletionsClient):
    """Wrapper to make sure the client is closed properly."""

    def __del__(self) -> None:
        """Close the client."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.close())
