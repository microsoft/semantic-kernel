# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC
from collections.abc import AsyncIterable
from typing import ClassVar

from opentelemetry import trace

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.kernel import Kernel


class CustomAgentBase(ChatCompletionAgent, ABC):
    AZURE_SERVICE_ID: ClassVar[str] = "azure_chat_completion"

    def _create_kernel(self) -> Kernel:
        kernel = Kernel()
        kernel.add_service(AzureChatCompletion(service_id=self.AZURE_SERVICE_ID))

        return kernel

    @override
    async def invoke(self, history: ChatHistory) -> AsyncIterable[ChatMessageContent]:
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

        tracer = trace.get_tracer(__name__)
        response_messages: list[ChatMessageContent] = []
        with tracer.start_as_current_span(self.name):
            # Cache the messages within the span such that subsequent spans
            # that process the message stream don't become children of this span
            async for response_message in super().invoke(filtered_chat_history):
                response_messages.append(response_message)

        for response_message in response_messages:
            yield response_message
