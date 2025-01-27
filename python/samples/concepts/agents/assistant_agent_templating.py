# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents.open_ai import AzureAssistantAgent, OpenAIAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

#####################################################################
# The following sample demonstrates how to create an assistant      #
# agent using either Azure OpenAI or OpenAI within Semantic Kernel. #
# It uses parameterized prompts and shows how to swap between       #
# "semantic-kernel," "jinja2," and "handlebars" template formats,   #
# This sample highlights how the agent’s threaded conversation      #
# state parallels the Chat History in Semantic Kernel, ensuring     #
# all responses and parameters remain consistent throughout the     #
# session.                                                          #
#####################################################################

inputs = [
    ("Home cooking is great.", None),
    ("Talk about world peace.", "iambic pentameter"),
    ("Say something about doing your best.", "e. e. cummings"),
    ("What do you think about having fun?", "old school rap"),
]


async def invoke_assistant_agent(agent: OpenAIAssistantAgent | AzureAssistantAgent, inputs):
    """Invokes the given agent with each (input, style) in inputs."""
    thread_id = await agent.create_thread()

    try:
        for user_input, style in inputs:
            # Add user message to the conversation
            await agent.add_chat_message(
                thread_id=thread_id,
                message=ChatMessageContent(role=AuthorRole.USER, content=user_input),
            )
            print(f"[USER]: {user_input}")

            # If style is specified, override the 'style' argument
            argument_overrides = None
            if style:
                argument_overrides = KernelArguments(style=style)

            # Stream agent responses
            async for response in agent.invoke(thread_id=thread_id, arguments=argument_overrides):
                print(f"[AGENT]: {response.content}")
    finally:
        # Clean up
        await agent.delete_thread(thread_id)
        await agent.delete()


async def invoke_agent_with_template(
    kernel: Kernel, template_str: str, template_format: str, default_style: str = "haiku"
):
    """Creates an agent with the specified template and format, then invokes it using invoke_assistant_agent."""
    # Switch between Azure or OpenAI as desired:
    use_azure_openai = False

    instructions = (
        "You are a friendly poet, skilled at writing a one verse poem on any requested topic. "
        "Always include the poem style in the final output."
    )

    # Configure the prompt template
    prompt_config = PromptTemplateConfig(template=template_str, template_format=template_format)

    if use_azure_openai:
        agent = await AzureAssistantAgent.create(
            kernel=kernel,
            service_id="agent",
            name="MyPoetAgent",
            instructions=instructions,
            prompt_template_config=prompt_config,
            arguments=KernelArguments(style=default_style),
        )
    else:
        agent = await OpenAIAssistantAgent.create(
            kernel=kernel,
            service_id="agent",
            name="MyPoetAgent",
            instructions=instructions,
            prompt_template_config=prompt_config,
            arguments=KernelArguments(style=default_style),
        )

    await invoke_assistant_agent(agent, inputs)


async def main():
    kernel = Kernel()

    # 1) Using "semantic-kernel" format
    print("\n===== SEMANTIC-KERNEL FORMAT =====\n")
    semantic_kernel_template = """
Write a one verse poem on the requested topic in the style of {{$style}}.
Always state the requested style of the poem.
"""
    await invoke_agent_with_template(
        kernel=kernel,
        template_str=semantic_kernel_template,
        template_format="semantic-kernel",
        default_style="haiku",
    )

    # 2) Using "jinja2" format
    print("\n===== JINJA2 FORMAT =====\n")
    jinja2_template = """
Write a one verse poem on the requested topic in the style of {{style}}.
Always state the requested style of the poem.
"""
    await invoke_agent_with_template(
        kernel=kernel, template_str=jinja2_template, template_format="jinja2", default_style="haiku"
    )

    # 3) Using "handlebars" format
    print("\n===== HANDLEBARS FORMAT =====\n")
    handlebars_template = """
Write a one verse poem on the requested topic in the style of {{style}}.
Always state the requested style of the poem.
"""
    await invoke_agent_with_template(
        kernel=kernel, template_str=handlebars_template, template_format="handlebars", default_style="haiku"
    )


if __name__ == "__main__":
    asyncio.run(main())
