# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import Field

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import AuthorRole, ChatMessageContent, StreamingChatMessageContent
from semantic_kernel.functions import KernelArguments


class RecordingCompletion(ChatCompletionClientBase):
    choices: list[str] = Field(default_factory=list)

    async def _inner_get_chat_message_contents(self, chat_history, settings):
        self.choices.append(settings.function_choice_behavior.type_.value)
        return [ChatMessageContent(role=AuthorRole.ASSISTANT, content="done")]

    async def _inner_get_streaming_chat_message_contents(self, chat_history, settings, function_invoke_attempt=0):
        self.choices.append(settings.function_choice_behavior.type_.value)
        yield [StreamingChatMessageContent(role=AuthorRole.ASSISTANT, choice_index=0, content="done")]


@pytest.mark.parametrize("invoke", ["get_response", "invoke", "invoke_stream"])
@pytest.mark.parametrize("explicit", [False, True])
async def test_agent_default_function_choice_does_not_modify_shared_settings(invoke, explicit):
    service = RecordingCompletion(service_id="model", ai_model_id="test-model")
    configured = FunctionChoiceBehavior.Required(auto_invoke=False) if explicit else None
    settings = PromptExecutionSettings(service_id="model", function_choice_behavior=configured)
    for behavior in [FunctionChoiceBehavior.Auto(), FunctionChoiceBehavior.NoneInvoke()]:
        agent = ChatCompletionAgent(
            name="Worker",
            service=service,
            arguments=KernelArguments(settings=settings),
            function_choice_behavior=behavior,
        )
        if invoke == "get_response":
            assert (await agent.get_response("hello")).message.content == "done"
        else:
            assert [item async for item in getattr(agent, invoke)("hello")]

    assert service.choices == (["required", "required"] if explicit else ["auto", "none"])
    assert settings.function_choice_behavior is configured
