# Copyright (c) Microsoft. All rights reserved.

import PyPDF2
import asyncio
import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
import os
from dotenv import load_dotenv

load_dotenv("var.env")
api_key = os.getenv('OPENAI_API_KEY')


collection_id = "generic"


def extract_text_from_pdf(pdf_file_path):
    text = ""
    with open(pdf_file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


async def populate_memory_from_files(memory: SemanticTextMemory) -> None:
    # Read text from .txt files and save them to the semantic memory
    with open("data\info1.txt", "r") as file:
        info1_text = file.read()
    with open("data\info3.txt", "r") as file:
        info2_text = file.read()
    with open("data\info2.txt", "r") as file:
        info3_text = file.read()
    info4_text = extract_text_from_pdf("data\info4.pdf")

    await memory.save_information(collection=collection_id, id="info1", text=info1_text)
    await memory.save_information(collection=collection_id, id="info2", text=info2_text)
    await memory.save_information(collection=collection_id, id="info3", text=info3_text)
    await memory.save_information(collection=collection_id, id="info4", text=info4_text)


async def setup_chat_with_memory(
    kernel: sk.Kernel,
    service_id: str,
) -> sk.KernelFunction:
    prompt = """
    Instructions:

    You name is Aqua, a personal chatbot, that will response to the query of user in a professional manner.
    Response to user query accordingly, do not provide any useful infromation to user yoursef, just provide realted information to user when he ask, otherwise behave normally.
    Provide Response in a formatted manner using bullet points, highlight words where necessary.


    Learn from this conversation between user and chatbot that how to behave on a beautiful manner:
    %Conversation Between Chatbot and User%

    User: What is Ai? Tell me in 50 words.
    Chatbot:AI, or Artificial Intelligence, refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. These machines can perform tasks such as learning, problem-solving, perception, and language understanding, often improving their performance based on experience.

    User:Hi there!
    Chatbot:Hello! How can I assist you today?

    User:What are AI's Subfields? list down just names.
    Chatbot: *Machine Learning
    *Natural Language Processing (NLP)
    *Robotics
    *Computer Vision
    *Expert Systems
    *Speech Recognition
    *Planning and Scheduling
    *Knowledge Representation

    User:Thank you!
    Chatbot:You're welcome! If you have any more questions or need further assistance, feel free to ask.


    Information about me, from previous conversations:
    - {{recall 'About Sarfaraz Ahmed'}}

    {{$request}}
    """.strip()

    prompt_template_config = PromptTemplateConfig(
        template=prompt,
        execution_settings={
            service_id: kernel.get_service(
                service_id).get_prompt_execution_settings_class()(service_id=service_id)
        },
    )

    chat_func = kernel.create_function_from_prompt(
        function_name="chat_with_memory",
        plugin_name="TextMemoryPlugin",
        prompt_template_config=prompt_template_config,
    )

    return chat_func


async def chat(kernel: sk.Kernel, chat_func: sk.KernelFunction) -> bool:
    user_input = input("User:> ")

    if user_input.lower() == "exit":
        print("\n\nExiting chat...")
        return False
    else:
        answer = await kernel.invoke(chat_func, request=user_input)
        print(f"ChatBot:> {answer}")
        return True


async def main() -> None:
    kernel = sk.Kernel()

    service_id = "chat-gpt"
    kernel.add_service(
        sk_oai.OpenAIChatCompletion(
            service_id=service_id, ai_model_id="gpt-4-turbo-preview", api_key=api_key)
    )
    embedding_gen = sk_oai.OpenAITextEmbedding(
        service_id="ada", ai_model_id="text-embedding-ada-002", api_key=api_key
    )
    kernel.add_service(embedding_gen)

    memory = SemanticTextMemory(
        storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)
    kernel.import_plugin_from_object(
        TextMemoryPlugin(memory), "TextMemoryPlugin")

    await populate_memory_from_files(memory)
    # await search_memory_examples(memory)
    chat_func = await setup_chat_with_memory(kernel, service_id)
    chatting = True
    while chatting:
        chatting = await chat(kernel, chat_func)


if __name__ == "__main__":
    asyncio.run(main())
