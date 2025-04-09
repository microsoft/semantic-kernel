# Copyright (c) Microsoft. All rights reserved.

import ast
import asyncio
import json
import math
from collections.abc import AsyncGenerator
from html import escape
from typing import Annotated, Any, Literal

from huggingface_hub import AsyncInferenceClient
from pydantic import HttpUrl

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents import (
    ChatHistory,
    ChatMessageContent,
    FunctionCallContent,
    StreamingChatMessageContent,
    TextContent,
)
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.functions import KernelArguments, kernel_function

kernel = Kernel()


@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def auto_function_invocation_filter(context: AutoFunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    print("\033[92m\n  Function called by Nexus Raven model\033[0m")
    print(f"    \033[96mFunction: {context.function.fully_qualified_name}")
    print(f"    Arguments: {context.arguments}")
    await next(context)
    print(f"    Result: {context.function_result}\n\033[0m")


#########################################################################
# Step 0: Define a custom AI Service, with Prompt Execution settings. ###
# This uses huggingface_hub package, so install that if needed.       ###
#########################################################################


class NexusRavenPromptExecutionSettings(PromptExecutionSettings):
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


class NexusRavenCompletion(TextCompletionClientBase, ChatCompletionClientBase):
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

    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list["ChatMessageContent"]:
        """Creates a chat message content with a function call content within.

        Uses the text content and and parses it into a function call content."""
        result = await self.get_text_contents(
            prompt=chat_history.messages[-1].content,
            settings=settings,
        )
        messages = []
        for part in result[0].text.split(";"):
            try:
                function_call, function_result = await self._execute_function_calls(part, chat_history, **kwargs)
                if function_call:
                    messages.extend([
                        ChatMessageContent(
                            role="assistant", items=[function_call], metadata={"ai_model_id": self.ai_model_id}
                        ),
                        ChatMessageContent(
                            role="tool",
                            items=[function_result],
                            name="nexus",
                            metadata={"ai_model_id": self.ai_model_id},
                        ),
                    ])
                else:
                    messages.append(ChatMessageContent(role="assistant", content=part, ai_model_id=self.ai_model_id))
            except Exception as e:
                messages.append(
                    ChatMessageContent(
                        role="assistant",
                        items=[
                            TextContent(
                                text=f"An error occurred while executing the function call: {e}",
                                ai_model_id=self.ai_model_id,
                            )
                        ],
                    )
                )
                return messages
        return messages

    async def _execute_function_calls(
        self, result: str, chat_history: ChatHistory, **kwargs: Any
    ) -> tuple[FunctionCallContent, FunctionResultContent] | None:
        function_call = result.strip().split("\n")[0].strip("Call:").strip()
        if not function_call:
            return None
        parsed_fc = ast.parse(function_call, mode="eval")
        if not isinstance(parsed_fc.body, ast.Call):
            return None
        idx = 0
        call_stack = {}
        queue = []
        current = parsed_fc.body
        queue.append((idx, parsed_fc.body))
        idx += 1
        while queue:
            current_idx, current = queue.pop(0)
            dependent_on = []
            args = {}
            for keyword in current.keywords:
                if isinstance(keyword.value, ast.Call):
                    queue.append((idx, keyword.value))
                    dependent_on.append(idx)
                    args[keyword.arg] = (idx, keyword.value)
                    idx += 1
                else:
                    args[keyword.arg] = keyword.value.value
            call = {
                "idx": current_idx,
                "func": current.func.id.replace("_", "-", 1),
                "args": args,
                "dependent_on": dependent_on,
                "fcc": None,
                "result": None,
            }
            call_stack[current_idx] = call
        while any(call["result"] is None for call in call_stack.values()):
            await asyncio.gather(*[
                self._execute_function_call(call, chat_history, kwargs.get("kernel"))
                for call in call_stack.values()
                if not any(isinstance(arg, tuple) for arg in call["args"].values()) and call["result"] is None
            ])
            for call in call_stack.values():
                if call["result"] is None:
                    for name, arg in call["args"].items():
                        if isinstance(arg, tuple) and call_stack[arg[0]]["result"] is not None:
                            function_result: FunctionResultContent = call_stack[arg[0]]["result"]
                            call["args"][name] = function_result.result
        return call_stack[0]["fcc"], call_stack[0]["result"]

    async def _execute_function_call(
        self, call_def: dict[str, Any], chat_history: ChatHistory, kernel: Kernel
    ) -> FunctionResultContent:
        """Execute a function call."""
        call_def["fcc"] = FunctionCallContent(
            name=call_def["func"], arguments=json.dumps(call_def["args"]), id=str(call_def["idx"])
        )
        result = await kernel.invoke_function_call(call_def["fcc"], chat_history)
        if not result:
            call_def["result"] = chat_history.messages[-1].items[0]
        else:
            call_def["result"] = result.function_result

    async def get_text_contents(self, prompt: str, settings: NexusRavenPromptExecutionSettings) -> list[TextContent]:
        result = await self.client.text_generation(prompt, **settings.prepare_settings_dict(), stream=False)
        return [TextContent(text=result.strip(), ai_model_id=self.ai_model_id)]

    async def get_streaming_text_contents(self, prompt: str, settings: NexusRavenPromptExecutionSettings):
        raise NotImplementedError("Streaming text contents not implemented.")

    def get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        raise NotImplementedError("Streaming chat message contents not implemented.")

    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        return NexusRavenPromptExecutionSettings


##########################################################
# Step 1: Define the functions you want to articulate. ###
##########################################################


class MathPlugin:
    @kernel_function
    def cylinder_volume(
        self,
        radius: Annotated[float, "The radius of the base of the cylinder."],
        height: Annotated[float, "The height of the cylinder."],
    ):
        """Calculate the volume of a cylinder."""
        if radius < 0 or height < 0:
            raise ValueError("Radius and height must be non-negative.")

        return math.pi * (radius**2) * height

    @kernel_function
    def add(
        self,
        input: Annotated[float, "the first number to add"],
        amount: Annotated[float, "the second number to add"],
    ) -> Annotated[float, "the output is a number"]:
        """Returns the Addition result of the values provided."""
        return MathPlugin.calculator(input, amount, "add")

    @kernel_function
    def subtract(
        self,
        input: Annotated[float, "the first number"],
        amount: Annotated[float, "the number to subtract"],
    ) -> float:
        """Returns the difference of numbers provided."""
        return MathPlugin.calculator(input, amount, "subtract")

    @kernel_function
    def multiply(
        self,
        input: Annotated[float, "the first number"],
        amount: Annotated[float, "the number to multiply with"],
    ) -> float:
        """Returns the product of numbers provided."""
        return MathPlugin.calculator(input, amount, "multiply")

    @kernel_function
    def divide(
        self,
        input: Annotated[float, "the first number"],
        amount: Annotated[float, "the number to divide by"],
    ) -> float:
        """Returns the quotient of numbers provided."""
        return MathPlugin.calculator(input, amount, "divide")

    @staticmethod
    def calculator(
        input_a: float,
        input_b: float,
        operation: Literal["add", "subtract", "multiply", "divide"],
    ):
        """Computes a calculation."""
        match operation:
            case "add":
                return input_a + input_b
            case "subtract":
                return input_a - input_b
            case "multiply":
                return input_a * input_b
            case "divide":
                return input_a / input_b


#############################################################
# Step 2: Let's define some utils for building the prompt ###
#############################################################


@kernel_function
def format_functions_for_prompt():
    filters = {"excluded_plugins": ["kernel"]}
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
            escape(
                f"OPTION:\n<func_start>{func_string}<func_end>\n<docstring_start>\n{func.description}\n<docstring_end>"
            )
        )
    return formatted_functions


