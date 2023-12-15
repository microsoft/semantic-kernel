import asyncio
import json
import time

import os

from semantic_kernel.connectors.memory.astradb.ai_sample.utils import *

import split_q_and_a


def get_input_data():
    scraped_results_file = os.path.join(
        os.path.dirname(__file__), 'scraped_results.json')
    with open(scraped_results_file) as f:
        scraped_data = json.load(f)

        faq_scraped_data = []
        for d in scraped_data:
            if "faq" in d["url"].lower():
                faq_scraped_data.append(d)
    return faq_scraped_data


async def populate():
    collection_exist = await memory_store.does_collection_exist_async(COLLECTION_NAME)
    if collection_exist == True:
        await memory_store.delete_collection_async(COLLECTION_NAME)
    await memory_store.create_collection_async(COLLECTION_NAME)

    input_data_faq = get_input_data()

    # process faq data
    for webpage in input_data_faq:
        q_and_a_data = split_q_and_a.split(webpage)
        count = 1
        for i in range(0, len(q_and_a_data["questions"])):
            question = q_and_a_data["questions"][i]
            answer = q_and_a_data["answers"][i]

            time.sleep(1)

            if (question == " Cluster?") or (question == "?"):
                print("Malformed question. Not adding to vector db.")
            else:
                await kernel.memory.save_information_async(
                    collection=COLLECTION_NAME, id=str(count), text=answer, description=question
                )
                count += 1


if __name__ == "__main__":
    s = time.perf_counter()
    asyncio.run(populate())
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
