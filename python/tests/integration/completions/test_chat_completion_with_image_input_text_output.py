# Copyright (c) Microsoft. All rights reserved.

import os
import sys
from functools import partial
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import ChatHistory, ChatMessageContent, TextContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from tests.integration.completions.chat_completion_test_base import (
    ChatCompletionTestBase,
    google_ai_setup,
    ollama_image_setup,
    onnx_setup,
    vertex_ai_setup,
)
from tests.integration.completions.completion_test_base import ServiceType
from tests.utils import retry

pytestmark = pytest.mark.parametrize(
    "service_id, execution_settings_kwargs, inputs, kwargs",
    [
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
            {},
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
            {},
            id="openai_image_input_file",
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
            {},
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
            {},
            id="azure_image_input_file",
        ),
        pytest.param(
            "onnx_gen_ai",
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
            {},
            marks=(
                pytest.mark.skipif(not onnx_setup, reason="Need a Onnx Model setup"),
                pytest.mark.onnx,
            ),
            id="onnx_gen_ai_image_input_file",
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
            {},
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
            {},
            id="azure_ai_inference_image_input_file",
        ),
        pytest.param(
            "google_ai",
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
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[TextContent(text="Where was it made? Make a guess if you are not sure.")],
                ),
            ],
            {},
            marks=[
                pytest.mark.skipif(not google_ai_setup, reason="Google AI Environment Variables not set"),
            ],
            id="google_ai_image_input_file",
        ),
        pytest.param(
            "vertex_ai",
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
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[TextContent(text="Where was it made? Make a guess if you are not sure.")],
                ),
            ],
            {},
            marks=pytest.mark.skipif(not vertex_ai_setup, reason="Vertex AI Environment Variables not set"),
            id="vertex_ai_image_input_file",
        ),
        pytest.param(
            "ollama_image",
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
                ChatMessageContent(
                    role=AuthorRole.USER,
                    items=[TextContent(text="Where was it made? Make a guess if you are not sure.")],
                ),
            ],
            {},
            marks=(
                pytest.mark.skipif(not ollama_image_setup, reason="Ollama Environment Variables not set"),
                pytest.mark.ollama,
            ),
            id="ollama_image_input_file",
        ),
        pytest.param(
            "bedrock_anthropic_claude",
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
            {},
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_anthropic_claude_image_input_file",
        ),
    ],
)


class TestChatCompletionWithImageInputTextOutput(ChatCompletionTestBase):
    """Test chat completion with image input and text output."""

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
                name="image_input",
            )
            if cmc:
                history.add_message(cmc)

        self.evaluate(history.messages, inputs=inputs)
