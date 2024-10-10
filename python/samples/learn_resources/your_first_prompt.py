# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.sk_service_configurator import add_service
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import InputVariable, PromptTemplateConfig


async def main(delay: int = 0):
    # <KernelCreation>
    # Initialize the kernel
    kernel = Kernel()

    # Add the service to the kernel
    # use_chat: True to use chat completion, False to use text completion
    kernel = add_service(kernel=kernel, use_chat=True)
    # </KernelCreation>
    print(
        "This sample uses different prompts with the same request, they are related to Emails, "
        "Tasks and Documents, make sure to include that in your request."
    )
    request = input("Your request: ")
    arguments = KernelArguments(
        request=request, settings=PromptExecutionSettings(max_tokens=100)
    )
    # <InitialPrompt> 0.0 Initial prompt
    prompt = "What is the intent of this request? {{$request}}"
    # </InitialPrompt>
    # <InvokeInitialPrompt>
    print("0.0 Initial prompt")
    print("-------------------------")
    result = await kernel.invoke_prompt(
        function_name="sample_zero",
        plugin_name="sample_plugin",
        prompt=prompt,
        arguments=arguments,
    )
    print(result)
    await asyncio.sleep(delay)
    print("-------------------------")
    # </InvokeInitialPrompt>

    # <MoreSpecificPrompt> 1.0 Make the prompt more specific
    prompt = """What is the intent of this request? {{$request}}
        You can choose between SendEmail, SendMessage, CompleteTask, CreateDocument."""
    # </MoreSpecificPrompt>
    print("1.0 Make the prompt more specific")
    print("-------------------------")
    result = await kernel.invoke_prompt(
        function_name="sample_one",
        plugin_name="sample_plugin",
        prompt=prompt,
        arguments=arguments,
    )
    print(result)
    await asyncio.sleep(delay)
    print("-------------------------")

    # <StructuredPrompt> 2.0 Add structure to the output with formatting
    prompt = """Instructions: What is the intent of this request?
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument.
        User Input: {{$request}}
        Intent: """
    # </StructuredPrompt>
    print("2.0 Add structure to the output with formatting")
    print("-------------------------")
    result = await kernel.invoke_prompt(
        function_name="sample_two",
        plugin_name="sample_plugin",
        prompt=prompt,
        arguments=arguments,
    )
    print(result)
    await asyncio.sleep(delay)
    print("-------------------------")

    # <FormattedPrompt> 2.1 Add structure to the output with formatting (using Markdown and JSON)
    prompt = """## Instructions
        Provide the intent of the request using the following format:
        ```json
        {
            "intent": {intent}
        }
        ```

        ## Choices
        You can choose between the following intents:
        ```json
        ["SendEmail", "SendMessage", "CompleteTask", "CreateDocument"]
        ```

        ## User Input
        The user input is:
        ```json
        {
            "request": "{{$request}}"\n'
        }
        ```

        ## Intent"""
    # </FormattedPrompt>
    print("2.1 Add structure to the output with formatting (using Markdown and JSON)")
    print("-------------------------")
    result = await kernel.invoke_prompt(
        function_name="sample_two_one",
        plugin_name="sample_plugin",
        prompt=prompt,
        arguments=arguments,
    )
    print(result)
    await asyncio.sleep(delay)
    print("-------------------------")

    # <FewShotPrompt> 3.0 Provide examples with few-shot prompting
    prompt = """Instructions: What is the intent of this request?
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument.

        User Input: Can you send a very quick approval to the marketing team?
        Intent: SendMessage

        User Input: Can you send the full update to the marketing team?
        Intent: SendEmail

        User Input: {{$request}}
        Intent: """
    # </FewShotPrompt>
    print("3.0 Provide examples with few-shot prompting")
    print("-------------------------")
    result = await kernel.invoke_prompt(
        function_name="sample_three",
        plugin_name="sample_plugin",
        prompt=prompt,
        arguments=arguments,
    )
    print(result)
    await asyncio.sleep(delay)
    print("-------------------------")

    # <AvoidPrompt> 4.0 Tell the AI what to do to avoid doing something wrong
    prompt = """Instructions: What is the intent of this request?
        If you don't know the intent, don't guess; instead respond with "Unknown".
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.

        User Input: Can you send a very quick approval to the marketing team?
        Intent: SendMessage

        User Input: Can you send the full update to the marketing team?
        Intent: SendEmail

        User Input: {{$request}}
        Intent: """
    # </AvoidPrompt>
    print("4.0 Tell the AI what to do to avoid doing something wrong")
    print("-------------------------")
    result = await kernel.invoke_prompt(
        function_name="sample_four",
        plugin_name="sample_plugin",
        prompt=prompt,
        arguments=arguments,
    )
    print(result)
    await asyncio.sleep(delay)
    print("-------------------------")

    # <ContextPrompt> 5.0 Provide context to the AI through a chat history of this user
    history = (
        "User input: I hate sending emails, no one ever reads them.\n"
        "AI response: I'm sorry to hear that. Messages may be a better way to communicate."
    )
    prompt = """Instructions: What is the intent of this request?\n"
        If you don't know the intent, don't guess; instead respond with "Unknown".
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.

        User Input: Can you send a very quick approval to the marketing team?
        Intent: SendMessage

        User Input: Can you send the full update to the marketing team?
        Intent: SendEmail

        {{$history}}
        User Input: {{$request}}
        Intent: """
    # </ContextPrompt>
    print("5.0 Provide context to the AI")
    print("-------------------------")
    arguments["history"] = history
    result = await kernel.invoke_prompt(
        function_name="sample_five",
        plugin_name="sample_plugin",
        prompt=prompt,
        arguments=arguments,
    )
    print(result)
    await asyncio.sleep(delay)
    print("-------------------------")

    # <RolePrompt> 6.0 Using message roles in chat completion prompts
    history = """
        <message role="user">I hate sending emails, no one ever reads them.</message>
        <message role="assistant">I'm sorry to hear that. Messages may be a better way to communicate.</message>
        """

    prompt = """
        <message role="system">Instructions: What is the intent of this request?
        If you don't know the intent, don't guess; instead respond with "Unknown".
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.</message>

        <message role="user">Can you send a very quick approval to the marketing team?</message>
        <message role="system">Intent:</message>
        <message role="assistant">SendMessage</message>

        <message role="user">Can you send the full update to the marketing team?</message>
        <message role="system">Intent:</message>
        <message role="assistant">SendEmail</message>

        {{$history}}
        <message role="user">{{$request}}</message>
        <message role="system">Intent:</message>
        """
    # </RolePrompt>
    print("6.0 Using message roles in chat completion prompts")
    print("-------------------------")
    arguments["history"] = history
    result = await kernel.invoke_prompt(
        function_name="sample_six",
        plugin_name="sample_plugin",
        prompt=prompt,
        arguments=arguments,
        prompt_template_config=PromptTemplateConfig(
            input_variables=[
                InputVariable(name="history", allow_dangerously_set_content=True)
            ]
        ),
    )
    print(result)
    await asyncio.sleep(delay)
    print("-------------------------")

    # <BonusPrompt> 7.0 Give your AI words of encouragement
    history = """
        <message role="user">I hate sending emails, no one ever reads them.</message>
        <message role="assistant">I'm sorry to hear that. Messages may be a better way to communicate.</message>
        """

    prompt = """
        <message role="system">Instructions: What is the intent of this request?
        If you don't know the intent, don't guess; instead respond with "Unknown".
        Choices: SendEmail, SendMessage, CompleteTask, CreateDocument, Unknown.
        Bonus: You'll get $20 if you get this right.</message>

        <message role="user">Can you send a very quick approval to the marketing team?</message>
        <message role="system">Intent:</message>
        <message role="assistant">SendMessage</message>

        <message role="user">Can you send the full update to the marketing team?</message>
        <message role="system">Intent:</message>
        <message role="assistant">SendEmail</message>

        {{$history}}
        <message role="user">{{$request}}</message>
        <message role="system">Intent:</message>
        """
    # </BonusPrompt>
    print("7.0 Give your AI words of encouragement")
    print("-------------------------")
    arguments["history"] = history
    result = await kernel.invoke_prompt(
        function_name="sample_seven",
        plugin_name="sample_plugin",
        prompt=prompt,
        arguments=arguments,
        prompt_template_config=PromptTemplateConfig(
            input_variables=[
                InputVariable(name="history", allow_dangerously_set_content=True)
            ]
        ),
    )
    print(result)
    print("-------------------------")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
