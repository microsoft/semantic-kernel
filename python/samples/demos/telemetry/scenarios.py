# Copyright (c) Microsoft. All rights reserved.

from opentelemetry import trace

from samples.demos.telemetry.demo_plugins import LocationPlugin, WeatherPlugin
from samples.demos.telemetry.repo_utils import get_sample_plugin_path
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


def set_up_kernel() -> Kernel:
    # Create a kernel and add services and plugins
    kernel = Kernel()

    # All built-in AI services are instrumented with telemetry.
    # Select any AI service to see the telemetry in action.
    kernel.add_service(OpenAIChatCompletion(service_id="open_ai"))
    # kernel.add_service(
    #     AzureAIInferenceChatCompletion(
    #         ai_model_id="serverless-deployment",
    #         service_id="azure-ai-inference",
    #     )
    # )
    # kernel.add_service(GoogleAIChatCompletion(service_id="google_ai"))

    if (sample_plugin_path := get_sample_plugin_path()) is None:
        raise FileNotFoundError("Sample plugin path not found.")
    kernel.add_plugin(
        plugin_name="WriterPlugin",
        parent_directory=sample_plugin_path,
    )
    kernel.add_plugin(WeatherPlugin(), "WeatherPlugin")
    kernel.add_plugin(LocationPlugin(), "LocationPlugin")

    return kernel


#############################################################
# Below are scenarios that are instrumented with telemetry. #
#############################################################


async def run_ai_service(stream: bool = False) -> None:
    """Run an AI service.

    This function runs an AI service and prints the output.
    Telemetry will be collected for the service execution behind the scenes,
    and the traces will be sent to the configured telemetry backend.

    The telemetry will include information about the AI service execution.

    Args:
        stream (bool): Whether to use streaming for the plugin
    """
    kernel = set_up_kernel()

    ai_service: AIServiceClientBase = kernel.get_service()

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("Scenario: AI Service") as current_span:
        print("Running scenario: AI Service")
        try:
            if isinstance(ai_service, ChatCompletionClientBase):
                chat_history = ChatHistory()
                chat_history.add_user_message("Why is the sky blue in one sentence?")

                if not stream:
                    responses = await ai_service.get_chat_message_contents(chat_history, PromptExecutionSettings())
                    print(responses[0].content)
                else:
                    async for update in ai_service.get_streaming_chat_message_contents(
                        chat_history, PromptExecutionSettings()
                    ):
                        print(update[0].content, end="")
                    print()
            elif isinstance(ai_service, TextCompletionClientBase):
                if not stream:
                    completion = await ai_service.get_text_contents(
                        "Why is the sky blue in one sentence?", PromptExecutionSettings()
                    )
                    print(completion)
                else:
                    async for update in ai_service.get_streaming_text_contents(
                        "Why is the sky blue?", PromptExecutionSettings()
                    ):
                        print(update[0].content, end="")
                    print()
            else:
                raise ValueError("AI service not recognized.")
        except Exception as e:
            current_span.record_exception(e)
            print(f"Error running AI service: {e}")


async def run_kernel_function(stream: bool = False) -> None:
    """Run a kernel function.

    This function runs a kernel function and prints the output.
    Telemetry will be collected for the function execution behind the scenes,
    and the traces will be sent to the configured telemetry backend.

    The telemetry will include information about the kernel function execution
    and the AI service execution.

    Args:
        stream (bool): Whether to use streaming for the plugin invocation.
    """
    kernel = set_up_kernel()

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("Scenario: Kernel Plugin") as current_span:
        print("Running scenario: Kernel Plugin")
        try:
            plugin = kernel.get_plugin("WriterPlugin")

            if not stream:
                poem = await kernel.invoke(
                    function=plugin["ShortPoem"],
                    arguments=KernelArguments(
                        input="Write a poem about John Doe.",
                    ),
                )
                print(f"Poem:\n{poem}")
            else:
                print("Poem:")
                async for update in kernel.invoke_stream(
                    function=plugin["ShortPoem"],
                    arguments=KernelArguments(
                        input="Write a poem about John Doe.",
                    ),
                ):
                    print(update[0].content, end="")
                print()
        except Exception as e:
            current_span.record_exception(e)
            print(f"Error running kernel plugin: {e}")


async def run_auto_function_invocation(stream: bool = False) -> None:
    """Run a task with auto function invocation.

    This function runs a task with auto function invocation and prints the output.
    Telemetry will be collected for the task execution behind the scenes,
    and the traces will be sent to the configured telemetry backend.

    The telemetry will include information about the auto function invocation loop,
    the AI service execution, and the kernel function execution.

    Args:
        stream (bool): Whether to use streaming for the prompt.
    """
    kernel = set_up_kernel()

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("Scenario: Auto Function Invocation") as current_span:
        print("Running scenario: Auto Function Invocation")
        try:
            if not stream:
                result = await kernel.invoke_prompt(
                    "What is the weather like in my location?",
                    arguments=KernelArguments(
                        settings=PromptExecutionSettings(
                            function_choice_behavior=FunctionChoiceBehavior.Auto(
                                filters={"excluded_plugins": ["WriterPlugin"]}
                            ),
                        ),
                    ),
                )

                print(result)
            else:
                async for update in kernel.invoke_prompt_stream(
                    "What is the weather like in my location?",
                    arguments=KernelArguments(
                        settings=PromptExecutionSettings(
                            function_choice_behavior=FunctionChoiceBehavior.Auto(
                                filters={"excluded_plugins": ["WriterPlugin"]}
                            ),
                        ),
                    ),
                ):
                    print(update[0].content, end="")
                print()
        except Exception as e:
            current_span.record_exception(e)
            print(f"Error running auto function invocation: {e}")
