# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
from functools import reduce
from typing import Annotated

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory, FunctionResultContent, StreamingChatMessageContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create a chat
completion call that assists users in solving a question
using a Semantic Kernel Plugin and function calling problems.
The chat plugin guides the user step-by-step through the
solution process using a structured output format based on
a Pydantic model.

NOTE: If using Azure OpenAI the the following is required:
- access to gpt-4o-2024-08-06
- the 2024-08-01-preview API version
- if using a token instead of an API KEY, you must have the
   `Cognitive Services OpenAI Contributor` role assigned to your
   Azure AD user.
- flip the `use_azure_openai` flag to `True`
"""

system_message = """
You are a helpful assistant who provides answers to the user's questions in structured JSON format.
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


"""
Define the Pydantic model that represents the
structured output from the OpenAI service. This model will be
used to parse the structured output from the OpenAI service,
and ensure that the model correctly outputs the schema based
on the Pydantic model.
"""
from pydantic import BaseModel, ConfigDict  # noqa: E402

# Note: The `extra=forbid` means to forbid extra fields during model initialization
# It is required to ensure that the model is strict and does not
# accept any extra fields that are not defined in the model.


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")
    explanation: str
    output: str


class Reasoning(BaseModel):
    model_config = ConfigDict(extra="forbid")
    steps: list[Step]
    final_answer: str


kernel = Kernel()

# You can select from the following chat completion services:
# Note: the model must allow for structured outputs.
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
# - Services.DEEPSEEK
# Please make sure you have configured your environment correctly for the selected chat completion service.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.AZURE_OPENAI)
kernel.add_service(chat_completion_service)

kernel.add_plugin(WeatherPlugin(), plugin_name="weather")

request_settings.response_format = Reasoning
request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["chat"]})

chat_function = kernel.add_function(
    prompt=system_message + """{{$chat_history}}""",
    function_name="chat",
    plugin_name="chat",
    prompt_execution_settings=request_settings,
)

history = ChatHistory()
history.add_user_message("What is the weather in Paris?")


async def main():
    stream = False
    if stream:
        answer = kernel.invoke_stream(
            chat_function,
            chat_history=history,
        )
        print("Mosscap:> ", end="")
        result_content: list[StreamingChatMessageContent] = []
        async for message in answer:
            if not any(isinstance(item, FunctionResultContent | FunctionResultContent) for item in message[0].items):
                print(str(message[0]), end="", flush=True)
                result_content.append(message[0])
        print()
        if result_content:
            full_response: StreamingChatMessageContent = reduce(lambda x, y: x + y, result_content)
            reasoned_result = Reasoning.model_validate(json.loads(full_response.content))
            print("Result formatted in JSON:")
            print(f"{reasoned_result.model_dump_json(indent=4)}")
            history.add_assistant_message(str(full_response))
    else:
        result = await kernel.invoke(
            chat_function,
            chat_history=history,
        )
        reasoned_result = Reasoning.model_validate(json.loads(result.value[0].content))
        print(f"{reasoned_result.model_dump_json(indent=4)}")
        history.add_assistant_message(str(result))

    """
    Sample Output:

    {
        "steps": [
            {
                "explanation": "User requested the current weather condition in Paris, so I utilized the 'weather-get_weather_for_city' function to retrieve the data.",
                "output": "The weather in Paris is 60 degrees Fahrenheit and rainy."
            }
        ],
        "final_answer": "The current weather in Paris is 60 degrees Fahrenheit and rainy."
    }
    """  # noqa: E501


if __name__ == "__main__":
    asyncio.run(main())
