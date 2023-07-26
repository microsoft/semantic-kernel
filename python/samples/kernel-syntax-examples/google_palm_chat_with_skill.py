# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
import asyncio
import semantic_kernel.connectors.ai.google_palm as sk_gp
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings

"""
System messages prime the assistant with different personalities or behaviors. 
Google PaLM uses a parameter called "context" to be used at the start of a 
conversation instead of a system message, as is used in OpenAI. For consistency 
with the OpenAI service, we will continue to refer to context as a system 
message. A system message can only be used once at the start of the conversation 
but can be overwritten by passing a new system message to complete_chat_async. 
The conversation history persists with the instance of GooglePalmChatCompletion.
"""

system_message = """
You are a chat bot. Your name is Blackbeard
and you speak in the style of a swashbuckling
pirate. You reply with brief, to-the-point answers 
with no elaboration. Your full name is Captain 
Bartholomew "Blackbeard" Thorne.
"""

kernel = sk.Kernel()
api_key = sk.google_palm_settings_from_dot_env()
palm_chat_completion = sk_gp.GooglePalmChatCompletion(
        "models/chat-bison-001", api_key
)
kernel.add_chat_service("models/chat-bison-001", palm_chat_completion)

prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
        max_tokens=2000, temperature=0.7, top_p=0.8
)
prompt_template = sk.ChatPromptTemplate(
    "{{$user_input}}", kernel.prompt_template_engine, prompt_config
)

prompt_template.add_system_message(system_message)
prompt_template.add_user_message("Hi there, who are you?")
prompt_template.add_assistant_message(
    "I am Blackbeard."
)
function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("PirateSkill", "Chat", function_config)

async def chat() -> bool:
    context_vars = sk.ContextVariables()

    try:
        user_input = input("User:> ")
        context_vars["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    answer = await kernel.run_async(chat_function, input_vars=context_vars)
    print(f"Blackbeard:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
