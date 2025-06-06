# Copyright (c) Microsoft. All rights reserved.
import asyncio
from dataclasses import dataclass
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
    OpenAITextEmbedding,
)
from semantic_kernel.connectors.in_memory import InMemoryCollection
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel
from semantic_kernel.functions import KernelArguments

"""
This sample shows a really easy way to have RAG with a vector store.
It creates a simple datamodel, and then creates a collection with that datamodel.
Then we create a function that can search the collection.
Finally, in two different ways we call the function to search the collection.
"""


# Define a data model for the collection
# This model will be used to store the information in the collection
@vectorstoremodel(collection_name="budget")
@dataclass
class BudgetItem:
    id: Annotated[str, VectorStoreField("key")]
    text: Annotated[str, VectorStoreField("data")]
    embedding: Annotated[
        list[float] | str | None,
        VectorStoreField("vector", dimensions=1536, embedding_generator=OpenAITextEmbedding()),
    ] = None

    def __post_init__(self):
        if self.embedding is None:
            self.embedding = self.text


async def main():
    kernel = Kernel()

    kernel.add_service(OpenAIChatCompletion())

    async with InMemoryCollection(record_type=BudgetItem) as collection:
        # Add information to the collection
        await collection.upsert(
            [
                BudgetItem(id="info1", text="My budget for 2022 is $50,000"),
                BudgetItem(id="info1", text="My budget for 2023 is $75,000"),
                BudgetItem(id="info1", text="My budget for 2024 is $100,000"),
                BudgetItem(id="info2", text="My budget for 2025 is $150,000"),
            ],
        )
        # Create a function to search the collection
        # note the string_mapper, this is used to map the result of the search to a string
        kernel.add_function(
            "memory",
            collection.create_search_function(
                function_name="recall",
                description="Recalls the budget information.",
                string_mapper=lambda x: x.record.text,
            ),
        )

        # Call the search function directly from from a template.
        result = await kernel.invoke_prompt(
            function_name="budget",
            plugin_name="BudgetPlugin",
            prompt="{{memory.recall 'budget by year'}} What is my budget for 2024?",
        )
        print("Called from template")
        print(result)
        print("======================")
        # Let the LLM choose the function to call
        result = await kernel.invoke_prompt(
            function_name="budget",
            plugin_name="BudgetPlugin",
            prompt="What is my budget for 2024?",
            arguments=KernelArguments(
                settings=OpenAIChatPromptExecutionSettings(
                    function_choice_behavior=FunctionChoiceBehavior.Auto(),
                ),
            ),
        )
        print("Called from LLM")
        print(result)


"""
Output:

Called from template
Your budget for 2024 is $100,000.
======================
Called from LLM
Your budget for 2024 is $100,000.

"""

if __name__ == "__main__":
    asyncio.run(main())
