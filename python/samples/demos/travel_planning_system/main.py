# Copyright (c) Microsoft. All rights reserved.

import asyncio

from opentelemetry import trace
from opentelemetry.trace.span import format_trace_id

from samples.demos.travel_planning_system.agents import get_agents
from samples.demos.travel_planning_system.observability import set_up_logging, set_up_tracing
from semantic_kernel.agents import HandoffOrchestration
from semantic_kernel.agents.orchestration.handoffs import OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import AuthorRole, ChatMessageContent


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    if message.content:
        print(f"# {message.name}\n{message.content}")


def human_response_function() -> ChatMessageContent:
    """Observer function to print the messages from the agents."""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("human_in_the_loop"):
        user_input = input("User: ")
        return ChatMessageContent(role=AuthorRole.USER, content=user_input)


def get_agents_and_handoffs():
    """Create agents and define handoffs for the travel planning system.

    Note: prompts need further refinement to ensure they are suitable for the agents.
    Note: the router agent seems unnecessary.
    """
    BASE_TRANSFER_DESCRIPTION = "Do not call this function in parallel with other functions."

    conversation_manager, planner, router, destination_expert, flight_agent, hotel_agent = get_agents()
    handoffs = (
        OrchestrationHandoffs()
        .add_many(
            source_agent=conversation_manager,
            target_agents={
                planner.name: f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for trip planning.",
                router.name: (
                    f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for routing tasks to specialized agents."
                ),
                destination_expert.name: (
                    f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for destination expertise."
                ),
                flight_agent.name: f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for flight-related tasks.",
                hotel_agent.name: f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for hotel-related tasks.",
            },
        )
        .add(
            source_agent=planner,
            target_agent=router,
            description=f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for routing tasks to specialized agents.",
        )
        .add_many(
            source_agent=router,
            target_agents={
                destination_expert.name: (
                    f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for destination expertise."
                ),
                flight_agent.name: f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for flight-related tasks.",
                hotel_agent.name: f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for hotel-related tasks.",
            },
        )
        .add(
            source_agent=destination_expert,
            target_agent=conversation_manager,
            description=f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for non-destination related questions.",
        )
        .add(
            source_agent=flight_agent,
            target_agent=conversation_manager,
            description=f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for non-flight related questions.",
        )
        .add(
            source_agent=hotel_agent,
            target_agent=conversation_manager,
            description=f"{BASE_TRANSFER_DESCRIPTION} Transfer to this agent for non-hotel related questions.",
        )
    )

    return [
        conversation_manager,
        planner,
        router,
        destination_expert,
        flight_agent,
        hotel_agent,
    ], handoffs


async def main():
    """Main function to run the agents."""
    # 0. Set up logging and observability
    set_up_logging()
    set_up_tracing()

    # 1. Create a handoff orchestration with multiple agents
    agents, handoffs = get_agents_and_handoffs()
    handoff_orchestration = HandoffOrchestration(
        members=agents,
        handoffs=handoffs,
        agent_response_callback=agent_response_callback,
        human_response_function=human_response_function,
    )

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("main") as current_span:
        print(f"Trace ID: {format_trace_id(current_span.get_span_context().trace_id)}")
        # 2. Create a runtime and start it
        runtime = InProcessRuntime()
        runtime.start()

        # 3. Invoke the orchestration with a task and the runtime
        orchestration_result = await handoff_orchestration.invoke(
            task=(
                "Plan a trip to bali for 5 days including flights, hotels, and "
                "activities for a vegetarian family of 4 members."
            ),
            runtime=runtime,
        )

        # 4. Wait for the results
        value = await orchestration_result.get()
        print(value)

    # 5. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())
