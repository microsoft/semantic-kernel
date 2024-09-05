# Copyright (c) Microsoft. All rights reserved.

import os
import sys
from functools import partial
from typing import Any

import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import ChatMessageContent, TextContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from tests.integration.completions.chat_completion_test_base import ChatCompletionTestBase
from tests.integration.completions.completion_test_base import ServiceType
from tests.integration.completions.test_utils import retry

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

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

anthropic_setup: bool = False
try:
    if os.environ["ANTHROPIC_API_KEY"] and os.environ["ANTHROPIC_CHAT_MODEL_ID"]:
        anthropic_setup = True
except KeyError:
    anthropic_setup = False


pytestmark = pytest.mark.parametrize(
    "service_id, execution_settings_kwargs, inputs, kwargs",
    [
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
            "anthropic",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            marks=pytest.mark.skipif(not anthropic_setup, reason="Anthropic Environment Variables not set"),
            id="anthropic_text_input",
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
            "vertex_ai",
            {},
            [
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello")]),
                ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="How are you today?")]),
            ],
            ["Hello", "well"],
            id="vertex_ai_text_input",
        ),
    ],
)


@pytest.mark.asyncio(scope="module")
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
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
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
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
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

        history = ChatHistory()
        for message in inputs:
            history.add_message(message)

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
            history.add_message(cmc)

        self.evaluate(history.messages, inputs=inputs)
