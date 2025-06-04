# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from samples.getting_started_with_processes.step03.models.food_ingredients import FoodIngredients
from samples.getting_started_with_processes.step03.steps.cut_food_step import CutFoodStep
from samples.getting_started_with_processes.step03.steps.cut_food_with_sharpening_step import CutFoodWithSharpeningStep
from samples.getting_started_with_processes.step03.steps.fry_food_step import FryFoodStep
from samples.getting_started_with_processes.step03.steps.gather_ingredients_step import (
    GatherIngredientsStep,
    GatherIngredientsWithStockStep,
)
from semantic_kernel.processes import ProcessBuilder


class GatherPotatoFriesIngredientsStep(GatherIngredientsStep):
    def __init__(self):
        super().__init__(FoodIngredients.POTATOES)


class GatherPotatoFriesIngredientsWithStockStep(GatherIngredientsWithStockStep):
    def __init__(self):
        super().__init__(FoodIngredients.POTATOES)


class PotatoFriesProcess:
    class ProcessEvents(Enum):
        PreparePotatoFries = "PreparePotatoFries"
        PotatoFriesReady = FryFoodStep.OutputEvents.FriedFoodReady.value

    @staticmethod
    def create_process(process_name: str = "PotatoFriesProcess"):
        process_builder = ProcessBuilder(process_name)
        gather_ingredients_step = process_builder.add_step(GatherPotatoFriesIngredientsStep)
        slice_step = process_builder.add_step(CutFoodStep, name="sliceStep")
        fry_step = process_builder.add_step(FryFoodStep)

        process_builder.on_input_event(PotatoFriesProcess.ProcessEvents.PreparePotatoFries).send_event_to(
            gather_ingredients_step
        )

        gather_ingredients_step.on_event(
            GatherPotatoFriesIngredientsStep.OutputEvents.IngredientsGathered
        ).send_event_to(slice_step, function_name=CutFoodStep.Functions.SliceFood)

        slice_step.on_event(CutFoodStep.OutputEvents.SlicingReady).send_event_to(fry_step)

        fry_step.on_event(FryFoodStep.OutputEvents.FoodRuined).send_event_to(gather_ingredients_step)

        return process_builder

    @staticmethod
    def create_process_with_stateful_steps(process_name: str = "PotatoFriesWithStatefulStepsProcess"):
        process_builder = ProcessBuilder(process_name)
        gather_ingredients_step = process_builder.add_step(GatherPotatoFriesIngredientsWithStockStep)
        slice_step = process_builder.add_step(CutFoodWithSharpeningStep, name="sliceStep")
        fry_step = process_builder.add_step(FryFoodStep)

        process_builder.on_input_event(PotatoFriesProcess.ProcessEvents.PreparePotatoFries).send_event_to(
            gather_ingredients_step
        )

        gather_ingredients_step.on_event(
            GatherPotatoFriesIngredientsWithStockStep.OutputEvents.IngredientsGathered
        ).send_event_to(slice_step, function_name=CutFoodWithSharpeningStep.Functions.SliceFood)

        gather_ingredients_step.on_event(
            GatherPotatoFriesIngredientsWithStockStep.OutputEvents.IngredientsOutOfStock
        ).stop_process()

        slice_step.on_event(CutFoodWithSharpeningStep.OutputEvents.SlicingReady).send_event_to(fry_step)

        slice_step.on_event(CutFoodWithSharpeningStep.OutputEvents.KnifeNeedsSharpening).send_event_to(
            slice_step, function_name=CutFoodWithSharpeningStep.Functions.SharpenKnife
        )

        slice_step.on_event(CutFoodWithSharpeningStep.OutputEvents.KnifeSharpened).send_event_to(
            slice_step, function_name=CutFoodWithSharpeningStep.Functions.SliceFood
        )

        fry_step.on_event(FryFoodStep.OutputEvents.FoodRuined).send_event_to(gather_ingredients_step)

        return process_builder
