# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

from samples.getting_started_with_agents.multi_agent_orchestration.observability import enable_observability
from semantic_kernel.agents import (
    Agent,
    AzureAIAgent,
    AzureAIAgentSettings,
    AzureAssistantAgent,
    ChatCompletionAgent,
    HandoffOrchestration,
    OrchestrationHandoffs,
)
from semantic_kernel.agents.open_ai.azure_responses_agent import AzureResponsesAgent
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureOpenAISettings
from semantic_kernel.contents import AuthorRole, ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.functions import kernel_function

"""
The following sample replicates sample "step4_handoff.py" but uses different agent types.
The following agent types are used:
- ChatCompletionAgent: A Chat Completion agent that is backed by an Azure OpenAI service.
- AzureAssistantAgent: An Azure Assistant agent that is backed by the Azure OpenAI Assistant API.
- AzureAIAgent: An Azure AI agent that is backed by the Azure AI Agent (a.k.a Foundry Agent) service.
- OpenAIResponsesAgent: An Azure Responses agent that is backed by the Azure OpenAI Responses API.

The Handoff orchestration doesn't support the following agent types:
- BedrockAgent
- CopilotStudioAgent
"""

azure_credential: DefaultAzureCredential | None = None
azure_ai_agent_client: AIProjectClient | None = None


async def init_azure_ai_agent_clients():
    global azure_credential, azure_ai_agent_client
    azure_credential = DefaultAzureCredential()
    azure_ai_agent_client = AzureAIAgent.create_client(credential=azure_credential)


async def close_azure_ai_agent_clients():
    global azure_credential, azure_ai_agent_client
    if azure_credential:
        await azure_credential.close()
    if azure_ai_agent_client:
        await azure_ai_agent_client.close()


class OrderStatusPlugin:
    @kernel_function
    def check_order_status(self, order_id: str) -> str:
        """Check the status of an order."""
        # Simulate checking the order status
        return f"Order {order_id} is shipped and will arrive in 2-3 days."


class OrderRefundPlugin:
    @kernel_function
    def process_refund(self, order_id: str, reason: str) -> str:
        """Process a refund for an order."""
        # Simulate processing a refund
        print(f"Processing refund for order {order_id} due to: {reason}")
        return f"Refund for order {order_id} has been processed successfully."


class OrderReturnPlugin:
    @kernel_function
    def process_return(self, order_id: str, reason: str) -> str:
        """Process a return for an order."""
        # Simulate processing a return
        print(f"Processing return for order {order_id} due to: {reason}")
        return f"Return for order {order_id} has been processed successfully."


