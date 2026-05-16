# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import ChatHistory, ChatMessageContent, FunctionCallContent, TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
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
