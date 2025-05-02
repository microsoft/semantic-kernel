# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.agent import AgentRegistry
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions. This sample demonstrates the basic steps to create an agent
and simulate a conversation with the agent.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""


class MenuPlugin:
    """A sample Menu Plugin used for the concept sample."""

    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> Annotated[str, "Returns the specials from the menu."]:
        return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(
        self, menu_item: Annotated[str, "The name of the menu item."]
    ) -> Annotated[str, "Returns the price of the menu item."]:
        return "$9.99"


# Hello World spec


spec = """
type: foundry_agent
name: MyAgent
description: My helpful agent.
instructions: You are helpful agent.
model:
  id: ${AzureAI:ChatModelId}
  connection:
    connection_string: ${AzureAI:ConnectionString}
"""

#  Code interpreter spec

spec = """
type: foundry_agent
name: CodeInterpreterAgent
description: Agent with code interpreter tool.
instructions: >
  Use the code interpreter tool to answer questions that require code to be generated
  and executed.
model:
  id: ${AzureAI:ChatModelId}
  connection:
    connection_string: ${AzureAI:ConnectionString}
tools:
  - type: code_interpreter
    options:
        file_ids: ["${AzureAI:FileId1}"]
"""

# Function spec

spec = """ 
type: foundry_agent
name: FunctionCallingAgent
description: This agent uses the provided functions to answer questions about the menu.
instructions: Use the provided functions to answer questions about the menu.
model:
  id: ${AzureAI:ChatModelId}
  connection:
    connection_string: ${AzureAI:ConnectionString}
  options:
    temperature: 0.4
tools:
  - id: GetSpecials
    type: function
    description: Get the specials from the menu.
    options:
      parameters:
        type: object
        properties: {}
  - id: GetItemPrice
    type: function
    description: Get the price of an item on the menu.
    options:
      parameters:
        type: object
        properties:
          menuItem:
            type: string
            description: The name of the menu item.
        required: ["menuItem"]
"""

spec = """
type: foundry_agent
name: FunctionCallingAgent
instructions: Use the provided functions to answer questions about the menu.
description: This agent uses the provided functions to answer questions about the menu.
model:
    id: ${AzureAI:ChatModelId}
    options:
    temperature: 0.4
tools:
    - id: GetSpecials
      type: function
      description: Get the specials from the menu.
    - id: GetItemPrice
      type: function
      description: Get the price of an item on the menu.
      options:
          parameters:
          - name: menuItem
              type: string
              required: true
              description: The name of the menu item.  
"""

settings = AzureAIAgentSettings()  # ChatModelId & ConnectionString come from env vars


async def bootstrap():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # csv_file_path = os.path.join(
        #     os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        #     "resources",
        #     "agent_assistant_file_manipulation",
        #     "sales.csv",
        # )

        try:
            # file = await client.agents.upload_file_and_poll(file_path=csv_file_path, purpose=FilePurpose.AGENTS)
            # print(file.id)

            kernel = Kernel()  # with your functions loaded
            kernel.add_plugin(MenuPlugin(), "MenuPlugin")
            agent: AzureAIAgent = await AgentRegistry.create_agent_from_yaml(
                spec,
                kernel=kernel,
                client=client,
                settings=settings,
                # extras={"FileId1": file.id},
            )
            async for resp in agent.invoke(
                messages="Using Python, give me the code to calculate the total sales for all segments."
            ):
                print(resp)
        finally:
            # Cleanup: Delete the thread and agent
            await client.agents.delete_agent(agent.id)
            # await client.agents.delete_file(file.id)


asyncio.run(bootstrap())
