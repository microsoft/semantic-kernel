# Copyright (c) Microsoft. All rights reserved.

import json
from enum import Enum

from samples.getting_started_with_processes.step03.processes.fried_fish_process import FriedFishProcess
from samples.getting_started_with_processes.step03.processes.potato_fries_process import PotatoFriesProcess
from samples.getting_started_with_processes.step03.steps.external_step import ExternalStep
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder


class AddFishAndChipsCondimentsStep(KernelProcessStep):
    class Functions(Enum):
        AddCondiments = "AddCondiments"

    class OutputEvents(Enum):
        CondimentsAdded = "CondimentsAdded"

    @kernel_function(name=Functions.AddCondiments)
    async def add_condiments(
        self, context: KernelProcessStepContext, fish_actions: list[str], potato_actions: list[str]
    ):
        print(
            f"ADD_CONDIMENTS: Added condiments to Fish & Chips - Fish: {json.dumps(fish_actions)}, Potatoes: {json.dumps(potato_actions)}"  # noqa: E501
        )
        fish_actions.extend(potato_actions)
        fish_actions.append("Condiments")
        await context.emit_event(
            process_event=AddFishAndChipsCondimentsStep.OutputEvents.CondimentsAdded, data=fish_actions
        )


class FishAndChipsProcess:
    class ProcessEvents(Enum):
        PrepareFishAndChips = "PrepareFishAndChips"
        FishAndChipsReady = "FishAndChipsReady"

    class ExternalFishAndChipsStep(ExternalStep):
        def __init__(self):
            super().__init__(FishAndChipsProcess.ProcessEvents.FishAndChipsReady)

    @staticmethod
    def create_process(process_name: str = "FishAndChipsProcess"):
        process_builder = ProcessBuilder(process_name)
        make_fried_fish_step = process_builder.add_step_from_process(FriedFishProcess.create_process())
        make_potato_fries_step = process_builder.add_step_from_process(PotatoFriesProcess.create_process())
        add_condiments_step = process_builder.add_step(AddFishAndChipsCondimentsStep)
        external_step = process_builder.add_step(FishAndChipsProcess.ExternalFishAndChipsStep)

        process_builder.on_input_event(FishAndChipsProcess.ProcessEvents.PrepareFishAndChips).send_event_to(
            make_fried_fish_step.where_input_event_is(FriedFishProcess.ProcessEvents.PrepareFriedFish)
        ).send_event_to(
            make_potato_fries_step.where_input_event_is(PotatoFriesProcess.ProcessEvents.PreparePotatoFries)
        )

        make_fried_fish_step.on_event(FriedFishProcess.ProcessEvents.FriedFishReady).send_event_to(
            ProcessFunctionTargetBuilder(add_condiments_step, parameter_name="fishActions")
        )

        make_potato_fries_step.on_event(PotatoFriesProcess.ProcessEvents.PotatoFriesReady).send_event_to(
            ProcessFunctionTargetBuilder(add_condiments_step, parameter_name="potatoActions")
        )

        add_condiments_step.on_event(AddFishAndChipsCondimentsStep.OutputEvents.CondimentsAdded).send_event_to(
            ProcessFunctionTargetBuilder(external_step, parameter_name="fishActions")
        )

        return process_builder
