# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel
from openai import OpenAI

# 
# Please Replace the url with the real NIM endpoint.
#
nim_url = "http://0.0.0.0:8000/v1"

class NLlama3Plugin:
    """A sample plugin that provides response from NIM."""

    @kernel_function(name="get_nllama3_opinion", description="Get the opinion of nllama3")
    def get_nllama3_opinion(self, question: Annotated[str, "The input question"]) -> Annotated[str, "The output is a string"]:
        
        prompt = question.replace("nllama3", "you")
        # Make sure model name match the model of NIM you deploy
        client = OpenAI(base_url=nim_url, api_key="not-used")
        response = client.completions.create(
            model="meta/llama-3.1-8b-instruct",
            prompt=prompt,
            max_tokens=64,
            stream=False
        )
        completion = response.choices[0].text
        return completion


async def main():
    kernel = Kernel()

    use_azure_openai = True
    service_id = "function_calling"
    if use_azure_openai:
        # Please make sure your AzureOpenAI Deployment allows for function calling
        ai_service = AzureChatCompletion(
            service_id=service_id,
        )
    else:
        ai_service = OpenAIChatCompletion(
            service_id=service_id,
            ai_model_id="gpt-3.5-turbo-1106",
        )
    kernel.add_service(ai_service)

    kernel.add_plugin(NLlama3Plugin(), plugin_name="nllama3")

    # Example 1: Use automated function calling with a non-streaming prompt
    print("========== Example 1: Use automated function calling with a non-streaming prompt ==========")
    settings: OpenAIChatPromptExecutionSettings = kernel.get_prompt_execution_settings_from_service_id(
        service_id=service_id
    )
    settings.function_call_behavior = FunctionCallBehavior.EnableFunctions(
        auto_invoke=True, filters={"included_plugins": ["nllama3"]}
    )

    print(
        await kernel.invoke_prompt(
            function_name="prompt_test",
            plugin_name="weather_test",
            prompt="What does nllama3 think about global warming?",
            settings=settings,
        )
    )

    # Example 2: Use automated function calling with a streaming prompt
    print("========== Example 2: Use automated function calling with a streaming prompt ==========")
    settings: OpenAIChatPromptExecutionSettings = kernel.get_prompt_execution_settings_from_service_id(
        service_id=service_id
    )
    settings.function_call_behavior = FunctionCallBehavior.EnableFunctions(
        auto_invoke=True, filters={"included_plugins": ["nllama3"]}
    )

    result = kernel.invoke_prompt_stream(
        function_name="prompt_test",
        plugin_name="weather_test",
        prompt="What does nllama3 think about global warming?",
        settings=settings,
    )

    async for message in result:
        print(str(message[0]), end="")
    print("")

    # Example 3: Use manual function calling with a non-streaming prompt
    print("========== Example 3: Use manual function calling with a non-streaming prompt ==========")

    chat: OpenAIChatCompletion | AzureChatCompletion = kernel.get_service(service_id)
    chat_history = ChatHistory()
    settings: OpenAIChatPromptExecutionSettings = kernel.get_prompt_execution_settings_from_service_id(
        service_id=service_id
    )
    settings.function_call_behavior = FunctionCallBehavior.EnableFunctions(
        auto_invoke=False, filters={"included_plugins": ["nllama3"]}
    )
    chat_history.add_user_message(
        "What does nllama3 think about global warming?"
    )

    while True:
        # The result is a list of ChatMessageContent objects, grab the first one
        result = await chat.get_chat_message_contents(chat_history=chat_history, settings=settings, kernel=kernel)
        result = result[0]

        if result.content:
            print(result.content)

        if not result.items or not any(isinstance(item, FunctionCallContent) for item in result.items):
            break

        chat_history.add_message(result)
        for item in result.items:
            await chat._process_function_call(
                function_call=item,
                kernel=kernel,
                chat_history=chat_history,
                arguments=KernelArguments(),
                function_call_count=1,
                request_index=0,
                function_call_behavior=settings.function_call_behavior,
            )


if __name__ == "__main__":
    asyncio.run(main())
