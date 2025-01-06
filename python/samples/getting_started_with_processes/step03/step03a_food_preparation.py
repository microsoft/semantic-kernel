# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
from pathlib import Path

from samples.getting_started_with_processes.step03.processes.fish_and_chips_process import FishAndChipsProcess
from samples.getting_started_with_processes.step03.processes.fish_sandwich_process import FishSandwichProcess
from samples.getting_started_with_processes.step03.processes.fried_fish_process import FriedFishProcess
from samples.getting_started_with_processes.step03.processes.potato_fries_process import PotatoFriesProcess
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.kernel_process.kernel_process_state_metadata import KernelProcessStateMetadata
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder

################################################################################################
# Demonstrate creation of KernelProcess and eliciting different food-related events,           #
# with additional load/save steps for state management, replicating the same approach used in  #
# the C# samples.                                                                              #
################################################################################################

# region Helper Methods


def _create_kernel_with_chat_completion(service_id: str = "sample") -> Kernel:
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id=service_id), overwrite=True)
    return kernel


async def use_prepare_specific_product(process: ProcessBuilder, external_trigger_event: str):
    """
    Helper function that builds a KernelProcess from a ProcessBuilder,
    starts it, and waits until completion.
    """
    kernel = _create_kernel_with_chat_completion("sample")

    kernel_process = process.build()
    print(f"=== Start SK Process '{process.name}' ===")
    async with await start(
        kernel_process,
        kernel,
        KernelProcessEvent(id=external_trigger_event, data=[]),
    ):
        pass
    print(f"=== End SK Process '{process.name}' ===\n")


async def execute_process_with_state(
    process: KernelProcess, kernel: Kernel, external_trigger_event: str, order_label: str
):
    """
    Starts the provided KernelProcess (with optional existing state),
    returns the updated state after the run.
    """
    print(f"=== {order_label} ===")
    async with await start(
        process,
        kernel,
        KernelProcessEvent(id=external_trigger_event, data=[]),
    ) as running_process:
        return await running_process.get_state()


# endregion

# region Local JSON file handling for process state


def dump_process_state_metadata_locally(process_state: KernelProcessStateMetadata, json_filename: str):
    """
    Saves the ProcessStateMetadata to a local JSON file.
    """
    # In your actual environment, set the path as desired:
    directory = Path("processesstates")  # or wherever you want to store these
    directory.mkdir(exist_ok=True)
    file_path = directory / json_filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(process_state.dict(), f, indent=4)
    print(f"Process state saved to '{file_path.resolve()}'")


def load_process_state_metadata(json_filename: str) -> KernelProcessStateMetadata | None:
    """
    Loads the ProcessStateMetadata from a local JSON file, if found.
    Returns None if the file doesn't exist or can't be parsed.
    """
    directory = Path("processesstates")
    file_path = directory / json_filename
    if not file_path.exists():
        print(f"Could not find '{file_path.resolve()}'")
        return None

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    try:
        # Recreate a ProcessStateMetadata instance from the JSON
        return KernelProcessStateMetadata(**data)
    except Exception as e:
        print(f"Error parsing state file '{file_path}': {e}")
        return None


# endregion

# region Stateless Processes


async def use_prepare_fried_fish_process():
    process = FriedFishProcess.create_process()
    await use_prepare_specific_product(process, FriedFishProcess.ProcessEvents.PrepareFriedFish.value)


async def use_prepare_potato_fries_process():
    process = PotatoFriesProcess.create_process()
    await use_prepare_specific_product(process, PotatoFriesProcess.ProcessEvents.PreparePotatoFries.value)


async def use_prepare_fish_sandwich_process():
    process = FishSandwichProcess.create_process()
    await use_prepare_specific_product(process, FishSandwichProcess.ProcessEvents.PrepareFishSandwich.value)


async def use_prepare_fish_and_chips_process():
    process = FishAndChipsProcess.create_process()
    await use_prepare_specific_product(process, FishAndChipsProcess.ProcessEvents.PrepareFishAndChips.value)


# endregion

# region Stateful Processes


async def use_prepare_stateful_fried_fish_process_no_shared_state():
    """
    Showcases building the stateful process multiple times.
    Each new build has fresh/independent state.
    """
    builder = FriedFishProcess.create_process_with_stateful_steps()
    event_name = FriedFishProcess.ProcessEvents.PrepareFriedFish.value
    kernel = _create_kernel_with_chat_completion()

    print(f"=== Start SK Process '{builder.name}' ===")
    # Each build() -> new instance
    await execute_process_with_state(builder.build(), kernel, event_name, "Order 1")
    await execute_process_with_state(builder.build(), kernel, event_name, "Order 2")
    print(f"=== End SK Process '{builder.name}' ===\n")


