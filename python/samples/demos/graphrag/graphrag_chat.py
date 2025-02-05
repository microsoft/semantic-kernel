# Copyright (c) Microsoft. All rights reserved.

import logging

from SKGraphRag import GraphRagChatCompletion, GraphRagPromptExecutionSettings

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents import ChatHistory, StreamingChatMessageContent

logger = logging.getLogger(__name__)


async def chat(service: ChatCompletionClientBase, chat_history: ChatHistory) -> StreamingChatMessageContent | None:
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return None
    except EOFError:
        print("\n\nExiting chat...")
        return None

    if user_input == "exit":
        print("\n\nExiting chat...")
        return None

    # Add the user message to the chat history so that the chatbot can respond to it.
    chat_history.add_user_message(user_input)

    # Capture the chunks of the response and print them as they come in.
    chunks: list[StreamingChatMessageContent] = []
    print("Graphrag:> ", end="")
    async for chunk in service.get_streaming_chat_message_content(
        chat_history=chat_history,
        settings=GraphRagPromptExecutionSettings(search_type="local"),
    ):
        if chunk:
            chunks.append(chunk)
            print(chunk, end="")
    print("")

    # Combine the chunks into a single message to add to the chat history.
    full_message = sum(chunks[1:], chunks[0])
    # Add the chat message to the chat history to keep track of the conversation.
    chat_history.add_message(full_message)
    # Return the full message, including context, to the caller.
    return full_message


async def main():
    # Control whether the full context of the message is printed as well.
    print_context = False

    graph_rag_chat_completion = GraphRagChatCompletion(project_directory="./ragtest")
    if not graph_rag_chat_completion.has_loaded():
        await graph_rag_chat_completion.setup()
    chat_history = ChatHistory()
    print("Welcome to Graphrag, a chatbot that can answer questions about document(s) indexed using GraphRag.")
    print("Type 'exit' to quit.")
    while True:
        # The main function returns either the full message, including context or None.
        message = await chat(graph_rag_chat_completion, chat_history)
        if message is None:
            break
        if print_context and "context" in message.metadata:
            print("Context:")
            for part in ["reports", "entities", "relationships", "claims", "sources"]:
                print(f"  {part}:")
                for values in message.metadata["context"][part]:
                    if isinstance(values, dict):
                        for key, value in values.items():
                            print(f"    {key}:{value}")
                    else:
                        print(f"    {values}")
            print("done")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
