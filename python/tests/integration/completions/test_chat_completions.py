# Copyright (c) Microsoft. All rights reserved.

import os
from functools import partial, reduce
from typing import Any

import pytest
from azure.ai.inference.aio import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from openai import AsyncAzureOpenAI

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_chat_completion import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion import GoogleAIChatCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_chat_completion import VertexAIChatCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion import MistralAIChatCompletion
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import OllamaChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import ChatHistory, ChatMessageContent, TextContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from tests.integration.completions.test_utils import retry

mistral_ai_setup: bool = False
try:
    if os.environ["MISTRALAI_API_KEY"] and os.environ["MISTRALAI_CHAT_MODEL_ID"]:
        mistral_ai_setup = True
except KeyError:
    mistral_ai_setup = False

ollama_setup: bool = False
try:
    if os.environ["OLLAMA_MODEL"]:
        ollama_setup = True
except KeyError:
    ollama_setup = False


def setup(
    kernel: Kernel,
    service: str,
    execution_settings_kwargs: dict[str, Any],
    services: dict[str, tuple[ChatCompletionClientBase, type[PromptExecutionSettings]]],
):
    kernel.add_service(services[service][0])
    kernel.add_plugin(MathPlugin(), plugin_name="math")
    kernel.add_function(
        function_name="chat",
        plugin_name="chat",
        prompt="If someone asks how you are, always include the word 'well', "
        "if you get a direct question, answer the question. {{$chat_history}}",
        prompt_execution_settings=services[service][1](**execution_settings_kwargs),
    )


@pytest.fixture(scope="function")
def history() -> ChatHistory:
    return ChatHistory()


@pytest.fixture(scope="module")
def services() -> dict[str, tuple[ChatCompletionClientBase | None, type[PromptExecutionSettings]]]:
    azure_openai_settings = AzureOpenAISettings.create()
    endpoint = azure_openai_settings.endpoint
    deployment_name = azure_openai_settings.chat_deployment_name
    api_key = azure_openai_settings.api_key.get_secret_value()
    api_version = azure_openai_settings.api_version
    azure_custom_client = AzureChatCompletion(
        async_client=AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=deployment_name,
            api_key=api_key,
            api_version=api_version,
            default_headers={"Test-User-X-ID": "test"},
        ),
    )
    azure_ai_inference_client = AzureAIInferenceChatCompletion(
        ai_model_id=deployment_name,
        client=ChatCompletionsClient(
            endpoint=f'{str(endpoint).strip("/")}/openai/deployments/{deployment_name}',
            credential=AzureKeyCredential(""),
            headers={"api-key": api_key},
        ),
    )

    return {
        "openai": (OpenAIChatCompletion(), OpenAIChatPromptExecutionSettings),
        "azure": (AzureChatCompletion(), AzureChatPromptExecutionSettings),
        "azure_custom_client": (azure_custom_client, AzureChatPromptExecutionSettings),
        "azure_ai_inference": (azure_ai_inference_client, AzureAIInferenceChatPromptExecutionSettings),
        "mistral_ai": (MistralAIChatCompletion() if mistral_ai_setup else None, MistralAIChatPromptExecutionSettings),
        "ollama": (OllamaChatCompletion() if ollama_setup else None, OllamaChatPromptExecutionSettings),
        "google_ai": (GoogleAIChatCompletion(), GoogleAIChatPromptExecutionSettings),
        "vertex_ai": (VertexAIChatCompletion(), VertexAIChatPromptExecutionSettings),
    }


