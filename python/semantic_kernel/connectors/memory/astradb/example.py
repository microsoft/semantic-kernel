import asyncio
import numpy as np

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.connectors.memory.astradb.astradb_memory_store import AstraDBMemoryStore


def memory_record(_id):
    return MemoryRecord(
        id=str(_id),
        text=f"{_id} text",
        is_reference=False,
        embedding=np.array([1 / (_id + val) for val in range(0, 5)]),
        description=f"{_id} description",
        external_source_name=f"{_id} external source",
        additional_metadata=f"{_id} additional metadata",
        timestamp=None,
        key=str(_id),
    )


async def main():
    store = AstraDBMemoryStore(
        astra_application_token="AstraCS:ZUJZcHtgmQswaEDUGqvfDZKU:88c0442ab720e1bb574c8b838c2afa6fbcf7a53b7ef3cc6237d7d4b763c565bd",
        astra_id="2ee186dc-3fa5-45b9-a585-5f978c3db9bd",
        astra_region="us-east1",
        keyspace_name="anant",
        embedding_dim=5,
        similarity="cosine")

    collection_name = "semantic"

    # exists = await store.does_collection_exist_async(collection_name)
    # if exists == True:
    #     print(f"Collection exists: {collection_name}, delete this one")
    #     await store.delete_collection_async(collection_name)

    # print(f"Create new collection: {collection_name}")
    # await store.create_collection_async(collection_name)

    # records = [memory_record(i) for i in range(1, 10)]

    # await store.upsert_async(collection_name, records[0])
    # await store.upsert_async(collection_name, records[2])

    # upserted_ids = await store.upsert_batch_async(collection_name, records)
    # print(f"Upserted ids: {upserted_ids}")

    # get_record = await store.get_async(collection_name, "1")
    # print(get_record)

    # await store.remove_async(collection_name, "3")

    # p, t = await store.get_nearest_match_async(collection_name, np.array([0.3, 0.2, 0.4, 0.3, 0.1]))
    # print(t)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
