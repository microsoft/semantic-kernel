# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import InputVariable, PromptTemplateConfig
from semantic_kernel.utils.settings import openai_settings_from_dot_env


async def main():
    kernel = Kernel()

    useAzureOpenAI = False
    model = "gpt-35-turbo" if useAzureOpenAI else "gpt-3.5-turbo-1106"
    service_id = model

    api_key, org_id = openai_settings_from_dot_env()
    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id, ai_model_id=model, api_key=api_key, org_id=org_id),
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
            InputVariable(name="chat_history", description="The conversation history", is_required=False, default=""),
            InputVariable(name="request", description="The user's request", is_required=True),
        ],
        execution_settings=OpenAIChatPromptExecutionSettings(service_id=service_id, max_tokens=4000, temperature=0.2),
    )

    chat = kernel.add_function(
        function_name="chat",
        plugin_name="ChatBot",
        prompt_template_config=prompt_template_config,
    )

    chat_history = ChatHistory()

    print("User > ")
    while (user_input := input()) != "exit":
        result = await kernel.invoke(
            chat,
            KernelArguments(
                request=user_input,
                chat_history=chat_history,
            ),
        )
        result = str(result)
        print(result)
        chat_history.add_user_message(user_input)
        chat_history.add_assistant_message(result)


if __name__ == "__main__":
    asyncio.run(main())
