# Copyright (c) Microsoft. All rights reserved.

from pydantic import ValidationError

from samples.service_settings import ServiceSettings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureTextCompletion,
    OpenAIChatCompletion,
    OpenAITextCompletion,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def add_service(
    kernel: Kernel, use_chat: bool = True, env_file_path: str | None = None, env_file_encoding: str | None = None
) -> Kernel:
    """
    Configure the AI service for the kernel

    Args:
        kernel (Kernel): The kernel to configure
        use_chat (bool): Whether to use the chat completion model, or the text completion model
        env_file_path (str | None): The absolute or relative file path to the .env file.
        env_file_encoding (str | None): The desired type of encoding. Defaults to utf-8.

    Returns:
        Kernel: The configured kernel
    """
    try:
        settings = ServiceSettings(
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )
    except ValidationError as ex:
        raise ServiceInitializationError("Unable to configure learn resources settings.", ex) from ex

    if "global_llm_service" not in settings.model_fields_set:
        print("GLOBAL_LLM_SERVICE not set, trying to use Azure OpenAI.")

    # The service_id is used to identify the service in the kernel.
    # This can be updated to a custom value if needed.
    # It should match the execution setting's key in a config.json file.
    service_id = "default"

    # Configure AI service used by the kernel. Load settings from the .env file.
    if settings.global_llm_service == "OpenAI":
        if use_chat:
            # <OpenAIKernelCreation>
            kernel.add_service(OpenAIChatCompletion(service_id=service_id))
            # </OpenAIKernelCreation>
        else:
            # <OpenAITextCompletionKernelCreation>
            kernel.add_service(OpenAITextCompletion(service_id=service_id))
            # </OpenAITextCompletionKernelCreation>
    else:
        if use_chat:
            # <TypicalKernelCreation>
            kernel.add_service(AzureChatCompletion(service_id=service_id))
            # </TypicalKernelCreation>
        else:
            # <TextCompletionKernelCreation>
            kernel.add_service(AzureTextCompletion(service_id=service_id))
            # </TextCompletionKernelCreation>

    return kernel
