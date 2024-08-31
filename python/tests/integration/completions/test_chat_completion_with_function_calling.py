# Copyright (c) Microsoft. All rights reserved.

import sys
from enum import Enum
from functools import partial
from typing import Any

import pytest

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel
from tests.integration.completions.chat_completion_test_base import ChatCompletionTestBase
from tests.integration.completions.completion_test_base import ServiceType
from tests.integration.completions.test_utils import retry

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class FunctionChoiceTestTypes(str, Enum):
    """Test function choice types."""

    AUTO = "auto"
    """
    Expect a FunctionCallContent, a FunctionResultContent, and a
    TextContent in the response, apart from the input.
    """
    NON_AUTO = "non_auto"
    """
    Expect a FunctionCallContent in the response, apart from the input.
    """
    FLOW = "flow"
    """
    Expect a TextContent in the response, apart from the input.
    """


pytestmark = pytest.mark.parametrize(
    "service_id, execution_settings_kwargs, inputs, kwargs",
    [
        pytest.param(
            "openai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="What is 345 + 3?")],
                    ),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            id="openai_tool_call_auto",
        ),
        pytest.param(
            "openai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="What is 345 + 3?")],
                    ),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.NON_AUTO},
            id="openai_tool_call_non_auto",
        ),
        pytest.param(
            "openai",
            {},
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="What was our 2024 revenue?")],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        items=[
                            FunctionCallContent(
                                id="fin", name="finance-search", arguments='{"company": "contoso", "year": 2024}'
                            )
                        ],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.TOOL,
                        items=[FunctionResultContent(id="fin", name="finance-search", result="1.2B")],
                    ),
                ],
            ],
            {"test_type": FunctionChoiceTestTypes.FLOW},
            id="openai_tool_call_flow",
        ),
        pytest.param(
            "azure",
            {"function_choice_behavior": FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["task_plugin"]})},
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 345 + 3?")]),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            id="azure_tool_call_auto",
        ),
        pytest.param(
            "azure",
            {"function_choice_behavior": "auto"},
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 345 + 3?")]),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            id="azure_tool_call_auto_as_string",
        ),
        pytest.param(
            "azure",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 345 + 3?")]),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.NON_AUTO},
            id="azure_tool_call_non_auto",
        ),
        pytest.param(
            "azure",
            {},
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="What was our 2024 revenue?")],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        items=[
                            FunctionCallContent(
                                id="fin", name="finance-search", arguments='{"company": "contoso", "year": 2024}'
                            )
                        ],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.TOOL,
                        items=[FunctionResultContent(id="fin", name="finance-search", result="1.2B")],
                    ),
                ],
            ],
            {"test_type": FunctionChoiceTestTypes.FLOW},
            id="azure_tool_call_flow",
        ),
        pytest.param(
            "azure_ai_inference",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                ),
                "max_tokens": 256,
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 345 + 3?")]),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            marks=pytest.mark.skip(
                reason="Possible regression on the Azure AI Inference side when"
                " returning tool calls in streaming responses. Investigating..."
            ),
            id="azure_ai_inference_tool_call_auto",
        ),
        pytest.param(
            "azure_ai_inference",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 345 + 3?")]),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.NON_AUTO},
            id="azure_ai_inference_tool_call_non_auto",
        ),
        pytest.param(
            "azure_ai_inference",
            {},
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="What was our 2024 revenue?")],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        items=[
                            FunctionCallContent(
                                id="fin", name="finance-search", arguments='{"company": "contoso", "year": 2024}'
                            )
                        ],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.TOOL,
                        items=[FunctionResultContent(id="fin", name="finance-search", result="1.2B")],
                    ),
                ],
            ],
            {"test_type": FunctionChoiceTestTypes.FLOW},
            id="azure_ai_inference_tool_call_flow",
        ),
        pytest.param(
            "google_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                ),
                "max_tokens": 256,
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 345 + 3?")]),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            id="google_ai_tool_call_auto",
        ),
        pytest.param(
            "google_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 345 + 3?")]),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.NON_AUTO},
            id="google_ai_tool_call_non_auto",
        ),
        pytest.param(
            "google_ai",
            {},
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="What was our 2024 revenue?")],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        items=[
                            FunctionCallContent(
                                id="fin", name="finance-search", arguments='{"company": "contoso", "year": 2024}'
                            )
                        ],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.TOOL,
                        items=[FunctionResultContent(id="fin", name="finance-search", result="1.2B")],
                    ),
                ],
            ],
            {"test_type": FunctionChoiceTestTypes.FLOW},
            marks=pytest.mark.skip(reason="Skipping due to 429s from Google AI."),
            id="google_ai_tool_call_flow",
        ),
        pytest.param(
            "vertex_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                ),
                "max_tokens": 256,
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 345 + 3?")]),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            id="vertex_ai_tool_call_auto",
        ),
        pytest.param(
            "vertex_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.SYSTEM,
                        items=[TextContent(text="You're very bad at math. Don't attempt to do it yourself.")],
                    ),
                    ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 345 + 3?")]),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.NON_AUTO},
            id="vertex_ai_tool_call_non_auto",
        ),
        pytest.param(
            "vertex_ai",
            {},
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="What was our 2024 revenue?")],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        items=[
                            FunctionCallContent(
                                id="fin", name="finance-search", arguments='{"company": "contoso", "year": 2024}'
                            )
                        ],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.TOOL,
                        items=[FunctionResultContent(id="fin", name="finance-search", result="1.2B")],
                    ),
                ],
            ],
            {"test_type": FunctionChoiceTestTypes.FLOW},
            id="vertex_ai_tool_call_flow",
        ),
    ],
)


