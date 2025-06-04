# Copyright (c) Microsoft. All rights reserved.
from enum import Enum

from samples.getting_started_with_processes.step03.models import FoodIngredients
from samples.getting_started_with_processes.step03.steps import (
    CutFoodStep,
    FryFoodStep,
    GatherIngredientsStep,
)
from samples.getting_started_with_processes.step03.steps.cut_food_with_sharpening_step import (
    CutFoodWithSharpeningStep,
)
from samples.getting_started_with_processes.step03.steps.gather_ingredients_step import (
    GatherIngredientsWithStockStep,
)
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import (
    kernel_process_step_metadata,
)


@kernel_process_step_metadata("GatherFishIngredient.V1")
class GatherFriedFishIngredientsStep(GatherIngredientsStep):
    def __init__(self) -> None:
        super().__init__(FoodIngredients.FISH)


@kernel_process_step_metadata("GatherFishIngredient.V2")
class GatherFriedFishIngredientsWithStockStep(GatherIngredientsWithStockStep):
    def __init__(self) -> None:
        super().__init__(FoodIngredients.FISH)


class FriedFishProcess:
    class ProcessEvents(Enum):
        PrepareFriedFish = "PrepareFriedFish"
        FriedFishReady = FryFoodStep.OutputEvents.FriedFoodReady.value

    @staticmethod
    def create_process(process_name: str = "FriedFishProcess") -> ProcessBuilder:
        process_builder = ProcessBuilder(process_name)
        gather = process_builder.add_step(GatherFriedFishIngredientsStep)
        chop = process_builder.add_step(CutFoodStep, name="chopStep")
        fry = process_builder.add_step(FryFoodStep)

        process_builder.on_input_event(FriedFishProcess.ProcessEvents.PrepareFriedFish).send_event_to(gather)

        gather.on_event(GatherFriedFishIngredientsStep.OutputEvents.IngredientsGathered).send_event_to(
            chop, function_name=CutFoodStep.Functions.ChopFood
        )

        chop.on_event(CutFoodStep.OutputEvents.ChoppingReady).send_event_to(fry)
        fry.on_event(FryFoodStep.OutputEvents.FoodRuined).send_event_to(gather)
        return process_builder

    @staticmethod
    def create_process_with_stateful_steps_v1(
        process_name: str = "FriedFishWithStatefulStepsProcess",
    ) -> ProcessBuilder:
        process_builder = ProcessBuilder(name=process_name, version="FriedFishProcess.v1")

        gather = process_builder.add_step(GatherFriedFishIngredientsWithStockStep)
        chop = process_builder.add_step(CutFoodWithSharpeningStep, name="chopStep")
        fry = process_builder.add_step(FryFoodStep)

        process_builder.on_input_event(FriedFishProcess.ProcessEvents.PrepareFriedFish).send_event_to(gather)

        gather.on_event(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsGathered).send_event_to(
            chop, function_name=CutFoodWithSharpeningStep.Functions.ChopFood
        )
        gather.on_event(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsOutOfStock).stop_process()

        chop.on_event(CutFoodWithSharpeningStep.OutputEvents.ChoppingReady).send_event_to(fry)
        chop.on_event(CutFoodWithSharpeningStep.OutputEvents.KnifeNeedsSharpening).send_event_to(
            chop, function_name=CutFoodWithSharpeningStep.Functions.SharpenKnife
        )
        chop.on_event(CutFoodWithSharpeningStep.OutputEvents.KnifeSharpened).send_event_to(
            chop, function_name=CutFoodWithSharpeningStep.Functions.ChopFood
        )

        fry.on_event(FryFoodStep.OutputEvents.FoodRuined).send_event_to(gather)
        return process_builder

    @staticmethod
    def create_process_with_stateful_steps_v2(
        process_name: str = "FriedFishWithStatefulStepsProcess",
    ) -> ProcessBuilder:
        process_builder = ProcessBuilder(name=process_name, version="FriedFishProcess.v2")

        gather = process_builder.add_step(
            GatherFriedFishIngredientsWithStockStep,
            name="gatherFishIngredientStep",
            aliases=["GatherFriedFishIngredientsWithStockStep"],
        )
        chop = process_builder.add_step(
            CutFoodWithSharpeningStep,
            name="chopFishStep",
            aliases=["CutFoodStep"],
        )
        fry = process_builder.add_step(FryFoodStep, name="fryFishStep", aliases=["FryFoodStep"])

        process_builder.on_input_event(FriedFishProcess.ProcessEvents.PrepareFriedFish).send_event_to(gather)

        gather.on_event(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsGathered).send_event_to(
            chop, function_name=CutFoodWithSharpeningStep.Functions.ChopFood
        )
        gather.on_event(GatherFriedFishIngredientsWithStockStep.OutputEvents.IngredientsOutOfStock).stop_process()

        chop.on_event(CutFoodWithSharpeningStep.OutputEvents.ChoppingReady).send_event_to(fry)
        chop.on_event(CutFoodWithSharpeningStep.OutputEvents.KnifeNeedsSharpening).send_event_to(
            chop, function_name=CutFoodWithSharpeningStep.Functions.SharpenKnife
        )
        chop.on_event(CutFoodWithSharpeningStep.OutputEvents.KnifeSharpened).send_event_to(
            chop, function_name=CutFoodWithSharpeningStep.Functions.ChopFood
        )

        fry.on_event(FryFoodStep.OutputEvents.FoodRuined).send_event_to(gather)
        return process_builder
