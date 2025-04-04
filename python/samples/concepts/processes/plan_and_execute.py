# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from enum import Enum
from typing import ClassVar

from pydantic import Field

from semantic_kernel import Kernel
from semantic_kernel.agents import OpenAIResponsesAgent
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import (
    KernelProcess,
    KernelProcessEvent,
    KernelProcessEventVisibility,
    KernelProcessStep,
    KernelProcessStepContext,
    KernelProcessStepState,
)
from semantic_kernel.processes.local_runtime.local_kernel_process import start as start_local_process

""" 
The following code demonstrates a simple plan and execute process using the Semantic Kernel Process Framework. 
It defines a multi-step workflow that leverages OpenAI's Responses API and integrated web search tools to generate, 
refine, and execute a plan based on a user's query.

The process is composed of several steps:

- PlannerStep: Generates an initial plan (a set of tasks) in response to the user's request.
- ReplanStep: Refines the plan when the initial tasks yield ambiguous or incomplete results.
- ExecuteStep: Sequentially executes each task in the plan, incorporating previously gathered partial results to 
    provide context.
- DecisionStep: Evaluates progress and decides whether to continue executing the remaining tasks or to replan 
    if necessary.
- OutputStep: Aggregates and displays the final result or intermediate outputs to the user.

Each step communicates via events within the Semantic Kernel framework, ensuring that state and context are maintained 
throughout the process. A helper function centralizes the setup of the OpenAIResponsesAgent.

This example illustrates how to build an extensible, asynchronous processing pipeline capable of dynamically handling 
user queries and providing detailed outputs. 
"""


# Define a method to get a response from the OpenAI agent
async def run_openai_agent(instructions: str, prompt: str, agent_name: str = "GenericAgent") -> str:
    client, model = OpenAIResponsesAgent.setup_resources()
    agent_tools = [OpenAIResponsesAgent.configure_web_search_tool()]

    agent = OpenAIResponsesAgent(
        ai_model_id=model,
        client=client,
        instructions=instructions,
        name=agent_name,
        tools=agent_tools,
    )
    response = await agent.get_response(messages=prompt)
    return response.message.content.strip()


#
# 1) Global Events
#
class PlanExecuteEvents(str, Enum):
    StartProcess = "StartProcess"
    PlanCreated = "PlanCreated"
    PlanRefined = "PlanRefined"
    ExecuteNext = "ExecuteNext"
    TaskExecuted = "TaskExecuted"
    ReplanNeeded = "ReplanNeeded"
    PlanFinished = "PlanFinished"


#
# 2) Planner Step
#
class PlannerStepState:
    times_called: int = 0


class PlannerStep(KernelProcessStep[PlannerStepState]):
    CREATE_PLAN: ClassVar[str] = "create_plan"
    state: PlannerStepState = Field(default_factory=PlannerStepState)

    async def activate(self, state: KernelProcessStepState[PlannerStepState]):
        self.state = state.state

    @kernel_function(name=CREATE_PLAN)
    async def create_plan(self, user_request: str, context: KernelProcessStepContext) -> dict:
        self.state.times_called += 1
        prompt = (
            f"The user wants:\n{user_request}\n"
            "Propose a short plan with 2 or 3 bullet points for how to solve it. Keep them concise."
            "Keep citations as part of the plan.\n\n"
        )

        response = await run_openai_agent(
            instructions="You generate short tasks to solve the user's request. Use any tool if relevant.",
            prompt=prompt,
            agent_name="PlanAgent",
        )
        plan_lines = response.strip().split("\n")

        tasks = [line.lstrip("-* ").strip() for line in plan_lines if line.strip()]
        print(f"[PlannerStep] Created plan: {tasks} (times_called={self.state.times_called})")

        return {"plan": tasks}


#
# 3) Replan Step
#
class ReplanStepState:
    times_called: int = 0


class ReplanStep(KernelProcessStep[ReplanStepState]):
    REFINE_PLAN: ClassVar[str] = "refine_plan"
    state: ReplanStepState = Field(default_factory=ReplanStepState)

    async def activate(self, state: KernelProcessStepState[ReplanStepState]):
        self.state = state.state

    @kernel_function(name=REFINE_PLAN)
    async def refine_plan(self, payload: dict, context: KernelProcessStepContext) -> dict:
        leftover = payload.get("leftover", [])
        reason = payload.get("reason", "")
        self.state.times_called += 1
        prompt = (
            f"Leftover tasks:\n{leftover}\n"
            f"Reason for replanning: {reason}\n"
            "Propose an updated set of tasks as bullet points."
        )
        response = await run_openai_agent(
            instructions="Refine or replan tasks for final answer.",
            prompt=prompt,
            agent_name="ReplanAgent",
        )
        plan_lines = response.strip().split("\n")
        new_plan = [line.lstrip("-* ").strip() for line in plan_lines if line.strip()]
        print(f"[ReplanStep] New plan: {new_plan} (times_called={self.state.times_called})")

        return {"plan": new_plan}


