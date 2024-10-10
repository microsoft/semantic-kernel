# Copyright (c) Microsoft. All rights reserved.


import asyncio

from semantic_kernel.connectors.ai.onnx import OnnxGenAITextCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments
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
# Then set ONNX_GEN_AI_TEXT_MODEL_FOLDER environment variable to the path to the model folder
#############################################
streaming = True

kernel.add_service(OnnxGenAITextCompletion(ai_model_id=service_id))

settings = kernel.get_prompt_execution_settings_from_service_id(service_id)

# Phi3 Model is using chat templates to generate responses
# With the Chat Template the model understands
# the context and roles of the conversation better
# https://huggingface.co/microsoft/Phi-3-mini-4k-instruct#chat-format
chat_function = kernel.add_function(
    plugin_name="ChatBot",
    function_name="Chat",
    prompt="<|user|>{{$user_input}}<|end|><|assistant|>",
    template_format="semantic-kernel",
    prompt_execution_settings=settings,
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

    if streaming:
        print("Mosscap:> ", end="")
        async for chunk in kernel.invoke_stream(chat_function, KernelArguments(user_input=user_input)):
            print(chunk[0].text, end="")
        print("\n")
    else:
        answer = await kernel.invoke(chat_function, KernelArguments(user_input=user_input))
        print(f"Mosscap:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
