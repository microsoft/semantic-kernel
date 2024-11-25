# Copyright (c) Microsoft. All rights reserved.

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
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


def get_chat_completion_service_and_request_settings(
    service_name: str,
) -> tuple[ChatCompletionClientBase, PromptExecutionSettings]:
    """Return service and request settings."""
    chat_services = {
        "openai": get_openai_chat_completion_service_and_request_settings,
        "azure_openai": get_azure_openai_chat_completion_service_and_request_settings,
        "azure_ai_inference": get_azure_ai_inference_chat_completion_service_and_request_settings,
        "anthropic": get_anthropic_chat_completion_service_and_request_settings,
        "bedrock": get_bedrock_chat_completion_service_and_request_settings,
        "google_ai": get_google_ai_chat_completion_service_and_request_settings,
        "mistral_ai": get_mistral_ai_chat_completion_service_and_request_settings,
        "ollama": get_ollama_chat_completion_service_and_request_settings,
        "onnx": get_onnx_chat_completion_service_and_request_settings,
        "vertex_ai": get_vertex_ai_chat_completion_service_and_request_settings,
    }

    return chat_services[service_name]()


def get_openai_chat_completion_service_and_request_settings() -> tuple[
    OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
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
    chat_service = OpenAIChatCompletion()
    request_settings = OpenAIChatPromptExecutionSettings(max_tokens=2000, temperature=0.7, top_p=0.8)

    return chat_service, request_settings


def get_azure_openai_chat_completion_service_and_request_settings() -> tuple[
    AzureChatCompletion, AzureChatPromptExecutionSettings
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
    chat_service = AzureChatCompletion()
    request_settings = AzureChatPromptExecutionSettings()

    return chat_service, request_settings


def get_azure_ai_inference_chat_completion_service_and_request_settings() -> tuple[
    AzureAIInferenceChatCompletion, AzureAIInferenceChatPromptExecutionSettings
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
    chat_service = AzureAIInferenceChatCompletion(
        ai_model_id="id",  # The model ID is simply an identifier as the model id cannot be obtained programmatically.
    )
    request_settings = AzureAIInferenceChatPromptExecutionSettings()

    return chat_service, request_settings


def get_anthropic_chat_completion_service_and_request_settings() -> tuple[
    AnthropicChatCompletion, AnthropicChatPromptExecutionSettings
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
    chat_service = AnthropicChatCompletion()
    request_settings = AnthropicChatPromptExecutionSettings()

    return chat_service, request_settings


def get_bedrock_chat_completion_service_and_request_settings() -> tuple[
    BedrockChatCompletion, BedrockChatPromptExecutionSettings
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
    chat_service = BedrockChatCompletion(model_id="cohere.command-r-v1:0")
    request_settings = BedrockChatPromptExecutionSettings(
        # For model specific settings, specify them in the extension_data dictionary.
        # For example, for Cohere Command specific settings, refer to:
        # https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command-r-plus.html
        extension_data={
            "presence_penalty": 0.5,
            "seed": 5,
        },
    )

    return chat_service, request_settings


def get_google_ai_chat_completion_service_and_request_settings() -> tuple[
    GoogleAIChatCompletion, GoogleAIChatPromptExecutionSettings
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
    chat_service = GoogleAIChatCompletion()
    request_settings = GoogleAIChatPromptExecutionSettings()

    return chat_service, request_settings


def get_mistral_ai_chat_completion_service_and_request_settings() -> tuple[
    MistralAIChatCompletion, MistralAIChatPromptExecutionSettings
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
    chat_service = MistralAIChatCompletion()
    request_settings = MistralAIChatPromptExecutionSettings()

    return chat_service, request_settings


def get_ollama_chat_completion_service_and_request_settings() -> tuple[
    OllamaChatCompletion, OllamaChatPromptExecutionSettings
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
    chat_service = OllamaChatCompletion()
    request_settings = OllamaChatPromptExecutionSettings(
        # For model specific settings, specify them in the options dictionary.
        # For more information on the available options, refer to the Ollama API documentation:
        # https://github.com/ollama/ollama/blob/main/docs/modelfile.md#valid-parameters-and-values
        options={
            "temperature": 0.8,
        }
    )

    return chat_service, request_settings


def get_onnx_chat_completion_service_and_request_settings() -> tuple[
    OnnxGenAIChatCompletion, OnnxGenAIPromptExecutionSettings
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
    chat_service = OnnxGenAIChatCompletion(ONNXTemplate.PHI3)
    request_settings = OnnxGenAIPromptExecutionSettings()

    return chat_service, request_settings


def get_vertex_ai_chat_completion_service_and_request_settings() -> tuple[
    VertexAIChatCompletion, VertexAIChatPromptExecutionSettings
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
    chat_service = VertexAIChatCompletion()
    request_settings = VertexAIChatPromptExecutionSettings()

    return chat_service, request_settings
