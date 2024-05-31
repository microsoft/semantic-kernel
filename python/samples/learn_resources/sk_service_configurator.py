# Copyright (c) Microsoft. All rights reserved.

from dotenv import dotenv_values

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureTextCompletion,
    OpenAIChatCompletion,
    OpenAITextCompletion,
)


def add_service(kernel: Kernel, use_chat: bool = True) -> Kernel:
    """
    Configure the AI service for the kernel

    Args:
        kernel (Kernel): The kernel to configure
        use_chat (bool): Whether to use the chat completion model, or the text completion model

    Returns:
        Kernel: The configured kernel
    """
    config = dotenv_values(".env")
    llm_service = config.get("GLOBAL_LLM_SERVICE", None)
    if not llm_service:
        print("GLOBAL_LLM_SERVICE not set, trying to use Azure OpenAI.")

    # The service_id is used to identify the service in the kernel.
    # This can be updated to a custom value if needed.
    # It should match the execution setting's key in a config.json file.
    service_id = "default"

    # Configure AI service used by the kernel. Load settings from the .env file.
    if llm_service == "OpenAI":
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
