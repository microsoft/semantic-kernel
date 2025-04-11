# Copyright (c) Microsoft. All rights reserved.

from importlib import util

import pytest
from azure.ai.inference.aio import EmbeddingsClient
from azure.identity import DefaultAzureCredential
from openai import AsyncAzureOpenAI

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceEmbeddingPromptExecutionSettings,
    AzureAIInferenceTextEmbedding,
)
from semantic_kernel.connectors.ai.bedrock import BedrockEmbeddingPromptExecutionSettings, BedrockTextEmbedding
from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
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
from tests.utils import is_service_setup_for_testing

hugging_face_setup = util.find_spec("torch") is not None

# Make sure all services are setup for before running the tests
# The following exceptions apply:
# 1. OpenAI and Azure OpenAI services are always setup for testing.
azure_openai_setup = True
# 2. The current Hugging Face service don't require any environment variables.
# 3. Bedrock services don't use API keys and model providers are tested individually,
#    so no environment variables are required.
mistral_ai_setup: bool = is_service_setup_for_testing(
    ["MISTRALAI_API_KEY", "MISTRALAI_EMBEDDING_MODEL_ID"], raise_if_not_set=False
)  # We don't have a MistralAI deployment
google_ai_setup: bool = is_service_setup_for_testing(["GOOGLE_AI_API_KEY", "GOOGLE_AI_EMBEDDING_MODEL_ID"])
vertex_ai_setup: bool = is_service_setup_for_testing(["VERTEX_AI_PROJECT_ID", "VERTEX_AI_EMBEDDING_MODEL_ID"])
ollama_setup: bool = is_service_setup_for_testing(["OLLAMA_EMBEDDING_MODEL_ID"])
# When testing Bedrock, after logging into AWS CLI this has been set, so we can use it to check if the service is setup
bedrock_setup: bool = is_service_setup_for_testing(["AWS_DEFAULT_REGION"], raise_if_not_set=False)


class EmbeddingServiceTestBase:
    @pytest.fixture(scope="class")
    def services(self) -> dict[str, tuple[EmbeddingGeneratorBase | None, type[PromptExecutionSettings]]]:
        azure_openai_setup = True
        azure_openai_settings = AzureOpenAISettings()
        endpoint = str(azure_openai_settings.endpoint)
        deployment_name = azure_openai_settings.embedding_deployment_name
        ad_token = get_entra_auth_token(azure_openai_settings.token_endpoint)
        if not ad_token:
            azure_openai_setup = False
        api_version = azure_openai_settings.api_version
        azure_custom_client = None
        azure_ai_inference_client = None
        if azure_openai_setup:
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
                    endpoint=f"{endpoint.strip('/')}/openai/deployments/{deployment_name}",
                    credential=DefaultAzureCredential(),
                    credential_scopes=["https://cognitiveservices.azure.com/.default"],
                ),
            )

        return {
            "openai": (OpenAITextEmbedding(), OpenAIEmbeddingPromptExecutionSettings),
            "azure": (AzureTextEmbedding() if azure_openai_setup else None, OpenAIEmbeddingPromptExecutionSettings),
            "azure_custom_client": (azure_custom_client, OpenAIEmbeddingPromptExecutionSettings),
            "azure_ai_inference": (azure_ai_inference_client, AzureAIInferenceEmbeddingPromptExecutionSettings),
            "mistral_ai": (
                MistralAITextEmbedding() if mistral_ai_setup else None,
                PromptExecutionSettings,
            ),
            "hugging_face": (
                HuggingFaceTextEmbedding(ai_model_id="sentence-transformers/all-MiniLM-L6-v2")
                if hugging_face_setup
                else None,
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
                BedrockTextEmbedding(model_id="amazon.titan-embed-text-v1") if bedrock_setup else None,
                BedrockEmbeddingPromptExecutionSettings,
            ),
            "bedrock_amazon_titan-v2": (
                BedrockTextEmbedding(model_id="amazon.titan-embed-text-v2:0") if bedrock_setup else None,
                BedrockEmbeddingPromptExecutionSettings,
            ),
            "bedrock_cohere": (
                BedrockTextEmbedding(model_id="cohere.embed-english-v3") if bedrock_setup else None,
                BedrockEmbeddingPromptExecutionSettings,
            ),
        }
