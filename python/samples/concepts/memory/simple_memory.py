# Copyright (c) Microsoft. All rights reserved.

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

from samples.concepts.memory.utils import print_record
from samples.concepts.resources.utils import Colors, print_with_color
from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.connectors.in_memory import InMemoryCollection
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel

# This is the most basic example of a vector store and collection
# For a more complex example, using different collection types, see "complex_memory.py"
# This sample uses openai text embeddings, so make sure to have your environment variables set up
# it needs openai api key and embedding model id
embedder = OpenAITextEmbedding(service_id="embedding")

# Next, you need to define your data structure
# In this case, we are using a dataclass to define our data structure
# you can also use a pydantic model, or a vanilla python class, see "data_models.py" for more examples
# Inside the model we define which fields we want to use, and which fields are vectors
# and for vector fields we define what kind of index we want to use, and what distance function we want to use
# This has been done in constants here for simplicity, but you can also define them in the model itself
# Next we create three records using that model


@vectorstoremodel(collection_name="test")
@dataclass
class DataModel:
    content: Annotated[str, VectorStoreField("data")]
    id: Annotated[str, VectorStoreField("key")] = field(default_factory=lambda: str(uuid4()))
    vector: Annotated[
        list[float] | str | None,
        VectorStoreField("vector", dimensions=1536),
    ] = None
    title: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)] = "title"
    tag: Annotated[str, VectorStoreField("data", is_indexed=True)] = "tag"

    def __post_init__(self):
        if self.vector is None:
            self.vector = self.content


records = [
    DataModel(
        content="Semantic Kernel is awesome",
        id="e6103c03-487f-4d7d-9c23-4723651c17f4",
        title="Overview",
        tag="general",
    ),
    DataModel(
        content="Semantic Kernel is available in dotnet, python and Java.",
        id="09caec77-f7e1-466a-bcec-f1d51c5b15be",
        title="Semantic Kernel Languages",
        tag="general",
    ),
    DataModel(
        content="```python\nfrom semantic_kernel import Kernel\nkernel = Kernel()\n```",
        id="d5c9913a-e015-4944-b960-5d4a84bca002",
        title="Code sample",
        tag="code",
    ),
]


async def main():
    print("-" * 30)
    # Create the collection here
    # by using the generic we make sure that IDE's understand what you need to pass in and get back
    # we also use the async with to open and close the connection
    # for the in memory collection, this is just a no-op
    # but for other collections, like Azure AI Search, this will open and close the connection
    async with InMemoryCollection[str, DataModel](
        record_type=DataModel,
        embedding_generator=embedder,
    ) as record_collection:
        # Create the collection after wiping it
        print_with_color("Creating test collection!", Colors.CGREY)
        await record_collection.delete_create_collection()

        # First add vectors to the records
        print_with_color("Adding records!", Colors.CBLUE)
        keys = await record_collection.upsert(records)
        print(f"    Upserted {keys=}")
        print("-" * 30)

        # Now we can get the records back
        print_with_color("Getting records!", Colors.CBLUE)
        results = await record_collection.get([records[0].id, records[1].id, records[2].id])
        if results and isinstance(results, Sequence):
            [print_record(record=result) for result in results]
        else:
            print("Nothing found...")
        print("-" * 30)

        # Now we can search for records
        # First we define the options
        # The most important option is the vector_field_name, which is the name of the field that contains the vector
        # The other options are optional, but can be useful
        # The filter option is used to filter the results based on the tag field
        options = {
            "vector_property_name": "vector",
            "filter": lambda x: x.tag == "general",
        }
        query = "python"
        print_with_color(f"Searching for '{query}', with filter 'tag == general'", Colors.CBLUE)
        print_with_color(
            "Using vectorized search, the lower the score the better",
            Colors.CBLUE,
        )
        search_results = await record_collection.search(
            values=query,
            **options,
        )
        if search_results.total_count == 0:
            print("\nNothing found...\n")
        else:
            [print_record(result) async for result in search_results.results]
        print("-" * 30)

        # lets cleanup!
        print_with_color("Deleting collection!", Colors.CBLUE)
        await record_collection.ensure_collection_deleted()
        print_with_color("Done!", Colors.CGREY)


if __name__ == "__main__":
    asyncio.run(main())
