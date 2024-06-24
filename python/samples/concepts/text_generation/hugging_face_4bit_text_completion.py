# Copyright (c) Microsoft. All rights reserved.

import asyncio

import torch
from transformers import QuantoConfig

from semantic_kernel.connectors.ai.hugging_face import HuggingFacePromptExecutionSettings, HuggingFaceTextCompletion
from semantic_kernel.kernel import Kernel

kernel = Kernel()
ai_model_id = "microsoft/Phi-3-mini-128k-instruct"

# replace with the relevant quantization configuration for your setup and model
# see https://huggingface.co/docs/transformers/en/quantization
quantization_config = QuantoConfig(weights="int4")
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
hf_text_completion = HuggingFaceTextCompletion(
    ai_model_id=ai_model_id, model_kwargs={"quantization_config": quantization_config}, device=device
)
kernel.add_service(hf_text_completion)


async def text_completion_example_complete(kernel: Kernel, user_mssg, settings):
    """Complete a text prompt using the Google PaLM model and print the results."""
    return await hf_text_completion.get_text_contents(user_mssg, settings)


async def main() -> None:
    settings = HuggingFacePromptExecutionSettings()

    user_mssg1 = (
        "Sam has three boxes, each containing a certain number of coins. "
        "The first box has twice as many coins as the second box, and the second "
        "box has three times as many coins as the third box. Together, the three "
        "boxes have 98 coins in total. How many coins are there in each box? "
        "Think about it step by step, and show your work."
    )
    response = await text_completion_example_complete(kernel, user_mssg1, settings)
    print(f"User:> {user_mssg1}\n\nChatBot:> {response}\n")
    # Use temperature to influence the variance of the responses
    settings.num_return_sequences = 3
    settings.temperature = 1
    user_mssg2 = "I need a concise answer. A common method for traversing a binary tree is"
    response = await text_completion_example_complete(kernel, user_mssg2, settings)
    print(f"User:> {user_mssg2}\n\nChatBot:> {response}")
    return


if __name__ == "__main__":
    asyncio.run(main())
