from unittest.mock import patch

import pytest

from semantic_kernel.core_plugins.wait_plugin import WaitPlugin
from semantic_kernel.exceptions import FunctionExecutionException

test_data_good = [
    0,
    1.0,
    -2,
    "0",
    "1",
    "2.1",
    "0.1",
    "0.01",
    "0.001",
    "0.0001",
    "-0.0001",
]

test_data_bad = [
    "$0",
    "one hundred",
    "20..,,2,1",
    ".2,2.1",
    "0.1.0",
    "00-099",
    "¹²¹",
    "2²",
    "zero",
    "-100 seconds",
    "1 second",
]


def test_can_be_instantiated():
    plugin = WaitPlugin()
    assert plugin is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("wait_time", test_data_good)
async def test_wait_valid_params(wait_time):
    plugin = WaitPlugin()
    with patch("asyncio.sleep") as patched_sleep:
        await plugin.wait(wait_time)

        assert patched_sleep.called_once_with(abs(float(wait_time)))


@pytest.mark.asyncio
@pytest.mark.parametrize("wait_time", test_data_bad)
async def test_wait_invalid_params(wait_time):
    plugin = WaitPlugin()

    with pytest.raises(FunctionExecutionException) as exc_info:
        await plugin.wait("wait_time")

    assert exc_info.value.args[0] == "seconds text must be a number"
