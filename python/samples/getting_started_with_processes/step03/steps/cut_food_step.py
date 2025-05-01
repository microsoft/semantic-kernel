# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep,
    KernelProcessStepContext,
    kernel_process_step_metadata,
)


@kernel_process_step_metadata("CutFoodStep.V1")
class CutFoodStep(KernelProcessStep):
    class Functions(Enum):
        ChopFood = "ChopFood"
        SliceFood = "SliceFood"

    class OutputEvents(Enum):
        ChoppingReady = "ChoppingReady"
        SlicingReady = "SlicingReady"

    def get_action_string(self, food: str, action: str) -> str:
        return f"{food}_{action}"

    @kernel_function(name=Functions.ChopFood)
    async def chop_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        food_to_be_cut = food_actions[0]
        food_actions.append(self.get_action_string(food_to_be_cut, "chopped"))
        print(f"CUTTING_STEP: Ingredient {food_to_be_cut} has been chopped!")
        await context.emit_event(process_event=CutFoodStep.OutputEvents.ChoppingReady, data=food_actions)

    @kernel_function(name=Functions.SliceFood)
    async def slice_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        food_to_be_cut = food_actions[0]
        food_actions.append(self.get_action_string(food_to_be_cut, "sliced"))
        print(f"CUTTING_STEP: Ingredient {food_to_be_cut} has been sliced!")
        await context.emit_event(process_event=CutFoodStep.OutputEvents.SlicingReady, data=food_actions)