async def use_prepare_stateful_fried_fish_process_shared_state():
    """
    Showcases building the stateful process once and reusing it,
    meaning runs 2 & 3 continue from the prior step's state.
    """
    builder = FriedFishProcess.create_process_with_stateful_steps()
    kernel = _create_kernel_with_chat_completion()
    event_name = FriedFishProcess.ProcessEvents.PrepareFriedFish.value

    single_process = builder.build()  # one instance => shared state
    print(f"=== Start SK Process '{builder.name}' ===")
    await execute_process_with_state(single_process, kernel, event_name, "Order 1")
    await execute_process_with_state(single_process, kernel, event_name, "Order 2")
    await execute_process_with_state(single_process, kernel, event_name, "Order 3")
    print(f"=== End SK Process '{builder.name}' ===\n")


async def use_prepare_stateful_potato_fries_process_shared_state():
    builder = PotatoFriesProcess.create_process_with_stateful_steps()
    kernel = _create_kernel_with_chat_completion()
    event_name = PotatoFriesProcess.ProcessEvents.PreparePotatoFries.value

    shared_process = builder.build()
    print(f"=== Start SK Process '{builder.name}' ===")
    await execute_process_with_state(shared_process, kernel, event_name, "Order 1")
    await execute_process_with_state(shared_process, kernel, event_name, "Order 2")
    await execute_process_with_state(shared_process, kernel, event_name, "Order 3")
    print(f"=== End SK Process '{builder.name}' ===\n")


# endregion

# region Loading / Storing state from local files

STATEFUL_FRIED_FISH_PROCESS_FILENAME = "FriedFishProcessStateSuccess.json"
STATEFUL_FRIED_FISH_LOWSTOCK_FILENAME = "FriedFishProcessStateSuccessLowStock.json"
STATEFUL_FRIED_FISH_NOSTOCK_FILENAME = "FriedFishProcessStateSuccessNoStock.json"
STATEFUL_FISH_SANDWICH_PROCESS_FILENAME = "FishSandwichStateProcessSuccess.json"
STATEFUL_FISH_SANDWICH_LOWSTOCK_FILENAME = "FishSandwichStateProcessSuccessLowStock.json"


async def run_and_store_stateful_fried_fish_process_state():
    """
    Runs the FriedFish stateful process once, then stores its state to JSON.
    """
    kernel = _create_kernel_with_chat_completion()
    builder = FriedFishProcess.create_process_with_stateful_steps()
    fried_fish_process = builder.build()

    print("=== Start run_and_store_stateful_fried_fish_process_state ===")
    final_state = await execute_process_with_state(
        fried_fish_process, kernel, FriedFishProcess.ProcessEvents.PrepareFriedFish.value, "Order 1"
    )
    # Convert final state to metadata for saving
    process_state_metadata = final_state.to_process_state_metadata()
    dump_process_state_metadata_locally(process_state_metadata, STATEFUL_FRIED_FISH_PROCESS_FILENAME)
    print("=== End run_and_store_stateful_fried_fish_process_state ===\n")


async def run_and_store_stateful_fish_sandwich_process_state():
    """
    Runs the FishSandwich stateful process once, then stores its state to JSON.
    """
    kernel = _create_kernel_with_chat_completion()
    builder = FishSandwichProcess.create_process()  # Or a stateful method if you have it
    # For demonstration, let's assume we want to store a regular FishSandwichProcess state
    # If you have a "create_process_with_stateful_steps" for FishSandwich, use that instead.
    fish_sandwich_process = builder.build()

    print("=== Start run_and_store_stateful_fish_sandwich_process_state ===")
    final_state = await execute_process_with_state(
        fish_sandwich_process, kernel, FishSandwichProcess.ProcessEvents.PrepareFishSandwich.value, "Order 1"
    )
    process_state_metadata = final_state.to_process_state_metadata()
    dump_process_state_metadata_locally(process_state_metadata, STATEFUL_FISH_SANDWICH_PROCESS_FILENAME)
    print("=== End run_and_store_stateful_fish_sandwich_process_state ===\n")


async def run_stateful_fried_fish_process_from_file():
    """
    Loads an existing JSON state file, rebuilds the process with that state,
    then triggers the external event again.
    """
    loaded_metadata = load_process_state_metadata(STATEFUL_FRIED_FISH_PROCESS_FILENAME)
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FriedFishProcess.create_process_with_stateful_steps()
    # Build the process with the loaded metadata
    process_from_file = builder.build(process_state_metadata=loaded_metadata)

    print("=== Start run_stateful_fried_fish_process_from_file ===")
    await execute_process_with_state(
        process_from_file, kernel, FriedFishProcess.ProcessEvents.PrepareFriedFish.value, "Using Stored State"
    )
    print("=== End run_stateful_fried_fish_process_from_file ===\n")


