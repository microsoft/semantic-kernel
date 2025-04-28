# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
from enum import Enum
from pathlib import Path

from samples.getting_started_with_processes.step03.processes.fish_and_chips_process import FishAndChipsProcess
from samples.getting_started_with_processes.step03.processes.fish_sandwich_process import FishSandwichProcess
from samples.getting_started_with_processes.step03.processes.fried_fish_process import FriedFishProcess
from samples.getting_started_with_processes.step03.processes.potato_fries_process import PotatoFriesProcess
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.kernel_process import KernelProcess, KernelProcessEvent, KernelProcessStateMetadata
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder

"""
Demonstrate the creation of KernelProcess and eliciting different food related events.
This includes load/save steps for state management.
For visual reference of the processes used here check the diagram in:
https://github.com/microsoft/semantic-kernel/tree/main/python/samples/
getting_started_with_processes#step03b_food_ordering
"""

# region Helper Methods


def _create_kernel_with_chat_completion(service_id: str = "sample") -> Kernel:
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id=service_id), overwrite=True)
    return kernel


async def use_prepare_specific_product(process: ProcessBuilder, external_trigger_event: Enum):
    """
    Helper function that:
     1. Builds a KernelProcess from a ProcessBuilder
     2. Starts it with the given external event
     3. Waits for completion
    """
    kernel = _create_kernel_with_chat_completion("sample")

    kernel_process = process.build()
    print(f"=== Start SK Process '{process.name}' ===")
    async with await start(
        kernel_process,
        kernel,
        KernelProcessEvent(id=external_trigger_event.value, data=[]),
    ):
        pass
    print(f"=== End SK Process '{process.name}' ===\n")


async def execute_process_with_state(
    process: KernelProcess, kernel: Kernel, external_trigger_event: Enum, order_label: str
) -> KernelProcess:
    """
    Starts the provided KernelProcess (with optional existing state),
    returns the updated state after the run.
    """
    print(f"=== {order_label} ===")
    async with await start(
        process,
        kernel,
        KernelProcessEvent(id=external_trigger_event.value, data=[]),
    ) as running_process:
        return await running_process.get_state()


# endregion


# region Local JSON file handling for process state
BASE_DIR = Path(__file__).resolve().parent.parent

# Build the path to "step03/processes_states"
PROCESS_STATE_DIRECTORY = BASE_DIR / "step03" / "processes_states"
PROCESS_STATE_DIRECTORY.mkdir(parents=True, exist_ok=True)


def dump_process_state_metadata_locally(process_state: KernelProcessStateMetadata, json_filename: str) -> None:
    """
    Saves the ProcessStateMetadata to a local JSON file in step03/processes_states,
    relative to the current script's grandparent folder.
    """
    file_path = PROCESS_STATE_DIRECTORY / json_filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(process_state.model_dump(exclude_none=True, by_alias=True, mode="json"), f, indent=4)
    print(f"Process state saved to '{file_path.resolve()}'")


def load_process_state_metadata(json_filename: str) -> KernelProcessStateMetadata | None:
    """
    Loads the ProcessStateMetadata from step03/processes_states if it exists.
    Returns None if the file doesn't exist or fails to parse.
    """
    file_path = PROCESS_STATE_DIRECTORY / json_filename
    if not file_path.exists():
        print(f"No such file: '{file_path.resolve()}'")
        return None

    try:
        with open(file_path, encoding="utf-8") as f:
            return KernelProcessStateMetadata.model_validate_json(f)
    except Exception as ex:
        print(f"Error reading state file '{file_path.resolve()}': {ex}")
        return None


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
    """
    Showcases building the stateful process multiple times.
    Each new build has fresh/independent state.
    """
    builder = FriedFishProcess.create_process_with_stateful_steps_v1()
    event_name = FriedFishProcess.ProcessEvents.PrepareFriedFish
    kernel = _create_kernel_with_chat_completion()

    print(f"=== Start SK Process '{builder.name}' ===")
    # Each build() -> new instance
    await execute_process_with_state(builder.build(), kernel, event_name, "Order 1")
    await execute_process_with_state(builder.build(), kernel, event_name, "Order 2")
    print(f"=== End SK Process '{builder.name}' ===\n")


