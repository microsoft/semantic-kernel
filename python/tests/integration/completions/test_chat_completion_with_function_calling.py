# Copyright (c) Microsoft. All rights reserved.

import sys
from enum import Enum
from functools import partial
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

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
from tests.integration.completions.chat_completion_test_base import (
    ChatCompletionTestBase,
    anthropic_setup,
    google_ai_setup,
    mistral_ai_setup,
    ollama_tool_call_setup,
    vertex_ai_setup,
)
from tests.integration.completions.completion_test_base import ServiceType
from tests.utils import retry


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
        # region OpenAI
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
            "openai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="Find the person whose id is 9b3f6e40.")],
                    ),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            id="openai_tool_call_auto_complex_return_type",
        ),
        # endregion
        # region Azure
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
            "azure",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="Find the person whose id is 9b3f6e40.")],
                    ),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            id="azure_tool_call_auto_complex_return_type",
        ),
        # endregion
        # region Azure AI Inference
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
            marks=pytest.mark.skip(
                reason="Possible regression on the Azure AI Inference side when"
                " returning tool calls in streaming responses. Investigating..."
            ),
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
            "azure_ai_inference",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="Find the person whose id is 9b3f6e40.")],
                    ),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            marks=pytest.mark.skip(
                reason="Possible regression on the Azure AI Inference side when"
                " returning tool calls in streaming responses. Investigating..."
            ),
            id="azure_ai_inference_tool_call_auto_complex_return_type",
        ),
        # endregion
        # region Mistral AI
        pytest.param(
            "mistral_ai",
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
            marks=pytest.mark.skipif(not mistral_ai_setup, reason="Mistral AI Environment Variables not set"),
            id="mistral_ai_tool_call_auto",
        ),
        pytest.param(
            "mistral_ai",
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
            marks=pytest.mark.skipif(not mistral_ai_setup, reason="Mistral AI Environment Variables not set"),
            id="mistral_ai_tool_call_non_auto",
        ),
        pytest.param(
            "mistral_ai",
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
                                id="123456789", name="finance-search", arguments='{"company": "contoso", "year": 2024}'
                            )
                        ],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.TOOL,
                        items=[FunctionResultContent(id="123456789", name="finance-search", result="1.2B")],
                    ),
                ],
            ],
            {"test_type": FunctionChoiceTestTypes.FLOW},
            marks=pytest.mark.skipif(not mistral_ai_setup, reason="Mistral AI Environment Variables not set"),
            id="mistral_ai_tool_call_flow",
        ),
        # endregion
        # region Anthropic
        pytest.param(
            "anthropic",
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
            marks=pytest.mark.skipif(not anthropic_setup, reason="Anthropic Environment Variables not set"),
            id="anthropic_tool_call_auto",
        ),
        pytest.param(
            "anthropic",
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
            marks=pytest.mark.skipif(not anthropic_setup, reason="Anthropic Environment Variables not set"),
            id="anthropic_tool_call_non_auto",
        ),
        pytest.param(
            "anthropic",
            {
                # Anthropic expects tools in the request when it sees tool use in the chat history.
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                ),
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="What was our 2024 revenue?")],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        items=[
                            # Anthropic will often include a chain of thought in the tool call by default.
                            # If this is not in the message, it will complain about the missing chain of thought.
                            TextContent(text="I will find the revenue for you."),
                            FunctionCallContent(
                                id="123456789", name="finance-search", arguments='{"company": "contoso", "year": 2024}'
                            ),
                        ],
                    ),
                    ChatMessageContent(
                        role=AuthorRole.TOOL,
                        items=[FunctionResultContent(id="123456789", name="finance-search", result="1.2B")],
                    ),
                ],
            ],
            {"test_type": FunctionChoiceTestTypes.FLOW},
            marks=pytest.mark.skipif(not anthropic_setup, reason="Anthropic Environment Variables not set"),
            id="anthropic_tool_call_flow",
        ),
        # endregion
        # region Google AI
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
            marks=[
                pytest.mark.skipif(not google_ai_setup, reason="Google AI Environment Variables not set"),
            ],
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
            marks=[
                pytest.mark.skipif(not google_ai_setup, reason="Google AI Environment Variables not set"),
            ],
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
            id="google_ai_tool_call_flow",
        ),
        pytest.param(
            "google_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="Find the person whose id is 9b3f6e40.")],
                    ),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            marks=[
                pytest.mark.skipif(not google_ai_setup, reason="Google AI Environment Variables not set"),
            ],
            id="google_ai_tool_call_auto_complex_return_type",
        ),
        # endregion
        # region Vertex AI
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
            marks=pytest.mark.skipif(not vertex_ai_setup, reason="Vertex AI Environment Variables not set"),
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
            marks=pytest.mark.skipif(not vertex_ai_setup, reason="Vertex AI Environment Variables not set"),
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
            marks=pytest.mark.skipif(not vertex_ai_setup, reason="Vertex AI Environment Variables not set"),
            id="vertex_ai_tool_call_flow",
        ),
        pytest.param(
            "vertex_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="Find the person whose id is 9b3f6e40.")],
                    ),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            marks=pytest.mark.skipif(not vertex_ai_setup, reason="Vertex AI Environment Variables not set"),
            id="vertex_ai_tool_call_auto_complex_return_type",
        ),
        # endregion
        # region Ollama
        pytest.param(
            "ollama_tool_call",
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
            {
                "test_type": FunctionChoiceTestTypes.AUTO,
            },
            marks=(
                pytest.mark.skipif(not ollama_tool_call_setup, reason="Need local Ollama setup"),
                pytest.mark.ollama,
            ),
            id="ollama_tool_call_auto",
        ),
        pytest.param(
            "ollama_tool_call",
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
            {
                "test_type": FunctionChoiceTestTypes.NON_AUTO,
            },
            marks=(
                pytest.mark.skipif(not ollama_tool_call_setup, reason="Need local Ollama setup"),
                pytest.mark.ollama,
            ),
            id="ollama_tool_call_non_auto",
        ),
        pytest.param(
            "ollama_tool_call",
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
            {
                "test_type": FunctionChoiceTestTypes.FLOW,
            },
            marks=(
                pytest.mark.skipif(not ollama_tool_call_setup, reason="Need local Ollama setup"),
                pytest.mark.ollama,
            ),
            id="ollama_tool_call_flow",
        ),
        pytest.param(
            "ollama_tool_call",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="Find the person whose id is 9b3f6e40.")],
                    ),
                ]
            ],
            {
                "test_type": FunctionChoiceTestTypes.AUTO,
            },
            marks=(
                pytest.mark.skipif(not ollama_tool_call_setup, reason="Need local Ollama setup"),
                pytest.mark.ollama,
            ),
            id="ollama_tool_call_auto_complex_return_type",
        ),
        # endregion
        # region Bedrock Anthropic Claude
        pytest.param(
            "bedrock_anthropic_claude",
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
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_anthropic_claude_tool_call_non_auto",
        ),
        pytest.param(
            "bedrock_anthropic_claude",
            {
                # This is required for Bedrock to have the tool config set when messages contain tool calls.
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
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
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_anthropic_claude_tool_call_flow",
        ),
        pytest.param(
            "bedrock_anthropic_claude",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="Find the person whose id is 9b3f6e40.")],
                    ),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_anthropic_claude_tool_call_auto_complex_return_type",
        ),
        # endregion
        # region Bedrock Cohere
        pytest.param(
            "bedrock_cohere_command",
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
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_cohere_command_tool_call_non_auto",
        ),
        pytest.param(
            "bedrock_cohere_command",
            {
                # This is required for Bedrock to have the tool config set when messages contain tool calls.
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
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
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_cohere_command_tool_call_flow",
        ),
        pytest.param(
            "bedrock_cohere_command",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["task_plugin"]}
                )
            },
            [
                [
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        items=[TextContent(text="Find the person whose id is 9b3f6e40.")],
                    ),
                ]
            ],
            {"test_type": FunctionChoiceTestTypes.AUTO},
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_cohere_command_tool_call_auto_complex_return_type",
        ),
        # endregion
    ],
)


