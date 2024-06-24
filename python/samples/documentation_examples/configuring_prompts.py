# Copyright (c) Microsoft. All rights reserved.
import asyncio

from service_configurator import add_service

import semantic_kernel as sk
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
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

    # The following execution settings are used for the ConversationSummaryPlugin
    execution_settings = PromptExecutionSettings(
        service_id=service_id, max_tokens=ConversationSummaryPlugin._max_tokens, temperature=0.1, top_p=0.5
    )
    prompt_template_config = PromptTemplateConfig(
        template=ConversationSummaryPlugin._summarize_conversation_prompt_template,
        description="Given a section of a conversation transcript, summarize the part of" " the conversation.",
        execution_settings=execution_settings,
    )

    # Import the ConversationSummaryPlugin
    kernel.import_plugin_from_object(
        ConversationSummaryPlugin(kernel=kernel, prompt_template_config=prompt_template_config),
        plugin_name="ConversationSummaryPlugin",
    )

    # Create the history
    history = ChatHistory()

    # Create the prompt with the ConversationSummaryPlugin
    prompt = """{{ConversationSummaryPlugin.SummarizeConversation $history}}
    User: {{$request}}
    Assistant:  """

    # These execution settings are tied to the chat function, created below.
    execution_settings = kernel.get_service(service_id).instantiate_prompt_execution_settings(service_id=service_id)
    chat_prompt_template_config = PromptTemplateConfig(
        template=prompt,
        description="Chat with the assistant",
        execution_settings=execution_settings,
        input_variables=[
            InputVariable(name="request", description="The user input", is_required=True),
            InputVariable(name="history", description="The history of the conversation", is_required=True),
        ],
    )

    # Create the function
    chat_function = kernel.create_function_from_prompt(
        prompt=prompt,
        plugin_name="Summarize_Conversation",
        function_name="Chat",
        description="Chat with the assistant",
        prompt_template_config=chat_prompt_template_config,
    )

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
            chat_function,
            request=request,
            history=history,
        )

        # Add the request to the history
        history.add_user_message(request)
        history.add_assistant_message(str(result))

        print(f"Assistant:> {result}")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
