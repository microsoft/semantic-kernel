# Copyright (c) Microsoft. All rights reserved.

import itertools
from typing import AsyncIterable, List

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.planning.sequential_planner.sequential_planner_config import (
    SequentialPlannerConfig,
)
from semantic_kernel.skill_definition.function_view import FunctionView


class SequentialPlannerFunctionViewExtension:
    @staticmethod
    def to_manual_string(function: FunctionView):
        inputs = [
            f"  - {parameter.name}: {parameter.description}"
            + (
                f" (default value: {parameter.default_value})"
                if parameter.default_value
                else ""
            )
            for parameter in function.parameters
        ]

        inputs = "\n".join(inputs)
        qualified_name = SequentialPlannerFunctionViewExtension.to_fully_qualified_name(
            function
        )

        return (
            f"{qualified_name}:\n  description: {function.description}\n  inputs:\n "
            f" {inputs}"
        )

    @staticmethod
    def to_fully_qualified_name(function: FunctionView):
        return f"{function.skill_name}.{function.name}"

    @staticmethod
    def to_embedding_string(function: FunctionView):
        inputs = "\n".join(
            [
                f"    - {parameter.name}: {parameter.description}"
                for parameter in function.parameters
            ]
        )
        return (
            f"{function.name}:\n  description: {function.description}\n "
            f" inputs:\n{inputs}"
        )


class SequentialPlannerSKContextExtension:
    PLANNER_MEMORY_COLLECTION_NAME = " Planning.SKFunctionManual"
    PLAN_SK_FUNCTIONS_ARE_REMEMBERED = "Planning.SKFunctionsAreRemembered"

    @staticmethod
    async def get_functions_manual_async(
        context: SKContext,
        semantic_query: str = None,
        config: SequentialPlannerConfig = None,
    ) -> str:
        config = config or SequentialPlannerConfig()

        if config.get_available_functions_async is None:
            functions = (
                await SequentialPlannerSKContextExtension.get_available_functions_async(
                    context, config, semantic_query
                )
            )
        else:
            functions = await config.get_available_functions_async(
                config, semantic_query
            )

        return "\n\n".join(
            [
                SequentialPlannerFunctionViewExtension.to_manual_string(func)
                for func in functions
            ]
        )

    @staticmethod
    async def get_available_functions_async(
        context: SKContext,
        config: SequentialPlannerConfig,
        semantic_query: str = None,
    ):
        excluded_skills = config.excluded_skills or []
        excluded_functions = config.excluded_functions or []
        included_functions = config.included_functions or []

        if context.skills is None:
            raise KernelException(
                KernelException.ErrorCodes.SkillCollectionNotSet,
                "Skill collection not found in the context",
            )

        functions_view = context.skills.get_functions_view()

        available_functions: List[FunctionView] = [
            *functions_view.semantic_functions.values(),
            *functions_view.native_functions.values(),
        ]
        available_functions = itertools.chain.from_iterable(available_functions)

        available_functions = [
            func
            for func in available_functions
            if (
                func.skill_name not in excluded_skills
                and func.name not in excluded_functions
            )
        ]

        if (
            semantic_query is None
            or isinstance(context.memory, NullMemory)
            or config.relevancy_threshold is None
        ):
            # If no semantic query is provided, return all available functions.
            # If a Memory provider has not been registered, return all available functions.
            return available_functions

        # Remember functions in memory so that they can be searched.
        await SequentialPlannerSKContextExtension.remember_functions_async(
            context, available_functions
        )

        # Search for functions that match the semantic query.
        memories = await context.memory.search_async(
            SequentialPlannerSKContextExtension.PLANNER_MEMORY_COLLECTION_NAME,
            semantic_query,
            config.max_relevant_functions,
            config.relevancy_threshold,
        )

        # Add functions that were found in the search results.
        relevant_functions = (
            await SequentialPlannerSKContextExtension.get_relevant_functions_async(
                context, available_functions, memories
            )
        )

        # Add any missing functions that were included but not found in the search results.
        missing_functions = [
            func
            for func in included_functions
            if func not in [func.name for func in relevant_functions]
        ]

        relevant_functions += [
            func for func in available_functions if func.name in missing_functions
        ]

        return sorted(relevant_functions, key=lambda x: (x.skill_name, x.name))

    @staticmethod
    async def get_relevant_functions_async(
        context: SKContext,
        available_functions: List[FunctionView],
        memories: AsyncIterable[MemoryQueryResult],
    ) -> List[FunctionView]:
        relevant_functions = []
        # TODO: cancellation
        async for memory_entry in memories:
            function = next(
                (
                    func
                    for func in available_functions
                    if SequentialPlannerFunctionViewExtension.to_fully_qualified_name(
                        func
                    )
                    == memory_entry.id
                ),
                None,
            )
            if function is not None:
                context.log.debug(
                    "Found relevant function. Relevance Score: {0}, Function: {1}".format(
                        memory_entry.relevance,
                        SequentialPlannerFunctionViewExtension.to_fully_qualified_name(
                            function
                        ),
                    )
                )
                relevant_functions.append(function)

        return relevant_functions

    @staticmethod
    async def remember_functions_async(
        context: SKContext, available_functions: List[FunctionView]
    ):
        # Check if the functions have already been saved to memory.
        if context.variables.contains_key(
            SequentialPlannerSKContextExtension.PLAN_SK_FUNCTIONS_ARE_REMEMBERED
        ):
            return

        for function in available_functions:
            function_name = (
                SequentialPlannerFunctionViewExtension.to_fully_qualified_name(function)
            )
            key = function_name
            description = function.description or function_name
            text_to_embed = SequentialPlannerFunctionViewExtension.to_embedding_string(
                function
            )

            # It'd be nice if there were a saveIfNotExists method on the memory interface
            memory_entry = await context.memory.get_async(
                collection=SequentialPlannerSKContextExtension.PLANNER_MEMORY_COLLECTION_NAME,
                key=key,
                with_embedding=False,
            )
            if memory_entry is None:
                # TODO It'd be nice if the minRelevanceScore could be a parameter for each item that was saved to memory
                # As folks may want to tune their functions to be more or less relevant.
                # Memory now supports these such strategies.
                await context.memory.save_information_async(
                    collection=SequentialPlannerSKContextExtension.PLANNER_MEMORY_COLLECTION_NAME,
                    text=text_to_embed,
                    id=key,
                    description=description,
                    additional_metadata="",
                )

        # Set a flag to indicate that the functions have been saved to memory.
        context.variables.set(
            SequentialPlannerSKContextExtension.PLAN_SK_FUNCTIONS_ARE_REMEMBERED, "true"
        )
