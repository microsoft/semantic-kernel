# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

prompt = """
ChatBot can have a conversation with you about any topic.
It can give explicit instructions or say 'I don't know'
when it doesn't know the answer.

{{$chat_history}}

User:> {{$user_input}}
ChatBot:>
"""

kernel = sk.Kernel()

api_key, org_id = sk.openai_settings_from_dot_env()
service_id = "chat-gpt"
kernel.add_service(
    sk_oai.OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo-1106", api_key=api_key, org_id=org_id)
)

settings = kernel.get_service(service_id).get_prompt_execution_settings_class()(service_id=service_id)
settings.max_tokens = 2000
settings.temperature = 0.7
settings.top_p = 0.8

prompt_template_config = PromptTemplateConfig(
    template=prompt,
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(
            name="user_input",
            description="The history of the conversation",
            description="The user input",
            is_required=True,
            default="",
        ),
        InputVariable(
            name="chat_history",
            description="The history of the conversation",
            is_required=True,
        ),
    ],
    execution_settings=settings,
)

chat_history = ChatHistory()
chat_history.add_user_message("Hi there, who are you?")
chat_history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need")

chat_function = kernel.create_function_from_prompt(
    plugin_name="ChatBot", function_name="Chat", prompt_template_config=prompt_template_config
)


async def chat(chat_history: ChatHistory) -> bool:
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

    answer = await kernel.invoke(chat_function, user_input=user_input, chat_history=chat_history)
    chat_history.add_user_message(user_input)
    chat_history.add_assistant_message(str(answer))

    print(f"ChatBot:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat(chat_history)


if __name__ == "__main__":
    asyncio.run(main())
