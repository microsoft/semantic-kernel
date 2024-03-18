# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.settings import (
    azure_openai_settings_from_dot_env_as_dict,
)


async def main():
    kernel = Kernel()

    service_id = "default"
    chat_service = AzureChatCompletion(
        service_id=service_id, **azure_openai_settings_from_dot_env_as_dict(include_api_version=True)
    )
    kernel.add_service(chat_service)

    cur_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
    plugin = kernel.import_plugin_from_yaml_prompt_directory(cur_dir, "sample_plugins")

    result = await kernel.invoke(plugin["Parrot"], count=2, user_message="I love parrots.")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
