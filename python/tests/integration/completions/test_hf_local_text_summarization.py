# Copyright (c) Microsoft. All rights reserved.

import asyncio

import e2e_text_completion
import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.hugging_face as sk_hf


@pytest.mark.asyncio
async def test_hf_local_summarization_service_with_skills():
    kernel = sk.Kernel()

    # Configure LLM service
    kernel.add_text_completion_service(
        "facebook/bart-large-cnn",
        sk_hf.HuggingFaceTextCompletion(
            "facebook/bart-large-cnn", task="summarization"
        ),
    )

    await e2e_text_completion.simple_summarization(kernel)


if __name__ == "__main__":
    asyncio.run(test_hf_local_summarization_service_with_skills())