#########################################################################
# Step 3: Let's define the two prompts, one for Nexus, one for OpenAI ###
# and add everything to the kernel!                                   ###
#########################################################################

kernel.add_function(
    "kernel",
    function_name="function_call",
    prompt="""{{chat_history}}&lt;human&gt;:
{{kernel-format_functions_for_prompt}}
\n\nUser Query: Question: {{user_query}}
Please pick a function from the above options that best answers the user query and fill in the appropriate arguments.&lt;human_end&gt;""",  # noqa: E501
    template_format="handlebars",
    prompt_execution_settings=NexusRavenPromptExecutionSettings(
        service_id="nexus",
        temperature=0.001,
        max_new_tokens=500,
        do_sample=False,
        stop_sequences=["\nReflection:", "\nThought:"],
    ),
)
kernel.add_function(
    "kernel",
    function_name="chat",
    prompt="""You are a chatbot that gets fed questions and answers, you write out the response to the question based on the answer, but you do not supply underlying math formulas nor do you try to do math yourself, just a nice sentence that repeats the question and gives the answer. {{chat_history}}""",  # noqa: E501
    template_format="handlebars",
    prompt_execution_settings=OpenAIChatPromptExecutionSettings(
        service_id="openai",
        temperature=0.0,
        max_tokens=1000,
    ),
)
kernel.add_plugin(MathPlugin(), "math")
kernel.add_function("kernel", format_functions_for_prompt)
kernel.add_service(
    NexusRavenCompletion(service_id="nexus", ai_model_id="raven", endpoint_url="http://nexusraven.nexusflow.ai")
)
kernel.add_service(OpenAIChatCompletion(service_id="openai"))

############################################
# Step 4: The main function and a runner ###
############################################


async def run_question(user_input: str, chat_history: ChatHistory):
    arguments = KernelArguments(
        user_query=user_input,
        chat_history=chat_history,
        kernel=kernel,
    )
    result = await kernel.invoke(plugin_name="kernel", function_name="function_call", arguments=arguments)
    chat_history.add_user_message(user_input)
    for msg in result.value:
        chat_history.add_message(msg)
    final_result = await kernel.invoke(plugin_name="kernel", function_name="chat", arguments=arguments)
    chat_history.add_message(final_result.value[0])


async def main():
    chat_history = ChatHistory()
    user_input_example = (
        "my cake is 3 centimers high and 20 centimers in radius, can you subtract 200 from that number?"
    )
    print("Welcome to the chatbot!")
    print(
        "This chatbot uses local function calling with Nexus Raven, and OpenAI for the final answer, "
        "it has some math skills so feel free to ask anything about that."
    )
    print(f'For example: "{user_input_example}".')
    print("You can type 'exit' to quit the chatbot.")
    while True:
        try:
            user_input = input("What is your question: ")
        except Exception:
            break
        if user_input == "exit":
            break
        if not user_input:
            user_input = user_input_example

        await run_question(user_input, chat_history)
        print(chat_history.messages[-1].content)
    print("Thanks for chatting with me!")


if __name__ == "__main__":
    asyncio.run(main())
