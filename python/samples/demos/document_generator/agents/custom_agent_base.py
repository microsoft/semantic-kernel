# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC
from collections.abc import AsyncIterable
from typing import Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.functions import KernelArguments
from semantic_kernel.kernel import Kernel


class CustomAgentBase(ChatCompletionAgent, ABC):
    SERVICE_ID: ClassVar[str] = "chat_completion"

    def _create_kernel(self) -> Kernel:
        kernel = Kernel()
        kernel.add_service(OpenAIChatCompletion(service_id=self.SERVICE_ID))

        return kernel

    @override
    async def invoke(
        self,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        # Since the history contains internal messages from other agents,
        # we will do our best to filter out those. Unfortunately, there will
        # be a side effect of losing the context of the conversation internal
        # to the agent when the conversation is handed back to the agent, i.e.
        # previous function call results.
        filtered_chat_history = ChatHistory()
        for message in history:
            content = message.content
            # We don't want to add messages whose text content is empty.
            # Those messages are likely messages from function calls and function results.
            if content:
                filtered_chat_history.add_message(message)

        async for response in super().invoke(filtered_chat_history, arguments=arguments, kernel=kernel, **kwargs):
            yield response
