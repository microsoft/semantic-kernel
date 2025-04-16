# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import PromptTemplateConfig

"""
The following sample demonstrates how to create an Azure AI
agent using Azure OpenAI within Semantic Kernel.
It uses parameterized prompts and shows how to swap between
"semantic-kernel," "jinja2," and "handlebars" template formats,
This sample highlights the agent's prompt templates are managed 
and how kernel arguments are passed in and used.
"""

# Define the inputs and styles to be used in the agent
inputs = [
    ("Home cooking is great.", None),
    ("Talk about world peace.", "iambic pentameter"),
    ("Say something about doing your best.", "e. e. cummings"),
    ("What do you think about having fun?", "old school rap"),
]


async def invoke_chat_completion_agent(agent: AzureAIAgent, inputs):
    """Invokes the given agent with each (input, style) in inputs."""

    thread = None

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
        print("\n")


async def invoke_agent_with_template(template_str: str, template_format: str, default_style: str = "haiku"):
    """Creates an agent with the specified template and format, then invokes it using invoke_chat_completion_agent."""

    # Configure the prompt template
    prompt_config = PromptTemplateConfig(template=template_str, template_format=template_format)

    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="MyPoetAgent",
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
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
