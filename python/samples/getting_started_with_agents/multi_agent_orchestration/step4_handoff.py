# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create a handoff orchestration that represents
a customer support triage system. The orchestration consists of 4 agents, each specialized
in a different area of customer support: triage, refunds, order status, and order returns.

Depending on the customer's request, agents can hand off the conversation to the appropriate
agent.

Human in the loop is achieved via a callback function similar to the one used in group chat
orchestration. Except that in the handoff orchestration, all agents have access to the
human response function, whereas in the group chat orchestration, only the manager has access
to the human response function.

This sample demonstrates the basic steps of creating and starting a runtime, creating
a handoff orchestration, invoking the orchestration, and finally waiting for the results.
"""


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


def get_agents() -> tuple[list[Agent], OrchestrationHandoffs]:
    """Return a list of agents that will participate in the Handoff orchestration and the handoff relationships.

    Feel free to add or remove agents and handoff connections.
    """
    support_agent = ChatCompletionAgent(
        name="TriageAgent",
        description="A customer support agent that triages issues.",
        instructions="Handle customer requests.",
        service=AzureChatCompletion(),
    )

    refund_agent = ChatCompletionAgent(
        name="RefundAgent",
        description="A customer support agent that handles refunds.",
        instructions="Handle refund requests.",
        service=AzureChatCompletion(),
        plugins=[OrderRefundPlugin()],
    )

    order_status_agent = ChatCompletionAgent(
        name="OrderStatusAgent",
        description="A customer support agent that checks order status.",
        instructions="Handle order status requests.",
        service=AzureChatCompletion(),
        plugins=[OrderStatusPlugin()],
    )

    order_return_agent = ChatCompletionAgent(
        name="OrderReturnAgent",
        description="A customer support agent that handles order returns.",
        instructions="Handle order return requests.",
        service=AzureChatCompletion(),
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
    """Observer function to print the messages from the agents."""
    print(f"{message.name}: {message.content}")


def human_response_function() -> ChatMessageContent:
    """Observer function to print the messages from the agents."""
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


async def main():
    """Main function to run the agents."""
    # 1. Create a handoff orchestration with multiple agents
    agents, handoffs = get_agents()
    handoff_orchestration = HandoffOrchestration(
        members=agents,
        handoffs=handoffs,
        agent_response_callback=agent_response_callback,
        human_response_function=human_response_function,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await handoff_orchestration.invoke(
        task="A customer is on the line.",
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get()
    print(value)

    # 5. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()

    """
    Sample output:
    TriageAgent: Hello! Thank you for reaching out. How can I assist you today?
    User: I'd like to track the status of my order
    OrderStatusAgent: Sure, I can help you with that. Could you please provide me with your order ID?
    User: My order ID is 123
    OrderStatusAgent: Your order with ID 123 has been shipped and is expected to arrive in 2-3 days. Is there anything
        else I can assist you with?
    User: I want to return another order of mine
    OrderReturnAgent: I can help you with returning your order. Could you please provide the order ID for the return
        and the reason you'd like to return it?
    User: Order ID 321
    OrderReturnAgent: Please provide the reason for returning the order with ID 321.
    User: Broken item
    Processing return for order 321 due to: Broken item
    OrderReturnAgent: The return for your order with ID 321 has been successfully processed due to the broken item.
        Is there anything else I can assist you with?
    User: No, bye
    Task is completed with summary: Handled order return for order ID 321 due to a broken item, and successfully
        processed the return.
    """


if __name__ == "__main__":
    asyncio.run(main())
