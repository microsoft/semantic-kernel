# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from datetime import datetime
from random import randint

from samples.concepts.realtime.utils import AudioPlayerWebRTC, AudioRecorderWebRTC, check_audio_devices
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    AzureRealtimeWebRTC,
    ListenEvents,
    OpenAIRealtimeExecutionSettings,
    TurnDetection,
)
from semantic_kernel.contents import ChatHistory, RealtimeTextEvent
from semantic_kernel.functions import kernel_function

logging.basicConfig(level=logging.WARNING)
utils_log = logging.getLogger("samples.concepts.realtime.utils")
utils_log.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

"""
This simple sample demonstrates how to use the OpenAI Realtime API to create
a agent that can listen and respond directly through audio.
It requires installing:
- semantic-kernel
- pyaudio
- sounddevice
- pydub
e.g. pip install pyaudio sounddevice pydub semantic-kernel

For more details of the exact setup, see the README.md in the realtime folder.
"""

# The characterics of your speaker and microphone are a big factor in a smooth conversation
# so you may need to try out different devices for each.
# you can also play around with the turn_detection settings to get the best results.
# It has device id's set in the AudioRecorderStream and AudioPlayerAsync classes,
# so you may need to adjust these for your system.
# you can disable the check for available devices by commenting the line below
check_audio_devices()


class Helpers:
    """A set of helper functions for the Realtime Agent."""

    @kernel_function
    def get_weather(self, location: str) -> str:
        """Get the weather for a location."""
        weather_conditions = ("sunny", "hot", "cloudy", "raining", "freezing", "snowing")
        weather = weather_conditions[randint(0, len(weather_conditions) - 1)]  # nosec
        logger.info(f"@ Getting weather for {location}: {weather}")
        return f"The weather in {location} is {weather}."

    @kernel_function
    def get_date_time(self) -> str:
        """Get the current date and time."""
        logger.info("@ Getting current datetime")
        return f"The current date and time is {datetime.now().isoformat()}."

    @kernel_function
    def goodbye(self):
        """When the user is done, say goodbye and then call this function."""
        logger.info("@ Goodbye has been called!")
        raise KeyboardInterrupt


async def main() -> None:
    print_transcript = True
    # create the audio player and audio track
    # both take a device_id parameter, which is the index of the device to use,
    # if None the default device will be used
    audio_player = AudioPlayerWebRTC()

    # create the realtime agent and optionally add the audio output function, this is optional
    # and can also be passed in the receive method
    # You can also pass in kernel, plugins, chat_history or settings here.
    # For WebRTC the audio_track is required
    realtime_agent = AzureRealtimeWebRTC(
        audio_track=AudioRecorderWebRTC(),
        region="swedencentral",
        plugins=[Helpers()],
    )

    # Create the settings for the session
    # The realtime api, does not use a system message, but takes instructions as a parameter for a session
    # Another important setting is to tune the server_vad turn detection
    # if this is turned off (by setting turn_detection=None), you will have to send
    # the "input_audio_buffer.commit" and "response.create" event to the realtime api
    # to signal the end of the user's turn and start the response.
    # manual VAD is not part of this sample
    # for more info: https://platform.openai.com/docs/api-reference/realtime-sessions/create#realtime-sessions-create-turn_detection
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
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    # and we can add a chat history to conversation after starting it
    chat_history = ChatHistory()
    chat_history.add_user_message("Hi there, who are you?")
    chat_history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

    # the context manager calls the create_session method on the client and starts listening to the audio stream
    async with (
        realtime_agent(
            settings=settings,
            chat_history=chat_history,
            create_response=True,
        ),
        audio_player,
    ):
        async for event in realtime_agent.receive(audio_output_callback=audio_player.client_callback):
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
                            logger.error(event.service_event)


if __name__ == "__main__":
    print(
        "Instructions: The model will start speaking immediately,"
        "this can be turned off by removing `create_response=True` above."
        "The model will detect when you stop and automatically generate a response. "
        "Press ctrl + c to stop the program."
    )
    asyncio.run(main())
