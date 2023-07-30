# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
import asyncio
import semantic_kernel.connectors.ai.google_palm as sk_gp
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings

async def chat_request_example(api_key):
    palm_chat_completion = sk_gp.GooglePalmChatCompletion(
        "models/chat-bison-001", api_key
    )
    settings = ChatRequestSettings()
    settings.temperature = 1
    
    chat_messages = list()
    user_mssg = "I'm planning a vacation. Which are some must-visit places in Europe?"
    chat_messages.append(("user", user_mssg))
    answer = await palm_chat_completion.complete_chat_async(chat_messages, settings)
    chat_messages.append(("assistant", str(answer)))
    user_mssg = "Where should I go in France?"
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
    api_key = sk.google_palm_settings_from_dot_env()
    chat = await chat_request_example(api_key)
    print(chat["chat_history"])
    return

if __name__ == "__main__":
    asyncio.run(main())