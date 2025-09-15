# Copyright (c) Microsoft. All rights reserved.

import sys
from functools import partial
from typing import Any

import pytest

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent, TextContent
from semantic_kernel.kernel_pydantic import KernelBaseModel
from tests.integration.completions.chat_completion_test_base import (
    ChatCompletionTestBase,
    anthropic_setup,
    mistral_ai_setup,
    ollama_setup,
    onnx_setup,
    vertex_ai_setup,
)
from tests.integration.completions.completion_test_base import ServiceType
from tests.utils import retry


class Step(KernelBaseModel):
    explanation: str
    output: str


class Reasoning(KernelBaseModel):
    steps: list[Step]
    final_answer: str


pytestmark = pytest.mark.parametrize(
    "service_id, execution_settings_kwargs, inputs, kwargs",
    [
        # region OpenAI
        pytest.param(
            "openai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            id="openai_text_input",
        ),
        pytest.param(
            "openai",
            {"response_format": Reasoning},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            id="openai_json_schema_response_format",
        ),
        # endregion
        # region Azure
        pytest.param(
            "azure",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            id="azure_text_input",
        ),
        pytest.param(
            "azure_custom_client",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            id="azure_custom_client",
        ),
        # endregion
        # region Azure AI Inference
        pytest.param(
            "azure_ai_inference",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            id="azure_ai_inference_text_input",
        ),
        # endregion
        # region Anthropic
        pytest.param(
            "anthropic",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=pytest.mark.skipif(not anthropic_setup, reason="Anthropic Environment Variables not set"),
            id="anthropic_text_input",
        ),
        # endregion
        # region Mistral AI
        pytest.param(
            "mistral_ai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=pytest.mark.skipif(not mistral_ai_setup, reason="Mistral AI Environment Variables not set"),
            id="mistral_ai_text_input",
        ),
        # endregion
        # region Ollama
        pytest.param(
            "ollama",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=(
                pytest.mark.skipif(not ollama_setup, reason="Need local Ollama setup"),
                pytest.mark.ollama,
            ),
            id="ollama_text_input",
        ),
        # endregion
        # region Onnx Gen AI
        pytest.param(
            "onnx_gen_ai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=(
                pytest.mark.skipif(not onnx_setup, reason="Need a Onnx Model setup"),
                pytest.mark.onnx,
            ),
            id="onnx_gen_ai",
        ),
        # endregion
        # region Google AI
        pytest.param(
            "google_ai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=pytest.mark.skip(reason="Skipping due to 429s from Google AI."),
            id="google_ai_text_input",
        ),
        # endregion
        # region Vertex AI
        pytest.param(
            "vertex_ai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=pytest.mark.skipif(not vertex_ai_setup, reason="Vertex AI Environment Variables not set"),
            id="vertex_ai_text_input",
        ),
        # endregion
        # region Bedrock
        pytest.param(
            "bedrock_amazon_titan",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            id="bedrock_amazon_titan_text_input",
        ),
        pytest.param(
            "bedrock_ai21labs",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_ai21labs_text_input",
        ),
        pytest.param(
            "bedrock_anthropic_claude",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_anthropic_claude_text_input",
        ),
        pytest.param(
            "bedrock_cohere_command",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_cohere_command_text_input",
        ),
        pytest.param(
            "bedrock_meta_llama",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_meta_llama_text_input",
        ),
        pytest.param(
            "bedrock_mistralai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            {},
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_mistralai_text_input",
        ),
        # endregion
    ],
)


class TestChatCompletion(ChatCompletionTestBase):
    """Test Chat Completions.

    This only tests if the services can return text completions given text inputs.
    """

    @override
    async def test_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[ChatMessageContent],
        kwargs: dict[str, Any],
    ):
        await self._test_helper(
            kernel,
            service_id,
            services,
            execution_settings_kwargs,
            inputs,
            False,
        )

    @override
    async def test_streaming_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[ChatMessageContent],
        kwargs: dict[str, Any],
    ):
        await self._test_helper(
            kernel,
            service_id,
            services,
            execution_settings_kwargs,
            inputs,
            True,
        )

    @override
    def evaluate(self, test_target: Any, **kwargs):
        inputs = kwargs.get("inputs")
        assert isinstance(inputs, list)
        assert len(test_target) == len(inputs) * 2
        for i in range(len(inputs)):
            message = test_target[i * 2 + 1]
            assert message.items, "No items in message"
            assert len(message.items) == 1, "Unexpected number of items in message"
            assert isinstance(message.items[0], TextContent), "Unexpected message item type"
            assert message.items[0].text, "Empty message text"

    async def _test_helper(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[ChatMessageContent],
        stream: bool,
    ):
        self.setup(kernel)
        service, settings_type = services[service_id]
        if service is None:
            pytest.skip(f"Service {service_id} not set up")

        history = ChatHistory()
        for message in inputs:
            history.add_message(message)

            cmc: ChatMessageContent | None = await retry(
                partial(
                    self.get_chat_completion_response,
                    kernel=kernel,
                    service=service,
                    execution_settings=settings_type(**execution_settings_kwargs),
                    chat_history=history,
                    stream=stream,
                ),
                retries=5,
                name="get_chat_completion_response",
            )
            if cmc:
                history.add_message(cmc)

        self.evaluate(history.messages, inputs=inputs)
