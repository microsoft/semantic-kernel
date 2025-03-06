# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

import pytest

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel


class WeatherPlugin:
    """Mock weather plugin."""

    @kernel_function(description="Get real-time weather information.")
    def current(self, location: Annotated[str, "The location to get the weather"]) -> str:
        """Returns the current weather."""
        return f"The weather in {location} is sunny."


@pytest.fixture
def kernel_with_dummy_function() -> Kernel:
    kernel = Kernel()
    kernel.add_plugin(WeatherPlugin(), plugin_name="weather")

    return kernel
