# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class Services(str, Enum):
    """Enum for supported embedding services.

    For service specific settings, refer to this documentation:
    https://github.com/microsoft/semantic-kernel/blob/main/python/samples/concepts/setup/ALL_SETTINGS.md
    """

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    AZURE_AI_INFERENCE = "azure_ai_inference"
    BEDROCK = "bedrock"
    GOOGLE_AI = "google_ai"
    HUGGING_FACE = "huggingface"
    MISTRAL_AI = "mistral_ai"
    OLLAMA = "ollama"
    VERTEX_AI = "vertex_ai"


def get_text_embedding_service_and_request_settings(
    service_name: Services,
) -> tuple["EmbeddingGeneratorBase", "PromptExecutionSettings"]:
    """Returns the embedding service and request settings for the given service name.

    Args:
        service_name (Services): The service name.

    Returns:
        Tuple[EmbeddingGeneratorBase, PromptExecutionSettings]: The embedding service and request settings.
    """
    # Use lambdas to delay instantiation of the services until needed.
    embedding_services = {
        Services.OPENAI: lambda: get_openai_text_embedding_service_and_request_settings(),
        Services.AZURE_OPENAI: lambda: get_azure_openai_text_embedding_service_and_request_settings(),
        Services.AZURE_AI_INFERENCE: lambda: get_azure_ai_inference_text_embedding_service_and_request_settings(),
        Services.BEDROCK: lambda: get_bedrock_text_embedding_service_and_request_settings(),
        Services.GOOGLE_AI: lambda: get_google_ai_text_embedding_service_and_request_settings(),
        Services.HUGGING_FACE: lambda: get_hugging_face_text_embedding_service_and_request_settings(),
        Services.MISTRAL_AI: lambda: get_mistral_ai_text_embedding_service_and_request_settings(),
        Services.OLLAMA: lambda: get_ollama_text_embedding_service_and_request_settings(),
        Services.VERTEX_AI: lambda: get_vertex_ai_text_embedding_service_and_request_settings(),
    }

    # Call the appropriate lambda or function based on the service name
    if service_name not in embedding_services:
        raise ValueError(f"Unsupported service name: {service_name}")
    return embedding_services[service_name]()


def get_openai_text_embedding_service_and_request_settings() -> tuple[
    "EmbeddingGeneratorBase", "PromptExecutionSettings"
]:
    """Return OpenAI embedding service and request settings.

    The service credentials can be read by 3 ways:
    1. Via the constructor
    2. Via the environment variables
    3. Via an environment file

    The request settings control the behavior of the service. The default settings are sufficient to get started.
    However, you can adjust the settings to suit your needs.
    Note: Some of the settings are NOT meant to be set by the user.
    Please refer to the Semantic Kernel Python documentation for more information:
    https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel-python
    """
    from semantic_kernel.connectors.ai.open_ai import OpenAIEmbeddingPromptExecutionSettings, OpenAITextEmbedding

    embedding_service = OpenAITextEmbedding(ai_model_id="text-embedding-3-large")
    # Note: not all models support specifying the dimensions or there may be constraints on the dimensions
    request_settings = OpenAIEmbeddingPromptExecutionSettings(dimensions=3072)

    return embedding_service, request_settings


def get_azure_openai_text_embedding_service_and_request_settings() -> tuple[
    "EmbeddingGeneratorBase", "PromptExecutionSettings"
]:
    """Return Azure OpenAI embedding service and request settings.

    The service credentials can be read by 3 ways:
    1. Via the constructor
    2. Via the environment variables
    3. Via an environment file

    The request settings control the behavior of the service. The default settings are sufficient to get started.
    However, you can adjust the settings to suit your needs.
    Note: Some of the settings are NOT meant to be set by the user.
    Please refer to the Semantic Kernel Python documentation for more information:
    https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel-python
    """
    from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding, OpenAIEmbeddingPromptExecutionSettings

    embedding_service = AzureTextEmbedding(deployment_name="text-embedding-3-large")
    # Note: not all models support specifying the dimensions or there may be constraints on the dimensions
    request_settings = OpenAIEmbeddingPromptExecutionSettings(dimensions=3072)

    return embedding_service, request_settings


