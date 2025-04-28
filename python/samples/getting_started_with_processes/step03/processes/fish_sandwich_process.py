# Copyright (c) Microsoft. All rights reserved.
from enum import Enum

from samples.getting_started_with_processes.step03.processes.fried_fish_process import (
    FriedFishProcess,
)
from samples.getting_started_with_processes.step03.steps.external_step import ExternalStep
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import (
    KernelProcessEventVisibility,
    KernelProcessStep,
    KernelProcessStepContext,
)


class AddBunStep(KernelProcessStep):
    class Functions(Enum):
        AddBuns = "AddBuns"

    class OutputEvents(Enum):
        BunsAdded = "BunsAdded"

    @kernel_function(name=Functions.AddBuns)
    async def slice_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        print(f"BUNS_ADDED_STEP: Buns added to ingredient {food_actions[0]}")
        food_actions.append("Buns")
        await context.emit_event(process_event=self.OutputEvents.BunsAdded, data=food_actions)


class AddSpecialSauceStep(KernelProcessStep):
    class Functions(Enum):
        AddSpecialSauce = "AddSpecialSauce"

    class OutputEvents(Enum):
        SpecialSauceAdded = "SpecialSauceAdded"

    @kernel_function(name=Functions.AddSpecialSauce)
    async def slice_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        print(f"SPECIAL_SAUCE_ADDED: Special sauce added to ingredient {food_actions[0]}")
        food_actions.append("Sauce")
        await context.emit_event(
            process_event=self.OutputEvents.SpecialSauceAdded,
            data=food_actions,
            visibility=KernelProcessEventVisibility.Public,
        )


class ExternalFriedFishStep(ExternalStep):
    def __init__(self) -> None:
        super().__init__(FishSandwichProcess.ProcessEvents.FishSandwichReady)


class FishSandwichProcess:
    class ProcessEvents(Enum):
        PrepareFishSandwich = "PrepareFishSandwich"
        FishSandwichReady = "FishSandwichReady"

    @staticmethod
    def create_process(process_name: str = "FishSandwichProcess") -> ProcessBuilder:
        process_builder = ProcessBuilder(process_name)

        make_fried_fish_step = process_builder.add_step_from_process(FriedFishProcess.create_process())
        add_buns_step = process_builder.add_step(AddBunStep)
        add_sauce_step = process_builder.add_step(AddSpecialSauceStep)
        external_step = process_builder.add_step(ExternalFriedFishStep)

        process_builder.on_input_event(FishSandwichProcess.ProcessEvents.PrepareFishSandwich).send_event_to(
            make_fried_fish_step.where_input_event_is(FriedFishProcess.ProcessEvents.PrepareFriedFish)
        )

        make_fried_fish_step.on_event(FriedFishProcess.ProcessEvents.FriedFishReady).send_event_to(add_buns_step)

        add_buns_step.on_event(AddBunStep.OutputEvents.BunsAdded).send_event_to(add_sauce_step)

        add_sauce_step.on_event(AddSpecialSauceStep.OutputEvents.SpecialSauceAdded).send_event_to(external_step)

        return process_builder

    @staticmethod
    def create_process_with_stateful_steps_v1(
        process_name: str = "FishSandwichWithStatefulStepsProcess",
    ) -> ProcessBuilder:
        process_builder = ProcessBuilder(process_name, version="FishSandwich.V1")

        make_fried_fish_step = process_builder.add_step_from_process(
            FriedFishProcess.create_process_with_stateful_steps_v1()
        )
        add_buns_step = process_builder.add_step(AddBunStep)
        add_sauce_step = process_builder.add_step(AddSpecialSauceStep)
        external_step = process_builder.add_step(ExternalFriedFishStep)

        process_builder.on_input_event(FishSandwichProcess.ProcessEvents.PrepareFishSandwich).send_event_to(
            make_fried_fish_step.where_input_event_is(FriedFishProcess.ProcessEvents.PrepareFriedFish)
        )

        make_fried_fish_step.on_event(FriedFishProcess.ProcessEvents.FriedFishReady).send_event_to(add_buns_step)

        add_buns_step.on_event(AddBunStep.OutputEvents.BunsAdded).send_event_to(add_sauce_step)

        add_sauce_step.on_event(AddSpecialSauceStep.OutputEvents.SpecialSauceAdded).send_event_to(external_step)

        return process_builder

    @staticmethod
    def create_process_with_stateful_steps_v2(
        process_name: str = "FishSandwichWithStatefulStepsProcess",
    ) -> ProcessBuilder:
        process_builder = ProcessBuilder(process_name, version="FishSandwich.V2")

        make_fried_fish_step = process_builder.add_step_from_process(
            FriedFishProcess.create_process_with_stateful_steps_v2(),
            aliases=["FriedFishWithStatefulStepsProcess"],
        )
        add_buns_step = process_builder.add_step(AddBunStep)
        add_sauce_step = process_builder.add_step(AddSpecialSauceStep)
        external_step = process_builder.add_step(ExternalFriedFishStep)

        process_builder.on_input_event(FishSandwichProcess.ProcessEvents.PrepareFishSandwich).send_event_to(
            make_fried_fish_step.where_input_event_is(FriedFishProcess.ProcessEvents.PrepareFriedFish)
        )

        make_fried_fish_step.on_event(FriedFishProcess.ProcessEvents.FriedFishReady).send_event_to(add_buns_step)

        add_buns_step.on_event(AddBunStep.OutputEvents.BunsAdded).send_event_to(add_sauce_step)

        add_sauce_step.on_event(AddSpecialSauceStep.OutputEvents.SpecialSauceAdded).send_event_to(external_step)

        return process_builder
