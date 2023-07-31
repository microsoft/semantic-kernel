# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter


class TextMemorySkill:
    COLLECTION_PARAM = "collection"
    RELEVANCE_PARAM = "relevance"
    KEY_PARAM = "key"
    NUM_RECORDS_PARAM = "num_records"
    DEFAULT_COLLECTION = "generic"
    DEFAULT_RELEVANCE = 0.75
    DEFAULT_NUM_RECORDS = 1

    # @staticmethod
    @sk_function(
        description="Recall a fact from the long term memory",
        name="recall",
        input_description="The information to retrieve",
    )
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
    @sk_function_context_parameter(
        name=NUM_RECORDS_PARAM,
        description="The number of records to retrieve, default is 1, when more then 1 a comma separated string of the results is returned.",
        default_value=DEFAULT_NUM_RECORDS,
    )
    async def recall_async(self, ask: str, context: SKContext) -> str:
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
        if context.variables is None:
            raise ValueError("Context has no variables")
        if context.memory is None:
            raise ValueError("Context has no memory")

        collection = (
            context.variables[TextMemorySkill.COLLECTION_PARAM]
            if context.variables.contains_key(TextMemorySkill.COLLECTION_PARAM)
            else TextMemorySkill.DEFAULT_COLLECTION
        )
        if not collection:
            raise ValueError("Memory collection not defined for TextMemorySkill")

        relevance = (
            context.variables[TextMemorySkill.RELEVANCE_PARAM]
            if context.variables.contains_key(TextMemorySkill.RELEVANCE_PARAM)
            else TextMemorySkill.DEFAULT_RELEVANCE
        )
        if relevance is None or str(relevance).strip() == "":
            relevance = TextMemorySkill.DEFAULT_RELEVANCE

        num_records = (
            context.variables[TextMemorySkill.NUM_RECORDS_PARAM]
            if context.variables.contains_key(TextMemorySkill.NUM_RECORDS_PARAM)
            else TextMemorySkill.DEFAULT_NUM_RECORDS
        )
        if num_records is None or str(num_records).strip() == "":
            num_records = TextMemorySkill.DEFAULT_NUM_RECORDS

        results = await context.memory.search_async(
            collection=collection, query=ask, limit=int(num_records), min_relevance_score=float(relevance)
        )
        if results is None or len(results) == 0:
            if context.log is not None:
                context.log.warning(f"Memory not found in collection: {collection}")
            return ""
        return ", ".join([result.text for result in results if result.text is not None])

    @sk_function(
        description="Save information to semantic memory",
        name="save",
        input_description="The information to save",
    )
    @sk_function_context_parameter(
        name=COLLECTION_PARAM,
        description="The collection to save the information",
        default_value=DEFAULT_COLLECTION,
    )
    @sk_function_context_parameter(
        name=KEY_PARAM,
        description="The unique key to associate with the information",
    )
    async def save_async(self, text: str, context: SKContext):
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
        if context.variables is None:
            raise ValueError("Context has no variables")
        if context.memory is None:
            raise ValueError("Context has no memory")

        collection = (
            context.variables[TextMemorySkill.COLLECTION_PARAM]
            if context.variables.contains_key(TextMemorySkill.COLLECTION_PARAM)
            else TextMemorySkill.DEFAULT_COLLECTION
        )
        if not collection:
            raise ValueError("Memory collection not defined for TextMemorySkill")

        key = (
            context.variables[TextMemorySkill.KEY_PARAM]
            if context.variables.contains_key(TextMemorySkill.KEY_PARAM)
            else None
        )
        if not key:
            raise ValueError("Memory key not defined for TextMemorySkill")

        await context.memory.save_information_async(collection, text=text, id=key)
