# Copyright (c) Microsoft. All rights reserved.
import logging

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion


def setup_logging():
    # Setup a detailed logging format.
    logging.basicConfig(
        format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set the logging level for  semantic_kernel.kernel to DEBUG.
    logging.getLogger("kernel").setLevel(logging.DEBUG)


async def main():
    kernel = sk.Kernel()

    api_key, org_id = sk.openai_settings_from_dot_env()

    kernel.add_chat_service(
        "chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
    )

    skill = kernel.import_semantic_skill_from_directory(
        "../../samples/skills", "FunSkill"
    )

    joke_function = skill["Joke"]

    print(joke_function("time travel to dinosaur age"))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
