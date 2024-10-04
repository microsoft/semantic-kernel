# Copyright (c) Microsoft. All rights reserved.

import asyncio

from service_configurator import add_service

import semantic_kernel as sk


async def main():
    # Initialize the kernel
    kernel = sk.Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel=kernel, use_chat=True)

    request = input("Your request: ")

    # 0.0 Initial prompt
    prompt = f"What is the intent of this request? {request}"
    print("0.0 Initial prompt")
    print("-------------------------")
    prompt_function = kernel.create_function_from_prompt(
        function_name="sample_zero", plugin_name="sample_plugin", prompt=prompt
    )
    result = await kernel.invoke(prompt_function, request=request)
    print(result)
    print("-------------------------")

    # 1.0 Make the prompt more specific
    prompt = f"""What is the intent of this request? {request}
        You can choose between SendEmail, SendMessage, CompleteTask, CreateDocument."""
    print("1.0 Make the prompt more specific")
    print("-------------------------")
    prompt_function = kernel.create_function_from_prompt(
        function_name="sample_one", plugin_name="sample_plugin", prompt=prompt
    )
    result = await kernel.invoke(prompt_function, request=request)
    print(result)
    print("-------------------------")

    # 2.0 Add structure to the output with formatting
    prompt = f"""Instructions: What is the intent of this request?
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument.
        User Input: {request}
        Intent: """
    print("2.0 Add structure to the output with formatting")
    print("-------------------------")
    prompt_function = kernel.create_function_from_prompt(
        function_name="sample_two", plugin_name="sample_plugin", prompt=prompt
    )
    result = await kernel.invoke(prompt_function, request=request)
    print(result)
    print("-------------------------")

    # 2.1 Add structure to the output with formatting (using Markdown and JSON)
    prompt = f"""## Instructions
        Provide the intent of the request using the following format:
        ```json
        {{
            "intent": {{intent}}
        }}
        ```

        ## Choices
        You can choose between the following intents:
        ```json
        ["SendEmail", "SendMessage", "CompleteTask", "CreateDocument"]
        ```

        ## User Input
        The user input is:
        ```json
        {{
            "request": "{request}"\n'
        }}
        ```

        ## Intent"""
    print("2.1 Add structure to the output with formatting (using Markdown and JSON)")
    print("-------------------------")
    prompt_function = kernel.create_function_from_prompt(
        function_name="sample_two_one", plugin_name="sample_plugin", prompt=prompt
    )
    result = await kernel.invoke(prompt_function, request=request)
    print(result)
    print("-------------------------")

    # 3.0 Provide examples with few-shot prompting
    prompt = f"""Instructions: What is the intent of this request?
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument.

        User Input: Can you send a very quick approval to the marketing team?
        Intent: SendMessage

        User Input: Can you send the full update to the marketing team?
        Intent: SendEmail

        User Input: {request}
        Intent: """
    print("3.0 Provide examples with few-shot prompting")
    print("-------------------------")
    prompt_function = kernel.create_function_from_prompt(
        function_name="sample_three", plugin_name="sample_plugin", prompt=prompt
    )
    result = await kernel.invoke(prompt_function, request=request)
    print(result)
    print("-------------------------")

    # 4.0 Tell the AI what to do to avoid doing something wrong
    prompt = f"""Instructions: What is the intent of this request?
        If you don't know the intent, don't guess; instead respond with "Unknown".
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.

        User Input: Can you send a very quick approval to the marketing team?
        Intent: SendMessage

        User Input: Can you send the full update to the marketing team?
        Intent: SendEmail

        User Input: {request}
        Intent: """
    print("4.0 Tell the AI what to do to avoid doing something wrong")
    print("-------------------------")
    prompt_function = kernel.create_function_from_prompt(
        function_name="sample_four", plugin_name="sample_plugin", prompt=prompt
    )
    result = await kernel.invoke(prompt_function, request=request)
    print(result)
    print("-------------------------")

    # 5.0 Provide context to the AI through a chat history of this user
    history = (
        "User input: I hate sending emails, no one ever reads them.\n"
        "AI response: I'm sorry to hear that. Messages may be a better way to communicate."
    )
    prompt = f"""Instructions: What is the intent of this request?\n"
        If you don't know the intent, don't guess; instead respond with "Unknown".
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.

        User Input: Can you send a very quick approval to the marketing team?
        Intent: SendMessage

        User Input: Can you send the full update to the marketing team?
        Intent: SendEmail

        {history}
        User Input: {request}
        Intent: """
    print("5.0 Provide context to the AI")
    print("-------------------------")
    prompt_function = kernel.create_function_from_prompt(
        function_name="sample_five", plugin_name="sample_plugin", prompt=prompt
    )
    result = await kernel.invoke(prompt_function, request=request, history=history)
    print(result)
    print("-------------------------")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
