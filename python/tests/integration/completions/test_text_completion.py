# Copyright (c) Microsoft. All rights reserved.

import sys
from functools import partial
from importlib import util
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import pytest
from openai import AsyncAzureOpenAI

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.bedrock import BedrockTextCompletion, BedrockTextPromptExecutionSettings
from semantic_kernel.connectors.ai.google.google_ai import GoogleAITextCompletion, GoogleAITextPromptExecutionSettings
from semantic_kernel.connectors.ai.google.vertex_ai import VertexAITextCompletion, VertexAITextPromptExecutionSettings
from semantic_kernel.connectors.ai.hugging_face import HuggingFacePromptExecutionSettings, HuggingFaceTextCompletion
from semantic_kernel.connectors.ai.ollama import OllamaTextCompletion, OllamaTextPromptExecutionSettings
from semantic_kernel.connectors.ai.onnx import OnnxGenAIPromptExecutionSettings, OnnxGenAITextCompletion
from semantic_kernel.connectors.ai.open_ai import (
    AzureOpenAISettings,
    AzureTextCompletion,
    OpenAITextCompletion,
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents import StreamingTextContent, TextContent
from semantic_kernel.utils.authentication.entra_id_authentication import get_entra_auth_token
from tests.integration.completions.completion_test_base import CompletionTestBase, ServiceType
from tests.utils import is_service_setup_for_testing, is_test_running_on_supported_platforms, retry

hugging_face_setup = util.find_spec("torch") is not None


azure_openai_setup = True
ollama_setup: bool = is_service_setup_for_testing(["OLLAMA_TEXT_MODEL_ID"]) and is_test_running_on_supported_platforms([
    "Linux"
])
google_ai_setup: bool = is_service_setup_for_testing(["GOOGLE_AI_API_KEY"])
vertex_ai_setup: bool = is_service_setup_for_testing(["VERTEX_AI_PROJECT_ID"])
onnx_setup: bool = is_service_setup_for_testing(
    ["ONNX_GEN_AI_TEXT_MODEL_FOLDER"], raise_if_not_set=False
)  # Tests are optional for ONNX

pytestmark = pytest.mark.parametrize(
    "service_id, execution_settings_kwargs, inputs, kwargs",
    [
        pytest.param(
            "openai",
            {},
            ["Repeat the word Hello once"],
            {},
            id="openai_text_completion",
        ),
        pytest.param(
            "azure",
            {},
            ["Repeat the word Hello once"],
            {},
            id="azure_text_completion",
        ),
        pytest.param(
            "hf_t2t",
            {},
            ["translate English to Dutch: Hello"],
            {},
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
            {},
            id="huggingface_text_completion_summarization",
        ),
        pytest.param(
            "hf_gen",
            {},
            ["Hello, I like sleeping and "],
            {},
            id="huggingface_text_completion_generation",
        ),
        pytest.param(
            "ollama",
            {},
            ["Repeat the word Hello once"],
            {},
            marks=(
                pytest.mark.skip(
                    reason="Need local Ollama setup" if not ollama_setup else "Ollama responses are not always correct."
                ),
                pytest.mark.ollama,
            ),
            id="ollama_text_completion",
        ),
        pytest.param(
            "google_ai",
            {},
            ["Repeat the word Hello once"],
            {},
            marks=pytest.mark.skip(reason="Skipping due to 429s from Google AI."),
            id="google_ai_text_completion",
        ),
        pytest.param(
            "vertex_ai",
            {},
            ["Repeat the word Hello once"],
            {},
            marks=pytest.mark.skipif(not vertex_ai_setup, reason="Need VertexAI setup"),
            id="vertex_ai_text_completion",
        ),
        pytest.param(
            "onnx_gen_ai",
            {},
            ["<|user|>Repeat the word Hello<|end|><|assistant|>"],
            {},
            marks=(
                pytest.mark.skipif(not onnx_setup, reason="Need a Onnx Model setup"),
                pytest.mark.onnx,
            ),
            id="onnx_gen_ai_text_completion",
        ),
        pytest.param(
            "bedrock_amazon_titan",
            {},
            ["Repeat the word Hello once"],
            {},
            id="bedrock_amazon_titan_text_completion",
        ),
        pytest.param(
            "bedrock_anthropic_claude",
            {},
            ["Repeat the word Hello once"],
            {"streaming": False},  # Streaming is not supported for models from this provider
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_anthropic_claude_text_completion",
        ),
        pytest.param(
            "bedrock_cohere_command",
            {},
            ["Repeat the word Hello once"],
            {"streaming": False},  # Streaming is not supported for models from this provider
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_cohere_command_text_completion",
        ),
        pytest.param(
            "bedrock_ai21labs",
            {},
            ["Repeat the word Hello once"],
            {"streaming": False},  # Streaming is not supported for models from this provider
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_ai21labs_text_completion",
        ),
        pytest.param(
            "bedrock_meta_llama",
            {},
            ["Repeat the word Hello once"],
            {"streaming": False},  # Streaming is not supported for models from this provider
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_meta_llama_text_completion",
        ),
        pytest.param(
            "bedrock_mistralai",
            {},
            ["Repeat the word Hello once"],
            {"streaming": False},  # Streaming is not supported for models from this provider
            marks=pytest.mark.skip(reason="Skipping due to occasional throttling from Bedrock."),
            id="bedrock_mistralai_text_completion",
        ),
    ],
)


class TestTextCompletion(CompletionTestBase):
    """Test class for text completion"""

    @override
    @pytest.fixture(scope="class")
    def services(self) -> dict[str, tuple[ServiceType | None, type[PromptExecutionSettings] | None]]:
        azure_openai_setup = True
        azure_openai_settings = AzureOpenAISettings()
        endpoint = str(azure_openai_settings.endpoint)
        deployment_name = azure_openai_settings.text_deployment_name
        ad_token = get_entra_auth_token(azure_openai_settings.token_endpoint)
        if not ad_token:
            azure_openai_setup = False
        api_version = azure_openai_settings.api_version
        azure_custom_client = None
        if azure_openai_setup:
            azure_custom_client = AzureTextCompletion(
                async_client=AsyncAzureOpenAI(
                    azure_endpoint=endpoint,
                    azure_deployment=deployment_name,
                    azure_ad_token=ad_token,
                    api_version=api_version,
                    default_headers={"Test-User-X-ID": "test"},
                ),
            )

        return {
            "openai": (OpenAITextCompletion(), OpenAITextPromptExecutionSettings),
            "azure": (AzureTextCompletion() if azure_openai_setup else None, OpenAITextPromptExecutionSettings),
            "azure_custom_client": (azure_custom_client, OpenAITextPromptExecutionSettings),
            "ollama": (OllamaTextCompletion() if ollama_setup else None, OllamaTextPromptExecutionSettings),
            "google_ai": (GoogleAITextCompletion() if google_ai_setup else None, GoogleAITextPromptExecutionSettings),
            "vertex_ai": (VertexAITextCompletion() if vertex_ai_setup else None, VertexAITextPromptExecutionSettings),
            "hf_t2t": (
                HuggingFaceTextCompletion(
                    service_id="patrickvonplaten/t5-tiny-random",
                    ai_model_id="patrickvonplaten/t5-tiny-random",
                    task="text2text-generation",
                )
                if hugging_face_setup
                else None,
                HuggingFacePromptExecutionSettings,
            ),
            "hf_summ": (
                HuggingFaceTextCompletion(
                    service_id="jotamunz/billsum_tiny_summarization",
                    ai_model_id="jotamunz/billsum_tiny_summarization",
                    task="summarization",
                )
                if hugging_face_setup
                else None,
                HuggingFacePromptExecutionSettings,
            ),
            "hf_gen": (
                HuggingFaceTextCompletion(
                    service_id="HuggingFaceM4/tiny-random-LlamaForCausalLM",
                    ai_model_id="HuggingFaceM4/tiny-random-LlamaForCausalLM",
                    task="text-generation",
                )
                if hugging_face_setup
                else None,
                HuggingFacePromptExecutionSettings,
            ),
            "onnx_gen_ai": (
                OnnxGenAITextCompletion() if onnx_setup else None,
                OnnxGenAIPromptExecutionSettings,
            ),
            # Amazon Bedrock supports models from multiple providers but requests to and responses from the models are
            # inconsistent. So we need to test each model separately.
            "bedrock_amazon_titan": (
                self._try_create_bedrock_text_completion_client("amazon.titan-text-premier-v1:0"),
                BedrockTextPromptExecutionSettings,
            ),
            "bedrock_anthropic_claude": (
                self._try_create_bedrock_text_completion_client("anthropic.claude-v2"),
                BedrockTextPromptExecutionSettings,
            ),
            "bedrock_cohere_command": (
                self._try_create_bedrock_text_completion_client("cohere.command-text-v14"),
                BedrockTextPromptExecutionSettings,
            ),
            "bedrock_ai21labs": (
                self._try_create_bedrock_text_completion_client("ai21.j2-mid-v1"),
                BedrockTextPromptExecutionSettings,
            ),
            "bedrock_meta_llama": (
                self._try_create_bedrock_text_completion_client("meta.llama3-70b-instruct-v1:0"),
                BedrockTextPromptExecutionSettings,
            ),
            "bedrock_mistralai": (
                self._try_create_bedrock_text_completion_client("mistral.mistral-7b-instruct-v0:2"),
                BedrockTextPromptExecutionSettings,
            ),
        }

    async def get_text_completion_response(
        self,
        service: ServiceType,
        execution_settings: PromptExecutionSettings,
        prompt: str,
        stream: bool,
    ) -> Any:
        """Get response from the service

        Args:
            kernel (Kernel): Kernel instance.
            service (ChatCompletionClientBase): Chat completion service.
            execution_settings (PromptExecutionSettings): Execution settings.
            prompt (str): Input string.
            stream (bool): Stream flag.
        """
        assert isinstance(service, TextCompletionClientBase)
        if stream:
            response = service.get_streaming_text_content(
                prompt=prompt,
                settings=execution_settings,
            )
            parts: list[StreamingTextContent] = [part async for part in response if part is not None]
            if parts:
                return sum(parts[1:], parts[0])
            raise AssertionError("No response")
        return await service.get_text_content(
            prompt=prompt,
            settings=execution_settings,
        )

        return response

    @override
    async def test_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str],
        kwargs: dict[str, Any],
    ) -> None:
        await self._test_helper(service_id, services, execution_settings_kwargs, inputs, False)

    @override
    async def test_streaming_completion(
        self,
        kernel: Kernel,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str],
        kwargs: dict[str, Any],
    ):
        if "streaming" in kwargs and not kwargs["streaming"]:
            pytest.skip("Skipping streaming test")

        await self._test_helper(service_id, services, execution_settings_kwargs, inputs, True)

    @override
    def evaluate(self, test_target: Any, **kwargs):
        print(test_target)
        if isinstance(test_target, TextContent):
            # Test is considered successful if the test_target is not empty
            assert test_target.text, "Error: Empty test target"
            return
        raise AssertionError(f"Unexpected output: {test_target}, type: {type(test_target)}")

    async def _test_helper(
        self,
        service_id: str,
        services: dict[str, tuple[ServiceType, type[PromptExecutionSettings]]],
        execution_settings_kwargs: dict[str, Any],
        inputs: list[str],
        stream: bool,
    ):
        service, settings_type = services[service_id]
        if not service:
            pytest.skip(f"Setup not ready for {service_id if service_id else 'None'}")
        for test_input in inputs:
            response = await retry(
                partial(
                    self.get_text_completion_response,
                    service=service,
                    execution_settings=settings_type(**execution_settings_kwargs),
                    prompt=test_input,
                    stream=stream,
                ),
                retries=5,
                name="text completions",
            )
            self.evaluate(response)

    def _try_create_bedrock_text_completion_client(self, model_id: str) -> BedrockTextCompletion | None:
        try:
            return BedrockTextCompletion(model_id=model_id)
        except Exception as ex:
            from conftest import logger

            logger.warning(ex)
            # Returning None so that the test that uses this service will be skipped
            return None