async def use_prepare_stateful_fried_fish_process_shared_state():
    """
    Showcases building the stateful process once and reusing it,
    meaning runs #2 and #3 continue from the prior run's state.
    """
    builder = FriedFishProcess.create_process_with_stateful_steps_v2()
    kernel = _create_kernel_with_chat_completion()
    event_name = FriedFishProcess.ProcessEvents.PrepareFriedFish

    single_process = builder.build()  # one instance => shared state
    print(f"=== Start SK Process '{builder.name}' ===")
    await execute_process_with_state(single_process, kernel, event_name, "Order 1")
    await execute_process_with_state(single_process, kernel, event_name, "Order 2")
    await execute_process_with_state(single_process, kernel, event_name, "Order 3")
    print(f"=== End SK Process '{builder.name}' ===\n")


async def use_prepare_stateful_potato_fries_process_shared_state():
    builder = PotatoFriesProcess.create_process_with_stateful_steps()
    kernel = _create_kernel_with_chat_completion()
    event_name = PotatoFriesProcess.ProcessEvents.PreparePotatoFries

    shared_process = builder.build()
    print(f"=== Start SK Process '{builder.name}' ===")
    await execute_process_with_state(shared_process, kernel, event_name, "Order 1")
    await execute_process_with_state(shared_process, kernel, event_name, "Order 2")
    await execute_process_with_state(shared_process, kernel, event_name, "Order 3")
    print(f"=== End SK Process '{builder.name}' ===\n")


# endregion


# region Filenames for sample states

STATEFUL_FRIED_FISH_PROCESS_FILENAME = "FriedFishProcessStateSuccess.json"
STATEFUL_FRIED_FISH_LOWSTOCK_FILENAME = "FriedFishProcessStateSuccessLowStock.json"
STATEFUL_FRIED_FISH_NOSTOCK_FILENAME = "FriedFishProcessStateSuccessNoStock.json"
STATEFUL_FISH_SANDWICH_PROCESS_FILENAME = "FishSandwichStateProcessSuccess.json"
STATEFUL_FISH_SANDWICH_LOWSTOCK_FILENAME = "FishSandwichStateProcessSuccessLowStock.json"

# endregion


# region Reading/Writing process state from/to file


async def run_and_store_stateful_fried_fish_process_state():
    """
    Runs the FriedFish stateful process once, then stores its state to JSON.
    """
    kernel = _create_kernel_with_chat_completion()
    builder = FriedFishProcess.create_process_with_stateful_steps_v1()
    fried_fish_process = builder.build()

    print("=== Start run_and_store_stateful_fried_fish_process_state ===")
    final_state = await execute_process_with_state(
        fried_fish_process, kernel, FriedFishProcess.ProcessEvents.PrepareFriedFish, "Order 1"
    )
    process_state_metadata = final_state.to_process_state_metadata()
    dump_process_state_metadata_locally(process_state_metadata, STATEFUL_FRIED_FISH_PROCESS_FILENAME)
    print("=== End run_and_store_stateful_fried_fish_process_state ===\n")


async def run_and_store_stateful_fish_sandwich_process_state():
    """
    Runs the FishSandwich stateful process once, then stores its state to JSON.
    """
    kernel = _create_kernel_with_chat_completion()
    builder = FishSandwichProcess.create_process_with_stateful_steps_v1()
    fish_sandwich_process = builder.build()

    print("=== Start run_and_store_stateful_fish_sandwich_process_state ===")
    final_state = await execute_process_with_state(
        fish_sandwich_process, kernel, FishSandwichProcess.ProcessEvents.PrepareFishSandwich, "Order 1"
    )
    process_state_metadata = final_state.to_process_state_metadata()
    dump_process_state_metadata_locally(process_state_metadata, STATEFUL_FISH_SANDWICH_PROCESS_FILENAME)
    print("=== End run_and_store_stateful_fish_sandwich_process_state ===\n")


