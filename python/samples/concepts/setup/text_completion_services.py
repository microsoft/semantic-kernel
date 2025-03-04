# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase


class Services(str, Enum):
    """Enum for supported text completion services.

    For service specific settings, refer to this documentation:
    https://github.com/microsoft/semantic-kernel/blob/main/python/samples/concepts/setup/ALL_SETTINGS.md
    """

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    GOOGLE_AI = "google_ai"
    HUGGING_FACE = "huggingface"
    OLLAMA = "ollama"
    ONNX = "onnx"
    VERTEX_AI = "vertex_ai"


def get_text_completion_service_and_request_settings(
    service_name: Services,
) -> tuple["TextCompletionClientBase", "PromptExecutionSettings"]:
    """Return service and request settings.

    Args:
        service_name (Services): The service name.
    """
    # Use lambdas or functions to delay instantiation
    text_services = {
        Services.OPENAI: lambda: get_openai_text_completion_service_and_request_settings(),
        Services.AZURE_OPENAI: lambda: get_azure_openai_text_completion_service_and_request_settings(),
        Services.BEDROCK: lambda: get_bedrock_text_completion_service_and_request_settings(),
        Services.GOOGLE_AI: lambda: get_google_ai_text_completion_service_and_request_settings(),
        Services.HUGGING_FACE: lambda: get_hugging_face_text_completion_service_and_request_settings(),
        Services.OLLAMA: lambda: get_ollama_text_completion_service_and_request_settings(),
        Services.ONNX: lambda: get_onnx_text_completion_service_and_request_settings(),
        Services.VERTEX_AI: lambda: get_vertex_ai_text_completion_service_and_request_settings(),
    }

    # Call the appropriate lambda or function based on the service name
    if service_name not in text_services:
        raise ValueError(f"Unsupported service name: {service_name}")
    return text_services[service_name]()


def get_openai_text_completion_service_and_request_settings() -> tuple[
    "TextCompletionClientBase", "PromptExecutionSettings"
]:
    """Return OpenAI text completion service and request settings.

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
    from semantic_kernel.connectors.ai.open_ai import OpenAITextCompletion, OpenAITextPromptExecutionSettings

    text_service = OpenAITextCompletion()
    request_settings = OpenAITextPromptExecutionSettings(max_tokens=20, temperature=0.7, top_p=0.8)

    return text_service, request_settings


def get_azure_openai_text_completion_service_and_request_settings() -> tuple[
    "TextCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Azure OpenAI text completion service and request settings.

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
    from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion, OpenAITextPromptExecutionSettings

    text_service = AzureTextCompletion()
    request_settings = OpenAITextPromptExecutionSettings()

    return text_service, request_settings


def get_bedrock_text_completion_service_and_request_settings() -> tuple[
    "TextCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Bedrock text completion service and request settings.

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
    from semantic_kernel.connectors.ai.bedrock import BedrockTextCompletion, BedrockTextPromptExecutionSettings

    text_service = BedrockTextCompletion(model_id="amazon.titan-text-premier-v1:0")
    request_settings = BedrockTextPromptExecutionSettings(
        # For model specific settings, specify them in the extension_data dictionary.
        # For example, for Cohere Command specific settings, refer to:
        # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-text.html
        extension_data={
            "temperature": 0.8,
            "maxTokenCount": 20,
        },
    )

    return text_service, request_settings


def get_google_ai_text_completion_service_and_request_settings() -> tuple[
    "TextCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Google AI text completion service and request settings.

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
        GoogleAITextCompletion,
        GoogleAITextPromptExecutionSettings,
    )

    text_service = GoogleAITextCompletion()
    request_settings = GoogleAITextPromptExecutionSettings()

    return text_service, request_settings


def get_hugging_face_text_completion_service_and_request_settings() -> tuple[
    "TextCompletionClientBase", "PromptExecutionSettings"
]:
    """Return HuggingFace text completion service and request settings.

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
    from semantic_kernel.connectors.ai.hugging_face import HuggingFacePromptExecutionSettings, HuggingFaceTextCompletion

    # Note this model is a demonstration model that outputs random text.
    text_service = HuggingFaceTextCompletion(ai_model_id="HuggingFaceM4/tiny-random-LlamaForCausalLM")
    request_settings = HuggingFacePromptExecutionSettings()

    return text_service, request_settings


def get_ollama_text_completion_service_and_request_settings() -> tuple[
    "TextCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Ollama text completion service and request settings.

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
    from semantic_kernel.connectors.ai.ollama import OllamaTextCompletion, OllamaTextPromptExecutionSettings

    text_service = OllamaTextCompletion()
    request_settings = OllamaTextPromptExecutionSettings(
        # For model specific settings, specify them in the options dictionary.
        # For more information on the available options, refer to the Ollama API documentation:
        # https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
        options={
            "temperature": 0.8,
        },
    )

    return text_service, request_settings


def get_onnx_text_completion_service_and_request_settings() -> tuple[
    "TextCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Onnx text completion service and request settings.

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
    from semantic_kernel.connectors.ai.onnx import (
        OnnxGenAIPromptExecutionSettings,
        OnnxGenAITextCompletion,
        ONNXTemplate,
    )

    text_service = OnnxGenAITextCompletion(
        ONNXTemplate.PHI3,
    )
    request_settings = OnnxGenAIPromptExecutionSettings()

    return text_service, request_settings


def get_vertex_ai_text_completion_service_and_request_settings() -> tuple[
    "TextCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Vertex AI text completion service and request settings.

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
        VertexAITextCompletion,
        VertexAITextPromptExecutionSettings,
    )

    text_service = VertexAITextCompletion()
    request_settings = VertexAITextPromptExecutionSettings()

    return text_service, request_settings
