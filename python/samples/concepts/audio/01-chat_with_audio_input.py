# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os

from samples.concepts.audio.audio_recorder import AudioRecorder
from semantic_kernel.connectors.ai.open_ai import (
    AzureAudioToText,
    AzureChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import AudioContent, ChatHistory

# This simple sample demonstrates how to use the AzureChatCompletion and AzureAudioToText services
# to create a chat bot that can communicate with the user using audio input.
# The user can enage a long conversation with the chat bot by speaking to it.

# Resources required for this sample:
# 1. An Azure OpenAI model deployment (e.g. GPT-4o-mini).
# 2. An Azure Speech to Text deployment (e.g. whisper).

# Additional dependencies required for this sample:
# - pyaudio: `pip install pyaudio` or `uv pip install pyaudio` if you are using uv and have a virtual env activated.
# - keyboard: `pip install keyboard` or `uv pip install keyboard` if you are using uv and have a virtual env activated.


logging.basicConfig(level=logging.WARNING)
AUDIO_FILEPATH = os.path.join(os.path.dirname(__file__), "output.wav")

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""


chat_service = AzureChatCompletion()
audio_to_text_service = AzureAudioToText()

history = ChatHistory()
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")


async def chat() -> bool:
    try:
        print("User:> ", end="", flush=True)
        with AudioRecorder(output_filepath=AUDIO_FILEPATH) as recorder:
            recorder.start_recording()
            user_input = await audio_to_text_service.get_text_content(AudioContent.from_audio_file(AUDIO_FILEPATH))
            print(user_input.text)
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if "exit" in user_input.text.lower():
        print("\n\nExiting chat...")
        return False

    history.add_user_message(user_input.text)

    chunks = chat_service.get_streaming_chat_message_content(
        chat_history=history,
        settings=OpenAIChatPromptExecutionSettings(
            max_tokens=2000,
            temperature=0.7,
            top_p=0.8,
        ),
    )

    print("Mosscap:> ", end="")
    answer = ""
    async for message in chunks:
        print(str(message), end="")
        answer += str(message)
    print("\n")

    history.add_assistant_message(str(answer))

    return True


async def main() -> None:
    print(
        "Instruction: when it's your turn to speak, press the spacebar to start recording."
        " Release the spacebar to stop recording."
    )
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
