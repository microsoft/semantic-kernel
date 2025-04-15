# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.filters import FunctionInvocationContext

"""
The following sample demonstrates how to create Chat Completion Agents
and use them as tools available for a Triage Agent to delegate requests
to the appropriate agent. A Function Invocation Filter is used to show
the function call content and the function result content so the caller
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


# Create and configure the kernel.
kernel = Kernel()

# The filter is used for demonstration purposes to show the function invocation.
kernel.add_filter("function_invocation", function_invocation_filter)

billing_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="BillingAgent",
    instructions=(
        "You specialize in handling customer questions related to billing issues. "
        "This includes clarifying invoice charges, payment methods, billing cycles, "
        "explaining fees, addressing discrepancies in billed amounts, updating payment details, "
        "assisting with subscription changes, and resolving payment failures. "
        "Your goal is to clearly communicate and resolve issues specifically about payments and charges."
    ),
)

refund_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="RefundAgent",
    instructions=(
        "You specialize in addressing customer inquiries regarding refunds. "
        "This includes evaluating eligibility for refunds, explaining refund policies, "
        "processing refund requests, providing status updates on refunds, handling complaints related to refunds, "
        "and guiding customers through the refund claim process. "
        "Your goal is to assist users clearly and empathetically to successfully resolve their refund-related concerns."
    ),
)

triage_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    kernel=kernel,
    name="TriageAgent",
    instructions=(
        "Your role is to evaluate the user's request and forward it to the appropriate agent based on the nature of "
        "the query. Forward requests about charges, billing cycles, payment methods, fees, or payment issues to the "
        "BillingAgent. Forward requests concerning refunds, refund eligibility, refund policies, or the status of "
        "refunds to the RefundAgent. Your goal is accurate identification of the appropriate specialist to ensure the "
        "user receives targeted assistance."
    ),
    plugins=[billing_agent, refund_agent],
)

thread: ChatHistoryAgentThread = None


async def chat() -> bool:
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


"""
Sample Output:

User:> I was charged twice for my subscription last month, can I get one of those payments refunded?
    Agent [BillingAgent] called with messages: I was charged twice for my subscription last month.
    Agent [RefundAgent] called with messages: Can I get one of those payments refunded?
    Response from agent RefundAgent: Of course, I'll be happy to help you with your refund inquiry. Could you please 
        provide a bit more detail about the specific payment you are referring to? For instance, the item or service 
        purchased, the transaction date, and the reason why you're seeking a refund? This will help me understand your 
        situation better and provide you with accurate guidance regarding our refund policy and process.
        Response from agent BillingAgent: I'm sorry to hear about the duplicate charge. To resolve this issue, could 
        you please provide the following details:

1. The date(s) of the transaction(s).
2. The last four digits of the card used for the transaction or any other payment method details.
3. The subscription plan you are on.

Once I have this information, I can look into the charges and help facilitate a refund for the duplicate transaction. 
Let me know if you have any questions in the meantime!

Agent :> To address your concern about being charged twice and seeking a refund for one of those payments, please 
    provide the following information:

1. **Duplicate Charge Details**: Please share the date(s) of the transaction(s), the last four digits of the card used 
    or details of any other payment method, and the subscription plan you are on. This information will help us verify 
    the duplicate charge and assist you with a refund.

2. **Refund Inquiry Details**: Please specify the transaction date, the item or service related to the payment you want 
    refunded, and the reason why you're seeking a refund. This will allow us to provide accurate guidance concerning 
    our refund policy and process.

Once we have these details, we can proceed with resolving the duplicate charge and consider your refund request. If you 
have any more questions, feel free to ask!
"""


async def main() -> None:
    print("Welcome to the chat bot!\n  Type 'exit' to exit.\n  Try to get some billing or refund help.")
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
