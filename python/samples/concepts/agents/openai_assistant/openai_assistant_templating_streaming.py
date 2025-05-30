# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import PromptTemplateConfig
from semantic_kernel.prompt_template.const import TEMPLATE_FORMAT_TYPES

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
    client = AzureAssistantAgent.create_client()

    # Configure the prompt template
    prompt_template_config = PromptTemplateConfig(template=template_str, template_format=template_format)

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
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

    # Create a new thread for use with the assistant
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: AssistantAgentThread = None

    try:
        for user_input, style in inputs:
            print(f"# User: {user_input}\n")

            # If style is specified, override the 'style' argument
            argument_overrides = None
            if style:
                # Arguments passed in at invocation time take precedence over
                # the default arguments that were added via the constructor.
                argument_overrides = KernelArguments(style=style)

            # Stream agent responses
            async for response in agent.invoke_stream(messages=user_input, thread=thread, arguments=argument_overrides):
                if response.content:
                    print(f"{response.content}", flush=True, end="")
                thread = response.thread
            print("\n")
    finally:
        # Clean up
        await thread.delete() if thread else None
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
