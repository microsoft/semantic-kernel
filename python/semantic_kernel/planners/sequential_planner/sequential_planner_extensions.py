# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import List, Optional

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.planners.sequential_planner.sequential_planner_config import SequentialPlannerConfig

logger: logging.Logger = logging.getLogger(__name__)


class SequentialPlannerFunctionExtension:
    @staticmethod
    def to_manual_string(function: KernelFunctionMetadata):
        inputs = [
            f"  - {parameter.name}: {parameter.description}"
            + (f" (default value: {parameter.default_value})" if parameter.default_value else "")
            for parameter in function.parameters
        ]
        inputs = "\n".join(inputs)
        return f"{function.fully_qualified_name}:\n  description: {function.description}\n  inputs:\n " f" {inputs}"

    @staticmethod
    def to_embedding_string(function: KernelFunctionMetadata):
        inputs = "\n".join([f"    - {parameter.name}: {parameter.description}" for parameter in function.parameters])
        return f"{function.name}:\n  description: {function.description}\n " f" inputs:\n{inputs}"


class SequentialPlannerKernelExtension:
    PLANNER_MEMORY_COLLECTION_NAME = " Planning.KernelFunctionManual"
    PLAN_KERNEL_FUNCTIONS_ARE_REMEMBERED = "Planning.KernelFunctionsAreRemembered"

    @staticmethod
    async def get_functions_manual(
        kernel: "Kernel",
        arguments: KernelArguments,
        semantic_query: str = None,
        config: SequentialPlannerConfig = None,
    ) -> str:
        config = config or SequentialPlannerConfig()

        if config.get_available_functions is None:
            functions = await SequentialPlannerKernelExtension.get_available_functions(
                kernel, arguments, config, semantic_query
            )
        else:
            functions = await config.get_available_functions(config, semantic_query)

        return "\n\n".join([SequentialPlannerFunctionExtension.to_manual_string(func) for func in functions])

    @staticmethod
    async def get_available_functions(
        kernel: Kernel,
        arguments: KernelArguments,
        config: SequentialPlannerConfig,
        semantic_query: Optional[str] = None,
    ):
        excluded_plugins = config.excluded_plugins or []
        excluded_functions = config.excluded_functions or []
        included_functions = config.included_functions or []

        available_functions = [
            func
            for func in kernel.plugins.get_list_of_function_metadata()
            if (func.plugin_name not in excluded_plugins and func.name not in excluded_functions)
        ]

        if semantic_query is None or config.relevancy_threshold is None:
            # If no semantic query is provided, return all available functions.
            # If a Memory provider has not been registered, return all available functions.
            return available_functions

        # Add functions that were found in the search results.
        relevant_functions = await SequentialPlannerKernelExtension.get_relevant_functions(
            kernel,
            available_functions,
        )

        # Add any missing functions that were included but not found in the search results.
        missing_functions = [
            func for func in included_functions if func not in [func.name for func in relevant_functions]
        ]

        relevant_functions += [func for func in available_functions if func.name in missing_functions]

        return sorted(relevant_functions, key=lambda x: (x.plugin_name, x.name))

    @staticmethod
    async def get_relevant_functions(
        kernel: Kernel,
        available_functions: List[KernelFunctionMetadata],
        memories: Optional[List[MemoryQueryResult]] = None,
    ) -> List[KernelFunctionMetadata]:
        relevant_functions = []
        # TODO: cancellation
        if memories is None:
            return relevant_functions
        for memory_entry in memories:
            function = next(
                (func for func in available_functions if func.fully_qualified_name == memory_entry.id),
                None,
            )
            if function is not None:
                logger.debug(
                    "Found relevant function. Relevance Score: {0}, Function: {1}".format(
                        memory_entry.relevance,
                        function.fully_qualified_name,
                    )
                )
                relevant_functions.append(function)

        return relevant_functions
