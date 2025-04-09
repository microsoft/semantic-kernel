# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.getting_started_with_processes.step03.processes.fish_and_chips_process import FishAndChipsProcess
from samples.getting_started_with_processes.step03.processes.fish_sandwich_process import FishSandwichProcess
from samples.getting_started_with_processes.step03.processes.fried_fish_process import FriedFishProcess
from samples.getting_started_with_processes.step03.processes.potato_fries_process import PotatoFriesProcess
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder

################################################################################################
# Demonstrate the creation of KernelProcess and eliciting different food related events.       #
# For visual reference of the processes used here check the diagram in:                        #
# https://github.com/microsoft/semantic-kernel/tree/main/python/samples/                       #
# getting_started_with_processes#step03a_food_preparation                                      #
################################################################################################

# region Helper Methods


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id=service_id), overwrite=True)
    return kernel


async def use_prepare_specific_product(process: ProcessBuilder, external_trigger_event):
    kernel = _create_kernel_with_chat_completion("sample")
    kernel_process = process.build()
    print(f"=== Start SK Process '{process.name}' ===")
    _ = await start(
        process=kernel_process, kernel=kernel, initial_event=KernelProcessEvent(id=external_trigger_event, data=[])
    )
    print(f"=== End SK Process '{process.name}' ===")


async def execute_process_with_state(process, kernel, external_trigger_event, order_label) -> KernelProcess:
    print(f"=== {order_label} ===")
    async with await start(process, kernel, KernelProcessEvent(id=external_trigger_event, data=[])) as running_process:
        return await running_process.get_state()


# endregion

# region Stateless Processes


async def use_prepare_fried_fish_process():
    process = FriedFishProcess.create_process()
    await use_prepare_specific_product(process, FriedFishProcess.ProcessEvents.PrepareFriedFish)


async def use_prepare_potato_fries_process():
    process = PotatoFriesProcess.create_process()
    await use_prepare_specific_product(process, PotatoFriesProcess.ProcessEvents.PreparePotatoFries)


async def use_prepare_fish_sandwich_process():
    process = FishSandwichProcess.create_process()
    await use_prepare_specific_product(process, FishSandwichProcess.ProcessEvents.PrepareFishSandwich)


async def use_prepare_fish_and_chips_process():
    process = FishAndChipsProcess.create_process()
    await use_prepare_specific_product(process, FishAndChipsProcess.ProcessEvents.PrepareFishAndChips)


# endregion

# region Stateful Processes


async def use_prepare_stateful_fried_fish_process_no_shared_state():
    process_builder = FriedFishProcess.create_process_with_stateful_steps()
    external_trigger_event = FriedFishProcess.ProcessEvents.PrepareFriedFish

    kernel = _create_kernel_with_chat_completion("sample")

    print(f"=== Start SK Process '{process_builder.name}' ===")
    await execute_process_with_state(process_builder.build(), kernel, external_trigger_event, "Order 1")
    await execute_process_with_state(process_builder.build(), kernel, external_trigger_event, "Order 2")
    print(f"=== End SK Process '{process_builder.name}' ===")


async def use_prepare_stateful_fried_fish_process_shared_state():
    process_builder = FriedFishProcess.create_process_with_stateful_steps()
    external_trigger_event = FriedFishProcess.ProcessEvents.PrepareFriedFish

    kernel = _create_kernel_with_chat_completion("sample")

    print(f"=== Start SK Process '{process_builder.name}' ===")
    await execute_process_with_state(process_builder.build(), kernel, external_trigger_event, "Order 1")
    await execute_process_with_state(process_builder.build(), kernel, external_trigger_event, "Order 2")
    await execute_process_with_state(process_builder.build(), kernel, external_trigger_event, "Order 3")
    print(f"=== End SK Process '{process_builder.name}' ===")


async def use_prepare_stateful_potato_fries_process_shared_state():
    process_builder = PotatoFriesProcess.create_process_with_stateful_steps()
    external_trigger_event = PotatoFriesProcess.ProcessEvents.PreparePotatoFries

    kernel = _create_kernel_with_chat_completion("sample")

    print(f"=== Start SK Process '{process_builder.name}' ===")
    await execute_process_with_state(process_builder.build(), kernel, external_trigger_event, "Order 1")
    await execute_process_with_state(process_builder.build(), kernel, external_trigger_event, "Order 2")
    await execute_process_with_state(process_builder.build(), kernel, external_trigger_event, "Order 3")
    print(f"=== End SK Process '{process_builder.name}' ===")


# endregion


if __name__ == "__main__":
    asyncio.run(use_prepare_fried_fish_process())
    asyncio.run(use_prepare_potato_fries_process())
    asyncio.run(use_prepare_fish_sandwich_process())
    asyncio.run(use_prepare_fish_and_chips_process())
    asyncio.run(use_prepare_stateful_fried_fish_process_no_shared_state())
    asyncio.run(use_prepare_stateful_fried_fish_process_shared_state())
    asyncio.run(use_prepare_stateful_potato_fries_process_shared_state())
