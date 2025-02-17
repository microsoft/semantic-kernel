# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from samples.concepts.realtime.utils import AudioPlayerWebRTC, AudioRecorderWebRTC, check_audio_devices
from semantic_kernel.connectors.ai.open_ai import (
    ListenEvents,
    OpenAIRealtime,
    OpenAIRealtimeExecutionSettings,
    TurnDetection,
)
from semantic_kernel.contents.events.realtime_event import RealtimeTextEvent

logging.basicConfig(level=logging.WARNING)
utils_log = logging.getLogger("samples.concepts.realtime.utils")
utils_log.setLevel(logging.INFO)
aiortc_log = logging.getLogger("aiortc")
aiortc_log.setLevel(logging.WARNING)
aioice_log = logging.getLogger("aioice")
aioice_log.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# This simple sample demonstrates how to use the OpenAI Realtime API to create
# a chat bot that can listen and respond directly through audio.
# It requires installing:
# - semantic-kernel[realtime]
# - pyaudio
# - sounddevice
# - pydub
# e.g. pip install pyaudio sounddevice pydub semantic_kernel[realtime]

# The characterics of your speaker and microphone are a big factor in a smooth conversation
# so you may need to try out different devices for each.
# you can also play around with the turn_detection settings to get the best results.
# It has device id's set in the AudioRecorderStream and AudioPlayerAsync classes,
# so you may need to adjust these for your system.
# you can check the available devices by uncommenting line below the function
check_audio_devices()


async def main() -> None:
    # create the realtime client and optionally add the audio output function, this is optional
    # you can define the protocol to use, either "websocket" or "webrtc"
    # they will behave the same way, even though the underlying protocol is quite different
    audio_player = AudioPlayerWebRTC()
    realtime_client = OpenAIRealtime(
        "webrtc",
        audio_output_callback=audio_player.client_callback,
        audio_track=AudioRecorderWebRTC(),
    )
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
    async with audio_player, realtime_client(settings=settings, create_response=True):
        async for event in realtime_client.receive():
            match event.service_type:
                case RealtimeTextEvent():
                    print(event.text.text, end="")
                case _:
                    # OpenAI Specific events
                    if event.service_type == ListenEvents.SESSION_UPDATED:
                        print("Session updated")
                    if event.service_type == ListenEvents.RESPONSE_CREATED:
                        print("\nMosscap (transcript): ", end="")


if __name__ == "__main__":
    print(
        "Instruction: start speaking, when you stop the API should detect you finished and start responding. "
        "Press ctrl + c to stop the program."
    )
    asyncio.run(main())
