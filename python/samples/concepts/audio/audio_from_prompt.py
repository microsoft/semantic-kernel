# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.audio.audio_player import AudioPlayer
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai import OpenAITextToAudio
from semantic_kernel.functions import KernelArguments

"""
This simple sample demonstrates how to use the AzureTextToAudio services
with a prompt and prompt rendering.

Resources required for this sample: An Azure Text to Speech deployment (e.g. tts).

Additional dependencies required for this sample:
- pyaudio: run `pip install pyaudio` or `uv pip install pyaudio` if you are using uv.
"""


async def main():
    kernel = Kernel()
    kernel.add_service(OpenAITextToAudio(service_id="tts"))

    result = await kernel.invoke_prompt(
        prompt="speak the following phrase: {{$phrase}}",
        arguments=KernelArguments(
            phrase="a painting of a flower vase",
            settings=PromptExecutionSettings(service_id="tts", voice="coral"),
        ),
    )
    if result:
        AudioPlayer(audio_content=result.value[0]).play()


if __name__ == "__main__":
    asyncio.run(main())
