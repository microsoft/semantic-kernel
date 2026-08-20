# Copyright (c) Microsoft. All rights reserved.


import asyncio
import os

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

# This concept sample shows how to use the OpenAI connector to create a chat
# experience with Kelly Intelligence (https://api.thedailylesson.com), a hosted
# OpenAI-compatible API with a built-in 162,000-word vocabulary RAG layer and an
# AI tutor persona, built on top of Claude. It is operated by Lesson of the Day,
# PBC, a public benefit corporation. The free tier requires no credit card.
#
# Although this file lives under "local_models", the same `AsyncOpenAI` +
# `base_url` pattern that powers `lm_studio_chat_completion.py` and
# `foundry_local_chatbot.py` works for any OpenAI-compatible endpoint, local or
# hosted. Kelly Intelligence is a hosted instance of that pattern.
#
# Get a free API key (no credit card) at https://api.thedailylesson.com and
# export it before running this sample:
#
#     export KELLY_API_KEY=...
#     python kelly_intelligence_chat_completion.py
#
# You can also try the API with no signup at all using its public `/v1/demo`
# endpoint, which is rate-limited at 5 requests per hour per IP:
#
#     curl -X POST https://api.thedailylesson.com/v1/demo \
#       -H "Content-Type: application/json" \
#       -d '{"messages":[{"role":"user","content":"What does ephemeral mean?"}]}'

system_message = """
You are Kelly, a friendly vocabulary tutor. When the user gives you a word,
teach it in one short paragraph: definition, a memorable example sentence,
and one related word. Keep the tone warm and encouraging.
"""

kernel = Kernel()

service_id = "kelly-intelligence"

# Kelly Intelligence is OpenAI wire-format compatible, so we point a standard
# AsyncOpenAI client at its `/v1` base URL and let `OpenAIChatCompletion`
# handle the rest. The free model id is `kelly-haiku`; `kelly-sonnet` and
# `kelly-opus` are also available on paid tiers.
openAIClient: AsyncOpenAI = AsyncOpenAI(
    api_key=os.environ.get("KELLY_API_KEY", "fake-key"),
    base_url="https://api.thedailylesson.com/v1",
)
kernel.add_service(
    OpenAIChatCompletion(
        service_id=service_id,
        ai_model_id="kelly-haiku",
        async_client=openAIClient,
    )
)

settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
settings.max_tokens = 800
settings.temperature = 0.7
settings.top_p = 0.9

chat_function = kernel.add_function(
    plugin_name="VocabularyTutor",
    function_name="Chat",
    prompt="{{$chat_history}}{{$user_input}}",
    template_format="semantic-kernel",
    prompt_execution_settings=settings,
)

chat_history = ChatHistory(system_message=system_message)
chat_history.add_user_message("Hi! I'd like to learn some new English words today.")
chat_history.add_assistant_message(
    "Wonderful! Give me any word you're curious about and I'll teach it to you in one short paragraph."
)


async def chat() -> bool:
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    answer = await kernel.invoke(
        chat_function,
        KernelArguments(user_input=user_input, chat_history=chat_history),
    )
    chat_history.add_user_message(user_input)
    chat_history.add_assistant_message(str(answer))
    print(f"Kelly:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()

    # Sample output:
    # User:> serendipity
    # Kelly:> "Serendipity" is the happy accident of finding something good without looking for it -
    #         like discovering a favorite cafe while you were just trying to get out of the rain.
    #         A close cousin is "fortuitous", which describes lucky timing more generally.


if __name__ == "__main__":
    asyncio.run(main())
