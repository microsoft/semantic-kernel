# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.chat_completion_services import (
    Services,
    get_chat_completion_service_and_request_settings,
)
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_calling_utils import (
    kernel_function_metadata_to_function_call_format,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.core_plugins.time_plugin import TimePlugin

"""
# Reasoning Models Sample

This sample demonstrates an example of how to use reasoning models such as OpenAI’s o1 and o1-mini for inference.
Reasoning models currently have certain limitations, which are outlined below.

1. Requires API version `2024-09-01-preview` or later.
  - `reasoning_effort` and `developer_message` are only supported in API version `2024-12-01-preview` or later.
  - o1-mini is not supported property `developer_message` `reasoning_effort` now.
2. Developer message must be used instead of system message
3. Parallel tool invocation is currently not supported
4. Token limit settings need to consider both reasoning and completion tokens

# Unsupported Properties ⛔

The following parameters are currently not supported:
- temperature
- top_p
- presence_penalty
- frequency_penalty
- logprobs
- top_logprobs
- logit_bias
- max_tokens
- stream
- tool_choice

# Unsupported Roles ⛔
- system
- tool

# .env examples

OpenAI: semantic_kernel/connectors/ai/open_ai/settings/open_ai_settings.py

```.env
OPENAI_API_KEY=*******************
OPENAI_CHAT_MODEL_ID=o1-2024-12-17
```

Azure OpenAI: semantic_kernel/connectors/ai/open_ai/settings/azure_open_ai_settings.py

```.env
AZURE_OPENAI_API_KEY=*******************
AZURE_OPENAI_ENDPOINT=https://*********.openai.azure.com
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=o1-2024-12-17
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
```

Note: Unsupported features may be added in future updates.
"""

chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(
    Services.OPENAI, instruction_role="developer"
)

# This is the system message that gives the chatbot its personality.
developer_message = """
As an assistant supporting the user,
 you recognize all user input
 as questions or consultations and answer them.
"""

# Create a ChatHistory object
chat_history = ChatHistory()

# Create a kernel and register plugin.
kernel = Kernel()
kernel.add_plugin(TimePlugin(), "time")


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

    # The developer message was newly introduced for reasoning models such as OpenAI’s o1 and o1-mini.
    # `system message` cannot be used with reasoning models.
    chat_history.add_developer_message(developer_message)
    chat_history.add_user_message(user_input)

    if not isinstance(request_settings, OpenAIChatPromptExecutionSettings):
        raise ValueError(f"{type(request_settings).__name__} settings are not supported for this sample.")

    # Set the reasoning effort to "medium" and the maximum completion tokens to 5000.
    request_settings.max_completion_tokens = 5000
    request_settings.reasoning_effort = "medium"

    # enable the function calling and disable parallel tool calls for reasoning models.
    request_settings.parallel_tool_calls = None
    request_settings.tool_choice = None
    request_settings.tools = [
        kernel_function_metadata_to_function_call_format(f) for f in kernel.get_full_list_of_function_metadata()
    ]

    # Get the chat message content from the chat completion service.
    response = await chat_completion_service.get_chat_message_content(
        chat_history=chat_history,
        settings=request_settings,
        kernel=kernel,
    )

    if not response:
        return True

    function_calls = [item for item in response.items if isinstance(item, FunctionCallContent)]
    if len(function_calls) == 0:
        print(f"Mosscap:> {response}")
        chat_history.add_message(response)
        return True

    # Invoke the function calls and update the chat history with the results.
    print(f"processing {len(function_calls)} tool calls")
    await asyncio.gather(
        *[
            kernel.invoke_function_call(
                function_call=function_call,
                chat_history=chat_history,
                function_call_count=len(function_calls),
                request_index=0,
            )
            for function_call in function_calls
        ],
    )

    # Convert the last tool message to a user message.
    fc_results = [item for item in chat_history.messages[-1].items if isinstance(item, FunctionResultContent)]

    result_prompt: list[str] = ["FUNCTION CALL RESULT"]
    for fc_result in fc_results:
        result_prompt.append(f"- {fc_result.plugin_name}: {fc_result.result}")

    chat_history.remove_message(chat_history.messages[-1])
    chat_history.add_user_message("\n".join(result_prompt))
    print("Tools:> ", "\n".join(result_prompt))

    # Get the chat message content from the chat completion service.
    request_settings.tools = None
    response = await chat_completion_service.get_chat_message_content(
        chat_history=chat_history,
        settings=request_settings,
    )

    # Add the chat message to the chat history to keep track of the conversation.
    if response:
        print(f"Mosscap:> {response}")
        chat_history.add_message(response)

    return True


async def main() -> None:
    # Start the chat loop. The chat loop will continue until the user types "exit".
    chatting = True
    while chatting:
        chatting = await chat()

    # Sample output:
    # User:> What time is it?
    # Tools:>  FUNCTION CALL RESULT
    #          - time: Thursday, January 09, 2025 05:41 AM
    # Mosscap:> The current time is 05:41 AM.


if __name__ == "__main__":
    asyncio.run(main())
