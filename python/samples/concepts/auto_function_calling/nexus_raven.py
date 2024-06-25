# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import math
from typing import Annotated, Any

from huggingface_hub import AsyncInferenceClient
from pydantic import HttpUrl

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments


class HuggingFaceHubPromptExecutionSettings(PromptExecutionSettings):
    do_sample: bool = True
    max_new_tokens: int | None = None
    stop_sequences: Any = None
    temperature: float | None = None
    top_p: float | None = None

    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Prepare the settings dictionary."""
        return self.model_dump(
            include={"max_new_tokens", "temperature", "top_p", "do_sample", "stop_sequences"},
            exclude_unset=False,
            exclude_none=True,
            by_alias=True,
        )


class HuggingFaceEndpoint(TextCompletionClientBase):
    """To use this class, you should have installed the ``huggingface_hub`` package, and
    the environment variable ``HUGGINGFACEHUB_API_TOKEN`` set with your API token,
    or given as a named parameter to the constructor."""

    client: AsyncInferenceClient

    def __init__(
        self,
        service_id: str,
        ai_model_id: str,
        endpoint_url: HttpUrl,
        api_token: str | None = None,
        client: AsyncInferenceClient | None = None,
    ):
        if not client:
            client = AsyncInferenceClient(model=endpoint_url, token=api_token)
        super().__init__(service_id=service_id, ai_model_id=ai_model_id, client=client)

    async def get_text_contents(
        self, prompt: str, settings: HuggingFaceHubPromptExecutionSettings
    ) -> list[TextContent]:
        result = await self.client.text_generation(prompt, **settings.prepare_settings_dict(), stream=False)
        return [TextContent(text=result, ai_model_id=self.ai_model_id)]

    async def get_streaming_text_contents(self, prompt: str, settings: HuggingFaceHubPromptExecutionSettings):
        raise NotImplementedError("Streaming chat message contents not implemented.")

    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        return HuggingFaceHubPromptExecutionSettings


##########################################################
# Step 1: Define the functions you want to articulate. ###
##########################################################


@kernel_function
def cylinder_volume(
    radius: Annotated[float, "The radius of the base of the cylinder."],
    height: Annotated[float, "The height of the cylinder."],
):
    """Calculate the volume of a cylinder."""
    if radius < 0 or height < 0:
        raise ValueError("Radius and height must be non-negative.")

    return math.pi * (radius**2) * height


kernel = Kernel()
kernel.add_plugin(MathPlugin(), "math")
kernel.add_plugin(TimePlugin(), "time")
kernel.add_function("math", cylinder_volume)

#############################################################
# Step 2: Let's define some utils for building the prompt ###
#############################################################


@kernel_function
def format_functions_for_prompt():
    filters = {"exclude_plugins": ["kernel"]}
    functions = kernel.get_list_of_function_metadata(filters)
    formatted_functions = []
    for func in functions:
        args_strings = []
        for arg in func.parameters:
            arg_string = f"{arg.name}: {arg.type_}"
            if arg.default_value:
                arg_string += f" = {arg.default_value}"
            args_strings.append(arg_string)
        func_string = f"{func.fully_qualified_name.replace('-', '_')}({', '.join(args_strings)})"
        formatted_functions.append(
            f"OPTION:\n<func_start>{func_string}<func_end>\n<docstring_start>\n{func.description}\n<docstring_end>"
        )
    return formatted_functions


kernel.add_function("kernel", format_functions_for_prompt)

##############################
# Step 3: Construct Prompt ###
##############################


def function_call_string_to_function_call_content(function_call: str) -> FunctionCallContent:
    """Convert a function call string to a FunctionCallContent object."""
    function_call = function_call.strip()
    function_name, args = function_call.split("(")
    function_name = function_name.replace("_", "-")
    args = args.strip(")").split(",")
    arguments = {}
    for arg in args:
        key, value = arg.split("=")
        arguments[key.strip()] = value.strip()

    return FunctionCallContent(id="manual", name=function_name, arguments=json.dumps(arguments))


async def execute_function_call(kernel: Kernel, function_call: FunctionCallContent):
    """Execute a function call."""
    function = kernel.get_function_from_fully_qualified_function_name(function_call.name)
    args = function_call.to_kernel_arguments()
    return await function.invoke(kernel=kernel, arguments=args)


async def main():
    # Build the model
    nexus = HuggingFaceEndpoint(service_id="nexus", ai_model_id="raven", endpoint_url="http://nexusraven.nexusflow.ai")

    kernel.add_service(nexus)
    prompt = """<human>:
    {{kernel-format_functions_for_prompt}}
    \n\nUser Query: Question: {{user_query}}
    Please pick a function from the above options that best answers the user query and fill in the appropriate arguments.<human_end>
    """
    func = kernel.add_function(
        function_name="function_call",
        plugin_name="kernel",
        prompt=prompt,
        template_format="handlebars",
    )
    arguments = KernelArguments(
        settings={
            "nexus": HuggingFaceHubPromptExecutionSettings(
                temperature=0.001, max_new_tokens=400, do_sample=False, stop_sequences=["\nReflection:", "\nThought:"]
            )
        },
        user_query="What is 1+10?",
    )

    result = await func.invoke(kernel=kernel, arguments=arguments)
    function_call = result.value[0].text.strip().split("\n")[0].strip("Call: ")
    print("Function Call:", function_call)
    fcc = function_call_string_to_function_call_content(function_call)
    print(fcc)
    result = await execute_function_call(kernel, fcc)

    print("Model Output:", function_call)
    print("Execution Result:", result)

    prompt = construct_prompt(
        "I have a cake that is about 3 centimenters high and 200 centimeters in diameter. How much cake do I have?"
    )
    model_output = text_gen(
        prompt,
        do_sample=False,
        max_new_tokens=400,
        return_full_text=False,
        stop=["\nReflection:"],
    )
    result = execute_function_call(model_output)

    print("Model Output:", model_output)
    print("Execution Result:", result)


if __name__ == "__main__":
    asyncio.run(main())
