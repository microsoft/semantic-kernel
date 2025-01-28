# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel.connectors.ai.open_ai import (
    OpenAIRealtime,
    OpenAIRealtimeExecutionSettings,
    TurnDetection,
)
from semantic_kernel.connectors.ai.utils import SKAudioPlayer

logging.basicConfig(level=logging.WARNING)
aiortc_log = logging.getLogger("aiortc")
aiortc_log.setLevel(logging.WARNING)
aioice_log = logging.getLogger("aioice")
aioice_log.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# This simple sample demonstrates how to use the OpenAI Realtime API to create
# a chat bot that can listen and respond directly through audio.
# It requires installing:
# - semantic-kernel[openai_realtime]
# - pyaudio
# - sounddevice
# - pydub
# - aiortc
# e.g. pip install pyaudio sounddevice pydub

# The characterics of your speaker and microphone are a big factor in a smooth conversation
# so you may need to try out different devices for each.
# you can also play around with the turn_detection settings to get the best results.
# It has device id's set in the AudioRecorderStream and AudioPlayerAsync classes,
# so you may need to adjust these for your system.
# you can check the available devices by uncommenting line below the function


def check_audio_devices():
    import sounddevice as sd

    logger.debug(sd.query_devices())


check_audio_devices()


async def main() -> None:
    # create the realtime client and optionally add the audio output function, this is optional
    # you can define the protocol to use, either "websocket" or "webrtc"
    # they will behave the same way, even though the underlying protocol is quite different
    realtime_client = OpenAIRealtime(protocol="webrtc")
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
        voice="alloy",
        turn_detection=TurnDetection(type="server_vad", create_response=True, silence_duration_ms=800, threshold=0.8),
    )
    # the context manager calls the create_session method on the client and start listening to the audio stream
    audio_player = SKAudioPlayer()
    async with realtime_client, audio_player:
        await realtime_client.update_session(settings=settings, create_response=True)
        async for event in realtime_client.start_streaming():
            match event.event_type:
                case "audio":
                    await audio_player.add_audio(event.audio)
                case "text":
                    print(event.text.text)
                case "service":
                    if event.service_type == "session.update":
                        print("Session updated")
                    if event.service_type == "error":
                        logger.error(event.event)


if __name__ == "__main__":
    print(
        "Instruction: start speaking, when you stop the API should detect you finished and start responding. "
        "Press ctrl + c to stop the program."
    )
    asyncio.run(main())
