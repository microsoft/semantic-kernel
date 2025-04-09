# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os

from samples.concepts.audio.audio_player import AudioPlayer
from samples.concepts.audio.audio_recorder import AudioRecorder
from semantic_kernel.connectors.ai.open_ai import (
    AzureAudioToText,
    AzureChatCompletion,
    AzureTextToAudio,
    OpenAIChatPromptExecutionSettings,
    OpenAITextToAudioExecutionSettings,
)
from semantic_kernel.contents import AudioContent, ChatHistory

# This simple sample demonstrates how to use the AzureChatCompletion, AzureTextToAudio, and AzureAudioToText
# services to create a chat bot that can communicate with the user using both audio input and output.
# The chatbot will engage in a conversation with the user by audio only.
# This sample combines the functionality of the samples/concepts/audio/01-chat_with_audio_input.py and
# samples/concepts/audio/02-chat_with_audio_output.py samples.

# Resources required for this sample:
# 1. An Azure OpenAI model deployment (e.g. GPT-4o-mini).
# 2. An Azure Text to Speech deployment (e.g. tts).
# 3. An Azure Speech to Text deployment (e.g. whisper).

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
text_to_audio_service = AzureTextToAudio()
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

    # No need to stream the response since we can only pass the
    # response to the text to audio service as a whole
    response = await chat_service.get_chat_message_content(
        chat_history=history,
        settings=OpenAIChatPromptExecutionSettings(
            max_tokens=2000,
            temperature=0.7,
            top_p=0.8,
        ),
    )

    # Need to set the response format to wav since the audio player only supports wav files
    audio_content = await text_to_audio_service.get_audio_content(
        response.content, OpenAITextToAudioExecutionSettings(response_format="wav")
    )
    print("Mosscap:> ", end="", flush=True)
    AudioPlayer(audio_content=audio_content).play(text=response.content)

    history.add_message(response)

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
