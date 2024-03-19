# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction

yaml_text = """
name: GenerateStory
template: |
  Tell a story about {{$topic}} that is {{$length}} sentences long.
template_format: semantic-kernel
description: A function that generates a story about a topic.
input_variables:
  - name: topic
    description: The topic of the story.
    is_required: true
  - name: length
    description: The number of sentences in the story.
    is_required: true
output_variable:
  description: The generated story.
execution_settings:
  default:
    temperature: 0.5
""".strip()

kernel = sk.Kernel()

api_key, org_id = sk.openai_settings_from_dot_env()

kernel.add_service(sk_oai.OpenAIChatCompletion(ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id))
kernel.add_service(sk_oai.OpenAIChatCompletion(ai_model_id="gpt-4", api_key=api_key, org_id=org_id))


async def main() -> None:
    chat_function: KernelFunction = kernel.create_function_from_prompt_yaml(yaml_text)
    arguments = KernelArguments(
        # PromptExecutionSettings(service_id="gpt-3.5-turbo"),
        **{
            "topic": "Dogs",
            "length": 3,
        },
    )

    result: FunctionResult = await kernel.invoke(chat_function, arguments)
    response = str(result)
    print(response)
    # Print Output:
    # Once there were four dogs named Axel, Tess, Daisy, and Poppy who lived in a cozy little house by the forest.
    # They spent their days chasing squirrels, playing fetch, and napping in the sun.
    # Together, they formed an inseparable bond and lived happily ever after.


if __name__ == "__main__":
    asyncio.run(main())
