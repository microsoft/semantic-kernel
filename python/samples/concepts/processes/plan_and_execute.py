# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.agents import OpenAIResponsesAgent
from semantic_kernel.functions import kernel_function
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
refine, and execute a plan based on a user's query. An OpenAI api key is required to run this sample. The Azure OpenAI 
Responses API does not yet support the web search tool.

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


#
# 1) Helper to run OpenAI agent
#
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
# 2) Global Events
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
# 3) Planner Step
#
class PlannerStepState(BaseModel):
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
# 4) Replan Step
#
class ReplanStepState(BaseModel):
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
# 5) Execute Step
#
class ExecuteStepState(BaseModel):
    current_index: int = 0


class ExecuteStep(KernelProcessStep[ExecuteStepState]):
    EXECUTE_PLAN: ClassVar[str] = "execute_plan"
    state: ExecuteStepState = Field(default_factory=ExecuteStepState)

    async def activate(self, state: KernelProcessStepState[ExecuteStepState]):
        self.state = state.state

    @kernel_function(name=EXECUTE_PLAN)
    async def execute_plan(self, payload: dict, context: KernelProcessStepContext) -> dict:
        plan = payload["plan"]
        partials = payload.get("partials", [])

        if self.state.current_index >= len(plan):
            return {
                "partial_result": "All tasks done",
                "plan": plan,
                "current_index": self.state.current_index,
            }

        current_task = plan[self.state.current_index]
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
# 6) Decision Step
#
class DecisionStepState(BaseModel):
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

        # A) If "All tasks done"
        if partial_result.strip().lower().startswith("all tasks done"):
            # No more tasks
            final_text = "\n".join(self.state.partials)
            payload = {
                "type": "final",
                "content": final_text.strip(),
            }
            await context.emit_event(PlanExecuteEvents.PlanFinished, data=payload)
            return

        # B) If physically done all tasks
        if current_index >= len(plan):
            final_text = "\n".join(self.state.partials)
            payload = {
                "type": "final",
                "content": final_text.strip(),
            }
            await context.emit_event(PlanExecuteEvents.PlanFinished, data=payload)
            return

        # C) Otherwise: let LLM decide whether to continue or replan
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
# 7) Output Step
#
class OutputStepState(BaseModel):
    debug_history: list[str] = Field(default_factory=list)
    final_answer: str = ""


class OutputStep(KernelProcessStep[OutputStepState]):
    SHOW_MESSAGE: ClassVar[str] = "show_message"
    state: OutputStepState = Field(default_factory=OutputStepState)

    async def activate(self, state: KernelProcessStepState[OutputStepState]):
        self.state = state.state

    @kernel_function(name=SHOW_MESSAGE)
    async def show_message(self, message: dict):
        """Handles either debug messages or final messages."""
        msg_type = message.get("type", "debug")
        content = message.get("content", "")

        if msg_type == "debug":
            self.state.debug_history.append(content)
            print(content)
        else:
            # final
            self.state.final_answer = content
            print("[OutputStep] Storing final result:", content)


#
# 8) Build the Process
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

    # 2) Planner => Executor + Output (debug)
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
    print(f"Starting process with: '{user_question}'")

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
        # Retrieve final state
        process_state = await process_context.get_state()
        output_step_state: KernelProcessStepState[OutputStepState] = next(
            (s.state for s in process_state.steps if s.state.name == "OutputStep"), None
        )

        if output_step_state:
            # Final user-facing answer:
            final_answer = output_step_state.state.final_answer.strip()

            print("\n[Final State]:")
            print(final_answer)
        else:
            print("[Final State]: No final message.")

    """
    Starting process with: 'Where was the quarterback of the winning team in the 2014 Super Bowl born?'
    [PlannerStep] Created plan: ['Identify the Winning Team:** Find out which team won the 2014 Super Bowl. 
        [NFL.com](https://www.nfl.com/)', 'Locate the Quarterback:** Determine who was the quarterback for the winning 
        team during that game.', 'Research Birthplace:** Search for the birthplace of the identified quarterback. 
        [Wikipedia](https://www.wikipedia.org/)'] (times_called=1)

    [DecisionStep] LLM decision: continue
    [DecisionStep] LLM decision: continue
    [DecisionStep] LLM decision: continue
    [OutputStep] Storing final result: The Seattle Seahawks won Super Bowl XLVIII in 2014, defeating the Denver Broncos 
        43-8. The Seahawks' defense dominated the game, forcing four turnovers and limiting the Broncos' high-scoring 
        offense. Linebacker Malcolm Smith was named Super Bowl MVP after returning an interception 69 yards for a 
        touchdown. ([nfl.com](https://www.nfl.com/news/seattle-seahawks-d-dominates-manning-denver-broncos-to-win-supe-0ap2000000323056?utm_source=openai))
    The quarterback for the Seattle Seahawks during Super Bowl XLVIII was Russell Wilson.
    Russell Wilson, the quarterback for the Seattle Seahawks during Super Bowl XLVIII, was born on November 29, 1988, 
        in Cincinnati, Ohio. ([britannica.com](https://www.britannica.com/facts/Russell-Wilson?utm_source=openai))

    [Final State]:
    The Seattle Seahawks won Super Bowl XLVIII in 2014, defeating the Denver Broncos 43-8. The Seahawks' defense 
        dominated the game, forcing four turnovers and limiting the Broncos' high-scoring offense. Linebacker Malcolm 
        Smith was named Super Bowl MVP after returning an interception 69 yards for a touchdown. 
        ([nfl.com](https://www.nfl.com/news/seattle-seahawks-d-dominates-manning-denver-broncos-to-win-supe-0ap2000000323056?utm_source=openai))
    The quarterback for the Seattle Seahawks during Super Bowl XLVIII was Russell Wilson.
    Russell Wilson, the quarterback for the Seattle Seahawks during Super Bowl XLVIII, was born on November 29, 1988, 
        in Cincinnati, Ohio. ([britannica.com](https://www.britannica.com/facts/Russell-Wilson?utm_source=openai))
    """


if __name__ == "__main__":
    asyncio.run(main())
