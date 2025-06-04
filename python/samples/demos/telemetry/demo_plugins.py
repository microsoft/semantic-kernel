# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function

###############################
# Plugins for demo purposes ###
###############################


class WeatherPlugin:
    """A demo plugin for getting the weather forecast."""

    @kernel_function(name="get_weather", description="Get the weather forecast for a location")
    def get_weather(
        self,
        location: Annotated[str, "The location of interest"],
    ) -> Annotated[str, "The weather forecast"]:
        """Get the weather forecast for a location.

        Args:
            location (str): The location.
        """
        return f"The weather in {location} is 75°F and sunny."


class LocationPlugin:
    """A demo plugin for getting the location of a place."""

    @kernel_function(name="get_current_location", description="Get the current location of the user")
    def get_current_location(self) -> Annotated[str, "The current location"]:
        """Get the current location of the user."""
        return "Seattle"
