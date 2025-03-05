# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from samples.demos.process_with_dapr.process.steps import (
    AStep,
    BStep,
    CommonEvents,
    CStep,
    CStepState,
    KickOffStep,
    bstep_factory,
)
from semantic_kernel.processes import ProcessBuilder

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess


def get_process() -> "KernelProcess":
    # Define the process builder
    process = ProcessBuilder(name="ProcessWithDapr")

    # Add the step types to the builder
    kickoff_step = process.add_step(step_type=KickOffStep)
    myAStep = process.add_step(step_type=AStep)
    myBStep = process.add_step(step_type=BStep, factory_function=bstep_factory)

    # Initialize the CStep with an initial state and the state's current cycle set to 1
    myCStep = process.add_step(step_type=CStep, initial_state=CStepState(current_cycle=1))

    # Define the input event and where to send it to
    process.on_input_event(event_id=CommonEvents.StartProcess).send_event_to(target=kickoff_step)

    # Define the process flow
    kickoff_step.on_event(event_id=CommonEvents.StartARequested).send_event_to(target=myAStep)
    kickoff_step.on_event(event_id=CommonEvents.StartBRequested).send_event_to(target=myBStep)
    myAStep.on_event(event_id=CommonEvents.AStepDone).send_event_to(target=myCStep, parameter_name="astepdata")

    # Define the fan in behavior once both AStep and BStep are done
    myBStep.on_event(event_id=CommonEvents.BStepDone).send_event_to(target=myCStep, parameter_name="bstepdata")
    myCStep.on_event(event_id=CommonEvents.CStepDone).send_event_to(target=kickoff_step)
    myCStep.on_event(event_id=CommonEvents.ExitRequested).stop_process()

    # Build the process
    return process.build()