async def get_agents() -> tuple[list[Agent], OrchestrationHandoffs]:
    """Return a list of agents that will participate in the Handoff orchestration and the handoff relationships.

    Feel free to add or remove agents and handoff connections.
    """
    # A Chat Completion agent that is backed by an Azure OpenAI service
    support_agent = ChatCompletionAgent(
        name="TriageAgent",
        description="A customer support agent that triages issues.",
        instructions="Handle customer requests.",
        service=AzureChatCompletion(),
    )

    # An Azure Assistant agent that is backed by the Azure OpenAI Assistant API
    azure_assistant_agent_client = AzureAssistantAgent.create_client()
    azure_assistant_agent_definition = await azure_assistant_agent_client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        description="A customer support agent that handles refunds.",
        instructions="Handle refund requests.",
        name="RefundAgent",
    )
    refund_agent = AzureAssistantAgent(
        client=azure_assistant_agent_client,
        definition=azure_assistant_agent_definition,
        plugins=[OrderRefundPlugin()],
    )

    # An Azure Responses agent that is backed by the Azure OpenAI Responses API
    azure_responses_agent_client = AzureResponsesAgent.create_client()
    order_status_agent = AzureResponsesAgent(
        ai_model_id=AzureOpenAISettings().responses_deployment_name,
        client=azure_responses_agent_client,
        instructions="Handle order status requests.",
        description="A customer support agent that checks order status.",
        name="OrderStatusAgent",
        plugins=[OrderStatusPlugin()],
    )

    # An Azure AI agent that is backed by the Azure AI Agent (a.k.a Foundry Agent) service
    azure_ai_agent_definition = await azure_ai_agent_client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="OrderReturnAgent",
        instructions="Handle order return requests.",
        description="A customer support agent that handles order returns.",
    )
    order_return_agent = AzureAIAgent(
        client=azure_ai_agent_client,
        definition=azure_ai_agent_definition,
        plugins=[OrderReturnPlugin()],
    )

    # Define the handoff relationships between agents
    handoffs = (
        OrchestrationHandoffs()
        .add_many(
            source_agent=support_agent.name,
            target_agents={
                refund_agent.name: "Transfer to this agent if the issue is refund related",
                order_status_agent.name: "Transfer to this agent if the issue is order status related",
                order_return_agent.name: "Transfer to this agent if the issue is order return related",
            },
        )
        .add(
            source_agent=refund_agent.name,
            target_agent=support_agent.name,
            description="Transfer to this agent if the issue is not refund related",
        )
        .add(
            source_agent=order_status_agent.name,
            target_agent=support_agent.name,
            description="Transfer to this agent if the issue is not order status related",
        )
        .add(
            source_agent=order_return_agent.name,
            target_agent=support_agent.name,
            description="Transfer to this agent if the issue is not order return related",
        )
    )

    return [support_agent, refund_agent, order_status_agent, order_return_agent], handoffs


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents.

    Please note that this function is called whenever the agent generates a response,
    including the internal processing messages (such as tool calls) that are not visible
    to other agents in the orchestration.
    """
    print(f"{message.name}: {message.content}")
    for item in message.items:
        if isinstance(item, FunctionCallContent):
            print(f"Calling '{item.name}' with arguments '{item.arguments}'")
        if isinstance(item, FunctionResultContent):
            print(f"Result from '{item.name}' is '{item.result}'")


def human_response_function() -> ChatMessageContent:
    """Observer function to print the messages from the agents."""
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


@enable_observability
async def main():
    """Main function to run the agents."""
    # 0. Initialize the Azure AI agent clients
    await init_azure_ai_agent_clients()

    # 1. Create a handoff orchestration with multiple agents
    agents, handoffs = await get_agents()
    handoff_orchestration = HandoffOrchestration(
        members=agents,
        handoffs=handoffs,
        agent_response_callback=agent_response_callback,
        human_response_function=human_response_function,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    try:
        # 3. Invoke the orchestration with a task and the runtime
        orchestration_result = await handoff_orchestration.invoke(
            task="Greet the customer who is reaching out for support.",
            runtime=runtime,
        )

        # 4. Wait for the results
        value = await orchestration_result.get()
        print(value)
    finally:
        # 5. Stop the runtime after the invocation is complete
        await runtime.stop_when_idle()

        # 6. Clean up the resources
        await close_azure_ai_agent_clients()

    """
    Sample output:
    TriageAgent: Hello! Thank you for reaching out for support. How can I assist you today?
    User: I'd like to track the status of my order
    TriageAgent:
    Calling 'Handoff-transfer_to_OrderStatusAgent' with arguments '{}'
    TriageAgent:
    Result from 'Handoff-transfer_to_OrderStatusAgent' is 'None'
    OrderStatusAgent: Could you please provide me with your order ID so I can check the status for you?
    User: My order ID is 123
    OrderStatusAgent:
    Calling 'OrderStatusPlugin-check_order_status' with arguments '{"order_id":"123"}'
    OrderStatusAgent:
    Result from 'OrderStatusPlugin-check_order_status' is 'Order 123 is shipped and will arrive in 2-3 days.'
    OrderStatusAgent: Your order with ID 123 has been shipped and is expected to arrive in 2-3 days. If you have any
        more questions, feel free to ask!
    User: I want to return another order of mine
    OrderStatusAgent: I can help you with that. Could you please provide me with the order ID of the order you want
        to return?
    User: Order ID 321
    OrderStatusAgent:
    Calling 'Handoff-transfer_to_TriageAgent' with arguments '{}'
    OrderStatusAgent:
    Result from 'Handoff-transfer_to_TriageAgent' is 'None'
    TriageAgent:
    Calling 'Handoff-transfer_to_OrderReturnAgent' with arguments '{}'
    TriageAgent:
    Result from 'Handoff-transfer_to_OrderReturnAgent' is 'None'
    OrderReturnAgent: Could you please provide me with the reason for the return for order ID 321?
    User: Broken item
    Processing return for order 321 due to: Broken item
    OrderReturnAgent:
    Calling 'OrderReturnPlugin-process_return' with arguments '{"order_id":"321","reason":"Broken item"}'
    OrderReturnAgent:
    Result from 'OrderReturnPlugin-process_return' is 'Return for order 321 has been processed successfully.'
    OrderReturnAgent: The return for order ID 321 has been processed successfully due to a broken item. If you need
        further assistance or have any other questions, feel free to let me know!
    User: No, bye
    Task is completed with summary: Processed the return request for order ID 321 due to a broken item.
    OrderReturnAgent:
    Calling 'Handoff-complete_task' with arguments '{"task_summary":"Processed the return request for order ID 321
        due to a broken item."}'
    OrderReturnAgent:
    Result from 'Handoff-complete_task' is 'None'
    """


if __name__ == "__main__":
    asyncio.run(main())
