# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from datetime import datetime
from random import randint

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    ListenEvents,
    OpenAIRealtime,
    OpenAIRealtimeExecutionSettings,
    TurnDetection,
)
from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.connectors.ai.utils import SKAudioPlayer
from semantic_kernel.contents import ChatHistory, StreamingChatMessageContent
from semantic_kernel.functions import kernel_function

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


class ReceivingStreamHandler:
    """This is a simple class that listens to the received buffer of the RealtimeClientBase.

    It can be used to play audio and print the transcript of the conversation.

    It can also be used to act on other events from the service.
    """

    def __init__(self, realtime_client: RealtimeClientBase, audio_player: SKAudioPlayer | None = None):
        self.audio_player = audio_player
        self.realtime_client = realtime_client

    async def listen(
        self,
        play_audio: bool = True,
        print_transcript: bool = True,
    ) -> None:
        # print the start message of the transcript
        if print_transcript:
            print("Mosscap (transcript): ", end="")
        try:
            # start listening for events
            while True:
                event_type, event = await self.realtime_client.receive_buffer.get()
                match event_type:
                    case ListenEvents.RESPONSE_AUDIO_DELTA:
                        if play_audio and self.audio_player and isinstance(event, StreamingChatMessageContent):
                            await self.audio_player.add_audio(event.items[0])
                    case ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
                        if print_transcript and isinstance(event, StreamingChatMessageContent):
                            print(event.content, end="")
                    case ListenEvents.RESPONSE_CREATED:
                        if print_transcript:
                            print("")
                    # case ....:
                    #     # add other event handling here
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            print("\nThanks for talking to Mosscap!")


@kernel_function
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    weather_conditions = ("sunny", "hot", "cloudy", "raining", "freezing", "snowing")
    weather = weather_conditions[randint(0, len(weather_conditions) - 1)]  # nosec
    logger.info(f"Getting weather for {location}: {weather}")
    return f"The weather in {location} is {weather}."


@kernel_function
def get_date_time() -> str:
    """Get the current date and time."""
    logger.info("Getting current datetime")
    return f"The current date and time is {datetime.now().isoformat()}."


async def main() -> None:
    # create the Kernel and add a simple function for function calling.
    kernel = Kernel()
    kernel.add_function(plugin_name="weather", function_name="get_weather", function=get_weather)
    kernel.add_function(plugin_name="time", function_name="get_date_time", function=get_date_time)

    # create the realtime client and optionally add the audio output function, this is optional
    audio_player = SKAudioPlayer()
    # you can define the protocol to use, either "websocket" or "webrtc"
    # they will behave the same way, even though the underlying protocol is quite different
    realtime_client = OpenAIRealtime(protocol="webrtc", audio_output_callback=audio_player.client_callback)

    # create stream receiver (defined above), this can play the audio,
    # if the audio_player is passed (commented out here)
    # and allows you to print the transcript of the conversation
    # and review or act on other events from the service
    stream_handler = ReceivingStreamHandler(realtime_client)  # SimplePlayer(device_id=None)

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
    async with realtime_client, audio_player:
        await realtime_client.update_session(
            settings=settings, chat_history=chat_history, kernel=kernel, create_response=True
        )
        # you can also send other events to the service, like this (the first has content, the second does not)
        # await realtime_client.send(
        #     SendEvents.CONVERSATION_ITEM_CREATE,
        #     item=ChatMessageContent(role="user", content="Hi there, who are you?")},
        # )
        # await realtime_client.send(SendEvents.RESPONSE_CREATE)
        async with asyncio.TaskGroup() as tg:
            tg.create_task(realtime_client.start_streaming())
            tg.create_task(stream_handler.listen())


if __name__ == "__main__":
    print(
        "Instruction: start speaking, when you stop the API should detect you finished and start responding. "
        "Press ctrl + c to stop the program."
    )
    asyncio.run(main())
