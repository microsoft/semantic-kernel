# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from pydantic import Field

from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep,
    KernelProcessStepContext,
    KernelProcessStepState,
    kernel_process_step_metadata,
)


class CutFoodWithSharpeningState(KernelBaseModel):
    knife_sharpness: int = Field(default=5, alias="KnifeSharpness")
    needs_sharpening_limit: int = Field(default=3, alias="NeedsSharpeningLimit")
    sharpening_boost: int = Field(default=5, alias="SharpeningBoost")


@kernel_process_step_metadata("CutFoodStep.V2")
class CutFoodWithSharpeningStep(KernelProcessStep[CutFoodWithSharpeningState]):
    class Functions(Enum):
        ChopFood = "ChopFood"
        SliceFood = "SliceFood"
        SharpenKnife = "SharpenKnife"

    class OutputEvents(Enum):
        ChoppingReady = "ChoppingReady"
        SlicingReady = "SlicingReady"
        KnifeNeedsSharpening = "KnifeNeedsSharpening"
        KnifeSharpened = "KnifeSharpened"

    state: CutFoodWithSharpeningState | None = None

    async def activate(self, state: KernelProcessStepState[CutFoodWithSharpeningState]) -> None:
        self.state = state.state

    def knife_needs_sharpening(self) -> bool:
        return self.state.knife_sharpness == self.state.needs_sharpening_limit

    def get_action_string(self, food: str, action: str) -> str:
        return f"{food}_{action}"

    @kernel_function(name=Functions.ChopFood)
    async def chop_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        food_to_be_cut = food_actions[0]
        if self.knife_needs_sharpening():
            print(f"CUTTING_STEP: Dull knife, cannot chop {food_to_be_cut} - needs sharpening.")
            await context.emit_event(
                process_event=CutFoodWithSharpeningStep.OutputEvents.KnifeNeedsSharpening, data=food_actions
            )

            return
        # Update knife sharpness
        self.state.knife_sharpness -= 1

        food_actions.append(self.get_action_string(food_to_be_cut, "chopped"))
        print(
            f"CUTTING_STEP: Ingredient {food_to_be_cut} has been chopped! - knife sharpness: {self.state.knife_sharpness}"  # noqa: E501
        )
        await context.emit_event(process_event=CutFoodWithSharpeningStep.OutputEvents.ChoppingReady, data=food_actions)

    @kernel_function(name=Functions.SliceFood)
    async def slice_food(self, context: KernelProcessStepContext, food_actions: list[str]):
        food_to_be_cut = food_actions[0]
        if self.knife_needs_sharpening():
            print(f"CUTTING_STEP: Dull knife, cannot slice {food_to_be_cut} - needs sharpening.")
            await context.emit_event(
                process_event=CutFoodWithSharpeningStep.OutputEvents.KnifeNeedsSharpening, data=food_actions
            )

            return
        # Update knife sharpness
        self.state.knife_sharpness -= 1

        food_actions.append(self.get_action_string(food_to_be_cut, "sliced"))
        print(
            f"CUTTING_STEP: Ingredient {food_to_be_cut} has been sliced! - knife sharpness: {self.state.knife_sharpness}"  # noqa: E501
        )
        await context.emit_event(process_event=CutFoodWithSharpeningStep.OutputEvents.SlicingReady, data=food_actions)

    @kernel_function(name=Functions.SharpenKnife)
    async def sharpen_knife(self, context: KernelProcessStepContext, food_actions: list[str]):
        self.state.knife_sharpness += self.state.sharpening_boost
        print(f"KNIFE SHARPENED: Knife sharpness is now {self.state.knife_sharpness}!")
        await context.emit_event(process_event=CutFoodWithSharpeningStep.OutputEvents.KnifeSharpened, data=food_actions)
