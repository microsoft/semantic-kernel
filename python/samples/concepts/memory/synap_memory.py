# Copyright (c) Microsoft. All rights reserved.

"""Sample: long-term memory via the Synap plugin.

[Synap](https://maximem.ai) is a managed long-term memory layer for AI agents.
The `synap-semantic-kernel` package exposes it as a Semantic Kernel plugin
(`SynapPlugin`) with `search_memory` and `store_memory` kernel functions, so a
chat completion service can recall and persist facts across sessions.

Setup:
    pip install synap-semantic-kernel maximem-synap semantic-kernel
    export SYNAP_API_KEY=<your-key>     # https://synap.maximem.ai
    export OPENAI_API_KEY=<your-key>

Open source integration package:
https://github.com/maximem-ai/maximem_synap_sdk/tree/main/packages/integrations/synap-semantic-kernel
"""

import asyncio
import os

from maximem_synap import MaximemSynapSDK
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from synap_semantic_kernel import SynapPlugin


async def main() -> None:
    sdk = MaximemSynapSDK(api_key=os.environ["SYNAP_API_KEY"])
    await sdk.initialize()

    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(ai_model_id="gpt-4o-mini"))
    kernel.add_plugin(
        SynapPlugin(sdk=sdk, user_id="demo-user-001", customer_id="demo-customer"),
        plugin_name="synap",
    )

    chat_service = kernel.get_service()
    settings = OpenAIChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )

    history = ChatHistory()
    history.add_system_message(
        "You are a helpful assistant with long-term memory. "
        "Use synap-search_memory to recall facts about the user. "
        "Use synap-store_memory to save important new facts."
    )

    # Turn 1: teach
    history.add_user_message(
        "I'm a software engineer who's allergic to peanuts. Remember this."
    )
    response = await chat_service.get_chat_message_content(
        chat_history=history, settings=settings, kernel=kernel
    )
    print(f"Assistant: {response}")
    history.add_message(response)

    # Turn 2: recall
    history.add_user_message("What do you know about my dietary restrictions?")
    response = await chat_service.get_chat_message_content(
        chat_history=history, settings=settings, kernel=kernel
    )
    print(f"Assistant: {response}")


if __name__ == "__main__":
    asyncio.run(main())
