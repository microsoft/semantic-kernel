# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import PromptTemplateConfig

"""
The following sample demonstrates how to create a chat completion
agent using Azure OpenAI within Semantic Kernel.
It uses parameterized prompts and shows how to swap between
"semantic-kernel," "jinja2," and "handlebars" template formats,
This sample highlights the agent's chat history conversation
is managed and how kernel arguments are passed in and used.
"""

# Define the inputs and styles to be used in the agent
inputs = [
    ("Home cooking is great.", None),
    ("Talk about world peace.", "iambic pentameter"),
    ("Say something about doing your best.", "e. e. cummings"),
    ("What do you think about having fun?", "old school rap"),
]


async def invoke_chat_completion_agent(agent: ChatCompletionAgent, inputs):
    """Invokes the given agent with each (input, style) in inputs."""

    thread: ChatHistoryAgentThread = None

    for user_input, style in inputs:
        print(f"[USER]: {user_input}\n")

        # If style is specified, override the 'style' argument
        argument_overrides = None
        if style:
            argument_overrides = KernelArguments(style=style)

        # Stream agent responses
        async for response in agent.invoke_stream(messages=user_input, thread=thread, arguments=argument_overrides):
            print(f"{response.content}", end="", flush=True)
            thread = response.thread
        print()


async def invoke_agent_with_template(template_str: str, template_format: str, default_style: str = "haiku"):
    """Creates an agent with the specified template and format, then invokes it using invoke_chat_completion_agent."""

    # Configure the prompt template
    prompt_config = PromptTemplateConfig(template=template_str, template_format=template_format)

    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="MyPoetAgent",
        prompt_template_config=prompt_config,
        arguments=KernelArguments(style=default_style),
    )

    await invoke_chat_completion_agent(agent, inputs)


async def main():
    # 1) Using "semantic-kernel" format
    print("\n===== SEMANTIC-KERNEL FORMAT =====\n")
    semantic_kernel_template = """
    Write a one verse poem on the requested topic in the style of {{$style}}.
    Always state the requested style of the poem.
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
    Always state the requested style of the poem.
    """
    await invoke_agent_with_template(template_str=jinja2_template, template_format="jinja2", default_style="haiku")

    # 3) Using "handlebars" format
    print("\n===== HANDLEBARS FORMAT =====\n")
    handlebars_template = """
    Write a one verse poem on the requested topic in the style of {{style}}.
    Always state the requested style of the poem.
    """
    await invoke_agent_with_template(
        template_str=handlebars_template, template_format="handlebars", default_style="haiku"
    )


if __name__ == "__main__":
    asyncio.run(main())
