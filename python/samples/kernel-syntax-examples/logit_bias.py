# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion
)


async def run_async():
    api_key_from_env, org_from_env = sk.openai_settings_from_dot_env()

    chat_completion = OpenAIChatCompletion(
        _model_id="gpt-3.5-turbo",
        api_key=api_key_from_env,
        org_id=org_from_env
    )

    keys = [
        3919, 626, 17201, 1300, 25782, 9800, 32016, 13571, 43582, 20189,
        1891, 10424, 9631, 16497, 12984, 20020, 24046, 13159, 805, 15817,
        5239, 2070, 13466, 32932, 8095, 1351, 25323
    ]

    settings = ChatRequestSettings()

    # Map each token in the keys list to a bias value from -100 (a potential ban) to 100 (exclusive selection)
    for key in keys:
        # For this example, each key is mapped to a value of -100
        settings.token_selection_biases[key] = -100

    print("Chat content:")
    print("------------------------")

    response = await chat_completion.complete_chat_async(
        messages=[
            ("Hi, I'm looking for some suggestions")
        ],
        **settings,
    )

    print(response)

    # message = response["choices"][0]["message"]["content"]

    response = await chat_completion.complete_chat_async(
        messages=[
            ("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?")
        ],
        **settings,
    )

    await run_async()


asyncio.run(run_async())
