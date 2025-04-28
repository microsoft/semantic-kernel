# Copyright (c) Microsoft. All rights reserved.


import asyncio

from samples.getting_started_with_processes.step03.models.food_order_item import FoodItem
from samples.getting_started_with_processes.step03.processes.single_food_item_process import SingleFoodItemProcess
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start

"""
Demonstrate the creation of KernelProcess and eliciting different food related events.
For visual reference of the processes used here check the diagram in:
https://github.com/microsoft/semantic-kernel/tree/main/python/samples/
getting_started_with_processes#step03b_food_ordering
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id=service_id), overwrite=True)
    return kernel


async def use_prepare_food_order_process_single_item(food_item: FoodItem):
    kernel = _create_kernel_with_chat_completion("sample")
    kernel_process = SingleFoodItemProcess.create_process().build()
    async with await start(
        kernel_process,
        kernel,
        KernelProcessEvent(id=SingleFoodItemProcess.ProcessEvents.SingleOrderReceived, data=food_item),
    ) as running_process:
        return running_process


async def use_single_order_fried_fish():
    await use_prepare_food_order_process_single_item(FoodItem.FRIED_FISH)


async def use_single_order_potato_fries():
    await use_prepare_food_order_process_single_item(FoodItem.POTATO_FRIES)


async def use_single_order_fish_sandwich():
    await use_prepare_food_order_process_single_item(FoodItem.FISH_SANDWICH)


async def use_single_order_fish_and_chips():
    await use_prepare_food_order_process_single_item(FoodItem.FISH_AND_CHIPS)


async def main():
    order_methods = [
        (use_single_order_fried_fish, "use_single_order_fried_fish"),
        (use_single_order_potato_fries, "use_single_order_potato_fries"),
        (use_single_order_fish_sandwich, "use_single_order_fish_sandwich"),
        (use_single_order_fish_and_chips, "use_single_order_fish_and_chips"),
    ]

    for method, name in order_methods:
        print(f"=== Start '{name}' ===")
        await method()
        print(f"=== End '{name}' ===\n")


if __name__ == "__main__":
    asyncio.run(main())
