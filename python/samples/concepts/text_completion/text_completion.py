# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.text_completion_services import Services, get_text_completion_service_and_request_settings

"""
This sample shows how to perform text completion. This sample uses the following component:
- an text completion service: This component is responsible for generating text completions.
"""


# You can select from the following text embedding services:
# - Services.OPENAI
# - Services.AZURE_OPENAI
# - Services.BEDROCK
# - Services.GOOGLE_AI
# - Services.HUGGING_FACE
# - Services.OLLAMA
# - Services.ONNX
# - Services.VERTEX_AI
# Please make sure you have configured your environment correctly for the selected text embedding service.
text_completion_service, request_settings = get_text_completion_service_and_request_settings(Services.OPENAI)


async def main() -> None:
    completion = await text_completion_service.get_text_content(
        "A dog ran joyfully through the green field, chasing after",
        request_settings,
    )
    print(completion)

    """
    Sample output:
     a butterfly that fluttered just out of reach. His tongue hung out of his mouth as he p ...
    """


if __name__ == "__main__":
    asyncio.run(main())
