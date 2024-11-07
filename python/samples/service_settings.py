# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class ServiceSettings(KernelBaseSettings):
    """The Learn Resources Service Settings.

    The settings are first loaded from environment variables. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8' as default or the specific encoding. If the settings are not found in the
    .env file, the settings are ignored; however, validation will fail alerting that the settings
    are missing.

    Args:
        global_llm_service (str | None): The LLM service to use for the samples, either "OpenAI" or "AzureOpenAI"
            If not provided, defaults to "AzureOpenAI".
    """

    global_llm_service: str | None = None
