# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from samples.getting_started_with_processes.step03.models import FoodIngredients
from samples.getting_started_with_processes.step03.steps import CutFoodStep, FryFoodStep, GatherIngredientsStep
from samples.getting_started_with_processes.step03.steps.cut_food_with_sharpening_step import CutFoodWithSharpeningStep
from samples.getting_started_with_processes.step03.steps.gather_ingredients_step import GatherIngredientsWithStockStep
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder


class GatherFriedFishIngredientsStep(GatherIngredientsStep):
    def __init__(self):
        super().__init__(FoodIngredients.FISH)


class GatherFriedFishIngredientsWithStockStep(GatherIngredientsWithStockStep):
    def __init__(self):
        super().__init__(FoodIngredients.FISH)


class FriedFishProcess:
    class ProcessEvents(Enum):
        PrepareFriedFish = "PrepareFriedFish"
        FriedFishReady = FryFoodStep.OutputEvents.FriedFoodReady.value

    @staticmethod
    def create_process(process_name: str = "FriedFishProcess") -> ProcessBuilder:
        process_builder = ProcessBuilder(process_name)
        gatherIngredientsStep = process_builder.add_step(GatherFriedFishIngredientsStep)
        chopStep = process_builder.add_step(CutFoodStep, name="chopStep")
        fryStep = process_builder.add_step(FryFoodStep)

        process_builder.on_input_event(FriedFishProcess.ProcessEvents.PrepareFriedFish).send_event_to(
            gatherIngredientsStep
        )

        gatherIngredientsStep.on_event(GatherFriedFishIngredientsStep.OutputEvents.IngredientsGathered).send_event_to(
            ProcessFunctionTargetBuilder(chopStep, function_name=CutFoodStep.Functions.ChopFood)
        )

        chopStep.on_event(CutFoodStep.OutputEvents.ChoppingReady).send_event_to(ProcessFunctionTargetBuilder(fryStep))

        fryStep.on_event(FryFoodStep.OutputEvents.FoodRuined).send_event_to(
            ProcessFunctionTargetBuilder(gatherIngredientsStep)
        )

        return process_builder

    @staticmethod
    def create_process_with_stateful_steps(process_name: str = "FriedFishWithStatefulStepsProcess") -> ProcessBuilder:
        process_builder = ProcessBuilder(process_name)

        gather_ingredients_step = process_builder.add_step(GatherFriedFishIngredientsWithStockStep)
        chop_step = process_builder.add_step(CutFoodWithSharpeningStep, name="chopStep")
        fry_step = process_builder.add_step(FryFoodStep)

        process_builder.on_input_event(FriedFishProcess.ProcessEvents.PrepareFriedFish).send_event_to(
            gather_ingredients_step
        )

        gather_ingredients_step.on_event(
            GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsGathered
        ).send_event_to(
            ProcessFunctionTargetBuilder(chop_step, function_name=CutFoodWithSharpeningStep.Functions.ChopFood)
        )

        gather_ingredients_step.on_event(
            GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsOutOfStock
        ).stop_process()

        chop_step.on_event(CutFoodWithSharpeningStep.OutputEvents.ChoppingReady).send_event_to(
            ProcessFunctionTargetBuilder(fry_step)
        )

        chop_step.on_event(CutFoodWithSharpeningStep.OutputEvents.KnifeNeedsSharpening).send_event_to(
            ProcessFunctionTargetBuilder(chop_step, function_name=CutFoodWithSharpeningStep.Functions.SharpenKnife)
        )

        chop_step.on_event(CutFoodWithSharpeningStep.OutputEvents.KnifeSharpened).send_event_to(
            ProcessFunctionTargetBuilder(chop_step, function_name=CutFoodWithSharpeningStep.Functions.ChopFood)
        )

        fry_step.on_event(FryFoodStep.OutputEvents.FoodRuined).send_event_to(
            ProcessFunctionTargetBuilder(gather_ingredients_step)
        )

        return process_builder
