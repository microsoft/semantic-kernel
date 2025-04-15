# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel import Kernel
from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    ChatCompletionAgent,
    ChatHistoryAgentThread,
)
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.filters import FunctionInvocationContext

"""
The following sample demonstrates how to create an Azure AI Agent Agent
and a ChatCompletionAgent use them as tools available for a Triage Agent 
to delegate requests to the appropriate agent. A Function Invocation Filter 
is used to show the function call content and the function result content so the caller
can see which agent was called and what the response was.
"""


# Define the auto function invocation filter that will be used by the kernel
async def function_invocation_filter(context: FunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    if "messages" not in context.arguments:
        await next(context)
        return
    print(f"    Agent [{context.function.name}] called with messages: {context.arguments['messages']}")
    await next(context)
    print(f"    Response from agent [{context.function.name}]: {context.result.value}")


async def chat(triage_agent: ChatCompletionAgent, thread: ChatHistoryAgentThread = None) -> bool:
    """
    Continuously prompt the user for input and show the assistant's response.
    Type 'exit' to exit.
    """
    try:
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting chat...")
        return False

    if user_input.lower().strip() == "exit":
        print("\n\nExiting chat...")
        return False

    response = await triage_agent.get_response(
        messages=user_input,
        thread=thread,
    )

    if response:
        print(f"Agent :> {response}")

    return True


async def main() -> None:
    # Create and configure the kernel.
    kernel = Kernel()

    # The filter is used for demonstration purposes to show the function invocation.
    kernel.add_filter("function_invocation", function_invocation_filter)

    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        # Create the agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="BillingAgent",
            instructions=(
                "You specialize in handling customer questions related to billing issues. "
                "This includes clarifying invoice charges, payment methods, billing cycles, "
                "explaining fees, addressing discrepancies in billed amounts, updating payment details, "
                "assisting with subscription changes, and resolving payment failures. "
                "Your goal is to clearly communicate and resolve issues specifically about payments and charges."
            ),
        )

        # Create the AzureAI Agent
        billing_agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        refund_agent = ChatCompletionAgent(
            service=AzureChatCompletion(),
            name="RefundAgent",
            instructions=(
                "You specialize in addressing customer inquiries regarding refunds. "
                "This includes evaluating eligibility for refunds, explaining refund policies, "
                "processing refund requests, providing status updates on refunds, handling complaints related to "
                "refunds, and guiding customers through the refund claim process. "
                "Your goal is to assist users clearly and empathetically to successfully resolve their refund-related "
                "concerns."
            ),
        )

        triage_agent = ChatCompletionAgent(
            service=AzureChatCompletion(),
            kernel=kernel,
            name="TriageAgent",
            instructions=(
                "Your role is to evaluate the user's request and forward it to the appropriate agent based on the "
                "nature of the query. Forward requests about charges, billing cycles, payment methods, fees, or "
                "payment issues to the BillingAgent. Forward requests concerning refunds, refund eligibility, "
                "refund policies, or the status of refunds to the RefundAgent. Your goal is accurate identification "
                "of the appropriate specialist to ensure the user receives targeted assistance."
            ),
            plugins=[billing_agent, refund_agent],
        )

        thread: ChatHistoryAgentThread = None

        print("Welcome to the chat bot!\n  Type 'exit' to exit.\n  Try to get some billing or refund help.")

        chatting = True
        while chatting:
            chatting = await chat(triage_agent, thread)

    """
    Sample Output:

    I canceled my subscription but I was still charged.
        Agent [BillingAgent] called with messages: I canceled my subscription but I was still charged.
        Response from agent [BillingAgent]: I understand how concerning that can be. It's possible that the charge you 
            received is for a billing cycle that was initiated before your cancellation was processed. Here are a few 
            steps you can take:

    1. **Check Cancellation Confirmation**: Make sure you received a confirmation of your cancellation. 
        This usually comes via email.

    2. **Billing Cycle**: Review your billing cycle to confirm whether the charge aligns with your subscription terms. 
        If your billing is monthly, charges can occur even if you cancel before the period ends.

    3. **Contact Support**: If you believe the charge was made in error, please reach out to customer support for 
        further clarification and to rectify the situation.

    If you can provide more details about the subscription and when you canceled it, I can help you further understand 
        the charges.
    
    Agent :> It's possible that the charge you received is for a billing cycle initiated before your cancellation was 
        processed. Please check if you received a cancellation confirmation, review your billing cycle, and contact 
        support for further clarification if you believe the charge was made in error. If you have more details, 
        I can help you understand the charges better.
    """


if __name__ == "__main__":
    asyncio.run(main())
