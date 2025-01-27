# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

#####################################################################
# The following sample demonstrates how to create a chat completion #
# agent using either Azure OpenAI or OpenAI within Semantic Kernel. #
# It uses parameterized prompts and shows how to swap between       #
# "semantic-kernel," "jinja2," and "handlebars" template formats,   #
# This sample highlights the agent’s chat history conversation      #
# is managed and how kernel arguments are passed in and used.       #
#####################################################################

inputs = [
    ("Home cooking is great.", None),
    ("Talk about world peace.", "iambic pentameter"),
    ("Say something about doing your best.", "e. e. cummings"),
    ("What do you think about having fun?", "old school rap"),
]


def _create_kernel_with_chat_completion_service(use_azure_openai: bool = True) -> Kernel:
    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(service_id="agent") if use_azure_openai else OpenAIChatCompletion(service_id="agent")
    )
    return kernel


async def invoke_chat_completion_agent(agent: ChatCompletionAgent, inputs):
    """Invokes the given agent with each (input, style) in inputs."""

    chat = ChatHistory()

    for user_input, style in inputs:
        # Add user message to the conversation
        chat.add_message(ChatMessageContent(role=AuthorRole.USER, content=user_input))
        print(f"[USER]: {user_input}")

        # If style is specified, override the 'style' argument
        argument_overrides = None
        if style:
            argument_overrides = KernelArguments(style=style)

        # Stream agent responses
        async for response in agent.invoke(history=chat, arguments=argument_overrides):
            print(f"[AGENT]: {response.content}")


async def invoke_agent_with_template(
    kernel: Kernel, template_str: str, template_format: str, default_style: str = "haiku"
):
    """Creates an agent with the specified template and format, then invokes it using invoke_chat_completion_agent."""

    instructions = (
        "You are a friendly poet, skilled at writing a one verse poem on any requested topic. "
        "Always include the poem style in the final output."
    )

    # Configure the prompt template
    prompt_config = PromptTemplateConfig(template=template_str, template_format=template_format)

    agent = ChatCompletionAgent(
        kernel=kernel,
        name="MyPoetAgent",
        instructions=instructions,
        prompt_template_config=prompt_config,
        arguments=KernelArguments(style=default_style),
    )

    await invoke_chat_completion_agent(agent, inputs)


async def main():
    kernel = _create_kernel_with_chat_completion_service()

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
