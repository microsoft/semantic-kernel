# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class Services(str, Enum):
    """Enum for supported chat completion services.

    For service specific settings, refer to this documentation:
    https://github.com/microsoft/semantic-kernel/blob/main/python/samples/concepts/setup/ALL_SETTINGS.md
    """

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    AZURE_AI_INFERENCE = "azure_ai_inference"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    GOOGLE_AI = "google_ai"
    MISTRAL_AI = "mistral_ai"
    OLLAMA = "ollama"
    ONNX = "onnx"
    VERTEX_AI = "vertex_ai"


service_id = "default"


def get_chat_completion_service_and_request_settings(
    service_name: Services,
) -> tuple["ChatCompletionClientBase", "PromptExecutionSettings"]:
    """Return service and request settings."""
    chat_services = {
        Services.OPENAI: get_openai_chat_completion_service_and_request_settings,
        Services.AZURE_OPENAI: get_azure_openai_chat_completion_service_and_request_settings,
        Services.AZURE_AI_INFERENCE: get_azure_ai_inference_chat_completion_service_and_request_settings,
        Services.ANTHROPIC: get_anthropic_chat_completion_service_and_request_settings,
        Services.BEDROCK: get_bedrock_chat_completion_service_and_request_settings,
        Services.GOOGLE_AI: get_google_ai_chat_completion_service_and_request_settings,
        Services.MISTRAL_AI: get_mistral_ai_chat_completion_service_and_request_settings,
        Services.OLLAMA: get_ollama_chat_completion_service_and_request_settings,
        Services.ONNX: get_onnx_chat_completion_service_and_request_settings,
        Services.VERTEX_AI: get_vertex_ai_chat_completion_service_and_request_settings,
    }
    return chat_services[service_name]()


def get_openai_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return OpenAI chat completion service and request settings.

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
    from semantic_kernel.connectors.ai.open_ai import (
        OpenAIChatCompletion,
        OpenAIChatPromptExecutionSettings,
    )

    chat_service = OpenAIChatCompletion(service_id=service_id)
    request_settings = OpenAIChatPromptExecutionSettings(
        service_id=service_id, max_tokens=2000, temperature=0.7, top_p=0.8
    )

    return chat_service, request_settings


def get_azure_openai_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Azure OpenAI chat completion service and request settings.

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
    from semantic_kernel.connectors.ai.open_ai import (
        AzureChatCompletion,
        AzureChatPromptExecutionSettings,
    )

    chat_service = AzureChatCompletion(service_id=service_id)
    request_settings = AzureChatPromptExecutionSettings(service_id=service_id)

    return chat_service, request_settings


def get_azure_ai_inference_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Azure AI Inference chat completion service and request settings.

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
        AzureAIInferenceChatCompletion,
        AzureAIInferenceChatPromptExecutionSettings,
    )

    chat_service = AzureAIInferenceChatCompletion(
        service_id=service_id,
        ai_model_id="id",  # The model ID is simply an identifier as the model id cannot be obtained programmatically.
    )
    request_settings = AzureAIInferenceChatPromptExecutionSettings(service_id=service_id)

    return chat_service, request_settings


def get_anthropic_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Anthropic chat completion service and request settings.

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
    from semantic_kernel.connectors.ai.anthropic import AnthropicChatCompletion, AnthropicChatPromptExecutionSettings

    chat_service = AnthropicChatCompletion(service_id=service_id)
    request_settings = AnthropicChatPromptExecutionSettings(service_id=service_id)

    return chat_service, request_settings


def get_bedrock_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Anthropic chat completion service and request settings.

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
    from semantic_kernel.connectors.ai.bedrock import BedrockChatCompletion, BedrockChatPromptExecutionSettings

    chat_service = BedrockChatCompletion(service_id=service_id, model_id="cohere.command-r-v1:0")
    request_settings = BedrockChatPromptExecutionSettings(
        # For model specific settings, specify them in the extension_data dictionary.
        # For example, for Cohere Command specific settings, refer to:
        # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command-r-plus.html
        service_id=service_id,
        extension_data={
            "presence_penalty": 0.5,
            "seed": 5,
        },
    )

    return chat_service, request_settings


def get_google_ai_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Google AI chat completion service and request settings.

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
        GoogleAIChatCompletion,
        GoogleAIChatPromptExecutionSettings,
    )

    chat_service = GoogleAIChatCompletion(service_id=service_id)
    request_settings = GoogleAIChatPromptExecutionSettings(service_id=service_id)

    return chat_service, request_settings


def get_mistral_ai_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Mistral AI chat completion service and request settings.

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
    from semantic_kernel.connectors.ai.mistral_ai import MistralAIChatCompletion, MistralAIChatPromptExecutionSettings

    chat_service = MistralAIChatCompletion(service_id=service_id)
    request_settings = MistralAIChatPromptExecutionSettings(service_id=service_id)

    return chat_service, request_settings


def get_ollama_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Ollama chat completion service and request settings.

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
    from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion, OllamaChatPromptExecutionSettings

    chat_service = OllamaChatCompletion(service_id=service_id)
    request_settings = OllamaChatPromptExecutionSettings(
        # For model specific settings, specify them in the options dictionary.
        # For more information on the available options, refer to the Ollama API documentation:
        # https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
        service_id=service_id,
        options={
            "temperature": 0.8,
        },
    )

    return chat_service, request_settings


def get_onnx_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Onnx chat completion service and request settings.

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
        OnnxGenAIChatCompletion,
        OnnxGenAIPromptExecutionSettings,
        ONNXTemplate,
    )

    chat_service = OnnxGenAIChatCompletion(ONNXTemplate.PHI3, service_id=service_id)
    request_settings = OnnxGenAIPromptExecutionSettings(service_id=service_id)

    return chat_service, request_settings


def get_vertex_ai_chat_completion_service_and_request_settings() -> tuple[
    "ChatCompletionClientBase", "PromptExecutionSettings"
]:
    """Return Vertex AI chat completion service and request settings.

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
        VertexAIChatCompletion,
        VertexAIChatPromptExecutionSettings,
    )

    chat_service = VertexAIChatCompletion(service_id=service_id)
    request_settings = VertexAIChatPromptExecutionSettings(service_id=service_id)

    return chat_service, request_settings
