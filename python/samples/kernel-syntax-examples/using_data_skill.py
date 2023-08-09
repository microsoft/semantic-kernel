# Copyright (c) Microsoft. All rights reserved.

import asyncio

import pandas as pd

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.core_skills import DataSkill

kernel = sk.Kernel()
api_key, org_id = sk.openai_settings_from_dot_env()
openai_chat_completion = sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
kernel.add_chat_service("chat_service", openai_chat_completion)


async def main() -> None:
    data1 = {
        "Name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "Age": [25, 32, 28, 22, 29],
        "City": ["New York", "Los Angeles", "Chicago", "Houston", "Miami"],
        "Salary": [60000, 75000, 52000, 48000, 67000],
    }
    data2 = {
        "Name": ["Amanda", "Brian", "Catherine", "Daniel", "Emily"],
        "Age": [27, 35, 31, 24, 30],
        "City": ["San Francisco", "Seattle", "Boston", "Austin", "Denver"],
        "Salary": [62000, 80000, 55000, 50000, 67000],
    }
    df1 = pd.DataFrame(data1)
    df2 = pd.DataFrame(data2)

    data_skill = kernel.import_skill(
        DataSkill(data=[df1, df2], service=openai_chat_completion), skill_name="data"
    )
    query_async = data_skill["queryAsync"]

    prompt = "How old is Bob and what city does Eve live in?"
    result = await query_async.invoke_async(prompt)
    print(result)
    #Output: Bob is 32 years old and Eve lives in Miami.

    prompt = "What is Emily's income?"
    result = await query_async.invoke_async(prompt)
    print(result)
    #Output: Emily's salary is $67,000.
    
    prompt = "Which group has a higher average salary and what is the difference?"
    query_async = data_skill["queryAsync"]
    result = await query_async.invoke_async(prompt)
    print(result)
    #Output: The group with a higher average salary is df2.
    

if __name__ == "__main__":
    asyncio.run(main())
