# Copyright (c) Microsoft. All rights reserved.

import json
import sys
from typing import ClassVar

from pydantic import model_validator

from semantic_kernel.agents.orchestration.group_chat import BooleanResult, GroupChatManager, MessageResult, StringResult
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class CustomGroupChatManager(GroupChatManager):
    """Custom group chat manager to enable user input and dynamic strategies."""

    chat_completion_service: ChatCompletionClientBase

    REQUEST_USER_INPUT_INSTRUCTION: ClassVar[str] = (
        "You are a group manager that coordinates multiple autonomous agents. "
        "Request user input when needed if failures occurs repeatedly or user confirmation is required."
    )
    TERMINATION_KEYWORD: ClassVar[str] = "terminate"
    SELECT_NEXT_AGENT_INSTRUCTION: ClassVar[str] = (
        "You are a group manager that coordinates multiple autonomous agents. "
        "After each agent message, you will select the next agent by the agent name to respond."
    )

    @classmethod
    @model_validator(mode="after")
    def validate_chat_completion_service(cls, instance: "CustomGroupChatManager") -> "CustomGroupChatManager":
        """Validate that the chat completion service is set."""
        prompt_execution_settings_class = instance.chat_completion_service.get_prompt_execution_settings_class()

        if "response_format" not in prompt_execution_settings_class.model_fields:
            raise ValueError("The chat completion service must support strctured output.")

        return instance

    @override
    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        """Override the default behavior to request user input after the reviewer's message.

        The manager will check if input from human is needed after each agent message.
        """
        if len(chat_history) == 0:
            return BooleanResult(result=False, reason="Chat history is empty.")

        if chat_history.messages[-1].role == AuthorRole.USER:
            return BooleanResult(result=False, reason="Last message is from the user, no need to request input.")

        messages = [ChatMessageContent(role=AuthorRole.SYSTEM, content=self.REQUEST_USER_INPUT_INSTRUCTION)]
        messages.extend(chat_history.messages)
        messages.append(ChatMessageContent(role=AuthorRole.USER, content="Do you need input from a human? "))

        prompt_execution_settings = self.chat_completion_service.instantiate_prompt_execution_settings()
        prompt_execution_settings.response_format = BooleanResult

        response = await self.chat_completion_service.get_chat_message_content(
            chat_history=ChatHistory(messages=messages),
            settings=prompt_execution_settings,
        )

        print(f"Response from should_request_user_input: {response.content}")

        return BooleanResult.model_validate(json.loads(response.content))

    @override
    async def should_terminate(self, chat_history) -> BooleanResult:
        """Override the default behavior to check if the chat should be terminated.

        The chat will not be terminated unless the user explicitly requests it.
        """
        # Call the base class method to check for termination conditions
        boolean_result = await super().should_terminate(chat_history)
        if boolean_result.result:
            return boolean_result

        last_message = chat_history.messages[-1]
        if last_message.role == AuthorRole.USER and self.TERMINATION_KEYWORD in last_message.content.lower():
            return BooleanResult(result=True, reason="Termination request found in the last message.")

        return BooleanResult(result=False, reason="No termination request found.")

    @override
    async def select_next_agent(
        self,
        chat_history: ChatHistory,
        participant_descriptions: dict[str, str],
    ) -> StringResult:
        """Override the default behavior to select the next agent based on the chat history.

        The manager will select the next agent based on the chat history and participant descriptions.
        """
        messages = [ChatMessageContent(role=AuthorRole.SYSTEM, content=self.SELECT_NEXT_AGENT_INSTRUCTION)]
        messages.extend(chat_history.messages)
        participant_list = "\n".join(f"{name}: {description}" for name, description in participant_descriptions.items())
        messages.append(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=f"Who should respond next?\n{participant_list}\nPlease provide the agent name as the response.",
            )
        )

        prompt_execution_settings = self.chat_completion_service.instantiate_prompt_execution_settings()
        prompt_execution_settings.response_format = StringResult

        response = await self.chat_completion_service.get_chat_message_content(
            chat_history=ChatHistory(messages=messages),
            settings=prompt_execution_settings,
        )

        print(f"Response from select_next_agent: {response.content}")

        return StringResult.model_validate(json.loads(response.content))

    @override
    async def filter_results(self, chat_history) -> MessageResult:
        """Override the default behavior to filter results based on the chat history.

        The result is not important in this case since there is a front end that displays the interactions.
        """
        return MessageResult(
            result=f"Number of rounds: {self.current_round}",
            reason="Return the number of rounds as the result of the filtering process.",
        )
