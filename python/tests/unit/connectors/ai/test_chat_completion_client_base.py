# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import (
    ChatHistory,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    TextContent,
)
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel


class StubChatCompletion(ChatCompletionClientBase):
    SUPPORTS_FUNCTION_CALLING = True
    responses: list[list[ChatMessageContent]]

    async def _inner_get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
    ) -> list[ChatMessageContent]:
        return self.responses.pop(0)


def _tool_call_message(text: str | None, call_id: str = "call_1") -> ChatMessageContent:
    items = []
    if text is not None:
        items.append(TextContent(text=text))
    items.append(FunctionCallContent(id=call_id, name="test-tool", arguments={}))
    return ChatMessageContent(role=AuthorRole.ASSISTANT, items=items)


async def test_auto_function_call_preserves_intermediate_text_in_final_response() -> None:
    kernel = Kernel()
    kernel.add_function("test", kernel_function(lambda: "tool result", name="tool"))

    chat_completion = StubChatCompletion(
        ai_model_id="test-model",
        responses=[
            [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    items=[
                        TextContent(text="I'll check that."),
                        FunctionCallContent(id="call_1", name="test-tool", arguments={}),
                    ],
                )
            ],
            [ChatMessageContent(role=AuthorRole.ASSISTANT, content="The answer is ready.")],
        ],
    )

    result = await chat_completion.get_chat_message_contents(
        chat_history=ChatHistory(system_message="Test"),
        settings=PromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.Auto()),
        kernel=kernel,
        arguments=KernelArguments(),
    )

    assert result[0].content == "I'll check that.\n\nThe answer is ready."


async def test_auto_function_call_preserves_intermediate_text_after_max_attempts() -> None:
    kernel = Kernel()
    kernel.add_function("test", kernel_function(lambda: "tool result", name="tool"))

    chat_completion = StubChatCompletion(
        ai_model_id="test-model",
        responses=[
            [_tool_call_message("I'll check that.")],
            [ChatMessageContent(role=AuthorRole.ASSISTANT, content="The answer is ready.")],
        ],
    )

    result = await chat_completion.get_chat_message_contents(
        chat_history=ChatHistory(system_message="Test"),
        settings=PromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(maximum_auto_invoke_attempts=1),
        ),
        kernel=kernel,
        arguments=KernelArguments(),
    )

    assert result[0].content == "I'll check that.\n\nThe answer is ready."


async def test_auto_function_call_preserves_text_from_multiple_intermediate_responses() -> None:
    kernel = Kernel()
    kernel.add_function("test", kernel_function(lambda: "tool result", name="tool"))

    chat_completion = StubChatCompletion(
        ai_model_id="test-model",
        responses=[
            [_tool_call_message("First tool call.", call_id="call_1")],
            [_tool_call_message("Second tool call.", call_id="call_2")],
            [ChatMessageContent(role=AuthorRole.ASSISTANT, content="The answer is ready.")],
        ],
    )

    result = await chat_completion.get_chat_message_contents(
        chat_history=ChatHistory(system_message="Test"),
        settings=PromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.Auto()),
        kernel=kernel,
        arguments=KernelArguments(),
    )

    assert result[0].content == "First tool call.\n\nSecond tool call.\n\nThe answer is ready."


async def test_auto_function_call_inserts_intermediate_text_when_final_response_has_no_text() -> None:
    kernel = Kernel()
    kernel.add_function("test", kernel_function(lambda: "tool result", name="tool"))

    chat_completion = StubChatCompletion(
        ai_model_id="test-model",
        responses=[
            [_tool_call_message("I'll check that.")],
            [ChatMessageContent(role=AuthorRole.ASSISTANT, items=[])],
        ],
    )

    result = await chat_completion.get_chat_message_contents(
        chat_history=ChatHistory(system_message="Test"),
        settings=PromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.Auto()),
        kernel=kernel,
        arguments=KernelArguments(),
    )

    assert result[0].content == "I'll check that."


async def test_auto_function_call_preserves_intermediate_text_when_filter_terminates() -> None:
    kernel = Kernel()
    kernel.add_function("test", kernel_function(lambda: "tool result", name="tool"))

    @kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
    async def auto_invoke_terminate(context, next):
        await next(context)
        context.terminate = True

    chat_completion = StubChatCompletion(
        ai_model_id="test-model",
        responses=[
            [_tool_call_message("I'll check that.")],
        ],
    )

    result = await chat_completion.get_chat_message_contents(
        chat_history=ChatHistory(system_message="Test"),
        settings=PromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.Auto()),
        kernel=kernel,
        arguments=KernelArguments(),
    )

    assert result[0].content == "I'll check that."
    assert any(isinstance(item, FunctionResultContent) for item in result[0].items)


async def test_auto_function_call_preserves_final_response_when_intermediate_has_no_text() -> None:
    kernel = Kernel()
    kernel.add_function("test", kernel_function(lambda: "tool result", name="tool"))
    final_response = ChatMessageContent(role=AuthorRole.ASSISTANT, content="The answer is ready.")

    chat_completion = StubChatCompletion(
        ai_model_id="test-model",
        responses=[
            [
                ChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    items=[FunctionCallContent(id="call_1", name="test-tool", arguments={})],
                )
            ],
            [final_response],
        ],
    )

    result = await chat_completion.get_chat_message_contents(
        chat_history=ChatHistory(system_message="Test"),
        settings=PromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.Auto()),
        kernel=kernel,
        arguments=KernelArguments(),
    )

    assert result == [final_response]
