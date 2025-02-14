# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime
from random import randint

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function


@kernel_function
def get_weather(location: str) -> str:
    """Get the weather for a location."""
    weather_conditions = ("sunny", "hot", "cloudy", "raining", "freezing", "snowing")
    weather = weather_conditions[randint(0, len(weather_conditions) - 1)]  # nosec
    return f"The weather in {location} is {weather}."


@kernel_function
def get_date_time() -> str:
    """Get the current date and time."""
    return f"The current date and time is {datetime.now().isoformat()}."


@kernel_function
def goodbye():
    """When the user is done, say goodbye and then call this function."""
    raise KeyboardInterrupt


def create_kernel() -> Kernel:
    kernel = Kernel()
    kernel.add_functions(plugin_name="helpers", functions=[goodbye, get_weather, get_date_time])
    return kernel