#
# 4) Execute Step
#
class ExecuteStepState:
    current_index: int = 0


class ExecuteStep(KernelProcessStep[ExecuteStepState]):
    EXECUTE_PLAN: ClassVar[str] = "execute_plan"
    state: ExecuteStepState = Field(default_factory=ExecuteStepState)

    async def activate(self, state: KernelProcessStepState[ExecuteStepState]):
        self.state = state.state

    @kernel_function(name=EXECUTE_PLAN)
    async def execute_plan(self, payload: dict, context: KernelProcessStepContext) -> dict:
        plan = payload["plan"]
        partials = payload.get("partials", [])  # May be empty on first run

        if self.state.current_index >= len(plan):
            # No more tasks
            return {
                "partial_result": "All tasks done",
                "plan": plan,
                "current_index": self.state.current_index,
            }

        current_task = plan[self.state.current_index]

        # Incorporate partial context into the prompt:
        prompt = (
            f"So far we have these partial results:\n\n{chr(10).join(partials)}\n\nNow your task is: {current_task}"
        )

        response = await run_openai_agent(
            instructions="Use the partial results and any relevant tools to complete the next step.",
            prompt=prompt,
            agent_name="ExecuteAgent",
        )

        partial_result = response.strip()

        executed_index = self.state.current_index
        self.state.current_index += 1

        return {
            "partial_result": partial_result,
            "plan": plan,
            "current_index": executed_index,
        }


#
# 5) Decision Step
#
class DecisionStepState(KernelBaseModel):
    partials: list[str] = Field(default_factory=list)
    last_decision: str = ""


class DecisionStep(KernelProcessStep[DecisionStepState]):
    MAKE_DECISION: ClassVar[str] = "make_decision"
    state: DecisionStepState = Field(default_factory=DecisionStepState)

    async def activate(self, state: KernelProcessStepState[DecisionStepState]):
        self.state = state.state

    @kernel_function(name=MAKE_DECISION)
    async def make_decision(self, data: dict, context: KernelProcessStepContext):
        partial_result = data.get("partial_result", "")
        plan = data.get("plan", [])
        current_index = data.get("current_index", 0)

        # Accumulate partial
        if partial_result and partial_result.lower() != "all tasks done":
            self.state.partials.append(partial_result)

        # (A) If "All tasks done"
        if partial_result.strip().lower().startswith("all tasks done"):
            final_text = "[FINAL] All tasks completed.\n\n=== Aggregated Partial Results ===\n" + "\n\n".join(
                self.state.partials
            )
            await context.emit_event(PlanExecuteEvents.PlanFinished, data=final_text)
            return

        # (B) If physically done all tasks
        if current_index >= len(plan):
            final_text = "[FINAL] No more tasks.\n\n=== Aggregated Partial Results ===\n" + "\n\n".join(
                self.state.partials
            )
            await context.emit_event(PlanExecuteEvents.PlanFinished, data=final_text)
            return

        # (C) Let LLM decide: continue or replan
        prompt = (
            "We have a plan with remaining tasks.\n"
            "PARTIAL RESULTS SO FAR:\n" + "\n".join(self.state.partials) + "\n\n"
            "Decide: 'continue' with the next step or 'replan' if something is invalid. "
            "DO NOT say 'finish' if tasks remain. Return only 'continue' or 'replan'."
        )

        response = await run_openai_agent(
            instructions="Plan orchestrator with web-search if needed. Only respond 'continue' or 'replan'.",
            prompt=prompt,
            agent_name="DecisionAgent",
        )

        decision = response.strip().lower()

        print(f"[DecisionStep] LLM decision: {decision}")
        self.state.last_decision = decision

        # If replan => emit ReplanNeeded
        if "replan" in decision:
            leftover = plan[current_index:]
            payload = {"leftover": leftover, "reason": partial_result}
            await context.emit_event(PlanExecuteEvents.ReplanNeeded, data=payload)
            return

        # Default => continue
        await context.emit_event(
            PlanExecuteEvents.ExecuteNext,
            data={
                "plan": plan,
                "partials": self.state.partials,
            },
        )


