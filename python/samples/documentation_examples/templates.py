# Copyright (c) Microsoft. All rights reserved.

import asyncio

from service_configurator import add_service

import semantic_kernel as sk
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel=kernel, use_chat=True)

    # Create the history
    history = ChatHistory()

    # An ideal prompt for this is {{$history}}{{$request}} as those
    # get cleanly parsed into a new chat_history object while invoking
    # the function. Another possibility is create the prompt as {{$history}}
    # and make sure to add the user message to the history before invoking.
    prompt = "{{$history}}"

    service_id = "default"
    req_settings = kernel.get_service("default").get_prompt_execution_settings_class()(service_id=service_id)
    chat_prompt_template_config = PromptTemplateConfig(
        template=prompt,
        description="Chat with the assistant",
        execution_settings={service_id: req_settings},
        input_variables=[
            InputVariable(name="request", description="The user input", is_required=True),
            InputVariable(name="history", description="The history of the conversation", is_required=True),
        ],
    )

    # Run the prompt
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

        # Add the request to the history before we
        # invoke the function to include it in the prompt
        history.add_user_message(request)

        result = await kernel.invoke(
            chat_function,
            request=request,
            history=history,
        )

        history.add_assistant_message(str(result))

        print(f"Assistant:> {result}")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
