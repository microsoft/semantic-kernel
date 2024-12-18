# Copyright (c) Microsoft. All rights reserved.

import asyncio
from functools import reduce
from typing import TYPE_CHECKING

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.functions import KernelFunction

# System message defining the behavior and persona of the chat bot.
system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose. You are also a math wizard,
especially for adding and subtracting.
You also excel at joke telling, where your tone is often sarcastic.
Once you have the answer I am looking for,
you will return a full answer to me as soon as possible.
"""

# Toggle this flag to switch between streaming and non-streaming modes.
stream = True

# Create and configure the kernel.
kernel = Kernel()

# Load some sample plugins (for demonstration of function calling).
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")

# Define a chat function (a template for how to handle user input).
chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

# You can select from the following chat completion services that support function calling:
# - Services.OPENAI
# - Services.AZURE_OPENAI
# - Services.AZURE_AI_INFERENCE
# - Services.ANTHROPIC
# - Services.BEDROCK
# - Services.GOOGLE_AI
# - Services.MISTRAL_AI
# - Services.OLLAMA
# - Services.ONNX
# - Services.VERTEX_AI
# Please make sure you have configured your environment correctly for the selected chat completion service.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.AZURE_OPENAI)

# Configure the function choice behavior. Here, we set it to Auto with auto_invoke=True.
# - If `auto_invoke=True`, the model will automatically choose and call functions as needed.
# - If `auto_invoke=False`, the model may return tool call instructions that you must handle and call manually.
request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(auto_invoke=True)

kernel.add_service(chat_completion_service)

# Pass the request settings to the kernel arguments.
arguments = KernelArguments(settings=request_settings)

# Create a chat history to store the system message, initial messages, and the conversation.
history = ChatHistory()
history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")


def print_tool_calls(message: ChatMessageContent) -> None:
    """
    A helper function to pretty print the tool calls found in a ChatMessageContent message.
    This is useful when auto tool invocation is disabled and the model returns calls that you must handle.
    """
    items = message.items
    formatted_tool_calls = []
    for i, item in enumerate(items, start=1):
        if isinstance(item, FunctionCallContent):
            tool_call_id = item.id
            function_name = item.name
            function_arguments = item.arguments
            formatted_str = (
                f"tool_call {i} id: {tool_call_id}\n"
                f"tool_call {i} function name: {function_name}\n"
                f"tool_call {i} arguments: {function_arguments}"
            )
            formatted_tool_calls.append(formatted_str)
    if len(formatted_tool_calls) > 0:
        print("\n[Tool calls returned by the model]:\n" + "\n\n".join(formatted_tool_calls))
    else:
        print("\n[No tool calls returned by the model]")


async def handle_streaming(
    kernel: Kernel,
    chat_function: "KernelFunction",
    arguments: KernelArguments,
) -> str | None:
    """
    Handle the streaming response from the model.
    This function demonstrates two possible paths:

    1. When auto function calling is ON (auto_invoke=True):
       - The model may call tools automatically and produce a continuous
         stream of assistant messages. We can simply print these as they come in.

    2. When auto function calling is OFF (auto_invoke=False):
       - The model may instead return tool call instructions embedded in the stream.
         We can track these calls using `function_invoke_attempt` attributes and print
         them for the user. The user can then manually invoke the tools and return the results
         to the model for further completion.
    """

    response = kernel.invoke_stream(
        chat_function,
        return_function_results=False,
        arguments=arguments,
    )

    # We will differentiate behavior based on whether auto invoking kernel functions is enabled.
    auto_invoking = request_settings.function_choice_behavior.auto_invoke_kernel_functions

    print("Mosscap:> ", end="", flush=True)

    # If auto_invoking is False, the model may return separate streaming chunks containing tool instructions.
    # We'll store them here.
    streamed_tool_chunks: list[StreamingChatMessageContent] = []

    # For content messages (the final assistant's response text), store them here.
    streamed_response_chunks: list[StreamingChatMessageContent] = []

    async for message in response:
        msg = message[0]

        # We only expect assistant messages here.
        if not isinstance(msg, StreamingChatMessageContent) or msg.role != AuthorRole.ASSISTANT:
            continue

        if auto_invoking:
            # When auto invocation is ON, no special handling is needed. Just print out messages as they arrive.
            streamed_response_chunks.append(msg)
            print(str(msg), end="", flush=True)
        else:
            # When auto invocation is OFF, the model may send chunks that represent tool calls.
            # Chunks that contain function call instructions will have a function_invoke_attempt attribute.
            if hasattr(msg, "function_invoke_attempt"):
                # This chunk is part of a tool call instruction sequence
                streamed_tool_chunks.append(msg)
            else:
                # This chunk is normal assistant response text
                streamed_response_chunks.append(msg)
                print(str(msg), end="", flush=True)

    print("\n", flush=True)

    # If auto function calling was OFF, handle any tool call instructions we captured.
    if not auto_invoking and streamed_tool_chunks:
        # Group streamed chunks by `function_invoke_attempt` to handle each invocation attempt separately.
        grouped_chunks = {}
        for chunk in streamed_tool_chunks:
            key = getattr(chunk, "function_invoke_attempt", None)
            if key is not None:
                grouped_chunks.setdefault(key, []).append(chunk)

        # Process each group of chunks
        for attempt, chunks in grouped_chunks.items():
            try:
                # Combine all chunks for a given attempt into one message.
                combined_content = reduce(lambda first, second: first + second, chunks)
                if hasattr(combined_content, "content"):
                    print(f"[function_invoke_attempt {attempt} content]:\n{combined_content.content}")

                print("[Auto function calling is OFF] Here are the returned tool calls:")
                print_tool_calls(combined_content)
            except Exception as e:
                print(f"Error processing chunks for function_invoke_attempt {attempt}: {e}")

    # Return the final concatenated assistant response (if any).
    if streamed_response_chunks:
        return "".join([str(content) for content in streamed_response_chunks])
    return None


async def chat() -> bool:
    """
    Continuously prompt the user for input and show the assistant's response.
    Type 'exit' to exit.
    """
    try:
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting chat...")
        return False

    if user_input.lower().strip() == "exit":
        print("\n\nExiting chat...")
        return False

    arguments["user_input"] = user_input
    arguments["chat_history"] = history

    if stream:
        # Handle streaming responses
        result = await handle_streaming(kernel, chat_function, arguments=arguments)
    else:
        # Handle non-streaming responses
        result = await kernel.invoke(chat_function, arguments=arguments)

        # If function calls are returned and auto invoking is off, we must show them.
        if not request_settings.function_choice_behavior.auto_invoke_kernel_functions and result and result.value:
            # Extract function calls from the returned content
            function_calls = [item for item in result.value[-1].items if isinstance(item, FunctionCallContent)]
            if len(function_calls) > 0:
                print_tool_calls(result.value[0])
                # At this point, you'd handle these calls manually if desired.
                # For now, we just print them.
                return True

        # If no function calls to handle, just print the assistant's response
        if result:
            print(f"Mosscap:> {result}")

    # Update the chat history with the user's input and the assistant's response
    if result:
        history.add_user_message(user_input)
        history.add_assistant_message(str(result))

    return True


async def main() -> None:
    print(
        "Welcome to the chat bot!\n"
        "  Type 'exit' to exit.\n"
        "  Try a math question to see function calling in action (e.g. 'what is 3+3?')."
    )
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
