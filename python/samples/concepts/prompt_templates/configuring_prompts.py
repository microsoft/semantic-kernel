# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import InputVariable, PromptTemplateConfig

kernel = Kernel()

useAzureOpenAI = False
model = "gpt-35-turbo" if useAzureOpenAI else "gpt-3.5-turbo"

kernel.add_service(
    OpenAIChatCompletion(service_id=model, ai_model_id=model),
)

template = """

Previous information from chat:
{{$chat_history}}

User: {{$request}}
Assistant:
"""

print("--- Rendered Prompt ---")
prompt_template_config = PromptTemplateConfig(
    template=template,
    name="chat",
    description="Chat with the assistant",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(
            name="chat_history",
            description="The conversation history",
            is_required=False,
            default="",
        ),
        InputVariable(
            name="request", description="The user's request", is_required=True
        ),
    ],
    execution_settings=OpenAIChatPromptExecutionSettings(
        service_id=model, max_tokens=4000, temperature=0.2
    ),
)

chat_function = kernel.add_function(
    function_name="chat",
    plugin_name="ChatBot",
    prompt_template_config=prompt_template_config,
)

chat_history = ChatHistory()


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

    answer = await kernel.invoke(
        function=chat_function,
        arguments=KernelArguments(
            request=user_input,
            chat_history=chat_history,
        ),
    )
    chat_history.add_user_message(user_input)
    chat_history.add_assistant_message(str(answer))
    print(f"Mosscap:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
