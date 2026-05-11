# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
from io import BytesIO

from semantic_kernel.prompt_template import PromptTemplateConfig

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
    service = OpenAITextToImage()
    kernel.add_service(service)
    kernel.add_service(OpenAIChatCompletion(service_id="default"))

    image_b64 = await service.generate_image(description="a painting of a flower vase", width=1024, height=1024)

    if pil_available:
        img = Image.open(BytesIO(base64.b64decode(image_b64)))
        img.show()

    result = await kernel.invoke_prompt(
        prompt="{{$chat_history}}",
        prompt_template_config=PromptTemplateConfig(allow_dangerously_set_content=True),
        arguments=KernelArguments(
            chat_history=ChatHistory(
                messages=[
                    ChatMessageContent(
                        role="user",
                        items=[
                            TextContent(text="What is in this image?"),
                            ImageContent(data=image_b64, data_format="base64", mime_type="image/png"),
                        ],
                    )
                ]
            )
        ),
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