@pytest.mark.asyncio(scope="module")
class TestChatCompletionWithFunctionCalling(ChatCompletionTestBase):
    """Test Chat Completion with function calling"""

    @override
    async def test_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
        kwargs: dict[str, Any],
    ):
        await self._test_helper(
            kernel,
            service_id,
            services,
            execution_settings_kwargs,
            inputs,
            kwargs,
            False,
        )

    @override
    async def test_streaming_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
        kwargs: dict[str, Any],
    ):
        await self._test_helper(
            kernel,
            service_id,
            services,
            execution_settings_kwargs,
            inputs,
            kwargs,
            True,
        )

    @override
    def evaluate(self, test_target: Any, **kwargs):
        inputs = kwargs.get("inputs")
        test_type = kwargs.get("test_type")

        if test_type == FunctionChoiceTestTypes.AUTO:
            self._evaluate_auto_function_choice(test_target, inputs)
            return
        if test_type == FunctionChoiceTestTypes.NON_AUTO:
            self._evaluate_non_auto_function_choice(test_target, inputs)
            return
        if test_type == FunctionChoiceTestTypes.FLOW:
            self._evaluate_flow_test_type(test_target, inputs)
            return

        raise ValueError(f"Invalid test type: {test_type}")

    def _evaluate_auto_function_choice(
        self,
        chat_history: ChatHistory,
        inputs: list[ChatMessageContent | list[ChatMessageContent]],
    ):
        # Skip the input messages
        skip_counts = len(inputs[0]) if isinstance(inputs[0], list) else 1

        # Expect a FunctionCallContent, a FunctionResultContent, and a
        # TextContent in the response, apart from the input.
        assert len(chat_history.messages) == skip_counts + 3

        # Expect the first message to be a FunctionCallContent
        assert any(isinstance(item, FunctionCallContent) for item in chat_history.messages[skip_counts].items)
        # Expect the second message to be a FunctionResultContent
        assert isinstance(chat_history.messages[skip_counts + 1].items[0], FunctionResultContent)
        # Expect the third message to be a TextContent
        assert any(isinstance(item, TextContent) for item in chat_history.messages[skip_counts + 2].items)

    def _evaluate_non_auto_function_choice(
        self,
        chat_history: ChatHistory,
        inputs: list[ChatMessageContent | list[ChatMessageContent]],
    ):
        # Skip the input messages
        skip_counts = len(inputs[0]) if isinstance(inputs[0], list) else 1

        # Expect a FunctionCallContent apart from the input.
        assert len(chat_history.messages) == skip_counts + 1

        # Expect the first message to be a FunctionCallContent
        assert any(isinstance(item, FunctionCallContent) for item in chat_history.messages[skip_counts].items)

    def _evaluate_flow_test_type(
        self,
        chat_history: ChatHistory,
        inputs: list[ChatMessageContent | list[ChatMessageContent]],
    ):
        # Skip the input messages
        skip_counts = len(inputs[0]) if isinstance(inputs[0], list) else 1

        # Expect a TextContent in the response, apart from the input.
        assert len(chat_history.messages) == skip_counts + 1

        # Expect a single item in each message
        for message in chat_history.messages[skip_counts:]:
            assert len(message.items) == 1

        # Expect the first message to be a TextContent
        assert any(isinstance(item, TextContent) for item in chat_history.messages[skip_counts].items)

    async def _test_helper(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[ChatMessageContent | list[ChatMessageContent]],
        kwargs: dict[str, Any],
        stream: bool,
    ):
        assert "test_type" in kwargs, "Invalid parameterization: Test type not provided"
        test_type = kwargs["test_type"]

        assert len(inputs) == 1, "Invalid parameterization: Only one input message or a single list are allowed"
        history = ChatHistory()
        if isinstance(inputs[0], list):
            [history.add_message(message) for message in inputs[0]]
        else:
            [history.add_message(message) for message in inputs]

        self.setup(kernel)
        service, settings_type = services[service_id]

        cmc = await retry(
            partial(
                self.get_chat_completion_response,
                kernel=kernel,
                service=service,
                execution_settings=settings_type(**execution_settings_kwargs),
                chat_history=history,
                stream=stream,
            ),
            retries=5,
        )

        # We need to add the latest message to the history because the connector is
        # not responsible for updating the history, unless it is related to auto function
        # calling, when the history is updated after the function calls are invoked.
        history.add_message(cmc)

        self.evaluate(history, inputs=inputs, test_type=test_type)
