# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from pydantic import Field

from samples.getting_started_with_processes.step03.models.food_ingredients import FoodIngredients
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState


class GatherIngredientsStep(KernelProcessStep):
    class Functions(Enum):
        GatherIngredients = "GatherIngredients"

    class OutputEvents(Enum):
        IngredientsGathered = "IngredientsGathered"
        IngredientsOutOfStock = "IngredientsOutOfStock"

    ingredient: FoodIngredients

    def __init__(self, ingredient: FoodIngredients):
        super().__init__(ingredient=ingredient)

    @kernel_function(name=Functions.GatherIngredients)
    async def gather_ingredients(self, context: KernelProcessStepContext, food_actions: list[str]):
        ingredient = self.ingredient.to_friendly_string()
        updated_food_actions = []
        updated_food_actions.extend(food_actions)
        if len(updated_food_actions) == 0:
            updated_food_actions.append(ingredient)
        updated_food_actions.append(f"{ingredient}_gathered")

        print(f"GATHER_INGREDIENT: Gathered ingredient {ingredient}")
        await context.emit_event(
            process_event=GatherIngredientsStep.OutputEvents.IngredientsGathered, data=updated_food_actions
        )


class GatherIngredientsState(KernelBaseModel):
    ingredients_stock: int = Field(default=5, alias="IngredientsStock")


class GatherIngredientsWithStockStep(KernelProcessStep[GatherIngredientsState]):
    class Functions(Enum):
        GatherIngredients = "GatherIngredients"

    class OutputEvents(Enum):
        IngredientsGathered = "IngredientsGathered"
        IngredientsOutOfStock = "IngredientsOutOfStock"

    ingredient: FoodIngredients
    state: GatherIngredientsState | None = None

    def __init__(self, ingredient: FoodIngredients):
        super().__init__(ingredient=ingredient)

    async def activate(self, state: KernelProcessStepState[GatherIngredientsState]) -> None:
        self.state = state.state

    @kernel_function(name=Functions.GatherIngredients)
    async def gather_ingredients(self, context: KernelProcessStepContext, food_actions: list[str]):
        ingredient = self.ingredient.to_friendly_string()
        updated_food_actions = []
        updated_food_actions.extend(food_actions)

        if self.state.ingredients_stock == 0:
            print(f"GATHER_INGREDIENT: Could not gather {ingredient} - OUT OF STOCK!")
            await context.emit_event(
                process_event=GatherIngredientsWithStockStep.OutputEvents.IngredientsOutOfStock,
                data=updated_food_actions,
            )
            return

        if len(updated_food_actions) == 0:
            updated_food_actions.append(ingredient)
        updated_food_actions.append(f"{ingredient}_gathered")

        self.state.ingredients_stock -= 1
        print(f"GATHER_INGREDIENT: Gathered ingredient {ingredient} - remaining: {self.state.ingredients_stock}")
        await context.emit_event(
            process_event=GatherIngredientsWithStockStep.OutputEvents.IngredientsGathered,
            data=updated_food_actions,
        )
