# Copyright (c) Microsoft. All rights reserved.

from dotenv import dotenv_values

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureTextCompletion,
    OpenAIChatCompletion,
    OpenAITextCompletion,
)
from semantic_kernel.kernel import Kernel


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
    assert llm_service, "The LLM_SERVICE environment variable is not set."

    # The service_id is used to identify the service in the kernel.
    # This can be updated to a custom value if needed.
    # It should match the execution setting's key in a config.json file.
    service_id = "default"

    # Configure AI service used by the kernel. Load settings from the .env file.
    if llm_service == "AzureOpenAI":
        _, api_key, endpoint = sk.azure_openai_settings_from_dot_env(include_deployment=False)
        deployment_name = (config.get("AZURE_OPEN_AI_CHAT_COMPLETION_DEPLOYMENT_NAME") if use_chat 
                           else config.get("AZURE_OPEN_AI_TEXT_COMPLETION_DEPLOYMENT_NAME"))

        if not deployment_name:
            raise ValueError("Deployment name for Azure AI is not set in .env file.")

        if use_chat:
            kernel.add_service(
                AzureChatCompletion(
                    service_id=service_id,
                    deployment_name=deployment_name,
                    endpoint=endpoint,
                    api_key=api_key,
                ),
            )
        else:
            kernel.add_service(
                AzureTextCompletion(
                    service_id=service_id,
                    deployment_name=deployment_name,
                    endpoint=endpoint,
                    api_key=api_key,
                ),
            )
    else:
        api_key, org_id = sk.openai_settings_from_dot_env()
        model_id = (config.get("OPEN_AI_CHAT_COMPLETION_MODEL_ID") if use_chat 
                    else config.get("OPEN_AI_TEXT_COMPLETION_MODEL_ID"))

        if not model_id:
            raise ValueError("Model ID for OpenAI is not set in .env file.")
        
        if use_chat:
            kernel.add_service(
                OpenAIChatCompletion(
                    service_id=service_id,
                    ai_model_id=model_id,
                    api_key=api_key,
                    org_id=org_id,
                ),
            )
        else:
            kernel.add_service(
                OpenAITextCompletion(
                    service_id=service_id,
                    ai_model_id=model_id,
                    api_key=api_key,
                    org_id=org_id,
                ),
            )

    return kernel
