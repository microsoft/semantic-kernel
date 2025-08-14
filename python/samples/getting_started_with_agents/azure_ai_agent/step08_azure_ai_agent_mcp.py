# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.agents.models import McpTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent

"""
The following sample demonstrates how to create a simple, Azure AI agent that
uses the mcp tool to connect to an mcp server.
"""

TASK = "Please summarize the Azure REST API specifications Readme"


async def handle_intermediate_messages(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Define the MCP tool with the server URL
        mcp_tool = McpTool(
            server_label="github",
            server_url="https://gitmcp.io/Azure/azure-rest-api-specs",
            allowed_tools=[],  # Specify allowed tools if needed
        )

        # Optionally you may configure to require approval
        # Allowed values are "never" or "always"
        mcp_tool.set_approval_mode("never")

        # 2. Create an agent with the MCP tool on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=mcp_tool.definitions,
            instructions="You are a helpful agent that can use MCP tools to assist users.",
        )

        # 3. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 4. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread | None = None

        try:
            print(f"# User: '{TASK}'")
            # 5. Invoke the agent for the specified thread for response
            async for response in agent.invoke(
                messages=TASK, thread=thread, on_intermediate_message=handle_intermediate_messages
            ):
                print(f"# Agent: {response}")
                thread = response.thread
        finally:
            # 6. Cleanup: Delete the thread, agent, and file
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        
        # User: 'Please summarize the Azure REST API specifications Readme'
        Function Call:> fetch_azure_rest_api_docs with arguments: {}
        The Azure REST API specifications Readme provides comprehensive documentation and guidelines for designing, 
            authoring, validating, and evolving Azure REST APIs. It covers key areas including:

        1. Breaking changes and versioning: Guidelines to manage API changes that break backward compatibility, when to 
            increment API versions, and how to maintain smooth API evolution.

        2. OpenAPI/Swagger specifications: How to author REST APIs using OpenAPI specification 2.0 (Swagger), including 
            structure, conventions, validation tools, and extensions used by AutoRest for generating client SDKs.

        3. TypeSpec language: Introduction to TypeSpec, a powerful language for describing and generating REST API 
            specifications and client SDKs with extensibility to other API styles.

        4. Directory structure and uniform versioning: Organizing service specifications by teams, resource provider 
            namespaces, and following uniform versioning to keep API versions consistent across documentation and SDKs.

        5. Validation and tooling: Tools and processes like OAV, AutoRest, RESTler, and CI checks used to validate API 
            specs, generate SDKs, detect breaking changes, lint specifications, and test service contract accuracy.

        6. Authoring best practices: Manual and automated guidelines for quality API spec authoring, including writing 
            effective descriptions, resource modeling, naming conventions, and examples.

        7. Code generation configurations: How to configure readme files to generate SDKs for various languages 
            including .NET, Java, Python, Go, Typescript, and Azure CLI using AutoRest.

        8. API Scenarios and testing: Defining API scenario test files for end-to-end REST API workflows, including 
            variables, ARM template integration, and usage of test-proxy for recording traffic.

        9. SDK automation and release requests: Workflows for SDK generation validation, suppressing breaking change
            warnings, and requesting official Azure SDK releases.

        Overall, the Readme acts as a central hub providing references, guidelines, examples, and tools for maintaining 
            high-quality Azure REST API specifications and seamless SDK generation across multiple languages and 
            platforms. It ensures consistent API design, versioning, validation, and developer experience in the Azure 
            ecosystem.
        """


if __name__ == "__main__":
    asyncio.run(main())
