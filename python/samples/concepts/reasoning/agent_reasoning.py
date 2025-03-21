# Copyright (c) Microsoft. All rights reserved.

import asyncio
from collections.abc import Awaitable, Callable

from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.filters import AutoFunctionInvocationContext, FilterTypes
from semantic_kernel.functions.kernel_arguments import KernelArguments

"""
# Reasoning Agents Sample

This sample demonstrates an example of how to use reasoning models such as OpenAI’s o1 and o1-mini for Agents.
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

agent = ChatCompletionAgent(
    service=OpenAIChatCompletion(service_id="reasoning", instruction_role="developer"),
    arguments=KernelArguments(
        settings=OpenAIChatPromptExecutionSettings(
            service_id="reasoning",
            max_completion_tokens=5000,
            reasoning_effort="medium",
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )
    ),
    plugins=[TimePlugin()],
)
# Set the reasoning effort to "medium" and the maximum completion tokens to 5000.
# also set the function_choice_behavior to auto and that includes auto invoking the functions.


# Create a ChatHistory object
# The reasoning models use developer instead of system, but because we set the instruction_role to developer,
# we can use the system message as the developer message.
chat_history = ChatHistory(
    system_message="""
As an assistant supporting the user,
you recognize all user input
as questions or consultations and answer them.
"""
)


@agent.kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def auto_function_invocation_filter(
    context: AutoFunctionInvocationContext, next: Callable[[AutoFunctionInvocationContext], Awaitable[None]]
) -> None:
    await next(context)
    print("Tools:>  FUNCTION CALL RESULT")
    print(f"       - time: {context.function_result}")


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

    chat_history.add_user_message(user_input)

    # Get the chat message content from the chat completion service.
    response = await agent.get_response(history=chat_history)
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
