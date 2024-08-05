# Copyright (c) Microsoft. All rights reserved.

import os
import sys
from functools import partial
from typing import Any

import pytest
from openai import AsyncAzureOpenAI

from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_completion import GoogleAITextCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_text_completion import VertexAITextCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.hugging_face.hf_prompt_execution_settings import HuggingFacePromptExecutionSettings
from semantic_kernel.connectors.ai.hugging_face.services.hf_text_completion import HuggingFaceTextCompletion
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaTextPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_text_completion import OllamaTextCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_text_completion import AzureTextCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import OpenAITextCompletion
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from tests.integration.completions.test_completion_base import ServiceType, TestCompletionBase
from tests.integration.completions.test_utils import retry

ollama_setup: bool = False
try:
    if os.environ["OLLAMA_MODEL"]:
        ollama_setup = True
except KeyError:
    ollama_setup = False


pytestmark = pytest.mark.parametrize(
    "service_id, execution_settings_kwargs, inputs",
    [
        pytest.param(
            "openai",
            {},
            ["Repeat the word Hello"],
            id="openai_text_completion",
        ),
        pytest.param(
            "azure",
            {},
            ["Repeat the word Hello"],
            id="azure_text_completion",
        ),
        pytest.param(
            "hf_t2t",
            {},
            ["translate English to Dutch: Hello"],
            id="huggingface_text_completion_translation",
        ),
        pytest.param(
            "hf_summ",
            {},
            [
                """Summarize: Whales are fully aquatic, open-ocean animals:
        they can feed, mate, give birth, suckle and raise their young at sea.
        Whales range in size from the 2.6 metres (8.5 ft) and 135 kilograms (298 lb)
        dwarf sperm whale to the 29.9 metres (98 ft) and 190 tonnes (210 short tons) blue whale,
        which is the largest known animal that has ever lived. The sperm whale is the largest
        toothed predator on Earth. Several whale species exhibit sexual dimorphism,
        in that the females are larger than males."""
            ],
            id="huggingface_text_completion_summarization",
        ),
        pytest.param(
            "hf_gen",
            {},
            ["Hello, I like sleeping and "],
            id="huggingface_text_completion_generation",
        ),
        pytest.param(
            "ollama",
            {},
            ["Repeat the word Hello"],
            marks=pytest.mark.skipif(not ollama_setup, reason="Need local Ollama setup"),
            id="ollama_text_input",
        ),
        pytest.param(
            "google_ai",
            {},
            ["Repeat the word Hello"],
            marks=pytest.mark.skip(reason="Skipping due to 429s from Google AI."),
            id="google_ai_text_completion",
        ),
        pytest.param(
            "vertex_ai",
            {},
            ["Repeat the word Hello"],
            id="vertex_ai_text_completion",
        ),
    ],
)


class TestTextCompletion(TestCompletionBase):
    """Test class for text completion"""

    @override
    @pytest.fixture(scope="class")
    def services(self) -> dict[str, tuple[ServiceType, type[PromptExecutionSettings]]]:
        azure_openai_settings = AzureOpenAISettings.create()
        endpoint = azure_openai_settings.endpoint
        deployment_name = azure_openai_settings.text_deployment_name
        api_key = azure_openai_settings.api_key.get_secret_value()
        api_version = azure_openai_settings.api_version
        azure_custom_client = AzureTextCompletion(
            async_client=AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                api_key=api_key,
                api_version=api_version,
                default_headers={"Test-User-X-ID": "test"},
            ),
        )

        return {
            "openai": (OpenAITextCompletion(), OpenAITextPromptExecutionSettings),
            "azure": (AzureTextCompletion(), OpenAITextPromptExecutionSettings),
            "azure_custom_client": (azure_custom_client, OpenAITextPromptExecutionSettings),
            "ollama": (OllamaTextCompletion() if ollama_setup else None, OllamaTextPromptExecutionSettings),
            "google_ai": (GoogleAITextCompletion(), GoogleAITextPromptExecutionSettings),
            "vertex_ai": (VertexAITextCompletion(), VertexAITextPromptExecutionSettings),
            "hf_t2t": (
                HuggingFaceTextCompletion(
                    service_id="patrickvonplaten/t5-tiny-random",
                    ai_model_id="patrickvonplaten/t5-tiny-random",
                    task="text2text-generation",
                ),
                HuggingFacePromptExecutionSettings,
            ),
            "hf_summ": (
                HuggingFaceTextCompletion(
                    service_id="jotamunz/billsum_tiny_summarization",
                    ai_model_id="jotamunz/billsum_tiny_summarization",
                    task="summarization",
                ),
                HuggingFacePromptExecutionSettings,
            ),
            "hf_gen": (
                HuggingFaceTextCompletion(
                    service_id="HuggingFaceM4/tiny-random-LlamaForCausalLM",
                    ai_model_id="HuggingFaceM4/tiny-random-LlamaForCausalLM",
                    task="text-generation",
                ),
                HuggingFacePromptExecutionSettings,
            ),
        }

    @override
    @pytest.mark.asyncio(scope="module")
    async def test_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
    ) -> None:
        self.setup(kernel, service_id, services, execution_settings_kwargs)
        for message in inputs:
            response = await retry(partial(self.execute_invoke, kernel=kernel, input=message, stream=False), retries=5)
            self.evaluate_response(response)

    @override
    @pytest.mark.asyncio(scope="module")
    async def test_streaming_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str | ChatMessageContent | list[ChatMessageContent]],
    ):
        self.setup(kernel, service_id, services, execution_settings_kwargs)
        for message in inputs:
            response = await retry(partial(self.execute_invoke, kernel=kernel, input=message, stream=True), retries=5)
            self.evaluate_response(response)

    @override
    def evaluate_response(self, response: Any, **kwargs):
        print(response)
        if isinstance(response, TextContent):
            # Test is considered successful if the response is not empty
            assert response.text, "Error: Empty response"
            return
        raise AssertionError(f"Unexpected output: response: {response}, type: {type(response)}")
