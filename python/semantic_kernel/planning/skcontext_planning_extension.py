from typing import List

from concurrent.futures import ThreadPoolExecutor

from semantic_kernel.core_skills.planner_skill import PlannerSkillConfig, Parameters
from semantic_kernel.kernel import SKContext
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.skill_definition.function_view import FunctionView
from semantic_kernel.memory.memory_query_result import MemoryQueryResult


class SKContextPlanningExtensions:
    PlannerMemoryCollectionName = "Planning.SKFunctionsManual"
    PlanSKFunctionsAreRemembered = "Planning.SKFunctionsAreRemembered"

    @staticmethod
    async def get_functions_manual_async(
        context: SKContext,
        semantic_query: str = None,
        config: PlannerSkillConfig = None,
    ) -> str:
        config = config or PlannerSkillConfig()
        functions = await SKContextPlanningExtensions.get_available_functions_async(
            context, config, semantic_query
        )

        return "\n\n".join(x.to_manual_string() for x in functions)

    @staticmethod
    async def get_available_functions_async(
        context: SKContext,
        config: PlannerSkillConfig = None,
        semantic_query: str = None,
    ) -> List[FunctionView]:
        excluded_skills = config.excluded_skills or []
        excluded_functions = config.excluded_functions or []
        included_functions = config.included_functions or []

        context.throw_if_skill_collection_not_set()
        functions_view = context.skills.get_functions_view()

        available_functions = [
            f for x in functions_view._semantic_functions.values() for f in x
        ] + [f for x in functions_view._native_functions.values() for f in x]

        available_functions = [
            f
            for f in available_functions
            if f.skill_name not in excluded_skills and f.name not in excluded_functions
        ]

        if (
            not semantic_query
            or isinstance(context.memory, NullMemory)
            or config.relevancy_threshold is None
        ):
            # If no semantic query is provided, return all available functions.
            # If a Memory provider has not been registered, return all available functions.
            result = available_functions
        else:
            result = []
            # Remember functions in memory so that they can be searched.
            await SKContextPlanningExtensions.remember_functions_async(
                context, available_functions
            )

            # Search for functions that match the semantic query.
            memories = context.memory.search_async(
                SKContextPlanningExtensions.PlannerMemoryCollectionName,
                semantic_query,
                config.max_relevant_functions,
                config.relevancy_threshold,
                context._cancellation_token,
            )

            # Add functions that were found in the search results.
            result += await SKContextPlanningExtensions.get_relevant_functions_async(
                context, available_functions, memories
            )

            # Add any missing functions that were included but not found in the search results.
            missing_functions = [
                f for f in included_functions if f.name not in [x.name for x in result]
            ]
            missing_functions = [
                af
                for f in missing_functions
                for af in available_functions
                if f == af.name
            ]

            result += missing_functions

        return result

    @staticmethod
    async def get_relevant_functions_async(
        context: SKContext,
        available_functions: List[FunctionView],
        memories: List[MemoryQueryResult],
    ) -> List[FunctionView]:
        relevant_functions = []
        with ThreadPoolExecutor() as executor:
            for memory_entry in memories:
                function = next(
                    (
                        x
                        for x in available_functions
                        if x.to_fully_qualified_name() == memory_entry.id
                    ),
                    None,
                )
                if function:
                    context.log.debug(
                        "Found relevant function. Relevance Score: %s, Function: %s",
                        memory_entry.relevance,
                        function.to_fully_qualified_name(),
                    )
                    relevant_functions.append(function)

        return relevant_functions

    @staticmethod
    async def remember_functions_async(
        context: SKContext, available_functions: List[FunctionView]
    ) -> None:
        # Check if the functions have already been saved to memory.
        if context.variables.get(
            SKContextPlanningExtensions.PlanSKFunctionsAreRemembered
        ):
            return

        for function in available_functions:
            function_name = function.to_fully_qualified_name()
            key = function.description if function.description else function_name

            # It'd be nice if there were a saveIfNotExists method on the memory interface
            memory_entry = await context.memory.get_async(
                SKContextPlanningExtensions.PlannerMemoryCollectionName,
                key,
                context._cancellation_token,
            )
            if not memory_entry:
                # TODO It'd be nice if the min_relevance_score could be a parameter for each item that was saved to memory
                # As folks may want to tune their functions to be more or less relevant.
                await context.memory.save_information_async(
                    SKContextPlanningExtensions.PlannerMemoryCollectionName,
                    key,
                    function_name,
                    function.to_manual_string(),
                    context._cancellation_token,
                )

        # Set a flag to indicate that the functions have been saved to memory.
        context.variables.set(
            SKContextPlanningExtensions.PlanSKFunctionsAreRemembered, "true"
        )

    @staticmethod
    def get_planner_skill_config(context: SKContext) -> PlannerSkillConfig:
        config = PlannerSkillConfig()

        threshold = context.variables.get(Parameters.relevancy_threshold)
        if threshold is not None:
            parsed_value = float(threshold)
            config.relevancy_threshold = parsed_value

        max_relevant_functions = context.variables.get(
            Parameters.max_relevant_functions
        )
        if max_relevant_functions is not None:
            parsed_value = int(max_relevant_functions)
            config.max_relevant_functions = parsed_value

        excluded_functions = context.variables.get(Parameters.excluded_functions)
        if excluded_functions is not None:
            excluded_functions_list = excluded_functions.split(",").map(str.strip)
            # Excluded functions and excluded skills from context.variables should be additive to the default excluded functions and skills.
            config.excluded_functions.update(
                excluded_functions_list - config.excluded_functions
            )

        excluded_skills = context.variables.get(Parameters.excluded_skills)
        if excluded_skills is not None:
            excluded_skills_list = excluded_skills.split(",").map(str.strip)
            # Excluded functions and excluded skills from context.variables should be additive to the default excluded functions and skills.
            config.excluded_skills.update(excluded_skills_list - config.excluded_skills)

        included_functions = context.variables.get(Parameters.included_functions)
        if included_functions is not None:
            included_functions_list = included_functions.split(",").map(str.strip)
            # Included functions from context.variables should not override the default excluded functions.
            config.included_functions.update(
                included_functions_list - config.excluded_functions
            )
            config.included_functions.difference_update(config.excluded_functions)

        return config
