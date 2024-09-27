# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.sk_service_configurator import add_service
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.core_plugins import ConversationSummaryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template import InputVariable, PromptTemplateConfig

# Initialize the kernel
kernel = Kernel()

# Add the service to the kernel
# use_chat: True to use chat completion, False to use text completion
kernel = add_service(kernel=kernel, use_chat=True)

service_id = "default"

# The following execution settings are used for the ConversationSummaryPlugin
execution_settings = PromptExecutionSettings(
    service_id=service_id,
    max_tokens=ConversationSummaryPlugin._max_tokens,
    temperature=0.1,
    top_p=0.5,
)
prompt_template_config = PromptTemplateConfig(
    template=ConversationSummaryPlugin._summarize_conversation_prompt_template,
    description="Given a section of a conversation transcript, summarize the part of the conversation.",
    execution_settings=execution_settings,
)

# Import the ConversationSummaryPlugin
kernel.add_plugin(
    ConversationSummaryPlugin(
        kernel=kernel, prompt_template_config=prompt_template_config
    ),
    plugin_name="ConversationSummaryPlugin",
)


# <FunctionFromPrompt>
# Create the function with the prompt
kernel.add_function(
    prompt_template_config=PromptTemplateConfig(
        template="""{{ConversationSummaryPlugin.SummarizeConversation $history}}
User: {{$request}}
Assistant:  """,
        description="Chat with the assistant",
        execution_settings=[
            PromptExecutionSettings(
                service_id="default", temperature=0.0, max_tokens=1000
            ),
            PromptExecutionSettings(
                service_id="gpt-3.5-turbo", temperature=0.2, max_tokens=4000
            ),
            PromptExecutionSettings(
                service_id="gpt-4", temperature=0.3, max_tokens=8000
            ),
        ],
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
    plugin_name="Summarize_Conversation",
    function_name="Chat",
    description="Chat with the assistant",
)
# </FunctionFromPrompt>

# Create the history
history = ChatHistory()


async def main():
    while True:
        try:
            request = input("User:> ")
        except (KeyboardInterrupt, EOFError):
            break
        if request == "exit":
            break

        result = await kernel.invoke(
            plugin_name="Summarize_Conversation",
            function_name="Chat",
            request=request,
            history=history,
        )

        # Add the request to the history
        history.add_user_message(request)
        history.add_assistant_message(str(result))

        print(f"Assistant:> {result}")

    print("\n\nExiting chat...")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
