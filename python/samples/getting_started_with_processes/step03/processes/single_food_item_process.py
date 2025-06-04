# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from samples.getting_started_with_processes.step03.models.food_order_item import FoodItem
from samples.getting_started_with_processes.step03.processes.fish_and_chips_process import FishAndChipsProcess
from samples.getting_started_with_processes.step03.processes.fish_sandwich_process import FishSandwichProcess
from samples.getting_started_with_processes.step03.processes.fried_fish_process import FriedFishProcess
from samples.getting_started_with_processes.step03.processes.potato_fries_process import PotatoFriesProcess
from samples.getting_started_with_processes.step03.steps.external_step import ExternalStep
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext


class PackOrderStep(KernelProcessStep):
    class Functions(Enum):
        PackFood = "PackFood"

    class OutputEvents(Enum):
        FoodPacked = "FoodPacked"

    @kernel_function(name=Functions.PackFood)
    async def pack_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        print(f"PACKING_FOOD: Food {food_actions[0]} Packed! - {food_actions}")
        await context.emit_event(process_event=PackOrderStep.OutputEvents.FoodPacked)


class ExternalSingleOrderStep(ExternalStep):
    def __init__(self):
        super().__init__(SingleFoodItemProcess.ProcessEvents.SingleOrderReady)


class DispatchSingleOrderStep(KernelProcessStep):
    class Functions(Enum):
        PrepareSingleOrder = "PrepareSingleOrder"

    class OutputEvents(Enum):
        PrepareFries = "PrepareFries"
        PrepareFriedFish = "PrepareFriedFish"
        PrepareFishSandwich = "PrepareFishSandwich"
        PrepareFishAndChips = "PrepareFishAndChips"

    @kernel_function(name=Functions.PrepareSingleOrder)
    async def dispatch_single_order(self, context: KernelProcessStepContext, food_item: FoodItem):
        food_name = food_item.to_friendly_string()
        print(f"DISPATCH_SINGLE_ORDER: Dispatching '{food_name}'!")
        food_actions = []

        if food_item == FoodItem.POTATO_FRIES:
            await context.emit_event(process_event=DispatchSingleOrderStep.OutputEvents.PrepareFries, data=food_actions)

        elif food_item == FoodItem.FRIED_FISH:
            await context.emit_event(
                process_event=DispatchSingleOrderStep.OutputEvents.PrepareFriedFish, data=food_actions
            )

        elif food_item == FoodItem.FISH_SANDWICH:
            await context.emit_event(
                process_event=DispatchSingleOrderStep.OutputEvents.PrepareFishSandwich, data=food_actions
            )

        elif food_item == FoodItem.FISH_AND_CHIPS:
            await context.emit_event(
                process_event=DispatchSingleOrderStep.OutputEvents.PrepareFishAndChips, data=food_actions
            )


class SingleFoodItemProcess:
    class ProcessEvents(Enum):
        SingleOrderReceived = "SingleOrderReceived"
        SingleOrderReady = "SingleOrderReady"

    @staticmethod
    def create_process(process_name: str = "SingleFoodItemProcess"):
        process_builder = ProcessBuilder(process_name)

        dispatch_order_step = process_builder.add_step(DispatchSingleOrderStep)
        make_fried_fish_step = process_builder.add_step_from_process(FriedFishProcess.create_process())
        make_potato_fries_step = process_builder.add_step_from_process(PotatoFriesProcess.create_process())
        make_fish_sandwich_step = process_builder.add_step_from_process(FishSandwichProcess.create_process())
        make_fish_and_chips_step = process_builder.add_step_from_process(FishAndChipsProcess.create_process())
        pack_order_step = process_builder.add_step(PackOrderStep)
        external_step = process_builder.add_step(ExternalSingleOrderStep)

        process_builder.on_input_event(SingleFoodItemProcess.ProcessEvents.SingleOrderReceived).send_event_to(
            dispatch_order_step
        )

        dispatch_order_step.on_event(DispatchSingleOrderStep.OutputEvents.PrepareFriedFish).send_event_to(
            make_fried_fish_step.where_input_event_is(FriedFishProcess.ProcessEvents.PrepareFriedFish)
        )

        dispatch_order_step.on_event(DispatchSingleOrderStep.OutputEvents.PrepareFries).send_event_to(
            make_potato_fries_step.where_input_event_is(PotatoFriesProcess.ProcessEvents.PreparePotatoFries)
        )

        dispatch_order_step.on_event(DispatchSingleOrderStep.OutputEvents.PrepareFishSandwich).send_event_to(
            make_fish_sandwich_step.where_input_event_is(FishSandwichProcess.ProcessEvents.PrepareFishSandwich)
        )

        dispatch_order_step.on_event(DispatchSingleOrderStep.OutputEvents.PrepareFishAndChips).send_event_to(
            make_fish_and_chips_step.where_input_event_is(FishAndChipsProcess.ProcessEvents.PrepareFishAndChips)
        )

        make_fried_fish_step.on_event(FriedFishProcess.ProcessEvents.FriedFishReady).send_event_to(pack_order_step)

        make_potato_fries_step.on_event(PotatoFriesProcess.ProcessEvents.PotatoFriesReady).send_event_to(
            pack_order_step
        )

        make_fish_sandwich_step.on_event(FishSandwichProcess.ProcessEvents.FishSandwichReady).send_event_to(
            pack_order_step
        )

        make_fish_and_chips_step.on_event(FishAndChipsProcess.ProcessEvents.FishAndChipsReady).send_event_to(
            pack_order_step
        )

        pack_order_step.on_event(PackOrderStep.OutputEvents.FoodPacked).send_event_to(external_step)

        return process_builder
