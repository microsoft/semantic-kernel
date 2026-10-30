# Copyright (c) Microsoft. All rights reserved.

import importlib.util
from pathlib import Path

import pytest

from semantic_kernel import Kernel
from semantic_kernel.filters import FilterTypes
from semantic_kernel.functions import kernel_function

SAMPLE_PATH = (
    Path(__file__).parents[3] / "samples" / "concepts" / "filtering" / "command_guard_filter.py"
)  # python/samples/concepts/filtering/command_guard_filter.py


@pytest.fixture(scope="module")
def sample():
    spec = importlib.util.spec_from_file_location("command_guard_filter_sample", SAMPLE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordingShellPlugin:
    def __init__(self) -> None:
        self.commands: list[str] = []

    @kernel_function(name="run")
    def run(self, command: str) -> str:
        self.commands.append(command)
        return f"ran: {command}"

    @kernel_function(name="other")
    def other(self, text: str) -> str:
        return text


def _kernel_with_guard(sample, scanner, **filter_kwargs) -> tuple[Kernel, RecordingShellPlugin]:
    kernel = Kernel()
    plugin = RecordingShellPlugin()
    kernel.add_plugin(plugin, plugin_name="shell")
    kernel.add_filter(FilterTypes.FUNCTION_INVOCATION, sample.create_command_guard_filter(scanner, **filter_kwargs))
    return kernel, plugin


async def test_allowed_command_runs(sample):
    kernel, plugin = _kernel_with_guard(sample, sample.DenyListScanner(["rm -rf /"]))

    result = await kernel.invoke(plugin_name="shell", function_name="run", command="ls -la")

    assert str(result) == "ran: ls -la"
    assert plugin.commands == ["ls -la"]


async def test_blocked_command_does_not_run(sample):
    kernel, plugin = _kernel_with_guard(sample, sample.DenyListScanner(["rm -rf /"]))

    result = await kernel.invoke(plugin_name="shell", function_name="run", command="rm -rf /")

    assert "Blocked by command guard" in str(result)
    assert "rm -rf /" in str(result)  # the reason from the scanner is passed on
    assert plugin.commands == []


async def test_async_scanner_is_supported(sample):
    class AsyncScanner:
        async def scan(self, command: str):
            return sample.ScanVerdict(allowed=False, reason="async says no")

    kernel, plugin = _kernel_with_guard(sample, AsyncScanner())

    result = await kernel.invoke(plugin_name="shell", function_name="run", command="anything")

    assert "async says no" in str(result)
    assert plugin.commands == []


async def test_function_without_the_command_argument_is_not_checked(sample):
    kernel, _ = _kernel_with_guard(sample, sample.DenyListScanner(["hello"]))

    result = await kernel.invoke(plugin_name="shell", function_name="other", text="hello")

    assert str(result) == "hello"


async def test_custom_argument_names(sample):
    kernel, _ = _kernel_with_guard(sample, sample.DenyListScanner(["hello"]), argument_names=("text",))

    result = await kernel.invoke(plugin_name="shell", function_name="other", text="hello")

    assert "Blocked by command guard" in str(result)
