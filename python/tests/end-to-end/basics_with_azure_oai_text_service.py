# Copyright (c) Microsoft. All rights reserved.

import asyncio

from utils import e2e_text_completion

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai

kernel = sk.Kernel()

# Load credentials from .env file
deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

# Configure LLM service
kernel.add_text_service(
    "davinci-003", sk_oai.AzureTextCompletion("text-davinci-003", endpoint, api_key)
)

asyncio.run(e2e_text_completion.summarize_function_test(kernel))