def get_azure_ai_inference_text_embedding_service_and_request_settings() -> tuple[
    "EmbeddingGeneratorBase", "PromptExecutionSettings"
]:
    """Return Azure AI Inference embedding service and request settings.

    The service credentials can be read by 3 ways:
    1. Via the constructor
    2. Via the environment variables
    3. Via an environment file

    The request settings control the behavior of the service. The default settings are sufficient to get started.
    However, you can adjust the settings to suit your needs.
    Note: Some of the settings are NOT meant to be set by the user.
    Please refer to the Semantic Kernel Python documentation for more information:
    https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel
    """
    from semantic_kernel.connectors.ai.azure_ai_inference import (
        AzureAIInferenceEmbeddingPromptExecutionSettings,
        AzureAIInferenceTextEmbedding,
    )

    # The AI model ID is used as an identifier for developers when they are using serverless endpoints
    # on AI Foundry. It is not actually used to identify the model in the service as the endpoint points
    # to only one model.
    # When developers are using one endpoint that can route to multiple models, the `ai_model_id` will be
    # used to identify the model. To use the latest routing feature on AI Foundry, please refer to the
    # following documentation:
    # https://learn.microsoft.com/en-us/azure/ai-services/multi-service-resource?%3Fcontext=%2Fazure%2Fai-services%2Fmodel-inference%2Fcontext%2Fcontext&pivots=azportal
    # https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/how-to/configure-project-connection?pivots=ai-foundry-portal
    # https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/how-to/inference?tabs=python

    embedding_service = AzureAIInferenceTextEmbedding(ai_model_id="id")
    # Note: not all models support specifying the dimensions or there may be constraints on the dimensions
    request_settings = AzureAIInferenceEmbeddingPromptExecutionSettings(dimensions=1024)

    return embedding_service, request_settings


def get_bedrock_text_embedding_service_and_request_settings() -> tuple[
    "EmbeddingGeneratorBase", "PromptExecutionSettings"
]:
    """Return Bedrock embedding service and request settings.

    The service credentials can be read by 3 ways:
    1. Via the constructor
    2. Via the environment variables
    3. Via an environment file

    The request settings control the behavior of the service. The default settings are sufficient to get started.
    However, you can adjust the settings to suit your needs.
    Note: Some of the settings are NOT meant to be set by the user.
    Please refer to the Semantic Kernel Python documentation for more information:
    https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel
    """
    from semantic_kernel.connectors.ai.bedrock import BedrockEmbeddingPromptExecutionSettings, BedrockTextEmbedding

    embedding_service = BedrockTextEmbedding(model_id="amazon.titan-embed-text-v2:0")
    request_settings = BedrockEmbeddingPromptExecutionSettings(
        # For model specific settings, specify them in the extension_data dictionary.
        # For example, for Cohere Command specific settings, refer to:
        # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-embed-text.html
        extension_data={"dimensions": 256},
    )

    return embedding_service, request_settings


def get_hugging_face_text_embedding_service_and_request_settings() -> tuple[
    "EmbeddingGeneratorBase", "PromptExecutionSettings"
]:
    """Return HuggingFace text embedding service and request settings.

    The service credentials can be read by 3 ways:
    1. Via the constructor
    2. Via the environment variables
    3. Via an environment file

    The request settings control the behavior of the service. The default settings are sufficient to get started.
    However, you can adjust the settings to suit your needs.
    Note: Some of the settings are NOT meant to be set by the user.
    Please refer to the Semantic Kernel Python documentation for more information:
    https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel
    """
    from semantic_kernel.connectors.ai.hugging_face import HuggingFacePromptExecutionSettings, HuggingFaceTextEmbedding

    embedding_service = HuggingFaceTextEmbedding(ai_model_id="sentence-transformers/all-MiniLM-L6-v2")
    request_settings = HuggingFacePromptExecutionSettings()

    return embedding_service, request_settings


