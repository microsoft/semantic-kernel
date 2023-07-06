from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion
)
import semantic_kernel as sk


async def run_async():
    apikey = sk.openai_settings_from_dot_env()

    chat_completion = OpenAIChatCompletion(
        _model_id="gpt-3.5-turbo",
        api_key=apikey
    )

    keys = [
        3919, 626, 17201, 1300, 25782, 9800, 32016, 13571, 43582, 20189,
        1891, 10424, 9631, 16497, 12984, 20020, 24046, 13159, 805, 15817,
        5239, 2070, 13466, 32932, 8095, 1351, 25323
    ]

    settings = ChatRequestSettings()

    for key in keys:
        settings.token_selection_biases[key] = -100

    print("Chat content:")
    print("------------------------")

    response = await chat_completion._send_chat_request(
        messages=[
            ("Hi, I'm looking for some suggestions")
        ],
        **settings,
        stream=True
    )

    print(response)

    # message = response["choices"][0]["message"]["content"]

    response = await chat_completion.send_message(
        messages=[
            ("I love history and philosophy, I'd like to learn something new about Greece, any suggestion?")
        ],
        **settings,
        stream=True
    )

    await run_async()
