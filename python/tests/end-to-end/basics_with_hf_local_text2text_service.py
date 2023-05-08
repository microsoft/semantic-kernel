# Copyright (c) Microsoft. All rights reserved.

import asyncio

from utils import e2e_text_completion

import semantic_kernel as sk
import semantic_kernel.connectors.ai.hugging_face as sk_hf

kernel = sk.Kernel()

# Configure LLM service
kernel.add_text_service(
    "google/flan-t5-base",
    sk_hf.HuggingFaceTextCompletion("google/flan-t5-base", task="text2text-generation"),
)

asyncio.run(e2e_text_completion.simple_completion(kernel))
