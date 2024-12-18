# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC
from collections.abc import AsyncIterable
from typing import ClassVar

from opentelemetry import trace

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.identity import DefaultAzureCredential

from samples.demos.document_generator.custom_chat_completion_client import CustomChatCompletionsClient
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_chat_completion import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.kernel import Kernel


class CustomAgentBase(ChatCompletionAgent, ABC):
    AZURE_AI_INFERENCE_SERVICE_ID: ClassVar[str] = "azure_chat_completion"

    def _create_kernel(self) -> Kernel:
        kernel = Kernel()

        azure_openai_settings = AzureOpenAISettings.create()
        endpoint = azure_openai_settings.endpoint
        deployment_name = azure_openai_settings.chat_deployment_name

        kernel.add_service(
            AzureAIInferenceChatCompletion(
                ai_model_id=deployment_name,
                service_id=self.AZURE_AI_INFERENCE_SERVICE_ID,
                client=CustomChatCompletionsClient(
                    endpoint=f"{str(endpoint).strip('/')}/openai/deployments/{deployment_name}",
                    credential=DefaultAzureCredential(),
                    credential_scopes=["https://cognitiveservices.azure.com/.default"],
                ),
            )
        )

        return kernel

    @override
    async def invoke(self, history: ChatHistory) -> AsyncIterable[ChatMessageContent]:
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(self.name):
            async for response_message in super().invoke(history):
                yield response_message