def get_google_ai_text_embedding_service_and_request_settings() -> tuple[
    "EmbeddingGeneratorBase", "PromptExecutionSettings"
]:
    """Return Google AI text embedding service and request settings.

    The service credentials can be read by 3 ways:
    1. Via the constructor
    2. Via the environment variables
    3. Via an environment file

    The request settings control the behavior of the service. The default settings are sufficient to get started.
    However, you can adjust the settings to suit your needs.
    Note: Some of the settings are NOT meant to be set by the user.
    Please refer to the Semantic Kernel Python documentation for more information:
    https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel
    """
    from semantic_kernel.connectors.ai.google.google_ai import (
        GoogleAIEmbeddingPromptExecutionSettings,
        GoogleAITextEmbedding,
    )

    embedding_service = GoogleAITextEmbedding()
    # Note: not all models support specifying the dimensions or there may be constraints on the dimensions
    request_settings = GoogleAIEmbeddingPromptExecutionSettings(output_dimensionality=768)

    return embedding_service, request_settings


def get_mistral_ai_text_embedding_service_and_request_settings() -> tuple[
    "EmbeddingGeneratorBase", "PromptExecutionSettings"
]:
    """Return Mistral AI text embedding service and request settings.

    The service credentials can be read by 3 ways:
    1. Via the constructor
    2. Via the environment variables
    3. Via an environment file

    The request settings control the behavior of the service. The default settings are sufficient to get started.
    However, you can adjust the settings to suit your needs.
    Note: Some of the settings are NOT meant to be set by the user.
    Please refer to the Semantic Kernel Python documentation for more information:
    https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel
    """
    from semantic_kernel.connectors.ai.mistral_ai import MistralAIPromptExecutionSettings, MistralAITextEmbedding

    embedding_service = MistralAITextEmbedding()
    request_settings = MistralAIPromptExecutionSettings()

    return embedding_service, request_settings


def get_ollama_text_embedding_service_and_request_settings() -> tuple[
    "EmbeddingGeneratorBase", "PromptExecutionSettings"
]:
    """Return Ollama text embedding service and request settings.

    The service credentials can be read by 3 ways:
    1. Via the constructor
    2. Via the environment variables
    3. Via an environment file

    The request settings control the behavior of the service. The default settings are sufficient to get started.
    However, you can adjust the settings to suit your needs.
    Note: Some of the settings are NOT meant to be set by the user.
    Please refer to the Semantic Kernel Python documentation for more information:
    https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel
    """
    from semantic_kernel.connectors.ai.ollama import OllamaEmbeddingPromptExecutionSettings, OllamaTextEmbedding

    embedding_service = OllamaTextEmbedding()
    request_settings = OllamaEmbeddingPromptExecutionSettings(
        # For model specific settings, specify them in the options dictionary.
        # For more information on the available options, refer to the Ollama API documentation:
        # https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
        options={
            "temperature": 0.8,
        },
    )

    return embedding_service, request_settings


def get_vertex_ai_text_embedding_service_and_request_settings() -> tuple[
    "EmbeddingGeneratorBase", "PromptExecutionSettings"
]:
    """Return Vertex AI text embedding service and request settings.

    The service credentials can be read by 3 ways:
    1. Via the constructor
    2. Via the environment variables
    3. Via an environment file

    The request settings control the behavior of the service. The default settings are sufficient to get started.
    However, you can adjust the settings to suit your needs.
    Note: Some of the settings are NOT meant to be set by the user.
    Please refer to the Semantic Kernel Python documentation for more information:
    https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel
    """
    from semantic_kernel.connectors.ai.google.vertex_ai import (
        VertexAIEmbeddingPromptExecutionSettings,
        VertexAITextEmbedding,
    )

    embedding_service = VertexAITextEmbedding()
    # Note: not all models support specifying the dimensions or there may be constraints on the dimensions
    request_settings = VertexAIEmbeddingPromptExecutionSettings(output_dimensionality=768)

    return embedding_service, request_settings
