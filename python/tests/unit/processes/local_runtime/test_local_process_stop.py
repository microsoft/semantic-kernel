# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.const import END_PROCESS_ID
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.process_end_step import EndStep

CALLS: list[str] = []


class LoopStep(KernelProcessStep):
    """Sends its input on to the worker and asks to stop the process, every time it runs."""

    @kernel_function
    async def run(self, value: str, context: KernelProcessStepContext) -> None:
        CALLS.append("run")
        await context.emit_event("Work", data=value)
        await context.emit_event("Exit", data=None)


class WorkerStep(KernelProcessStep):
    """Sends its input back to the loop step."""

    @kernel_function
    async def work(self, value: str) -> str:
        CALLS.append("work")
        return value


def _build_loop(stop_with_event: str = "Exit"):
    builder = ProcessBuilder(name="stopper")
    loop_step = builder.add_step(LoopStep)
    worker_step = builder.add_step(WorkerStep)
    builder.on_input_event("go").send_event_to(loop_step, function_name="run", parameter_name="value")
    loop_step.on_event("Work").send_event_to(worker_step, function_name="work", parameter_name="value")
    loop_step.on_event(stop_with_event).stop_process()
    worker_step.on_function_result("work").send_event_to(loop_step, function_name="run", parameter_name="value")
    return builder, loop_step


def test_end_step_id_is_the_end_process_id():
    assert EndStep.get_instance().id == END_PROCESS_ID


def test_stop_process_edge_is_registered_for_the_event_it_was_set_on():
    builder, loop_step = _build_loop()

    process = builder.build()

    edges = next(step.output_edges for step in process.steps if step.state.name == "LoopStep")
    assert "END" not in edges
    assert [edge.output_target.step_id for edge in edges[loop_step.get_scoped_event_id("Exit")]] == [END_PROCESS_ID]


async def test_stop_process_ends_a_process_that_would_loop():
    CALLS.clear()
    builder, _ = _build_loop()

    await start(process=builder.build(), kernel=Kernel(), initial_event=KernelProcessEvent(id="go", data="x"))

    # The worker message that was sent in the same superstep as the stop still runs, then the process ends.
    assert CALLS == ["run", "work"]


async def test_process_without_stop_process_keeps_looping_until_the_superstep_limit():
    CALLS.clear()
    builder, _ = _build_loop(stop_with_event="Unused")

    await start(
        process=builder.build(), kernel=Kernel(), initial_event=KernelProcessEvent(id="go", data="x"), max_supersteps=6
    )

    assert CALLS == ["run", "work", "run", "work", "run", "work"]
