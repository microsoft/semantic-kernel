# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.const import TEMPLATE_FORMAT_TYPES
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

"""
The following sample demonstrates how to create an assistant
agent using either Azure OpenAI or OpenAI within Semantic Kernel.
It uses parameterized prompts and shows how to swap between
"semantic-kernel," "jinja2," and "handlebars" template formats,
This sample highlights how the agent's threaded conversation
state parallels the Chat History in Semantic Kernel, ensuring
all responses and parameters remain consistent throughout the
session.
"""

inputs = [
    ("Home cooking is great.", None),
    ("Talk about world peace.", "iambic pentameter"),
    ("Say something about doing your best.", "e. e. cummings"),
    ("What do you think about having fun?", "old school rap"),
]


async def invoke_agent_with_template(
    template_str: str, template_format: TEMPLATE_FORMAT_TYPES, default_style: str = "haiku"
):
    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # Configure the prompt template
    prompt_template_config = PromptTemplateConfig(template=template_str, template_format=template_format)

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        name="MyPoetAgent",
    )

    # Create the AzureAssistantAgent instance using the client, the assistant definition,
    # the prompt template config, and the constructor-level Kernel Arguments
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
        prompt_template_config=prompt_template_config,  # type: ignore
        arguments=KernelArguments(style=default_style),
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    try:
        for user_input, style in inputs:
            # Add user message to the conversation
            await agent.add_chat_message(
                thread_id=thread.id,
                message=user_input,
            )
            print(f"# User: {user_input}\n")

            # If style is specified, override the 'style' argument
            argument_overrides = None
            if style:
                # Arguments passed in at invocation time take precedence over
                # the default arguments that were added via the constructor.
                argument_overrides = KernelArguments(style=style)

            # Stream agent responses
            async for response in agent.invoke_stream(thread_id=thread.id, arguments=argument_overrides):
                if response.content:
                    print(f"{response.content}", flush=True, end="")
            print("\n")
    finally:
        # Clean up
        await client.beta.threads.delete(thread.id)
        await client.beta.assistants.delete(agent.id)


async def main():
    # 1) Using "semantic-kernel" format
    print("\n===== SEMANTIC-KERNEL FORMAT =====\n")
    semantic_kernel_template = """
Write a one verse poem on the requested topic in the style of {{$style}}.
Always state the requested style of the poem. Write appropriate G-rated content.
"""
    await invoke_agent_with_template(
        template_str=semantic_kernel_template,
        template_format="semantic-kernel",
        default_style="haiku",
    )

    # 2) Using "jinja2" format
    print("\n===== JINJA2 FORMAT =====\n")
    jinja2_template = """
Write a one verse poem on the requested topic in the style of {{style}}.
Always state the requested style of the poem. Write appropriate G-rated content.
"""
    await invoke_agent_with_template(template_str=jinja2_template, template_format="jinja2", default_style="haiku")

    # 3) Using "handlebars" format
    print("\n===== HANDLEBARS FORMAT =====\n")
    handlebars_template = """
Write a one verse poem on the requested topic in the style of {{style}}.
Always state the requested style of the poem. Write appropriate G-rated content.
"""
    await invoke_agent_with_template(
        template_str=handlebars_template, template_format="handlebars", default_style="haiku"
    )


if __name__ == "__main__":
    asyncio.run(main())
