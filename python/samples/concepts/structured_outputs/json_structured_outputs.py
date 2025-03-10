# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent

###################################################################
# The following sample demonstrates how to create a chat          #
# completion call that assists users in solving math problems.    #
# The bot guides the user step-by-step through the solution       #
# process using a structured output format based on either a      #
# Pydantic model or a non-Pydantic model.                         #
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
use_azure_openai = False

system_message = """
You are a helpful math tutor. Guide the user through the solution step by step.
"""


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
        reasoned_result = Reasoning.model_validate_json(result.value[0].content)
        print(f"Mosscap:> {reasoned_result}")
    history.add_assistant_message(str(result))


if __name__ == "__main__":
    asyncio.run(main())
