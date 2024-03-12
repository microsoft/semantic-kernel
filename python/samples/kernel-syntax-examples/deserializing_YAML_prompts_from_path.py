# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_plugin import KernelPlugin

kernel = sk.Kernel()

api_key, org_id = sk.openai_settings_from_dot_env()

kernel.add_service(sk_oai.OpenAIChatCompletion(ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id))

# TODO @jmj - This only tests the case where we explicitly give the path to the YAML file.


async def main() -> None:
    # chat_function: KernelFunction = kernel.create_function_from_prompt_yaml(yaml_text)
    script_directory = os.path.dirname(__file__)
    kernel_plugin: KernelPlugin = kernel.register_plugin_from_path(
        os.path.join(
            script_directory, "serialized_kernel_functions/generate_story.yaml"
        )  # TODO @jmj - Probably could come up with a better name for the directory
    )

    arguments = KernelArguments(
        **{
            "topic": "Dogs",
            "length": 3,
        }
    )

    result: FunctionResult = await kernel.invoke(kernel_plugin["GenerateStory"], arguments)
    response = str(result)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
