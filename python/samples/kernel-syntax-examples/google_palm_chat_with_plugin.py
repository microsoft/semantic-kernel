# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.google_palm as sk_gp
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.prompt_template.input_variable import InputVariable

"""
System messages prime the assistant with different personalities or behaviors.
The system message is added to the prompt template, and a chat history can be 
added as well to provide further context. 
A system message can only be used once at the start of the conversation, and 
conversation history persists with the instance of GooglePalmChatCompletion. To 
overwrite the system message and start a new conversation, you must create a new 
instance of GooglePalmChatCompletion.
Sometimes, PaLM struggles to use the information in the prompt template. In this 
case, it is recommended to experiment with the messages in the prompt template 
or ask different questions. 
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
service_id = "models/chat-bison-001"
palm_chat_completion = sk_gp.GooglePalmChatCompletion(service_id, api_key)
kernel.add_service(palm_chat_completion)

req_settings = kernel.get_service(service_id).get_prompt_execution_settings_class()(service_id=service_id)
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8

prompt_template_config = sk.PromptTemplateConfig(
    template="{{$user_input}}",
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(name="user_input", description="The user input", is_required=True),
        InputVariable(name="chat_history", description="The history of the conversation", is_required=True),
    ],
    execution_settings=req_settings,
)

chat_func = kernel.create_function_from_prompt(
    plugin_name="PiratePlugin", function_name="Chat", prompt_template_config=prompt_template_config
)

chat_history = ChatHistory()
chat_history.add_system_message(system_message)
chat_history.add_user_message("Hi there, who are you?")
chat_history.add_assistant_message("I am Blackbeard.")


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

    answer = await kernel.invoke(chat_func, user_input=user_input, chat_history=chat_history)
    print(f"Blackbeard:> {answer}")
    chat_history.add_user_message(user_input)
    chat_history.add_assistant_message(str(answer))
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
