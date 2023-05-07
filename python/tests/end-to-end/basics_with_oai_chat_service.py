# Copyright (c) Microsoft. All rights reserved.

import asyncio

from utils import e2e_text_completion

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai

kernel = sk.Kernel()

# Load credentials from .env file

api_key, org_id = sk.openai_settings_from_dot_env()
kernel.add_chat_service(
    "chat-gpt", sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
)

asyncio.run(e2e_text_completion.summarize_function_test(kernel))