pytestmark = pytest.mark.parametrize(
    "service, execution_settings_kwargs, inputs, outputs",
    [
        pytest.param(
            "openai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            id="openai_text_input",
        ),
        pytest.param(
            "openai",
            {},
            [
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[
                        TextContent(text="What is in this image?"),
                        ImageContent(
                            uri="https://upload.wikimedia.org/wikipedia/commons/d/d5/Half-timbered_mansion%2C_Zirkel%2C_East_view.jpg"
                        ),
                    ],
                ),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Where was it made?")]),
            ],
            ["house", "germany"],
            id="openai_image_input_uri",
        ),
        pytest.param(
            "openai",
            {},
            [
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[
                        TextContent(text="What is in this image?"),
                        ImageContent.from_image_path(
                            image_path=os.path.join(os.path.dirname(__file__), "../../", "assets/sample_image.jpg")
                        ),
                    ],
                ),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Where was it made?")]),
            ],
            ["house", "germany"],
            id="openai_image_input_file",
        ),
        pytest.param(
            "openai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["chat"]}
                )
            },
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
            id="openai_tool_call_auto",
        ),
        pytest.param(
            "openai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["chat"]}
                )
            },
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
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
            ["1.2"],
            id="openai_tool_call_flow",
        ),
        pytest.param(
            "azure",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            id="azure_text_input",
        ),
        pytest.param(
            "azure",
            {},
            [
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[
                        TextContent(text="What is in this image?"),
                        ImageContent(
                            uri="https://upload.wikimedia.org/wikipedia/commons/d/d5/Half-timbered_mansion%2C_Zirkel%2C_East_view.jpg"
                        ),
                    ],
                ),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Where was it made?")]),
            ],
            ["house", "germany"],
            id="azure_image_input_uri",
        ),
        pytest.param(
            "azure",
            {},
            [
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[
                        TextContent(text="What is in this image?"),
                        ImageContent.from_image_path(
                            image_path=os.path.join(os.path.dirname(__file__), "../../", "assets/sample_image.jpg")
                        ),
                    ],
                ),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Where was it made?")]),
            ],
            ["house", "germany"],
            id="azure_image_input_file",
        ),
        pytest.param(
            "azure",
            {"function_choice_behavior": FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["chat"]})},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
            id="azure_tool_call_auto",
        ),
        pytest.param(
            "azure",
            {"function_choice_behavior": "auto"},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
            id="azure_tool_call_auto_as_string",
        ),
        pytest.param(
            "azure",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["chat"]}
                )
            },
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
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
            ["1.2"],
            id="azure_tool_call_flow",
        ),
        pytest.param(
            "azure_custom_client",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            id="azure_custom_client",
        ),
        pytest.param(
            "azure_ai_inference",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            id="azure_ai_inference_text_input",
        ),
        pytest.param(
            "azure_ai_inference",
            {
                "max_tokens": 256,
            },
            [
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[
                        TextContent(text="What is in this image?"),
                        ImageContent(
                            uri="https://upload.wikimedia.org/wikipedia/commons/d/d5/Half-timbered_mansion%2C_Zirkel%2C_East_view.jpg"
                        ),
                    ],
                ),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Where was it made?")]),
            ],
            ["house", "germany"],
            id="azure_ai_inference_image_input_uri",
        ),
        pytest.param(
            "azure_ai_inference",
            {
                "max_tokens": 256,
            },
            [
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[
                        TextContent(text="What is in this image?"),
                        ImageContent.from_image_path(
                            image_path=os.path.join(os.path.dirname(__file__), "../../", "assets/sample_image.jpg")
                        ),
                    ],
                ),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Where was it made?")]),
            ],
            ["house", "germany"],
            id="azure_ai_inference_image_input_file",
        ),
        pytest.param(
            "azure_ai_inference",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["chat"]}
                ),
                "max_tokens": 256,
            },
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
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
                    auto_invoke=False, filters={"excluded_plugins": ["chat"]}
                )
            },
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
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
            ["1.2"],
            id="azure_ai_inference_tool_call_flow",
        ),
        pytest.param(
            "mistral_ai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            marks=pytest.mark.skipif(not mistral_ai_setup, reason="Mistral AI Environment Variables not set"),
            id="mistral_ai_text_input",
        ),
        pytest.param(
            "ollama",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            marks=pytest.mark.skipif(not ollama_setup, reason="Need local Ollama setup"),
            id="ollama_text_input",
        ),
        pytest.param(
            "google_ai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            marks=pytest.mark.skip(reason="Skipping due to 429s from Google AI."),
            id="google_ai_text_input",
        ),
        pytest.param(
            "google_ai",
            {
                "max_tokens": 256,
            },
            [
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[
                        TextContent(text="What is in this image?"),
                        ImageContent.from_image_path(
                            image_path=os.path.join(os.path.dirname(__file__), "../../", "assets/sample_image.jpg")
                        ),
                    ],
                ),
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[TextContent(text="Where was it made? Make a guess if you are not sure.")],
                ),
            ],
            ["house", "germany"],
            id="google_ai_image_input_file",
        ),
        pytest.param(
            "google_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["chat"]}
                ),
                "max_tokens": 256,
            },
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
            id="google_ai_tool_call_auto",
        ),
        pytest.param(
            "google_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["chat"]}
                )
            },
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
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
            ["1.2"],
            marks=pytest.mark.skip(reason="Skipping due to 429s from Google AI."),
            id="google_ai_tool_call_flow",
        ),
        pytest.param(
            "vertex_ai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            id="vertex_ai_text_input",
        ),
        pytest.param(
            "vertex_ai",
            {
                "max_tokens": 256,
            },
            [
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[
                        TextContent(text="What is in this image?"),
                        ImageContent.from_image_path(
                            image_path=os.path.join(os.path.dirname(__file__), "../../", "assets/sample_image.jpg")
                        ),
                    ],
                ),
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[TextContent(text="Where was it made? Make a guess if you are not sure.")],
                ),
            ],
            ["house", "germany"],
            id="vertex_ai_image_input_file",
        ),
        pytest.param(
            "vertex_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=True, filters={"excluded_plugins": ["chat"]}
                ),
                "max_tokens": 256,
            },
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
            id="vertex_ai_tool_call_auto",
        ),
        pytest.param(
            "vertex_ai",
            {
                "function_choice_behavior": FunctionChoiceBehavior.Auto(
                    auto_invoke=False, filters={"excluded_plugins": ["chat"]}
                )
            },
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="What is 3+345?")]),
            ],
            ["348"],
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
            ["1.2"],
            id="vertex_ai_tool_call_flow",
        ),
    ],
)


