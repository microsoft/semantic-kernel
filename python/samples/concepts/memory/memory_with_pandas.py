# Copyright (c) Microsoft. All rights reserved.

import asyncio
from uuid import uuid4

import pandas as pd

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIEmbeddingPromptExecutionSettings,
    OpenAITextEmbedding,
)
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection
from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_search import add_vector_to_records

model_fields = VectorStoreRecordDefinition(
    container_mode=True,
    fields={
        "content": VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector"),
        "id": VectorStoreRecordKeyField(),
        "vector": VectorStoreRecordVectorField(
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)}
        ),
    },
    to_dict=lambda record, **_: record.to_dict(orient="records"),
    from_dict=lambda records, **_: pd.DataFrame(records),
)


async def main():
    # setup the kernel
    kernel = Kernel()
    kernel.add_service(OpenAITextEmbedding(service_id="embedding", ai_model_id="text-embedding-3-small"))

    # create the record collection
    async with AzureAISearchCollection[pd.DataFrame](
        data_model_type=pd.DataFrame,
        data_model_definition=model_fields,
    ) as record_collection:
        # create some records
        records = [
            {"id": str(uuid4()), "content": "my dict text", "vector": None},
            {"id": str(uuid4()), "content": "my second text", "vector": None},
        ]

        # create the dataframe and add the embeddings
        df = pd.DataFrame(records)
        df = await add_vector_to_records(kernel, df, None, data_model_definition=model_fields)
        print("Records with embeddings:")
        print(df.shape)
        print(df.head(5))

        # upsert the records (for a container, upsert and upsert_batch are equivalent)
        await record_collection.upsert_batch(df)

        # retrieve a record
        result = await record_collection.get(records[0]["id"])
        print("Retrieved records:")
        print(result.shape)
        print(result.head(5))


if __name__ == "__main__":
    asyncio.run(main())
