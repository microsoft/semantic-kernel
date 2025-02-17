# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from datetime import datetime
from random import randint

from samples.concepts.realtime.utils import AudioPlayerWebsocket, AudioRecorderWebsocket
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    AzureRealtime,
    ListenEvents,
    OpenAIRealtimeExecutionSettings,
    TurnDetection,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.events import RealtimeTextEvent
from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# This simple sample demonstrates how to use the OpenAI Realtime API to create
# a chat bot that can listen and respond directly through audio.
# It requires installing:
# - semantic-kernel[realtime]
# - pyaudio
# - sounddevice
# - pydub
# e.g. pip install pyaudio sounddevice pydub semantic_kernel[realtime]


@kernel_function
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    weather_conditions = ("sunny", "hot", "cloudy", "raining", "freezing", "snowing")
    weather = weather_conditions[randint(0, len(weather_conditions) - 1)]  # nosec
    logger.info(f"@ Getting weather for {location}: {weather}")
    return f"The weather in {location} is {weather}."


@kernel_function
def get_date_time() -> str:
    """Get the current date and time."""
    logger.info("@ Getting current datetime")
    return f"The current date and time is {datetime.now().isoformat()}."


@kernel_function
def goodbye():
    """When the user is done, say goodbye and then call this function."""
    logger.info("@ Goodbye has been called!")
    raise KeyboardInterrupt


async def main() -> None:
    print_transcript = True
    # create the Kernel and add a simple function for function calling.
    kernel = Kernel()
    kernel.add_functions(plugin_name="helpers", functions=[goodbye, get_weather, get_date_time])

    # create the audio player and audio track
    # both take a device_id parameter, which is the index of the device to use, if None the default device is used
    audio_player = AudioPlayerWebsocket()
    # create the realtime client and add the audio output function, this is optional
    # you can define the protocol to use, either "websocket" or "webrtc"
    # (at this time Azure only support websockets)
    # they will behave the same way, even though the underlying protocol is quite different
    realtime_client = AzureRealtime(
        protocol="websocket",
        audio_output_callback=audio_player.client_callback,
    )
    audio_recorder = AudioRecorderWebsocket(realtime_client=realtime_client)

    # Create the settings for the session
    # The realtime api, does not use a system message, but takes instructions as a parameter for a session
    instructions = """
    You are a chat bot. Your name is Mosscap and
    you have one goal: figure out what people need.
    Your full name, should you need to know it, is
    Splendid Speckled Mosscap. You communicate
    effectively, but you tend to answer with long
    flowery prose.
    """
    # the key thing to decide on is to enable the server_vad turn detection
    # if turn is turned off (by setting turn_detection=None), you will have to send
    # the "input_audio_buffer.commit" and "response.create" event to the realtime api
    # to signal the end of the user's turn and start the response.
    # manual VAD is not part of this sample
    settings = OpenAIRealtimeExecutionSettings(
        instructions=instructions,
        voice="alloy",
        turn_detection=TurnDetection(type="server_vad", create_response=True, silence_duration_ms=800, threshold=0.8),
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    # and we can add a chat history to conversation after starting it
    chat_history = ChatHistory()
    chat_history.add_user_message("Hi there, who are you?")
    chat_history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

    # the context manager calls the create_session method on the client and start listening to the audio stream
    async with (
        audio_player,
        audio_recorder,
        realtime_client(
            settings=settings,
            chat_history=chat_history,
            kernel=kernel,
            create_response=True,
        ),
    ):
        async for event in realtime_client.receive():
            match event:
                case RealtimeTextEvent():
                    if print_transcript:
                        print(event.text.text, end="")
                case _:
                    # OpenAI Specific events
                    match event.service_type:
                        case ListenEvents.RESPONSE_CREATED:
                            if print_transcript:
                                print("\nMosscap (transcript): ", end="")
                        case ListenEvents.ERROR:
                            print(event.service_event)
                            logger.error(event.service_event)


if __name__ == "__main__":
    print(
        "Instruction: start speaking, when you stop the API should detect you finished and start responding. "
        "Press ctrl + c to stop the program."
    )
    asyncio.run(main())
