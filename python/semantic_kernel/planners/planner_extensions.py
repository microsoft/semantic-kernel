# Copyright (c) Microsoft. All rights reserved.

import logging

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.planner_options import PlannerOptions

logger: logging.Logger = logging.getLogger(__name__)

# NOTE these extensions will be used going forward by the FunctionCallingStepWisePlanner and others.
# The other sequential planner extensions will be left in right now for as long as we support that planner
# and will be removed once we deprecate it.


class PlannerFunctionExtension:
    """Function extension for the planner."""

    @staticmethod
    def to_manual_string(function: KernelFunctionMetadata):
        """Convert the function to a string that can be used in the manual."""
        inputs = [
            f"  - {parameter.name}: {parameter.description}"
            + (f" (default value: {parameter.default_value})" if parameter.default_value else "")
            for parameter in function.parameters
        ]
        inputs = "\n".join(inputs)
        return f"{function.fully_qualified_name}:\n  description: {function.description}\n  inputs:\n  {inputs}"

    @staticmethod
    def to_embedding_string(function: KernelFunctionMetadata):
        """Convert the function to a string that can be used as an embedding."""
        inputs = "\n".join([f"    - {parameter.name}: {parameter.description}" for parameter in function.parameters])
        return f"{function.name}:\n  description: {function.description}\n  inputs:\n{inputs}"


class PlannerKernelExtension:
    """Kernel extension for the planner."""

    PLANNER_MEMORY_COLLECTION_NAME = " Planning.KernelFunctionManual"
    PLAN_KERNEL_FUNCTIONS_ARE_REMEMBERED = "Planning.KernelFunctionsAreRemembered"

    @staticmethod
    async def get_functions_manual(
        kernel: "Kernel",
        arguments: KernelArguments,
        options: PlannerOptions = None,
    ) -> str:
        """Get the string of the function."""
        options = options or PlannerOptions()

        if options.get_available_functions is None:
            functions = await PlannerKernelExtension.get_available_functions(kernel, arguments, options)
        else:
            functions = await options.get_available_functions(options)

        return "\n\n".join([PlannerFunctionExtension.to_manual_string(func) for func in functions])

    @staticmethod
    async def get_available_functions(
        kernel: Kernel,
        arguments: KernelArguments,
        options: PlannerOptions,
    ):
        """Get the available functions for the kernel."""
        excluded_plugins = options.excluded_plugins or []
        excluded_functions = options.excluded_functions or []

        return [
            func
            for func in kernel.get_list_of_function_metadata()
            if (func.plugin_name not in excluded_plugins and func.name not in excluded_functions)
        ]
