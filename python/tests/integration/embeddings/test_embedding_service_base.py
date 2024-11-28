# Copyright (c) Microsoft. All rights reserved.

import pytest
from azure.ai.inference.aio import EmbeddingsClient
from azure.identity import DefaultAzureCredential
from openai import AsyncAzureOpenAI

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceEmbeddingPromptExecutionSettings,
    AzureAIInferenceTextEmbedding,
)
from semantic_kernel.connectors.ai.bedrock import BedrockEmbeddingPromptExecutionSettings, BedrockTextEmbedding
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.google.google_ai import (
    GoogleAIEmbeddingPromptExecutionSettings,
    GoogleAITextEmbedding,
)
from semantic_kernel.connectors.ai.google.vertex_ai import (
    VertexAIEmbeddingPromptExecutionSettings,
    VertexAITextEmbedding,
)
from semantic_kernel.connectors.ai.hugging_face import HuggingFaceTextEmbedding
from semantic_kernel.connectors.ai.mistral_ai import MistralAITextEmbedding
from semantic_kernel.connectors.ai.ollama import OllamaEmbeddingPromptExecutionSettings, OllamaTextEmbedding
from semantic_kernel.connectors.ai.open_ai import (
    AzureOpenAISettings,
    AzureTextEmbedding,
    OpenAIEmbeddingPromptExecutionSettings,
    OpenAITextEmbedding,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.utils.authentication.entra_id_authentication import get_entra_auth_token
from tests.utils import is_service_setup_for_testing, is_test_running_on_supported_platforms

# Make sure all services are setup for before running the tests
# The following exceptions apply:
# 1. OpenAI and Azure OpenAI services are always setup for testing.
# 2. The current Hugging Face service don't require any environment variables.
# 3. Bedrock services don't use API keys and model providers are tested individually,
#    so no environment variables are required.
mistral_ai_setup: bool = is_service_setup_for_testing(
    ["MISTRALAI_API_KEY", "MISTRALAI_EMBEDDING_MODEL_ID"], raise_if_not_set=False
)  # We don't have a MistralAI deployment
google_ai_setup: bool = is_service_setup_for_testing(["GOOGLE_AI_API_KEY", "GOOGLE_AI_EMBEDDING_MODEL_ID"])
vertex_ai_setup: bool = is_service_setup_for_testing(["VERTEX_AI_PROJECT_ID", "VERTEX_AI_EMBEDDING_MODEL_ID"])
ollama_setup: bool = is_service_setup_for_testing([
    "OLLAMA_EMBEDDING_MODEL_ID"
]) and is_test_running_on_supported_platforms(["Linux"])


class EmbeddingServiceTestBase:
    @pytest.fixture(scope="class")
    def services(self) -> dict[str, tuple[EmbeddingGeneratorBase, type[PromptExecutionSettings]]]:
        azure_openai_settings = AzureOpenAISettings.create()
        endpoint = azure_openai_settings.endpoint
        deployment_name = azure_openai_settings.embedding_deployment_name
        ad_token = get_entra_auth_token(azure_openai_settings.token_endpoint)
        api_version = azure_openai_settings.api_version
        azure_custom_client = AzureTextEmbedding(
            async_client=AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                azure_ad_token=ad_token,
                api_version=api_version,
                default_headers={"Test-User-X-ID": "test"},
            ),
        )
        azure_ai_inference_client = AzureAIInferenceTextEmbedding(
            ai_model_id=deployment_name,
            client=EmbeddingsClient(
                endpoint=f"{str(endpoint).strip('/')}/openai/deployments/{deployment_name}",
                credential=DefaultAzureCredential(),
                credential_scopes=["https://cognitiveservices.azure.com/.default"],
            ),
        )

        return {
            "openai": (OpenAITextEmbedding(), OpenAIEmbeddingPromptExecutionSettings),
            "azure": (AzureTextEmbedding(), OpenAIEmbeddingPromptExecutionSettings),
            "azure_custom_client": (azure_custom_client, OpenAIEmbeddingPromptExecutionSettings),
            "azure_ai_inference": (azure_ai_inference_client, AzureAIInferenceEmbeddingPromptExecutionSettings),
            "mistral_ai": (
                MistralAITextEmbedding() if mistral_ai_setup else None,
                PromptExecutionSettings,
            ),
            "hugging_face": (
                HuggingFaceTextEmbedding(ai_model_id="sentence-transformers/all-MiniLM-L6-v2"),
                PromptExecutionSettings,
            ),
            "ollama": (OllamaTextEmbedding() if ollama_setup else None, OllamaEmbeddingPromptExecutionSettings),
            "google_ai": (
                GoogleAITextEmbedding() if google_ai_setup else None,
                GoogleAIEmbeddingPromptExecutionSettings,
            ),
            "vertex_ai": (
                VertexAITextEmbedding() if vertex_ai_setup else None,
                VertexAIEmbeddingPromptExecutionSettings,
            ),
            "bedrock_amazon_titan-v1": (
                BedrockTextEmbedding(model_id="amazon.titan-embed-text-v1"),
                BedrockEmbeddingPromptExecutionSettings,
            ),
            "bedrock_amazon_titan-v2": (
                BedrockTextEmbedding(model_id="amazon.titan-embed-text-v2:0"),
                BedrockEmbeddingPromptExecutionSettings,
            ),
            "bedrock_cohere": (
                BedrockTextEmbedding(model_id="cohere.embed-english-v3"),
                BedrockEmbeddingPromptExecutionSettings,
            ),
        }
