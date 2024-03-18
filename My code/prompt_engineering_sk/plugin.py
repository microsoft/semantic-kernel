from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, AzureChatCompletion
import semantic_kernel as sk
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('var.env')
key = os.getenv('OPENAI_API_KEY')


kernel = sk.Kernel()

kernel.add_chat_service(
    "chat-gpt", OpenAIChatCompletion("gpt-3.5-turbo", key))


async def main():

    plugins_directory = "./plugins"
    writer_plugin = kernel.import_semantic_plugin_from_directory(
        plugins_directory, "WriterPlugin")
    poem_function = writer_plugin["ShortPoem"]

    while True:
        context = input("\nProvide Context to write a short poem: ")
        print("")

        if context.upper() == 'EXIT':
            break

        else:
            poemResult_context = await poem_function(context)
            final_poem = poemResult_context.result
            print(f"POEM on the context: {context}\n")
            print(final_poem)


if __name__ == "__main__":
    asyncio.run(main())
