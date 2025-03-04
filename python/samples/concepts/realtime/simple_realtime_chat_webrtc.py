# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from samples.concepts.realtime.utils import AudioPlayerWebRTC, AudioRecorderWebRTC, check_audio_devices
from semantic_kernel.connectors.ai.open_ai import (
    ListenEvents,
    OpenAIRealtimeExecutionSettings,
    OpenAIRealtimeWebRTC,
)

logging.basicConfig(level=logging.WARNING)
utils_log = logging.getLogger("samples.concepts.realtime.utils")
utils_log.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

"""
This simple sample demonstrates how to use the OpenAI Realtime API to create
a chat bot that can listen and respond directly through audio.
It requires installing:
- semantic-kernel[realtime]
- pyaudio
- sounddevice
- pydub
e.g. pip install pyaudio sounddevice pydub semantic_kernel[realtime]

For more details of the exact setup, see the README.md in the realtime folder.
"""

# The characteristics of your speaker and microphone are a big factor in a smooth conversation
# so you may need to try out different devices for each.
# you can also play around with the turn_detection settings to get the best results.
# It has device id's set in the AudioRecorderStream and AudioPlayerAsync classes,
# so you may need to adjust these for your system.
# you can disable the check for available devices by commenting the line below
check_audio_devices()


async def main() -> None:
    # create the realtime client and optionally add the audio output function, this is optional
    # you can define the protocol to use, either "websocket" or "webrtc"
    # they will behave the same way, even though the underlying protocol is quite different
    realtime_client = OpenAIRealtimeWebRTC(audio_track=AudioRecorderWebRTC())
    # Create the settings for the session
    settings = OpenAIRealtimeExecutionSettings(
        instructions="""
    You are a chat bot. Your name is Mosscap and
    you have one goal: figure out what people need.
    Your full name, should you need to know it, is
    Splendid Speckled Mosscap. You communicate
    effectively, but you tend to answer with long
    flowery prose.
    """,
        # there are different voices to choose from, since that list is bound to change, it is not checked beforehand,
        # see https://platform.openai.com/docs/api-reference/realtime-sessions/create#realtime-sessions-create-voice
        # for more details.
        voice="alloy",
    )
    audio_player = AudioPlayerWebRTC()
    # the context manager calls the create_session method on the client and starts listening to the audio stream
    async with audio_player, realtime_client(settings=settings, create_response=True):
        async for event in realtime_client.receive(audio_output_callback=audio_player.client_callback):
            match event.event_type:
                case "text":
                    # the model returns both audio and transcript of the audio, which we will print
                    print(event.text.text, end="")
                case "service":
                    # OpenAI Specific events
                    if event.service_type == ListenEvents.SESSION_UPDATED:
                        print("Session updated")
                    if event.service_type == ListenEvents.RESPONSE_CREATED:
                        print("\nMosscap (transcript): ", end="")


if __name__ == "__main__":
    print(
        "Instructions: The model will start speaking immediately,"
        "this can be turned off by removing `create_response=True` above."
        "The model will detect when you stop and automatically generate a response. "
        "Press ctrl + c to stop the program."
    )
    asyncio.run(main())
