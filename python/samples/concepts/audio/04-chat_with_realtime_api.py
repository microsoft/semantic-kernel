# Copyright (c) Microsoft. All rights reserved.
import asyncio
import contextlib
import logging
import signal
from typing import Any

import numpy as np
from aiortc.mediastreams import MediaStreamError, MediaStreamTrack
from av import AudioFrame
from openai.types.beta.realtime.realtime_server_event import RealtimeServerEvent

from samples.concepts.audio.audio_player_async import AudioPlayerAsync
from samples.concepts.audio.audio_recorder_stream import AudioRecorderStream
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIRealtimeExecutionSettings,
    OpenAIRealtimeWebRTC,
    TurnDetection,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.contents import AudioContent, ChatHistory, StreamingTextContent
from semantic_kernel.functions import kernel_function

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# This simple sample demonstrates how to use the OpenAI Realtime API to create
# a chat bot that can listen and respond directly through audio.
# It requires installing:
# - semantic-kernel[openai_realtime]
# - pyaudio
# - sounddevice
# - pydub
# e.g. pip install semantic-kernel[openai_realtime] pyaudio sounddevice pydub

# The characterics of your speaker and microphone are a big factor in a smooth conversation
# so you may need to try out different devices for each.
# you can also play around with the turn_detection settings to get the best results.
# It has device id's set in the AudioRecorderStream and AudioPlayerAsync classes,
# so you may need to adjust these for your system.
# you can check the available devices by uncommenting line below the function


def check_audio_devices():
    import sounddevice as sd  # type: ignore

    print(sd.query_devices())


check_audio_devices()


class Speaker:
    """This is a simple class that opens the session with the realtime api and plays the audio response.

    At the same time it prints the transcript of the conversation to the console.
    """

    def __init__(self, audio_player: AudioPlayerAsync, realtime_client: RealtimeClientBase, kernel: Kernel):
        self.audio_player = audio_player
        self.realtime_client = realtime_client
        self.kernel = kernel

    async def play(
        self,
        chat_history: ChatHistory,
        settings: OpenAIRealtimeExecutionSettings,
        print_transcript: bool = True,
    ) -> None:
        # reset the frame count for the audio player
        self.audio_player.reset_frame_count()
        # print the start message of the transcript
        if print_transcript:
            print("Mosscap (transcript): ", end="")
        try:
            # start listening for events
            while True:
                _, content = await self.realtime_client.output_buffer.get()
                if not content:
                    continue
                # the contents returned should be StreamingChatMessageContent
                # so we will loop through the items within it.
                for item in content.items:
                    match item:
                        case StreamingTextContent():
                            if print_transcript:
                                print(item.text, end="")
                            await asyncio.sleep(0.01)
                            continue
                        case AudioContent():
                            self.audio_player.add_data(item.data)
                            await asyncio.sleep(0.01)
                            continue
        except asyncio.CancelledError:
            print("\nThanks for talking to Mosscap!")


class Microphone(MediaStreamTrack):
    """This is a simple class that opens the microphone and sends the audio to the realtime api."""

    kind = "audio"

    def __init__(self, audio_recorder: AudioRecorderStream, realtime_client: RealtimeClientBase):
        self.audio_recorder = audio_recorder
        self.realtime_client = realtime_client
        self.queue = asyncio.Queue()
        self.loop = asyncio.get_running_loop()
        self._pts = 0

    async def recv(self) -> Any:
        # start the audio recording
        try:
            return await self.queue.get()
        except Exception as e:
            logger.error(f"Error receiving audio frame: {str(e)}")
            raise MediaStreamError("Failed to receive audio frame")

    async def record_audio(self):
        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio input status: {status}")
            audio_data = indata.copy()

            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)

            # Create AudioFrame with incrementing pts
            frame = AudioFrame(
                samples=len(audio_data),
                layout="mono",
                format="s16",  # 16-bit signed integer
            )
            frame.rate = 48000
            frame.pts = self._pts
            self._pts += len(audio_data)  # Increment pts by frame size

            frame.planes[0].update(audio_data.tobytes())

            asyncio.run_coroutine_threadsafe(self.queue.put(frame), self.loop)

        await self.realtime_client.input_buffer.put("response.create")
        await self.audio_recorder.stream_audio_content_with_callback(callback=callback)


# this function is used to stop the processes when ctrl + c is pressed
def signal_handler():
    for task in asyncio.all_tasks():
        task.cancel()


@kernel_function
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    logger.debug(f"Getting weather for {location}")
    return f"The weather in {location} is sunny."


def response_created_callback(
    event: RealtimeServerEvent, settings: PromptExecutionSettings | None = None, **kwargs: Any
) -> None:
    """Add a empty print to start a new line for a new response."""
    print("")


async def main() -> None:
    # setup the asyncio loop with the signal event handler
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)

    # create the Kernel and add a simple function for function calling.
    kernel = Kernel()
    kernel.add_function(plugin_name="weather", function_name="get_weather", function=get_weather)

    # create the realtime client and register the response created callback
    realtime_client = OpenAIRealtimeWebRTC(ai_model_id="gpt-4o-realtime-preview-2024-12-17")
    realtime_client.register_event_handler("response.created", response_created_callback)

    # create the speaker and microphone
    speaker = Speaker(AudioPlayerAsync(device_id=None), realtime_client, kernel)
    microphone = Microphone(AudioRecorderStream(device_id=None), realtime_client)

    # Create the settings for the session
    # the key thing to decide on is to enable the server_vad turn detection
    # if turn is turned off (by setting turn_detection=None), you will have to send
    # the "input_audio_buffer.commit" and "response.create" event to the realtime api
    # to signal the end of the user's turn and start the response.

    # The realtime api, does not use a system message, but takes instructions as a parameter for a session
    instructions = """
    You are a chat bot. Your name is Mosscap and
    you have one goal: figure out what people need.
    Your full name, should you need to know it, is
    Splendid Speckled Mosscap. You communicate
    effectively, but you tend to answer with long
    flowery prose.
    """
    # but we can add a chat history to conversation after starting it
    chat_history = ChatHistory()
    chat_history.add_user_message("Hi there, who are you?")
    chat_history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

    settings = OpenAIRealtimeExecutionSettings(
        instructions=instructions,
        voice="sage",
        turn_detection=TurnDetection(type="server_vad", create_response=True, silence_duration_ms=800, threshold=0.8),
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    async with realtime_client:
        await realtime_client.update_session(settings=settings, chat_history=chat_history)
        await realtime_client.start_listening(settings, chat_history)
        await realtime_client.start_sending(input_audio_track=microphone)
        # await realtime_client.start_streaming(settings, chat_history, input_audio_track=microphone)
        # start the the speaker and the microphone
        with contextlib.suppress(asyncio.CancelledError):
            await speaker.play(chat_history, settings)


if __name__ == "__main__":
    print(
        "Instruction: start speaking, when you stop the API should detect you finished and start responding. "
        "Press ctrl + c to stop the program."
    )
    asyncio.run(main())
