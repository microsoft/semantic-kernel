# Copyright (c) Microsoft. All rights reserved.

# TODO @jmj: Finish tests

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments

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
  oai_chat_gpt:
    temperature: 0.6
""".strip()

kernel = sk.Kernel()

api_key, org_id = sk.openai_settings_from_dot_env()

kernel.add_service(
    sk_oai.OpenAIChatCompletion(ai_model_id="gpt-3.5-turbo", service_id="oai_chat_gpt", api_key=api_key, org_id=org_id)
)


async def main() -> None:
    chat_function = kernel.create_function_from_prompt_yaml(yaml_text)

    arguments = KernelArguments(
        **{
            "topic": "Dogs",
            "length": 3,
        }
    )
    result: FunctionResult = await kernel.invoke(chat_function, arguments)
    response = str(result)
    print(response)
    # Print Output:
    # "Once there were three stray dogs who roamed the streets together, searching for scraps of food and shelter. Despite
    # their hardships, they remained loyal to each other, always sticking together through thick and thin. Eventually, a
    # kind-hearted family took them in, giving them a warm home and plenty of love for the rest of their days.'


if __name__ == "__main__":
    asyncio.run(main())
