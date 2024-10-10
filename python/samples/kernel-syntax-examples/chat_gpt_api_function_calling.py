# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.utils import (
    chat_completion_with_tool_call,
    get_tool_call_object,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins import MathPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable
from functools import reduce
from typing import TYPE_CHECKING, Any, Dict, List, Union

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import OpenAIChatMessageContent
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_streaming_chat_message_content import (
    OpenAIStreamingChatMessageContent,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.utils import get_tool_call_object
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_function import KernelFunction

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

kernel = sk.Kernel()

# Note: the underlying gpt-35/gpt-4 model version needs to be at least version 0613 to support tools.
deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
api_version = "2023-12-01-preview"
kernel.add_service(
    sk_oai.AzureChatCompletion(
        service_id="chat",
        deployment_name=deployment_name,
        base_url=endpoint,
        api_key=api_key,
        api_version=api_version,
api_key, org_id = sk.openai_settings_from_dot_env()
kernel.add_service(
    sk_oai.OpenAIChatCompletion(
        service_id="chat",
        ai_model_id="gpt-3.5-turbo-1106",
        api_key=api_key,
    ),
)

plugins_directory = os.path.join(__file__, "../../../../samples/plugins")
# adding plugins to the kernel
# the joke plugin in the FunPlugins is a semantic plugin and has the function calling disabled.
# kernel.import_plugin_from_prompt_directory("chat", plugins_directory, "FunPlugin")
# the math plugin is a core plugin and has the function calling enabled.
kernel.import_plugin(MathPlugin(), plugin_name="math")

kernel.import_plugin_from_object(MathPlugin(), plugin_name="math")
kernel.import_plugin_from_object(TimePlugin(), plugin_name="time")

chat_function = kernel.create_function_from_prompt(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)
# enabling or disabling function calling is done by setting the function_call parameter for the completion.
# when the function_call parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific function, set the name of that function in this parameter,
# the format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.
execution_settings = sk_oai.AzureChatPromptExecutionSettings(
    service_id="chat",
    ai_model_id=deployment_name,

# Note: the number of responses for auto inoking tool calls is limited to 1.
# If configured to be greater than one, this value will be overridden to 1.
execution_settings = sk_oai.OpenAIChatPromptExecutionSettings(
    service_id="chat",
    ai_model_id="gpt-3.5-turbo-1106",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    tool_choice="auto",
    tools=get_tool_call_object(kernel, {"exclude_plugin": ["ChatBot"]}),
)

prompt_template_config = sk.PromptTemplateConfig(
    template="{{$user_input}}",
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(name="user_input", description="The user input", is_required=True),
        InputVariable(name="history", description="The history of the conversation", is_required=True, default=""),
    ],
    execution_settings={"default": execution_settings},
    auto_invoke_kernel_functions=True,
    max_auto_invoke_attempts=3,
)

history = ChatHistory()

history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

arguments = KernelArguments()

chat_function = kernel.create_function_from_prompt(
    prompt_template_config=prompt_template_config,
    plugin_name="ChatBot",
    function_name="Chat",
)
arguments = KernelArguments(settings=execution_settings)


def print_tool_calls(message: Union[OpenAIChatMessageContent, OpenAIStreamingChatMessageContent]) -> None:
    # A helper method to pretty print the tool calls from the message.
    # This is only triggered if auto invoke tool calls is disabled.
    if isinstance(message, (OpenAIChatMessageContent, OpenAIStreamingChatMessageContent)):
        tool_calls = message.tool_calls
        formatted_tool_calls = []
        for i, tool_call in enumerate(tool_calls, start=1):
            tool_call_id = tool_call.id
            function_name = tool_call.function.name
            function_arguments = tool_call.function.arguments
            formatted_str = (
                f"tool_call {i} id: {tool_call_id}\n"
                f"tool_call {i} function name: {function_name}\n"
                f"tool_call {i} arguments: {function_arguments}"
            )
            formatted_tool_calls.append(formatted_str)
        print("Tool calls:\n" + "\n\n".join(formatted_tool_calls))


async def handle_streaming(
    kernel: sk.Kernel,
    chat_function: "KernelFunction",
    user_input: str,
    history: ChatHistory,
    execution_settings: OpenAIPromptExecutionSettings,
) -> None:
    response = kernel.invoke_stream(
        chat_function,
        return_function_results=False,
        user_input=user_input,
        chat_history=history,
    )

    print("Mosscap:> ", end="")
    streamed_chunks: List[OpenAIStreamingChatMessageContent] = []
    tool_call_ids_by_index: Dict[str, Any] = {}

    async for message in response:
        if not execution_settings.auto_invoke_kernel_functions and isinstance(
            message[0], OpenAIStreamingChatMessageContent
        ):
            streamed_chunks.append(message[0])
            if message[0].tool_calls is not None:
                for tc in message[0].tool_calls:
                    if tc.id not in tool_call_ids_by_index:
                        tool_call_ids_by_index[tc.id] = tc
                    else:
                        for tc in message[0].tool_calls:
                            tool_call_ids_by_index[tc.id] += tc
        else:
            print(str(message[0]), end="")

    if streamed_chunks:
        streaming_chat_message = reduce(lambda first, second: first + second, streamed_chunks)
        streaming_chat_message.tool_calls = list(tool_call_ids_by_index.values())
        print("Auto tool calls is disabled, printing returned tool calls...")
        print_tool_calls(streaming_chat_message)

    print("\n")


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
    arguments = KernelArguments(
        user_input=user_input, history=("\n").join([f"{msg.role}: {msg.content}" for msg in history])
    )
    result = await chat_completion_with_tool_call(
        kernel=kernel,
        arguments=arguments,
        chat_plugin_name="ChatBot",
        chat_function_name="Chat",
    )
    print(f"Mosscap:> {result}")

    stream = True
    if stream:
        await handle_streaming(kernel, chat_function, user_input, history, execution_settings)
    else:
        result = await kernel.invoke(chat_function, user_input=user_input, chat_history=history)

        # If tools are used, and auto invoke tool calls is False, the response will be of type
        # OpenAIChatMessageContent with information about the tool calls, which need to be sent
        # back to the model to get the final response.
        if not execution_settings.auto_invoke_kernel_functions and isinstance(
            result.value[0], OpenAIChatMessageContent
        ):
            print_tool_calls(result.value[0])
            return True

        print(f"Mosscap:> {result}")
    return True


async def main() -> None:
    chatting = True
    print(
        "Welcome to the chat bot!\
\n  Type 'exit' to exit.\
\n  Try a math question to see the function calling in action (i.e. what is 3+3?)."
        \n  Type 'exit' to exit.\
        \n  Try a math question to see the function calling in action (i.e. what is 3+3?)."
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
