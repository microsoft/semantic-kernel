# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from datetime import datetime
from random import randint

from samples.concepts.realtime.utils import AudioPlayerWebsocket, AudioRecorderWebsocket
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    AzureRealtimeExecutionSettings,
    AzureRealtimeWebsocket,
    ListenEvents,
    TurnDetection,
)
from semantic_kernel.contents import ChatHistory, RealtimeTextEvent
from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

"""
This simple sample demonstrates how to use the OpenAI Realtime API to create
a chat bot that can listen and respond directly through audio.
It requires installing:
- semantic-kernel[realtime]
- pyaudio
- sounddevice
- pydub
e.g. pip install pyaudio sounddevice pydub semantic-kernel[realtime]

For more details of the exact setup, see the README.md in the realtime folder.
"""


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
    # create a Kernel and add a simple function for function calling.
    kernel = Kernel()
    kernel.add_functions(plugin_name="helpers", functions=[goodbye, get_weather, get_date_time])

    # create the realtime agent, in this using Azure OpenAI through Websockets,
    # there are also OpenAI Websocket and WebRTC clients
    # See realtime_agent_with_function_calling_webrtc.py for an example of the WebRTC client
    realtime_agent = AzureRealtimeWebsocket()
    # create the audio player and audio track
    # both take a device_id parameter, which is the index of the device to use, if None the default device is used
    audio_player = AudioPlayerWebsocket()
    audio_recorder = AudioRecorderWebsocket(realtime_client=realtime_agent)

    # Create the settings for the session
    # The realtime api, does not use a system message, but, like agents, takes instructions as a parameter for a session
    # Another important setting is to tune the server_vad turn detection
    # if this is turned off (by setting turn_detection=None), you will have to send
    # the "input_audio_buffer.commit" and "response.create" event to the realtime api
    # to signal the end of the user's turn and start the response.
    # manual VAD is not part of this sample
    # for more info: https://platform.openai.com/docs/api-reference/realtime-sessions/create#realtime-sessions-create-turn_detection
    settings = AzureRealtimeExecutionSettings(
        instructions="""
    You are a chat bot. Your name is Mosscap and
    you have one goal: figure out what people need.
    Your full name, should you need to know it, is
    Splendid Speckled Mosscap. You communicate
    effectively, but you tend to answer with long
    flowery prose.
    """,
        # see https://platform.openai.com/docs/api-reference/realtime-sessions/create#realtime-sessions-create-voice for the full list of voices # noqa: E501
        voice="alloy",
        turn_detection=TurnDetection(type="server_vad", create_response=True, silence_duration_ms=800, threshold=0.8),
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    # and we can add a chat history to conversation to seed the conversation
    chat_history = ChatHistory()
    chat_history.add_user_message("Hi there, I'm based in Amsterdam.")
    chat_history.add_assistant_message(
        "I am Mosscap, a chat bot. I'm trying to figure out what people need, "
        "I can tell you what the weather is or the time."
    )

    # the context manager calls the create_session method on the agent and starts listening to the audio stream
    async with (
        audio_recorder,
        realtime_agent(
            settings=settings,
            chat_history=chat_history,
            kernel=kernel,
            create_response=True,
        ),
        audio_player,
    ):
        # the audio_output_callback can be added here or in the constructor
        # using this gives the smoothest experience
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
                            print(event.service_event)
                            logger.error(event.service_event)


if __name__ == "__main__":
    print(
        "Instructions: The agent will start speaking immediately,"
        "this can be turned off by removing `create_response=True` above."
        "The model will detect when you stop and automatically generate a response. "
        "Press ctrl + c to stop the program."
    )
    asyncio.run(main())
