import asyncio
import logging
from typing import Any

from semantic_kernel.skill_definition.parameter_view import ParameterView as Parameter

from .sk_function_new import SKFunctionNew

_LOGGER = logging.getLogger(__name__)


class NativeFunction(SKFunctionNew):
    function: Any

    def __init__(self, function):
        input_variables = []
        output_variables = []
        for parameter in function.__sk_function_context_parameters__:
            if parameter["direction"] == "input":
                input_variables.append(
                    Parameter(
                        name=parameter["name"],
                        description=parameter["description"],
                        default_value=parameter["default_value"],
                        type=parameter["type"],
                        required=parameter["required"],
                    )
                )
                continue
            output_variables.append(
                Parameter(
                    name=parameter["name"],
                    description=parameter["description"],
                    default_value=parameter["default_value"],
                    type=parameter["type"],
                    required=parameter["required"],
                )
            )
        if len(output_variables) == 0:
            output_variables.append(
                Parameter(
                    name="result",
                    description="result of the function",
                    default_value="",
                    type="string",
                    required=True,
                )
            )
        super().__init__(
            name=function.__sk_function_name__,
            description=function.__sk_function_description__,
            input_variables=input_variables,
            output_variables=output_variables,
        )
        self.function = function

    async def run_async(self, *args, **kwargs) -> dict:
        if asyncio.iscoroutinefunction(self.function):
            return await self.function(*args, **kwargs)
        return self.function(*args, **kwargs)
