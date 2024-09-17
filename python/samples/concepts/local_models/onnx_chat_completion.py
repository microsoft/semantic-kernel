# Copyright (c) Microsoft. All rights reserved.


import asyncio

from semantic_kernel.connectors.ai.onnx import OnnxGenAIChatCompletion, OnnxGenAIPromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.kernel import Kernel

# This concept sample shows how to use the Onnx connector with
# a local model running in Onnx

kernel = Kernel()

service_id = "phi3"
#############################################
# Make sure to download an ONNX model
# e.g (https://huggingface.co/microsoft/Phi-3-mini-128k-instruct-onnx)
# Then set the path to the model folder
#############################################
streaming = True
model_path = r"C:\GIT\models\phi3-cpu-onnx"

prompt_template = """
{% for message in messages %}
    {% if message['role'] == 'system' %}
        {{'<|system|>\n' + message['content'] + '<|end|>\n'}}
    {% elif message['role'] == 'user' %}
        {{'<|user|>\n' + message['content'] + '<|end|>\n'}}
    {% elif message['role'] == 'assistant' %}
        {{'<|assistant|>\n' + message['content'] + '<|end|>\n' }}
    {% endif %}
{% endfor %}
<|assistant|>"""


chat_completion = OnnxGenAIChatCompletion(
    ai_model_path=model_path, ai_model_id=service_id, prompt_template=prompt_template
)
settings = OnnxGenAIPromptExecutionSettings(
    max_length=3072,
)

system_message = """You are a helpful assistant."""
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
            if chunk:
                print(str(chunk), end="")
                message += str(chunk)
        print("\n")
        chat_history.add_assistant_message(message)
    else:
        answer = await chat_completion.get_chat_message_content(
            chat_history=chat_history, settings=settings, kernel=kernel
        )
        print(f"Mosscap:> {answer}")
        chat_history.add_assistant_message(answer)
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