async def run_stateful_fried_fish_process_from_file():
    loaded_metadata = KernelProcessStateMetadata.load_from_file(
        json_filename=STATEFUL_FRIED_FISH_PROCESS_FILENAME, directory=PROCESS_STATE_DIRECTORY
    )
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FriedFishProcess.create_process_with_stateful_steps_v1()
    process_from_file = builder.build(state_metadata=loaded_metadata)

    print("=== Start run_stateful_fried_fish_process_from_file ===")
    await execute_process_with_state(
        process_from_file,
        kernel,
        FriedFishProcess.ProcessEvents.PrepareFriedFish,
        "Using Stored State",
    )
    print("=== End run_stateful_fried_fish_process_from_file ===\n")


async def run_stateful_fried_fish_process_with_low_stock_from_file():
    loaded_metadata = KernelProcessStateMetadata.load_from_file(
        json_filename=STATEFUL_FRIED_FISH_LOWSTOCK_FILENAME, directory=PROCESS_STATE_DIRECTORY
    )
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FriedFishProcess.create_process_with_stateful_steps_v1()
    process_from_file = builder.build(state_metadata=loaded_metadata)

    print("=== Start run_stateful_fried_fish_process_with_low_stock_from_file ===")
    await execute_process_with_state(
        process_from_file,
        kernel,
        FriedFishProcess.ProcessEvents.PrepareFriedFish,
        "Using Low Stock State",
    )
    print("=== End run_stateful_fried_fish_process_with_low_stock_from_file ===\n")


async def run_stateful_fried_fish_process_with_no_stock_from_file():
    loaded_metadata = KernelProcessStateMetadata.load_from_file(
        json_filename=STATEFUL_FRIED_FISH_NOSTOCK_FILENAME, directory=PROCESS_STATE_DIRECTORY
    )
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FriedFishProcess.create_process_with_stateful_steps_v1()
    process_from_file = builder.build(state_metadata=loaded_metadata)

    print("=== Start run_stateful_fried_fish_process_with_no_stock_from_file ===")
    await execute_process_with_state(
        process_from_file,
        kernel,
        FriedFishProcess.ProcessEvents.PrepareFriedFish,
        "Using No Stock State",
    )
    print("=== End run_stateful_fried_fish_process_with_no_stock_from_file ===\n")


async def run_stateful_fish_sandwich_process_from_file():
    loaded_metadata = KernelProcessStateMetadata.load_from_file(
        json_filename=STATEFUL_FISH_SANDWICH_PROCESS_FILENAME, directory=PROCESS_STATE_DIRECTORY
    )
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FishSandwichProcess.create_process()
    process_from_file = builder.build(state_metadata=loaded_metadata)

    print("=== Start run_stateful_fish_sandwich_process_from_file ===")
    await execute_process_with_state(
        process_from_file,
        kernel,
        FishSandwichProcess.ProcessEvents.PrepareFishSandwich,
        "Using Stored State",
    )
    print("=== End run_stateful_fish_sandwich_process_from_file ===\n")


async def run_stateful_fish_sandwich_process_with_low_stock_from_file():
    loaded_metadata = KernelProcessStateMetadata.load_from_file(
        json_filename=STATEFUL_FISH_SANDWICH_LOWSTOCK_FILENAME, directory=PROCESS_STATE_DIRECTORY
    )
    if not loaded_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    builder = FishSandwichProcess.create_process()
    process_from_file = builder.build(state_metadata=loaded_metadata)

    print("=== Start run_stateful_fish_sandwich_process_with_low_stock_from_file ===")
    await execute_process_with_state(
        process_from_file,
        kernel,
        FishSandwichProcess.ProcessEvents.PrepareFishSandwich,
        "Using Low Stock State",
    )
    print("=== End run_stateful_fish_sandwich_process_with_low_stock_from_file ===\n")


