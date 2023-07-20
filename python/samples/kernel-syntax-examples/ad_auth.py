# Copyright (c) Microsoft. All rights reserved.


import semantic_kernel as sk
from semantic_kernel.connectors.ai import ChatRequestSettings
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion


async def main():
    _, _, endpoint = sk.azure_openai_settings_from_dot_env(include_api_key=False)
    service = AzureChatCompletion("gpt-35-turbo", endpoint=endpoint, ad_auth="auto")
    request_settings = ChatRequestSettings(
        max_tokens=150,
        temperature=0.7,
        top_p=1,
        frequency_penalty=0.5,
        presence_penalty=0.5,
    )

    result = await service.complete_chat_stream_async(
        "What is the purpose of a rubber duck?", request_settings
    )

    async for text in result:
        print(text, end="")  # end = "" to avoid newlines


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
