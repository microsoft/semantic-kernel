# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json

from pydantic import BaseModel, ConfigDict

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory, StreamingChatMessageContent

"""
The following sample demonstrates how to create a chat
completion call that assists users in solving math problems.
The bot guides the user step-by-step through the solution
process using a structured output format based on either a
Pydantic model or a non-Pydantic model.


NOTE: If using Azure OpenAI the the following is required:
- access to gpt-4o-2024-08-06
- the 2024-08-01-preview API version
- if using a token instead of an API KEY, you must have the
   `Cognitive Services OpenAI Contributor` role assigned to your
   Azure AD user.
- flip the `use_azure_openai` flag to `True`
"""

system_message = """
You are a helpful math tutor. Guide the user through the solution step by step.
"""

"""
Define the Pydantic model that represents the
structured output from the OpenAI service. This model will be
used to parse the structured output from the OpenAI service,
and ensure that the model correctly outputs the schema based
on the Pydantic model.
"""

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

request_settings.max_tokens = 2000
request_settings.temperature = 0.7
request_settings.top_p = 0.8
request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["chat"]})

# NOTE: This is the key setting in this example that tells the OpenAI service
# to return structured output based on the Pydantic model Reasoning.
request_settings.response_format = Reasoning


chat_function = kernel.add_function(
    prompt=system_message + """{{$chat_history}}""",
    function_name="chat",
    plugin_name="chat",
    prompt_execution_settings=request_settings,
)

history = ChatHistory()
history.add_user_message("how can I solve 8x + 7y = -23, and 4x=12?")


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
            result_content.append(message[0])
            print(str(message[0]), end="", flush=True)
        if result_content:
            result = "".join([str(content) for content in result_content])
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