async def run_stateful_fried_fish_process_with_low_stock_from_file():
    loaded_metadata = load_process_state_metadata(STATEFUL_FRIED_FISH_LOWSTOCK_FILENAME)
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FriedFishProcess.create_process_with_stateful_steps()
    process_from_file = builder.build(process_state_metadata=loaded_metadata)

    print("=== Start run_stateful_fried_fish_process_with_low_stock_from_file ===")
    await execute_process_with_state(
        process_from_file, kernel, FriedFishProcess.ProcessEvents.PrepareFriedFish.value, "Using Low Stock State"
    )
    print("=== End run_stateful_fried_fish_process_with_low_stock_from_file ===\n")


async def run_stateful_fried_fish_process_with_no_stock_from_file():
    loaded_metadata = load_process_state_metadata(STATEFUL_FRIED_FISH_NOSTOCK_FILENAME)
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FriedFishProcess.create_process_with_stateful_steps()
    process_from_file = builder.build(process_state_metadata=loaded_metadata)

    print("=== Start run_stateful_fried_fish_process_with_no_stock_from_file ===")
    await execute_process_with_state(
        process_from_file, kernel, FriedFishProcess.ProcessEvents.PrepareFriedFish.value, "Using No Stock State"
    )
    print("=== End run_stateful_fried_fish_process_with_no_stock_from_file ===\n")


async def run_stateful_fish_sandwich_process_from_file():
    loaded_metadata = load_process_state_metadata(STATEFUL_FISH_SANDWICH_PROCESS_FILENAME)
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FishSandwichProcess.create_process()
    process_from_file = builder.build(process_state_metadata=loaded_metadata)

    print("=== Start run_stateful_fish_sandwich_process_from_file ===")
    await execute_process_with_state(
        process_from_file, kernel, FishSandwichProcess.ProcessEvents.PrepareFishSandwich.value, "Using Stored State"
    )
    print("=== End run_stateful_fish_sandwich_process_from_file ===\n")


async def run_stateful_fish_sandwich_process_with_low_stock_from_file():
    loaded_metadata = load_process_state_metadata(STATEFUL_FISH_SANDWICH_LOWSTOCK_FILENAME)
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FishSandwichProcess.create_process()
    process_from_file = builder.build(process_state_metadata=loaded_metadata)

    print("=== Start run_stateful_fish_sandwich_process_with_low_stock_from_file ===")
    await execute_process_with_state(
        process_from_file, kernel, FishSandwichProcess.ProcessEvents.PrepareFishSandwich.value, "Using Low Stock State"
    )
    print("=== End run_stateful_fish_sandwich_process_with_low_stock_from_file ===\n")


# You can also demonstrate versioning compatibility by using the same V2 approach the C# code has,
# but below is an example if you define a V2 process in Python:
#
# async def run_stateful_fried_fish_v2_process_with_low_stock_v1_state_from_file():
#     loaded_metadata = load_process_state_metadata(STATEFUL_FRIED_FISH_LOWSTOCK_FILENAME)
#     if not loaded_metadata:
#         return
#
#     kernel = _create_kernel_with_chat_completion()
#     builder = FriedFishProcess.create_process_with_stateful_steps_v2()  # hypothetically if you had a v2
#     process_from_file = builder.build(process_state_metadata=loaded_metadata)
#
#     print("=== Start run_stateful_fried_fish_v2_process_with_low_stock_v1_state_from_file ===")
#     await execute_process_with_state(
#         process_from_file,
#         kernel,
#         FriedFishProcess.ProcessEvents.PrepareFriedFish.value,
#         "Using Low Stock V1 State"
#     )
#     print("=== End run_stateful_fried_fish_v2_process_with_low_stock_v1_state_from_file ===\n")

# endregion


async def main():
    # Show basic usage of "stateless" processes
    await use_prepare_fried_fish_process()
    await use_prepare_potato_fries_process()
    await use_prepare_fish_sandwich_process()
    await use_prepare_fish_and_chips_process()

    # Show "stateful" processes, not storing or loading yet
    await use_prepare_stateful_fried_fish_process_no_shared_state()
    await use_prepare_stateful_fried_fish_process_shared_state()
    await use_prepare_stateful_potato_fries_process_shared_state()

    # Demonstration of storing then reloading state:
    await run_and_store_stateful_fried_fish_process_state()
    await run_and_store_stateful_fish_sandwich_process_state()

    await run_stateful_fried_fish_process_from_file()
    await run_stateful_fried_fish_process_with_low_stock_from_file()
    await run_stateful_fried_fish_process_with_no_stock_from_file()
    await run_stateful_fish_sandwich_process_from_file()
    await run_stateful_fish_sandwich_process_with_low_stock_from_file()

    # If you define a "create_process_with_stateful_steps_v2()" in your Python code,
    # you can similarly show how to load V1 states into V2 processes here.


if __name__ == "__main__":
    asyncio.run(main())
