# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.google_palm as sk_gp
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)


async def text_completion_example_complete_async(kernel, api_key, user_mssg, settings):
    """
    Complete a text prompt using the Google PaLM model and print the results.
    """
    palm_text_completion = sk_gp.GooglePalmTextCompletion(
        "models/text-bison-001", api_key
    )
    kernel.add_text_completion_service("models/text-bison-001", palm_text_completion)
    answer = await palm_text_completion.complete_async(user_mssg, settings)
    return answer


async def main() -> None:
    kernel = sk.Kernel()
    apikey = sk.google_palm_settings_from_dot_env()
    settings = CompleteRequestSettings()

    user_mssg1 = (
        "Sam has three boxes, each containing a certain number of coins. "
        "The first box has twice as many coins as the second box, and the second "
        "box has three times as many coins as the third box. Together, the three "
        "boxes have 98 coins in total. How many coins are there in each box? "
        "Think about it step by step, and show your work."
    )
    response = await text_completion_example_complete_async(
        kernel, apikey, user_mssg1, settings
    )
    print(f"User:> {user_mssg1}\n\nChatBot:> {response}\n")
    # Use temperature to influence the variance of the responses
    settings.number_of_responses = 3
    settings.temperature = 1
    user_mssg2 = (
        "I need a concise answer. A common method for traversing a binary tree is"
    )
    response = await text_completion_example_complete_async(
        kernel, apikey, user_mssg2, settings
    )
    print(f"User:> {user_mssg2}\n\nChatBot:> {response}")
    return


if __name__ == "__main__":
    asyncio.run(main())
