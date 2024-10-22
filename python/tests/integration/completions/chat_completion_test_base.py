# Copyright (c) Microsoft. All rights reserved.


import platform
import sys
from functools import reduce
from typing import Annotated, Any

import pytest
from azure.ai.inference.aio import ChatCompletionsClient
from azure.identity import DefaultAzureCredential
from openai import AsyncAzureOpenAI

from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_chat_completion import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.bedrock_chat_completion import BedrockChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
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
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
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
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from tests.integration.completions.completion_test_base import CompletionTestBase, ServiceType
from tests.integration.completions.test_utils import is_service_setup_for_testing

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

# This can later also be simplified as map probably
mistral_ai_setup: bool = is_service_setup_for_testing("MISTRALAI_API_KEY")
ollama_setup: bool = is_service_setup_for_testing("OLLAMA_MODEL")
google_ai_setup: bool = is_service_setup_for_testing("GOOGLE_AI_API_KEY")
vertex_ai_setup: bool = is_service_setup_for_testing("VERTEX_AI_PROJECT_ID")
anthropic_setup: bool = is_service_setup_for_testing("ANTHROPIC_API_KEY")
onnx_setup: bool = is_service_setup_for_testing("ONNX_GEN_AI_CHAT_MODEL_FOLDER")

skip_on_mac_available = platform.system() == "Darwin"
if not skip_on_mac_available:
    from semantic_kernel.connectors.ai.onnx import OnnxGenAIChatCompletion, OnnxGenAIPromptExecutionSettings
    from semantic_kernel.connectors.ai.onnx.utils import ONNXTemplate


# A mock plugin that contains a function that returns a complex object.
class PersonDetails(KernelBaseModel):
    id: str
    name: str
    age: int


class PersonSearchPlugin:
    @kernel_function(name="SearchPerson", description="Search details of a person given their id.")
    def search_person(
        self, person_id: Annotated[str, "The person ID to search"]
    ) -> Annotated[PersonDetails, "The details of the person"]:
        return PersonDetails(id=person_id, name="John Doe", age=42)


class ChatCompletionTestBase(CompletionTestBase):
    """Base class for testing completion services."""

    @override
    @pytest.fixture(scope="class")
    def services(self) -> dict[str, tuple[ServiceType, type[PromptExecutionSettings]]]:
        azure_openai_settings = AzureOpenAISettings.create()
        endpoint = azure_openai_settings.endpoint
        deployment_name = azure_openai_settings.chat_deployment_name
        ad_token = azure_openai_settings.get_azure_openai_auth_token()
        api_version = azure_openai_settings.api_version
        azure_custom_client = AzureChatCompletion(
            async_client=AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                azure_ad_token=ad_token,
                api_version=api_version,
                default_headers={"Test-User-X-ID": "test"},
            ),
        )
        azure_ai_inference_client = AzureAIInferenceChatCompletion(
            ai_model_id=deployment_name,
            client=ChatCompletionsClient(
                endpoint=f'{str(endpoint).strip("/")}/openai/deployments/{deployment_name}',
                credential=DefaultAzureCredential(),
                credential_scopes=["https://cognitiveservices.azure.com/.default"],
                api_version=DEFAULT_AZURE_API_VERSION,
            ),
        )

        return {
            "openai": (OpenAIChatCompletion(), OpenAIChatPromptExecutionSettings),
            "azure": (AzureChatCompletion(), AzureChatPromptExecutionSettings),
            "azure_custom_client": (azure_custom_client, AzureChatPromptExecutionSettings),
            "azure_ai_inference": (azure_ai_inference_client, AzureAIInferenceChatPromptExecutionSettings),
            "mistral_ai": (
                MistralAIChatCompletion() if mistral_ai_setup else None,
                MistralAIChatPromptExecutionSettings,
            ),
            "ollama": (OllamaChatCompletion() if ollama_setup else None, OllamaChatPromptExecutionSettings),
            "google_ai": (GoogleAIChatCompletion() if google_ai_setup else None, GoogleAIChatPromptExecutionSettings),
            "vertex_ai": (VertexAIChatCompletion() if vertex_ai_setup else None, VertexAIChatPromptExecutionSettings),
            "onnx_gen_ai": (
                OnnxGenAIChatCompletion(template=ONNXTemplate.PHI3V) if onnx_setup else None,
                OnnxGenAIPromptExecutionSettings if not skip_on_mac_available else None,
            ),
            "bedrock_amazon_titan": (
                BedrockChatCompletion(model_id="amazon.titan-text-premier-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_ai21labs": (
                BedrockChatCompletion(model_id="ai21.jamba-1-5-mini-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_anthropic_claude": (
                BedrockChatCompletion(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_cohere_command": (
                BedrockChatCompletion(model_id="cohere.command-r-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_meta_llama": (
                BedrockChatCompletion(model_id="meta.llama3-70b-instruct-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_mistralai": (
                BedrockChatCompletion(model_id="mistral.mistral-small-2402-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
        }

    def setup(self, kernel: Kernel):
        """Setup the kernel with the completion service and function."""
        kernel.add_plugin(MathPlugin(), plugin_name="math")
        kernel.add_plugin(PersonSearchPlugin(), plugin_name="search")

    async def get_chat_completion_response(
        self,
        kernel: Kernel,
        service: ChatCompletionClientBase,
        execution_settings: PromptExecutionSettings,
        chat_history: ChatHistory,
        stream: bool,
    ) -> Any:
        """Get response from the service

        Args:
            kernel (Kernel): Kernel instance.
            service (ChatCompletionClientBase): Chat completion service.
            execution_settings (PromptExecutionSettings): Execution settings.
            input (str): Input string.
            stream (bool): Stream flag.
        """
        if stream:
            response = service.get_streaming_chat_message_content(
                chat_history,
                execution_settings,
                kernel=kernel,
            )
            parts = [part async for part in response]
            if parts:
                response = reduce(lambda p, r: p + r, parts)
            else:
                raise AssertionError("No response")
        else:
            response = await service.get_chat_message_content(
                chat_history,
                execution_settings,
                kernel=kernel,
            )

        return response
