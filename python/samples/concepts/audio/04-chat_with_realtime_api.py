# Copyright (c) Microsoft. All rights reserved.
import asyncio
import contextlib
import logging
import signal

from samples.concepts.audio.audio_player_async import AudioPlayerAsync

# This simple sample demonstrates how to use the OpenAI Realtime API to create
# a chat bot that can listen and respond directly through audio.
# It requires installing semantic-kernel[openai_realtime] which includes the
# OpenAI Realtime API client and some packages for handling audio locally.
# It has hardcoded device id's set in the AudioRecorderStream and AudioPlayerAsync classes,
# so you may need to adjust these for your system.
from samples.concepts.audio.audio_recorder_stream import AudioRecorderStream
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (
    OpenAIRealtimeExecutionSettings,
    TurnDetection,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_realtime import OpenAIRealtime
from semantic_kernel.contents import AudioContent, ChatHistory, StreamingTextContent
from semantic_kernel.functions import kernel_function

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def signal_handler():
    for task in asyncio.all_tasks():
        task.cancel()


system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

history = ChatHistory()
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")


class Speaker:
    def __init__(self, audio_player: AudioPlayerAsync, realtime_client: OpenAIRealtime, kernel: Kernel):
        self.audio_player = audio_player
        self.realtime_client = realtime_client
        self.kernel = kernel

    async def play(
        self,
        chat_history: ChatHistory,
        settings: OpenAIRealtimeExecutionSettings,
    ) -> None:
        self.audio_player.reset_frame_count()
        print("Mosscap (transcript): ", end="")
        try:
            async for content in self.realtime_client.get_streaming_chat_message_content(
                chat_history=chat_history, settings=settings, kernel=self.kernel
            ):
                if not content:
                    continue
                for item in content.items:
                    match item:
                        case StreamingTextContent():
                            print(item.text, end="")
                            await asyncio.sleep(0.01)
                            continue
                        case AudioContent():
                            self.audio_player.add_data(item.data)
                            await asyncio.sleep(0.01)
                            continue
        except asyncio.CancelledError:
            print("\nThanks for talking to Mosscap!")


class Microphone:
    def __init__(self, audio_recorder: AudioRecorderStream, realtime_client: OpenAIRealtime):
        self.audio_recorder = audio_recorder
        self.realtime_client = realtime_client

    async def record_audio(self):
        with contextlib.suppress(asyncio.CancelledError):
            async for audio in self.audio_recorder.stream_audio_content():
                if audio.data:
                    await self.realtime_client.send_content(content=audio)
                await asyncio.sleep(0.01)


@kernel_function
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    logger.debug(f"Getting weather for {location}")
    return f"The weather in {location} is sunny."


async def main() -> None:
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)
    settings = OpenAIRealtimeExecutionSettings(
        instructions=system_message,
        voice="sage",
        turn_detection=TurnDetection(type="server_vad", create_response=True, silence_duration_ms=800, threshold=0.8),
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    realtime_client = OpenAIRealtime(ai_model_id="gpt-4o-realtime-preview-2024-12-17")
    kernel = Kernel()
    kernel.add_function(plugin_name="weather", function_name="get_weather", function=get_weather)

    speaker = Speaker(AudioPlayerAsync(), realtime_client, kernel)
    microphone = Microphone(AudioRecorderStream(), realtime_client)
    with contextlib.suppress(asyncio.CancelledError):
        await asyncio.gather(*[speaker.play(history, settings), microphone.record_audio()])


if __name__ == "__main__":
    print(
        "Instruction: start speaking, when you stop the API should detect you finished and start responding."
        "Press ctrl + c to stop the program."
    )
    asyncio.run(main())
