# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import (
    sk_function,
    sk_function_context_parameter,
    sk_function_input,
    sk_function_name,
)


class TextMemorySkill:

    COLLECTION_PARAM = "collection"
    RELEVANCE_PARAM = "relevance"
    KEY_PARAM = "key"
    DEFAULT_COLLECTION = "generic"
    DEFAULT_RELEVANCE = 0.75

    # @staticmethod
    @sk_function("Recall a fact from the long term memory")
    @sk_function_name("recall")
    @sk_function_input(description="The information to retrieve")
    @sk_function_context_parameter(
        name=COLLECTION_PARAM,
        description="The collection to search for information",
        default_value=DEFAULT_COLLECTION,
    )
    @sk_function_context_parameter(
        name=RELEVANCE_PARAM,
        description="The relevance score, from 0.0 to 1.0; 1.0 means perfect match",
        default_value=DEFAULT_RELEVANCE,
    )
    async def recall_async(ask: str, context: SKContext) -> str:
        """
        Recall a fact from the long term memory.

        Example:
            sk_context["input"] = "what is the capital of France?"
            {{memory.recall $input}} => "Paris"

        Args:
            ask -- The question to ask the memory
            context -- Contains the 'collection' to search for information
                and the 'relevance' score to use when searching

        Returns:
            The nearest item from the memory store
        """
        Verify.not_null(context.variables, "Context has no variables")
        assert context.variables is not None  # for type checker
        Verify.not_null(context.memory, "Context has no memory")
        assert context.memory is not None  # for type checker

        collection = (
            context.variables[TextMemorySkill.COLLECTION_PARAM]
            if context.variables.contains_key(TextMemorySkill.COLLECTION_PARAM)
            else TextMemorySkill.DEFAULT_COLLECTION
        )
        Verify.not_empty(
            collection, "Memory collection not defined for TextMemorySkill"
        )

        relevance = (
            context.variables[TextMemorySkill.RELEVANCE_PARAM]
            if context.variables.contains_key(TextMemorySkill.RELEVANCE_PARAM)
            else TextMemorySkill.DEFAULT_RELEVANCE
        )
        if relevance is None or str(relevance).strip() == "":
            relevance = TextMemorySkill.DEFAULT_RELEVANCE

        results = await context.memory.search_async(
            collection, ask, min_relevance_score=float(relevance)
        )
        if results is None or len(results) == 0:
            if context.log is not None:
                context.log.warning(f"Memory not found in collection: {collection}")
            return ""

        return results[0].text if results[0].text is not None else ""

    # @staticmethod
    @sk_function("Save information to semantic memory")
    @sk_function_name("save")
    @sk_function_input(description="The information to save")
    @sk_function_context_parameter(
        name=COLLECTION_PARAM,
        description="The collection to save the information",
        default_value=DEFAULT_COLLECTION,
    )
    @sk_function_context_parameter(
        name=KEY_PARAM,
        description="The unique key to associate with the information",
    )
    async def save_async(text: str, context: SKContext):
        """
        Save a fact to the long term memory.

        Example:
            sk_context["input"] = "the capital of France is Paris"
            sk_context[TextMemorySkill.KEY_PARAM] = "countryInfo1"
            {{memory.save $input}}

        Args:
            text -- The text to save to the memory
            context -- Contains the 'collection' to save the information
                and unique 'key' to associate with the information
        """
        Verify.not_null(context.variables, "Context has no variables")
        assert context.variables is not None  # for type checker
        Verify.not_null(context.memory, "Context has no memory")
        assert context.memory is not None  # for type checker

        collection = (
            context.variables[TextMemorySkill.COLLECTION_PARAM]
            if context.variables.contains_key(TextMemorySkill.COLLECTION_PARAM)
            else TextMemorySkill.DEFAULT_COLLECTION
        )
        Verify.not_empty(
            collection, "Memory collection not defined for TextMemorySkill"
        )

        key = (
            context.variables[TextMemorySkill.KEY_PARAM]
            if context.variables.contains_key(TextMemorySkill.KEY_PARAM)
            else None
        )
        Verify.not_empty(key, "Memory key not defined for TextMemorySkill")
        assert key is not None  # for type checker

        await context.memory.save_information_async(collection, text=text, id=key)
