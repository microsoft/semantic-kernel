# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from samples.concepts.audio.audio_player import AudioPlayer
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureTextToAudio,
    OpenAIChatPromptExecutionSettings,
    OpenAITextToAudioExecutionSettings,
)
from semantic_kernel.contents import ChatHistory

# This simple sample demonstrates how to use the AzureChatCompletion and AzureTextToAudio services
# to create a chat bot that can communicate with the user using audio output.
# The chatbot will engage in a conversation with the user and respond using audio output.

# Resources required for this sample:
# 1. An Azure OpenAI model deployment (e.g. GPT-4o-mini).
# 2. An Azure Text to Speech deployment (e.g. tts).

# Additional dependencies required for this sample:
# - pyaudio: `pip install pyaudio` or `uv pip install pyaudio` if you are using uv and have a virtual env activated.
# - keyboard: `pip install keyboard` or `uv pip install keyboard` if you are using uv and have a virtual env activated.


logging.basicConfig(level=logging.WARNING)

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

history = ChatHistory()
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")


async def chat() -> bool:
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    history.add_user_message(user_input)

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
    AudioPlayer(audio_content=audio_content).play()

    print(f"Mosscap:> {response.content}")

    history.add_message(response)

    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
