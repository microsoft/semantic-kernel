# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from azure.identity import DefaultAzureCredential
from opentelemetry import trace

from samples.demos.document_generator.custom_chat_completion_client import CustomChatCompletionsClient
from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_chat_completion import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.agents import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


@experimental_class
class CustomSelectionStrategy(SelectionStrategy):
    """A selection strategy that selects the next agent intelligently."""

    chat_completion_service: AzureAIInferenceChatCompletion

    def __init__(self, **kwargs):
        azure_openai_settings = AzureOpenAISettings.create()
        endpoint = azure_openai_settings.endpoint
        deployment_name = azure_openai_settings.chat_deployment_name

        chat_completion_service = AzureAIInferenceChatCompletion(
            ai_model_id=deployment_name,
            client=CustomChatCompletionsClient(
                endpoint=f"{str(endpoint).strip('/')}/openai/deployments/{deployment_name}",
                credential=DefaultAzureCredential(),
                credential_scopes=["https://cognitiveservices.azure.com/.default"],
            ),
        )

        super().__init__(chat_completion_service=chat_completion_service, **kwargs)

    async def next(self, agents: list["Agent"], history: list["ChatMessageContent"]) -> "Agent":
        """Select the next agent to interact with.

        Args:
            agents: The list of agents to select from.
            history: The history of messages in the conversation.

        Returns:
            The next agent to interact with.
        """
        if len(agents) == 0:
            raise ValueError("No agents to select from")

        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("selection_strategy"):
            chat_history = ChatHistory(system_message=self.get_system_message(agents))

            for message in history:
                content = message.content
                if content:
                    chat_history.add_message(message)

            completion = await self.chat_completion_service.get_chat_message_content(
                chat_history,
                AzureAIInferenceChatPromptExecutionSettings(),
            )

            return agents[int(completion.content)]

    def get_system_message(self, agents: list["Agent"]) -> str:
        return f"""
You will be given a chat history where there will be one user, one writer, and {len(agents) - 1} reviewers.
The writer is responsible for creating content.
The reviewers are responsible for providing feedback and approving the content.
The chat history may be empty at the beginning.

Following are the indices, names and descriptions of the participants in fullfilling the user's request:
{"\n".join(f"[{index}] {agent.name}:\n{agent.description}" for index, agent in enumerate(agents))}

Pick the most appropriate participant to interact with based on the conversation history by its index.
No participant should be picked consecutively.

You response should be a number between 0 and {len(agents) - 1}.
Only return the index of the participant and nothing else. Your response should be parsaable as an integer.
"""
