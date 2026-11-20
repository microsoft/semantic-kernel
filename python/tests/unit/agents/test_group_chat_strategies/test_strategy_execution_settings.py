# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import Field

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.agents.strategies.selection.kernel_function_selection_strategy import (
    KernelFunctionSelectionStrategy,
)
from semantic_kernel.agents.strategies.termination.kernel_function_termination_strategy import (
    KernelFunctionTerminationStrategy,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import KernelArguments, KernelFunction, kernel_function
from semantic_kernel.prompt_template import PromptTemplateConfig


@pytest.mark.parametrize("kind", ["selection", "termination"])
@pytest.mark.parametrize("configured", [False, True])
async def test_strategy_preserves_execution_settings(kind, configured):
    kernel = Kernel()
    kernel.add_service(ChatCompletionClientBase(service_id="default", ai_model_id="default-model"))
    kernel.add_service(ChatCompletionClientBase(service_id="router", ai_model_id="router-model"))
    settings = PromptExecutionSettings(service_id="router", extension_data={"temperature": 0.1}) if configured else None
    arguments = KernelArguments(settings=settings, router="application-context")
    observed = []

    @kernel_function
    def decide(execution_settings: PromptExecutionSettings, arguments: KernelArguments) -> str:
        observed.append((execution_settings.service_id, execution_settings.extension_data, arguments.get("router")))
        return "Worker" if kind == "selection" else "true"

    function = KernelFunction.from_method(method=decide, plugin_name="routing")
    agent = ChatCompletionAgent(name="Worker", kernel=kernel)
    if kind == "selection":
        strategy = KernelFunctionSelectionStrategy(kernel=kernel, function=function, arguments=arguments)
        assert await strategy.next([agent], []) is agent
    else:
        strategy = KernelFunctionTerminationStrategy(kernel=kernel, function=function, arguments=arguments)
        assert await strategy.should_agent_terminate(agent, []) is True

    expected_settings = ("router", {"temperature": 0.1}) if configured else (None, {})
    assert observed == [(*expected_settings, "application-context")]
    assert arguments == {"router": "application-context"}
    assert arguments.execution_settings == ({"router": settings} if configured else None)


class RecordingCompletion(ChatCompletionClientBase):
    """Record model settings without calling a remote provider."""

    reply: str
    requests: list[PromptExecutionSettings] = Field(default_factory=list)

    async def _inner_get_chat_message_contents(self, chat_history, settings):
        self.requests.append(settings)
        return [ChatMessageContent(role=AuthorRole.ASSISTANT, content=self.reply)]


@pytest.mark.parametrize("kind", ["selection", "termination"])
@pytest.mark.parametrize("configured", [False, True])
async def test_strategy_prompt_uses_requested_service_without_mutating_arguments(kind, configured):
    kernel = Kernel()
    reply = "Worker" if kind == "selection" else "true"
    default = RecordingCompletion(service_id="default", ai_model_id="default-model", reply=reply)
    router = RecordingCompletion(service_id="router", ai_model_id="router-model", reply=reply)
    kernel.add_service(default)
    kernel.add_service(router)
    requested = PromptExecutionSettings(service_id="router", extension_data={"temperature": 0.1})
    arguments = KernelArguments(settings=requested if configured else None, context_value="application-context")
    fallback = PromptExecutionSettings(service_id="default", extension_data={"temperature": 0.9})
    function = KernelFunction.from_prompt(
        prompt_template_config=PromptTemplateConfig(
            template="Decide the next step", allow_dangerously_set_content=True
        ),
        function_name="decide",
        plugin_name="routing",
        prompt_execution_settings=fallback,
    )
    agent = ChatCompletionAgent(name="Worker", kernel=kernel)
    if kind == "selection":
        strategy = KernelFunctionSelectionStrategy(kernel=kernel, function=function, arguments=arguments)
        assert await strategy.next([agent], []) is agent
    else:
        strategy = KernelFunctionTerminationStrategy(kernel=kernel, function=function, arguments=arguments)
        assert await strategy.should_agent_terminate(agent, []) is True

    selected = router if configured else default
    unused = default if configured else router
    assert len(selected.requests) == 1
    assert unused.requests == []
    assert selected.requests[0].extension_data == ({"temperature": 0.1} if configured else {"temperature": 0.9})
    assert arguments == {"context_value": "application-context"}
    assert arguments.execution_settings == ({"router": requested} if configured else None)
