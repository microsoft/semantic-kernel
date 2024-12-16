# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from azure.ai.inference.aio import ChatCompletionsClient
from azure.identity import DefaultAzureCredential
from opentelemetry import trace

from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_chat_completion import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.contents.chat_history import ChatHistory

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


SYSTEM_MESSAGE = """
You will be given a conversation history where there will be one writer and multiple reviewers.
The writer is responsible for creating content. The reviewers are responsible for providing feedback and
approving the content.

The content is considered approved only when the reviewers agree that the content is ready for publication.
Determine if the content has been approved. If so, say "yes".
"""

TERMINATE_KEYWORD = "yes"


class CustomTerminationStrategy(TerminationStrategy):
    maximum_iterations: int = 10
    chat_completion_service: AzureAIInferenceChatCompletion

    def __init__(self):
        azure_openai_settings = AzureOpenAISettings.create()
        endpoint = azure_openai_settings.endpoint
        deployment_name = azure_openai_settings.chat_deployment_name

        chat_completion_service = AzureAIInferenceChatCompletion(
            ai_model_id=deployment_name,
            client=ChatCompletionsClient(
                endpoint=f"{str(endpoint).strip('/')}/openai/deployments/{deployment_name}",
                credential=DefaultAzureCredential(),
                credential_scopes=["https://cognitiveservices.azure.com/.default"],
            ),
        )

        super().__init__(chat_completion_service=chat_completion_service)

    async def should_agent_terminate(self, agent: "Agent", history: list["ChatMessageContent"]) -> bool:
        """Check if the agent should terminate.

        Args:
            agent: The agent to check.
            history: The history of messages in the conversation.
        """
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("terminate_strategy"):
            chat_history = ChatHistory(system_message=SYSTEM_MESSAGE)

            history_content: list[dict[str, str]] = []
            for message in history:
                history_content.append(message.to_dict())

            chat_history.add_user_message(str(history_content))

            completion = await self.chat_completion_service.get_chat_message_content(
                chat_history,
                AzureAIInferenceChatPromptExecutionSettings(),
            )

            return TERMINATE_KEYWORD in completion.content
