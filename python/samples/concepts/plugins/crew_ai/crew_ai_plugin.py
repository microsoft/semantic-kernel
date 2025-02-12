# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins.crew_ai import CrewAIEnterprise
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata

logging.basicConfig(level=logging.INFO)


async def using_crew_ai_enterprise():
    # Create an instance of the CrewAI Enterprise Crew
    async with CrewAIEnterprise() as crew:
        #####################################################################
        #              Using the CrewAI Enterprise Crew directly            #
        #####################################################################

        # The required inputs for the Crew must be known in advance. This example is modeled after the
        # Enterprise Content Marketing Crew Template and requires the following inputs:
        inputs = {"company": "CrewAI", "topic": "Agentic products for consumers"}

        # Invoke directly with our inputs
        kickoff_id = await crew.kickoff(inputs)
        print(f"CrewAI Enterprise Crew kicked off with ID: {kickoff_id}")

        # Wait for completion
        result = await crew.wait_for_crew_completion(kickoff_id)
        print("CrewAI Enterprise Crew completed with the following result:")
        print(result)

        #####################################################################
        #              Using the CrewAI Enterprise as a Plugin              #
        #####################################################################

        # Define the description of the Crew. This will used as the semantic description of the plugin.
        crew_description = (
            "Conducts thorough research on the specified company and topic to identify emerging trends,"
            "analyze competitor strategies, and gather data-driven insights."
        )

        # The required inputs for the Crew must be known in advance. This example is modeled after the
        # Enterprise Content Marketing Crew Template and requires string inputs for the company and topic.
        # We need to describe the type and purpose of each input to allow the LLM to invoke the crew as expected.
        crew_input_parameters = [
            KernelParameterMetadata(
                name="company",
                type="string",
                type_object=str,
                description="The name of the company that should be researched",
                is_required=True,
            ),
            KernelParameterMetadata(
                name="topic",
                type="string",
                type_object=str,
                description="The topic that should be researched",
                is_required=True,
            ),
        ]

        # Create the CrewAI Plugin. This builds a plugin that can be added to the Kernel and invoked like any other
        # plugin. The plugin will contain the following functions:
        # - kickoff: Starts the Crew with the specified inputs and returns the Id of the scheduled kickoff.
        # - kickoff_and_wait: Starts the Crew with the specified inputs and waits for the Crew to complete before
        #   returning the result.
        # - wait_for_completion: Waits for the specified Crew kickoff to complete and returns the result.
        # - get_status: Gets the status of the specified Crew kickoff.
        crew_plugin = crew.create_kernel_plugin(
            name="EnterpriseContentMarketingCrew",
            description=crew_description,
            parameters=crew_input_parameters,
        )

        # Configure the kernel for chat completion and add the CrewAI plugin.
        kernel, chat_completion, settings = configure_kernel_for_chat()
        kernel.add_plugin(crew_plugin)

        # Create a chat history to store the system message, initial messages, and the conversation.
        history = ChatHistory()
        history.add_system_message("You are an AI assistant that can help me with research.")
        history.add_user_message(
            "I'm looking for emerging marketplace trends about Crew AI and their concumer AI products."
        )

        # Invoke the chat completion service with enough information for the CrewAI plugin to be invoked.
        response = await chat_completion.get_chat_message_content(history, settings, kernel=kernel)
        print(response)

        # expected output:
        # INFO:semantic_kernel.connectors.ai.open_ai.services.open_ai_handler:OpenAI usage: ...
        # INFO:semantic_kernel.connectors.ai.chat_completion_client_base:processing 1 tool calls in parallel.
        # INFO:semantic_kernel.kernel:Calling EnterpriseContentMarketingCrew-kickoff_and_wait function with args:
        #   {"company":"Crew AI","topic":"emerging marketplace trends in consumer AI products"}
        # INFO:semantic_kernel.functions.kernel_function:Function EnterpriseContentMarketingCrew-kickoff_and_wait
        #   invoking.
        # INFO:semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise:CrewAI Crew kicked off with Id: *****
        # INFO:semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise:CrewAI Crew with kickoff Id: ***** completed with
        #   status: SUCCESS
        # INFO:semantic_kernel.functions.kernel_function:Function EnterpriseContentMarketingCrew-kickoff_and_wait
        #   succeeded.
        # Here are some emerging marketplace trends related to Crew AI and their consumer AI products, along with
        #   suggested content pieces to explore these trends: ...


def configure_kernel_for_chat() -> tuple[Kernel, ChatCompletionClientBase, PromptExecutionSettings]:
    kernel = Kernel()

    # You can select from the following chat completion services that support function calling:
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
    chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.OPENAI)

    # Configure the function choice behavior. Here, we set it to Auto, where auto_invoke=True by default.
    # With `auto_invoke=True`, the model will automatically choose and call functions as needed.
    request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Pass the request settings to the kernel arguments.
    kernel.add_service(chat_completion_service)
    return kernel, chat_completion_service, request_settings


if __name__ == "__main__":
    asyncio.run(using_crew_ai_enterprise())
