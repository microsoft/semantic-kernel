# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from random import Random

from pydantic import Field

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEventVisibility,
)
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext


class FryFoodStep(KernelProcessStep):
    class Functions(Enum):
        FryFood = "FryFood"

    class OutputEvents(Enum):
        FoodRuined = "FoodRuined"
        FriedFoodReady = "FriedFoodReady"

    random_seed: int = Field(default_factory=Random)

    @kernel_function(name=Functions.FryFood.value)
    async def fry_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        food_to_fry = food_actions[0]
        fryer_malfunction = self.random_seed.randint(0, 10)

        # Oh no! Food got burnt :(
        if fryer_malfunction < 5:
            food_actions.append(f"{food_to_fry}_frying_failed")
            print(f"FRYING_STEP: Ingredient {food_to_fry} got burnt while frying :(")
            await context.emit_event(process_event=FryFoodStep.OutputEvents.FoodRuined.value, data=food_actions)
            return

        food_actions.append(f"{food_to_fry}_frying_succeeded")
        print(f"FRYING_STEP: Ingredient {food_to_fry} is ready!")
        await context.emit_event(
            process_event=FryFoodStep.OutputEvents.FriedFoodReady.value,
            data=food_actions,
            visibility=KernelProcessEventVisibility.Public,
        )
