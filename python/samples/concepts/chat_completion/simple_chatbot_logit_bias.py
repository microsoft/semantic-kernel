# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.chat_completion_services import (
    Services,
    get_chat_completion_service_and_request_settings,
)
from semantic_kernel.contents import ChatHistory

# This sample shows how to create a chatbot that whose output can be biased using logit bias.
# This sample uses the following three main components:
# - a ChatCompletionService: This component is responsible for generating responses to user messages.
# - a ChatHistory: This component is responsible for keeping track of the chat history.
# - a list of tokens whose bias value will be reduced, meaning the likelihood of these tokens appearing
#   in the output will be reduced.
# The chatbot in this sample is called Mosscap, who is an expert in basketball.

# To learn more about logit bias, see: https://help.openai.com/en/articles/5247780-using-logit-bias-to-define-token-probability


# You can select from the following chat completion services:
# - Services.OPENAI
# - Services.AZURE_OPENAI
# Please make sure you have configured your environment correctly for the selected chat completion service.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.AZURE_OPENAI)

# This is the system message that gives the chatbot its personality.
system_message = """
You are a chat bot whose expertise is basketball.
Your name is Mosscap and you have one goal: to answer questions about basketball.
"""

# Create a chat history object with the system message.
chat_history = ChatHistory(system_message=system_message)
# Create a list of tokens whose bias value will be reduced.
# The token ids of these words can be obtained using the GPT Tokenizer: https://platform.openai.com/tokenizer
# the targeted model series is GPT-4o & GPT-4o mini
# banned_words = ["basketball", "NBA", "player", "career", "points"]
banned_tokens = [
    # "basketball"
    106622,
    5052,
    # "NBA"
    99915,
    # " NBA"
    32272,
    # "player"
    6450,
    # " player"
    5033,
    # "career"
    198069,
    # " career"
    8461,
    # "points"
    14011,
    # " points"
    5571,
]
# Configure the logit bias settings to minimize the likelihood of the
# tokens in the banned_tokens list appearing in the output.
request_settings.logit_bias = {k: -100 for k in banned_tokens}  # type: ignore


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

    # Add the user message to the chat history so that the chatbot can respond to it.
    chat_history.add_user_message(user_input)

    # Get the chat message content from the chat completion service.
    response = await chat_completion_service.get_chat_message_content(
        chat_history=chat_history,
        settings=request_settings,
    )
    if response:
        print(f"Mosscap:> {response}")

        # Add the chat message to the chat history to keep track of the conversation.
        chat_history.add_message(response)

    return True


async def main() -> None:
    # Start the chat loop. The chat loop will continue until the user types "exit".
    chatting = True
    while chatting:
        chatting = await chat()

    # Sample output:
    # User:> Who has the most career points in NBA history?
    # Mosscap:> As of October 2023, the all-time leader in total regular-season scoring in the history of the National
    #           Basketball Association (N.B.A.) is Kareem Abdul-Jabbar, who scored 38,387 total regular-seasonPoints
    #           during his illustrious 20-year playing Career.


if __name__ == "__main__":
    asyncio.run(main())
