# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
from samples.sk_service_configurator import add_service
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins import ConversationSummaryPlugin
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel=kernel, use_chat=True)

    service_id = "default"
    execution_settings = PromptExecutionSettings(
        service_id=service_id,
        max_tokens=ConversationSummaryPlugin._max_tokens,
        temperature=0.1,
        top_p=0.5,
    )

    template = (
        "BEGIN CONTENT TO SUMMARIZE:\n{{" + "$history" + "}}\n{{" + "$input" + "}}\n"
        "END CONTENT TO SUMMARIZE.\nSummarize the conversation in 'CONTENT TO"
        " SUMMARIZE',            identifying main points of discussion and any"
        " conclusions that were reached.\nDo not incorporate other general"
        " knowledge.\nSummary is in plain text, in complete sentences, with no markup"
        " or tags.\n\nBEGIN SUMMARY:\n"
    )

    prompt_template_config = PromptTemplateConfig(
        template=template,
        description="Given a section of a conversation transcript, summarize the part of the conversation.",
        execution_settings=execution_settings,
        InputVariables=[
            InputVariable(name="input", description="The user input", is_required=True),
            InputVariable(
                name="history",
                description="The history of the conversation",
                is_required=True,
            ),
        ],
    )

    # Import the ConversationSummaryPlugin
    kernel.add_plugin(
        ConversationSummaryPlugin(
            kernel=kernel, prompt_template_config=prompt_template_config
        ),
        plugin_name="ConversationSummaryPlugin",
    )

    summarize_function = kernel.get_function(
        plugin_name="ConversationSummaryPlugin", function_name="SummarizeConversation"
    )

    # Create the history
    history = ChatHistory()

    while True:
        try:
            request = input("User:> ")
        except KeyboardInterrupt:
            print("\n\nExiting chat...")
            return False
        except EOFError:
            print("\n\nExiting chat...")
            return False

        if request == "exit":
            print("\n\nExiting chat...")
            return False

        result = await kernel.invoke(
            summarize_function,
            input=request,
            history=history,
        )

        # Add the request to the history
        history.add_user_message(request)
        history.add_assistant_message(str(result))

        print(f"Assistant:> {result}")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
