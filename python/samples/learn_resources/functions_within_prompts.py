# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.sk_service_configurator import add_service
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.core_plugins import ConversationSummaryPlugin
from semantic_kernel.prompt_template import InputVariable, PromptTemplateConfig


async def main():
    # <KernelCreation>
    # Initialize the kernel
    kernel = Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel=kernel, use_chat=True)

    service_id = "default"
    prompt_template_config = PromptTemplateConfig(
        template=ConversationSummaryPlugin._summarize_conversation_prompt_template,
        description="Given a section of a conversation transcript, summarize the part of the conversation.",
        execution_settings=PromptExecutionSettings(
            service_id=service_id,
            max_tokens=ConversationSummaryPlugin._max_tokens,
            temperature=0.1,
            top_p=0.5,
        ),
    )

    # Import the ConversationSummaryPlugin
    kernel.add_plugin(
        ConversationSummaryPlugin(
            kernel=kernel, prompt_template_config=prompt_template_config
        ),
        plugin_name="ConversationSummaryPlugin",
    )
    # </KernelCreation>

    # <FunctionFromPrompt>
    chat_function = kernel.add_function(
        plugin_name="Summarize_Conversation",
        function_name="Chat",
        description="Chat with the assistant",
        prompt_template_config=PromptTemplateConfig(
            template="""{{ConversationSummaryPlugin.SummarizeConversation $history}}
    User: {{$request}}
    Assistant:  """,
            execution_settings=kernel.get_prompt_execution_settings_from_service_id(
                service_id=service_id
            ),
            description="Chat with the assistant",
            input_variables=[
                InputVariable(
                    name="request", description="The user input", is_required=True
                ),
                InputVariable(
                    name="history",
                    description="The history of the conversation",
                    is_required=True,
                    allow_dangerously_set_content=True,
                ),
            ],
        ),
    )
    # </FunctionFromPrompt>

    # <Chat>
    # Create the history
    history = ChatHistory()

    while True:
        try:
            request = input("User:> ")
        except (KeyboardInterrupt, EOFError):
            break
        if request == "exit":
            break

        result = await kernel.invoke(
            chat_function,
            request=request,
            history=history,
        )

        # Add the request to the history
        history.add_user_message(request)
        history.add_assistant_message(str(result))

        print(f"Assistant:> {result}")
    print("\n\nExiting chat...")
    # </Chat>


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
