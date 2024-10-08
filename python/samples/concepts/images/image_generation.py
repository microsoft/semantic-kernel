# Copyright (c) Microsoft. All rights reserved.

import asyncio
from urllib.request import urlopen

try:
    from PIL import Image

    pil_available = True
except ImportError:
    pil_available = False

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAITextToImage
from semantic_kernel.contents import ChatHistory, ChatMessageContent, ImageContent, TextContent
from semantic_kernel.functions.kernel_arguments import KernelArguments


async def main():
    kernel = Kernel()
    dalle3 = OpenAITextToImage()
    kernel.add_service(dalle3)
    kernel.add_service(OpenAIChatCompletion(service_id="default"))

    image = await dalle3.generate_image(
        description="a painting of a flower vase", width=1024, height=1024, quality="hd", style="vivid"
    )
    print(image)
    if pil_available:
        img = Image.open(urlopen(image))  # nosec
        img.show()

    result = await kernel.invoke_prompt(
        prompt="{{$chat_history}}",
        arguments=KernelArguments(
            chat_history=ChatHistory(
                messages=[
                    ChatMessageContent(
                        role="user",
                        items=[
                            TextContent(text="What is in this image?"),
                            ImageContent(uri=image),
                        ],
                    )
                ]
            )
        ),
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
