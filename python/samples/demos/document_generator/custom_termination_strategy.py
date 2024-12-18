# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from azure.identity import DefaultAzureCredential
from opentelemetry import trace

from samples.demos.document_generator.custom_chat_completion_client import CustomChatCompletionsClient
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


TERMINATE_KEYWORD = "yes"


class CustomTerminationStrategy(TerminationStrategy):
    maximum_iterations: int = 10
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

    async def should_agent_terminate(self, agent: "Agent", history: list["ChatMessageContent"]) -> bool:
        """Check if the agent should terminate.

        Args:
            agent: The agent to check.
            history: The history of messages in the conversation.
        """
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("terminate_strategy"):
            chat_history = ChatHistory(system_message=self.get_system_message())

            history_content: list[str] = []
            for message in history:
                content = message.content
                if content:
                    if message.name is None:
                        history_content.append(f"{str(message.role)}:\n{content}")
                    else:
                        history_content.append(f"{message.name}:\n{content}")

            chat_history.add_user_message("\n\n".join(history_content))

            completion = await self.chat_completion_service.get_chat_message_content(
                chat_history,
                AzureAIInferenceChatPromptExecutionSettings(),
            )

            return TERMINATE_KEYWORD in completion.content.lower()

    def get_system_message(self) -> str:
        return f"""
You will be given a conversation history where there will be one writer
and {len(self.agents) - 1} reviewers. The writer is responsible for creating
content. The reviewers are responsible for providing feedback and approving
the content.

Following are the names of the participants in fullfilling the user's request:
{"\n".join(agent.name for agent in self.agents)}

The content is considered approved only when the reviewers agree that the
content is ready for publication. The content is not approved when none of
the reviewers have spoken yet. All reviewers must at least have spoken once.

Determine if the content has been approved. If so, say "{TERMINATE_KEYWORD}".
Otherwise, say "no".
"""
