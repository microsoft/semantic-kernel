# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


async def main():
    kernel = sk.Kernel()

    useAzureOpenAI = False
    model = "gpt-35-turbo" if useAzureOpenAI else "gpt-3.5-turbo-1106"
    service_id = model

    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_service(
        sk_oai.OpenAIChatCompletion(service_id=service_id, ai_model_id=model, api_key=api_key, org_id=org_id),
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
        execution_settings=sk_oai.OpenAIChatPromptExecutionSettings(
            service_id=service_id, max_tokens=4000, temperature=0.2
        ),
    )

    chat = kernel.create_function_from_prompt(
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