@pytest.mark.asyncio(scope="module")
async def test_chat_completion(
    kernel: Kernel,
    service: str,
    execution_settings_kwargs: dict[str, Any],
    inputs: list[ChatMessageContent | list[ChatMessageContent]],
    outputs: list[str],
    services: dict[str, tuple[ChatCompletionClientBase, type[PromptExecutionSettings]]],
    history: ChatHistory,
):
    setup(kernel, service, execution_settings_kwargs, services)
    for message, output in zip(inputs, outputs):
        if isinstance(message, list):
            for msg in message:
                history.add_message(msg)
        else:
            history.add_message(message)

        cmc = await retry(
            partial(execute_invoke, kernel=kernel, history=history, output=output, stream=False), retries=5
        )
        history.add_message(cmc)


@pytest.mark.asyncio(scope="module")
async def test_streaming_chat_completion(
    kernel: Kernel,
    service: str,
    execution_settings_kwargs: dict[str, Any],
    inputs: list[ChatMessageContent | list[ChatMessageContent]],
    outputs: list[str],
    services: dict[str, tuple[ChatCompletionClientBase, type[PromptExecutionSettings]]],
    history: ChatHistory,
):
    setup(kernel, service, execution_settings_kwargs, services)
    for message, output in zip(inputs, outputs):
        if isinstance(message, list):
            for msg in message:
                history.add_message(msg)
        else:
            history.add_message(message)
        cmc = await retry(
            partial(execute_invoke, kernel=kernel, history=history, output=output, stream=True), retries=5
        )
        history.add_message(cmc)


async def execute_invoke(kernel: Kernel, history: ChatHistory, output: str, stream: bool) -> "ChatMessageContent":
    if stream:
        invocation = kernel.invoke_stream(function_name="chat", plugin_name="chat", chat_history=history)
        parts = [part[0] async for part in invocation]
        if parts:
            response = reduce(lambda p, r: p + r, parts)
        else:
            raise AssertionError("No response")
    else:
        invocation = await kernel.invoke(function_name="chat", plugin_name="chat", chat_history=history)
        assert invocation is not None
        response = invocation.value[0]
    print(response)
    if isinstance(response, ChatMessageContent):
        assert response.items, "No items in response"
        for item in response.items:
            if isinstance(item, TextContent):
                assert item.text is not None
                assert output.lower() in item.text.lower()
            if isinstance(item, FunctionCallContent):
                assert item.arguments
                assert kernel.get_function_from_fully_qualified_function_name(item.name)
        return response
    raise AssertionError(f"Unexpected output: response: {invocation}, type: {type(invocation)}")
