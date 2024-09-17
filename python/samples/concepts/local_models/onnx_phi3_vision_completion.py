# Copyright (c) Microsoft. All rights reserved.


import asyncio

from semantic_kernel.connectors.ai.onnx import OnnxGenAIChatCompletion, OnnxGenAIPromptExecutionSettings
from semantic_kernel.contents import AuthorRole, ChatMessageContent, ImageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.kernel import Kernel

# This concept sample shows how to use the Onnx connector with
# a local model running in Onnx

kernel = Kernel()

service_id = "phi3"
#############################################
# Make sure to download an ONNX model
# e.g (https://huggingface.co/microsoft/Phi-3-vision-128k-instruct-onnx-cpu)
# Then set the path to the model folder
#############################################
streaming = False
model_path = r"C:\GIT\models\phi3V-cpu-onnx"

prompt_template = """
{% for message in messages %}
    {% if message['content'] is not string %}
        {{'<|image_1|>'}}
    {% else %}
        {% if message['role'] == 'system' %}
            {{'<|system|>\n' + message['content'] + '<|end|>\n'}}
        {% elif message['role'] == 'user' %}
            {{'<|user|>\n' + message['content'] + '<|end|>\n'}}
        {% elif message['role'] == 'assistant' %}
            {{'<|assistant|>\n' + message['content'] + '<|end|>\n' }}
        {% endif %}
    {% endif %}
{% endfor %}
<|assistant|>"""

chat_completion = OnnxGenAIChatCompletion(
    ai_model_path=model_path, ai_model_id=service_id, prompt_template_config=prompt_template
)
settings = OnnxGenAIPromptExecutionSettings(
    max_length=3072,
)

system_message = """
You are a helpful assistant.
You know about provided images and the history of the conversation.
"""
chat_history = ChatHistory(system_message=system_message)


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
    chat_history.add_user_message(user_input)
    if streaming:
        print("Mosscap:> ", end="")
        message = ""
        async for chunk in chat_completion.get_streaming_chat_message_content(
            chat_history=chat_history, settings=settings, kernel=kernel
        ):
            print(chunk.content, end="")
            if chunk.content:
                message += chunk.content
        print("\n")
        chat_history.add_message(message)
    else:
        answer = await chat_completion.get_chat_message_content(
            chat_history=chat_history, settings=settings, kernel=kernel
        )
        print(f"Mosscap:> {answer}")
        chat_history.add_message(answer)
    return True


async def main() -> None:
    chatting = True
    image_path = input("Image Path (leave empty if no image): ")
    if image_path:
        chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                items=[
                    ImageContent.from_image_path(image_path=image_path),
                ],
            ),
        )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
