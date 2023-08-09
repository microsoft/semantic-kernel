# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.core_skills import CodeSkill

kernel = sk.Kernel()
api_key, org_id = sk.openai_settings_from_dot_env()
openai_chat_completion = sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
kernel.add_chat_service("chat_service", openai_chat_completion)


async def main() -> None:
    # Setup and fetch functions to use
    code_skill = kernel.import_skill(
        CodeSkill(openai_chat_completion), skill_name="code"
    )
    code_async = code_skill["codeAsync"]
    execute_async = code_skill["executeAsync"]
    execute_code_async = code_skill["executeCodeAsync"]

    # Generate code for FizzBuzz
    fizzbuzz_prompt = "Write a function to solve FizzBuzz with parameter n, and print output for n up to 10"
    fizzbuzz_code = await code_async.invoke_async(fizzbuzz_prompt)
    print(fizzbuzz_code)

    # Pass into execution
    await execute_code_async.invoke_async(fizzbuzz_code)
    """Output
    def fizzbuzz(n):
    for i in range(1, n+1):
        if i % 3 == 0 and i % 5 == 0:
            print("FizzBuzz")
        elif i % 3 == 0:
            print("Fizz")
        elif i % 5 == 0:
            print("Buzz")
        else:
            print(i)

    fizzbuzz(10)

    1
    2
    Fizz
    4
    Buzz
    Fizz
    7
    8
    Fizz
    Buzz
    """

    # Generate and execute altogether
    print("Fibonacci sequence for 5 terms: ", end="")
    await execute_async.invoke_async("Write 5 terms of the Fibonacci sequence.")
    """Output:
    [0, 1, 1, 2, 3]
    """


if __name__ == "__main__":
    asyncio.run(main())