class TestChatCompletionWithFunctionCalling(ChatCompletionTestBase):
    """Test Chat Completion with function calling"""

    @override
    async def test_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[ChatMessageContent | list[ChatMessageContent]],
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
        inputs: list[ChatMessageContent | list[ChatMessageContent]],
        kwargs: dict[str, Any],
    ):
        if "streaming" in kwargs and not kwargs["streaming"]:
            pytest.skip("Skipping streaming test")

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
        assert isinstance(inputs, list)

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
        service, settings_type = services[service_id]
        if not service:
            pytest.skip(f"Skipping test for {service_id}")
        assert "test_type" in kwargs, "Invalid parameterization: Test type not provided"
        test_type = kwargs["test_type"]

        assert len(inputs) == 1, "Invalid parameterization: Only one input message or a single list are allowed"
        history = ChatHistory()
        if isinstance(inputs[0], list):
            [history.add_message(message) for message in inputs[0]]
        else:
            [history.add_message(message) for message in inputs if not isinstance(message, list)]

        self.setup(kernel)

        cmc: ChatMessageContent | None = await retry(
            partial(
                self.get_chat_completion_response,
                kernel=kernel,
                service=service,  # type: ignore
                execution_settings=settings_type(**execution_settings_kwargs),
                chat_history=history,
                stream=stream,
            ),
            retries=5,
            name="function_calling",
        )

        # We need to add the latest message to the history because the connector is
        # not responsible for updating the history, unless it is related to auto function
        # calling, when the history is updated after the function calls are invoked.
        if cmc:
            history.add_message(cmc)

        self.evaluate(history, inputs=inputs, test_type=test_type)
