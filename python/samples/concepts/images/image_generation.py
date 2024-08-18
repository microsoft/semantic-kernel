# Copyright (c) Microsoft. All rights reserved.

import asyncio
from urllib.request import urlopen

from PIL import Image

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAITextToImage


async def main():
    kernel = Kernel()
    dalle3 = OpenAITextToImage(ai_model_id="dall-e-3")
    kernel.add_service(dalle3)

    image = await dalle3.generate_image(
        description="a painting of a flower vase",
        width=1024,
        height=1024,
    )
    print(image)

    img = Image.open(urlopen(image))  # nosec
    img.show()


if __name__ == "__main__":
    asyncio.run(main())