#
# 6) Output Step
#
class OutputStepState:
    last_message: str = ""


class OutputStep(KernelProcessStep[OutputStepState]):
    SHOW_MESSAGE: ClassVar[str] = "show_message"
    state: OutputStepState = Field(default_factory=OutputStepState)

    async def activate(self, state: KernelProcessStepState[OutputStepState]):
        self.state = state.state

    @kernel_function(name=SHOW_MESSAGE)
    async def show_message(self, message: str | list[str]):
        self.state.last_message = message
        print(f"[OutputStep] {message}")


#
# 7) Build the Process
#
def build_process() -> KernelProcess:
    builder = ProcessBuilder(name="GeneralPlanAndExecute")

    # Steps
    planner = builder.add_step(PlannerStep)
    replan = builder.add_step(ReplanStep)
    executor = builder.add_step(ExecuteStep)
    decider = builder.add_step(DecisionStep)
    output = builder.add_step(OutputStep)

    # 1) Start => Planner
    builder.on_input_event(PlanExecuteEvents.StartProcess).send_event_to(target=planner, parameter_name="user_request")

    # 2) Planner => Executor + Output
    planner.on_function_result(PlannerStep.CREATE_PLAN).send_event_to(target=executor, parameter_name="payload")

    planner.on_function_result(PlannerStep.CREATE_PLAN).send_event_to(
        target=output,
        parameter_name="message",
    )

    # 3) Executor => Decision
    executor.on_function_result(ExecuteStep.EXECUTE_PLAN).send_event_to(target=decider, parameter_name="data")

    # 4) Decision => (ExecuteNext, ReplanNeeded, PlanFinished)
    decider.on_event(PlanExecuteEvents.ExecuteNext).send_event_to(target=executor, parameter_name="payload")
    decider.on_event(PlanExecuteEvents.ReplanNeeded).send_event_to(target=replan, parameter_name="payload")
    decider.on_event(PlanExecuteEvents.PlanFinished).send_event_to(target=output, parameter_name="message")
    decider.on_event(PlanExecuteEvents.PlanFinished).stop_process()

    # 5) Replan => Executor
    replan.on_function_result(ReplanStep.REFINE_PLAN).send_event_to(target=executor, parameter_name="payload")

    return builder.build()


async def main():
    logging.basicConfig(level=logging.WARNING)

    # Provide any user question
    user_question = "Where was the quarterback of the winning team in the 2014 Super Bowl born?"
    print(f"Starting process with: {user_question}")

    process = build_process()
    async with await start_local_process(
        process=process,
        kernel=Kernel(),
        initial_event=KernelProcessEvent(
            id=PlanExecuteEvents.StartProcess,
            data=user_question,
            visibility=KernelProcessEventVisibility.Public,
        ),
    ) as process_context:
        # Finally, get the Output
        process_state = await process_context.get_state()
        output_step_state: KernelProcessStepState[OutputStepState] = next(
            (s.state for s in process_state.steps if s.state.name == "OutputStep"), None
        )
        final_msg = output_step_state.state.last_message if output_step_state else "No final message."
        print(f"\n\n[Final State] => {final_msg}")

    """
    Sample Output:

    Starting process with: Where was the quarterback of the winning team in the 2014 Super Bowl born?
    [PlannerStep] Created plan: ['1. Identify the winning team and quarterback of the 2014 Super Bowl.', '2. Find the 
        birthplace of that quarterback.'] (times_called=1)
    [OutputStep] {'plan': ['1. Identify the winning team and quarterback of the 2014 Super Bowl.', '2. Find the 
        birthplace of that quarterback.']}
    [DecisionStep] LLM decision: continue
    [DecisionStep] LLM decision: continue
    [OutputStep] [FINAL] All tasks completed.

    === Aggregated Partial Results ===
    The winning team of the 2014 Super Bowl (Super Bowl XLVIII) was the Seattle Seahawks. The quarterback for the 
        Seahawks at that time was Russell Wilson.

    Russell Wilson was born in Cincinnati, Ohio.


    [Final State] => [FINAL] All tasks completed.

    === Aggregated Partial Results ===
    The winning team of the 2014 Super Bowl (Super Bowl XLVIII) was the Seattle Seahawks. The quarterback for the 
        Seahawks at that time was Russell Wilson.
    """


if __name__ == "__main__":
    asyncio.run(main())
