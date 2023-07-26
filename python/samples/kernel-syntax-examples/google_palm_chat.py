# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
import asyncio
import semantic_kernel.connectors.ai.google_palm as sk_gp
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
import google.generativeai as palm

async def chat_request_example(api_key):
    palm_chat_completion = sk_gp.GooglePalmChatCompletion(
        "models/chat-bison-001", api_key
    )
    settings = ChatRequestSettings()
    settings.temperature = 1
    
    chat_messages = list()
    user_mssg = "I love the LA Lakers, tell me an interesting fact about LeBron James."
    chat_messages.append(("user", user_mssg))
    answer = await palm_chat_completion.complete_chat_async(chat_messages, settings)
    chat_messages.append(("assistant", str(answer)))
    user_mssg = "What are his best all-time stats?"
    chat_messages.append(("user", user_mssg))
    answer = await palm_chat_completion.complete_chat_async(chat_messages, settings)
    chat_messages.append(("assistant", str(answer)))

    context_vars = sk.ContextVariables()
    context_vars["chat_history"] = ""
    context_vars["chat_bot_ans"] = ""
    for role, mssg in chat_messages:
        if role == "user":
            context_vars["chat_history"] += f"User:> {mssg}\n"
        elif role == "assistant":
            context_vars["chat_history"] += f"ChatBot:> {mssg}\n"
            context_vars["chat_bot_ans"] += f"{mssg}\n"
    
    return context_vars

async def main() -> None:
    kernel = sk.Kernel()
    api_key = sk.google_palm_settings_from_dot_env()
    chat = await chat_request_example(kernel, api_key)
    print(chat["chat_history"])
    return

if __name__ == "__main__":
    asyncio.run(main())