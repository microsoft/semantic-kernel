# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.functions.kernel_function_decorator import kernel_function

###################################################################
# The following sample demonstrates how to create a chat          #
# completion call that assists users in solving a question        #
# using a Semantic Kernel Plugin and function calling problems.   #
# The chat plugin guides the user step-by-step through the        #
# solution process using a structured output format based on      #
# either a Pydantic model or a non-Pydantic model                 #
###################################################################


###################################################################
# NOTE: If using Azure OpenAI the the following is required:
# - access to gpt-4o-2024-08-06
# - the 2024-08-01-preview API version
# - if using a token instead of an API KEY, you must have the
#    `Cognitive Services OpenAI Contributor` role assigned to your
#    Azure AD user.
# - flip the `use_azure_openai` flag to `True`
###################################################################
use_azure_openai = True

system_message = """
You are a helpful math tutor. Guide the user through the solution step by step.
"""


# Define a sample plugin to use for function calling
class WeatherPlugin:
    """A sample plugin that provides weather information for cities."""

    @kernel_function(name="get_weather_for_city", description="Get the weather for a city")
    def get_weather_for_city(self, city: Annotated[str, "The input city"]) -> Annotated[str, "The output is a string"]:
        if city == "Boston":
            return "61 and rainy"
        if city == "London":
            return "55 and cloudy"
        if city == "Miami":
            return "80 and sunny"
        if city == "Paris":
            return "60 and rainy"
        if city == "Tokyo":
            return "50 and sunny"
        if city == "Sydney":
            return "75 and sunny"
        if city == "Tel Aviv":
            return "80 and sunny"
        return "31 and snowing"


###################################################################
# OPTION 1: Define the Pydantic model that represents the
# structured output from the OpenAI service. This model will be
# used to parse the structured output from the OpenAI service,
# and ensure that the model correctly outputs the schema based
# on the Pydantic model.
from semantic_kernel.kernel_pydantic import KernelBaseModel  # noqa: E402


class Step(KernelBaseModel):
    explanation: str
    output: str


class Reasoning(KernelBaseModel):
    steps: list[Step]
    final_answer: str


###################################################################


# OPTION 2: Define a non-Pydantic model that should represent the
# structured output from the OpenAI service. This model will be
# converted to the proper JSON Schema and sent to the LLM.
# Uncomment the follow lines and comment out the Pydantic model
# above to use this option.
# class Step:
#     explanation: str
#     output: str


# class Reasoning:
#     steps: list[Step]
#     final_answer: str


###################################################################

kernel = Kernel()

service_id = "structured-output"
if use_azure_openai:
    chat_service = AzureChatCompletion(
        service_id=service_id,
    )
else:
    chat_service = OpenAIChatCompletion(
        service_id=service_id,
    )
kernel.add_service(chat_service)

kernel.add_plugin(WeatherPlugin(), plugin_name="weather")

req_settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8
req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["chat"]})

# NOTE: This is the key setting in this example that tells the OpenAI service
# to return structured output based on the Pydantic model Reasoning.
req_settings.response_format = Reasoning


chat_function = kernel.add_function(
    prompt=system_message + """{{$chat_history}}""",
    function_name="chat",
    plugin_name="chat",
    prompt_execution_settings=req_settings,
)

history = ChatHistory()
history.add_user_message("Using the available plugin, what is the weather in Paris?")


async def main():
    stream = True
    if stream:
        answer = kernel.invoke_stream(
            chat_function,
            chat_history=history,
        )
        print("Mosscap:> ", end="")
        result_content: list[StreamingChatMessageContent] = []
        async for message in answer:
            result_content.append(message[0])
            print(str(message[0]), end="", flush=True)
        if result_content:
            result = "".join([str(content) for content in result_content])
    else:
        result = await kernel.invoke(
            chat_function,
            chat_history=history,
        )
        print(f"Mosscap:> {result}")
    history.add_assistant_message(str(result))


if __name__ == "__main__":
    asyncio.run(main())
