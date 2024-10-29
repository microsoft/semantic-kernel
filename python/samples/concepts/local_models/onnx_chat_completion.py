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
# (https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-onnx)
# If onnxruntime-genai is used:
# use the model stored in /cpu folder
# If onnxruntime-genai-cuda is installed for gpu use:
# use the model stored in /cuda folder
# Then set ONNX_GEN_AI_CHAT_MODEL_FOLDER environment variable to the path to the model folder
#############################################
streaming = True

chat_completion = OnnxGenAIChatCompletion(ai_model_id=service_id, template="phi3")
settings = OnnxGenAIPromptExecutionSettings()

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
        chat_history.add_assistant_message(message)
        print("")
    else:
        answer = await chat_completion.get_chat_message_content(
            chat_history=chat_history, settings=settings, kernel=kernel
        )
        print(f"Mosscap:> {answer}")
        chat_history.add_message(answer)
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
