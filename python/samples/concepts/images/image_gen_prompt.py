# Copyright (c) Microsoft. All rights reserved.

import asyncio
from urllib.request import urlopen

try:
    from PIL import Image

    pil_available = True
except ImportError:
    pil_available = False

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import OpenAITextToImage
from semantic_kernel.functions import KernelArguments

"""
This sample demonstrates how to use the OpenAI text-to-image service to generate an image from a prompt.
It uses the OpenAITextToImage class to create an image based on the provided prompt and settings.
The generated image is then displayed using the PIL library if available.
"""


async def main():
    kernel = Kernel()
    kernel.add_service(OpenAITextToImage(service_id="dalle3"))

    result = await kernel.invoke_prompt(
        prompt="Generate a image of {{$topic}} in the style of a {{$style}}",
        arguments=KernelArguments(
            topic="a flower vase",
            style="painting",
            settings=PromptExecutionSettings(
                service_id="dalle3",
                width=1024,
                height=1024,
                quality="hd",
                style="vivid",
            ),
        ),
    )
    if result and pil_available:
        img = Image.open(urlopen(str(result.value[0].uri)))  # nosec
        img.show()


if __name__ == "__main__":
    asyncio.run(main())
