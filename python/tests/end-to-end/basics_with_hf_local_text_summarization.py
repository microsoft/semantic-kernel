# Copyright (c) Microsoft. All rights reserved.

import asyncio

from utils import e2e_text_completion

import semantic_kernel as sk
import semantic_kernel.connectors.ai.hugging_face as sk_hf

kernel = sk.Kernel()

# Configure LLM service
kernel.add_text_service(
    "facebook/bart-large-cnn",
    sk_hf.HuggingFaceTextCompletion("facebook/bart-large-cnn", task="summarization"),
)

asyncio.run(e2e_text_completion.simple_summarization(kernel))
