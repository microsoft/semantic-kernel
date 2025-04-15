# Copyright (c) Microsoft. All rights reserved.


import os
import sys
from typing import Annotated

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import pytest
from azure.ai.inference.aio import ChatCompletionsClient
from azure.identity import DefaultAzureCredential
from openai import AsyncAzureOpenAI

from semantic_kernel.connectors.ai.anthropic import AnthropicChatCompletion, AnthropicChatPromptExecutionSettings
from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatCompletion,
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.bedrock import BedrockChatCompletion, BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.google.google_ai import GoogleAIChatCompletion, GoogleAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.google.vertex_ai import VertexAIChatCompletion, VertexAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.mistral_ai import MistralAIChatCompletion, MistralAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion, OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.onnx import OnnxGenAIChatCompletion, OnnxGenAIPromptExecutionSettings, ONNXTemplate
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
    AzureOpenAISettings,
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.authentication.entra_id_authentication import get_entra_auth_token
from tests.integration.completions.completion_test_base import CompletionTestBase, ServiceType
from tests.utils import is_service_setup_for_testing

# Make sure all services are setup for before running the tests
# The following exceptions apply:
# 1. OpenAI and Azure OpenAI services are always setup for testing.
azure_openai_setup: bool = True
# 2. Bedrock services don't use API keys and model providers are tested individually,
#    so no environment variables are required.
mistral_ai_setup: bool = is_service_setup_for_testing(
    ["MISTRALAI_API_KEY", "MISTRALAI_CHAT_MODEL_ID"], raise_if_not_set=False
)  # We don't have a MistralAI deployment
# There is no single model in Ollama that supports both image and tool call in chat completion
# We are splitting the Ollama test into three services: chat, image, and tool call. The chat model
# can be any model that supports chat completion. Also, Ollama is only available on Linux runners in our pipeline.
ollama_setup: bool = is_service_setup_for_testing(["OLLAMA_CHAT_MODEL_ID"])
ollama_image_setup: bool = is_service_setup_for_testing(["OLLAMA_CHAT_MODEL_ID_IMAGE"])
ollama_tool_call_setup: bool = is_service_setup_for_testing(["OLLAMA_CHAT_MODEL_ID_TOOL_CALL"])
google_ai_setup: bool = is_service_setup_for_testing(["GOOGLE_AI_API_KEY", "GOOGLE_AI_GEMINI_MODEL_ID"])
vertex_ai_setup: bool = is_service_setup_for_testing(["VERTEX_AI_PROJECT_ID", "VERTEX_AI_GEMINI_MODEL_ID"])
onnx_setup: bool = is_service_setup_for_testing(
    ["ONNX_GEN_AI_CHAT_MODEL_FOLDER"], raise_if_not_set=False
)  # Tests are optional for ONNX
anthropic_setup: bool = is_service_setup_for_testing(["ANTHROPIC_API_KEY", "ANTHROPIC_CHAT_MODEL_ID"])


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
    @pytest.fixture(
        scope="function"
    )  # This needs to be scoped to function to avoid resources getting cleaned up after each test
    def services(self) -> dict[str, tuple[ServiceType | None, type[PromptExecutionSettings] | None]]:
        azure_openai_setup = True
        azure_openai_settings = AzureOpenAISettings()
        endpoint = str(azure_openai_settings.endpoint)
        deployment_name = azure_openai_settings.chat_deployment_name
        ad_token = get_entra_auth_token(azure_openai_settings.token_endpoint)
        if not ad_token:
            azure_openai_setup = False
        api_version = azure_openai_settings.api_version
        azure_custom_client = None
        azure_ai_inference_client = None
        if azure_openai_setup:
            azure_custom_client = AzureChatCompletion(
                async_client=AsyncAzureOpenAI(
                    azure_endpoint=endpoint,
                    azure_deployment=deployment_name,
                    azure_ad_token=ad_token,
                    api_version=api_version,
                    default_headers={"Test-User-X-ID": "test"},
                ),
            )
            assert deployment_name
            azure_ai_inference_client = AzureAIInferenceChatCompletion(
                ai_model_id=deployment_name,
                client=ChatCompletionsClient(
                    endpoint=f"{endpoint.strip('/')}/openai/deployments/{deployment_name}",
                    credential=DefaultAzureCredential(),  # type: ignore
                    credential_scopes=["https://cognitiveservices.azure.com/.default"],
                ),
            )

        return {
            "openai": (OpenAIChatCompletion(), OpenAIChatPromptExecutionSettings),
            "azure": (AzureChatCompletion() if azure_openai_setup else None, AzureChatPromptExecutionSettings),
            "azure_custom_client": (azure_custom_client, AzureChatPromptExecutionSettings),
            "azure_ai_inference": (azure_ai_inference_client, AzureAIInferenceChatPromptExecutionSettings),
            "anthropic": (AnthropicChatCompletion() if anthropic_setup else None, AnthropicChatPromptExecutionSettings),
            "mistral_ai": (
                MistralAIChatCompletion() if mistral_ai_setup else None,
                MistralAIChatPromptExecutionSettings,
            ),
            "ollama": (OllamaChatCompletion() if ollama_setup else None, OllamaChatPromptExecutionSettings),
            "ollama_image": (
                OllamaChatCompletion(ai_model_id=os.environ["OLLAMA_CHAT_MODEL_ID_IMAGE"])
                if ollama_image_setup
                else None,
                OllamaChatPromptExecutionSettings,
            ),
            "ollama_tool_call": (
                OllamaChatCompletion(ai_model_id=os.environ["OLLAMA_CHAT_MODEL_ID_TOOL_CALL"])
                if ollama_tool_call_setup
                else None,
                OllamaChatPromptExecutionSettings,
            ),
            "google_ai": (GoogleAIChatCompletion() if google_ai_setup else None, GoogleAIChatPromptExecutionSettings),
            "vertex_ai": (VertexAIChatCompletion() if vertex_ai_setup else None, VertexAIChatPromptExecutionSettings),
            "onnx_gen_ai": (
                OnnxGenAIChatCompletion(template=ONNXTemplate.PHI3V) if onnx_setup else None,
                OnnxGenAIPromptExecutionSettings,
            ),
            "bedrock_amazon_titan": (
                self._try_create_bedrock_chat_completion_client("amazon.titan-text-premier-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_ai21labs": (
                self._try_create_bedrock_chat_completion_client("ai21.jamba-1-5-mini-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_anthropic_claude": (
                self._try_create_bedrock_chat_completion_client("anthropic.claude-3-sonnet-20240229-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_cohere_command": (
                self._try_create_bedrock_chat_completion_client("cohere.command-r-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_meta_llama": (
                self._try_create_bedrock_chat_completion_client("meta.llama3-70b-instruct-v1:0"),
                BedrockChatPromptExecutionSettings,
            ),
            "bedrock_mistralai": (
                self._try_create_bedrock_chat_completion_client("mistral.mistral-small-2402-v1:0"),
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
        service: ServiceType,
        execution_settings: PromptExecutionSettings,
        chat_history: ChatHistory,
        stream: bool,
    ) -> ChatMessageContent | StreamingChatMessageContent | None:
        """Get response from the service

        Args:
            kernel (Kernel): Kernel instance.
            service (ChatCompletionClientBase): Chat completion service.
            execution_settings (PromptExecutionSettings): Execution settings.
            input (str): Input string.
            stream (bool): Stream flag.
        """
        assert isinstance(service, ChatCompletionClientBase)
        if not stream:
            return await service.get_chat_message_content(
                chat_history,
                execution_settings,
                kernel=kernel,
            )
        parts: list[StreamingChatMessageContent] = [
            part
            async for part in service.get_streaming_chat_message_content(
                chat_history,
                execution_settings,
                kernel=kernel,
            )
            if part
        ]
        if parts:
            return sum(parts[1:], parts[0])
        raise AssertionError("No response")

    def _try_create_bedrock_chat_completion_client(self, model_id: str) -> BedrockChatCompletion | None:
        try:
            return BedrockChatCompletion(model_id=model_id)
        except Exception as ex:
            from conftest import logger

            logger.warning(ex)
            # Returning None so that the test that uses this service will be skipped
            return None
