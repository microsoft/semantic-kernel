# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from samples.getting_started_with_processes.step03.processes.fried_fish_process import FriedFishProcess
from samples.getting_started_with_processes.step03.steps.external_step import ExternalStep
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder


class AddBunStep(KernelProcessStep):
    class Functions(Enum):
        AddBuns = "AddBuns"

    class OutputEvents(Enum):
        BunsAdded = "BunsAdded"

    @kernel_function(name=Functions.AddBuns.value)
    async def slice_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        print(f"BUNS_ADDED_STEP: Buns added to ingredient {food_actions[0]}")
        food_actions.append("Buns")
        await context.emit_event(process_event=self.OutputEvents.BunsAdded.value, data=food_actions)


class AddSpecialSauceStep(KernelProcessStep):
    class Functions(Enum):
        AddSpecialSauce = "AddSpecialSauce"

    class OutputEvents(Enum):
        SpecialSauceAdded = "SpecialSauceAdded"

    @kernel_function(name=Functions.AddSpecialSauce.value)
    async def slice_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        print(f"SPECIAL_SAUCE_ADDED: Special sauce added to ingredient {food_actions[0]}")
        food_actions.append("Sauce")
        await context.emit_event(process_event=self.OutputEvents.SpecialSauceAdded.value, data=food_actions)


class ExternalFriedFishStep(ExternalStep):
    def __init__(self):
        super().__init__(FishSandwichProcess.ProcessEvents.FishSandwichReady.value)


class FishSandwichProcess:
    class ProcessEvents(Enum):
        PrepareFishSandwich = "PrepareFishSandwich"
        FishSandwichReady = "FishSandwichReady"

    @staticmethod
    def create_process(process_name: str = "FishSandwichProcess"):
        process_builder = ProcessBuilder(process_name)
        make_fried_fish_step = process_builder.add_step_from_process(FriedFishProcess.create_process())
        add_buns_step = process_builder.add_step(AddBunStep)
        add_special_sauce_step = process_builder.add_step(AddSpecialSauceStep)
        external_step = process_builder.add_step(ExternalFriedFishStep)

        process_builder.on_input_event(FishSandwichProcess.ProcessEvents.PrepareFishSandwich.value).send_event_to(
            make_fried_fish_step.where_input_event_is(FriedFishProcess.ProcessEvents.PrepareFriedFish.value)
        )

        make_fried_fish_step.on_event(FriedFishProcess.ProcessEvents.FriedFishReady.value).send_event_to(
            ProcessFunctionTargetBuilder(add_buns_step)
        )

        add_buns_step.on_event(AddBunStep.OutputEvents.BunsAdded.value).send_event_to(
            ProcessFunctionTargetBuilder(add_special_sauce_step)
        )

        add_special_sauce_step.on_event(AddSpecialSauceStep.OutputEvents.SpecialSauceAdded.value).send_event_to(
            ProcessFunctionTargetBuilder(external_step)
        )

        return process_builder
