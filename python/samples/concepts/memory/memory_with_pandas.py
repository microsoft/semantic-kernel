# Copyright (c) Microsoft. All rights reserved.

import asyncio
from uuid import uuid4

import pandas as pd

from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection
from semantic_kernel.data import VectorStoreCollectionDefinition, VectorStoreField

definition = VectorStoreCollectionDefinition(
    collection_name="pandas_test_index",
    fields=[
        VectorStoreField("key", name="id", type="str"),
        VectorStoreField("data", name="title", type="str"),
        VectorStoreField("data", name="content", type="str", is_full_text_indexed=True),
        VectorStoreField(
            "vector",
            name="vector",
            type="float",
            dimensions=1536,
            embedding_generator=OpenAITextEmbedding(ai_model_id="text-embedding-3-small"),
        ),
    ],
    to_dict=lambda record, **_: record.to_dict(orient="records"),
    from_dict=lambda records, **_: pd.DataFrame(records),
    container_mode=True,
)


async def main():
    # create the record collection
    async with AzureAISearchCollection[str, pd.DataFrame](
        record_type=pd.DataFrame,
        definition=definition,
    ) as collection:
        await collection.ensure_collection_exists()
        # create some records
        records = [
            {
                "id": str(uuid4()),
                "title": "Document about Semantic Kernel.",
                "content": "Semantic Kernel is a framework for building AI applications.",
            },
            {
                "id": str(uuid4()),
                "title": "Document about Python",
                "content": "Python is a programming language that lets you work quickly.",
            },
        ]

        # create the dataframe and add the content you want to embed to a new column
        df = pd.DataFrame(records)
        df["vector"] = df.apply(lambda row: f"title: {row['title']}, content: {row['content']}", axis=1)
        print(df.head(1))
        # upsert the records (for a container, upsert and upsert_batch are equivalent)
        await collection.upsert(df)

        # retrieve a record
        result = await collection.get(top=2)
        if result is None:
            print("No records found, this is sometimes because the get is too fast and the index is not ready yet.")
        else:
            print("Retrieved records:")
            print(result.to_string())

        await collection.ensure_collection_deleted()


if __name__ == "__main__":
    asyncio.run(main())