async def run_stateful_fried_fish_v2_with_low_stock_v1_state() -> None:
    state_metadata = KernelProcessStateMetadata.load_from_file(
        json_filename=STATEFUL_FRIED_FISH_LOWSTOCK_FILENAME, directory=PROCESS_STATE_DIRECTORY
    )
    if not state_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    process = FriedFishProcess.create_process_with_stateful_steps_v2().build(state_metadata=state_metadata)

    await execute_process_with_state(
        process,
        kernel,
        FriedFishProcess.ProcessEvents.PrepareFriedFish,
        "V2+low-stockV1state",
    )


async def run_stateful_fish_sandwich_v2_with_low_stock_v1_state() -> None:
    state_metadata = KernelProcessStateMetadata.load_from_file(
        json_filename=STATEFUL_FISH_SANDWICH_LOWSTOCK_FILENAME, directory=PROCESS_STATE_DIRECTORY
    )
    if not state_metadata:
        return

    kernel = _create_kernel_with_chat_completion()
    process = FishSandwichProcess.create_process_with_stateful_steps_v2().build(state_metadata=state_metadata)

    await execute_process_with_state(
        process,
        kernel,
        FishSandwichProcess.ProcessEvents.PrepareFishSandwich,
        "V2+low-stockV1state",
    )


# endregion


async def _make_low_and_no_stock_states() -> None:
    """Create the three 'low/no stock' JSON files expected by the sample."""
    # ------------------------------------------------------------------ #
    # 1.  Fried‑Fish  — base stateful process (V1)                       #
    # ------------------------------------------------------------------ #
    ff_builder = FriedFishProcess.create_process_with_stateful_steps_v1()
    ff_state_meta = ff_builder.build().to_process_state_metadata()

    gather_meta = ff_state_meta.steps_state["GatherFriedFishIngredientsWithStockStep"]
    gather_meta.state.ingredients_stock = 1
    dump_process_state_metadata_locally(ff_state_meta, STATEFUL_FRIED_FISH_LOWSTOCK_FILENAME)

    gather_meta.state.ingredients_stock = 0
    dump_process_state_metadata_locally(ff_state_meta, STATEFUL_FRIED_FISH_NOSTOCK_FILENAME)

    # ------------------------------------------------------------------ #
    # 2.  Fish‑Sandwich  — nested Fried‑Fish low‑stock                   #
    # ------------------------------------------------------------------ #
    fs_builder = FishSandwichProcess.create_process_with_stateful_steps_v1()
    fs_state_meta = fs_builder.build().to_process_state_metadata()

    nested_ff_meta = fs_state_meta.steps_state["FriedFishWithStatefulStepsProcess"].steps_state[
        "GatherFriedFishIngredientsWithStockStep"
    ]
    nested_ff_meta.state.ingredients_stock = 1

    dump_process_state_metadata_locally(fs_state_meta, STATEFUL_FISH_SANDWICH_LOWSTOCK_FILENAME)


async def main():
    # Uncomment the following line to create the low/no stock states
    # await _make_low_and_no_stock_states()

    # Show basic usage of "stateless" processes
    await use_prepare_fried_fish_process()
    await use_prepare_potato_fries_process()
    await use_prepare_fish_sandwich_process()
    await use_prepare_fish_and_chips_process()

    # # Show "stateful" processes, not storing or loading yet
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

    await run_stateful_fried_fish_v2_with_low_stock_v1_state()
    await run_stateful_fish_sandwich_v2_with_low_stock_v1_state()


if __name__ == "__main__":
    asyncio.run(main())
