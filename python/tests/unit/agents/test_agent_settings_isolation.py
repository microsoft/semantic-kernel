# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import Field

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import KernelArguments


class RecordingCompletion(ChatCompletionClientBase):
    requests: list[dict] = Field(default_factory=list)

    async def _inner_get_chat_message_contents(self, chat_history, settings):
        self.requests.append(dict(settings.extension_data))
        return [ChatMessageContent(role=AuthorRole.ASSISTANT, content="done")]


@pytest.mark.parametrize("invoke", ["get_response", "invoke"])
@pytest.mark.parametrize("override", [False, True])
async def test_agent_call_settings_do_not_replace_defaults(invoke, override):
    service = RecordingCompletion(service_id="model", ai_model_id="test-model")
    default = PromptExecutionSettings(service_id="model", extension_data={"temperature": 0.1})
    requested = PromptExecutionSettings(service_id="model", extension_data={"temperature": 0.9})
    defaults = KernelArguments(settings=default, context="base")
    arguments = KernelArguments(settings=requested if override else None, context="request")
    agent = ChatCompletionAgent(name="Worker", service=service, arguments=defaults)

    if invoke == "get_response":
        await agent.get_response("first", arguments=arguments)
        await agent.get_response("second")
    else:
        assert [item async for item in agent.invoke("first", arguments=arguments)]
        assert [item async for item in agent.invoke("second")]

    assert service.requests == [
        {"temperature": 0.9 if override else 0.1},
        {"temperature": 0.1},
    ]
    assert defaults.execution_settings == {"model": default}
    assert defaults == {"context": "base"}
    assert arguments.execution_settings == ({"model": requested} if override else None)
    assert arguments == {"context": "request"}
