# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

###################################################################
# The following sample demonstrates how to configure the auto     #
# function invocation filter with use of a ChatCompletionAgent.   #
###################################################################


def _create_kernel_with_chat_completionand_filter(service_id: str) -> Kernel:
    """A helper function to create a kernel with a chat completion service and a filter."""
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: ChatCompletionAgent, input: str, chat_history: ChatHistory) -> None:
    """Invoke the agent with the user input."""
    chat_history.add_user_message(input)
    print(f"# {AuthorRole.USER}: '{input}'")

    async for message in agent.invoke(chat_history):
        chat_history.add_message(message)
        print(message.content)


async def main():
    service_id = "agent"

    # Create the kernel used by the chat completion agent
    kernel = _create_kernel_with_chat_completionand_filter(service_id=service_id)

    # Create the agent
    # agent = ChatCompletionAgent(
    #     service_id=service_id,
    #     kernel=kernel,
    #     instructions="""
    #     Write a one verse poem on the requested topic in the style of {{$style}}.
    #     Always state the requested style of the poem.
    #     """,
    #     arguments=KernelArguments(style="Haiku"),
    # )

    # h_prompt_template_config = PromptTemplateConfig(
    #     template="""
    #     Write a one verse poem on the requested topic in the style of {{style}}.
    #     Always state the requested style of the poem.
    #     """,
    #     template_format="handlebars",
    # )

    # handlebars_agent = ChatCompletionAgent(
    #     service_id=service_id,
    #     kernel=kernel,
    #     arguments=KernelArguments(style="Haiku"),
    #     prompt_template_config=h_prompt_template_config,
    # )

    jinja2_agent = ChatCompletionAgent(
        service_id=service_id,
        kernel=kernel,
        arguments=KernelArguments(style="Haiku"),
        prompt_template_config=PromptTemplateConfig(
            template="""
            Write a one verse poem on the requested topic in the style of {{style}}.
            Always state the requested style of the poem.
            """,
            template_format="jinja2",
        ),
    )

    # Define the chat history
    chat = ChatHistory()

    # Respond to user input
    await invoke_agent(agent=jinja2_agent, input="Home cooking is great.", chat_history=chat)


if __name__ == "__main__":
    asyncio.run(main())
